"""
FloodGuardAI — Classification Service (Hugging Face Spaces)
API Flask pour la détection d'inondation par image avec ConvNeXt-Tiny.
"""
from __future__ import annotations

import io
import os

import timm
import torch
from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image
from torchvision import transforms

from config import CLASS_NAMES, IMG_SIZE, MODELS_DIR, SEUIL_OPTIMAL

app = Flask(__name__)
CORS(app)

# ── Chargement du modèle ────────────────────────────────────────────────────
_device = torch.device("cpu")
_DEFAULT_THRESHOLD = SEUIL_OPTIMAL  # seuil optimal calibré lors de l'entraînement

_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    # ConvNeXt-Tiny exige la normalisation ImageNet standard.
    # Sans elle, les pixels [0,1] ne correspondent pas aux entrées attendues.
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])


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

def _load_model() -> torch.nn.Module:
    model_path = MODELS_DIR / "best_ConvNeXt_Tiny.pth"
    if not model_path.exists():
        raise FileNotFoundError(f"Modèle introuvable : {model_path}")

    model = timm.create_model("convnext_tiny", pretrained=False, num_classes=len(CLASS_NAMES))
    state = torch.load(model_path, map_location=_device)

    # Certains checkpoints ont les clés préfixées par "model."
    if isinstance(state, dict) and any(k.startswith("model.") for k in state.keys()):
        state = {k.partition("model.")[-1]: v for k, v in state.items()}

    model.load_state_dict(state)
    model.to(_device)
    model.eval()
    print(f"[app] Modèle chargé depuis {model_path}")
    return model

_model = _load_model()


# ── Routes ──────────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
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

        proba_dict = {name: float(probabilities[idx]) for idx, name in enumerate(CLASS_NAMES)}
        flood_probability = float(probabilities[_FLOOD_INDEX])
        decision_is_flooded = flood_probability >= _DECISION_THRESHOLD
        decision_label = _FLOOD_LABEL if decision_is_flooded else _NON_FLOOD_LABEL
        decision_confidence = flood_probability if decision_is_flooded else 1.0 - flood_probability

        return jsonify({
            "prediction": decision_label,
            "proba": float(decision_confidence),
            "probabilities": proba_dict,
            "decision_is_flooded": decision_is_flooded,
            "decision_label": decision_label,
            "decision_threshold": _DECISION_THRESHOLD,
            "flood_probability": flood_probability,
            "raw_prediction": CLASS_NAMES[raw_prediction_idx],
            "raw_proba": float(probabilities[raw_prediction_idx]),
        })

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
