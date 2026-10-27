from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.app.database import get_db
from backend.app.models import Alert, Location, User
from backend.app.schemas import AlertCreate, AlertResponse
from backend.app.utils.security import get_optional_current_user, require_role
from backend.app.services.notification_service import notification_service

router = APIRouter(prefix="/api/alerts", tags=["Alerts & Early Warning"])

SIREN_SYSTEM_STATE = {
    "active": False,
    "last_triggered_at": None,
    "triggered_by": None,
    "active_locations": []
}

@router.get("", response_model=List[AlertResponse])
def get_alerts(
    state: Optional[str] = None,
    severity: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Alert)
    if state and state.lower() != "all":
        query = query.filter(Alert.state.ilike(f"%{state}%"))
    if severity and severity.lower() != "all":
        query = query.filter(Alert.severity.ilike(f"%{severity}%"))
    if status_filter and status_filter.lower() != "all":
        query = query.filter(Alert.status.ilike(f"%{status_filter}%"))
    
    records = query.order_by(Alert.created_at.desc()).limit(limit).all()
    results = []
    for r in records:
        time_str = r.created_at.strftime("%I:%M %p") if r.created_at else "Now"
        loc_display = r.location if (r.state and r.state in r.location) else (f"{r.location}, {r.state}" if r.state else r.location)
        results.append(AlertResponse(
            id=r.id,
            location=loc_display,
            state=r.state,
            hazard_type=r.hazard_type,
            severity=r.severity,
            status=r.status,
            title=r.title,
            message=r.message,
            time=time_str,
            created_at=r.created_at
        ))
    return results

@router.get("/active", response_model=List[AlertResponse])
def get_active_alerts(db: Session = Depends(get_db)):
    records = db.query(Alert).filter(
        Alert.status.in_(["Active", "Issued", "Triggered"])
    ).order_by(Alert.created_at.desc()).all()
    results = []
    for r in records:
        time_str = r.created_at.strftime("%I:%M %p") if r.created_at else "Now"
        loc_display = r.location if (r.state and r.state in r.location) else (f"{r.location}, {r.state}" if r.state else r.location)
        results.append(AlertResponse(
            id=r.id,
            location=loc_display,
            state=r.state,
            hazard_type=r.hazard_type,
            severity=r.severity,
            status=r.status,
            title=r.title,
            message=r.message,
            time=time_str,
            created_at=r.created_at
        ))
    return results

@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    alert_id = f"AL-{int(datetime.utcnow().timestamp()) % 10000 + 2000}"
    loc_state = payload.state
    lat = payload.latitude
    lon = payload.longitude
    
    if not loc_state or not lat:
        loc = db.query(Location).filter(Location.name.ilike(f"%{payload.location.split(',')[0]}%")).first()
        if loc:
            loc_state = loc.state
            lat = lat or loc.latitude
            lon = lon or loc.longitude
        else:
            loc_state = loc_state or "NER"

    title = payload.title or f"{payload.severity.upper()} Hazard: {payload.hazard_type} in {payload.location}"
    message = payload.message or f"Immediate advisory for {payload.location}. Risk level: {payload.severity}. Evacuate vulnerable slopes if advised by SDMA."
    
    new_alert = Alert(
        id=alert_id,
        location=payload.location,
        state=loc_state,
        hazard_type=payload.hazard_type,
        severity=payload.severity.capitalize(),
        status="Active",
        title=title,
        message=message,
        latitude=lat,
        longitude=lon,
        created_at=datetime.utcnow()
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    
    notification_service.dispatch_alert_notification(
        db=db,
        alert_id=alert_id,
        location=payload.location,
        hazard_type=payload.hazard_type,
        severity=payload.severity,
        message=message
    )
    
    time_str = new_alert.created_at.strftime("%I:%M %p")
    return AlertResponse(
        id=new_alert.id,
        location=new_alert.location,
        state=new_alert.state,
        hazard_type=new_alert.hazard_type,
        severity=new_alert.severity,
        status=new_alert.status,
        title=new_alert.title,
        message=new_alert.message,
        time=time_str,
        created_at=new_alert.created_at
    )

@router.patch("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    alert.status = "Resolved"
    alert.resolved_at = datetime.utcnow()
    if current_user:
        alert.resolved_by = current_user.email
    db.commit()
    db.refresh(alert)
    time_str = alert.created_at.strftime("%I:%M %p") if alert.created_at else "Earlier"
    return AlertResponse(
        id=alert.id,
        location=alert.location,
        state=alert.state,
        hazard_type=alert.hazard_type,
        severity=alert.severity,
        status=alert.status,
        title=alert.title,
        message=alert.message,
        time=time_str,
        created_at=alert.created_at
    )

@router.post("/sirens/trigger")
def trigger_sirens(
    location: str = "Guwahati, Assam",
    duration_seconds: int = 60,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    SIREN_SYSTEM_STATE["active"] = True
    SIREN_SYSTEM_STATE["last_triggered_at"] = datetime.utcnow().isoformat()
    SIREN_SYSTEM_STATE["triggered_by"] = current_user.email if current_user else "Disaster Response Unit"
    if location not in SIREN_SYSTEM_STATE["active_locations"]:
        SIREN_SYSTEM_STATE["active_locations"].append(location)

    notification_service.dispatch_alert_notification(
        db=db,
        alert_id=f"SIREN-{int(datetime.utcnow().timestamp()) % 10000}",
        location=location,
        hazard_type="Siren Broadcast",
        severity="Critical",
        message=f"EMERGENCY SIREN ACTIVATED in {location}. Evacuate immediately to designated relief shelters."
    )

    return {
        "status": "success",
        "message": f"Emergency siren successfully activated for {location}",
        "siren_active": True,
        "duration_seconds": duration_seconds,
        "active_locations": SIREN_SYSTEM_STATE["active_locations"],
        "triggered_at": SIREN_SYSTEM_STATE["last_triggered_at"]
    }

@router.post("/sirens/stop")
def stop_sirens():
    SIREN_SYSTEM_STATE["active"] = False
    SIREN_SYSTEM_STATE["active_locations"] = []
    return {
        "status": "success",
        "message": "All sirens deactivated.",
        "siren_active": False
    }

@router.get("/sirens/status")
def get_sirens_status(db: Session = Depends(get_db)):
    locations = db.query(Location).limit(8).all()
    siren_nodes = []
    for loc in locations:
        siren_nodes.append({
            "station": loc.name,
            "state": loc.state,
            "status": "ONLINE",
            "decibel_rating": "120 dB",
            "backup_power": "Solar + Battery 98%",
            "siren_active": SIREN_SYSTEM_STATE["active"] and (loc.name in str(SIREN_SYSTEM_STATE["active_locations"]))
        })
    return {
        "system_online": True,
        "global_siren_active": SIREN_SYSTEM_STATE["active"],
        "active_locations": SIREN_SYSTEM_STATE["active_locations"],
        "last_triggered_at": SIREN_SYSTEM_STATE["last_triggered_at"],
        "siren_nodes": siren_nodes
    }
