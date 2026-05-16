from datetime import date
import json

from app.etl.compute import run_etl
from app.etl.congress_adapter import load_congress_bill_cache, load_congress_sample_bundle
from app.etl.seed import build_seed_bundle


def test_load_congress_sample_bundle_normalizes_official_style_records() -> None:
    bundle = load_congress_sample_bundle()

    assert len(bundle.legislators) == 3
    assert bundle.legislators[0]["id"] == "leg_alex_morgan"
    assert len(bundle.bills) == 12
    assert bundle.roll_calls[0]["bill_ref"] == "bill_118_hr_101"
    assert bundle.votes_cast[0]["roll_call_id"] == "rc_house_001"


def test_run_etl_supports_congress_sample_source() -> None:
    result = run_etl(source="congress_sample", as_of=date(2026, 3, 12))

    assert result.records_loaded == 48
    assert result.records_classified == 12
    assert result.fingerprints_computed == 24
    assert result.drift_scores_computed == 3


def test_build_seed_bundle_supports_congress_sample_source() -> None:
    bundle = build_seed_bundle(source="congress_sample", as_of=date(2026, 3, 12))

    assert len(bundle.legislators) == 3
    assert len(bundle.vote_classifications) == 12
    assert len(bundle.summaries) == 3


def test_load_congress_bill_cache_merges_summary_and_subject_subresources(tmp_path) -> None:
    bills_dir = tmp_path / "congress" / "bills"
    summaries_dir = tmp_path / "congress" / "bill_summaries"
    subjects_dir = tmp_path / "congress" / "bill_subjects"
    bills_dir.mkdir(parents=True)
    summaries_dir.mkdir()
    subjects_dir.mkdir()

    (bills_dir / "119_hr_120.json").write_text(
        json.dumps(
            {
                "bill": {
                    "congress": 119,
                    "type": "HR",
                    "number": "120",
                    "title": "Test Act",
                    "summaries": {
                        "count": 1,
                        "url": "https://api.congress.gov/v3/bill/119/hr/120/summaries",
                    },
                    "subjects": {
                        "count": 1,
                        "url": "https://api.congress.gov/v3/bill/119/hr/120/subjects",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (summaries_dir / "119_hr_120.json").write_text(
        json.dumps({"summaries": [{"text": "CRS says the bill expands a grant program."}]}),
        encoding="utf-8",
    )
    (subjects_dir / "119_hr_120.json").write_text(
        json.dumps({"subjects": [{"name": "Education programs"}]}),
        encoding="utf-8",
    )

    cache = load_congress_bill_cache(bills_dir)

    bill = cache[(119, "hr", 120)]
    assert bill["summary"] == "CRS says the bill expands a grant program."
    assert bill["subjects"] == ["Education programs"]


def test_load_congress_bill_cache_flattens_nested_subject_subresource(tmp_path) -> None:
    bills_dir = tmp_path / "congress" / "bills"
    subjects_dir = tmp_path / "congress" / "bill_subjects"
    bills_dir.mkdir(parents=True)
    subjects_dir.mkdir()

    (bills_dir / "119_hr_498.json").write_text(
        json.dumps(
            {
                "bill": {
                    "congress": 119,
                    "type": "HR",
                    "number": "498",
                    "title": "Do No Harm in Medicaid Act",
                }
            }
        ),
        encoding="utf-8",
    )
    (subjects_dir / "119_hr_498.json").write_text(
        json.dumps(
            {
                "subjects": {
                    "legislativeSubjects": [{"name": "Medicaid"}],
                    "policyArea": {"name": "Health"},
                }
            }
        ),
        encoding="utf-8",
    )

    cache = load_congress_bill_cache(bills_dir)

    assert cache[(119, "hr", 498)]["subjects"] == ["Medicaid", "Health"]
