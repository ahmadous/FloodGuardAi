# GESIN — Application Mobile Flutter

**GESIN** = Gestion des Inondations au Sénégal  
Application mobile Flutter pour la détection et prédiction des inondations, intégrée à l'API INNOND.

---

## 🗂️ Structure du projet

```
gesin/
├── lib/
│   ├── main.dart                        # Entrée principale
│   ├── core/
│   │   ├── constants/app_constants.dart # Constantes (URL API, régions...)
│   │   ├── theme/
│   │   │   ├── app_colors.dart          # Palette de couleurs premium
│   │   │   └── app_theme.dart           # Thème Material 3 sombre
│   │   ├── router/app_router.dart       # Navigation GoRouter + Shell
│   │   └── providers/navigation_provider.dart
│   └── features/
│       ├── splash/          # Écran de démarrage animé
│       ├── onboarding/      # 4 slides d'introduction
│       ├── dashboard/       # Tableau de bord principal
│       ├── map/             # Carte interactive (Flutter Map + OSM)
│       ├── alerts/          # Centre d'alertes avec filtres
│       ├── forecast/        # Prévisions météo + graphiques
│       ├── profile/         # Profil utilisateur & statut API
│       └── settings/        # Paramètres complets
└── assets/
    ├── images/, icons/, animations/, fonts/
```

---

## 📱 Fonctionnalités

| Écran | Fonctionnalités |
|-------|----------------|
| **Splash** | Animation logo avec scale + fade, navigation auto vers onboarding ou home |
| **Onboarding** | 4 slides swipables, indicateurs animés, bouton gradient |
| **Dashboard** | Risque en % + jauge circulaire, statistiques, actions rapides, alertes récentes, régions |
| **Carte** | OpenStreetMap, cercles de zones à risque colorés, markers cliquables, légende, zoom |
| **Alertes** | 7 alertes + filtres niveau, badges "NOUVEAU", actions rapides |
| **Prévisions** | Sélecteur région, graphe barres 7j (fl_chart), météo détaillée, prédiction manuelle IA |
| **Profil** | Avatar, stats, préférences, statut services API |
| **Paramètres** | Notifications, synchronisation, affichage, à propos |

---

## 📦 Stack technique

- **Flutter** 3.35.7 / Dart 3.9.2
- **Navigation** : GoRouter 14 + ShellRoute (bottom nav)
- **State** : Riverpod 2
- **Maps** : flutter_map + latlong2 (OpenStreetMap)
- **Charts** : fl_chart
- **UI** : Google Fonts (Outfit), shimmer, flutter_animate
- **Storage** : shared_preferences, flutter_secure_storage
- **API** : Dio + Retrofit → `https://innond-api.onrender.com`

---

## 🎨 Design System

- **Thème** : Sombre (dark mode), Material 3
- **Couleurs** : Bleu océan `#0A4FD6` + Cyan `#00D4FF`
- **Alertes** : Rouge critique / Orange élevé / Jaune modéré / Vert faible
- **Police** : Outfit (400→700)
- **Cards** : Glassmorphism avec borders lumineux

---

## 🚀 Lancer l'application

```bash
cd /Users/mac/Documents/Innond/gesin

# Avec un émulateur/device connecté
flutter run

# Build Android
flutter build apk --debug

# Build iOS
flutter build ios --debug
```

---

## 🔗 API INNOND intégrée

| Endpoint | Usage |
|----------|-------|
| `POST /predict_class` | Classification image inondation |
| `POST /predict_meteo` | Prévision météo auto |
| `POST /predict_meteo_manual` | Prédiction avec données manuelles |
| `GET /health` | Statut des services |
| `/geo/*` | Données géospatiales |

