from datetime import datetime
import json
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from ..database import Base

# 1. ROLES
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # ADMIN, DISASTER_OFFICIAL, FIELD_OFFICER, CITIZEN
    description = Column(String(255), nullable=True)

# 2. USERS
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(60), default="LandSafe")
    last_name = Column(String(60), default="User")
    phone = Column(String(20), nullable=True)
    role = Column(String(50), default="CITIZEN")  # ADMIN, CITIZEN, DISASTER_OFFICIAL, FIELD_OFFICER
    state = Column(String(100), default="Assam")
    city = Column(String(100), default="Guwahati")
    blood_group = Column(String(10), nullable=True)
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    relationship_to_contact = Column(String(50), nullable=True)
    flood_notifications = Column(Boolean, default=True)
    landslide_notifications = Column(Boolean, default=True)
    rainfall_notifications = Column(Boolean, default=True)
    siren_notifications = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 3. LOCATIONS (32 NER Stations)
class Location(Base):
    __tablename__ = "locations"
    id = Column(String(50), primary_key=True, index=True)  # e.g., 'AS-GUWAHATI'
    name = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    population_exposed = Column(Integer, default=0)
    roads_exposed = Column(Integer, default=0)
    critical_assets = Column(Integer, default=0)
    primary_hazard = Column(String(50), default="Landslide")
    created_at = Column(DateTime, default=datetime.utcnow)

# 4. LANDSLIDE EVENTS (Historical NASA NER Records)
class LandslideEvent(Base):
    __tablename__ = "landslide_events"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), nullable=True)
    event_date = Column(String(50), nullable=True)
    location_description = Column(String(255), nullable=True)
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    landslide_category = Column(String(100), default="Landslide")
    landslide_trigger = Column(String(100), default="Rain")
    landslide_size = Column(String(50), default="Medium")
    fatality_count = Column(Integer, default=0)
    injury_count = Column(Integer, default=0)
    source = Column(String(100), default="NASA Landslide Catalog")
    created_at = Column(DateTime, default=datetime.utcnow)

# 5. RAINFALL RECORDS
class RainfallRecord(Base):
    __tablename__ = "rainfall_records"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(String(50), ForeignKey("locations.id"), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    rainfall_1day = Column(Float, default=0.0)
    rainfall_3day = Column(Float, default=0.0)
    rainfall_7day = Column(Float, default=0.0)
    rainfall_30day = Column(Float, default=0.0)
    intensity_mm_h = Column(Float, default=0.0)
    source = Column(String(50), default="Open-Meteo Live")
    recorded_at = Column(DateTime, default=datetime.utcnow)

# 6. SOIL MOISTURE RECORDS
class SoilMoistureRecord(Base):
    __tablename__ = "soil_moisture_records"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(String(50), ForeignKey("locations.id"), nullable=True)
    sensor_id = Column(String(50), nullable=True)
    soil_moisture_pct = Column(Float, nullable=False)
    pore_pressure_kpa = Column(Float, default=0.0)
    soil_saturation = Column(Float, default=0.0)
    temperature_c = Column(Float, default=24.0)
    recorded_at = Column(DateTime, default=datetime.utcnow)

# 7. SENSOR DEVICES
class SensorDevice(Base):
    __tablename__ = "sensor_devices"
    id = Column(String(50), primary_key=True, index=True)  # e.g., 'SN-AR-001'
    name = Column(String(100), nullable=False)
    location_id = Column(String(50), ForeignKey("locations.id"), nullable=True)
    state = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(50), default="Active")  # Active, Low Battery, Offline
    battery_pct = Column(Integer, default=95)
    signal_dbm = Column(Integer, default=-68)
    last_ping = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

# 8. SENSOR READINGS
class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), ForeignKey("sensor_devices.id"), nullable=False, index=True)
    soil_moisture = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    pore_pressure = Column(Float, default=0.0)
    ground_vibration = Column(Float, default=0.0)
    battery_level = Column(Integer, default=95)
    signal_strength = Column(Integer, default=-65)
    is_simulated = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

