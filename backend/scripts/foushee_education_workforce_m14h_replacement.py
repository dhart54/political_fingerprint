"""Prepare and, only under later sealed authority, execute M14H V2R.

The ``prepare`` and ``capture-preflight`` modes are read-only with respect to
the database.  Production ``apply`` and ``rollback`` additionally require an
explicit command-line confirmation and a sealed, accepted V2R authority.
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
from app.editorial_presentations.publication_replacement_governance_v2 import (  # noqa: E402
    EXACT_CAPS,
    POSITIVE_AUTHORIZATIONS_V2R,
    REPLACEMENT_AUTHORITY_SCHEMA_V2,
    REPLACEMENT_PREFLIGHT_SCHEMA_V2,
    REPLACEMENT_WRITE_SET_SCHEMA_V2,
    REVIEWER_AUTHORITY_V2R,
    RUNTIME_EVIDENCE_SCHEMA_V2,
    TARGET,
    replacement_write_set_subject_sha256,
    validate_execution,
    validate_positive_authority,
    validate_write_set,
)
from app.editorial_presentations.publication_replacement_runtime_v2r import (  # noqa: E402
    select_public_presentations_v2r,
)
from scripts.editorial_artifact_store import (  # noqa: E402
    StoreSafetyError,
    _connect,
    target_info,
)
from scripts.foushee_education_workforce_publication_preparation import (  # noqa: E402
    _counts,
    _state_fingerprint,
)

BASE_SHA = "ac922506fe9fd61120d3638060cc18398b461df2"
MEMBER_ID = TARGET["member_bioguide_id"]
MEMBER_SLUG = "leg_valerie_p_foushee"
ISSUE_ID = TARGET["issue_id"]
CONGRESS = 119
PRESENTATION_KEY = "site-integration-candidate:f000477:education_workforce:m14g:v1"
SOURCE_KEY = f"{PRESENTATION_KEY}:publication-source-manifest"
VALIDATION_KEY = f"{PRESENTATION_KEY}:publication-validation"
TARGET_KEYS = [PRESENTATION_KEY, SOURCE_KEY, VALIDATION_KEY]
BATCH_KEY = "foushee_education_workforce_m14h_replacement_v1-ac922506"
LOCK_KEY = "political_fingerprint:f000477:education_workforce:publication-replacement"
OUTPUT = ROOT / "docs/editorial/publication_replacements/f000477_education_workforce_m14h_v1"
M14G = ROOT / "docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1"
CANDIDATE_PATH = M14G / "site_integration_candidate.json"
ACCEPTED_PATH = M14G / "accepted_site_integration.json"
SITE_AUTHORITY_PATH = M14G / "human_site_integration_authority.json"
EXPECTED_CANDIDATE_SUBJECT = "92d491a97ff675d60896d64fe3cb9e5d9e87ffc684f19f151a13f01b99ab05d0"
EXPECTED_CANDIDATE_FILE = "7022fff0cbd8e54acab095401c2810b93359c3a55d8a5a03eba86e4e6d14d2c6"
EXPECTED_ACCEPTED_SUBJECT = "854c184469dc9338820cb3274418c8b16b2289497b3fd551aebccd46531c070b"
EXPECTED_SITE_AUTHORITY_SUBJECT = "7042fd16cc707ffc2bef57d7eff4925d01ffe551cf3d09e0aabc05e52b51e35e"
SHA40 = re.compile(r"^[0-9a-f]{40}$")

SOURCE_PATHS = (
    CANDIDATE_PATH,
    SITE_AUTHORITY_PATH,
    ACCEPTED_PATH,
    ROOT / "docs/editorial/public_wording_candidates/f000477_education_workforce_m14f_v1/accepted_public_copy.json",
    ROOT / "docs/editorial/public_wording_candidates/f000477_education_workforce_m14f_v1/human_public_wording_prominence_authority.json",
    ROOT / "docs/editorial/analytical_candidates/f000477_education_workforce_m14d_v1/accepted_behavioral_findings.json",
    ROOT / "docs/editorial/analytical_candidates/f000477_education_workforce_m14d_v1/human_behavioral_candidate_authority.json",
    ROOT / "docs/editorial/shared_corpora/house_119_v2/shared_action_core.json",
    ROOT / "docs/editorial/shared_corpora/house_119_v2/member_projections/f000477.json",
    ROOT / "docs/editorial/shared_corpora/house_119_v2/promotion_manifest.json",
)
RUNTIME_PATHS = (
    ROOT / "backend/app/main.py",
    ROOT / "backend/app/api/editorial_presentations.py",
    ROOT / "backend/app/api/positions.py",
    ROOT / "backend/app/editorial_artifacts/repository.py",
    ROOT / "backend/app/editorial_presentations/selector.py",
    ROOT / "backend/app/editorial_presentations/site_publication.py",
    ROOT / "backend/app/editorial_presentations/education_workforce_m14g_integration_candidate.py",
    ROOT / "backend/app/editorial_presentations/publication_replacement_runtime_v2r.py",
    ROOT / "frontend/components/IssueDetail.js",
    ROOT / "frontend/components/ReviewedAnalysisSection.js",
    ROOT / "frontend/components/ActionReceipt.js",
    ROOT / "frontend/lib/selectedIssueExperience.mjs",
    ROOT / "frontend/lib/publicReceipt.mjs",
)
EXECUTION_PATHS = (
    ROOT / "backend/app/editorial_presentations/publication_replacement_governance_v2.py",
    ROOT / "backend/scripts/foushee_education_workforce_m14h_replacement.py",
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise StoreSafetyError(f"expected JSON object: {path}")
    return value


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _binding(path: Path, subject_field: str | None = None) -> dict[str, Any]:
    result = {"path": path.relative_to(ROOT).as_posix(), "file_sha256": _file_sha(path)}
    if subject_field:
        value = _load(path)
        result["artifact_id"] = value.get("artifact_id")
        result["subject_sha256"] = value.get(subject_field)
    return result


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def _registry_rows(conn: Any) -> list[dict[str, Any]]:
    return [
        _jsonable(dict(row))
        for row in conn.execute(
            """SELECT registry.member_bioguide_id,registry.issue_id,
                      registry.artifact_id,registry.publicly_active,
                      registry.activated_at,registry.deactivated_at,
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
        "member_bioguide_id": row["member_bioguide_id"],
        "issue_id": row["issue_id"],
        "artifact_id": row["artifact_id"],
        "artifact_version": row["artifact_version"],
        "presentation_natural_key": row["natural_key"],
        "content_sha256": row["content_sha256"],
        "source_commit_sha": row["source_commit_sha"],
        "publication_metadata_sha256": semantic_hash(row["publication_metadata_jsonb"]),
        "publicly_active": row["publicly_active"],
        "activated_at": row["activated_at"],
        "deactivated_at": row["deactivated_at"],
    }


