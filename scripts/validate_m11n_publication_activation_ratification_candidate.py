from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.editorial_artifacts.bundle import semantic_hash  # noqa: E402
from app.editorial_presentations.site_publication import (  # noqa: E402
    ACTIVATION_AUTHORITY_ID,
    ACTIVATION_AUTHORITY_SCHEMA_VERSION,
    ACTIVATION_REVIEWER_AUTHORITY,
    POSITIVE_AUTHORIZATIONS,
)
from scripts.foushee_national_security_publication_activation import (  # noqa: E402
    AUTHORITY_PATH,
    M11M_ARTIFACT_ID,
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
MEMBER_ID = "F000477"
ISSUE_ID = "NATIONAL_SECURITY_FOREIGN"
POST_M11N_MAIN = "5d5f65e2e3f40e5b95d1a5cc38e60f40f073ec38"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    candidate = _load(CANDIDATE_PATH)
    authority = _load(AUTHORITY_PATH)
    write_set = _load(WRITE_SET_PATH)
    preflight = _load(PREFLIGHT_PATH)
    runtime_proof = _load(RUNTIME_PROOF_PATH)
    validate_preflight(preflight)
    validate_runtime_health_proof(runtime_proof)
    validate_write_set(write_set, authority=authority)

    subject = candidate.get("prospective_authority_subject")
    if (
        candidate.get("schema_version")
        != "m11n_publication_activation_ratification_candidate_v1"
        or candidate.get("artifact_id")
        != "publication-activation-ratification-candidate:f000477:national_security_foreign:119:v1"
        or candidate.get("immutable") is not True
        or candidate.get("accepted") is not False
        or candidate.get("sealed") is not False
        or candidate.get("authority_contract")
        != {
            "artifact_id": ACTIVATION_AUTHORITY_ID,
            "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        }
        or not isinstance(subject, dict)
        or candidate.get("prospective_authority_subject_sha256")
        != semantic_hash(subject)
    ):
        raise ValueError("M11N ratification-candidate envelope differs")

    metadata = write_set["publication_registry"]["publication_metadata"]
    expected_runtime = {
        "reviewed_runtime_manifest_sha256": metadata["reviewed_runtime_binding"][
            "reviewed_runtime_manifest_sha256"
        ],
        "reviewed_commit": POST_M11N_MAIN,
        "deployed_commit": runtime_proof["deployed_commit"],
        "health_commit": runtime_proof["health_commit"],
        "health_proof_subject_sha256": runtime_proof[
            "runtime_health_proof_subject_sha256"
        ],
    }
    expected_registry = {
        "member_bioguide_id": MEMBER_ID,
        "issue_id": ISSUE_ID,
        "presentation_natural_key": M11M_ARTIFACT_ID,
        "presentation_artifact_version": 1,
    }
    try:
        datetime.fromisoformat(
            subject["decision_recorded_at_utc"].replace("Z", "+00:00")
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("prospective decision timestamp is invalid") from exc
    if (
        subject.get("decision") != "approve_exact_publication_activation"
        or subject.get("reviewer") != "ChatGPT"
        or subject.get("reviewer_authority") != ACTIVATION_REVIEWER_AUTHORITY
        or subject.get("product_owner") != "dhart54"
        or subject.get("member_bioguide_id") != MEMBER_ID
        or subject.get("issue_id") != ISSUE_ID
        or subject.get("congress") != 119
        or subject.get("accepted_m11m_binding") != write_set["accepted_m11m_binding"]
        or subject.get("candidate_preparation_authority_binding")
        != {
            **write_set["authority_binding"],
            "authority_file_sha256": canonical_file_sha256(AUTHORITY_PATH),
        }
        or subject.get("activation_write_set_binding")
        != activation_write_set_binding(write_set)
        or subject.get("publication_registry_target") != expected_registry
        or subject.get("presentation_content_sha256")
        != metadata["active_artifact_sha256"]
        or subject.get("preflight_binding") != metadata["preflight_binding"]
        or subject.get("runtime_binding") != expected_runtime
        or subject.get("production_target_identity_sha256")
        != preflight["production_target_identity_sha256"]
        or subject.get("rollback_binding") != write_set["rollback"]
        or subject.get("authorizations") != POSITIVE_AUTHORIZATIONS
    ):
        raise ValueError("prospective publication-activation subject differs")
    if (
        runtime_proof["deployed_commit"] != POST_M11N_MAIN
        or preflight["deployed_commit"] != POST_M11N_MAIN
        or preflight["m11n_target_rows"] != []
        or preflight["counts"] != write_set["expected_counts"]["before"]
        or preflight["selector_pre_activation"]["scopes"]["119"][ISSUE_ID]["tier"]
        != "receipts_only"
        or preflight["selector_pre_activation"]["scopes"]["all"][ISSUE_ID]["tier"]
        != "receipts_only"
        or preflight["selector_pre_activation"]["scopes"]["118"][ISSUE_ID]["tier"]
        != "receipts_only"
    ):
        raise ValueError("M11N pre-activation production boundary differs")
    print(
        json.dumps(
            {
                "status": "valid_non_authorizing_ratification_candidate",
                "accepted": False,
                "sealed": False,
                "prospective_authority_subject_sha256": candidate[
                    "prospective_authority_subject_sha256"
                ],
                "post_m11n_main": POST_M11N_MAIN,
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
