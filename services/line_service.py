from services.extraction_service import adapt_to_legacy_report_info, extract_report_entities

REPORT_KEYWORDS = {"@通報", "通報"}


def should_create_report(raw_text: str) -> bool:
    """Check if message contains disaster report keywords or extractable entities."""
    entities = extract_report_entities(raw_text)
    incident = entities.get("incident", {})
    return any(
        [
            bool(entities.get("location")),
            bool(incident),
            bool(entities.get("needs")),
            bool(incident.get("severity")),
            any(keyword in raw_text for keyword in REPORT_KEYWORDS),
        ]
    )


def extract_report_info(raw_text: str) -> dict:
    """Extract structured information from message text."""
    return adapt_to_legacy_report_info(raw_text)
