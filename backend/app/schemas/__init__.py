from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

# AUTH SCHEMAS
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str = "LandSafe"
    last_name: str = "User"
    phone: Optional[str] = None
    role: str = "CITIZEN"
    state: str = "Assam"
    city: str = "Guwahati"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserProfile(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    role: str
    state: str
    city: str
    blood_group: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    relationship_to_contact: Optional[str] = None
    flood_notifications: bool = True
    landslide_notifications: bool = True
    rainfall_notifications: bool = True
    siren_notifications: bool = True

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    relationship_to_contact: Optional[str] = None
    flood_notifications: Optional[bool] = None
    landslide_notifications: Optional[bool] = None
    rainfall_notifications: Optional[bool] = None
    siren_notifications: Optional[bool] = None

# RISK PREDICTION SCHEMAS
class PredictionRequest(BaseModel):
    latitude: float = Field(..., ge=21.0, le=30.0, description="Latitude in North Eastern Region")
    longitude: float = Field(..., ge=88.0, le=98.0, description="Longitude in North Eastern Region")
    state: Optional[str] = "Assam"
    district: Optional[str] = "Kamrup Metro"
    rainfall_24h_mm: Optional[float] = None
    rainfall_72h_mm: Optional[float] = None
    soil_moisture_pct: Optional[float] = None
    slope_angle_deg: Optional[float] = None
    elevation_m: Optional[float] = None
    distance_to_road_m: Optional[float] = None

class RiskFactor(BaseModel):
    factor: str
    status: str
    value: Any
    severity: str

class PredictionResponse(BaseModel):
    risk_score: float  # 0 to 100
    risk_probability: float  # 0.0 to 1.0
    risk_level: str  # LOW, MODERATE, HIGH, CRITICAL
    location: Dict[str, Any]
    environmental_features: Dict[str, Any]
    contributing_factors: List[str]
    recommendations: List[str]
    alert_summary: Dict[str, str]
    model_version: str
    timestamp: datetime

# SENSOR SCHEMAS
class SensorDataSubmission(BaseModel):
    sensor_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    soil_moisture: float = Field(..., ge=0.0, le=100.0)
    temperature: float = Field(default=24.0, ge=-20.0, le=60.0)
    pore_pressure: Optional[float] = 0.0
    ground_vibration: Optional[float] = 0.0
    battery_level: Optional[int] = Field(default=95, ge=0, le=100)
    signal_strength: Optional[int] = Field(default=-65, ge=-120, le=0)
    is_simulated: bool = True
    timestamp: Optional[datetime] = None

class SensorResponse(BaseModel):
    id: str
    name: str
    state: str
    latitude: float
    longitude: float
    status: str
    battery_pct: int
    signal_dbm: int
    last_reading: Optional[Dict[str, Any]] = None

# FIELD REPORT SCHEMAS
class ReportCreate(BaseModel):
    issue_type: str  # landslide, flood, road, crack, drainage, other
    severity: str = "moderate"  # low, moderate, high, critical
    location: str
    state: str
    city: Optional[str] = ""
    description: str
    is_emergency: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ReportResponse(BaseModel):
    id: str
    user_name: str
    issue_type: str
    severity: str
    location_name: str
    state: str
    city: Optional[str]
    description: str
    is_emergency: bool
    status: str
    evidence_desc: str
    media_url: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    created_at: datetime

class ReportStatusUpdate(BaseModel):
    status: str  # Verified, Rejected, Resolved

# ALERT SCHEMAS
class AlertCreate(BaseModel):
    location: str
    state: Optional[str] = None
    hazard_type: str = "Landslide"
    severity: str = "High"  # Critical, High, Medium, Low
    title: Optional[str] = None
    message: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class AlertResponse(BaseModel):
    id: str
    location: str
    state: Optional[str]
    hazard_type: str
    severity: str
    status: str
    title: Optional[str]
    message: Optional[str]
    time: str
    created_at: datetime

# EMERGENCY SCHEMAS
class EmergencyStatusUpdate(BaseModel):
    status: str  # Assigned, In Progress, Resolved
    assigned_team: Optional[str] = None

class EmergencyPriorityItem(BaseModel):
    id: str
    location: str
    state: str
    request_type: str
    priority: str
    status: str
    priority_score: float
    affected_population: int
    recommended_action: str
    reason: str
    coordinates: Optional[str]
    shelter: Optional[str]

# OFFLINE SYNC SCHEMAS
class SyncPushItem(BaseModel):
    local_id: str
    device_id: str
    entity_type: str  # report, sensor_reading, alert_ack
    payload: Dict[str, Any]
    client_created_at: Optional[str] = None

class SyncPushRequest(BaseModel):
    items: List[SyncPushItem]

class SyncPushResultItem(BaseModel):
    local_id: str
    server_id: Optional[str]
    status: str  # SUCCESS, DUPLICATE, ERROR
    message: str

class SyncPushResponse(BaseModel):
    processed: int
    successful: int
    results: List[SyncPushResultItem]
