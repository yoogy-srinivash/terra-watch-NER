# TerraWatch NER - AI/ML Model Evaluation & Scientific Benchmark Report

**Course Context:** Intelligent Model Design using AI (IMDAI)  
**Project Classification:** Academic Multi-Modal AI Research Prototype  
**Concept Inspiration:** North Eastern Region (NER) Landslide Risk Problem Statement  
**Evaluation Date:** October 2026  

---

## 1. Scientific Integrity & Provenance Disclosures

> [!CAUTION]
> **CRITICAL SCIENTIFIC & METHODOLOGICAL DISCLOSURE**
> 1. **Synthetic Training Dataset:** The machine learning models in this repository were trained on a **synthetic dataset of 7,000 samples** parameterized around regional geotechnical ranges for the North Eastern Region of India.
> 2. **Benchmark Metric Scope:** The high benchmark metrics reported below (e.g., 97.00% accuracy, 0.9961 ROC-AUC) reflect model performance **strictly on this synthetic distribution**.
> 3. **No Real-World Ground-Truth Claim:** These metrics **do not establish real-world landslide prediction accuracy**. High performance on synthetic distributions often reflects synthetic regularity rather than field readiness.
> 4. **Prerequisites for Real-World Validation:** Deploying a scientifically defensible operational early warning system requires:
>    - Authoritative geospatial survey layers (ALOS PALSAR / SRTM DEMs, Geological Survey of India lithology, NRSC/ISRO landslide inventory maps);
>    - Continuously calibrated, in-situ geotechnical telemetry (piezometers, borehole inclinometers, volumetric water content sensors);
>    - Verified, domain-labeled landslide photographic repositories with localized geospatial coordinates.
> 5. **Terrain Attribute Classification:** The 32 monitored station profiles are **Category D heuristic baselines** (geographically plausible estimates), not ground-truth GIS measurements.

---

## 2. Algorithm Benchmark Comparison

The repository benchmarks six supervised learning algorithms across 20 input geotechnical, topographic, meteorological, and categorical dimensions (`backend/models/best_model_metadata.json`):

| Algorithm Architecture | Accuracy | Recall (Sensitivity) | Precision | F1-Score | ROC-AUC | Training Time (s) | Architectural Role |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **LightGBM Classifier** | **97.00%** | **98.04%** | **97.40%** | **0.9772** | **0.9961** | **0.22 s** | **Primary Active Model** |
| **XGBoost Classifier** | **96.93%** | **97.82%** | **97.50%** | **0.9766** | **0.9961** | **0.65 s** | **Standby Ensemble / Failover** |
| Random Forest (100 Trees) | 97.29% | 96.80% | 97.78% | 0.9729 | 0.9951 | 1.84 s | Offline Benchmark |
| Gradient Boosting (GBDT) | 96.85% | 96.40% | 97.28% | 0.9684 | 0.9942 | 3.12 s | Offline Benchmark |
| Decision Tree (Cart) | 94.71% | 94.40% | 95.00% | 0.9470 | 0.9471 | 0.08 s | Interpretable Baseline |
| Logistic Regression (L2) | 87.43% | 86.20% | 88.32% | 0.8725 | 0.9421 | 0.15 s | Linear Baseline |

*Note: All metrics above are authentic outputs from the model evaluation pipeline recorded in `backend/models/best_model_metadata.json` and benchmark logs on the 7,000 synthetic sample set. No cross-validation figures or unverified metrics have been fabricated.*

---

## 3. Dual-Model Active/Standby Architecture

To prevent single-point-of-failure in disaster risk assessment, TerraWatch NER deploys a dual-model architecture:

1. **Active Primary Model (`best_landslide_model.joblib`):**
   - **Architecture:** LightGBM Classifier with histogram-based gradient boosting.
   - **Objective:** Maximum sensitivity (recall = 98.04%) with sub-15ms inference latency.
   - **Inference Path:** Invoked on every `/api/risk/predict` and `/api/risk/live` query.

2. **Standby Failover Model (`standby_landslide_model.joblib`):**
   - **Architecture:** XGBoost Classifier with exact greedy tree-splitting.
   - **Objective:** Parallel independent prediction (recall = 97.82%) serving two purposes:
     - **Ensemble Agreement Verification:** The system computes the consensus agreement between LightGBM and XGBoost (`ensemble_agreement_pct`), exposing it transparently to the decision layer.
     - **Hot Failover:** If the LightGBM artifact fails to load, corrupts, or produces a runtime exception, the engine automatically falls back to XGBoost without service interruption.

---

## 4. Input Feature Space (20 Dimensions)

