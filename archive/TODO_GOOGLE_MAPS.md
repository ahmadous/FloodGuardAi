# Plan: Intégration Google Maps

## Étape 1: Préparer l'environnement
- [x] 1.1 Ajouter @googlemaps/js-api-loader aux dépendances
- [x] 1.2 Mettre à jour index.html avec l'API Google Maps

## Étape 2: Modifier MapDisplay.vue
- [x] 2.1 Remplacer l'import Leaflet par Google Maps API
- [x] 2.2 Adapter la méthode initMap() pour Google Maps
- [x] 2.3 Adapter createMarker() pour Google Maps
- [x] 2.4 Adapter les couches géographiques (GeoJSON)
- [x] 2.5 Conserver la géolocalisation utilisateur
- [x] 2.6 Adapter le style CSS pour Google Maps

## Étape 3: Tester
- [x] 3.1 Vérifier que le projet compile
- [x] 3.2 Vérifier le fonctionnement de la carte

## Note importante
- La clé API Google Maps dans le code est une clé démo (AIzaSyDemo_Key). 
- Vous devez la remplacer par votre propre clé API Google Maps valide pour que la carte fonctionne en production.
- Pour obtenir une clé: https://console.cloud.google.com/google/maps-apis/

