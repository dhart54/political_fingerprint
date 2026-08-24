from __future__ import annotations

from copy import deepcopy

import pytest

from backend.app.etl.full_record_public_wording_candidates import (
    PublicWordingCandidateError,
    seal,
    validate_public_wording_candidate_package,
)
from backend.scripts.build_m13k_education_workforce_public_wording_candidates import (
    build,
    build_package,
    preflight,
)
from scripts.validate_m13k_education_workforce_public_wording_candidates import validate


def inputs():
    sources = preflight()
    return build_package(*sources), *sources


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
        "repeated_pattern": 1,
        "notable_choice": 1,
    }
    assert validate()["no_synthesis_card"] is True


def test_no_synthesis_surface_or_source_exists() -> None:
    package, *_ = inputs()
    items = package["subject"]["wording_items"]
    assert all(item["surface"] != "synthesis" for item in items)
    assert all(
        binding["source_kind"] == "behavioral"
        for item in items
        for binding in item["semantic_source_bindings"]
    )
    assert package["subject"]["source_accounting"]["synthesis_record_count"] == 0


def test_overview_keeps_findings_separate() -> None:
    package, *_ = inputs()
    overview = next(
        row
        for row in package["subject"]["wording_items"]
        if row["surface"] == "issue_overview"
    )
    assert "Separately" in overview["primary_sentence"]
    assert "not one overall position" in overview["secondary_clarification"]
    assert overview["direction_display"] is None


def test_pattern_title_preserves_relationships_or_support_scope() -> None:
    package, *_ = inputs()
    pattern = next(
        row
        for row in package["subject"]["wording_items"]
        if row["surface"] == "repeated_pattern"
    )
    assert pattern["public_title"].endswith("relationships or support")


def test_public_evidence_labels_do_not_expose_acceptance_status() -> None:
    package, *_ = inputs()
    assert all(
        "accepted" not in row["evidence_count_label"].lower()
        for row in package["subject"]["wording_items"]
    )


def test_mixed_notable_does_not_become_directional_pattern() -> None:
    package, *_ = inputs()
    notable = next(
        row
        for row in package["subject"]["wording_items"]
        if row["surface"] == "notable_choice"
    )
    assert notable["direction_display"] == {"label": "Mixed", "symbol": "±"}
    assert "distinct whole" in notable["primary_sentence"]
    assert (
        "does not show opposition to the accepted amendment"
        in notable["secondary_clarification"]
    )
    assert (
        notable["wording_item_subject_sha256"]
        == "9a5dd2ddbf54b0295b1df89b0197790f89f898bc41e36112aa2f50a726675ca2"
    )


def test_fake_synthesis_surface_is_rejected() -> None:
    package, h_authority, h_implementation, j_authority, j_implementation = inputs()
    mutated = deepcopy(package)
    mutated["subject"]["wording_definitions"][0]["surface"] = "synthesis"
    mutated = seal(mutated, "public_wording_candidate_package_subject_sha256")
    with pytest.raises(PublicWordingCandidateError):
        validate_package(
            mutated, h_authority, h_implementation, j_authority, j_implementation
        )


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
