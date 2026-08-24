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
    M12M_PATH,
    MEMBER_ID,
    PREFLIGHT_PATH,
    RUNTIME_PROOF_PATH,
    WRITE_SET_PATH,
    activation_write_set_binding,
    canonical_file_sha256,
    reviewed_runtime_manifest,
    validate_preflight,
    validate_runtime_health_proof,
    validate_write_set,
)


OUTPUT_ROOT = (
    ROOT / "docs/editorial/full_record_reviews/publication_activation_candidates/"
    "f000477_environment_energy_119_v3"
)
CANDIDATE_PATH = OUTPUT_ROOT / "positive_activation_ratification_candidate.json"
REVIEW_PACKET_PATH = OUTPUT_ROOT / "ratification_review_packet.json"
REVIEW_DOSSIER_PATH = OUTPUT_ROOT / "ratification_review_packet.md"
POST_REPAIR_MAIN = "c480dfabc2fcbd65bf5b22037200af509adb7b5b"
REPAIRED_RUNTIME_MANIFEST = (
    "a831d472f27a1785ebdcc609c174fc2e19da7213245adde3d12720736158ba8a"
)
FAILED_RUNTIME_MANIFEST = (
    "a22bee788697eb84da900be5ec9a0aef0c6949c59a6a9c2d7f697cdf369036c1"
)
FAILED_AUTHORITY_ID = (
    "publication-activation-authority:f000477:environment_energy:119:v1"
)
FAILED_AUTHORITY_SUBJECT_SHA256 = (
    "0adb87796e6e0d008586a03ddc075179837b3f18bc5f52f52c7e9ed9cce50e36"
)
CANDIDATE_PREPARED_AT_UTC = "2026-08-24T01:11:19Z"
RATIFICATION_CANDIDATE_ID = (
    "publication-activation-ratification-candidate:f000477:environment_energy:119:v3"
)
REVIEW_PACKET_ID = (
    "publication-activation-ratification-review-packet:"
    "f000477:environment_energy:119:v3"
)
REVIEWER_IDENTITY = "chatgpt:political_fingerprint_authority_thread"
EXPECTED_COUNTS = {
    "batches": 5,
    "artifacts": 149,
    "relationships": 161,
    "publication_registry": 2,
}
EXPECTED_FINGERPRINT = (
    "b22908fb081fa3dcefbb2e7326b0619b9f95fecc1bbebc76e783628dceddb0eb"
)


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _json_text(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _file_binding(path: Path, subject_field: str) -> dict[str, str]:
    value = _load(path)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "file_sha256": canonical_file_sha256(path),
        subject_field: value[subject_field],
    }


def build_candidate() -> dict:
    authority = _load(AUTHORITY_PATH)
    write_set = _load(WRITE_SET_PATH)
    preflight = _load(PREFLIGHT_PATH)
    runtime_proof = _load(RUNTIME_PROOF_PATH)
    validate_preflight(preflight, require_current_runtime=True)
    validate_runtime_health_proof(runtime_proof, require_current_runtime=True)
    validate_write_set(write_set, authority=authority)

    manifest = reviewed_runtime_manifest()["reviewed_runtime_manifest_sha256"]
    if (
        manifest != REPAIRED_RUNTIME_MANIFEST
        or runtime_proof["reviewed_runtime_manifest_sha256"] != manifest
        or runtime_proof["deployed_commit"] != POST_REPAIR_MAIN
        or runtime_proof["health_commit"] != POST_REPAIR_MAIN
        or preflight["deployed_commit"] != POST_REPAIR_MAIN
    ):
        raise ValueError("V3 repaired runtime identity differs")
    if (
        preflight["counts"] != EXPECTED_COUNTS
        or preflight["state_fingerprint_sha256"] != EXPECTED_FINGERPRINT
        or preflight["environment_registry_rows"] != []
        or preflight["m12n_target_rows"] != []
        or any(
            preflight["selector_pre_activation"]["scopes"][scope][ISSUE_ID]["tier"]
            != "receipts_only"
            for scope in ("119", "all", "118")
        )
    ):
        raise ValueError("V3 inactive production baseline differs")

    metadata = write_set["publication_registry"]["publication_metadata"]
    stable_runtime = {
        "reviewed_runtime_manifest_sha256": REPAIRED_RUNTIME_MANIFEST,
        "reviewed_commit": POST_REPAIR_MAIN,
        "deployed_commit": POST_REPAIR_MAIN,
        "health_commit": POST_REPAIR_MAIN,
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
            "reviewed_runtime_manifest_sha256": REPAIRED_RUNTIME_MANIFEST,
            "deployed_commit": POST_REPAIR_MAIN,
            "health_commit": POST_REPAIR_MAIN,
        },
        "production_target_identity_sha256": preflight[
            "production_target_identity_sha256"
        ],
        "rollback_binding": write_set["rollback"],
        "authorizations": POSITIVE_AUTHORIZATIONS,
    }
    return {
        "schema_version": "m12n_publication_activation_ratification_candidate_v3",
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
        "evidence_file_bindings": {
            "accepted_site_integration": {
                "path": M12M_PATH.relative_to(ROOT).as_posix(),
                "file_sha256": canonical_file_sha256(M12M_PATH),
                "subject_sha256": write_set["accepted_site_integration_binding"][
                    "subject_sha256"
                ],
            },
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
        },
        "historical_failed_authority_boundary": {
            "artifact_id": FAILED_AUTHORITY_ID,
            "authority_subject_sha256": FAILED_AUTHORITY_SUBJECT_SHA256,
            "failed_runtime_manifest_sha256": FAILED_RUNTIME_MANIFEST,
            "current_runtime_manifest_sha256": REPAIRED_RUNTIME_MANIFEST,
            "reusable_for_v3_execution": False,
        },
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
            "This immutable candidate is unaccepted and unsealed. It cannot be used "
            "for public selection, database mutation, registry mutation, rollback, "
            "or deployment, and no V3 positive authority exists."
        ),
    }


