import json
import shutil
from pathlib import Path

from scripts.generate_data_inventory_manifest import build_manifest


CASE_ROOT = Path(__file__).resolve().parent / "_data_inventory_cases"


def case_root(name: str) -> Path:
    root = CASE_ROOT / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_manifest_handles_missing_directories_gracefully():
    root = case_root("missing_directories")
    manifest = build_manifest(root)

    assert manifest["scope"]["read_only"] is True
    assert manifest["scope"]["requires_production_credentials"] is False
    assert manifest["source_cache_inventory"]["house_clerk"][0]["roll_xml_count"] == 0
    assert any("House Clerk cache gap" in warning for warning in manifest["warnings"])


def test_fixture_counts_are_deterministic():
    root = case_root("fixture_counts")
    write_json(
        root / "backend/fixtures/legislators.json",
        [
            {
                "id": "leg_a",
                "bioguide_id": "A000001",
                "name_display": "Example A",
                "chamber": "house",
                "state": "NC",
                "district": "04",
                "party": "D",
                "in_office": True,
            },
            {
                "id": "leg_b",
                "bioguide_id": "B000001",
                "name_display": "Example B",
                "chamber": "senate",
                "state": "NC",
                "district": None,
                "party": "R",
                "in_office": True,
            },
        ],
    )
    write_json(
        root / "backend/fixtures/roll_calls.json",
        [
            {
                "id": "rc1",
                "chamber": "house",
                "congress": 119,
                "rollcall_number": 1,
                "vote_date": "2025-01-10T00:00:00Z",
                "bill_ref": "bill_a",
                "source_url": "https://clerk.house.gov/Votes/20251",
            }
        ],
    )
    write_json(
        root / "backend/fixtures/votes_cast.json",
        [{"roll_call_id": "rc1", "legislator_id": "leg_a", "position": "yea"}],
    )
    write_json(root / "backend/fixtures/vote_subject_tags.json", {"bill_a": ["Economy"]})
    write_json(root / "backend/fixtures/zip_district_map.json", [{"zip": "27701", "state": "NC", "district": "04"}])

    manifest = build_manifest(root)

    assert manifest["legislator_metadata_inventory"]["fixture_legislators"]["total"] == 2
    assert manifest["vote_row_inventory"]["fixture_roll_call_rows"] == 1
    assert manifest["vote_row_inventory"]["fixture_member_vote_rows"] == 1
    assert manifest["zip_district_inventory"]["unique_zips"] == 1
    assert manifest["source_url_coverage"]["rows_with_official_source_url"] == 1


def test_warning_generation_flags_non_official_sources_and_zip_limits():
    root = case_root("warnings")
    write_json(
        root / "backend/fixtures/legislators.json",
        [
            {
                "id": "leg_a",
                "bioguide_id": "",
                "name_display": "Example A",
                "chamber": "house",
                "state": "NC",
                "district": "04",
                "party": "D",
                "in_office": True,
            }
        ],
    )
    write_json(
        root / "backend/fixtures/roll_calls.json",
        [
            {
                "id": "rc1",
                "chamber": "house",
                "congress": 118,
                "rollcall_number": 1,
                "vote_date": "2024-01-10T00:00:00Z",
                "source_url": "https://example.com/not-official",
            }
        ],
    )
    write_json(root / "backend/fixtures/votes_cast.json", [])
    write_json(root / "backend/fixtures/zip_district_map.json", [{"zip": "27701", "state": "NC", "district": "04"}])

    manifest = build_manifest(root)
    warnings = "\n".join(manifest["warnings"])

    assert "non-official source URLs" in warnings
    assert "missing bioguide_id" in warnings
    assert "split-ZIP/address ambiguity" in warnings


def test_manifest_does_not_require_production_credentials(monkeypatch):
    root = case_root("no_credentials")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)

    manifest = build_manifest(root)

    assert manifest["scope"]["requires_production_credentials"] is False
