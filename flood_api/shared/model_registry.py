from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from .config import CLASS_NAMES, IMG_SIZE, MODELS_DIR

try:
    import torch
    from torchvision import models, transforms
    import timm
except ModuleNotFoundError:  # Torch only nécessaire pour la classification image
    torch = None
    models = None
    transforms = None
    timm = None


_DEVICE = None if torch is None else torch.device("cuda" if torch.cuda.is_available() else "cpu")


def get_device() -> torch.device:
    _ensure_torch_available("get_device")
    return _DEVICE


def get_image_transform() -> transforms.Compose:
    _ensure_torch_available("get_image_transform")
    return transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        # ConvNeXt-Tiny (et tous les modèles pré-entraînés ImageNet) exigent
        # cette normalisation exacte. Sans elle, les prédictions sont aberrantes.
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])


@lru_cache(maxsize=1)
def load_image_classifier() -> torch.nn.Module:
    _ensure_torch_available("load_image_classifier")

    # build model architecture first (ConvNeXt-Tiny model)
    model = timm.create_model('convnext_tiny', pretrained=False, num_classes=len(CLASS_NAMES))

    # decide which checkpoint to load.  prefer the new ConvNeXt model file
    # and allow overriding via env var so deployment can be flexible.
    env_path = os.getenv("IMAGE_CLASSIFIER_PATH")
    candidates = []
    if env_path:
        candidates.append(env_path)
    # look for the ConvNeXt model first, then fall back to older models if needed
    candidates.extend(["best_ConvNeXt_Tiny.pth", "best_flood_model.pth", "best_flood_classifier (1).pth"])

    state_path: Path | None = None
    for fname in candidates:
        p = MODELS_DIR / fname
        if p.exists():
            state_path = p
            break
    if state_path is None:
        raise FileNotFoundError(
            f"no image classifier weights found in {MODELS_DIR}; tried {candidates}"
        )

    # load state dict; some checkpoints may have been saved with all keys
    # prefixed by "model.". We strip this prefix if necessary.
    state = torch.load(state_path, map_location=_DEVICE)
    if isinstance(state, dict):
        # strip prefix if necessary
        if any(k.startswith("model.") for k in state.keys()):
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"checkpoint {state_path} contains wrapped keys; stripping prefix")
            stripped = {k.partition("model.")[-1]: v for k, v in state.items()}
            state = stripped
    model.load_state_dict(state)
    model.to(_DEVICE)
    model.eval()
    return model


def _ensure_torch_available(caller: str) -> None:
    if torch is None:
        raise ImportError(
            "PyTorch est requis pour utiliser '{}' mais n'est pas installé. "
            "Installez les dépendances du service de classification.".format(caller)
        )
