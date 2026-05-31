# cURL Examples

Start the API before running these examples:

```bash
uvicorn app.main:app --reload
```

Swagger UI is available at:

```text
http://127.0.0.1:8000/docs
```

## Official Report

```bash
curl -X POST "http://127.0.0.1:8000/webhook/report" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "LINE",
    "sender_id": "official_curl_001",
    "group_id": "official_group_001",
    "message_type": "text",
    "content": "@? 擐砍云?漯璈鋆??閬?2 ?唳芣?",
    "timestamp": "2026-05-31T10:00:00Z"
  }'
```

Expected behavior:

```text
status = waiting_confirmation
current_state = WAITING_CONFIRMATION
source_type = official
missing_fields = []
```

## Citizen Incomplete Report

```bash
curl -X POST "http://127.0.0.1:8000/webhook/report" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "LINE",
    "sender_id": "citizen_curl_001",
    "group_id": null,
    "message_type": "text",
    "content": "??蝻箸偌嚗振鋆⊥溯瘞港?",
    "timestamp": "2026-05-31T10:05:00Z"
  }'
```

Expected behavior:

```text
status = need_more_info
current_state = LOW_CONFIDENCE_REVIEW
missing_fields includes location, reporter.name, reporter.phone
reply_message.type = question
```

## Citizen Follow-Up

Send the follow-up with the same `sender_id`, `platform`, and `group_id` context. The service will update the existing open session.

```bash
curl -X POST "http://127.0.0.1:8000/webhook/report" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "LINE",
    "sender_id": "citizen_curl_001",
    "group_id": null,
    "message_type": "text",
    "content": "?啣??航?桃腦?儔??XXX 頝?12 ????????餉店 0912-345-678",
    "timestamp": "2026-05-31T10:06:00Z"
  }'
```

Expected behavior:

```text
session_id = same session_id as the incomplete report
status = waiting_confirmation
current_state = WAITING_CONFIRMATION
missing_fields = []
```

## Confirm

Replace `<SESSION_ID>` with the `session_id` returned by `POST /webhook/report`.

```bash
curl -X POST "http://127.0.0.1:8000/sessions/<SESSION_ID>/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "citizen_curl_001",
    "action": "confirm"
  }'
```

Expected behavior:

```text
status = confirmed
current_state = EXPORTED
final_report is created
```

## GET /reports

```bash
curl -X GET "http://127.0.0.1:8000/reports"
```

Expected behavior:

```text
Returns persisted report records ordered by created_at descending.
Confirmed session reports have state = confirmed.
```
