from datetime import date

from app.metrics.drift import (
    build_share_vector,
    compute_drift,
    compute_drift_window_bounds,
)
from app.metrics.fingerprint import build_eligible_vote


def test_compute_drift_window_bounds_uses_exact_365_day_split() -> None:
    bounds = compute_drift_window_bounds(date(2026, 3, 13))

    assert bounds == (
        date(2024, 3, 14),
        date(2026, 3, 13),
        date(2024, 3, 14),
        date(2025, 3, 13),
        date(2025, 3, 14),
        date(2026, 3, 13),
    )


def test_build_share_vector_returns_explicit_zeroes() -> None:
    vector = build_share_vector([])

    assert len(vector) == 8
    assert all(value == 0.0 for value in vector.values())


def test_compute_drift_matches_l1_formula() -> None:
    votes = []

    for vote_date in [date(2024, 5, 1)] * 8:
        votes.append(build_eligible_vote(legislator_id=4, vote_date=vote_date, primary_domain="ECONOMY_TAXES"))
    for vote_date in [date(2024, 7, 1)] * 2:
        votes.append(build_eligible_vote(legislator_id=4, vote_date=vote_date, primary_domain="HEALTH_SOCIAL"))
    for vote_date in [date(2025, 6, 1)] * 2:
        votes.append(build_eligible_vote(legislator_id=4, vote_date=vote_date, primary_domain="ECONOMY_TAXES"))
    for vote_date in [date(2025, 8, 1)] * 8:
        votes.append(build_eligible_vote(legislator_id=4, vote_date=vote_date, primary_domain="IMMIGRATION_BORDER"))

    result = compute_drift(
        legislator_id=4,
        votes=votes,
        as_of=date(2026, 3, 13),
        classification_version="v1",
    )

    assert result.insufficient_data is False
    assert result.total_votes == 20
    assert result.early_total_votes == 10
    assert result.recent_total_votes == 10
    assert result.drift_value == 0.8


def test_compute_drift_marks_insufficient_data_below_threshold() -> None:
    votes = [
        build_eligible_vote(
            legislator_id=5,
            vote_date=date(2025, 9, 1),
            primary_domain="JUSTICE_PUBLIC_SAFETY",
        )
        for _ in range(19)
    ]

    result = compute_drift(
        legislator_id=5,
        votes=votes,
        as_of=date(2026, 3, 13),
        classification_version="v1",
    )

    assert result.insufficient_data is True
    assert result.total_votes == 19
    assert result.drift_value is None
