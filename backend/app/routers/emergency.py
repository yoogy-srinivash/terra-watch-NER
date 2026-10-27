from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.app.database import get_db
from backend.app.models import EmergencyTask, User
from backend.app.schemas import EmergencyStatusUpdate, EmergencyPriorityItem
from backend.app.services.emergency_service import emergency_service
from backend.app.utils.security import get_optional_current_user

router = APIRouter(prefix="/api/emergency", tags=["Emergency Response & Rescue Dispatch"])

@router.get("/requests")
def get_emergency_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Retrieve all emergency assistance requests submitted across the NER region."""
    query = db.query(EmergencyTask)
    if status_filter and status_filter.lower() != "all":
        query = query.filter(EmergencyTask.status.ilike(f"%{status_filter}%"))
    if priority and priority.lower() != "all":
        query = query.filter(EmergencyTask.priority.ilike(f"%{priority}%"))
    
    tasks = query.order_by(EmergencyTask.created_at.desc()).limit(limit).all()
    results = []
    for t in tasks:
        submitted_str = t.created_at.strftime("%I:%M %p") if t.created_at else "Earlier"
        results.append({
            "id": t.id,
            "user": t.user_name,
            "location": t.location,
            "state": t.state,
            "type": t.request_type,
            "priority": t.priority,
            "status": t.status,
            "submitted": f"Today, {submitted_str}",
            "description": t.description,
            "coordinates": t.coordinates or "26.1445, 91.7362",
            "shelter": t.shelter or "Nearest District Relief Shelter",
            "assigned_team": t.assigned_team,
            "priority_score": t.priority_score
        })
    return results

@router.get("/priorities")
def get_emergency_priorities(db: Session = Depends(get_db)):
    """
    Returns automated multi-criteria rescue priorities:
    Rank = 0.50 * Hazard_Severity + 0.30 * Exposed_Population + 0.20 * Critical_Road_Vulnerability
    """
    priorities = emergency_service.calculate_rescue_priorities(db)
    return priorities

@router.patch("/requests/{task_id}/status")
def update_emergency_status(
    task_id: str,
    payload: EmergencyStatusUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Update status and assigned response team for an emergency task."""
    task = db.query(EmergencyTask).filter(EmergencyTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Emergency task {task_id} not found")
    
    task.status = payload.status
    if payload.assigned_team:
        task.assigned_team = payload.assigned_team
    elif not task.assigned_team and payload.status in ["Assigned", "In Progress"]:
        task.assigned_team = "SDRF Rapid Response Unit 1"
        
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    
    return {
        "status": "success",
        "message": f"Task {task_id} status updated to {task.status}",
        "id": task.id,
        "new_status": task.status,
        "assigned_team": task.assigned_team
    }

@router.post("/requests", status_code=status.HTTP_201_CREATED)
def create_emergency_request(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Submit a new emergency SOS rescue request."""
    task_id = f"ER-{int(datetime.utcnow().timestamp()) % 10000 + 3000}"
    user_name = data.get("user") or (f"{current_user.first_name} {current_user.last_name}" if current_user else "Citizen Requester")
    location = data.get("location", "Guwahati, Assam")
    req_type = data.get("type", "Trapped")
    priority = data.get("priority", "High")
    desc = data.get("description", "Emergency assistance requested due to hazard conditions.")
    coords = data.get("coordinates", "26.1445, 91.7362")
    shelter = data.get("shelter", "District Relief Shelter")
    state = data.get("state")
    if not state and "," in location:
        state = location.split(",")[-1].strip()
    else:
        state = state or "Assam"
        
    new_task = EmergencyTask(
        id=task_id,
        user_name=user_name,
        location=location,
        state=state,
        request_type=req_type,
        priority=priority,
        status="Pending",
        description=desc,
        coordinates=coords,
        shelter=shelter,
        priority_score=85.0 if priority == "Critical" else 70.0,
        created_at=datetime.utcnow()
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    return {
        "status": "success",
        "message": "Emergency dispatch request created successfully",
        "id": new_task.id,
        "task": {
            "id": new_task.id,
            "user": new_task.user_name,
            "location": new_task.location,
            "priority": new_task.priority,
            "status": new_task.status
        }
    }
