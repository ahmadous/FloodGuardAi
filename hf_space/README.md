---
title: Saytu Mbeund Classification
emoji: 🌊
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# Saytu Mbeund — Classification Service

API de détection d'inondation par image (ConvNeXt-Tiny).

## Endpoint

```
POST /predict_class
Content-Type: multipart/form-data
Body: file=<image>
```

## Réponse

```json
{
  "prediction": "flooded",
  "proba": 0.92,
  "probabilities": {
    "flooded": 0.92,
    "not_flooded": 0.08
  }
}
```
