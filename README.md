# Disaster Report Workflow API

防災積木元件創新賽 submission package for a disaster-reporting API component.

This project is a FastAPI MVP service component for receiving disaster report messages, extracting structured fields, maintaining a short multi-message session, and exporting a confirmed report record after human confirmation.

The current main workflow is:

1. `POST /webhook/report`
2. `POST /sessions/{session_id}/confirm`
3. `GET /reports`

This repository does not claim production readiness. It does not include completed real LINE production integration; `POST /webhook/report` is the current HTTP webhook-compatible entry point for testing and component integration.

## Competition Context

This project is prepared for the 防災積木元件創新賽 as a reusable disaster-response building block.

Component positioning:

- 通報 Call Component
- API service component
- Backend workflow component for structured disaster-report intake

The component can sit behind a LINE adapter, web form, dashboard, or test client. Its role is to receive report-like messages, normalize them into session state, detect missing information, and create a final report only after explicit confirmation.

## Project Overview

The service accepts report messages from LINE-like clients, classifies the sender route as official or citizen, extracts disaster entities with deterministic rules, asks for missing fields when needed, and creates a report record after user confirmation.

Core capabilities:

- Session-based report intake through `POST /webhook/report`
- Official route and citizen route handling
- Missing-field detection and follow-up prompts
- Explicit confirm, correct, and cancel session actions
- SQLite-backed MVP report persistence
- Swagger UI and OpenAPI documentation from FastAPI
- Test coverage for extraction, reports, sessions, and end-to-end workflows

## Problem Statement

Disaster reports often arrive as short, incomplete, or conversational messages. Response teams need structured records that capture where the incident happened, what happened, what resource is needed, who reported it when required, and whether the report has been confirmed.

災害現場通報常常是片段式、口語化或資訊不完整的訊息。救災單位需要把這些訊息整理成可追蹤、可確認、可後續派工或彙整的結構化資料。本元件的目標是提供一個「通報訊息到結構化報告」的 API 服務流程，並保留人工確認機制，避免未確認資訊直接輸出。

## Component Positioning

This project is the backend service component in a larger disaster-reporting workflow.

- Upstream: LINE bot adapter, web client, dashboard form, or test client sends message payloads.
- This service: normalizes messages, extracts fields, manages session state, asks for missing information, and persists confirmed reports.
- Downstream: command center dashboard, dispatch workflow, analytics database, or report export process.

LINE production integration is intentionally outside the current MVP scope. The existing `/line/webhook` route is a legacy/testing route; the main competition workflow uses `/webhook/report`.

## Quick Start

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Open:

- API base URL: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Python Version and Dependencies

## Python Version and Dependencies

Recommended: Python 3.11+

Local verified environment: Python 3.14.3.

The service uses FastAPI, SQLAlchemy, Pydantic, Uvicorn, HTTPX, Requests, and Pytest dependencies listed in `requirements.txt`.

Install only from `requirements.txt`; do not package local virtual environments, caches, or SQLite database files.

Excluded local artifacts:

- `venv/`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `*.db`

## API Endpoint Summary

Main workflow endpoint:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/webhook/report` | Create or update a disaster-report session from a LINE-like text message. |

Session endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/sessions/{session_id}` | Read current session state and extracted entities. |
| `POST` | `/sessions/{session_id}/confirm` | Confirm a completed session and create the final report. |
| `POST` | `/sessions/{session_id}/correct` | Add corrected text to the same session. |
| `POST` | `/sessions/{session_id}/cancel` | Cancel an open session. |

Report endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/reports` | List persisted reports. |
| `GET` | `/reports/{report_id}` | Read one persisted report. |
| `POST` | `/reports/{report_id}/confirm` | Mark a persisted report as confirmed. |
| `POST` | `/reports/{report_id}/cancel` | Mark a persisted report as cancelled. |

Supporting and legacy endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Health check. |
| `POST` | `/line/webhook` | Legacy LINE-style webhook report creation for MVP testing. |
| `POST` | `/report/ingest` | Legacy direct report ingest. |
| `POST` | `/chat/report` | Legacy text-only chat ingest. |

## Input / Process / Output

Input:

- `platform`: source platform label, for example `LINE`
- `sender_id`: user identifier
- `group_id`: group identifier for official/group reports, or `null` for citizen direct reports
- `message_type`: currently only `text` is supported
- `content`: raw report text
- `timestamp`: ISO 8601 timestamp

Process:

1. The webhook router validates the request and rejects non-text messages.
2. The session service finds an open session for the same sender, platform, and group context, or creates a new session.
3. The extraction service applies deterministic keyword and regex rules.
4. Missing required fields are calculated from route-specific requirements.
5. The response either asks for more information or requests confirmation.
6. Confirmation creates a persisted report in the `reports` table.

Output:

- Incomplete reports return `status: "need_more_info"` and a `missing_fields` list.
- Complete reports return `status: "waiting_confirmation"` and confirmation actions.
- Confirmed sessions return `status: "confirmed"` and a `final_report` object.

## Main Workflow Example

Create or update a report session:

```bash
curl -X POST "http://127.0.0.1:8000/webhook/report" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "LINE",
    "sender_id": "official_demo_001",
    "group_id": "official_group_001",
    "message_type": "text",
    "content": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手",
    "timestamp": "2026-05-31T10:00:00Z"
  }'
