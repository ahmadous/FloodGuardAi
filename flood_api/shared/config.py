from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

IMG_SIZE = 128
CLASS_NAMES = ["flooded", "not_flooded"]
SEUIL_OPTIMAL = 0.35
