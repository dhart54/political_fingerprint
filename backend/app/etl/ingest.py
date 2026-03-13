import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"


@dataclass(frozen=True)
class FixtureBundle:
    legislators: list[dict[str, Any]]
    bills: list[dict[str, Any]]
    roll_calls: list[dict[str, Any]]
    votes_cast: list[dict[str, Any]]
    vote_subject_tags: dict[str, list[str]]
    zip_district_map: list[dict[str, Any]]


@dataclass(frozen=True)
class IngestResult:
    source: str
    records_loaded: int
    fixtures: FixtureBundle


def load_fixture_bundle(fixtures_dir: Path = FIXTURES_DIR) -> FixtureBundle:
    return FixtureBundle(
        legislators=_load_json(fixtures_dir / "legislators.json"),
        bills=_load_json(fixtures_dir / "bills.json"),
        roll_calls=_load_json(fixtures_dir / "roll_calls.json"),
        votes_cast=_load_json(fixtures_dir / "votes_cast.json"),
        vote_subject_tags=_load_json(fixtures_dir / "vote_subject_tags.json"),
        zip_district_map=_load_json(fixtures_dir / "zip_district_map.json"),
    )


def run_ingest(*, source: str = "fixtures") -> IngestResult:
    fixtures = load_fixture_bundle()
    records_loaded = (
        len(fixtures.legislators)
        + len(fixtures.bills)
        + len(fixtures.roll_calls)
        + len(fixtures.votes_cast)
        + len(fixtures.zip_district_map)
    )
    return IngestResult(
        source=source,
        records_loaded=records_loaded,
        fixtures=fixtures,
    )


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text())
