from __future__ import annotations

import copy
import os

import pytest

from app.editorial_artifacts.bundle import semantic_hash
from app.editorial_artifacts.publication_activation import load_activation_bundle
from app.editorial_presentations.site_publication import (
    ACTIVATION_AUTHORITY_SCHEMA_VERSION,
    ACTIVATION_REVIEWER_AUTHORITY,
    EDUCATION_ACTIVATION_AUTHORITY_ID,
    ENVIRONMENT_ACTIVATION_AUTHORITY_ID,
    POSITIVE_AUTHORIZATIONS,
)
from scripts.editorial_artifact_store import StoreSafetyError, _connect
from scripts.foushee_education_workforce_publication_preparation import (
    ISSUE_ID,
    PRODUCTION_TARGET_IDENTITY_SHA256,
    _apply,
    _counts,
    _registry_rows,
    _rollback,
    _selector_state,
    _state_fingerprint,
    _write_set_digest,
    activation_write_set_binding,
    build_authority,
    build_write_set,
    capture_preflight,
)
from scripts.foushee_environment_energy_publication_preparation import (
    ISSUE_ID as ENVIRONMENT_ISSUE_ID,
    POST_M12M_MAIN,
    _apply as apply_environment,
    activation_write_set_binding as environment_write_set_binding,
    build_authority as build_environment_authority,
    build_write_set as build_environment_write_set,
    capture_preflight as capture_environment_preflight,
)
from scripts.foushee_justice_full_record_activation import (
    _apply as apply_justice_full_record,
    build_bundle as build_justice_full_record_bundle,
    preflight as justice_full_record_preflight,
)
from scripts.foushee_justice_publication_activation import (
    _apply as apply_justice_compact,
)
from scripts.foushee_national_security_publication_activation import (
    POST_M11M_MAIN,
    _apply as apply_national_security,
    activation_write_set_binding as national_security_write_set_binding,
    build_authority as build_national_security_authority,
    build_write_set as build_national_security_write_set,
    capture_preflight as capture_national_security_preflight,
)

DATABASE_URL = os.getenv("M13NR_DISPOSABLE_DATABASE_URL")
DEPLOYED_COMMIT = "a" * 40

pytestmark = pytest.mark.skipif(
    not DATABASE_URL, reason="M13NR_DISPOSABLE_DATABASE_URL is required"
)


def _activation(
    write_set: dict, *, issue_id: str, artifact_id: str, write_binding: dict
) -> dict:
    metadata = write_set["publication_registry"]["publication_metadata"]
    runtime_manifest = metadata["reviewed_runtime_binding"][
        "reviewed_runtime_manifest_sha256"
    ]
    subject = {
        "decision": "approve_exact_publication_activation",
        "decision_recorded_at_utc": "2026-08-25T00:30:00Z",
        "reviewer": "synthetic-disposable-reviewer",
        "reviewer_authority": ACTIVATION_REVIEWER_AUTHORITY,
        "product_owner": "dhart54",
        "member_bioguide_id": "F000477",
        "issue_id": issue_id,
        "congress": 119,
        "accepted_site_integration_binding": write_set[
            "accepted_site_integration_binding"
        ],
        "candidate_preparation_authority_binding": write_set["authority_binding"],
        "activation_write_set_binding": write_binding,
        "publication_registry_target": {
            "member_bioguide_id": "F000477",
            "issue_id": issue_id,
            "presentation_natural_key": write_set["publication_registry"][
                "presentation_natural_key"
            ],
            "presentation_artifact_version": 1,
        },
        "presentation_content_sha256": metadata["active_artifact_sha256"],
        "preflight_binding": metadata["preflight_binding"],
        "rollback_binding": metadata["rollback_binding"],
        "runtime_binding": {
            "reviewed_runtime_manifest_sha256": runtime_manifest,
            "reviewed_commit": write_set["preflight_binding"]["deployed_commit"],
            "deployed_commit": write_set["preflight_binding"]["deployed_commit"],
            "health_commit": write_set["preflight_binding"]["deployed_commit"],
        },
        "ratification_runtime_evidence_binding": {
            "runtime_health_proof_subject_sha256": "c" * 64,
            "captured_at_utc": "2026-08-25T00:29:00Z",
            "reviewed_runtime_manifest_sha256": runtime_manifest,
            "deployed_commit": write_set["preflight_binding"]["deployed_commit"],
            "health_commit": write_set["preflight_binding"]["deployed_commit"],
        },
        "production_target_identity_sha256": metadata[
            "production_target_identity_sha256"
        ],
        "authorizations": copy.deepcopy(POSITIVE_AUTHORIZATIONS),
    }
    return {
        "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "immutable": True,
        "sealed": True,
        "accepted": True,
        "test_only_synthetic": True,
        "subject": subject,
        "activation_authority_subject_sha256": semantic_hash(subject),
    }


