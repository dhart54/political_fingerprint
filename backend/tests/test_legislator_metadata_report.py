import json
import shutil
from pathlib import Path

import pytest

from scripts.generate_legislator_metadata_report import build_report


CASE_ROOT = Path(__file__).resolve().parent / "_legislator_metadata_cases"


@pytest.fixture(autouse=True)
def cleanup_case_root():
    yield
    if CASE_ROOT.exists():
        shutil.rmtree(CASE_ROOT)


def case_root(name: str) -> Path:
    root = CASE_ROOT / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def table_row(report: dict, section: str, source_kind: str) -> dict:
    return next(row for row in report[section]["table"] if row["source_kind"] == source_kind)


def test_missing_identity_fields_are_reported() -> None:
    root = case_root("missing_identity")
    write_json(
        root / "backend/fixtures/legislators.json",
        [
            {
                "id": "leg_missing",
                "bioguide_id": "",
                "name_display": "",
                "chamber": "house",
                "state": "NC",
                "district": "04",
                "party": "D",
                "in_office": True,
            }
        ],
    )

    report = build_report(root)
    row = table_row(report, "identity_completeness", "fixture_legislators")

    assert row["missing_bioguide_id"] == 1
    assert row["missing_display_name"] == 1
    assert row["missing_persisted_slug"] == 1
    assert report["scope"]["requires_production_credentials"] is False


def test_duplicate_bioguide_ids_are_reported() -> None:
    root = case_root("duplicate_bioguide")
    write_json(
        root / "backend/fixtures/legislators.json",
        [
            {
                "id": "leg_one",
                "bioguide_id": "D000001",
                "name_display": "Dana One",
                "chamber": "house",
                "state": "NC",
                "district": "01",
                "party": "D",
                "in_office": True,
            },
            {
                "id": "leg_two",
                "bioguide_id": "D000001",
                "name_display": "Dana Two",
                "chamber": "house",
                "state": "NC",
                "district": "02",
                "party": "D",
                "in_office": True,
            },
        ],
    )

    report = build_report(root)

    assert report["identity_completeness"]["table"][0]["duplicate_bioguide_ids"] == 1
    assert report["duplicate_conflict_findings"]["same_bioguide_mapped_to_multiple_app_ids"]
    assert any("Duplicate Bioguide" in warning for warning in report["warnings"])


def test_house_missing_district_and_senate_missing_lis_are_reported() -> None:
    root = case_root("chamber_identity")
    write_json(
        root / "backend/fixtures/legislators.json",
        [
            {
                "id": "leg_house",
                "bioguide_id": "H000001",
                "name_display": "House Example",
                "chamber": "house",
                "state": "NC",
                "district": None,
                "party": "D",
                "in_office": True,
            },
            {
                "id": "leg_senate",
                "bioguide_id": "S000001",
                "name_display": "Senate Example",
                "chamber": "senate",
                "state": "NC",
                "district": None,
                "party": "R",
                "in_office": True,
            },
        ],
    )

    report = build_report(root)
    identity = table_row(report, "identity_completeness", "fixture_legislators")
    chamber = table_row(report, "chamber_state_district_quality", "fixture_legislators")
    senate = table_row(report, "senate_metadata_readiness", "fixture_legislators")

    assert identity["missing_lis_id_for_senators"] == 1
    assert chamber["house_rows_missing_district"] == 1
    assert senate["missing_lis_id"] == 1
    assert any("Missing Senate LIS" in warning for warning in report["warnings"])


def test_stale_and_ambiguous_term_inference_is_reported() -> None:
    root = case_root("term_inference")
    write_json(
        root / "backend/data_sources/congress/members/118_members.json",
        {
            "congress": 118,
            "members": [
                {
                    "bioguideId": "S000100",
                    "name": "Stale, Member",
                    "partyName": "Republican",
                    "state": "North Carolina",
                    "district": 4,
                    "terms": {
                        "item": [
                            {
                                "chamber": "House of Representatives",
                                "startYear": 2023,
                                "endYear": 2024,
                            }
                        ]
                    },
                },
                {
                    "bioguideId": "A000100",
                    "name": "Ambiguous, Member",
                    "partyName": "Democratic",
                    "state": "North Carolina",
                    "district": 5,
                    "terms": {
                        "item": [
                            {
                                "chamber": "House of Representatives",
                                "startYear": 2025,
                            }
                        ]
                    },
                },
            ],
        },
    )

    report = build_report(root)
    currentness = table_row(report, "currentness_term_boundary", "congress_gov_member_cache")

    assert currentness["clearly_stale"] == 1
    assert currentness["ambiguous_currentness"] == 1
    assert currentness["term_dates_before_supported_window"] == 1
    assert any("Stale member rows" in warning for warning in report["warnings"])


def test_split_zip_fixture_detection_and_no_credentials_required() -> None:
    root = case_root("split_zip")
    write_json(
        root / "backend/fixtures/legislators.json",
        [
            {
                "id": "leg_house",
                "bioguide_id": "H000001",
                "name_display": "House Example",
                "chamber": "house",
                "state": "NC",
                "district": "04",
                "party": "D",
                "in_office": True,
            }
        ],
    )
    write_json(root / "backend/fixtures/zip_district_map.json", [{"zip": "27601", "state": "NC", "district": "04"}])
    write_json(root / "backend/fixtures/senate_xml_sample/zip_district_map.json", [{"zip": "27601", "state": "NC", "district": "02"}])

    report = build_report(root)

    assert report["scope"]["read_only"] is True
    assert report["scope"]["requires_production_credentials"] is False
    assert report["zip_district_lookup_implications"]["multi_district_zips_detected"] == {
        "27601": ["NC-02", "NC-04"]
    }
    assert any("Split-ZIP ambiguity" in warning for warning in report["warnings"])
