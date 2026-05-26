import json
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from models.session import SessionORM
from services.extraction_service import extract_report_entities, merge_extraction_results
from services.reports_service import create_report_from_entities

OPEN_STATES = {
    "RECEIVED",
    "LOW_CONFIDENCE_REVIEW",
    "WAITING_CONFIRMATION",
    "USER_CORRECTION",
}
FINAL_STATES = {"CONFIRMED", "EXPORTED", "CANCELLED", "CLOSED", "TIMEOUT"}


_parse_text_entities = extract_report_entities
_merge_entities = merge_extraction_results


def _normalize_message(content: str, message_type: str, timestamp: Any) -> dict[str, Any]:
    ts = timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp)
    return {
        "timestamp": ts,
        "message_type": message_type,
        "content": content,
    }


def _determine_source(content: str, group_id: Optional[str]) -> tuple[str, str]:
    if group_id and "@通報" in content:
        return "official", "OFFICIAL_GROUP"
    return "citizen", "CITIZEN_DIRECT"


def _collect_missing_fields(session: SessionORM) -> list[str]:
    fields: list[str] = []
    entities = json.loads(session.extracted_entities or "{}")
    location = entities.get("location", {}).get("address")
    incident = entities.get("incident", {})
    needs = entities.get("needs", [])
    reporter = entities.get("reporter", {})

    if not session.sender_id:
        fields.append("sender_id")
    if session.source_type == "official":
        if not session.group_id:
            fields.append("group_id")
    if not location:
        fields.append("location")
    if not incident.get("type") and not needs:
        fields.append("incident_or_needs")
    if session.source_type == "citizen":
        if not reporter.get("name"):
            fields.append("reporter.name")
        if not reporter.get("phone"):
            fields.append("reporter.phone")
    return fields


def _build_reply_message(missing_fields: list[str], status: str) -> dict[str, Any]:
    if status == "need_more_info":
        field_prompts = {
            "location": "請提供詳細地址或地點。",
            "reporter.name": "請提供聯絡人姓名。",
            "reporter.phone": "請提供聯絡電話。",
            "group_id": "請提供通報群組資訊。",
            "incident_or_needs": "請描述災情或需要的支援。",
            "sender_id": "請提供通報者識別資訊。",
        }
        if missing_fields:
            prompts = [field_prompts.get(field, "請補充相關通報資訊。") for field in missing_fields]
            text = "為了完成通報，" + "".join(prompts)
        else:
            text = "請再提供更多通報資訊，方便我們協助確認。"
        return {"type": "question", "text": text, "actions": None}
        if not missing_fields:
            text = "請補充更多災情資訊，例如地點、需求或聯絡方式。"
        elif "location" in missing_fields:
            text = "請提供您的詳細地址，方便救援或物資送達。"
        else:
            text = "請補充：" + ", ".join(missing_fields)
        return {"type": "question", "text": text, "actions": None}
    return {
        "type": "confirmation",
        "text": "我們已收到通報，請確認以下資訊是否正確。",
        "actions": ["confirm", "correct", "cancel"],
    }


def _build_status(current_state: str) -> str:
    if current_state in {"LOW_CONFIDENCE_REVIEW"}:
        return "need_more_info"
    if current_state in {"WAITING_CONFIRMATION"}:
        return "waiting_confirmation"
    if current_state in {"EXPORTED"}:
        return "confirmed"
    if current_state in {"CANCELLED"}:
        return "cancelled"
    return "in_progress"


def _determine_next_state(missing_fields: list[str]) -> str:
    if missing_fields:
        return "LOW_CONFIDENCE_REVIEW"
    return "WAITING_CONFIRMATION"


def _format_session_response(session: SessionORM) -> dict[str, Any]:
    raw_events = json.loads(session.raw_events) if session.raw_events else []
    normalized_messages = json.loads(session.normalized_messages) if session.normalized_messages else []
    extracted_entities = json.loads(session.extracted_entities) if session.extracted_entities else {}
    missing_fields = json.loads(session.missing_fields) if session.missing_fields else []
    status = _build_status(session.current_state)
    reply_message = _build_reply_message(missing_fields, status)

    return {
        "session_id": session.session_id,
        "report_id": session.report_id,
        "platform": session.platform,
        "sender_id": session.sender_id,
        "group_id": session.group_id,
        "source_type": session.source_type,
        "source_context": session.source_context,
        "current_state": session.current_state,
        "raw_events": raw_events,
        "normalized_messages": normalized_messages,
        "extracted_entities": extracted_entities,
        "missing_fields": missing_fields,
        "status": status,
        "reply_message": reply_message,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "expired_at": session.expired_at,
    }


