from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from backend.app.etl.full_record_behavioral_semantic_ir_decisions import (
    BehavioralSemanticIRDecisionError,
    validate_authority,
    validate_implementation,
)
from backend.scripts.build_m13h_education_workforce_semantic_ir_acceptance import (
    ACTION_IMPLEMENTATION_PATH,
    AUTHORITY_PATH,
    AUTHORITY_SCHEMA_PATH,
    CANDIDATE_PATH,
    EPISODE_AUTHORITY_PATH,
    EPISODE_IMPLEMENTATION_PATH,
    IMPLEMENTATION_PATH,
    IMPLEMENTATION_SCHEMA_PATH,
    build,
)
from scripts.validate_m13h_education_workforce_semantic_ir_acceptance import validate


ROOT = Path(__file__).resolve().parents[2]
M11H_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_national_security_foreign_119_v1"
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def inputs() -> tuple[dict, dict, dict, dict, dict, dict]:
    return (
        load(CANDIDATE_PATH),
        load(AUTHORITY_PATH),
        load(IMPLEMENTATION_PATH),
        load(EPISODE_AUTHORITY_PATH),
        load(EPISODE_IMPLEMENTATION_PATH),
        load(ACTION_IMPLEMENTATION_PATH),
    )


def test_m13h_build_and_independent_validator_pass() -> None:
    assert build(check=True)["accepted_proposition_count"] == 2
    result = validate()
    assert result["status"] == "pass"
    assert result["episode_dispositions"]["unused_non_directional_evidence"] == 1


def test_generic_schemas_accept_historical_m11h_and_m13h() -> None:
    authority_schema = load(AUTHORITY_SCHEMA_PATH)
    implementation_schema = load(IMPLEMENTATION_SCHEMA_PATH)
    Draft7Validator(authority_schema).validate(load(AUTHORITY_PATH))
    Draft7Validator(implementation_schema).validate(load(IMPLEMENTATION_PATH))
    Draft7Validator(authority_schema).validate(
        load(M11H_ROOT / "human_behavioral_semantic_ir_authority.json")
    )
    Draft7Validator(implementation_schema).validate(
        load(M11H_ROOT / "behavioral_semantic_ir_decision_implementation.json")
    )


def test_changed_reviewed_proposition_is_rejected() -> None:
    candidate, authority, *_ = inputs()
    changed = deepcopy(authority)
    changed["subject"]["proposition_decisions"][0]["candidate_direction"] = "support"
    with pytest.raises(BehavioralSemanticIRDecisionError):
        validate_authority(changed, candidate=candidate)


def test_unused_non_directional_disposition_cannot_be_collapsed() -> None:
    (
        candidate,
        authority,
        implementation,
        episode_authority,
        episode_impl,
        action_impl,
    ) = inputs()
    changed = deepcopy(implementation)
    row = next(
        row
        for row in changed["subject"]["accepted_episode_disposition_ledger"]
        if row["episode_id"] == "single-119-hr-1005-1-312"
    )
    row["disposition"] = "no_safe_higher_level_behavioral_proposition"
    with pytest.raises(BehavioralSemanticIRDecisionError):
        validate_implementation(
            changed,
            authority=authority,
            candidate=candidate,
            accepted_episode_authority=episode_authority,
            accepted_episode_implementation=episode_impl,
            accepted_action_interpretation_implementation=action_impl,
        )


def test_contrast_or_no_safe_episode_cannot_enter_accepted_evidence() -> None:
    (
        candidate,
        authority,
        implementation,
        episode_authority,
        episode_impl,
        action_impl,
    ) = inputs()
    changed = deepcopy(implementation)
    record = changed["subject"]["implementation_records"][0]
    record["evidence_lineage"].append(
        {
            "episode_id": "single-119-hr-1005-1-312",
            "episode_record_id": "invented",
            "episode_record_subject_sha256": "invented",
            "member_direction": "non_directional_not_voting",
            "accepted_action_lineage": [],
        }
    )
    with pytest.raises(BehavioralSemanticIRDecisionError):
        validate_implementation(
            changed,
            authority=authority,
            candidate=candidate,
            accepted_episode_authority=episode_authority,
            accepted_episode_implementation=episode_impl,
            accepted_action_interpretation_implementation=action_impl,
        )
