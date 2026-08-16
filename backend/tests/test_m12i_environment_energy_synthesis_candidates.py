from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from backend.app.etl.full_record_synthesis_candidates import (
    SynthesisCandidateError,
    compile_synthesis_candidate_package,
    validate_synthesis_candidate_package,
)
from backend.scripts.build_m12h_environment_energy_semantic_ir_acceptance import (
    AUTHORITY_PATH,
    IMPLEMENTATION_PATH,
)
from backend.scripts.build_m12i_environment_energy_synthesis_candidates import (
    CANDIDATE_DEFINITIONS,
    PACKAGE_PATH,
    PACKAGE_SCHEMA_PATH,
    PROPOSITION_ACCOUNTING,
    PROPOSITION_IDS,
    build,
)
from scripts.validate_m12i_environment_energy_synthesis_candidates import validate


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_m12i_build_and_independent_validator_pass() -> None:
    assert build(check=True)["candidate_count"] == 1
    result = validate()
    assert result["status"] == "valid"
    assert result["unique_episode_count"] == 13
    assert result["intentionally_standalone_proposition_ids"] == []


def test_zero_candidate_fail_closed_package_is_valid() -> None:
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    accounting = [
        {
            "proposition_id": proposition_id,
            "accounting_role": "intentionally_standalone_no_safe_synthesis",
            "reason": "No accepted cross-proposition relationship survives review.",
        }
        for proposition_id in PROPOSITION_IDS
    ]
    package = compile_synthesis_candidate_package(
        authority=authority,
        implementation=implementation,
        candidate_definitions=[],
        proposition_accounting=accounting,
        legacy_binding_names=False,
        subject={
            "artifact_id": "synthetic-zero-candidate-package",
            "member_bioguide_id": "F000477",
            "member_slug": "leg_valerie_p_foushee",
            "issue_id": "ENVIRONMENT_ENERGY",
            "congress": 119,
            "chamber": "House",
            "base_binding": {},
            "accepted_behavioral_semantic_ir_file_bindings": {},
            "source_authority_boundary": "Accepted Behavioral Semantic IR only.",
        },
    )
    Draft7Validator(load(PACKAGE_SCHEMA_PATH)).validate(package)
    result = validate_synthesis_candidate_package(
        package, authority=authority, implementation=implementation
    )
    assert result["candidate_count"] == 0
    assert result["accounting_counts"] == {
        "intentionally_standalone_no_safe_synthesis": 3
    }


def test_nonzero_candidate_requires_two_accepted_inputs() -> None:
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    definition = deepcopy(CANDIDATE_DEFINITIONS[0])
    definition["inputs"] = definition["inputs"][:1]
    with pytest.raises(SynthesisCandidateError, match="distinct and plural"):
        compile_synthesis_candidate_package(
            authority=authority,
            implementation=implementation,
            candidate_definitions=[definition],
            proposition_accounting=PROPOSITION_ACCOUNTING,
            legacy_binding_names=False,
            subject={"artifact_id": "synthetic"},
        )


def test_raw_episode_or_action_evidence_cannot_enter_definition() -> None:
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    definition = deepcopy(CANDIDATE_DEFINITIONS[0])
    definition["evidence_episode_ids"] = ["single-119-hr-6387-2-136"]
    with pytest.raises(SynthesisCandidateError, match="supplied directly"):
        compile_synthesis_candidate_package(
            authority=authority,
            implementation=implementation,
            candidate_definitions=[definition],
            proposition_accounting=PROPOSITION_ACCOUNTING,
            legacy_binding_names=False,
            subject={"artifact_id": "synthetic"},
        )


def test_topic_only_or_ideological_synthesis_is_rejected() -> None:
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    topic_only = deepcopy(CANDIDATE_DEFINITIONS[0])
    topic_only["relationship_basis"]["topic_similarity_only"] = True
    with pytest.raises(SynthesisCandidateError, match="topic-only"):
        compile_synthesis_candidate_package(
            authority=authority,
            implementation=implementation,
            candidate_definitions=[topic_only],
            proposition_accounting=PROPOSITION_ACCOUNTING,
            legacy_binding_names=False,
            subject={"artifact_id": "synthetic"},
        )
    ideological = deepcopy(CANDIDATE_DEFINITIONS[0])
    ideological["proposition"] += " This establishes ideology."
    with pytest.raises(SynthesisCandidateError, match="prohibited"):
        compile_synthesis_candidate_package(
            authority=authority,
            implementation=implementation,
            candidate_definitions=[ideological],
            proposition_accounting=PROPOSITION_ACCOUNTING,
            legacy_binding_names=False,
            subject={"artifact_id": "synthetic"},
        )


def test_generated_package_uses_only_generic_binding_names() -> None:
    subject = load(PACKAGE_PATH)["subject"]
    assert "accepted_behavioral_semantic_ir_authority_binding" in subject
    assert "accepted_behavioral_semantic_ir_implementation_binding" in subject
    assert "accepted_behavioral_semantic_ir_file_bindings" in subject
    assert "m11h_authority_binding" not in subject
    assert "m11h_implementation_binding" not in subject
    assert "accepted_m11h_file_bindings" not in subject
