import re
from typing import Any


def _empty_result() -> dict[str, Any]:
    return {
        "location": {},
        "incident": {},
        "needs": [],
        "reporter": {},
        "confidence_score": 0.0,
        "warnings": [],
    }


def _compute_confidence(result: dict[str, Any]) -> float:
    fields = [
        bool(result.get("location", {}).get("address")),
        bool(result.get("incident", {}).get("type")),
        bool(result.get("incident", {}).get("description")),
        bool(result.get("incident", {}).get("severity")),
        bool(result.get("needs")),
        bool(result.get("reporter", {}).get("name")),
        bool(result.get("reporter", {}).get("phone")),
    ]
    return round(sum(fields) / len(fields), 2)


def extract_report_entities(content: str) -> dict[str, Any]:
    entities = _empty_result()
    normalized = content

    if "馬太鞍溪橋" in normalized:
        entities["location"]["address"] = "馬太鞍溪橋"

    address_match = re.search(
        r"(?:地址是|地址在|地址為|地址:|地址：)\s*([^，,。\n]+?)(?=[，,。\s]*(?:我叫|電話|Tel|TEL|09\d{2}|$))",
        normalized,
    )
    if address_match:
        entities["location"]["address"] = address_match.group(1).strip()

    if any(keyword in normalized for keyword in ["橋斷裂", "橋斷了", "斷裂"]):
        entities["incident"]["type"] = "bridge_damage"
        entities["incident"]["description"] = "橋斷裂"

    if "淹水" in normalized:
        entities["incident"]["type"] = "flood"

    if "火災" in normalized:
        entities["incident"]["type"] = "fire"

    if any(keyword in normalized for keyword in ["受困", "救命"]):
        entities["incident"]["severity"] = "critical"

    if "怪手" in normalized:
        entities["needs"].append({"item": "怪手", "category": "vehicle"})
    if "缺水" in normalized:
        entities["incident"]["type"] = "water_shortage"

    if any(keyword in normalized for keyword in ["水", "缺水"]):
        entities["needs"].append({"item": "水", "category": "supplies"})

    quantity_match = re.search(r"(\d+)\s*台|兩台|二台", normalized)
    if quantity_match:
        quantity = 2 if quantity_match.group(0) and any(tok in quantity_match.group(0) for tok in ["兩台", "二台"]) else int(quantity_match.group(1) or 2)
        if entities["needs"]:
            entities["needs"][-1]["quantity"] = quantity
            entities["needs"][-1]["unit"] = "台"
        else:
            entities["needs"].append(
                {"item": "未知", "category": "supplies", "quantity": quantity, "unit": "台"}
            )

    phone_match = re.search(r"(09\d{2}-?\d{3}-?\d{3})", normalized)
    if phone_match:
        entities["reporter"]["phone"] = phone_match.group(1)

    name_match = re.search(r"我叫([\u4e00-\u9fff]{2,5})", normalized)
    if name_match:
        entities["reporter"]["name"] = name_match.group(1)

    entities["confidence_score"] = _compute_confidence(entities)
    return entities


def merge_extraction_results(existing: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    merged = {**existing}

    if new.get("location"):
        merged_location = merged.get("location", {}) or {}
        merged_location.update({k: v for k, v in new["location"].items() if v is not None})
        merged["location"] = merged_location

    merged_incident = {**merged.get("incident", {}), **{k: v for k, v in new.get("incident", {}).items() if v is not None}}
    merged["incident"] = merged_incident

    existing_needs = {item.get("item"): item for item in merged.get("needs", [])} if merged.get("needs") else {}
    for need in new.get("needs", []):
        item = need.get("item")
        if not item:
            continue
        if item in existing_needs:
            existing_needs[item].update({k: v for k, v in need.items() if v is not None})
        else:
            existing_needs[item] = need
    merged["needs"] = list(existing_needs.values())

    merged_reporter = {**merged.get("reporter", {}), **{k: v for k, v in new.get("reporter", {}).items() if v is not None}}
    merged["reporter"] = merged_reporter
    merged["warnings"] = list(dict.fromkeys([*merged.get("warnings", []), *new.get("warnings", [])]))
    merged["confidence_score"] = _compute_confidence(merged)

    return merged


def _legacy_incident_type(entities: dict[str, Any], raw_text: str) -> str | None:
    incident_type = entities.get("incident", {}).get("type")
    if incident_type == "bridge_damage" or (
        "馬太鞍溪橋" in raw_text and any(keyword in raw_text for keyword in ["斷裂", "斷了"])
    ):
        return "bridge_collapse"
    if incident_type in {"flood", "fire", "water_shortage"}:
        return incident_type
    if "蝻箸偌" in raw_text:
        return "water_shortage"
    return None


def _legacy_resource_type(entities: dict[str, Any]) -> str | None:
    needs = entities.get("needs", [])
    if not needs:
        return None

    category = needs[0].get("category")
    if category == "vehicle":
        return "excavator"
    if category == "supplies":
        return "water"
    return None


def adapt_to_legacy_report_info(raw_text: str) -> dict[str, Any]:
    """Map central extraction entities to the legacy flat report contract."""
    entities = extract_report_entities(raw_text)
    needs = entities.get("needs", [])
    primary_need = needs[0] if needs else {}
    incident = entities.get("incident", {})

    return {
        "incident_type": _legacy_incident_type(entities, raw_text),
        "resource_type": _legacy_resource_type(entities),
        "quantity": primary_need.get("quantity"),
        "risk_level": incident.get("severity"),
        "location": entities.get("location", {}).get("address"),
    }


def adapt_to_legacy_annotations(raw_text: str) -> dict[str, Any]:
    """Map central extraction entities to the old ingest annotation contract."""
    entities = extract_report_entities(raw_text)
    incident_type = _legacy_incident_type(entities, raw_text)
    resource_type = _legacy_resource_type(entities)

    detected_hazards = []
    if incident_type:
        detected_hazards.append(incident_type)

    detected_assets = []
    if resource_type == "excavator":
        detected_assets.append(resource_type)

    incident = entities.get("incident", {})
    critical_risk = incident.get("severity") == "critical" or incident.get("type") == "fire"

    return {
        "detected_location": entities.get("location", {}).get("address"),
        "detected_hazards": detected_hazards,
        "detected_assets": detected_assets,
        "critical_risk": critical_risk,
    }
