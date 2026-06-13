from pathlib import Path
from app.etl.senate_amendment_facts import (
    PHASE_19_APPROVAL_PHRASE,
    SenateAmendmentProductionState,
    _parse_bill_reference,
    apply_senate_amendment_reference_migration,
    build_phase_18_amendment_import_manifest,
    build_senate_amendment_fact_manifest,
    run_senate_amendment_fact_import,
    run_senate_amendment_import_dry_run_for_manifest,
    validate_local_amendment_reference_migration,
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


def test_build_phase_18_manifest_marks_rows_non_counting_import_preflight() -> None:
    manifest = build_phase_18_amendment_import_manifest(senate_xml_dir=SENATE_XML_DIR)

    candidates = manifest["included_candidate_roll_calls"]
    deferred = manifest["excluded_or_deferred_roll_calls"]

    assert manifest["phase"] == "Phase 18"
    assert manifest["approval_required_before_any_write"] is True
    assert len(candidates) == 112
    assert len(deferred) == 1
    assert deferred[0]["roll_number"] == 344
    assert manifest["summary"]["planned_amendment_reference_inserts"] == 112
    assert manifest["summary"]["planned_vote_interpretation_inserts"] == 0
    assert candidates[0]["support_oppose_positions_inferred"] is False
    assert candidates[0]["counts_as_interpretation"] is False


def test_senate_amendment_import_dry_run_plans_fact_and_reference_rows_only() -> None:
    result = run_senate_amendment_import_dry_run_for_manifest(
        manifest=build_phase_18_amendment_import_manifest(senate_xml_dir=SENATE_XML_DIR),
        senate_xml_dir=SENATE_XML_DIR,
    )

    assert len(result.candidate_roll_numbers) == 112
    assert result.planned_bill_inserts == 10
    assert result.planned_roll_call_inserts == 112
    assert result.planned_votes_cast_inserts == 11197
    assert result.planned_vote_context_inserts == 11197
    assert result.planned_amendment_reference_inserts == 112
    assert result.planned_vote_interpretation_inserts == 0
    assert result.planned_vote_interpretation_updates == 0
    assert result.planned_vote_interpretation_deletes == 0
    assert result.errors == []


def test_senate_amendment_import_dry_run_fails_closed_for_counting_claim() -> None:
    manifest = build_phase_18_amendment_import_manifest(senate_xml_dir=SENATE_XML_DIR)
    manifest["included_candidate_roll_calls"] = [
        {
            **manifest["included_candidate_roll_calls"][0],
            "counts_as_interpretation": True,
        }
    ]
    result = run_senate_amendment_import_dry_run_for_manifest(
        manifest=manifest,
        senate_xml_dir=SENATE_XML_DIR,
        production_state=_local_amendment_production_state(),
    )

    assert result.planned_vote_interpretation_inserts == 0
    assert "Roll 3 must not count as an interpretation." in result.errors
    assert "Roll 3 counts as interpretation; dry run fails closed." in result.errors


def test_senate_amendment_import_dry_run_fails_closed_for_interpreted_roll() -> None:
    result = run_senate_amendment_import_dry_run_for_manifest(
        manifest=build_phase_18_amendment_import_manifest(senate_xml_dir=SENATE_XML_DIR),
        senate_xml_dir=SENATE_XML_DIR,
        production_state=_local_amendment_production_state(
            roll_numbers_with_interpretations={3},
            legislator_bioguide_ids={_SHEEHY_EARLY_ROLL_LIS_ID},
        ),
    )

    assert result.planned_roll_call_inserts == 111
    assert "Roll 3 already has vote_interpretations rows; dry run fails closed." in result.errors


def test_senate_amendment_import_dry_run_reports_member_mapping_failures() -> None:
    manifest = build_phase_18_amendment_import_manifest(senate_xml_dir=SENATE_XML_DIR)
    manifest["included_candidate_roll_calls"] = [manifest["included_candidate_roll_calls"][0]]

    result = run_senate_amendment_import_dry_run_for_manifest(
        manifest=manifest,
        senate_xml_dir=SENATE_XML_DIR,
        production_state=_local_amendment_production_state(),
    )

    assert result.planned_roll_call_inserts == 0
    assert result.member_mapping_failures == [
        {
            "roll_number": 3,
            "missing_bioguide_ids": [_SHEEHY_EARLY_ROLL_LIS_ID],
        }
    ]
    assert "Roll 3 has member votes without production legislator mapping." in result.errors


def test_local_amendment_reference_migration_is_additive_and_non_interpretive() -> None:
    result = validate_local_amendment_reference_migration()

    assert result["creates_target_table"] is True
    assert result["references_roll_calls"] is True
    assert result["touches_vote_interpretations"] is False
    assert result["has_destructive_drop"] is False
    assert result["has_parent_bill_index"] is True
    assert result["has_fact_status_constraint"] is True


def test_phase_19_migration_requires_exact_approval_phrase_before_database_access() -> None:
    try:
        apply_senate_amendment_reference_migration(
            approval_phrase=PHASE_19_APPROVAL_PHRASE.replace("Phase 18", "Phase XVIII")
        )
    except ValueError as error:
        assert "Phase 19 approval gate" in str(error)
    else:
        raise AssertionError("Phase 19 migration must require exact approval phrase")


def test_phase_19_amendment_import_requires_exact_approval_phrase_before_database_access() -> None:
    try:
        run_senate_amendment_fact_import(
            manifest_path=REPO_ROOT / "docs" / "review_packets" / "senate_amendment_fact_import_manifest_phase_18.json",
            senate_xml_dir=SENATE_XML_DIR,
            approval_phrase=PHASE_19_APPROVAL_PHRASE.replace("112", "one hundred twelve"),
        )
    except ValueError as error:
        assert "Phase 19 approval gate" in str(error)
    else:
        raise AssertionError("Phase 19 amendment import must require exact approval phrase")


_SHEEHY_EARLY_ROLL_LIS_ID = "S350"


def _local_amendment_production_state(
    *,
    existing_roll_numbers: set[int] | None = None,
    existing_bill_keys: set[tuple[int, str, int]] | None = None,
    roll_numbers_with_interpretations: set[int] | None = None,
    legislator_bioguide_ids: set[str] | None = None,
) -> SenateAmendmentProductionState:
    from xml.etree import ElementTree

    from app.etl.senate_xml_adapter import _parse_members

    member_tree = ElementTree.parse(SENATE_XML_DIR / "members.xml")
    bioguide_ids = {
        str(row["bioguide_id"])
        for row in _parse_members(member_tree)
    }
    bioguide_ids.update(legislator_bioguide_ids or set())
    return SenateAmendmentProductionState(
        existing_roll_numbers=existing_roll_numbers or set(),
        existing_bill_keys=existing_bill_keys or set(),
        legislator_bioguide_ids=bioguide_ids,
        roll_numbers_with_interpretations=roll_numbers_with_interpretations or set(),
        roll_numbers_with_amendment_references=set(),
        amendment_reference_table_exists=False,
        migration_compatibility={
            "target_table_exists": False,
            "can_apply_cleanly_in_principle": True,
            "production_migration_applied": False,
        },
    )
