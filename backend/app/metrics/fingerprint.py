from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.classification.classifier import ISSUE_DOMAINS


ROLLING_WINDOW_DAYS = 730


@dataclass(frozen=True)
class EligibleVote:
    legislator_id: int
    vote_date: date
    primary_domain: str


@dataclass(frozen=True)
class FingerprintRecord:
    legislator_id: int
    window_start: date
    window_end: date
    classification_version: str
    domain: str
    vote_count: int
    total_votes: int
    vote_share: float


def compute_window_bounds(as_of: date) -> tuple[date, date]:
    return as_of - timedelta(days=ROLLING_WINDOW_DAYS - 1), as_of


def compute_fingerprint(
    *,
    legislator_id: int,
    votes: list[EligibleVote],
    as_of: date,
    classification_version: str,
) -> list[FingerprintRecord]:
    window_start, window_end = compute_window_bounds(as_of)
    filtered_votes = [
        vote
        for vote in votes
        if vote.legislator_id == legislator_id
        and window_start <= vote.vote_date <= window_end
        and vote.primary_domain in ISSUE_DOMAINS
    ]

    total_votes = len(filtered_votes)
    domain_counts = {domain: 0 for domain in ISSUE_DOMAINS}

    for vote in filtered_votes:
        domain_counts[vote.primary_domain] += 1

    return [
        FingerprintRecord(
            legislator_id=legislator_id,
            window_start=window_start,
            window_end=window_end,
            classification_version=classification_version,
            domain=domain,
            vote_count=domain_counts[domain],
            total_votes=total_votes,
            vote_share=calculate_vote_share(
                vote_count=domain_counts[domain],
                total_votes=total_votes,
            ),
        )
        for domain in ISSUE_DOMAINS
    ]


def calculate_vote_share(*, vote_count: int, total_votes: int) -> float:
    if total_votes == 0:
        return 0.0
    return vote_count / total_votes


def build_eligible_vote(*, legislator_id: int, vote_date: date | datetime, primary_domain: str) -> EligibleVote:
    normalized_date = vote_date.date() if isinstance(vote_date, datetime) else vote_date
    return EligibleVote(
        legislator_id=legislator_id,
        vote_date=normalized_date,
        primary_domain=primary_domain,
    )