def _find_open_session(
    db: Session, sender_id: str, platform: str, group_id: Optional[str]
) -> SessionORM | None:
    query = (
        db.query(SessionORM)
        .filter(SessionORM.sender_id == sender_id)
        .filter(SessionORM.platform == platform)
        .filter(SessionORM.current_state.notin_(FINAL_STATES))
    )

    if group_id:
        query = query.filter(SessionORM.group_id == group_id)
    else:
        query = query.filter(SessionORM.group_id.is_(None))

    return query.order_by(SessionORM.updated_at.desc()).first()


def create_or_update_session(db: Session, payload: dict[str, Any]) -> SessionORM:
    if isinstance(payload.get("timestamp"), datetime):
        payload["timestamp"] = payload["timestamp"].isoformat()

    source_type, source_context = _determine_source(payload["content"], payload.get("group_id"))
    session = _find_open_session(
        db,
        payload["sender_id"],
        payload["platform"],
        payload.get("group_id"),
    )
    normalized_message = _normalize_message(payload["content"], payload["message_type"], payload["timestamp"])
    extracted = _parse_text_entities(payload["content"])

    if session is None:
        session = SessionORM(
            session_id=str(uuid.uuid4()),
            platform=payload["platform"],
            sender_id=payload["sender_id"],
            group_id=payload.get("group_id"),
            source_type=source_type,
            source_context=source_context,
            current_state="RECEIVED",
            raw_events=json.dumps([payload]),
            normalized_messages=json.dumps([normalized_message]),
            extracted_entities=json.dumps(extracted),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    else:
        current_events = json.loads(session.raw_events or "[]")
        current_events.append(payload)
        current_normalized = json.loads(session.normalized_messages or "[]")
        current_normalized.append(normalized_message)
        current_extracted = json.loads(session.extracted_entities or "{}")
        merged_extracted = _merge_entities(current_extracted, extracted)

        session.raw_events = json.dumps(current_events)
        session.normalized_messages = json.dumps(current_normalized)
        session.extracted_entities = json.dumps(merged_extracted)
        session.updated_at = datetime.utcnow()

    missing_fields = _collect_missing_fields(session)
    session.missing_fields = json.dumps(missing_fields) if missing_fields else json.dumps([])
    session.current_state = _determine_next_state(missing_fields)
    session.updated_at = datetime.utcnow()

    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: str) -> SessionORM | None:
    return db.query(SessionORM).filter(SessionORM.session_id == session_id).first()


def confirm_session(db: Session, session_id: str, sender_id: str) -> tuple[SessionORM, Any]:
    session = get_session(db, session_id)
    if not session:
        return None, None
    if session.sender_id != sender_id:
        raise PermissionError("此確認卡僅限原通報者操作")

    report = create_report_from_entities(db, session)
    session.report_id = report.id
    session.current_state = "EXPORTED"
    session.updated_at = datetime.utcnow()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session, report


def correct_session(db: Session, session_id: str, sender_id: str, content: str) -> SessionORM | None:
    session = get_session(db, session_id)
    if not session:
        return None
    if session.sender_id != sender_id:
        raise PermissionError("此更正卡僅限原通報者操作")

    extracted = _parse_text_entities(content)
    normalized_message = _normalize_message(content, "text", datetime.utcnow())
    current_normalized = json.loads(session.normalized_messages or "[]")
    current_normalized.append(normalized_message)
    current_extracted = json.loads(session.extracted_entities or "{}")
    merged_extracted = _merge_entities(current_extracted, extracted)

    session.normalized_messages = json.dumps(current_normalized)
    session.extracted_entities = json.dumps(merged_extracted)
    session.missing_fields = json.dumps(_collect_missing_fields(session))
    session.current_state = _determine_next_state(json.loads(session.missing_fields))
    session.updated_at = datetime.utcnow()

    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def cancel_session(db: Session, session_id: str, sender_id: str) -> SessionORM | None:
    session = get_session(db, session_id)
    if not session:
        return None
    if session.sender_id != sender_id:
        raise PermissionError("此取消卡僅限原通報者操作")

    session.current_state = "CANCELLED"
    session.updated_at = datetime.utcnow()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def format_session_response(session: SessionORM) -> dict[str, Any]:
    return _format_session_response(session)
