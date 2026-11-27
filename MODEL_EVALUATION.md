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

The repository benchmarks six supervised learning algorithms across 20 input geotechnical, topographic, meteorological, and categorical dimensions (`backend/models/benchmark_results.csv` and `backend/models/best_model_metadata.json`):

| Algorithm Architecture | Accuracy | Recall (Sensitivity) | Precision | F1-Score | ROC-AUC | Composite Disaster Score | Training Time (s) | Architectural Role |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **LightGBM Classifier** | **97.00%** | **98.04%** | **97.40%** | **0.9772** | **0.9961** | **0.9871** | **0.22 s** | **Primary Active Model** |
| Gradient Boosting (GBDT) | 96.93% | 98.26% | 97.09% | 0.9767 | 0.9936 | 0.9867 | 7.15 s | Offline Benchmark |
| **XGBoost Classifier** | **96.93%** | **97.82%** | **97.50%** | **0.9766** | **0.9961** | **0.9862** | **0.65 s** | **Standby Ensemble / Failover** |
| Logistic Regression (L2) | 96.86% | 97.82% | 97.39% | 0.9761 | 0.9955 | 0.9859 | 0.07 s | Linear Baseline |
| Random Forest (150 Trees) | 95.00% | 95.20% | 97.11% | 0.9615 | 0.9918 | 0.9724 | 0.45 s | Offline Benchmark |
| Decision Tree (CART) | 93.00% | 95.86% | 93.61% | 0.9472 | 0.9624 | 0.9593 | 0.09 s | Interpretable Baseline |

**Model Selection Criterion:**  
Models are ranked by a weighted **Composite Disaster Score** prioritizing missed-disaster avoidance (Recall) and ranking quality (ROC-AUC / PR-AUC):
$$\text{Composite Disaster Score} = 0.35 \cdot \text{Recall} + 0.30 \cdot \text{ROC-AUC} + 0.20 \cdot \text{F1} + 0.15 \cdot \text{PR-AUC}$$

*Note: All metrics above are authentic outputs from `ml_pipeline/training/train_models.py` recorded in `backend/models/benchmark_results.csv` on the 7,000-sample synthetic dataset (80/20 stratified split).*

---

## 2.1. Synthetic Dataset Generation Specification

The 7,000-sample training dataset (`backend/data/ner_landslide_dataset.csv`) is generated programmatically in `ml_pipeline/training/train_models.py`:

- **Regional Sampling:** Draws uniformly from 18 NER district profiles across all 8 states, each with `base_elev`, `tectonic` multiplier (`1.0–1.7`), and `monsoon` multiplier (`1.1–2.2`).
- **Terrain & Proximity:** Slope angles follow $\text{Beta}(2.2, 3.2) \times 52 + 8$; road, fault, and stream distances follow exponential distributions; aspect is uniform $[0, 360)^\circ$.
- **Monsoon (35%) vs. Non-Monsoon (65%) Regimes:**
  - *Monsoon:* 24h rainfall $\sim \text{Gamma}(3.2, 32.0) \times m_{\text{factor}}$; soil moisture clipped to $[45, 98]\%$; pore pressure derived from soil moisture excess and clipped to $[2, 42]\text{ kPa}$.
  - *Non-Monsoon:* 24h rainfall $\sim \text{Exp}(12.0) \times 0.4 m_{\text{factor}}$; soil moisture $\sim \mathcal{N}(32, 10)$ clipped to $[10, 58]\%$; pore pressure clipped to $[0.5, 12]\text{ kPa}$.
- **Physics-Inspired Instability & Labeling:**
  - Driving force combines $\sin(\text{slope})$, pore pressure, road-cut factor ($1.45$ if `distance_to_road_m < 40`), and $\sqrt{\text{tectonic}}$.
  - Resisting force combines $\cos(\text{slope}) \tan(28^\circ)$, vegetation NDVI, and categorical vulnerability factors for lithology, soil type, and land use.
  - Instability index $I = 0.38 \cdot (\text{driving} / (\text{resisting} + 0.05)) + 0.62 \cdot \text{rain\_trig}$ is mapped via $\sigma(4.2(I - 1.0)) + \mathcal{N}(0, 0.02)$ and labeled `1` when $\text{prob} \ge 0.50$.

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

### C. Topographical & Geomorphological (Estimated Baselines for 32 Stations)
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
- **Deterministic Safety Overrides:** Trigger immediate tier elevation to `CRITICAL` (with an `0.80` / `80%` minimum score floor) whenever critical geotechnical boundaries are breached (e.g. pore pressure $\ge 25.0\text{ kPa}$, vibration $\ge 1.5\text{ g}$ or $\ge 4.0\times$ baseline, temporal score $\ge 85.0$, spatial probability $\ge 0.85$, or high localized debris).
- **Advisory Temporal Forecasting (TFT):** For multi-horizon soil moisture and pore-pressure forecasting (`1h`, `6h`, `24h`), see [TEMPORAL_FORECASTING.md](TEMPORAL_FORECASTING.md).

---

## 7. Academic Verification & Testing

The machine learning, forecasting, and fusion pipelines are verified by automated regression test suites (`71` total tests across `7` files):
- `backend/tests/test_phase1_ml.py`: Validates model loading, dual-model failover, and TreeSHAP attribution extraction.
- `backend/tests/test_temporal_service.py`: Validates sliding-window dynamics and threshold triggers.
- `backend/tests/test_cv_service.py`: Validates visual quality gates and uncalibrated confidence disclosures.
- `backend/tests/test_fusion_service.py`: Validates multi-modal mathematical weighting and safety override execution.
- `backend/tests/test_tft_forecasting.py`: Validates TFT sequence preparation, multi-horizon forecasts, checkpoint loading, and fusion isolation.
