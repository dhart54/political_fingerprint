import pytest
from fastapi import HTTPException

from app.api.compare import compare_legislators
from app.main import app


def test_app_registers_legislator_compare_route() -> None:
    assert "/compare/legislators" in {route.path for route in app.routes}


def test_compare_legislators_returns_side_by_side_payloads() -> None:
    payload = compare_legislators(
        left_legislator_id="leg_alex_morgan",
        right_legislator_id="leg_jordan_lee",
        comparison_party="ALL",
    )

    assert payload["comparison_party"] == "ALL"
    assert payload["left"]["legislator"]["name_display"] == "Alex Morgan"
    assert payload["right"]["legislator"]["name_display"] == "Jordan Lee"
    assert payload["left"]["fingerprint"]["legislator_id"] == "leg_alex_morgan"
    assert payload["right"]["drift"]["legislator_id"] == "leg_jordan_lee"
    assert "summary_text" in payload["left"]["summary"]


def test_compare_legislators_supports_overlay_toggle() -> None:
    payload = compare_legislators(
        left_legislator_id="leg_jordan_lee",
        right_legislator_id="leg_taylor_nguyen",
        comparison_party="R",
    )

    assert payload["comparison_party"] == "R"
    assert payload["left"]["fingerprint"]["comparison_party"] == "R"
    assert payload["right"]["fingerprint"]["comparison_party"] == "R"


def test_compare_legislators_returns_404_for_unknown_left_legislator() -> None:
    with pytest.raises(HTTPException) as exc_info:
        compare_legislators(
            left_legislator_id="unknown",
            right_legislator_id="leg_jordan_lee",
            comparison_party="ALL",
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Left legislator not found"


def test_compare_legislators_returns_404_for_unknown_right_legislator() -> None:
    with pytest.raises(HTTPException) as exc_info:
        compare_legislators(
            left_legislator_id="leg_alex_morgan",
            right_legislator_id="unknown",
            comparison_party="ALL",
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Right legislator not found"
