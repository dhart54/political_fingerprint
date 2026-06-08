from pathlib import Path
from xml.etree import ElementTree

from app.etl.senate_fact_import import (
    PHASE_14_APPROVAL_PHRASE,
    SenateProductionState,
    run_senate_fact_import,
    run_senate_fact_dry_run,
)
from app.etl.senate_xml_adapter import _parse_members


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "docs" / "review_packets" / "senate_vote_facts_expansion_manifest_phase_11.json"
PHASE_14_MANIFEST_PATH = REPO_ROOT / "docs" / "review_packets" / "senate_fact_only_expansion_manifest_phase_14.json"
SENATE_XML_DIR = REPO_ROOT / "backend" / "data_sources" / "senate_xml"


def test_senate_fact_dry_run_plans_manifest_fact_inserts_without_interpretations() -> None:
    result = run_senate_fact_dry_run(
        manifest_path=MANIFEST_PATH,
        senate_xml_dir=SENATE_XML_DIR,
        production_state=_local_production_state(),
        skip_existing=True,
    )

    assert result.candidate_roll_numbers == [
        97,
        150,
        151,
        161,
        162,
        169,
        191,
        206,
        207,
        222,
        223,
        224,
        228,
        231,
        232,
        236,
        239,
        276,
        277,
        278,
        279,
        280,
        281,
    ]
    assert result.planned_bill_inserts == 12
    assert result.planned_roll_call_inserts == 23
    assert result.planned_votes_cast_inserts == 2300
    assert result.planned_vote_context_inserts == 2300
    assert result.planned_vote_interpretation_inserts == 0
    assert result.planned_vote_interpretation_updates == 0
    assert result.planned_vote_interpretation_deletes == 0
    assert result.errors == []


def test_senate_fact_dry_run_fails_closed_for_existing_roll_without_skip() -> None:
    result = run_senate_fact_dry_run(
        manifest_path=MANIFEST_PATH,
        senate_xml_dir=SENATE_XML_DIR,
        production_state=_local_production_state(existing_roll_numbers={97}),
        skip_existing=False,
    )

    assert result.planned_roll_call_inserts == 22
    assert "Roll 97 is already present in production; pass explicit skip-existing behavior." in result.errors


def test_senate_fact_dry_run_skips_existing_roll_when_explicit() -> None:
    result = run_senate_fact_dry_run(
        manifest_path=MANIFEST_PATH,
        senate_xml_dir=SENATE_XML_DIR,
        production_state=_local_production_state(existing_roll_numbers={97}),
        skip_existing=True,
    )

    assert result.skipped_existing_roll_calls == [97]
    assert result.planned_roll_call_inserts == 22
    assert result.planned_votes_cast_inserts == 2200
    assert result.planned_vote_interpretation_inserts == 0
    assert result.errors == []


def test_senate_fact_dry_run_fails_closed_if_target_has_interpretation() -> None:
    result = run_senate_fact_dry_run(
        manifest_path=MANIFEST_PATH,
        senate_xml_dir=SENATE_XML_DIR,
        production_state=_local_production_state(roll_numbers_with_interpretations={97}),
        skip_existing=True,
    )

    assert result.planned_roll_call_inserts == 22
    assert "Roll 97 already has vote_interpretations rows; dry run fails closed." in result.errors


def test_senate_fact_dry_run_supports_phase_14_bounded_package() -> None:
    result = run_senate_fact_dry_run(
        manifest_path=PHASE_14_MANIFEST_PATH,
        senate_xml_dir=SENATE_XML_DIR,
        production_state=_local_production_state(),
        skip_existing=True,
    )

    assert len(result.candidate_roll_numbers) == 70
    assert result.planned_bill_inserts == 25
    assert result.planned_roll_call_inserts == 70
    assert result.planned_votes_cast_inserts == 7000
    assert result.planned_vote_context_inserts == 7000
    assert result.planned_vote_interpretation_inserts == 0
    assert result.planned_vote_interpretation_updates == 0
    assert result.planned_vote_interpretation_deletes == 0
    assert result.errors == []


def test_senate_fact_import_requires_exact_phase_14_approval_phrase_before_database_access() -> None:
    try:
        run_senate_fact_import(
            manifest_path=PHASE_14_MANIFEST_PATH,
            senate_xml_dir=SENATE_XML_DIR,
            approval_phrase=PHASE_14_APPROVAL_PHRASE.replace("Phase 14", "Phase XIV"),
            skip_existing=True,
        )
    except ValueError as error:
        assert "Phase 14 approval gate" in str(error)
    else:
        raise AssertionError("Phase 14 production import must require the exact approval phrase")


def _local_production_state(
    *,
    existing_roll_numbers: set[int] | None = None,
    roll_numbers_with_interpretations: set[int] | None = None,
) -> SenateProductionState:
    member_tree = ElementTree.parse(SENATE_XML_DIR / "members.xml")
    bioguide_ids = {
        str(row["bioguide_id"])
        for row in _parse_members(member_tree)
    }
    return SenateProductionState(
        existing_roll_numbers=existing_roll_numbers or set(),
        existing_bill_keys=set(),
        legislator_bioguide_ids=bioguide_ids,
        roll_numbers_with_interpretations=roll_numbers_with_interpretations or set(),
    )