def _prior_artifact(conn: Any, artifact_id: int) -> dict[str, Any]:
    row = conn.execute(
        """SELECT artifact_id,artifact_type,natural_key,schema_version,
                  artifact_version,payload_jsonb,content_sha256,
                  source_manifest_sha256,source_commit_sha,batch_id,
                  supersedes_artifact_id,member_bioguide_id,issue_id,congress,
                  chamber,editorial_status,benchmark_status,production_eligible,
                  review_route
             FROM editorial_artifact_versions WHERE artifact_id=%s""",
        (artifact_id,),
    ).fetchone()
    if row is None:
        raise StoreSafetyError("prior Education presentation is absent")
    return _jsonable(dict(row))


def _prior_graph(conn: Any, artifact_id: int) -> list[dict[str, Any]]:
    return [
        _jsonable(dict(row))
        for row in conn.execute(
            """SELECT child.artifact_id,child.artifact_type,child.natural_key,
                      child.artifact_version,child.content_sha256,
                      rel.relationship_type,rel.ordinal,rel.metadata_jsonb
                 FROM editorial_artifact_relationships rel
                 JOIN editorial_artifact_versions child
                   ON child.artifact_id=rel.child_artifact_id
                WHERE rel.parent_artifact_id=%s
                ORDER BY rel.relationship_type,rel.ordinal,child.natural_key""",
            (artifact_id,),
        ).fetchall()
    ]


def _selector_state(conn: Any, *, allow_test_authority: bool = False) -> dict[str, Any]:
    rows = EditorialArtifactRepository(conn).publication_selector()
    scopes = {}
    for scope in ("119", "all", "118"):
        selected = select_public_presentations_v2r(
            rows,
            legislator_id=MEMBER_SLUG,
            member_bioguide_id=MEMBER_ID,
            scope=scope,
            allow_test_activation_authority=allow_test_authority,
        )
        scopes[scope] = {
            item["issue_id"]: item["tier"] for item in selected["presentations"]
        }
    return {"selector_rows": len(rows), "scopes": scopes}


def target_identity(database_url: str, target: str) -> str:
    info = target_info(database_url, target, None)
    return semantic_hash({key: info[key] for key in ("scheme", "host", "port", "database")})


def capture_preflight(
    conn: Any, *, production_target_identity_sha256: str,
    allow_test_authority: bool = False,
) -> dict[str, Any]:
    rows = _registry_rows(conn)
    education = [
        row for row in rows
        if row["member_bioguide_id"] == MEMBER_ID and row["issue_id"] == ISSUE_ID
    ]
    found = [
        _jsonable(dict(row))
        for row in conn.execute(
            """SELECT artifact_id,natural_key,artifact_version,content_sha256
                 FROM editorial_artifact_versions
                WHERE natural_key=ANY(%s) ORDER BY natural_key,artifact_version""",
            (TARGET_KEYS,),
        ).fetchall()
    ]
    if len(education) != 1:
        raise StoreSafetyError("production must contain exactly one Education registry row")
    prior = education[0]
    if prior["natural_key"] == PRESENTATION_KEY:
        raise StoreSafetyError("ALREADY_ACTIVE")
    if (
        prior["natural_key"] != "site-integration-candidate:f000477:education_workforce:119:v1"
        or prior["content_sha256"] != "ea482f71f1bce872574fd91abd76869423f0ba2fd4dddc78eb24e77806f5294c"
        or prior["publicly_active"] is not True
        or prior["deactivated_at"] is not None
        or found
    ):
        raise StoreSafetyError("unexplained Education identity or conflicting M14G artifacts")
    selector = _selector_state(conn, allow_test_authority=allow_test_authority)
    if (
        selector["scopes"]["119"].get(ISSUE_ID) != "reviewed_conclusion"
        or selector["scopes"]["all"].get(ISSUE_ID) != "reviewed_conclusion"
        or selector["scopes"]["118"].get(ISSUE_ID) != "receipts_only"
    ):
        raise StoreSafetyError("unexpected Education selector state")
    baseline = {
        "production_target_identity_sha256": production_target_identity_sha256,
        "state_fingerprint_sha256": _state_fingerprint(conn),
        "counts": _counts(conn),
        "existing_registry_identities": [_registry_identity(row) for row in rows],
        "prior_registry_row": _jsonable(prior),
        "prior_presentation_artifact": _prior_artifact(conn, int(prior["artifact_id"])),
        "prior_presentation_graph": _prior_graph(conn, int(prior["artifact_id"])),
        "target_new_natural_keys_checked": TARGET_KEYS,
        "target_new_natural_keys_found": found,
        "selector_state": selector,
        "state_predicates": {
            "exactly_one_active_education_registry_row": True,
            "prior_education_is_historical_m13": True,
            "other_registry_rows_must_remain_exact": True,
            "new_m14g_natural_keys_absent": True,
        },
        "write_preconditions": {
            "prior_registry_row_exact": True,
            "prior_presentation_immutable": True,
            "target_natural_keys_absent": True,
            "registry_update_target_exact": True,
        },
    }
    report = {
        "schema_version": REPLACEMENT_PREFLIGHT_SCHEMA_V2,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "transaction_read_only": True,
        **baseline,
    }
    report["preflight_subject_sha256"] = semantic_hash(report)
    return report


