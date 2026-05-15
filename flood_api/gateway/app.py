from __future__ import annotations

import os
from typing import Any

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

from flood_api.gateway.geo import geo_bp
 
def _get_service_url(env_key: str, default: str) -> str:
    raw = os.getenv(env_key, default)
    value = (raw or "").strip()
    if value and (value.startswith("http://") or value.startswith("https://")):
        return value.rstrip("/")
    return default


CLASSIFICATION_SERVICE_URL = _get_service_url("CLASSIFICATION_SERVICE_URL", "http://localhost:5001")
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
        return {"classification": classification}, 200

    @app.route("/predict_class", methods=["POST"])
    def predict_class():
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        file.stream.seek(0)
        files = {"file": (file.filename, file.stream, file.content_type)}
        return _proxy_json(f"{CLASSIFICATION_SERVICE_URL}/predict_class", files=files)

    @app.route("/", methods=["GET"])
    def root() -> str:
        return "Flood API Gateway"

    return app


gateway_app = create_app()


if __name__ == "__main__":
    gateway_app.run(host="0.0.0.0", port=5000, debug=True)
