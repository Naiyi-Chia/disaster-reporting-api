# LINE Disaster Report API - MVP

A production-ready FastAPI backend for receiving and managing disaster reports via LINE group messages and web APIs.

## Features

- LINE webhook integration for receiving disaster reports from group messages
- Automatic disaster report detection and classification
- SQLite database for storing reports
- RESTful APIs for querying and managing reports
- Structured information extraction from unstructured text
- Report state management (pending → confirmed/cancelled)

## Project Structure

```
app/
  main.py                 # FastAPI app initialization
  database.py             # SQLAlchemy setup
routers/
  health.py               # Health check endpoint
  line.py                 # LINE webhook router
  report.py               # Web-based report ingest router
  reports.py              # Report management APIs
services/
  line_service.py         # LINE message parsing and extraction
  report_service.py       # Report CRUD operations
  reports_service.py      # Report database service
models/
  report.py               # Report ORM and Pydantic schemas
  line.py                 # LINE webhook schemas
tests/
  test_report.py          # Comprehensive test suite
requirements.txt
README.md
```

## Installation

1. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

2. Activate the environment:

   **Windows PowerShell:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   **Windows CMD:**
   ```cmd
   .\.venv\Scripts\activate.bat
   ```

   **macOS/Linux:**
   ```bash
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

## Running the Server

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

**Swagger UI:** http://localhost:8000/docs
**ReDoc:** http://localhost:8000/redoc

## API Endpoints

### Health Check
```
GET /health
```

### LINE Webhook
```
POST /line/webhook
```
Receives LINE webhook events and creates reports for messages containing disaster keywords.

### Web Report Ingest
```
POST /report/ingest
```
Directly ingest a report via web API.

### Natural Language Chat Report Ingest
```
POST /chat/report
```
Ingest an unstructured natural language report using text-only payloads.

### Reports Management
```
GET /reports                    # List all reports
GET /reports/{report_id}         # Get specific report
POST /reports/{report_id}/confirm # Mark as confirmed
POST /reports/{report_id}/cancel  # Mark as cancelled
```

## Report Detection

The system automatically creates reports when a message contains any of these keywords:
- `@通報`
- `通報`
- `救命`
- `受困`
- `缺水`
- `火災`
- `淹水`

## Information Extraction

The system extracts the following information from messages:

| Pattern | Field | Value |
|---------|-------|-------|
| `馬太鞍溪橋` | location | 馬太鞍溪橋|
| `橋斷裂` / `斷裂` | incident_type | bridge_collapse |
| `缺水` | incident_type | water_shortage |
| `淹水` | incident_type | flood |
| `火災` | incident_type | fire |
| `怪手` | resource_type | excavator |
| `受困` / `救命` | risk_level | critical |
| `\d+台` | quantity | [number] |

## Example Usage

### LINE Webhook Example

```bash
curl -X POST "http://localhost:8000/line/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "type": "message",
        "source": {
          "type": "group",
          "groupId": "mock-group-id",
          "userId": "mock-user-id"
        },
        "message": {
          "type": "text",
          "text": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手"
        }
      }
    ]
  }'
```

Response:
```json
{
  "processed": true,
  "created_reports": [
    {
      "id": 1,
      "incident_type": "bridge_collapse",
      "location": "馬太鞍溪橋",
      "state": "pending_confirmation"
    }
  ]
}
```

### Chat Report Example
```bash
curl -X POST "http://localhost:8000/chat/report" \
  -H "Content-Type: application/json" \
  -d '{"text":"@通報 馬太鞍溪橋斷了，需要兩台怪手"}'
```

Response:
```json
{
  "id": 1,
  "raw_text": "@通報 馬太鞍溪橋斷了，需要兩台怪手",
  "location": "馬太鞍溪橋",
  "hazard_type": "bridge_collapse",
  "requested_resource": "excavator",
  "quantity": 2,
  "critical_risk": true,
  "confidence_score": 0.8,
  "missing_fields": [],
  "validation_warnings": [],
  "state": "pending_confirmation"
}
```

### List Reports

```bash
curl -X GET "http://localhost:8000/reports"
```

Response:
```json
[
  {
    "id": 1,
    "source_channel": "line",
    "line_group_id": "mock-group-id",
    "line_user_id": "mock-user-id",
    "original_message": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手",
    "route": "B_citizen",
    "location": "馬太鞍溪橋",
    "incident_type": "bridge_collapse",
    "resource_type": "excavator",
    "quantity": 2,
    "risk_level": null,
    "state": "pending_confirmation",
    "created_at": "2026-05-24T14:30:00",
    "updated_at": "2026-05-24T14:30:00"
  }
]
```

### Get Specific Report

```bash
curl -X GET "http://localhost:8000/reports/1"
```

### Confirm Report

```bash
curl -X POST "http://localhost:8000/reports/1/confirm"
```

### Cancel Report

```bash
curl -X POST "http://localhost:8000/reports/1/cancel"
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Database

The application uses SQLite with SQLAlchemy ORM. The database file is created automatically as `disaster_reports.db` in the project root.

### Report Table Schema

| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary key |
| source_channel | String | Where the report came from (line, web) |
| line_group_id | String | LINE group ID if from LINE |
| line_user_id | String | LINE user ID if from LINE |
| original_message | Text | Full original message |
| route | String | A_official or B_citizen |
| location | String | Detected location |
| incident_type | String | Type of disaster (bridge_collapse, fire, flood, etc.) |
| resource_type | String | Type of resource needed (excavator, etc.) |
| quantity | Integer | Quantity of resources |
| risk_level | String | Risk assessment (critical, high, etc.) |
| state | String | Current state (pending_confirmation, confirmed, cancelled) |
| created_at | DateTime | Timestamp when created |
| updated_at | DateTime | Timestamp when last updated |

## Development Notes

- The LINE webhook parser is currently a mock implementation for testing
- In production, implement proper LINE signature verification
- All text extraction uses simple keyword matching; can be upgraded with NLP
- Consider adding authentication and rate limiting for production use