def load_candidate() -> dict[str, Any]:
    candidate = _load(CANDIDATE_PATH)
    accepted = _load(ACCEPTED_PATH)
    site_authority = _load(SITE_AUTHORITY_PATH)
    if (
        _file_sha(CANDIDATE_PATH) != EXPECTED_CANDIDATE_FILE
        or candidate.get("candidate_subject_sha256") != EXPECTED_CANDIDATE_SUBJECT
        or accepted.get("accepted_site_integration_subject_sha256") != EXPECTED_ACCEPTED_SUBJECT
        or site_authority.get("authority_subject_sha256") != EXPECTED_SITE_AUTHORITY_SUBJECT
    ):
        raise StoreSafetyError("accepted M14G identity differs")
    return candidate


def _manifest(paths: tuple[Path, ...], schema: str) -> dict[str, Any]:
    files = [_binding(path) for path in paths]
    subject = {"files": files}
    return {"schema_version": schema, "subject": subject, "subject_sha256": semantic_hash(subject)}


def public_runtime_manifest(*, backend_health_commit: str | None) -> dict[str, Any]:
    manifest = _manifest(RUNTIME_PATHS, "m14h_reviewed_public_runtime_manifest_v1")
    manifest["production_observation"] = {
        "backend_health_commit": backend_health_commit,
        "backend_compatible": backend_health_commit == BASE_SHA,
        "frontend_exact_deployment_identity": None,
        "frontend_compatible_proven": False,
        "deployment_required_before_activation": True,
    }
    return manifest


def preparation_authority(baseline: dict[str, Any]) -> dict[str, Any]:
    subject = {
        "decision": "approve_exact_publication_replacement_preparation",
        "decision_source": "user_supplied_continue_after_m14g_close",
        "authority_effect": "prepare_exact_m14g_publication_replacement_only",
        "member_bioguide_id": MEMBER_ID,
        "issue_id": ISSUE_ID,
        "accepted_site_integration_subject_sha256": EXPECTED_ACCEPTED_SUBJECT,
        "reviewed_candidate_subject_sha256": EXPECTED_CANDIDATE_SUBJECT,
        "stable_production_baseline_sha256": semantic_hash(baseline),
        "authorizations": {
            "record_production_eligibility": True,
            "read_only_production_discovery": True,
            "stable_baseline_construction": True,
            "replacement_write_set_construction": True,
            "rollback_preparation": True,
            "disposable_postgresql_execution_proof": True,
            "prospective_activation_authority_candidate": True,
            "production_database_write": False,
            "publication_registry_mutation": False,
            "publication_activation": False,
            "production_persistence": False,
            "public_activation": False,
            "deployment": False,
            "live_activation": False,
        },
    }
    return {
        "schema_version": "site_integration_publication_replacement_preparation_authority_v1",
        "artifact_id": "publication-replacement-preparation-authority:f000477:education_workforce:m14h:v1",
        "immutable": True,
        "accepted": True,
        "subject": subject,
        "authority_subject_sha256": semantic_hash(subject),
    }


def rollback_contract(baseline: dict[str, Any]) -> dict[str, Any]:
    subject = {
        "registry_primary_key": TARGET,
        "restore_prior_registry_row": baseline["prior_registry_row"],
        "expected_new_presentation_natural_key": PRESENTATION_KEY,
        "owned_batch_key": BATCH_KEY,
        "delete_relationships": 2,
        "delete_artifact_natural_keys": TARGET_KEYS,
        "delete_batches": 1,
        "restore_counts": baseline["counts"],
        "restore_state_fingerprint_sha256": baseline["state_fingerprint_sha256"],
        "restore_registry_identities": baseline["existing_registry_identities"],
        "restore_selector_state": baseline["selector_state"],
        "prior_artifact_must_remain_immutable": True,
    }
    return {
        "schema_version": "publication_replacement_rollback_contract_v1",
        "artifact_id": "publication-replacement-rollback:f000477:education_workforce:m14h:v1",
        "immutable": True,
        "subject": subject,
        "rollback_contract_subject_sha256": semantic_hash(subject),
    }


