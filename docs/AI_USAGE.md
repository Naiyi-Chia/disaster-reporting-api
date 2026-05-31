# AI Usage

## Current MVP Extraction Architecture

The current MVP does not call an LLM at runtime. Extraction is implemented as a deterministic rule-based parser in `services/extraction_service.py`.

The parser returns a structured entity object:

```json
{
  "location": {},
  "incident": {},
  "needs": [],
  "reporter": {},
  "confidence_score": 0.0,
  "warnings": []
}
```

The session service stores this object in `sessions.extracted_entities`, merges follow-up messages into it, and computes missing required fields before asking for confirmation.

## Rule-Based Parser Explanation

The parser uses:

- Keyword checks for incident and need categories.
- Regex patterns for address-like text, phone numbers, names, and quantities.
- A simple confidence score based on the fraction of expected fields found.
- Merge logic that preserves previously extracted fields and fills in new fields from follow-up messages.

This approach is transparent and predictable, which is useful for an MVP and competition demo. It is also limited: wording variations outside the known patterns may not extract correctly.

## Future LLM / AI Agent Extension Point

The cleanest future extension point is `extract_report_entities(content)` in `services/extraction_service.py`.

A future LLM or AI-agent extraction layer could:

- Parse natural disaster reports into the same entity schema.
- Return field-level confidence and rationale.
- Normalize location, incident taxonomy, resource names, and quantities.
- Ask targeted follow-up questions when confidence is low.
- Route high-risk reports for human review.

The downstream session and report services should keep the same contract:

```json
{
  "location": {
    "address": "..."
  },
  "incident": {
    "type": "...",
    "description": "...",
    "severity": "..."
  },
  "needs": [
    {
      "item": "...",
      "category": "...",
      "quantity": 1,
      "unit": "..."
    }
  ],
  "reporter": {
    "name": "...",
    "phone": "..."
  },
  "confidence_score": 0.86,
  "warnings": []
}
```

## Data Source

Runtime data sources in the MVP:

- HTTP request payloads sent to `POST /webhook/report`
- Follow-up messages from the same sender/session context
- SQLite tables created by SQLAlchemy:
  - `sessions`
  - `reports`

The repository also includes demo/test strings and test fixtures that exercise official and citizen workflows.

## Risks and Limitations

- Rule-based extraction can miss valid reports with unfamiliar wording.
- Encoded demo text may not represent all real LINE message formats.
- Confidence scoring is heuristic and should not be treated as a safety guarantee.
- No production authentication, rate limiting, or LINE signature verification is included.
- No geocoding, GIS validation, duplicate detection, or severity escalation exists yet.
- SQLite is suitable for MVP demonstration but not disaster-scale production operations.
- A future LLM could hallucinate fields unless constrained by schema validation and human review.

## Human-in-the-Loop Policy

The MVP requires human confirmation before final report export.

Policy:

- Missing fields trigger a follow-up question instead of silent export.
- Complete sessions return confirmation actions: `confirm`, `correct`, `cancel`.
- `POST /sessions/{session_id}/confirm` must be called by the same `sender_id` that owns the session.
- Confirmation creates the final persisted report.
- Corrections should be added before confirmation when the extracted fields are wrong or incomplete.

This keeps the system assistive rather than fully autonomous.

## Generative AI Tools Used During Development

Generative AI assistance was used during development/documentation packaging to:

- Draft documentation structure for competition submission.
- Summarize current API behavior from local source files.
- Prepare example client snippets and cURL examples.
- Identify documentation gaps around AI usage and human-in-the-loop controls.

No runtime generative AI model is currently invoked by the service.
