# Modélisation du risque d'inondation

Ce guide décrit la nouvelle chaîne de traitement mise en place pour exploiter les séries météo horaires disponibles dans `flood_api/donnees` et entraîner un classifieur compatible avec le service `forecast_service`.

## Structure des données

- 6 fichiers CSV horaires couvrant la période 2005-2025 pour différentes localités (Keur Massar, Kaolack Léona, Kolda, Matam, Tambacounda, Touba).
- Chaque fichier contient deux lignes de métadonnées (latitude, longitude, altitude…) suivies du tableau horaire.
- Variables clés utilisées par le modèle : `precipitation_mm`, `relative_humidity_2m_pct`, `temperature_2m_degc`.

## Prétraitement & EDA

Le script `flood_api/modeling/train_flood_model.py` :

1. Normalise les en-têtes de colonnes (ASCII only) et concatène tous les jeux de données.
2. Agrège les observations par jour et par localisation (`sum`, `max`, `mean` selon la variable) en se limitant automatiquement aux mois de la saison des pluies (juin-octobre).
3. Produit un aperçu EDA :
   - Intervalle temporel train/test.
   - Distribution de la cible proxy.
   - Statistiques descriptives de la pluie journalière (médiane, quantiles 90/95/99).
4. Conserve six features finales alignées avec les API d'inférence :
   - `precipitation_mm_sum`
   - `precipitation_mm_max`
   - `relative_humidity_2m_pct_mean`
   - `relative_humidity_2m_pct_max`
   - `temperature_2m_degc_mean`
   - `temperature_2m_degc_max`

## Cible proxy « inondation »

- Découpage temporel par défaut : train avant le 1er janvier 2023, test ensuite.
- Seuils calculés sur l'échantillon d'entraînement (configurables via `--daily-quantile` et `--three-day-quantile`).
- Étiquette positive lorsque `precipitation_mm_sum` dépasse le quantile quotidien choisi **ou** que la somme glissante sur 3 jours dépasse le quantile correspondant.
- Les seuils retenus sont exportés dans `flood_api/models/flood_model_metadata.json`.

## Entraînement

Le pipeline :

1. Met à l'échelle les features avec `StandardScaler`.
2. Entraîne un `RandomForestClassifier` (`n_estimators=400`, `max_depth=10`, `class_weight="balanced_subsample"`).
3. Évalue les performances (ROC-AUC, Average Precision, précision/rappel/F1) sur l'échantillon test.
4. Sauvegarde :
   - `flood_api/models/random_forest_model.pkl`
   - `flood_api/models/scaler.pkl`
   - `flood_api/models/flood_model_metadata.json` (métadonnées, seuils, supports de classes).

⚠️ Le service `forecast_service` suppose que ces artefacts ont été générés avec ce pipeline. Après un `git pull`, relancez l'entraînement pour régénérer les fichiers avant de redémarrer l'API.

## Utilisation

```bash
# Depuis la racine du dépôt
python -m flood_api.modeling.train_flood_model \
    --data-dir flood_api/donnees \
    --models-dir flood_api/models \
    --split-date 2023-01-01 \
    --daily-quantile 0.97 \
    --three-day-quantile 0.95
```

Options disponibles :
- `--split-date`: ajuster le découpage temporel.
- `--daily-quantile` & `--three-day-quantile`: ajuster la sensibilité de la cible.

Le script affiche l'EDA et les métriques de test, puis indique où les artefacts ont été sauvegardés.

## Prochaines pistes

1. **Affiner la cible** avec des observations d'inondations (sondages terrain, bases de données nationales) afin de calibrer les seuils automatiques.
2. **Intégrer des features contextuelles** (indices de sol, distance aux zones inondables) via `flood_api/shared/geodata.py`.
3. **Tester des modèles séquentiels** (LSTM/Temporal Fusion Transformer) en fournissant au pipeline des séquences horaires plutôt que des agrégats quotidiens.
4. **Élaborer une validation croisée temporelle** pour mesurer la robustesse inter-années.
