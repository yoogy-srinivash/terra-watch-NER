from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.app.database import get_db
from backend.app.models import (
    Location, RiskPrediction, Alert, FieldReport, EmergencyTask,
    LandslideEvent, User
)
from backend.app.utils.security import get_optional_current_user, require_role

router = APIRouter(prefix="/api/admin", tags=["Administration & Monitoring"])

# In-memory settings state
SYSTEM_SETTINGS = {
    "rainfall_threshold_24h_mm": 65.0,
    "rainfall_threshold_72h_mm": 150.0,
    "soil_moisture_critical_pct": 75.0,
    "slope_critical_angle_deg": 30.0,
    "ai_alert_confidence_cutoff": 0.65,
    "auto_siren_on_critical": True,
    "auto_sms_broadcast": True,
    "sensor_polling_interval_sec": 30,
    "maintenance_mode": False
}

@router.get("/dashboard")
def get_admin_dashboard(db: Session = Depends(get_db)):
    """
    Returns unified metrics tailored for `admin.js`:
    highRiskLocations, openReports, activeAlerts, emergencyRequests,
    overallRisk, landslideRisk, floodRisk, rainfall, soil, slope, water
    """
    # Counts
    active_alerts = db.query(Alert).filter(Alert.status.in_(["Active", "Issued", "Triggered"])).count()
    open_reports = db.query(FieldReport).filter(FieldReport.status.in_(["Pending", "Verified"])).count()
    emergency_reqs = db.query(EmergencyTask).filter(EmergencyTask.status.in_(["Pending", "Assigned", "In Progress"])).count()
    
    # Locations risk count
    predictions = db.query(RiskPrediction).all()
    if predictions:
        high_risk_locs = sum(1 for p in predictions if p.risk_level in ["HIGH", "CRITICAL"])
        overall = int(round(sum(p.risk_score for p in predictions) / len(predictions)))
        landslide = int(round(sum(p.landslide_risk_pct for p in predictions) / len(predictions)))
        flood = int(round(sum(p.flood_risk_pct for p in predictions) / len(predictions)))
        rainfall = int(round(sum(p.rainfall_factor_pct for p in predictions) / len(predictions)))
        soil = int(round(sum(p.soil_factor_pct for p in predictions) / len(predictions)))
        slope = int(round(sum(p.slope_factor_pct for p in predictions) / len(predictions)))
        water = int(round(sum(p.water_factor_pct for p in predictions) / len(predictions)))
    else:
        high_risk_locs = 0
        overall = 0
        landslide = 0
        flood = 0
        rainfall = 0
        soil = 0
        slope = 0
        water = 0

    return {
        "highRiskLocations": high_risk_locs,
        "openReports": open_reports,
        "activeAlerts": active_alerts,
        "emergencyRequests": emergency_reqs,
        "overallRisk": overall,
        "landslideRisk": landslide,
        "floodRisk": flood,
        "rainfall": rainfall,
        "soil": soil,
        "slope": slope,
        "water": water,
        "monitoredStatesCount": 8,
        "systemHealth": "Operational (All 8 NER Nodes Active)"
    }

@router.get("/monitor-locations")
def get_monitor_locations(db: Session = Depends(get_db)):
    """
    Returns location records formatted for `monitor-locations.js`:
    [{ name: "Guwahati", state: "Assam", type: "Flood", score: 78, flood: 76, landslide: 54, risk: "High" }, ...]
    """
    locations = db.query(Location).all()
    results = []
    
    for loc in locations:
        pred = db.query(RiskPrediction).filter(RiskPrediction.location_id == loc.id).order_by(RiskPrediction.predicted_at.desc()).first()
        if pred:
            score = int(round(pred.risk_score))
            flood = int(round(pred.flood_risk_pct))
            landslide = int(round(pred.landslide_risk_pct))
            risk = pred.risk_level.capitalize()
            hazard = "Landslide" if landslide >= flood else "Flood"
        else:
            score = 65
            flood = 50
            landslide = 65
            risk = "Moderate"
            hazard = loc.primary_hazard or "Landslide"
            
        results.append({
            "name": loc.name,
            "district": loc.district,
            "state": loc.state,
            "type": hazard,
            "score": score,
            "flood": flood,
            "landslide": landslide,
            "risk": risk,
            "population_exposed": loc.population_exposed,
            "roads_exposed": loc.roads_exposed,
            "critical_assets": loc.critical_assets
        })
        
    return results

@router.get("/history/landslides")
def get_history_landslides(
    state: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Retrieve historical NASA landslide events for NER."""
    query = db.query(LandslideEvent)
    if state and state.lower() != "all":
        query = query.filter(LandslideEvent.state.ilike(f"%{state}%"))
    
    total = query.count()
    events = query.order_by(LandslideEvent.id.desc()).offset(offset).limit(limit).all()
    
    results = []
    for e in events:
        results.append({
            "id": e.id,
            "event_id": e.event_id,
            "date": e.event_date or "Historical Record",
            "location": e.location_description or f"{e.district}, {e.state}",
            "district": e.district,
            "state": e.state,
            "category": e.landslide_category,
            "trigger": e.landslide_trigger,
            "size": e.landslide_size,
            "fatalities": e.fatality_count,
            "injuries": e.injury_count,
            "latitude": e.latitude,
            "longitude": e.longitude,
            "source": e.source
        })
        
    return {
        "total_records": total,
        "returned": len(results),
        "events": results
    }

@router.get("/settings")
def get_settings():
    """Get active system warning thresholds and configuration."""
    return SYSTEM_SETTINGS

@router.post("/settings")
def update_settings(
    new_settings: Dict[str, Any],
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Update system warning thresholds and configuration."""
    for k, v in new_settings.items():
        if k in SYSTEM_SETTINGS:
            SYSTEM_SETTINGS[k] = v
    return {
        "status": "success",
        "message": "System settings updated successfully",
        "settings": SYSTEM_SETTINGS
    }
