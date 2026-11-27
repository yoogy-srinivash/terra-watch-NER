# Temporal Fusion Transformer (TFT) — Multi-Horizon Subsurface Forecasting

## 1. Overview & Architectural Role

TerraWatch NER employs a dual-modality AI architecture that strictly decouples **Spatial Landslide Susceptibility** from **Temporal Subsurface Forecasting**:

```
+--------------------------------------------------------------------------------------------------+
|                                    TERRAWATCH NER AI PIPELINE                                    |
+--------------------------------------------------------------------------------------------------+
|  1. SPATIAL SUSCEPTIBILITY (Phase 1)                |  2. TEMPORAL FORECASTING (Phase 2 Upgrade) |
|  - Engine: LightGBM Active + XGBoost Standby       |  - Engine: Temporal Fusion Transformer (TFT)|
|  - Inputs: Static DEM terrain, lithology, weather   |  - Inputs: Multivariate IoT sensor streams |
|  - Output: Landslide probability [0.0 - 1.0]        |  - Output: Multi-horizon soil saturation   |
|  - Explainability: Native TreeSHAP log-odds         |    and pore water pressure [p10, p50, p90] |
|  - Role: Primary operational early warning          |  - Role: Independent advisory foresight    |
+--------------------------------------------------------------------------------------------------+
```

---

## 2. Theoretical Architecture

The Temporal Fusion Transformer (Lim et al., 2021) is engineered for multi-horizon time-series forecasting with heterogeneous inputs:

1. **Gated Residual Networks (GRN):**
   Non-linear processing units with Gated Linear Unit (GLU) activation and residual skip connections, conditioned on static station context vectors ($c$):
   $$\text{GRN}(a, c) = \text{LayerNorm}(a + \text{GLU}(\eta_2))$$
2. **Variable Selection Networks (VSN):**
   Dynamically weights feature importance at each time step, filtering uninformative sensor noise:
   $$v_t = \text{Softmax}(\text{GRN}_v([x_1, \dots, x_K], c))$$
   $$\tilde{x}_t = \sum_{k=1}^K v_{t,k} \text{GRN}_k(x_{t,k})$$
3. **LSTM Sequence Processing:**
   * Past observed sequence ($t-23 \dots t$): Handled by an LSTM Encoder.
   * Future known sequence ($t+1 \dots t+24$): Handled by an LSTM Decoder.
4. **Interpretable Multi-Head Self-Attention:**
   Shares the value matrix across all heads to yield direct, interpretable attention weights $\alpha(t, \tau)$ revealing which historical time-steps most influenced future risk.
5. **Multi-Quantile Outputs:**
   Predicts 10th percentile ($p_{10}$), median ($p_{50}$), and 90th percentile ($p_{90}$) simultaneously using pinball loss:
   $$\mathcal{L}(y, \hat{y}_q) = \max(q(y - \hat{y}_q), (1-q)(\hat{y}_q - y))$$

---

## 3. Benchmark Evaluation (TFT vs. Statistical Baselines)

The TFT model (`backend/models/tft/tft_metadata.json`, 97,704 parameters, best epoch 9) was evaluated on a held-out chronological test split (zero future leakage):

| Target Variable | Horizon | TFT MAE | TFT RMSE | Persistence MAE | Persistence RMSE | 24h Moving Avg MAE | MAE Reduction vs. Persistence |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Soil Moisture (%)** | **1h** | **1.088** | **2.261** | 1.441 | 3.097 | 10.387 | **24.5%** |
| | **6h** | **1.519** | **4.059** | 7.732 | 13.514 | 13.365 | **80.4%** |
| | **24h** | **2.191** | **4.327** | 19.783 | 25.742 | 19.937 | **88.9%** |
| **Pore Water Pressure (kPa)** | **1h** | **0.797** | **1.775** | 1.072 | 3.131 | 11.316 | **25.7%** |
| | **6h** | **1.155** | **3.453** | 6.499 | 12.622 | 16.018 | **82.2%** |
| | **24h** | **2.567** | **5.705** | 25.612 | 30.980 | 27.455 | **90.0%** |

---

## 4. REST API Endpoints

### 4.1 System Status & Provenance
* **Endpoint:** `GET /api/forecast/status`
* **Response:**
  ```json
  {
    "status": "READY",
    "engine": "Temporal Fusion Transformer (TFT)",
    "device": "cpu",
    "model_loaded": true,
    "forecast_horizons": ["1h", "6h", "24h"],
    "targets": ["soil_moisture_pct", "pore_pressure_kpa"],
    "quantiles": [0.1, 0.5, 0.9],
    "advisory_mode": true,
    "fusion_isolated": true,
    "provenance": "Category C (Simulation-Based Academic Advisory Model)"
  }
  ```

### 4.2 Multi-Horizon Station Forecast
* **Endpoint:** `GET /api/forecast/tft?station_id=SN-AS-001&horizon=24h`
* **Parameters:**
  * `station_id` (string): Station identifier (e.g. `SN-AS-001`) or city name (e.g. `Guwahati`).
  * `horizon` (string): `1h`, `6h`, or `24h`.
* **Output:** Structured response containing 12-hour observed historical context, 24-step forecast trajectory with $p_{10}, p_{50}, p_{90}$ quantiles, and CPU latency ($< 150\,\text{ms}$).

### 4.3 Interactive Scenario Simulator
* **Endpoint:** `POST /api/forecast/simulate`
* **Body:**
  ```json
  {
    "sensor_id": "SN-AS-001",
    "initial_moisture_pct": 40.0,
    "initial_pore_pressure_kpa": 5.0,
    "rainfall_scenario_mm": 80.0,
    "horizon_hours": 24
  }
  ```

---

## 5. Academic Provenance & Life-Safety Boundaries

> [!IMPORTANT]
> **Advisory Mode Isolation:**
> 1. Physical field piezometers and dielectric probes are not deployed on the mountain; training used calibrated regional telemetry patterns.
> 2. The TFT forecasting layer is strictly decoupled from the operational decision engine (`fusion_service.py`).
> 3. Operational landslide risk levels and emergency dispatch sirens are driven exclusively by the primary LightGBM model and deterministic geotechnical override rules ($P \ge 25\,\text{kPa}$, vibration $\ge 1.5\,\text{g}$).
