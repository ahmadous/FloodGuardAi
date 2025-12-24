from __future__ import annotations

import os
from typing import Any

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

from flood_api.gateway.geo import geo_bp
 
CLASSIFICATION_SERVICE_URL = os.getenv("CLASSIFICATION_SERVICE_URL", "http://localhost:5001")
FORECAST_SERVICE_URL = os.getenv("FORECAST_SERVICE_URL", "http://localhost:5002")
REQUEST_TIMEOUT = float(os.getenv("GATEWAY_TIMEOUT", "15"))


def _proxy_json(
    url: str,
    payload: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
):
    try:
        response = requests.post(url, json=payload, files=files, timeout=REQUEST_TIMEOUT)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as exc:
        return jsonify({"error": str(exc)}), 502


def _service_health(url: str) -> tuple[dict[str, Any], int]:
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        return response.json(), response.status_code
    except requests.RequestException as exc:
        return {"status": "unreachable", "error": str(exc)}, 502


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(geo_bp)

    @app.route("/health", methods=["GET"])
    def health() -> tuple[dict[str, Any], int]:
        classification, _ = _service_health(f"{CLASSIFICATION_SERVICE_URL}/health")
        forecast, _ = _service_health(f"{FORECAST_SERVICE_URL}/health")
        return {"classification": classification, "forecast": forecast}, 200

    @app.route("/predict_class", methods=["POST"])
    def predict_class():
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        file.stream.seek(0)
        files = {"file": (file.filename, file.stream, file.content_type)}
        return _proxy_json(f"{CLASSIFICATION_SERVICE_URL}/predict_class", files=files)

    @app.route("/predict_meteo", methods=["POST"])
    def proxy_predict_meteo():
        return _proxy_json(
            f"{FORECAST_SERVICE_URL}/predict_meteo",
            payload=request.get_json(silent=True),
        )

    @app.route("/predict_meteo_manual", methods=["POST"])
    def proxy_predict_meteo_manual():
        return _proxy_json(
            f"{FORECAST_SERVICE_URL}/predict_meteo_manual",
            payload=request.get_json(silent=True),
        )

    @app.route("/predict_meteo_batch", methods=["POST"])
    def proxy_predict_meteo_batch():
        return _proxy_json(
            f"{FORECAST_SERVICE_URL}/predict_meteo_batch",
            payload=request.get_json(silent=True),
        )

    @app.route("/predict_meteo_auto", methods=["POST"])
    def proxy_predict_meteo_auto():
        return _proxy_json(
            f"{FORECAST_SERVICE_URL}/predict_meteo_auto",
            payload=request.get_json(silent=True),
        )

    @app.route("/", methods=["GET"])
    def root() -> str:
        return "Flood API Gateway"

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
