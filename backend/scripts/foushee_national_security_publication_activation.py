"""M11N production-eligibility and publication-activation candidate tooling.

Production-facing modes are read-only. Mutation modes are deliberately limited
to disposable PostgreSQL targets until a later explicit activation authority.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import urlopen

from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.editorial_artifacts.bundle import semantic_hash  # noqa: E402
from app.editorial_artifacts.repository import EditorialArtifactRepository  # noqa: E402
from app.editorial_presentations.integration_candidate import (  # noqa: E402
    BLOCKED_ACTION_ID,
    load_site_integration_candidate,
    validate_site_integration_candidate,
)
from app.editorial_presentations.selector import (  # noqa: E402
    select_public_presentations,
)
from app.editorial_presentations.site_publication import (  # noqa: E402
    ACTIVATION_AUTHORITY_ID,
    ACTIVATION_AUTHORITY_SCHEMA_VERSION,
    ACTIVATION_REVIEWER_AUTHORITY,
    M11M_ARTIFACT_ID,
    M11M_FILE_SHA256,
    M11M_SUBJECT_SHA256,
    POSITIVE_AUTHORIZATIONS,
    validate_positive_activation_authority,
    validate_publication_authority,
)
from scripts.editorial_artifact_store import (  # noqa: E402
    EXPECTED_PRODUCTION_TARGET,
    StoreSafetyError,
    _connect,
    target_info,
)


MEMBER_ID = "F000477"
MEMBER_SLUG = "leg_valerie_p_foushee"
ISSUE_ID = "NATIONAL_SECURITY_FOREIGN"
CONGRESS = 119
POST_M11M_MAIN = "b12a0939b4452fb9dcc9ae150d8159ec0a18b6bd"
M11M_ACCEPTED_HEAD = "7e1d399e4dc2a2b49b083c7b4ed117a256293050"
M11M_ACCEPTED_PR = 145
AUTHORITY_ID = (
    "production-eligibility-publication-authority:"
    "f000477:national_security_foreign:119:v1"
)
WRITE_SET_ID = (
    "publication-activation-write-set:f000477:national_security_foreign:119:v1"
)
ACTIVATION_TEMPLATE_ID = (
    "human-publication-activation-decision-template:"
    "f000477:national_security_foreign:119:v1"
)
BUNDLE_ID = "foushee_national_security_foreign_119_publication_activation_v1"
SOURCE_KEY = f"{M11M_ARTIFACT_ID}:publication-source-manifest"
VALIDATION_KEY = f"{M11M_ARTIFACT_ID}:publication-validation"
LOCK_KEY = f"political_fingerprint:{BUNDLE_ID}"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

M11M_PATH = (
    ROOT / "docs/editorial/full_record_reviews/site_integration_candidates/"
    "f000477_national_security_foreign_119_v1/site_integration_candidate.json"
)
M11L_ROOT = (
    ROOT / "docs/editorial/full_record_reviews/public_wording_implementations/"
    "f000477_national_security_foreign_119_v1"
)
M11L_AUTHORITY_PATH = M11L_ROOT / "human_public_wording_authority.json"
M11L_IMPLEMENTATION_PATH = M11L_ROOT / "reviewed_wording_decision_implementation.json"
M11L_PARITY_PATH = M11L_ROOT / "implementation_parity_manifest.json"
OUTPUT_ROOT = (
    ROOT / "docs/editorial/full_record_reviews/publication_activation_candidates/"
    "f000477_national_security_foreign_119_v1"
)
PREFLIGHT_PATH = OUTPUT_ROOT / "current_production_preflight.json"
AUTHORITY_PATH = OUTPUT_ROOT / "production_eligibility_publication_authority.json"
WRITE_SET_PATH = OUTPUT_ROOT / "expected_production_write_set.json"
REVIEW_PACKET_PATH = OUTPUT_ROOT / "review_packet.json"
REVIEW_DOSSIER_PATH = OUTPUT_ROOT / "review_packet.md"
ACTIVATION_TEMPLATE_PATH = OUTPUT_ROOT / "human_activation_decision_template.json"
RUNTIME_PROOF_PATH = OUTPUT_ROOT / "runtime_health_proof.json"

RUNTIME_SOURCE_PATHS = (
    BACKEND / "app/api/positions.py",
    BACKEND / "app/editorial_presentations/selector.py",
    BACKEND / "app/editorial_presentations/site_publication.py",
    BACKEND / "scripts/foushee_national_security_publication_activation.py",
)
PRODUCTION_TARGET_IDENTITY_SHA256 = semantic_hash(EXPECTED_PRODUCTION_TARGET)

EXPECTED_M11L = {
    M11L_AUTHORITY_PATH: (
        "5c0c888c6c3569b2434fa6057d8be9290b22b7ed019e25e9a245150feaf5fffb"
    ),
    M11L_IMPLEMENTATION_PATH: (
        "42c4888fbc48eef65fb8038d89006fed225ded40361686561f893885902a285b"
    ),
    M11L_PARITY_PATH: (
        "3798d412ffc782759f15dc5d5f5a961f08c4a56897a07a50fd6d37bca4696686"
    ),
}
JUSTICE_NATURAL_KEY = (
    "public-issue-presentation-candidate:f000477:justice_public_safety:119:v1"
)
JUSTICE_CONTENT_SHA256 = (
    "1c088fc4a98e8442263899faffd7e203967cf60c387944884e4ce755d6ba7943"
)
CURRENT_COUNTS = {
    "batches": 4,
    "artifacts": 146,
    "relationships": 159,
    "publication_registry": 1,
}
EXPECTED_AFTER_COUNTS = {
    "batches": 5,
    "artifacts": 149,
    "relationships": 161,
    "publication_registry": 2,
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise StoreSafetyError(f"expected JSON object: {path}")
    return value


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str, sort_keys=True))


def _json_text(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _write_or_check(path: Path, content: str, *, check: bool) -> None:
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            raise StoreSafetyError(f"deterministic M11N artifact differs: {path}")
        return
    _write(path, content)


def canonical_file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _file_record(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "file_sha256": canonical_file_sha256(path),
    }


def reviewed_runtime_manifest() -> dict[str, Any]:
    files = [_file_record(path) for path in RUNTIME_SOURCE_PATHS]
    return {
        "schema_version": "m11n_reviewed_runtime_manifest_v1",
        "files": files,
        "reviewed_runtime_manifest_sha256": semantic_hash(files),
    }


def capture_runtime_health(base_url: str) -> dict[str, Any]:
    """Read the actual deployed health identity; never accept an expected SHA."""

    endpoint = urljoin(base_url.rstrip("/") + "/", "health")
    with urlopen(endpoint, timeout=20) as response:  # noqa: S310 - bounded operator URL
        health = json.load(response)
    commit = health.get("commit_sha")
    if not isinstance(commit, str) or not SHA40.fullmatch(commit):
        raise StoreSafetyError("live health endpoint lacks an exact commit SHA")
    body = {
        "schema_version": "m11n_live_runtime_health_proof_v1",
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
    proof: dict[str, Any], *, require_fresh: bool = False
) -> None:
    body = copy.deepcopy(proof)
    claimed = body.pop("runtime_health_proof_subject_sha256", None)
    if claimed != semantic_hash(body):
        raise StoreSafetyError("runtime health proof digest mismatch")
    if (
        proof.get("schema_version") != "m11n_live_runtime_health_proof_v1"
        or proof.get("deployed_commit") != proof.get("health_commit")
        or not SHA40.fullmatch(proof.get("deployed_commit", ""))
        or proof.get("reviewed_runtime_manifest_sha256")
        != reviewed_runtime_manifest()["reviewed_runtime_manifest_sha256"]
    ):
        raise StoreSafetyError("runtime health proof does not bind reviewed runtime")
    if require_fresh:
        try:
            captured = datetime.fromisoformat(proof["captured_at_utc"])
        except (KeyError, TypeError, ValueError) as exc:
            raise StoreSafetyError("runtime health proof timestamp is invalid") from exc
        age = datetime.now(timezone.utc) - captured.astimezone(timezone.utc)
        if age.total_seconds() < 0 or age.total_seconds() > 1800:
            raise StoreSafetyError("runtime health proof is not fresh")


def target_identity_sha256(info: dict[str, Any]) -> str:
    identity = {key: info[key] for key in ("scheme", "host", "port", "database")}
    return semantic_hash(identity)


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
    return {
        key: row[key]
        for key in (
            "member_bioguide_id",
            "issue_id",
            "artifact_id",
            "publicly_active",
            "natural_key",
            "artifact_version",
            "content_sha256",
            "source_commit_sha",
        )
    } | {
        "publication_metadata_sha256": semantic_hash(row["publication_metadata_jsonb"])
    }


def _target_rows(conn: Any) -> list[dict[str, Any]]:
    return [
        _jsonable(dict(row))
        for row in conn.execute(
            """SELECT artifact_id,natural_key,artifact_version,content_sha256
                 FROM editorial_artifact_versions
                WHERE natural_key=ANY(%s)
                ORDER BY natural_key,artifact_version""",
            ([M11M_ARTIFACT_ID, SOURCE_KEY, VALIDATION_KEY],),
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
            item["issue_id"]: {
                "tier": item["tier"],
                "requested_scope": item["requested_scope"],
            }
            for item in response["presentations"]
            if item["issue_id"] in {"JUSTICE_PUBLIC_SAFETY", ISSUE_ID}
        }
    return {"selector_rows": len(rows), "scopes": scopes}


def capture_preflight(
    conn: Any,
    *,
    deployed_commit: str,
    runtime_health_proof: dict[str, Any] | None = None,
    production_target_identity_sha256: str | None = None,
) -> dict[str, Any]:
    if not SHA40.fullmatch(deployed_commit):
        raise StoreSafetyError("deployed commit must be an exact lowercase SHA-40")
    counts = _counts(conn)
    registry = _registry_rows(conn)
    targets = _target_rows(conn)
    selector = _selector_state(conn)
    if counts != CURRENT_COUNTS:
        raise StoreSafetyError(f"unexpected current production counts: {counts}")
    if len(registry) != 1:
        raise StoreSafetyError("Justice is not the sole production publication")
    justice = registry[0]
    if (
        justice["member_bioguide_id"] != MEMBER_ID
        or justice["issue_id"] != "JUSTICE_PUBLIC_SAFETY"
        or justice["natural_key"] != JUSTICE_NATURAL_KEY
        or justice["content_sha256"] != JUSTICE_CONTENT_SHA256
        or justice["publicly_active"] is not True
    ):
        raise StoreSafetyError("accepted Justice production identity differs")
    if targets:
        raise StoreSafetyError("M11N natural keys already exist")
    if any(
        selector["scopes"][scope][ISSUE_ID]["tier"] != "receipts_only"
        for scope in ("119", "all", "118")
    ):
        raise StoreSafetyError("National Security selector is not fail-closed")
    if (
        selector["scopes"]["119"]["JUSTICE_PUBLIC_SAFETY"]["tier"]
        != "reviewed_conclusion"
        or selector["scopes"]["all"]["JUSTICE_PUBLIC_SAFETY"]["tier"]
        != "reviewed_conclusion"
        or selector["scopes"]["118"]["JUSTICE_PUBLIC_SAFETY"]["tier"] != "receipts_only"
    ):
        raise StoreSafetyError("accepted Justice selector state differs")
    report = {
        "schema_version": "m11n_current_production_preflight_v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "deployed_commit": deployed_commit,
        "transaction_read_only": True,
        "counts": counts,
        "state_fingerprint_sha256": _state_fingerprint(conn),
        "justice_registry_row": _registry_identity(justice),
        "m11n_target_rows": targets,
        "selector_pre_activation": selector,
    }
    if runtime_health_proof is not None:
        validate_runtime_health_proof(runtime_health_proof)
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


def validate_preflight(report: dict[str, Any]) -> None:
    body = copy.deepcopy(report)
    claimed = body.pop("preflight_subject_sha256", None)
    if claimed != semantic_hash(body):
        raise StoreSafetyError("M11N preflight digest mismatch")
    if (
        report.get("schema_version") != "m11n_current_production_preflight_v1"
        or report.get("transaction_read_only") is not True
        or report.get("counts") != CURRENT_COUNTS
        or report.get("m11n_target_rows") != []
        or not SHA40.fullmatch(report.get("deployed_commit", ""))
        or not SHA256.fullmatch(report.get("state_fingerprint_sha256", ""))
    ):
        raise StoreSafetyError("M11N preflight contract differs")
    justice = report["justice_registry_row"]
    if (
        justice["natural_key"] != JUSTICE_NATURAL_KEY
        or justice["content_sha256"] != JUSTICE_CONTENT_SHA256
        or justice["issue_id"] != "JUSTICE_PUBLIC_SAFETY"
        or justice["publicly_active"] is not True
    ):
        raise StoreSafetyError("M11N preflight Justice binding differs")
    runtime_binding = report.get("runtime_health_proof_binding")
    if runtime_binding is not None and (
        runtime_binding.get("deployed_commit") != report["deployed_commit"]
        or runtime_binding.get("reviewed_runtime_manifest_sha256")
        != reviewed_runtime_manifest()["reviewed_runtime_manifest_sha256"]
        or not SHA256.fullmatch(
            runtime_binding.get("runtime_health_proof_subject_sha256", "")
        )
    ):
        raise StoreSafetyError("M11N preflight live-runtime binding differs")
    target_binding = report.get("production_target_identity_sha256")
    if (
        target_binding is not None
        and target_binding != PRODUCTION_TARGET_IDENTITY_SHA256
    ):
        raise StoreSafetyError("M11N preflight target binding differs")


def build_authority(preflight: dict[str, Any]) -> dict[str, Any]:
    validate_preflight(preflight)
    candidate = load_site_integration_candidate(M11M_PATH)
    subject = {
        "decision": (
            "approve_production_eligibility_and_publication_activation_candidate"
        ),
        "decision_recorded_at_utc": "2026-08-14T02:49:38Z",
        "reviewer": "dhart54",
        "reviewer_authority": "publication_candidate_preparation_authority_v1",
        "member_bioguide_id": MEMBER_ID,
        "member_slug": MEMBER_SLUG,
        "issue_id": ISSUE_ID,
        "congress": CONGRESS,
        "accepted_m11m_binding": {
            "artifact_id": M11M_ARTIFACT_ID,
            "subject_sha256": M11M_SUBJECT_SHA256,
            "file_sha256": M11M_FILE_SHA256,
            "content_sha256": semantic_hash(candidate),
        },
        "repository_binding": {
            "accepted_m11m_pr": M11M_ACCEPTED_PR,
            "accepted_m11m_head": M11M_ACCEPTED_HEAD,
            "post_m11m_main": POST_M11M_MAIN,
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
            "reason": (
                "These are the existing immutable publication-table gates for an "
                "accepted full-record reference; they do not activate publication."
            ),
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
            "deployment": False,
        },
        "downstream_boundary": (
            "Independent ChatGPT review is required before any later production "
            "activation authorization. This authority cannot authorize its own "
            "database write, registry mutation, deployment, or publication."
        ),
    }
    authority = {
        "schema_version": (
            "site_integration_production_eligibility_publication_authority_v1"
        ),
        "artifact_id": AUTHORITY_ID,
        "immutable": True,
        "accepted": True,
        "subject": subject,
        "authority_subject_sha256": semantic_hash(subject),
    }
    validate_publication_authority(authority, candidate=candidate)
    return authority


def _artifact(
    *,
    artifact_type: str,
    natural_key: str,
    payload: dict[str, Any],
    source_manifest_sha256: str,
) -> dict[str, Any]:
    return {
        "artifact_type": artifact_type,
        "natural_key": natural_key,
        "schema_version": payload["schema_version"],
        "artifact_version": 1,
        "payload": payload,
        "content_sha256": semantic_hash(payload),
        "source_manifest_sha256": source_manifest_sha256,
        "source_commit_sha": POST_M11M_MAIN,
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
    candidate = load_site_integration_candidate(M11M_PATH)
    validate_publication_authority(authority, candidate=candidate)
    for path, expected in EXPECTED_M11L.items():
        if canonical_file_sha256(path) != expected:
            raise StoreSafetyError(f"accepted M11L file digest differs: {path.name}")
    source_files = [
        _file_record(path)
        for path in (
            M11M_PATH,
            M11L_AUTHORITY_PATH,
            M11L_IMPLEMENTATION_PATH,
            M11L_PARITY_PATH,
        )
    ]
    source_manifest_sha256 = semantic_hash(source_files)
    source_payload = {
        "schema_version": "editorial_publication_source_manifest_v1",
        "activation_bundle_id": BUNDLE_ID,
        "complete_required_sources": True,
        "source_files": source_files,
        "accepted_m11m_subject_sha256": M11M_SUBJECT_SHA256,
        "accepted_m11m_file_sha256": M11M_FILE_SHA256,
    }
    validation_payload = {
        "schema_version": "editorial_publication_validation_v1",
        "activation_bundle_id": BUNDLE_ID,
        "successful": True,
        "current": True,
        "blocking_findings": 0,
        "semantic_tier": "reviewed_conclusion",
        "approved_universe_actions": 82,
        "accepted_interpreted_actions": 81,
        "source_blocked_actions": [BLOCKED_ACTION_ID],
        "accepted_public_wording_items": 18,
        "accepted_m11m_subject_sha256": M11M_SUBJECT_SHA256,
        "accepted_m11m_file_sha256": M11M_FILE_SHA256,
        "production_activation_authorized": False,
    }
    artifacts = [
        _artifact(
            artifact_type="issue_public_presentation",
            natural_key=M11M_ARTIFACT_ID,
            payload=candidate,
            source_manifest_sha256=source_manifest_sha256,
        ),
        _artifact(
            artifact_type="source_manifest",
            natural_key=SOURCE_KEY,
            payload=source_payload,
            source_manifest_sha256=source_manifest_sha256,
        ),
        _artifact(
            artifact_type="standardization_validation_result",
            natural_key=VALIDATION_KEY,
            payload=validation_payload,
            source_manifest_sha256=source_manifest_sha256,
        ),
    ]
    artifacts.sort(key=lambda item: item["natural_key"])
    by_key = {item["natural_key"]: item for item in artifacts}
    relationships = sorted(
        [
            {
                "parent_natural_key": M11M_ARTIFACT_ID,
                "child_natural_key": SOURCE_KEY,
                "relationship_type": "uses_source_manifest",
                "ordinal": 0,
                "metadata": {"activation_bundle_id": BUNDLE_ID},
            },
            {
                "parent_natural_key": M11M_ARTIFACT_ID,
                "child_natural_key": VALIDATION_KEY,
                "relationship_type": "has_validation",
                "ordinal": 0,
                "metadata": {"activation_bundle_id": BUNDLE_ID},
            },
        ],
        key=lambda item: item["relationship_type"],
    )
    rollback_contract = {
        "delete_registry_primary_key": {
            "member_bioguide_id": MEMBER_ID,
            "issue_id": ISSUE_ID,
        },
        "delete_relationship_count": 2,
        "delete_artifact_natural_keys": sorted(
            [M11M_ARTIFACT_ID, SOURCE_KEY, VALIDATION_KEY]
        ),
        "delete_batch_key": f"{BUNDLE_ID}-{POST_M11M_MAIN[:8]}",
        "restore_counts": CURRENT_COUNTS,
        "restore_state_fingerprint_sha256": preflight["state_fingerprint_sha256"],
        "justice_registry_row_unchanged": preflight["justice_registry_row"],
    }
    authority_text = _json_text(authority)
    metadata = {
        "activation_bundle_id": BUNDLE_ID,
        "production_eligibility_publication_authority": authority,
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "authority_file_sha256": hashlib.sha256(
            authority_text.encode("utf-8")
        ).hexdigest(),
        "accepted_m11m_subject_sha256": M11M_SUBJECT_SHA256,
        "accepted_m11m_file_sha256": M11M_FILE_SHA256,
        "presentation_natural_key": M11M_ARTIFACT_ID,
        "presentation_artifact_version": 1,
        "active_artifact_sha256": by_key[M11M_ARTIFACT_ID]["content_sha256"],
        "validation_natural_key": VALIDATION_KEY,
        "validation_artifact_version": 1,
        "validation_content_sha256": by_key[VALIDATION_KEY]["content_sha256"],
        "source_manifest_natural_key": SOURCE_KEY,
        "source_manifest_artifact_version": 1,
        "source_manifest_content_sha256": by_key[SOURCE_KEY]["content_sha256"],
        "relationship_metadata": {"activation_bundle_id": BUNDLE_ID},
        "candidate_preparation_authority_binding": {
            "artifact_id": AUTHORITY_ID,
            "authority_subject_sha256": authority["authority_subject_sha256"],
            "authority_file_sha256": hashlib.sha256(
                authority_text.encode("utf-8")
            ).hexdigest(),
        },
        "preflight_binding": {
            "preflight_subject_sha256": preflight["preflight_subject_sha256"],
            "state_fingerprint_sha256": preflight["state_fingerprint_sha256"],
        },
        "reviewed_runtime_binding": reviewed_runtime_manifest(),
        "production_target_identity_sha256": PRODUCTION_TARGET_IDENTITY_SHA256,
        "rollback_binding": rollback_contract,
        "activation_authority_contract": {
            "artifact_id": ACTIVATION_AUTHORITY_ID,
            "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
            "reviewer_authority": ACTIVATION_REVIEWER_AUTHORITY,
            "required_authorizations": POSITIVE_AUTHORIZATIONS,
        },
    }
    body = {
        "schema_version": "site_integration_publication_activation_write_set_v1",
        "artifact_id": WRITE_SET_ID,
        "bundle_id": BUNDLE_ID,
        "deterministic_batch_key": f"{BUNDLE_ID}-{POST_M11M_MAIN[:8]}",
        "source_commit_sha": POST_M11M_MAIN,
        "accepted_m11m_binding": authority["subject"]["accepted_m11m_binding"],
        "authority_binding": {
            "artifact_id": AUTHORITY_ID,
            "authority_subject_sha256": authority["authority_subject_sha256"],
            "authority_file_sha256": metadata["authority_file_sha256"],
        },
        "preflight_binding": {
            "preflight_subject_sha256": preflight["preflight_subject_sha256"],
            "state_fingerprint_sha256": preflight["state_fingerprint_sha256"],
            "counts": preflight["counts"],
            "deployed_commit": preflight["deployed_commit"],
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
            "presentation_natural_key": M11M_ARTIFACT_ID,
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
            "justice_rows_touched": 0,
        },
        "public_smoke_contract": {
            "NATIONAL_SECURITY_FOREIGN": {
                "119": "reviewed_conclusion",
                "all": "reviewed_conclusion_with_reviewed_119_boundary",
                "118": "receipts_only",
            },
            "JUSTICE_PUBLIC_SAFETY": {
                "119": "reviewed_conclusion_unchanged",
                "all": "reviewed_conclusion_unchanged",
                "118": "receipts_only_unchanged",
            },
        },
        "rollback": rollback_contract,
        "activation_authorized": False,
        "production_write_authorized": False,
        "next_required_gate": "independent_chatgpt_mechanical_review",
        "finalization_required": {
            "fresh_live_runtime_health_proof": True,
            "fresh_production_preflight": True,
            "sealed_positive_activation_authority": True,
        },
    }
    body["write_set_subject_sha256"] = semantic_hash(body)
    validate_write_set(body, authority=authority)
    return body


def validate_write_set(write_set: dict[str, Any], *, authority: dict[str, Any]) -> None:
    candidate = load_site_integration_candidate(M11M_PATH)
    validate_site_integration_candidate(candidate)
    validate_publication_authority(authority, candidate=candidate)
    body = copy.deepcopy(write_set)
    claimed = body.pop("write_set_subject_sha256", None)
    if claimed != semantic_hash(body):
        raise StoreSafetyError("M11N write-set digest mismatch")
    if (
        write_set.get("schema_version")
        != "site_integration_publication_activation_write_set_v1"
        or write_set.get("artifact_id") != WRITE_SET_ID
        or write_set.get("bundle_id") != BUNDLE_ID
        or write_set.get("source_commit_sha") != POST_M11M_MAIN
        or write_set.get("expected_counts")
        != {"before": CURRENT_COUNTS, "after": EXPECTED_AFTER_COUNTS}
        or write_set.get("activation_authorized") is not False
        or write_set.get("production_write_authorized") is not False
    ):
        raise StoreSafetyError("M11N write-set identity or authority differs")
    if write_set.get("write_caps") != {
        "batch_inserts": 1,
        "artifact_inserts": 3,
        "relationship_inserts": 2,
        "registry_inserts": 1,
        "registry_updates": 0,
        "deletes_during_activation": 0,
        "justice_rows_touched": 0,
    }:
        raise StoreSafetyError("M11N write caps differ")
    if len(write_set["artifacts"]) != 3 or len(write_set["relationships"]) != 2:
        raise StoreSafetyError("M11N activation graph size differs")
    by_key = {item["natural_key"]: item for item in write_set["artifacts"]}
    if set(by_key) != {M11M_ARTIFACT_ID, SOURCE_KEY, VALIDATION_KEY}:
        raise StoreSafetyError("M11N activation natural keys differ")
    if by_key[M11M_ARTIFACT_ID]["payload"] != candidate:
        raise StoreSafetyError("M11N rewrote the accepted M11M artifact")
    for artifact in write_set["artifacts"]:
        if (
            artifact["content_sha256"] != semantic_hash(artifact["payload"])
            or artifact["editorial_status"] != "human_approved"
            or artifact["benchmark_status"] != "gold_benchmark"
            or artifact["production_eligible"] is not True
        ):
            raise StoreSafetyError("M11N artifact persistence gate differs")
    validation = by_key[VALIDATION_KEY]["payload"]
    if (
        validation["source_blocked_actions"] != [BLOCKED_ACTION_ID]
        or validation["production_activation_authorized"] is not False
        or validation["accepted_interpreted_actions"] != 81
        or validation["approved_universe_actions"] != 82
    ):
        raise StoreSafetyError("M11N H.R. 8800 or accounting boundary differs")
    metadata = write_set["publication_registry"]["publication_metadata"]
    validate_publication_authority(
        metadata["production_eligibility_publication_authority"],
        candidate=candidate,
    )
    if (
        write_set["rollback"]["justice_registry_row_unchanged"]["content_sha256"]
        != JUSTICE_CONTENT_SHA256
    ):
        raise StoreSafetyError("M11N rollback does not isolate Justice")
    metadata = write_set["publication_registry"]["publication_metadata"]
    if (
        metadata.get("candidate_preparation_authority_binding")
        != write_set["authority_binding"]
        or metadata.get("preflight_binding")
        != {
            "preflight_subject_sha256": write_set["preflight_binding"][
                "preflight_subject_sha256"
            ],
            "state_fingerprint_sha256": write_set["preflight_binding"][
                "state_fingerprint_sha256"
            ],
        }
        or metadata.get("production_target_identity_sha256")
        != PRODUCTION_TARGET_IDENTITY_SHA256
        or metadata.get("rollback_binding") != write_set.get("rollback")
        or metadata.get("activation_authority_contract")
        != {
            "artifact_id": ACTIVATION_AUTHORITY_ID,
            "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
            "reviewer_authority": ACTIVATION_REVIEWER_AUTHORITY,
            "required_authorizations": POSITIVE_AUTHORIZATIONS,
        }
    ):
        raise StoreSafetyError("M11N activation-authority contract differs")


def activation_write_set_binding(write_set: dict[str, Any]) -> dict[str, str]:
    return {
        "artifact_id": WRITE_SET_ID,
        "write_set_subject_sha256": write_set["write_set_subject_sha256"],
    }


def build_activation_decision_template(
    write_set: dict[str, Any], authority: dict[str, Any]
) -> dict[str, Any]:
    """Create an unsealed decision form; this is not live authority."""

    validate_write_set(write_set, authority=authority)
    metadata = write_set["publication_registry"]["publication_metadata"]
    subject = {
        "decision_options": [
            "approve_exact_publication_activation",
            "reject_publication_activation",
        ],
        "required_reviewer_authority": ACTIVATION_REVIEWER_AUTHORITY,
        "product_owner": "dhart54",
        "fixed_bindings": {
            "member_bioguide_id": MEMBER_ID,
            "issue_id": ISSUE_ID,
            "congress": CONGRESS,
            "accepted_m11m_binding": write_set["accepted_m11m_binding"],
            "candidate_preparation_authority_binding": write_set["authority_binding"],
            "activation_write_set_binding": activation_write_set_binding(write_set),
            "publication_registry_target": {
                "member_bioguide_id": MEMBER_ID,
                "issue_id": ISSUE_ID,
                "presentation_natural_key": M11M_ARTIFACT_ID,
                "presentation_artifact_version": 1,
            },
            "presentation_content_sha256": metadata["active_artifact_sha256"],
            "candidate_preflight_binding": metadata["preflight_binding"],
            "reviewed_runtime_manifest_sha256": metadata["reviewed_runtime_binding"][
                "reviewed_runtime_manifest_sha256"
            ],
            "production_target_identity_sha256": (PRODUCTION_TARGET_IDENTITY_SHA256),
            "exact_bounded_rollback": write_set["rollback"],
        },
        "completion_required_after_live_runtime_deployment": {
            "decision": None,
            "reviewer": None,
            "decision_recorded_at_utc": None,
            "fresh_preflight_subject_sha256": None,
            "fresh_preflight_state_fingerprint_sha256": None,
            "reviewed_runtime_commit": None,
            "deployed_runtime_commit": None,
            "live_health_proof_subject_sha256": None,
            "authorizations": {key: None for key in POSITIVE_AUTHORIZATIONS},
        },
        "ratification_boundary": (
            "This unsealed template cannot authorize selection or mutation. A fresh "
            "live-runtime health proof and production preflight must be filled and "
            "the exact sealed authority mechanically ratified before apply."
        ),
    }
    template = {
        "schema_version": "m11n_publication_activation_decision_template_v1",
        "artifact_id": ACTIVATION_TEMPLATE_ID,
        "immutable": True,
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
    subject = template.get("subject")
    if (
        template.get("schema_version")
        != "m11n_publication_activation_decision_template_v1"
        or template.get("artifact_id") != ACTIVATION_TEMPLATE_ID
        or template.get("immutable") is not True
        or template.get("sealed") is not False
        or template.get("accepted") is not False
        or not isinstance(subject, dict)
        or template.get("template_subject_sha256") != semantic_hash(subject)
        or subject["fixed_bindings"]["activation_write_set_binding"]
        != activation_write_set_binding(write_set)
        or any(
            value is not None
            for value in subject["completion_required_after_live_runtime_deployment"][
                "authorizations"
            ].values()
        )
    ):
        raise StoreSafetyError("M11N activation decision template differs")


def publication_metadata_for_activation(
    write_set: dict[str, Any],
    candidate_authority: dict[str, Any],
    activation_authority: dict[str, Any],
    *,
    allow_test_authority: bool = False,
) -> dict[str, Any]:
    candidate = load_site_integration_candidate(M11M_PATH)
    metadata = copy.deepcopy(write_set["publication_registry"]["publication_metadata"])
    metadata["activation_write_set_binding"] = activation_write_set_binding(write_set)
    metadata["publication_activation_authority"] = copy.deepcopy(activation_authority)
    metadata["activation_authority_subject_sha256"] = activation_authority.get(
        "activation_authority_subject_sha256"
    )
    validate_positive_activation_authority(
        activation_authority,
        candidate=candidate,
        candidate_authority=candidate_authority,
        metadata=metadata,
        allow_test_authority=allow_test_authority,
    )
    return metadata


def _review_packet(
    preflight: dict[str, Any],
    authority: dict[str, Any],
    write_set: dict[str, Any],
    activation_template: dict[str, Any],
) -> dict[str, Any]:
    packet = {
        "schema_version": "m11n_review_packet_v1",
        "milestone": "M11N",
        "exact_base": POST_M11M_MAIN,
        "accepted_m11m_binding": authority["subject"]["accepted_m11m_binding"],
        "candidate_preparation_authority": {
            "artifact_id": AUTHORITY_ID,
            "authority_subject_sha256": authority["authority_subject_sha256"],
            "file_sha256": hashlib.sha256(
                _json_text(authority).encode("utf-8")
            ).hexdigest(),
        },
        "write_set": {
            "artifact_id": WRITE_SET_ID,
            "write_set_subject_sha256": write_set["write_set_subject_sha256"],
            "file_sha256": hashlib.sha256(
                _json_text(write_set).encode("utf-8")
            ).hexdigest(),
        },
        "activation_authority_template": {
            "artifact_id": ACTIVATION_TEMPLATE_ID,
            "template_subject_sha256": activation_template["template_subject_sha256"],
            "file_sha256": hashlib.sha256(
                _json_text(activation_template).encode("utf-8")
            ).hexdigest(),
            "sealed": False,
            "accepted": False,
        },
        "current_production_state": {
            "captured_at_utc": preflight["captured_at_utc"],
            "deployed_commit": preflight["deployed_commit"],
            "transaction_read_only": preflight["transaction_read_only"],
            "counts": preflight["counts"],
            "state_fingerprint_sha256": preflight["state_fingerprint_sha256"],
            "selector_pre_activation": preflight["selector_pre_activation"],
        },
        "expected_production_writes": write_set["write_caps"],
        "expected_counts": write_set["expected_counts"],
        "rollback": write_set["rollback"],
        "justice_isolation": {
            "natural_key": JUSTICE_NATURAL_KEY,
            "content_sha256": JUSTICE_CONTENT_SHA256,
            "rows_touched": 0,
        },
        "blocked_action": {
            "action_id": BLOCKED_ACTION_ID,
            "state": "source_blocked_uninterpreted_outside_public_findings",
        },
        "authorization_boundary": {
            "production_write": False,
            "publication_activation": False,
            "registry_mutation": False,
            "deployment": False,
        },
        "future_activation_sequence": [
            "merge the mechanically accepted M11N runtime",
            "deploy that exact runtime while the registry target remains absent",
            "verify National Security remains receipts-only",
            "capture the actual live /health commit identity",
            "capture a fresh read-only production preflight bound to that health proof",
            "finalize the write set and seal a distinct positive activation authority",
            "stop for a small mechanical ratification",
            "apply the exact authority-bound write and verify live production",
        ],
        "required_review": "independent_chatgpt_mechanical_review",
    }
    packet["review_packet_subject_sha256"] = semantic_hash(packet)
    return packet


def _review_markdown(packet: dict[str, Any]) -> str:
    writes = packet["expected_production_writes"]
    return "\n".join(
        [
            "# M11N National Security Production-Eligibility Review",
            "",
            "This is a content-bound publication-activation candidate. It does not authorize or perform a production write.",
            "",
            f"- Exact base: `{packet['exact_base']}`",
            f"- Accepted M11M artifact: `{packet['accepted_m11m_binding']['artifact_id']}`",
            f"- M11M subject: `{packet['accepted_m11m_binding']['subject_sha256']}`",
            f"- Preparation authority subject: `{packet['candidate_preparation_authority']['authority_subject_sha256']}`",
            f"- Write-set subject: `{packet['write_set']['write_set_subject_sha256']}`",
            f"- Unsealed activation template: `{packet['activation_authority_template']['template_subject_sha256']}`",
            "",
            "## Expected write envelope",
            "",
            f"- 1 batch, {writes['artifact_inserts']} artifacts, {writes['relationship_inserts']} relationships, and {writes['registry_inserts']} new registry row.",
            "- No updates, no activation-time deletes, and zero Justice rows touched.",
            "- Rollback deletes only the exact National Security registry row and its new immutable batch graph.",
            "",
            "## Current public boundary",
            "",
            "- Justice remains active and unchanged.",
            "- National Security remains receipts-only before activation.",
            "- H.R. 8800 remains source-blocked, uninterpreted, and excluded from public findings.",
            "- Production write, publication activation, registry mutation, and deployment remain unauthorized.",
            "- The preparation authority alone cannot make the candidate publicly selectable.",
            "",
            "## Required next decision",
            "",
            "Independent ChatGPT mechanical review of the exact authority, write set, current preflight, disposable apply/idempotency/rollback proof, selector behavior, and hosted CI.",
            "",
        ]
    )


def build(
    *, check: bool = False, preflight_path: Path = PREFLIGHT_PATH
) -> dict[str, Any]:
    preflight = _load(preflight_path)
    validate_preflight(preflight)
    authority = build_authority(preflight)
    write_set = build_write_set(preflight, authority)
    activation_template = build_activation_decision_template(write_set, authority)
    packet = _review_packet(preflight, authority, write_set, activation_template)
    outputs = {
        AUTHORITY_PATH: _json_text(authority),
        WRITE_SET_PATH: _json_text(write_set),
        ACTIVATION_TEMPLATE_PATH: _json_text(activation_template),
        REVIEW_PACKET_PATH: _json_text(packet),
        REVIEW_DOSSIER_PATH: _review_markdown(packet),
    }
    for path, content in outputs.items():
        _write_or_check(path, content, check=check)
    return {
        "authority": authority,
        "write_set": write_set,
        "activation_template": activation_template,
        "review_packet": packet,
    }


def _assert_bound_preflight(conn: Any, write_set: dict[str, Any]) -> dict[str, Any]:
    actual = capture_preflight(
        conn, deployed_commit=write_set["preflight_binding"]["deployed_commit"]
    )
    if (
        actual["state_fingerprint_sha256"]
        != write_set["preflight_binding"]["state_fingerprint_sha256"]
    ):
        raise StoreSafetyError("database state drifted from M11N preflight")
    return actual


def _baseline_fingerprint_without_m11n(conn: Any, *, batch_key: str) -> str:
    keys = [M11M_ARTIFACT_ID, SOURCE_KEY, VALIDATION_KEY]
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
    allow_test_authority: bool = False,
) -> dict[str, Any]:
    if _counts(conn) != write_set["expected_counts"]["after"]:
        raise StoreSafetyError("M11N post-activation counts differ")
    batch = conn.execute(
        """SELECT deterministic_batch_key,source_commit_sha,manifest_sha256,status,
                  artifact_count,relationship_count
             FROM editorial_artifact_batches WHERE deterministic_batch_key=%s""",
        (write_set["deterministic_batch_key"],),
    ).fetchall()
    expected_batch = {
        "deterministic_batch_key": write_set["deterministic_batch_key"],
        "source_commit_sha": write_set["source_commit_sha"],
        "manifest_sha256": write_set["write_set_subject_sha256"],
        "status": "applied",
        "artifact_count": 3,
        "relationship_count": 2,
    }
    if [_jsonable(dict(row)) for row in batch] != [expected_batch]:
        raise StoreSafetyError("M11N exact batch graph differs")
    artifact_rows = [
        _jsonable(dict(row))
        for row in conn.execute(
            """SELECT natural_key,artifact_type,schema_version,artifact_version,
                      content_sha256,source_manifest_sha256,source_commit_sha,
                      member_bioguide_id,issue_id,congress,chamber,editorial_status,
                      benchmark_status,production_eligible,payload_jsonb
                 FROM editorial_artifact_versions WHERE natural_key=ANY(%s)
                 ORDER BY natural_key""",
            ([M11M_ARTIFACT_ID, SOURCE_KEY, VALIDATION_KEY],),
        ).fetchall()
    ]
    expected_artifacts = []
    for item in sorted(write_set["artifacts"], key=lambda row: row["natural_key"]):
        expected_artifacts.append(
            {
                key: item[key]
                for key in (
                    "natural_key",
                    "artifact_type",
                    "schema_version",
                    "artifact_version",
                    "content_sha256",
                    "source_manifest_sha256",
                    "source_commit_sha",
                    "member_bioguide_id",
                    "issue_id",
                    "congress",
                    "chamber",
                    "editorial_status",
                    "benchmark_status",
                    "production_eligible",
                )
            }
            | {"payload_jsonb": item["payload"]}
        )
    if artifact_rows != expected_artifacts:
        raise StoreSafetyError("M11N exact artifact graph differs")
    relationship_rows = [
        _jsonable(dict(row))
        for row in conn.execute(
            """SELECT parent.natural_key AS parent_natural_key,
                      child.natural_key AS child_natural_key,
                      rel.relationship_type,rel.ordinal,rel.metadata_jsonb AS metadata
                 FROM editorial_artifact_relationships rel
                 JOIN editorial_artifact_versions parent
                   ON parent.artifact_id=rel.parent_artifact_id
                 JOIN editorial_artifact_versions child
                   ON child.artifact_id=rel.child_artifact_id
                WHERE parent.natural_key=%s
                ORDER BY rel.relationship_type,rel.ordinal,child.natural_key""",
            (M11M_ARTIFACT_ID,),
        ).fetchall()
    ]
    if relationship_rows != write_set["relationships"]:
        raise StoreSafetyError("M11N exact relationship graph differs")
    registry = _registry_rows(conn)
    justice = next(
        row for row in registry if row["issue_id"] == "JUSTICE_PUBLIC_SAFETY"
    )
    national_security = next(
        (row for row in registry if row["issue_id"] == ISSUE_ID), None
    )
    if (
        _registry_identity(justice)
        != write_set["rollback"]["justice_registry_row_unchanged"]
    ):
        raise StoreSafetyError("M11N changed the Justice registry row")
    if (
        national_security is None
        or national_security["natural_key"] != M11M_ARTIFACT_ID
        or national_security["content_sha256"]
        != write_set["publication_registry"]["publication_metadata"][
            "active_artifact_sha256"
        ]
    ):
        raise StoreSafetyError("M11N National Security registry identity differs")
    expected_metadata = publication_metadata_for_activation(
        write_set,
        candidate_authority,
        activation_authority,
        allow_test_authority=allow_test_authority,
    )
    if national_security["publication_metadata_jsonb"] != expected_metadata:
        raise StoreSafetyError("M11N exact publication registry metadata differs")
    if (
        len(registry) != 2
        or _baseline_fingerprint_without_m11n(
            conn, batch_key=write_set["deterministic_batch_key"]
        )
        != write_set["preflight_binding"]["state_fingerprint_sha256"]
    ):
        raise StoreSafetyError("M11N changed Justice or unrelated production rows")
    selector = _selector_state(
        conn, allow_test_activation_authority=allow_test_authority
    )
    ns = selector["scopes"]
    if (
        ns["119"][ISSUE_ID]["tier"] != "reviewed_conclusion"
        or ns["all"][ISSUE_ID]["tier"] != "reviewed_conclusion"
        or ns["118"][ISSUE_ID]["tier"] != "receipts_only"
    ):
        raise StoreSafetyError("M11N public selector postcondition differs")
    return {
        "counts": _counts(conn),
        "batch": expected_batch,
        "artifacts": artifact_rows,
        "relationships": relationship_rows,
        "registry": registry,
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
    bound = _assert_bound_preflight(conn, write_set)
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
        (
            MEMBER_ID,
            ISSUE_ID,
            ids[M11M_ARTIFACT_ID],
            Jsonb(publication_metadata),
        ),
    )
    if inserted.rowcount != 1:
        raise StoreSafetyError("M11N registry insert count differs")
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
        raise StoreSafetyError("M11N rollback batch is absent")
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
        raise StoreSafetyError("M11N rollback write counts differ")
    if _counts(conn) != write_set["expected_counts"]["before"]:
        raise StoreSafetyError("M11N rollback counts differ")
    fingerprint = _state_fingerprint(conn)
    if fingerprint != write_set["rollback"]["restore_state_fingerprint_sha256"]:
        raise StoreSafetyError("M11N rollback fingerprint differs")
    return {
        "counts": _counts(conn),
        "state_fingerprint_sha256": fingerprint,
        "selector": _selector_state(conn),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=(
            "capture-runtime",
            "capture-preflight",
            "build",
            "dry-run",
            "apply",
            "postcheck",
            "rollback",
        ),
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--database-url")
    parser.add_argument(
        "--target", choices=("disposable", "production"), default="disposable"
    )
    parser.add_argument("--deployed-commit", default=POST_M11M_MAIN)
    parser.add_argument("--health-base-url")
    parser.add_argument("--runtime-proof-path", type=Path, default=RUNTIME_PROOF_PATH)
    parser.add_argument("--preflight-path", type=Path, default=PREFLIGHT_PATH)
    parser.add_argument("--report-path", type=Path, default=PREFLIGHT_PATH)
    parser.add_argument("--write-set-path", type=Path, default=WRITE_SET_PATH)
    parser.add_argument("--authority-path", type=Path, default=AUTHORITY_PATH)
    parser.add_argument("--activation-authority-path", type=Path)
    parser.add_argument("--confirm-write-set-digest")
    parser.add_argument("--confirm-activation-authority-digest")
    parser.add_argument("--confirm-production-activation", action="store_true")
    parser.add_argument("--confirm-production-rollback", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.mode == "capture-runtime":
        if not args.health_base_url:
            raise StoreSafetyError("capture-runtime requires --health-base-url")
        proof = capture_runtime_health(args.health_base_url)
        _write(args.runtime_proof_path, _json_text(proof))
        print(_json_text(proof))
        return 0
    if args.mode == "build":
        result = build(check=args.check, preflight_path=args.preflight_path)
        print(
            json.dumps(
                {
                    "authority_subject_sha256": result["authority"][
                        "authority_subject_sha256"
                    ],
                    "write_set_subject_sha256": result["write_set"][
                        "write_set_subject_sha256"
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.mode in {"dry-run", "apply", "postcheck", "rollback"} and (
        args.activation_authority_path is None
    ):
        raise StoreSafetyError("exact positive activation authority is required")
    load_dotenv(BACKEND / ".env")
    db_url = args.database_url or (
        os.getenv("DATABASE_URL")
        if args.target == "production"
        else os.getenv("M11N_DISPOSABLE_DATABASE_URL")
    )
    if not db_url:
        raise StoreSafetyError("an explicit database URL is required")
    db_target = target_info(db_url, args.target, None)
    if args.mode == "capture-preflight":
        runtime_proof = (
            _load(args.runtime_proof_path) if args.runtime_proof_path.exists() else None
        )
        if args.target == "production" and runtime_proof is None:
            raise StoreSafetyError(
                "production preflight requires a fresh live runtime health proof"
            )
        deployed_commit = (
            runtime_proof["deployed_commit"]
            if runtime_proof is not None
            else args.deployed_commit
        )
        with _connect(db_url, autocommit=True) as conn:
            conn.execute("SET default_transaction_read_only=on")
            with conn.transaction():
                conn.execute("SET TRANSACTION READ ONLY")
                report = capture_preflight(
                    conn,
                    deployed_commit=deployed_commit,
                    runtime_health_proof=runtime_proof,
                    production_target_identity_sha256=(
                        target_identity_sha256(db_target)
                        if args.target == "production"
                        else None
                    ),
                )
        _write(args.report_path, _json_text(report))
        print(_json_text(report))
        return 0
    authority = _load(args.authority_path)
    write_set = _load(args.write_set_path)
    validate_write_set(write_set, authority=authority)
    activation_authority = _load(args.activation_authority_path)
    activation_digest = activation_authority.get("activation_authority_subject_sha256")
    if args.confirm_activation_authority_digest != activation_digest:
        raise StoreSafetyError(
            "exact activation-authority digest confirmation required"
        )
    allow_test_authority = args.target == "disposable"
    publication_metadata_for_activation(
        write_set,
        authority,
        activation_authority,
        allow_test_authority=allow_test_authority,
    )
    if args.target == "production":
        if activation_authority.get("test_only_synthetic") is True:
            raise StoreSafetyError(
                "synthetic activation authority cannot target production"
            )
        if not args.runtime_proof_path.exists():
            raise StoreSafetyError("production operation requires live runtime proof")
        runtime_proof = _load(args.runtime_proof_path)
        validate_runtime_health_proof(runtime_proof, require_fresh=True)
        authority_runtime = activation_authority["subject"]["runtime_binding"]
        if (
            write_set["preflight_binding"].get("runtime_health_proof_binding") is None
            or write_set["preflight_binding"].get("production_target_identity_sha256")
            != target_identity_sha256(db_target)
            or activation_authority["subject"]["production_target_identity_sha256"]
            != target_identity_sha256(db_target)
            or authority_runtime["deployed_commit"] != runtime_proof["deployed_commit"]
            or authority_runtime["health_proof_subject_sha256"]
            != runtime_proof["runtime_health_proof_subject_sha256"]
        ):
            raise StoreSafetyError(
                "production operation lacks fresh runtime/preflight/target binding"
            )
        if args.mode in {"dry-run", "apply"} and not args.confirm_production_activation:
            raise StoreSafetyError(
                "explicit production activation confirmation required"
            )
        if args.mode == "rollback" and not args.confirm_production_rollback:
            raise StoreSafetyError("explicit production rollback confirmation required")
    if args.mode in {"dry-run", "apply", "rollback"} and (
        args.confirm_write_set_digest != write_set["write_set_subject_sha256"]
    ):
        raise StoreSafetyError("exact M11N write-set digest confirmation required")
    read_only = args.mode == "postcheck"
    with _connect(db_url, autocommit=read_only) as conn:
        if read_only:
            conn.execute("SET default_transaction_read_only=on")
        with conn.transaction(force_rollback=args.mode == "dry-run"):
            conn.execute("SET LOCAL lock_timeout='10000ms'")
            conn.execute("SET LOCAL statement_timeout='120000ms'")
            if not read_only:
                conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (LOCK_KEY,))
            if args.mode in {"dry-run", "apply"}:
                result = _apply(
                    conn,
                    write_set,
                    authority,
                    activation_authority,
                    allow_test_authority=allow_test_authority,
                )
            elif args.mode == "postcheck":
                result = _postcheck(
                    conn,
                    write_set,
                    authority,
                    activation_authority,
                    allow_test_authority=allow_test_authority,
                )
            else:
                result = _rollback(
                    conn,
                    write_set,
                    authority,
                    activation_authority,
                    allow_test_authority=allow_test_authority,
                )
    print(json.dumps({"mode": args.mode, "result": result}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (StoreSafetyError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}), file=sys.stderr)
        raise SystemExit(2)