def build_review_packet(candidate: dict) -> dict:
    subject = candidate["prospective_authority_subject"]
    packet_subject = {
        "candidate_binding": {
            "artifact_id": candidate["artifact_id"],
            "prospective_authority_subject_sha256": candidate[
                "prospective_authority_subject_sha256"
            ],
            "candidate_file_sha256": canonical_file_sha256(CANDIDATE_PATH),
        },
        "repaired_runtime": subject["runtime_binding"],
        "fresh_runtime_evidence": candidate["evidence_file_bindings"][
            "runtime_health_proof"
        ],
        "fresh_production_preflight": {
            **candidate["evidence_file_bindings"]["production_preflight"],
            "state_fingerprint_sha256": EXPECTED_FINGERPRINT,
            "counts": EXPECTED_COUNTS,
            "environment_registry_absent": True,
        },
        "existing_publication_identities": {
            "justice": _load(PREFLIGHT_PATH)["justice_registry_row"],
            "national_security": _load(PREFLIGHT_PATH)[
                "national_security_registry_row"
            ],
        },
        "prospective_write_envelope": {
            "batch_inserts": 1,
            "artifact_inserts": 3,
            "relationship_inserts": 2,
            "registry_inserts": 1,
            "registry_updates": 0,
            "activation_time_deletes": 0,
            "justice_rows_touched": 0,
            "national_security_rows_touched": 0,
            "prospective_counts": {
                "batches": 6,
                "artifacts": 152,
                "relationships": 163,
                "publication_registry": 3,
            },
        },
        "active_http_regression_required": True,
        "historical_failed_authority_boundary": candidate[
            "historical_failed_authority_boundary"
        ],
        "review_question": (
            "Does the already-approved Environment publication receive activation "
            "authority on this exact repaired runtime and unchanged production state?"
        ),
        "authorizing": False,
    }
    return {
        "schema_version": "m12n_publication_activation_ratification_review_packet_v3",
        "artifact_id": REVIEW_PACKET_ID,
        "immutable": True,
        "subject": packet_subject,
        "review_packet_subject_sha256": semantic_hash(packet_subject),
    }


