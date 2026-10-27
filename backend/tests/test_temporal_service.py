import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import SensorDevice, SensorReading, Location
from backend.app.services.temporal_service import temporal_engine, TemporalPolicyThresholds

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture(autouse=True)
def cleanup_test_data(db_session):
    # Setup test devices
    test_ids = ["TEST-SN-INSUF", "TEST-SN-STABLE", "TEST-SN-MOIST", "TEST-SN-PORE", "TEST-SN-VIB", "TEST-SN-COMBO", "TEST-SN-DECL", "TEST-SN-ISO-A", "TEST-SN-ISO-B", "TEST-SN-FUTURE"]
    for tid in test_ids:
        dev = db_session.query(SensorDevice).filter(SensorDevice.id == tid).first()
        if not dev:
            db_session.add(SensorDevice(id=tid, name=f"Device {tid}", state="Assam", latitude=26.14, longitude=91.73, status="Active"))
    db_session.commit()

    yield

    # Teardown test readings & devices
    db_session.query(SensorReading).filter(SensorReading.sensor_id.in_(test_ids)).delete(synchronize_session=False)
    db_session.query(SensorDevice).filter(SensorDevice.id.in_(test_ids)).delete(synchronize_session=False)
    db_session.commit()


def test_1_insufficient_historical_data_detected(db_session):
    """Test 1: Verify that 0 or 1 observation explicitly produces INSUFFICIENT data sufficiency."""
    station_id = "TEST-SN-INSUF"
    now = datetime.utcnow()

    # Case A: 0 observations
    res_zero = temporal_engine.analyze_station_temporal_risk(db_session, station_id, reference_time=now)
    assert res_zero["data_sufficiency"] == "INSUFFICIENT"
    assert res_zero["available_observations"] == 0
    assert res_zero["temporal_risk_score"] == 0.0
    assert "1h" in res_zero["missing_windows"]
    assert "6h" in res_zero["missing_windows"]
    assert "24h" in res_zero["missing_windows"]

    # Case B: Exactly 1 observation (cannot construct time series or rate of change)
    single_reading = SensorReading(
        sensor_id=station_id,
        soil_moisture=72.0,
        temperature=22.0,
        pore_pressure=14.0,
        ground_vibration=0.03,
        timestamp=now - timedelta(minutes=10)
    )
    db_session.add(single_reading)
    db_session.commit()

    res_one = temporal_engine.analyze_station_temporal_risk(db_session, station_id, reference_time=now)
    assert res_one["data_sufficiency"] == "INSUFFICIENT"
    assert res_one["available_observations"] == 1
    assert res_one["temporal_risk_score"] == 0.0
    assert res_one["trend"] == "INSUFFICIENT_DATA"
    assert any("single point cannot construct" in exp.lower() for exp in res_one["explanation"])


def test_2_stable_sensor_series_produces_stable_trend(db_session):
    """Test 2: A series with stationary values produces a STABLE trend and low temporal risk score."""
    station_id = "TEST-SN-STABLE"
    now = datetime.utcnow()

    # Insert 6 observations across 12 hours with stable values
    for i in range(6):
        t = now - timedelta(hours=(10 - i * 2))
        db_session.add(SensorReading(
            sensor_id=station_id,
            soil_moisture=52.0,
            temperature=21.0,
            pore_pressure=4.0,
            ground_vibration=0.02,
            timestamp=t
        ))
    db_session.commit()

    res = temporal_engine.analyze_station_temporal_risk(db_session, station_id, reference_time=now)
    assert res["data_sufficiency"] in ["PARTIAL", "SUFFICIENT"]
    assert res["trend"] == "STABLE"
    assert res["temporal_risk_score"] < 15.0
    assert abs(res["sensor_factors"]["soil_moisture"]["rate_per_hr"]) < 0.2
    assert abs(res["sensor_factors"]["pore_pressure"]["rate_per_hr"]) < 0.2


def test_3_increasing_soil_moisture_produces_rising_signal(db_session):
    """Test 3: Increasing soil moisture produces a RISING temporal signal and positive rate."""
    station_id = "TEST-SN-MOIST"
    now = datetime.utcnow()

    # Soil moisture rising from 50% to 86% over 8 hours (+4.5%/hr)
    for i, sm in enumerate([50.0, 58.0, 68.0, 78.0, 86.0]):
        t = now - timedelta(hours=(8 - i * 2))
        db_session.add(SensorReading(
            sensor_id=station_id,
            soil_moisture=sm,
            temperature=20.0,
            pore_pressure=5.0,
            ground_vibration=0.03,
            timestamp=t
        ))
    db_session.commit()

    res = temporal_engine.analyze_station_temporal_risk(db_session, station_id, reference_time=now)
    assert res["trend"] in ["RISING", "ACCELERATING"]
    assert res["sensor_factors"]["soil_moisture"]["rate_per_hr"] > 1.0
    assert res["sensor_factors"]["soil_moisture"]["delta_24h"] > 30.0
    assert res["temporal_risk_score"] > 15.0
    assert any("soil moisture" in exp.lower() for exp in res["explanation"])


