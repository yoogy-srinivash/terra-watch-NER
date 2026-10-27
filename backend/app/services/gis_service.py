from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models import Location, Infrastructure, Road, LandslideEvent, SensorDevice
from .ml_service import ml_engine

def get_locations_geojson(db: Session) -> Dict[str, Any]:
    locations = db.query(Location).all()
    features = []

    for loc in locations:
        # Run ML risk inference
        pred = ml_engine.predict({
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "state": loc.state,
            "district": loc.district
        })

        features.append({
            "type": "Feature",
            "id": loc.id,
            "geometry": {
                "type": "Point",
                "coordinates": [loc.longitude, loc.latitude]
            },
            "properties": {
                "id": loc.id,
                "name": loc.name,
                "district": loc.district,
                "state": loc.state,
                "hazard": loc.primary_hazard,
                "risk": pred["risk_score"],
                "risk_probability": pred["risk_probability"],
                "riskLevel": pred["risk_level"],
                "landslide_risk": pred["landslide_risk_pct"],
                "flood_risk": pred["flood_risk_pct"],
                "status": f"{pred['risk_level']} Risk",
                "rainfall": f"{pred['environmental_features']['rainfall_24h_mm']} mm",
                "population_exposed": loc.population_exposed,
                "roads_exposed": loc.roads_exposed,
                "critical_assets": loc.critical_assets,
                "factors": pred["factors"],
                "contributing_factors": pred["contributing_factors"],
                "recommendations": pred["recommendations"]
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }

def get_shelters_geojson(db: Session) -> Dict[str, Any]:
    shelters = db.query(Infrastructure).filter(Infrastructure.category == "Shelter").all()
    features = []

    for s in shelters:
        features.append({
            "type": "Feature",
            "id": s.id,
            "geometry": {
                "type": "Point",
                "coordinates": [s.longitude, s.latitude]
            },
            "properties": {
                "id": s.id,
                "name": s.name,
                "type": s.type,
                "capacity": s.capacity,
                "availability": s.availability,
                "hazardSafe": s.hazard_safe,
                "distance": "Local Zone",
                "state": s.state
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }

def get_rescue_points_geojson(db: Session) -> Dict[str, Any]:
    points = db.query(Infrastructure).filter(Infrastructure.category == "Rescue Point").all()
    features = []

    for p in points:
        features.append({
            "type": "Feature",
            "id": p.id,
            "geometry": {
                "type": "Point",
                "coordinates": [p.longitude, p.latitude]
            },
            "properties": {
                "id": p.id,
                "name": p.name,
                "service": p.type,
                "status": p.status,
                "state": p.state
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }

def get_roads_geojson(db: Session) -> Dict[str, Any]:
    roads = db.query(Road).all()
    features = []

    for r in roads:
        features.append({
            "type": "Feature",
            "id": r.id,
            "geometry": {
                "type": "Point",
                "coordinates": [r.longitude or 92.0, r.latitude or 26.0]
            },
            "properties": {
                "id": r.id,
                "name": r.name,
                "state": r.state,
                "start": r.start_point,
                "end": r.end_point,
                "status": r.status,
                "blockage_reason": r.blockage_reason,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }

def get_landslides_geojson(db: Session, limit: int = 200) -> Dict[str, Any]:
    events = db.query(LandslideEvent).limit(limit).all()
    features = []

    for e in events:
        features.append({
            "type": "Feature",
            "id": e.id,
            "geometry": {
                "type": "Point",
                "coordinates": [e.longitude, e.latitude]
            },
            "properties": {
                "event_id": e.event_id,
                "date": e.event_date,
                "location": e.location_description,
                "state": e.state,
                "category": e.landslide_category,
                "trigger": e.landslide_trigger,
                "fatalities": e.fatality_count,
                "source": e.source
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }
