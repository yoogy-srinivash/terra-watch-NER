"""
LandSafe Connect - Multi-Modal Risk Fusion & Decision Layer Test Suite (Phase 4)
Verifies:
1. Low spatial + low temporal + no visual evidence -> LOW.
2. Elevated spatial risk increases fused risk.
3. Rising temporal risk increases fused risk.
4. Strong temporal acceleration increases fused risk.
5. Visual evidence affects fusion only when geographically associated.
6. Unlocalized visual evidence does not affect unrelated stations.
7. Heuristic CV evidence does not become fake probability.
8. Missing/insufficient temporal data is handled explicitly.
9. Missing visual evidence is handled explicitly.
10. All three evidence streams combine deterministically.
11. Critical pore-pressure override is triggered correctly.
12. Critical vibration override is triggered correctly.
13. Override reason/value/threshold are recorded.
14. Calculated score remains distinguishable from override-adjusted final decision.
15. Risk tiers are deterministic around threshold boundaries.
16. API endpoints integration (/api/risk/fusion and /api/risk/live).
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.services.fusion_service import (
    RiskFusionEngine,
    FusionPolicyConfig,
    check_visual_localization,
    haversine_distance_km
)


# -----------------------------------------------------------------------------
# FIXTURES
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_low_spatial():
    return {
        "risk_probability": 0.15,
        "risk_score": 15,
        "risk_level": "LOW",
        "model_metadata": {
            "active_model": "LightGBM Classifier",
            "standby_model": "XGBoost Classifier",
            "ensemble_agreement_pct": 100.0
        },
        "explainability": {"top_factors": [{"feature": "slope_angle_deg", "impact": 0.05}]}
    }


@pytest.fixture
def mock_high_spatial():
    return {
        "risk_probability": 0.72,
        "risk_score": 72,
        "risk_level": "HIGH",
        "model_metadata": {
            "active_model": "LightGBM Classifier",
            "standby_model": "XGBoost Classifier",
            "ensemble_agreement_pct": 98.0
        },
        "explainability": {"top_factors": [{"feature": "rainfall_24h_mm", "impact": 0.35}]}
    }


@pytest.fixture
def mock_low_temporal():
    return {
        "temporal_risk_score": 12.0,
        "trend": "STABLE",
        "data_sufficiency": "SUFFICIENT",
        "sensor_factors": {
            "soil_moisture": {"current": 62.0, "rate_per_hr": 0.05},
            "pore_pressure": {"current": 9.5, "rate_per_hr": 0.02},
            "vibration": {"current": 0.04, "anomaly_ratio": 1.0}
        }
    }


@pytest.fixture
def mock_rising_temporal():
    return {
        "temporal_risk_score": 68.0,
        "trend": "RISING",
        "data_sufficiency": "SUFFICIENT",
        "sensor_factors": {
            "soil_moisture": {"current": 84.0, "rate_per_hr": 2.1},
            "pore_pressure": {"current": 19.5, "rate_per_hr": 1.2},
            "vibration": {"current": 0.12, "anomaly_ratio": 2.2}
        }
    }


# -----------------------------------------------------------------------------
# TEST 1: Low spatial + low temporal + no visual evidence -> LOW
# -----------------------------------------------------------------------------
def test_1_low_spatial_low_temporal_no_visual_produces_low(mock_low_spatial, mock_low_temporal):
    res = RiskFusionEngine.fuse_evidence(
        spatial_pred=mock_low_spatial,
        temporal_analysis=mock_low_temporal,
        visual_analysis=None
    )
    assert res["risk_tier"] == "LOW"
    assert res["fused_risk_score"] < FusionPolicyConfig.TIER_LOW_MAX
    assert res["overrides"]["triggered"] is False


# -----------------------------------------------------------------------------
# TEST 2: Elevated spatial risk increases fused risk
# -----------------------------------------------------------------------------
def test_2_elevated_spatial_risk_increases_fused_risk(mock_low_spatial, mock_high_spatial, mock_low_temporal):
    res_low = RiskFusionEngine.fuse_evidence(mock_low_spatial, mock_low_temporal)
    res_high = RiskFusionEngine.fuse_evidence(mock_high_spatial, mock_low_temporal)

    assert res_high["fused_risk_score"] > res_low["fused_risk_score"]
    assert res_high["components"]["spatial"]["score"] == 0.72


# -----------------------------------------------------------------------------
# TEST 3: Rising temporal risk increases fused risk
# -----------------------------------------------------------------------------
def test_3_rising_temporal_risk_increases_fused_risk(mock_low_spatial, mock_low_temporal, mock_rising_temporal):
    res_stable = RiskFusionEngine.fuse_evidence(mock_low_spatial, mock_low_temporal)
    res_rising = RiskFusionEngine.fuse_evidence(mock_low_spatial, mock_rising_temporal)

    assert res_rising["fused_risk_score"] > res_stable["fused_risk_score"]
    assert res_rising["components"]["temporal"]["trend"] == "RISING"


# -----------------------------------------------------------------------------
# TEST 4: Strong temporal acceleration increases fused risk
# -----------------------------------------------------------------------------
def test_4_strong_temporal_acceleration_increases_fused_risk(mock_low_spatial):
    temporal_stable = {
        "temporal_risk_score": 40.0,
        "trend": "STABLE",
        "data_sufficiency": "SUFFICIENT",
        "sensor_factors": {
            "soil_moisture": {"rate_per_hr": 0.2},
            "pore_pressure": {"rate_per_hr": 0.1}
        }
    }
    temporal_accel = {
        "temporal_risk_score": 78.0,
        "trend": "ACCELERATING",
        "data_sufficiency": "SUFFICIENT",
        "sensor_factors": {
            "soil_moisture": {"rate_per_hr": 3.4},
            "pore_pressure": {"rate_per_hr": 1.8}
        }
    }
    res_stable = RiskFusionEngine.fuse_evidence(mock_low_spatial, temporal_stable)
    res_accel = RiskFusionEngine.fuse_evidence(mock_low_spatial, temporal_accel)

    assert res_accel["fused_risk_score"] > res_stable["fused_risk_score"]
    assert res_accel["components"]["temporal"]["trend"] == "ACCELERATING"


# -----------------------------------------------------------------------------
# TEST 5: Visual evidence affects fusion only when geographically associated
# -----------------------------------------------------------------------------
def test_5_visual_evidence_affects_fusion_when_geographically_associated(mock_low_spatial, mock_low_temporal):
    station_meta = {
        "latitude": 25.5788,
        "longitude": 91.8933,
        "name": "Shillong Slope Watch"
    }
    # Localized image within 2 km
    visual_loc = {
        "latitude": 25.5820,
        "longitude": 91.8960,
        "hazard_detected": True,
        "hazard_type": "exposed_soil_or_scar",
        "evidence_strength": "MODERATE",
        "scientific_status": "HEURISTIC_NOT_VALIDATED",
        "trained_classifier": False,
        "confidence": None
    }

    res_without = RiskFusionEngine.fuse_evidence(mock_low_spatial, mock_low_temporal, location_meta=station_meta)
    res_with = RiskFusionEngine.fuse_evidence(mock_low_spatial, mock_low_temporal, visual_analysis=visual_loc, location_meta=station_meta)

    assert res_with["components"]["visual"]["localized"] is True
    assert res_with["components"]["visual"]["available"] is True
    assert res_with["fused_risk_score"] > res_without["fused_risk_score"]


# -----------------------------------------------------------------------------
# TEST 6: Unlocalized visual evidence does not affect unrelated stations
# -----------------------------------------------------------------------------
def test_6_unlocalized_visual_evidence_does_not_affect_unrelated_stations(mock_low_spatial, mock_low_temporal):
    # Station in Shillong, Meghalaya
    station_meta = {
        "latitude": 25.5788,
        "longitude": 91.8933,
        "name": "Shillong Slope Watch"
    }
    # Photo taken in Tawang, Arunachal Pradesh (~220 km away)
    visual_distant = {
        "latitude": 27.5861,
        "longitude": 91.8594,
        "location_name": "Tawang Mountain Pass",
        "hazard_detected": True,
        "hazard_type": "landslide_debris",
        "evidence_strength": "HIGH",
        "scientific_status": "HEURISTIC_NOT_VALIDATED",
        "trained_classifier": False,
        "confidence": None
    }

    res_without = RiskFusionEngine.fuse_evidence(mock_low_spatial, mock_low_temporal, location_meta=station_meta)
    res_distant = RiskFusionEngine.fuse_evidence(mock_low_spatial, mock_low_temporal, visual_analysis=visual_distant, location_meta=station_meta)

    # Must be recognized as UNLOCALIZED and ignored
    assert res_distant["components"]["visual"]["localized"] is False
    assert res_distant["components"]["visual"]["available"] is False
    assert res_distant["weights_applied"]["visual"] == 0.0
    assert res_distant["fused_risk_score"] == res_without["fused_risk_score"]


# -----------------------------------------------------------------------------
# TEST 7: Heuristic CV evidence does not become fake probability
# -----------------------------------------------------------------------------
def test_7_heuristic_cv_evidence_does_not_become_fake_probability(mock_low_spatial, mock_low_temporal):
    visual_heuristic = {
        "hazard_detected": True,
        "hazard_type": "landslide_debris",
        "evidence_strength": "HIGH",
        "scientific_status": "HEURISTIC_NOT_VALIDATED",
        "trained_classifier": False,
        "confidence": None,
        "location_name": "Guwahati Hills"
    }
    res = RiskFusionEngine.fuse_evidence(
        mock_low_spatial,
        mock_low_temporal,
        visual_analysis=visual_heuristic,
        location_meta={"name": "Guwahati Hills"}
    )
    # Confidence MUST remain strictly None
    assert res["components"]["visual"]["confidence"] is None
    assert res["components"]["visual"]["trained_classifier"] is False
    assert any("heuristic and not produced by a trained classifier" in exp for exp in res["explanation"])


# -----------------------------------------------------------------------------
# TEST 8: Missing/insufficient temporal data is handled explicitly
# -----------------------------------------------------------------------------
def test_8_missing_insufficient_temporal_data_handled_explicitly(mock_low_spatial):
    temporal_insufficient = {
        "temporal_risk_score": 0.0,
        "trend": "INSUFFICIENT_DATA",
        "data_sufficiency": "INSUFFICIENT",
        "sensor_factors": {}
    }
    res = RiskFusionEngine.fuse_evidence(mock_low_spatial, temporal_analysis=temporal_insufficient)

    assert res["components"]["temporal"]["available"] is False
    assert res["components"]["temporal"]["data_sufficiency"] == "INSUFFICIENT"
    assert res["weights_applied"]["temporal"] == 0.0
    # Spatial weight should absorb the contribution (rebalanced to 1.0)
    assert res["weights_applied"]["spatial"] == 1.0
    assert any("insufficient" in exp for exp in res["explanation"])


# -----------------------------------------------------------------------------
# TEST 9: Missing visual evidence is handled explicitly
# -----------------------------------------------------------------------------
def test_9_missing_visual_evidence_handled_explicitly(mock_low_spatial, mock_low_temporal):
    res = RiskFusionEngine.fuse_evidence(mock_low_spatial, mock_low_temporal, visual_analysis=None)

    assert res["components"]["visual"]["available"] is False
    assert res["weights_applied"]["visual"] == 0.0
    assert res["weights_applied"]["spatial"] == FusionPolicyConfig.WEIGHT_SPATIAL_NO_VISUAL
    assert res["weights_applied"]["temporal"] == FusionPolicyConfig.WEIGHT_TEMPORAL_NO_VISUAL


# -----------------------------------------------------------------------------
# TEST 10: All three evidence streams combine deterministically
# -----------------------------------------------------------------------------
def test_10_all_three_evidence_streams_combine_deterministically(mock_low_spatial, mock_rising_temporal):
    visual = {
        "hazard_detected": True,
        "hazard_type": "exposed_soil_or_scar",
        "evidence_strength": "MODERATE",
        "scientific_status": "HEURISTIC_NOT_VALIDATED",
        "trained_classifier": False,
        "confidence": None,
        "location_name": "Test Site"
    }
    loc_meta = {"name": "Test Site"}

    run_1 = RiskFusionEngine.fuse_evidence(mock_low_spatial, mock_rising_temporal, visual, loc_meta)
    run_2 = RiskFusionEngine.fuse_evidence(mock_low_spatial, mock_rising_temporal, visual, loc_meta)

    assert run_1["fused_risk_score"] == run_2["fused_risk_score"]
    assert run_1["risk_tier"] == run_2["risk_tier"]
    assert run_1["weights_applied"] == run_2["weights_applied"]
    assert run_1["decision_basis"] == run_2["decision_basis"]


# -----------------------------------------------------------------------------
# TEST 11: Critical pore-pressure override is triggered correctly
# -----------------------------------------------------------------------------
def test_11_critical_pore_pressure_override_triggered_correctly(mock_low_spatial):
    temporal_critical_pore = {
        "temporal_risk_score": 45.0,
        "trend": "RISING",
        "data_sufficiency": "SUFFICIENT",
        "sensor_factors": {
            "pore_pressure": {"current": 26.8, "rate_per_hr": 2.2},
            "vibration": {"current": 0.04, "anomaly_ratio": 1.0}
        }
    }
    res = RiskFusionEngine.fuse_evidence(mock_low_spatial, temporal_critical_pore)

    assert res["overrides"]["triggered"] is True
    assert res["risk_tier"] == "CRITICAL"
    rules = [r["rule_id"] for r in res["overrides"]["rules"]]
    assert "CRITICAL_PORE_PRESSURE_OVERRIDE" in rules


# -----------------------------------------------------------------------------
# TEST 12: Critical vibration override is triggered correctly
# -----------------------------------------------------------------------------
def test_12_critical_vibration_override_triggered_correctly(mock_low_spatial, mock_low_temporal):
    temporal_vibration_spike = {
        "temporal_risk_score": 35.0,
        "trend": "STABLE",
        "data_sufficiency": "SUFFICIENT",
        "sensor_factors": {
            "pore_pressure": {"current": 10.0, "rate_per_hr": 0.0},
            "vibration": {"current": 1.75, "anomaly_ratio": 5.2}
        }
    }
    res = RiskFusionEngine.fuse_evidence(mock_low_spatial, temporal_vibration_spike)

    assert res["overrides"]["triggered"] is True
    assert res["risk_tier"] == "CRITICAL"
    rules = [r["rule_id"] for r in res["overrides"]["rules"]]
    assert "CRITICAL_VIBRATION_SPIKE_OVERRIDE" in rules or "CRITICAL_VIBRATION_RATIO_OVERRIDE" in rules


# -----------------------------------------------------------------------------
# TEST 13: Override reason, value, and threshold are recorded
# -----------------------------------------------------------------------------
def test_13_override_reason_value_threshold_recorded(mock_low_spatial):
    temporal_critical = {
        "temporal_risk_score": 40.0,
        "trend": "RISING",
        "data_sufficiency": "SUFFICIENT",
        "sensor_factors": {
            "pore_pressure": {"current": 27.5, "rate_per_hr": 1.5},
            "vibration": {"current": 0.02, "anomaly_ratio": 1.0}
        }
    }
    res = RiskFusionEngine.fuse_evidence(mock_low_spatial, temporal_critical)
    override = res["overrides"]["rules"][0]

    assert "override_reason" in override
    assert override["measured_value"] == 27.5
    assert override["threshold"] == FusionPolicyConfig.OVERRIDE_PORE_PRESSURE_KPA
    assert "Category C" in override["provenance"]


# -----------------------------------------------------------------------------
# TEST 14: Calculated score remains distinguishable from override-adjusted final decision
# -----------------------------------------------------------------------------
def test_14_calculated_score_distinguishable_from_override_adjusted_final_decision(mock_low_spatial):
    # Calculated weighted score would be ~0.25 (LOW) without override
    temporal_critical_override = {
        "temporal_risk_score": 40.0,
        "trend": "RISING",
        "data_sufficiency": "SUFFICIENT",
        "sensor_factors": {
            "pore_pressure": {"current": 28.0, "rate_per_hr": 2.0},
            "vibration": {"current": 0.03, "anomaly_ratio": 1.0}
        }
    }
    res = RiskFusionEngine.fuse_evidence(mock_low_spatial, temporal_critical_override)

    assert res["calculated_fused_score"] < 0.40  # Underlying score is low
    assert res["final_score"] >= FusionPolicyConfig.OVERRIDE_MIN_CRITICAL_SCORE  # Override elevated it to 0.80
    assert res["final_score"] != res["calculated_fused_score"]
    assert res["risk_tier"] == "CRITICAL"


# -----------------------------------------------------------------------------
# TEST 15: Risk tiers are deterministic around threshold boundaries
# -----------------------------------------------------------------------------
def test_15_risk_tiers_deterministic_around_boundaries():
    assert RiskFusionEngine.classify_risk_tier(0.0) == "LOW"
    assert RiskFusionEngine.classify_risk_tier(0.34) == "LOW"
    assert RiskFusionEngine.classify_risk_tier(0.35) == "MODERATE"
    assert RiskFusionEngine.classify_risk_tier(0.54) == "MODERATE"
    assert RiskFusionEngine.classify_risk_tier(0.55) == "HIGH"
    assert RiskFusionEngine.classify_risk_tier(0.74) == "HIGH"
    assert RiskFusionEngine.classify_risk_tier(0.75) == "CRITICAL"
    assert RiskFusionEngine.classify_risk_tier(1.0) == "CRITICAL"


# -----------------------------------------------------------------------------
# TEST 16: API endpoints integration
# -----------------------------------------------------------------------------
def test_16_api_endpoints_integration():
    with TestClient(app) as client:
        # 1. Dedicated fusion endpoint
        resp_fusion = client.get("/api/risk/fusion?location=Guwahati")
        assert resp_fusion.status_code == 200
        fused = resp_fusion.json()
        assert "fused_risk_score" in fused
        assert "risk_tier" in fused
        assert "components" in fused
        assert "spatial" in fused["components"]
        assert "temporal" in fused["components"]
        assert "visual" in fused["components"]

        # 2. Live risk enriched with fusion
        resp_live = client.get("/api/risk/live?location=Guwahati")
        assert resp_live.status_code == 200
        live = resp_live.json()
        assert "fusion" in live
        assert "overall" in live
        assert "landslide" in live
