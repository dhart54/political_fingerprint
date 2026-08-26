"""M13N Education & Workforce publication preparation and execution runtime.

This module is production-sensitive code, but it contains no captured production
state and creates no governed artifacts by itself.  Production mutation requires
the future exact preparation authority, sealed positive activation authority,
write set, production target, preflight, and fresh execution-runtime proof.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import urlopen

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.editorial_artifacts.bundle import semantic_hash  # noqa: E402
from app.editorial_artifacts.repository import EditorialArtifactRepository  # noqa: E402
from app.editorial_presentations.education_workforce_integration_candidate import (  # noqa: E402
    M13M_ARTIFACT_ID,
    load_education_workforce_site_integration_candidate,
)
from app.editorial_presentations.selector import select_public_presentations  # noqa: E402
from app.editorial_presentations.site_publication import (  # noqa: E402
    ACTIVATION_AUTHORITY_SCHEMA_VERSION,
    ACTIVATION_REVIEWER_AUTHORITY,
    EDUCATION_ACTIVATION_AUTHORITY_ID,
    EDUCATION_AUTHORITY_ID,
    EDUCATION_FILE_SHA256,
    EDUCATION_SUBJECT_SHA256,
    POSITIVE_AUTHORIZATIONS,
    validate_education_candidate_preparation_authority,
    validate_education_positive_activation_authority,
    validate_fresh_execution_runtime_proof,
)
from scripts.editorial_artifact_store import (  # noqa: E402
    EXPECTED_PRODUCTION_TARGET,
    StoreSafetyError,
    _connect,
    target_info,
)

MEMBER_ID = "F000477"
MEMBER_SLUG = "leg_valerie_p_foushee"
ISSUE_ID = "EDUCATION_WORKFORCE"
CONGRESS = 119
WRITE_SET_ID = "publication-activation-write-set:f000477:education_workforce:119:v1"
ACTIVATION_TEMPLATE_ID = (
    "human-publication-activation-decision-template:f000477:education_workforce:119:v1"
)
BUNDLE_ID = "foushee_education_workforce_119_publication_activation_v1"
SOURCE_KEY = f"{M13M_ARTIFACT_ID}:publication-source-manifest"
VALIDATION_KEY = f"{M13M_ARTIFACT_ID}:publication-validation"
LOCK_KEY = f"political_fingerprint:{BUNDLE_ID}"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

M13M_PATH = (
    ROOT / "docs/editorial/full_record_reviews/site_integration_candidates/"
    "f000477_education_workforce_119_v1/site_integration_candidate.json"
)
M13L_ROOT = (
    ROOT / "docs/editorial/full_record_reviews/public_wording_implementations/"
    "f000477_education_workforce_119_v1"
)
M13L_AUTHORITY_PATH = M13L_ROOT / "human_public_wording_authority.json"
M13L_IMPLEMENTATION_PATH = M13L_ROOT / "reviewed_wording_decision_implementation.json"
M13L_PARITY_PATH = M13L_ROOT / "implementation_parity_manifest.json"

RUNTIME_SOURCE_PATHS = (
    BACKEND / "app/api/positions.py",
    BACKEND / "app/api/editorial_presentations.py",
    BACKEND / "app/editorial_presentations/selector.py",
    BACKEND / "app/editorial_presentations/site_publication.py",
    BACKEND
    / "app/editorial_presentations/education_workforce_integration_candidate.py",
    BACKEND / "scripts/foushee_education_workforce_publication_preparation.py",
)

PRODUCTION_TARGET_IDENTITY_SHA256 = semantic_hash(EXPECTED_PRODUCTION_TARGET)
CURRENT_COUNTS = {
    "batches": 6,
    "artifacts": 152,
    "relationships": 163,
    "publication_registry": 3,
}
EXPECTED_AFTER_COUNTS = {
    "batches": 7,
    "artifacts": 155,
    "relationships": 165,
    "publication_registry": 4,
}
BASELINE_IDENTITIES = {
    "JUSTICE_PUBLIC_SAFETY": (
        "public-issue-presentation-candidate:f000477:justice_public_safety:119:v1",
        "1c088fc4a98e8442263899faffd7e203967cf60c387944884e4ce755d6ba7943",
    ),
    "NATIONAL_SECURITY_FOREIGN": (
        "site-integration-candidate:f000477:national_security_foreign:119:v1",
        "05661086601991075f04195090a41e0febaad7f8e6acda53f0cab838f97e860c",
    ),
    "ENVIRONMENT_ENERGY": (
        "site-integration-candidate:f000477:environment_energy:119:v1",
        "7389aa33deca20cfa51293beab2b7602b39cb40258f1bca4a9cacf06aa818b53",
    ),
}


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str, sort_keys=True))


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise StoreSafetyError(f"expected JSON object: {path}")
    return value


def canonical_file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _file_record(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise StoreSafetyError(f"M13N runtime source is absent: {path}")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "file_sha256": canonical_file_sha256(path),
    }


def reviewed_runtime_manifest() -> dict[str, Any]:
    """Build the complete six-file runtime manifest; every path must exist now."""

    files = [_file_record(path) for path in RUNTIME_SOURCE_PATHS]
    return {
        "schema_version": "m13n_reviewed_runtime_manifest_v1",
        "files": files,
        "reviewed_runtime_manifest_sha256": semantic_hash(files),
    }


def assert_runtime_source_convergence() -> None:
    manifest = reviewed_runtime_manifest()
    actual = {item["path"] for item in manifest["files"]}
    expected = {path.relative_to(ROOT).as_posix() for path in RUNTIME_SOURCE_PATHS}
    if actual != expected or len(actual) != 6:
        raise StoreSafetyError("M13N runtime-source set is incomplete")


def capture_runtime_health(base_url: str) -> dict[str, Any]:
    endpoint = urljoin(base_url.rstrip("/") + "/", "health")
    with urlopen(endpoint, timeout=20) as response:  # noqa: S310
        health = json.load(response)
    commit = health.get("commit_sha")
    if not isinstance(commit, str) or not SHA40.fullmatch(commit):
        raise StoreSafetyError("live health endpoint lacks an exact commit SHA")
    body = {
        "schema_version": "m13n_live_runtime_health_proof_v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "health_endpoint": endpoint,
        "deployed_commit": commit,
        "health_commit": commit,
        "reviewed_runtime_manifest_sha256": reviewed_runtime_manifest()[
            "reviewed_runtime_manifest_sha256"
        ],
        "health_payload_sha256": semantic_hash(health),
    }
    body["runtime_health_proof_subject_sha256"] = semantic_hash(body)
    return body


def validate_runtime_health_proof(
    proof: dict[str, Any], *, require_fresh: bool, require_current_runtime: bool
) -> None:
    body = copy.deepcopy(proof)
    claimed = body.pop("runtime_health_proof_subject_sha256", None)
    if claimed != semantic_hash(body):
        raise StoreSafetyError("M13N runtime health proof digest mismatch")
    if (
        proof.get("schema_version") != "m13n_live_runtime_health_proof_v1"
        or proof.get("deployed_commit") != proof.get("health_commit")
        or not SHA40.fullmatch(proof.get("deployed_commit", ""))
    ):
        raise StoreSafetyError("M13N runtime health proof identity differs")
    if (
        require_current_runtime
        and proof.get("reviewed_runtime_manifest_sha256")
        != reviewed_runtime_manifest()["reviewed_runtime_manifest_sha256"]
    ):
        raise StoreSafetyError("production_runtime_not_converged")
    if require_fresh:
        try:
            captured = datetime.fromisoformat(proof["captured_at_utc"])
        except (KeyError, TypeError, ValueError) as exc:
            raise StoreSafetyError("M13N runtime proof timestamp is invalid") from exc
        age = datetime.now(timezone.utc) - captured.astimezone(timezone.utc)
        if age.total_seconds() < 0 or age.total_seconds() > 1800:
            raise StoreSafetyError("M13N runtime proof is not fresh")


def validate_production_execution_runtime(
    activation_authority: dict[str, Any], runtime_proof: dict[str, Any] | None
) -> None:
    if runtime_proof is None:
        raise StoreSafetyError("production operation requires fresh execution proof")
    validate_runtime_health_proof(
        runtime_proof, require_fresh=True, require_current_runtime=True
    )
    try:
        validate_fresh_execution_runtime_proof(
            runtime_proof,
            stable_runtime=activation_authority["subject"]["runtime_binding"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise StoreSafetyError(str(exc)) from exc


def target_identity_sha256(info: dict[str, Any]) -> str:
    return semantic_hash(
        {key: info[key] for key in ("scheme", "host", "port", "database")}
    )


def _counts(conn: Any) -> dict[str, int]:
    tables = {
        "batches": "editorial_artifact_batches",
        "artifacts": "editorial_artifact_versions",
        "relationships": "editorial_artifact_relationships",
        "publication_registry": "editorial_publication_registry",
    }
    return {
        key: int(conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"])
        for key, table in tables.items()
    }


def _state_fingerprint(conn: Any) -> str:
    queries = (
        """SELECT deterministic_batch_key,source_commit_sha,manifest_sha256,status,
                  artifact_count,relationship_count
             FROM editorial_artifact_batches ORDER BY deterministic_batch_key""",
        """SELECT artifact_type,natural_key,schema_version,artifact_version,
                  content_sha256,source_manifest_sha256,source_commit_sha,batch_id,
                  member_bioguide_id,issue_id,congress,chamber,canonical_action_id,
                  episode_id,policy_family_id,editorial_status,benchmark_status,
                  production_eligible,review_route
             FROM editorial_artifact_versions
             ORDER BY natural_key,artifact_version,content_sha256""",
        """SELECT parent.natural_key AS parent_natural_key,
                  child.natural_key AS child_natural_key,relationship_type,ordinal,
                  metadata_jsonb
             FROM editorial_artifact_relationships rel
             JOIN editorial_artifact_versions parent
               ON parent.artifact_id=rel.parent_artifact_id
             JOIN editorial_artifact_versions child
               ON child.artifact_id=rel.child_artifact_id
             ORDER BY parent.natural_key,relationship_type,ordinal,child.natural_key""",
        """SELECT registry.member_bioguide_id,registry.issue_id,artifact.natural_key,
                  artifact.artifact_version,registry.publicly_active,
                  registry.publication_metadata_jsonb
             FROM editorial_publication_registry registry
             JOIN editorial_artifact_versions artifact
               ON artifact.artifact_id=registry.artifact_id
             ORDER BY registry.member_bioguide_id,registry.issue_id""",
    )
    return semantic_hash(
        [
            [_jsonable(dict(row)) for row in conn.execute(query).fetchall()]
            for query in queries
        ]
    )


def _registry_rows(conn: Any) -> list[dict[str, Any]]:
    return [
        _jsonable(dict(row))
        for row in conn.execute(
            """SELECT registry.member_bioguide_id,registry.issue_id,
                      registry.artifact_id,registry.publicly_active,
                      registry.publication_metadata_jsonb,artifact.natural_key,
                      artifact.artifact_version,artifact.content_sha256,
                      artifact.source_commit_sha
                 FROM editorial_publication_registry registry
                 JOIN editorial_artifact_versions artifact
                   ON artifact.artifact_id=registry.artifact_id
                 ORDER BY registry.member_bioguide_id,registry.issue_id"""
        ).fetchall()
    ]


def _registry_identity(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "member_bioguide_id",
        "issue_id",
        "artifact_id",
        "publicly_active",
        "natural_key",
        "artifact_version",
        "content_sha256",
        "source_commit_sha",
    )
    return {key: row[key] for key in keys} | {
        "publication_metadata_sha256": semantic_hash(row["publication_metadata_jsonb"])
    }


def _target_rows(conn: Any) -> list[dict[str, Any]]:
    return [
        _jsonable(dict(row))
        for row in conn.execute(
            """SELECT artifact_id,natural_key,artifact_version,content_sha256
                 FROM editorial_artifact_versions
                WHERE natural_key=ANY(%s) ORDER BY natural_key,artifact_version""",
            ([M13M_ARTIFACT_ID, SOURCE_KEY, VALIDATION_KEY],),
        ).fetchall()
    ]


def _selector_state(
    conn: Any, *, allow_test_activation_authority: bool = False
) -> dict[str, Any]:
    rows = EditorialArtifactRepository(conn).publication_selector()
    scopes: dict[str, Any] = {}
    for scope in ("119", "all", "118"):
        response = select_public_presentations(
            rows,
            legislator_id=MEMBER_SLUG,
            member_bioguide_id=MEMBER_ID,
            scope=scope,
            allow_test_activation_authority=allow_test_activation_authority,
        )
        scopes[scope] = {
            item["issue_id"]: item["tier"] for item in response["presentations"]
        }
    return {"selector_rows": len(rows), "scopes": scopes}


def capture_preflight(
    conn: Any,
    *,
    deployed_commit: str,
    runtime_health_proof: dict[str, Any] | None = None,
    production_target_identity_sha256: str | None = None,
    allow_test_activation_authority: bool = False,
) -> dict[str, Any]:
    """Capture an exact transaction-read-only baseline for future M13N."""

    if not SHA40.fullmatch(deployed_commit):
        raise StoreSafetyError("deployed commit must be an exact lowercase SHA-40")
    counts = _counts(conn)
    registry = _registry_rows(conn)
    targets = _target_rows(conn)
    selector = _selector_state(
        conn, allow_test_activation_authority=allow_test_activation_authority
    )
    if counts != CURRENT_COUNTS:
        raise StoreSafetyError(f"unexpected M13N baseline counts: {counts}")
    if len(registry) != 3 or targets:
        raise StoreSafetyError("M13N publication baseline or target absence differs")
    by_issue = {row["issue_id"]: row for row in registry}
    baseline: dict[str, dict[str, Any]] = {}
    for issue_id, (natural_key, content_sha256) in BASELINE_IDENTITIES.items():
        row = by_issue.get(issue_id)
        if (
            row is None
            or row["member_bioguide_id"] != MEMBER_ID
            or row["natural_key"] != natural_key
            or row["content_sha256"] != content_sha256
            or row["publicly_active"] is not True
        ):
            raise StoreSafetyError(f"accepted {issue_id} production identity differs")
        baseline[issue_id] = _registry_identity(row)
    for scope in ("119", "all"):
        if any(
            selector["scopes"][scope][issue] != "reviewed_conclusion"
            for issue in BASELINE_IDENTITIES
        ):
            raise StoreSafetyError("existing publication selector state differs")
        if selector["scopes"][scope][ISSUE_ID] != "receipts_only":
            raise StoreSafetyError("Education selector is not fail-closed")
    if any(
        selector["scopes"]["118"][issue] != "receipts_only"
        for issue in (*BASELINE_IDENTITIES, ISSUE_ID)
    ):
        raise StoreSafetyError("118th-Congress publication boundary differs")
    report = {
        "schema_version": "m13n_current_production_preflight_v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "deployed_commit": deployed_commit,
        "transaction_read_only": True,
        "counts": counts,
        "state_fingerprint_sha256": _state_fingerprint(conn),
        "baseline_registry_rows": baseline,
        "education_registry_rows": [],
        "m13n_target_rows": targets,
        "selector_pre_activation": selector,
    }
    if runtime_health_proof is not None:
        validate_runtime_health_proof(
            runtime_health_proof,
            require_fresh=True,
            require_current_runtime=True,
        )
        if runtime_health_proof["deployed_commit"] != deployed_commit:
            raise StoreSafetyError("preflight runtime proof commit differs")
        report["runtime_health_proof_binding"] = {
            "runtime_health_proof_subject_sha256": runtime_health_proof[
                "runtime_health_proof_subject_sha256"
            ],
            "reviewed_runtime_manifest_sha256": runtime_health_proof[
                "reviewed_runtime_manifest_sha256"
            ],
            "deployed_commit": deployed_commit,
        }
    if production_target_identity_sha256 is not None:
        if production_target_identity_sha256 != PRODUCTION_TARGET_IDENTITY_SHA256:
            raise StoreSafetyError("preflight production target identity differs")
        report["production_target_identity_sha256"] = production_target_identity_sha256
    report["preflight_subject_sha256"] = semantic_hash(report)
    return report


def validate_preflight(
    report: dict[str, Any], *, require_execution_bindings: bool = False
) -> None:
    body = copy.deepcopy(report)
    claimed = body.pop("preflight_subject_sha256", None)
    if claimed != semantic_hash(body):
        raise StoreSafetyError("M13N preflight digest mismatch")
    if (
        report.get("schema_version") != "m13n_current_production_preflight_v1"
        or report.get("transaction_read_only") is not True
        or report.get("counts") != CURRENT_COUNTS
        or report.get("education_registry_rows") != []
        or report.get("m13n_target_rows") != []
        or not SHA40.fullmatch(report.get("deployed_commit", ""))
        or not SHA256.fullmatch(report.get("state_fingerprint_sha256", ""))
    ):
        raise StoreSafetyError("M13N preflight contract differs")
    baseline = report.get("baseline_registry_rows", {})
    for issue_id, (natural_key, content_sha256) in BASELINE_IDENTITIES.items():
        row = baseline.get(issue_id, {})
        if (
            row.get("natural_key") != natural_key
            or row.get("content_sha256") != content_sha256
            or row.get("publicly_active") is not True
        ):
            raise StoreSafetyError(f"M13N preflight {issue_id} binding differs")
    runtime = report.get("runtime_health_proof_binding")
    target = report.get("production_target_identity_sha256")
    if runtime is not None and (
        runtime.get("deployed_commit") != report["deployed_commit"]
        or runtime.get("reviewed_runtime_manifest_sha256")
        != reviewed_runtime_manifest()["reviewed_runtime_manifest_sha256"]
        or not SHA256.fullmatch(runtime.get("runtime_health_proof_subject_sha256", ""))
    ):
        raise StoreSafetyError("production_runtime_not_converged")
    if target is not None and target != PRODUCTION_TARGET_IDENTITY_SHA256:
        raise StoreSafetyError("M13N preflight target binding differs")
    if require_execution_bindings and (runtime is None or target is None):
        raise StoreSafetyError("M13N execution preflight lacks runtime/target binding")
    if require_execution_bindings:
        try:
            captured = datetime.fromisoformat(report["captured_at_utc"])
        except (KeyError, TypeError, ValueError) as exc:
            raise StoreSafetyError(
                "M13N execution preflight timestamp is invalid"
            ) from exc
        age = datetime.now(timezone.utc) - captured.astimezone(timezone.utc)
        if age.total_seconds() < 0 or age.total_seconds() > 1800:
            raise StoreSafetyError("M13N execution preflight is not fresh")


def load_candidate() -> dict[str, Any]:
    candidate = load_education_workforce_site_integration_candidate(M13M_PATH)
    if (
        canonical_file_sha256(M13M_PATH) != EDUCATION_FILE_SHA256
        or candidate["candidate_subject_sha256"] != EDUCATION_SUBJECT_SHA256
    ):
        raise StoreSafetyError("accepted M13M file or subject differs")
    return candidate


def build_authority(
    preflight: dict[str, Any],
    *,
    reviewer: str = "dhart54",
    decision_recorded_at_utc: str = "2026-08-25T00:00:00Z",
) -> dict[str, Any]:
    """Construct the exact non-activating Education preparation authority."""

    validate_preflight(preflight)
    candidate = load_candidate()
    subject = {
        "decision": "approve_production_eligibility_and_publication_preparation_candidate",
        "decision_recorded_at_utc": decision_recorded_at_utc,
        "reviewer": reviewer,
        "reviewer_authority": "publication_candidate_preparation_authority_v1",
        "member_bioguide_id": MEMBER_ID,
        "member_slug": MEMBER_SLUG,
        "issue_id": ISSUE_ID,
        "congress": CONGRESS,
        "accepted_site_integration_binding": {
            "artifact_id": M13M_ARTIFACT_ID,
            "subject_sha256": EDUCATION_SUBJECT_SHA256,
            "file_sha256": EDUCATION_FILE_SHA256,
            "content_sha256": semantic_hash(candidate),
        },
        "current_production_preflight_binding": {
            "preflight_subject_sha256": preflight["preflight_subject_sha256"],
            "state_fingerprint_sha256": preflight["state_fingerprint_sha256"],
            "deployed_commit": preflight["deployed_commit"],
        },
        "storage_gate_decision": {
            "editorial_status": "human_approved",
            "benchmark_status": "gold_benchmark",
            "production_eligible": True,
        },
        "authorizations": {
            "record_production_eligibility": True,
            "build_publication_activation_candidate": True,
            "build_expected_production_write_set": True,
            "perform_fresh_read_only_production_preflight": True,
            "prepare_rollback_and_disposable_proof": True,
            "production_database_write": False,
            "publication_registry_mutation": False,
            "publication_activation": False,
            "production_persistence": False,
            "deployment": False,
            "live_activation": False,
        },
        "downstream_boundary": (
            "A distinct sealed positive activation authority, stable runtime proof, "
            "fresh execution proof, exact target, and unchanged preflight are required."
        ),
    }
    authority = {
        "schema_version": (
            "site_integration_production_eligibility_publication_authority_v1"
        ),
        "artifact_id": EDUCATION_AUTHORITY_ID,
        "immutable": True,
        "accepted": True,
        "subject": subject,
        "authority_subject_sha256": semantic_hash(subject),
    }
    validate_education_candidate_preparation_authority(authority, candidate=candidate)
    return authority


def _artifact(
    *,
    artifact_type: str,
    natural_key: str,
    payload: dict[str, Any],
    source_manifest_sha256: str,
    source_commit_sha: str,
) -> dict[str, Any]:
    return {
        "artifact_type": artifact_type,
        "natural_key": natural_key,
        "schema_version": payload["schema_version"],
        "artifact_version": 1,
        "payload": payload,
        "content_sha256": semantic_hash(payload),
        "source_manifest_sha256": source_manifest_sha256,
        "source_commit_sha": source_commit_sha,
        "member_bioguide_id": MEMBER_ID,
        "issue_id": ISSUE_ID,
        "congress": CONGRESS,
        "chamber": "house",
        "canonical_action_id": None,
        "episode_id": None,
        "policy_family_id": None,
        "editorial_status": "human_approved",
        "benchmark_status": "gold_benchmark",
        "production_eligible": True,
        "review_route": "human_exception",
    }


def build_write_set(
    preflight: dict[str, Any], authority: dict[str, Any]
) -> dict[str, Any]:
    validate_preflight(preflight)
    candidate = load_candidate()
    validate_education_candidate_preparation_authority(authority, candidate=candidate)
    source_files = [
        _file_record(path)
        for path in (
            M13M_PATH,
            M13L_AUTHORITY_PATH,
            M13L_IMPLEMENTATION_PATH,
            M13L_PARITY_PATH,
        )
    ]
    source_manifest_sha256 = semantic_hash(source_files)
    source_payload = {
        "schema_version": "editorial_publication_source_manifest_v1",
        "activation_bundle_id": BUNDLE_ID,
        "complete_required_sources": True,
        "source_files": source_files,
        "accepted_site_integration_subject_sha256": EDUCATION_SUBJECT_SHA256,
        "accepted_site_integration_file_sha256": EDUCATION_FILE_SHA256,
    }
    validation_payload = {
        "schema_version": "editorial_publication_validation_v1",
        "activation_bundle_id": BUNDLE_ID,
        "successful": True,
        "current": True,
        "blocking_findings": 0,
        "semantic_tier": "reviewed_conclusion",
        "approved_universe_actions": 17,
        "accepted_interpreted_actions": 17,
        "accepted_episode_count": 16,
        "unused_non_directional_actions": ["house:119:1:312"],
        "accepted_public_wording_items": 3,
        "accepted_site_integration_subject_sha256": EDUCATION_SUBJECT_SHA256,
        "accepted_site_integration_file_sha256": EDUCATION_FILE_SHA256,
        "production_activation_authorized": False,
    }
    source_commit = preflight["deployed_commit"]
    artifacts = [
        _artifact(
            artifact_type="issue_public_presentation",
            natural_key=M13M_ARTIFACT_ID,
            payload=candidate,
            source_manifest_sha256=source_manifest_sha256,
            source_commit_sha=source_commit,
        ),
        _artifact(
            artifact_type="source_manifest",
            natural_key=SOURCE_KEY,
            payload=source_payload,
            source_manifest_sha256=source_manifest_sha256,
            source_commit_sha=source_commit,
        ),
        _artifact(
            artifact_type="standardization_validation_result",
            natural_key=VALIDATION_KEY,
            payload=validation_payload,
            source_manifest_sha256=source_manifest_sha256,
            source_commit_sha=source_commit,
        ),
    ]
    artifacts.sort(key=lambda item: item["natural_key"])
    by_key = {item["natural_key"]: item for item in artifacts}
    relationships = sorted(
        [
            {
                "parent_natural_key": M13M_ARTIFACT_ID,
                "child_natural_key": SOURCE_KEY,
                "relationship_type": "uses_source_manifest",
                "ordinal": 0,
                "metadata": {"activation_bundle_id": BUNDLE_ID},
            },
            {
                "parent_natural_key": M13M_ARTIFACT_ID,
                "child_natural_key": VALIDATION_KEY,
                "relationship_type": "has_validation",
                "ordinal": 0,
                "metadata": {"activation_bundle_id": BUNDLE_ID},
            },
        ],
        key=lambda item: item["relationship_type"],
    )
    rollback = {
        "delete_registry_primary_key": {
            "member_bioguide_id": MEMBER_ID,
            "issue_id": ISSUE_ID,
        },
        "delete_relationship_count": 2,
        "delete_artifact_natural_keys": sorted(
            [M13M_ARTIFACT_ID, SOURCE_KEY, VALIDATION_KEY]
        ),
        "delete_batch_key": f"{BUNDLE_ID}-{source_commit[:8]}",
        "restore_counts": CURRENT_COUNTS,
        "restore_state_fingerprint_sha256": preflight["state_fingerprint_sha256"],
        "baseline_registry_rows_unchanged": preflight["baseline_registry_rows"],
    }
    authority_file_sha256 = hashlib.sha256(
        (json.dumps(authority, sort_keys=True, indent=2) + "\n").encode()
    ).hexdigest()
    authority_binding = {
        "artifact_id": EDUCATION_AUTHORITY_ID,
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "authority_file_sha256": authority_file_sha256,
    }
    runtime_binding = reviewed_runtime_manifest()
    preflight_metadata = {
        "preflight_subject_sha256": preflight["preflight_subject_sha256"],
        "state_fingerprint_sha256": preflight["state_fingerprint_sha256"],
    }
    metadata = {
        "activation_bundle_id": BUNDLE_ID,
        "production_eligibility_publication_authority": authority,
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "authority_file_sha256": authority_file_sha256,
        "accepted_site_integration_subject_sha256": EDUCATION_SUBJECT_SHA256,
        "accepted_site_integration_file_sha256": EDUCATION_FILE_SHA256,
        "presentation_natural_key": M13M_ARTIFACT_ID,
        "presentation_artifact_version": 1,
        "active_artifact_sha256": by_key[M13M_ARTIFACT_ID]["content_sha256"],
        "validation_natural_key": VALIDATION_KEY,
        "validation_artifact_version": 1,
        "validation_content_sha256": by_key[VALIDATION_KEY]["content_sha256"],
        "source_manifest_natural_key": SOURCE_KEY,
        "source_manifest_artifact_version": 1,
        "source_manifest_content_sha256": by_key[SOURCE_KEY]["content_sha256"],
        "relationship_metadata": {"activation_bundle_id": BUNDLE_ID},
        "candidate_preparation_authority_binding": authority_binding,
        "preflight_binding": preflight_metadata,
        "reviewed_runtime_binding": runtime_binding,
        "production_target_identity_sha256": PRODUCTION_TARGET_IDENTITY_SHA256,
        "rollback_binding": rollback,
        "activation_authority_contract": {
            "artifact_id": EDUCATION_ACTIVATION_AUTHORITY_ID,
            "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
            "reviewer_authority": ACTIVATION_REVIEWER_AUTHORITY,
            "required_authorizations": POSITIVE_AUTHORIZATIONS,
        },
    }
    body = {
        "schema_version": "site_integration_publication_activation_write_set_v1",
        "artifact_id": WRITE_SET_ID,
        "bundle_id": BUNDLE_ID,
        "deterministic_batch_key": f"{BUNDLE_ID}-{source_commit[:8]}",
        "source_commit_sha": source_commit,
        "accepted_site_integration_binding": authority["subject"][
            "accepted_site_integration_binding"
        ],
        "authority_binding": authority_binding,
        "preflight_binding": {
            **preflight_metadata,
            "counts": preflight["counts"],
            "deployed_commit": source_commit,
            "runtime_health_proof_binding": preflight.get(
                "runtime_health_proof_binding"
            ),
            "production_target_identity_sha256": preflight.get(
                "production_target_identity_sha256"
            ),
        },
        "artifacts": artifacts,
        "relationships": relationships,
        "publication_registry": {
            "member_bioguide_id": MEMBER_ID,
            "issue_id": ISSUE_ID,
            "presentation_natural_key": M13M_ARTIFACT_ID,
            "presentation_artifact_version": 1,
            "publicly_active": True,
            "publication_metadata": metadata,
        },
        "expected_counts": {
            "before": CURRENT_COUNTS,
            "after": EXPECTED_AFTER_COUNTS,
        },
        "write_caps": {
            "batch_inserts": 1,
            "artifact_inserts": 3,
            "relationship_inserts": 2,
            "registry_inserts": 1,
            "registry_updates": 0,
            "deletes_during_activation": 0,
            "existing_registry_rows_touched": 0,
        },
        "public_smoke_contract": {
            ISSUE_ID: {
                "119": "reviewed_conclusion",
                "all": "reviewed_conclusion_with_reviewed_119_boundary",
                "118": "receipts_only",
            },
            **{
                issue: {
                    "119": "reviewed_conclusion_unchanged",
                    "all": "reviewed_conclusion_unchanged",
                    "118": "receipts_only_unchanged",
                }
                for issue in BASELINE_IDENTITIES
            },
        },
        "rollback": rollback,
        "activation_authorized": False,
        "production_write_authorized": False,
        "finalization_required": {
            "fresh_live_runtime_health_proof": True,
            "fresh_production_preflight": True,
            "sealed_positive_activation_authority": True,
        },
    }
    # The write-set digest excludes its derived binding embedded in metadata to
    # avoid a self-referential digest. Validation recomputes this canonical form.
    body["write_set_subject_sha256"] = _write_set_digest(body)
    metadata["activation_write_set_binding"] = activation_write_set_binding(body)
    validate_write_set(body, authority=authority)
    return body


def _write_set_digest(write_set: dict[str, Any]) -> str:
    body = copy.deepcopy(write_set)
    body.pop("write_set_subject_sha256", None)
    body["publication_registry"]["publication_metadata"].pop(
        "activation_write_set_binding", None
    )
    return semantic_hash(body)


def activation_write_set_binding(write_set: dict[str, Any]) -> dict[str, str]:
    return {
        "artifact_id": WRITE_SET_ID,
        "write_set_subject_sha256": write_set["write_set_subject_sha256"],
    }


def validate_write_set(write_set: dict[str, Any], *, authority: dict[str, Any]) -> None:
    candidate = load_candidate()
    validate_education_candidate_preparation_authority(authority, candidate=candidate)
    if write_set.get("write_set_subject_sha256") != _write_set_digest(write_set):
        raise StoreSafetyError("M13N write-set digest mismatch")
    if (
        write_set.get("schema_version")
        != "site_integration_publication_activation_write_set_v1"
        or write_set.get("artifact_id") != WRITE_SET_ID
        or write_set.get("bundle_id") != BUNDLE_ID
        or write_set.get("expected_counts")
        != {"before": CURRENT_COUNTS, "after": EXPECTED_AFTER_COUNTS}
        or write_set.get("activation_authorized") is not False
        or write_set.get("production_write_authorized") is not False
        or write_set.get("write_caps")
        != {
            "batch_inserts": 1,
            "artifact_inserts": 3,
            "relationship_inserts": 2,
            "registry_inserts": 1,
            "registry_updates": 0,
            "deletes_during_activation": 0,
            "existing_registry_rows_touched": 0,
        }
    ):
        raise StoreSafetyError("M13N write-set identity or caps differ")
    if len(write_set["artifacts"]) != 3 or len(write_set["relationships"]) != 2:
        raise StoreSafetyError("M13N bounded write graph differs")
    by_key = {item["natural_key"]: item for item in write_set["artifacts"]}
    if set(by_key) != {M13M_ARTIFACT_ID, SOURCE_KEY, VALIDATION_KEY}:
        raise StoreSafetyError("M13N activation natural keys differ")
    if by_key[M13M_ARTIFACT_ID]["payload"] != candidate:
        raise StoreSafetyError("M13N rewrote the accepted M13M candidate")
    for artifact in write_set["artifacts"]:
        if (
            artifact["content_sha256"] != semantic_hash(artifact["payload"])
            or artifact["editorial_status"] != "human_approved"
            or artifact["benchmark_status"] != "gold_benchmark"
            or artifact["production_eligible"] is not True
        ):
            raise StoreSafetyError("M13N artifact persistence gate differs")
    validation = by_key[VALIDATION_KEY]["payload"]
    if (
        validation["approved_universe_actions"] != 17
        or validation["accepted_interpreted_actions"] != 17
        or validation["accepted_episode_count"] != 16
        or validation["production_activation_authorized"] is not False
    ):
        raise StoreSafetyError("M13N accounting boundary differs")
    metadata = write_set["publication_registry"]["publication_metadata"]
    if (
        metadata.get("candidate_preparation_authority_binding")
        != write_set["authority_binding"]
        or metadata.get("activation_write_set_binding")
        != activation_write_set_binding(write_set)
        or metadata.get("production_target_identity_sha256")
        != PRODUCTION_TARGET_IDENTITY_SHA256
        or metadata.get("rollback_binding") != write_set["rollback"]
        or metadata.get("reviewed_runtime_binding") != reviewed_runtime_manifest()
    ):
        raise StoreSafetyError("M13N activation binding differs")


def build_activation_decision_template(
    write_set: dict[str, Any], authority: dict[str, Any]
) -> dict[str, Any]:
    """Build an empty form. It is deliberately not activation authority."""

    validate_write_set(write_set, authority=authority)
    subject = {
        "candidate_write_set_binding": activation_write_set_binding(write_set),
        "candidate_preparation_authority_binding": write_set["authority_binding"],
        "reviewed_runtime_binding": write_set["publication_registry"][
            "publication_metadata"
        ]["reviewed_runtime_binding"],
        "completion_required_after_exact_runtime_deployment": {
            "decision": None,
            "decision_recorded_at_utc": None,
            "reviewer": None,
            "runtime_health_proof_subject_sha256": None,
            "fresh_preflight_subject_sha256": None,
            "fresh_preflight_state_fingerprint_sha256": None,
            "production_target_identity_sha256": None,
            "authorizations": {key: None for key in POSITIVE_AUTHORIZATIONS},
        },
        "boundary": (
            "Unsealed or incomplete forms cannot authorize database mutation or "
            "publication. Ratification must bind this exact deployed runtime."
        ),
    }
    template = {
        "schema_version": "human_publication_activation_decision_template_v1",
        "artifact_id": ACTIVATION_TEMPLATE_ID,
        "sealed": False,
        "accepted": False,
        "subject": subject,
        "template_subject_sha256": semantic_hash(subject),
    }
    validate_activation_decision_template(template, write_set, authority)
    return template


def validate_activation_decision_template(
    template: dict[str, Any],
    write_set: dict[str, Any],
    authority: dict[str, Any],
) -> None:
    validate_write_set(write_set, authority=authority)
    body = template.get("subject", {})
    completion = body.get("completion_required_after_exact_runtime_deployment", {})
    if (
        template.get("schema_version")
        != "human_publication_activation_decision_template_v1"
        or template.get("artifact_id") != ACTIVATION_TEMPLATE_ID
        or template.get("sealed") is not False
        or template.get("accepted") is not False
        or template.get("template_subject_sha256") != semantic_hash(body)
        or body.get("candidate_write_set_binding")
        != activation_write_set_binding(write_set)
        or any(
            value is not None
            for value in completion.values()
            if not isinstance(value, dict)
        )
        or any(
            value is not None for value in completion.get("authorizations", {}).values()
        )
    ):
        raise StoreSafetyError("M13N activation decision template differs")


def publication_metadata_for_activation(
    write_set: dict[str, Any],
    candidate_authority: dict[str, Any],
    activation_authority: dict[str, Any],
    *,
    allow_test_authority: bool = False,
) -> dict[str, Any]:
    validate_write_set(write_set, authority=candidate_authority)
    candidate = load_candidate()
    metadata = copy.deepcopy(write_set["publication_registry"]["publication_metadata"])
    metadata["publication_activation_authority"] = copy.deepcopy(activation_authority)
    metadata["activation_authority_subject_sha256"] = activation_authority.get(
        "activation_authority_subject_sha256"
    )
    validate_education_positive_activation_authority(
        activation_authority,
        candidate=candidate,
        candidate_authority=candidate_authority,
        metadata=metadata,
        allow_test_authority=allow_test_authority,
    )
    return metadata


def _assert_bound_preflight(
    conn: Any,
    write_set: dict[str, Any],
    *,
    allow_test_activation_authority: bool,
) -> dict[str, Any]:
    actual = capture_preflight(
        conn,
        deployed_commit=write_set["preflight_binding"]["deployed_commit"],
        allow_test_activation_authority=allow_test_activation_authority,
    )
    if (
        actual["state_fingerprint_sha256"]
        != write_set["preflight_binding"]["state_fingerprint_sha256"]
    ):
        raise StoreSafetyError("database state drifted from M13N preflight")
    return actual


def _baseline_fingerprint_without_m13n(conn: Any, *, batch_key: str) -> str:
    keys = [M13M_ARTIFACT_ID, SOURCE_KEY, VALIDATION_KEY]
    queries = (
        (
            """SELECT deterministic_batch_key,source_commit_sha,manifest_sha256,status,
                      artifact_count,relationship_count
                 FROM editorial_artifact_batches
                WHERE deterministic_batch_key<>%s ORDER BY deterministic_batch_key""",
            (batch_key,),
        ),
        (
            """SELECT artifact_type,natural_key,schema_version,artifact_version,
                      content_sha256,source_manifest_sha256,source_commit_sha,batch_id,
                      member_bioguide_id,issue_id,congress,chamber,canonical_action_id,
                      episode_id,policy_family_id,editorial_status,benchmark_status,
                      production_eligible,review_route
                 FROM editorial_artifact_versions
                WHERE NOT natural_key=ANY(%s)
                ORDER BY natural_key,artifact_version,content_sha256""",
            (keys,),
        ),
        (
            """SELECT parent.natural_key AS parent_natural_key,
                      child.natural_key AS child_natural_key,relationship_type,ordinal,
                      metadata_jsonb
                 FROM editorial_artifact_relationships rel
                 JOIN editorial_artifact_versions parent
                   ON parent.artifact_id=rel.parent_artifact_id
                 JOIN editorial_artifact_versions child
                   ON child.artifact_id=rel.child_artifact_id
                WHERE NOT parent.natural_key=ANY(%s)
                  AND NOT child.natural_key=ANY(%s)
                ORDER BY parent.natural_key,relationship_type,ordinal,child.natural_key""",
            (keys, keys),
        ),
        (
            """SELECT registry.member_bioguide_id,registry.issue_id,artifact.natural_key,
                      artifact.artifact_version,registry.publicly_active,
                      registry.publication_metadata_jsonb
                 FROM editorial_publication_registry registry
                 JOIN editorial_artifact_versions artifact
                   ON artifact.artifact_id=registry.artifact_id
                WHERE NOT (registry.member_bioguide_id=%s AND registry.issue_id=%s)
                ORDER BY registry.member_bioguide_id,registry.issue_id""",
            (MEMBER_ID, ISSUE_ID),
        ),
    )
    return semantic_hash(
        [
            [_jsonable(dict(row)) for row in conn.execute(query, params).fetchall()]
            for query, params in queries
        ]
    )


def _postcheck(
    conn: Any,
    write_set: dict[str, Any],
    candidate_authority: dict[str, Any],
    activation_authority: dict[str, Any],
    *,
    allow_test_authority: bool,
) -> dict[str, Any]:
    if _counts(conn) != write_set["expected_counts"]["after"]:
        raise StoreSafetyError("M13N post-activation counts differ")
    rows = _registry_rows(conn)
    by_issue = {row["issue_id"]: row for row in rows}
    for issue_id, expected in write_set["rollback"][
        "baseline_registry_rows_unchanged"
    ].items():
        if _registry_identity(by_issue[issue_id]) != expected:
            raise StoreSafetyError(f"M13N changed existing {issue_id} row")
    education = by_issue.get(ISSUE_ID)
    metadata = publication_metadata_for_activation(
        write_set,
        candidate_authority,
        activation_authority,
        allow_test_authority=allow_test_authority,
    )
    if (
        len(rows) != 4
        or education is None
        or education["natural_key"] != M13M_ARTIFACT_ID
        or education["publication_metadata_jsonb"] != metadata
        or _baseline_fingerprint_without_m13n(
            conn, batch_key=write_set["deterministic_batch_key"]
        )
        != write_set["preflight_binding"]["state_fingerprint_sha256"]
    ):
        raise StoreSafetyError("M13N exact publication graph differs")
    selector = _selector_state(
        conn, allow_test_activation_authority=allow_test_authority
    )
    if (
        selector["scopes"]["119"][ISSUE_ID] != "reviewed_conclusion"
        or selector["scopes"]["all"][ISSUE_ID] != "reviewed_conclusion"
        or selector["scopes"]["118"][ISSUE_ID] != "receipts_only"
    ):
        raise StoreSafetyError("M13N Education selector postcondition differs")
    for issue_id in BASELINE_IDENTITIES:
        if (
            selector["scopes"]["119"][issue_id] != "reviewed_conclusion"
            or selector["scopes"]["all"][issue_id] != "reviewed_conclusion"
            or selector["scopes"]["118"][issue_id] != "receipts_only"
        ):
            raise StoreSafetyError(f"M13N changed {issue_id} selector behavior")
    return {
        "counts": _counts(conn),
        "registry": rows,
        "selector": selector,
        "baseline_fingerprint_unchanged": True,
    }


def _apply(
    conn: Any,
    write_set: dict[str, Any],
    candidate_authority: dict[str, Any],
    activation_authority: dict[str, Any],
    *,
    allow_test_authority: bool = False,
) -> dict[str, Any]:
    from psycopg.types.json import Jsonb

    validate_write_set(write_set, authority=candidate_authority)
    publication_metadata = publication_metadata_for_activation(
        write_set,
        candidate_authority,
        activation_authority,
        allow_test_authority=allow_test_authority,
    )
    if _counts(conn) == write_set["expected_counts"]["after"]:
        return {
            "already_applied": True,
            "postcheck": _postcheck(
                conn,
                write_set,
                candidate_authority,
                activation_authority,
                allow_test_authority=allow_test_authority,
            ),
        }
    bound = _assert_bound_preflight(
        conn,
        write_set,
        allow_test_activation_authority=allow_test_authority,
    )
    batch = conn.execute(
        """INSERT INTO editorial_artifact_batches
           (deterministic_batch_key,source_commit_sha,manifest_sha256,status,
            artifact_count,relationship_count,applied_at)
           VALUES (%s,%s,%s,'applied',3,2,NOW()) RETURNING batch_id""",
        (
            write_set["deterministic_batch_key"],
            write_set["source_commit_sha"],
            write_set["write_set_subject_sha256"],
        ),
    ).fetchone()
    batch_id = int(batch["batch_id"])
    ids: dict[str, int] = {}
    for item in write_set["artifacts"]:
        row = conn.execute(
            """INSERT INTO editorial_artifact_versions
               (artifact_type,natural_key,schema_version,artifact_version,payload_jsonb,
                content_sha256,source_manifest_sha256,source_commit_sha,batch_id,
                member_bioguide_id,issue_id,congress,chamber,canonical_action_id,
                episode_id,policy_family_id,editorial_status,benchmark_status,
                production_eligible,review_route)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               RETURNING artifact_id""",
            (
                item["artifact_type"],
                item["natural_key"],
                item["schema_version"],
                item["artifact_version"],
                Jsonb(item["payload"]),
                item["content_sha256"],
                item["source_manifest_sha256"],
                item["source_commit_sha"],
                batch_id,
                item["member_bioguide_id"],
                item["issue_id"],
                item["congress"],
                item["chamber"],
                item["canonical_action_id"],
                item["episode_id"],
                item["policy_family_id"],
                item["editorial_status"],
                item["benchmark_status"],
                item["production_eligible"],
                item["review_route"],
            ),
        ).fetchone()
        ids[item["natural_key"]] = int(row["artifact_id"])
    for relation in write_set["relationships"]:
        conn.execute(
            """INSERT INTO editorial_artifact_relationships
               (parent_artifact_id,child_artifact_id,relationship_type,ordinal,metadata_jsonb)
               VALUES (%s,%s,%s,%s,%s)""",
            (
                ids[relation["parent_natural_key"]],
                ids[relation["child_natural_key"]],
                relation["relationship_type"],
                relation["ordinal"],
                Jsonb(relation["metadata"]),
            ),
        )
    inserted = conn.execute(
        """INSERT INTO editorial_publication_registry
           (member_bioguide_id,issue_id,artifact_id,publicly_active,activated_at,
            deactivated_at,publication_metadata_jsonb)
           VALUES (%s,%s,%s,TRUE,NOW(),NULL,%s)""",
        (MEMBER_ID, ISSUE_ID, ids[M13M_ARTIFACT_ID], Jsonb(publication_metadata)),
    )
    if inserted.rowcount != 1:
        raise StoreSafetyError("M13N registry insert count differs")
    return {
        "already_applied": False,
        "batch_id": batch_id,
        "artifact_ids": sorted(ids.values()),
        "preflight": bound,
        "postcheck": _postcheck(
            conn,
            write_set,
            candidate_authority,
            activation_authority,
            allow_test_authority=allow_test_authority,
        ),
    }


def _rollback(
    conn: Any,
    write_set: dict[str, Any],
    candidate_authority: dict[str, Any],
    activation_authority: dict[str, Any],
    *,
    allow_test_authority: bool = False,
) -> dict[str, Any]:
    _postcheck(
        conn,
        write_set,
        candidate_authority,
        activation_authority,
        allow_test_authority=allow_test_authority,
    )
    batch = conn.execute(
        "SELECT batch_id FROM editorial_artifact_batches WHERE deterministic_batch_key=%s",
        (write_set["deterministic_batch_key"],),
    ).fetchone()
    if batch is None:
        raise StoreSafetyError("M13N rollback batch is absent")
    batch_id = int(batch["batch_id"])
    deleted_registry = conn.execute(
        "DELETE FROM editorial_publication_registry WHERE member_bioguide_id=%s AND issue_id=%s",
        (MEMBER_ID, ISSUE_ID),
    )
    deleted_relationships = conn.execute(
        """DELETE FROM editorial_artifact_relationships rel
            USING editorial_artifact_versions parent
            WHERE rel.parent_artifact_id=parent.artifact_id AND parent.batch_id=%s""",
        (batch_id,),
    )
    conn.execute(
        "SELECT set_config('app.editorial_artifact_rollback_batch',%s,true)",
        (write_set["deterministic_batch_key"],),
    )
    deleted_artifacts = conn.execute(
        "DELETE FROM editorial_artifact_versions WHERE batch_id=%s", (batch_id,)
    )
    deleted_batch = conn.execute(
        "DELETE FROM editorial_artifact_batches WHERE batch_id=%s", (batch_id,)
    )
    if (
        deleted_registry.rowcount,
        deleted_relationships.rowcount,
        deleted_artifacts.rowcount,
        deleted_batch.rowcount,
    ) != (1, 2, 3, 1):
        raise StoreSafetyError("M13N rollback write counts differ")
    fingerprint = _state_fingerprint(conn)
    if (
        _counts(conn) != write_set["expected_counts"]["before"]
        or fingerprint != write_set["rollback"]["restore_state_fingerprint_sha256"]
    ):
        raise StoreSafetyError("M13N rollback did not restore exact baseline")
    return {
        "counts": _counts(conn),
        "state_fingerprint_sha256": fingerprint,
        "selector": _selector_state(conn),
    }


def validate_production_execution_inputs(
    *,
    database_url: str,
    preflight: dict[str, Any],
    write_set: dict[str, Any],
    candidate_authority: dict[str, Any],
    activation_authority: dict[str, Any] | None,
    runtime_proof: dict[str, Any] | None,
) -> None:
    """Fail closed before opening a production mutation transaction."""

    if activation_authority is None:
        raise StoreSafetyError("exact positive activation authority is required")
    try:
        info = target_info(database_url, "production", None)
    except StoreSafetyError as exc:
        raise StoreSafetyError("refusing non-exact production target") from exc
    if target_identity_sha256(info) != PRODUCTION_TARGET_IDENTITY_SHA256:
        raise StoreSafetyError("production target identity differs")
    validate_preflight(preflight, require_execution_bindings=True)
    validate_write_set(write_set, authority=candidate_authority)
    if (
        write_set["preflight_binding"]["preflight_subject_sha256"]
        != preflight["preflight_subject_sha256"]
        or write_set["preflight_binding"]["state_fingerprint_sha256"]
        != preflight["state_fingerprint_sha256"]
        or preflight["production_target_identity_sha256"]
        != PRODUCTION_TARGET_IDENTITY_SHA256
    ):
        raise StoreSafetyError("production preflight/write-set binding differs")
    publication_metadata_for_activation(
        write_set,
        candidate_authority,
        activation_authority,
        allow_test_authority=False,
    )
    validate_production_execution_runtime(activation_authority, runtime_proof)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=(
            "manifest",
            "capture-runtime",
            "capture-preflight",
            "apply",
            "rollback",
        ),
    )
    parser.add_argument("--database-url")
    parser.add_argument("--base-url")
    parser.add_argument("--deployed-commit")
    parser.add_argument("--runtime-proof-path", type=Path)
    parser.add_argument("--preflight-path", type=Path)
    parser.add_argument("--authority-path", type=Path)
    parser.add_argument("--write-set-path", type=Path)
    parser.add_argument("--activation-authority-path", type=Path)
    parser.add_argument("--target", choices=("disposable", "production"))
    parser.add_argument("--confirm-production-activation", action="store_true")
    parser.add_argument("--confirm-production-rollback", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.mode == "manifest":
        print(json.dumps(reviewed_runtime_manifest(), sort_keys=True, indent=2))
        return 0
    if args.mode == "capture-runtime":
        if not args.base_url:
            raise StoreSafetyError("--base-url is required")
        print(
            json.dumps(capture_runtime_health(args.base_url), sort_keys=True, indent=2)
        )
        return 0
    if args.mode == "capture-preflight":
        if not args.database_url or not args.deployed_commit:
            raise StoreSafetyError("database URL and deployed commit are required")
        runtime = _load(args.runtime_proof_path) if args.runtime_proof_path else None
        if runtime is None:
            raise StoreSafetyError(
                "production preflight requires a fresh live runtime health proof"
            )
        info = target_info(args.database_url, "production", None)
        with _connect(args.database_url, autocommit=False) as conn:
            conn.execute("SET default_transaction_read_only=on")
            with conn.transaction():
                conn.execute("SET TRANSACTION READ ONLY")
                report = capture_preflight(
                    conn,
                    deployed_commit=args.deployed_commit,
                    runtime_health_proof=runtime,
                    production_target_identity_sha256=target_identity_sha256(info),
                )
        print(json.dumps(report, sort_keys=True, indent=2))
        return 0
    required = (
        args.database_url,
        args.preflight_path,
        args.authority_path,
        args.write_set_path,
        args.activation_authority_path,
        args.target,
    )
    if any(value is None for value in required):
        raise StoreSafetyError(
            "execution requires all exact governed inputs and target"
        )
    preflight = _load(args.preflight_path)
    authority = _load(args.authority_path)
    write_set = _load(args.write_set_path)
    activation = _load(args.activation_authority_path)
    allow_test = args.target == "disposable"
    if args.target == "production":
        if activation.get("test_only_synthetic") is True:
            raise StoreSafetyError(
                "synthetic activation authority cannot target production"
            )
        runtime = _load(args.runtime_proof_path) if args.runtime_proof_path else None
        validate_production_execution_inputs(
            database_url=args.database_url,
            preflight=preflight,
            write_set=write_set,
            candidate_authority=authority,
            activation_authority=activation,
            runtime_proof=runtime,
        )
        if args.mode == "apply" and not args.confirm_production_activation:
            raise StoreSafetyError(
                "explicit production activation confirmation required"
            )
        if args.mode == "rollback" and not args.confirm_production_rollback:
            raise StoreSafetyError("explicit production rollback confirmation required")
    with _connect(args.database_url, autocommit=False) as conn:
        with conn.transaction():
            conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (LOCK_KEY,))
            result = (
                _apply(
                    conn,
                    write_set,
                    authority,
                    activation,
                    allow_test_authority=allow_test,
                )
                if args.mode == "apply"
                else _rollback(
                    conn,
                    write_set,
                    authority,
                    activation,
                    allow_test_authority=allow_test,
                )
            )
    print(json.dumps(result, sort_keys=True, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
