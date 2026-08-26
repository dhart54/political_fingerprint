from __future__ import annotations

import copy
from datetime import datetime, timezone

import pytest

from app.editorial_presentations.compiler import canonical_digest
from app.editorial_presentations.publication_activation_governance_v2 import (
    ACTIVATION_AUTHORITY_SCHEMA_VERSION_V2,
    ACTIVATION_REVIEWER_AUTHORITY_V2,
    ACTIVATION_WRITE_SET_SCHEMA_VERSION_V2,
    POSITIVE_AUTHORIZATIONS_V2,
    PREFLIGHT_EVIDENCE_SCHEMA_VERSION_V2,
    RUNTIME_EVIDENCE_SCHEMA_VERSION_V2,
    VOLATILE_PREFLIGHT_FIELDS,
    VOLATILE_RUNTIME_FIELDS,
    PublicationActivationGovernanceError,
    stable_authority_subject_sha256,
    stable_write_set_subject_sha256,
    validate_execution_v2,
    validate_stable_positive_authority,
)

NOW = datetime(2026, 8, 26, 2, 0, tzinfo=timezone.utc)
RUNTIME_COMMIT = "1" * 40
RUNTIME_MANIFEST = "2" * 64
PRODUCTION_TARGET = "3" * 64
BASELINE_FINGERPRINT = "4" * 64
TEST_ISSUE_ID = "SYNTHETIC_CONTRACT_TEST"
TARGET_KEY = "test-site-integration-candidate:f000477:synthetic_contract:119:v1"


def _binding(artifact_id: str, *, content_sha256: str = "5" * 64) -> dict:
    return {
        "artifact_id": artifact_id,
        "subject_sha256": "6" * 64,
        "file_sha256": "7" * 64,
        "content_sha256": content_sha256,
    }


def _baseline() -> dict:
    return {
        "production_target_identity_sha256": PRODUCTION_TARGET,
        "state_fingerprint_sha256": BASELINE_FINGERPRINT,
        "counts": {
            "batches": 7,
            "artifacts": 155,
            "relationships": 165,
            "publication_registry": 4,
        },
        "existing_registry_identities": [
            {
                "member_bioguide_id": "F000477",
                "issue_id": "EDUCATION_WORKFORCE",
                "artifact_id": 242,
                "artifact_version": 1,
                "presentation_natural_key": (
                    "site-integration-candidate:f000477:education_workforce:119:v1"
                ),
                "content_sha256": "8" * 64,
                "source_commit_sha": "1" * 40,
                "publication_metadata_sha256": "8" * 64,
                "publicly_active": True,
            },
            {
                "member_bioguide_id": "F000477",
                "issue_id": "ENVIRONMENT_ENERGY",
                "artifact_id": 239,
                "artifact_version": 1,
                "presentation_natural_key": (
                    "site-integration-candidate:f000477:environment_energy:119:v1"
                ),
                "content_sha256": "9" * 64,
                "source_commit_sha": "2" * 40,
                "publication_metadata_sha256": "9" * 64,
                "publicly_active": True,
            },
            {
                "member_bioguide_id": "F000477",
                "issue_id": "JUSTICE_PUBLIC_SAFETY",
                "artifact_id": 221,
                "artifact_version": 1,
                "presentation_natural_key": (
                    "site-integration-candidate:f000477:justice_public_safety:119:v1"
                ),
                "content_sha256": "a" * 64,
                "source_commit_sha": "3" * 40,
                "publication_metadata_sha256": "a" * 64,
                "publicly_active": True,
            },
            {
                "member_bioguide_id": "F000477",
                "issue_id": "NATIONAL_SECURITY_FOREIGN",
                "artifact_id": 227,
                "artifact_version": 1,
                "presentation_natural_key": (
                    "site-integration-candidate:f000477:national_security_foreign:119:v1"
                ),
                "content_sha256": "b" * 64,
                "source_commit_sha": "4" * 40,
                "publication_metadata_sha256": "b" * 64,
                "publicly_active": True,
            },
        ],
        "target_registry_identity": {
            "member_bioguide_id": "F000477",
            "issue_id": TEST_ISSUE_ID,
            "presentation_natural_key": TARGET_KEY,
            "presentation_artifact_version": 1,
        },
        "target_artifact_natural_keys": [TARGET_KEY],
        "state_predicates": {
            "existing_publication_rows_unchanged": True,
            "target_registry_row_absent": True,
            "target_artifacts_absent": True,
        },
        "write_preconditions": {
            "artifact_natural_keys_available": True,
            "registry_primary_key_available": True,
            "relationship_graph_insertable": True,
        },
    }


