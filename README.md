# 通報積木 API Disaster Report Workflow API

本專案是為「防災積木元件創新賽」整理的 API service component，定位為可重複使用的「通報 Call Component」。它以 FastAPI 提供災害通報訊息接收、欄位抽取、短期多輪 session 管理，以及人工確認後產生 final report 的 MVP 工作流程。

目前主要流程為：

1. `POST /webhook/report`
2. `POST /sessions/{session_id}/confirm`
3. `GET /reports`

本專案不宣稱 production-ready，也不宣稱已完成真實 LINE production integration。現階段主要入口為 HTTP webhook-compatible endpoint：`POST /webhook/report`，用於測試、展示與元件整合。

## Competition Context

本專案面向台灣公共部門與防災應用情境，作為「防災積木元件創新賽」的通報流程積木。它的重點不是完整災害平台，而是一個可被其他系統串接的後端 API 元件。

元件定位：

- 通報 Call Component
- API service component
- Backend workflow component for structured disaster-report intake

此元件可放在 LINE adapter、web form、dashboard form 或測試 client 後方。它負責接收類似通報的訊息，轉換成 session 狀態，辨識缺漏資訊，並在使用者明確確認後建立 final report。

## Project Overview

此服務接收 LINE-like client 或 web client 傳入的災害通報文字，依照來源情境區分 official route 與 citizen route，使用 deterministic rules 抽取災害實體欄位，並在資訊不足時回傳 follow-up prompt。

核心能力：

- Session-based report intake through `POST /webhook/report`
- Official route and citizen route handling
- Missing-field detection and follow-up prompts
- Explicit confirm, correct, and cancel session actions
- SQLite-backed MVP report persistence
- Swagger UI and OpenAPI documentation from FastAPI
- Test coverage for extraction, reports, sessions, and end-to-end workflows

## Problem Statement

災害通報往往不是完整表單，而是短句、口語、分段、或資訊不足的訊息。第一線應變單位需要把這些訊息整理成可查詢、可確認、可後續派工或彙整的結構化資料。

本元件要解決的問題是：將「非結構化通報文字」轉換成「可確認的結構化報告流程」。它會保留人工確認步驟，避免尚未確認的資訊直接成為 final report。

必要資訊包含：

- 發生地點
- 災害或事件類型
- 所需資源
- citizen route 所需的回報者姓名與電話
- 是否已由原通報者確認

## Component Positioning

本專案是較大防災通報流程中的 backend API service component。

- Upstream: LINE bot adapter, web client, dashboard form, or test client sends message payloads.
- This service: normalizes messages, extracts fields, manages session state, asks for missing information, and persists confirmed reports.
- Downstream: command center dashboard, GIS system, dispatch workflow, analytics database, or report export process.

LINE production integration 不在目前 MVP 範圍內。既有 `/line/webhook` 屬於 legacy/testing route；競賽展示的主要 workflow 使用 `/webhook/report`。

```mermaid
flowchart TD
    A[User / LINE-like Client / Web Client] --> B[POST /webhook/report]
    B --> C[Session Service]
    C --> D[Extraction Service]
    D --> E[Missing fields check]
    E -->|missing fields| F[Need more info]
    E -->|complete enough| G[Waiting confirmation]
    F --> B
    G --> H[POST /sessions/{session_id}/confirm]
    H --> I[Final Report]
    I --> J[(SQLite)]
    J --> K[GET /reports]
    K --> L[Dashboard / GIS / Dispatch System]
```

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

Input 是由 client 傳入的 JSON payload。主要欄位如下：

- `platform`: source platform label, for example `LINE`
- `sender_id`: user identifier
- `group_id`: group identifier for official/group reports, or `null` for citizen direct reports
- `message_type`: currently only `text` is supported
- `content`: raw report text
- `timestamp`: ISO 8601 timestamp

Process 是服務內部的處理流程：

1. The webhook router validates the request and rejects non-text messages.
2. The session service finds an open session for the same sender, platform, and group context, or creates a new session.
3. The extraction service applies deterministic keyword and regex rules.
4. Missing required fields are calculated from route-specific requirements.
5. The response either asks for more information or requests confirmation.
6. Confirmation creates a persisted report in the `reports` table.

Output 依照資料完整度分成三種主要狀態：

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
    "content": "@? 擐砍云?漯璈鋆??閬?2 ?唳芣?",
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

目前 MVP runtime 不呼叫 LLM。抽取邏輯實作在 `services/extraction_service.py`，使用 deterministic rule-based parser，而不是訓練完成的 NLP model 或 AI agent。

目前 AI-related architecture：

- Rule-based keyword and regex extraction
- Entity merge across follow-up messages in the same session
- Heuristic confidence score based on extracted fields
- Human confirmation before final report creation

目前限制：

- Parser 只能處理已設計的關鍵字與格式，可能漏掉其他自然語言變體。
- Confidence score 是簡單 heuristic，不代表安全性或正確性保證。
- Runtime 沒有 generative AI agent 進行自動決策。
- 若未來加入 LLM，仍應維持 schema validation 與 human-in-the-loop review。

Future extension point:

- `extract_report_entities(content)` can be replaced or augmented by an LLM/AI-agent extractor that returns the same structured entity schema.
- Any future LLM output should remain schema-constrained and human-reviewed before final report export.

## Generative AI Usage Disclosure

開發與文件整理過程中曾使用 generative AI assistance 協助：

- Draft and revise competition-oriented documentation.
- Summarize implemented API behavior from local source files.
- Prepare example client and cURL usage.
- Identify documentation gaps around AI usage, limitations, and human-in-the-loop behavior.

目前服務在 runtime 不呼叫 generative AI model。

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

Current clean package verification: 30 passed.

Run a specific test file:

```bash
python -m pytest tests/test_workflow_e2e.py
```

## Known Limitations

以下限制是目前 MVP 的實際狀態，尚未實作的項目不在此版本中宣稱已完成：

- This MVP is not production-ready.
- Real LINE production integration is not complete.
- LINE signature verification is not implemented for production use.
- Authentication and authorization are not implemented.
- Rate limiting and spam filtering are not implemented.
- Timeout handling, auto-cancel behavior, and fallback loop prevention are not implemented.
- The extraction architecture is rule-based, not an LLM or trained NLP model.
- Current parser examples include encoded demo strings from the MVP test data.
- Only text messages are supported by `POST /webhook/report`.
- SQLite is used for MVP storage.
- The checked-in `openapi.yaml` is a static submission artifact; the live FastAPI spec at `/openapi.json` is the source to regenerate from.
- Human confirmation is required before final report export.

## Roadmap

後續可擴充方向如下，皆屬 roadmap，不代表目前已完成：

- Add production LINE webhook adapter and signature verification.
- Replace or augment rule extraction with an LLM/AI-agent extraction layer.
- Add stronger confidence thresholds, audit trails, and reviewer assignment.
- Add dashboard, GIS, or dispatch-system integration.
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
