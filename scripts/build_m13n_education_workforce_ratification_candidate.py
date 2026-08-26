from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.editorial_artifacts.bundle import semantic_hash  # noqa: E402
from app.editorial_presentations.site_publication import (  # noqa: E402
    ACTIVATION_AUTHORITY_SCHEMA_VERSION,
    ACTIVATION_REVIEWER_AUTHORITY,
    EDUCATION_ACTIVATION_AUTHORITY_ID,
    POSITIVE_AUTHORIZATIONS,
    validate_ratification_runtime_evidence_binding,
    validate_stable_ratified_runtime_binding,
)
from scripts.foushee_education_workforce_publication_preparation import (  # noqa: E402
    ISSUE_ID,
    M13M_ARTIFACT_ID,
    M13M_PATH,
    MEMBER_ID,
    activation_write_set_binding,
    build_activation_decision_template,
    build_authority,
    build_write_set,
    canonical_file_sha256,
    reviewed_runtime_manifest,
    validate_activation_decision_template,
    validate_preflight,
    validate_runtime_health_proof,
    validate_write_set,
)

OUTPUT_ROOT = (
    ROOT / "docs/editorial/full_record_reviews/publication_activation_candidates/"
    "f000477_education_workforce_119_v1"
)
RUNTIME_MANIFEST_PATH = OUTPUT_ROOT / "reviewed_runtime_manifest.json"
RUNTIME_PROOF_PATH = OUTPUT_ROOT / "runtime_health_proof.json"
PREFLIGHT_PATH = OUTPUT_ROOT / "current_production_preflight.json"
AUTHORITY_PATH = OUTPUT_ROOT / "production_eligibility_publication_authority.json"
WRITE_SET_PATH = OUTPUT_ROOT / "expected_production_write_set.json"
ROLLBACK_PATH = OUTPUT_ROOT / "rollback_contract.json"
ACTIVATION_TEMPLATE_PATH = OUTPUT_ROOT / "human_activation_decision_template.json"
CANDIDATE_PATH = OUTPUT_ROOT / "positive_activation_ratification_candidate.json"
REVIEW_PACKET_PATH = OUTPUT_ROOT / "ratification_review_packet.json"
REVIEW_DOSSIER_PATH = OUTPUT_ROOT / "ratification_review_packet.md"
PARITY_PATH = OUTPUT_ROOT / "preparation_parity_manifest.json"

