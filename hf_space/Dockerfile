# ─── Dockerfile — HF Space Classification Service ─────────────────────────────
# Télécharge best_ConvNeXt_Tiny.pth depuis Passeydou/floodguard-models
# et expose l'API Flask sur le port 7860 (port standard HF Spaces).
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Dépendances système minimales
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Dépendances Python ──────────────────────────────────────────────────────
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r /tmp/requirements.txt

# ── Code de l'application ───────────────────────────────────────────────────
COPY app.py /app/app.py
COPY config.py /app/config.py
COPY download_model.py /app/download_model.py

# ── Téléchargement du modèle au moment du build ─────────────────────────────
# Le modèle est stocké dans Passeydou/floodguard-models sur HF Hub
RUN python /app/download_model.py

ENV PYTHONUNBUFFERED=1

# HF Spaces écoute sur le port 7860
EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--threads", "2", "--timeout", "120", "app:app"]
