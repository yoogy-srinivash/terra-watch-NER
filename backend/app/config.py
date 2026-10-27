import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "TerraWatch NER - IMDAI Academic Prototype"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    DEMO_MODE: bool = True
    API_PREFIX: str = "/api"

    # Security & Auth: SECRET_KEY must be supplied via environment variable or .env file.
    # No hardcoded fallback secret is permitted in the source code.
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Database
    DATABASE_URL: str = "sqlite:///./terrawatch.db"

    # Uploads & Storage
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    MAX_UPLOAD_SIZE_MB: int = 25

    # Models & Data
    MODELS_DIR: str = str(BASE_DIR / "models")
    DATA_DIR: str = str(BASE_DIR / "data")

    # External APIs
    WEATHER_API_URL: str = "https://api.open-meteo.com/v1/forecast"

    # Notifications
    SMS_PROVIDER: str = "console"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_PHONE: str = ""
    DEFAULT_LANGUAGE: str = "en"

    # Risk Thresholds
    RISK_THRESHOLD_LOW: float = 0.20
    RISK_THRESHOLD_MODERATE: float = 0.40
    RISK_THRESHOLD_HIGH: float = 0.60
    RISK_THRESHOLD_CRITICAL: float = 0.80

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Ensure required runtime directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.MODELS_DIR, exist_ok=True)
os.makedirs(settings.DATA_DIR, exist_ok=True)