POST_M13NR_MAIN = "1a01725dbd3311bfa8dcdea31009466f2c51c6a1"
RUNTIME_MANIFEST_SHA256 = (
    "ad95d769f3d860431cfc7418b2bd4fd076f6ba991eff00c65031bf1fffe0e904"
)
RUNTIME_PROOF_SUBJECT_SHA256 = (
    "2a2309a13c14ad92bd04335e4f5909e612f9737da15fcc6b27d08ca02bead3b8"
)
PREFLIGHT_SUBJECT_SHA256 = (
    "06457121bcc9ef6017272e9989930abf4c786b941026ab0af971c2b36fddce88"
)
BASELINE_FINGERPRINT_SHA256 = (
    "7fd41a05d8fcc033b8b1522e54a5ecda12ce9782c040e723d04613f30d30a860"
)
PREPARATION_DECISION_RECORDED_AT_UTC = "2026-08-26T01:38:13.268576Z"
PREPARATION_REVIEWER = "dhart54"
CANDIDATE_PREPARED_AT_UTC = "2026-08-26T00:47:09.030374Z"
RATIFICATION_REVIEWER = "chatgpt:political_fingerprint_authority_thread"
RATIFICATION_CANDIDATE_ID = (
    "publication-activation-ratification-candidate:f000477:education_workforce:119:v1"
)
REVIEW_PACKET_ID = (
    "publication-activation-ratification-review-packet:"
    "f000477:education_workforce:119:v1"
)
EXPECTED_BEFORE = {
    "batches": 6,
    "artifacts": 152,
    "relationships": 163,
    "publication_registry": 3,
}
EXPECTED_AFTER = {
    "batches": 7,
    "artifacts": 155,
    "relationships": 165,
    "publication_registry": 4,
}


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _json_text(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _write(path: Path, value: dict | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = value if isinstance(value, str) else _json_text(value)
    path.write_text(text, encoding="utf-8", newline="\n")


def _file_binding(path: Path, subject_field: str) -> dict[str, str]:
    value = _load(path)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "file_sha256": canonical_file_sha256(path),
        subject_field: value[subject_field],
    }


def _validate_captured_evidence() -> tuple[dict, dict, dict]:
    manifest = _load(RUNTIME_MANIFEST_PATH)
    proof = _load(RUNTIME_PROOF_PATH)
    preflight = _load(PREFLIGHT_PATH)
    if manifest != reviewed_runtime_manifest():
        raise ValueError("M13N six-file runtime manifest differs from reviewed bytes")
    validate_runtime_health_proof(
        proof, require_fresh=False, require_current_runtime=True
    )
    validate_preflight(preflight, require_execution_bindings=False)
    if (
        manifest["reviewed_runtime_manifest_sha256"] != RUNTIME_MANIFEST_SHA256
        or proof["runtime_health_proof_subject_sha256"] != RUNTIME_PROOF_SUBJECT_SHA256
        or preflight["preflight_subject_sha256"] != PREFLIGHT_SUBJECT_SHA256
        or preflight["state_fingerprint_sha256"] != BASELINE_FINGERPRINT_SHA256
        or proof["deployed_commit"] != POST_M13NR_MAIN
        or proof["health_commit"] != POST_M13NR_MAIN
        or preflight["deployed_commit"] != POST_M13NR_MAIN
        or preflight["counts"] != EXPECTED_BEFORE
        or preflight["education_registry_rows"] != []
        or preflight["m13n_target_rows"] != []
        or preflight["runtime_health_proof_binding"]["reviewed_runtime_manifest_sha256"]
        != RUNTIME_MANIFEST_SHA256
    ):
        raise ValueError(
            "M13N captured runtime or inactive production baseline differs"
        )
    return manifest, proof, preflight


def build_preparation() -> dict[str, dict]:
    manifest, proof, preflight = _validate_captured_evidence()
    authority = build_authority(
        preflight,
        reviewer=PREPARATION_REVIEWER,
        decision_recorded_at_utc=PREPARATION_DECISION_RECORDED_AT_UTC,
    )
    write_set = build_write_set(preflight, authority)
    template = build_activation_decision_template(write_set, authority)
    validate_write_set(write_set, authority=authority)
    validate_activation_decision_template(template, write_set, authority)
    if (
        write_set["expected_counts"]
        != {"before": EXPECTED_BEFORE, "after": EXPECTED_AFTER}
        or write_set["write_caps"]
        != {
            "batch_inserts": 1,
            "artifact_inserts": 3,
            "relationship_inserts": 2,
            "registry_inserts": 1,
            "registry_updates": 0,
            "deletes_during_activation": 0,
            "existing_registry_rows_touched": 0,
        }
        or write_set["activation_authorized"] is not False
        or write_set["production_write_authorized"] is not False
    ):
        raise ValueError("M13N bounded write envelope differs")
    rollback_subject = {
        "member_bioguide_id": MEMBER_ID,
        "issue_id": ISSUE_ID,
        "congress": 119,
        "ownership": write_set["rollback"],
        "restores_exact_preflight_fingerprint": True,
        "education_registry_row_absent_after_rollback": True,
        "existing_registry_rows_unchanged": True,
    }
    rollback = {
        "schema_version": "publication_preparation_rollback_contract_v1",
        "artifact_id": (
            "publication-rollback-contract:f000477:education_workforce:119:v1"
        ),
        "subject": rollback_subject,
        "rollback_subject_sha256": semantic_hash(rollback_subject),
    }
    return {
        "manifest": manifest,
        "proof": proof,
        "preflight": preflight,
        "authority": authority,
        "write_set": write_set,
        "template": template,
        "rollback": rollback,
    }


def build_candidate(preparation: dict[str, dict]) -> dict:
    proof = preparation["proof"]
    preflight = preparation["preflight"]
    write_set = preparation["write_set"]
    metadata = write_set["publication_registry"]["publication_metadata"]
    stable_runtime = {
        "reviewed_runtime_manifest_sha256": RUNTIME_MANIFEST_SHA256,
        "reviewed_commit": POST_M13NR_MAIN,
        "deployed_commit": POST_M13NR_MAIN,
        "health_commit": POST_M13NR_MAIN,
    }
    runtime_evidence = {
        "runtime_health_proof_subject_sha256": proof[
            "runtime_health_proof_subject_sha256"
        ],
        "captured_at_utc": proof["captured_at_utc"],
        "reviewed_runtime_manifest_sha256": RUNTIME_MANIFEST_SHA256,
        "deployed_commit": POST_M13NR_MAIN,
        "health_commit": POST_M13NR_MAIN,
    }
    validate_stable_ratified_runtime_binding(
        stable_runtime,
        expected_runtime_manifest_sha256=RUNTIME_MANIFEST_SHA256,
    )
    validate_ratification_runtime_evidence_binding(
        runtime_evidence, stable_runtime=stable_runtime
    )
    subject = {
        "decision": "approve_exact_publication_activation",
        "candidate_prepared_at_utc": CANDIDATE_PREPARED_AT_UTC,
        "reviewer": RATIFICATION_REVIEWER,
        "reviewer_authority": ACTIVATION_REVIEWER_AUTHORITY,
        "product_owner": "dhart54",
        "member_bioguide_id": MEMBER_ID,
        "issue_id": ISSUE_ID,
        "congress": 119,
        "accepted_site_integration_binding": write_set[
            "accepted_site_integration_binding"
        ],
        "candidate_preparation_authority_binding": {
            **write_set["authority_binding"],
            "authority_file_sha256": canonical_file_sha256(AUTHORITY_PATH),
        },
        "activation_write_set_binding": activation_write_set_binding(write_set),
        "publication_registry_target": {
            "member_bioguide_id": MEMBER_ID,
            "issue_id": ISSUE_ID,
            "presentation_natural_key": M13M_ARTIFACT_ID,
            "presentation_artifact_version": 1,
        },
        "presentation_content_sha256": metadata["active_artifact_sha256"],
        "preflight_binding": metadata["preflight_binding"],
        "rollback_binding": write_set["rollback"],
        "runtime_binding": stable_runtime,
        "ratification_runtime_evidence_binding": runtime_evidence,
        "production_target_identity_sha256": preflight[
            "production_target_identity_sha256"
        ],
        "expected_live_postconditions": {
            "counts": EXPECTED_AFTER,
            "education_119_tier": "reviewed_conclusion",
            "education_all_tier": "reviewed_conclusion",
            "education_118_tier": "receipts_only",
            "existing_three_domains_unchanged": True,
        },
        "authorizations": POSITIVE_AUTHORIZATIONS,
    }
    if "decision_recorded_at_utc" in subject:
        raise ValueError(
            "M13N candidate contains a human activation decision timestamp"
        )
    return {
        "schema_version": "m13n_publication_activation_ratification_candidate_v1",
        "artifact_id": RATIFICATION_CANDIDATE_ID,
        "immutable": True,
        "accepted": False,
        "sealed": False,
        "authority_contract": {
            "artifact_id": EDUCATION_ACTIVATION_AUTHORITY_ID,
            "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        },
        "prospective_authority_subject": subject,
        "prospective_authority_subject_sha256": semantic_hash(subject),
        "evidence_file_bindings": {
            "accepted_site_integration": {
                "path": M13M_PATH.relative_to(ROOT).as_posix(),
                "file_sha256": canonical_file_sha256(M13M_PATH),
                "subject_sha256": write_set["accepted_site_integration_binding"][
                    "subject_sha256"
                ],
            },
            "reviewed_runtime_manifest": _file_binding(
                RUNTIME_MANIFEST_PATH, "reviewed_runtime_manifest_sha256"
            ),
            "runtime_health_proof": _file_binding(
                RUNTIME_PROOF_PATH, "runtime_health_proof_subject_sha256"
            ),
            "production_preflight": _file_binding(
                PREFLIGHT_PATH, "preflight_subject_sha256"
            ),
            "preparation_authority": _file_binding(
                AUTHORITY_PATH, "authority_subject_sha256"
            ),
            "activation_write_set": _file_binding(
                WRITE_SET_PATH, "write_set_subject_sha256"
            ),
            "rollback_contract": _file_binding(
                ROLLBACK_PATH, "rollback_subject_sha256"
            ),
            "empty_activation_template": _file_binding(
                ACTIVATION_TEMPLATE_PATH, "template_subject_sha256"
            ),
        },
        "authority_materialization_contract": {
            "decision_recorded_at_utc": (
                "must be added only after independent activation review at the "
                "truthful decision time"
            ),
            "all_other_subject_fields": (
                "must equal this prospective subject after replacing "
                "candidate_prepared_at_utc with decision_recorded_at_utc"
            ),
            "fresh_execution_runtime_proof_required": True,
        },
        "authorization_boundary": (
            "This immutable candidate is unaccepted and unsealed. It is not a "
            "positive activation authority and cannot authorize production writes, "
            "registry mutation, publication, rollback, deployment, or live activation."
        ),
    }


def build_review_packet(candidate: dict, preparation: dict[str, dict]) -> dict:
    subject = {
        "candidate_binding": {
            "artifact_id": candidate["artifact_id"],
            "candidate_file_sha256": canonical_file_sha256(CANDIDATE_PATH),
            "prospective_authority_subject_sha256": candidate[
                "prospective_authority_subject_sha256"
            ],
        },
        "post_m13nr_main": POST_M13NR_MAIN,
        "runtime_manifest_sha256": RUNTIME_MANIFEST_SHA256,
        "runtime_health_proof_subject_sha256": RUNTIME_PROOF_SUBJECT_SHA256,
        "production_preflight_subject_sha256": PREFLIGHT_SUBJECT_SHA256,
        "production_state_fingerprint_sha256": BASELINE_FINGERPRINT_SHA256,
        "preparation_authority_binding": candidate["evidence_file_bindings"][
            "preparation_authority"
        ],
        "write_set_binding": candidate["evidence_file_bindings"][
            "activation_write_set"
        ],
        "rollback_binding": candidate["evidence_file_bindings"]["rollback_contract"],
        "empty_activation_template_binding": candidate["evidence_file_bindings"][
            "empty_activation_template"
        ],
        "preparation_decision": {
            "reviewer": PREPARATION_REVIEWER,
            "decision_recorded_at_utc": PREPARATION_DECISION_RECORDED_AT_UTC,
            "activating": False,
        },
        "write_envelope": preparation["write_set"]["write_caps"],
        "counts": {"before": EXPECTED_BEFORE, "after": EXPECTED_AFTER},
        "review_question": (
            "Does this exact non-authorizing Education candidate safely qualify "
            "for later positive activation-authority materialization?"
        ),
        "authorizing": False,
    }
    return {
        "schema_version": "m13n_publication_activation_ratification_review_packet_v1",
        "artifact_id": REVIEW_PACKET_ID,
        "immutable": True,
        "subject": subject,
        "review_packet_subject_sha256": semantic_hash(subject),
    }


def build_dossier(candidate: dict, packet: dict) -> str:
    subject = packet["subject"]
    return f"""# M13N Education & Workforce Activation Ratification Candidate

This package is immutable, unaccepted, unsealed, and non-authorizing. It creates
no usable positive activation authority and performs no production write.

## Exact deployed runtime and inactive baseline

- Post-M13N-R main/deployed/health: `{POST_M13NR_MAIN}`
- Six-file runtime manifest: `{RUNTIME_MANIFEST_SHA256}`
- Runtime-health proof subject: `{RUNTIME_PROOF_SUBJECT_SHA256}`
- Production preflight subject: `{PREFLIGHT_SUBJECT_SHA256}`
- Production fingerprint: `{BASELINE_FINGERPRINT_SHA256}`
- Counts: `6 batches / 152 artifacts / 163 relationships / 3 registry rows`
- Education registry and target rows: absent; Education remains receipts-only

## Non-activating preparation

- Reviewer: `{PREPARATION_REVIEWER}`
- Decision timestamp: `{PREPARATION_DECISION_RECORDED_AT_UTC}`
- Preparation authority subject: `{subject["preparation_authority_binding"]["authority_subject_sha256"]}`
- Write set subject: `{subject["write_set_binding"]["write_set_subject_sha256"]}`
- Rollback subject: `{subject["rollback_binding"]["rollback_subject_sha256"]}`
- Empty activation template: `{subject["empty_activation_template_binding"]["template_subject_sha256"]}`
- Writes if later authorized: `1 batch / 3 artifacts / 2 relationships / 1 registry insert`
- Prospective counts: `7 / 155 / 165 / 4`

## Detached activation candidate

- Candidate: `{candidate["artifact_id"]}`
- Prospective authority subject: `{candidate["prospective_authority_subject_sha256"]}`
- Candidate accepted: `false`
- Candidate sealed: `false`
- Human activation decision timestamp: absent
- Positive activation authority artifact: absent

## Review question

{subject["review_question"]}
"""


def build_parity(candidate: dict, packet: dict) -> dict:
    subject = {
        "milestone": "M13N",
        "member_bioguide_id": MEMBER_ID,
        "issue_id": ISSUE_ID,
        "congress": 119,
        "post_m13nr_main": POST_M13NR_MAIN,
        "runtime_source_files_unchanged": True,
        "governed_files": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "file_sha256": canonical_file_sha256(path),
            }
            for path in (
                RUNTIME_MANIFEST_PATH,
                RUNTIME_PROOF_PATH,
                PREFLIGHT_PATH,
                AUTHORITY_PATH,
                WRITE_SET_PATH,
                ROLLBACK_PATH,
                ACTIVATION_TEMPLATE_PATH,
                CANDIDATE_PATH,
                REVIEW_PACKET_PATH,
                REVIEW_DOSSIER_PATH,
            )
        ],
        "candidate_subject_sha256": candidate["prospective_authority_subject_sha256"],
        "review_packet_subject_sha256": packet["review_packet_subject_sha256"],
        "positive_activation_authority_absent": True,
        "production_write_performed": False,
    }
    return {
        "schema_version": "publication_preparation_parity_v1",
        "artifact_id": (
            "publication-preparation-parity:f000477:education_workforce:119:v1"
        ),
        "subject": subject,
        "parity_subject_sha256": semantic_hash(subject),
    }


