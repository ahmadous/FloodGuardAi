# Geodata ingestion & integration

Ce projet consomme des couches SIG (shapefiles) provenant de GeoSenegal
pour enrichir la détection/prévision des inondations. Les étapes suivantes
permettent de préparer et d’utiliser ces données.

## 1. Préparation (one-shot)

```bash
pip install -r flood_api/services/forecast_service/requirements.txt
python scripts/prepare_geodata.py --source flood_api/models --dest flood_api/models/geodata
```

Le script :

- convertit chaque répertoire `<region>_shapefile` en un GeoPackage
  `flood_api/models/geodata/<region>.gpkg` (CRS EPSG:4326) ;
- génère `flood_api/models/geodata_manifest.json` listant les couches et
  leurs métadonnées (bounds, nombre de features, etc.).

## 2. API et consommation front

- `GET /geo/regions` : renvoie le manifeste complet.
- `GET /geo/regions/<region>/layers` : détail des couches pour une région.
- `GET /geo/regions/<region>/layers/<layer>` : GeoJSON de la couche.
- `GET /geo/features?lat=<>&lon=<>&region=<>` : indicateurs géospatiaux pour
  un point (distance à l’axe d’écoulement, présence en zone humide…).

Le module `flood_api.shared.geodata` centralise le chargement des GeoPackages
et l’extraction d’indicateurs. Toutes les fonctions dégradent proprement si
``geopandas`` n’est pas disponible.

### Déploiement backend

- Les images Docker `gateway` et `forecast_service` installent GDAL et les
  bibliothèques requises. Assure-toi de reconstruire/pousser les images après
  avoir ajouté de nouvelles couches géo (`docker compose build`).
- `geodata_manifest.json` et les geopackages doivent être copiés dans l’image ;
  c’est déjà le cas avec le `COPY . /app/flood_api` des Dockerfiles.

### Déploiement frontend

- Définis `VITE_API_GATEWAY_URL` (en `.env.local` ou `.env.production`) pour
  pointer vers l’URL publique de l’API Gateway (`https://...`). Sans cela,
  Firebase Hosting ne peut pas accéder aux couches `/geo`.
- Après mise à jour de la variable, rebuild (`npm run build`) puis
  `firebase deploy`.

## 3. Enrichissement des modèles IA

`compute_context_features` renvoie des métriques prêtes à être injectées dans
les pipelines ML (forecast ou classification). Adapter les services Flask pour
ajouter ces features aux requêtes avant d’appeler les modèles.

## 4. Visualisation

Le front peut consommer les endpoints `/geo` et afficher les couches dans
`MapDisplay.vue` (sous forme d’overlays ou de heatmaps) ainsi que dans les
dashboards admin pour les analyses par bassin/zone humide.

## 5. Maintenance

- Mettre à jour les shapefiles → relancer `scripts/prepare_geodata.py --force`.
- Versionner le manifeste et les GeoPackages dans un stockage adapté
  (bucket, artefact) pour éviter d’alourdir Git.
- Documenter dans ce dossier la source, la licence et la date d’acquisition
  des données pour chaque région.