def _artifact(
    *, artifact_type: str, natural_key: str, payload: dict[str, Any],
    source_manifest_sha256: str, supersedes_artifact_id: int | None = None,
) -> dict[str, Any]:
    return {
        "artifact_type": artifact_type,
        "natural_key": natural_key,
        "schema_version": payload["schema_version"],
        "artifact_version": 1,
        "payload": payload,
        "content_sha256": semantic_hash(payload),
        "source_manifest_sha256": source_manifest_sha256,
        "source_commit_sha": BASE_SHA,
        "supersedes_artifact_id": supersedes_artifact_id,
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
    baseline: dict[str, Any], authority: dict[str, Any], rollback: dict[str, Any],
    runtime: dict[str, Any], execution: dict[str, Any],
) -> dict[str, Any]:
    candidate = load_candidate()
    source_files = [_binding(path) for path in SOURCE_PATHS]
    source_payload = {
        "schema_version": "editorial_publication_source_manifest_v1",
        "complete_required_sources": True,
        "source_files": source_files,
        "accepted_site_integration_subject_sha256": EXPECTED_ACCEPTED_SUBJECT,
        "reviewed_candidate_subject_sha256": EXPECTED_CANDIDATE_SUBJECT,
    }
    source_hash = semantic_hash(source_files)
    validation_payload = {
        "schema_version": "editorial_publication_validation_v1",
        "successful": True,
        "current": True,
        "blocking_findings": 0,
        "production_activation_authorized": False,
        "accounting": {
            "reviewed_actions": 17,
            "reviewed_episodes": 16,
            "findings": 3,
            "finding_supporting_actions": 6,
            "main_takeaway_actions": 4,
            "main_takeaway_episodes": 3,
            "main_takeaway_linked_findings": 2,
            "retained_limitation_instances": 7,
            "accepted_public_wording_items": 4,
        },
        "semantic_bindings": {
            "hr1005": "Not Voting / resolved_non_directional",
            "hr1048": "one episode / two actions / Mixed",
            "hr5408": "exact rich V2 meaning",
            "reviewed_candidate_subject_sha256": EXPECTED_CANDIDATE_SUBJECT,
            "accepted_site_integration_subject_sha256": EXPECTED_ACCEPTED_SUBJECT,
        },
    }
    prior = baseline["prior_registry_row"]
    artifacts = [
        _artifact(
            artifact_type="issue_public_presentation", natural_key=PRESENTATION_KEY,
            payload=candidate, source_manifest_sha256=source_hash,
            supersedes_artifact_id=int(prior["artifact_id"]),
        ),
        _artifact(
            artifact_type="source_manifest", natural_key=SOURCE_KEY,
            payload=source_payload, source_manifest_sha256=source_hash,
        ),
        _artifact(
            artifact_type="standardization_validation_result", natural_key=VALIDATION_KEY,
            payload=validation_payload, source_manifest_sha256=source_hash,
        ),
    ]
    relation_metadata = {"replacement_bundle_id": BATCH_KEY}
    relationships = [
        {"parent_natural_key": PRESENTATION_KEY, "child_natural_key": SOURCE_KEY,
         "relationship_type": "uses_source_manifest", "ordinal": 0,
         "metadata": relation_metadata},
        {"parent_natural_key": PRESENTATION_KEY, "child_natural_key": VALIDATION_KEY,
         "relationship_type": "has_validation", "ordinal": 0,
         "metadata": relation_metadata},
    ]
    metadata = {
        "presentation_natural_key": PRESENTATION_KEY,
        "presentation_artifact_version": 1,
        "active_artifact_sha256": artifacts[0]["content_sha256"],
        "source_manifest_natural_key": SOURCE_KEY,
        "source_manifest_artifact_version": 1,
        "source_manifest_content_sha256": artifacts[1]["content_sha256"],
        "validation_natural_key": VALIDATION_KEY,
        "validation_artifact_version": 1,
        "validation_content_sha256": artifacts[2]["content_sha256"],
        "relationship_metadata": relation_metadata,
        "m14g_accepted_site_integration_subject_sha256": EXPECTED_ACCEPTED_SUBJECT,
        "m14g_human_site_integration_authority_subject_sha256": EXPECTED_SITE_AUTHORITY_SUBJECT,
        "m14g_reviewed_candidate_subject_sha256": EXPECTED_CANDIDATE_SUBJECT,
        "m14g_reviewed_candidate_complete_file_sha256": EXPECTED_CANDIDATE_FILE,
        "m14h_preparation_authority_subject_sha256": authority["authority_subject_sha256"],
        "production_target_identity_sha256": baseline["production_target_identity_sha256"],
        "stable_prior_registry_identity_sha256": semantic_hash(prior),
        "superseded_presentation_artifact_id": prior["artifact_id"],
        "rollback_contract_subject_sha256": rollback["rollback_contract_subject_sha256"],
        "execution_code_manifest_subject_sha256": execution["subject_sha256"],
        "reviewed_public_runtime_manifest_subject_sha256": runtime["subject_sha256"],
        "v2r_write_set_subject_sha256": None,
    }
    expected_counts = copy.deepcopy(baseline["counts"])
    expected_counts["batches"] += 1
    expected_counts["artifacts"] += 3
    expected_counts["relationships"] += 2
    body = {
        "schema_version": REPLACEMENT_WRITE_SET_SCHEMA_V2,
        "artifact_id": "publication-replacement-write-set:f000477:education_workforce:m14h:v1",
        "immutable": True,
        "subject": {
            "accepted_site_integration_binding": {
                "artifact_id": _load(ACCEPTED_PATH)["artifact_id"],
                "subject_sha256": EXPECTED_ACCEPTED_SUBJECT,
            },
            "preparation_authority_binding": {
                "artifact_id": authority["artifact_id"],
                "subject_sha256": authority["authority_subject_sha256"],
            },
            "production_target_identity_sha256": baseline["production_target_identity_sha256"],
            "stable_production_baseline": baseline,
            "target_new_natural_keys": TARGET_KEYS,
            "artifacts": artifacts,
            "relationships": relationships,
            "publication_registry_update": {
                "primary_key": TARGET,
                "prior_row": prior,
                "new_presentation_natural_key": PRESENTATION_KEY,
                "publicly_active": True,
                "activated_at": "activation_execution_timestamp",
                "deactivated_at": None,
                "publication_metadata_jsonb": metadata,
                "require_rowcount": 1,
                "insert_allowed": False,
                "delete_allowed": False,
            },
            "mutation_caps": EXACT_CAPS,
            "rollback_contract_binding": {
                "artifact_id": rollback["artifact_id"],
                "subject_sha256": rollback["rollback_contract_subject_sha256"],
            },
            "execution_code_manifest_binding": {
                "subject_sha256": execution["subject_sha256"]
            },
            "public_runtime_manifest_binding": {"subject_sha256": runtime["subject_sha256"]},
            "expected_postconditions": {
                "counts": expected_counts,
                "registry_rows": baseline["counts"]["publication_registry"],
                "education_119": "reviewed_conclusion",
                "education_all": "reviewed_conclusion_with_119th_congress_boundary",
                "education_118": "receipts_only",
                "other_registry_rows_unchanged": True,
            },
            "activation_authorized": False,
            "production_write_authorized": False,
        },
        "write_set_subject_sha256": "",
    }
    body["write_set_subject_sha256"] = replacement_write_set_subject_sha256(body)
    metadata["v2r_write_set_subject_sha256"] = body["write_set_subject_sha256"]
    validate_write_set(body)
    return body


