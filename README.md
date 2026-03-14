# FloodGuardAI 🌊🤖
## AI-Powered Early Flood Detection and Prediction System for Senegal

**Live platform:** https://sengaal-b4ab0.web.app/
**Demo video:** https://youtu.be/ml16aAvDvzs

## Results
- Random Forest: AUC-ROC = 1.000 | Recall = 100% 
  Zero missed flood events on 2,202 test observations
- ConvNeXt-Tiny: F1-Score = 96.48% | Zero false alerts
  Validated on 113 images
- Coverage: 6 zones across Senegal (2005–2025)

## System Architecture
FloodGuardAI operates as a two-component AI pipeline:

**Component 1 — Meteorological Prediction (Random Forest)**
- 20 years of climate data (2005–2025)
- 6 representative zones of Senegal
- Multi-day cumulative precipitation features
- Strict temporal cross-validation (TimeSeriesSplit, 5 folds)

**Component 2 — Visual Detection (ConvNeXt-Tiny)**
- Citizen-submitted smartphone images
- Transfer learning (3 progressive phases)
- Grad-CAM explainability
- Zero false alerts

**Component 3 — Collaborative Platform**
- Geolocated citizen reporting
- Real-time authority dashboards
- Interactive flood risk maps

## Academic Validation
Master's thesis defended February 16, 2026
Université Iba Der Thiam de Thiès (UIDT) /
Université de Technologie de Troyes (UTT)
Supervised by Pr. Ibrahima Gueye — EPT

## Author
Papa Ahmadou Seydou SOW
paseydou.sow@univ-thies.sn
Yaatal Digital — Senegal

## International Recognition
- WSIS Prizes 2026 — AL C7 E-environment
  Project ID: 17734472422205614
- AI for Good Impact Awards 2026 — AI for Planet
- Partner2Connect Digital Coalition — ITU

## Note
The full source code is available upon request
for verified research and institutional partnerships.
Contact: paseydou.sow@univ-thies.sn
