from pathlib import Path

MODELS_DIR = Path("/app/models")
CLASS_NAMES = ["flooded", "not_flooded"]
IMG_SIZE = 128
SEUIL_OPTIMAL = 0.35  # seuil calibré lors de l'entraînement