```

Confirm the session after the response returns `status: "waiting_confirmation"`:

```bash
curl -X POST "http://127.0.0.1:8000/sessions/<SESSION_ID>/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "official_demo_001",
    "action": "confirm"
  }'
```

List reports:

```bash
curl -X GET "http://127.0.0.1:8000/reports"
```

## AI Architecture and Limitations

The current MVP does not call an LLM at runtime. Extraction is implemented with deterministic rules in `services/extraction_service.py`.

Current AI-related architecture:

- Rule-based keyword and regex extraction
- Entity merge across follow-up messages in the same session
- Heuristic confidence score based on extracted fields
- Human confirmation before final report creation

Current limitations:

- The parser may miss valid reports that use wording outside the known patterns.
- The parser is not a trained NLP model and does not understand all natural-language variations.
- The confidence score is a simple heuristic, not a safety guarantee.
- No runtime generative AI agent currently performs autonomous decisions.

Future extension point:

- `extract_report_entities(content)` can be replaced or augmented by an LLM/AI-agent extractor that returns the same structured entity schema.
- Any future LLM output should remain schema-constrained and human-reviewed before final report export.

## Generative AI Usage Disclosure

Generative AI assistance was used during development and documentation packaging to:

- Draft and revise competition-oriented documentation.
- Summarize implemented API behavior from local source files.
- Prepare example client and cURL usage.
- Identify documentation gaps around AI usage, limitations, and human-in-the-loop behavior.

No runtime generative AI model is currently invoked by this service.

## Client Sample Code

Sample client code is provided under `client_samples/`.

- `client_samples/python_client.py`: demonstrates the official report flow, citizen incomplete report flow, citizen follow-up message, session confirmation, and `GET /reports`.
- `client_samples/curl_examples.md`: provides cURL examples for manually calling the API endpoints.

To run the Python client sample, start the API server first:

```bash
uvicorn app.main:app --reload
```

Then open another terminal and run:

```bash
python client_samples/python_client.py
```

The sample client demonstrates:

1. Creating an official group report
2. Confirming the official report session
3. Creating a citizen incomplete report
4. Sending a citizen follow-up message with missing information
5. Confirming the citizen report session
6. Reading created reports from `GET /reports`

For manual API calls, see:

```text
client_samples/curl_examples.md
```

## Swagger / OpenAPI Usage

FastAPI serves live API documentation at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- ReDoc: `http://127.0.0.1:8000/redoc`

The repository also contains `openapi.yaml` for submission/reference packaging. If API routes change later, regenerate a fresh spec from the running FastAPI app:

```bash
uvicorn app.main:app --reload
```

Then download:

```text
http://127.0.0.1:8000/openapi.json
```

If YAML is required, convert the generated OpenAPI JSON to YAML and replace `openapi.yaml`.



## How to Run Tests

Run the full test suite:

```bash
python -m pytest
```

Run a specific test file:

```bash
python -m pytest tests/test_workflow_e2e.py
```

## Known Limitations

- This MVP is not production-ready.
- Real LINE production integration is not complete.
- LINE signature verification is not implemented for production use.
- Authentication, authorization, rate limiting, and spam filtering are not implemented.
- Timeout handling, auto-cancel behavior, and fallback loop prevention are not implemented.
- The extraction architecture is rule-based, not an LLM or trained NLP model.
- Current parser examples include encoded demo strings from the MVP test data.
- Only text messages are supported by `POST /webhook/report`.
- SQLite is used for MVP storage.
- The checked-in `openapi.yaml` is a static submission artifact; the live FastAPI spec at `/openapi.json` is the source to regenerate from.
- Human confirmation is required before final report export.

## Roadmap

- Add production LINE webhook adapter and signature verification.
- Replace or augment rule extraction with an LLM/AI-agent extraction layer.
- Add stronger confidence thresholds, audit trails, and reviewer assignment.
- Add dashboard or dispatch-system integration.
- Add authentication and role-based access control.
- Add rate limiting and spam-abuse controls.
- Add timeout and auto-cancel policy after the behavior is designed and tested.
- Add production database migrations and deployment configuration.
- Regenerate and align `openapi.yaml` automatically in CI.

## Additional Documentation

- [API specification](docs/API_SPEC.md)
- [System architecture](docs/SYSTEM_ARCHITECTURE.md)
- [AI usage](docs/AI_USAGE.md)
- [Python client sample](client_samples/python_client.py)
- [cURL examples](client_samples/curl_examples.md)
