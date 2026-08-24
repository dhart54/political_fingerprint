from __future__ import annotations

import json

from scripts.foushee_environment_energy_publication_preparation import (
    canonical_file_sha256,
)
from scripts.finalize_m12n_environment_energy_activation_v3 import (
    ARTIFACT_IDS,
    BATCH_ID,
    CURRENT_STATE_PATH,
    EXPECTED_AFTER,
    SUCCESS_RECEIPT_PATH,
    validate_files as validate_activation_closeout,
)
from scripts.materialize_m12n_environment_energy_activation_authority import (
    FAILED_RECEIPT_PATH as HISTORICAL_FAILED_RECEIPT_PATH,
    POSITIVE_AUTHORITY_PATH as HISTORICAL_AUTHORITY_PATH,
)
from scripts.materialize_m12n_environment_energy_activation_authority_v3 import (
    DECISION_RECORDED_AT_UTC,
    MATERIALIZATION_RECEIPT_PATH,
    POSITIVE_AUTHORITY_PATH,
    RATIFIED_PROSPECTIVE_SUBJECT_SHA256,
    validate_files as validate_v3_materialization,
)


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v3_authority_adds_only_ratified_decision_timestamp() -> None:
    authority, receipt = validate_v3_materialization()
    stripped = dict(authority["subject"])
    assert stripped.pop("decision_recorded_at_utc") == DECISION_RECORDED_AT_UTC
    assert receipt["subject"]["timestamp_only_parity"] == {
        "removed_field": "decision_recorded_at_utc",
        "removed_value": DECISION_RECORDED_AT_UTC,
        "reproduces_ratified_prospective_subject": True,
        "stripped_subject_sha256": RATIFIED_PROSPECTIVE_SUBJECT_SHA256,
    }
    assert authority["immutable"] is True
    assert authority["accepted"] is True
    assert authority["sealed"] is True


def test_v3_materialization_is_distinct_from_failed_v2_history() -> None:
    authority, _receipt = validate_v3_materialization()
    historical = _load(HISTORICAL_AUTHORITY_PATH)
    assert POSITIVE_AUTHORITY_PATH != HISTORICAL_AUTHORITY_PATH
    assert (
        authority["activation_authority_subject_sha256"]
        != historical["activation_authority_subject_sha256"]
    )
    assert canonical_file_sha256(HISTORICAL_AUTHORITY_PATH) == (
        "38109df86271987e994502e2534923046ce0b0ffa97e4c334d97ec0535838408"
    )
    assert canonical_file_sha256(HISTORICAL_FAILED_RECEIPT_PATH) == (
        "205e56488898e168fd842be1b4afe8cc40a03e17efe635e49e8eb5eafa5eff99"
    )


def test_success_receipt_closes_exact_graph_and_live_contract() -> None:
    receipt, state = validate_activation_closeout()
    subject = receipt["subject"]
    assert subject["activation_survived_postcheck"] is True
    assert subject["rollback"]["executed"] is False
    assert subject["production_apply"]["batch_id"] == BATCH_ID
    assert subject["production_apply"]["artifact_ids"] == ARTIFACT_IDS
    assert subject["production_apply"]["post_write_counts"] == EXPECTED_AFTER
    assert subject["idempotent_second_apply"]["already_applied"] is True
    assert subject["live_presentation_verification"]["scope_tiers"] == {
        "119": "reviewed_conclusion",
        "all": "reviewed_conclusion",
        "118": "receipts_only",
    }
    evidence = subject["live_environment_evidence_verification"]
    assert evidence["119"]["row_count"] == 63
    assert evidence["all"]["governed_119_row_count"] == 63
    assert evidence["118"]["governed_119_row_count"] == 0
    assert evidence["hr_6387"] == {
        "analytical_support_set_memberships": 0,
        "canonical_action_id": "house:119:2:136",
        "exact_choice_position_effect": "non_directional_not_voting",
        "present_in_119_and_all": True,
    }
    assert state["subject"]["environment_publication_active"] is True
    assert state["subject"]["production_counts"] == EXPECTED_AFTER
    assert state["subject"]["rollback_executed"] is False
    assert SUCCESS_RECEIPT_PATH.exists()
    assert CURRENT_STATE_PATH.exists()
    assert MATERIALIZATION_RECEIPT_PATH.exists()
