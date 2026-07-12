from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

from backend.app import zip_member_readiness as readiness


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_SCRIPT = REPO_ROOT / "backend/scripts/dry_run_zip_source_import.py"
EXCERPT = REPO_ROOT / "backend/fixtures/zip_source_dry_run_sample/census_119_cd_zcta_official_layout_excerpt.txt"
EVALUATOR = REPO_ROOT / "backend/scripts/evaluate_zip_source_member_readiness.py"
CASES_ROOT = REPO_ROOT / "backend/tests/_zip_member_readiness_cases"
PACKET = REPO_ROOT / "docs/review_packets/zip_source_member_readiness_gate_v1.json"

spec = importlib.util.spec_from_file_location("zip_source", SOURCE_SCRIPT)
zip_source = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(zip_source)

evaluator_spec = importlib.util.spec_from_file_location("zip_member_evaluator", EVALUATOR)
evaluator = importlib.util.module_from_spec(evaluator_spec)
assert evaluator_spec.loader is not None
evaluator_spec.loader.exec_module(evaluator)

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
    result = evaluate([member(state="DC", district="98", member_type="delegate")], state="DC", district="98")
    assert result.status == readiness.DELEGATE_REVIEW
    assert result.at_large_type == "dc_delegate"
    assert result.district == "98"


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


def test_nonempty_mapping_table_fails_closed_and_empty_status_uses_row_count() -> None:
    empty = evaluator.validate_mapping_table_state(table_exists=True, row_count=0)
    assert empty["actual_row_count"] == 0
    assert empty["empty"] is True
    try:
        evaluator.validate_mapping_table_state(table_exists=True, row_count=1)
    except evaluator.ReadinessSafetyError as exc:
        assert "contains 1 rows" in str(exc)
    else:
        raise AssertionError("nonempty mapping table did not fail closed")


def test_route_confirmations_are_derived_from_inspected_source() -> None:
    root = _write_route_fixture(new_table=False, flag_value=None)
    try:
        inspected = evaluator.inspect_repository_state(root)
        assert inspected["route_state"]["lookup_zip_reads_zip_district_map"] is True
        assert inspected["route_state"]["lookup_zip_races_reads_zip_district_map"] is True
        assert inspected["route_state"]["either_public_endpoint_reads_zip_district_mappings"] is False
        precomputed = root / "backend/app/api/precomputed.py"
        precomputed.write_text(precomputed.read_text(encoding="utf-8").replace("FROM zip_district_map", "FROM zip_district_mappings"), encoding="utf-8")
        changed = evaluator.inspect_repository_state(root)
        assert changed["route_state"]["either_public_endpoint_reads_zip_district_mappings"] is True
        try:
            evaluator.ensure_repository_state_safe(changed)
        except evaluator.ReadinessSafetyError:
            pass
        else:
            raise AssertionError("new-table public route did not fail closed")
    finally:
        shutil.rmtree(root)


def test_enabled_flag_fails_closed_and_absent_flag_is_accurate() -> None:
    absent_root = _write_route_fixture(new_table=False, flag_value=None)
    enabled_root = CASES_ROOT / "enabled"
    try:
        absent = evaluator.inspect_repository_state(absent_root)
        assert absent["feature_flag"]["status"] == "absent_not_configured"
        _write_route_fixture(new_table=False, flag_value="true", root=enabled_root)
        enabled = evaluator.inspect_repository_state(enabled_root)
        assert enabled["feature_flag"]["status"] == "enabled"
        try:
            evaluator.ensure_repository_state_safe(enabled)
        except evaluator.ReadinessSafetyError as exc:
            assert "enabled" in str(exc)
        else:
            raise AssertionError("enabled flag did not fail closed")
    finally:
        if CASES_ROOT.exists():
            shutil.rmtree(CASES_ROOT)


def test_generated_packet_reports_dc_source_district_98_and_zero_production_eligibility() -> None:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    dc_rows = packet["sample_pair_results_by_status"][readiness.DELEGATE_REVIEW]
    assert dc_rows[0]["state"] == "DC"
    assert dc_rows[0]["district"] == "98"
    assert packet["summary"]["production_auto_select_eligible_count"] == 0


def _write_route_fixture(*, new_table: bool, flag_value: str | None, root: Path | None = None) -> Path:
    root = root or (CASES_ROOT / "routes")
    api = root / "backend/app/api"
    api.mkdir(parents=True, exist_ok=True)
    (root / "frontend").mkdir(parents=True, exist_ok=True)
    table = "zip_district_mappings" if new_table else "zip_district_map"
    (api / "lookup.py").write_text(
        "def lookup_zip(zip_code):\n    return get_zip_lookup_response(zip_code=zip_code)\n\n"
        "def lookup_zip_races(zip_code):\n    return get_zip_race_response(zip_code=zip_code)\n",
        encoding="utf-8",
    )
    (api / "precomputed.py").write_text(
        "def get_zip_lookup_response(zip_code):\n    return _get_db_zip_lookup_response(zip_code=zip_code)\n\n"
        "def get_zip_race_response(zip_code):\n    return _get_db_zip_race_response(zip_code=zip_code)\n\n"
        "def _get_db_zip_lookup_response(zip_code):\n    return _get_db_zip_record(zip_code=zip_code)\n\n"
        "def _get_db_zip_race_response(zip_code):\n    return _get_db_zip_record(zip_code=zip_code)\n\n"
        f"def _get_db_zip_record(zip_code):\n    sql = 'SELECT zip FROM {table}'\n    return sql\n\n"
        "def _get_db_house_rep(state, district):\n    sql = \"SELECT * FROM legislators WHERE chamber = 'house' AND state = %s AND district = %s ORDER BY id LIMIT 1\"\n    return sql\n",
        encoding="utf-8",
    )
    if flag_value is not None:
        (root / "backend/.env").write_text(f"ZIP_MULTI_ROW_LOOKUP_ENABLED={flag_value}\n", encoding="utf-8")
    return root
