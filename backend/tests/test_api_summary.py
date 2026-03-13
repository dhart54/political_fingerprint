import pytest
from fastapi import HTTPException

from app.api.summary import get_legislator_summary
from app.main import app


def test_app_registers_summary_route() -> None:
    assert "/legislators/{legislator_id}/summary" in {route.path for route in app.routes}


def test_get_summary_endpoint_generates_deterministic_fallback_summary() -> None:
    payload = get_legislator_summary("leg_alex_morgan")

    assert payload["legislator_id"] == "leg_alex_morgan"
    assert payload["generation_method"] == "deterministic_fallback"
    assert "eligible votes" in payload["summary_text"]
    assert "INFRASTRUCTURE_TECH_TRANSPORT" in payload["summary_text"]
    assert "fewer than 20 eligible votes" in payload["summary_text"]


def test_get_summary_endpoint_returns_stable_fallback_fields_without_in_memory_cache() -> None:
    first = get_legislator_summary("leg_jordan_lee")
    second = get_legislator_summary("leg_jordan_lee")

    assert first["legislator_id"] == second["legislator_id"]
    assert first["window_end"] == second["window_end"]
    assert first["classification_version"] == second["classification_version"]
    assert first["summary_text"] == second["summary_text"]
    assert first["generation_method"] == second["generation_method"]


def test_get_summary_endpoint_returns_404_for_unknown_legislator() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_legislator_summary("unknown")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Legislator not found"
