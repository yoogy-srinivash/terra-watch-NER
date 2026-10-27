import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from backend.app.database import get_db
from backend.app.models import (
    OfflineSyncQueue, FieldReport, SensorReading, SensorDevice,
    Location, Infrastructure, Alert, EmergencyTask
)
from backend.app.schemas import SyncPushRequest, SyncPushResponse, SyncPushResultItem

router = APIRouter(prefix="/api/sync", tags=["Offline Synchronization Engine"])

@router.post("/push", response_model=SyncPushResponse)
def push_offline_sync(
    payload: SyncPushRequest,
    db: Session = Depends(get_db)
):
    """
    Idempotently ingests queued offline submissions from field devices and citizen clients.
    Guarantees no duplicate records even under sporadic network re-transmissions.
    """
    results = []
    successful_count = 0
    
    for item in payload.items:
        # Check idempotency via local_id
        existing = db.query(OfflineSyncQueue).filter(OfflineSyncQueue.local_id == item.local_id).first()
        if existing:
            results.append(SyncPushResultItem(
                local_id=item.local_id,
                server_id=None,
                status="DUPLICATE",
                message="Item already synced previously."
            ))
            successful_count += 1
            continue
            
        try:
            server_id = None
            if item.entity_type == "report":
                data = item.payload
                report_id = f"LS-SYNC-{int(datetime.utcnow().timestamp()) % 100000}"
                server_id = report_id
                
                rep = FieldReport(
                    id=report_id,
                    user_name=data.get("user_name", "Offline Citizen"),
                    issue_type=data.get("issue_type", "landslide"),
                    severity=data.get("severity", "moderate"),
                    location_name=data.get("location", "NER Monitored Zone"),
                    state=data.get("state", "Assam"),
                    city=data.get("city", ""),
                    description=data.get("description", "Synced offline field report"),
                    latitude=data.get("latitude"),
                    longitude=data.get("longitude"),
                    is_emergency=data.get("is_emergency", False),
                    status="Pending",
                    evidence_desc="Synced from offline queue",
                    created_at=datetime.utcnow()
                )
                db.add(rep)
                
                if rep.is_emergency or rep.severity in ["high", "critical"]:
                    task_id = f"ER-SYNC-{int(datetime.utcnow().timestamp()) % 10000}"
                    em_task = EmergencyTask(
                        id=task_id,
                        user_name=rep.user_name,
                        location=f"{rep.location_name}, {rep.state}",
                        state=rep.state,
                        request_type=rep.issue_type.capitalize(),
                        priority="Critical" if rep.severity == "critical" else "High",
                        status="Pending",
                        description=f"[OFFLINE SYNC RESCUE DISPATCH] {rep.description}",
                        coordinates=f"{rep.latitude}, {rep.longitude}" if rep.latitude else "26.1445, 91.7362",
                        shelter="Nearest Designated District Shelter",
                        priority_score=90.0 if rep.severity == "critical" else 75.0,
                        created_at=datetime.utcnow()
                    )
                    db.add(em_task)

            elif item.entity_type == "sensor_reading":
                data = item.payload
                sensor_id = data.get("sensor_id", "SN-AR-001")
                reading = SensorReading(
                    sensor_id=sensor_id,
                    soil_moisture=float(data.get("soil_moisture", 45.0)),
                    temperature=float(data.get("temperature", 24.0)),
                    pore_pressure=float(data.get("pore_pressure", 0.0)),
                    ground_vibration=float(data.get("ground_vibration", 0.0)),
                    battery_level=int(data.get("battery_level", 95)),
                    signal_strength=int(data.get("signal_strength", -70)),
                    is_simulated=data.get("is_simulated", True),
                    timestamp=datetime.utcnow()
                )
                db.add(reading)
                server_id = f"SR-{sensor_id}"

            # Record in offline queue log for deduplication
            sync_log = OfflineSyncQueue(
                local_id=item.local_id,
                device_id=item.device_id,
                entity_type=item.entity_type,
                payload_json=json.dumps(item.payload),
                sync_status="SYNCED",
                client_created_at=item.client_created_at,
                synced_at=datetime.utcnow()
            )
            db.add(sync_log)
            db.commit()
            
            successful_count += 1
            results.append(SyncPushResultItem(
                local_id=item.local_id,
                server_id=server_id,
                status="SUCCESS",
                message=f"Entity {item.entity_type} successfully ingested and committed."
            ))
        except Exception as e:
            db.rollback()
            results.append(SyncPushResultItem(
                local_id=item.local_id,
                server_id=None,
                status="ERROR",
                message=str(e)
            ))

    return SyncPushResponse(
        processed=len(payload.items),
        successful=successful_count,
        results=results
    )

@router.get("/pull")
def pull_offline_cache(db: Session = Depends(get_db)):
    """
    Provides an essential pre-caching package for low-connectivity zones.
    Includes active alerts, monitored stations, emergency shelters, and safety rules.
    """
    alerts = db.query(Alert).filter(Alert.status.in_(["Active", "Issued", "Triggered"])).all()
    locations = db.query(Location).all()
    shelters = db.query(Infrastructure).filter(Infrastructure.category == "Shelter").all()
    
    return {
        "sync_timestamp": datetime.utcnow().isoformat(),
        "version": "1.0-offline-pack",
        "active_alerts": [
            {
                "id": a.id,
                "location": a.location,
                "state": a.state,
                "hazard_type": a.hazard_type,
                "severity": a.severity,
                "title": a.title,
                "message": a.message
            } for a in alerts
        ],
        "stations": [
            {
                "id": l.id,
                "name": l.name,
                "district": l.district,
                "state": l.state,
                "latitude": l.latitude,
                "longitude": l.longitude
            } for l in locations
        ],
        "shelters": [
            {
                "id": s.id,
                "name": s.name,
                "state": s.state,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "capacity": s.capacity,
                "availability": s.availability
            } for s in shelters
        ],
        "emergency_contacts": [
            {"service": "NDRF Disaster Helpline", "phone": "1078"},
            {"service": "NER State Disaster Management Authority", "phone": "1070"},
            {"service": "Emergency Police / Fire / Ambulance", "phone": "112"},
            {"service": "LandSafe Emergency Dispatch Room", "phone": "1800-345-5263"}
        ]
    }

@router.get("/status")
def get_sync_status(db: Session = Depends(get_db)):
    """Get offline queue health and sync statistics."""
    total_synced = db.query(OfflineSyncQueue).count()
    return {
        "offline_engine_status": "ONLINE",
        "total_offline_records_synced": total_synced,
        "supported_entities": ["report", "sensor_reading", "alert_ack"],
        "storage_mode": "IndexedDB + LocalStorage client fallback"
    }
