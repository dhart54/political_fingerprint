"""Fail-closed governance for replacing one active publication selection.

V2R is deliberately additive.  Publication Activation Governance V2 remains
the insert-only contract; this companion admits exactly one registry UPDATE for
one bound member/issue primary key while retaining the prior immutable graph.
"""

from __future__ import annotations

import copy
import re
from datetime import datetime, timezone
from typing import Any

from .compiler import canonical_digest

REPLACEMENT_AUTHORITY_SCHEMA_V2 = (
    "site_integration_publication_replacement_activation_authority_v2"
)
REPLACEMENT_WRITE_SET_SCHEMA_V2 = "publication_replacement_write_set_v2"
REPLACEMENT_PREFLIGHT_SCHEMA_V2 = (
    "publication_replacement_production_preflight_evidence_v2"
)
REPLACEMENT_EXECUTION_SCHEMA_V2 = "publication_replacement_execution_validation_v2"
RUNTIME_EVIDENCE_SCHEMA_V2 = "publication_replacement_runtime_execution_evidence_v2r"
REVIEWER_AUTHORITY_V2R = "publication_replacement_review_authority_v2"
TARGET = {"member_bioguide_id": "F000477", "issue_id": "EDUCATION_WORKFORCE"}
AUTHORITY_ARTIFACT_ID = (
    "publication-replacement-activation-authority:f000477:education_workforce:m14h:v1"
)
ACCEPTED_SITE_INTEGRATION_SUBJECT_SHA256 = (
    "854c184469dc9338820cb3274418c8b16b2289497b3fd551aebccd46531c070b"
)
HUMAN_SITE_INTEGRATION_AUTHORITY_SHA256 = (
    "7042fd16cc707ffc2bef57d7eff4925d01ffe551cf3d09e0aabc05e52b51e35e"
)
REVIEWED_CANDIDATE_SUBJECT_SHA256 = (
    "92d491a97ff675d60896d64fe3cb9e5d9e87ffc684f19f151a13f01b99ab05d0"
)
REVIEWED_CANDIDATE_COMPLETE_FILE_SHA256 = (
    "7022fff0cbd8e54acab095401c2810b93359c3a55d8a5a03eba86e4e6d14d2c6"
)
EXACT_CAPS = {
    "insert_batches": 1,
    "insert_artifacts": 3,
    "insert_relationships": 2,
    "insert_registry_rows": 0,
    "update_registry_rows": 1,
    "other_updates": 0,
    "deletes_during_activation": 0,
    "unauthorized_table_writes": 0,
}
POSITIVE_AUTHORIZATIONS_V2R = {
    "deploy_exact_reviewed_runtime": True,
    "production_database_write": True,
    "publication_registry_mutation": True,
    "publication_replacement": True,
    "exact_bounded_rollback": True,
    "execute_only_under_fresh_matching_evidence": True,
}

SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")

# The existing issue_public_presentation artifact type carries a reviewed public
# projection. This is a transport contract, not a new semantic compiler/type tree.
PROJECTION_SCHEMA_V2R = "editorial_site_integration_publication_v2r"
SUPPORTED_REPLACEMENT_ISSUES = {
    "NATIONAL_SECURITY_FOREIGN", "JUSTICE_PUBLIC_SAFETY",
    "ENVIRONMENT_ENERGY", "EDUCATION_WORKFORCE",
}
PERSISTED_CAPS = {**EXACT_CAPS, "insert_batches": 0, "insert_artifacts": 0,
                  "insert_relationships": 0}


