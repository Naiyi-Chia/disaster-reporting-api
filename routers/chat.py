from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from models.chat import ChatReportRequest
from services.reports_service import create_report

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/report")
def chat_report(message: ChatReportRequest, db: Session = Depends(get_db)):
    """Create a report from natural language chat text."""
    route = "A_official" if "@通報" in message.text else "B_citizen"

    report = create_report(
        db=db,
        source_channel="chat",
        line_group_id=None,
        line_user_id=None,
        original_message=message.text,
        route=route,
        message_id=None,
        source_type="chat",
    )

    import json

    missing = json.loads(report.missing_fields) if report.missing_fields else []
    warnings = json.loads(report.validation_warnings) if report.validation_warnings else []

    return {
        "id": report.id,
        "raw_text": report.raw_text,
        "location": report.location,
        "hazard_type": report.hazard_type,
        "requested_resource": report.requested_resource,
        "quantity": report.quantity,
        "critical_risk": bool(report.critical_risk),
        "confidence_score": report.confidence_score,
        "missing_fields": missing,
        "validation_warnings": warnings,
        "state": report.state,
    }
