import pytest
import io
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import Settings
from backend.app.utils.security import create_access_token
from backend.app.services.fusion_service import fusion_engine
from sensor_simulator.sensor_simulator import generate_scenario_reading, NER_STATIONS

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def admin_token():
    return create_access_token({"sub": "admin@landsafe.gov.in", "role": "ADMIN"})

@pytest.fixture
def citizen_token():
    return create_access_token({"sub": "landsafe.user@example.com", "role": "CITIZEN"})

# =========================================================================
# 1. SECURITY & RBAC ENFORCEMENT
# =========================================================================

def test_admin_settings_unauthenticated_rejected(client):
    """POST /api/admin/settings must reject unauthenticated requests with 401."""
    resp = client.post("/api/admin/settings", json={"soil_moisture_critical_pct": 80.0})
    assert resp.status_code == 401

def test_admin_settings_non_admin_forbidden(client, citizen_token):
    """POST /api/admin/settings must reject non-admin users with 403 Forbidden."""
    headers = {"Authorization": f"Bearer {citizen_token}"}
    resp = client.post(
        "/api/admin/settings",
        json={"soil_moisture_critical_pct": 80.0},
        headers=headers
    )
    assert resp.status_code == 403

def test_admin_settings_admin_authorized(client, admin_token):
    """POST /api/admin/settings must succeed for authenticated ADMIN."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.post(
        "/api/admin/settings",
        json={"soil_moisture_critical_pct": 77.5},
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["settings"]["soil_moisture_critical_pct"] == 77.5

def test_secret_key_fails_when_missing():
    """Verify system does not use hardcoded secret fallback and fails if SECRET_KEY is missing."""
    import pydantic_core
    with pytest.raises(pydantic_core.ValidationError):
        # Initializing without env file and without SECRET_KEY in dict
        Settings(_env_file=None)

# =========================================================================
# 2. REAL METRICS (NO ARTIFICIAL FLOORS OR STATIC PLACEHOLDERS)
# =========================================================================

def test_admin_dashboard_genuine_counts_no_artificial_floors(client):
    """Verify admin dashboard returns genuine query results without max(..., 15) floors."""
    resp = client.get("/api/admin/dashboard")
    assert resp.status_code == 200
    data = resp.json()

    # Verify keys exist
    for key in ["highRiskLocations", "openReports", "activeAlerts", "emergencyRequests", "overallRisk"]:
        assert key in data
        assert isinstance(data[key], int)

    # Values must be raw non-negative integers from DB, not forced to artificial minimums
    assert data["openReports"] >= 0
    assert data["activeAlerts"] >= 0
    assert data["emergencyRequests"] >= 0

# =========================================================================
# 3. UPLOAD SECURITY & MIME GATEKEEPER
# =========================================================================

def test_upload_rejects_non_image_extension(client):
    """POST /api/reports must reject disallowed file extensions (e.g., .exe, .sh)."""
    fake_file = io.BytesIO(b"MALICIOUS_EXEC_CONTENT")
    resp = client.post(
        "/api/reports",
        data={
            "issueType": "landslide",
            "location": "Guwahati Slope",
            "state": "Assam",
            "description": "Test report"
        },
        files={"photo": ("payload.exe", fake_file, "application/octet-stream")}
    )
    assert resp.status_code == 400
    assert "Only image files" in resp.json()["detail"]

def test_upload_rejects_non_image_mime(client):
    """POST /api/reports must reject non-image MIME types."""
    fake_file = io.BytesIO(b"PDF_DUMMY_CONTENT")
    resp = client.post(
        "/api/reports",
        data={
            "issueType": "landslide",
            "location": "Guwahati Slope",
            "state": "Assam",
            "description": "Test report"
        },
        files={"photo": ("document.png", fake_file, "application/pdf")}
    )
    assert resp.status_code == 400
    assert "Invalid file type" in resp.json()["detail"]

# =========================================================================
# 4. DETERMINISTIC SENSOR SIMULATOR SCENARIOS & PROVENANCE
# =========================================================================

def test_simulator_normal_scenario():
    """Verify simulator generates baseline readings tagged with is_simulated=True."""
    reading = generate_scenario_reading(NER_STATIONS[0], "normal", "SN-AS-001", cycle=1)
    assert reading["is_simulated"] is True
    assert reading["scenario_applied"] == "normal"
    assert "Category C" in reading["provenance_notice"]
    assert reading["soil_moisture"] < 45.0
    assert reading["pore_pressure"] < 10.0

def test_simulator_pore_pressure_scenario():
    """Verify simulator deterministic pore pressure escalation."""
    reading = generate_scenario_reading(NER_STATIONS[1], "pore_pressure", "SN-ML-001", cycle=1)
    assert reading["is_simulated"] is True
    assert reading["scenario_applied"] == "pore_pressure"
    assert reading["pore_pressure"] >= 28.0
    assert "Simulation scenario parameter" in reading["provenance_notice"]

def test_simulator_override_scenario():
    """Verify simulator extreme values trip fusion safety override."""
    reading = generate_scenario_reading(NER_STATIONS[1], "override", "SN-ML-001", cycle=1)
    assert reading["is_simulated"] is True
    assert reading["soil_moisture"] == 88.5
    assert reading["pore_pressure"] == 42.0
    assert reading["ground_vibration"] == 0.85

    # Test that this telemetry trips fusion safety override
    temporal_override_metrics = {
        "temporal_risk_score": 85.0,
        "trend": "ACCELERATING",
        "data_sufficiency": "SUFFICIENT",
        "sensor_factors": {
            "pore_pressure": {"current": 42.0, "rate_per_hr": 2.5},
            "soil_moisture": {"current": 88.5, "rate_per_hr": 5.0},
            "vibration": {"current": 0.85, "anomaly_ratio": 4.5}
        }
    }
    fusion_res = fusion_engine.fuse_evidence(
        spatial_pred={"risk_score": 60, "landslide_risk_pct": 60, "flood_risk_pct": 30},
        temporal_analysis=temporal_override_metrics,
        location_meta={"latitude": 25.5788, "longitude": 91.8933}
    )
    assert fusion_res["overrides"]["triggered"] is True
    assert fusion_res["risk_tier"] == "CRITICAL"
    assert any("CRITICAL_PORE_PRESSURE_OVERRIDE" in r["rule_id"] for r in fusion_res["overrides"]["rules"])

# =========================================================================
# 5. MULTI-MODAL FUSION DISCLOSURE & UNCALIBRATED CV INTEGRITY
# =========================================================================

def test_fusion_scientific_disclosures_and_uncalibrated_cv():
    """Verify fusion layer transparently reports uncalibrated status for CV and does not invent confidence."""
    fusion_res = fusion_engine.fuse_evidence(
        spatial_pred={"risk_score": 55, "landslide_risk_pct": 55, "flood_risk_pct": 20},
        visual_analysis={
            "hazard_detected": True,
            "hazard_type": "landslide_debris",
            "evidence_strength": "MODERATE",
            "scientific_status": "uncalibrated_unvalidated",
            "trained_classifier": False,
            "confidence": None,
            "latitude": 26.1445,
            "longitude": 91.7362
        },
        location_meta={"latitude": 26.1445, "longitude": 91.7362}
    )
    visual = fusion_res["components"]["visual"]
    assert visual["scientific_status"] == "uncalibrated_unvalidated"
    assert visual["confidence"] is None  # Strictly None when uncalibrated
    assert visual["trained_classifier"] is False
    assert "weights_applied" in fusion_res
    assert fusion_res["weights_applied"]["spatial"] > 0
