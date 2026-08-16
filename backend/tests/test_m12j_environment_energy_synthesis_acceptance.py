from __future__ import annotations

from copy import deepcopy

import pytest

from backend.app.etl.full_record_synthesis_decisions import (
    SynthesisDecisionError,
    seal,
    validate_authority,
    validate_implementation,
)
from backend.scripts.build_m12j_environment_energy_synthesis_acceptance import (
    build,
    build_authority,
    build_implementation,
    preflight,
)
from scripts.validate_m12j_environment_energy_synthesis_acceptance import validate


def inputs():
    package, template, behavioral_authority, behavioral_implementation = preflight()
    authority = build_authority(package, template)
    implementation = build_implementation(
        package,
        template,
        authority,
        behavioral_authority,
        behavioral_implementation,
    )
    return (
        package,
        template,
        behavioral_authority,
        behavioral_implementation,
        authority,
        implementation,
    )


def test_m12j_build_and_independent_validator_pass() -> None:
    assert build(check=True)["decision_accounting"]["accept_candidate_as_written"] == 1
    assert validate()["historical_m11j_byte_compatibility"] == "pass"


def test_exact_decision_has_no_bounded_revision() -> None:
    package, template, _, _, authority, _ = inputs()
    decision = authority["subject"]["synthesis_decisions"][0]
    assert decision["decision"] == "accept_candidate_as_written"
    assert decision["bounded_revision"] is None
    assert (
        validate_authority(authority, package=package, decision_template=template)[
            "accept_candidate_as_written"
        ]
        == 1
    )


def test_candidate_content_drift_fails_closed() -> None:
    (
        package,
        template,
        behavioral_authority,
        behavioral_implementation,
        authority,
        implementation,
    ) = inputs()
    mutated = deepcopy(implementation)
    mutated["subject"]["implementation_records"][0]["implemented_synthesis_content"][
        "unresolved_ambiguity"
    ] = "cleaned up"
    mutated["subject"]["implementation_records"][0] = seal(
        mutated["subject"]["implementation_records"][0], "record_subject_sha256"
    )
    mutated = seal(mutated, "implementation_subject_sha256")
    with pytest.raises(SynthesisDecisionError):
        validate_implementation(
            mutated,
            authority=authority,
            package=package,
            decision_template=template,
            accepted_behavioral_semantic_ir_authority=behavioral_authority,
            accepted_behavioral_semantic_ir_implementation=behavioral_implementation,
        )


def test_unused_non_directional_accounting_cannot_disappear() -> None:
    (
        package,
        template,
        behavioral_authority,
        behavioral_implementation,
        authority,
        implementation,
    ) = inputs()
    mutated = deepcopy(implementation)
    del mutated["subject"]["accepted_episode_disposition_accounting"][
        "unused_non_directional_evidence_episode_count"
    ]
    mutated = seal(mutated, "implementation_subject_sha256")
    with pytest.raises(SynthesisDecisionError):
        validate_implementation(
            mutated,
            authority=authority,
            package=package,
            decision_template=template,
            accepted_behavioral_semantic_ir_authority=behavioral_authority,
            accepted_behavioral_semantic_ir_implementation=behavioral_implementation,
        )


def test_legacy_and_generic_behavioral_bindings_are_mutually_exclusive() -> None:
    (
        package,
        template,
        behavioral_authority,
        behavioral_implementation,
        authority,
        implementation,
    ) = inputs()
    mutated = deepcopy(implementation)
    mutated["subject"]["m11h_authority_binding"] = deepcopy(
        mutated["subject"]["accepted_behavioral_semantic_ir_authority_binding"]
    )
    mutated = seal(mutated, "implementation_subject_sha256")
    with pytest.raises(SynthesisDecisionError):
        validate_implementation(
            mutated,
            authority=authority,
            package=package,
            decision_template=template,
            accepted_behavioral_semantic_ir_authority=behavioral_authority,
            accepted_behavioral_semantic_ir_implementation=behavioral_implementation,
        )


def test_incomplete_behavioral_lineage_fails_closed() -> None:
    (
        package,
        template,
        behavioral_authority,
        behavioral_implementation,
        authority,
        implementation,
    ) = inputs()
    mutated = deepcopy(implementation)
    mutated["subject"]["implementation_records"][0][
        "behavioral_proposition_lineage"
    ].pop()
    mutated["subject"]["implementation_records"][0] = seal(
        mutated["subject"]["implementation_records"][0], "record_subject_sha256"
    )
    mutated = seal(mutated, "implementation_subject_sha256")
    with pytest.raises(SynthesisDecisionError):
        validate_implementation(
            mutated,
            authority=authority,
            package=package,
            decision_template=template,
            accepted_behavioral_semantic_ir_authority=behavioral_authority,
            accepted_behavioral_semantic_ir_implementation=behavioral_implementation,
        )
