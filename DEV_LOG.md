## 2026-05-26 Phase 2B Legacy Endpoint Adapter Migration Summary

### Status
Phase 2B completed and verified.

### Goal
Migrate legacy endpoints to use the centralized `extraction_service` through adapter mappings while preserving each endpoint's existing request and response shape.

### Endpoints Updated
- `POST /report/ingest`
- `POST /chat/report`
- `POST /line/webhook`

Main workflow endpoint `/webhook/report` was not changed.

### Files Changed
- `services/extraction_service.py`
- `services/line_service.py`
- `services/report_service.py`
- `tests/test_extraction_service.py`

### Parser Logic Replaced
- Removed duplicated natural-language extraction from `line_service.extract_report_info()`.
- Removed duplicated annotation parsing from `report_service._extract_annotations()`.
- Legacy endpoints now use `extraction_service` via adapters.

### Adapters Added
- `adapt_to_legacy_report_info(raw_text)`
- `adapt_to_legacy_annotations(raw_text)`

### Test Result
- Command: `python -m pytest`
- Result: `30 passed, 156 warnings`

### Remaining Risks
- Extraction is still keyword / heuristic based.
- Test runs mutate local SQLite DB and bytecode caches.
- `.pytest_cache` permission warning remains.
- Real LINE integration has not started yet.
- DB schema was not changed.

### Recommended Next Step
Create a clean Git checkpoint, then proceed to Phase 2C: session correction / cancel / timeout behavior.

## 2026-05-26 Phase 2A Manual Validation

- Official complete report passed
- Citizen incomplete report returned need_more_info
- Citizen follow-up reused same session and reached WAITING_CONFIRMATION
- Citizen confirm created final_report
- GET /reports returned confirmed citizen report id=80
- Current status: Phase 2A parser centralization validated

## 2026-05-26 Phase 2A Parser Centralization Summary

### Files Changed
- `services/extraction_service.py`
- `services/session_service.py`
- `tests/test_extraction_service.py`

### Logic Moved
- Moved rule-based natural-language extraction logic from `session_service` into `services/extraction_service.py`.
- Added centralized extraction contract:
  - `location.address`
  - `incident.type`
  - `incident.description`
  - `incident.severity`
  - `needs[]`
  - `reporter.name`
  - `reporter.phone`
  - `confidence_score`
  - `warnings`
- `/webhook/report` now uses the centralized parser while preserving session workflow behavior.

### Tests
- Added `tests/test_extraction_service.py`.
- Covered extraction contract and follow-up merge behavior.

### Test Result
- `python -m pytest`
- Result: `28 passed, 156 warnings`

### Known Risks
- `/line/webhook`, `/chat/report`, and `/report/ingest` still use older parser paths.
- `confidence_score` is currently heuristic.
- Legacy endpoints still need adapter-based migration.
- Git is not installed yet, so no git diff/checkpoint was created.

### Recommended Next Step
- Phase 2B: migrate legacy endpoints to use `extraction_service` via adapters while preserving their current response shapes.

## 2026-05-26 E2E Workflow Test Checkpoint

### Test Result
- Ran `python -m pytest`
- Result: `26 passed, 156 warnings`
- Added/confirmed automated end-to-end workflow tests

### Meaning
Manual Swagger acceptance tests are now mostly automated.

Covered workflows:
- Official complete workflow
- Citizen incomplete then follow-up workflow
- Permission lock
- GET /reports after confirmed report

### Notes
- Warnings remain but no test failures.
- Pydantic/FastAPI/datetime deprecation warnings can be handled later.

## 2026-05-26 Test Checkpoint

- Ran `python -m pytest`
- Result: 22 passed, 123 warnings
- Current status: Phase 1 stabilization tests passed
- Notes: warnings remain but no test failures
## 2026-05-24 Codex Phase 1 Stabilization Summary

### Files Changed
- services/session_service.py
- tests/test_sessions.py

No legacy endpoint files were changed.

### Tests Added Or Updated
Added focused session workflow tests for:
- Official session follow-up without `@通報` keeps `source_type = official`
- Same `sender_id` in a different `group_id` creates a new session
- Same `sender_id` on a different `platform` creates a new direct session
- `need_more_info` reply text uses user-friendly Chinese and does not expose field names like `location` or `reporter.phone`

Existing characterization tests already covered:
- Official complete report returns `waiting_confirmation`
- Citizen incomplete report returns `need_more_info`, not `422`
- Citizen follow-up reuses same session
- Citizen follow-up can reach `WAITING_CONFIRMATION`
- Confirm creates final report
- Different sender cannot confirm another user’s session

### Bugs Fixed
- Fixed source overwrite risk: follow-up messages no longer recalculate and overwrite an existing session’s `source_type` / `source_context`.
- Fixed overly broad session reuse: sessions are no longer reused only by `sender_id`; they now also respect `platform` and group context.
- Fixed user-facing reply leakage: missing field names are no longer shown directly in `reply_message.text`.

### Behavior Changed
- Session source is now decided only when the session is created.
- Follow-up messages preserve the original source identity.
- Open session lookup now uses:
  - `sender_id`
  - `platform`
  - same `group_id` if present
  - `group_id is None` for citizen direct messages
- `need_more_info` replies now say things like:
  - `請提供詳細地址或地點。`
  - `請提供聯絡人姓名。`
  - `請提供聯絡電話。`

### Current Test Status
- `python -m pytest tests\test_sessions.py` -> `10 passed`
- `python -m pytest` -> `22 passed`

There are warnings, but no failures.

### Known Remaining Issues
- Pydantic/FastAPI deprecation warnings remain.
- `datetime.utcnow()` deprecation warnings remain.
- Natural-language parsing is still duplicated across services.
- Session/report state names are still inconsistent.
- JSON is still stored in `Text` fields without centralized parsing helpers.
- Legacy endpoints still bypass the session workflow.

### Recommended Next Steps
- Phase 2: centralize extraction/parsing into one service contract.
- Add tests for real Chinese examples, not only current mojibake fixtures.
- Normalize state naming between sessions, reports, and response status.
- Add session expiry / timeout behavior.
- Later, split ORM models from Pydantic schemas once behavior is stable.