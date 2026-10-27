"""
LandSafe Connect - Multi-Modal Risk Fusion & Decision Layer (Phase 4)

Combines three independent evidence streams:
1. Spatial ML risk (Phase 1: LightGBM active + XGBoost standby, TreeSHAP, grounded terrain)
2. Temporal sensor risk (Phase 2: sliding windows 1h/6h/24h, pore pressure, moisture rate, vibration)
3. Visual evidence (Phase 3: deterministic optical & spectral indicators, quality check, uncalibrated heuristics)

SCIENTIFIC STATUS & PROVENANCE NOTICE:
--------------------------------------
Unless explicitly cited from external standards, fusion weights, risk tier boundaries,
and safety override thresholds are operational policy heuristics (Category C).
They are NOT universally verified geotechnical failure criteria.
Visual evidence from Phase 3 is strictly uncalibrated (confidence = None) and must
never be presented as a trained classifier probability.
"""

import os
from datetime import datetime, timedelta
import math
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from ..models import Location, SensorDevice, FieldReport, UploadedMedia
from ..services.ml_service import ml_engine
from ..services.temporal_service import temporal_engine, resolve_station_sensor_id, TemporalPolicyThresholds
from ..services.cv_service import analyze_field_image
from ..utils.logging import audit_logger


# =============================================================================
# 1. CENTRALIZED FUSION POLICY CONFIGURATION
# =============================================================================

class FusionPolicyConfig:
    """
    Centralized configuration for multi-modal risk fusion, evidence weighting,
    risk tiers, and safety overrides.

    Provenance Classifications:
    - Category B: Documented project requirement / system API contract
    - Category C: Operational demo policy / engineering heuristic
    - Category D: Authoritative external standard
    """

    # -------------------------------------------------------------------------
    # EVIDENCE COMPONENT WEIGHTS (Category C: Operational Policy Parameters)
    # Sum of active weights is always normalized to 1.0
    # -------------------------------------------------------------------------
    # Tri-modal weights (Spatial + Temporal + Localized Visual all available)
    WEIGHT_SPATIAL_DEFAULT: float = 0.50       # Primary terrain, lithology, and live weather baseline
    WEIGHT_TEMPORAL_DEFAULT: float = 0.35      # Real-time IoT sensor infiltration & pressure dynamics
    WEIGHT_VISUAL_DEFAULT: float = 0.15        # Ground confirmation from localized field imagery

    # Dual-modal weights: Spatial + Temporal (No localized visual evidence)
    WEIGHT_SPATIAL_NO_VISUAL: float = 0.60
    WEIGHT_TEMPORAL_NO_VISUAL: float = 0.40

    # Dual-modal weights: Spatial + Visual (Temporal data insufficient or unavailable)
    WEIGHT_SPATIAL_NO_TEMPORAL: float = 0.80
    WEIGHT_VISUAL_NO_TEMPORAL: float = 0.20

    # Single-modal weight: Spatial only (No temporal sensors, no field photos)
    WEIGHT_SPATIAL_ONLY: float = 1.00

    # -------------------------------------------------------------------------
    # VISUAL HEURISTIC EVIDENCE SCALING (Category C: Operational Policy)
    # When no trained CV classifier exists, evidence_strength maps to these weights.
    # NOT calibrated probabilities.
    # -------------------------------------------------------------------------
    VISUAL_SCORE_STABLE: float = 0.05          # Continuous canopy, normal terrain
    VISUAL_SCORE_LOW: float = 0.20             # Minor/borderline visual evidence
    VISUAL_SCORE_MODERATE: float = 0.50        # Distinct bare cut or tension feature
    VISUAL_SCORE_HIGH: float = 0.85            # Pervasive debris flow or active mud scar

    # -------------------------------------------------------------------------
    # RISK TIER BOUNDARIES (Category B: Documented Project Four-Tier System)
    # Normalized [0.0, 1.0] scale
    # -------------------------------------------------------------------------
    TIER_LOW_MAX: float = 0.35                 # [0.00, 0.35) -> LOW
    TIER_MODERATE_MAX: float = 0.55            # [0.35, 0.55) -> MODERATE
    TIER_HIGH_MAX: float = 0.75                # [0.55, 0.75) -> HIGH
    TIER_CRITICAL_MIN: float = 0.75            # [0.75, 1.00] -> CRITICAL

    # -------------------------------------------------------------------------
    # SAFETY OVERRIDE THRESHOLDS (Category C: Operational Safety Policies)
    # Critical physiological triggers that elevate tier to CRITICAL immediately
    # -------------------------------------------------------------------------
    # Rule 1: Critical Piezometer Pore Pressure
    OVERRIDE_PORE_PRESSURE_KPA: float = 25.0   # Matches TemporalPolicyThresholds.PORE_PRESSURE_CRITICAL_KPA
    # Rule 2: Critical Dynamic Ground Vibration Spike
    OVERRIDE_VIBRATION_SPIKE_G: float = 1.5    # Absolute acceleration shock
    OVERRIDE_VIBRATION_RATIO: float = 4.0      # Severe anomaly relative to rolling median baseline
    # Rule 3: Extreme Temporal Saturation Acceleration
    OVERRIDE_TEMPORAL_SCORE_CRITICAL: float = 85.0
    # Rule 4: Extreme Spatial Probability
    OVERRIDE_SPATIAL_PROB_CRITICAL: float = 0.85
    # Rule 5: Severe Localized Visual Debris
    OVERRIDE_VISUAL_HIGH_DEBRIS: bool = True   # Triggered on localized high landslide_debris evidence

    # Floor score applied when an override forces CRITICAL tier
    OVERRIDE_MIN_CRITICAL_SCORE: float = 0.80

    # -------------------------------------------------------------------------
    # GEOGRAPHIC LOCALIZATION (Category C: Proximity Cutoff)
    # -------------------------------------------------------------------------
    LOCALIZATION_MAX_DISTANCE_KM: float = 15.0  # Max radius to associate field photo with station


