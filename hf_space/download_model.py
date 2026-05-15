"""
Télécharge best_ConvNeXt_Tiny.pth depuis Passeydou/floodguard-models sur HF Hub.
Exécuté une fois au moment du docker build.
"""
from pathlib import Path
from huggingface_hub import hf_hub_download

MODELS_DIR = Path("/app/models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

print("[download_model] Téléchargement de best_ConvNeXt_Tiny.pth ...")

path = hf_hub_download(
    repo_id="Passeydou/floodguard-models",
    filename="best_ConvNeXt_Tiny.pth",
    local_dir=str(MODELS_DIR),
)

print(f"[download_model] Modèle téléchargé : {path}")
