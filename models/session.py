from datetime import datetime
from typing import List, Optional, Dict

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, DateTime, Text

from app.database import Base


class WebhookReportRequest(BaseModel):
    platform: str = Field(..., example="LINE")
    sender_id: str = Field(..., example="U123456")
    group_id: Optional[str] = Field(None, example="G999")
    message_type: str = Field(..., example="text")
    content: str = Field(..., example="@通報 馬太鞍溪橋斷裂，需要 2 台怪手")
    timestamp: datetime = Field(..., example="2026-05-24T10:00:00Z")


class ConfirmRequest(BaseModel):
    sender_id: str = Field(..., example="U123456")
    action: str = Field(..., example="confirm")


class CorrectRequest(BaseModel):
    sender_id: str = Field(..., example="U123456")
    content: str = Field(..., example="不是 2 台怪手，是 3 台")


class CancelRequest(BaseModel):
    sender_id: str = Field(..., example="U123456")


class ReplyMessage(BaseModel):
    type: str = Field(..., example="question")
    text: str = Field(..., example="請告訴我發生地點與聯絡方式。")
    actions: Optional[List[str]] = None


class SessionResponse(BaseModel):
    session_id: str
    report_id: Optional[int]
    platform: str
    sender_id: str
    group_id: Optional[str]
    source_type: str
    source_context: str
    current_state: str
    raw_events: Optional[List[Dict]] = None
    normalized_messages: Optional[List[Dict]] = None
    extracted_entities: Optional[Dict] = None
    missing_fields: Optional[List[str]] = None
    status: str
    reply_message: Optional[ReplyMessage] = None
    created_at: datetime
    updated_at: datetime
    expired_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class SessionORM(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    report_id = Column(Integer, nullable=True)
    platform = Column(String, nullable=False)
    sender_id = Column(String, nullable=False, index=True)
    group_id = Column(String, nullable=True, index=True)
    source_type = Column(String, nullable=False)
    source_context = Column(String, nullable=False)
    current_state = Column(String, nullable=False, default="RECEIVED")
    raw_events = Column(Text, nullable=True)
    normalized_messages = Column(Text, nullable=True)
    extracted_entities = Column(Text, nullable=True)
    missing_fields = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    expired_at = Column(DateTime, nullable=True)
