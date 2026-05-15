# Documentation UML - Système de Détection d'Inondations au Sénégal

Cette documentation contient l'ensemble des diagrammes UML du système de détection et prédiction des inondations.

## Table des matières

1. [Diagramme de Classes](#diagramme-de-classes)
2. [Diagramme de Cas d'Utilisation](#diagramme-de-cas-dutilisation)
3. [Diagrammes de Séquence](#diagrammes-de-séquence)
4. [Comment visualiser les diagrammes](#comment-visualiser-les-diagrammes)

---

## Diagramme de Classes

**Fichier:** `class_diagram.puml`

Ce diagramme présente l'architecture complète du système avec :

### Packages principaux

- **Backend Services**
  - `APIGateway` : Point d'entrée unique (pattern Gateway)
  - `GeoBlueprint` : Gestion des endpoints géographiques
  - `ClassificationService` : Service de classification d'images (ResNet18)

- **Shared Layer**
  - `ModelRegistry` : Chargement centralisé des modèles ML (pattern Singleton avec LRU cache)
  - `GeoDataService` : Gestion des données géospatiales (shapefiles, geopackages)
  - `Config` : Configuration globale

- **Machine Learning Models**
  - `ImageClassifier` : ResNet18 pré-entraîné
  - `Scaler` : Normalisation des features

- **Frontend (Vue.js)**
  - `User` : Entité utilisateur avec rôles (citizen, local_admin, super_admin)
  - `Alert` : Entité alerte avec statuts (pending, verified, resolved, rejected)
  - `APIClient` : Client HTTP pour communication avec l'API Gateway
  - `AuthService` : Gestion authentification Firebase

### Relations clés

- L'API Gateway proxie vers les microservices
- Les services utilisent ModelRegistry pour charger les modèles
- Le frontend communique uniquement avec l'API Gateway

---

## Diagramme de Cas d'Utilisation

**Fichier:** `usecase_diagram.puml`

Ce diagramme identifie les acteurs et leurs interactions avec le système.

### Acteurs

1. **Citoyen**
   - Créer/consulter alertes
   - Classifier images
   - Prédictions manuelles/automatiques
   - Consulter carte et consignes

2. **Maire/Admin Local**
   - Gérer alertes de sa zone
   - Valider/rejeter alertes
   - Dashboard local
   - Notifier citoyens

3. **Super Admin**
   - Gérer tous les utilisateurs
   - Attribuer rôles et zones
   - Superviser toutes les alertes
   - Prédictions batch
   - Rapports nationaux

4. **Système Météo (Open-Meteo)**
   - Fournir données temps réel
   - Prévisions 5 jours

### Cas d'utilisation principaux

- **Gestion des Alertes** : Signalement et suivi par citoyens
- **Détection par Image** : Classification automatique des inondations
- **Gestion des Alertes** : signalement, validation, traitement et suivi local
- **Cartographie** : Visualisation zones à risque
- **Administration** : Gestion locale et nationale

---

## Diagrammes de Séquence

### 1. Citoyen crée une alerte (`sequence_01_citizen_alert.puml`)

**Scénario :** Un citoyen signale une inondation avec photo

**Flux principal :**
1. Authentification Firebase
2. Upload et classification de l'image (ResNet18)
3. Enrichissement avec géolocalisation (distance cours d'eau, zone inondable)
4. Sauvegarde dans Firestore avec statut "pending"

**Acteurs :** Citoyen, Frontend, Firebase, API Gateway, Classification Service, Model Registry

**Points clés :**
- Classification automatique pour triage initial
- Contexte géographique enrichi automatiquement
- Alerte créée avec statut "pending" pour validation maire

---

### 2. Prédiction automatique météo (`sequence_02_prediction_auto.puml`)

**Scénario :** Prédiction automatique des inondations pour une zone (ex: Dakar)

**Flux principal :**
1. Sélection d'une zone prédéfinie
2. Récupération données Open-Meteo (5 jours × 24h)
3. Calcul du contexte géographique (distance cours d'eau, zones inondables)
4. Agrégation des features jour par jour avec historique (rolling 3j, 7j, 15j)
5. Prédiction via Random Forest pour chaque jour
6. Affichage graphique des résultats (Chart.js)

**Acteurs :** Utilisateur, Frontend, API Gateway, Forecast Service, Open-Meteo API, GeoData Service

**Features calculées :**
- Précipitations (1j, 3j, 7j, 15j)
- Humidité (moyenne, max)
- Température (moyenne, max)
- Contexte géographique

**Seuil de décision :** 0.35 (si proba ≥ 0.35 → Inondation)

---

### 3. Maire valide une alerte (`sequence_03_mayor_validation.puml`)

**Scénario :** Un maire consulte et valide une alerte de sa zone

**Flux principal :**
1. Authentification et vérification du rôle (local_admin)
2. Consultation des alertes filtrées par zone (ex: Dakar uniquement)
3. Visualisation détail avec carte interactive
4. Validation avec ajout de sévérité et commentaire
5. Notification automatique du citoyen
6. Mise à jour des statistiques dashboard

**Acteurs :** Maire, Frontend, Firebase Auth/Firestore, API Gateway

**Points clés :**
- Filtrage automatique par zone du maire
- Actions possibles : valider, rejeter, demander infos, marquer résolu
- Notification temps réel du citoyen
- Mise à jour statistiques en temps réel

---

### 4. Prédiction par lot - Batch (`sequence_04_batch_prediction.puml`)

**Scénario :** Super Admin lance une prédiction batch pour analyse de scénarios

**Flux principal :**
1. Chargement fichier CSV ou saisie manuelle (50+ scénarios)
2. Envoi requête batch avec tous les échantillons
3. Traitement en boucle avec gestion des erreurs par sample
4. Pour chaque échantillon :
   - Validation des données
   - Construction du vecteur de features
   - Prédiction via Random Forest
   - Calcul du contexte géographique
5. Génération de statistiques et visualisations
6. Export des résultats (CSV/Excel)

**Acteurs :** Super Admin, Frontend, API Gateway, Forecast Service

**Cas d'usage :**
- Tests de scénarios what-if
- Analyse de sensibilité
- Planification urbanisme
- Études d'impact
- Rapports gouvernementaux

**Traitement robuste :**
- Continue si erreur sur un échantillon
- Retourne résultats + erreurs séparément
- Ne bloque pas tout le batch

---

### 5. Prédiction manuelle (`sequence_05_manual_prediction.puml`)

**Scénario :** Un citoyen saisit manuellement des données météo pour prédiction

**Flux principal :**
1. Saisie des données de base (précipitations, humidité, température)
2. [Optionnel] Saisie des données avancées (max, cumuls 3j/7j/15j)
3. Sélection de la localisation (GPS ou manuelle)
4. Validation et construction du vecteur de features
5. Enrichissement avec contexte géographique
6. Prédiction via Random Forest
7. Affichage résultat avec jauge de risque et recommandations
8. [Optionnel] Créer alerte ou voir carte

**Acteurs :** Citoyen, Frontend, API Gateway, Forecast Service, GeoData Service

**Points clés :**
- Valeurs par défaut intelligentes (max = mean si non fourni)
- Permet usage simplifié (3 champs obligatoires)
- Résultat enrichi avec recommandations contextuelles
- Possibilité de créer alerte directement

---

## Comment visualiser les diagrammes

### Option 1 : VS Code (Recommandé)

1. Installer l'extension **PlantUML** dans VS Code
2. Installer Java (requis pour PlantUML)
3. Ouvrir un fichier `.puml`
4. Clic droit → `Preview Current Diagram`

### Option 2 : PlantUML Online

1. Aller sur https://www.plantuml.com/plantuml/uml/
2. Copier/coller le contenu d'un fichier `.puml`
3. Visualiser le diagramme généré

### Option 3 : Ligne de commande

```bash
# Installer plantuml
brew install plantuml  # macOS
# ou
apt-get install plantuml  # Linux

# Générer les images
plantuml docs/uml/*.puml

# Génère des fichiers PNG dans le même dossier
```

### Option 4 : PlantUML Server (Docker)

```bash
docker run -d -p 8080:8080 plantuml/plantuml-server:jetty
# Accéder à http://localhost:8080
```

---

## Zones géographiques couvertes

- **Dakar** (Keur Massar) : lat=15.43058, lon=-15.887329
- **Kaolack** (Leona) : lat=13.813708, lon=-15.551483
- **Kolda** : lat=12.899824, lon=-14.959137
- **Tambacounda** : lat=13.743409, lon=-13.636383
- **Touba** : lat=14.86819, lon=-15.852753

Chaque région dispose de couches géospatiales :
- `Axe_ecoulement_temporaire` : Cours d'eau temporaires
- `Zone_inondable_humide` : Zones inondables identifiées

---

## Technologies utilisées

### Backend
- **Python 3.x** : Langage principal
- **Flask** : Framework web
- **PyTorch** : Classification d'images (ResNet18)
- **scikit-learn** : Prédiction météo (Random Forest)
- **geopandas** : Traitement géospatial
- **joblib** : Sérialisation des modèles
- **Open-Meteo API** : Données météo temps réel

### Frontend
- **Vue.js 3** : Framework SPA
- **Vue Router** : Routing avec guards
- **Vite** : Build tool
- **Leaflet** : Cartographie interactive
- **Chart.js** : Visualisations
- **Firebase** : Auth + Firestore

### Infrastructure
- **Docker** : Containerisation
- **Docker Compose** : Orchestration des microservices

---

## Architecture microservices

```
Frontend (5173) → API Gateway (5000) → Classification Service (5001)
                                      → Forecast Service (5002)
                                      → GeoData Service (embedded)
```

**Pattern architectural :** API Gateway + Microservices + Shared Kernel

---

## Modèles Machine Learning

### 1. Classification d'images
- **Modèle :** ResNet18 pré-entraîné et fine-tuné
- **Classes :** flooded, not_flooded
- **Fichier :** `best_flood_classifier (1).pth`
- **Input :** Image RGB 128×128
- **Output :** Probabilités [flooded, not_flooded]

### 2. Prédiction météorologique
- **Modèle :** Random Forest
- **Type :** Classification binaire (inondation/pas d'inondation)
- **Fichiers :**
  - `random_forest_predict_model.pkl` : Modèle
  - `scaler_predict.pkl` : StandardScaler
  - `flood_predict_metadata.json` : Métadonnées
- **Features :** 9 variables météorologiques
- **Seuil optimal :** 0.35 (calibré)

---

## Rôles utilisateurs

| Rôle | Description | Permissions |
|------|-------------|-------------|
| **guest** | Visiteur non connecté | Consulter alertes publiques, carte |
| **citizen** | Citoyen inscrit | Créer/suivre ses alertes, prédictions |
| **local_admin** | Maire/Admin local | Gérer alertes de sa zone, dashboard local |
| **super_admin** | Administrateur national | Accès total, gestion utilisateurs, batch |

---

## Contact et contribution

Ce système est développé pour la prévention des inondations au Sénégal.

Pour toute question sur l'architecture ou les diagrammes, consultez ce README.

---

**Date de création :** 2025-10-13
**Version :** 1.0
