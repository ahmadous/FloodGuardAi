from __future__ import annotations

import io

from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image
import torch

from flood_api.shared.config import CLASS_NAMES
from flood_api.shared.model_registry import (
    get_device,
    get_image_transform,
    load_image_classifier,
)

app = Flask(__name__)
CORS(app)

_device = get_device()
_transform = get_image_transform()
_model = load_image_classifier()


@app.route("/health", methods=["GET"])
def health_check() -> tuple[dict[str, str], int]:
    return {"status": "ok"}, 200


@app.route("/predict_class", methods=["POST"])
def predict_class():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    try:
        contents = file.read()
        if not contents:
            return jsonify({"error": "Empty file"}), 400

        image = Image.open(io.BytesIO(contents)).convert("RGB")
        img_tensor = _transform(image).unsqueeze(0).to(_device)

        with torch.no_grad():
            out = _model(img_tensor)
            probabilities = torch.softmax(out, dim=1)[0]
            prediction = probabilities.argmax().item()

        return jsonify(
            {
                "prediction": CLASS_NAMES[prediction],
                "proba": float(probabilities[prediction]),
            }
        )
    except Exception as exc:  # noqa: BLE001 - we want to bubble any runtime failure
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
