from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Location, RiskPrediction, SensorReading, SensorDevice
from ..schemas import PredictionRequest, PredictionResponse
from ..services.ml_service import ml_engine
from ..services.gis_service import get_locations_geojson
from ..services.temporal_service import temporal_engine, resolve_station_sensor_id
from ..services.fusion_service import fusion_engine

router = APIRouter(prefix="/api/risk", tags=["Landslide Risk Assessment"])

@router.post("/predict")
def predict_risk(req: PredictionRequest, db: Session = Depends(get_db)):
    pred = ml_engine.predict(req.dict())
    fused = fusion_engine.fuse_evidence(
        spatial_pred=pred,
        location_meta={
            "latitude": req.latitude,
            "longitude": req.longitude,
            "state": req.state,
            "district": req.district
        }
    )
    return {
        "status": "success",
        "latitude": req.latitude,
        "longitude": req.longitude,
        "state": req.state,
        "district": req.district,
        "prediction": pred,
        "fusion": fused,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/live")
def get_live_risk(location: Optional[str] = "Guwahati", db: Session = Depends(get_db)):
    # Default monitored location: Guwahati, Assam or user requested
    loc = db.query(Location).filter(Location.name.ilike(f"%{location}%")).first()
    if not loc:
        loc = db.query(Location).first()

    pred = ml_engine.predict({
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "state": loc.state,
        "district": loc.district
    })

    # Temporal sensor telemetry analysis for this station
    sensor_id = resolve_station_sensor_id(db, loc.name)
    temporal_analysis = None
    if sensor_id:
        temporal_analysis = temporal_engine.analyze_station_temporal_risk(db, sensor_id)

    fused = fusion_engine.fuse_location_risk(db, loc.name)

    return {
        "location": {
            "id": loc.id,
            "name": f"{loc.name}, {loc.state}",
            "city": loc.name,
            "state": loc.state,
            "latitude": loc.latitude,
            "longitude": loc.longitude
        },
        "overall": int(pred["risk_score"]),
        "landslide": int(pred["landslide_risk_pct"]),
        "flood": int(pred["flood_risk_pct"]),
        "level": pred["risk_level"],
        "environmental_factors": pred["environmental_features"],
        "factors": pred["factors"],
        "contributing_factors": pred["contributing_factors"],
        "recommendations": pred["recommendations"],
        "alert": pred["alert"],
        "temporal_analysis": temporal_analysis,
        "fusion": fused,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/probability")
def get_probability_report(location: Optional[str] = "Guwahati", db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.name.ilike(f"%{location}%")).first()
    if not loc:
        loc = db.query(Location).first()

    pred = ml_engine.predict({
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "state": loc.state,
        "district": loc.district
    })

    score = int(pred["risk_score"])

    # Reconstruct authentic temporal progression from sensor readings (NO fake hardcoded multiples)
    trend_data = temporal_engine.get_empirical_progression_trend(db, loc.name, score)

    # Detailed sliding-window analysis if station sensor exists
    sensor_id = resolve_station_sensor_id(db, loc.name)
    temporal_analysis = None
    if sensor_id:
        temporal_analysis = temporal_engine.analyze_station_temporal_risk(db, sensor_id)

    fused = fusion_engine.fuse_location_risk(db, loc.name)

    return {
        "location": f"{loc.name}, {loc.state}",
        "overall": score,
        "landslide": int(pred["landslide_risk_pct"]),
        "flood": int(pred["flood_risk_pct"]),
        "level": pred["risk_level"],
        "factors": pred["factors"],
        "trend": {
            "labels": trend_data["labels"],
            "values": trend_data["values"],
            "data_sufficiency": trend_data["data_sufficiency"],
            "has_sensor_series": trend_data["has_sensor_series"],
            "observations_count": trend_data["observations_count"],
            "message": trend_data["message"]
        },
        "temporal_analysis": temporal_analysis,
        "fusion": fused,
        "contributing_factors": pred["contributing_factors"],
        "recommendations": pred["recommendations"]
    }

@router.get("/locations/{location_id}/detail")
def get_location_risk_detail(location_id: str, db: Session = Depends(get_db)):
    loc = db.query(Location).filter((Location.id == location_id) | (Location.name.ilike(f"%{location_id}%"))).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found in NER registry.")

    pred = ml_engine.predict({
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "state": loc.state,
        "district": loc.district
    })

    sensor_id = resolve_station_sensor_id(db, loc.name)
    temporal_analysis = None
    if sensor_id:
        temporal_analysis = temporal_engine.analyze_station_temporal_risk(db, sensor_id)

    fused = fusion_engine.fuse_location_risk(db, loc.name)

    return {
        "location": {
            "id": loc.id,
            "name": f"{loc.name}, {loc.state}",
            "city": loc.name,
            "state": loc.state,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "population_exposed": loc.population_exposed,
            "roads_exposed": loc.roads_exposed,
            "critical_assets": loc.critical_assets
        },
        "overall": int(pred["risk_score"]),
        "flood": int(pred["flood_risk_pct"]),
        "landslide": int(pred["landslide_risk_pct"]),
        "level": pred["risk_level"],
        "factors": pred["factors"],
        "environmental_features": pred["environmental_features"],
        "contributing_factors": pred["contributing_factors"],
        "recommendations": pred["recommendations"],
        "alert": pred["alert"],
        "temporal_analysis": temporal_analysis,
        "fusion": fused,
        "last_updated": datetime.utcnow().strftime("%I:%M %p")
    }

@router.get("/fusion")
def get_fused_risk(location: Optional[str] = "Guwahati", db: Session = Depends(get_db)):
    """Dedicated endpoint returning comprehensive multi-modal fused risk."""
    return fusion_engine.fuse_location_risk(db, location)

@router.get("/map")
def get_risk_map(db: Session = Depends(get_db)):
    return get_locations_geojson(db)
