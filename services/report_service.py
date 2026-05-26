from datetime import datetime

from models.report import IncomingMessage, RoutedReport
from services.extraction_service import adapt_to_legacy_annotations


ROUTE_MAP = {
    "official_group": "A_official",
    "citizen_line": "B_citizen",
    "web_form": "B_citizen",
    "voice": "B_citizen",
}


def _extract_annotations(raw_text: str) -> dict:
    return adapt_to_legacy_annotations(raw_text)


def ingest_report(message: IncomingMessage) -> RoutedReport:
    route = ROUTE_MAP.get(message.source_type, "unassigned")
    annotations = _extract_annotations(message.raw_text)

    return RoutedReport(
        message_id=message.message_id,
        source_type=message.source_type,
        route=route,
        detected_location=annotations["detected_location"],
        detected_hazards=annotations["detected_hazards"],
        detected_assets=annotations["detected_assets"],
        critical_risk=annotations["critical_risk"],
        raw_text=message.raw_text,
        received=datetime.utcnow(),
    )
