from datetime import datetime
from typing import List

from models.report import IncomingMessage, RoutedReport


ROUTE_MAP = {
    "official_group": "A_official",
    "citizen_line": "B_citizen",
    "web_form": "B_citizen",
    "voice": "B_citizen",
}


def _extract_annotations(raw_text: str) -> dict:
    normalized = raw_text
    detected_location = "馬太鞍溪橋" if "馬太鞍溪橋" in normalized else None

    detected_hazards: List[str] = []
    if "橋斷裂" in normalized or "斷裂" in normalized:
        detected_hazards.append("bridge_collapse")
    if "缺水" in normalized:
        detected_hazards.append("water_shortage")

    detected_assets: List[str] = []
    if "怪手" in normalized:
        detected_assets.append("excavator")

    critical_risk = any(keyword in normalized for keyword in ["受困", "被困", "火災"])

    return {
        "detected_location": detected_location,
        "detected_hazards": detected_hazards,
        "detected_assets": detected_assets,
        "critical_risk": critical_risk,
    }


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