def _national_security_activation(write_set: dict) -> dict:
    metadata = write_set["publication_registry"]["publication_metadata"]
    subject = {
        "decision": "approve_exact_publication_activation",
        "decision_recorded_at_utc": "2026-08-14T12:00:00Z",
        "reviewer": "synthetic-disposable-reviewer",
        "reviewer_authority": ACTIVATION_REVIEWER_AUTHORITY,
        "product_owner": "dhart54",
        "member_bioguide_id": "F000477",
        "issue_id": "NATIONAL_SECURITY_FOREIGN",
        "congress": 119,
        "accepted_m11m_binding": write_set["accepted_m11m_binding"],
        "candidate_preparation_authority_binding": write_set["authority_binding"],
        "activation_write_set_binding": national_security_write_set_binding(write_set),
        "publication_registry_target": {
            "member_bioguide_id": "F000477",
            "issue_id": "NATIONAL_SECURITY_FOREIGN",
            "presentation_natural_key": write_set["publication_registry"][
                "presentation_natural_key"
            ],
            "presentation_artifact_version": 1,
        },
        "presentation_content_sha256": metadata["active_artifact_sha256"],
        "preflight_binding": metadata["preflight_binding"],
        "rollback_binding": metadata["rollback_binding"],
        "runtime_binding": {
            "reviewed_runtime_manifest_sha256": metadata["reviewed_runtime_binding"][
                "reviewed_runtime_manifest_sha256"
            ],
            "reviewed_commit": write_set["preflight_binding"]["deployed_commit"],
            "deployed_commit": write_set["preflight_binding"]["deployed_commit"],
            "health_commit": write_set["preflight_binding"]["deployed_commit"],
            "health_proof_subject_sha256": "b" * 64,
        },
        "production_target_identity_sha256": metadata[
            "production_target_identity_sha256"
        ],
        "authorizations": copy.deepcopy(POSITIVE_AUTHORIZATIONS),
    }
    return {
        "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        "artifact_id": "publication-activation-authority:f000477:national_security_foreign:119:v1",
        "immutable": True,
        "sealed": True,
        "accepted": True,
        "test_only_synthetic": True,
        "subject": subject,
        "activation_authority_subject_sha256": semantic_hash(subject),
    }


