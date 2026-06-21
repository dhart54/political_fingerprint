import copy
import json
import sys
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.analysis.house_comparable_families import (  # noqa: E402
    ARTIFACT_VERSION,
    DEFAULT_ARTIFACT_PATH,
    EXPECTED_TOTALS,
    ComparableFamilyArtifactError,
    load_house_comparable_family_artifact,
    validate_artifact_payload,
)


def artifact_payload() -> dict:
    return json.loads(DEFAULT_ARTIFACT_PATH.read_text(encoding="utf-8"))


def test_loads_expected_artifact_and_validates_version_metadata() -> None:
    artifact = load_house_comparable_family_artifact()

    assert artifact.artifact_version == ARTIFACT_VERSION
    assert artifact.totals["target_interpreted_roll_calls"] == EXPECTED_TOTALS["target_interpreted_roll_calls"]
    assert artifact.recommendations["product_framing_recommendation"] == "Record Across Congresses"


def test_missing_artifact_fails() -> None:
    with pytest.raises(ComparableFamilyArtifactError, match="not found"):
        load_house_comparable_family_artifact(REPO_ROOT / "docs" / "derived" / "missing_house_family_artifact.json")


def test_artifact_version_mismatch_fails() -> None:
    payload = artifact_payload()
    payload["artifact_version"] = "wrong-version"

    with pytest.raises(ComparableFamilyArtifactError, match="Unexpected artifact version"):
        validate_artifact_payload(payload)


def test_required_metadata_validation_fails_when_missing() -> None:
    payload = artifact_payload()
    del payload["recommendations"]

    with pytest.raises(ComparableFamilyArtifactError, match="Missing required top-level key"):
        validate_artifact_payload(payload)


def test_non_authorization_flags_are_required() -> None:
    payload = artifact_payload()
    payload["explicit_non_authorization"]["does_not_authorize_behavioral_movement_claims"] = False

    with pytest.raises(ComparableFamilyArtifactError, match="non-authorization"):
        validate_artifact_payload(payload)


def test_invalid_comparability_status_fails() -> None:
    payload = artifact_payload()
    payload["families"][0]["comparability_status"] = "broad_domain_overlap"

    with pytest.raises(ComparableFamilyArtifactError, match="invalid comparability status"):
        validate_artifact_payload(payload)


def test_family_lookup_by_id_and_roll_call_ids_by_congress() -> None:
    artifact = load_house_comparable_family_artifact()
    family = artifact.family_by_id("nsf_annual_defense_authorization")

    assert family.family_name == "Annual defense authorization"
    assert family.roll_call_ids_by_congress[118]
    assert family.roll_call_ids_by_congress[119]
    assert artifact.roll_call_ids_by_congress("nsf_annual_defense_authorization") == family.roll_call_ids_by_congress


def test_family_filtering_by_domain_and_status() -> None:
    artifact = load_house_comparable_family_artifact()

    national_security = artifact.families_by_domain("NATIONAL_SECURITY_FOREIGN")
    direct = artifact.families_by_status("directly_comparable")

    assert {family.family_id for family in national_security} == {
        "nsf_annual_defense_authorization",
        "nsf_ukraine_assistance_restrictions",
        "nsf_war_powers_removal_resolutions",
    }
    assert len(direct) == EXPECTED_TOTALS["directly_comparable_common_families"]
    assert all(family.is_directly_comparable for family in direct)


def test_eligible_family_filters_split_direct_and_conditional() -> None:
    artifact = load_house_comparable_family_artifact()

    eligible = artifact.eligible_families()
    direct = artifact.directly_comparable_eligible_families()
    conditional = artifact.conditionally_comparable_eligible_families()

    assert len(eligible) == (
        EXPECTED_TOTALS["directly_comparable_common_families"]
        + EXPECTED_TOTALS["conditionally_comparable_common_families"]
    )
    assert len(direct) == EXPECTED_TOTALS["directly_comparable_common_families"]
    assert len(conditional) == EXPECTED_TOTALS["conditionally_comparable_common_families"]


def test_related_and_ungrouped_records_are_explicitly_ineligible() -> None:
    artifact = load_house_comparable_family_artifact()

    related = artifact.related_but_not_comparable_families()
    assert len(related) == EXPECTED_TOTALS["related_but_non_comparable_clusters"]
    assert all(not family.eligible_for_future_limited_record_across_congresses for family in related)
    assert artifact.ungrouped.comparability_status == "ungrouped"
    assert artifact.ungrouped.eligible_for_future_limited_record_across_congresses is False
    assert artifact.ungrouped.roll_call_count == EXPECTED_TOTALS["ungrouped_roll_calls"]


def test_direct_and_conditional_families_preserve_caveats() -> None:
    artifact = load_house_comparable_family_artifact()

    for family in artifact.eligible_families():
        assert family.caveats_and_limitations
        assert family.governing_question
        assert family.inclusion_criteria
        assert family.exclusion_criteria


def test_accessor_output_has_no_generated_continuity_change_or_movement_fields() -> None:
    artifact = load_house_comparable_family_artifact()
    serialized = json.dumps(artifact, default=lambda value: value.__dict__, sort_keys=True).lower()

    assert "movement_label" not in serialized
    assert "changed_position" not in serialized
    assert "ideological_movement_label" not in serialized
    assert "behavioral_movement_label" not in serialized
    assert "causal_claim_label" not in serialized


def test_generated_movement_field_fails_validation() -> None:
    payload = copy.deepcopy(artifact_payload())
    payload["families"][0]["movement_label"] = "changed"

    with pytest.raises(ComparableFamilyArtifactError, match="forbidden"):
        validate_artifact_payload(payload)
