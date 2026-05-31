# Disaster Report Workflow API

FastAPI MVP service component for receiving disaster reports, extracting structured fields, keeping a short multi-message session, and exporting a confirmed report record.

This repository is packaged for competition submission as a backend service component. It does not include a production LINE bot integration yet; the current official entry point is the HTTP webhook-compatible endpoint `POST /webhook/report`.

## Project Overview

The service accepts report messages from LINE-like clients, classifies the sender route as official or citizen, extracts disaster entities with deterministic rules, asks for missing fields when needed, and creates a final report after explicit user confirmation.

Core capabilities:

- Session-based report intake through `POST /webhook/report`
- Official route and citizen route handling
- Missing-field detection and follow-up prompts
- Explicit confirm, correct, and cancel session actions
- SQLite-backed report persistence
- Swagger UI and OpenAPI documentation from FastAPI
- Test coverage for session, extraction, report, and end-to-end workflows

## Problem Statement

During disasters, reports often arrive as short, incomplete, or conversational messages. Response teams need a structured record that includes location, incident type, resource needs, reporter identity when required, and a confirmed final state.

This MVP focuses on the service layer that turns free-text reports into structured, confirmable records while preserving a human confirmation step before export.

## Component Positioning

This project is the backend service component in a larger disaster-reporting workflow.

- Upstream: LINE bot adapter, web client, or test client sends message payloads.
- This service: normalizes messages, extracts fields, manages session state, and persists reports.
- Downstream: command center dashboard, dispatch system, analytics database, or report export pipeline.

LINE production integration is intentionally not started in this packaging pass.

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

## Python Version and Dependencies

The current local packaging was verified with Python `3.14.3`. The service uses standard FastAPI, SQLAlchemy, Pydantic, Uvicorn, HTTPX, and Pytest dependencies listed in `requirements.txt`.

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
| `POST` | `/line/webhook` | Legacy LINE-style webhook report creation. |
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

## Swagger / OpenAPI Usage

FastAPI serves live API documentation at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- ReDoc: `http://127.0.0.1:8000/redoc`

The repository also contains `openapi.yaml` for submission/reference packaging. If API routes change later, regenerate a fresh spec from the running FastAPI app, then convert JSON to YAML if needed:

```bash
uvicorn app.main:app --reload
```

Then download:

```text
http://127.0.0.1:8000/openapi.json
```

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

- The extraction architecture is rule-based, not an LLM or trained NLP model.
- Current parser examples include encoded demo strings from the MVP test data.
- Only text messages are supported by `POST /webhook/report`.
- Authentication, authorization, rate limiting, and LINE signature verification are not production-ready.
- SQLite is used for MVP storage.
- The checked-in `openapi.yaml` is a static submission artifact; the live FastAPI spec at `/openapi.json` is the source to regenerate from.
- Human confirmation is required before final report export.

## Roadmap

- Add production LINE webhook adapter and signature verification.
- Replace or augment rule extraction with an LLM/AI-agent extraction layer.
- Add confidence thresholds, audit trails, and reviewer assignment.
- Add dashboard or dispatch-system integration.
- Add authentication and role-based access control.
- Add production database migrations and deployment configuration.
- Regenerate and align `openapi.yaml` automatically in CI.

## Additional Documentation

- [API specification](docs/API_SPEC.md)
- [System architecture](docs/SYSTEM_ARCHITECTURE.md)
- [AI usage](docs/AI_USAGE.md)
- [Python client sample](client_samples/python_client.py)
- [cURL examples](client_samples/curl_examples.md)
