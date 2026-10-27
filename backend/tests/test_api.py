import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

def test_health_check(client):
    """Verify system health endpoint and ML model status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["ml_model_status"] == "LOADED"
    assert "North Eastern Region" in data["region"]

def test_auth_login_and_me(client):
    """Verify JWT authentication for default administrator."""
    login_resp = client.post("/api/auth/login", json={
        "email": "admin@landsafe.gov.in",
        "password": "admin123"
    })
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # Verify protected /me endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    user_data = me_resp.json()
    assert user_data["email"] == "admin@landsafe.gov.in"
    assert user_data["role"] == "ADMIN"

def test_ml_risk_prediction(client):
    """Verify ML ensemble prediction pipeline with explainable factors."""
    payload = {
        "latitude": 25.5788,
        "longitude": 91.8933,
        "state": "Meghalaya",
        "district": "East Khasi Hills",
        "rainfall_24h_mm": 115.0,
        "rainfall_72h_mm": 240.0,
        "soil_moisture_pct": 84.5,
        "slope_angle_deg": 35.0,
        "elevation_m": 1496.0,
        "distance_to_road_m": 20.0
    }
    response = client.post("/api/risk/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    pred = data["prediction"]
    assert "risk_score" in pred
    assert 0 <= pred["risk_score"] <= 100
    assert pred["risk_level"] in ["MODERATE", "HIGH", "CRITICAL"]
    assert len(pred["contributing_factors"]) > 0
    assert len(pred["recommendations"]) > 0

def test_live_risk_location(client):
    """Verify live risk query for monitored NER capital."""
    response = client.get("/api/risk/live?location=Guwahati")
    assert response.status_code == 200
    data = response.json()
    assert "overall" in data
    assert "landslide" in data
    assert "flood" in data
    assert data["location"]["city"] == "Guwahati"

def test_gis_geojson_layers(client):
    """Verify GIS GeoJSON layers (locations, shelters, roads)."""
    # Locations
    loc_resp = client.get("/api/gis/locations")
    assert loc_resp.status_code == 200
    loc_data = loc_resp.json()
    assert loc_data["type"] == "FeatureCollection"
    assert len(loc_data["features"]) >= 32

    # Shelters
    shelter_resp = client.get("/api/gis/shelters")
    assert shelter_resp.status_code == 200
    shelter_data = shelter_resp.json()
    assert shelter_data["type"] == "FeatureCollection"
    assert len(shelter_data["features"]) > 0

    # Roads
    road_resp = client.get("/api/gis/roads")
    assert road_resp.status_code == 200
    road_data = road_resp.json()
    assert road_data["type"] == "FeatureCollection"
    assert len(road_data["features"]) >= 6

def test_iot_sensor_ingestion(client):
    """Verify IoT sensor data ingestion and retrieval."""
    reading_payload = {
        "sensor_id": "SN-ML-001",
        "latitude": 25.5788,
        "longitude": 91.8933,
        "soil_moisture": 78.5,
        "temperature": 21.0,
        "pore_pressure": 12.4,
        "ground_vibration": 0.08,
        "battery_level": 94,
        "signal_strength": -64,
        "is_simulated": True
    }
    post_resp = client.post("/api/sensors/data", json=reading_payload)
    assert post_resp.status_code in [200, 201]

    # Verify latest reading retrieval
    latest_resp = client.get("/api/sensors/SN-ML-001/latest")
    assert latest_resp.status_code == 200
    latest = latest_resp.json()
    assert latest["sensor_id"] == "SN-ML-001"
    assert latest["soil_moisture"] == 78.5

def test_alerts_and_sirens(client):
    """Verify active alerts and siren broadcast triggering."""
    active_resp = client.get("/api/alerts/active")
    assert active_resp.status_code == 200
    assert isinstance(active_resp.json(), list)

    # Trigger siren
    siren_resp = client.post("/api/alerts/sirens/trigger?location=Shillong%2C%20Meghalaya&duration_seconds=30")
    assert siren_resp.status_code == 200
    siren_data = siren_resp.json()
    assert siren_data["siren_active"] is True

    # Stop siren
    stop_resp = client.post("/api/alerts/sirens/stop")
    assert stop_resp.status_code == 200
    assert stop_resp.json()["siren_active"] is False

def test_emergency_prioritization(client):
    """Verify multi-criteria rescue ranking algorithm."""
    resp = client.get("/api/emergency/priorities")
    assert resp.status_code == 200
    priorities = resp.json()
    assert len(priorities) > 0
    # Confirm descending priority order
    scores = [p["priority_score"] for p in priorities]
    assert scores == sorted(scores, reverse=True)

def test_offline_sync_push_and_pull(client):
    """Verify offline batch push with deduplication and cache pull."""
    # Push item
    sync_item = {
        "local_id": f"TEST-SYNC-{pytest.__name__}-001",
        "device_id": "TEST-DEVICE-01",
        "entity_type": "report",
        "payload": {
            "issue_type": "landslide",
            "severity": "high",
            "location": "Aizawl Slope",
            "state": "Mizoram",
            "description": "Offline test report submission"
        }
    }
    push_resp = client.post("/api/sync/push", json={"items": [sync_item]})
    assert push_resp.status_code == 200
    res_data = push_resp.json()
    assert res_data["successful"] >= 1

    # Idempotent push of duplicate item
    dup_resp = client.post("/api/sync/push", json={"items": [sync_item]})
    assert dup_resp.status_code == 200
    assert dup_resp.json()["results"][0]["status"] == "DUPLICATE"

    # Pull cache pack
    pull_resp = client.get("/api/sync/pull")
    assert pull_resp.status_code == 200
    cache = pull_resp.json()
    assert "stations" in cache
    assert "shelters" in cache
    assert "active_alerts" in cache

def test_admin_dashboard(client):
    """Verify admin unified dashboard aggregation metrics."""
    resp = client.get("/api/admin/dashboard")
    assert resp.status_code == 200
    dash = resp.json()
    assert "highRiskLocations" in dash
    assert "activeAlerts" in dash
    assert "overallRisk" in dash
    assert "rainfall" in dash
    assert "soil" in dash