def activation_candidate(
    write_set: dict[str, Any], authority: dict[str, Any], rollback: dict[str, Any],
    runtime: dict[str, Any], execution: dict[str, Any],
) -> dict[str, Any]:
    subject = {
        "decision": "approve_exact_publication_replacement_v2",
        "decision_recorded_at_utc": None,
        "reviewer": None,
        "reviewer_authority": REVIEWER_AUTHORITY_V2R,
        "member_bioguide_id": MEMBER_ID,
        "issue_id": ISSUE_ID,
        "congress": CONGRESS,
        "accepted_site_integration_subject_sha256": EXPECTED_CANDIDATE_SUBJECT,
        "semantic_human_authority_lineage": [
            EXPECTED_SITE_AUTHORITY_SUBJECT, EXPECTED_ACCEPTED_SUBJECT
        ],
        "preparation_authority_subject_sha256": authority["authority_subject_sha256"],
        "stable_production_baseline_sha256": semantic_hash(
            write_set["subject"]["stable_production_baseline"]
        ),
        "exact_write_set_subject_sha256": write_set["write_set_subject_sha256"],
        "replacement_registry_target": TARGET,
        "prior_registry_identity_sha256": semantic_hash(
            write_set["subject"]["stable_production_baseline"]["prior_registry_row"]
        ),
        "rollback_contract_subject_sha256": rollback["rollback_contract_subject_sha256"],
        "expected_postconditions_sha256": semantic_hash(
            write_set["subject"]["expected_postconditions"]
        ),
        "execution_code_manifest_subject_sha256": execution["subject_sha256"],
        "public_runtime_manifest_subject_sha256": runtime["subject_sha256"],
        "production_target_identity_sha256": write_set["subject"]["production_target_identity_sha256"],
        "authorizations": POSITIVE_AUTHORIZATIONS_V2R,
    }
    return {
        "schema_version": REPLACEMENT_AUTHORITY_SCHEMA_V2,
        "artifact_id": "publication-replacement-activation-authority:f000477:education_workforce:m14h:v1",
        "immutable": True,
        "sealed": False,
        "accepted": False,
        "subject": subject,
        "prospective_activation_subject_sha256": semantic_hash(subject),
    }


