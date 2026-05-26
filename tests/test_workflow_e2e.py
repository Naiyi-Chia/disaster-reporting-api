from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client(tmp_path):
    import models.report  # noqa: F401
    import models.session  # noqa: F401

    db_path = tmp_path / "workflow_e2e.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _timestamp() -> str:
    return datetime.utcnow().isoformat() + "Z"


def test_official_complete_workflow(client: TestClient) -> None:
    response = client.post(
        "/webhook/report",
        json={
            "platform": "LINE",
            "sender_id": "official_auto_001",
            "group_id": "official_group_001",
            "message_type": "text",
            "content": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手",
            "timestamp": _timestamp(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "waiting_confirmation"
    assert data["current_state"] == "WAITING_CONFIRMATION"
    assert data["source_type"] == "official"
    assert data["extracted_entities"]["location"]["address"] == "馬太鞍溪橋"
    assert data["extracted_entities"]["needs"][0]["item"] == "怪手"
    assert data["extracted_entities"]["needs"][0]["quantity"] == 2

    confirm_response = client.post(
        f"/sessions/{data['session_id']}/confirm",
        json={"sender_id": "official_auto_001", "action": "confirm"},
    )

    assert confirm_response.status_code == 200
    confirm_data = confirm_response.json()
    assert confirm_data["status"] == "confirmed"
    assert confirm_data["current_state"] == "EXPORTED"
    assert confirm_data["final_report"]["id"] is not None


def test_citizen_incomplete_then_follow_up_workflow(client: TestClient) -> None:
    first_response = client.post(
        "/webhook/report",
        json={
            "platform": "LINE",
            "sender_id": "citizen_auto_001",
            "group_id": None,
            "message_type": "text",
            "content": "我這邊缺水，家裡淹水了",
            "timestamp": _timestamp(),
        },
    )

    assert first_response.status_code == 200
    first_data = first_response.json()
    assert first_data["status"] == "need_more_info"
    assert first_data["current_state"] == "LOW_CONFIDENCE_REVIEW"
    assert "location" in first_data["missing_fields"]
    assert "reporter.name" in first_data["missing_fields"]
    assert "reporter.phone" in first_data["missing_fields"]

    follow_up_response = client.post(
        "/webhook/report",
        json={
            "platform": "LINE",
            "sender_id": "citizen_auto_001",
            "group_id": None,
            "message_type": "text",
            "content": "地址是花蓮縣光復鄉 XXX 路 12 號，我叫王小明，電話 0912-345-678",
            "timestamp": _timestamp(),
        },
    )

    assert follow_up_response.status_code == 200
    follow_up_data = follow_up_response.json()
    assert follow_up_data["session_id"] == first_data["session_id"]
    assert follow_up_data["status"] == "waiting_confirmation"
    assert follow_up_data["current_state"] == "WAITING_CONFIRMATION"
    assert follow_up_data["missing_fields"] == []
    assert follow_up_data["extracted_entities"]["location"]["address"] == "花蓮縣光復鄉 XXX 路 12 號"
    assert follow_up_data["extracted_entities"]["reporter"]["name"] == "王小明"
    assert follow_up_data["extracted_entities"]["reporter"]["phone"] == "0912-345-678"

    confirm_response = client.post(
        f"/sessions/{follow_up_data['session_id']}/confirm",
        json={"sender_id": "citizen_auto_001", "action": "confirm"},
    )

    assert confirm_response.status_code == 200
    confirm_data = confirm_response.json()
    assert confirm_data["status"] == "confirmed"
    assert confirm_data["final_report"]["id"] is not None


def test_permission_lock(client: TestClient) -> None:
    create_response = client.post(
        "/webhook/report",
        json={
            "platform": "LINE",
            "sender_id": "firefighter_A",
            "group_id": "official_group_001",
            "message_type": "text",
            "content": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手",
            "timestamp": _timestamp(),
        },
    )

    assert create_response.status_code == 200
    session_id = create_response.json()["session_id"]

    confirm_response = client.post(
        f"/sessions/{session_id}/confirm",
        json={"sender_id": "firefighter_B", "action": "confirm"},
    )

    assert confirm_response.status_code == 403


def test_get_reports_after_confirmed_report(client: TestClient) -> None:
    create_response = client.post(
        "/webhook/report",
        json={
            "platform": "LINE",
            "sender_id": "reports_auto_001",
            "group_id": "official_group_001",
            "message_type": "text",
            "content": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手",
            "timestamp": _timestamp(),
        },
    )
    session_id = create_response.json()["session_id"]

    confirm_response = client.post(
        f"/sessions/{session_id}/confirm",
        json={"sender_id": "reports_auto_001", "action": "confirm"},
    )
    report_id = confirm_response.json()["final_report"]["id"]

    reports_response = client.get("/reports")

    assert reports_response.status_code == 200
    reports = reports_response.json()
    assert any(
        report["id"] == report_id and report["state"] in {"confirmed", "exported"}
        for report in reports
    )
