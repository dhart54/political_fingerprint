from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FixtureBundle:
    legislators: list[dict[str, Any]]
    bills: list[dict[str, Any]]
    roll_calls: list[dict[str, Any]]
    votes_cast: list[dict[str, Any]]
    vote_subject_tags: dict[str, list[str]]
    zip_district_map: list[dict[str, Any]]
