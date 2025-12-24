from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

from flood_api.shared.config import SEUIL_OPTIMAL


@dataclass
class PredictionResult:
    prediction: int
    proba_inondation: float

    @property
    def inondation(self) -> bool:
        return bool(self.prediction)


def build_feature_vector(
    precipitation_sum: float,
    humidity_mean: float,
    temperature_mean: float,
    precipitation_max: Optional[float] = None,
    humidity_max: Optional[float] = None,
    temperature_max: Optional[float] = None,
    precip_3d_sum: Optional[float] = None,
    precip_7d_sum: Optional[float] = None,
    precip_15d_sum: Optional[float] = None,
) -> Mapping[str, float]:
    precipitation_sum = float(precipitation_sum)
    precipitation_max = float(precipitation_sum if precipitation_max is None else precipitation_max)
    humidity_mean = float(humidity_mean)
    humidity_max = float(humidity_mean if humidity_max is None else humidity_max)
    temperature_mean = float(temperature_mean)
    temperature_max = float(temperature_mean if temperature_max is None else temperature_max)

    precip_3d_sum = precipitation_sum if precip_3d_sum is None else float(precip_3d_sum)
    precip_7d_sum = precipitation_sum if precip_7d_sum is None else float(precip_7d_sum)
    precip_15d_sum = precipitation_sum if precip_15d_sum is None else float(precip_15d_sum)

    return {
        "precipitation_mm_sum": precipitation_sum,
        "precipitation_mm_max": precipitation_max,
        "relative_humidity_2m_pct_mean": humidity_mean,
        "relative_humidity_2m_pct_max": humidity_max,
        "temperature_2m_degc_mean": temperature_mean,
        "temperature_2m_degc_max": temperature_max,
        "precip_3d_sum": precip_3d_sum,
        "precip_7d_sum": precip_7d_sum,
        "precip_15d_sum": precip_15d_sum,
    }


def set_feature_order(feature_names: Sequence[str]) -> None:
    global _FEATURE_ORDER
    _FEATURE_ORDER = list(feature_names)


def get_feature_order() -> List[str]:
    return list(_FEATURE_ORDER)


def _as_model_input(features: Iterable[float], scaler):
    if isinstance(features, Mapping):
        ordered = [float(features.get(name, 0.0)) for name in _FEATURE_ORDER]
    else:
        ordered = list(features)
        if len(ordered) < len(_FEATURE_ORDER):
            ordered.extend([0.0] * (len(_FEATURE_ORDER) - len(ordered)))
        elif len(ordered) > len(_FEATURE_ORDER):
            ordered = ordered[: len(_FEATURE_ORDER)]
    values = np.array(ordered, dtype=float).reshape(1, -1)
    return values


def predict_from_features(features: Iterable[float], model, scaler) -> PredictionResult:
    model_input = _as_model_input(features, scaler)
    scaled_features = scaler.transform(model_input)
    probabilities = model.predict_proba(scaled_features)[0]
    proba_inond = float(probabilities[1])
    prediction = int(proba_inond >= SEUIL_OPTIMAL)
    return PredictionResult(prediction=prediction, proba_inondation=proba_inond)


def aggregate_daily_features(
    day_slice: pd.DataFrame,
    recent_precipitation_sums: Optional[Sequence[float]] = None,
) -> Mapping[str, float]:
    precipitation_sum = float(day_slice["precipitation"].sum())
    precipitation_max = float(day_slice["precipitation"].max())
    humidity_mean = float(day_slice["relative_humidity_2m"].mean())
    humidity_max = float(day_slice["relative_humidity_2m"].max())
    temperature_mean = float(day_slice["temperature_2m"].mean())
    temperature_max = float(day_slice["temperature_2m"].max())

    base_vector = build_feature_vector(
        precipitation_sum=precipitation_sum,
        precipitation_max=precipitation_max,
        humidity_mean=humidity_mean,
        humidity_max=humidity_max,
        temperature_mean=temperature_mean,
        temperature_max=temperature_max,
    )

    history = list(recent_precipitation_sums or [])
    history.append(precipitation_sum)
    base_vector = dict(base_vector)
    base_vector["precip_3d_sum"] = _rolling_sum(history, 3)
    base_vector["precip_7d_sum"] = _rolling_sum(history, 7)
    base_vector["precip_15d_sum"] = _rolling_sum(history, 15)
    return base_vector


def _rolling_sum(values: Sequence[float], window: int) -> float:
    if window <= 0:
        return 0.0
    if not values:
        return 0.0
    tail = values[-window:]
    return float(sum(tail))


_FEATURE_ORDER = [
    "precipitation_mm_sum",
    "precipitation_mm_max",
    "relative_humidity_2m_pct_mean",
    "relative_humidity_2m_pct_max",
    "temperature_2m_degc_mean",
    "temperature_2m_degc_max",
    "precip_3d_sum",
    "precip_7d_sum",
    "precip_15d_sum",
]
