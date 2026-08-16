from __future__ import annotations

from copy import deepcopy

import pytest

from backend.app.etl.full_record_public_wording_candidates import (
    PublicWordingCandidateError,
    seal,
    validate_public_wording_candidate_package,
)
from backend.scripts.build_m12k_environment_energy_public_wording_candidates import (
    build,
    build_package,
    preflight,
)
from scripts.validate_m12k_environment_energy_public_wording_candidates import validate


def inputs():
    h_authority, h_implementation, j_authority, j_implementation = preflight()
    package = build_package(
        h_authority, h_implementation, j_authority, j_implementation
    )
    return package, h_authority, h_implementation, j_authority, j_implementation


def validate_package(
    package, h_authority, h_implementation, j_authority, j_implementation
):
    return validate_public_wording_candidate_package(
        package,
        behavioral_authority=h_authority,
        behavioral_implementation=h_implementation,
        synthesis_authority=j_authority,
        synthesis_implementation=j_implementation,
    )


def test_build_and_independent_validator_pass() -> None:
    assert build(check=True)["wording_item_accounting"] == {
        "issue_overview": 1,
        "synthesis": 1,
        "repeated_pattern": 3,
    }
    assert validate()["historical_m11k_byte_compatibility"] == "pass"


def test_zero_blocked_actions_and_generic_bindings() -> None:
    package, *_ = inputs()
    subject = package["subject"]
    assert subject["blocked_action_boundaries"] == []
    assert subject["blocked_actions"] == []
    assert "behavioral_semantic_ir_authority_binding" in subject
    assert "synthesis_authority_binding" in subject
    assert "m11h_authority_binding" not in subject


def test_all_five_items_keep_direction_in_behavioral_sentence() -> None:
    package, *_ = inputs()
    for item in package["subject"]["wording_items"]:
        assert item["direction_display"] is None
        assert "opposed congressional efforts to overturn" in item["primary_sentence"]
        assert item["semantic_guard"]["raw_yea_nay_maps_to_direction"] is False


def test_raw_vote_cannot_become_wording_authority() -> None:
    package, h_authority, h_implementation, j_authority, j_implementation = inputs()
    mutated = deepcopy(package)
    mutated["subject"]["wording_definitions"][0]["semantic_guard"][
        "raw_yea_nay_maps_to_direction"
    ] = True
    mutated = seal(mutated, "public_wording_candidate_package_subject_sha256")
    with pytest.raises(PublicWordingCandidateError):
        validate_package(
            mutated, h_authority, h_implementation, j_authority, j_implementation
        )


def test_limitation_cannot_disappear() -> None:
    package, h_authority, h_implementation, j_authority, j_implementation = inputs()
    mutated = deepcopy(package)
    mutated["subject"]["wording_definitions"][1]["limitation_treatments"].pop()
    mutated = seal(mutated, "public_wording_candidate_package_subject_sha256")
    with pytest.raises(PublicWordingCandidateError):
        validate_package(
            mutated, h_authority, h_implementation, j_authority, j_implementation
        )
