from dataclasses import dataclass
from datetime import date, timedelta

from app.classification.classifier import ISSUE_DOMAINS
from app.metrics.fingerprint import EligibleVote


DRIFT_WINDOW_DAYS = 730
HALF_WINDOW_DAYS = 365
INSUFFICIENT_DATA_THRESHOLD = 20


@dataclass(frozen=True)
class DriftResult:
    legislator_id: int
    window_start: date
    window_end: date
    early_window_start: date
    early_window_end: date
    recent_window_start: date
    recent_window_end: date
    classification_version: str
    total_votes: int
    early_total_votes: int
    recent_total_votes: int
    insufficient_data: bool
    drift_value: float | None


def compute_drift_window_bounds(as_of: date) -> tuple[date, date, date, date, date, date]:
    window_end = as_of
    window_start = as_of - timedelta(days=DRIFT_WINDOW_DAYS - 1)
    early_window_start = window_start
    early_window_end = early_window_start + timedelta(days=HALF_WINDOW_DAYS - 1)
    recent_window_start = early_window_end + timedelta(days=1)
    recent_window_end = window_end
    return (
        window_start,
        window_end,
        early_window_start,
        early_window_end,
        recent_window_start,
        recent_window_end,
    )


def compute_drift(
    *,
    legislator_id: int,
    votes: list[EligibleVote],
    as_of: date,
    classification_version: str,
) -> DriftResult:
    (
        window_start,
        window_end,
        early_window_start,
        early_window_end,
        recent_window_start,
        recent_window_end,
    ) = compute_drift_window_bounds(as_of)

    relevant_votes = [
        vote
        for vote in votes
        if vote.legislator_id == legislator_id
        and window_start <= vote.vote_date <= window_end
        and vote.primary_domain in ISSUE_DOMAINS
    ]

    early_votes = [vote for vote in relevant_votes if early_window_start <= vote.vote_date <= early_window_end]
    recent_votes = [vote for vote in relevant_votes if recent_window_start <= vote.vote_date <= recent_window_end]

    total_votes = len(relevant_votes)
    early_total_votes = len(early_votes)
    recent_total_votes = len(recent_votes)

    if total_votes < INSUFFICIENT_DATA_THRESHOLD:
        return DriftResult(
            legislator_id=legislator_id,
            window_start=window_start,
            window_end=window_end,
            early_window_start=early_window_start,
            early_window_end=early_window_end,
            recent_window_start=recent_window_start,
            recent_window_end=recent_window_end,
            classification_version=classification_version,
            total_votes=total_votes,
            early_total_votes=early_total_votes,
            recent_total_votes=recent_total_votes,
            insufficient_data=True,
            drift_value=None,
        )

    early_vector = build_share_vector(early_votes)
    recent_vector = build_share_vector(recent_votes)
    drift_value = 0.5 * sum(
        abs(early_vector[domain] - recent_vector[domain])
        for domain in ISSUE_DOMAINS
    )

    return DriftResult(
        legislator_id=legislator_id,
        window_start=window_start,
        window_end=window_end,
        early_window_start=early_window_start,
        early_window_end=early_window_end,
        recent_window_start=recent_window_start,
        recent_window_end=recent_window_end,
        classification_version=classification_version,
        total_votes=total_votes,
        early_total_votes=early_total_votes,
        recent_total_votes=recent_total_votes,
        insufficient_data=False,
        drift_value=drift_value,
    )


def build_share_vector(votes: list[EligibleVote]) -> dict[str, float]:
    total_votes = len(votes)
    counts = {domain: 0 for domain in ISSUE_DOMAINS}

    for vote in votes:
        counts[vote.primary_domain] += 1

    if total_votes == 0:
        return {domain: 0.0 for domain in ISSUE_DOMAINS}

    return {domain: counts[domain] / total_votes for domain in ISSUE_DOMAINS}
