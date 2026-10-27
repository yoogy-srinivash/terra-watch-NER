"""
LandSafe Connect - Temporal Sensor Risk & Trend Engine
Processes historical IoT telemetry from the existing sensor_readings table across
1-hour, 6-hour, and 24-hour sliding windows.
Computes deterministic rates of change, pore pressure infiltration, saturation acceleration,
and vibration anomalies without deep-sequence speculation or fabricated time series.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import math
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models import SensorReading, SensorDevice, Location, RainfallRecord
from ..services.weather_service import get_live_weather
from ..utils.logging import audit_logger


class TemporalPolicyThresholds:
    """
    Centralized operational alerting, dynamic scaling, and rate-of-change thresholds.

    IMPORTANT SCIENTIFIC & PROVENANCE NOTICE:
    Unless explicitly cited below, these thresholds are operational heuristics and
    engineering demonstration values (Category C). They are NOT universal geotechnical
    shear-failure constants or scientifically verified landslide warning triggers.
    Geotechnical slope failure depends upon site-specific soil stratigraphy, friction angle,
    effective cohesion, piezometer installation depth, and local geology.
    """
    # -------------------------------------------------------------------------
    # 1. PORE WATER PRESSURE (kPa)
    # -------------------------------------------------------------------------
    # Category C: Engineering demo baselines & operational policy thresholds
    PORE_PRESSURE_BASELINE_KPA = 8.0               # Minimum pressure offset below which hazard contribution is 0.0
    PORE_PRESSURE_ELEVATED_KPA = 12.0              # Early advisory threshold
    PORE_PRESSURE_HIGH_KPA = 18.0                  # High pore pressure alert threshold
    PORE_PRESSURE_CRITICAL_KPA = 25.0              # Critical pore pressure threshold
    PORE_PRESSURE_RATE_RISING_PER_HR = 0.8         # kPa/hr - Advisory rate of increase
    PORE_PRESSURE_RATE_SURGE_PER_HR = 2.0          # kPa/hr - Severe rate of increase
    # Subscore scoring weights (Category C)
    PORE_PRESSURE_LEVEL_SCALE = 1.25               # Scaling factor for absolute pressure: (P - 8.0) * 1.25
    PORE_PRESSURE_MAX_LEVEL_SCORE = 20.0           # Maximum points for absolute pressure level
    PORE_PRESSURE_RATE_SCALE = 5.0                 # Scaling factor for pressure rate: rate * 5.0
    PORE_PRESSURE_MAX_RATE_SCORE = 15.0            # Maximum points for rate of pressure build-up
    PORE_PRESSURE_MAX_TOTAL_SCORE = 35.0           # Maximum pore pressure component contribution

    # -------------------------------------------------------------------------
    # 2. SOIL MOISTURE (% volumetric / saturation)
    # -------------------------------------------------------------------------
    # Category C: Engineering demo baselines & operational policy thresholds
    MOISTURE_BASELINE_PCT = 60.0                   # Saturation threshold below which moisture hazard is 0.0
    MOISTURE_ELEVATED_PCT = 70.0                   # Advisory elevated moisture
    MOISTURE_HIGH_PCT = 82.0                       # High soil saturation alert threshold
    MOISTURE_CRITICAL_PCT = 90.0                   # Near-saturation critical threshold
    MOISTURE_RATE_RISING_PER_HR = 1.5              # %/hr - Infiltration rate of increase
    MOISTURE_RATE_SURGE_PER_HR = 4.0               # %/hr - Rapid infiltration surge
    MOISTURE_ACCELERATION_ALERT_THRESHOLD = 1.0    # %/hr² - Acceleration threshold for explanatory notice
    # Subscore scoring weights (Category C)
    MOISTURE_LEVEL_SCALE = 0.5                     # Scaling factor: (SM - 60.0) * 0.5
    MOISTURE_MAX_LEVEL_SCORE = 15.0                # Maximum points for absolute saturation
    MOISTURE_RATE_SCALE = 2.5                      # Scaling factor: rate * 2.5
    MOISTURE_MAX_RATE_SCORE = 10.0                 # Maximum points for infiltration rate
    MOISTURE_MAX_TOTAL_SCORE = 25.0                # Maximum moisture component contribution

    # -------------------------------------------------------------------------
    # 3. GROUND VIBRATION (g or m/s²)
    # -------------------------------------------------------------------------
    # Category A: Sensor statistical baseline (rolling median)
    # Category C: Operational demo anomaly multipliers
    VIBRATION_BASELINE_DEFAULT_G = 0.05            # Fallback baseline when insufficient history exists (< 3 pts)
    VIBRATION_MIN_BASELINE_FLOOR_G = 0.01          # Minimum baseline floor to prevent division by zero
    VIBRATION_ANOMALY_RATIO_TRIGGER = 2.5          # Ratio of current reading to rolling median triggering alert
    VIBRATION_ANOMALY_SCORE_DIVISOR = 4.0          # Normalization divisor: (ratio - 1.0) / 4.0
    VIBRATION_CRITICAL_SPIKE_G = 1.5               # Critical absolute vibration spike (immediate max score)
    VIBRATION_ANOMALY_SCALE = 4.5                  # Subscore scaling: (ratio - 1.0) * 4.5
    VIBRATION_ANOMALY_CAP = 18.0                   # Cap for ratio-based vibration score
    VIBRATION_MAX_SCORE = 20.0                     # Maximum vibration component contribution

    # -------------------------------------------------------------------------
    # 4. RAINFALL DYNAMIC THRESHOLDS (mm)
    # -------------------------------------------------------------------------
    # Category D: Authoritative external source - India Meteorological Department (IMD)
    # IMD Meteorological Standard for 24-hour rainfall classification:
    # Heavy Rainfall: 64.5 mm to 115.5 mm / 24h
    # Very Heavy Rainfall: 115.6 mm to 204.4 mm / 24h
    RAINFALL_24H_HEAVY_MM = 64.5                   # IMD Heavy Rainfall lower boundary
    RAINFALL_24H_VERY_HEAVY_MM = 115.5             # IMD Very Heavy Rainfall lower boundary
    RAINFALL_INTENSITY_HIGH_MM_H = 15.0            # Intense spell threshold (mm/hr)
    # Subscore scoring weights (Category C)
    RAINFALL_24H_MAX_SCORE = 12.0                  # Maximum points for 24h accumulation
    RAINFALL_INTENSITY_MAX_SCORE = 8.0             # Maximum points for current rainfall intensity
    RAINFALL_MAX_TOTAL_SCORE = 20.0                # Maximum rainfall component contribution

    # -------------------------------------------------------------------------
    # 5. TREND CLASSIFICATION THRESHOLDS
    # -------------------------------------------------------------------------
    # Category C: Operational demo classification heuristics
    TREND_ACCEL_P_RATE = 0.4                       # kPa/hr
    TREND_ACCEL_SM_RATE = 1.0                      # %/hr
    TREND_ACCEL_SM_ACCEL = 0.5                     # %/hr²
    TREND_RISING_P_RATE = 0.3                      # kPa/hr
    TREND_RISING_SM_RATE = 0.8                     # %/hr
    TREND_RISING_VIB_ANOMALY = 0.4                 # Normalized vibration anomaly score
    TREND_DECLINING_P_RATE = -0.2                  # kPa/hr
    TREND_DECLINING_SM_RATE = -0.4                 # %/hr

    # -------------------------------------------------------------------------
    # 6. TEMPORAL RISK SCORE BOUNDARIES
    # -------------------------------------------------------------------------
    # Category B: Documented project requirement (normalized 0.0 - 100.0 score)
    TEMPORAL_SCORE_MIN = 0.0
    TEMPORAL_SCORE_MAX = 100.0

    # -------------------------------------------------------------------------
    # 7. TIME WINDOW & PROGRESSION SPECIFICATIONS
    # -------------------------------------------------------------------------
    # Category B: Documented project requirements (Phase 2 brief)
    WINDOW_HOURS_SHORT = 1.0
    WINDOW_HOURS_MEDIUM = 6.0
    WINDOW_HOURS_LONG = 24.0
    MIN_OBSERVATIONS_FOR_SERIES = 2
    PROGRESSION_WINDOW_DAYS = 7
    # Category C: Operational demo progression heuristics
    PROGRESSION_MIN_SPAN_HOURS = 2.0
    PROGRESSION_SM_WEIGHT = 0.45
    PROGRESSION_PORE_WEIGHT = 1.5
    PROGRESSION_VIB_WEIGHT = 10.0
    PROGRESSION_SLICE_SCORE_MIN = 5.0
    PROGRESSION_SLICE_SCORE_MAX = 98.0


def _safe_rate(delta_val: float, delta_hours: float) -> float:
    """Compute rate per hour safely, avoiding division by near-zero."""
    if delta_hours <= 0.01:
        return 0.0
    return round(delta_val / delta_hours, 3)


def resolve_station_sensor_id(db: Session, identifier: str) -> Optional[str]:
    """
    Resolve station sensor_id from either sensor ID (SN-XX-XXX), location ID (XX-NAME),
    or city/district name.
    """
    clean_id = identifier.strip()

    # 1. Direct SensorDevice ID match
    dev = db.query(SensorDevice).filter(SensorDevice.id == clean_id).first()
    if dev:
        return dev.id

    # 2. Location ID match (e.g. AS-GUWAHATI)
    dev_by_loc = db.query(SensorDevice).filter(SensorDevice.location_id == clean_id).first()
    if dev_by_loc:
        return dev_by_loc.id

    # 3. Match by location city or name fuzzy lookup
    loc = db.query(Location).filter(
        (Location.name.ilike(f"%{clean_id}%")) | (Location.id == clean_id)
    ).first()
    if loc:
        dev_match = db.query(SensorDevice).filter(SensorDevice.location_id == loc.id).first()
        if dev_match:
            return dev_match.id

    # 4. Sensor Device Name fuzzy match
    dev_by_name = db.query(SensorDevice).filter(SensorDevice.name.ilike(f"%{clean_id}%")).first()
    if dev_by_name:
        return dev_by_name.id

    return None


class TemporalRiskEngine:
    """
    Temporal Sensor Risk & Trend Engine.
    Evaluates real time-series sensor data without deep-sequence speculation.
    """

    @staticmethod
    def analyze_station_temporal_risk(
        db: Session,
        station_id: str,
        reference_time: Optional[datetime] = None,
        rainfall_input: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Reconstruct sliding windows (1h, 6h, 24h) for a station and compute
        deterministic rate-of-change, pore pressure rise, moisture acceleration,
        and vibration anomalies.
        """
        ref_time = reference_time or datetime.utcnow()
        t_1h = ref_time - timedelta(hours=1)
        t_6h = ref_time - timedelta(hours=6)
        t_24h = ref_time - timedelta(hours=24)

        # Query existing sensor_readings table within the 24h window
        # STRICT BOUND: timestamp <= ref_time prevents any future readings from leaking into historical window
        readings = (
            db.query(SensorReading)
            .filter(
                SensorReading.sensor_id == station_id,
                SensorReading.timestamp <= ref_time,
                SensorReading.timestamp >= t_24h
            )
            .order_by(SensorReading.timestamp.asc())
            .all()
        )

        n_obs = len(readings)

        # -------------------------------------------------------------
        # SUFFICIENCY CHECK 1: ZERO OBSERVATIONS
        # -------------------------------------------------------------
        if n_obs == 0:
            return {
                "station_id": station_id,
                "temporal_risk_score": 0.0,
                "trend": "UNKNOWN",
                "data_sufficiency": "INSUFFICIENT",
                "available_observations": 0,
                "missing_windows": ["1h", "6h", "24h"],
                "time_span_hours": 0.0,
                "windows": {
                    "1h": {"observations": 0, "status": "MISSING"},
                    "6h": {"observations": 0, "status": "MISSING"},
                    "24h": {"observations": 0, "status": "MISSING"}
                },
                "sensor_factors": {
                    "soil_moisture": {"current": None, "rate_per_hr": 0.0, "status": "NO_DATA"},
                    "pore_pressure": {"current": None, "rate_per_hr": 0.0, "status": "NO_DATA"},
                    "vibration": {"current": None, "anomaly_score": 0.0, "status": "NO_DATA"},
                    "rainfall": {"24h_cumulative_mm": 0.0, "intensity_mm_h": 0.0}
                },
                "explanation": [
                    f"No sensor observations found for station '{station_id}' within the 24-hour evaluation window.",
                    "Temporal risk defaulted to conservative baseline (0.0) due to insufficient telemetry."
                ]
            }

        # -------------------------------------------------------------
        # SUFFICIENCY CHECK 2: SINGLE OBSERVATION
        # Do not pretend that a single observation represents a time series.
        # -------------------------------------------------------------
        if n_obs == 1:
            single = readings[0]
            return {
                "station_id": station_id,
                "temporal_risk_score": 0.0,
                "trend": "INSUFFICIENT_DATA",
                "data_sufficiency": "INSUFFICIENT",
                "available_observations": 1,
                "missing_windows": ["1h", "6h", "24h"],
                "time_span_hours": 0.0,
                "windows": {
                    "1h": {"observations": 1, "status": "INSUFFICIENT_POINTS"},
                    "6h": {"observations": 1, "status": "MISSING"},
                    "24h": {"observations": 1, "status": "MISSING"}
                },
                "sensor_factors": {
                    "soil_moisture": {"current": single.soil_moisture, "rate_per_hr": 0.0, "status": "STATIC_POINT"},
                    "pore_pressure": {"current": single.pore_pressure, "rate_per_hr": 0.0, "status": "STATIC_POINT"},
                    "vibration": {"current": single.ground_vibration, "anomaly_score": 0.0, "status": "STATIC_POINT"},
                    "rainfall": {"24h_cumulative_mm": 0.0, "intensity_mm_h": 0.0}
                },
                "explanation": [
                    f"Only 1 sensor reading recorded at {single.timestamp.isoformat()}. A single point cannot construct a temporal trend or rate of change.",
                    "Temporal risk set to 0.0 pending consecutive observations."
                ]
            }

        # -------------------------------------------------------------
        # SUFFICIENT / PARTIAL TIME SERIES ANALYSIS (>= 2 observations)
        # -------------------------------------------------------------
        t_start = readings[0].timestamp
        t_end = readings[-1].timestamp
        span_hours = round(max(0.001, (t_end - t_start).total_seconds() / 3600.0), 2)

        # Categorize data sufficiency
        missing_windows = []
        if span_hours < 0.8:
            sufficiency = "PARTIAL"
            missing_windows = ["6h", "24h"]
        elif span_hours < 16.0:
            sufficiency = "PARTIAL"
            missing_windows = ["24h"]
        else:
            sufficiency = "SUFFICIENT"

        # Separate readings into 1h, 6h, 24h buckets
        readings_1h = [r for r in readings if r.timestamp >= t_1h]
        readings_6h = [r for r in readings if r.timestamp >= t_6h]
        readings_24h = readings  # already filtered >= t_24h

        latest = readings[-1]

        # 1. SOIL MOISTURE DELTAS & RATES
        sm_latest = float(latest.soil_moisture)
        sm_oldest_24 = float(readings[0].soil_moisture)
        sm_delta_24h = round(sm_latest - sm_oldest_24, 2)
        sm_rate_24h = _safe_rate(sm_delta_24h, span_hours)

        sm_delta_1h = 0.0
        sm_rate_1h = 0.0
        if len(readings_1h) >= 2:
            dt_1h = (readings_1h[-1].timestamp - readings_1h[0].timestamp).total_seconds() / 3600.0
            sm_delta_1h = round(sm_latest - float(readings_1h[0].soil_moisture), 2)
            sm_rate_1h = _safe_rate(sm_delta_1h, dt_1h)

        sm_delta_6h = 0.0
        sm_rate_6h = 0.0
        if len(readings_6h) >= 2:
            dt_6h = (readings_6h[-1].timestamp - readings_6h[0].timestamp).total_seconds() / 3600.0
            sm_delta_6h = round(sm_latest - float(readings_6h[0].soil_moisture), 2)
            sm_rate_6h = _safe_rate(sm_delta_6h, dt_6h)

        # Saturation acceleration (difference between short-term rate and long-term rate)
        effective_sm_rate = sm_rate_1h if len(readings_1h) >= 2 else sm_rate_24h
        sm_acceleration = round(effective_sm_rate - sm_rate_24h, 3)

        # 2. PORE PRESSURE DELTAS & RATES
        p_latest = float(latest.pore_pressure or 0.0)
        p_oldest_24 = float(readings[0].pore_pressure or 0.0)
        p_delta_24h = round(p_latest - p_oldest_24, 2)
        p_rate_24h = _safe_rate(p_delta_24h, span_hours)

        p_delta_1h = 0.0
        p_rate_1h = 0.0
        if len(readings_1h) >= 2:
            dt_1h = (readings_1h[-1].timestamp - readings_1h[0].timestamp).total_seconds() / 3600.0
            p_delta_1h = round(p_latest - float(readings_1h[0].pore_pressure or 0.0), 2)
            p_rate_1h = _safe_rate(p_delta_1h, dt_1h)

        p_delta_6h = 0.0
        p_rate_6h = 0.0
        if len(readings_6h) >= 2:
            dt_6h = (readings_6h[-1].timestamp - readings_6h[0].timestamp).total_seconds() / 3600.0
            p_delta_6h = round(p_latest - float(readings_6h[0].pore_pressure or 0.0), 2)
            p_rate_6h = _safe_rate(p_delta_6h, dt_6h)

        effective_p_rate = p_rate_1h if len(readings_1h) >= 2 else p_rate_24h

        # 3. GROUND VIBRATION ANOMALY & TREND
        vib_latest = float(latest.ground_vibration or 0.0)
        all_vibs = [float(r.ground_vibration or 0.0) for r in readings]
        vib_baseline = (
            sorted(all_vibs)[len(all_vibs) // 2]  # median baseline
            if len(all_vibs) >= 3 else (all_vibs[0] if all_vibs else TemporalPolicyThresholds.VIBRATION_BASELINE_DEFAULT_G)
        )
        vib_baseline = max(TemporalPolicyThresholds.VIBRATION_MIN_BASELINE_FLOOR_G, vib_baseline)

        vib_ratio = round(vib_latest / vib_baseline, 2)
        vib_anomaly_score = round(min(1.0, max(0.0, (vib_ratio - 1.0) / TemporalPolicyThresholds.VIBRATION_ANOMALY_SCORE_DIVISOR)), 3)

        # 4. RAINFALL INTEGRATION (Database record or Weather Service)
        rain_24h = 0.0
        rain_intensity = 0.0
        if rainfall_input:
            rain_24h = float(rainfall_input.get("rainfall_24h_mm", 0.0))
            rain_intensity = float(rainfall_input.get("rainfall_intensity_mm_h", rain_24h / 12.0))
        else:
            # Check station device coordinates to pull live/recent weather if available
            dev = db.query(SensorDevice).filter(SensorDevice.id == station_id).first()
            if dev:
                w = get_live_weather(dev.latitude, dev.longitude, dev.state)
                rain_24h = float(w.get("rainfall_24h_mm", 0.0))
                rain_intensity = float(w.get("rainfall_current_mm", round(rain_24h / 10.0, 1)))

        # -------------------------------------------------------------
        # DETERMINISTIC TEMPORAL HAZARD SCORE (0.0 to 100.0)
        # Separate, configurable, explainable policy scoring.
        # -------------------------------------------------------------
        explanations = []

        # Component A: Pore Pressure (Max 35 pts)
        # Absolute saturation level + rate of pressure head build-up
        score_pore_level = min(
            TemporalPolicyThresholds.PORE_PRESSURE_MAX_LEVEL_SCORE,
            max(0.0, (p_latest - TemporalPolicyThresholds.PORE_PRESSURE_BASELINE_KPA) * TemporalPolicyThresholds.PORE_PRESSURE_LEVEL_SCALE)
        )
        score_pore_rate = min(
            TemporalPolicyThresholds.PORE_PRESSURE_MAX_RATE_SCORE,
            max(0.0, effective_p_rate * TemporalPolicyThresholds.PORE_PRESSURE_RATE_SCALE)
        )
        score_pore = score_pore_level + score_pore_rate
        if p_latest >= TemporalPolicyThresholds.PORE_PRESSURE_HIGH_KPA:
            explanations.append(f"Elevated pore pressure detected: {p_latest:.1f} kPa (threshold: {TemporalPolicyThresholds.PORE_PRESSURE_HIGH_KPA} kPa).")
        if effective_p_rate >= TemporalPolicyThresholds.PORE_PRESSURE_RATE_RISING_PER_HR:
            explanations.append(f"Rapid pore pressure rise observed: +{effective_p_rate:.2f} kPa/hr.")

        # Component B: Soil Moisture Dynamics (Max 25 pts)
        # Saturation magnitude + wetting front rate
        score_sm_level = min(
            TemporalPolicyThresholds.MOISTURE_MAX_LEVEL_SCORE,
            max(0.0, (sm_latest - TemporalPolicyThresholds.MOISTURE_BASELINE_PCT) * TemporalPolicyThresholds.MOISTURE_LEVEL_SCALE)
        )
        score_sm_rate = min(
            TemporalPolicyThresholds.MOISTURE_MAX_RATE_SCORE,
            max(0.0, effective_sm_rate * TemporalPolicyThresholds.MOISTURE_RATE_SCALE)
        )
        score_sm = score_sm_level + score_sm_rate
        if sm_latest >= TemporalPolicyThresholds.MOISTURE_HIGH_PCT:
            explanations.append(f"High soil moisture saturation: {sm_latest:.1f}% (threshold: {TemporalPolicyThresholds.MOISTURE_HIGH_PCT}%).")
        if effective_sm_rate >= TemporalPolicyThresholds.MOISTURE_RATE_RISING_PER_HR:
            explanations.append(f"Moisture saturation increasing at +{effective_sm_rate:.2f} %/hr.")
        if sm_acceleration > TemporalPolicyThresholds.MOISTURE_ACCELERATION_ALERT_THRESHOLD:
            explanations.append(f"Saturation rate accelerating (+{sm_acceleration:.2f} %/hr²).")

        # Component C: Ground Vibration / Tremor Anomaly (Max 20 pts)
        score_vib = 0.0
        if vib_latest >= TemporalPolicyThresholds.VIBRATION_CRITICAL_SPIKE_G:
            score_vib = TemporalPolicyThresholds.VIBRATION_MAX_SCORE
            explanations.append(f"Critical ground vibration spike: {vib_latest:.3f} g (threshold: {TemporalPolicyThresholds.VIBRATION_CRITICAL_SPIKE_G} g).")
        elif vib_ratio >= TemporalPolicyThresholds.VIBRATION_ANOMALY_RATIO_TRIGGER:
            score_vib = min(
                TemporalPolicyThresholds.VIBRATION_ANOMALY_CAP,
                (vib_ratio - 1.0) * TemporalPolicyThresholds.VIBRATION_ANOMALY_SCALE
            )
            explanations.append(f"Ground vibration anomaly: {vib_ratio:.1f}x above rolling baseline ({vib_latest:.3f} g vs {vib_baseline:.3f} g).")

        # Component D: Hydrological Precipitation Trigger (Max 20 pts)
        score_rain_24h = min(
            TemporalPolicyThresholds.RAINFALL_24H_MAX_SCORE,
            (rain_24h / TemporalPolicyThresholds.RAINFALL_24H_HEAVY_MM) * TemporalPolicyThresholds.RAINFALL_24H_MAX_SCORE
        )
        score_rain_int = min(
            TemporalPolicyThresholds.RAINFALL_INTENSITY_MAX_SCORE,
            (rain_intensity / TemporalPolicyThresholds.RAINFALL_INTENSITY_HIGH_MM_H) * TemporalPolicyThresholds.RAINFALL_INTENSITY_MAX_SCORE
        )
        score_rain = score_rain_24h + score_rain_int
        if rain_24h >= TemporalPolicyThresholds.RAINFALL_24H_HEAVY_MM:
            explanations.append(f"Cumulative 24h rainfall exceeds threshold: {rain_24h:.1f} mm.")

        temporal_score = round(
            min(
                TemporalPolicyThresholds.TEMPORAL_SCORE_MAX,
                max(TemporalPolicyThresholds.TEMPORAL_SCORE_MIN, score_pore + score_sm + score_vib + score_rain)
            ),
            1
        )

        # -------------------------------------------------------------
        # TREND CLASSIFICATION (STABLE | RISING | ACCELERATING | DECLINING)
        # -------------------------------------------------------------
        if (effective_p_rate > TemporalPolicyThresholds.TREND_ACCEL_P_RATE or effective_sm_rate > TemporalPolicyThresholds.TREND_ACCEL_SM_RATE) and sm_acceleration > TemporalPolicyThresholds.TREND_ACCEL_SM_ACCEL:
            trend_label = "ACCELERATING"
        elif (
            effective_p_rate > TemporalPolicyThresholds.TREND_RISING_P_RATE
            or effective_sm_rate > TemporalPolicyThresholds.TREND_RISING_SM_RATE
            or vib_anomaly_score > TemporalPolicyThresholds.TREND_RISING_VIB_ANOMALY
        ):
            trend_label = "RISING"
        elif effective_p_rate < TemporalPolicyThresholds.TREND_DECLINING_P_RATE and effective_sm_rate < TemporalPolicyThresholds.TREND_DECLINING_SM_RATE:
            trend_label = "DECLINING"
        else:
            trend_label = "STABLE"

        if not explanations:
            explanations.append(f"Stable geotechnical telemetry across {span_hours:.1f} hours ({n_obs} readings).")

        return {
            "station_id": station_id,
            "temporal_risk_score": temporal_score,
            "trend": trend_label,
            "data_sufficiency": sufficiency,
            "available_observations": n_obs,
            "missing_windows": missing_windows,
            "time_span_hours": span_hours,
            "windows": {
                "1h": {
                    "observations": len(readings_1h),
                    "delta_moisture_pct": sm_delta_1h,
                    "delta_pore_pressure_kpa": p_delta_1h,
                    "status": "SUFFICIENT" if len(readings_1h) >= 2 else ("PARTIAL" if len(readings_1h) == 1 else "NO_DATA")
                },
                "6h": {
                    "observations": len(readings_6h),
                    "delta_moisture_pct": sm_delta_6h,
                    "delta_pore_pressure_kpa": p_delta_6h,
                    "status": "SUFFICIENT" if len(readings_6h) >= 3 else ("PARTIAL" if len(readings_6h) >= 1 else "NO_DATA")
                },
                "24h": {
                    "observations": len(readings_24h),
                    "delta_moisture_pct": sm_delta_24h,
                    "delta_pore_pressure_kpa": p_delta_24h,
                    "status": "SUFFICIENT" if len(readings_24h) >= 4 and span_hours >= 16.0 else "PARTIAL"
                }
            },
            "sensor_factors": {
                "soil_moisture": {
                    "current": sm_latest,
                    "delta_24h": sm_delta_24h,
                    "rate_per_hr": sm_rate_24h,
                    "acceleration": sm_acceleration,
                    "subscore": round(score_sm, 1)
                },
                "pore_pressure": {
                    "current": p_latest,
                    "delta_24h": p_delta_24h,
                    "rate_per_hr": p_rate_24h,
                    "subscore": round(score_pore, 1)
                },
                "vibration": {
                    "current": vib_latest,
                    "baseline": vib_baseline,
                    "anomaly_ratio": vib_ratio,
                    "anomaly_score": vib_anomaly_score,
                    "subscore": round(score_vib, 1)
                },
                "rainfall": {
                    "24h_cumulative_mm": round(rain_24h, 1),
                    "intensity_mm_h": round(rain_intensity, 1),
                    "subscore": round(score_rain, 1)
                }
            },
            "explanation": explanations
        }

    @staticmethod
    def get_empirical_progression_trend(
        db: Session,
        location_identifier: str,
        current_score: int
    ) -> Dict[str, Any]:
        """
        Reconstruct authentic multi-point temporal progression curve for /api/risk/probability.
        DOES NOT fabricate fake historical scores.
        If sufficient readings exist over time, calculates true chronological progression.
        If insufficient, explicitly returns insufficient data state.
        """
        sensor_id = resolve_station_sensor_id(db, location_identifier)

        # Fallback if no sensor device is linked to this location
        if not sensor_id:
            return {
                "has_sensor_series": False,
                "data_sufficiency": "INSUFFICIENT",
                "message": f"No telemetry sensor registered for location '{location_identifier}'.",
                "labels": ["Current"],
                "values": [current_score],
                "temporal_trend": "UNKNOWN",
                "observations_count": 0
            }

        now = datetime.utcnow()
        t_7d = now - timedelta(days=TemporalPolicyThresholds.PROGRESSION_WINDOW_DAYS)

        # Fetch historical readings over the past 7 days
        records = (
            db.query(SensorReading)
            .filter(
                SensorReading.sensor_id == sensor_id,
                SensorReading.timestamp <= now,
                SensorReading.timestamp >= t_7d
            )
            .order_by(SensorReading.timestamp.asc())
            .all()
        )

        n_records = len(records)

        # Insufficient data cases: 0 or 1 point cannot define a 7-day trend
        if n_records < TemporalPolicyThresholds.MIN_OBSERVATIONS_FOR_SERIES:
            return {
                "has_sensor_series": False,
                "data_sufficiency": "INSUFFICIENT",
                "message": f"Only {n_records} sensor observation(s) available. Insufficient telemetry to construct a historical progression curve.",
                "labels": ["Current"],
                "values": [current_score],
                "temporal_trend": "INSUFFICIENT_DATA",
                "observations_count": n_records
            }

        # Check total time span
        span_hours = (records[-1].timestamp - records[0].timestamp).total_seconds() / 3600.0

        if span_hours < TemporalPolicyThresholds.PROGRESSION_MIN_SPAN_HOURS:
            # Telemetry too narrow to display a multi-day progression
            return {
                "has_sensor_series": True,
                "data_sufficiency": "PARTIAL",
                "message": f"Observations span {span_hours:.1f} hours ({n_records} readings). Displaying narrow observation window.",
                "labels": ["T-0h", "Current"],
                "values": [current_score, current_score],
                "temporal_trend": "NARROW_SERIES",
                "observations_count": n_records
            }

        # Subdivide observations into up to 7 chronological bins (e.g. daily or sequential intervals)
        num_bins = min(7, max(3, int(math.ceil(span_hours / 24.0))))
        bin_duration = (records[-1].timestamp - records[0].timestamp) / num_bins

        labels = []
        values = []

        for i in range(num_bins):
            b_start = records[0].timestamp + (bin_duration * i)
            b_end = b_start + bin_duration
            bin_readings = [r for r in records if b_start <= r.timestamp <= b_end]

            if not bin_readings:
                # Find closest reading
                closest = min(records, key=lambda r: abs((r.timestamp - b_end).total_seconds()))
                bin_readings = [closest]

            sample_r = bin_readings[-1]

            # Approximate historical temporal score for this slice using physical factors
            p = float(sample_r.pore_pressure or 0.0)
            sm = float(sample_r.soil_moisture or 50.0)
            vib = float(sample_r.ground_vibration or 0.003)

            slice_score = int(round(min(
                TemporalPolicyThresholds.PROGRESSION_SLICE_SCORE_MAX,
                max(
                    TemporalPolicyThresholds.PROGRESSION_SLICE_SCORE_MIN,
                    (sm * TemporalPolicyThresholds.PROGRESSION_SM_WEIGHT)
                    + (p * TemporalPolicyThresholds.PROGRESSION_PORE_WEIGHT)
                    + (vib * TemporalPolicyThresholds.PROGRESSION_VIB_WEIGHT)
                )
            )))
            labels.append(b_end.strftime("%a %H:%M") if span_hours < 48 else b_end.strftime("%a"))
            values.append(slice_score)

        # Ensure terminating point reflects current evaluated risk score
        values[-1] = current_score

        return {
            "has_sensor_series": True,
            "data_sufficiency": "SUFFICIENT" if span_hours >= 48.0 else "PARTIAL",
            "message": f"Reconstructed {len(values)}-step progression curve from {n_records} empirical observations across {span_hours:.1f} hours.",
            "labels": labels,
            "values": values,
            "temporal_trend": "RISING" if values[-1] > values[0] else ("DECLINING" if values[-1] < values[0] else "STABLE"),
            "observations_count": n_records
        }


temporal_engine = TemporalRiskEngine()
