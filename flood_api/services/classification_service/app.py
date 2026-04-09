from __future__ import annotations

import io
import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image
import torch

from flood_api.shared.config import CLASS_NAMES, SEUIL_OPTIMAL
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
_DEFAULT_THRESHOLD = SEUIL_OPTIMAL  # seuil optimal calibré lors de l'entraînement


def _safe_threshold(value: str | None, default: float = _DEFAULT_THRESHOLD) -> float:
    try:
        threshold = float(value) if value is not None else default
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, threshold))


_DECISION_THRESHOLD = _safe_threshold(os.getenv("FLOOD_DECISION_THRESHOLD"))
_FLOOD_LABEL = "flooded" if "flooded" in CLASS_NAMES else CLASS_NAMES[0]
_NON_FLOOD_LABEL = "not_flooded" if "not_flooded" in CLASS_NAMES else CLASS_NAMES[-1]
_FLOOD_INDEX = CLASS_NAMES.index(_FLOOD_LABEL)
# expose which model file we're using so the docker logs make it obvious
try:
    setting = os.getenv("IMAGE_CLASSIFIER_PATH")
    if setting is not None:
        app.logger.info(f"IMAGE_CLASSIFIER_PATH overridden to {setting}")
    # infer actual path from state dict object if available
    # (the loader may print path during load; we store it there)
except Exception:
    pass


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
            raw_prediction_idx = probabilities.argmax().item()

        # build a dict of all class probabilities so caller cannot misinterpret
        proba_dict = {name: float(probabilities[idx]) for idx, name in enumerate(CLASS_NAMES)}
        flood_probability = float(probabilities[_FLOOD_INDEX])
        decision_is_flooded = flood_probability >= _DECISION_THRESHOLD
        decision_label = _FLOOD_LABEL if decision_is_flooded else _NON_FLOOD_LABEL
        decision_confidence = flood_probability if decision_is_flooded else 1.0 - flood_probability

        return jsonify(
            {
                "prediction": decision_label,
                "proba": float(decision_confidence),
                "probabilities": proba_dict,  # e.g. {"flooded":0.22, "not_flooded":0.78}
                "decision_is_flooded": decision_is_flooded,
                "decision_label": decision_label,
                "decision_threshold": _DECISION_THRESHOLD,
                "flood_probability": flood_probability,
                "raw_prediction": CLASS_NAMES[raw_prediction_idx],
                "raw_proba": float(probabilities[raw_prediction_idx]),
            }
        )
    except Exception as exc:  # noqa: BLE001 - we want to bubble any runtime failure
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
