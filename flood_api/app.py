from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import numpy as np
from joblib import load
from PIL import Image
import io
import requests
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
import zipfile
import tempfile
import rasterio
# ---------------------------
app = Flask(__name__)
CORS(app)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# Chargement des modèles RandomForest et scaler
# ---------------------------
rf_model = load("models/modele_inondation_rf.joblib")
scaler = load("models/scaler_inondation.joblib")


# --- Paramètres du classifieur ---
IMG_SIZE = 128
val_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
])

class_names = ['flooded', 'not_flooded']  # adapte selon tes dossiers

model = models.resnet18(weights=None)
model.fc = torch.nn.Linear(model.fc.in_features, 2)
model.load_state_dict(torch.load("models/best_flood_classifier (1).pth", map_location=device))
model = model.to(device)
model.eval()

@app.route("/predict_class", methods=["POST"])
def predict_class():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    try:
        img = Image.open(file.stream).convert("RGB")
        img_t = val_transform(img).unsqueeze(0).to(device)
        with torch.no_grad():
            out = model(img_t)
            prob = torch.softmax(out, dim=1)[0]
            pred = prob.argmax().item()
        return jsonify({
            "prediction": class_names[pred],
            "proba": float(prob[pred])
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
# ---------------------------
# API prédiction tabulaire (RandomForest)
# ---------------------------
@app.route("/predict_meteo", methods=["POST"])
def predict_meteo():
    data = request.get_json()
    if not data or "features" not in data:
        return jsonify({"error": "Features missing"}), 400
    features = np.array(data["features"]).reshape(1, -1)
    features_scaled = scaler.transform(features)
    pred = int(rf_model.predict(features_scaled)[0])
    probas = rf_model.predict_proba(features_scaled)[0]
    return jsonify({
        "prediction": pred,
        "prob_inondation": float(probas[1]),
        "prob_non_inondation": float(probas[0])
    })

# ---------------------------
# API prédiction auto avec Open-Meteo
# ---------------------------
ZONE_COORDS = {
    "keur massar": (14.792139, -17.314924),
    "kaolack": (14.165202, -16.038788),
    "touba": (14.86819, -15.852753),
    "saintlouis": (15.99297, -16.433289),
}
import pandas as pd

@app.route("/predict_meteo_auto", methods=["POST"])
def predict_meteo_auto():
    import pandas as pd
    data = request.get_json()
    if not data or "zone" not in data:
        return jsonify({"error": "Zone manquante"}), 400
    zone = data["zone"].strip().lower()
    if zone not in ZONE_COORDS:
        return jsonify({"error": "Zone inconnue"}), 400
    lat, lon = ZONE_COORDS[zone]

    api_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,precipitation,relative_humidity_2m"
        f"&forecast_days=5&timezone=Africa%2FDakar"
    )
    r = requests.get(api_url)
    if not r.ok:
        return jsonify({"error": "Erreur Open-Meteo"}), 500
    meteo = r.json()["hourly"]
    df = pd.DataFrame({
        "time": meteo["time"],
        "temperature_2m": meteo["temperature_2m"],
        "relative_humidity_2m": meteo["relative_humidity_2m"],
        "precipitation": meteo["precipitation"]
    })
    df["time"] = pd.to_datetime(df["time"])

    results = []
    # Regroupe les 24h de chaque jour pour créer les features
    days = df["time"].dt.date.unique()
    for day in days:
        day_df = df[df["time"].dt.date == day]
        if len(day_df) < 24:
            continue
        features = [
            day_df["precipitation"].sum(),               # precip_3d_hist (remplacé par 1d)
            day_df["precipitation"].sum(),               # precip_5d_hist (remplacé par 1d)
            day_df["relative_humidity_2m"].mean(),       # humidity_3d_hist (remplacé par 1d)
            day_df["relative_humidity_2m"].mean(),       # humidity_5d_hist (remplacé par 1d)
            day_df["temperature_2m"].mean(),             # temp_3d_hist (remplacé par 1d)
            day_df["temperature_2m"].mean(),             # temp_5d_hist (remplacé par 1d)
        ]
        X_scaled = scaler.transform([features])
        pred = int(rf_model.predict(X_scaled)[0])
        proba = rf_model.predict_proba(X_scaled)[0][1]
        results.append({
            "date": str(day),
            "precip_1d_sum": float(features[0]),
            "humidity_1d_mean": float(features[2]),
            "temp_1d_mean": float(features[4]),
            "proba_inondation": float(proba),
            "inondation": bool(pred)
        })

    return jsonify({
        "zone": zone,
        "results": results
    })
@app.route("/predict_meteo_manual", methods=["POST"])
def predict_meteo_manual():
    """
    L'utilisateur envoie :
    {
        "precipitation": 10.5,     # mm
        "humidity": 85.2,          # %
        "temperature": 27.6        # °C
    }
    """
    data = request.get_json()
    # Vérification des champs
    try:
        precip = float(data.get("precipitation"))
        humidity = float(data.get("humidity"))
        temp = float(data.get("temperature"))
    except (TypeError, ValueError):
        return jsonify({"error": "Champs invalides"}), 400

    # Construction des features attendues par le modèle (x2)
    features = [
        precip, precip,      # précipitations (dupliqué)
        humidity, humidity,  # humidité (dupliqué)
        temp, temp           # température (dupliqué)
    ]
    X_scaled = scaler.transform([features])
    pred = int(rf_model.predict(X_scaled)[0])
    proba = rf_model.predict_proba(X_scaled)[0][1]

    return jsonify({
        "prediction": pred,
        "proba_inondation": float(proba),
        "inondation": bool(pred)
    })
@app.route("/predict_meteo_batch", methods=["POST"])
def predict_meteo_batch():
    """
    L'utilisateur envoie une liste de jours :
    {
      "samples": [
        {"precipitation": 10, "humidity": 90, "temperature": 25},
        {"precipitation": 20, "humidity": 80, "temperature": 28}
      ]
    }
    """
    data = request.get_json()
    samples = data.get("samples", [])
    results = []

    for d in samples:
        try:
            precip = float(d.get("precipitation"))
            humidity = float(d.get("humidity"))
            temp = float(d.get("temperature"))
            features = [precip, precip, humidity, humidity, temp, temp]
            X_scaled = scaler.transform([features])
            pred = int(rf_model.predict(X_scaled)[0])
            proba = rf_model.predict_proba(X_scaled)[0][1]
            results.append({
                "precipitation": precip,
                "humidity": humidity,
                "temperature": temp,
                "prediction": pred,
                "proba_inondation": float(proba),
                "inondation": bool(pred)
            })
        except Exception as e:
            results.append({"error": str(e), "input": d})

    return jsonify({"results": results})


# ---------------------------
# Accueil simple
# ---------------------------
@app.route("/", methods=["GET"])
def home():
    return "API Inondation Sénégal - CNN Image & RandomForest Météo"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
