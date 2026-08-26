from __future__ import annotations

import copy
import json
from pathlib import Path

from app.editorial_artifacts.bundle import semantic_hash
from app.editorial_presentations.site_publication import (
    ACTIVATION_AUTHORITY_SCHEMA_VERSION,
    EDUCATION_ACTIVATION_AUTHORITY_ID,
    POSITIVE_AUTHORIZATIONS,
    validate_education_positive_activation_authority,
)
from scripts.build_m13n_education_workforce_ratification_candidate import (
    ACTIVATION_TEMPLATE_PATH,
    AUTHORITY_PATH,
    CANDIDATE_PATH,
    EXPECTED_AFTER,
    EXPECTED_BEFORE,
    PARITY_PATH,
    PREFLIGHT_PATH,
    PREPARATION_DECISION_RECORDED_AT_UTC,
    PREPARATION_REVIEWER,
    REVIEW_PACKET_PATH,
    ROLLBACK_PATH,
    RUNTIME_MANIFEST_PATH,
    RUNTIME_PROOF_PATH,
    WRITE_SET_PATH,
    validate_outputs,
)
from scripts.foushee_education_workforce_publication_preparation import (
    ROOT,
    RUNTIME_SOURCE_PATHS,
    reviewed_runtime_manifest,
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_m13n_package_is_exact_deterministic_and_non_authorizing() -> None:
    result = validate_outputs()
    preflight = _load(PREFLIGHT_PATH)
    authority = _load(AUTHORITY_PATH)
    write_set = _load(WRITE_SET_PATH)
    rollback = _load(ROLLBACK_PATH)
    template = _load(ACTIVATION_TEMPLATE_PATH)
    candidate = _load(CANDIDATE_PATH)
    packet = _load(REVIEW_PACKET_PATH)
    parity = _load(PARITY_PATH)

    assert preflight["transaction_read_only"] is True
    assert preflight["counts"] == EXPECTED_BEFORE
    assert preflight["education_registry_rows"] == []
    assert preflight["m13n_target_rows"] == []
    assert authority["subject"]["reviewer"] == PREPARATION_REVIEWER
    assert (
        authority["subject"]["decision_recorded_at_utc"]
        == PREPARATION_DECISION_RECORDED_AT_UTC
    )
    assert (
        authority["subject"]["authorizations"]["record_production_eligibility"] is True
    )
    assert (
        authority["subject"]["authorizations"]["build_publication_activation_candidate"]
        is True
    )
    for key in (
        "production_database_write",
        "publication_registry_mutation",
        "publication_activation",
        "production_persistence",
        "deployment",
        "live_activation",
    ):
        assert authority["subject"]["authorizations"][key] is False
    assert write_set["expected_counts"] == {
        "before": EXPECTED_BEFORE,
        "after": EXPECTED_AFTER,
    }
    assert write_set["activation_authorized"] is False
    assert write_set["production_write_authorized"] is False
    assert rollback["subject"]["ownership"] == write_set["rollback"]
    assert template["sealed"] is False and template["accepted"] is False
    completion = template["subject"][
        "completion_required_after_exact_runtime_deployment"
    ]
    assert all(
        value is None for key, value in completion.items() if key != "authorizations"
    )
    assert all(value is None for value in completion["authorizations"].values())
    assert candidate["sealed"] is False and candidate["accepted"] is False
    assert "decision_recorded_at_utc" not in candidate["prospective_authority_subject"]
    assert candidate["prospective_authority_subject"]["authorizations"] == (
        POSITIVE_AUTHORIZATIONS
    )
    assert packet["subject"]["authorizing"] is False
    assert parity["subject"]["positive_activation_authority_absent"] is True
    assert parity["subject"]["production_write_performed"] is False
    assert (
        result["candidate_subject_sha256"]
        == candidate["prospective_authority_subject_sha256"]
    )


def test_six_file_runtime_manifest_remains_byte_exact() -> None:
    manifest = _load(RUNTIME_MANIFEST_PATH)
    assert manifest == reviewed_runtime_manifest()
    assert all(path.is_file() for path in RUNTIME_SOURCE_PATHS)
    assert {item["path"] for item in manifest["files"]} == {
        path.relative_to(ROOT).as_posix() for path in RUNTIME_SOURCE_PATHS
    }
    assert (
        _load(RUNTIME_PROOF_PATH)["reviewed_runtime_manifest_sha256"]
        == manifest["reviewed_runtime_manifest_sha256"]
    )


def test_prospective_subject_mechanically_completes_to_exact_test_authority() -> None:
    ratification_candidate = _load(CANDIDATE_PATH)
    preparation_authority = _load(AUTHORITY_PATH)
    write_set = _load(WRITE_SET_PATH)
    presentation = next(
        item["payload"]
        for item in write_set["artifacts"]
        if item["natural_key"]
        == "site-integration-candidate:f000477:education_workforce:119:v1"
    )
    subject = copy.deepcopy(ratification_candidate["prospective_authority_subject"])
    subject.pop("candidate_prepared_at_utc")
    subject["decision_recorded_at_utc"] = "2026-08-26T00:55:00Z"
    completed = {
        "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        "artifact_id": EDUCATION_ACTIVATION_AUTHORITY_ID,
        "immutable": True,
        "sealed": True,
        "accepted": True,
        "test_only_synthetic": True,
        "subject": subject,
        "activation_authority_subject_sha256": semantic_hash(subject),
    }
    validate_education_positive_activation_authority(
        completed,
        candidate=presentation,
        candidate_authority=preparation_authority,
        metadata=write_set["publication_registry"]["publication_metadata"],
        allow_test_authority=True,
    )
