import pytest
from fastapi import HTTPException

from app.api.summary import get_legislator_summary
from app.main import app
from app.summaries.cache import SUMMARY_CACHE


@pytest.fixture(autouse=True)
def clear_summary_cache() -> None:
    SUMMARY_CACHE.clear()


def test_app_registers_summary_route() -> None:
    assert "/legislators/{legislator_id}/summary" in {route.path for route in app.routes}


def test_get_summary_endpoint_generates_deterministic_fallback_summary() -> None:
    payload = get_legislator_summary("leg_alex_morgan")

    assert payload["legislator_id"] == "leg_alex_morgan"
    assert payload["generation_method"] == "deterministic_fallback"
    assert "eligible votes" in payload["summary_text"]
    assert "INFRASTRUCTURE_TECH_TRANSPORT" in payload["summary_text"]
    assert "fewer than 20 eligible votes" in payload["summary_text"]


def test_get_summary_endpoint_reuses_cached_summary_without_regeneration() -> None:
    first = get_legislator_summary("leg_jordan_lee")
    second = get_legislator_summary("leg_jordan_lee")

    assert first == second
    assert first["created_at"] == second["created_at"]


def test_get_summary_endpoint_returns_404_for_unknown_legislator() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_legislator_summary("unknown")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Legislator not found"