def validate_projection(payload: dict[str, Any]) -> None:
    if set(payload) != {"schema_version", "artifact_id", "subject"} or payload.get("schema_version") != PROJECTION_SCHEMA_V2R:
        _fail("replacement projection envelope differs")
    s = payload["subject"]
    if set(s) != {"member_bioguide_id", "member_slug", "issue_id", "congress", "presentations", "receipt_projections"}:
        _fail("replacement projection fields differ")
    if (not s["member_bioguide_id"] or not s["member_slug"] or s["issue_id"] not in SUPPORTED_REPLACEMENT_ISSUES
            or not isinstance(s["congress"], int) or s["congress"] < 1
            or set(s["presentations"]) != {str(s["congress"]), "all"}):
        _fail("replacement projection identity/scope differs")
    for scope, presentation in s["presentations"].items():
        if (presentation.get("issue_id") != s["issue_id"] or presentation.get("requested_scope") != scope
                or presentation.get("tier") not in {"reviewed_conclusion", "reviewed_pattern", "reviewed_receipts"}
                or presentation.get("review_state", {}).get("candidate_preview")
                or not isinstance(presentation.get("limitations"), list)):
            _fail("replacement public projection is not eligible")
    from .reviewed_record import canonical_action_id
    from .limitation_treatment import public_caveats
    ids = []
    for row in s["receipt_projections"]:
        action = canonical_action_id(row)
        receipt = row.get("governed_receipt_projection")
        if row.get("position") not in {"yea", "nay", "present", "not_voting"}:
            _fail("replacement receipt lacks resolved member action")
        if (action and receipt is None and row.get("governed_receipt_control", {}).get("status") == "noncounting_control"
                and row["governed_receipt_control"].get("boundary_type") and row["governed_receipt_control"].get("detail")):
            ids.append(action)
            continue
        if not action or not isinstance(receipt, dict) or not receipt.get("exact_action_meaning"):
            _fail("replacement receipt lacks exact meaning/identity")
        if (receipt.get("canonical_action_id") != action
                or str(receipt.get("member_action", "")).lower().replace(" ", "_") != row["position"]):
            _fail("replacement receipt conflicts with bound action")
        ids.append(action)
        if "limitation_treatments" in receipt:
            projected = public_caveats(receipt["limitation_treatments"], source_caveats=receipt.get("caveats"))
            if "public_caveats" in receipt and receipt["public_caveats"] != projected:
                _fail("replacement public caveats conflict")
    if not ids or len(ids) != len(set(ids)):
        _fail("replacement receipt coverage is empty/duplicated")


def artifact_identity(artifact: dict[str, Any]) -> dict[str, Any]:
    return {k: artifact[k] for k in ("artifact_id", "natural_key", "artifact_version", "content_sha256")}


