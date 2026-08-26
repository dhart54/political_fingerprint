from __future__ import annotations

import copy

import pytest

from app.editorial_artifacts.bundle import semantic_hash
from app.editorial_presentations.site_publication import (
    ACTIVATION_AUTHORITY_SCHEMA_VERSION,
    ACTIVATION_REVIEWER_AUTHORITY,
    EDUCATION_ACTIVATION_AUTHORITY_ID,
    POSITIVE_AUTHORIZATIONS,
)
from scripts.editorial_artifact_store import StoreSafetyError
from scripts.foushee_education_workforce_publication_preparation import (
    BACKEND,
    BASELINE_IDENTITIES,
    CURRENT_COUNTS,
    ISSUE_ID,
    M13M_ARTIFACT_ID,
    PRODUCTION_TARGET_IDENTITY_SHA256,
    ROOT,
    RUNTIME_SOURCE_PATHS,
    _write_set_digest,
    activation_write_set_binding,
    assert_runtime_source_convergence,
    build_activation_decision_template,
    build_authority,
    build_write_set,
    reviewed_runtime_manifest,
    validate_production_execution_inputs,
    validate_runtime_health_proof,
    validate_write_set,
)

DEPLOYED_COMMIT = "a" * 40


def synthetic_preflight() -> dict:
    report = {
        "schema_version": "m13n_current_production_preflight_v1",
        "captured_at_utc": "2026-08-25T00:00:00+00:00",
        "deployed_commit": DEPLOYED_COMMIT,
        "transaction_read_only": True,
        "counts": copy.deepcopy(CURRENT_COUNTS),
        "state_fingerprint_sha256": "b" * 64,
        "baseline_registry_rows": {
            issue_id: {
                "natural_key": natural_key,
                "content_sha256": content_sha256,
                "publicly_active": True,
            }
            for issue_id, (natural_key, content_sha256) in BASELINE_IDENTITIES.items()
        },
        "education_registry_rows": [],
        "m13n_target_rows": [],
        "selector_pre_activation": {},
    }
    report["preflight_subject_sha256"] = semantic_hash(report)
    return report


def synthetic_activation_authority(write_set: dict) -> dict:
    metadata = write_set["publication_registry"]["publication_metadata"]
    runtime_manifest = metadata["reviewed_runtime_binding"][
        "reviewed_runtime_manifest_sha256"
    ]
    runtime = {
        "reviewed_runtime_manifest_sha256": runtime_manifest,
        "reviewed_commit": DEPLOYED_COMMIT,
        "deployed_commit": DEPLOYED_COMMIT,
        "health_commit": DEPLOYED_COMMIT,
    }
    subject = {
        "decision": "approve_exact_publication_activation",
        "decision_recorded_at_utc": "2026-08-25T00:30:00Z",
        "reviewer": "synthetic-disposable-reviewer",
        "reviewer_authority": ACTIVATION_REVIEWER_AUTHORITY,
        "product_owner": "dhart54",
        "member_bioguide_id": "F000477",
        "issue_id": ISSUE_ID,
        "congress": 119,
        "accepted_site_integration_binding": write_set[
            "accepted_site_integration_binding"
        ],
        "candidate_preparation_authority_binding": write_set["authority_binding"],
        "activation_write_set_binding": activation_write_set_binding(write_set),
        "publication_registry_target": {
            "member_bioguide_id": "F000477",
            "issue_id": ISSUE_ID,
            "presentation_natural_key": M13M_ARTIFACT_ID,
            "presentation_artifact_version": 1,
        },
        "presentation_content_sha256": metadata["active_artifact_sha256"],
        "preflight_binding": metadata["preflight_binding"],
        "rollback_binding": metadata["rollback_binding"],
        "runtime_binding": runtime,
        "ratification_runtime_evidence_binding": {
            "runtime_health_proof_subject_sha256": "c" * 64,
            "captured_at_utc": "2026-08-25T00:29:00Z",
            "reviewed_runtime_manifest_sha256": runtime_manifest,
            "deployed_commit": DEPLOYED_COMMIT,
            "health_commit": DEPLOYED_COMMIT,
        },
        "production_target_identity_sha256": PRODUCTION_TARGET_IDENTITY_SHA256,
        "authorizations": copy.deepcopy(POSITIVE_AUTHORIZATIONS),
    }
    return {
        "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        "artifact_id": EDUCATION_ACTIVATION_AUTHORITY_ID,
        "immutable": True,
        "sealed": True,
        "accepted": True,
        "test_only_synthetic": True,
        "subject": subject,
        "activation_authority_subject_sha256": semantic_hash(subject),
    }


