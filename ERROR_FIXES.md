# Corrigé des Erreurs - Guide de Résolution

## ✅ Erreurs Corrigées

### 1. **Google Maps API - Loading Async**
**Erreur**: `Google Maps JavaScript API has been loaded directly without loading=async`
**Solution**: ✅ **Corrigée**
- Modifié `frontend/index.html`
- Ajouté les attributs `async defer` au script Google Maps
- Cela améliore les performances et élimine l'avertissement

### 2. **google.maps.Marker Déprécié**
**Erreur**: `As of February 21st, 2024, google.maps.Marker is deprecated`
**Solution**: ✅ **Partially Corrigée** (compatible backward)
- Créé une méthode wrapper `createMarker()` dans MapDisplay.vue
- Permet un upgrade futur vers `AdvancedMarkerElement` sans refonte majeure
- Code reste opérationnel pour l'instant

---

## ⚠️ Erreurs Nécessitant une Action Backend

### 3. **404 - /geo/regions**
**Erreur**: `Failed to load resource: the server responded with a status of 404`
**Cause**: L'endpoint `/geo/regions` n'est pas accessible
**Solutions à appliquer**:

```bash
# 1. Vérifier que le gateway est démarré
cd /Users/mac/Documents/Innond
docker-compose ps

# 2. Vérifier les logs
docker-compose logs flood_api_gateway

# 3. Vérifier que geodata_manifest.json existe
ls -la flood_api/models/geodata_manifest.json

# 4. Vérifier la configuration des variables d'environnement
cat .env  # ou vérifier docker-compose.yml
```

### 4. **404 - /predict_meteo_auto**
**Erreur**: `Failed to load resource: the server responded with a status of 404`
**Cause**: Le service forecast n'est pas accessible ou n'est pas démarré
**Solutions à appliquer**:

```bash
# 1. Vérifier le statut des services
docker-compose ps
# Doit voir flood_api_gateway et flood_api_forecast_service

# 2. Vérifier que le forecast service répond
curl http://localhost:5002/health

# 3. Vérifier les logs du service forecast
docker-compose logs flood_api_forecast_service
```

### 5. **Manifeste Géospatial Indisponible**
**Erreur**: `Impossible de charger le manifeste géospatial`
**Cause**: Même source que l'erreur 404 `/geo/regions`
**Solution**: Voir section #3 ci-dessus

---

## 🔧 Configuration API à Vérifier

### Variables d'Environnement Frontend
```javascript
// frontend/.env.local (ou fichier équivalent)
VITE_API_GATEWAY_URL=http://localhost:5000
VITE_CLASSIFICATION_SERVICE_URL=http://localhost:5001
VITE_FORECAST_SERVICE_URL=http://localhost:5002
```

### Configuration du Gateway
Vérifier que le gateway route correctement vers les services:
- `/geo/*` → mappé à `geodata` module
- `/predict_meteo_auto` → forward vers forecast service (port 5002)
- `/predict_class` → forward vers classification service (port 5001)

---

## 📊 Problèmes Réseau/Firestore

### 6. **Firebase Firestore - Index Manquant**
**Erreur**: `The query requires an index`
**Action**: 
- Lien Firebase automatiquement fourni dans l'erreur
- Créer l'index composite via la console Firebase
- Utilisateurs affectés: Ceux qui visualisent les alertes

### 7. **Firebase - ERR_INTERNET_DISCONNECTED**
**Cause**: Problème de connectivité réseau (pas une erreur code)
- Vérifier la connexion internet
- Vérifier les CORS sur les endpoints Firebase

### 8. **TypeError: e.formatRelative is not a function**
**Cause**: Fonction de formatage de date manquante dans une dépendance
**Solution**: 
```bash
cd frontend
npm install  # ou yarn install
npm update date-fns  # si utilisé
```

---

## 🚀 Étapes de Débogage Complètes

1. **Vérifier docker-compose**:
```bash
cd /Users/mac/Documents/Innond
docker-compose up -d  # Démarrer les services
sleep 5             # Laisser temps de démarrage
docker-compose ps   # Vérifier statut
```

2. **Tester chaque endpoint**:
```bash
# Gateway
curl -X GET http://localhost:5000/health

# Geo regions
curl -X GET http://localhost:5000/geo/regions

# Forecast
curl -X POST http://localhost:5000/predict_meteo_auto \
  -H "Content-Type: application/json" \
  -d '{"zone":"dakar_keur_massar"}'
```

3. **Vérifier fichiers critique**:
```bash
ls -la flood_api/models/geodata_manifest.json
ls -la flood_api/models/geodata/
```

4. **Redémarrer le frontend** après fixes:
```bash
cd frontend
npm run dev
```

---

## 📝 Modifications Effectuées

- ✅ `frontend/index.html` - Ajout `async defer` au script Google Maps
- ✅ `frontend/src/components/MapDisplay.vue` - Ajout wrapper `createMarker()`
- ✅ `frontend/src/components/PredictAuto.vue` - Amélioration gestion erreurs 404

## ⏭️ Prochaines Étapes

1. Lancer `docker-compose up -d`
2. Vérifier les endpoints comme décrit ci-dessus
3. Si `/geo/regions` retourne 200 OK, rafraîchir le navigateur
4. Si `/predict_meteo_auto` retourne 200 OK, tester prédictions

Besoin d'aide? Vérifiez les logs: `docker-compose logs -f`
