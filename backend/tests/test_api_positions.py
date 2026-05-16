import pytest
from fastapi import HTTPException

from app.api.positions import get_legislator_position_evidence, get_legislator_positions
from app.main import app


def test_app_registers_positions_route() -> None:
    assert "/legislators/{legislator_id}/positions" in {route.path for route in app.routes}
    assert "/legislators/{legislator_id}/positions/{domain}/evidence" in {route.path for route in app.routes}


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


def test_get_position_evidence_endpoint_rejects_unknown_domain() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_legislator_position_evidence("leg_alex_morgan", "NOT_A_DOMAIN")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Evidence not found"
