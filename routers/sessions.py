from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from models.session import ConfirmRequest, CorrectRequest, CancelRequest, SessionResponse
from services.session_service import (
    get_session,
    confirm_session,
    correct_session,
    cancel_session,
    format_session_response,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("/{session_id}", response_model=SessionResponse)
def get_session_detail(session_id: str, db: Session = Depends(get_db)) -> SessionResponse:
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return format_session_response(session)


@router.post("/{session_id}/confirm")
def confirm_session_endpoint(
    session_id: str, request: ConfirmRequest, db: Session = Depends(get_db)
) -> dict:
    try:
        session, report = confirm_session(db, session_id, request.sender_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "status": "confirmed",
        "current_state": session.current_state,
        "final_report": {
            "id": report.id,
            "source_type": report.source_type,
            "route": report.route,
            "location": report.location,
            "hazard_type": report.hazard_type,
            "requested_resource": report.requested_resource,
            "quantity": report.quantity,
            "critical_risk": bool(report.critical_risk),
            "state": report.state,
        },
    }


@router.post("/{session_id}/correct")
def correct_session_endpoint(
    session_id: str, request: CorrectRequest, db: Session = Depends(get_db)
) -> dict:
    try:
        session = correct_session(db, session_id, request.sender_id, request.content)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return format_session_response(session)


@router.post("/{session_id}/cancel")
def cancel_session_endpoint(
    session_id: str, request: CancelRequest, db: Session = Depends(get_db)
) -> dict:
    try:
        session = cancel_session(db, session_id, request.sender_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return format_session_response(session)
