import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ml_service import ml_engine
from backend.app.services.terrain_service import get_station_terrain, NER_STATION_TERRAIN

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

def test_grounded_station_terrain_resolution():
    """Verify that station terrain lookups return grounded topographic & geotechnical parameters."""
    # 1. Direct ID lookup for Himalayan high-altitude station (Tawang)
    tawang = get_station_terrain(location_id="AR-TAWANG")
    assert tawang["elevation_m"] > 3000.0
    assert tawang["slope_angle_deg"] > 40.0
    assert tawang["lithology"] == "Hard Quartzite"
    assert tawang["land_use"] == "Roadside Cut Slope"

    # 2. Direct ID lookup for Brahmaputra valley lowland station (Guwahati)
    guwahati = get_station_terrain(location_id="AS-GUWAHATI")
    assert guwahati["elevation_m"] < 100.0
    assert guwahati["slope_angle_deg"] < 20.0
    assert guwahati["soil_type"] == "Residual Clay"

    # 3. Name lookup
    gangtok = get_station_terrain(name="Gangtok")
    assert gangtok["elevation_m"] > 1600.0
    assert gangtok["slope_angle_deg"] >= 38.0

    # 4. Proximity coordinate matching within NER
    near_shillong = get_station_terrain(latitude=25.58, longitude=91.89)
    assert near_shillong["elevation_m"] > 1400.0

    # 5. Regional state fallback
    fallback = get_station_terrain(state="Sikkim")
    assert fallback["elevation_m"] > 1000.0

def test_dual_model_loading_and_consensus():
    """Verify that both primary active (LightGBM) and standby (XGBoost) models are active with consensus."""
    assert ml_engine._active_model is not None, "Active model (LightGBM) must be loaded"
    assert ml_engine._standby_model is not None, "Standby ensemble model (XGBoost) must be loaded"
    assert ml_engine.model is not None, "Backward compatible ml_service.model must be present"

    payload = {
        "latitude": 27.3389,
        "longitude": 88.6065,
        "location": "Gangtok",
        "state": "Sikkim",
        "district": "East Sikkim",
        "rainfall_24h_mm": 95.0,
        "rainfall_72h_mm": 190.0,
        "soil_moisture_pct": 78.0
    }
    res = ml_engine.predict(payload)
    assert "risk_score" in res
    assert 0 <= res["risk_score"] <= 100
    meta = res["model_metadata"]
    assert "active_model" in meta
    assert "standby_model" in meta
    assert meta["active_status"] == "ONLINE"
    assert meta["standby_status"] == "READY"
    assert meta["failover_active"] is False
    assert 0 <= meta["ensemble_agreement_pct"] <= 100

def test_runtime_failover_to_standby_xgboost():
    """Verify seamless runtime failover to standby XGBoost if active model encounters an exception."""
    original_active = ml_engine._active_model
    try:
        # Mock active model throwing an error
        class BrokenModel:
            def predict_proba(self, X):
                raise RuntimeError("Simulated active model hardware/runtime error")

        ml_engine._active_model = BrokenModel()

        payload = {
            "latitude": 25.5788,
            "longitude": 91.8933,
            "location": "Shillong",
            "state": "Meghalaya",
            "rainfall_24h_mm": 110.0,
            "rainfall_72h_mm": 220.0
        }
        res = ml_engine.predict(payload)
        assert res["risk_score"] > 0
        meta = res["model_metadata"]
        assert meta["failover_active"] is True
        assert meta["active_status"] == "FAILOVER_STANDBY"
    finally:
        # Restore original active model
        ml_engine._active_model = original_active

def test_treeshap_scientific_explainability():
    """Verify that TreeSHAP feature attributions are computed and exposed in the prediction response."""
    payload = {
        "location_id": "SK-MANGAN",
        "state": "Sikkim",
        "district": "Mangan",
        "latitude": 27.5,
        "longitude": 88.5333,
        "rainfall_24h_mm": 130.0,
        "rainfall_72h_mm": 260.0,
        "soil_moisture_pct": 88.0,
        "pore_pressure_kpa": 24.0
    }
    res = ml_engine.predict(payload)
    assert "explainability" in res
    assert res["explainability"]["method"] == "TreeSHAP Local Attributions"
    top_factors = res["explainability"]["top_factors"]
    assert len(top_factors) > 0

    # Ensure contributing factors list contains grounded factor descriptions
    reasons = res["contributing_factors"]
    assert len(reasons) > 0
    assert any("rainfall" in r.lower() or "slope" in r.lower() for r in reasons)

def test_grounded_spatial_differentiation(client):
    """Verify that live risk for steep mountain stations yields higher terrain susceptibility than flat plains."""
    # Tawang (high mountain slope, 42 deg slope, quartzite)
    tawang_resp = client.get("/api/risk/live?location=Tawang")
    assert tawang_resp.status_code == 200
    tawang_data = tawang_resp.json()

    # Agartala (flat river basin, 5 deg slope)
    agartala_resp = client.get("/api/risk/live?location=Agartala")
    assert agartala_resp.status_code == 200
    agartala_data = agartala_resp.json()

    # Environmental slope and elevation should be properly grounded
    assert tawang_data["environmental_factors"]["slope_angle_deg"] > 35.0
    assert agartala_data["environmental_factors"]["slope_angle_deg"] < 10.0
    assert tawang_data["environmental_factors"]["elevation_m"] > 2500.0
    assert agartala_data["environmental_factors"]["elevation_m"] < 50.0
