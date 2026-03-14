# FloodGuardAI 🌊🤖
## AI-Powered Early Flood Detection and Prediction System for Senegal

**Live platform:** https://sengaal-b4ab0.web.app/
**Demo video:** https://youtu.be/ml16aAvDvzs

## Results
- Random Forest: AUC-ROC = 1.000 | Recall = 100% | Zero missed flood events
- ConvNeXt-Tiny: F1-Score = 96.48% | Zero false alerts
- Test set: 2,202 observations (2023–2025) across 6 Senegalese zones

## Description
FloodGuardAI combines machine learning and deep learning 
to detect and predict floods in Senegal, integrating 
citizen participation for real-time early warnings.

## Academic Validation
Master's thesis defended February 16, 2026
Université Iba Der Thiam de Thiès (UIDT) / 
Université de Technologie de Troyes (UTT)

## Author
Papa Ahmadou Seydou SOW
paseydou.sow@univ-thies.sn
Yaatal Digital — Senegal

## Awards
- WSIS Prizes 2026 — AL C7 E-environment
- AI for Good Impact Awards 2026 — AI for Planet
# Flood Monitoring Platform

This repository now follows a microservice layout:

- **Classification Service (5001)** – image flood detection (`flood_api/services/classification_service`).
- **Forecast Service (5002)** – weather driven flood scoring (`flood_api/services/forecast_service`).
- **API Gateway (5000)** – single entry point forwarding requests to the services (`flood_api/gateway`).
- **Frontend (5173)** – Vue 3 client served with Vite (`frontend`).

## Project structure

```
.
├── docker-compose.yml
├── flood_api
│   ├── __init__.py
│   ├── app.py                 # keeps local compatibility by booting the gateway
│   ├── gateway/
│   ├── services/
│   │   ├── classification_service/
│   │   └── forecast_service/
│   ├── shared/
│   └── models/                # shared ML artefacts
└── frontend
    ├── Dockerfile
    └── src/
```

## Quick start with Docker

```bash
docker compose up --build
```

Services are exposed on:

- `http://localhost:5000` (gateway)
- `http://localhost:5001` (classification)
- `http://localhost:5002` (forecast)
- `http://localhost:5173` (frontend)

Model files are mounted from `flood_api/models/`, so make sure the artefacts are present before launching the stack.

## Automatic alert workflow

- Le module de prévision automatique (`PredictAuto`) crée une alerte Firestore pour chaque jour détecté à risque et l’interface citoyenne affiche un résumé synthétique.
- La barre supérieure expose un bandeau d’urgence et une cloche d’alertes pointant vers le centre d’alertes (`/alertes`).
- Le module `PredictAuto` affiche une synthèse des jours critiques (J+2, J+3, …) pour guider la prévention.
- Les composants de détection image (`FloodClassify`, `DetectImage`) alimentent aussi automatiquement le registre d’alertes.
- Le formulaire citoyen `/signaler` recommande la validation IA mais autorise l’envoi manuel pour ne pas bloquer les visiteurs.

## Gestion des rôles

- `guest` : visiteur sans compte. Peut consulter la carte, la liste publique et déposer un signalement simplifié.
- `citizen` : utilisateur connecté (créé automatiquement à la première connexion). Accède à l’historique de ses alertes (`/mes-alertes`).
- `local_admin` : comité local ou municipalité. Dispose du tableau de bord `/admin` et des outils de prédiction détaillés.
- `super_admin` : fédération. Peut gérer les comptes/permissions et superviser l’ensemble des données.

Les rôles sont stockés dans `userRoles/{uid}`. Une entrée est créée automatiquement (citizen) à la première connexion. Les responsables peuvent ensuite promouvoir un compte en ajustant la propriété `role` dans Firestore.

## Manual start (without Docker)

Create a virtual environment and install the shared dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r flood_api/requirements.txt
```

Run each backend service in its own terminal:

```bash
cd flood_api
python -m flood_api.services.classification_service.app
python -m flood_api.services.forecast_service.app
python -m flood_api.gateway.app
```

Launch the frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend reads the service URLs from these environment variables:

- `VITE_API_GATEWAY_URL`
- `VITE_CLASSIFICATION_SERVICE_URL`
- `VITE_FORECAST_SERVICE_URL`

By default they fall back to `http://localhost:5000`, `http://localhost:5001` and `http://localhost:5002` respectively.

## Configuration notes

- Gateway targets can be overridden with `CLASSIFICATION_SERVICE_URL`, `FORECAST_SERVICE_URL`, and optionally `GATEWAY_TIMEOUT`.
- Global constants (image size, probability threshold, supported zones) live in `flood_api/shared/config.py`.

## Next steps

- Add a dedicated satellite detection service to back the `DetectImage` component.
- Apply authentication at the gateway level.
- Wire a CI pipeline to build the Docker images and run automated tests.
