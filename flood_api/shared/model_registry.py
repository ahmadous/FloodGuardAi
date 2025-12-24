from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Tuple

from joblib import load

from .config import CLASS_NAMES, IMG_SIZE, MODELS_DIR

try:
    import torch
    from torchvision import models, transforms
except ModuleNotFoundError:  # Torch only nécessaire pour la classification image
    torch = None
    models = None
    transforms = None


_DEVICE = None if torch is None else torch.device("cuda" if torch.cuda.is_available() else "cpu")


def get_device() -> torch.device:
    _ensure_torch_available("get_device")
    return _DEVICE


def get_image_transform() -> transforms.Compose:
    _ensure_torch_available("get_image_transform")
    return transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
    ])


@lru_cache(maxsize=1)
def load_image_classifier() -> torch.nn.Module:
    _ensure_torch_available("load_image_classifier")
    model = models.resnet18(weights=None)
    model.fc = torch.nn.Linear(model.fc.in_features, len(CLASS_NAMES))
    state_path = MODELS_DIR / "best_flood_classifier (1).pth"
    model.load_state_dict(torch.load(state_path, map_location=_DEVICE))
    model.to(_DEVICE)
    model.eval()
    return model


@lru_cache(maxsize=1)
def load_weather_artifacts() -> "WeatherArtifacts":
    model_path = MODELS_DIR / "random_forest_predict_model.pkl"
    scaler_path = MODELS_DIR / "scaler_predict.pkl"
    metadata_path = MODELS_DIR / "flood_predict_metadata.json"

    rf_model = load(model_path)
    scaler = load(scaler_path)
    metadata = {}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return WeatherArtifacts(model=rf_model, scaler=scaler, metadata=metadata)


@dataclass(frozen=True)
class WeatherArtifacts:
    model: object
    scaler: object
    metadata: dict


def _ensure_torch_available(caller: str) -> None:
    if torch is None:
        raise ImportError(
            "PyTorch est requis pour utiliser '{}' mais n'est pas installé. "
            "Installez les dépendances du service de classification.".format(caller)
        )