def _package() -> tuple[dict, dict, dict]:
    candidate = {
        "schema_version": "editorial_site_integration_candidate_v1",
        "artifact_id": TARGET_KEY,
        "subject": {"member_bioguide_id": "F000477", "issue_id": TEST_ISSUE_ID},
    }
    candidate_binding = _binding(TARGET_KEY, content_sha256=canonical_digest(candidate))
    preparation = {
        "artifact_id": (
            "test-publication-preparation-authority:f000477:synthetic_contract:119:v2"
        ),
        "authority_subject_sha256": "c" * 64,
        "decision_recorded_at_utc": "2026-08-26T00:30:00Z",
    }
    runtime = {
        "reviewed_runtime_manifest_sha256": RUNTIME_MANIFEST,
        "reviewed_source_commit": RUNTIME_COMMIT,
    }
    baseline = _baseline()
    rollback = {
        "owned_artifact_natural_keys": [TARGET_KEY],
        "restore_counts": baseline["counts"],
        "restore_state_fingerprint_sha256": BASELINE_FINGERPRINT,
    }
    postconditions = {
        "counts": {
            "batches": 8,
            "artifacts": 156,
            "relationships": 165,
            "publication_registry": 5,
        },
        "selector": {"119": "reviewed_conclusion", "118": "receipts_only"},
        "existing_domain_isolation": True,
    }
    write_subject = {
        "accepted_site_integration_binding": candidate_binding,
        "preparation_authority_binding": preparation,
        "stable_runtime_binding": runtime,
        "stable_production_baseline_binding_sha256": canonical_digest(baseline),
        "production_target_identity_sha256": PRODUCTION_TARGET,
        "artifacts": [
            {
                "natural_key": TARGET_KEY,
                "payload": candidate,
                "content_sha256": canonical_digest(candidate),
            }
        ],
        "relationships": [],
        "publication_registry_target": baseline["target_registry_identity"],
        "mutation_caps": {
            "insert_batches": 1,
            "insert_artifacts": 1,
            "insert_relationships": 0,
            "insert_registry_rows": 1,
            "updates": 0,
            "deletes": 0,
            "unauthorized_table_writes": 0,
        },
        "rollback_contract": rollback,
        "expected_postconditions": postconditions,
    }
    write_set = {
        "schema_version": ACTIVATION_WRITE_SET_SCHEMA_VERSION_V2,
        "artifact_id": (
            "test-publication-activation-write-set:f000477:synthetic_contract:119:v2"
        ),
        "immutable": True,
        "subject": write_subject,
        "write_set_subject_sha256": canonical_digest(write_subject),
    }
    authority_subject = {
        "decision": "approve_exact_publication_activation_v2",
        "decision_recorded_at_utc": "2026-08-26T01:00:00Z",
        "reviewer": "governance-reviewer",
        "reviewer_authority": ACTIVATION_REVIEWER_AUTHORITY_V2,
        "member_bioguide_id": "F000477",
        "issue_id": TEST_ISSUE_ID,
        "congress": 119,
        "accepted_site_integration_binding": candidate_binding,
        "semantic_authority_lineage": [
            _binding("test-human-semantic-authority:f000477:synthetic_contract:119:v1")
        ],
        "preparation_authority_binding": preparation,
        "stable_runtime_binding": runtime,
        "stable_production_baseline": baseline,
        "exact_write_set_subject_sha256": write_set["write_set_subject_sha256"],
        "publication_registry_target": baseline["target_registry_identity"],
        "rollback_contract_sha256": canonical_digest(rollback),
        "expected_postconditions_sha256": canonical_digest(postconditions),
        "authorizations": POSITIVE_AUTHORIZATIONS_V2,
    }
    authority = {
        "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION_V2,
        "artifact_id": (
            "test-publication-activation-authority:f000477:synthetic_contract:119:v2"
        ),
        "immutable": True,
        "sealed": True,
        "accepted": True,
        "subject": authority_subject,
        "activation_authority_subject_sha256": canonical_digest(authority_subject),
    }
    return candidate, write_set, authority


