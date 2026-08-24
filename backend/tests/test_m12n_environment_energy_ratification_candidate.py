from __future__ import annotations

import copy
import json
from datetime import datetime, timedelta, timezone

import pytest

from app.editorial_artifacts.bundle import semantic_hash
from app.editorial_presentations.environment_integration_candidate import (
    load_environment_site_integration_candidate,
)
from app.editorial_presentations.site_publication import (
    ACTIVATION_AUTHORITY_SCHEMA_VERSION,
    ACTIVATION_REVIEWER_AUTHORITY,
    ENVIRONMENT_ACTIVATION_AUTHORITY_ID,
    POSITIVE_AUTHORIZATIONS,
    validate_environment_positive_activation_authority,
)
from scripts.editorial_artifact_store import StoreSafetyError
from scripts.foushee_environment_energy_publication_preparation import (
    AUTHORITY_PATH,
    M12M_PATH,
    WRITE_SET_PATH,
    activation_write_set_binding,
    reviewed_runtime_manifest,
    validate_production_execution_runtime,
)
from scripts.validate_m12n_publication_activation_ratification_candidate import (
    validate_candidate,
)
from scripts.materialize_m12n_environment_energy_activation_authority import (
    DECISION_RECORDED_AT_UTC,
    POSITIVE_AUTHORITY_PATH,
    RATIFIED_PROSPECTIVE_SUBJECT_SHA256,
    build_authority,
    validate_files,
    validate_authority,
)


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _runtime_proof(
    *,
    captured_at: datetime,
    commit: str,
    manifest_sha256: str,
    health_commit: str | None = None,
) -> dict:
    body = {
        "schema_version": "m12n_live_runtime_health_proof_v1",
        "captured_at_utc": captured_at.astimezone(timezone.utc).isoformat(),
        "health_endpoint": "https://example.invalid/health",
        "deployed_commit": commit,
        "health_commit": health_commit or commit,
        "reviewed_runtime_manifest_sha256": manifest_sha256,
        "health_payload_sha256": "9" * 64,
    }
    body["runtime_health_proof_subject_sha256"] = semantic_hash(body)
    return body


def _synthetic_authority(*, commit: str, manifest_sha256: str) -> dict:
    write_set = _load(WRITE_SET_PATH)
    metadata = copy.deepcopy(write_set["publication_registry"]["publication_metadata"])
    metadata["activation_write_set_binding"] = activation_write_set_binding(write_set)
    stable_runtime = {
        "reviewed_runtime_manifest_sha256": manifest_sha256,
        "reviewed_commit": commit,
        "deployed_commit": commit,
        "health_commit": commit,
    }
    subject = {
        "decision": "approve_exact_publication_activation",
        "decision_recorded_at_utc": "2026-08-17T00:00:00Z",
        "reviewer": "synthetic-disposable-reviewer",
        "reviewer_authority": ACTIVATION_REVIEWER_AUTHORITY,
        "product_owner": "dhart54",
        "member_bioguide_id": "F000477",
        "issue_id": "ENVIRONMENT_ENERGY",
        "congress": 119,
        "accepted_site_integration_binding": write_set[
            "accepted_site_integration_binding"
        ],
        "candidate_preparation_authority_binding": metadata[
            "candidate_preparation_authority_binding"
        ],
        "activation_write_set_binding": activation_write_set_binding(write_set),
        "publication_registry_target": {
            "member_bioguide_id": "F000477",
            "issue_id": "ENVIRONMENT_ENERGY",
            "presentation_natural_key": write_set["publication_registry"][
                "presentation_natural_key"
            ],
            "presentation_artifact_version": 1,
        },
        "presentation_content_sha256": metadata["active_artifact_sha256"],
        "preflight_binding": metadata["preflight_binding"],
        "rollback_binding": metadata["rollback_binding"],
        "runtime_binding": stable_runtime,
        "ratification_runtime_evidence_binding": {
            "runtime_health_proof_subject_sha256": "1" * 64,
            "captured_at_utc": "2020-01-01T00:00:00Z",
            "reviewed_runtime_manifest_sha256": manifest_sha256,
            "deployed_commit": commit,
            "health_commit": commit,
        },
        "production_target_identity_sha256": metadata[
            "production_target_identity_sha256"
        ],
        "authorizations": copy.deepcopy(POSITIVE_AUTHORIZATIONS),
    }
    return {
        "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        "artifact_id": ENVIRONMENT_ACTIVATION_AUTHORITY_ID,
        "immutable": True,
        "sealed": True,
        "accepted": True,
        "test_only_synthetic": True,
        "subject": subject,
        "activation_authority_subject_sha256": semantic_hash(subject),
    }


