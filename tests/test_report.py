from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_report_ingest_success() -> None:
    payload = {
        "message_id": "MSG-20260524-001",
        "source_type": "official_group",
        "raw_text": "馬太鞍溪橋橋斷裂，怪手已到場，缺水且火災風險高。",
        "timestamp": "2026-05-24T14:30:00Z",
        "contact": {"name": "Jane Doe", "phone": "09xx-xxx-xxx"},
    }

    response = client.post("/report/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["message_id"] == payload["message_id"]
    assert data["source_type"] == payload["source_type"]
    assert data["route"] == "A_official"
    assert data["location"] == "馬太鞍溪橋"
    assert data["hazard_type"] == "bridge_collapse"
    assert data["requested_resource"] == "excavator"
    assert data["quantity"] is None
    assert data["critical_risk"] is False
    assert data["missing_fields"] == []
    assert data["state"] == "pending_confirmation"


def test_report_ingest_routing_for_citizen_sources() -> None:
    payload = {
        "message_id": "MSG-20260524-002",
        "source_type": "citizen_line",
        "raw_text": "這裡有怪手在馬太鞍溪橋附近，受困情況需要協助。",
        "timestamp": "2026-05-24T14:35:00Z",
    }

    response = client.post("/report/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "B_citizen"
    assert data["critical_risk"] is True
    assert data["location"] == "馬太鞍溪橋"
    # hazard_type missing -> needs clarification
    assert "hazard_type" in data["missing_fields"]


def test_line_webhook_creates_report() -> None:
    payload = {
        "events": [
            {
                "type": "message",
                "source": {
                    "type": "group",
                    "groupId": "mock-group-id",
                    "userId": "mock-user-id",
                },
                "message": {
                    "type": "text",
                    "text": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手",
                },
            }
        ]
    }

    response = client.post("/line/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["processed"] is True
    assert len(data["created_reports"]) == 1
    report = data["created_reports"][0]
    assert report["hazard_type"] == "bridge_collapse"
    assert report["location"] == "馬太鞍溪橋"
    assert report["state"] == "pending_confirmation"


def test_line_webhook_ignores_unrelated_message() -> None:
    payload = {
        "events": [
            {
                "type": "message",
                "source": {
                    "type": "group",
                    "groupId": "mock-group-id",
                    "userId": "mock-user-id",
                },
                "message": {
                    "type": "text",
                    "text": "今天天氣真好",
                },
            }
        ]
    }

    response = client.post("/line/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["processed"] is True
    assert len(data["created_reports"]) == 0


def test_get_reports() -> None:
    payload = {
        "events": [
            {
                "type": "message",
                "source": {
                    "type": "group",
                    "groupId": "mock-group-id",
                    "userId": "mock-user-id",
                },
                "message": {
                    "type": "text",
                    "text": "@通報 缺水緊急",
                },
            }
        ]
    }

    create_response = client.post("/line/webhook", json=payload)
    assert create_response.status_code == 200
    created_reports = create_response.json()["created_reports"]
    assert len(created_reports) == 1
    created_report_id = created_reports[0]["id"]
    assert created_reports[0]["hazard_type"] == "water_shortage"

    list_response = client.get("/reports")
    assert list_response.status_code == 200
    reports = list_response.json()
    created_report = next(r for r in reports if r["id"] == created_report_id)
    assert created_report["hazard_type"] == "water_shortage"


def test_get_report_detail() -> None:
    payload = {
        "events": [
            {
                "type": "message",
                "source": {
                    "type": "group",
                    "groupId": "mock-group-id",
                    "userId": "mock-user-id",
                },
                "message": {
                    "type": "text",
                    "text": "@通報 火災緊急",
                },
            }
        ]
    }

    create_response = client.post("/line/webhook", json=payload)
    assert create_response.status_code == 200
    report_id = create_response.json()["created_reports"][0]["id"]

    detail_response = client.get(f"/reports/{report_id}")
    assert detail_response.status_code == 200
    data = detail_response.json()
    assert data["id"] == report_id
    assert data["hazard_type"] == "fire"


def test_chat_report_complete_official() -> None:
    payload = {"text": "@通報 馬太鞍溪橋斷了，需要兩台怪手"}

    response = client.post("/chat/report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "馬太鞍溪橋"
    assert data["hazard_type"] == "bridge_collapse"
    assert data["requested_resource"] == "excavator"
    assert data["quantity"] == 2
    assert data["missing_fields"] == []
    assert data["state"] == "pending_confirmation"


def test_chat_report_incomplete_citizen() -> None:
    payload = {"text": "這邊需要水"}

    response = client.post("/chat/report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["requested_resource"] == "water"
    assert "location" in data["missing_fields"]
    assert "hazard_type" in data["missing_fields"]
    assert data["state"] == "needs_clarification"


def test_confirm_report() -> None:
    payload = {
        "events": [
            {
                "type": "message",
                "source": {
                    "type": "group",
                    "groupId": "mock-group-id",
                    "userId": "mock-user-id",
                },
                "message": {
                    "type": "text",
                    "text": "@通報 淹水緊急",
                },
            }
        ]
    }

    create_response = client.post("/line/webhook", json=payload)
    assert create_response.status_code == 200
    report_id = create_response.json()["created_reports"][0]["id"]

    confirm_response = client.post(f"/reports/{report_id}/confirm")
    assert confirm_response.status_code == 200
    data = confirm_response.json()
    assert data["state"] == "confirmed"


def test_cancel_report() -> None:
    payload = {
        "events": [
            {
                "type": "message",
                "source": {
                    "type": "group",
                    "groupId": "mock-group-id",
                    "userId": "mock-user-id",
                },
                "message": {
                    "type": "text",
                    "text": "@通報 救命",
                },
            }
        ]
    }

    create_response = client.post("/line/webhook", json=payload)
    assert create_response.status_code == 200
    report_id = create_response.json()["created_reports"][0]["id"]

    cancel_response = client.post(f"/reports/{report_id}/cancel")
    assert cancel_response.status_code == 200
    data = cancel_response.json()
    assert data["state"] == "cancelled"


def test_report_ingest_persists_to_db() -> None:
    payload = {
        "message_id": "MSG-20260524-100",
        "source_type": "official_group",
        "raw_text": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手",
        "timestamp": "2026-05-24T15:00:00Z",
    }

    response = client.post("/report/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    created_id = data["id"]

    # Confirm the report is returned by the list endpoint
    list_response = client.get("/reports")
    assert list_response.status_code == 200
    reports = list_response.json()
    assert any(r["id"] == created_id for r in reports)
