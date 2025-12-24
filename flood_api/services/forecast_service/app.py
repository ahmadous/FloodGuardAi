from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import requests

from flood_api.shared.config import OPEN_METEO_URL, ZONE_COORDS
from flood_api.shared.forecast import (
    aggregate_daily_features,
    build_feature_vector,
    predict_from_features,
    set_feature_order,
    get_feature_order,
)
from flood_api.shared.model_registry import load_weather_artifacts
from flood_api.shared.geodata import compute_context_features

app = Flask(__name__)
CORS(app)

_artifacts = load_weather_artifacts()
_rf_model = _artifacts.model
_scaler = _artifacts.scaler
_metadata = _artifacts.metadata or {}

_FEATURE_NAMES = _metadata.get("features")
if _FEATURE_NAMES:
    set_feature_order(_FEATURE_NAMES)

_FEATURE_NAMES = get_feature_order()

ZONE_REGION_HINT = {
    "dakar_keur_massar": "dakar",
    "kaolack_leona": "kaolack",
    "kolda": None,
    "tambacounda": None,
    "touba": None,
}


def _default_geo_context() -> dict[str, Any]:
    return {
        "geo_available": False,
        "distance_to_flow_m": None,
        "inside_flood_zone": False,
        "region": None,
    }


def _compute_geo_context(lat: Any, lon: Any, region: str | None = None) -> dict[str, Any]:
    try:
        if lat is None or lon is None:
            return _default_geo_context()
        if not region:
            return _default_geo_context()
        lat_f = float(lat)
        lon_f = float(lon)
        ctx = compute_context_features(lat_f, lon_f, region)
        ctx["region"] = region
        return ctx
    except (ValueError, TypeError):
        return _default_geo_context()
    except Exception:  # pragma: no cover - geopandas optional
        return _default_geo_context()


