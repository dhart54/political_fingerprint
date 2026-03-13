import pytest
from fastapi import HTTPException

from app.api.fingerprint import get_legislator_fingerprint
from app.main import app


def test_app_registers_fingerprint_route() -> None:
    assert "/legislators/{legislator_id}/fingerprint" in {route.path for route in app.routes}


def test_get_fingerprint_endpoint_returns_precomputed_vector() -> None:
    payload = get_legislator_fingerprint("leg_alex_morgan", comparison_party="ALL")

    assert payload["legislator_id"] == "leg_alex_morgan"
    assert payload["comparison_party"] == "ALL"
    assert payload["last_updated"] == "2026-03-12T00:00:00+00:00"
    assert len(payload["fingerprint"]) == 8
    assert next(item for item in payload["fingerprint"] if item["domain"] == "HEALTH_SOCIAL") == {
        "domain": "HEALTH_SOCIAL",
        "vote_count": 0,
        "total_votes": 5,
        "vote_share": 0.0,
        "median_share": 0.0,
    }


def test_get_fingerprint_endpoint_supports_party_overlay_toggle() -> None:
    payload = get_legislator_fingerprint("leg_jordan_lee", comparison_party="R")

    assert payload["comparison_party"] == "R"
    assert next(item for item in payload["fingerprint"] if item["domain"] == "HEALTH_SOCIAL")["median_share"] == 0.2


def test_get_fingerprint_endpoint_returns_404_for_unknown_legislator() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_legislator_fingerprint("unknown")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Legislator not found"
