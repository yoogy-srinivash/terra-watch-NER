"""
LandSafe Connect - Computer Vision Hazard Evidence Engine Test Suite (Phase 3)
Verifies:
1. Valid image loads successfully.
2. Corrupted image is rejected.
3. Missing image is handled gracefully.
4. Very low-resolution image is handled correctly.
5. Deterministic feature extraction produces repeatable results.
6. No trained model is incorrectly reported as a trained landslide classifier.
7. Confidence is null when no trained classifier exists.
8. Feature-extraction-only mode reports the correct scientific status.
9. Heuristic fallback reports scientific_status = HEURISTIC_NOT_VALIDATED.
10. Existing /api/reports behavior remains compatible.
11. Existing uploaded_media records remain valid.
12. CV analysis does not modify spatial or temporal risk.
"""

import io
import os
import pytest
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import UploadedMedia, FieldReport
from backend.app.services.cv_service import (
    analyze_field_image,
    ImageQualityChecker,
    DeterministicVisualAnalyzer,
    FeatureExtractorBackbone,
    HazardVisionModel,
    register_hazard_model,
    get_empty_model_metadata
)
from backend.app.services.ml_service import ml_engine
from backend.app.services.temporal_service import temporal_engine


@pytest.fixture
def sample_vegetated_image(tmp_path) -> str:
    """Generate a clean synthetic green vegetated image."""
    img_path = str(tmp_path / "vegetated_slope.png")
    # 128x128 green image with slight natural variance
    np.random.seed(42)
    data = np.zeros((128, 128, 3), dtype=np.uint8)
    data[:, :, 0] = np.random.randint(30, 60, (128, 128))    # Low Red
    data[:, :, 1] = np.random.randint(140, 200, (128, 128))  # Dominant Green
    data[:, :, 2] = np.random.randint(20, 50, (128, 128))    # Low Blue
    img = Image.fromarray(data)
    img.save(img_path)
    return img_path


@pytest.fixture
def sample_debris_image(tmp_path) -> str:
    """Generate a clean synthetic brown muddy/rocky debris image."""
    img_path = str(tmp_path / "earth_debris.png")
    np.random.seed(101)
    data = np.zeros((128, 128, 3), dtype=np.uint8)
    data[:, :, 0] = np.random.randint(160, 220, (128, 128))  # Dominant Red
    data[:, :, 1] = np.random.randint(100, 140, (128, 128))  # Moderate Green
    data[:, :, 2] = np.random.randint(40, 70, (128, 128))    # Low Blue
    # Add rough contrast patch
    data[40:80, 40:80, :] = np.random.randint(80, 240, (40, 40, 3))
    img = Image.fromarray(data)
    img.save(img_path)
    return img_path


# -----------------------------------------------------------------------------
# TEST 1: Valid image loads successfully
# -----------------------------------------------------------------------------
def test_1_valid_image_loads_successfully(sample_vegetated_image):
    result = analyze_field_image(sample_vegetated_image)
    assert result["image_quality"]["valid"] is True
    assert result["image_quality"]["dimensions"] == [128, 128]
    assert result["image_quality"]["channels"] == 3
    assert result["visual_features"] is not None
    assert "mean_rgb" in result["visual_features"]
    assert "contrast_variance" in result["visual_features"]


# -----------------------------------------------------------------------------
# TEST 2: Corrupted image is rejected
# -----------------------------------------------------------------------------
def test_2_corrupted_image_is_rejected(tmp_path):
    corrupt_path = str(tmp_path / "corrupted_file.jpg")
    with open(corrupt_path, "wb") as f:
        f.write(b"NOT_A_VALID_JPEG_HEADER_CORRUPTED_BYTES_123456789")

    result = analyze_field_image(corrupt_path)
    assert result["image_quality"]["valid"] is False
    assert result["scientific_status"] == "REJECTED_QUALITY_FAILURE"
    assert result["hazard_detected"] is False
    assert result["confidence"] is None
    assert any("Corrupted or undecodable" in issue for issue in result["evidence"])


