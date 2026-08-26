"""Future-only publication activation governance with durable human authority.

V2 deliberately keeps volatile runtime and database evidence out of stable
authority and write-set subjects.  A caller must capture fresh evidence and pass
this validation boundary *before* opening a production mutation transaction.
Accepted V1 authorities and publication rows continue to use ``site_publication``.
"""

from __future__ import annotations

import copy
import re
from datetime import datetime, timezone
from typing import Any

from .compiler import canonical_digest

ACTIVATION_AUTHORITY_SCHEMA_VERSION_V2 = (
    "site_integration_publication_activation_authority_v2"
)
ACTIVATION_WRITE_SET_SCHEMA_VERSION_V2 = "publication_activation_write_set_v2"
RUNTIME_EVIDENCE_SCHEMA_VERSION_V2 = (
    "publication_activation_runtime_execution_evidence_v2"
)
PREFLIGHT_EVIDENCE_SCHEMA_VERSION_V2 = (
    "publication_activation_production_preflight_evidence_v2"
)
EXECUTION_VALIDATION_SCHEMA_VERSION_V2 = (
    "publication_activation_execution_validation_v2"
)
ACTIVATION_REVIEWER_AUTHORITY_V2 = "publication_activation_review_authority_v2"

POSITIVE_AUTHORIZATIONS_V2 = {
    "production_database_write": True,
    "publication_registry_mutation": True,
    "publication_activation": True,
    "exact_bounded_rollback": True,
    "execute_only_under_fresh_matching_evidence": True,
}

VOLATILE_RUNTIME_FIELDS = frozenset(
    {
        "captured_at_utc",
        "runtime_health_proof_file_sha256",
        "runtime_health_proof_subject_sha256",
    }
)
VOLATILE_PREFLIGHT_FIELDS = frozenset(
    {
        "captured_at_utc",
        "execution_preflight_file_sha256",
        "preflight_subject_sha256",
    }
)

SHA40 = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")


class PublicationActivationGovernanceError(ValueError):
    """A fail-closed V2 publication-governance validation failure."""


def _fail(message: str) -> None:
    raise PublicationActivationGovernanceError(message)


def _exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        _fail(f"{label} fields differ")
    return value


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        _fail(f"{label} is not a SHA-256 digest")
    return value


