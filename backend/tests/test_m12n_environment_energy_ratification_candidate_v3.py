from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from app.editorial_artifacts.bundle import semantic_hash
from app.editorial_presentations.environment_integration_candidate import (
    load_environment_site_integration_candidate,
)
from app.editorial_presentations.site_publication import (
    validate_environment_positive_activation_authority,
)
from scripts.editorial_artifact_store import StoreSafetyError
from scripts.foushee_environment_energy_publication_preparation import (
    AUTHORITY_PATH,
    M12M_PATH,
    RUNTIME_PROOF_PATH,
    WRITE_SET_PATH,
    reviewed_runtime_manifest,
    validate_production_execution_runtime,
)
from scripts.materialize_m12n_environment_energy_activation_authority import (
    POSITIVE_AUTHORITY_PATH,
)
from scripts.build_m12n_environment_energy_ratification_candidate_v3 import (
    FAILED_RUNTIME_MANIFEST,
    POST_REPAIR_MAIN,
    REPAIRED_RUNTIME_MANIFEST,
    REVIEW_PACKET_PATH,
    validate_candidate,
)
from scripts.materialize_m12n_environment_energy_activation_authority_v3 import (
    POSITIVE_AUTHORITY_PATH as V3_POSITIVE_AUTHORITY_PATH,
)


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _fresh_runtime_proof(*, commit: str, manifest_sha256: str) -> dict:
    body = {
        "schema_version": "m12n_live_runtime_health_proof_v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "health_endpoint": "https://example.invalid/health",
        "deployed_commit": commit,
        "health_commit": commit,
        "reviewed_runtime_manifest_sha256": manifest_sha256,
        "health_payload_sha256": "9" * 64,
    }
    body["runtime_health_proof_subject_sha256"] = semantic_hash(body)
    return body


def test_v3_candidate_is_exact_and_non_authorizing() -> None:
    candidate = validate_candidate()
    subject = candidate["prospective_authority_subject"]
    assert candidate["immutable"] is True
    assert candidate["accepted"] is False
    assert candidate["sealed"] is False
    assert "decision_recorded_at_utc" not in subject
    assert "health_proof_subject_sha256" not in subject["runtime_binding"]
    assert subject["runtime_binding"] == {
        "reviewed_runtime_manifest_sha256": REPAIRED_RUNTIME_MANIFEST,
        "reviewed_commit": POST_REPAIR_MAIN,
        "deployed_commit": POST_REPAIR_MAIN,
        "health_commit": POST_REPAIR_MAIN,
    }
    assert candidate["historical_failed_authority_boundary"] == {
        "artifact_id": (
            "publication-activation-authority:f000477:environment_energy:119:v1"
        ),
        "authority_subject_sha256": (
            "0adb87796e6e0d008586a03ddc075179837b3f18bc5f52f52c7e9ed9cce50e36"
        ),
        "failed_runtime_manifest_sha256": FAILED_RUNTIME_MANIFEST,
        "current_runtime_manifest_sha256": REPAIRED_RUNTIME_MANIFEST,
        "reusable_for_v3_execution": False,
    }


def test_v3_preserves_exact_presentation_and_bounded_write_envelope() -> None:
    candidate = validate_candidate()
    write_set = _load(WRITE_SET_PATH)
    presentation = load_environment_site_integration_candidate(M12M_PATH)
    presentation_row = next(
        row
        for row in write_set["artifacts"]
        if row["natural_key"]
        == "site-integration-candidate:f000477:environment_energy:119:v1"
    )
    assert presentation_row["payload"] == presentation
    assert write_set["write_caps"] == {
        "batch_inserts": 1,
        "artifact_inserts": 3,
        "relationship_inserts": 2,
        "registry_inserts": 1,
        "registry_updates": 0,
        "deletes_during_activation": 0,
        "justice_rows_touched": 0,
        "national_security_rows_touched": 0,
    }
    assert write_set["expected_counts"] == {
        "before": {
            "batches": 5,
            "artifacts": 149,
            "relationships": 161,
            "publication_registry": 2,
        },
        "after": {
            "batches": 6,
            "artifacts": 152,
            "relationships": 163,
            "publication_registry": 3,
        },
    }
    assert (
        candidate["prospective_authority_subject"]["presentation_content_sha256"]
        == write_set["publication_registry"]["publication_metadata"][
            "active_artifact_sha256"
        ]
    )


def test_v3_candidate_cannot_satisfy_live_authority_contract() -> None:
    candidate = validate_candidate()
    write_set = _load(WRITE_SET_PATH)
    with pytest.raises(ValueError, match="binding differs"):
        validate_environment_positive_activation_authority(
            candidate,
            candidate=load_environment_site_integration_candidate(M12M_PATH),
            candidate_authority=_load(AUTHORITY_PATH),
            metadata=write_set["publication_registry"]["publication_metadata"],
        )


def test_failed_authority_cannot_execute_on_v3_runtime() -> None:
    with pytest.raises(StoreSafetyError, match="runtime"):
        validate_production_execution_runtime(
            _load(POSITIVE_AUTHORITY_PATH), _load(RUNTIME_PROOF_PATH)
        )


def test_frozen_v3_authority_cannot_execute_on_changed_current_runtime() -> None:
    authority = _load(V3_POSITIVE_AUTHORITY_PATH)
    accepted_manifest = authority["subject"]["runtime_binding"][
        "reviewed_runtime_manifest_sha256"
    ]
    current_manifest = reviewed_runtime_manifest()["reviewed_runtime_manifest_sha256"]
    assert accepted_manifest == REPAIRED_RUNTIME_MANIFEST
    assert current_manifest != accepted_manifest

    proof = _fresh_runtime_proof(
        commit=authority["subject"]["runtime_binding"]["deployed_commit"],
        manifest_sha256=current_manifest,
    )
    with pytest.raises(StoreSafetyError, match="runtime"):
        validate_production_execution_runtime(authority, proof)


def test_v3_review_packet_is_non_authorizing() -> None:
    validate_candidate()
    packet = _load(REVIEW_PACKET_PATH)
    assert packet["subject"]["authorizing"] is False
    assert (
        packet["subject"]["fresh_production_preflight"]["environment_registry_absent"]
        is True
    )
    assert packet["subject"]["prospective_write_envelope"]["prospective_counts"] == {
        "batches": 6,
        "artifacts": 152,
        "relationships": 163,
        "publication_registry": 3,
    }
