import json

from app.etl.manual_interpretations import (
    _enrich_packets_from_congress_cache,
    _serialize_packet,
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


def test_serialize_packet_includes_vote_context_and_so_what_template() -> None:
    packet = _serialize_packet(
        {
            "roll_call_id": 50,
            "chamber": "house",
            "congress": 119,
            "rollcall_number": 50,
            "vote_date": "2025-02-25",
            "primary_domain": "ECONOMY_TAXES",
            "classification_reason": "policy_vote",
            "classification_version": "v1",
            "bill_title": "Budget resolution",
            "bill_congress": 119,
            "bill_type": "hconres",
            "bill_number": 14,
            "bill_summary": "Official summary.",
            "bill_subjects": ["Budget process"],
            "question": "On Agreeing to the Resolution",
            "description": "Establishing the congressional budget.",
            "source_url": "https://example.com/roll/50",
            "member_vote": "nay",
            "member_party": "D",
            "vote_type": "final_passage",
            "final_result": "passed",
            "vote_margin": 2,
            "winning_position": "yea",
            "party_vote_totals": {"D": {"yea": 0, "nay": 2}},
            "member_party_majority_position": "nay",
            "member_voted_with_party_majority": True,
            "member_voted_with_winning_side": False,
            "bipartisan_majority": False,
            "sponsor_party": None,
            "context_source_list": [{"source_type": "official_roll_call", "url": "https://example.com/roll/50"}],
            "context_version": "vote_context_v1",
            "interpretation_status": "interpreted",
            "interpretation_reason": "Manual review.",
            "plain_english_summary": "Plain read.",
            "yea_meaning": "Yea supported the resolution.",
            "nay_meaning": "Nay opposed the resolution.",
            "policy_effect": "Would set budget levels.",
            "issue_facet": "budget_process",
            "confidence": "medium",
            "uncertainty_note": None,
        }
    )

    assert packet["vote_context"]["member_voted_with_party_majority"] is True
    assert packet["vote_context"]["member_voted_with_winning_side"] is False
    assert packet["draft_template"]["what_happened"] == ""
    assert packet["draft_template"]["why_it_mattered"] == ""
    assert packet["draft_template"]["member_vote_context"] == ""
    assert packet["draft_template"]["what_not_to_infer"] == ""
    assert "rule | motion | concurrence | procedural" in packet["draft_template"]["vote_type"]
