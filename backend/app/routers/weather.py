from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from backend.app.database import get_db
from backend.app.models import Location
from backend.app.services.weather_service import weather_service

router = APIRouter(prefix="/api/weather", tags=["Meteorological & Rainfall Intelligence"])

@router.get("/current")
async def get_current_weather(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    location_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve live rainfall, temperature, and atmospheric conditions."""
    if location_id:
        loc = db.query(Location).filter(Location.id == location_id).first()
        if not loc:
            raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
        lat = loc.latitude
        lon = loc.longitude
        loc_name = loc.name
        state = loc.state
    else:
        lat = lat or 26.1445
        lon = lon or 91.7362
        loc_name = "Assam (Guwahati)"
        state = "Assam"
        
    weather_data = await weather_service.get_live_rainfall(lat, lon)
    return {
        "location": loc_name,
        "state": state,
        "latitude": lat,
        "longitude": lon,
        "rainfall_data": weather_data,
        "source": "Open-Meteo & IMD NER Doppler Network"
    }

@router.get("/forecast")
async def get_weather_forecast(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    location_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve multi-day precipitation forecast and risk projection for a locality."""
    if location_id:
        loc = db.query(Location).filter(Location.id == location_id).first()
        if not loc:
            raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
        lat = loc.latitude
        lon = loc.longitude
        loc_name = loc.name
        state = loc.state
    else:
        lat = lat or 26.1445
        lon = lon or 91.7362
        loc_name = "Assam (Guwahati)"
        state = "Assam"

    forecast = await weather_service.get_weather_forecast(lat, lon)
    return {
        "location": loc_name,
        "state": state,
        "latitude": lat,
        "longitude": lon,
        "forecast": forecast
    }

@router.get("/stations")
async def get_stations_weather(db: Session = Depends(get_db)):
    """Retrieve weather snapshots across primary monitoring hubs in all 8 NER states."""
    locations = db.query(Location).limit(8).all()
    stations = []
    for loc in locations:
        weather = await weather_service.get_live_rainfall(loc.latitude, loc.longitude)
        stations.append({
            "id": loc.id,
            "name": loc.name,
            "state": loc.state,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "rainfall_24h_mm": weather.get("rainfall_24h_mm", 0.0),
            "rainfall_72h_mm": weather.get("rainfall_72h_mm", 0.0),
            "temperature_c": weather.get("temperature_c", 24.0),
            "precipitation_category": "Heavy" if weather.get("rainfall_24h_mm", 0.0) > 64.5 else ("Moderate" if weather.get("rainfall_24h_mm", 0.0) > 15.5 else "Light")
        })
    return stations
