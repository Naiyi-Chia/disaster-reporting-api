from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, DateTime, Text

# Use the shared Base from the application's database module so
# all ORM models are registered on the same metadata.
from app.database import Base


class Contact(BaseModel):
    name: str = Field(..., example="Jane Doe")
    phone: str = Field(..., example="09xx-xxx-xxx")


class IncomingMessage(BaseModel):
    message_id: str = Field(..., example="MSG-20260524-001")
    source_type: str = Field(..., example="official_group")
    raw_text: str = Field(..., example="馬太鞍溪橋橋斷裂，怪手已到場，缺水且有火災風險。")
    timestamp: datetime = Field(..., example="2026-05-24T14:30:00Z")
    contact: Optional[Contact] = None


class RoutedReport(BaseModel):
    message_id: str
    source_type: str
    route: str
    detected_location: Optional[str] = None
    detected_hazards: List[str] = Field(default_factory=list)
    detected_assets: List[str] = Field(default_factory=list)
    critical_risk: bool = False
    raw_text: str
    received: datetime = Field(default_factory=datetime.utcnow, example="2026-05-24T14:30:05Z")


class ReportORM(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, nullable=True, index=True)
    source_type = Column(String, nullable=True, index=True)
    route = Column(String, nullable=True)
    raw_text = Column(Text)
    location = Column(String, nullable=True)
    hazard_type = Column(String, nullable=True)
    requested_resource = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    critical_risk = Column(Integer, default=0)
    confidence_score = Column(String, nullable=True)
    missing_fields = Column(String, nullable=True)
    validation_warnings = Column(String, nullable=True)
    state = Column(String, default="pending_confirmation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class ReportResponse(BaseModel):
    id: int
    message_id: Optional[str]
    source_type: Optional[str]
    route: Optional[str]
    raw_text: str
    location: Optional[str]
    hazard_type: Optional[str]
    requested_resource: Optional[str]
    quantity: Optional[int]
    critical_risk: bool
    confidence_score: Optional[str]
    missing_fields: Optional[list]
    validation_warnings: Optional[list]
    state: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