def test_m12n_ratification_candidate_is_exact_and_non_authorizing() -> None:
    candidate = validate_candidate()
    subject = candidate["prospective_authority_subject"]
    assert candidate["immutable"] is True
    assert candidate["accepted"] is False
    assert candidate["sealed"] is False
    assert "decision_recorded_at_utc" not in subject
    assert subject["candidate_prepared_at_utc"] == "2026-08-17T00:57:58Z"
    assert "health_proof_subject_sha256" not in subject["runtime_binding"]
    assert (
        subject["ratification_runtime_evidence_binding"][
            "runtime_health_proof_subject_sha256"
        ]
        == "22f9dfd2e1a42e1c9d4c1ffc3bf1f7799911036e7b6c0c78a20a2e65e42d7516"
    )


def test_m12n_ratification_candidate_cannot_satisfy_live_selector_authority() -> None:
    candidate = validate_candidate()
    write_set = _load(WRITE_SET_PATH)
    with pytest.raises(ValueError, match="binding differs"):
        validate_environment_positive_activation_authority(
            candidate,
            candidate=load_environment_site_integration_candidate(M12M_PATH),
            candidate_authority=_load(AUTHORITY_PATH),
            metadata=write_set["publication_registry"]["publication_metadata"],
        )


def test_materialized_authority_adds_only_ratified_decision_timestamp() -> None:
    candidate = validate_candidate()
    authority = build_authority()
    stripped = copy.deepcopy(authority["subject"])
    assert stripped.pop("decision_recorded_at_utc") == DECISION_RECORDED_AT_UTC
    assert stripped == candidate["prospective_authority_subject"]
    assert semantic_hash(stripped) == RATIFIED_PROSPECTIVE_SUBJECT_SHA256
    assert authority["accepted"] is True
    assert authority["sealed"] is True
    assert authority["immutable"] is True
    validate_authority(authority)


def test_failed_activation_and_rollback_remain_governed_history() -> None:
    _, _, receipt, state = validate_files()
    assert receipt["immutable"] is True
    assert receipt["subject"]["attempt"]["initial_apply"]["batch_id"] == 18
    assert receipt["subject"]["attempt"]["initial_apply"]["artifact_ids"] == [
        233,
        234,
        235,
    ]
    assert receipt["subject"]["live_postcheck"]["http_status_by_scope"] == {
        "119": 500,
        "all": 500,
        "118": 500,
    }
    assert (
        receipt["subject"]["live_postcheck"]["production_activation_survived_postcheck"]
        is False
    )
    assert receipt["subject"]["rollback"]["completed"] is True
    assert state["subject"] == {
        "activation_attempted": True,
        "activation_survived_postcheck": False,
        "rollback_completed": True,
        "environment_publication_active": False,
        "environment_selector_state": {
            "119": "receipts_only",
            "all": "receipts_only",
            "118": "receipts_only",
        },
        "blocking_runtime_defect": "active_environment_receipt_evidence_dispatch",
        "failed_activation_receipt_binding": state["subject"][
            "failed_activation_receipt_binding"
        ],
        "sealed_authority_reuse": "prohibited_after_runtime_repair",
    }


