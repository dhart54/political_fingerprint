import json

from app.etl.manual_interpretations import (
    _enrich_packets_from_congress_cache,
    import_manual_interpretations,
    validate_manual_interpretations,
)


def test_validate_manual_interpretations_accepts_neutral_interpreted_record() -> None:
    result = validate_manual_interpretations(
        [
            {
                "roll_call_id": 1,
                "interpretation_status": "interpreted",
                "support_position": "yea",
                "oppose_position": "nay",
                "plain_english_summary": "This vote was on final passage of a bill funding bridge repairs.",
                "yea_meaning": "A Yea vote supported passing the bill.",
                "nay_meaning": "A Nay vote opposed passing the bill.",
                "policy_effect": "Would fund bridge repair grants.",
                "issue_facet": "infrastructure_funding",
                "confidence": "medium",
                "source_basis": ["bill_title", "question"],
            }
        ]
    )

    assert result.errors == []
    assert result.valid_count == 1


def test_validate_manual_interpretations_rejects_persuasive_language() -> None:
    result = validate_manual_interpretations(
        [
            {
                "roll_call_id": 1,
                "interpretation_status": "interpreted",
                "support_position": "yea",
                "oppose_position": "nay",
                "plain_english_summary": "This was a good thing for voters.",
                "yea_meaning": "A Yea vote supported passing the bill.",
                "nay_meaning": "A Nay vote opposed passing the bill.",
                "policy_effect": "Would fund bridge repair grants.",
                "confidence": "medium",
                "source_basis": ["bill_title"],
            }
        ]
    )

    assert any("forbidden language" in error for error in result.errors)


def test_import_manual_interpretations_validates_before_persisting(tmp_path, monkeypatch) -> None:
    input_path = tmp_path / "interpretations.json"
    input_path.write_text(
        json.dumps(
            {
                "interpretations": [
                    {
                        "roll_call_id": 1,
                        "interpretation_status": "interpreted",
                        "support_position": "yea",
                        "oppose_position": "nay",
                        "plain_english_summary": "This was the best vote.",
                        "yea_meaning": "A Yea vote supported passing the bill.",
                        "nay_meaning": "A Nay vote opposed passing the bill.",
                        "policy_effect": "Would fund bridge repair grants.",
                        "confidence": "medium",
                        "source_basis": ["bill_title"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("app.etl.manual_interpretations._persist_manual_interpretations", lambda rows: None)

    result = import_manual_interpretations(input_path=input_path)

    assert result["imported_count"] == 0
    assert result["errors"]


def test_enrich_packets_from_congress_cache_prefers_cached_summary_and_subjects(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.etl.manual_interpretations.load_congress_bill_cache",
        lambda cache_dir: {
            (119, "hr", 120): {
                "summary": "CRS summary explains the bill's operating change.",
                "subjects": ["Health care costs"],
                "latest_action": {"action_date": "2025-02-01", "text": "Passed House."},
                "introduced_date": "2025-01-03",
                "origin_chamber": "House",
                "laws": [],
                "cbo_cost_estimates": [{"title": "CBO estimate", "url": "https://example.com/cbo"}],
                "text_versions": [{"type": "Engrossed in House"}],
                "actions": [{"actionDate": "2025-02-01", "text": "Passed House."}],
                "amendments": [{"number": "1", "purpose": "Test amendment"}],
                "committees": [{"name": "Committee on Testing"}],
                "legislation_url": "https://www.congress.gov/bill/119th-congress/house-bill/120",
            }
        },
    )

    packets = _enrich_packets_from_congress_cache(
        [
            {
                "official_text": {
                    "bill_congress": 119,
                    "bill_type": "hr",
                    "bill_number": 120,
                    "bill_summary": "",
                    "bill_subjects": [],
                }
            }
        ]
    )

    assert packets[0]["official_text"]["bill_summary"] == "CRS summary explains the bill's operating change."
    assert packets[0]["official_text"]["bill_subjects"] == ["Health care costs"]
    assert packets[0]["so_what_context"]["bill_lifecycle"]["latest_action"]["text"] == "Passed House."
    assert packets[0]["so_what_context"]["available_enrichment"]["cbo_cost_estimates"] == 1
    assert packets[0]["so_what_context"]["available_enrichment"]["amendments"] == 1
