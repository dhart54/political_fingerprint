from __future__ import annotations

import json

from scripts.finalize_m13n_education_workforce_activation import (
    AUTHORITY_PATH,
    CURRENT_STATE_PATH,
    EXECUTION_PROOF_PATH,
    MATERIALIZATION_PATH,
    RECEIPT_PATH,
    validate_outputs,
)


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_m13n_successful_closeout_is_exact_and_deterministic() -> None:
    result = validate_outputs()
    authority = _load(AUTHORITY_PATH)
    materialization = _load(MATERIALIZATION_PATH)
    execution = _load(EXECUTION_PROOF_PATH)
    receipt = _load(RECEIPT_PATH)
    current = _load(CURRENT_STATE_PATH)

    assert authority["immutable"] is True
    assert authority["accepted"] is True
    assert authority["sealed"] is True
    assert "test_only_synthetic" not in authority
    assert materialization["subject"]["every_other_subject_field_identical"] is True
    assert execution["deployed_commit"] == execution["health_commit"]
    assert receipt["subject"]["final_counts"] == {
        "batches": 7,
        "artifacts": 155,
        "relationships": 165,
        "publication_registry": 4,
    }
    assert receipt["subject"]["idempotent_second_apply"]["already_applied"] is True
    assert receipt["subject"]["rollback"]["executed"] is False
    assert receipt["subject"]["hr1005_proof"] == {
        "canonical_action_id": "house:119:1:312",
        "member_action": "Not_Voting",
        "exact_choice_position_effect": "non_directional_not_voting",
        "directional_analytical_memberships": 0,
    }
    assert current["subject"]["status"] == "successfully_activated"
    assert result["receipt_subject_sha256"] == receipt["receipt_subject_sha256"]
    assert (
        result["current_state_subject_sha256"]
        == current["current_state_subject_sha256"]
    )
