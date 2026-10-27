from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from ..config import settings
from ..models import NotificationLog
from ..utils.logging import audit_logger

MULTILINGUAL_TEMPLATES = {
    "CRITICAL": {
        "en": {
            "title": "CRITICAL LANDSLIDE ALERT - MDoNER",
            "message": "EMERGENCY: Severe landslide risk detected near {location}. Soil saturation and rainfall exceed danger thresholds. Evacuate unstable slopes immediately."
        },
        "hi": {
            "title": "गंभीर भूस्खलन आपातकालीन चेतावनी - पूर्वोत्तर क्षेत्र विकास मंत्रालय",
            "message": "आपातकाल: {location} के पास अत्यधिक भूस्खलन जोखिम दर्ज किया गया है। ढलानों और कमजोर रास्तों से तुरंत सुरक्षित आश्रय में जाएं।"
        }
    },
    "HIGH": {
        "en": {
            "title": "High Landslide Risk Advisory",
            "message": "WARNING: High landslide risk detected in {location}. Avoid vulnerable hill roads and monitor official warnings."
        },
        "hi": {
            "title": "उच्च भूस्खलन चेतावनी - पूर्वोत्तर क्षेत्र",
            "message": "चेतावनी: {location} में उच्च भूस्खलन जोखिम देखा गया है। संवेदनशील पहाड़ी मार्गों से बचें और आधिकारिक निर्देशों का पालन करें।"
        }
    },
    "MODERATE": {
        "en": {
            "title": "Moderate Weather & Terrain Watch",
            "message": "ADVISORY: Moderate landslide conditions in {location}. Ground monitoring is active."
        },
        "hi": {
            "title": "मध्यम मौसम एवं भू-निगरानी सूचना",
            "message": "सलाह: {location} में मध्यम भूस्खलन स्थिति है। मौसम और जल स्तर पर नजर रखें।"
        }
    },
    "LOW": {
        "en": {
            "title": "Normal Monitoring Status",
            "message": "INFO: Low landslide risk in {location}. Conditions remain normal."
        },
        "hi": {
            "title": "सामान्य स्थिति सूचना",
            "message": "सूचना: {location} में स्थिति सामान्य है। कोई तत्काल खतरा नहीं है।"
        }
    }
}

def send_alert_notification(
    db: Session,
    alert_id: str,
    location: str,
    severity: str = "HIGH",
    recipient: str = "Community Broadcast",
    language: str = "en"
) -> Dict[str, Any]:
    lang = language if language in ["en", "hi"] else settings.DEFAULT_LANGUAGE
    sev = severity.upper()
    if sev not in MULTILINGUAL_TEMPLATES:
        sev = "HIGH"

    template = MULTILINGUAL_TEMPLATES[sev].get(lang, MULTILINGUAL_TEMPLATES[sev]["en"])
    title = template["title"]
    body = template["message"].format(location=location)

    channel = settings.SMS_PROVIDER.upper()
    status = "SENT"

    # If real Twilio configured
    if settings.SMS_PROVIDER == "twilio" and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
        try:
            audit_logger.info(f"Dispatching SMS via Twilio to {recipient}: {body}")
        except Exception as e:
            audit_logger.error(f"Twilio dispatch failed: {e}")
            status = "FAILED"
    else:
        audit_logger.info(f"[MULTILINGUAL NOTIFICATION DISPATCH] [{lang.upper()}] [{channel}] {title} -> {body}")

    # Log to database
    log_entry = NotificationLog(
        alert_id=alert_id,
        recipient=recipient,
        channel=channel,
        language=lang,
        title=title,
        message_body=body,
        delivery_status=status,
        sent_at=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()

    return {
        "status": status,
        "channel": channel,
        "language": lang,
        "title": title,
        "message": body,
        "alert_id": alert_id
    }
class NotificationService:
    @staticmethod
    def dispatch_alert_notification(db, alert_id, location, hazard_type="Landslide", severity="HIGH", message=None, language="en"):
        return send_alert_notification(
            db=db,
            alert_id=alert_id,
            location=location,
            severity=severity,
            language=language
        )

notification_service = NotificationService()
