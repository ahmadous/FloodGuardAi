from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

IMG_SIZE = 128
CLASS_NAMES = ["flooded", "not_flooded"]
SEUIL_OPTIMAL = 0.35

ZONE_COORDS = {
    "dakar_keur_massar": (15.43058, -15.887329),
    "kaolack_leona": (13.813708, -15.551483),
    "kolda": (12.899824, -14.959137),
    "tambacounda": (13.743409, -13.636383),
    "touba": (14.86819, -15.852753),
}

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast?"
    "latitude={lat}&longitude={lon}"
    "&hourly=temperature_2m,precipitation,relative_humidity_2m"
    "&forecast_days=15&timezone=Africa%2FDakar"
)
