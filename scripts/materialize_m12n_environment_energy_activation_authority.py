from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.editorial_artifacts.bundle import semantic_hash  # noqa: E402
from app.editorial_presentations.environment_integration_candidate import (  # noqa: E402
    load_environment_site_integration_candidate,
)
from app.editorial_presentations.site_publication import (  # noqa: E402
    ACTIVATION_AUTHORITY_SCHEMA_VERSION,
    ENVIRONMENT_ACTIVATION_AUTHORITY_ID,
    validate_environment_positive_activation_authority,
)
from scripts.foushee_environment_energy_publication_preparation import (  # noqa: E402
    AUTHORITY_PATH,
    M12M_PATH,
    OUTPUT_ROOT,
    WRITE_SET_PATH,
    activation_write_set_binding,
    canonical_file_sha256,
)

sys.path.insert(0, str(ROOT / "scripts"))
from validate_m12n_publication_activation_ratification_candidate import (  # noqa: E402
    CANDIDATE_PATH,
    RATIFICATION_CANDIDATE_ID,
    validate_candidate,
)


DECISION_RECORDED_AT_UTC = "2026-08-17T01:12:42Z"
RATIFIED_PR = 159
RATIFIED_HEAD = "66083fc067756303be9ffd784841f6cb93cb7bae"
RATIFIED_CANDIDATE_FILE_SHA256 = (
    "fd3894248f3120e2cccf53b240b75dbdb05ab42e30315540199a07c7b5434757"
)
RATIFIED_PROSPECTIVE_SUBJECT_SHA256 = (
    "a0bf52b86d0078a947008b464f147023d8739f3665e36ea41b2213d95a8d8b5e"
)
POSITIVE_AUTHORITY_PATH = OUTPUT_ROOT / "positive_activation_authority.json"
MATERIALIZATION_RECEIPT_PATH = (
    OUTPUT_ROOT / "activation_ratification_materialization_receipt.json"
)
EXECUTION_PROOF_PATH = OUTPUT_ROOT / "execution_runtime_health_proof.json"
EXECUTION_PREFLIGHT_PATH = OUTPUT_ROOT / "execution_production_preflight.json"
FAILED_RECEIPT_PATH = OUTPUT_ROOT / "failed_activation_rollback_receipt.json"
FAILED_STATE_PATH = OUTPUT_ROOT / "failed_activation_current_state.json"


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _json_text(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def build_authority() -> dict:
    candidate = validate_candidate()
    if (
        candidate["artifact_id"] != RATIFICATION_CANDIDATE_ID
        or canonical_file_sha256(CANDIDATE_PATH) != RATIFIED_CANDIDATE_FILE_SHA256
        or candidate["prospective_authority_subject_sha256"]
        != RATIFIED_PROSPECTIVE_SUBJECT_SHA256
    ):
        raise ValueError("ratified M12N V2 candidate identity differs")

    subject = copy.deepcopy(candidate["prospective_authority_subject"])
    if "decision_recorded_at_utc" in subject:
        raise ValueError("prospective authority already contains decision timestamp")
    subject["decision_recorded_at_utc"] = DECISION_RECORDED_AT_UTC
    return {
        "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        "artifact_id": ENVIRONMENT_ACTIVATION_AUTHORITY_ID,
        "immutable": True,
        "accepted": True,
        "sealed": True,
        "subject": subject,
        "activation_authority_subject_sha256": semantic_hash(subject),
    }


def validate_authority(authority: dict) -> None:
    candidate = validate_candidate()
    stripped = copy.deepcopy(authority["subject"])
    if stripped.pop("decision_recorded_at_utc", None) != DECISION_RECORDED_AT_UTC:
        raise ValueError("materialized decision timestamp differs")
    if (
        stripped != candidate["prospective_authority_subject"]
        or semantic_hash(stripped) != RATIFIED_PROSPECTIVE_SUBJECT_SHA256
    ):
        raise ValueError("materialized authority differs beyond decision timestamp")

    write_set = _load(WRITE_SET_PATH)
    metadata = copy.deepcopy(write_set["publication_registry"]["publication_metadata"])
    metadata["activation_write_set_binding"] = activation_write_set_binding(write_set)
    validate_environment_positive_activation_authority(
        authority,
        candidate=load_environment_site_integration_candidate(M12M_PATH),
        candidate_authority=_load(AUTHORITY_PATH),
        metadata=metadata,
    )


def build_materialization_receipt(authority: dict) -> dict:
    stripped = copy.deepcopy(authority["subject"])
    stripped.pop("decision_recorded_at_utc")
    subject = {
        "ratified_candidate": {
            "artifact_id": RATIFICATION_CANDIDATE_ID,
            "file_sha256": RATIFIED_CANDIDATE_FILE_SHA256,
            "prospective_authority_subject_sha256": (
                RATIFIED_PROSPECTIVE_SUBJECT_SHA256
            ),
            "pull_request": RATIFIED_PR,
            "reviewed_head": RATIFIED_HEAD,
        },
        "ratification": {
            "decision": "approve_exact_publication_activation",
            "reviewer": "chatgpt:political_fingerprint_authority_thread",
            "reviewer_authority": "publication_activation_review_authority_v1",
            "decision_recorded_at_utc": DECISION_RECORDED_AT_UTC,
        },
        "materialized_authority": {
            "artifact_id": authority["artifact_id"],
            "subject_sha256": authority["activation_authority_subject_sha256"],
            "file_sha256": canonical_file_sha256(POSITIVE_AUTHORITY_PATH),
            "accepted": True,
            "sealed": True,
            "immutable": True,
        },
        "timestamp_only_parity": {
            "removed_field": "decision_recorded_at_utc",
            "removed_value": DECISION_RECORDED_AT_UTC,
            "stripped_subject_sha256": semantic_hash(stripped),
            "reproduces_ratified_prospective_subject": (
                stripped == _load(CANDIDATE_PATH)["prospective_authority_subject"]
                and semantic_hash(stripped) == RATIFIED_PROSPECTIVE_SUBJECT_SHA256
            ),
        },
    }
    return {
        "schema_version": "m12n_activation_ratification_materialization_receipt_v1",
        "receipt_id": (
            "activation-ratification-materialization-receipt:"
            "f000477:environment_energy:119:v1"
        ),
        "immutable": True,
        "subject": subject,
        "receipt_subject_sha256": semantic_hash(subject),
    }


def build_failed_activation_receipt(authority: dict) -> dict:
    proof = _load(EXECUTION_PROOF_PATH)
    preflight = _load(EXECUTION_PREFLIGHT_PATH)
    write_set = _load(WRITE_SET_PATH)
    subject = {
        "activation_authority": {
            "artifact_id": authority["artifact_id"],
            "subject_sha256": authority["activation_authority_subject_sha256"],
            "file_sha256": canonical_file_sha256(POSITIVE_AUTHORITY_PATH),
        },
        "ratification": {
            "candidate_artifact_id": RATIFICATION_CANDIDATE_ID,
            "candidate_file_sha256": RATIFIED_CANDIDATE_FILE_SHA256,
            "prospective_subject_sha256": RATIFIED_PROSPECTIVE_SUBJECT_SHA256,
            "decision_recorded_at_utc": DECISION_RECORDED_AT_UTC,
        },
        "execution_runtime_evidence": {
            "captured_at_utc": proof["captured_at_utc"],
            "subject_sha256": proof["runtime_health_proof_subject_sha256"],
            "file_sha256": canonical_file_sha256(EXECUTION_PROOF_PATH),
            "reviewed_runtime_manifest_sha256": proof[
                "reviewed_runtime_manifest_sha256"
            ],
            "deployed_commit": proof["deployed_commit"],
            "health_commit": proof["health_commit"],
        },
        "pre_write_state": {
            "captured_at_utc": preflight["captured_at_utc"],
            "preflight_subject_sha256": preflight["preflight_subject_sha256"],
            "preflight_file_sha256": canonical_file_sha256(EXECUTION_PREFLIGHT_PATH),
            "state_fingerprint_sha256": preflight["state_fingerprint_sha256"],
            "production_target_identity_sha256": preflight[
                "production_target_identity_sha256"
            ],
            "counts": preflight["counts"],
            "environment_registry_rows": [],
        },
        "production_write_set": {
            "artifact_id": write_set["artifact_id"],
            "subject_sha256": write_set["write_set_subject_sha256"],
            "file_sha256": canonical_file_sha256(WRITE_SET_PATH),
        },
        "attempt": {
            "dry_run": {
                "successful": True,
                "forced_rollback": True,
                "hypothetical_counts": write_set["expected_counts"]["after"],
            },
            "initial_apply": {
                "successful": True,
                "batch_id": 18,
                "artifact_ids": [233, 234, 235],
                "artifact_natural_keys": [
                    item["natural_key"] for item in write_set["artifacts"]
                ],
                "relationships": write_set["relationships"],
                "registry_insert": {
                    "member_bioguide_id": "F000477",
                    "issue_id": "ENVIRONMENT_ENERGY",
                    "presentation_natural_key": write_set["publication_registry"][
                        "presentation_natural_key"
                    ],
                },
                "post_write_counts": write_set["expected_counts"]["after"],
            },
            "idempotent_second_apply": {
                "successful": True,
                "already_applied": True,
                "additional_mutations": 0,
            },
        },
        "live_postcheck": {
            "presentation_api_successful": True,
            "presentation_surfaces": [
                {"title": "Environment & Energy", "supporting_action_count": 13},
                {
                    "title": "Congressional efforts to overturn agency decisions",
                    "supporting_action_count": 13,
                },
                {
                    "title": "California vehicle-emissions waivers",
                    "supporting_action_count": 2,
                },
                {
                    "title": "Appliance and commercial-equipment rules",
                    "supporting_action_count": 4,
                },
                {
                    "title": "Bureau of Land Management decisions",
                    "supporting_action_count": 7,
                },
            ],
            "direction_displays_present": False,
            "failed_endpoint": "/positions/ENVIRONMENT_ENERGY/evidence",
            "http_status_by_scope": {"119": 500, "all": 500, "118": 500},
            "classification": "live_receipt_evidence_failure",
            "production_activation_survived_postcheck": False,
        },
        "rollback": {
            "decision": "execute_authorized_exact_environment_rollback",
            "completed": True,
            "scope": "environment_owned_batch_graph_and_registry_row_only",
            "deleted": {
                "batches": 1,
                "artifacts": 3,
                "relationships": 2,
                "publication_registry": 1,
            },
            "restored_counts": write_set["expected_counts"]["before"],
            "restored_state_fingerprint_sha256": write_set["rollback"][
                "restore_state_fingerprint_sha256"
            ],
            "environment_registry_absent": True,
            "justice_registry_row_unchanged": write_set["rollback"][
                "justice_registry_row_unchanged"
            ],
            "national_security_registry_row_unchanged": write_set["rollback"][
                "national_security_registry_row_unchanged"
            ],
            "final_environment_state": "inactive_receipts_only",
        },
    }
    return {
        "schema_version": "m12n_failed_activation_rollback_receipt_v1",
        "receipt_id": (
            "failed-activation-rollback-receipt:f000477:environment_energy:119:v1"
        ),
        "immutable": True,
        "subject": subject,
        "receipt_subject_sha256": semantic_hash(subject),
    }


def build_failed_activation_state(receipt: dict) -> dict:
    subject = {
        "activation_attempted": True,
        "activation_survived_postcheck": False,
        "rollback_completed": True,
        "environment_publication_active": False,
        "environment_selector_state": {
            "119": "receipts_only",
            "all": "receipts_only",
            "118": "receipts_only",
        },
        "blocking_runtime_defect": "active_environment_receipt_evidence_dispatch",
        "failed_activation_receipt_binding": {
            "receipt_id": receipt["receipt_id"],
            "subject_sha256": receipt["receipt_subject_sha256"],
            "file_sha256": canonical_file_sha256(FAILED_RECEIPT_PATH),
        },
        "sealed_authority_reuse": "prohibited_after_runtime_repair",
    }
    return {
        "schema_version": "m12n_failed_activation_current_state_v1",
        "artifact_id": "failed-activation-current-state:f000477:environment_energy:119:v1",
        "immutable": True,
        "subject": subject,
        "current_state_subject_sha256": semantic_hash(subject),
    }


def write_and_validate() -> tuple[dict, dict, dict, dict]:
    authority = build_authority()
    POSITIVE_AUTHORITY_PATH.write_text(
        _json_text(authority), encoding="utf-8", newline="\n"
    )
    validate_authority(authority)
    receipt = build_materialization_receipt(authority)
    MATERIALIZATION_RECEIPT_PATH.write_text(
        _json_text(receipt), encoding="utf-8", newline="\n"
    )
    failed_receipt = build_failed_activation_receipt(authority)
    FAILED_RECEIPT_PATH.write_text(
        _json_text(failed_receipt), encoding="utf-8", newline="\n"
    )
    failed_state = build_failed_activation_state(failed_receipt)
    FAILED_STATE_PATH.write_text(
        _json_text(failed_state), encoding="utf-8", newline="\n"
    )
    return authority, receipt, failed_receipt, failed_state


def validate_files() -> tuple[dict, dict, dict, dict]:
    authority = _load(POSITIVE_AUTHORITY_PATH)
    validate_authority(authority)
    expected_receipt = build_materialization_receipt(authority)
    receipt = _load(MATERIALIZATION_RECEIPT_PATH)
    if receipt != expected_receipt:
        raise ValueError("ratification materialization receipt differs")
    failed_receipt = _load(FAILED_RECEIPT_PATH)
    if failed_receipt != build_failed_activation_receipt(authority):
        raise ValueError("failed activation rollback receipt differs")
    failed_state = _load(FAILED_STATE_PATH)
    if failed_state != build_failed_activation_state(failed_receipt):
        raise ValueError("failed activation current state differs")
    return authority, receipt, failed_receipt, failed_state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    authority, receipt, failed_receipt, failed_state = (
        write_and_validate() if args.write else validate_files()
    )
    print(
        json.dumps(
            {
                "status": "valid_sealed_activation_authority",
                "authority_subject_sha256": authority[
                    "activation_authority_subject_sha256"
                ],
                "authority_file_sha256": canonical_file_sha256(POSITIVE_AUTHORITY_PATH),
                "materialization_receipt_subject_sha256": receipt[
                    "receipt_subject_sha256"
                ],
                "materialization_receipt_file_sha256": canonical_file_sha256(
                    MATERIALIZATION_RECEIPT_PATH
                ),
                "prospective_subject_reproduced": True,
                "failed_activation_receipt_subject_sha256": failed_receipt[
                    "receipt_subject_sha256"
                ],
                "failed_activation_receipt_file_sha256": canonical_file_sha256(
                    FAILED_RECEIPT_PATH
                ),
                "failed_activation_state_subject_sha256": failed_state[
                    "current_state_subject_sha256"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