def build_package(
    preflight: dict[str, Any], *, backend_health_commit: str | None,
    disposable_result: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    load_candidate()
    baseline = {key: value for key, value in preflight.items() if key not in {
        "schema_version", "captured_at_utc", "transaction_read_only", "preflight_subject_sha256"
    }}
    authority = preparation_authority(baseline)
    rollback = rollback_contract(baseline)
    runtime = public_runtime_manifest(backend_health_commit=backend_health_commit)
    execution = _manifest(EXECUTION_PATHS, "m14h_execution_code_manifest_v1")
    write_set = build_write_set(baseline, authority, rollback, runtime, execution)
    candidate = activation_candidate(write_set, authority, rollback, runtime, execution)
    review_subject = {
        "accepted_m14g": {
            "accepted_site_integration_subject_sha256": EXPECTED_ACCEPTED_SUBJECT,
            "human_site_integration_authority_subject_sha256": EXPECTED_SITE_AUTHORITY_SUBJECT,
            "reviewed_candidate_subject_sha256": EXPECTED_CANDIDATE_SUBJECT,
            "reviewed_candidate_complete_file_sha256": EXPECTED_CANDIDATE_FILE,
        },
        "prior_education_registry_identity": _registry_identity(
            baseline["prior_registry_row"]
        ),
        "old_to_new": {
            "old_artifact_id": baseline["prior_registry_row"]["artifact_id"],
            "old_natural_key": baseline["prior_registry_row"]["natural_key"],
            "new_natural_key": PRESENTATION_KEY,
        },
        "production_baseline": {
            "counts": baseline["counts"],
            "state_fingerprint_sha256": baseline["state_fingerprint_sha256"],
        },
        "preparation_authority_subject_sha256": authority["authority_subject_sha256"],
        "replacement_write_set_subject_sha256": write_set["write_set_subject_sha256"],
        "prospective_activation_subject_sha256": candidate["prospective_activation_subject_sha256"],
        "mutation_envelope": EXACT_CAPS,
        "runtime_readiness": runtime["production_observation"],
        "disposable_proof": disposable_result,
        "downstream_denials": authority["subject"]["authorizations"],
    }
    review = {
        "schema_version": "m14h_publication_replacement_review_package_v1",
        "subject": review_subject,
        "review_package_subject_sha256": semantic_hash(review_subject),
    }
    return {
        "production_baseline.json": preflight,
        "publication_replacement_preparation_authority.json": authority,
        "publication_replacement_write_set.json": write_set,
        "rollback_contract.json": rollback,
        "public_runtime_manifest.json": runtime,
        "execution_code_manifest.json": execution,
        "positive_replacement_activation_candidate.json": candidate,
        "review_package.json": review,
    }


def _exact_current_registry_row(conn: Any) -> dict[str, Any]:
    rows = _registry_rows(conn)
    matches = [row for row in rows if row["member_bioguide_id"] == MEMBER_ID and row["issue_id"] == ISSUE_ID]
    if len(matches) != 1:
        raise StoreSafetyError("exactly one Education registry row is required")
    return matches[0]


def publication_metadata_for_activation(
    write_set: dict[str, Any], activation_authority: dict[str, Any]
) -> dict[str, Any]:
    metadata = copy.deepcopy(
        write_set["subject"]["publication_registry_update"]["publication_metadata_jsonb"]
    )
    metadata["publication_replacement_activation_authority"] = copy.deepcopy(
        activation_authority
    )
    metadata["activation_authority_subject_sha256"] = activation_authority[
        "activation_authority_subject_sha256"
    ]
    return metadata


def _already_applied(
    conn: Any, write_set: dict[str, Any], activation_authority: dict[str, Any]
) -> bool:
    row = _exact_current_registry_row(conn)
    metadata = publication_metadata_for_activation(write_set, activation_authority)
    if row["natural_key"] != PRESENTATION_KEY:
        return False
    if row["publication_metadata_jsonb"] != metadata or row["deactivated_at"] is not None:
        raise StoreSafetyError("partial or drifted replacement state")
    found = conn.execute(
        "SELECT natural_key,artifact_type,artifact_version,payload_jsonb,content_sha256 "
        "FROM editorial_artifact_versions WHERE natural_key=ANY(%s) ORDER BY natural_key",
        (TARGET_KEYS,),
    ).fetchall()
    expected_artifacts = {
        item["natural_key"]: item for item in write_set["subject"]["artifacts"]
    }
    if len(found) != 3 or any(
        row["natural_key"] not in expected_artifacts
        or row["artifact_type"] != expected_artifacts[row["natural_key"]]["artifact_type"]
        or row["artifact_version"] != 1
        or row["payload_jsonb"] != expected_artifacts[row["natural_key"]]["payload"]
        or row["content_sha256"] != expected_artifacts[row["natural_key"]]["content_sha256"]
        for row in found
    ):
        raise StoreSafetyError("replacement graph is incomplete")
    relationships = conn.execute(
        """SELECT parent.natural_key AS parent_natural_key,
                  child.natural_key AS child_natural_key,
                  rel.relationship_type,rel.ordinal,rel.metadata_jsonb
             FROM editorial_artifact_relationships rel
             JOIN editorial_artifact_versions parent ON parent.artifact_id=rel.parent_artifact_id
             JOIN editorial_artifact_versions child ON child.artifact_id=rel.child_artifact_id
            WHERE parent.natural_key=%s
            ORDER BY rel.relationship_type,rel.ordinal,child.natural_key""",
        (PRESENTATION_KEY,),
    ).fetchall()
    expected_relationships = sorted(
        write_set["subject"]["relationships"],
        key=lambda item: (item["relationship_type"], item["ordinal"], item["child_natural_key"]),
    )
    normalized_relationships = [
        {
            "parent_natural_key": row["parent_natural_key"],
            "child_natural_key": row["child_natural_key"],
            "relationship_type": row["relationship_type"],
            "ordinal": row["ordinal"],
            "metadata": _jsonable(row["metadata_jsonb"]),
        }
        for row in relationships
    ]
    if normalized_relationships != expected_relationships:
        raise StoreSafetyError("replacement relationships differ")
    selector = _selector_state(conn, allow_test_authority=True)
    if [selector["scopes"][scope][ISSUE_ID] for scope in ("119", "all", "118")] != [
        "reviewed_conclusion", "reviewed_conclusion", "receipts_only"
    ]:
        raise StoreSafetyError("already-applied selector state differs")
    return True


def apply_replacement(
    conn: Any, write_set: dict[str, Any], activation_authority: dict[str, Any],
    *, allow_test_authority: bool, fault_after: str | None = None,
) -> dict[str, Any]:
    from psycopg.types.json import Jsonb

    candidate = load_candidate()
    if allow_test_authority:
        if not activation_authority.get("test_only_synthetic"):
            raise StoreSafetyError("disposable apply requires explicit synthetic authority")
    validate_positive_authority(activation_authority, write_set=write_set, candidate=candidate)
    if _already_applied(conn, write_set, activation_authority):
        return {"status": "ALREADY_APPLIED", "writes": 0}
    baseline = write_set["subject"]["stable_production_baseline"]
    current = _exact_current_registry_row(conn)
    if current != baseline["prior_registry_row"]:
        raise StoreSafetyError("prior Education registry row drifted")
    if _counts(conn) != baseline["counts"] or _state_fingerprint(conn) != baseline["state_fingerprint_sha256"]:
        raise StoreSafetyError("complete production baseline drifted")
    found = conn.execute(
        "SELECT COUNT(*) AS n FROM editorial_artifact_versions WHERE natural_key=ANY(%s)",
        (TARGET_KEYS,),
    ).fetchone()["n"]
    if int(found) != 0:
        raise StoreSafetyError("new target partial existence is forbidden")
    batch = conn.execute(
        """INSERT INTO editorial_artifact_batches
           (deterministic_batch_key,source_commit_sha,manifest_sha256,status,
            artifact_count,relationship_count,applied_at)
           VALUES (%s,%s,%s,'applied',3,2,NOW()) RETURNING batch_id""",
        (BATCH_KEY, BASE_SHA, write_set["write_set_subject_sha256"]),
    ).fetchone()
    batch_id = int(batch["batch_id"])
    if fault_after == "batch":
        raise RuntimeError("injected failure after batch")
    ids: dict[str, int] = {}
    for item in write_set["subject"]["artifacts"]:
        row = conn.execute(
            """INSERT INTO editorial_artifact_versions
               (artifact_type,natural_key,schema_version,artifact_version,payload_jsonb,
                content_sha256,source_manifest_sha256,source_commit_sha,batch_id,
                supersedes_artifact_id,member_bioguide_id,issue_id,congress,chamber,
                canonical_action_id,episode_id,policy_family_id,editorial_status,
                benchmark_status,production_eligible,review_route)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               RETURNING artifact_id""",
            (item["artifact_type"], item["natural_key"], item["schema_version"],
             item["artifact_version"], Jsonb(item["payload"]), item["content_sha256"],
             item["source_manifest_sha256"], item["source_commit_sha"], batch_id,
             item["supersedes_artifact_id"], item["member_bioguide_id"], item["issue_id"],
             item["congress"], item["chamber"], item["canonical_action_id"],
             item["episode_id"], item["policy_family_id"], item["editorial_status"],
             item["benchmark_status"], item["production_eligible"], item["review_route"]),
        ).fetchone()
        ids[item["natural_key"]] = int(row["artifact_id"])
    if fault_after == "artifacts":
        raise RuntimeError("injected failure after artifacts")
    for rel in write_set["subject"]["relationships"]:
        conn.execute(
            """INSERT INTO editorial_artifact_relationships
               (parent_artifact_id,child_artifact_id,relationship_type,ordinal,metadata_jsonb)
               VALUES (%s,%s,%s,%s,%s)""",
            (ids[rel["parent_natural_key"]], ids[rel["child_natural_key"]],
             rel["relationship_type"], rel["ordinal"], Jsonb(rel["metadata"])),
        )
    if fault_after == "relationships":
        raise RuntimeError("injected failure after relationships")
    prior = baseline["prior_registry_row"]
    publication_metadata = publication_metadata_for_activation(
        write_set, activation_authority
    )
    update = conn.execute(
        """UPDATE editorial_publication_registry
              SET artifact_id=%s,publicly_active=TRUE,activated_at=NOW(),
                  deactivated_at=NULL,publication_metadata_jsonb=%s
            WHERE member_bioguide_id=%s AND issue_id=%s AND artifact_id=%s
              AND publicly_active=%s AND activated_at=%s AND deactivated_at IS NOT DISTINCT FROM %s
              AND publication_metadata_jsonb=%s""",
        (ids[PRESENTATION_KEY], Jsonb(publication_metadata),
         MEMBER_ID, ISSUE_ID, prior["artifact_id"], prior["publicly_active"],
         prior["activated_at"], prior["deactivated_at"], Jsonb(prior["publication_metadata_jsonb"])),
    )
    if update.rowcount != 1:
        raise StoreSafetyError("exact Education registry UPDATE count differs")
    if fault_after == "registry_update":
        raise RuntimeError("injected failure after registry UPDATE")
    expected = write_set["subject"]["expected_postconditions"]["counts"]
    selector = _selector_state(conn, allow_test_authority=allow_test_authority)
    if _counts(conn) != expected or [selector["scopes"][scope][ISSUE_ID] for scope in ("119", "all", "118")] != [
        "reviewed_conclusion", "reviewed_conclusion", "receipts_only"
    ]:
        raise StoreSafetyError("replacement postconditions differ")
    current_rows = _registry_rows(conn)
    before_other = [
        identity for identity in baseline["existing_registry_identities"]
        if identity["issue_id"] != ISSUE_ID
    ]
    after_other = [
        _registry_identity(row) for row in current_rows if row["issue_id"] != ISSUE_ID
    ]
    if after_other != before_other:
        raise StoreSafetyError("replacement changed another registry identity")
    if _prior_artifact(conn, int(prior["artifact_id"])) != baseline[
        "prior_presentation_artifact"
    ]:
        raise StoreSafetyError("replacement modified the prior Education artifact")
    return {
        "status": "APPLIED", "batch_id": batch_id, "artifact_ids": ids,
        "mutation_counts": EXACT_CAPS, "selector": selector,
    }


def rollback_replacement(
    conn: Any, write_set: dict[str, Any], activation_authority: dict[str, Any],
    *, allow_test_authority: bool,
) -> dict[str, Any]:
    from psycopg.types.json import Jsonb

    validate_positive_authority(activation_authority, write_set=write_set, candidate=load_candidate())
    baseline = write_set["subject"]["stable_production_baseline"]
    current = _exact_current_registry_row(conn)
    expected_metadata = publication_metadata_for_activation(
        write_set, activation_authority
    )
    if current["natural_key"] != PRESENTATION_KEY or current["publication_metadata_jsonb"] != expected_metadata:
        raise StoreSafetyError("rollback requires the exact applied M14H registry state")
    prior = baseline["prior_registry_row"]
    restored = conn.execute(
        """UPDATE editorial_publication_registry
              SET artifact_id=%s,publicly_active=%s,activated_at=%s,deactivated_at=%s,
                  publication_metadata_jsonb=%s
            WHERE member_bioguide_id=%s AND issue_id=%s AND artifact_id=%s
              AND publication_metadata_jsonb=%s""",
        (prior["artifact_id"], prior["publicly_active"], prior["activated_at"],
         prior["deactivated_at"], Jsonb(prior["publication_metadata_jsonb"]), MEMBER_ID,
         ISSUE_ID, current["artifact_id"], Jsonb(expected_metadata)),
    )
    if restored.rowcount != 1:
        raise StoreSafetyError("rollback registry UPDATE count differs")
    batch = conn.execute(
        "SELECT batch_id FROM editorial_artifact_batches WHERE deterministic_batch_key=%s",
        (BATCH_KEY,),
    ).fetchone()
    if batch is None:
        raise StoreSafetyError("owned M14H batch is absent")
    batch_id = int(batch["batch_id"])
    rel = conn.execute(
        """DELETE FROM editorial_artifact_relationships rel USING editorial_artifact_versions parent
            WHERE rel.parent_artifact_id=parent.artifact_id AND parent.batch_id=%s""",
        (batch_id,),
    )
    conn.execute("SELECT set_config('app.editorial_artifact_rollback_batch',%s,true)", (BATCH_KEY,))
    artifacts = conn.execute("DELETE FROM editorial_artifact_versions WHERE batch_id=%s", (batch_id,))
    batch_deleted = conn.execute("DELETE FROM editorial_artifact_batches WHERE batch_id=%s", (batch_id,))
    if (rel.rowcount, artifacts.rowcount, batch_deleted.rowcount) != (2, 3, 1):
        raise StoreSafetyError("exact rollback delete counts differ")
    if (
        _counts(conn) != baseline["counts"]
        or _state_fingerprint(conn) != baseline["state_fingerprint_sha256"]
    ):
        raise StoreSafetyError("rollback did not restore exact baseline")
    if [_registry_identity(row) for row in _registry_rows(conn)] != baseline["existing_registry_identities"]:
        raise StoreSafetyError("rollback registry identities differ")
    selector = _selector_state(conn, allow_test_authority=allow_test_authority)
    if selector != baseline["selector_state"]:
        raise StoreSafetyError("rollback selector state differs")
    return {"status": "ROLLED_BACK", "counts": _counts(conn), "selector": selector}


def capture_runtime(base_url: str, runtime_manifest: dict[str, Any]) -> dict[str, Any]:
    endpoint = urljoin(base_url.rstrip("/") + "/", "health")
    with urlopen(endpoint, timeout=30) as response:  # noqa: S310
        health = json.load(response)
    commit = health.get("commit_sha")
    if not isinstance(commit, str) or not SHA40.fullmatch(commit):
        raise StoreSafetyError("health endpoint lacks exact commit SHA")
    body = {
        "schema_version": RUNTIME_EVIDENCE_SCHEMA_V2,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "healthy": health.get("status") == "ok",
        "deployed_commit": commit,
        "health_commit": commit,
        "current_runtime_manifest_sha256": runtime_manifest["subject_sha256"],
        "deployment_required_before_activation": runtime_manifest[
            "production_observation"
        ]["deployment_required_before_activation"],
    }
    body["runtime_health_proof_subject_sha256"] = semantic_hash(body)
    return body


def _write_package(package: dict[str, dict[str, Any]]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, value in package.items():
        (OUTPUT / name).write_text(
            json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("capture-preflight", "prepare", "apply", "rollback"))
    parser.add_argument("--database-url")
    parser.add_argument("--target", choices=("production", "disposable"))
    parser.add_argument("--preflight-path", type=Path)
    parser.add_argument("--preflight-output", type=Path)
    parser.add_argument("--write-set-path", type=Path)
    parser.add_argument("--activation-authority-path", type=Path)
    parser.add_argument("--backend-health-commit")
    parser.add_argument("--runtime-evidence-path", type=Path)
    parser.add_argument("--confirm-production-replacement", action="store_true")
    parser.add_argument("--confirm-production-rollback", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.mode == "capture-preflight":
        if not args.database_url or not args.target:
            raise StoreSafetyError("database URL and target are required")
        identity = target_identity(args.database_url, args.target)
        with _connect(args.database_url, autocommit=False) as conn:
            conn.execute("SET default_transaction_read_only=on")
            with conn.transaction():
                conn.execute("SET TRANSACTION READ ONLY")
                report = capture_preflight(conn, production_target_identity_sha256=identity)
        rendered = json.dumps(report, sort_keys=True, indent=2) + "\n"
        if args.preflight_output:
            args.preflight_output.parent.mkdir(parents=True, exist_ok=True)
            args.preflight_output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        return 0
    if args.mode == "prepare":
        if not args.preflight_path:
            raise StoreSafetyError("preflight path is required")
        package = build_package(
            _load(args.preflight_path), backend_health_commit=args.backend_health_commit
        )
        _write_package(package)
        return 0
    if not all((args.database_url, args.target, args.write_set_path, args.activation_authority_path)):
        raise StoreSafetyError("execution requires database, target, write set, and authority")
    write_set = _load(args.write_set_path)
    activation = _load(args.activation_authority_path)
    allow_test = args.target == "disposable"
    if args.target == "production":
        if activation.get("test_only_synthetic") is True:
            raise StoreSafetyError("synthetic authority cannot target production")
        if args.mode == "apply" and not args.confirm_production_replacement:
            raise StoreSafetyError("explicit production replacement confirmation required")
        if args.mode == "rollback" and not args.confirm_production_rollback:
            raise StoreSafetyError("explicit production rollback confirmation required")
        if not args.preflight_path or not args.runtime_evidence_path:
            raise StoreSafetyError("production execution requires fresh preflight/runtime evidence")
        if target_identity(args.database_url, "production") != write_set["subject"][
            "production_target_identity_sha256"
        ]:
            raise StoreSafetyError("production target identity differs from write set")
        validate_execution(
            authority=activation, write_set=write_set, candidate=load_candidate(),
            runtime_evidence=_load(args.runtime_evidence_path),
            production_preflight=_load(args.preflight_path),
        )
    with _connect(args.database_url, autocommit=False) as conn:
        with conn.transaction():
            conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (LOCK_KEY,))
            result = (
                apply_replacement(conn, write_set, activation, allow_test_authority=allow_test)
                if args.mode == "apply"
                else rollback_replacement(conn, write_set, activation, allow_test_authority=allow_test)
            )
    print(json.dumps(result, sort_keys=True, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
