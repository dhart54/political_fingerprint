from pathlib import Path

from app.etl.senate_amendment_facts import (
    _parse_bill_reference,
    build_senate_amendment_fact_manifest,
    validate_senate_amendment_fact_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SENATE_XML_DIR = REPO_ROOT / "backend" / "data_sources" / "senate_xml"


def test_parse_bill_reference_supports_senate_concurrent_resolution_parent() -> None:
    assert _parse_bill_reference("S.Con.Res. 7") == {
        "bill_type": "sconres",
        "bill_number": 7,
        "display": "S.Con.Res. 7",
    }


def test_build_senate_amendment_manifest_preserves_identity_and_requires_model_change() -> None:
    manifest = build_senate_amendment_fact_manifest(senate_xml_dir=SENATE_XML_DIR)

    candidates = manifest["included_candidate_roll_calls"]
    deferred = manifest["excluded_or_deferred_roll_calls"]

    assert manifest["import_policy"] == "local dry-run only; do not import"
    assert manifest["schema_migration_required_before_import"] is True
    assert len(candidates) == 112
    assert len(deferred) == 1
    assert manifest["summary"]["planned_bill_inserts"] == 10
    assert manifest["summary"]["planned_roll_call_inserts"] == 112
    assert manifest["summary"]["planned_votes_cast_inserts"] == 11197
    assert manifest["summary"]["planned_vote_context_inserts"] == 11197
    assert manifest["summary"]["planned_amendment_reference_inserts"] == 112
    assert manifest["summary"]["planned_vote_interpretation_inserts"] == 0

    first = candidates[0]
    assert first["roll_number"] == 3
    assert first["amendment_number"] == "S.Amdt. 14"
    assert first["parent_bill"] == {
        "bill_type": "s",
        "bill_number": 5,
        "display": "S. 5",
    }
    assert first["amendment_purpose"]
    assert first["schema_model_available"] is True
    assert first["production_migration_required_before_import"] is True
    assert first["interpretations_included"] is False
    assert first["planned_senate_amendment_reference"] == {
        "roll_call_lookup": {
            "chamber": "senate",
            "congress": 119,
            "roll_number": first["roll_number"],
        },
        "amendment_number": first["amendment_number"],
        "amendment_type": "S.Amdt.",
        "amendment_to_amendment_number": first["amendment_to_amendment_number"],
        "parent_bill_type": "s",
        "parent_bill_number": 5,
        "parent_bill_display": "S. 5",
        "amendment_purpose": first["amendment_purpose"],
        "source_url": first["source_url"],
        "source_xml_path": first["source_xml_path"],
        "fact_status": "fact_only_uninterpreted",
        "source_version": "senate_xml_119_2025_v1",
    }


def test_validate_senate_amendment_manifest_rejects_missing_parent_context() -> None:
    manifest = build_senate_amendment_fact_manifest(senate_xml_dir=SENATE_XML_DIR)
    broken = {
        **manifest,
        "included_candidate_roll_calls": [
            {
                **manifest["included_candidate_roll_calls"][0],
                "parent_bill": None,
            }
        ],
    }

    result = validate_senate_amendment_fact_manifest(broken)

    assert result.planned_vote_interpretation_inserts == 0
    assert "Roll 3 is missing parent bill context." in result.errors
