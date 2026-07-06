from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CASES_ROOT = REPO_ROOT / "backend/tests/_zip_district_ambiguity_cases"
SCRIPT_PATH = REPO_ROOT / "backend/scripts/generate_zip_district_ambiguity_report.py"


spec = importlib.util.spec_from_file_location("zip_district_ambiguity_report", SCRIPT_PATH)
zip_report = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(zip_report)


def setup_function() -> None:
    _clean_cases()


def teardown_function() -> None:
    _clean_cases()


def test_one_zip_one_district_has_no_ambiguity_and_one_house_match() -> None:
    repo_root = make_case(
        "single",
        zip_rows=[{"zip": "12345", "state": "NC", "district": "04"}],
        legislators=[
            {
                "id": "leg_single",
                "bioguide_id": "H000004",
                "name_display": "Single Member",
                "chamber": "house",
                "state": "NC",
                "district": "04",
                "party": "D",
                "in_office": True,
            }
        ],
    )

    report = zip_report.build_report(repo_root)

    assert report["zip_mapping_inventory"]["unique_zips"] == 1
    assert report["ambiguity_findings"]["multi_district_zips"] == {}
    assert report["ambiguity_findings"]["multi_state_zips"] == {}
    assert report["house_member_match_findings"]["zip_rows_without_matching_local_house_legislator"] == []
    assert report["house_member_match_findings"]["zip_rows_with_multiple_matching_current_house_legislators"] == []


def test_detects_same_state_multi_district_multi_state_and_duplicate_mappings() -> None:
    repo_root = make_case(
        "ambiguous",
        zip_rows=[
            {"zip": "11111", "state": "NC", "district": "04"},
            {"zip": "11111", "state": "NC", "district": "04"},
            {"zip": "11111", "state": "NC", "district": "02"},
            {"zip": "22222", "state": "NC", "district": "04"},
            {"zip": "22222", "state": "SC", "district": "01"},
        ],
        legislators=[
            house("H000004", "NC Four", "NC", "04"),
            house("H000002", "NC Two", "NC", "02"),
            house("H000001", "SC One", "SC", "01"),
        ],
    )

    report = zip_report.build_report(repo_root)
    warning_keys = active_warning_keys(report)

    assert report["ambiguity_findings"]["multi_district_zips"] == {
        "11111": ["NC-02", "NC-04"],
        "22222": ["NC-04", "SC-01"],
    }
    assert report["ambiguity_findings"]["multi_state_zips"] == {"22222": ["NC", "SC"]}
    assert report["zip_mapping_inventory"]["duplicate_identical_mappings"] == [
        {
            "mapping_key": "11111:NC:04",
            "count": 2,
            "source_files": ["backend/fixtures/zip_district_map.json"],
        }
    ]
    assert "split_zips_detected" in warning_keys
    assert "multi_state_zips_detected" in warning_keys
    assert "duplicate_mappings" in warning_keys


def test_flags_missing_state_missing_district_and_invalid_district() -> None:
    repo_root = make_case(
        "invalid",
        zip_rows=[
            {"zip": "33333", "district": "04"},
            {"zip": "44444", "state": "NC"},
            {"zip": "55555", "state": "NC", "district": "four"},
        ],
        legislators=[house("H000004", "NC Four", "NC", "04")],
    )

    report = zip_report.build_report(repo_root)
    inventory = report["zip_mapping_inventory"]
    warning_keys = active_warning_keys(report)

    assert [row["zip"] for row in inventory["missing_state_rows"]] == ["33333"]
    assert [row["zip"] for row in inventory["missing_district_rows"]] == ["44444"]
    assert [row["zip"] for row in inventory["invalid_district_rows"]] == ["55555"]
    assert "missing_state_or_district" in warning_keys
    assert "invalid_district_values" in warning_keys


def test_house_matching_flags_no_match_and_multiple_current_house_people() -> None:
    repo_root = make_case(
        "house_matches",
        zip_rows=[
            {"zip": "66666", "state": "NC", "district": "04"},
            {"zip": "77777", "state": "NC", "district": "05"},
        ],
        legislators=[
            house("H000004", "NC Four A", "NC", "04"),
            house("H100004", "NC Four B", "NC", "04"),
        ],
    )

    report = zip_report.build_report(repo_root)
    house_matches = report["house_member_match_findings"]
    warning_keys = active_warning_keys(report)

    assert [row["zip"] for row in house_matches["zip_rows_without_matching_local_house_legislator"]] == ["77777"]
    assert [row["zip"] for row in house_matches["zip_rows_with_multiple_matching_current_house_legislators"]] == ["66666"]
    assert "no_matching_house_legislator" in warning_keys
    assert "multiple_matching_current_house_legislators" in warning_keys


def test_report_uses_no_credentials_and_json_output_is_deterministic() -> None:
    repo_root = make_case(
        "deterministic",
        zip_rows=[{"zip": "88888", "state": "NC", "district": "04"}],
        legislators=[house("H000004", "NC Four", "NC", "04")],
    )
    markdown_out = repo_root / "docs/review_packets/report.md"
    json_out = repo_root / "docs/review_packets/report.json"

    first = zip_report.build_report(repo_root)
    second = zip_report.build_report(repo_root)
    zip_report.write_outputs(first, repo_root=repo_root, markdown_out=markdown_out, json_out=json_out)

    assert first["scope"]["requires_production_credentials"] is False
    assert first["scope"]["production_credentials_used"] is False
    assert first["scope"]["production_tables_queried"] is False
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert json.loads(json_out.read_text(encoding="utf-8"))["schema_version"] == "zip_district_ambiguity_hardening_v1"
    assert zip_report.COVERAGE_STATEMENT in markdown_out.read_text(encoding="utf-8")


def make_case(name: str, *, zip_rows: list[dict[str, object]], legislators: list[dict[str, object]]) -> Path:
    repo_root = CASES_ROOT / name
    fixtures = repo_root / "backend/fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)
    (fixtures / "zip_district_map.json").write_text(json.dumps(zip_rows, indent=2), encoding="utf-8")
    (fixtures / "legislators.json").write_text(json.dumps(legislators, indent=2), encoding="utf-8")
    return repo_root


def house(bioguide_id: str, name: str, state: str, district: str) -> dict[str, object]:
    return {
        "id": f"leg_{bioguide_id.lower()}",
        "bioguide_id": bioguide_id,
        "name_display": name,
        "chamber": "house",
        "state": state,
        "district": district,
        "party": "D",
        "in_office": True,
    }


def active_warning_keys(report: dict[str, object]) -> set[str]:
    return {item["warning_key"] for item in report["warning_catalog"] if item["active"]}


def _clean_cases() -> None:
    if CASES_ROOT.exists():
        resolved = CASES_ROOT.resolve()
        expected_parent = (REPO_ROOT / "backend/tests").resolve()
        assert expected_parent in resolved.parents
        shutil.rmtree(resolved)
