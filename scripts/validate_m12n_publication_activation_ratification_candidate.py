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
    ENVIRONMENT_ACTIVATION_AUTHORITY_ID,
    POSITIVE_AUTHORIZATIONS,
)
from scripts.foushee_environment_energy_publication_preparation import (  # noqa: E402
    AUTHORITY_PATH,
    ISSUE_ID,
    M12M_ARTIFACT_ID,
    MEMBER_ID,
    OUTPUT_ROOT,
    PREFLIGHT_PATH,
    RUNTIME_PROOF_PATH,
    WRITE_SET_ID,
    WRITE_SET_PATH,
    activation_write_set_binding,
    canonical_file_sha256,
    validate_preflight,
    validate_runtime_health_proof,
    validate_write_set,
)


CANDIDATE_PATH = OUTPUT_ROOT / "positive_activation_ratification_candidate.json"
RATIFICATION_DOSSIER_PATH = OUTPUT_ROOT / "positive_activation_ratification_review.md"
POSITIVE_AUTHORITY_PATH = OUTPUT_ROOT / "positive_activation_authority.json"
POST_CORRECTED_RUNTIME_MAIN = "b23a26cde2143bd646f0300fed18bd0c97a71a2b"
CANDIDATE_PREPARED_AT_UTC = "2026-08-17T00:57:58Z"
RATIFICATION_CANDIDATE_ID = (
    "publication-activation-ratification-candidate:f000477:environment_energy:119:v2"
)
REVIEWER_IDENTITY = "chatgpt:political_fingerprint_authority_thread"


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _json_text(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def build_candidate() -> dict:
    authority = _load(AUTHORITY_PATH)
    write_set = _load(WRITE_SET_PATH)
    preflight = _load(PREFLIGHT_PATH)
    runtime_proof = _load(RUNTIME_PROOF_PATH)
    validate_preflight(preflight, require_current_runtime=True)
    validate_runtime_health_proof(runtime_proof, require_current_runtime=True)
    validate_write_set(write_set, authority=authority)

    metadata = write_set["publication_registry"]["publication_metadata"]
    stable_runtime = {
        "reviewed_runtime_manifest_sha256": metadata["reviewed_runtime_binding"][
            "reviewed_runtime_manifest_sha256"
        ],
        "reviewed_commit": POST_CORRECTED_RUNTIME_MAIN,
        "deployed_commit": runtime_proof["deployed_commit"],
        "health_commit": runtime_proof["health_commit"],
    }
    subject = {
        "decision": "approve_exact_publication_activation",
        "candidate_prepared_at_utc": CANDIDATE_PREPARED_AT_UTC,
        "reviewer": REVIEWER_IDENTITY,
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
            "presentation_natural_key": M12M_ARTIFACT_ID,
            "presentation_artifact_version": 1,
        },
        "presentation_content_sha256": metadata["active_artifact_sha256"],
        "preflight_binding": metadata["preflight_binding"],
        "runtime_binding": stable_runtime,
        "ratification_runtime_evidence_binding": {
            "runtime_health_proof_subject_sha256": runtime_proof[
                "runtime_health_proof_subject_sha256"
            ],
            "captured_at_utc": runtime_proof["captured_at_utc"],
            "reviewed_runtime_manifest_sha256": runtime_proof[
                "reviewed_runtime_manifest_sha256"
            ],
            "deployed_commit": runtime_proof["deployed_commit"],
            "health_commit": runtime_proof["health_commit"],
        },
        "production_target_identity_sha256": preflight[
            "production_target_identity_sha256"
        ],
        "rollback_binding": write_set["rollback"],
        "authorizations": POSITIVE_AUTHORIZATIONS,
    }
    return {
        "schema_version": "m12n_publication_activation_ratification_candidate_v2",
        "artifact_id": RATIFICATION_CANDIDATE_ID,
        "immutable": True,
        "accepted": False,
        "sealed": False,
        "authority_contract": {
            "artifact_id": ENVIRONMENT_ACTIVATION_AUTHORITY_ID,
            "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        },
        "prospective_authority_subject": subject,
        "prospective_authority_subject_sha256": semantic_hash(subject),
        "authority_materialization_contract": {
            "decision_recorded_at_utc": (
                "must be added only after independent ratification at the actual "
                "decision time"
            ),
            "all_other_subject_fields": (
                "must equal this prospective authority subject exactly"
            ),
            "execution_runtime_proof": (
                "must be newly captured at execution, digest-valid, no more than "
                "1,800 seconds old, and match runtime_binding; its proof digest is "
                "not required to equal ratification_runtime_evidence_binding"
            ),
        },
        "authorization_boundary": (
            "This is a non-authorizing ratification candidate. It cannot be used "
            "for public selection, database mutation, registry mutation, rollback, "
            "or deployment unless independently ratified and separately "
            "materialized with the actual decision timestamp as an accepted, "
            "sealed authority."
        ),
    }


def build_dossier(candidate: dict) -> str:
    subject = candidate["prospective_authority_subject"]
    runtime = subject["runtime_binding"]
    evidence = subject["ratification_runtime_evidence_binding"]
    return f"""# M12N Environment & Energy Activation Ratification V2

This package is unaccepted and unsealed. It cannot authorize a production write,
registry mutation, activation, rollback, or deployment.

## Proposed stable authority

- Prospective subject: `{candidate["prospective_authority_subject_sha256"]}`
- Proposed decision: `{subject["decision"]}`
- Proposed reviewer: `{subject["reviewer"]}`
- Candidate prepared: `{subject["candidate_prepared_at_utc"]}`
- Decision recorded: absent until independent ratification
- Write set: `{subject["activation_write_set_binding"]["write_set_subject_sha256"]}`
- Production target: `{subject["production_target_identity_sha256"]}`

## Stable ratified runtime identity

- Reviewed manifest: `{runtime["reviewed_runtime_manifest_sha256"]}`
- Reviewed commit: `{runtime["reviewed_commit"]}`
- Deployed commit observed at ratification: `{runtime["deployed_commit"]}`
- Health commit observed at ratification: `{runtime["health_commit"]}`

## Historical ratification evidence

- Health-proof subject: `{evidence["runtime_health_proof_subject_sha256"]}`
- Captured: `{evidence["captured_at_utc"]}`

This proof establishes what the reviewer saw. Its digest is not an execution-time
digest requirement and may be older than 1,800 seconds after ratification.

## Execution-time contract

Every production dry-run, apply, postcheck, or rollback must supply a newly
captured, digest-valid runtime proof no more than 1,800 seconds old. Its reviewed
manifest, deployed commit, and health commit must equal the stable identity above.
Its proof-subject digest may differ from the historical ratification proof.

Fresh database-state drift checks, exact production-target binding, exact
authority/write-set digest confirmations, synthetic-authority rejection, and the
bounded rollback contract remain mandatory.

## Current production boundary

- Preflight subject: `{subject["preflight_binding"]["preflight_subject_sha256"]}`
- Production fingerprint: `{subject["preflight_binding"]["state_fingerprint_sha256"]}`
- Environment & Energy: absent from the registry and receipts-only
- Justice & Public Safety: active and unchanged
- National Security & Foreign Policy: active and unchanged
"""


def validate_candidate() -> dict:
    candidate = _load(CANDIDATE_PATH)
    expected = build_candidate()
    if candidate != expected:
        raise ValueError("M12N ratification candidate differs deterministically")
    if not RATIFICATION_DOSSIER_PATH.exists() or RATIFICATION_DOSSIER_PATH.read_text(
        encoding="utf-8"
    ) != build_dossier(candidate):
        raise ValueError("M12N ratification review dossier differs deterministically")
    subject = candidate["prospective_authority_subject"]
    try:
        prepared = datetime.fromisoformat(
            subject["candidate_prepared_at_utc"].replace("Z", "+00:00")
        )
        if prepared.tzinfo is None:
            raise ValueError
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("candidate preparation timestamp is invalid") from exc
    if (
        "decision_recorded_at_utc" in subject
        or "health_proof_subject_sha256" in subject["runtime_binding"]
        or candidate["prospective_authority_subject_sha256"] != semantic_hash(subject)
        or POSITIVE_AUTHORITY_PATH.exists()
    ):
        raise ValueError("M12N candidate authority/provenance boundary differs")

    preflight = _load(PREFLIGHT_PATH)
    runtime_proof = _load(RUNTIME_PROOF_PATH)
    write_set = _load(WRITE_SET_PATH)
    if (
        runtime_proof["deployed_commit"] != POST_CORRECTED_RUNTIME_MAIN
        or runtime_proof["health_commit"] != POST_CORRECTED_RUNTIME_MAIN
        or preflight["deployed_commit"] != POST_CORRECTED_RUNTIME_MAIN
        or preflight["environment_registry_rows"] != []
        or preflight["m12n_target_rows"] != []
        or preflight["counts"] != write_set["expected_counts"]["before"]
        or any(
            preflight["selector_pre_activation"]["scopes"][scope][ISSUE_ID]["tier"]
            != "receipts_only"
            for scope in ("119", "all", "118")
        )
    ):
        raise ValueError("M12N pre-activation production boundary differs")
    return candidate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        candidate = build_candidate()
        CANDIDATE_PATH.write_text(_json_text(candidate), encoding="utf-8", newline="\n")
        RATIFICATION_DOSSIER_PATH.write_text(
            build_dossier(candidate), encoding="utf-8", newline="\n"
        )
    candidate = validate_candidate()
    preflight = _load(PREFLIGHT_PATH)
    runtime_proof = _load(RUNTIME_PROOF_PATH)
    write_set = _load(WRITE_SET_PATH)
    print(
        json.dumps(
            {
                "status": "valid_non_authorizing_ratification_candidate",
                "accepted": False,
                "sealed": False,
                "candidate_prepared_at_utc": CANDIDATE_PREPARED_AT_UTC,
                "prospective_authority_subject_sha256": candidate[
                    "prospective_authority_subject_sha256"
                ],
                "post_corrected_runtime_main": POST_CORRECTED_RUNTIME_MAIN,
                "runtime_health_proof_subject_sha256": runtime_proof[
                    "runtime_health_proof_subject_sha256"
                ],
                "preflight_subject_sha256": preflight["preflight_subject_sha256"],
                "state_fingerprint_sha256": preflight["state_fingerprint_sha256"],
                "write_set_id": WRITE_SET_ID,
                "write_set_subject_sha256": write_set["write_set_subject_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
