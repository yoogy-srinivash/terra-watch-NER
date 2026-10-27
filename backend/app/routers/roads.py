from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from backend.app.database import get_db
from backend.app.models import Road, User
from backend.app.utils.security import get_optional_current_user

router = APIRouter(prefix="/api/roads", tags=["Critical Infrastructure & Road Corridors"])

class RoadStatusUpdate(BaseModel):
    status: str  # OPEN, PARTIALLY_BLOCKED, BLOCKED
    blockage_reason: Optional[str] = None

class RoadCreate(BaseModel):
    id: str
    name: str
    state: str
    start_point: Optional[str] = None
    end_point: Optional[str] = None
    status: str = "OPEN"
    blockage_reason: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

@router.get("")
def get_roads(
    state: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve all critical highway and lifeline transportation corridors in NER."""
    query = db.query(Road)
    if state and state.lower() != "all":
        query = query.filter(Road.state.ilike(f"%{state}%"))
    if status_filter and status_filter.lower() != "all":
        query = query.filter(Road.status.ilike(f"%{status_filter}%"))
    
    roads = query.all()
    results = []
    for r in roads:
        results.append({
            "id": r.id,
            "name": r.name,
            "state": r.state,
            "start_point": r.start_point,
            "end_point": r.end_point,
            "status": r.status,
            "blockage_reason": r.blockage_reason,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None
        })
    return results

@router.get("/{road_id}")
def get_road_detail(road_id: str, db: Session = Depends(get_db)):
    """Retrieve specific road corridor details."""
    road = db.query(Road).filter(Road.id == road_id).first()
    if not road:
        raise HTTPException(status_code=404, detail=f"Road corridor {road_id} not found")
    return {
        "id": road.id,
        "name": road.name,
        "state": road.state,
        "start_point": road.start_point,
        "end_point": road.end_point,
        "status": road.status,
        "blockage_reason": road.blockage_reason,
        "latitude": road.latitude,
        "longitude": road.longitude,
        "updated_at": road.updated_at.isoformat() if road.updated_at else None
    }

@router.patch("/{road_id}/status")
def update_road_status(
    road_id: str,
    payload: RoadStatusUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Update status (OPEN, PARTIALLY_BLOCKED, BLOCKED) for a road corridor."""
    road = db.query(Road).filter(Road.id == road_id).first()
    if not road:
        raise HTTPException(status_code=404, detail=f"Road corridor {road_id} not found")
    
    road.status = payload.status.upper()
    if payload.blockage_reason is not None:
        road.blockage_reason = payload.blockage_reason
    road.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(road)
    
    return {
        "status": "success",
        "message": f"Road {road_id} status updated to {road.status}",
        "road": {
            "id": road.id,
            "name": road.name,
            "status": road.status,
            "blockage_reason": road.blockage_reason
        }
    }
