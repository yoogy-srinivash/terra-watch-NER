import os
import json
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from ..app.database import engine, Base, SessionLocal
from ..app.models import (
    Role, User, Location, LandslideEvent, SensorDevice, SensorReading,
    Road, Infrastructure, Alert, FieldReport, EmergencyTask, RainfallRecord,
    SoilMoistureRecord, TerrainFeature, RiskPrediction
)
from ..app.utils.security import hash_password
from ml_pipeline.data_ingestion.landslide_loader import load_nasa_ner_landslides

def seed_database():
    print("Initializing Database tables...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. ROLES
        if db.query(Role).count() == 0:
            print("Seeding Roles...")
            roles = [
                Role(name="ADMIN", description="Disaster System Administrator with full oversight"),
                Role(name="DISASTER_OFFICIAL", description="MDoNER / SDMA Official with alert dispatch authority"),
                Role(name="FIELD_OFFICER", description="On-ground emergency responder and verification officer"),
                Role(name="CITIZEN", description="Community resident with access to alerts and reporting")
            ]
            db.add_all(roles)
            db.commit()

        # 2. USERS
        if db.query(User).count() == 0:
            print("Seeding Default Users...")
            users = [
                # Primary TerraWatch NER accounts
                User(
                    email="admin@terrawatch.in",
                    hashed_password=hash_password("admin123"),
                    first_name="TerraWatch",
                    last_name="Administrator",
                    phone="+919876543200",
                    role="ADMIN",
                    state="Assam",
                    city="Guwahati"
                ),
                User(
                    email="disaster@terrawatch.in",
                    hashed_password=hash_password("disaster123"),
                    first_name="Disaster",
                    last_name="Officer",
                    phone="+919876543201",
                    role="DISASTER_OFFICIAL",
                    state="Meghalaya",
                    city="Shillong"
                ),
                User(
                    email="officer@terrawatch.in",
                    hashed_password=hash_password("officer123"),
                    first_name="Field",
                    last_name="Inspector",
                    phone="+919876543202",
                    role="FIELD_OFFICER",
                    state="Mizoram",
                    city="Aizawl"
                ),
                User(
                    email="citizen@terrawatch.in",
                    hashed_password=hash_password("citizen123"),
                    first_name="Community",
                    last_name="Citizen",
                    phone="+919876543203",
                    role="CITIZEN",
                    state="Assam",
                    city="Guwahati",
                    emergency_contact_name="Family Contact",
                    emergency_contact_phone="+919876543299",
                    blood_group="O+"
                ),
                # Legacy / Backwards-compatible aliases
                User(
                    email="admin@landsafe.gov.in",
                    hashed_password=hash_password("admin123"),
                    first_name="Admin",
                    last_name="Commander",
                    phone="+919876543210",
                    role="ADMIN",
                    state="Assam",
                    city="Guwahati"
                ),
                User(
                    email="official@landsafe.gov.in",
                    hashed_password=hash_password("official123"),
                    first_name="Disaster",
                    last_name="Official",
                    phone="+919876543211",
                    role="DISASTER_OFFICIAL",
                    state="Meghalaya",
                    city="Shillong"
                ),
                User(
                    email="field@landsafe.gov.in",
                    hashed_password=hash_password("field123"),
                    first_name="Field",
                    last_name="Inspector",
                    phone="+919876543212",
                    role="FIELD_OFFICER",
                    state="Mizoram",
                    city="Aizawl"
                ),
                User(
                    email="landsafe.user@example.com",
                    hashed_password=hash_password("user123"),
                    first_name="LandSafe",
                    last_name="User",
                    phone="+919876543213",
                    role="CITIZEN",
                    state="Assam",
                    city="Guwahati",
                    emergency_contact_name="Family Contact",
                    emergency_contact_phone="+919876543299",
                    blood_group="O+"
                )
            ]
            db.add_all(users)
            db.commit()

        # 3. LOCATIONS (from gis/locations.json)
        base_dir = Path(__file__).resolve().parent.parent.parent
        locations_file = base_dir / "gis" / "locations.json"
        
        if db.query(Location).count() == 0 and locations_file.exists():
            print("Seeding 32 NER Monitored Stations from gis/locations.json...")
            with open(locations_file, "r", encoding="utf-8") as f:
                loc_data = json.load(f)
                
            for item in loc_data:
                loc = Location(
                    id=item["id"],
                    name=item["location"],
                    district=item["district"],
                    state=item["state"],
                    latitude=float(item["latitude"]),
                    longitude=float(item["longitude"]),
                    population_exposed=int(item.get("population_exposed", 0)),
                    roads_exposed=int(item.get("roads_exposed", 0)),
                    critical_assets=int(item.get("critical_assets", 0)),
                    primary_hazard="Flood" if item["location"] in ["Guwahati", "Agartala", "Silchar", "Goalpara", "Belonia"] else "Landslide"
                )
                db.add(loc)
            db.commit()

        # 3.1 TERRAIN FEATURES (for 32 Monitored Stations)
        if db.query(TerrainFeature).count() == 0 and locations_file.exists():
            print("Seeding Grounded Terrain Features for Monitored Stations...")
            with open(locations_file, "r", encoding="utf-8") as f:
                loc_data = json.load(f)
            for item in loc_data:
                tf = TerrainFeature(
                    location_id=item["id"],
                    latitude=float(item["latitude"]),
                    longitude=float(item["longitude"]),
                    elevation_m=float(item.get("elevation_m", 500.0)),
                    slope_deg=float(item.get("slope_angle_deg", 25.0)),
                    aspect_deg=float(item.get("aspect_deg", 180.0)),
                    plan_curvature=float(item.get("plan_curvature", 0.0)),
                    profile_curvature=float(item.get("profile_curvature", 0.0)),
                    terrain_ruggedness=1.0,
                    lithology=str(item.get("lithology", "Weathered Phyllite/Schist")),
                    soil_type=str(item.get("soil_type", "Weathered Debris/Talus")),
                    land_use=str(item.get("land_use", "Roadside Cut Slope")),
                    ndvi=float(item.get("ndvi", 0.45)),
                    distance_to_road_m=float(item.get("distance_to_road_m", 50.0)),
                    distance_to_fault_m=float(item.get("distance_to_fault_m", 1200.0)),
                    distance_to_stream_m=float(item.get("distance_to_stream_m", 150.0))
                )
                db.add(tf)
            db.commit()
            print(f"Added {len(loc_data)} grounded TerrainFeature records.")

        # 4. HISTORICAL LANDSLIDE EVENTS (from NASA Catalog)
        if db.query(LandslideEvent).count() == 0:
            print("Seeding NASA Historical Landslides...")
            nasa_records = load_nasa_ner_landslides()
            if nasa_records:
                for rec in nasa_records:
                    ev = LandslideEvent(
                        event_id=rec["event_id"],
                        event_date=rec["event_date"],
                        location_description=rec["location_description"],
                        state=rec["state"],
                        district=rec["district"],
                        latitude=rec["latitude"],
                        longitude=rec["longitude"],
                        landslide_category=rec["landslide_category"],
                        landslide_trigger=rec["landslide_trigger"],
                        landslide_size=rec["landslide_size"],
                        fatality_count=rec["fatality_count"],
                        injury_count=rec["injury_count"],
                        source=rec["source"]
                    )
                    db.add(ev)
                db.commit()
                print(f"Added {len(nasa_records)} historical landslide records.")

        # 5. SENSOR STATIONS & TELEMETRY
        if db.query(SensorDevice).count() == 0:
            print("Seeding IoT Sensor Stations across 8 NER states...")
            sensors_seed = [
                {"id": "SN-AS-001", "name": "Guwahati Hill Sensor 1", "loc": "AS-GUWAHATI", "state": "Assam", "lat": 26.155, "lon": 91.745, "sm": 84.0, "p": 28.5},
                {"id": "SN-ML-001", "name": "Shillong Peak Sensor 1", "loc": "ML-SHILLONG", "state": "Meghalaya", "lat": 25.568, "lon": 91.885, "sm": 78.5, "p": 24.0},
                {"id": "SN-MZ-001", "name": "Aizawl Slope Sensor 1", "loc": "MZ-AIZAWL", "state": "Mizoram", "lat": 23.731, "lon": 92.712, "sm": 71.0, "p": 19.5},
                {"id": "SN-SK-001", "name": "Gangtok Highway Sensor 1", "loc": "SK-GANGTOK", "state": "Sikkim", "lat": 27.342, "lon": 88.612, "sm": 62.0, "p": 14.0},
                {"id": "SN-NL-001", "name": "Kohima Ridge Sensor 1", "loc": "NL-KOHIMA", "state": "Nagaland", "lat": 25.680, "lon": 94.112, "sm": 56.5, "p": 11.2},
                {"id": "SN-MN-001", "name": "Ukhrul Mountain Sensor 1", "loc": "MN-UKHRUL", "state": "Manipur", "lat": 25.102, "lon": 94.368, "sm": 68.0, "p": 18.0},
                {"id": "SN-AR-001", "name": "Tawang Pass Sensor 1", "loc": "AR-TAWANG", "state": "Arunachal Pradesh", "lat": 27.592, "lon": 91.865, "sm": 58.0, "p": 12.0},
                {"id": "SN-TR-001", "name": "Agartala Lowland Sensor 1", "loc": "TR-AGARTALA", "state": "Tripura", "lat": 23.835, "lon": 91.292, "sm": 74.0, "p": 20.0}
            ]
            for s in sensors_seed:
                dev = SensorDevice(
                    id=s["id"],
                    name=s["name"],
                    location_id=s["loc"],
                    state=s["state"],
                    latitude=s["lat"],
                    longitude=s["lon"],
                    status="Active",
                    battery_pct=95,
                    signal_dbm=-65,
                    last_ping=datetime.utcnow()
                )
                db.add(dev)
                
                # Add initial telemetry reading
                reading = SensorReading(
                    sensor_id=s["id"],
                    soil_moisture=s["sm"],
                    temperature=22.5,
                    pore_pressure=s["p"],
                    ground_vibration=0.003,
                    battery_level=95,
                    signal_strength=-65,
                    is_simulated=True,
                    timestamp=datetime.utcnow()
                )
                db.add(reading)
            db.commit()

        # 6. INFRASTRUCTURE (Shelters & Rescue Points matching UI)
        if db.query(Infrastructure).count() == 0:
            print("Seeding Emergency Shelters & Rescue Points...")
            infras = [
                Infrastructure(id="shelter1", name="Guwahati Relief Shelter", type="Emergency Relief Centre", category="Shelter", state="Assam", latitude=26.1550, longitude=91.7500, capacity=250, availability="Available", hazard_safe="Flood-safe elevated shelter"),
                Infrastructure(id="shelter2", name="Shillong Higher Ground Shelter", type="Higher Ground Shelter", category="Shelter", state="Meghalaya", latitude=25.5900, longitude=91.8800, capacity=180, availability="Available", hazard_safe="Landslide-aware safe zone"),
                Infrastructure(id="shelter3", name="Aizawl Community Relief Centre", type="Relief Shelter", category="Shelter", state="Mizoram", latitude=23.7350, longitude=92.7300, capacity=150, availability="Limited", hazard_safe="Emergency relocation centre"),
                Infrastructure(id="shelter4", name="Agartala Emergency Shelter", type="Emergency Relief Centre", category="Shelter", state="Tripura", latitude=23.8400, longitude=91.3000, capacity=220, availability="Available", hazard_safe="Flood evacuation shelter"),
                Infrastructure(id="rescue1", name="Guwahati Rescue Point", type="Emergency Rescue Team", category="Rescue Point", state="Assam", latitude=26.1350, longitude=91.7250, capacity=50, availability="Available", status="Active"),
                Infrastructure(id="rescue2", name="Shillong Rescue Point", type="Mountain Rescue Team", category="Rescue Point", state="Meghalaya", latitude=25.5700, longitude=91.9050, capacity=40, availability="Available", status="Active"),
                Infrastructure(id="rescue3", name="Aizawl Rescue Point", type="Emergency Response Team", category="Rescue Point", state="Mizoram", latitude=23.7150, longitude=92.7000, capacity=35, availability="Available", status="Active")
            ]
            db.add_all(infras)
            db.commit()

        # 7. ROADS (NER Key Transport Lifelines)
        if db.query(Road).count() == 0:
            print("Seeding NER Strategic Highway Corridors...")
            roads = [
                Road(id="NH-29", name="NH-29 Kohima-Dimapur Corridor", state="Nagaland", start_point="Dimapur", end_point="Kohima", status="PARTIALLY_BLOCKED", blockage_reason="Debris flow at km 38", latitude=25.75, longitude=93.90),
                Road(id="NH-27", name="NH-27 East-West Guwahati Corridor", state="Assam", start_point="Guwahati", end_point="Silchar", status="OPEN", blockage_reason=None, latitude=26.12, longitude=91.80),
                Road(id="NH-10", name="NH-10 Siliguri-Gangtok Highway", state="Sikkim", start_point="Siliguri", end_point="Gangtok", status="BLOCKED", blockage_reason="Major rockfall near Teesta bridge", latitude=27.18, longitude=88.45),
                Road(id="NH-53", name="NH-53 Imphal-Silchar Highway", state="Manipur", start_point="Silchar", end_point="Imphal", status="PARTIALLY_BLOCKED", blockage_reason="Slope slip near Noney", latitude=24.78, longitude=93.55),
                Road(id="NH-54", name="NH-54 Aizawl Arterial Route", state="Mizoram", start_point="Silchar", end_point="Aizawl", status="OPEN", blockage_reason=None, latitude=23.85, longitude=92.75),
                Road(id="NH-44", name="NH-44 Shillong-Agartala Highway", state="Meghalaya", start_point="Shillong", end_point="Agartala", status="OPEN", blockage_reason=None, latitude=25.30, longitude=92.15)
            ]
            db.add_all(roads)
            db.commit()

        # 8. ALERTS (matching existing ui/admin-alerts.js)
        if db.query(Alert).count() == 0:
            print("Seeding Initial Active & Resolved Alerts...")
            alerts = [
                Alert(id="AL-2001", location="Guwahati, Assam", state="Assam", hazard_type="Flood", severity="Critical", status="Active", title="Critical Flood Alert", message="Water level has increased rapidly in low-lying zones.", latitude=26.1445, longitude=91.7362),
                Alert(id="AL-2002", location="Shillong, Meghalaya", state="Meghalaya", hazard_type="Landslide", severity="High", status="Active", title="High Landslide Alert", message="Cracks and ground displacement observed on roadside slopes.", latitude=25.5788, longitude=91.8933),
                Alert(id="AL-2003", location="Aizawl, Mizoram", state="Mizoram", hazard_type="Landslide", severity="High", status="Active", title="High Slope Instability Warning", message="Soil saturation exceeds threshold on unstable hillside sectors.", latitude=23.7271, longitude=92.7176),
                Alert(id="AL-2004", location="Agartala, Tripura", state="Tripura", hazard_type="Flood", severity="Medium", status="Active", title="Moderate Inundation Watch", message="River water levels monitoring active.", latitude=23.8315, longitude=91.2868),
                Alert(id="AL-2005", location="Imphal, Manipur", state="Manipur", hazard_type="Flood", severity="Medium", status="Resolved", title="Water Level Normalized", message="Resolved following drainage clearance.", latitude=24.8170, longitude=93.9368),
                Alert(id="AL-2006", location="Kohima, Nagaland", state="Nagaland", hazard_type="Landslide", severity="Low", status="Resolved", title="Minor Rockfall Cleared", message="Debris cleared by BRO highway crew.", latitude=25.6751, longitude=94.1086),
                Alert(id="AL-2007", location="Itanagar, Arunachal Pradesh", state="Arunachal Pradesh", hazard_type="Flood", severity="Low", status="Resolved", title="Normal Monitoring Resumed", message="Cleared without structural incident.", latitude=27.0844, longitude=93.6053)
            ]
            db.add_all(alerts)
            db.commit()

        # 9. FIELD REPORTS (matching ui/user-reports.js)
        if db.query(FieldReport).count() == 0:
            print("Seeding Initial Field Reports...")
            reports = [
                FieldReport(id="LS-1048", user_name="Rahul Sharma", issue_type="flood", severity="critical", location_name="Guwahati, Assam", state="Assam", city="Guwahati", description="Water level has increased near the residential area and several roads are becoming impassable.", is_emergency=True, status="Pending", latitude=26.1445, longitude=91.7362),
                FieldReport(id="LS-1047", user_name="Ananya Das", issue_type="landslide", severity="high", location_name="Shillong, Meghalaya", state="Meghalaya", city="Shillong", description="Large structural cracks and loose soil observed near the hillside road.", is_emergency=False, status="Verified", latitude=25.5788, longitude=91.8933),
                FieldReport(id="LS-1046", user_name="Mizoram Citizen", issue_type="landslide", severity="high", location_name="Aizawl, Mizoram", state="Mizoram", city="Aizawl", description="Rock and soil movement has been observed near a local road.", is_emergency=False, status="Pending", latitude=23.7271, longitude=92.7176),
                FieldReport(id="LS-1045", user_name="Priya Singh", issue_type="road", severity="moderate", location_name="Gangtok, Sikkim", state="Sikkim", city="Gangtok", description="Mud and debris have partially blocked the road after heavy rainfall.", is_emergency=False, status="Verified", latitude=27.3389, longitude=88.6065)
            ]
            db.add_all(reports)
            db.commit()

        # 10. EMERGENCY TASKS (matching ui/emergency-requests.js)
        if db.query(EmergencyTask).count() == 0:
            print("Seeding Emergency Rescue Tasks...")
            tasks = [
                EmergencyTask(id="ER-3008", user_name="Rahul Sharma", location="Guwahati, Assam", state="Assam", request_type="Trapped", priority="Critical", status="Pending", description="User reports being trapped inside a flooded residential area and requests immediate rescue assistance.", coordinates="26.1445, 91.7362", shelter="Guwahati Relief Shelter", priority_score=92.0),
                EmergencyTask(id="ER-3007", user_name="Ananya Das", location="Shillong, Meghalaya", state="Meghalaya", request_type="Landslide", priority="Critical", status="In Progress", description="A landslide has blocked the nearby road and user reports unsafe conditions around residence.", coordinates="25.5788, 91.8933", shelter="Shillong Higher Ground Shelter", assigned_team="SDRF Team 1", priority_score=88.5),
                EmergencyTask(id="ER-3006", user_name="Mizoram Citizen", location="Aizawl, Mizoram", state="Mizoram", request_type="Trapped", priority="High", status="Assigned", description="User reports being unable to safely leave affected area because of soil and rock movement.", coordinates="23.7271, 92.7176", shelter="Aizawl Community Relief Centre", assigned_team="NDRF Unit 3", priority_score=75.0),
                EmergencyTask(id="ER-3005", user_name="Priya Singh", location="Gangtok, Sikkim", state="Sikkim", request_type="Medical", priority="High", status="In Progress", description="Medical assistance requested after a person was injured near a landslide-affected road.", coordinates="27.3389, 88.6065", shelter="Nearby Emergency Shelter", assigned_team="Medical Quick Reaction Team", priority_score=81.0)
            ]
            db.add_all(tasks)
            db.commit()

        print("Database Seeding Completed Successfully!")
    except Exception as e:
        db.rollback()
        print(f"Database seeding error: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
