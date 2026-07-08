from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CASES_ROOT = REPO_ROOT / "backend/tests/_zip_source_metadata_cases"
SCRIPT_PATH = REPO_ROOT / "backend/scripts/generate_zip_source_metadata_report.py"


spec = importlib.util.spec_from_file_location("zip_source_metadata_report", SCRIPT_PATH)
zip_report = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(zip_report)


def setup_function() -> None:
    _clean_cases()


def teardown_function() -> None:
    _clean_cases()


def test_schema_capability_detection_blocks_current_db_auto_select() -> None:
    repo_root = make_case(
        "schema",
        zip_rows=[{"zip": "27701", "state": "NC", "district": "04"}],
        zip_table_sql="""
CREATE TABLE zip_district_map (
    zip TEXT PRIMARY KEY CHECK (zip ~ '^[0-9]{5}$'),
    state TEXT NOT NULL,
    district TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""",
    )

    report = zip_report.build_report(repo_root)
    coverage = report["db_zip_metadata_coverage"]

    assert coverage["zip_primary_key"] is True
    assert coverage["can_store_multiple_districts_per_zip"] is False
    assert coverage["can_store_source_name"] is False
    assert coverage["can_store_source_retrieved_at"] is False
    assert coverage["can_store_source_effective_date"] is False
    assert coverage["can_store_source_version"] is False
    assert report["frontend_gating_implications"]["current_db_path_remains_blocked_from_auto_select"] is True


def test_fixture_metadata_coverage_detects_missing_source_fields_and_split_zip() -> None:
    repo_root = make_case(
        "fixtures",
        zip_rows=[
            {"zip": "27601", "state": "NC", "district": "04"},
            {"zip": "27601", "state": "NC", "district": "02"},
            {"zip": "27701", "state": "NC", "district": "04"},
        ],
    )

    report = zip_report.build_report(repo_root)
    fixture = report["fixture_zip_metadata_coverage"]

    assert fixture["fixture_row_count"] == 3
    assert fixture["fixture_zip_files_include_source_metadata"] is False
    assert fixture["rows_with_all_source_metadata"] == 0
    assert fixture["source_currentness"] == "fixture_sample"
    assert fixture["multi_district_zips"] == {"27601": ["NC-02", "NC-04"]}
    assert report["ambiguity_capability_by_source"]["fixtures"]["ambiguity_detection_level"] == "local_fixture_scan"


def test_report_outputs_are_deterministic_and_include_coverage_statement() -> None:
    repo_root = make_case(
        "deterministic",
        zip_rows=[{"zip": "88888", "state": "NC", "district": "04"}],
    )
    markdown_out = repo_root / "docs/review_packets/report.md"
    json_out = repo_root / "docs/review_packets/report.json"

    first = zip_report.build_report(repo_root)
    second = zip_report.build_report(repo_root)
    zip_report.write_outputs(first, repo_root=repo_root, markdown_out=markdown_out, json_out=json_out)

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert json.loads(json_out.read_text(encoding="utf-8"))["schema_version"] == zip_report.SCHEMA_VERSION
    assert zip_report.COVERAGE_STATEMENT in markdown_out.read_text(encoding="utf-8")
    assert first["api_response_contract"]["api_responses_include_standard_metadata_fields"] is True
    assert first["frontend_gating_implications"]["gates_missing_metadata"] is True


def make_case(name: str, *, zip_rows: list[dict[str, object]], zip_table_sql: str | None = None) -> Path:
    repo_root = CASES_ROOT / name
    fixtures = repo_root / "backend/fixtures"
    migrations = repo_root / "backend/migrations"
    api_dir = repo_root / "backend/app/api"
    frontend_lib = repo_root / "frontend/lib"
    frontend_components = repo_root / "frontend/components"
    docs = repo_root / "docs/review_packets"
    for path in [fixtures, migrations, api_dir, frontend_lib, frontend_components, docs]:
        path.mkdir(parents=True, exist_ok=True)

    (fixtures / "zip_district_map.json").write_text(json.dumps(zip_rows, indent=2), encoding="utf-8")
    (migrations / "0001_initial_schema.sql").write_text(zip_table_sql or default_zip_table_sql(), encoding="utf-8")
    (api_dir / "precomputed.py").write_text(precomputed_contract_text(), encoding="utf-8")
    (api_dir / "lookup.py").write_text("raise HTTPException(status_code=404, detail=\"ZIP not loaded\")\n", encoding="utf-8")
    (frontend_lib / "zipLookupState.mjs").write_text(frontend_classifier_text(), encoding="utf-8")
    (frontend_components / "ZipLookupPanel.js").write_text(
        '{"data_source": "none", "district_mappings": [], "source_currentness": "unsupported", "ambiguity_detection_level": "none"}',
        encoding="utf-8",
    )
    return repo_root


def default_zip_table_sql() -> str:
    return """
CREATE TABLE zip_district_map (
    zip TEXT PRIMARY KEY CHECK (zip ~ '^[0-9]{5}$'),
    state TEXT NOT NULL,
    district TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def precomputed_contract_text() -> str:
    return """
def _build_zip_lookup_metadata():
    return {
        "source_type": source_type,
        "source_name": source_name,
        "source_retrieved_at": source_retrieved_at,
        "source_effective_date": source_effective_date,
        "source_version": source_version,
        "source_currentness": source_currentness,
        "fixture_sample_only": fixture_sample_only,
        "stale_or_unknown_source": stale_or_unknown_source,
        "member_metadata_uncertain": member_metadata_uncertain,
        "can_represent_multiple_districts": can_represent_multiple_districts,
        "ambiguity_detection_level": ambiguity_detection_level,
        "district_mappings": [],
    }
_build_zip_lookup_metadata(source_currentness="stale_or_unknown", stale_or_unknown_source=True, ambiguity_detection_level="single_row")
_build_zip_lookup_metadata(source_currentness="fixture_sample", fixture_sample_only=True, ambiguity_detection_level="local_fixture_scan")
"""


def frontend_classifier_text() -> str:
    return """
const sourceIsStaleOrUnknown = metadata.source_currentness === "stale_or_unknown" || (!isFixtureSample && !sourceKnown);
const isFixtureSample = metadata.fixture_sample_only === true || metadata.source_currentness === "fixture_sample";
if (uniqueDistrictKeys.length > 1) {}
if (uniqueStates.length > 1) {}
if (ZIP_LOOKUP_STATES.UNSUPPORTED_ZIP) {}
const canAutoSelectHouse = state === ZIP_LOOKUP_STATES.SINGLE_DISTRICT_READY;
const current = metadata.source_currentness === "current";
"""


def _clean_cases() -> None:
    if CASES_ROOT.exists():
        resolved = CASES_ROOT.resolve()
        expected_parent = (REPO_ROOT / "backend/tests").resolve()
        assert expected_parent in resolved.parents
        shutil.rmtree(resolved)