def build_dossier(candidate: dict, packet: dict) -> str:
    subject = candidate["prospective_authority_subject"]
    runtime = subject["runtime_binding"]
    evidence = subject["ratification_runtime_evidence_binding"]
    preflight = packet["subject"]["fresh_production_preflight"]
    return f"""# M12N Environment & Energy Activation Ratification V3

This package is immutable, unaccepted, unsealed, and non-authorizing. It creates
no usable positive activation authority and performs no production write.

## Exact repaired deployment and inactive production state

- Deployed/health commit: `{runtime["deployed_commit"]}`
- Reviewed runtime manifest: `{runtime["reviewed_runtime_manifest_sha256"]}`
- Fresh health-proof subject: `{evidence["runtime_health_proof_subject_sha256"]}`
- Health proof captured: `{evidence["captured_at_utc"]}`
- Fresh preflight subject: `{preflight["preflight_subject_sha256"]}`
- Production fingerprint: `{preflight["state_fingerprint_sha256"]}`
- Counts: `5 batches / 149 artifacts / 161 relationships / 2 registry rows`
- Environment registry/artifact keys: absent; receipts-only at 119/all/118
- Justice content: `1c088fc4a98e8442263899faffd7e203967cf60c387944884e4ce755d6ba7943`
- National Security content: `05661086601991075f04195090a41e0febaad7f8e6acda53f0cab838f97e860c`

## Exact proposed activation envelope

- Candidate: `{candidate["artifact_id"]}`
- Prospective authority subject: `{candidate["prospective_authority_subject_sha256"]}`
- Preparation authority: `{subject["candidate_preparation_authority_binding"]["authority_subject_sha256"]}`
- Write set: `{subject["activation_write_set_binding"]["write_set_subject_sha256"]}`
- Writes: `1 batch / 3 artifacts / 2 relationships / 1 registry insert`
- Prospective counts: `6 / 152 / 163 / 3`
- Accepted M12M presentation content: `{subject["presentation_content_sha256"]}`
- Decision timestamp: absent until independent ratification

The disposable PostgreSQL gate must reprove the active presentation, exact
Environment and National Security position accounting, 119/all/118 Environment
evidence behavior, H.R. 6387's non-directional status, 13/13/2/4/7 supporting
sets, idempotency, and exact rollback.

## Historical failed authority boundary

The sealed V2 failed-attempt authority `{FAILED_AUTHORITY_SUBJECT_SHA256}` remains
immutable history. It binds runtime `{FAILED_RUNTIME_MANIFEST}` and cannot execute
against repaired runtime `{REPAIRED_RUNTIME_MANIFEST}`. It is not reused or
revoked by this candidate.

## Review question

Does the already-approved Environment publication receive activation authority
on this exact repaired runtime and unchanged production state?
"""


def validate_candidate() -> dict:
    candidate = _load(CANDIDATE_PATH)
    expected = build_candidate()
    if candidate != expected:
        raise ValueError("M12N V3 ratification candidate differs deterministically")
    subject = candidate["prospective_authority_subject"]
    try:
        prepared = datetime.fromisoformat(
            subject["candidate_prepared_at_utc"].replace("Z", "+00:00")
        )
        if prepared.tzinfo is None:
            raise ValueError
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("V3 candidate preparation timestamp is invalid") from exc
    if (
        "decision_recorded_at_utc" in subject
        or "health_proof_subject_sha256" in subject["runtime_binding"]
        or candidate["accepted"] is not False
        or candidate["sealed"] is not False
        or candidate["prospective_authority_subject_sha256"] != semantic_hash(subject)
    ):
        raise ValueError("V3 candidate authority boundary differs")
    packet = _load(REVIEW_PACKET_PATH)
    if packet != build_review_packet(candidate):
        raise ValueError("M12N V3 review packet differs deterministically")
    if REVIEW_DOSSIER_PATH.read_text(encoding="utf-8") != build_dossier(
        candidate, packet
    ):
        raise ValueError("M12N V3 review dossier differs deterministically")
    return candidate


def write_outputs() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    candidate = build_candidate()
    CANDIDATE_PATH.write_text(_json_text(candidate), encoding="utf-8", newline="\n")
    packet = build_review_packet(candidate)
    REVIEW_PACKET_PATH.write_text(_json_text(packet), encoding="utf-8", newline="\n")
    REVIEW_DOSSIER_PATH.write_text(
        build_dossier(candidate, packet), encoding="utf-8", newline="\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        write_outputs()
    candidate = validate_candidate()
    packet = _load(REVIEW_PACKET_PATH)
    print(
        json.dumps(
            {
                "status": "valid_non_authorizing_v3_ratification_candidate",
                "artifact_id": candidate["artifact_id"],
                "accepted": candidate["accepted"],
                "sealed": candidate["sealed"],
                "candidate_prepared_at_utc": CANDIDATE_PREPARED_AT_UTC,
                "prospective_authority_subject_sha256": candidate[
                    "prospective_authority_subject_sha256"
                ],
                "review_packet_subject_sha256": packet["review_packet_subject_sha256"],
                "runtime_health_proof_subject_sha256": candidate[
                    "prospective_authority_subject"
                ]["ratification_runtime_evidence_binding"][
                    "runtime_health_proof_subject_sha256"
                ],
                "preflight_subject_sha256": candidate["prospective_authority_subject"][
                    "preflight_binding"
                ]["preflight_subject_sha256"],
                "write_set_subject_sha256": candidate["prospective_authority_subject"][
                    "activation_write_set_binding"
                ]["write_set_subject_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