def _runtime_proof(captured_at: str, *, commit: str = RUNTIME_COMMIT) -> dict:
    proof = {
        "schema_version": RUNTIME_EVIDENCE_SCHEMA_VERSION_V2,
        "captured_at_utc": captured_at,
        "healthy": True,
        "deployed_commit": commit,
        "health_commit": commit,
        "current_runtime_manifest_sha256": RUNTIME_MANIFEST,
    }
    proof["runtime_health_proof_subject_sha256"] = canonical_digest(proof)
    return proof


def _preflight(captured_at: str) -> dict:
    baseline = _baseline()
    preflight = {
        "schema_version": PREFLIGHT_EVIDENCE_SCHEMA_VERSION_V2,
        "captured_at_utc": captured_at,
        "transaction_read_only": True,
        "production_target_identity_sha256": PRODUCTION_TARGET,
        "state_fingerprint_sha256": BASELINE_FINGERPRINT,
        "counts": baseline["counts"],
        "existing_registry_identities": baseline["existing_registry_identities"],
        "target_registry_identity": baseline["target_registry_identity"],
        "target_registry_rows": [],
        "target_artifact_natural_keys_checked": baseline[
            "target_artifact_natural_keys"
        ],
        "target_artifact_natural_keys_found": [],
        "state_predicates": baseline["state_predicates"],
        "write_preconditions": baseline["write_preconditions"],
    }
    preflight["preflight_subject_sha256"] = canonical_digest(preflight)
    return preflight


def _rehash(document: dict, digest_field: str) -> None:
    body = copy.deepcopy(document)
    body.pop(digest_field, None)
    document[digest_field] = canonical_digest(body)


def _execution(
    authority: dict, candidate: dict, write_set: dict, proof: dict, preflight: dict
) -> dict:
    return validate_execution_v2(
        authority=authority,
        candidate=candidate,
        write_set=write_set,
        runtime_proof=proof,
        production_preflight=preflight,
        now=NOW,
    )


def test_equivalent_fresh_evidence_keeps_stable_authority_and_write_set() -> None:
    candidate, write_set, authority = _package()
    proof_a = _runtime_proof("2026-08-26T01:45:00Z")
    proof_b = _runtime_proof("2026-08-26T01:55:00Z")
    preflight_a = _preflight("2026-08-26T01:46:00Z")
    preflight_b = _preflight("2026-08-26T01:56:00Z")
    authority_identity = stable_authority_subject_sha256(authority)
    write_set_identity = stable_write_set_subject_sha256(write_set)

    result_a = _execution(authority, candidate, write_set, proof_a, preflight_a)
    result_b = _execution(authority, candidate, write_set, proof_b, preflight_b)

    assert result_a["status"] == result_b["status"] == "VALID_FOR_EXECUTION"
    assert (
        proof_a["runtime_health_proof_subject_sha256"]
        != proof_b["runtime_health_proof_subject_sha256"]
    )
    assert (
        preflight_a["preflight_subject_sha256"]
        != preflight_b["preflight_subject_sha256"]
    )
    assert stable_authority_subject_sha256(authority) == authority_identity
    assert stable_write_set_subject_sha256(write_set) == write_set_identity
    assert (
        result_a["stable_activation_authority_subject_sha256"]
        == result_b["stable_activation_authority_subject_sha256"]
    )
    assert (
        result_a["stable_write_set_subject_sha256"]
        == result_b["stable_write_set_subject_sha256"]
    )


