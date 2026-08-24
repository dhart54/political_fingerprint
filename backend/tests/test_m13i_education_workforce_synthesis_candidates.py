from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.etl.full_record_synthesis_candidates import (
    SynthesisCandidateError,
    compile_synthesis_candidate_package,
)
from backend.scripts.build_m13h_education_workforce_semantic_ir_acceptance import (
    AUTHORITY_PATH,
    IMPLEMENTATION_PATH,
)
from backend.scripts.build_m13i_education_workforce_synthesis_candidates import (
    PACKAGE_ID,
    PROPOSITION_ACCOUNTING,
    PROPOSITION_IDS,
    build,
)
from scripts.validate_m13i_education_workforce_synthesis_candidates import validate


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compile_package(*, definitions: list[dict], accounting: list[dict]) -> dict:
    return compile_synthesis_candidate_package(
        authority=load(AUTHORITY_PATH),
        implementation=load(IMPLEMENTATION_PATH),
        candidate_definitions=definitions,
        proposition_accounting=accounting,
        legacy_binding_names=False,
        subject={
            "artifact_id": f"{PACKAGE_ID}:synthetic",
            "member_bioguide_id": "F000477",
            "member_slug": "leg_valerie_p_foushee",
            "issue_id": "EDUCATION_WORKFORCE",
            "congress": 119,
            "chamber": "House",
            "base_binding": {},
            "accepted_behavioral_semantic_ir_file_bindings": {},
            "source_authority_boundary": "Accepted M13H IR only.",
        },
    )


def test_m13i_build_and_independent_validator_pass() -> None:
    assert build(check=True)["candidate_count"] == 0
    result = validate()
    assert result["status"] == "valid"
    assert set(result["intentionally_standalone_proposition_ids"]) == set(
        PROPOSITION_IDS
    )


def test_explicit_zero_candidate_state_accounts_for_both_propositions() -> None:
    package = compile_package(definitions=[], accounting=PROPOSITION_ACCOUNTING)
    assert package["subject"]["synthesis_candidate_count"] == 0
    assert package["subject"]["proposition_accounting_counts"] == {
        "intentionally_standalone_no_safe_synthesis": 2
    }


def test_mixed_notable_cannot_become_directional_support() -> None:
    definition = {
        "synthesis_candidate_id": "unsafe-directional-inflation",
        "semantic_role": "synthesis",
        "synthesis_type": "uniform_direction",
        "direction": "opposition",
        "conclusion_relevance": "primary",
        "proposition": "Unsafe proposed synthesis.",
        "inputs": [
            {
                "proposition_id": PROPOSITION_IDS[0],
                "relationship_role": "primary_support",
                "concise_input_summary": "Bounded funding-restriction pattern.",
            },
            {
                "proposition_id": PROPOSITION_IDS[1],
                "relationship_role": "primary_support",
                "concise_input_summary": "Mixed H.R. 1048 notable.",
            },
        ],
        "relationship_basis": {
            "basis_type": "unsafe_topic_grouping",
            "semantic_relationship": "Purported shared foreign-influence topic.",
            "topic_similarity_only": False,
        },
        "relationship_rationale": "Synthetic adversarial case.",
        "why_synthesis_not_topic_grouping": "Synthetic adversarial claim.",
        "material_limitations": ["Mixed input cannot establish direction."],
        "competing_interpretation": "Keep both standalone.",
        "unresolved_ambiguity": "None.",
        "prohibited_inferences": ["general policy position"],
    }
    with pytest.raises(SynthesisCandidateError, match="direction differs"):
        compile_package(definitions=[definition], accounting=PROPOSITION_ACCOUNTING)


def test_raw_hr1005_evidence_cannot_enter_synthesis() -> None:
    definition = {
        "synthesis_candidate_id": "unsafe-raw-evidence",
        "semantic_role": "synthesis",
        "synthesis_type": "no_common_throughline",
        "direction": "mixed",
        "conclusion_relevance": "limiting",
        "proposition": "Unsafe raw-evidence candidate.",
        "evidence_episode_ids": ["single-119-hr-1005-1-312"],
        "inputs": [],
        "relationship_basis": {
            "basis_type": "none",
            "semantic_relationship": "None.",
            "topic_similarity_only": False,
        },
        "relationship_rationale": "Unsafe.",
        "why_synthesis_not_topic_grouping": "Unsafe.",
        "material_limitations": [],
        "competing_interpretation": "None.",
        "unresolved_ambiguity": "None.",
        "prohibited_inferences": [],
    }
    with pytest.raises(SynthesisCandidateError, match="supplied directly"):
        compile_package(definitions=[definition], accounting=PROPOSITION_ACCOUNTING)


def test_incomplete_standalone_accounting_is_rejected() -> None:
    with pytest.raises(SynthesisCandidateError, match="accounting differs"):
        compile_package(definitions=[], accounting=PROPOSITION_ACCOUNTING[:1])