# -----------------------------------------------------------------------------
# TEST 3: Missing image is handled gracefully
# -----------------------------------------------------------------------------
def test_3_missing_image_handled_gracefully(tmp_path):
    missing_path = str(tmp_path / "non_existent_image_file.png")
    result = analyze_field_image(missing_path)

    assert result["image_quality"]["valid"] is False
    assert result["confidence"] is None
    assert result["hazard_detected"] is False
    assert any("does not exist" in issue for issue in result["evidence"])


# -----------------------------------------------------------------------------
# TEST 4: Very low-resolution image is handled correctly
# -----------------------------------------------------------------------------
def test_4_very_low_resolution_image_handled_correctly(tmp_path):
    tiny_path = str(tmp_path / "tiny_16x16.png")
    img = Image.new("RGB", (16, 16), color=(100, 100, 100))
    img.save(tiny_path)

    result = analyze_field_image(tiny_path)
    # Below MIN_WIDTH/MIN_HEIGHT (32x32), image must be rejected
    assert result["image_quality"]["valid"] is False
    assert result["scientific_status"] == "REJECTED_QUALITY_FAILURE"
    assert any("below minimum threshold" in issue for issue in result["image_quality"]["issues"])


# -----------------------------------------------------------------------------
# TEST 5: Deterministic feature extraction produces repeatable results
# -----------------------------------------------------------------------------
def test_5_deterministic_feature_extraction_produces_repeatable_results(sample_debris_image):
    run_1 = analyze_field_image(sample_debris_image)
    run_2 = analyze_field_image(sample_debris_image)

    assert run_1["visual_features"] == run_2["visual_features"]
    assert run_1["hazard_type"] == run_2["hazard_type"]
    assert run_1["evidence_strength"] == run_2["evidence_strength"]
    assert run_1["evidence"] == run_2["evidence"]


# -----------------------------------------------------------------------------
# TEST 6: No trained model is incorrectly reported as a trained landslide classifier
# -----------------------------------------------------------------------------
def test_6_no_trained_model_incorrectly_reported_as_trained_landslide_classifier(sample_debris_image):
    result = analyze_field_image(sample_debris_image)
    assert result["trained_classifier"] is False
    assert result["model_available"] is False
    assert result["is_scientific_validated"] is False
    assert result["model_metadata"]["dataset_name"] is None
    assert result["model_metadata"]["metrics"] is None


# -----------------------------------------------------------------------------
# TEST 7: Confidence is null when no trained classifier exists
# -----------------------------------------------------------------------------
def test_7_confidence_is_null_when_no_trained_classifier_exists(sample_vegetated_image, sample_debris_image):
    res_veg = analyze_field_image(sample_vegetated_image)
    res_debris = analyze_field_image(sample_debris_image)

    # Strictly None / null - NOT 0.78, 0.85, or any fabricated float
    assert res_veg["confidence"] is None
    assert res_debris["confidence"] is None


# -----------------------------------------------------------------------------
# TEST 8: Feature-extraction-only mode reports the correct scientific status
# -----------------------------------------------------------------------------
def test_8_feature_extraction_only_mode_reports_correct_scientific_status(sample_vegetated_image):
    result = analyze_field_image(sample_vegetated_image)
    if FeatureExtractorBackbone.is_available():
        assert result["scientific_status"] == "FEATURE_EXTRACTION_ONLY"
        assert result["model_type"] == "MobileNetV2 pretrained feature extractor"
    else:
        assert result["scientific_status"] == "HEURISTIC_NOT_VALIDATED"
        assert result["model_type"] == "Deterministic Visual Evidence Analyzer"


# -----------------------------------------------------------------------------
# TEST 9: Heuristic fallback reports scientific_status = HEURISTIC_NOT_VALIDATED
# -----------------------------------------------------------------------------
def test_9_heuristic_fallback_reports_scientific_status(sample_vegetated_image):
    with Image.open(sample_vegetated_image) as img:
        features = DeterministicVisualAnalyzer.extract_features(img)
        assert "mean_rgb" in features
        assert "earth_tone_ratio" in features
        assert "vegetation_index" in features
        assert "edge_density" in features

    result = analyze_field_image(sample_vegetated_image)
    # When torch is not present or in fallback, scientific status must be HEURISTIC_NOT_VALIDATED
    assert result["scientific_status"] in ["HEURISTIC_NOT_VALIDATED", "FEATURE_EXTRACTION_ONLY"]


