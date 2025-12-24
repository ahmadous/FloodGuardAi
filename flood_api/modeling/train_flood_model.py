"""Train a flood-risk classifier from historical meteorological observations.

This module assembles a reproducible workflow that:
    1. Ingests the hourly CSV exports stored under ``flood_api/donnees``.
    2. Cleans and aggregates the signal at a daily cadence for each location.
    3. Engineers rolling rainfall indicators and seasonal covariates.
    4. Builds a proxy flood target based on high-intensity rainfall windows.
    5. Trains and evaluates a classifier, then persists the scaler/model artefacts.

Run the script from the repository root once the Python dependencies are available::

    python -m flood_api.modeling.train_flood_model \
        --data-dir flood_api/donnees \
        --models-dir flood_api/models

The resulting ``random_forest_model.pkl`` and ``scaler.pkl`` are compatible with
``flood_api.services.forecast_service``.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------------
# Configuration containers
# ---------------------------------------------------------------------------

RAINY_MONTHS = {6, 7, 8, 9, 10}

AGGREGATION_MAP: Dict[str, Iterable[str]] = {
    "precipitation_mm": ("sum", "max"),
    "rain_mm": ("sum", "max"),
    "relative_humidity_2m_pct": ("mean", "min", "max"),
    "temperature_2m_degc": ("mean", "min", "max"),
    "dew_point_2m_degc": ("mean",),
    "vapour_pressure_deficit_kpa": ("mean", "max"),
    "pressure_msl_hpa": ("mean",),
    "surface_pressure_hpa": ("mean",),
    "wind_speed_10m_km_per_h": ("mean",),
    "wind_speed_100m_km_per_h": ("mean",),
    "wind_gusts_10m_km_per_h": ("mean", "max"),
    "soil_moisture_0_to_7cm_m3_per_m3": ("mean", "max"),
    "soil_moisture_7_to_28cm_m3_per_m3": ("mean",),
    "soil_moisture_28_to_100cm_m3_per_m3": ("mean",),
    "soil_moisture_100_to_255cm_m3_per_m3": ("mean",),
    "soil_temperature_0_to_7cm_degc": ("mean",),
    "soil_temperature_7_to_28cm_degc": ("mean",),
    "soil_temperature_28_to_100cm_degc": ("mean",),
    "soil_temperature_100_to_255cm_degc": ("mean",),
    "cloud_cover_pct": ("mean",),
    "cloud_cover_low_pct": ("mean",),
    "cloud_cover_mid_pct": ("mean",),
    "cloud_cover_high_pct": ("mean",),
    "et0_fao_evapotranspiration_mm": ("sum",),
    "shortwave_radiation_w_per_m2": ("sum", "mean"),
}


@dataclass
class TrainingMetrics:
    roc_auc: float
    average_precision: float
    recall: float
    precision: float
    f1: float
    support: Dict[str, int]
    threshold_daily_mm: float
    threshold_three_day_mm: float


@dataclass
class TrainingReport:
    features: List[str]
    rainy_months: List[int]
    train_span: Tuple[str, str]
    test_span: Tuple[str, str]
    metrics: TrainingMetrics


# ---------------------------------------------------------------------------
# Data ingestion utilities
# ---------------------------------------------------------------------------

def _normalise_column(label: str) -> str:
    substitutions = {
        " ": "_",
        "/": "_per_",
        "%": "pct",
        "°": "deg",
        "²": "2",
        "³": "3",
        "(": "",
        ")": "",
        "-": "_",
    }
    normalised = label.strip().lower()
    for orig, replacement in substitutions.items():
        normalised = normalised.replace(orig, replacement)
    while "__" in normalised:
        normalised = normalised.replace("__", "_")
    return normalised.strip("_")


def _extract_metadata(path: Path) -> Dict[str, str]:
    head = pd.read_csv(path, nrows=1, encoding="utf-8")
    if head.empty:
        return {}
    record = head.iloc[0].to_dict()
    return {_normalise_column(key): value for key, value in record.items()}


def _location_from_path(path: Path) -> Tuple[str, str]:
    parts = path.stem.split("_")
    if len(parts) >= 3 and all(part.isdigit() for part in parts[-2:]):
        location = "_".join(parts[:-2])
        region = parts[0]
    else:
        location = path.stem
        region = parts[0]
    return location, region


def load_hourly_data(data_dir: Path) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for csv_path in sorted(data_dir.glob("*.csv")):
        metadata = _extract_metadata(csv_path)
        frame = pd.read_csv(csv_path, skiprows=3, encoding="utf-8")
        frame.columns = [_normalise_column(col) for col in frame.columns]
        if "time" not in frame.columns:
            raise ValueError(f"'time' column missing in {csv_path.name}")

        frame["time"] = pd.to_datetime(frame["time"], errors="coerce")
        frame = frame.dropna(subset=["time"])

        numeric_cols = [col for col in frame.columns if col != "time"]
        frame[numeric_cols] = frame[numeric_cols].apply(pd.to_numeric, errors="coerce")

        location, region = _location_from_path(csv_path)
        frame["location"] = location
        frame["region"] = region

        for key in ("latitude", "longitude", "elevation", "utc_offset_seconds"):
            if key in metadata:
                frame[key] = pd.to_numeric(metadata[key], errors="coerce")

        frames.append(frame)

    if not frames:
        raise FileNotFoundError(f"Aucun CSV trouvé dans {data_dir}")

    data = pd.concat(frames, ignore_index=True)
    data = data.sort_values(["location", "time"])

    return data


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def _flatten_columns(columns: pd.MultiIndex) -> List[str]:
    flattened = []
    for base, stat in columns:
        if not stat or stat == "<lambda>":
            flattened.append(base)
        else:
            flattened.append(f"{base}_{stat}")
    return flattened


def aggregate_daily(hourly: pd.DataFrame) -> pd.DataFrame:
    hourly = hourly.copy()
    hourly["date"] = hourly["time"].dt.floor("D")

    agg_dict: Dict[str, List[str]] = {}
    for feature, stats in AGGREGATION_MAP.items():
        if feature in hourly.columns:
            agg_dict[feature] = list(stats)

    base_columns = {
        "latitude": "first",
        "longitude": "first",
        "elevation": "first",
        "region": "first",
    }

    grouped = (
        hourly.groupby(["location", "date"])
        .agg({**base_columns, **agg_dict})
        .dropna(how="all")
    )

    grouped.columns = _flatten_columns(grouped.columns)
    grouped = grouped.reset_index()

    return grouped


def _seasonal_features(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["month"] = frame["date"].dt.month
    frame["dayofyear"] = frame["date"].dt.dayofyear
    frame["is_rainy_season"] = frame["month"].isin(RAINY_MONTHS).astype(int)
    frame["dayofyear_sin"] = np.sin(2 * math.pi * frame["dayofyear"] / 365.25)
    frame["dayofyear_cos"] = np.cos(2 * math.pi * frame["dayofyear"] / 365.25)
    return frame


def _rolling_features(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.sort_values(["location", "date"]).copy()

    def enrich(group: pd.DataFrame) -> pd.DataFrame:
        group = group.sort_values("date")

        precip = group.get("precipitation_mm_sum")
        rain_sum = group.get("rain_mm_sum")
        humidity = group.get("relative_humidity_2m_pct_mean")
        temperature = group.get("temperature_2m_degc_mean")
        soil_top = group.get("soil_moisture_0_to_7cm_m3_per_m3_mean")
        soil_sub = group.get("soil_moisture_7_to_28cm_m3_per_m3_mean")

        if precip is not None:
            group["precip_3d_sum"] = precip.rolling(3, min_periods=1).sum()
            group["precip_7d_sum"] = precip.rolling(7, min_periods=1).sum()

        if rain_sum is not None:
            group["rain_3d_sum"] = rain_sum.rolling(3, min_periods=1).sum()
            group["rain_7d_sum"] = rain_sum.rolling(7, min_periods=1).sum()

        if humidity is not None:
            group["humidity_3d_mean"] = humidity.rolling(3, min_periods=1).mean()
            group["humidity_7d_mean"] = humidity.rolling(7, min_periods=1).mean()

        if temperature is not None:
            group["temp_3d_mean"] = temperature.rolling(3, min_periods=1).mean()
            group["temp_7d_mean"] = temperature.rolling(7, min_periods=1).mean()

        if soil_top is not None and soil_sub is not None:
            group["soil_moisture_gradient"] = soil_top - soil_sub

        if precip is not None and soil_top is not None:
            group["rain_to_moisture_ratio"] = precip / (soil_top.clip(lower=1e-3))

        return group

    enriched = frame.groupby("location", group_keys=False).apply(enrich)
    return enriched


def build_training_table(hourly: pd.DataFrame) -> pd.DataFrame:
    daily = aggregate_daily(hourly)
    daily = daily.drop(columns=["latitude", "longitude", "elevation", "region"], errors="ignore")
    daily = _seasonal_features(daily)
    if not daily.empty:
        daily = daily[daily["date"].dt.month.isin(RAINY_MONTHS)]
    daily = _rolling_features(daily)
    daily = daily.dropna(subset=["precipitation_mm_sum"])
    return daily


# ---------------------------------------------------------------------------
# Labelling and train/test slicing
# ---------------------------------------------------------------------------

def derive_targets(
    table: pd.DataFrame,
    split_date: pd.Timestamp,
    daily_quantile: float,
    three_day_quantile: float,
) -> Tuple[pd.DataFrame, pd.DataFrame, float, float]:
    table = table.copy()
    table["date"] = pd.to_datetime(table["date"])

    train_mask = table["date"] < split_date
    train = table.loc[train_mask]
    test = table.loc[~train_mask]

    if train.empty or test.empty:
        raise ValueError("Train/test split produced empty partitions; adjust --split-date.")

    daily_cutoff = float(train["precipitation_mm_sum"].quantile(daily_quantile))
    three_day_cutoff = float(train["precip_3d_sum"].quantile(three_day_quantile))

    def _label(df: pd.DataFrame) -> pd.DataFrame:
        target = (
            (df["precipitation_mm_sum"] >= daily_cutoff)
            | (df["precip_3d_sum"] >= three_day_cutoff)
        ).astype(int)
        df = df.copy()
        df["flood_risk"] = target
        return df

    train = _label(train)
    test = _label(test)

    # Guard against degenerate targets.
    if train["flood_risk"].nunique() < 2:
        raise ValueError(
            "La cible proxy est dégénérée (classe unique). "
            "Abaissez les quantiles ou ajustez les seuils."
        )

    return train, test, daily_cutoff, three_day_cutoff


# ---------------------------------------------------------------------------
# Model training / evaluation
# ---------------------------------------------------------------------------

SELECTED_FEATURES = [
    "precipitation_mm_sum",
    "precipitation_mm_max",
    "relative_humidity_2m_pct_mean",
    "relative_humidity_2m_pct_max",
    "temperature_2m_degc_mean",
    "temperature_2m_degc_max",
]


def _prepare_matrix(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    features = df[SELECTED_FEATURES].fillna(method="ffill").fillna(method="bfill").fillna(0)
    target = df["flood_risk"].to_numpy(dtype=int)
    return features.to_numpy(dtype=float), target


def train_model(train: pd.DataFrame, test: pd.DataFrame) -> Tuple[RandomForestClassifier, StandardScaler, TrainingMetrics]:
    X_train, y_train = _prepare_matrix(train)
    X_test, y_test = _prepare_matrix(test)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=400,
        max_depth=10,
        min_samples_leaf=5,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train_scaled, y_train)

    proba_test = model.predict_proba(X_test_scaled)[:, 1]
    pred_test = (proba_test >= 0.5).astype(int)

    roc_auc = float(roc_auc_score(y_test, proba_test))
    avg_precision = float(average_precision_score(y_test, proba_test))
    report = classification_report(y_test, pred_test, output_dict=True)
    support = {
        "train_total": int(y_train.size),
        "train_positive": int(y_train.sum()),
        "test_total": int(y_test.size),
        "test_positive": int(y_test.sum()),
    }

    metrics = TrainingMetrics(
        roc_auc=roc_auc,
        average_precision=avg_precision,
        recall=float(report["1"]["recall"]),
        precision=float(report["1"]["precision"]),
        f1=float(report["1"]["f1-score"]),
        support=support,
        threshold_daily_mm=0.0,  # placeholder, set by caller
        threshold_three_day_mm=0.0,
    )

    return model, scaler, metrics


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

def _dump_metadata(
    models_dir: Path,
    report: TrainingReport,
) -> None:
    payload = {
        "features": report.features,
        "rainy_months": report.rainy_months,
        "train_span": {"start": report.train_span[0], "end": report.train_span[1]},
        "test_span": {"start": report.test_span[0], "end": report.test_span[1]},
        "performance": {
            "roc_auc_test": report.metrics.roc_auc,
            "average_precision_test": report.metrics.average_precision,
            "recall_test": report.metrics.recall,
            "precision_test": report.metrics.precision,
            "f1_test": report.metrics.f1,
        },
        "class_support": report.metrics.support,
        "label_thresholds": {
            "daily_rain_mm": report.metrics.threshold_daily_mm,
            "three_day_rain_mm": report.metrics.threshold_three_day_mm,
        },
    }

    target = models_dir / "flood_model_metadata.json"
    with target.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=True)


def _print_eda_snapshot(train: pd.DataFrame, test: pd.DataFrame) -> None:
    print("=== Aperçu EDA ===")
    print("Train span:", train["date"].min(), "->", train["date"].max())
    print("Test span :", test["date"].min(), "->", test["date"].max())

    print("\nRépartition cible (train/test):")
    train_counter = Counter(train["flood_risk"])
    test_counter = Counter(test["flood_risk"])
    print("  Train:", dict(train_counter))
    print("  Test :", dict(test_counter))

    print("\nStatistiques précipitations (train):")
    print(train["precipitation_mm_sum"].describe(percentiles=[0.5, 0.9, 0.95, 0.99]))

    print("\nStatistiques précipitations (test):")
    print(test["precipitation_mm_sum"].describe(percentiles=[0.5, 0.9, 0.95, 0.99]))

    cm = confusion_matrix(test["flood_risk"], (test["flood_risk"] == 1).astype(int))
    print("\nMatrice de confusion (cible proxy vs elle-même, sanity check):")
    print(cm)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a flood prediction classifier.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("flood_api/donnees"),
        help="Répertoire contenant les CSV horaires (par défaut: flood_api/donnees).",
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=Path("flood_api/models"),
        help="Répertoire de sortie des artefacts (par défaut: flood_api/models).",
    )
    parser.add_argument(
        "--split-date",
        type=str,
        default="2023-01-01",
        help="Date ISO scindant train/test (ex: 2023-01-01).",
    )
    parser.add_argument(
        "--daily-quantile",
        type=float,
        default=0.97,
        help="Quantile train pour le seuil pluie journalière.",
    )
    parser.add_argument(
        "--three-day-quantile",
        type=float,
        default=0.95,
        help="Quantile train pour le seuil pluie cumulée 3 jours.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    hourly = load_hourly_data(args.data_dir)
    table = build_training_table(hourly)

    split_ts = pd.Timestamp(args.split_date)
    train, test, daily_cutoff, three_day_cutoff = derive_targets(
        table,
        split_ts,
        args.daily_quantile,
        args.three_day_quantile,
    )

    _print_eda_snapshot(train, test)

    model, scaler, metrics = train_model(train, test)
    metrics.threshold_daily_mm = daily_cutoff
    metrics.threshold_three_day_mm = three_day_cutoff

    models_dir: Path = args.models_dir
    models_dir.mkdir(parents=True, exist_ok=True)

    model_path = models_dir / "random_forest_model.pkl"
    scaler_path = models_dir / "scaler.pkl"

    pd.to_pickle(model, model_path)
    pd.to_pickle(scaler, scaler_path)

    report = TrainingReport(
        features=SELECTED_FEATURES,
        rainy_months=sorted(RAINY_MONTHS),
        train_span=(
            train["date"].min().isoformat(),
            train["date"].max().isoformat(),
        ),
        test_span=(
            test["date"].min().isoformat(),
            test["date"].max().isoformat(),
        ),
        metrics=metrics,
    )
    _dump_metadata(models_dir, report)

    print("\n=== Evaluation test ===")
    print(f"ROC-AUC      : {metrics.roc_auc:.3f}")
    print(f"AveragePrec. : {metrics.average_precision:.3f}")
    print(f"Recall       : {metrics.recall:.3f}")
    print(f"Precision    : {metrics.precision:.3f}")
    print(f"F1           : {metrics.f1:.3f}")
    print("Supports     :", metrics.support)
    print("Seuils pluie :", {"1j_mm": daily_cutoff, "3j_mm": three_day_cutoff})
    print(f"\nArtefacts sauvegardés dans: {models_dir}")


if __name__ == "__main__":
    main()
