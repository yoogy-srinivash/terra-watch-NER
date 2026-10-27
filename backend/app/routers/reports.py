import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from pathlib import Path

from ..config import settings
from ..database import get_db
from ..models import FieldReport, UploadedMedia, EmergencyTask
from ..schemas import ReportResponse, ReportStatusUpdate
from ..services.cv_service import analyze_field_image

router = APIRouter(prefix="/api/reports", tags=["Citizen & Field Reporting"])

@router.get("", response_model=List[ReportResponse])
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(FieldReport).order_by(FieldReport.created_at.desc()).all()
    out = []
    for r in reports:
        media_url = f"/uploads/{Path(r.media_path).name}" if r.media_path else None
        out.append(ReportResponse(
            id=r.id,
            user_name=r.user_name,
            issue_type=r.issue_type,
            severity=r.severity,
            location_name=r.location_name,
            state=r.state,
            city=r.city,
            description=r.description,
            is_emergency=r.is_emergency,
            status=r.status,
            evidence_desc=r.evidence_desc or "No photo uploaded",
            media_url=media_url,
            latitude=r.latitude,
            longitude=r.longitude,
            created_at=r.created_at
        ))
    return out

@router.post("")
async def submit_field_report(
    issueType: str = Form(...),
    severity: str = Form("moderate"),
    location: str = Form(...),
    state: str = Form("Assam"),
    city: Optional[str] = Form(""),
    description: str = Form(...),
    emergency: Optional[bool] = Form(False),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    userName: Optional[str] = Form("Citizen Reporter"),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # Unique sequential/random report ID format matching UI: LS-2026-XXXXX
    rand_num = int(uuid.uuid4().int % 90000) + 10000
    report_id = f"LS-2026-{rand_num}"

    media_path = None
    evidence_desc = "No evidence uploaded"
    ai_label = None
    ai_conf = None

    if photo and photo.filename:
        # Secure extension check
        ext = Path(photo.filename).suffix.lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            raise HTTPException(status_code=400, detail="Only image files (.jpg, .png, .webp) are allowed.")

        # Content-type verification
        if photo.content_type and not photo.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid file type: must be an image.")

        # Enforce maximum upload size (default 25 MB)
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        contents = await photo.read()
        if len(contents) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_MB} MB."
            )

        save_filename = f"{report_id}_{uuid.uuid4().hex[:8]}{ext}"
        dest_path = Path(settings.UPLOAD_DIR) / save_filename
        with open(dest_path, "wb") as buffer:
            buffer.write(contents)

        media_path = str(dest_path)
        evidence_desc = "Photo uploaded by user"

        # Run CV analysis
        cv_result = analyze_field_image(str(dest_path))
        ai_label = cv_result.get("hazard_label")
        ai_conf = cv_result.get("confidence")

    new_report = FieldReport(
        id=report_id,
        user_name=userName,
        issue_type=issueType,
        severity=severity,
        location_name=location,
        state=state,
        city=city,
        description=description,
        is_emergency=bool(emergency),
        latitude=latitude,
        longitude=longitude,
        status="Pending",
        media_path=media_path,
        evidence_desc=evidence_desc,
        created_at=datetime.utcnow()
    )
    db.add(new_report)

    if media_path:
        file_size = os.path.getsize(media_path)
        media_rec = UploadedMedia(
            report_id=report_id,
            file_name=Path(media_path).name,
            file_path=media_path,
            file_size_bytes=file_size,
            ai_hazard_label=ai_label,
            ai_confidence=ai_conf
        )
        db.add(media_rec)

    # If marked emergency, automatically instantiate EmergencyTask
    if emergency:
        er_task = EmergencyTask(
            id=f"ER-{3000 + rand_num % 1000}",
            user_name=userName,
            location=f"{location}, {state}",
            state=state,
            request_type=issueType.title(),
            priority="Critical" if severity.lower() == "critical" else "High",
            status="Pending",
            description=description,
            coordinates=f"{latitude}, {longitude}" if latitude and longitude else None,
            created_at=datetime.utcnow()
        )
        db.add(er_task)

    db.commit()
    db.refresh(new_report)

    return {
        "status": "success",
        "reportId": report_id,
        "ai_analysis": {
            "hazard_label": ai_label,
            "confidence": ai_conf,
            "hazard_type": cv_result.get("hazard_type"),
            "evidence_strength": cv_result.get("evidence_strength"),
            "scientific_status": cv_result.get("scientific_status"),
            "trained_classifier": cv_result.get("trained_classifier", False),
            "evidence": cv_result.get("evidence", [])
        } if ai_label else None
    }

@router.get("/{report_id}")
def get_report(report_id: str, db: Session = Depends(get_db)):
    r = db.query(FieldReport).filter(FieldReport.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found.")
    return r

@router.patch("/{report_id}/status")
def update_report_status(
    report_id: str,
    status_update: ReportStatusUpdate,
    db: Session = Depends(get_db)
):
    r = db.query(FieldReport).filter(FieldReport.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found.")

    r.status = status_update.status
    if status_update.status == "Verified":
        r.verified_at = datetime.utcnow()
        r.verified_by = "Admin / Field Officer"
    db.commit()
    db.refresh(r)
    return {"status": "success", "report_id": r.id, "new_status": r.status}