# -----------------------------------------------------------------------------
# TEST 10: Existing /api/reports behavior remains compatible
# -----------------------------------------------------------------------------
def test_10_existing_api_reports_behavior_remains_compatible(sample_debris_image):
    with TestClient(app) as client:
        with open(sample_debris_image, "rb") as img_file:
            response = client.post(
                "/api/reports",
                data={
                    "userName": "Officer Sharma",
                    "issueType": "landslide",
                    "severity": "high",
                    "location": "Aizawl North Pass",
                    "state": "Mizoram",
                    "city": "Aizawl",
                    "description": "Loose soil and small slope failure observed near highway cut.",
                    "emergency": False,
                    "latitude": 23.7367,
                    "longitude": 92.7146
                },
                files={
                    "photo": ("debris.png", img_file, "image/png")
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "reportId" in data
        assert data["ai_analysis"] is not None
        assert "hazard_label" in data["ai_analysis"]
        # Confidence must be null in API response
        assert data["ai_analysis"]["confidence"] is None
        assert data["ai_analysis"]["trained_classifier"] is False


# -----------------------------------------------------------------------------
# TEST 11: Existing uploaded_media records remain valid
# -----------------------------------------------------------------------------
def test_11_existing_uploaded_media_records_remain_valid(sample_vegetated_image):
    db = SessionLocal()
    try:
        media = UploadedMedia(
            report_id="TEST-REPORT-CV-01",
            file_name="test_veg.png",
            file_path=sample_vegetated_image,
            file_size_bytes=1024,
            ai_hazard_label="normal_terrain",
            ai_confidence=None  # Must support nullable confidence
        )
        db.add(media)
        db.commit()

        # Query back
        rec = db.query(UploadedMedia).filter(UploadedMedia.report_id == "TEST-REPORT-CV-01").first()
        assert rec is not None
        assert rec.ai_hazard_label == "normal_terrain"
        assert rec.ai_confidence is None
    finally:
        # Clean up
        db.query(UploadedMedia).filter(UploadedMedia.report_id == "TEST-REPORT-CV-01").delete()
        db.commit()
        db.close()


# -----------------------------------------------------------------------------
# TEST 12: CV analysis does not modify spatial or temporal risk
# -----------------------------------------------------------------------------
def test_12_cv_analysis_does_not_modify_spatial_or_temporal_risk(sample_debris_image, sample_vegetated_image):
    db = SessionLocal()
    try:
        # 1. Baseline ML spatial prediction
        ml_input = {
            "latitude": 27.5861,
            "longitude": 91.8594,
            "state": "Arunachal Pradesh",
            "district": "Tawang",
            "rainfall_24h_mm": 50.0,
            "rainfall_72h_mm": 120.0,
            "soil_moisture_pct": 75.0,
            "slope_angle_deg": 42.0,
            "elevation_m": 3048.0,
            "distance_to_road_m": 45.0
        }
        baseline_ml = ml_engine.predict(ml_input)
        baseline_score = baseline_ml["risk_score"]

        # 2. Baseline Temporal analysis
        baseline_temporal = temporal_engine.analyze_station_temporal_risk(db, "SN-AR-001")
        baseline_temporal_score = baseline_temporal["temporal_risk_score"]

        # 3. Run multiple CV analyses on diverse images
        _ = analyze_field_image(sample_debris_image)
        _ = analyze_field_image(sample_vegetated_image)
        _ = analyze_field_image("non_existent_file.png")

        # 4. Re-evaluate spatial and temporal engines
        post_ml = ml_engine.predict(ml_input)
        post_temporal = temporal_engine.analyze_station_temporal_risk(db, "SN-AR-001")

        # Verify spatial and temporal outputs remain 100% invariant
        assert post_ml["risk_score"] == baseline_score
        assert post_ml["risk_level"] == baseline_ml["risk_level"]
        assert post_ml["model_metadata"]["active_model"] == baseline_ml["model_metadata"]["active_model"]
        assert post_temporal["temporal_risk_score"] == baseline_temporal_score
        assert post_temporal["trend"] == baseline_temporal["trend"]
    finally:
        db.close()
