#!/bin/bash
# ─── start_render.sh ──────────────────────────────────────────────────────────
# Script de démarrage pour Render.com.
# Démarre uniquement le gateway sur le port $PORT fourni par Render.
# ──────────────────────────────────────────────────────────────────────────────
set -e

RENDER_PORT="${PORT:-10000}"

echo "[render] Démarrage du gateway sur 0.0.0.0:$RENDER_PORT ..."
exec gunicorn \
    --bind "0.0.0.0:$RENDER_PORT" \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --log-level info \
    "flood_api.gateway.app:gateway_app"