def test_4_rapid_pore_pressure_increase_produces_stronger_signal(db_session):
    """Test 4: Rapid pore-pressure surge triggers high rate of change and elevated temporal score."""
    station_id = "TEST-SN-PORE"
    now = datetime.utcnow()

    # Pore pressure jumping from 3 kPa to 26 kPa over 4 hours (+5.75 kPa/hr)
    for i, p in enumerate([3.0, 8.0, 15.0, 26.0]):
        t = now - timedelta(hours=(4 - i))
        db_session.add(SensorReading(
            sensor_id=station_id,
            soil_moisture=70.0,
            temperature=21.0,
            pore_pressure=p,
            ground_vibration=0.04,
            timestamp=t
        ))
    db_session.commit()

    res = temporal_engine.analyze_station_temporal_risk(db_session, station_id, reference_time=now)
    assert res["trend"] in ["RISING", "ACCELERATING"]
    assert res["sensor_factors"]["pore_pressure"]["rate_per_hr"] > 2.0
    assert res["sensor_factors"]["pore_pressure"]["current"] >= 25.0
    assert res["temporal_risk_score"] >= 30.0
    assert any("pore pressure" in exp.lower() for exp in res["explanation"])


def test_5_vibration_anomaly_detected(db_session):
    """Test 5: Ground vibration spike above rolling baseline is flagged as an anomaly."""
    station_id = "TEST-SN-VIB"
    now = datetime.utcnow()

    # Low baseline readings of 0.02g, followed by sudden spike to 0.85g (>40x baseline)
    for i in range(5):
        t = now - timedelta(hours=(6 - i))
        db_session.add(SensorReading(
            sensor_id=station_id,
            soil_moisture=55.0,
            temperature=20.0,
            pore_pressure=4.0,
            ground_vibration=0.02,
            timestamp=t
        ))
    # Spike at current time
    db_session.add(SensorReading(
        sensor_id=station_id,
        soil_moisture=55.0,
        temperature=20.0,
        pore_pressure=4.0,
        ground_vibration=0.85,
        timestamp=now
    ))
    db_session.commit()

    res = temporal_engine.analyze_station_temporal_risk(db_session, station_id, reference_time=now)
    vib_data = res["sensor_factors"]["vibration"]
    assert vib_data["anomaly_ratio"] > 10.0
    assert vib_data["anomaly_score"] > 0.5
    assert any("vibration anomaly" in exp.lower() for exp in res["explanation"])


def test_6_combined_rainfall_moisture_pore_pressure_surge(db_session):
    """Test 6: Combined saturation, pressure head, and rain surge yields high temporal score."""
    station_id = "TEST-SN-COMBO"
    now = datetime.utcnow()

    # Severe compound storm infiltration
    for i in range(5):
        t = now - timedelta(hours=(5 - i))
        sm = 70.0 + (i * 5.0)  # reaches 90%
        p = 10.0 + (i * 3.5)   # reaches 24 kPa
        db_session.add(SensorReading(
            sensor_id=station_id,
            soil_moisture=sm,
            temperature=19.0,
            pore_pressure=p,
            ground_vibration=0.08,
            timestamp=t
        ))
    db_session.commit()

    rainfall_input = {"rainfall_24h_mm": 125.0, "rainfall_intensity_mm_h": 22.0}
    res = temporal_engine.analyze_station_temporal_risk(
        db_session, station_id, reference_time=now, rainfall_input=rainfall_input
    )
    assert res["temporal_risk_score"] >= 50.0
    assert res["trend"] in ["RISING", "ACCELERATING"]
    assert len(res["explanation"]) >= 3


