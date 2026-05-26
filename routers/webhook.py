from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from models.session import WebhookReportRequest
from services.session_service import create_or_update_session, format_session_response

router = APIRouter(prefix="/webhook", tags=["Webhook"])


@router.post("/report")
def webhook_report(request: WebhookReportRequest, db: Session = Depends(get_db)) -> dict:
    if request.message_type != "text":
        raise HTTPException(status_code=422, detail="Only text messages are supported in Phase 1.")

    session = create_or_update_session(db, request.dict())
    return format_session_response(session)
