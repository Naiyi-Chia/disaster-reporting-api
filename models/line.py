from typing import Any, List, Optional

from pydantic import BaseModel


class LineSource(BaseModel):
    type: str
    groupId: Optional[str] = None
    userId: Optional[str] = None


class LineMessage(BaseModel):
    type: str
    text: str


class LineEvent(BaseModel):
    type: str
    source: LineSource
    message: LineMessage


class LineWebhookRequest(BaseModel):
    events: List[LineEvent]


class LineWebhookResponse(BaseModel):
    processed: bool
    created_reports: List[dict]
