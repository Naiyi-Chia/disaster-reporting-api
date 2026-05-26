from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from models.line import LineWebhookRequest, LineWebhookResponse
from services.line_service import should_create_report
from services.reports_service import create_report

router = APIRouter(prefix="/line", tags=["LINE"])


@router.post("/webhook", response_model=LineWebhookResponse)
def webhook(
    request: LineWebhookRequest, db: Session = Depends(get_db)
) -> LineWebhookResponse:
    """Handle LINE webhook events."""
    created_reports = []

    for event in request.events:
        if event.type != "message" or event.message.type != "text":
            continue

        raw_text = event.message.text

        if not should_create_report(raw_text):
            continue

        line_group_id = event.source.groupId if event.source.type == "group" else None
        line_user_id = event.source.userId if hasattr(event.source, "userId") else None

        route = "A_official" if "官方" in raw_text else "B_citizen"

        # Pass message identifier and source_type if available
        message_id = None
        source_type = event.source.type if hasattr(event.source, "type") else None

        report = create_report(
            db=db,
            source_channel="line",
            line_group_id=line_group_id,
            line_user_id=line_user_id,
            original_message=raw_text,
            route=route,
            message_id=message_id,
            source_type=source_type,
        )

        created_reports.append(
            {
                "id": report.id,
                "hazard_type": report.hazard_type,
                "location": report.location,
                "state": report.state,
            }
        )

    return LineWebhookResponse(
        processed=True,
        created_reports=created_reports,
    )