def validate_persisted_write_set(write_set: dict[str, Any]) -> None:
    if (set(write_set) != {"schema_version", "artifact_id", "immutable", "subject", "write_set_subject_sha256"}
            or write_set["schema_version"] != REPLACEMENT_WRITE_SET_SCHEMA_V2 or write_set["immutable"] is not True):
        _fail("V2R write-set envelope differs")
    s = write_set["subject"]
    if set(s) != {"replacement_mode", "registry_key", "expected_old", "proposed_new", "replacement_authority_binding",
                   "production_target_identity_sha256", "stable_production_baseline", "publication_registry_update",
                   "mutation_caps", "rollback_target", "public_runtime_manifest_binding"}:
        _fail("persisted replacement write-set fields differ")
    key = s["registry_key"]
    if (set(key) != {"member_bioguide_id", "issue_id"} or not key["member_bioguide_id"]
            or key["issue_id"] not in SUPPORTED_REPLACEMENT_ISSUES):
        _fail("explicit replacement registry key required")
    for identity in (s["expected_old"], s["proposed_new"]):
        if (set(identity) != {"artifact_id", "natural_key", "artifact_version", "content_sha256"}
                or not isinstance(identity["artifact_id"], int) or identity["artifact_id"] <= 0
                or not identity["natural_key"] or not isinstance(identity["artifact_version"], int) or identity["artifact_version"] < 1):
            _fail("exact persisted artifact identity required")
        _digest(identity["content_sha256"], "artifact content")
    if s["expected_old"]["artifact_id"] == s["proposed_new"]["artifact_id"] or s["rollback_target"] != s["expected_old"]:
        _fail("replacement/rollback identities differ")
    binding = s["replacement_authority_binding"]
    if set(binding) != {"artifact_id", "subject_sha256"} or not binding["artifact_id"]:
        _fail("semantic authority identity required")
    _digest(binding["subject_sha256"], "semantic authority")
    _digest(s["production_target_identity_sha256"], "production target")
    prior = s["stable_production_baseline"]["prior_registry_row"]
    if s["stable_production_baseline"] != {
        "prior_registry_row": prior, "expected_old": s["expected_old"], "proposed_new": s["proposed_new"],
        "production_target_identity_sha256": s["production_target_identity_sha256"],
    }:
        _fail("stable baseline differs from bound replacement")
    if (any(prior.get(k) != v for k, v in key.items()) or prior.get("artifact_id") != s["expected_old"]["artifact_id"]
            or prior.get("publicly_active") is not True or prior.get("deactivated_at") is not None):
        _fail("exact prior registry identity differs")
    u = s["publication_registry_update"]
    if (set(u) != {"primary_key", "prior_row", "require_rowcount", "insert_allowed", "delete_allowed", "publication_metadata_jsonb"}
            or u["primary_key"] != key or u["prior_row"] != prior or u["require_rowcount"] != 1
            or u["insert_allowed"] is not False or u["delete_allowed"] is not False or s["mutation_caps"] != PERSISTED_CAPS):
        _fail("one exact registry UPDATE required")
    metadata = u["publication_metadata_jsonb"]
    if set(metadata) != {"presentation_natural_key", "presentation_artifact_version", "active_artifact_sha256",
            "source_manifest_natural_key", "source_manifest_artifact_version", "source_manifest_content_sha256",
            "validation_natural_key", "validation_artifact_version", "validation_content_sha256",
            "relationship_metadata", "v2r_write_set_subject_sha256"}:
        _fail("replacement metadata graph fields differ")
    for prefix in ("validation", "source_manifest"):
        if (not isinstance(metadata[f"{prefix}_natural_key"], str) or not metadata[f"{prefix}_natural_key"]
                or type(metadata[f"{prefix}_artifact_version"]) is not int or metadata[f"{prefix}_artifact_version"] < 1):
            _fail("exact provenance identity required")
    if not isinstance(metadata["relationship_metadata"], dict) or not metadata["relationship_metadata"]:
        _fail("exact relationship metadata required")
    new = s["proposed_new"]
    if (metadata.get("presentation_natural_key") != new["natural_key"]
            or metadata.get("presentation_artifact_version") != new["artifact_version"]
            or metadata.get("active_artifact_sha256") != new["content_sha256"]):
        _fail("proposed registry artifact differs")
    for field in ("source_manifest_content_sha256", "validation_content_sha256"):
        _digest(metadata.get(field), field)
    for field in ("backend_submanifest_sha256", "frontend_submanifest_sha256"):
        _digest(s["public_runtime_manifest_binding"].get(field), field)
    if (metadata.get("v2r_write_set_subject_sha256") != write_set["write_set_subject_sha256"]
            or write_set["write_set_subject_sha256"] != replacement_write_set_subject_sha256(write_set)):
        _fail("V2R write-set subject digest mismatch")


def validate_persisted_authority(authority, *, write_set, candidate):
    validate_persisted_write_set(write_set)
    validate_projection(candidate)
    s = write_set["subject"]
    subject = authority.get("subject", {})
    keys = {"schema_version", "artifact_id", "immutable", "sealed", "accepted", "subject", "activation_authority_subject_sha256"}
    if (set(authority) not in (keys, keys | {"test_only_synthetic"})
            or ("test_only_synthetic" in authority and authority["test_only_synthetic"] is not True)
            or authority.get("schema_version") != REPLACEMENT_AUTHORITY_SCHEMA_V2 or authority.get("sealed") is not True
            or authority.get("accepted") is not True or authority.get("immutable") is not True
            or not authority.get("artifact_id") or not subject.get("reviewer")):
        _fail("sealed human replacement authority required")
    _utc(subject.get("decision_recorded_at_utc"), "decision timestamp")
    expected = {
        "decision": "approve_exact_publication_replacement_v2", "reviewer": subject.get("reviewer"),
        "reviewer_authority": REVIEWER_AUTHORITY_V2R, "decision_recorded_at_utc": subject.get("decision_recorded_at_utc"),
        "registry_key": s["registry_key"], "expected_old": s["expected_old"], "proposed_new": s["proposed_new"],
        "semantic_authority_binding": s["replacement_authority_binding"], "rollback_target": s["rollback_target"],
        "production_target_identity_sha256": s["production_target_identity_sha256"],
        "exact_write_set_subject_sha256": write_set["write_set_subject_sha256"], "authorizations": POSITIVE_AUTHORIZATIONS_V2R,
    }
    if (subject != expected or authority.get("activation_authority_subject_sha256") != canonical_digest(subject)
            or canonical_digest(candidate) != s["proposed_new"]["content_sha256"]
            or candidate["artifact_id"] != s["proposed_new"]["natural_key"]
            or any(candidate["subject"].get(k) != v for k, v in s["registry_key"].items())):
        _fail("authority binds a different replacement")