# 9. TERRAIN FEATURES
class TerrainFeature(Base):
    __tablename__ = "terrain_features"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(String(50), ForeignKey("locations.id"), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation_m = Column(Float, default=500.0)
    slope_deg = Column(Float, default=25.0)
    aspect_deg = Column(Float, default=180.0)
    plan_curvature = Column(Float, default=0.0)
    profile_curvature = Column(Float, default=0.0)
    terrain_ruggedness = Column(Float, default=1.0)
    lithology = Column(String(100), default="Weathered Phyllite/Schist")
    soil_type = Column(String(100), default="Weathered Debris/Talus")
    land_use = Column(String(100), default="Roadside Cut Slope")
    ndvi = Column(Float, default=0.45)
    distance_to_road_m = Column(Float, default=50.0)
    distance_to_fault_m = Column(Float, default=1200.0)
    distance_to_stream_m = Column(Float, default=150.0)

# 10. WEATHER RECORDS
class WeatherRecord(Base):
    __tablename__ = "weather_records"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(String(50), ForeignKey("locations.id"), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    temperature_c = Column(Float, default=24.0)
    humidity_pct = Column(Float, default=80.0)
    rainfall_mm = Column(Float, default=0.0)
    weather_condition = Column(String(100), default="Overcast")
    forecast_risk = Column(String(50), default="Moderate")
    recorded_at = Column(DateTime, default=datetime.utcnow)

# 11. ROADS
class Road(Base):
    __tablename__ = "roads"
    id = Column(String(50), primary_key=True, index=True)  # 'NH-29', 'NH-27'
    name = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    start_point = Column(String(100), nullable=True)
    end_point = Column(String(100), nullable=True)
    status = Column(String(50), default="OPEN")  # OPEN, PARTIALLY_BLOCKED, BLOCKED, UNKNOWN
    blockage_reason = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

# 12. VILLAGES
class Village(Base):
    __tablename__ = "villages"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    population = Column(Integer, default=1500)
    vulnerability_rating = Column(String(50), default="HIGH")
    nearest_shelter = Column(String(100), nullable=True)

# 13. INFRASTRUCTURE (Shelters, Rescue Points, Hospitals)
class Infrastructure(Base):
    __tablename__ = "infrastructure"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # Relief Shelter, Higher Ground Shelter, Emergency Rescue Team
    category = Column(String(50), default="Shelter")  # Shelter, Rescue Point, Hospital
    district = Column(String(100), nullable=True)
    state = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    capacity = Column(Integer, default=200)
    availability = Column(String(50), default="Available")  # Available, Limited, Full
    hazard_safe = Column(String(255), default="Landslide-aware safe zone")
    status = Column(String(50), default="Active")

# 14. RISK PREDICTIONS
class RiskPrediction(Base):
    __tablename__ = "risk_predictions"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(String(50), ForeignKey("locations.id"), nullable=False)
    risk_score = Column(Float, nullable=False)  # 0 to 100
    risk_probability = Column(Float, nullable=False)  # 0.00 to 1.00
    risk_level = Column(String(50), nullable=False)  # LOW, MODERATE, HIGH, CRITICAL
    landslide_risk_pct = Column(Float, default=0.0)
    flood_risk_pct = Column(Float, default=0.0)
    rainfall_factor_pct = Column(Float, default=0.0)
    soil_factor_pct = Column(Float, default=0.0)
    slope_factor_pct = Column(Float, default=0.0)
    water_factor_pct = Column(Float, default=0.0)
    factors_json = Column(Text, nullable=True)  # JSON string of causal factors
    recommendations_json = Column(Text, nullable=True)  # JSON recommendations
    predicted_at = Column(DateTime, default=datetime.utcnow)

# 15. ALERTS
class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String(50), primary_key=True, index=True)  # 'AL-2001'
    location = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)
    hazard_type = Column(String(50), default="Landslide")  # Landslide, Flood, Cloudburst
    severity = Column(String(50), default="High")  # Critical, High, Medium, Low
    status = Column(String(50), default="Active")  # Active, Resolved
    title = Column(String(200), nullable=True)
    message = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)

# 16. FIELD REPORTS (Citizen & Officer Submissions)
class FieldReport(Base):
    __tablename__ = "field_reports"
    id = Column(String(50), primary_key=True, index=True)  # 'LS-2026-12345'
    user_name = Column(String(100), default="Citizen Reporter")
    issue_type = Column(String(50), nullable=False)  # landslide, flood, road, crack, drainage, other
    severity = Column(String(50), default="moderate")  # low, moderate, high, critical
    location_name = Column(String(200), nullable=False)
    state = Column(String(100), nullable=False)
    city = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_emergency = Column(Boolean, default=False)
    status = Column(String(50), default="Pending")  # Pending, Verified, Rejected, Resolved
    media_path = Column(String(255), nullable=True)
    evidence_desc = Column(String(100), default="Photo uploaded by user")
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# 17. UPLOADED MEDIA
class UploadedMedia(Base):
    __tablename__ = "uploaded_media"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("field_reports.id"), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_type = Column(String(50), default="image/jpeg")
    file_size_bytes = Column(Integer, default=0)
    ai_hazard_label = Column(String(100), nullable=True)  # crack, landslide, road_blockage, normal
    ai_confidence = Column(Float, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

# 18. EMERGENCY TASKS (Rescue & Dispatch Priorities)
class EmergencyTask(Base):
    __tablename__ = "emergency_tasks"
    id = Column(String(50), primary_key=True, index=True)  # 'ER-3001'
    user_name = Column(String(100), default="Citizen Requester")
    location = Column(String(200), nullable=False)
    state = Column(String(100), nullable=True)
    request_type = Column(String(50), default="Trapped")  # Trapped, Landslide, Flood, Medical, Other
    priority = Column(String(50), default="High")  # Critical, High, Medium, Low
    status = Column(String(50), default="Pending")  # Pending, Assigned, In Progress, Resolved
    description = Column(Text, nullable=False)
    coordinates = Column(String(100), nullable=True)
    shelter = Column(String(100), nullable=True)
    assigned_team = Column(String(100), nullable=True)
    priority_score = Column(Float, default=50.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 19. NOTIFICATION LOGS (Multilingual Dispatch Log)
class NotificationLog(Base):
    __tablename__ = "notification_logs"
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(50), nullable=True)
    recipient = Column(String(100), nullable=False)
    channel = Column(String(50), default="CONSOLE")  # SMS, EMAIL, PUSH, CONSOLE
    language = Column(String(10), default="en")  # en, hi
    title = Column(String(200), nullable=True)
    message_body = Column(Text, nullable=False)
    delivery_status = Column(String(50), default="SENT")
    sent_at = Column(DateTime, default=datetime.utcnow)

# 20. OFFLINE SYNC QUEUE (Idempotent client synchronization)
class OfflineSyncQueue(Base):
    __tablename__ = "offline_sync_queue"
    id = Column(Integer, primary_key=True, index=True)
    local_id = Column(String(100), unique=True, index=True, nullable=False)
    device_id = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)  # report, sensor_reading, alert_ack
    payload_json = Column(Text, nullable=False)
    sync_status = Column(String(50), default="SYNCED")  # PENDING, SYNCED, CONFLICT
    client_created_at = Column(String(50), nullable=True)
    synced_at = Column(DateTime, default=datetime.utcnow)
