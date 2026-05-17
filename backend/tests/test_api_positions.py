import pytest
from fastapi import HTTPException

from app.api.lookup import lookup_zip_races
from app.api import precomputed
from app.api.positions import get_legislator_position_evidence, get_legislator_positions
from app.main import app


def test_app_registers_positions_route() -> None:
    assert "/legislators/{legislator_id}/positions" in {route.path for route in app.routes}
    assert "/legislators/{legislator_id}/positions/{domain}/evidence" in {route.path for route in app.routes}


def test_app_registers_zip_races_route() -> None:
    assert "/lookup/zip/{zip_code}/races" in {route.path for route in app.routes}


def test_get_positions_endpoint_returns_domain_position_profile() -> None:
    payload = get_legislator_positions("leg_alex_morgan")

    assert payload["legislator_id"] == "leg_alex_morgan"
    assert payload["classification_version"] == "v1"
    assert len(payload["positions"]) == 8
    assert next(item for item in payload["positions"] if item["domain"] == "EDUCATION_WORKFORCE") == {
        "domain": "EDUCATION_WORKFORCE",
        "yea_count": 1,
        "nay_count": 0,
        "other_count": 1,
        "total_votes": 2,
        "recorded_votes": 1,
        "yea_share": 1.0,
        "nay_share": 0.0,
        "interpreted_support_count": 1,
        "interpreted_oppose_count": 0,
        "interpreted_other_count": 1,
        "interpreted_total": 2,
    }


def test_get_positions_endpoint_returns_404_for_unknown_legislator() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_legislator_positions("unknown")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Legislator not found"


def test_get_position_evidence_endpoint_returns_underlying_votes() -> None:
    payload = get_legislator_position_evidence("leg_alex_morgan", "EDUCATION_WORKFORCE")

    assert payload["legislator_id"] == "leg_alex_morgan"
    assert payload["domain"] == "EDUCATION_WORKFORCE"
    assert payload["classification_version"] == "v1"
    assert len(payload["evidence"]) == 2
    assert payload["evidence"][0]["position"] == "yea"
    assert payload["evidence"][0]["bill_title"] == "A bill to support teacher workforce apprenticeships"
    assert payload["evidence"][0]["classification_reason"] == "policy_vote"
    assert payload["evidence"][0]["source_url"] == "https://example.com/rollcalls/house/2"
    assert payload["evidence"][0]["interpretation_status"] in {
        "interpreted",
        "ambiguous",
        "insufficient_evidence",
    }
    assert "plain_english_summary" in payload["evidence"][0]


def test_get_position_evidence_endpoint_rejects_unknown_domain() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_legislator_position_evidence("leg_alex_morgan", "NOT_A_DOMAIN")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Evidence not found"


def test_lookup_zip_races_returns_federal_races() -> None:
    payload = lookup_zip_races("27701")

    assert payload["zip"] == "27701"
    assert payload["data_source"] in {"fixtures", "database"}
    assert payload["races"]
    house_race = next(race for race in payload["races"] if race["chamber"] == "house")
    assert house_race["office_name"] == "U.S. House"
    assert house_race["status"] == "upcoming"
    assert house_race["candidates"]
    assert house_race["candidates"][0]["candidate_status"] in {
        "current_official_context",
        "declared_candidate",
        "filed_candidate",
        "unknown",
    }
    assert house_race["candidates"][0]["evidence_tier"] in {
        "recorded_governing_behavior",
        "institutional_record",
        "sourced_stated_position",
        "insufficient_evidence",
    }


def test_candidate_voting_summary_uses_precomputed_rows(monkeypatch) -> None:
    monkeypatch.setattr(
        precomputed,
        "_get_db_fingerprint_rows",
        lambda *, legislator_db_id: [
            {
                "domain": "ECONOMY_TAXES",
                "vote_count": 7,
                "total_votes": 10,
                "vote_share": 0.7,
                "window_start": "2025-01-01",
                "window_end": "2026-12-31",
                "classification_version": "v1",
                "created_at": "2026-12-31",
            },
            {
                "domain": "HEALTH_SOCIAL",
                "vote_count": 3,
                "total_votes": 10,
                "vote_share": 0.3,
                "window_start": "2025-01-01",
                "window_end": "2026-12-31",
                "classification_version": "v1",
                "created_at": "2026-12-31",
            },
            {
                "domain": "EDUCATION_WORKFORCE",
                "vote_count": 0,
                "total_votes": 10,
                "vote_share": 0.0,
                "window_start": "2025-01-01",
                "window_end": "2026-12-31",
                "classification_version": "v1",
                "created_at": "2026-12-31",
            },
        ],
    )
    monkeypatch.setattr(
        precomputed,
        "_get_db_position_rows",
        lambda *, legislator_db_id, window_start, window_end, classification_version: [
            {
                "domain": "ECONOMY_TAXES",
                "yea_count": 4,
                "nay_count": 3,
                "other_count": 0,
                "interpreted_support_count": 2,
                "interpreted_oppose_count": 1,
                "interpreted_other_count": 0,
            },
            {
                "domain": "HEALTH_SOCIAL",
                "yea_count": 2,
                "nay_count": 1,
                "other_count": 0,
                "interpreted_support_count": 1,
                "interpreted_oppose_count": 0,
                "interpreted_other_count": 0,
            },
        ],
    )

    summary = precomputed._build_candidate_voting_summary(legislator_db_id=123)

    assert summary == {
        "window_start": "2025-01-01",
        "window_end": "2026-12-31",
        "classification_version": "v1",
        "eligible_vote_count": 10,
        "interpreted_vote_count": 4,
        "top_domains": [
            {"domain": "ECONOMY_TAXES", "vote_count": 7, "vote_share": 0.7},
            {"domain": "HEALTH_SOCIAL", "vote_count": 3, "vote_share": 0.3},
        ],
    }


def test_candidate_serialization_leaves_unlinked_candidates_without_voting_summary() -> None:
    candidate = precomputed._serialize_race_candidate(
        {
            "candidate_id": 1,
            "candidate_name": "Casey Candidate",
            "party": "D",
            "incumbent": False,
            "candidate_status": "declared_candidate",
            "evidence_tier": "insufficient_evidence",
            "evidence_note": "No voting record linked.",
            "candidate_source_url": "https://example.com",
            "candidate_source_type": "fixture",
            "candidate_source_retrieved_at": None,
            "external_candidate_id": "H6NC00000",
            "legislator_db_id": None,
        }
    )

    assert candidate["linked_legislator"] is None
    assert candidate["voting_summary"] is None