def test_declared_runtime_source_set_is_complete_and_exists() -> None:
    expected = {
        "backend/app/api/positions.py",
        "backend/app/api/editorial_presentations.py",
        "backend/app/editorial_presentations/selector.py",
        "backend/app/editorial_presentations/site_publication.py",
        "backend/app/editorial_presentations/education_workforce_integration_candidate.py",
        "backend/scripts/foushee_education_workforce_publication_preparation.py",
    }
    assert_runtime_source_convergence()
    assert len(RUNTIME_SOURCE_PATHS) == 6
    assert all(path.is_file() for path in RUNTIME_SOURCE_PATHS)
    assert {
        path.relative_to(ROOT).as_posix() for path in RUNTIME_SOURCE_PATHS
    } == expected
    assert {item["path"] for item in reviewed_runtime_manifest()["files"]} == expected
    assert RUNTIME_SOURCE_PATHS[-1] == (
        BACKEND / "scripts/foushee_education_workforce_publication_preparation.py"
    )


def test_preparation_graph_is_exact_non_authorizing_and_candidate_is_m13m() -> None:
    preflight = synthetic_preflight()
    authority = build_authority(preflight)
    write_set = build_write_set(preflight, authority)
    template = build_activation_decision_template(write_set, authority)
    validate_write_set(write_set, authority=authority)
    candidate_row = next(
        row for row in write_set["artifacts"] if row["natural_key"] == M13M_ARTIFACT_ID
    )
    assert candidate_row["payload"]["artifact_id"] == M13M_ARTIFACT_ID
    assert len(write_set["artifacts"]) == 3
    assert len(write_set["relationships"]) == 2
    assert write_set["activation_authorized"] is False
    assert write_set["production_write_authorized"] is False
    assert template["sealed"] is False and template["accepted"] is False
    completion = template["subject"][
        "completion_required_after_exact_runtime_deployment"
    ]
    assert all(
        value is None for key, value in completion.items() if key != "authorizations"
    )
    assert all(value is None for value in completion["authorizations"].values())


def test_runtime_manifest_drift_and_write_graph_drift_fail_closed() -> None:
    preflight = synthetic_preflight()
    authority = build_authority(preflight)
    write_set = build_write_set(preflight, authority)
    drifted = copy.deepcopy(write_set)
    drifted["artifacts"][0]["content_sha256"] = "0" * 64
    drifted["write_set_subject_sha256"] = _write_set_digest(drifted)
    drifted["publication_registry"]["publication_metadata"][
        "activation_write_set_binding"
    ] = activation_write_set_binding(drifted)
    with pytest.raises(StoreSafetyError, match="persistence gate"):
        validate_write_set(drifted, authority=authority)

    proof = {
        "schema_version": "m13n_live_runtime_health_proof_v1",
        "captured_at_utc": "2026-08-25T00:00:00+00:00",
        "health_endpoint": "https://example.invalid/health",
        "deployed_commit": DEPLOYED_COMMIT,
        "health_commit": DEPLOYED_COMMIT,
        "reviewed_runtime_manifest_sha256": "0" * 64,
        "health_payload_sha256": "d" * 64,
    }
    proof["runtime_health_proof_subject_sha256"] = semantic_hash(proof)
    with pytest.raises(StoreSafetyError, match="production_runtime_not_converged"):
        validate_runtime_health_proof(
            proof, require_fresh=False, require_current_runtime=True
        )


def test_production_execution_is_impossible_without_future_exact_authority() -> None:
    preflight = synthetic_preflight()
    authority = build_authority(preflight)
    write_set = build_write_set(preflight, authority)
    with pytest.raises(StoreSafetyError, match="positive activation authority"):
        validate_production_execution_inputs(
            database_url="postgresql://wrong.invalid/db",
            preflight=preflight,
            write_set=write_set,
            candidate_authority=authority,
            activation_authority=None,
            runtime_proof=None,
        )
    activation = synthetic_activation_authority(write_set)
    with pytest.raises(StoreSafetyError, match="non-exact production target"):
        validate_production_execution_inputs(
            database_url="postgresql://wrong.invalid/db",
            preflight=preflight,
            write_set=write_set,
            candidate_authority=authority,
            activation_authority=activation,
            runtime_proof=None,
        )


def test_m13n_package_contains_no_authorizing_or_mutation_artifacts() -> None:
    output = (
        ROOT / "docs/editorial/full_record_reviews/publication_activation_candidates/"
        "f000477_education_workforce_119_v1"
    )
    assert output.exists()
    forbidden = {
        "positive_activation_authority.json",
        "activation_receipt.json",
        "current_state.json",
    }
    assert not any((output / name).exists() for name in forbidden)
