from services.extraction_service import (
    adapt_to_legacy_annotations,
    adapt_to_legacy_report_info,
    extract_report_entities,
    merge_extraction_results,
)


def test_extract_report_entities_returns_central_contract() -> None:
    result = extract_report_entities(
        "馬太鞍溪橋橋斷裂，受困，需要2台怪手，我叫王小明，電話0912-345-678"
    )

    assert result["location"]["address"] == "馬太鞍溪橋"
    assert result["incident"]["type"] == "bridge_damage"
    assert result["incident"]["description"] == "橋斷裂"
    assert result["incident"]["severity"] == "critical"
    assert result["needs"] == [
        {"item": "怪手", "category": "vehicle", "quantity": 2, "unit": "台"}
    ]
    assert result["reporter"]["name"] == "王小明"
    assert result["reporter"]["phone"] == "0912-345-678"
    assert isinstance(result["confidence_score"], float)
    assert result["warnings"] == []


def test_merge_extraction_results_preserves_follow_up_behavior() -> None:
    existing = extract_report_entities("淹水")
    follow_up = extract_report_entities("地址是花蓮縣光復鄉 XXX 路 12 號，我叫王小明，電話0912-345-678")

    merged = merge_extraction_results(existing, follow_up)

    assert merged["location"]["address"] == "花蓮縣光復鄉 XXX 路 12 號"
    assert merged["incident"]["type"] == "flood"
    assert merged["reporter"]["name"] == "王小明"
    assert merged["reporter"]["phone"] == "0912-345-678"
    assert merged["warnings"] == []


def test_legacy_report_info_adapter_preserves_flat_contract() -> None:
    result = adapt_to_legacy_report_info("馬太鞍溪橋橋斷裂，怪手已到場，缺水且火災風險高。")

    assert result == {
        "incident_type": "bridge_collapse",
        "resource_type": "excavator",
        "quantity": None,
        "risk_level": None,
        "location": "馬太鞍溪橋",
    }


def test_legacy_annotations_adapter_preserves_ingest_contract() -> None:
    result = adapt_to_legacy_annotations("馬太鞍溪橋橋斷裂，需要 2 台怪手")

    assert result == {
        "detected_location": "馬太鞍溪橋",
        "detected_hazards": ["bridge_collapse"],
        "detected_assets": ["excavator"],
        "critical_risk": False,
    }
