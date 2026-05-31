# API Specification

This document describes the current MVP API behavior for the competition submission package. It documents existing behavior only.

## Main Endpoint: `POST /webhook/report`

Creates a new report session or appends a follow-up message to an existing open session for the same `sender_id`, `platform`, and `group_id` context.

Request body:

```json
{
  "platform": "LINE",
  "sender_id": "official_user_001",
  "group_id": "official_group_001",
  "message_type": "text",
  "content": "@? disaster report text with location, incident, and resource need",
  "timestamp": "2026-05-31T10:00:00Z"
}
```

Important fields:

| Field | Required | Notes |
| --- | --- | --- |
| `platform` | Yes | Platform label, usually `LINE` in the MVP examples. |
| `sender_id` | Yes | Used with platform and group context to find open sessions. |
| `group_id` | No | Present for group/official route; `null` for direct citizen route. |
| `message_type` | Yes | Must be `text` in Phase 1. |
| `content` | Yes | Raw message text parsed by the rule-based extractor. |
| `timestamp` | Yes | ISO 8601 timestamp accepted by Pydantic. |

If `message_type` is not `text`, the API returns HTTP `422`.

## Example: Complete Official Report

Request:

```json
{
  "platform": "LINE",
  "sender_id": "official_user_001",
  "group_id": "official_group_001",
  "message_type": "text",
  "content": "@? disaster bridge damage at demo location, need 2 excavators",
  "timestamp": "2026-05-31T10:00:00Z"
}
```

Representative response shape:

```json
{
  "session_id": "7d5c3a8a-0c56-4eb4-a468-8e01759c2b02",
  "report_id": null,
  "platform": "LINE",
  "sender_id": "official_user_001",
  "group_id": "official_group_001",
  "source_type": "official",
  "source_context": "OFFICIAL_GROUP",
  "current_state": "WAITING_CONFIRMATION",
  "extracted_entities": {
    "location": {
      "address": "demo location"
    },
    "incident": {
      "type": "bridge_damage"
    },
    "needs": [
      {
        "item": "excavator",
        "category": "vehicle",
        "quantity": 2
      }
    ],
    "reporter": {},
    "confidence_score": 0.57,
    "warnings": []
  },
  "missing_fields": [],
  "status": "waiting_confirmation",
  "reply_message": {
    "type": "confirmation",
    "text": "confirmation prompt",
    "actions": ["confirm", "correct", "cancel"]
  },
  "created_at": "2026-05-31T10:00:00",
  "updated_at": "2026-05-31T10:00:00",
  "expired_at": null
}
```

Actual extracted values depend on the rule-based parser and the exact demo terms used in `content`.

## Missing Fields Behavior

The session service computes missing fields after every message.

Common missing fields:

| Missing field | Meaning |
| --- | --- |
| `sender_id` | Sender identity is missing. |
| `group_id` | Official route requires a group context. |
| `location` | Parser has not found a usable location/address. |
| `incident_or_needs` | Parser has not found an incident type or resource need. |
| `reporter.name` | Citizen route requires reporter name. |
| `reporter.phone` | Citizen route requires reporter phone. |

If required fields are missing, the response uses:

```json
{
  "current_state": "LOW_CONFIDENCE_REVIEW",
  "status": "need_more_info",
  "missing_fields": ["location", "reporter.name", "reporter.phone"],
  "reply_message": {
    "type": "question",
    "text": "follow-up prompt",
    "actions": null
  }
}
```

Follow-up messages are sent to `POST /webhook/report` again with the same `sender_id`, `platform`, and `group_id` context. The service appends the message to the open session and merges newly extracted fields.

## Confirm Behavior

Confirmation is session-based for the main workflow.

Endpoint:

```http
POST /sessions/{session_id}/confirm
```

Request:

```json
{
  "sender_id": "official_user_001",
  "action": "confirm"
}
```

Response:

```json
{
  "status": "confirmed",
  "current_state": "EXPORTED",
  "final_report": {
    "id": 1,
    "source_type": "official",
    "route": "A_official",
    "location": "demo location",
    "hazard_type": "bridge_damage",
    "requested_resource": "excavator",
    "quantity": 2,
    "critical_risk": false,
    "state": "confirmed"
  }
}
```

Rules:

- The confirming `sender_id` must match the session owner.
- A different sender receives HTTP `403`.
- Unknown sessions receive HTTP `404`.
- Confirmation creates a persisted report and changes session state to `EXPORTED`.

## Session Endpoints

| Method | Path | Request body | Response |
| --- | --- | --- | --- |
| `GET` | `/sessions/{session_id}` | None | Full session response. |
| `POST` | `/sessions/{session_id}/confirm` | `sender_id`, `action` | Final report export response. |
| `POST` | `/sessions/{session_id}/correct` | `sender_id`, `content` | Updated session response. |
| `POST` | `/sessions/{session_id}/cancel` | `sender_id` | Cancelled session response. |

Correction request:

```json
{
  "sender_id": "citizen_user_001",
  "content": "corrected or additional report details"
}
```

Cancel request:

```json
{
  "sender_id": "citizen_user_001"
}
```

## Report Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/reports` | List reports ordered by creation time descending. |
| `GET` | `/reports/{report_id}` | Read a single report. |
| `POST` | `/reports/{report_id}/confirm` | Mark an existing report `confirmed`. |
| `POST` | `/reports/{report_id}/cancel` | Mark an existing report `cancelled`. |

Report response shape:

```json
{
  "id": 1,
  "message_id": null,
  "source_type": "official",
  "route": "A_official",
  "raw_text": "original and follow-up message text",
  "location": "demo location",
  "hazard_type": "bridge_damage",
  "requested_resource": "excavator",
  "quantity": 2,
  "critical_risk": false,
  "confidence_score": "0.8",
  "missing_fields": [],
  "validation_warnings": [],
  "state": "confirmed",
  "created_at": "2026-05-31T10:00:00",
  "updated_at": "2026-05-31T10:00:00"
}
```
