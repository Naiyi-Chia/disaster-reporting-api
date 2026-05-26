from datetime import datetime
from typing import List, Optional
import json

from sqlalchemy.orm import Session

from models.report import ReportORM
from models.session import SessionORM
from services.line_service import extract_report_info


def _compute_confidence(extracted: dict) -> float:
    # Simple heuristic: fraction of fields we were able to extract
    fields = ["location", "incident_type", "resource_type", "quantity", "risk_level"]
    found = sum(1 for f in fields if extracted.get(f) is not None)
    return round(found / len(fields), 2)


def create_report_from_entities(db: Session, session: "SessionORM") -> ReportORM:
    extracted = json.loads(session.extracted_entities or "{}")
    location = extracted.get("location", {}).get("address")
    incident = extracted.get("incident", {})
    needs = extracted.get("needs", [])

    hazard_type = incident.get("type")
    critical_risk = bool(incident.get("severity") == "critical")
    requested_resource = None
    quantity = None

    if needs:
        primary_need = needs[0]
        requested_resource = primary_need.get("item")
        quantity = primary_need.get("quantity")

    report = ReportORM(
        message_id=None,
        source_type=session.source_type,
        route="A_official" if session.source_type == "official" else "B_citizen",
        raw_text=" \n".join(
            [m.get("content", "") for m in json.loads(session.normalized_messages or "[]")]
        ),
        location=location,
        hazard_type=hazard_type,
        requested_resource=requested_resource,
        quantity=quantity,
        critical_risk=int(critical_risk),
        confidence_score=str(_compute_confidence({
            "location": location,
            "incident_type": hazard_type,
            "resource_type": requested_resource,
            "quantity": quantity,
            "risk_level": incident.get("severity"),
        })),
        missing_fields=session.missing_fields,
        validation_warnings=None,
        state="confirmed",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def create_report(
    db: Session,
    source_channel: str,
    line_group_id: Optional[str],
    line_user_id: Optional[str],
    original_message: str,
    route: str,
    message_id: Optional[str] = None,
    source_type: Optional[str] = None,
) -> ReportORM:
    """Create a new report in database using extraction + validation rules."""
    extracted = extract_report_info(original_message)

    # Map extracted fields to standardized schema
    location = extracted.get("location")
    hazard_type = extracted.get("incident_type")
    requested_resource = extracted.get("resource_type")
    quantity = extracted.get("quantity")
    critical_risk = bool(extracted.get("risk_level") == "critical")

    # Validation
    missing_fields = []
    validation_warnings = []
    if not location:
        missing_fields.append("location")
    if not hazard_type:
        missing_fields.append("hazard_type")
    if requested_resource and quantity is None:
        validation_warnings.append("resource_quantity_missing")

    state = "needs_clarification" if missing_fields else "pending_confirmation"

    confidence_score = _compute_confidence(extracted)

    report = ReportORM(
        message_id=message_id,
        source_type=source_type,
        route=route,
        raw_text=original_message,
        location=location,
        hazard_type=hazard_type,
        requested_resource=requested_resource,
        quantity=quantity,
        critical_risk=int(critical_risk),
        confidence_score=str(confidence_score),
        missing_fields=json.dumps(missing_fields) if missing_fields else None,
        validation_warnings=json.dumps(validation_warnings) if validation_warnings else None,
        state=state,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def list_reports(db: Session) -> List[ReportORM]:
    """List all reports."""
    return db.query(ReportORM).order_by(ReportORM.created_at.desc()).all()


def get_report(db: Session, report_id: int) -> Optional[ReportORM]:
    """Get a specific report by ID."""
    return db.query(ReportORM).filter(ReportORM.id == report_id).first()


def update_report_state(
    db: Session, report_id: int, new_state: str
) -> Optional[ReportORM]:
    """Update report state."""
    report = get_report(db, report_id)
    if report:
        report.state = new_state
        report.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(report)
    return report
