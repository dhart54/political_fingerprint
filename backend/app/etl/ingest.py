import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.etl.congress_adapter import load_congress_sample_bundle
from app.etl.house_clerk_adapter import load_house_clerk_sample_bundle
from app.etl.types import FixtureBundle


FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"


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
    if source == "fixtures":
        fixtures = load_fixture_bundle()
    elif source == "congress_sample":
        fixtures = load_congress_sample_bundle()
    elif source == "house_clerk_sample":
        fixtures = load_house_clerk_sample_bundle()
    else:
        raise ValueError(f"Unsupported ingest source: {source}")

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
