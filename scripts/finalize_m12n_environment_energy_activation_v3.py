from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT / "scripts"))

from app.editorial_artifacts.bundle import semantic_hash  # noqa: E402
from scripts.foushee_environment_energy_publication_preparation import (  # noqa: E402
    WRITE_SET_PATH,
    canonical_file_sha256,
)

from build_m12n_environment_energy_ratification_candidate_v3 import (  # noqa: E402
    OUTPUT_ROOT,
    RATIFICATION_CANDIDATE_ID,
    RATIFICATION_CANDIDATE_ID as V3_CANDIDATE_ID,
    validate_candidate,
)
from materialize_m12n_environment_energy_activation_authority_v3 import (  # noqa: E402
    MATERIALIZATION_RECEIPT_PATH,
    POSITIVE_AUTHORITY_PATH,
    RATIFIED_CANDIDATE_FILE_SHA256,
    RATIFIED_PROSPECTIVE_SUBJECT_SHA256,
    validate_files as validate_materialization,
)


EXECUTION_PROOF_PATH = OUTPUT_ROOT / "execution_runtime_health_proof.json"
EXECUTION_PREFLIGHT_PATH = OUTPUT_ROOT / "execution_production_preflight.json"
SUCCESS_RECEIPT_PATH = OUTPUT_ROOT / "successful_production_activation_receipt.json"
CURRENT_STATE_PATH = OUTPUT_ROOT / "activation_current_state.json"
CLOSEOUT_PATH = OUTPUT_ROOT / "activation_closeout.md"
HISTORICAL_ROOT = OUTPUT_ROOT.parent / "f000477_environment_energy_119_v1"
HISTORICAL_FAILED_RECEIPT_PATH = (
    HISTORICAL_ROOT / "failed_activation_rollback_receipt.json"
)
ACTIVATION_AT_UTC = "2026-08-24T01:37:40.815760+00:00"
VERIFICATION_COMPLETED_AT_UTC = "2026-08-24T01:39:05Z"
BATCH_ID = 20
ARTIFACT_IDS = [239, 240, 241]
EXPECTED_AFTER = {
    "batches": 6,
    "artifacts": 152,
    "relationships": 163,
    "publication_registry": 3,
}


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _json_text(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def build_success_receipt() -> dict:
    candidate = validate_candidate()
    authority, materialization = validate_materialization()
    proof = _load(EXECUTION_PROOF_PATH)
    preflight = _load(EXECUTION_PREFLIGHT_PATH)
    write_set = _load(WRITE_SET_PATH)
    if candidate["artifact_id"] != RATIFICATION_CANDIDATE_ID:
        raise ValueError("V3 candidate identity differs during activation closeout")
    subject = {
        "ratification_candidate": {
            "artifact_id": V3_CANDIDATE_ID,
            "file_sha256": RATIFIED_CANDIDATE_FILE_SHA256,
            "prospective_authority_subject_sha256": (
                RATIFIED_PROSPECTIVE_SUBJECT_SHA256
            ),
            "accepted": False,
            "sealed": False,
        },
        "sealed_activation_authority": {
            "artifact_id": authority["artifact_id"],
            "subject_sha256": authority["activation_authority_subject_sha256"],
            "file_sha256": canonical_file_sha256(POSITIVE_AUTHORITY_PATH),
        },
        "materialization_receipt": {
            "receipt_id": materialization["receipt_id"],
            "subject_sha256": materialization["receipt_subject_sha256"],
            "file_sha256": canonical_file_sha256(MATERIALIZATION_RECEIPT_PATH),
        },
        "stable_runtime": authority["subject"]["runtime_binding"],
        "execution_runtime_proof": {
            "captured_at_utc": proof["captured_at_utc"],
            "subject_sha256": proof["runtime_health_proof_subject_sha256"],
            "file_sha256": canonical_file_sha256(EXECUTION_PROOF_PATH),
            "reviewed_runtime_manifest_sha256": proof[
                "reviewed_runtime_manifest_sha256"
            ],
            "deployed_commit": proof["deployed_commit"],
            "health_commit": proof["health_commit"],
            "fresh_within_seconds": 1800,
        },
        "pre_write_production_state": {
            "captured_at_utc": preflight["captured_at_utc"],
            "preflight_subject_sha256": preflight["preflight_subject_sha256"],
            "preflight_file_sha256": canonical_file_sha256(EXECUTION_PREFLIGHT_PATH),
            "state_fingerprint_sha256": preflight["state_fingerprint_sha256"],
            "production_target_identity_sha256": preflight[
                "production_target_identity_sha256"
            ],
            "counts": preflight["counts"],
            "environment_registry_absent": True,
        },
        "production_write_set": {
            "artifact_id": write_set["artifact_id"],
            "subject_sha256": write_set["write_set_subject_sha256"],
            "file_sha256": canonical_file_sha256(WRITE_SET_PATH),
            "write_caps": write_set["write_caps"],
            "rollback": write_set["rollback"],
        },
        "dry_run": {
            "successful": True,
            "forced_rollback": True,
            "hypothetical_batch_id": 19,
            "hypothetical_artifact_ids": [236, 237, 238],
            "hypothetical_counts": EXPECTED_AFTER,
        },
        "production_apply": {
            "successful": True,
            "already_applied": False,
            "batch_id": BATCH_ID,
            "artifact_ids": ARTIFACT_IDS,
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
            "post_write_counts": EXPECTED_AFTER,
            "activation_at_utc": ACTIVATION_AT_UTC,
        },
        "idempotent_second_apply": {
            "successful": True,
            "already_applied": True,
            "additional_batches": 0,
            "additional_artifacts": 0,
            "additional_relationships": 0,
            "additional_registry_rows": 0,
        },
        "live_presentation_verification": {
            "http_status": 200,
            "scope_tiers": {
                "119": "reviewed_conclusion",
                "all": "reviewed_conclusion",
                "118": "receipts_only",
            },
            "surfaces": [
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
        },
        "live_positions_verification": {
            "http_status": 200,
            "environment": {
                "yea_count": 15,
                "nay_count": 47,
                "other_count": 1,
                "total_votes": 63,
                "recorded_votes": 62,
                "interpreted_support_count": 15,
                "interpreted_oppose_count": 47,
                "interpreted_other_count": 1,
                "interpreted_total": 63,
            },
            "national_security": {
                "yea_count": 39,
                "nay_count": 43,
                "other_count": 0,
                "total_votes": 82,
                "recorded_votes": 82,
                "interpreted_support_count": 39,
                "interpreted_oppose_count": 42,
                "interpreted_other_count": 0,
                "interpreted_total": 81,
            },
            "justice": {
                "yea_count": 6,
                "nay_count": 18,
                "other_count": 0,
                "total_votes": 24,
                "recorded_votes": 24,
                "interpreted_support_count": 2,
                "interpreted_oppose_count": 9,
                "interpreted_other_count": 0,
                "interpreted_total": 11,
            },
        },
        "live_environment_evidence_verification": {
            "119": {
                "http_status": 200,
                "row_count": 63,
                "governed_119_row_count": 63,
                "unique_119_action_count": 63,
                "all_governed_rows_have_receipt_projection": True,
            },
            "all": {
                "http_status": 200,
                "row_count": 97,
                "governed_119_row_count": 63,
                "unique_119_action_count": 63,
                "retained_prior_congress_row_count": 34,
                "duplicated_119_rows": 0,
            },
            "118": {
                "http_status": 200,
                "row_count": 34,
                "governed_119_row_count": 0,
            },
            "hr_6387": {
                "canonical_action_id": "house:119:2:136",
                "exact_choice_position_effect": "non_directional_not_voting",
                "present_in_119_and_all": True,
                "analytical_support_set_memberships": 0,
            },
        },
        "preservation": {
            "justice_registry_row": preflight["justice_registry_row"],
            "national_security_registry_row": preflight[
                "national_security_registry_row"
            ],
            "m12m_presentation_content_sha256": authority["subject"][
                "presentation_content_sha256"
            ],
        },
        "historical_failed_activation": {
            "receipt_subject_sha256": (
                "9dc3abeeb95d060d59d3df2e291772771ef758e6eb4bff2aec9ab80ae80745bf"
            ),
            "receipt_file_sha256": canonical_file_sha256(
                HISTORICAL_FAILED_RECEIPT_PATH
            ),
            "modified": False,
        },
        "rollback": {
            "authorized_contract_retained": True,
            "executed": False,
            "reason": "all production postchecks succeeded",
        },
        "verification_completed_at_utc": VERIFICATION_COMPLETED_AT_UTC,
        "activation_survived_postcheck": True,
    }
    return {
        "schema_version": "m12n_successful_production_activation_receipt_v3",
        "receipt_id": (
            "successful-production-activation-receipt:f000477:environment_energy:119:v3"
        ),
        "immutable": True,
        "subject": subject,
        "receipt_subject_sha256": semantic_hash(subject),
    }


def build_current_state(receipt: dict) -> dict:
    subject = {
        "activation_survived_postcheck": True,
        "environment_publication_active": True,
        "environment_selector_state": {
            "119": "reviewed_conclusion",
            "all": "reviewed_conclusion",
            "118": "receipts_only",
        },
        "production_counts": EXPECTED_AFTER,
        "production_graph": {
            "batch_id": BATCH_ID,
            "artifact_ids": ARTIFACT_IDS,
            "relationship_count": 2,
            "registry_row_count": 1,
        },
        "successful_activation_receipt_binding": {
            "receipt_id": receipt["receipt_id"],
            "subject_sha256": receipt["receipt_subject_sha256"],
            "file_sha256": canonical_file_sha256(SUCCESS_RECEIPT_PATH),
        },
        "rollback_executed": False,
        "justice_preserved": True,
        "national_security_preserved": True,
    }
    return {
        "schema_version": "m12n_activation_current_state_v3",
        "artifact_id": "activation-current-state:f000477:environment_energy:119:v3",
        "immutable": True,
        "subject": subject,
        "current_state_subject_sha256": semantic_hash(subject),
    }


def build_closeout(receipt: dict, state: dict) -> str:
    authority = receipt["subject"]["sealed_activation_authority"]
    proof = receipt["subject"]["execution_runtime_proof"]
    return f"""# M12N Environment & Energy V3 Activation Closeout

Environment & Energy is production-active. All production postchecks passed and
the authorized rollback was not executed.

- V3 authority subject: `{authority["subject_sha256"]}`
- V3 authority file: `{authority["file_sha256"]}`
- Execution proof subject: `{proof["subject_sha256"]}`
- Activated graph: batch `{BATCH_ID}`, artifacts `{", ".join(map(str, ARTIFACT_IDS))}`
- Production counts: `6 batches / 152 artifacts / 163 relationships / 3 registry rows`
- Successful receipt subject: `{receipt["receipt_subject_sha256"]}`
- Current-state subject: `{state["current_state_subject_sha256"]}`

Live presentations, positions, and Environment evidence passed at 119/all/118.
H.R. 6387 remains non-directional and outside every analytical support set.
Justice and National Security remain unchanged.
"""


def write_and_validate() -> tuple[dict, dict]:
    receipt = build_success_receipt()
    SUCCESS_RECEIPT_PATH.write_text(_json_text(receipt), encoding="utf-8", newline="\n")
    state = build_current_state(receipt)
    CURRENT_STATE_PATH.write_text(_json_text(state), encoding="utf-8", newline="\n")
    CLOSEOUT_PATH.write_text(
        build_closeout(receipt, state), encoding="utf-8", newline="\n"
    )
    return validate_files()


def validate_files() -> tuple[dict, dict]:
    receipt = _load(SUCCESS_RECEIPT_PATH)
    if receipt != build_success_receipt():
        raise ValueError("M12N V3 successful activation receipt differs")
    if receipt["receipt_subject_sha256"] != semantic_hash(receipt["subject"]):
        raise ValueError("M12N V3 successful activation receipt digest differs")
    state = _load(CURRENT_STATE_PATH)
    if state != build_current_state(receipt):
        raise ValueError("M12N V3 activation current state differs")
    if CLOSEOUT_PATH.read_text(encoding="utf-8") != build_closeout(receipt, state):
        raise ValueError("M12N V3 activation closeout differs")
    return receipt, state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    receipt, state = write_and_validate() if args.write else validate_files()
    print(
        json.dumps(
            {
                "status": "valid_successful_m12n_v3_production_activation",
                "activation_survived_postcheck": True,
                "rollback_executed": False,
                "receipt_subject_sha256": receipt["receipt_subject_sha256"],
                "receipt_file_sha256": canonical_file_sha256(SUCCESS_RECEIPT_PATH),
                "current_state_subject_sha256": state["current_state_subject_sha256"],
                "current_state_file_sha256": canonical_file_sha256(CURRENT_STATE_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