def _sha40(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA40.fullmatch(value):
        _fail(f"{label} is not a source commit")
    return value


def _utc(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        _fail(f"{label} is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PublicationActivationGovernanceError(f"{label} is invalid") from exc
    if parsed.tzinfo is None:
        _fail(f"{label} is invalid")
    return parsed.astimezone(timezone.utc)


def _validate_identity(binding: Any, label: str) -> dict[str, Any]:
    binding = _exact_keys(
        binding,
        {"artifact_id", "subject_sha256", "file_sha256", "content_sha256"},
        label,
    )
    if not isinstance(binding["artifact_id"], str) or not binding["artifact_id"]:
        _fail(f"{label} artifact identity differs")
    for field in ("subject_sha256", "file_sha256", "content_sha256"):
        _sha256(binding[field], f"{label}.{field}")
    return binding


def _validate_preparation_binding(binding: Any) -> dict[str, Any]:
    binding = _exact_keys(
        binding,
        {"artifact_id", "authority_subject_sha256", "decision_recorded_at_utc"},
        "preparation authority binding",
    )
    if not isinstance(binding["artifact_id"], str) or not binding["artifact_id"]:
        _fail("preparation authority artifact identity differs")
    _sha256(
        binding["authority_subject_sha256"],
        "preparation authority subject",
    )
    _utc(binding["decision_recorded_at_utc"], "preparation decision timestamp")
    return binding


def _validate_runtime_binding(runtime: Any) -> dict[str, Any]:
    runtime = _exact_keys(
        runtime,
        {"reviewed_runtime_manifest_sha256", "reviewed_source_commit"},
        "stable runtime binding",
    )
    _sha256(
        runtime["reviewed_runtime_manifest_sha256"],
        "reviewed runtime manifest",
    )
    _sha40(runtime["reviewed_source_commit"], "reviewed source commit")
    return runtime


def _validate_counts(counts: Any, label: str) -> dict[str, int]:
    if (
        not isinstance(counts, dict)
        or not counts
        or any(not isinstance(key, str) or not key for key in counts)
        or any(type(value) is not int or value < 0 for value in counts.values())
    ):
        _fail(f"{label} differ")
    return counts


def _validate_registry_identity(identity: Any, label: str) -> dict[str, Any]:
    identity = _exact_keys(
        identity,
        {
            "member_bioguide_id",
            "issue_id",
            "artifact_id",
            "artifact_version",
            "presentation_natural_key",
            "content_sha256",
            "source_commit_sha",
            "publication_metadata_sha256",
            "publicly_active",
        },
        label,
    )
    if any(
        not isinstance(identity[field], str) or not identity[field]
        for field in (
            "member_bioguide_id",
            "issue_id",
            "presentation_natural_key",
        )
    ):
        _fail(f"{label} differs")
    if (
        type(identity["artifact_id"]) is not int
        or type(identity["artifact_version"]) is not int
    ):
        _fail(f"{label} artifact identity differs")
    _sha256(identity["content_sha256"], f"{label}.content_sha256")
    _sha40(identity["source_commit_sha"], f"{label}.source_commit_sha")
    _sha256(
        identity["publication_metadata_sha256"],
        f"{label}.publication_metadata_sha256",
    )
    if type(identity["publicly_active"]) is not bool:
        _fail(f"{label} active state differs")
    return identity


def _validate_registry_target(target: Any) -> dict[str, Any]:
    target = _exact_keys(
        target,
        {
            "member_bioguide_id",
            "issue_id",
            "presentation_natural_key",
            "presentation_artifact_version",
        },
        "publication registry target",
    )
    if (
        any(
            not isinstance(target[field], str) or not target[field]
            for field in (
                "member_bioguide_id",
                "issue_id",
                "presentation_natural_key",
            )
        )
        or type(target["presentation_artifact_version"]) is not int
    ):
        _fail("publication registry target differs")
    return target


def _validate_baseline(baseline: Any) -> dict[str, Any]:
    baseline = _exact_keys(
        baseline,
        {
            "production_target_identity_sha256",
            "state_fingerprint_sha256",
            "counts",
            "existing_registry_identities",
            "target_registry_identity",
            "target_artifact_natural_keys",
            "state_predicates",
            "write_preconditions",
        },
        "stable production baseline",
    )
    _sha256(baseline["production_target_identity_sha256"], "production target identity")
    _sha256(baseline["state_fingerprint_sha256"], "baseline state fingerprint")
    _validate_counts(baseline["counts"], "baseline counts")
    identities = baseline["existing_registry_identities"]
    if not isinstance(identities, list):
        _fail("existing registry identities differ")
    for index, identity in enumerate(identities):
        _validate_registry_identity(identity, f"existing registry identity {index}")
    if identities != sorted(
        identities,
        key=lambda item: (item["member_bioguide_id"], item["issue_id"]),
    ):
        _fail("existing registry identities are not canonical")
    _validate_registry_target(baseline["target_registry_identity"])
    target_keys = baseline["target_artifact_natural_keys"]
    if (
        not isinstance(target_keys, list)
        or not target_keys
        or target_keys != sorted(set(target_keys))
        or any(not isinstance(key, str) or not key for key in target_keys)
    ):
        _fail("target artifact identities differ")
    for field in ("state_predicates", "write_preconditions"):
        if not isinstance(baseline[field], dict) or not baseline[field]:
            _fail(f"baseline {field} differ")
    return baseline


def stable_write_set_subject_sha256(write_set: dict[str, Any]) -> str:
    """Return the stable write-set subject identity after intrinsic validation."""

    subject = _validate_write_set_intrinsic(write_set)
    return canonical_digest(subject)


def stable_authority_subject_sha256(authority: dict[str, Any]) -> str:
    """Return the stable human-authority identity after intrinsic validation."""

    subject = _validate_authority_intrinsic(authority)
    return canonical_digest(subject)


def _validate_write_set_intrinsic(write_set: Any) -> dict[str, Any]:
    write_set = _exact_keys(
        write_set,
        {
            "schema_version",
            "artifact_id",
            "immutable",
            "subject",
            "write_set_subject_sha256",
        },
        "V2 write set",
    )
    subject = _exact_keys(
        write_set["subject"],
        {
            "accepted_site_integration_binding",
            "preparation_authority_binding",
            "stable_runtime_binding",
            "stable_production_baseline_binding_sha256",
            "production_target_identity_sha256",
            "artifacts",
            "relationships",
            "publication_registry_target",
            "mutation_caps",
            "rollback_contract",
            "expected_postconditions",
        },
        "V2 write-set subject",
    )
    if (
        write_set["schema_version"] != ACTIVATION_WRITE_SET_SCHEMA_VERSION_V2
        or not isinstance(write_set["artifact_id"], str)
        or not write_set["artifact_id"]
        or write_set["immutable"] is not True
    ):
        _fail("V2 write-set envelope differs")
    _validate_identity(
        subject["accepted_site_integration_binding"], "candidate binding"
    )
    _validate_preparation_binding(subject["preparation_authority_binding"])
    _validate_runtime_binding(subject["stable_runtime_binding"])
    _sha256(
        subject["stable_production_baseline_binding_sha256"],
        "stable production baseline binding",
    )
    _sha256(subject["production_target_identity_sha256"], "production target identity")
    _validate_registry_target(subject["publication_registry_target"])
    artifacts = subject["artifacts"]
    relationships = subject["relationships"]
    if not isinstance(artifacts, list) or not artifacts:
        _fail("bounded artifact graph differs")
    if not isinstance(relationships, list):
        _fail("bounded relationship graph differs")
    natural_keys: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            _fail("bounded artifact graph differs")
        key = artifact.get("natural_key")
        payload = artifact.get("payload")
        if (
            not isinstance(key, str)
            or not key
            or key in natural_keys
            or not isinstance(payload, dict)
            or artifact.get("content_sha256") != canonical_digest(payload)
        ):
            _fail("bounded artifact graph differs")
        natural_keys.add(key)
    caps = _exact_keys(
        subject["mutation_caps"],
        {
            "insert_batches",
            "insert_artifacts",
            "insert_relationships",
            "insert_registry_rows",
            "updates",
            "deletes",
            "unauthorized_table_writes",
        },
        "mutation caps",
    )
    if caps != {
        "insert_batches": 1,
        "insert_artifacts": len(artifacts),
        "insert_relationships": len(relationships),
        "insert_registry_rows": 1,
        "updates": 0,
        "deletes": 0,
        "unauthorized_table_writes": 0,
    }:
        _fail("mutation caps differ from exact write graph")
    if (
        not isinstance(subject["rollback_contract"], dict)
        or not subject["rollback_contract"]
    ):
        _fail("rollback contract differs")
    if (
        not isinstance(subject["expected_postconditions"], dict)
        or not subject["expected_postconditions"]
    ):
        _fail("expected postconditions differ")
    claimed = write_set["write_set_subject_sha256"]
    if claimed != canonical_digest(subject):
        _fail("V2 write-set subject digest mismatch")
    return subject


def _validate_authority_intrinsic(authority: Any) -> dict[str, Any]:
    authority = _exact_keys(
        authority,
        {
            "schema_version",
            "artifact_id",
            "immutable",
            "sealed",
            "accepted",
            "subject",
            "activation_authority_subject_sha256",
        },
        "V2 stable authority",
    )
    subject = _exact_keys(
        authority["subject"],
        {
            "decision",
            "decision_recorded_at_utc",
            "reviewer",
            "reviewer_authority",
            "member_bioguide_id",
            "issue_id",
            "congress",
            "accepted_site_integration_binding",
            "semantic_authority_lineage",
            "preparation_authority_binding",
            "stable_runtime_binding",
            "stable_production_baseline",
            "exact_write_set_subject_sha256",
            "publication_registry_target",
            "rollback_contract_sha256",
            "expected_postconditions_sha256",
            "authorizations",
        },
        "V2 stable authority subject",
    )
    if (
        authority["schema_version"] != ACTIVATION_AUTHORITY_SCHEMA_VERSION_V2
        or not isinstance(authority["artifact_id"], str)
        or not authority["artifact_id"]
        or authority["immutable"] is not True
        or authority["sealed"] is not True
        or authority["accepted"] is not True
        or subject["decision"] != "approve_exact_publication_activation_v2"
        or subject["reviewer_authority"] != ACTIVATION_REVIEWER_AUTHORITY_V2
        or not isinstance(subject["reviewer"], str)
        or not subject["reviewer"].strip()
        or not isinstance(subject["member_bioguide_id"], str)
        or not subject["member_bioguide_id"]
        or not isinstance(subject["issue_id"], str)
        or not subject["issue_id"]
        or type(subject["congress"]) is not int
        or subject["authorizations"] != POSITIVE_AUTHORIZATIONS_V2
    ):
        _fail("V2 stable authority envelope differs")
    decision_time = _utc(
        subject["decision_recorded_at_utc"], "activation decision timestamp"
    )
    candidate_binding = _validate_identity(
        subject["accepted_site_integration_binding"], "candidate binding"
    )
    if (
        not isinstance(subject["semantic_authority_lineage"], list)
        or not subject["semantic_authority_lineage"]
    ):
        _fail("semantic authority lineage differs")
    for index, binding in enumerate(subject["semantic_authority_lineage"]):
        _validate_identity(binding, f"semantic authority lineage {index}")
    preparation = _validate_preparation_binding(
        subject["preparation_authority_binding"]
    )
    if decision_time < _utc(
        preparation["decision_recorded_at_utc"], "preparation decision timestamp"
    ):
        _fail("activation decision precedes the preparation authority it approves")
    _validate_runtime_binding(subject["stable_runtime_binding"])
    baseline = _validate_baseline(subject["stable_production_baseline"])
    _sha256(subject["exact_write_set_subject_sha256"], "exact write-set subject")
    _validate_registry_target(subject["publication_registry_target"])
    _sha256(subject["rollback_contract_sha256"], "rollback contract")
    _sha256(subject["expected_postconditions_sha256"], "expected postconditions")
    if (
        candidate_binding["artifact_id"]
        != subject["publication_registry_target"]["presentation_natural_key"]
    ):
        _fail("candidate and registry target identities differ")
    if baseline["target_registry_identity"] != subject["publication_registry_target"]:
        _fail("baseline and authority registry targets differ")
    claimed = authority["activation_authority_subject_sha256"]
    if claimed != canonical_digest(subject):
        _fail("V2 stable authority subject digest mismatch")
    return subject


def validate_exact_write_set(
    write_set: dict[str, Any],
    *,
    candidate: dict[str, Any],
    authority: dict[str, Any],
) -> None:
    """Validate the exact stable graph and its bindings to candidate/authority."""

    write_subject = _validate_write_set_intrinsic(write_set)
    authority_subject = _validate_authority_intrinsic(authority)
    candidate_binding = authority_subject["accepted_site_integration_binding"]
    if candidate_binding["content_sha256"] != canonical_digest(candidate):
        _fail("candidate bytes differ from stable human authority")
    if write_subject["accepted_site_integration_binding"] != candidate_binding:
        _fail("write set candidate binding differs from stable human authority")
    if (
        write_subject["preparation_authority_binding"]
        != authority_subject["preparation_authority_binding"]
        or write_subject["stable_runtime_binding"]
        != authority_subject["stable_runtime_binding"]
        or write_subject["stable_production_baseline_binding_sha256"]
        != canonical_digest(authority_subject["stable_production_baseline"])
        or write_subject["production_target_identity_sha256"]
        != authority_subject["stable_production_baseline"][
            "production_target_identity_sha256"
        ]
        or write_subject["publication_registry_target"]
        != authority_subject["publication_registry_target"]
        or write_set["write_set_subject_sha256"]
        != authority_subject["exact_write_set_subject_sha256"]
        or canonical_digest(write_subject["rollback_contract"])
        != authority_subject["rollback_contract_sha256"]
        or canonical_digest(write_subject["expected_postconditions"])
        != authority_subject["expected_postconditions_sha256"]
    ):
        _fail("stable authority and exact write set differ")
    if not any(
        artifact["natural_key"] == candidate_binding["artifact_id"]
        and artifact["payload"] == candidate
        for artifact in write_subject["artifacts"]
    ):
        _fail("write graph does not contain the exact ratified candidate")


def validate_stable_positive_authority(
    authority: dict[str, Any],
    *,
    candidate: dict[str, Any],
    write_set: dict[str, Any],
) -> None:
    """Validate durable human authority without consulting execution evidence."""

    validate_exact_write_set(write_set, candidate=candidate, authority=authority)


def validate_fresh_runtime_evidence(
    proof: dict[str, Any],
    *,
    stable_runtime: dict[str, Any],
    max_age_seconds: int = 1800,
    now: datetime | None = None,
) -> None:
    """Validate fresh live health evidence against the ratified runtime identity."""

    proof = _exact_keys(
        proof,
        {
            "schema_version",
            "captured_at_utc",
            "healthy",
            "deployed_commit",
            "health_commit",
            "current_runtime_manifest_sha256",
            "runtime_health_proof_subject_sha256",
        },
        "runtime execution evidence",
    )
    _validate_runtime_binding(stable_runtime)
    body = copy.deepcopy(proof)
    claimed = body.pop("runtime_health_proof_subject_sha256")
    if claimed != canonical_digest(body):
        _fail("runtime execution evidence digest mismatch")
    captured = _utc(proof["captured_at_utc"], "runtime evidence timestamp")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    age = (current - captured).total_seconds()
    if age < 0 or age > max_age_seconds:
        _fail("runtime execution evidence is stale; capture a fresh proof")
    if (
        proof["schema_version"] != RUNTIME_EVIDENCE_SCHEMA_VERSION_V2
        or proof["healthy"] is not True
        or proof["deployed_commit"] != stable_runtime["reviewed_source_commit"]
        or proof["health_commit"] != stable_runtime["reviewed_source_commit"]
        or proof["deployed_commit"] != proof["health_commit"]
        or proof["current_runtime_manifest_sha256"]
        != stable_runtime["reviewed_runtime_manifest_sha256"]
    ):
        _fail("fresh runtime evidence differs from ratified runtime")


def validate_fresh_production_preflight(
    preflight: dict[str, Any],
    *,
    stable_baseline: dict[str, Any],
    max_age_seconds: int = 1800,
    now: datetime | None = None,
) -> None:
    """Compare a fresh read-only observation to every stable baseline invariant."""

    preflight = _exact_keys(
        preflight,
        {
            "schema_version",
            "captured_at_utc",
            "transaction_read_only",
            "production_target_identity_sha256",
            "state_fingerprint_sha256",
            "counts",
            "existing_registry_identities",
            "target_registry_identity",
            "target_registry_rows",
            "target_artifact_natural_keys_checked",
            "target_artifact_natural_keys_found",
            "state_predicates",
            "write_preconditions",
            "preflight_subject_sha256",
        },
        "production execution preflight",
    )
    _validate_baseline(stable_baseline)
    body = copy.deepcopy(preflight)
    claimed = body.pop("preflight_subject_sha256")
    if claimed != canonical_digest(body):
        _fail("production execution preflight digest mismatch")
    captured = _utc(preflight["captured_at_utc"], "preflight timestamp")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    age = (current - captured).total_seconds()
    if age < 0 or age > max_age_seconds:
        _fail("production execution preflight is stale; capture a fresh preflight")
    if (
        preflight["schema_version"] != PREFLIGHT_EVIDENCE_SCHEMA_VERSION_V2
        or preflight["transaction_read_only"] is not True
        or preflight["production_target_identity_sha256"]
        != stable_baseline["production_target_identity_sha256"]
        or preflight["state_fingerprint_sha256"]
        != stable_baseline["state_fingerprint_sha256"]
        or preflight["counts"] != stable_baseline["counts"]
        or preflight["existing_registry_identities"]
        != stable_baseline["existing_registry_identities"]
        or preflight["target_registry_identity"]
        != stable_baseline["target_registry_identity"]
        or preflight["target_registry_rows"] != []
        or preflight["target_artifact_natural_keys_checked"]
        != stable_baseline["target_artifact_natural_keys"]
        or preflight["target_artifact_natural_keys_found"] != []
        or preflight["state_predicates"] != stable_baseline["state_predicates"]
        or preflight["write_preconditions"] != stable_baseline["write_preconditions"]
    ):
        _fail("fresh production state differs from ratified baseline")


def validate_current_write_preconditions(
    preflight: dict[str, Any], *, write_set: dict[str, Any]
) -> None:
    """Fail closed when the current observations cannot admit the exact graph."""

    subject = _validate_write_set_intrinsic(write_set)
    caps = subject["mutation_caps"]
    expected = preflight.get("write_preconditions")
    if not isinstance(expected, dict) or any(
        value is not True for value in expected.values()
    ):
        _fail("current write preconditions are not all satisfied")
    if (
        caps["updates"] != 0
        or caps["deletes"] != 0
        or caps["unauthorized_table_writes"] != 0
    ):
        _fail("write envelope permits unauthorized mutation")


def validate_execution_v2(
    *,
    authority: dict[str, Any],
    candidate: dict[str, Any],
    write_set: dict[str, Any],
    runtime_proof: dict[str, Any],
    production_preflight: dict[str, Any],
    max_age_seconds: int = 1800,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Validate all V2 gates before a production mutation transaction may open."""

    validate_stable_positive_authority(
        authority, candidate=candidate, write_set=write_set
    )
    subject = authority["subject"]
    validate_fresh_runtime_evidence(
        runtime_proof,
        stable_runtime=subject["stable_runtime_binding"],
        max_age_seconds=max_age_seconds,
        now=now,
    )
    validate_fresh_production_preflight(
        production_preflight,
        stable_baseline=subject["stable_production_baseline"],
        max_age_seconds=max_age_seconds,
        now=now,
    )
    validate_current_write_preconditions(production_preflight, write_set=write_set)
    validated_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return {
        "schema_version": EXECUTION_VALIDATION_SCHEMA_VERSION_V2,
        "status": "VALID_FOR_EXECUTION",
        "validated_at_utc": validated_at.isoformat().replace("+00:00", "Z"),
        "stable_activation_authority_subject_sha256": authority[
            "activation_authority_subject_sha256"
        ],
        "stable_write_set_subject_sha256": write_set["write_set_subject_sha256"],
        "runtime_health_proof_subject_sha256": runtime_proof[
            "runtime_health_proof_subject_sha256"
        ],
        "execution_preflight_subject_sha256": production_preflight[
            "preflight_subject_sha256"
        ],
    }
