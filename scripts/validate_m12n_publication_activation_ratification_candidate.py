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
    ACTIVATION_AUTHORITY_SCHEMA_VERSION,
    ACTIVATION_REVIEWER_AUTHORITY,
    ENVIRONMENT_ACTIVATION_AUTHORITY_ID,
    POSITIVE_AUTHORIZATIONS,
)
from scripts.foushee_environment_energy_publication_preparation import (  # noqa: E402
    AUTHORITY_PATH,
    M12M_ARTIFACT_ID,
    MEMBER_ID,
    ISSUE_ID,
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
POSITIVE_AUTHORITY_PATH = OUTPUT_ROOT / "positive_activation_authority.json"
POST_M12N_MAIN = "79d49f3e613e7914e4dc81d2f3b6a348cf80fafc"
RATIFICATION_CANDIDATE_ID = (
    "publication-activation-ratification-candidate:f000477:environment_energy:119:v1"
)
REVIEWER_IDENTITY = "chatgpt:political_fingerprint_authority_thread"


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def validate_candidate() -> dict:
    candidate = _load(CANDIDATE_PATH)
    authority = _load(AUTHORITY_PATH)
    write_set = _load(WRITE_SET_PATH)
    preflight = _load(PREFLIGHT_PATH)
    runtime_proof = _load(RUNTIME_PROOF_PATH)
    validate_preflight(preflight, require_current_runtime=True)
    validate_runtime_health_proof(runtime_proof, require_current_runtime=True)
    validate_write_set(write_set, authority=authority)

    subject = candidate.get("prospective_authority_subject")
    if (
        candidate.get("schema_version")
        != "m12n_publication_activation_ratification_candidate_v1"
        or candidate.get("artifact_id") != RATIFICATION_CANDIDATE_ID
        or candidate.get("immutable") is not True
        or candidate.get("accepted") is not False
        or candidate.get("sealed") is not False
        or candidate.get("authority_contract")
        != {
            "artifact_id": ENVIRONMENT_ACTIVATION_AUTHORITY_ID,
            "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        }
        or not isinstance(subject, dict)
        or candidate.get("prospective_authority_subject_sha256")
        != semantic_hash(subject)
    ):
        raise ValueError("M12N ratification-candidate envelope differs")
    if POSITIVE_AUTHORITY_PATH.exists():
        raise ValueError(
            "usable Environment positive activation authority must be absent"
        )

    metadata = write_set["publication_registry"]["publication_metadata"]
    expected_runtime = {
        "reviewed_runtime_manifest_sha256": metadata["reviewed_runtime_binding"][
            "reviewed_runtime_manifest_sha256"
        ],
        "reviewed_commit": POST_M12N_MAIN,
        "deployed_commit": runtime_proof["deployed_commit"],
        "health_commit": runtime_proof["health_commit"],
        "health_proof_subject_sha256": runtime_proof[
            "runtime_health_proof_subject_sha256"
        ],
    }
    expected_registry = {
        "member_bioguide_id": MEMBER_ID,
        "issue_id": ISSUE_ID,
        "presentation_natural_key": M12M_ARTIFACT_ID,
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
        or subject.get("reviewer") != REVIEWER_IDENTITY
        or subject.get("reviewer_authority") != ACTIVATION_REVIEWER_AUTHORITY
        or subject.get("product_owner") != "dhart54"
        or subject.get("member_bioguide_id") != MEMBER_ID
        or subject.get("issue_id") != ISSUE_ID
        or subject.get("congress") != 119
        or subject.get("accepted_site_integration_binding")
        != write_set["accepted_site_integration_binding"]
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
        raise ValueError("prospective Environment activation subject differs")
    if (
        runtime_proof["deployed_commit"] != POST_M12N_MAIN
        or runtime_proof["health_commit"] != POST_M12N_MAIN
        or preflight["deployed_commit"] != POST_M12N_MAIN
        or preflight["environment_registry_rows"] != []
        or preflight["m12n_target_rows"] != []
        or preflight["counts"] != write_set["expected_counts"]["before"]
        or write_set["expected_counts"]["after"]
        != {
            "batches": 6,
            "artifacts": 152,
            "relationships": 163,
            "publication_registry": 3,
        }
        or any(
            preflight["selector_pre_activation"]["scopes"][scope][ISSUE_ID]["tier"]
            != "receipts_only"
            for scope in ("119", "all", "118")
        )
    ):
        raise ValueError("M12N pre-activation production boundary differs")
    return candidate


def main() -> int:
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
                "prospective_authority_subject_sha256": candidate[
                    "prospective_authority_subject_sha256"
                ],
                "post_m12n_main": POST_M12N_MAIN,
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
