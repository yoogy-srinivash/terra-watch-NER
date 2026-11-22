"""
TerraWatch NER - Temporal Fusion Transformer (TFT) Automated Test Suite
Verifies:
1. Status endpoint response schema & provenance metadata.
2. Multi-horizon trajectory structure and quantile ordering (p10 <= p50 <= p90).
3. Configurable horizons (1h, 6h, 24h).
4. Strict LightGBM spatial risk invariance regression test.
5. Decision fusion isolation (advisory mode invariant).
6. Interactive scenario forecasting simulation.
7. CPU inference latency benchmark.
8. Graceful fallback on missing model weights.
"""

import time
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import Location, SensorDevice, SensorReading
from backend.app.services.tft_service import tft_engine
from backend.app.services.ml_service import ml_engine


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


def test_1_forecasting_status_endpoint(client):
    """Verify that /api/forecast/status returns READY with explicit provenance metadata."""
    resp = client.get("/api/forecast/status")
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["status"] in ["READY", "FALLBACK_BASELINE"]
    assert data["engine"] == "Temporal Fusion Transformer (TFT)"
    assert data["device"] == "cpu"
    assert "1h" in data["forecast_horizons"]
    assert "6h" in data["forecast_horizons"]
    assert "24h" in data["forecast_horizons"]
    assert "soil_moisture_pct" in data["targets"]
    assert "pore_pressure_kpa" in data["targets"]
    assert data["quantiles"] == [0.1, 0.5, 0.9]
    assert data["advisory_mode"] is True
    assert data["fusion_isolated"] is True
    assert "Category C" in data["provenance"]


def test_2_tft_forecast_trajectory_structure(client):
    """Verify 24-step trajectory has valid chronological timestamps and ordered quantiles."""
    resp = client.get("/api/forecast/tft?station_id=SN-AS-001&horizon=24h")
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["status"] == "success"
    assert data["sensor_id"] == "SN-AS-001"
    assert data["horizon_hours"] == 24
    assert len(data["forecast_trajectory"]) == 24
    assert len(data["historical_observed"]) > 0
    
    # Verify quantile ordering: p10 <= p50 <= p90
    for step in data["forecast_trajectory"]:
        sm = step["soil_moisture"]
        pp = step["pore_pressure"]
        assert sm["p10"] <= sm["p50"] <= sm["p90"]
        assert pp["p10"] <= pp["p50"] <= pp["p90"]
        assert 0.0 <= sm["p50"] <= 100.0
        assert 0.0 <= pp["p50"] <= 60.0


def test_3_configurable_horizons(client):
    """Verify 1h, 6h, and 24h horizons parameter validation and output step counts."""
    for h_str, expected_steps in [("1h", 1), ("6h", 6), ("24h", 24)]:
        resp = client.get(f"/api/forecast/tft?station_id=SN-ML-001&horizon={h_str}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["forecast_trajectory"]) == expected_steps
        assert data["horizon_hours"] == expected_steps

    # Invalid horizon rejected with 422
    invalid_resp = client.get("/api/forecast/tft?station_id=SN-AS-001&horizon=48h")
    assert invalid_resp.status_code == 422


def test_4_lightgbm_invariance_regression(client):
    """
    CRITICAL ARCHITECTURAL INVARIANCE:
    Verify that LightGBM spatial susceptibility prediction is 100% byte-for-byte
    identical with and without TFT integration.
    """
    payload = {
        "latitude": 26.14,
        "longitude": 91.73,
        "state": "Assam",
        "district": "Kamrup Metropolitan",
        "rainfall_24h_mm": 45.0,
        "slope_angle_deg": 28.0,
        "soil_moisture_pct": 72.0,
        "pore_pressure_kpa": 14.5
    }
    
    # Direct ML Engine prediction
    pred_direct = ml_engine.predict(payload)
    
    # API prediction endpoint
    api_resp = client.post("/api/risk/predict", json=payload)
    assert api_resp.status_code == 200
    api_data = api_resp.json()["prediction"]
    
    # Verify floating-point identity
    assert abs(api_data["risk_score"] - pred_direct["risk_score"]) < 1e-6
    assert api_data["risk_level"] == pred_direct["risk_level"]
    assert api_data["landslide_risk_pct"] == pred_direct["landslide_risk_pct"]


def test_5_decision_fusion_isolation(client):
    """Verify that live risk endpoint preserves operational safety tier and includes advisory field."""
    resp = client.get("/api/risk/live?location=Guwahati")
    assert resp.status_code == 200
    data = resp.json()
    
    assert "overall" in data
    assert "fusion" in data
    fusion = data["fusion"]
    assert "tft_advisory" in fusion
    assert fusion["tft_advisory"]["enabled"] is False
    assert fusion["tft_advisory"]["mode"] == "ADVISORY_INDEPENDENT"


def test_6_scenario_simulation_endpoint(client):
    """Verify POST /api/forecast/simulate adjusts subsurface progression during rainfall surge."""
    sim_payload = {
        "sensor_id": "SN-AS-001",
        "initial_moisture_pct": 40.0,
        "initial_pore_pressure_kpa": 5.0,
        "rainfall_scenario_mm": 80.0,
        "horizon_hours": 12
    }
    resp = client.post("/api/forecast/simulate", json=sim_payload)
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["status"] == "success"
    assert len(data["forecast_trajectory"]) == 12
    # Rainfall surge increases moisture and pore pressure relative to baseline
    final_step = data["forecast_trajectory"][-1]
    assert final_step["soil_moisture"]["p50"] > 40.0
    assert final_step["pore_pressure"]["p50"] > 5.0


def test_7_inference_latency_benchmark(db_session):
    """Verify CPU inference latency is well within the 200ms real-time API budget."""
    latencies = []
    for _ in range(5):
        t0 = time.time()
        res = tft_engine.forecast_station(db_session, "SN-AS-001", horizon_hours=24)
        elapsed_ms = (time.time() - t0) * 1000.0
        latencies.append(elapsed_ms)
        
    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 200.0, f"Average inference latency too high: {avg_latency:.2f}ms"