def write_outputs() -> None:
    preparation = build_preparation()
    _write(AUTHORITY_PATH, preparation["authority"])
    _write(WRITE_SET_PATH, preparation["write_set"])
    _write(ROLLBACK_PATH, preparation["rollback"])
    _write(ACTIVATION_TEMPLATE_PATH, preparation["template"])
    candidate = build_candidate(preparation)
    _write(CANDIDATE_PATH, candidate)
    packet = build_review_packet(candidate, preparation)
    _write(REVIEW_PACKET_PATH, packet)
    _write(REVIEW_DOSSIER_PATH, build_dossier(candidate, packet))
    _write(PARITY_PATH, build_parity(candidate, packet))


def validate_outputs() -> dict:
    preparation = build_preparation()
    expected = {
        AUTHORITY_PATH: preparation["authority"],
        WRITE_SET_PATH: preparation["write_set"],
        ROLLBACK_PATH: preparation["rollback"],
        ACTIVATION_TEMPLATE_PATH: preparation["template"],
    }
    for path, value in expected.items():
        if _load(path) != value:
            raise ValueError(f"M13N governed artifact differs: {path.name}")
    candidate = _load(CANDIDATE_PATH)
    if candidate != build_candidate(preparation):
        raise ValueError("M13N ratification candidate differs deterministically")
    packet = _load(REVIEW_PACKET_PATH)
    if packet != build_review_packet(candidate, preparation):
        raise ValueError("M13N review packet differs deterministically")
    if REVIEW_DOSSIER_PATH.read_text(encoding="utf-8") != build_dossier(
        candidate, packet
    ):
        raise ValueError("M13N review dossier differs deterministically")
    if _load(PARITY_PATH) != build_parity(candidate, packet):
        raise ValueError("M13N preparation parity differs deterministically")
    template = preparation["template"]
    completion = template["subject"][
        "completion_required_after_exact_runtime_deployment"
    ]
    forbidden = (
        OUTPUT_ROOT / "positive_activation_authority.json",
        OUTPUT_ROOT / "production_activation_receipt.json",
        OUTPUT_ROOT / "current_state.json",
    )
    if (
        candidate["accepted"] is not False
        or candidate["sealed"] is not False
        or "decision_recorded_at_utc" in candidate["prospective_authority_subject"]
        or template["accepted"] is not False
        or template["sealed"] is not False
        or any(
            value is not None
            for key, value in completion.items()
            if key != "authorizations"
        )
        or any(value is not None for value in completion["authorizations"].values())
        or any(path.exists() for path in forbidden)
    ):
        raise ValueError("M13N authorization boundary differs")
    datetime.fromisoformat(PREPARATION_DECISION_RECORDED_AT_UTC.replace("Z", "+00:00"))
    return {
        "authority_subject_sha256": preparation["authority"][
            "authority_subject_sha256"
        ],
        "write_set_subject_sha256": preparation["write_set"][
            "write_set_subject_sha256"
        ],
        "rollback_subject_sha256": preparation["rollback"]["rollback_subject_sha256"],
        "template_subject_sha256": preparation["template"]["template_subject_sha256"],
        "candidate_subject_sha256": candidate["prospective_authority_subject_sha256"],
        "review_packet_subject_sha256": packet["review_packet_subject_sha256"],
        "parity_subject_sha256": _load(PARITY_PATH)["parity_subject_sha256"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        write_outputs()
    result = validate_outputs()
    print(
        json.dumps(
            {
                "status": "valid_non_authorizing_m13n_ratification_candidate",
                "accepted": False,
                "sealed": False,
                "preparation_reviewer": PREPARATION_REVIEWER,
                "preparation_decision_recorded_at_utc": (
                    PREPARATION_DECISION_RECORDED_AT_UTC
                ),
                **result,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
