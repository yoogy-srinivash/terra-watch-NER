import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse

# Ensure root directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.services.ml_service import ml_service
from backend.app.routers import (
    auth, risk, gis, sensors, reports, alerts,
    emergency, roads, weather, analytics, sync, admin
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    print("[TerraWatch] Initializing TerraWatch NER System...")
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed baseline data if database is empty
    try:
        from backend.data.seed_data import seed_database
        seed_database()
    except Exception as e:
        print(f"[TerraWatch] Notice on database seeding: {e}")

    # Preload ML model
    print("[TerraWatch] Pre-loading ML ensemble risk model...")
    ml_service.load_model()
    
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    print(f"[TerraWatch] Uploads directory ready at: {settings.UPLOAD_DIR}")
    
    print("[TerraWatch] System initialized successfully. Ready to serve early warning requests.")
    yield
    print("[TerraWatch] Shutting down TerraWatch NER System...")

app = FastAPI(
    title="TerraWatch NER - Academic Multi-Modal AI Landslide Risk System",
    description="Academic multi-modal AI prototype for landslide risk assessment developed for the IMDAI course (concept inspired by SIH NER landslide risk problem statement).",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register All API Routers
app.include_router(auth.router)
app.include_router(risk.router)
app.include_router(gis.router)
app.include_router(sensors.router)
app.include_router(reports.router)
app.include_router(alerts.router)
app.include_router(emergency.router)
app.include_router(roads.router)
app.include_router(weather.router)
app.include_router(analytics.router)
app.include_router(sync.router)
app.include_router(admin.router)

# Mount Uploads
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Mount UI static directory
UI_DIR = BASE_DIR / "ui"
if UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")

# Mount GIS static directory for locations.json and geojson files
GIS_DIR = BASE_DIR / "gis"
if GIS_DIR.exists():
    app.mount("/gis", StaticFiles(directory=str(GIS_DIR)), name="gis")

@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root access directly to TerraWatch Citizen Dashboard."""
    return RedirectResponse(url="/ui/index.html")

@app.get("/health", tags=["System Health"])
@app.get("/api/health", tags=["System Health"])
def health_check():
    """System health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "TerraWatch NER Early Warning Engine",
        "region": "North Eastern Region (Assam, Meghalaya, Mizoram, Sikkim, Arunachal Pradesh, Nagaland, Manipur, Tripura)",
        "ml_model_status": "LOADED" if ml_service.model is not None else "STANDBY",
        "environment": "Development / SIH 2026 Demo"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
