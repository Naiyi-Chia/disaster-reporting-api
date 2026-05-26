import re
from typing import Optional, Tuple

REPORT_KEYWORDS = {"@通報", "通報", "救命", "受困", "缺水", "火災", "淹水"}


def should_create_report(raw_text: str) -> bool:
    """Check if message contains disaster report keywords."""
    return any(keyword in raw_text for keyword in REPORT_KEYWORDS)


def extract_report_info(raw_text: str) -> dict:
    """Extract structured information from message text."""
    incident_type = None
    resource_type = None
    quantity = None
    risk_level = None
    location = None

    if "馬太鞍溪橋" in raw_text:
        location = "馬太鞍溪橋"

    if (
        "橋斷裂" in raw_text
        or ("斷裂" in raw_text and "橋" in raw_text)
        or "橋斷了" in raw_text
        or ("斷了" in raw_text and "橋" in raw_text)
    ):
        incident_type = "bridge_collapse"
    elif "缺水" in raw_text:
        incident_type = "water_shortage"
    elif "淹水" in raw_text:
        incident_type = "flood"
    elif "火災" in raw_text:
        incident_type = "fire"

    if "怪手" in raw_text:
        resource_type = "excavator"
    elif "水" in raw_text:
        resource_type = "water"

    if "受困" in raw_text or "救命" in raw_text:
        risk_level = "critical"

    quantity_match = re.search(r"(\d+)\s*台", raw_text)
    if quantity_match:
        quantity = int(quantity_match.group(1))
    elif "兩台" in raw_text or "二台" in raw_text:
        quantity = 2
    elif "三台" in raw_text:
        quantity = 3
    elif "四台" in raw_text:
        quantity = 4

    return {
        "incident_type": incident_type,
        "resource_type": resource_type,
        "quantity": quantity,
        "risk_level": risk_level,
        "location": location,
    }
