from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

from backend.app import zip_member_readiness as readiness


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_SCRIPT = REPO_ROOT / "backend/scripts/dry_run_zip_source_import.py"
EXCERPT = REPO_ROOT / "backend/fixtures/zip_source_dry_run_sample/census_119_cd_zcta_official_layout_excerpt.txt"
EVALUATOR = REPO_ROOT / "backend/scripts/evaluate_zip_source_member_readiness.py"
CASES_ROOT = REPO_ROOT / "backend/tests/_zip_member_readiness_cases"

spec = importlib.util.spec_from_file_location("zip_source", SOURCE_SCRIPT)
zip_source = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(zip_source)

FULL_SCHEMA = set(readiness.REQUIRED_CURRENTNESS_FIELDS) | {
    "bioguide_id", "chamber", "state", "district", "metadata_currentness"
}


def member(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "bioguide_id": "A000001",
        "chamber": "house",
        "state": "NC",
        "district": "04",
        "in_office": True,
        "congress": 119,
        "term_start": "2025-01-03",
        "term_end": "2027-01-03",
        "seat_status": "filled",
        "member_type": "voting_representative",
        "metadata_source_url": "https://example.gov/member",
        "metadata_retrieved_at": "2026-07-12",
        "metadata_currentness": "current",
    }
    row.update(overrides)
    return row


def evaluate(rows: list[dict[str, object]], *, state: str = "NC", district: str = "04", schema: set[str] = FULL_SCHEMA):
    return readiness.evaluate_pair(state=state, district=district, members=rows, schema_fields=schema)


def test_exactly_one_current_voting_house_member_is_diagnostically_ready() -> None:
    assert evaluate([member()]).status == readiness.READY


def test_zero_current_matches() -> None:
    assert evaluate([]).status == readiness.NO_MATCH


def test_duplicate_current_matches() -> None:
    assert evaluate([member(), member(bioguide_id="B000002")]).status == readiness.DUPLICATE


def test_one_current_plus_one_former_member() -> None:
    result = evaluate([member(), member(bioguide_id="B000002", in_office=False)])
    assert result.status == readiness.READY
    assert result.current_matching_member_count == 1


def test_stale_and_unknown_currentness() -> None:
    assert evaluate([member(metadata_currentness="stale")]).status == readiness.STALE
    assert evaluate([member(metadata_currentness="unknown")]).status == readiness.CURRENTNESS_UNKNOWN


def test_missing_stable_identifier() -> None:
    assert evaluate([member(bioguide_id="")]).status == readiness.MISSING_IDENTIFIER


def test_chamber_state_and_district_mismatches() -> None:
    assert evaluate([member(chamber="senate")]).status == readiness.CHAMBER_MISMATCH
    assert evaluate([member(state="SC")]).status == readiness.STATE_MISMATCH
    assert evaluate([member(district="05")]).status == readiness.DISTRICT_MISMATCH


def test_valid_voting_at_large_state_district_zero() -> None:
    result = evaluate([member(state="AK", district="00")], state="AK", district="0")
    assert result.status == readiness.READY
    assert result.at_large_type == "voting_at_large_state"


def test_dc_delegate_requires_review() -> None:
    result = evaluate([member(state="DC", district="00", member_type="delegate")], state="DC", district="00")
    assert result.status == readiness.DELEGATE_REVIEW
    assert result.at_large_type == "dc_delegate"


def test_unsupported_territory_and_resident_commissioner() -> None:
    assert evaluate([], state="GU", district="00").status == readiness.UNSUPPORTED_TERRITORY
    assert evaluate([], state="PR", district="00").status == readiness.RESIDENT_COMMISSIONER_REVIEW


def test_vacancy_blocks_readiness() -> None:
    assert evaluate([member(seat_status="vacant")]).status == readiness.VACANCY


def test_schema_insufficient_blocks_otherwise_matching_member() -> None:
    assert evaluate([member()], schema={"bioguide_id", "chamber", "state", "district", "in_office"}).status == readiness.SCHEMA_INSUFFICIENT


def test_fixture_source_identity_remains_non_official() -> None:
    report = zip_source.build_report(input_path=EXCERPT)
    assert report["input"]["official_file_identity_verified"] is False
    assert report["input"]["input_classification"] == "test_or_sample_input"


def test_spoofed_official_filename_still_fails_closed() -> None:
    CASES_ROOT.mkdir(parents=True, exist_ok=True)
    spoof = CASES_ROOT / zip_source.EXPECTED_OFFICIAL_FILE_NAME
    try:
        spoof.write_text("spoof", encoding="utf-8")
        try:
            zip_source.inspect_official_file_identity(spoof)
        except ValueError as exc:
            assert "pinned identity verification failed" in str(exc)
        else:
            raise AssertionError("spoofed official filename did not fail closed")
    finally:
        if CASES_ROOT.exists():
            shutil.rmtree(CASES_ROOT)


def test_evaluator_has_no_database_write_sql_and_final_eligibility_is_fixed_zero() -> None:
    script = EVALUATOR.read_text(encoding="utf-8").lower()
    for statement in ("insert into", "update ", "delete from", "truncate ", "drop table", "copy ", "alter table", ".commit("):
        assert statement not in script
    assert '"production_auto_select_eligible_count": 0' in script
