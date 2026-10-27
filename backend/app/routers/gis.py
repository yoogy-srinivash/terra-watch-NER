from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.gis_service import (
    get_locations_geojson, get_shelters_geojson, get_rescue_points_geojson,
    get_roads_geojson, get_landslides_geojson
)

router = APIRouter(prefix="/api/gis", tags=["GIS Engine & Spatial Data"])

@router.get("/locations")
def get_locations(db: Session = Depends(get_db)):
    return get_locations_geojson(db)

@router.get("/shelters")
def get_shelters(db: Session = Depends(get_db)):
    return get_shelters_geojson(db)

@router.get("/rescue-points")
def get_rescue_points(db: Session = Depends(get_db)):
    return get_rescue_points_geojson(db)

@router.get("/roads")
def get_roads(db: Session = Depends(get_db)):
    return get_roads_geojson(db)

@router.get("/landslides")
def get_landslides(limit: int = Query(200, ge=1, le=1000), db: Session = Depends(get_db)):
    return get_landslides_geojson(db, limit=limit)

@router.get("/risk-zones")
def get_risk_zones(db: Session = Depends(get_db)):
    all_locs = get_locations_geojson(db)
    # Filter to High and Critical zones
    high_critical = [
        f for f in all_locs["features"]
        if f["properties"]["riskLevel"] in ["HIGH", "CRITICAL"]
    ]
    return {
        "type": "FeatureCollection",
        "features": high_critical
    }

@router.get("/admin-map")
def get_admin_map_data(db: Session = Depends(get_db)):
    return {
        "locations": get_locations_geojson(db),
        "shelters": get_shelters_geojson(db),
        "rescue_points": get_rescue_points_geojson(db),
        "roads": get_roads_geojson(db)
    }
