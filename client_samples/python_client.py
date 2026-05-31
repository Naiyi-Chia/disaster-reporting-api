"""Minimal client examples for the Disaster Report Workflow API.

Run the API first:

    uvicorn app.main:app --reload

Then run this file:

    python client_samples/python_client.py

The examples use only the Python standard library so they do not add
dependencies beyond the application requirements.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:8000"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        f"{BASE_URL}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else None
    except HTTPError as exc:
        raw = exc.read().decode("utf-8")
        return exc.code, json.loads(raw) if raw else raw


def post_webhook_report(payload: dict[str, Any]) -> dict[str, Any]:
    status, data = request_json("POST", "/webhook/report", payload)
    print("\nPOST /webhook/report")
    print("Status:", status)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return data


def post_follow_up(sender_id: str, content: str) -> dict[str, Any]:
    payload = {
        "platform": "LINE",
        "sender_id": sender_id,
        "group_id": None,
        "message_type": "text",
        "content": content,
        "timestamp": now_iso(),
    }
    return post_webhook_report(payload)


def confirm_session(session_id: str, sender_id: str) -> dict[str, Any]:
    payload = {"sender_id": sender_id, "action": "confirm"}
    status, data = request_json("POST", f"/sessions/{session_id}/confirm", payload)
    print(f"\nPOST /sessions/{session_id}/confirm")
    print("Status:", status)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return data


def get_reports() -> list[dict[str, Any]]:
    status, data = request_json("GET", "/reports")
    print("\nGET /reports")
    print("Status:", status)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return data


def demo_official_report() -> None:
    payload = {
        "platform": "LINE",
        "sender_id": "official_python_client_001",
        "group_id": "official_group_001",
        "message_type": "text",
        "content": "@? 擐砍云?漯璈鋆??閬?2 ?唳芣?",
        "timestamp": now_iso(),
    }
    result = post_webhook_report(payload)
    confirm_session(result["session_id"], payload["sender_id"])


def demo_citizen_follow_up_and_confirm() -> None:
    sender_id = "citizen_python_client_001"
    first_payload = {
        "platform": "LINE",
        "sender_id": sender_id,
        "group_id": None,
        "message_type": "text",
        "content": "??蝻箸偌嚗振鋆⊥溯瘞港?",
        "timestamp": now_iso(),
    }
    first_result = post_webhook_report(first_payload)

    post_follow_up(
        sender_id,
        "?啣??航?桃腦?儔??XXX 頝?12 ????????餉店 0912-345-678",
    )
    confirm_session(first_result["session_id"], sender_id)


if __name__ == "__main__":
    demo_official_report()
    demo_citizen_follow_up_and_confirm()
    get_reports()
