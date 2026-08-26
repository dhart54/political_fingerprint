from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.editorial_artifacts.bundle import semantic_hash  # noqa: E402
from scripts.foushee_education_workforce_publication_preparation import (  # noqa: E402
    canonical_file_sha256,
)

OUTPUT = (
    ROOT / "docs/editorial/full_record_reviews/publication_activation_candidates/"
    "f000477_education_workforce_119_v1"
)
AUTHORITY_PATH = OUTPUT / "positive_activation_authority.json"
MATERIALIZATION_PATH = OUTPUT / "activation_ratification_materialization_receipt.json"
EXECUTION_PROOF_PATH = OUTPUT / "execution_runtime_health_proof.json"
PREFLIGHT_PATH = OUTPUT / "current_production_preflight.json"
WRITE_SET_PATH = OUTPUT / "expected_production_write_set.json"
ROLLBACK_PATH = OUTPUT / "rollback_contract.json"
RECEIPT_PATH = OUTPUT / "production_activation_receipt.json"
CURRENT_STATE_PATH = OUTPUT / "current_state.json"

RATIFIED_HEAD = "f5b762d748e1f87dc4c5c5da58acaaf6f1c40878"
RATIFIED_BASE = "1a01725dbd3311bfa8dcdea31009466f2c51c6a1"
AUTHORITY_FILE_SHA256 = (
    "7e42d43a9c8ab8bfa71d9ae295dbcc2fcd8a6a066235d83eafeba74a9c997787"
)
AUTHORITY_SUBJECT_SHA256 = (
    "3a901faf83365e7baf416045ed7ae3a9bea4225c77a1e97ab73fe8b3ba72d791"
)
MATERIALIZATION_FILE_SHA256 = (
    "988f89bdba2d02ef4e0ffb19029bf2acaa6d68fbb3ad0842c8bbad9b2b285a24"
)
MATERIALIZATION_SUBJECT_SHA256 = (
    "9c396506b046622af8d486fd3e21eb4f50a371322c8d34c96509a64848091c57"
)
EXECUTION_PROOF_SUBJECT_SHA256 = (
    "a6fb51b72d7c9f4d598f4c7b8e4e8c6802bde77d7d99ab3c804fd9498d6f074d"
)
PREFLIGHT_SUBJECT_SHA256 = (
    "06457121bcc9ef6017272e9989930abf4c786b941026ab0af971c2b36fddce88"
)
BASELINE_FINGERPRINT = (
    "7fd41a05d8fcc033b8b1522e54a5ecda12ce9782c040e723d04613f30d30a860"
)
WRITE_SET_SUBJECT_SHA256 = (
    "10de5dc0a7266870601df4d36cd2ef388f63923d9189dbd927c9a43be936ecf3"
)
ROLLBACK_SUBJECT_SHA256 = (
    "9667a7d2f960ea456ed4a91b203a60f0d5b44a210ef87a5678d5cc85afa49236"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _text(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _validate_inputs() -> None:
    authority = _load(AUTHORITY_PATH)
    materialization = _load(MATERIALIZATION_PATH)
    execution = _load(EXECUTION_PROOF_PATH)
    preflight = _load(PREFLIGHT_PATH)
    write_set = _load(WRITE_SET_PATH)
    rollback = _load(ROLLBACK_PATH)
    if (
        canonical_file_sha256(AUTHORITY_PATH) != AUTHORITY_FILE_SHA256
        or authority["activation_authority_subject_sha256"] != AUTHORITY_SUBJECT_SHA256
        or authority.get("accepted") is not True
        or authority.get("sealed") is not True
        or authority.get("test_only_synthetic") is not None
        or canonical_file_sha256(MATERIALIZATION_PATH) != MATERIALIZATION_FILE_SHA256
        or materialization["receipt_subject_sha256"] != MATERIALIZATION_SUBJECT_SHA256
        or execution["runtime_health_proof_subject_sha256"]
        != EXECUTION_PROOF_SUBJECT_SHA256
        or preflight["preflight_subject_sha256"] != PREFLIGHT_SUBJECT_SHA256
        or preflight["state_fingerprint_sha256"] != BASELINE_FINGERPRINT
        or write_set["write_set_subject_sha256"] != WRITE_SET_SUBJECT_SHA256
        or rollback["rollback_subject_sha256"] != ROLLBACK_SUBJECT_SHA256
    ):
        raise ValueError("M13N successful closeout input identity differs")


def build_receipt() -> dict:
    _validate_inputs()
    preflight = _load(PREFLIGHT_PATH)
    subject = {
        "ratified_pr": 172,
        "ratified_head": RATIFIED_HEAD,
        "ratified_base": RATIFIED_BASE,
        "member_bioguide_id": "F000477",
        "issue_id": "EDUCATION_WORKFORCE",
        "activation_authority": {
            "file_sha256": AUTHORITY_FILE_SHA256,
            "subject_sha256": AUTHORITY_SUBJECT_SHA256,
        },
        "materialization_receipt": {
            "file_sha256": MATERIALIZATION_FILE_SHA256,
            "subject_sha256": MATERIALIZATION_SUBJECT_SHA256,
        },
        "execution_runtime_proof": {
            "file_sha256": canonical_file_sha256(EXECUTION_PROOF_PATH),
            "subject_sha256": EXECUTION_PROOF_SUBJECT_SHA256,
        },
        "production_apply": {
            "already_applied": False,
            "batch_id": 21,
            "artifact_ids": {
                "presentation": 242,
                "source_manifest": 243,
                "validation": 244,
            },
            "batch_inserts": 1,
            "artifact_inserts": 3,
            "relationship_inserts": 2,
            "registry_inserts": 1,
            "registry_updates": 0,
            "deletes": 0,
        },
        "final_counts": {
            "batches": 7,
            "artifacts": 155,
            "relationships": 165,
            "publication_registry": 4,
        },
        "idempotent_second_apply": {
            "already_applied": True,
            "additional_batches": 0,
            "additional_artifacts": 0,
            "additional_relationships": 0,
            "additional_registry_mutations": 0,
        },
        "live_education_presentation": {
            "tiers": {
                "119": "reviewed_conclusion",
                "all": "reviewed_conclusion",
                "118": "receipts_only",
            },
            "overview_count": 1,
            "repeated_pattern_count": 1,
            "notable_choice_count": 1,
            "synthesis_count": 0,
            "trajectory_count": 0,
            "overview_direction": None,
            "pattern_direction": None,
            "notable": {
                "title": "H.R. 1048 amendment and final passage",
                "direction": "mixed",
                "direction_label": "Mixed",
                "direction_symbol": "±",
            },
        },
        "live_positions": {
            "yea_count": 6,
            "nay_count": 10,
            "other_count": 1,
            "total_votes": 17,
            "recorded_votes": 16,
            "interpreted_support_count": 6,
            "interpreted_oppose_count": 10,
            "interpreted_other_count": 1,
            "interpreted_total": 17,
        },
        "live_evidence": {
            "scope_119_governed_actions": 17,
            "scope_119_unique_actions": 17,
            "scope_119_episodes": 16,
            "all_scope_governed_119_actions": 17,
            "all_scope_unique_119_actions": 17,
            "scope_118_governed_119_actions": 0,
        },
        "hr1005_proof": {
            "canonical_action_id": "house:119:1:312",
            "member_action": "Not_Voting",
            "exact_choice_position_effect": "non_directional_not_voting",
            "directional_analytical_memberships": 0,
        },
        "existing_domain_isolation": {
            "baseline_fingerprint_unchanged": True,
            "registry_rows": preflight["baseline_registry_rows"],
            "tiers_119_and_all": "reviewed_conclusion",
            "tiers_118": "receipts_only",
        },
        "rollback": {
            "executed": False,
            "contract_subject_sha256": ROLLBACK_SUBJECT_SHA256,
        },
    }
    return {
        "schema_version": "m13n_successful_production_activation_receipt_v1",
        "artifact_id": (
            "successful-production-activation-receipt:"
            "f000477:education_workforce:119:v1"
        ),
        "immutable": True,
        "subject": subject,
        "receipt_subject_sha256": semantic_hash(subject),
    }


def build_current_state(receipt: dict) -> dict:
    subject = {
        "member_bioguide_id": "F000477",
        "issue_id": "EDUCATION_WORKFORCE",
        "congress": 119,
        "status": "successfully_activated",
        "presentation_artifact_id": 242,
        "presentation_content_sha256": (
            "ea482f71f1bce872574fd91abd76869423f0ba2fd4dddc78eb24e77806f5294c"
        ),
        "counts": receipt["subject"]["final_counts"],
        "tiers": receipt["subject"]["live_education_presentation"]["tiers"],
        "activation_authority_subject_sha256": AUTHORITY_SUBJECT_SHA256,
        "production_activation_receipt_subject_sha256": receipt[
            "receipt_subject_sha256"
        ],
        "rollback_executed": False,
    }
    return {
        "schema_version": "m13n_current_publication_state_v1",
        "artifact_id": "current-publication-state:f000477:education_workforce:119:v1",
        "immutable": True,
        "subject": subject,
        "current_state_subject_sha256": semantic_hash(subject),
    }


def write_outputs() -> None:
    receipt = build_receipt()
    RECEIPT_PATH.write_text(_text(receipt), encoding="utf-8", newline="\n")
    current = build_current_state(receipt)
    CURRENT_STATE_PATH.write_text(_text(current), encoding="utf-8", newline="\n")


def validate_outputs() -> dict:
    expected_receipt = build_receipt()
    if _load(RECEIPT_PATH) != expected_receipt:
        raise ValueError("M13N successful activation receipt differs")
    expected_current = build_current_state(expected_receipt)
    if _load(CURRENT_STATE_PATH) != expected_current:
        raise ValueError("M13N current state differs")
    return {
        "receipt_file_sha256": canonical_file_sha256(RECEIPT_PATH),
        "receipt_subject_sha256": expected_receipt["receipt_subject_sha256"],
        "current_state_file_sha256": canonical_file_sha256(CURRENT_STATE_PATH),
        "current_state_subject_sha256": expected_current[
            "current_state_subject_sha256"
        ],
    }


def main() -> int:
    write_outputs()
    print(json.dumps(validate_outputs(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
