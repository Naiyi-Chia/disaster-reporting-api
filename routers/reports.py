from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from models.report import ReportResponse
from services.reports_service import (
    list_reports,
    get_report,
    update_report_state,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=list[ReportResponse])
def get_reports(db: Session = Depends(get_db)) -> list[ReportResponse]:
    """List all reports."""
    import json

    reports = list_reports(db)
    out = []
    for r in reports:
        missing = json.loads(r.missing_fields) if r.missing_fields else []
        warnings = json.loads(r.validation_warnings) if r.validation_warnings else []
        out.append(
            {
                "id": r.id,
                "message_id": r.message_id,
                "source_type": r.source_type,
                "route": r.route,
                "raw_text": r.raw_text,
                "location": r.location,
                "hazard_type": r.hazard_type,
                "requested_resource": r.requested_resource,
                "quantity": r.quantity,
                "critical_risk": bool(r.critical_risk),
                "confidence_score": r.confidence_score,
                "missing_fields": missing,
                "validation_warnings": warnings,
                "state": r.state,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
        )
    return out


@router.get("/{report_id}", response_model=ReportResponse)
def get_report_detail(
    report_id: int, db: Session = Depends(get_db)
) -> ReportResponse:
    """Get a specific report."""
    report = get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
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


@router.post("/{report_id}/confirm", response_model=ReportResponse)
def confirm_report(
    report_id: int, db: Session = Depends(get_db)
) -> ReportResponse:
    """Confirm a report."""
    report = update_report_state(db, report_id, "confirmed")
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
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


@router.post("/{report_id}/cancel", response_model=ReportResponse)
def cancel_report(
    report_id: int, db: Session = Depends(get_db)
) -> ReportResponse:
    """Cancel a report."""
    report = update_report_state(db, report_id, "cancelled")
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
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