# =============================================================================
# 2. GEOGRAPHIC DISTANCE & LOCALIZATION UTILITY
# =============================================================================

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two GPS coordinates in kilometers."""
    r_earth = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r_earth * c, 2)


def check_visual_localization(
    visual_evidence: Dict[str, Any],
    station_lat: Optional[float],
    station_lon: Optional[float],
    station_name: Optional[str] = None
) -> Tuple[bool, str, Optional[float]]:
    """
    Determine whether visual evidence is geographically attributable to a monitored station.
    Returns: (is_localized, reason, distance_km_or_none)
    """
    v_lat = visual_evidence.get("latitude")
    v_lon = visual_evidence.get("longitude")
    v_loc_name = visual_evidence.get("location_name", "")

    # 1. Coordinate-based proximity check
    if v_lat is not None and v_lon is not None and station_lat is not None and station_lon is not None:
        dist_km = haversine_distance_km(float(v_lat), float(v_lon), float(station_lat), float(station_lon))
        if dist_km <= FusionPolicyConfig.LOCALIZATION_MAX_DISTANCE_KM:
            return True, f"Coordinate proximity match: {dist_km:.1f} km from station (cutoff: {FusionPolicyConfig.LOCALIZATION_MAX_DISTANCE_KM} km).", dist_km
        else:
            return False, f"Geographically distant: {dist_km:.1f} km from station exceeds {FusionPolicyConfig.LOCALIZATION_MAX_DISTANCE_KM} km threshold.", dist_km

    # 2. Name / text matching fallback
    if station_name and v_loc_name:
        clean_v = v_loc_name.lower().strip()
        clean_s = station_name.lower().strip()
        if clean_v in clean_s or clean_s in clean_v:
            return True, f"Location name textual match: '{v_loc_name}' corresponds to '{station_name}'.", None

    return False, "UNLOCALIZED: Photo lacks spatial coordinates or recognizable station link.", None


# =============================================================================
# 3. CORE MULTI-MODAL FUSION ENGINE
# =============================================================================

class RiskFusionEngine:
    """
    Multi-Modal Risk Fusion & Decision Engine.
    Combines Spatial, Temporal, and Visual evidence streams using transparent
    operational weighting and auditable safety overrides.
    """

    @staticmethod
    def classify_risk_tier(score: float) -> str:
        """Map normalized [0.0, 1.0] score to project risk tier."""
        if score >= FusionPolicyConfig.TIER_CRITICAL_MIN:
            return "CRITICAL"
        elif score >= FusionPolicyConfig.TIER_MODERATE_MAX:
            return "HIGH"
        elif score >= FusionPolicyConfig.TIER_LOW_MAX:
            return "MODERATE"
        else:
            return "LOW"

    @classmethod
    def fuse_evidence(
        cls,
        spatial_pred: Dict[str, Any],
        temporal_analysis: Optional[Dict[str, Any]] = None,
        visual_analysis: Optional[Dict[str, Any]] = None,
        location_meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Pure deterministic multi-modal fusion combining pre-computed evidence streams.
        """
        explanations: List[str] = []
        decision_basis: List[str] = []
        overrides_triggered: List[Dict[str, Any]] = []

        # -------------------------------------------------------------
        # 1. STREAM 1: SPATIAL RISK (PHASE 1)
        # -------------------------------------------------------------
        spatial_available = True
        spatial_prob = float(spatial_pred.get("risk_probability", 0.0))
        spatial_score_norm = min(1.0, max(0.0, spatial_prob))
        spatial_model_meta = spatial_pred.get("model_metadata", {})
        active_model = spatial_model_meta.get("active_model", "LightGBM Classifier")
        standby_model = spatial_model_meta.get("standby_model", "XGBoost Classifier")
        ensemble_agreement = spatial_model_meta.get("ensemble_agreement_pct", 100.0)

        shap_info = spatial_pred.get("explainability", {}).get("top_factors", [])
        top_factor_names = [f["feature"] for f in shap_info[:2]] if shap_info else []

        if top_factor_names:
            explanations.append(
                f"Spatial model ({active_model}) evaluates terrain/weather risk at {spatial_score_norm:.2f} "
                f"(primary drivers: {', '.join(top_factor_names)})."
            )
        else:
            explanations.append(f"Spatial model evaluates baseline terrain hazard at {spatial_score_norm:.2f}.")

        # -------------------------------------------------------------
        # 2. STREAM 2: TEMPORAL SENSOR RISK (PHASE 2)
        # -------------------------------------------------------------
        temporal_available = False
        temporal_sufficiency = "NOT_PROVIDED"
        temporal_score_norm = 0.0
        raw_temporal_score = 0.0
        temporal_trend = "UNKNOWN"
        temporal_metrics = {}

        if temporal_analysis:
            temporal_sufficiency = temporal_analysis.get("data_sufficiency", "INSUFFICIENT")
            temporal_trend = temporal_analysis.get("trend", "UNKNOWN")
            raw_temporal_score = float(temporal_analysis.get("temporal_risk_score", 0.0))
            temporal_metrics = temporal_analysis.get("sensor_factors", {})

            if temporal_sufficiency in ["SUFFICIENT", "PARTIAL"]:
                temporal_available = True
                temporal_score_norm = min(1.0, max(0.0, raw_temporal_score / 100.0))

                trend_desc = f"Temporal telemetry indicates {temporal_trend} risk ({temporal_score_norm:.2f})."
                sm_rate = temporal_metrics.get("soil_moisture", {}).get("rate_per_hr", 0.0)
                p_rate = temporal_metrics.get("pore_pressure", {}).get("rate_per_hr", 0.0)
                if sm_rate > 0.5:
                    trend_desc += f" Soil wetting rate: +{sm_rate:.2f} %/hr."
                if p_rate > 0.3:
                    trend_desc += f" Pore pressure rising: +{p_rate:.2f} kPa/hr."
                explanations.append(trend_desc)
            else:
                explanations.append(
                    "Temporal telemetry was insufficient (requires >= 2 readings across time window); "
                    "relying on spatial terrain and weather baseline."
                )
        else:
            explanations.append("No IoT sensor telemetry available for this location.")

        # -------------------------------------------------------------
        # 3. STREAM 3: VISUAL EVIDENCE (PHASE 3)
        # -------------------------------------------------------------
        visual_available = False
        visual_localized = False
        visual_score_norm = 0.0
        visual_hazard_type = "none"
        visual_strength = "NONE"
        visual_status = "NOT_PROVIDED"
        visual_trained = False
        visual_confidence = None

        if visual_analysis:
            visual_status = visual_analysis.get("scientific_status", "HEURISTIC_NOT_VALIDATED")
            visual_trained = visual_analysis.get("trained_classifier", False)
            visual_confidence = visual_analysis.get("confidence")  # MUST remain None if uncalibrated
            visual_hazard_type = visual_analysis.get("hazard_type", "unclassified")
            visual_strength = visual_analysis.get("evidence_strength", "LOW")
            hazard_detected = visual_analysis.get("hazard_detected", False)

            # Check geographic localization
            st_lat = location_meta.get("latitude") if location_meta else None
            st_lon = location_meta.get("longitude") if location_meta else None
            st_name = location_meta.get("name") if location_meta else None

            is_loc, loc_reason, _ = check_visual_localization(visual_analysis, st_lat, st_lon, st_name)

            if is_loc:
                visual_localized = True
                if visual_status != "REJECTED_QUALITY_FAILURE":
                    visual_available = True
                    # Map evidence strength to operational policy score
                    if not hazard_detected:
                        visual_score_norm = FusionPolicyConfig.VISUAL_SCORE_STABLE
                    elif visual_strength == "HIGH":
                        visual_score_norm = FusionPolicyConfig.VISUAL_SCORE_HIGH
                    elif visual_strength == "MODERATE":
                        visual_score_norm = FusionPolicyConfig.VISUAL_SCORE_MODERATE
                    else:
                        visual_score_norm = FusionPolicyConfig.VISUAL_SCORE_LOW

                    explanations.append(
                        f"Field image contains {visual_strength} visual evidence of {visual_hazard_type} ({visual_score_norm:.2f})."
                    )
                    if not visual_trained:
                        explanations.append("Visual evidence is heuristic and not produced by a trained classifier.")
                else:
                    explanations.append(f"Visual evidence rejected: {visual_analysis.get('notes', 'Quality check failed')}.")
            else:
                explanations.append(f"Visual evidence ignored: {loc_reason}")

        # -------------------------------------------------------------
        # 4. ADAPTIVE WEIGHT REBALANCING
        # -------------------------------------------------------------
        if temporal_available and visual_available:
            w_spatial = FusionPolicyConfig.WEIGHT_SPATIAL_DEFAULT
            w_temporal = FusionPolicyConfig.WEIGHT_TEMPORAL_DEFAULT
            w_visual = FusionPolicyConfig.WEIGHT_VISUAL_DEFAULT
            basis_str = "Tri-modal fusion applied: Spatial 50%, Temporal 35%, Visual 15%."
        elif temporal_available and not visual_available:
            w_spatial = FusionPolicyConfig.WEIGHT_SPATIAL_NO_VISUAL
            w_temporal = FusionPolicyConfig.WEIGHT_TEMPORAL_NO_VISUAL
            w_visual = 0.0
            basis_str = "Dual-modal fusion applied: Spatial 60%, Temporal 40% (no localized visual evidence)."
        elif not temporal_available and visual_available:
            w_spatial = FusionPolicyConfig.WEIGHT_SPATIAL_NO_TEMPORAL
            w_temporal = 0.0
            w_visual = FusionPolicyConfig.WEIGHT_VISUAL_NO_TEMPORAL
            basis_str = "Dual-modal fusion applied: Spatial 80%, Visual 20% (temporal telemetry insufficient)."
        else:
            w_spatial = FusionPolicyConfig.WEIGHT_SPATIAL_ONLY
            w_temporal = 0.0
            w_visual = 0.0
            basis_str = "Single-modal assessment: Spatial 100% (temporal telemetry and visual evidence unavailable)."

        decision_basis.append(basis_str)

        # Compute Base Weighted Fused Score
        raw_fused_score = (
            (w_spatial * spatial_score_norm)
            + (w_temporal * temporal_score_norm)
            + (w_visual * visual_score_norm)
        )
        calculated_fused_score = round(min(1.0, max(0.0, raw_fused_score)), 3)

        # -------------------------------------------------------------
        # 5. SAFETY OVERRIDE EVALUATION
        # Transparent rule checks for critical geotechnical conditions
        # -------------------------------------------------------------
        # Rule 1: Critical Pore Water Pressure
        if temporal_available:
            p_val = float(temporal_metrics.get("pore_pressure", {}).get("current", 0.0) or 0.0)
            if p_val >= FusionPolicyConfig.OVERRIDE_PORE_PRESSURE_KPA:
                overrides_triggered.append({
                    "rule_id": "CRITICAL_PORE_PRESSURE_OVERRIDE",
                    "override_reason": f"Pore pressure ({p_val:.1f} kPa) exceeded critical operational policy threshold ({FusionPolicyConfig.OVERRIDE_PORE_PRESSURE_KPA} kPa).",
                    "measured_value": p_val,
                    "threshold": FusionPolicyConfig.OVERRIDE_PORE_PRESSURE_KPA,
                    "provenance": "Operational Safety Policy (Category C)"
                })

            # Rule 2: Critical Dynamic Vibration Spike or Anomaly
            vib_val = float(temporal_metrics.get("vibration", {}).get("current", 0.0) or 0.0)
            vib_ratio = float(temporal_metrics.get("vibration", {}).get("anomaly_ratio", 1.0) or 1.0)
            if vib_val >= FusionPolicyConfig.OVERRIDE_VIBRATION_SPIKE_G:
                overrides_triggered.append({
                    "rule_id": "CRITICAL_VIBRATION_SPIKE_OVERRIDE",
                    "override_reason": f"Ground vibration spike ({vib_val:.3f} g) exceeded critical shock threshold ({FusionPolicyConfig.OVERRIDE_VIBRATION_SPIKE_G} g).",
                    "measured_value": vib_val,
                    "threshold": FusionPolicyConfig.OVERRIDE_VIBRATION_SPIKE_G,
                    "provenance": "Operational Safety Policy (Category C)"
                })
            elif vib_ratio >= FusionPolicyConfig.OVERRIDE_VIBRATION_RATIO:
                overrides_triggered.append({
                    "rule_id": "CRITICAL_VIBRATION_RATIO_OVERRIDE",
                    "override_reason": f"Ground vibration ratio ({vib_ratio:.1f}x) exceeded baseline anomaly threshold ({FusionPolicyConfig.OVERRIDE_VIBRATION_RATIO}x).",
                    "measured_value": vib_ratio,
                    "threshold": FusionPolicyConfig.OVERRIDE_VIBRATION_RATIO,
                    "provenance": "Operational Safety Policy (Category C)"
                })

            # Rule 3: Extreme Temporal Acceleration
            if raw_temporal_score >= FusionPolicyConfig.OVERRIDE_TEMPORAL_SCORE_CRITICAL:
                overrides_triggered.append({
                    "rule_id": "CRITICAL_TEMPORAL_ACCELERATION_OVERRIDE",
                    "override_reason": f"Temporal hazard score ({raw_temporal_score:.1f}) reached extreme saturation/pressure surge threshold ({FusionPolicyConfig.OVERRIDE_TEMPORAL_SCORE_CRITICAL}).",
                    "measured_value": raw_temporal_score,
                    "threshold": FusionPolicyConfig.OVERRIDE_TEMPORAL_SCORE_CRITICAL,
                    "provenance": "Operational Safety Policy (Category C)"
                })

        # Rule 4: Extreme Spatial Probability
        if spatial_prob >= FusionPolicyConfig.OVERRIDE_SPATIAL_PROB_CRITICAL:
            overrides_triggered.append({
                "rule_id": "CRITICAL_SPATIAL_RISK_OVERRIDE",
                "override_reason": f"Spatial ML model predicted extreme hazard probability ({spatial_prob:.2f} >= {FusionPolicyConfig.OVERRIDE_SPATIAL_PROB_CRITICAL}).",
                "measured_value": spatial_prob,
                "threshold": FusionPolicyConfig.OVERRIDE_SPATIAL_PROB_CRITICAL,
                "provenance": "Operational Safety Policy (Category C)"
            })

        # Rule 5: Severe Localized Visual Debris
        if visual_available and visual_hazard_type == "landslide_debris" and visual_strength == "HIGH":
            overrides_triggered.append({
                "rule_id": "CRITICAL_VISUAL_DEBRIS_OVERRIDE",
                "override_reason": "High-strength visual evidence of active landslide debris confirmed in field photo.",
                "measured_value": visual_strength,
                "threshold": "HIGH landslide_debris",
                "provenance": "Operational Safety Policy (Category C)"
            })

        # Resolve Final Score and Risk Tier
        has_override = len(overrides_triggered) > 0
        if has_override:
            final_score = max(calculated_fused_score, FusionPolicyConfig.OVERRIDE_MIN_CRITICAL_SCORE)
            risk_tier = "CRITICAL"
            override_names = [o["rule_id"] for o in overrides_triggered]
            decision_basis.append(
                f"SAFETY OVERRIDE TRIGGERED: Tier elevated to CRITICAL by [{', '.join(override_names)}]. "
                f"Score adjusted from {calculated_fused_score:.3f} to {final_score:.3f}."
            )
        else:
            final_score = calculated_fused_score
            risk_tier = cls.classify_risk_tier(final_score)
            decision_basis.append(f"Calculated fused score: {final_score:.3f} (Tier: {risk_tier}). No safety override triggered.")

        # Determine overall confidence status
        if spatial_available and temporal_available and visual_available:
            confidence_status = "TRI_MODAL_COMPLETE"
        elif spatial_available and temporal_available:
            confidence_status = "SPATIAL_TEMPORAL_CONVERGENT"
        elif spatial_available and visual_available:
            confidence_status = "SPATIAL_VISUAL_PARTIAL"
        else:
            confidence_status = "SPATIAL_TERRAIN_ONLY"

        return {
            "fused_risk_score": final_score,
            "final_score": final_score,
            "calculated_fused_score": calculated_fused_score,
            "risk_tier": risk_tier,
            "risk_level": risk_tier,                   # Backward compatibility alias
            "components": {
                "spatial": {
                    "score": round(spatial_score_norm, 3),
                    "raw_probability": spatial_prob,
                    "raw_risk_score": int(spatial_pred.get("risk_score", 0)),
                    "available": spatial_available,
                    "active_model": active_model,
                    "standby_model": standby_model,
                    "ensemble_agreement_pct": ensemble_agreement,
                    "top_shap_factors": shap_info
                },
                "temporal": {
                    "score": round(temporal_score_norm, 3),
                    "raw_temporal_score": raw_temporal_score,
                    "available": temporal_available,
                    "data_sufficiency": temporal_sufficiency,
                    "trend": temporal_trend,
                    "metrics": temporal_metrics
                },
                "visual": {
                    "score": round(visual_score_norm, 3),
                    "available": visual_available,
                    "localized": visual_localized,
                    "hazard_detected": visual_analysis.get("hazard_detected", False) if visual_analysis else False,
                    "hazard_type": visual_hazard_type,
                    "evidence_strength": visual_strength,
                    "scientific_status": visual_status,
                    "trained_classifier": visual_trained,
                    "confidence": visual_confidence     # Strictly None if uncalibrated
                }
            },
            "weights_applied": {
                "spatial": w_spatial,
                "temporal": w_temporal,
                "visual": w_visual
            },
            "overrides": {
                "triggered": has_override,
                "rules": overrides_triggered
            },
            "confidence_status": confidence_status,
            "explanation": explanations,
            "decision_basis": decision_basis
        }

    @classmethod
    def fuse_location_risk(
        cls,
        db: Session,
        location_identifier: str,
        visual_evidence: Optional[Dict[str, Any]] = None,
        reference_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate multi-modal risk fusion for a registered NER location by querying
        the database for spatial attributes, temporal telemetry, and recent field photos.
        """
        clean_id = location_identifier.strip()
        loc = (
            db.query(Location)
            .filter((Location.id == clean_id) | (Location.name.ilike(f"%{clean_id}%")))
            .first()
        )
        if not loc:
            loc = db.query(Location).first()
            if not loc:
                raise ValueError(f"No monitored locations registered in database matching '{location_identifier}'.")

        # 1. Compute Spatial Risk from Phase 1
        spatial_pred = ml_engine.predict({
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "state": loc.state,
            "district": loc.district
        })

        # 2. Compute Temporal Risk from Phase 2
        sensor_id = resolve_station_sensor_id(db, loc.name)
        temporal_analysis = None
        if sensor_id:
            temporal_analysis = temporal_engine.analyze_station_temporal_risk(
                db, sensor_id, reference_time=reference_time
            )

        # 3. Resolve Visual Evidence from Phase 3 if not provided
        resolved_visual = visual_evidence
        if resolved_visual is None:
            # Query the most recent FieldReport associated with this location that contains an image
            recent_report = (
                db.query(FieldReport)
                .filter(
                    (FieldReport.location_name.ilike(f"%{loc.name}%")) |
                    (FieldReport.state == loc.state)
                )
                .filter(FieldReport.media_path.isnot(None))
                .order_by(FieldReport.created_at.desc())
                .first()
            )
            if recent_report and recent_report.media_path and os.path.exists(recent_report.media_path):
                resolved_visual = analyze_field_image(recent_report.media_path)
                resolved_visual["latitude"] = recent_report.latitude
                resolved_visual["longitude"] = recent_report.longitude
                resolved_visual["location_name"] = recent_report.location_name

        location_meta = {
            "id": loc.id,
            "name": loc.name,
            "state": loc.state,
            "district": loc.district,
            "latitude": loc.latitude,
            "longitude": loc.longitude
        }

        # 4. Fuse All Streams
        fused = cls.fuse_evidence(
            spatial_pred=spatial_pred,
            temporal_analysis=temporal_analysis,
            visual_analysis=resolved_visual,
            location_meta=location_meta
        )
        fused["location"] = location_meta
        return fused


fusion_engine = RiskFusionEngine()