def _optional_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _require_float(value: Any, field: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Champ '{field}' invalide")


def _ensure_feature_mapping(features: Any) -> Dict[str, float]:
    if isinstance(features, Mapping):
        return {name: float(features.get(name, 0.0)) for name in _FEATURE_NAMES}
    values: Sequence[Any] = list(features or [])
    mapping: Dict[str, float] = {}
    for idx, name in enumerate(_FEATURE_NAMES):
        try:
            mapping[name] = float(values[idx])
        except IndexError:
            mapping[name] = 0.0
        except (TypeError, ValueError):
            mapping[name] = 0.0
    return mapping


def _serialize_features(features: Mapping[str, Any]) -> Dict[str, float]:
    return {name: float(features.get(name, 0.0)) for name in _FEATURE_NAMES}


@app.route("/health", methods=["GET"])
def health_check() -> tuple[dict[str, str], int]:
    return {"status": "ok"}, 200


@app.route("/predict_meteo", methods=["POST"])
def predict_meteo():
    payload = request.get_json(silent=True) or {}
    features = payload.get("features")
    if not features:
        return jsonify({"error": "Features missing"}), 400

    feature_vector = _ensure_feature_mapping(features)

    geo_context = _compute_geo_context(
        payload.get("lat") or payload.get("latitude"),
        payload.get("lon") or payload.get("longitude"),
        payload.get("region"),
    )

    prediction = predict_from_features(feature_vector, _rf_model, _scaler)
    return jsonify(
        {
            "prediction": prediction.prediction,
            "proba_inondation": prediction.proba_inondation,
            "prob_non_inondation": 1 - prediction.proba_inondation,
            "inondation": prediction.inondation,
            "geo_context": geo_context,
            "features": _serialize_features(feature_vector),
        }
    )


@app.route("/predict_meteo_manual", methods=["POST"])
def predict_meteo_manual():
    payload = request.get_json(silent=True) or {}
    try:
        precipitation = _require_float(payload.get("precipitation"), "precipitation")
        humidity = _require_float(payload.get("humidity"), "humidity")
        temperature = _require_float(payload.get("temperature"), "temperature")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    feature_vector = dict(
        build_feature_vector(
            precipitation_sum=precipitation,
            humidity_mean=humidity,
            temperature_mean=temperature,
            precipitation_max=_optional_float(payload.get("precipitation_max")),
            humidity_max=_optional_float(payload.get("humidity_max")),
            temperature_max=_optional_float(payload.get("temperature_max")),
            precip_3d_sum=_optional_float(payload.get("precip_3d_sum")),
            precip_7d_sum=_optional_float(payload.get("precip_7d_sum")),
            precip_15d_sum=_optional_float(payload.get("precip_15d_sum")),
        )
    )

    geo_context = _compute_geo_context(
        payload.get("lat") or payload.get("latitude"),
        payload.get("lon") or payload.get("longitude"),
        payload.get("region"),
    )

    prediction = predict_from_features(feature_vector, _rf_model, _scaler)
    return jsonify(
        {
            "prediction": prediction.prediction,
            "proba_inondation": prediction.proba_inondation,
            "inondation": prediction.inondation,
            "geo_context": geo_context,
            "features": _serialize_features(feature_vector),
        }
    )


@app.route("/predict_meteo_batch", methods=["POST"])
def predict_meteo_batch():
    payload = request.get_json(silent=True) or {}
    samples = payload.get("samples", [])

    results: List[Dict[str, Any]] = []
    for entry in samples:
        try:
            precipitation = _require_float(entry.get("precipitation"), "precipitation")
            humidity = _require_float(entry.get("humidity"), "humidity")
            temperature = _require_float(entry.get("temperature"), "temperature")

            feature_vector = dict(
                build_feature_vector(
                    precipitation_sum=precipitation,
                    humidity_mean=humidity,
                    temperature_mean=temperature,
                    precipitation_max=_optional_float(entry.get("precipitation_max")),
                    humidity_max=_optional_float(entry.get("humidity_max")),
                    temperature_max=_optional_float(entry.get("temperature_max")),
                    precip_3d_sum=_optional_float(entry.get("precip_3d_sum")),
                    precip_7d_sum=_optional_float(entry.get("precip_7d_sum")),
                    precip_15d_sum=_optional_float(entry.get("precip_15d_sum")),
                )
            )
            prediction = predict_from_features(feature_vector, _rf_model, _scaler)
            geo_context = _compute_geo_context(
                entry.get("lat") or entry.get("latitude"),
                entry.get("lon") or entry.get("longitude"),
                entry.get("region"),
            )
            serialized_features = _serialize_features(feature_vector)
            results.append(
                {
                    "precipitation": serialized_features["precipitation_mm_sum"],
                    "humidity": serialized_features["relative_humidity_2m_pct_mean"],
                    "temperature": serialized_features["temperature_2m_degc_mean"],
                    "precip_3d_sum": serialized_features["precip_3d_sum"],
                    "precip_7d_sum": serialized_features["precip_7d_sum"],
                    "precip_15d_sum": serialized_features["precip_15d_sum"],
                    "prediction": prediction.prediction,
                    "proba_inondation": prediction.proba_inondation,
                    "inondation": prediction.inondation,
                    "geo_context": geo_context,
                    "features": serialized_features,
                }
            )
        except Exception as exc:  # noqa: BLE001 - capture bad entries without failing the whole batch
            results.append({"error": str(exc), "input": entry})

    return jsonify({"results": results})


@app.route("/predict_meteo_auto", methods=["POST"])
def predict_meteo_auto():
    payload = request.get_json(silent=True) or {}
    zone = (payload.get("zone") or "").strip().lower()
    if zone not in ZONE_COORDS:
        return jsonify({"error": "Zone inconnue"}), 400

    lat, lon = ZONE_COORDS[zone]
    region_hint = ZONE_REGION_HINT.get(zone)
    geo_context = _compute_geo_context(lat, lon, region_hint)
    response = requests.get(OPEN_METEO_URL.format(lat=lat, lon=lon), timeout=10)
    if not response.ok:
        return jsonify({"error": "Erreur Open-Meteo"}), 502

    hourly = response.json().get("hourly", {})
    if not hourly:
        return jsonify({"error": "Réponse Open-Meteo invalide"}), 500

    frame = pd.DataFrame(
        {
            "time": hourly.get("time", []),
            "temperature_2m": hourly.get("temperature_2m", []),
            "relative_humidity_2m": hourly.get("relative_humidity_2m", []),
            "precipitation": hourly.get("precipitation", []),
        }
    )

    if frame.empty:
        return jsonify({"error": "Données météo indisponibles"}), 500

    frame["time"] = pd.to_datetime(frame["time"])
    results: List[Dict[str, Any]] = []
    recent_precip: List[float] = []

    for day in frame["time"].dt.date.unique():
        slice_df = frame[frame["time"].dt.date == day]
        if len(slice_df) < 24:
            continue

        feature_vector = dict(aggregate_daily_features(slice_df, recent_precip))
        serialized = _serialize_features(feature_vector)
        prediction = predict_from_features(feature_vector, _rf_model, _scaler)
        recent_precip.append(serialized["precipitation_mm_sum"])
        if len(recent_precip) > 15:
            recent_precip = recent_precip[-15:]
        results.append(
            {
                "date": str(day),
                "precip_1d_sum": serialized["precipitation_mm_sum"],
                "precip_3d_sum": serialized["precip_3d_sum"],
                "precip_7d_sum": serialized["precip_7d_sum"],
                "precip_15d_sum": serialized["precip_15d_sum"],
                "humidity_1d_mean": serialized["relative_humidity_2m_pct_mean"],
                "temp_1d_mean": serialized["temperature_2m_degc_mean"],
                "proba_inondation": prediction.proba_inondation,
                "inondation": prediction.inondation,
                "geo_context": geo_context,
                "features": serialized,
            }
        )

    return jsonify({"zone": zone, "geo_context": geo_context, "results": results})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
