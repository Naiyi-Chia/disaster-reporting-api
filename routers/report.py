from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from models.report import IncomingMessage
from services import report_service
from services.reports_service import create_report

router = APIRouter(prefix="/report", tags=["Report"])


@router.post("/ingest")
def ingest(message: IncomingMessage, db: Session = Depends(get_db)):
    """Parse incoming message, persist to DB, and return structured report."""
    # Persist via reports service (extraction + validation happens inside)
    report = create_report(
        db=db,
        source_channel="web",
        line_group_id=None,
        line_user_id=None,
        original_message=message.raw_text,
        route=report_service.ROUTE_MAP.get(message.source_type, "unassigned"),
        message_id=message.message_id,
        source_type=message.source_type,
    )

    # prepare response
    import json

    missing = json.loads(report.missing_fields) if report.missing_fields else []
    warnings = json.loads(report.validation_warnings) if report.validation_warnings else []

    return {
        "id": report.id,
        "message_id": report.message_id,
        "source_type": report.source_type,
        "route": report.route,
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
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }
