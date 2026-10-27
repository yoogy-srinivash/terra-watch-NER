# TerraWatch NER - Academic Demonstration & Verification Guide

**Course Context:** Intelligent Model Design using AI (IMDAI)  
**Target Audience:** Course Evaluators, Academic Reviewers, and Testers  
**Prototype Role:** Academic Multi-Modal AI Research Prototype  

---

## 1. Quickstart & Environment Setup

### Prerequisites
- Python 3.12+ (Virtual environment in `./venv`)
- SQLite3 (Included in standard library)

### Step 1: Configure Environment Secret
Copy `.env.example` to `.env` (or verify that `.env` exists):
```bash
cp .env.example .env
```
Ensure `SECRET_KEY` is configured (a key is already pre-configured for local testing in `.env`).

### Step 2: Start the FastAPI Backend Server
```powershell
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The server will start at `http://127.0.0.1:8000`.  
- Web Dashboard: `http://127.0.0.1:8000/ui/index.html`
- Interactive Probability & Fusion: `http://127.0.0.1:8000/ui/probability-risk.html`
- GIS Live Risk Map: `http://127.0.0.1:8000/ui/live-risk-map.html`
- Model Evaluation Architecture: `http://127.0.0.1:8000/ui/model-information.html`
- Interactive API Documentation: `http://127.0.0.1:8000/docs`

---

## 2. Reproducible IoT Telemetry Demonstration Scenarios

The sensor simulator (`sensor_simulator/sensor_simulator.py`) generates deterministic, reproducible telemetry trajectories. All readings are explicitly tagged with `is_simulated: True` and Category C demonstration provenance notices.

### Scenario 1: Normal Baseline Telemetry
Demonstrates stable geotechnical equilibrium across all 8 NER states:
```powershell
.\venv\Scripts\python.exe sensor_simulator/sensor_simulator.py --scenario normal --iterations 2
```
*Expected Behavior:* Soil moisture stays ~35-40%, pore pressure < 6 kPa, vibration < 0.05 m/s². The risk level remains `LOW` or `MODERATE`.

### Scenario 2: Heavy Rainfall Precursor Event
Demonstrates IMD rainfall accumulation in temporal sliding windows:
```powershell
.\venv\Scripts\python.exe sensor_simulator/sensor_simulator.py --scenario rainfall --station SN-ML-001 --iterations 3
```
*Expected Behavior:* Station `SN-ML-001` (Shillong Ridge Node) records rainfall accumulation exceeding 64.5 mm/24h. Temporal trend elevates to `RISING`.

### Scenario 3: Soil Moisture Saturation Surge
Demonstrates rapid volumetric water infiltration:
```powershell
.\venv\Scripts\python.exe sensor_simulator/sensor_simulator.py --scenario moisture --station SN-ML-001 --iterations 3
```
*Expected Behavior:* Soil moisture rapidly increases past 48% with a positive rate of change (> 5%/hour), triggering temporal risk score escalation.

### Scenario 4: Pore-Water Pressure Escalation
Demonstrates in-situ piezometer pressure buildup behind a failure plane:
```powershell
.\venv\Scripts\python.exe sensor_simulator/sensor_simulator.py --scenario pore_pressure --station SN-ML-001 --iterations 3
```
*Expected Behavior:* Pore pressure rises above 29.5 kPa.

### Scenario 5: Dynamic Vibration Shock Anomaly
Demonstrates micro-seismic slope movement or heavy machinery disturbance:
```powershell
.\venv\Scripts\python.exe sensor_simulator/sensor_simulator.py --scenario vibration --station SN-ML-001 --iterations 3
```
*Expected Behavior:* Ground vibration spikes to 3.8x baseline, triggering the vibration anomaly detector.

### Scenario 6: Progressive Compound Deterioration
Demonstrates progressive slope instability across multiple telemetry cycles:
```powershell
.\venv\Scripts\python.exe sensor_simulator/sensor_simulator.py --scenario deterioration --station SN-ML-001 --iterations 4
```
*Expected Behavior:* Compound multi-sensor degradation: simultaneous rainfall, moisture surge, pressure buildup, and vibration increase.

### Scenario 7: Life-Safety Override Trigger
Demonstrates the multi-modal safety override mechanism:
```powershell
.\venv\Scripts\python.exe sensor_simulator/sensor_simulator.py --scenario override --station SN-ML-001 --iterations 2
```
*Expected Behavior:* Extreme values (pore pressure = 42.0 kPa, vibration = 0.85 m/s²) immediately trip `CRITICAL_PORE_PRESSURE_OVERRIDE` in `fusion_service.py`, forcing the fused risk tier to `CRITICAL` regardless of other streams.

---

## 3. Verifying Key Academic AI Capabilities

### 3.1. TreeSHAP Explainability Attribution
Navigate to `http://127.0.0.1:8000/ui/probability-risk.html` or run:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/risk/live?location=Shillong" -Method GET
```
Inspect `prediction.contributing_factors` and `fusion.components.spatial.top_shap_factors`.  
You will observe exact marginal feature contributions (e.g. `rainfall_24h_mm: +0.428`, `soil_moisture_pct: +0.312`).

### 3.2. Dual-Model Consensus & Failover
Inspect `fusion.components.spatial`:
- `active_model`: LightGBM Classifier
- `standby_model`: XGBoost Classifier
- `ensemble_agreement_pct`: Shows consensus percentage between both models.

### 3.3. Multi-Modal Risk Fusion Panel
On `http://127.0.0.1:8000/ui/probability-risk.html`:
- Observe the **Multi-Modal Risk Fusion Decision Engine** card.
- Displays Stream 1 (Spatial ML + SHAP), Stream 2 (Temporal Dynamics), and Stream 3 (Visual Evidence).
- Shows dynamic operational weights (`w = 0.50`, `w = 0.35`, `w = 0.15`) and data sufficiency.

---

## 4. Verifying Security & Integrity Hardening

### 4.1. Unauthenticated Settings Mutation Rejection
Attempt to mutate system thresholds without admin authentication:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/admin/settings" -Method POST -ContentType "application/json" -Body '{"soil_moisture_critical_pct": 99.0}'
```
*Expected Result:* **HTTP 401 Unauthorized** (or 403 Forbidden for non-admin accounts). Mutation is strictly rejected.

### 4.2. Upload File Size Restriction
Attempt to upload a payload exceeding 25 MB to `/api/reports`:
*Expected Result:* **HTTP 413 Payload Too Large** (enforced by upload size gatekeeper).

### 4.3. Absence of Hardcoded JWT Secret Fallback
Verify that removing `SECRET_KEY` causes a clear, immediate validation error rather than silently defaulting to a known string:
```powershell
.\venv\Scripts\python.exe -c "from backend.app.config import Settings; Settings(_env_file=None)"
```
*Expected Result:* `pydantic_core._pydantic_core.ValidationError: SECRET_KEY Field required`.

---

## 5. Automated Test Suite Execution

Run the complete automated pytest suite:
```powershell
.\venv\Scripts\python.exe -m pytest backend/tests/ -v
```
All tests across Phases 1, 2, 3, 4, 5, and the core API pass synchronously.
