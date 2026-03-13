import pytest
from fastapi import HTTPException

from app.api.drift import get_legislator_drift
from app.main import app


def test_app_registers_drift_route() -> None:
    assert "/legislators/{legislator_id}/drift" in {route.path for route in app.routes}


def test_get_drift_endpoint_returns_precomputed_result() -> None:
    payload = get_legislator_drift("leg_alex_morgan")

    assert payload["legislator_id"] == "leg_alex_morgan"
    assert payload["classification_version"] == "v1"
    assert payload["total_votes"] == 5
    assert payload["early_total_votes"] == 3
    assert payload["recent_total_votes"] == 2
    assert payload["insufficient_data"] is True
    assert payload["drift_value"] is None


def test_get_drift_endpoint_returns_404_for_unknown_legislator() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_legislator_drift("unknown")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Legislator not found"