def _prepare_post_m12n_baseline(conn) -> None:
    compact = load_activation_bundle()
    with conn.transaction():
        apply_justice_compact(conn, compact)
    justice_preflight = justice_full_record_preflight(conn, POST_M11M_MAIN)
    justice_bundle = build_justice_full_record_bundle(justice_preflight, POST_M11M_MAIN)
    with conn.transaction():
        apply_justice_full_record(conn, justice_bundle)
    ns_preflight = capture_national_security_preflight(
        conn, deployed_commit=POST_M11M_MAIN
    )
    ns_authority = build_national_security_authority(ns_preflight)
    ns_write_set = build_national_security_write_set(ns_preflight, ns_authority)
    with conn.transaction():
        apply_national_security(
            conn,
            ns_write_set,
            ns_authority,
            _national_security_activation(ns_write_set),
            allow_test_authority=True,
        )
    env_preflight = capture_environment_preflight(
        conn,
        deployed_commit=POST_M12M_MAIN,
        allow_test_activation_authority=True,
    )
    env_authority = build_environment_authority(env_preflight)
    env_write_set = build_environment_write_set(env_preflight, env_authority)
    env_activation = _activation(
        env_write_set,
        issue_id=ENVIRONMENT_ISSUE_ID,
        artifact_id=ENVIRONMENT_ACTIVATION_AUTHORITY_ID,
        write_binding=environment_write_set_binding(env_write_set),
    )
    with conn.transaction():
        apply_environment(
            conn,
            env_write_set,
            env_authority,
            env_activation,
            allow_test_authority=True,
        )


def test_disposable_apply_idempotency_drift_refusal_and_exact_rollback() -> None:
    assert DATABASE_URL is not None
    with _connect(DATABASE_URL, autocommit=False) as conn:
        _prepare_post_m12n_baseline(conn)
        before_counts = _counts(conn)
        before_fingerprint = _state_fingerprint(conn)
        before_registry = _registry_rows(conn)
        before_selector = _selector_state(conn, allow_test_activation_authority=True)
        preflight = capture_preflight(
            conn,
            deployed_commit=DEPLOYED_COMMIT,
            allow_test_activation_authority=True,
        )
        authority = build_authority(preflight)
        write_set = build_write_set(preflight, authority)
        activation = _activation(
            write_set,
            issue_id=ISSUE_ID,
            artifact_id=EDUCATION_ACTIVATION_AUTHORITY_ID,
            write_binding=activation_write_set_binding(write_set),
        )

        drifted = copy.deepcopy(write_set)
        drifted["preflight_binding"]["state_fingerprint_sha256"] = "0" * 64
        drifted["publication_registry"]["publication_metadata"]["preflight_binding"][
            "state_fingerprint_sha256"
        ] = "0" * 64
        drifted["write_set_subject_sha256"] = _write_set_digest(drifted)
        drifted["publication_registry"]["publication_metadata"][
            "activation_write_set_binding"
        ] = activation_write_set_binding(drifted)
        drift_activation = _activation(
            drifted,
            issue_id=ISSUE_ID,
            artifact_id=EDUCATION_ACTIVATION_AUTHORITY_ID,
            write_binding=activation_write_set_binding(drifted),
        )
        with pytest.raises(StoreSafetyError, match="drifted from M13N preflight"):
            with conn.transaction(force_rollback=True):
                _apply(
                    conn,
                    drifted,
                    authority,
                    drift_activation,
                    allow_test_authority=True,
                )

        with conn.transaction():
            first = _apply(
                conn,
                write_set,
                authority,
                activation,
                allow_test_authority=True,
            )
        assert first["already_applied"] is False
        assert first["postcheck"]["counts"]["publication_registry"] == 4
        assert first["postcheck"]["selector"]["scopes"]["119"][ISSUE_ID] == (
            "reviewed_conclusion"
        )
        with conn.transaction():
            second = _apply(
                conn,
                write_set,
                authority,
                activation,
                allow_test_authority=True,
            )
        assert second["already_applied"] is True

        with conn.transaction():
            rolled_back = _rollback(
                conn,
                write_set,
                authority,
                activation,
                allow_test_authority=True,
            )
        assert rolled_back["counts"] == before_counts
        assert rolled_back["state_fingerprint_sha256"] == before_fingerprint
        assert _registry_rows(conn) == before_registry
        assert (
            _selector_state(conn, allow_test_activation_authority=True)
            == before_selector
        )
        assert PRODUCTION_TARGET_IDENTITY_SHA256
