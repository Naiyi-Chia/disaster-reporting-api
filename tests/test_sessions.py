from datetime import datetime
import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_official_complete_report_waiting_confirmation() -> None:
    sender_id = f"U_{uuid.uuid4().hex[:8]}"
    payload = {
        "platform": "LINE",
        "sender_id": sender_id,
        "group_id": "G100",
        "message_type": "text",
        "content": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    response = client.post("/webhook/report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "waiting_confirmation"
    assert data["current_state"] == "WAITING_CONFIRMATION"
    assert data["missing_fields"] == []
    assert data["reply_message"]["type"] == "confirmation"
    assert data["reply_message"]["actions"] == ["confirm", "correct", "cancel"]
    assert data["extracted_entities"]["location"]["address"] == "馬太鞍溪橋"
    assert data["extracted_entities"]["incident"]["type"] == "bridge_damage"


def test_citizen_incomplete_report_returns_need_more_info() -> None:
    sender_id = f"U_{uuid.uuid4().hex[:8]}"
    payload = {
        "platform": "LINE",
        "sender_id": sender_id,
        "group_id": None,
        "message_type": "text",
        "content": "我這邊淹水了，好像需要水跟食物",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    response = client.post("/webhook/report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "need_more_info"
    assert data["current_state"] == "LOW_CONFIDENCE_REVIEW"
    assert "location" in data["missing_fields"]
    assert "reporter.name" in data["missing_fields"]
    assert "reporter.phone" in data["missing_fields"]
    assert data["reply_message"]["type"] == "question"


def test_citizen_follow_up_updates_same_session() -> None:
    sender_id = f"U_{uuid.uuid4().hex[:8]}"
    first_payload = {
        "platform": "LINE",
        "sender_id": sender_id,
        "group_id": None,
        "message_type": "text",
        "content": "我這邊淹水了，好像需要水跟食物",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    first_response = client.post("/webhook/report", json=first_payload)
    assert first_response.status_code == 200
    first_data = first_response.json()
    session_id = first_data["session_id"]
    assert first_data["status"] == "need_more_info"

    second_payload = {
        "platform": "LINE",
        "sender_id": sender_id,
        "group_id": None,
        "message_type": "text",
        "content": "地址在馬太鞍溪橋附近，我叫王小明，0912345678",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    second_response = client.post("/webhook/report", json=second_payload)
    assert second_response.status_code == 200
    second_data = second_response.json()
    assert second_data["session_id"] == session_id
    assert second_data["status"] == "waiting_confirmation"
    assert second_data["current_state"] == "WAITING_CONFIRMATION"
    assert second_data["missing_fields"] == []


def test_citizen_follow_up_extracts_address_and_returns_address_prompt() -> None:
    sender_id = f"U_{uuid.uuid4().hex[:8]}"
    first_payload = {
        "platform": "LINE",
        "sender_id": sender_id,
        "group_id": None,
        "message_type": "text",
        "content": "我這邊淹水了，好像需要水跟食物",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    first_response = client.post("/webhook/report", json=first_payload)
    assert first_response.status_code == 200
    first_data = first_response.json()
    session_id = first_data["session_id"]
    assert first_data["status"] == "need_more_info"

    second_payload = {
        "platform": "LINE",
        "sender_id": sender_id,
        "group_id": None,
        "message_type": "text",
        "content": "地址是花蓮縣光復鄉 XXX 路 12 號，我叫王小明，電話 0912-345-678",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    second_response = client.post("/webhook/report", json=second_payload)
    assert second_response.status_code == 200
    second_data = second_response.json()
    assert second_data["session_id"] == session_id
    assert second_data["status"] == "waiting_confirmation"
    assert second_data["current_state"] == "WAITING_CONFIRMATION"
    assert second_data["missing_fields"] == []
    assert second_data["extracted_entities"]["location"]["address"] == "花蓮縣光復鄉 XXX 路 12 號"
    assert second_data["reply_message"]["type"] == "confirmation"


def test_confirm_creates_final_report() -> None:
    sender_id = f"U_{uuid.uuid4().hex[:8]}"
    payload = {
        "platform": "LINE",
        "sender_id": sender_id,
        "group_id": "G400",
        "message_type": "text",
        "content": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    create_response = client.post("/webhook/report", json=payload)
    assert create_response.status_code == 200
    session_id = create_response.json()["session_id"]

    confirm_response = client.post(
        f"/sessions/{session_id}/confirm",
        json={"sender_id": sender_id, "action": "confirm"},
    )
    assert confirm_response.status_code == 200
    confirm_data = confirm_response.json()
    assert confirm_data["status"] == "confirmed"
    assert confirm_data["current_state"] == "EXPORTED"
    assert confirm_data["final_report"]["hazard_type"] == "bridge_damage"


def test_different_sender_cannot_confirm_group_session() -> None:
    sender_id = f"U_{uuid.uuid4().hex[:8]}"
    payload = {
        "platform": "LINE",
        "sender_id": sender_id,
        "group_id": "G500",
        "message_type": "text",
        "content": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    create_response = client.post("/webhook/report", json=payload)
    assert create_response.status_code == 200
    session_id = create_response.json()["session_id"]

    confirm_response = client.post(
        f"/sessions/{session_id}/confirm",
        json={"sender_id": "U999", "action": "confirm"},
    )
    assert confirm_response.status_code == 403
    assert "此確認卡僅限原通報者操作" in confirm_response.json()["detail"]
def test_official_follow_up_without_mention_keeps_original_source() -> None:
    sender_id = f"U_{uuid.uuid4().hex[:8]}"
    first_payload = {
        "platform": "LINE",
        "sender_id": sender_id,
        "group_id": "G_SOURCE_KEEP",
        "message_type": "text",
        "content": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    first_response = client.post("/webhook/report", json=first_payload)
    assert first_response.status_code == 200
    first_data = first_response.json()
    assert first_data["source_type"] == "official"
    assert first_data["source_context"] == "OFFICIAL_GROUP"

    follow_up_payload = {
        "platform": "LINE",
        "sender_id": sender_id,
        "group_id": "G_SOURCE_KEEP",
        "message_type": "text",
        "content": "補充：現場仍需要協助",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    follow_up_response = client.post("/webhook/report", json=follow_up_payload)
    assert follow_up_response.status_code == 200
    follow_up_data = follow_up_response.json()
    assert follow_up_data["session_id"] == first_data["session_id"]
    assert follow_up_data["source_type"] == "official"
    assert follow_up_data["source_context"] == "OFFICIAL_GROUP"
    assert "reporter.name" not in follow_up_data["missing_fields"]
    assert "reporter.phone" not in follow_up_data["missing_fields"]


def test_same_sender_different_group_creates_new_session() -> None:
    sender_id = f"U_{uuid.uuid4().hex[:8]}"
    first_payload = {
        "platform": "LINE",
        "sender_id": sender_id,
        "group_id": "G_FIRST",
        "message_type": "text",
        "content": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    second_payload = {
        "platform": "LINE",
        "sender_id": sender_id,
        "group_id": "G_SECOND",
        "message_type": "text",
        "content": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    first_response = client.post("/webhook/report", json=first_payload)
    second_response = client.post("/webhook/report", json=second_payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    first_data = first_response.json()
    second_data = second_response.json()
    assert second_data["session_id"] != first_data["session_id"]
    assert first_data["group_id"] == "G_FIRST"
    assert second_data["group_id"] == "G_SECOND"


def test_same_sender_different_platform_creates_new_direct_session() -> None:
    sender_id = f"U_{uuid.uuid4().hex[:8]}"
    first_payload = {
        "platform": "LINE",
        "sender_id": sender_id,
        "group_id": None,
        "message_type": "text",
        "content": "淹水",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    second_payload = {
        "platform": "TEST",
        "sender_id": sender_id,
        "group_id": None,
        "message_type": "text",
        "content": "淹水",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    first_response = client.post("/webhook/report", json=first_payload)
    second_response = client.post("/webhook/report", json=second_payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["session_id"] != first_response.json()["session_id"]


def test_need_more_info_reply_uses_user_friendly_chinese() -> None:
    sender_id = f"U_{uuid.uuid4().hex[:8]}"
    payload = {
        "platform": "LINE",
        "sender_id": sender_id,
        "group_id": None,
        "message_type": "text",
        "content": "淹水",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    response = client.post("/webhook/report", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "need_more_info"
    reply_text = data["reply_message"]["text"]
    assert "請提供詳細地址或地點。" in reply_text
    assert "請提供聯絡人姓名。" in reply_text
    assert "請提供聯絡電話。" in reply_text
    assert "location" not in reply_text
    assert "reporter.name" not in reply_text
    assert "reporter.phone" not in reply_text
