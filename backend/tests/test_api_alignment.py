import pytest
from fastapi import HTTPException

from app.api.alignment import AlignmentRequest, get_legislator_alignment
from app.main import app


def test_app_registers_alignment_route() -> None:
    assert "/legislators/{legislator_id}/alignment" in {route.path for route in app.routes}


def test_alignment_returns_evidence_based_label_for_selected_issue() -> None:
    payload = get_legislator_alignment(
        "leg_alex_morgan",
        AlignmentRequest(preferences={"EDUCATION_WORKFORCE": "support_more_action"}),
    )

    assert payload["legislator_id"] == "leg_alex_morgan"
    assert payload["preferences"] == {"EDUCATION_WORKFORCE": "support_more_action"}
    assert payload["alignment"][0]["domain"] == "EDUCATION_WORKFORCE"
    assert payload["alignment"][0]["label"] == "aligned"
    assert payload["alignment"][0]["aligned_count"] == 1
    assert payload["alignment"][0]["not_aligned_count"] == 0
    assert payload["alignment"][0]["interpreted_count"] == 1


def test_alignment_can_return_not_aligned_for_opposite_preference() -> None:
    payload = get_legislator_alignment(
        "leg_alex_morgan",
        AlignmentRequest(preferences={"EDUCATION_WORKFORCE": "oppose_more_action"}),
    )

    assert payload["alignment"][0]["label"] == "not_aligned"
    assert payload["alignment"][0]["not_aligned_count"] == 1


def test_alignment_ignores_unknown_domains() -> None:
    payload = get_legislator_alignment(
        "leg_alex_morgan",
        AlignmentRequest(preferences={"NOT_A_DOMAIN": "support_more_action"}),
    )

    assert payload["preferences"] == {}
    assert payload["alignment"] == []


def test_alignment_returns_404_for_unknown_legislator() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_legislator_alignment(
            "unknown",
            AlignmentRequest(preferences={"EDUCATION_WORKFORCE": "support_more_action"}),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Legislator not found"
