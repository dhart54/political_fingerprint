from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "backend/scripts/dry_run_zip_source_import.py"
FIXTURE_PATH = REPO_ROOT / "backend/fixtures/zip_source_dry_run_sample/census_119_cd_zcta_sample.csv"
OFFICIAL_EXCERPT_PATH = REPO_ROOT / "backend/fixtures/zip_source_dry_run_sample/census_119_cd_zcta_official_layout_excerpt.txt"
CASES_ROOT = REPO_ROOT / "backend/tests/_zip_source_dry_run_cases"


spec = importlib.util.spec_from_file_location("zip_source_dry_run_import", SCRIPT_PATH)
zip_dry_run = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(zip_dry_run)


def setup_function() -> None:
    _clean_cases()


def teardown_function() -> None:
    _clean_cases()


def test_dry_run_report_detects_ambiguity_and_rejections() -> None:
    report = zip_dry_run.build_report(input_path=FIXTURE_PATH)
    summary = report["dry_run_summary"]

    assert report["schema_version"] == zip_dry_run.SCHEMA_VERSION
    assert report["source_approval"]["decision"] == "approved_for_bounded_dry_run_only"
    assert report["source_approval"]["production_ingestion_approved"] is False
    assert summary["row_count"] == 11
    assert summary["accepted_row_count"] == 7
    assert summary["rejected_row_count"] == 4
    assert summary["unique_zip_zcta_count"] == 4
    assert summary["state_count"] == 2
    assert summary["unique_state_district_pair_count"] == 4
    assert summary["same_state_multi_district_count"] == 1
    assert summary["same_state_multi_district_zips"] == {"09991": ["NC-02", "NC-04"]}
    assert summary["multi_state_count"] == 1
    assert summary["multi_state_zips"] == {"09992": ["NC-04", "SC-07"]}
    assert summary["duplicate_active_row_count"] == 1
    assert summary["missing_required_metadata_count"] == 1
    assert summary["invalid_zip_zcta_format_count"] == 1
    assert summary["invalid_state_count"] == 1
    assert summary["invalid_district_count"] == 1
    assert summary["source_only_future_auto_select_candidate_zip_count"] == 1
    assert summary["future_auto_select_eligible_zip_count"] == 0
    assert summary["would_any_row_be_auto_select_eligible_under_strict_gates"] is False
    assert summary["database_write_occurred"] is False
    assert summary["supabase_connection_opened"] is False


def test_dry_run_fail_closed_without_flag() -> None:
    CASES_ROOT.mkdir(parents=True, exist_ok=True)
    output_path = CASES_ROOT / "zip_source_dry_run_report.json"

    result = zip_dry_run.main(["--input", str(FIXTURE_PATH), "--output", str(output_path)])

    assert result == 2
    assert not output_path.exists()


def test_official_census_pipe_layout_is_adapted_without_guessing_columns() -> None:
    report = zip_dry_run.build_report(input_path=OFFICIAL_EXCERPT_PATH)
    summary = report["dry_run_summary"]

    assert summary["row_count"] == 2
    assert summary["accepted_row_count"] == 2
    assert summary["rejected_row_count"] == 0
    assert summary["unique_zip_zcta_count"] == 2
    assert summary["state_count"] == 1
    assert report["sample_rows"][0] == {
        "zip": "36009",
        "state": "AL",
        "district": "01",
        "source_currentness": "current",
        "confidence": "source_backed",
        "ambiguity_detection_level": "multi_row_source",
    }
    assert report["input"]["sha256"]


def test_dry_run_writes_review_packet_outputs() -> None:
    CASES_ROOT.mkdir(parents=True, exist_ok=True)
    json_output = CASES_ROOT / "zip_source_dry_run_report.json"
    markdown_output = CASES_ROOT / "zip_source_dry_run_report.md"

    result = zip_dry_run.main(
        [
            "--dry-run",
            "--input",
            str(FIXTURE_PATH),
            "--output",
            str(json_output),
            "--markdown-output",
            str(markdown_output),
        ]
    )

    assert result == 0
    payload = json.loads(json_output.read_text(encoding="utf-8"))
    markdown = markdown_output.read_text(encoding="utf-8")
    assert payload["dry_run_summary"]["explicit_no_db_write"] is True
    assert payload["scope"]["route_switch_made"] is False
    assert "Production ingestion is not approved" in markdown


def test_script_does_not_import_database_clients_or_write_sql() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8").lower()

    assert "psycopg" not in script
    assert "from supabase" not in script
    assert "create_client" not in script
    assert "os.environ" not in script
    assert "getenv" not in script
    assert "insert into" not in script
    assert "update " not in script
    assert "delete from" not in script
    assert "truncate " not in script
    assert "drop table" not in script


def _clean_cases() -> None:
    if CASES_ROOT.exists():
        shutil.rmtree(CASES_ROOT)