class PublicationReplacementGovernanceError(ValueError):
    pass


def _fail(message: str) -> None:
    raise PublicationReplacementGovernanceError(message)


def _digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        _fail(f"{label} is not a SHA-256 digest")
    return value


def _utc(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        _fail(f"{label} is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PublicationReplacementGovernanceError(f"{label} is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        _fail(f"{label} is invalid")
    return parsed.astimezone(timezone.utc)


def replacement_write_set_subject(write_set: dict[str, Any]) -> dict[str, Any]:
    """Return the stable subject with its one derived self-binding removed."""

    subject = copy.deepcopy(write_set.get("subject"))
    if not isinstance(subject, dict):
        _fail("V2R write-set subject differs")
    metadata = subject.get("publication_registry_update", {}).get(
        "publication_metadata_jsonb"
    )
    if not isinstance(metadata, dict):
        _fail("V2R registry metadata differs")
    metadata.pop("v2r_write_set_subject_sha256", None)
    return subject


def replacement_write_set_subject_sha256(write_set: dict[str, Any]) -> str:
    return canonical_digest(replacement_write_set_subject(write_set))


def validate_write_set(write_set: dict[str, Any]) -> None:
    if write_set.get("subject", {}).get("replacement_mode") == "persisted_artifact":
        return validate_persisted_write_set(write_set)
    if (
        set(write_set) != {
            "schema_version", "artifact_id", "immutable", "subject",
            "write_set_subject_sha256",
        }
        or write_set["schema_version"] != REPLACEMENT_WRITE_SET_SCHEMA_V2
        or write_set["immutable"] is not True
    ):
        _fail("V2R write-set envelope differs")
    subject = write_set["subject"]
    required = {
        "accepted_site_integration_binding", "preparation_authority_binding",
        "production_target_identity_sha256", "stable_production_baseline",
        "target_new_natural_keys", "artifacts", "relationships",
        "publication_registry_update", "mutation_caps", "rollback_contract_binding",
        "execution_code_manifest_binding", "public_runtime_manifest_binding",
        "expected_postconditions", "activation_authorized",
        "production_write_authorized",
    }
    if not isinstance(subject, dict) or set(subject) != required:
        _fail("V2R write-set fields differ")
    _digest(subject["production_target_identity_sha256"], "production target")
    baseline = subject["stable_production_baseline"]
    if not isinstance(baseline, dict):
        _fail("stable baseline differs")
    prior = baseline.get("prior_registry_row")
    if not isinstance(prior, dict) or {
        "member_bioguide_id": prior.get("member_bioguide_id"),
        "issue_id": prior.get("issue_id"),
    } != TARGET:
        _fail("exact prior Education registry row differs")
    if baseline.get("target_new_natural_keys_found") != []:
        _fail("new target partial existence is forbidden")
    artifacts = subject["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) != 3:
        _fail("exact three-artifact graph differs")
    keys = [item.get("natural_key") for item in artifacts if isinstance(item, dict)]
    if len(keys) != 3 or len(set(keys)) != 3 or sorted(keys) != sorted(
        subject["target_new_natural_keys"]
    ):
        _fail("artifact natural keys differ")
    for item in artifacts:
        if item.get("content_sha256") != canonical_digest(item.get("payload")):
            _fail("artifact content differs")
    presentation = next(
        (item for item in artifacts if item.get("artifact_type") == "issue_public_presentation"),
        None,
    )
    if presentation is None or presentation.get("supersedes_artifact_id") != prior.get(
        "artifact_id"
    ):
        _fail("presentation supersedes binding differs")
    relationships = subject["relationships"]
    if not isinstance(relationships, list) or len(relationships) != 2 or {
        rel.get("relationship_type") for rel in relationships
    } != {"uses_source_manifest", "has_validation"}:
        _fail("exact two-relationship graph differs")
    if subject["mutation_caps"] != EXACT_CAPS:
        _fail("exact replacement mutation caps differ")
    update = subject["publication_registry_update"]
    if not isinstance(update, dict) or update.get("primary_key") != TARGET:
        _fail("registry UPDATE target differs")
    if update.get("prior_row") != prior or update.get("require_rowcount") != 1:
        _fail("registry prior-row recheck differs")
    if update.get("insert_allowed") is not False or update.get("delete_allowed") is not False:
        _fail("registry insert/delete must be forbidden")
    metadata = update.get("publication_metadata_jsonb", {})
    accepted_binding = subject["accepted_site_integration_binding"]
    if (
        not isinstance(accepted_binding, dict)
        or accepted_binding.get("subject_sha256")
        != ACCEPTED_SITE_INTEGRATION_SUBJECT_SHA256
        or metadata.get("m14g_accepted_site_integration_subject_sha256")
        != ACCEPTED_SITE_INTEGRATION_SUBJECT_SHA256
        or metadata.get("m14g_human_site_integration_authority_subject_sha256")
        != HUMAN_SITE_INTEGRATION_AUTHORITY_SHA256
        or metadata.get("m14g_reviewed_candidate_subject_sha256")
        != REVIEWED_CANDIDATE_SUBJECT_SHA256
        or metadata.get("m14g_reviewed_candidate_complete_file_sha256")
        != REVIEWED_CANDIDATE_COMPLETE_FILE_SHA256
    ):
        _fail("exact accepted M14G identity bindings differ")
    for label, binding in (
        ("accepted site integration", accepted_binding),
        ("preparation authority", subject["preparation_authority_binding"]),
        ("rollback contract", subject["rollback_contract_binding"]),
    ):
        if not isinstance(binding, dict) or set(binding) != {
            "artifact_id", "subject_sha256"
        }:
            _fail(f"{label} binding fields differ")
        _digest(binding["subject_sha256"], f"{label} subject")
    execution_binding = subject["execution_code_manifest_binding"]
    if not isinstance(execution_binding, dict) or set(execution_binding) != {
        "subject_sha256"
    }:
        _fail("execution-code binding fields differ")
    _digest(execution_binding["subject_sha256"], "execution-code subject")
    runtime_binding = subject["public_runtime_manifest_binding"]
    if not isinstance(runtime_binding, dict) or set(runtime_binding) != {
        "subject_sha256", "backend_submanifest_sha256",
        "frontend_submanifest_sha256",
    }:
        _fail("public-runtime binding fields differ")
    for field in runtime_binding:
        _digest(runtime_binding[field], f"public-runtime {field}")
    if metadata.get("v2r_write_set_subject_sha256") != write_set[
        "write_set_subject_sha256"
    ]:
        _fail("registry metadata write-set binding differs")
    if subject["activation_authorized"] is not False or subject[
        "production_write_authorized"
    ] is not False:
        _fail("preparation cannot authorize activation")
    claimed = write_set["write_set_subject_sha256"]
    if claimed != replacement_write_set_subject_sha256(write_set):
        _fail("V2R write-set subject digest mismatch")


def validate_positive_authority(
    authority: dict[str, Any], *, write_set: dict[str, Any], candidate: dict[str, Any]
) -> None:
    validate_write_set(write_set)
    if write_set["subject"].get("replacement_mode") == "persisted_artifact":
        return validate_persisted_authority(authority, write_set=write_set, candidate=candidate)
    presentation = next(
        item
        for item in write_set["subject"]["artifacts"]
        if item.get("artifact_type") == "issue_public_presentation"
    )
    if presentation.get("payload") != candidate:
        _fail("accepted candidate drifted from the exact write set")
    authority_keys = {
        "schema_version", "artifact_id", "immutable", "sealed", "accepted",
        "subject", "activation_authority_subject_sha256",
    }
    actual_authority_keys = set(authority)
    synthetic = actual_authority_keys == authority_keys | {"test_only_synthetic"}
    if (
        actual_authority_keys not in (authority_keys, authority_keys | {"test_only_synthetic"})
        or (synthetic and authority.get("test_only_synthetic") is not True)
        or authority.get("schema_version") != REPLACEMENT_AUTHORITY_SCHEMA_V2
        or authority.get("artifact_id") != AUTHORITY_ARTIFACT_ID
        or authority.get("immutable") is not True
        or authority.get("sealed") is not True
        or authority.get("accepted") is not True
    ):
        _fail("sealed accepted positive V2R authority is required")
    subject = authority.get("subject")
    stable = write_set["subject"]
    metadata = stable["publication_registry_update"]["publication_metadata_jsonb"]
    if not isinstance(subject, dict):
        _fail("positive V2R authority subject differs")
    reviewer = subject.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip():
        _fail("positive V2R reviewer is required")
    decision_timestamp = subject.get("decision_recorded_at_utc")
    _utc(decision_timestamp, "activation decision timestamp")
    expected_subject = {
        "decision": "approve_exact_publication_replacement_v2",
        "decision_recorded_at_utc": decision_timestamp,
        "reviewer": reviewer,
        "reviewer_authority": REVIEWER_AUTHORITY_V2R,
        "member_bioguide_id": TARGET["member_bioguide_id"],
        "issue_id": TARGET["issue_id"],
        "congress": 119,
        "accepted_site_integration_subject_sha256": (
            ACCEPTED_SITE_INTEGRATION_SUBJECT_SHA256
        ),
        "reviewed_candidate_subject_sha256": REVIEWED_CANDIDATE_SUBJECT_SHA256,
        "reviewed_candidate_complete_file_sha256": (
            REVIEWED_CANDIDATE_COMPLETE_FILE_SHA256
        ),
        "semantic_human_authority_lineage": [
            HUMAN_SITE_INTEGRATION_AUTHORITY_SHA256,
            ACCEPTED_SITE_INTEGRATION_SUBJECT_SHA256,
        ],
        "preparation_authority_subject_sha256": stable[
            "preparation_authority_binding"
        ]["subject_sha256"],
        "stable_production_baseline_sha256": canonical_digest(
            stable["stable_production_baseline"]
        ),
        "exact_write_set_subject_sha256": write_set["write_set_subject_sha256"],
        "replacement_registry_target": TARGET,
        "prior_registry_identity_sha256": canonical_digest(
            stable["stable_production_baseline"]["prior_registry_row"]
        ),
        "rollback_contract_subject_sha256": stable[
            "rollback_contract_binding"
        ]["subject_sha256"],
        "expected_postconditions_sha256": canonical_digest(
            stable["expected_postconditions"]
        ),
        "execution_code_manifest_subject_sha256": stable[
            "execution_code_manifest_binding"
        ]["subject_sha256"],
        "public_runtime_manifest_subject_sha256": stable[
            "public_runtime_manifest_binding"
        ]["subject_sha256"],
        "production_target_identity_sha256": stable[
            "production_target_identity_sha256"
        ],
        "authorizations": POSITIVE_AUTHORIZATIONS_V2R,
    }
    if (
        set(subject) != set(expected_subject)
        or subject != expected_subject
        or candidate.get("candidate_subject_sha256")
        != REVIEWED_CANDIDATE_SUBJECT_SHA256
        or metadata.get("m14g_reviewed_candidate_subject_sha256")
        != REVIEWED_CANDIDATE_SUBJECT_SHA256
    ):
        _fail("positive V2R authority subject differs")
    if authority.get("activation_authority_subject_sha256") != canonical_digest(subject):
        _fail("positive V2R authority digest mismatch")


def _fresh(timestamp: Any, *, now: datetime | None, max_age_seconds: int) -> None:
    captured = _utc(timestamp, "evidence timestamp")
    age = ((now or datetime.now(timezone.utc)).astimezone(timezone.utc) - captured).total_seconds()
    if age < 0 or age > max_age_seconds:
        _fail("execution evidence is stale")


def validate_execution(
    *, authority: dict[str, Any], write_set: dict[str, Any], candidate: dict[str, Any],
    runtime_evidence: dict[str, Any], production_preflight: dict[str, Any],
    now: datetime | None = None, max_age_seconds: int = 1800,
) -> dict[str, Any]:
    validate_positive_authority(authority, write_set=write_set, candidate=candidate)
    stable = write_set["subject"]
    if runtime_evidence.get("schema_version") != RUNTIME_EVIDENCE_SCHEMA_V2:
        _fail("runtime evidence schema differs")
    runtime_body = copy.deepcopy(runtime_evidence)
    runtime_claim = runtime_body.pop("runtime_health_proof_subject_sha256", None)
    if runtime_claim != canonical_digest(runtime_body):
        _fail("runtime evidence digest mismatch")
    _fresh(runtime_evidence.get("captured_at_utc"), now=now, max_age_seconds=max_age_seconds)
    runtime_binding = stable["public_runtime_manifest_binding"]
    runtime_keys = {
        "schema_version", "captured_at_utc", "healthy", "backend_deployment",
        "frontend_deployment", "deployment_required_before_activation",
        "runtime_health_proof_subject_sha256",
    }
    if set(runtime_evidence) != runtime_keys:
        _fail("runtime evidence fields differ")

    def validate_deployment(
        deployment: Any, *, expected_sha256: Any, backend: bool,
    ) -> None:
        expected_keys = {
            "deployed_commit_sha", "verification_method", "files",
            "submanifest_sha256",
        }
        if backend:
            expected_keys.add("health_commit_sha")
        else:
            expected_keys.add("deployment_source_identity")
        if not isinstance(deployment, dict) or set(deployment) != expected_keys:
            _fail("runtime deployment evidence fields differ")
        commit = deployment.get("deployed_commit_sha")
        if not isinstance(commit, str) or not SHA40.fullmatch(commit):
            _fail("runtime deployed commit is not exact")
        if backend and deployment.get("health_commit_sha") != commit:
            _fail("backend health commit differs from deployed commit")
        if not backend and (
            not isinstance(deployment.get("deployment_source_identity"), str)
            or not deployment["deployment_source_identity"].strip()
        ):
            _fail("frontend deployment identity is unproven")
        if deployment.get("verification_method") != "immutable_git_object_read":
            _fail("runtime deployment verification method differs")
        files = deployment.get("files")
        if not isinstance(files, list) or not files:
            _fail("runtime deployed file manifest is missing")
        if any(
            not isinstance(item, dict)
            or set(item) != {"path", "file_sha256"}
            or not isinstance(item.get("path"), str)
            or not SHA256.fullmatch(item.get("file_sha256", ""))
            for item in files
        ):
            _fail("runtime deployed file manifest differs")
        observed_sha256 = canonical_digest({"files": files})
        if (
            deployment.get("submanifest_sha256") != observed_sha256
            or deployment.get("submanifest_sha256") != expected_sha256
        ):
            _fail("runtime deployed submanifest differs")

    validate_deployment(
        runtime_evidence.get("backend_deployment"),
        expected_sha256=runtime_binding.get("backend_submanifest_sha256"),
        backend=True,
    )
    validate_deployment(
        runtime_evidence.get("frontend_deployment"),
        expected_sha256=runtime_binding.get("frontend_submanifest_sha256"),
        backend=False,
    )
    if (
        runtime_evidence.get("healthy") is not True
        or runtime_evidence.get("deployment_required_before_activation") is not False
    ):
        _fail("runtime drift or incompatibility detected")
    if production_preflight.get("schema_version") != REPLACEMENT_PREFLIGHT_SCHEMA_V2:
        _fail("production preflight schema differs")
    preflight_body = copy.deepcopy(production_preflight)
    preflight_claim = preflight_body.pop("preflight_subject_sha256", None)
    if preflight_claim != canonical_digest(preflight_body):
        _fail("production preflight digest mismatch")
    _fresh(production_preflight.get("captured_at_utc"), now=now, max_age_seconds=max_age_seconds)
    baseline = stable["stable_production_baseline"]
    comparable = {key: production_preflight.get(key) for key in baseline}
    if production_preflight.get("transaction_read_only") is not True or comparable != baseline:
        _fail("fresh production state differs from stable replacement baseline")
    return {
        "schema_version": REPLACEMENT_EXECUTION_SCHEMA_V2,
        "status": "VALID_FOR_EXECUTION",
        "stable_write_set_subject_sha256": write_set["write_set_subject_sha256"],
        "runtime_health_proof_subject_sha256": runtime_claim,
        "preflight_subject_sha256": preflight_claim,
    }