def test_old_ratification_proof_does_not_expire_stable_authority() -> None:
    write_set = _load(WRITE_SET_PATH)
    manifest = write_set["publication_registry"]["publication_metadata"][
        "reviewed_runtime_binding"
    ]["reviewed_runtime_manifest_sha256"]
    authority = _synthetic_authority(commit="a" * 40, manifest_sha256=manifest)
    metadata = copy.deepcopy(write_set["publication_registry"]["publication_metadata"])
    metadata["activation_write_set_binding"] = activation_write_set_binding(write_set)

    validate_environment_positive_activation_authority(
        authority,
        candidate=load_environment_site_integration_candidate(M12M_PATH),
        candidate_authority=_load(AUTHORITY_PATH),
        metadata=metadata,
        allow_test_authority=True,
    )


def test_failed_attempt_authority_cannot_bind_repaired_runtime() -> None:
    authority = _load(POSITIVE_AUTHORITY_PATH)
    current_manifest = reviewed_runtime_manifest()["reviewed_runtime_manifest_sha256"]
    failed_attempt_manifest = authority["subject"]["runtime_binding"][
        "reviewed_runtime_manifest_sha256"
    ]
    assert failed_attempt_manifest == (
        "a22bee788697eb84da900be5ec9a0aef0c6949c59a6a9c2d7f697cdf369036c1"
    )
    assert current_manifest != failed_attempt_manifest

    repaired_runtime_proof = _runtime_proof(
        captured_at=datetime.now(timezone.utc),
        commit=authority["subject"]["runtime_binding"]["deployed_commit"],
        manifest_sha256=current_manifest,
    )
    with pytest.raises(StoreSafetyError, match="runtime"):
        validate_production_execution_runtime(authority, repaired_runtime_proof)


def test_production_execution_requires_new_fresh_proof() -> None:
    manifest = reviewed_runtime_manifest()["reviewed_runtime_manifest_sha256"]
    authority = _synthetic_authority(commit="a" * 40, manifest_sha256=manifest)

    with pytest.raises(StoreSafetyError, match="fresh execution proof"):
        validate_production_execution_runtime(authority, None)

    stale = _runtime_proof(
        captured_at=datetime.now(timezone.utc) - timedelta(seconds=1801),
        commit="a" * 40,
        manifest_sha256=manifest,
    )
    with pytest.raises(StoreSafetyError, match="not fresh"):
        validate_production_execution_runtime(authority, stale)


@pytest.mark.parametrize("mutation", ["deployed_commit", "health_commit", "manifest"])
def test_execution_proof_must_match_stable_runtime(mutation: str) -> None:
    manifest = reviewed_runtime_manifest()["reviewed_runtime_manifest_sha256"]
    authority = _synthetic_authority(commit="a" * 40, manifest_sha256=manifest)
    proof = _runtime_proof(
        captured_at=datetime.now(timezone.utc),
        commit="a" * 40,
        manifest_sha256=manifest,
    )
    if mutation == "deployed_commit":
        proof["deployed_commit"] = "b" * 40
    elif mutation == "health_commit":
        proof["health_commit"] = "b" * 40
    else:
        proof["reviewed_runtime_manifest_sha256"] = "b" * 64
    proof_body = copy.deepcopy(proof)
    proof_body.pop("runtime_health_proof_subject_sha256")
    proof["runtime_health_proof_subject_sha256"] = semantic_hash(proof_body)

    with pytest.raises(StoreSafetyError, match="runtime"):
        validate_production_execution_runtime(authority, proof)


def test_fresh_execution_proof_digest_may_differ_from_ratification_digest() -> None:
    manifest = reviewed_runtime_manifest()["reviewed_runtime_manifest_sha256"]
    authority = _synthetic_authority(commit="a" * 40, manifest_sha256=manifest)
    proof = _runtime_proof(
        captured_at=datetime.now(timezone.utc),
        commit="a" * 40,
        manifest_sha256=manifest,
    )
    assert (
        proof["runtime_health_proof_subject_sha256"]
        != (
            authority["subject"]["ratification_runtime_evidence_binding"][
                "runtime_health_proof_subject_sha256"
            ]
        )
    )

    validate_production_execution_runtime(authority, proof)
