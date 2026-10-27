from typing import List, Union, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SensorDevice, SensorReading
from ..schemas import SensorDataSubmission, SensorResponse

router = APIRouter(prefix="/api/sensors", tags=["IoT Sensors & Telemetry"])

@router.get("", response_model=List[SensorResponse])
def list_sensors(db: Session = Depends(get_db)):
    sensors = db.query(SensorDevice).all()
    out = []
    for s in sensors:
        latest = db.query(SensorReading).filter(SensorReading.sensor_id == s.id).order_by(SensorReading.timestamp.desc()).first()
        reading_dict = None
        if latest:
            reading_dict = {
                "soil_moisture": latest.soil_moisture,
                "temperature": latest.temperature,
                "pore_pressure": latest.pore_pressure,
                "ground_vibration": latest.ground_vibration,
                "battery_level": latest.battery_level,
                "signal_strength": latest.signal_strength,
                "is_simulated": latest.is_simulated,
                "timestamp": latest.timestamp.isoformat()
            }
        out.append(SensorResponse(
            id=s.id,
            name=s.name,
            state=s.state,
            latitude=s.latitude,
            longitude=s.longitude,
            status=s.status,
            battery_pct=s.battery_pct,
            signal_dbm=s.signal_dbm,
            last_reading=reading_dict
        ))
    return out

@router.post("/register")
def register_sensor(device_in: Dict[str, Any], db: Session = Depends(get_db)):
    device_id = device_in.get("id") or f"SN-{device_in.get('state', 'NER')[:2].upper()}-{int(datetime.utcnow().timestamp()) % 1000:03d}"
    existing = db.query(SensorDevice).filter(SensorDevice.id == device_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Sensor ID {device_id} already registered.")

    new_device = SensorDevice(
        id=device_id,
        name=device_in.get("name", f"Sensor Station {device_id}"),
        state=device_in.get("state", "Assam"),
        latitude=float(device_in.get("latitude", 26.14)),
        longitude=float(device_in.get("longitude", 91.73)),
        battery_pct=int(device_in.get("battery_level", 95)),
        signal_dbm=int(device_in.get("signal_strength", -65)),
        status="Active",
        last_ping=datetime.utcnow()
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return {"status": "registered", "sensor_id": new_device.id}

@router.post("/data")
def ingest_sensor_data(
    payload: Union[SensorDataSubmission, List[SensorDataSubmission]],
    db: Session = Depends(get_db)
):
    items = payload if isinstance(payload, list) else [payload]
    saved_count = 0

    for item in items:
        # Check or auto-register sensor
        dev = db.query(SensorDevice).filter(SensorDevice.id == item.sensor_id).first()
        if not dev:
            dev = SensorDevice(
                id=item.sensor_id,
                name=f"Auto-Station {item.sensor_id}",
                state="Assam",
                latitude=item.latitude or 26.1445,
                longitude=item.longitude or 91.7362,
                status="Active"
            )
            db.add(dev)
            db.commit()

        dev.last_ping = datetime.utcnow()
        if item.battery_level is not None:
            dev.battery_pct = item.battery_level
        if item.signal_strength is not None:
            dev.signal_dbm = item.signal_strength

        reading = SensorReading(
            sensor_id=item.sensor_id,
            soil_moisture=item.soil_moisture,
            temperature=item.temperature,
            pore_pressure=item.pore_pressure or 0.0,
            ground_vibration=item.ground_vibration or 0.0,
            battery_level=item.battery_level or 95,
            signal_strength=item.signal_strength or -65,
            is_simulated=item.is_simulated,
            timestamp=item.timestamp or datetime.utcnow()
        )
        db.add(reading)
        saved_count += 1

    db.commit()
    return {
        "status": "success",
        "records_ingested": saved_count,
        "is_simulated": True,
        "label": "SIMULATED_SENSOR"
    }

@router.get("/{sensor_id}")
def get_sensor(sensor_id: str, db: Session = Depends(get_db)):
    sensor = db.query(SensorDevice).filter(SensorDevice.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor device not found.")
    return sensor

@router.get("/{sensor_id}/latest")
def get_sensor_latest(sensor_id: str, db: Session = Depends(get_db)):
    latest = db.query(SensorReading).filter(SensorReading.sensor_id == sensor_id).order_by(SensorReading.timestamp.desc()).first()
    if not latest:
        raise HTTPException(status_code=404, detail="No readings found for this sensor.")
    return latest

@router.get("/{sensor_id}/temporal")
def get_sensor_temporal(sensor_id: str, db: Session = Depends(get_db)):
    from ..services.temporal_service import temporal_engine
    return temporal_engine.analyze_station_temporal_risk(db, sensor_id)