def test_expired_evidence_is_mechanically_replaceable_without_human_review() -> None:
    candidate, write_set, authority = _package()
    stale_proof = _runtime_proof("2026-08-26T01:00:00Z")
    stale_preflight = _preflight("2026-08-26T01:00:00Z")
    with pytest.raises(PublicationActivationGovernanceError, match="stale"):
        _execution(authority, candidate, write_set, stale_proof, stale_preflight)

    fresh_proof = _runtime_proof("2026-08-26T01:59:00Z")
    fresh_preflight = _preflight("2026-08-26T01:59:00Z")
    result = _execution(authority, candidate, write_set, fresh_proof, fresh_preflight)
    assert result["status"] == "VALID_FOR_EXECUTION"
    assert (
        result["stable_activation_authority_subject_sha256"]
        == authority["activation_authority_subject_sha256"]
    )
    assert (
        result["stable_write_set_subject_sha256"]
        == write_set["write_set_subject_sha256"]
    )


@pytest.mark.parametrize("drift", ["commit", "manifest"])
def test_runtime_drift_fails_closed(drift: str) -> None:
    candidate, write_set, authority = _package()
    proof = _runtime_proof("2026-08-26T01:59:00Z")
    if drift == "commit":
        proof["deployed_commit"] = proof["health_commit"] = "f" * 40
    else:
        proof["current_runtime_manifest_sha256"] = "f" * 64
    _rehash(proof, "runtime_health_proof_subject_sha256")
    with pytest.raises(PublicationActivationGovernanceError, match="ratified runtime"):
        _execution(
            authority, candidate, write_set, proof, _preflight("2026-08-26T01:59:00Z")
        )


@pytest.mark.parametrize(
    "drift",
    [
        "fingerprint",
        "registry_content",
        "registry_metadata",
        "target",
        "counts",
        "precondition",
    ],
)
def test_production_state_and_precondition_drift_fail_closed(drift: str) -> None:
    candidate, write_set, authority = _package()
    preflight = _preflight("2026-08-26T01:59:00Z")
    if drift == "fingerprint":
        preflight["state_fingerprint_sha256"] = "f" * 64
    elif drift == "registry_content":
        preflight["existing_registry_identities"][0]["content_sha256"] = "f" * 64
    elif drift == "registry_metadata":
        preflight["existing_registry_identities"][0]["publication_metadata_sha256"] = (
            "f" * 64
        )
    elif drift == "target":
        preflight["target_registry_rows"] = [{"unexpected": True}]
    elif drift == "counts":
        preflight["counts"]["artifacts"] += 1
    else:
        preflight["write_preconditions"]["artifact_natural_keys_available"] = False
    _rehash(preflight, "preflight_subject_sha256")
    with pytest.raises(PublicationActivationGovernanceError):
        _execution(
            authority,
            candidate,
            write_set,
            _runtime_proof("2026-08-26T01:59:00Z"),
            preflight,
        )


def test_write_graph_drift_fails_closed_under_existing_authority() -> None:
    candidate, write_set, authority = _package()
    changed = copy.deepcopy(write_set)
    changed["subject"]["artifacts"][0]["payload"]["subject"]["issue_id"] = "DRIFT"
    changed["subject"]["artifacts"][0]["content_sha256"] = canonical_digest(
        changed["subject"]["artifacts"][0]["payload"]
    )
    changed["write_set_subject_sha256"] = canonical_digest(changed["subject"])
    with pytest.raises(PublicationActivationGovernanceError, match="exact write set"):
        validate_stable_positive_authority(
            authority, candidate=candidate, write_set=changed
        )


def test_volatile_execution_fields_are_absent_from_stable_subjects() -> None:
    _, write_set, authority = _package()
    stable_text = repr(authority["subject"]) + repr(write_set["subject"])
    for field in VOLATILE_RUNTIME_FIELDS | VOLATILE_PREFLIGHT_FIELDS:
        assert field not in stable_text


def test_human_decision_cannot_predate_preparation_authority() -> None:
    candidate, write_set, authority = _package()
    authority["subject"]["decision_recorded_at_utc"] = "2026-08-25T23:59:00Z"
    authority["activation_authority_subject_sha256"] = canonical_digest(
        authority["subject"]
    )
    with pytest.raises(PublicationActivationGovernanceError, match="precedes"):
        validate_stable_positive_authority(
            authority, candidate=candidate, write_set=write_set
        )
