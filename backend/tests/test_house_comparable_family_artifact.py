import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.house_comparable_family_artifact import (  # noqa: E402
    ARTIFACT_VERSION,
    EXPECTED_TOTALS,
    SCHEMA_VERSION,
    validate_artifact,
)


ARTIFACT_PATH = REPO_ROOT / "docs" / "derived" / "house_comparable_policy_question_families_v1.json"
SOURCE_AUDIT_PATH = REPO_ROOT / "docs" / "analysis" / "house_comparable_policy_question_families.json"

EXPECTED_FAMILY_IDS = [
    "eco_budget_reconciliation_process",
    "eco_government_funding_packages",
    "eco_small_business_finance_regulation",
    "env_critical_minerals_supply",
    "env_energy_permitting_fossil_infrastructure",
    "env_home_appliance_energy_rules",
    "env_hunting_fishing_access",
    "jps_federal_officer_service_weapons",
    "jps_fentanyl_scheduling_penalties",
    "jps_law_enforcement_safety_reporting",
    "jps_law_enforcement_support_resolutions",
    "jps_violent_offenders_pretrial_detention",
    "nsf_annual_defense_authorization",
    "nsf_ukraine_assistance_restrictions",
    "nsf_war_powers_removal_resolutions",
]


def load_artifact() -> dict:
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def load_source_audit() -> dict:
    return json.loads(SOURCE_AUDIT_PATH.read_text(encoding="utf-8"))


def test_artifact_schema_version_and_metadata_are_stable() -> None:
    artifact = load_artifact()

    assert artifact["artifact_version"] == ARTIFACT_VERSION
    assert artifact["schema_version"] == SCHEMA_VERSION
    assert artifact["source_basis"]["source_pull_request"] == 44
    assert artifact["source_basis"]["source_audit_commit"] == "0f0eac9811351d371ee0da50f9333b22cf8be53f"
    assert artifact["recommendations"]["product_framing_recommendation"] == "Record Across Congresses"
    assert artifact["explicit_non_authorization"]["does_not_authorize_continuity_change_claims"] is True


def test_family_ids_and_reconciliation_totals_match_pr44_audit() -> None:
    artifact = load_artifact()

    assert [family["family_id"] for family in artifact["families"]] == EXPECTED_FAMILY_IDS
    for key, expected in EXPECTED_TOTALS.items():
        assert artifact["totals"][key] == expected
    assert validate_artifact(artifact, load_source_audit()) == []


def test_comparable_families_are_common_and_related_families_are_not_eligible() -> None:
    artifact = load_artifact()

    for family in artifact["families"]:
        status = family["comparability_status"]
        if status in {"directly_comparable", "conditionally_comparable"}:
            assert family["roll_call_ids_by_congress"]["118"]
            assert family["roll_call_ids_by_congress"]["119"]
            assert family["eligible_for_future_limited_record_across_congresses"] is True
        if status == "related_but_not_comparable":
            assert family["eligible_for_future_limited_record_across_congresses"] is False


def test_roll_call_identity_preserves_chamber_congress_session_and_slot() -> None:
    artifact = load_artifact()

    for family in artifact["families"]:
        for congress, entries in family["roll_calls_by_congress"].items():
            for entry in entries:
                assert entry["chamber"] == "house"
                assert str(entry["congress"]) == congress
                assert entry["session"] is not None
                assert entry["rollcall_number"] is not None


def test_ungrouped_rows_are_excluded_from_future_eligibility() -> None:
    artifact = load_artifact()
    ungrouped = artifact["ungrouped"]

    assert ungrouped["comparability_status"] == "ungrouped"
    assert ungrouped["eligible_for_future_limited_record_across_congresses"] is False
    assert ungrouped["roll_call_count"] == EXPECTED_TOTALS["ungrouped_roll_calls"]


def test_artifact_has_no_generated_continuity_change_or_movement_labels() -> None:
    artifact_text = ARTIFACT_PATH.read_text(encoding="utf-8").lower()

    assert "continuity / change" not in artifact_text
    assert "movement_label" not in artifact_text
    assert "changed_position" not in artifact_text
    assert "ideological_movement_label" not in artifact_text
    assert "behavioral_movement_label" not in artifact_text
