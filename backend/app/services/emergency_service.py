from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models import EmergencyTask, FieldReport, Location

SEVERITY_WEIGHTS = {
    "Critical": 100.0,
    "critical": 100.0,
    "High": 75.0,
    "high": 75.0,
    "Medium": 50.0,
    "moderate": 50.0,
    "Low": 25.0,
    "low": 25.0
}

RECOMMENDED_ACTIONS = {
    "Trapped": "Deploy NDRF/SDRF specialized evacuation team with high-clearance rescue vehicles.",
    "Landslide": "Dispatch Road Clearance Battalion & establish geotechnical safety perimeter.",
    "Flood": "Deploy Inflatable Motorized Rescue Boats & activate flood shelter relocation.",
    "Medical": "Immediate deployment of Quick Reaction Medical Ambulances with trauma kit.",
    "Road Blockage": "Deploy BRO / PWD heavy earthmovers for emergency corridor opening.",
    "Other": "Deploy local civil defense volunteers for on-site safety assessment."
}

def calculate_priority_score(task: EmergencyTask, loc: Location = None) -> float:
    base_sev = SEVERITY_WEIGHTS.get(task.priority, 50.0)
    pop_factor = min(100.0, (loc.population_exposed / 1000.0)) if loc else 40.0
    roads_factor = min(100.0, (loc.roads_exposed * 15.0)) if loc else 30.0
    
    # Composite priority calculation
    score = (0.50 * base_sev) + (0.30 * pop_factor) + (0.20 * roads_factor)
    return round(score, 1)

def get_emergency_priorities(db: Session) -> List[Dict[str, Any]]:
    tasks = db.query(EmergencyTask).order_by(EmergencyTask.created_at.desc()).all()
    priorities = []

    for t in tasks:
        loc = db.query(Location).filter(Location.name.ilike(f"%{t.location.split(',')[0]}%")).first()
        score = calculate_priority_score(t, loc)
        
        action = RECOMMENDED_ACTIONS.get(t.request_type, "Deploy local response unit and assess ground stability.")
        
        reason = f"High risk event ({t.request_type}) in {t.location}."
        if loc and loc.population_exposed > 10000:
            reason += f" Affects approx {loc.population_exposed:,} residents with {loc.roads_exposed} transport links."

        priorities.append({
            "id": t.id,
            "user": t.user_name,
            "location": t.location,
            "state": t.state or (loc.state if loc else "NER Region"),
            "request_type": t.request_type,
            "priority": t.priority,
            "status": t.status,
            "priority_score": score,
            "affected_population": loc.population_exposed if loc else 5000,
            "reason": reason,
            "recommended_action": action,
            "description": t.description,
            "coordinates": t.coordinates,
            "shelter": t.shelter or "Designated NER Community Shelter",
            "assigned_team": t.assigned_team or "Pending Assignment",
            "submitted": t.created_at.strftime("%b %d, %I:%M %p")
        })

    # Sort descending by priority score
    priorities.sort(key=lambda x: x["priority_score"], reverse=True)
    return priorities
class EmergencyService:
    @staticmethod
    def calculate_rescue_priorities(db: Session) -> List[Dict[str, Any]]:
        return get_emergency_priorities(db)

emergency_service = EmergencyService()