The model ingests 20 features across 4 distinct physical and environmental domains:

### A. Geotechnical & In-Situ Sensor Telemetry
- `soil_moisture_pct`: Volumetric soil moisture content (%) from capacitive sensors.
- `pore_pressure_kpa`: In-situ pore-water pressure from piezometers (kPa).
- `ground_vibration_g`: Dynamic triaxial acceleration from geophones/MEMS accelerometers (g).

### B. Meteorological Telemetry
- `rainfall_24h_mm`: Cumulative precipitation over the preceding 24 hours.
- `rainfall_72h_mm`: Antecedent rainfall accumulation over 72 hours (proxy for slope pre-wetting).
- `rainfall_intensity_mm_h`: Peak hourly precipitation intensity.

### C. Topographical & Geomorphological (DEM Derived)
- `elevation_m`: Absolute altitude above mean sea level.
- `slope_angle_deg`: Slope inclination (degrees).
- `aspect_deg`: Slope azimuth orientation (0-360 degrees).
- `plan_curvature`: Horizontal curvature perpendicular to slope direction.
- `profile_curvature`: Vertical curvature in the direction of maximum slope.
- `soil_depth_m`: Regolith/soil layer thickness to bedrock.
- `ndvi`: Normalized Difference Vegetation Index (-1.0 to +1.0).

### D. Anthropogenic & Geological Proximity
- `distance_to_road_m`: Proximity to toe-cut highway excavations.
- `distance_to_fault_m`: Proximity to tectonic shear zones and fault traces.
- `distance_to_stream_m`: Proximity to toe-eroding mountain streams.
- `state`: Categorical administrative identifier (Assam, Meghalaya, Mizoram, Sikkim, etc.).
- `lithology`: Categorical geological formation (Sandstone, Shale, Phyllite, Gneiss, Alluvium).
- `soil_type`: Soil taxonomy (Sandy Loam, Clayey Loam, Silty Clay, Gravelly Sand).
- `land_use`: Categorical land cover (Dense Forest, Shifting Cultivation, Urban Settlement, Tea Plantation).

---

## 5. TreeSHAP Feature Explainability

In life-safety disaster systems, "black-box" outputs are unacceptable. TerraWatch NER implements **TreeSHAP (SHapley Additive exPlanations)** on tree models:

1. **Local Attributions:** For every inference, TreeSHAP calculates the exact marginal contribution $\phi_i$ of each feature to the log-odds change from the base expected value $E[f(x)]$.
2. **Top Contributing Drivers:** The top 3 positive attributions are extracted, humanized, and returned in the API payload:
   - Example: `rainfall_24h_mm` ($+0.428$), `soil_moisture_pct` ($+0.312$), `slope_angle_deg` ($+0.185$).
3. **Operational Transparency:** Field operators and rescue dispatchers receive clear geotechnical explanations alongside raw risk percentages.

---

## 6. Multi-Modal Fusion Integration (Phases 1–4)

The spatial ML prediction does not operate in isolation; it is integrated into a multi-modal fusion layer:

$$\text{Fused Risk Score} = w_{\text{spatial}} \cdot S_{\text{norm}} + w_{\text{temporal}} \cdot T_{\text{norm}} + w_{\text{visual}} \cdot V_{\text{norm}}$$

- **Operational Weights:** $w_{\text{spatial}} = 0.50$, $w_{\text{temporal}} = 0.35$, $w_{\text{visual}} = 0.15$ (renormalized dynamically if evidence streams are absent).
- **Temporal Dynamics (Phase 2):** Evaluates 1h, 6h, and 24h sliding windows for pore pressure rise rates, moisture acceleration, and vibration shock anomalies.
- **Visual Evidence (Phase 3):** Deterministic image quality, edge density, and soil chroma analysis strictly labeled as `uncalibrated_unvalidated`.
- **Deterministic Safety Overrides:** Trigger immediate tier elevation to `CRITICAL` whenever critical geotechnical boundaries are breached (e.g. pore pressure $\ge 28.0\text{ kPa}$, vibration $\ge 0.5\text{ g}$, or extreme temporal acceleration).

---

## 7. Academic Verification & Testing

The machine learning and fusion pipeline is verified by automated regression test suites:
- `backend/tests/test_phase1_ml.py`: Validates model loading, dual-model failover, and TreeSHAP attribution extraction.
- `backend/tests/test_temporal_service.py`: Validates sliding-window dynamics and threshold triggers.
- `backend/tests/test_cv_service.py`: Validates visual quality gates and uncalibrated confidence disclosures.
- `backend/tests/test_fusion_service.py`: Validates multi-modal mathematical weighting and safety override execution.
