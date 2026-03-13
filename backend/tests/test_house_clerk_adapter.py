from datetime import date
import json
from pathlib import Path

from app.etl.compute import run_etl
from app.etl.house_clerk_adapter import HOUSE_CLERK_SAMPLE_DIR, load_house_clerk_bundle, load_house_clerk_sample_bundle
from app.etl.seed import build_seed_bundle


def test_load_house_clerk_sample_bundle_normalizes_house_clerk_xml() -> None:
    bundle = load_house_clerk_sample_bundle()

    assert len(bundle.legislators) == 3
    assert bundle.legislators[0]["id"] == "leg_alex_morgan"
    assert len(bundle.bills) == 4
    assert bundle.roll_calls[0]["bill_ref"] == "bill_119_hr_120"
    assert bundle.bills[0]["committee"] == "Transportation and Infrastructure"
    assert bundle.vote_subject_tags["bill_119_hr_120"] == ["transportation", "infrastructure", "broadband"]
    assert bundle.votes_cast[0]["roll_call_id"] == "rc_house_001"
    assert bundle.votes_cast[1]["position"] == "nay"


def test_run_etl_supports_house_clerk_sample_source() -> None:
    result = run_etl(source="house_clerk_sample", as_of=date(2026, 3, 12))

    assert result.records_loaded == 26
    assert result.records_classified == 4
    assert result.fingerprints_computed == 24
    assert result.drift_scores_computed == 3


def test_build_seed_bundle_supports_house_clerk_sample_source() -> None:
    bundle = build_seed_bundle(source="house_clerk_sample", as_of=date(2026, 3, 12))

    assert len(bundle.legislators) == 3
    assert len(bundle.vote_classifications) == 4
    assert len(bundle.summaries) == 3


def test_house_clerk_bundle_prefers_cached_congress_bill_metadata(tmp_path: Path) -> None:
    source_dir = tmp_path / "house_cache"
    source_dir.mkdir()
    (source_dir / "roll001.xml").write_text((HOUSE_CLERK_SAMPLE_DIR / "roll001.xml").read_text())

    congress_cache_dir = tmp_path / "congress" / "bills"
    congress_cache_dir.mkdir(parents=True)
    (congress_cache_dir / "119_hr_120.json").write_text(
        json.dumps(
            {
                "bill": {
                    "congress": 119,
                    "type": "hr",
                    "number": 120,
                    "title": "Cached Infrastructure Title",
                },
                "summaries": [{"text": "Cached summary"}],
                "committees": [{"name": "Cached Committee"}],
                "subjects": [{"name": "cached subject"}],
            }
        )
    )

    bundle = load_house_clerk_bundle(
        source_dir=source_dir,
        fallback_dir=HOUSE_CLERK_SAMPLE_DIR,
        congress_cache_dir=congress_cache_dir,
    )

    bill = next(item for item in bundle.bills if item["id"] == "bill_119_hr_120")
    assert bill["title"] == "Cached Infrastructure Title"
    assert bill["summary"] == "Cached summary"
    assert bill["committee"] == "Cached Committee"
    assert bill["subjects"] == ["cached subject"]
