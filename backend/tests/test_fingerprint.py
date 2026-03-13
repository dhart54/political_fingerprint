from datetime import date, datetime

from app.metrics.fingerprint import (
    FingerprintRecord,
    build_eligible_vote,
    calculate_vote_share,
    compute_fingerprint,
    compute_window_bounds,
)


def test_compute_window_bounds_uses_exact_730_day_window() -> None:
    window_start, window_end = compute_window_bounds(date(2026, 3, 13))

    assert window_start == date(2024, 3, 14)
    assert window_end == date(2026, 3, 13)


def test_compute_fingerprint_returns_explicit_zero_rows_for_all_domains() -> None:
    records = compute_fingerprint(
        legislator_id=1,
        votes=[],
        as_of=date(2026, 3, 13),
        classification_version="v1",
    )

    assert len(records) == 8
    assert all(
        record == FingerprintRecord(
            legislator_id=1,
            window_start=date(2024, 3, 14),
            window_end=date(2026, 3, 13),
            classification_version="v1",
            domain=record.domain,
            vote_count=0,
            total_votes=0,
            vote_share=0.0,
        )
        for record in records
    )


def test_compute_fingerprint_calculates_vote_shares_from_total_eligible_votes() -> None:
    votes = [
        build_eligible_vote(
            legislator_id=7,
            vote_date=date(2025, 6, 1),
            primary_domain="ECONOMY_TAXES",
        ),
        build_eligible_vote(
            legislator_id=7,
            vote_date=datetime(2025, 8, 1, 12, 30),
            primary_domain="ECONOMY_TAXES",
        ),
        build_eligible_vote(
            legislator_id=7,
            vote_date=date(2025, 9, 1),
            primary_domain="HEALTH_SOCIAL",
        ),
        build_eligible_vote(
            legislator_id=99,
            vote_date=date(2025, 9, 1),
            primary_domain="HEALTH_SOCIAL",
        ),
        build_eligible_vote(
            legislator_id=7,
            vote_date=date(2024, 3, 13),
            primary_domain="JUSTICE_PUBLIC_SAFETY",
        ),
    ]

    records = compute_fingerprint(
        legislator_id=7,
        votes=votes,
        as_of=date(2026, 3, 13),
        classification_version="v2",
    )

    records_by_domain = {record.domain: record for record in records}

    assert records_by_domain["ECONOMY_TAXES"].vote_count == 2
    assert records_by_domain["ECONOMY_TAXES"].total_votes == 3
    assert records_by_domain["ECONOMY_TAXES"].vote_share == 2 / 3
    assert records_by_domain["HEALTH_SOCIAL"].vote_count == 1
    assert records_by_domain["HEALTH_SOCIAL"].vote_share == 1 / 3
    assert records_by_domain["JUSTICE_PUBLIC_SAFETY"].vote_count == 0
    assert records_by_domain["JUSTICE_PUBLIC_SAFETY"].vote_share == 0.0


def test_calculate_vote_share_returns_zero_when_no_votes_exist() -> None:
    assert calculate_vote_share(vote_count=0, total_votes=0) == 0.0
