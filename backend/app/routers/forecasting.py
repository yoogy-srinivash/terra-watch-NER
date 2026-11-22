"""
TerraWatch NER - Temporal Forecasting Router (/api/forecast)
Provides endpoints for Temporal Fusion Transformer (TFT) multi-horizon predictions.
Strictly decoupled from /api/risk/predict and /api/risk/live.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database import get_db
from ..models import Location, SensorDevice
from ..services.tft_service import tft_engine
from ..services.temporal_service import resolve_station_sensor_id

router = APIRouter(prefix="/api/forecast", tags=["Temporal Forecasting (TFT)"])


class ScenarioForecastRequest(BaseModel):
    sensor_id: str = Field(default="SN-AS-001", description="Station sensor identifier")
    initial_moisture_pct: float = Field(default=35.0, ge=5.0, le=100.0)
    initial_pore_pressure_kpa: float = Field(default=4.0, ge=0.0, le=60.0)
    rainfall_scenario_mm: float = Field(default=0.0, ge=0.0, le=300.0)
    horizon_hours: int = Field(default=24, ge=1, le=24)


@router.get("/status")
def get_forecasting_status():
    """Returns TFT forecasting module status, device, horizons, and academic provenance."""
    return tft_engine.get_status()


@router.get("/tft")
def get_station_tft_forecast(
    station_id: Optional[str] = Query(default="SN-AS-001", description="Sensor ID (e.g. SN-AS-001) or City name"),
    horizon: Optional[str] = Query(default="24h", pattern="^(1h|6h|24h)$"),
    db: Session = Depends(get_db)
):
    """
    Get multi-horizon (1h, 6h, 24h) forecasted Soil Moisture and Pore Water Pressure
    with p10, p50, and p90 prediction intervals.
    """
    horizon_map = {"1h": 1, "6h": 6, "24h": 24}
    horizon_hours = horizon_map.get(horizon, 24)

    # Resolve Station / Location Details
    resolved_sensor_id = resolve_station_sensor_id(db, station_id) or station_id

    # Find matching station or location
    loc = db.query(Location).filter(
        (Location.id.ilike(f"%{station_id}%")) | (Location.name.ilike(f"%{station_id}%"))
    ).first()

    if not loc:
        # Check sensor devices table
        dev = db.query(SensorDevice).filter(SensorDevice.id == resolved_sensor_id).first()
        if dev and dev.location_id:
            loc = db.query(Location).filter(Location.id == dev.location_id).first()

    station_name = f"{loc.name}, {loc.state}" if loc else f"Station {resolved_sensor_id}"
    state = loc.state if loc else "Assam"
    elevation = 350.0
    slope = 22.0

    if loc:
        from ..services.terrain_service import get_station_terrain
        terr = get_station_terrain(loc.id, loc.name, loc.state, loc.latitude, loc.longitude)
        elevation = terr.get("elevation_m", 350.0)
        slope = terr.get("slope_angle_deg", 22.0)

    forecast_data = tft_engine.forecast_station(
        db=db,
        sensor_id=resolved_sensor_id,
        station_name=station_name,
        state=state,
        elevation_m=elevation,
        slope_angle_deg=slope,
        horizon_hours=horizon_hours
    )

    return forecast_data


@router.post("/simulate")
def simulate_forecast_scenario(
    req: ScenarioForecastRequest,
    db: Session = Depends(get_db)
):
    """
    Interactive stress-testing: forecasts subsurface progression given simulated initial conditions.
    """
    loc = db.query(Location).first()
    elevation = 350.0
    slope = 22.0
    if loc:
        from ..services.terrain_service import get_station_terrain
        terr = get_station_terrain(loc.id, loc.name, loc.state, loc.latitude, loc.longitude)
        elevation = terr.get("elevation_m", 350.0)
        slope = terr.get("slope_angle_deg", 22.0)

    # Call forecasting engine
    res = tft_engine.forecast_station(
        db=db,
        sensor_id=req.sensor_id,
        station_name=f"Simulated Node ({req.sensor_id})",
        elevation_m=elevation,
        slope_angle_deg=slope,
        horizon_hours=req.horizon_hours
    )

    # Offset trajectory based on simulated rainfall scenario
    if req.rainfall_scenario_mm > 0:
        added_moisture = min(50.0, req.rainfall_scenario_mm * 0.35)
        added_pore = min(30.0, req.rainfall_scenario_mm * 0.22)
        for step in res["forecast_trajectory"]:
            step["soil_moisture"]["p50"] = round(min(98.0, step["soil_moisture"]["p50"] + added_moisture), 2)
            step["soil_moisture"]["p10"] = round(max(10.0, step["soil_moisture"]["p10"] + added_moisture * 0.8), 2)
            step["soil_moisture"]["p90"] = round(min(99.0, step["soil_moisture"]["p90"] + added_moisture * 1.2), 2)
            step["pore_pressure"]["p50"] = round(min(50.0, step["pore_pressure"]["p50"] + added_pore), 2)
            step["pore_pressure"]["p10"] = round(max(0.5, step["pore_pressure"]["p10"] + added_pore * 0.8), 2)
            step["pore_pressure"]["p90"] = round(min(52.0, step["pore_pressure"]["p90"] + added_pore * 1.2), 2)

    return res