def test_7_declining_sensor_values_produce_declining_trend(db_session):
    """Test 7: Drainage and pore pressure dissipation produce a DECLINING trend."""
    station_id = "TEST-SN-DECL"
    now = datetime.utcnow()

    # Drying/dissipating slope: moisture drops from 85% to 55%, pore pressure from 22 to 5 kPa
    for i in range(5):
        t = now - timedelta(hours=(6 - i))
        sm = 85.0 - (i * 7.0)
        p = 22.0 - (i * 4.0)
        db_session.add(SensorReading(
            sensor_id=station_id,
            soil_moisture=sm,
            temperature=24.0,
            pore_pressure=p,
            ground_vibration=0.02,
            timestamp=t
        ))
    db_session.commit()

    res = temporal_engine.analyze_station_temporal_risk(db_session, station_id, reference_time=now)
    assert res["trend"] == "DECLINING"
    assert res["sensor_factors"]["soil_moisture"]["rate_per_hr"] < -0.5
    assert res["sensor_factors"]["pore_pressure"]["rate_per_hr"] < -0.3


def test_8_multiple_stations_remain_isolated(db_session):
    """Test 8: Telemetry from Station A does not leak into Station B."""
    st_a = "TEST-SN-ISO-A"
    st_b = "TEST-SN-ISO-B"
    now = datetime.utcnow()

    # Station A: extreme hazard values
    for i in range(3):
        t = now - timedelta(hours=(3 - i))
        db_session.add(SensorReading(
            sensor_id=st_a,
            soil_moisture=92.0,
            temperature=20.0,
            pore_pressure=28.0,
            ground_vibration=1.8,
            timestamp=t
        ))

    # Station B: pristine calm baseline values
    for i in range(3):
        t = now - timedelta(hours=(3 - i))
        db_session.add(SensorReading(
            sensor_id=st_b,
            soil_moisture=35.0,
            temperature=22.0,
            pore_pressure=1.0,
            ground_vibration=0.01,
            timestamp=t
        ))
    db_session.commit()

    res_a = temporal_engine.analyze_station_temporal_risk(db_session, st_a, reference_time=now)
    res_b = temporal_engine.analyze_station_temporal_risk(db_session, st_b, reference_time=now)

    # Confirm complete isolation
    assert res_a["temporal_risk_score"] >= 50.0
    assert res_b["temporal_risk_score"] < 10.0
    assert res_a["temporal_risk_score"] > res_b["temporal_risk_score"] + 40.0
    assert res_a["sensor_factors"]["soil_moisture"]["current"] == 92.0
    assert res_b["sensor_factors"]["soil_moisture"]["current"] == 35.0


def test_9_no_future_timestamps_included_in_window(db_session):
    """Test 9: Verify that readings with timestamps ahead of reference_time are excluded."""
    station_id = "TEST-SN-FUTURE"
    now = datetime.utcnow()

    # Past reading at T - 2h (normal value)
    db_session.add(SensorReading(
        sensor_id=station_id,
        soil_moisture=50.0,
        temperature=21.0,
        pore_pressure=3.0,
        ground_vibration=0.02,
        timestamp=now - timedelta(hours=2)
    ))

    # Past reading at T - 1h (normal value)
    db_session.add(SensorReading(
        sensor_id=station_id,
        soil_moisture=52.0,
        temperature=21.0,
        pore_pressure=3.5,
        ground_vibration=0.02,
        timestamp=now - timedelta(hours=1)
    ))

    # Future reading at T + 3h (extreme spike that shouldn't be seen yet)
    db_session.add(SensorReading(
        sensor_id=station_id,
        soil_moisture=98.0,
        temperature=21.0,
        pore_pressure=35.0,
        ground_vibration=2.5,
        timestamp=now + timedelta(hours=3)
    ))
    db_session.commit()

    # Query using current reference time
    res = temporal_engine.analyze_station_temporal_risk(db_session, station_id, reference_time=now)

    # Future reading MUST be excluded
    assert res["available_observations"] == 2
    assert res["sensor_factors"]["soil_moisture"]["current"] == 52.0
    assert res["sensor_factors"]["pore_pressure"]["current"] == 3.5
    assert res["temporal_risk_score"] < 15.0


def test_10_api_risk_probability_endpoint_integration(client):
    """Test 10: Verify /api/risk/probability returns empirical progression data without hardcoded multiples."""
    resp = client.get("/api/risk/probability?location=Guwahati")
    assert resp.status_code == 200
    data = resp.json()

    assert "trend" in data
    trend = data["trend"]
    assert "labels" in trend
    assert "values" in trend
    assert "data_sufficiency" in trend
    assert "has_sensor_series" in trend

    # Response must also contain temporal analysis details
    assert "temporal_analysis" in data
    assert "location" in data
    assert "overall" in data
    assert "landslide" in data
    assert "flood" in data
