from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = REPO_ROOT / "backend/migrations/0013_zip_district_mappings.sql"
FIXTURE_PATH = REPO_ROOT / "backend/fixtures/zip_multi_row_schema_sample/zip_district_mappings.json"
SCRIPT_PATH = REPO_ROOT / "backend/scripts/generate_zip_source_metadata_report.py"

spec = importlib.util.spec_from_file_location("zip_source_metadata_report", SCRIPT_PATH)
zip_report = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(zip_report)


def test_multi_row_zip_migration_is_additive_and_keeps_compatibility_table() -> None:
    migration_sql = MIGRATION_PATH.read_text(encoding="utf-8")
    lowered = migration_sql.lower()

    assert "create table if not exists zip_district_mappings" in lowered
    assert "id bigserial primary key" in lowered
    assert not re.search(r"\bzip\s+text\s+primary\s+key\b", lowered)
    assert "check (zip ~ '^[0-9]{5}$')" in lowered
    assert "drop table" not in lowered
    assert not re.search(r"\balter\s+table\s+zip_district_map\b", lowered)


def test_multi_row_zip_migration_has_required_metadata_columns_checks_and_indexes() -> None:
    report = zip_report.build_report(REPO_ROOT)
    schema = report["multi_row_schema_contract"]

    assert schema["migration_exists"] is True
    assert schema["table_found"] is True
    assert schema["surrogate_id_primary_key"] is True
    assert schema["zip_not_primary_key"] is True
    assert schema["all_required_columns_present"] is True
    assert schema["all_source_metadata_columns_present"] is True
    assert schema["controlled_source_currentness_check_present"] is True
    assert schema["controlled_confidence_check_present"] is True
    assert schema["all_required_indexes_present"] is True
    assert schema["unique_active_source_period_rule"] is True
    assert schema["can_represent_multiple_districts_per_zip"] is True
    assert schema["old_table_compatibility_only"] is True


def test_synthetic_multi_row_fixture_covers_required_cases_and_detection() -> None:
    rows = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    report = zip_report.build_report(REPO_ROOT)
    fixture = report["multi_row_synthetic_fixture_coverage"]

    assert len(rows) == fixture["row_count"]
    assert fixture["has_single_district_case"] is True
    assert fixture["has_same_state_multi_district_case"] is True
    assert fixture["has_multi_state_case"] is True
    assert fixture["has_fixture_sample_case"] is True
    assert fixture["has_stale_unknown_case"] is True
    assert fixture["has_current_source_backed_case"] is True
    assert fixture["has_duplicate_detection_case"] is True
    assert fixture["multi_district_zips"] == {
        "09991": ["NC-02", "NC-04"],
        "09992": ["NC-04", "SC-01"],
    }
    assert fixture["multi_state_zips"] == {"09992": ["NC", "SC"]}
    assert fixture["duplicate_active_source_key_count"] == 1
    assert fixture["missing_source_metadata_row_count"] == 1


def test_report_confirms_route_switch_absent_and_old_db_path_gated() -> None:
    report = zip_report.build_report(REPO_ROOT)
    route = report["route_switch_status"]
    checks = {row["check"]: row["passed"] for row in report["coverage_checks"]}

    assert route["current_lookup_route_uses_old_gated_path"] is True
    assert route["new_table_route_switch_absent"] is True
    assert route["old_table_query_present"] is True
    assert route["new_table_query_present"] is False
    assert checks["current_lookup_route_still_uses_old_gated_path"] is True
    assert checks["new_table_route_switch_absent"] is True
    assert checks["old_table_remains_compatibility_only"] is True
