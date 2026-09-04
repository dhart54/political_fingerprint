from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.editorial_presentations.compiler import canonical_digest
from app.editorial_presentations.publication_replacement_governance_v2 import (
    EXACT_CAPS,
    PublicationReplacementGovernanceError,
    REPLACEMENT_PREFLIGHT_SCHEMA_V2,
    RUNTIME_EVIDENCE_SCHEMA_V2,
    validate_execution,
    validate_positive_authority,
    validate_write_set,
)
from app.editorial_presentations.publication_replacement_runtime_v2r import (
    eligible_m14g_replacement,
    select_public_presentations_v2r,
)
from scripts.foushee_education_workforce_m14h_replacement import (
    BASE_SHA,
    CANDIDATE_PATH,
    EXPECTED_ACCEPTED_SUBJECT,
    EXPECTED_CANDIDATE_FILE,
    EXPECTED_CANDIDATE_SUBJECT,
    EXPECTED_SITE_AUTHORITY_SUBJECT,
    OUTPUT,
    PRESENTATION_KEY,
    _file_sha,
    load_candidate,
    publication_metadata_for_activation,
)

ROOT = Path(__file__).resolve().parents[2]
V2_PATH = ROOT / "backend/app/editorial_presentations/publication_activation_governance_v2.py"
MIGRATION_PATH = ROOT / "backend/migrations/0016_editorial_artifact_persistence.sql"


def _load(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def _canonical_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _sealed_authority() -> dict:
    template = _load("positive_replacement_activation_candidate.json")
    subject = copy.deepcopy(template["subject"])
    subject["decision_recorded_at_utc"] = "2026-09-03T12:00:00Z"
    subject["reviewer"] = "synthetic-disposable-reviewer"
    return {
        "schema_version": template["schema_version"],
        "artifact_id": template["artifact_id"],
        "immutable": True,
        "sealed": True,
        "accepted": True,
        "test_only_synthetic": True,
        "subject": subject,
        "activation_authority_subject_sha256": canonical_digest(subject),
    }


def test_exact_m14g_inputs_and_payload_are_unchanged() -> None:
    candidate = load_candidate()
    write_set = _load("publication_replacement_write_set.json")
    presentation = next(
        item for item in write_set["subject"]["artifacts"]
        if item["natural_key"] == PRESENTATION_KEY
    )
    assert _file_sha(CANDIDATE_PATH) == EXPECTED_CANDIDATE_FILE
    assert candidate["candidate_subject_sha256"] == EXPECTED_CANDIDATE_SUBJECT
    assert presentation["payload"] == candidate
    assert presentation["supersedes_artifact_id"] == 242
    assert write_set["subject"]["accepted_site_integration_binding"][
        "subject_sha256"
    ] == EXPECTED_ACCEPTED_SUBJECT
    metadata = write_set["subject"]["publication_registry_update"][
        "publication_metadata_jsonb"
    ]
    assert metadata["m14g_human_site_integration_authority_subject_sha256"] == (
        EXPECTED_SITE_AUTHORITY_SUBJECT
    )


def test_v2_and_migration_remain_byte_identical_to_exact_baseline() -> None:
    assert _canonical_file(V2_PATH) == (
        "e5a5ae28ebd0ce240a708200e9ccf12a01eb425df3aa736c023fc5f0e665637b"
    )
    assert _canonical_file(MIGRATION_PATH) == (
        "bfb654b7fbcb1adc4052e31ca019d9808d8c1c35819c4a687a10cd40974ca163"
    )


def test_exact_replacement_caps_and_prior_row_are_bound() -> None:
    write_set = _load("publication_replacement_write_set.json")
    validate_write_set(write_set)
    subject = write_set["subject"]
    assert subject["mutation_caps"] == EXACT_CAPS
    assert subject["mutation_caps"]["insert_registry_rows"] == 0
    assert subject["mutation_caps"]["update_registry_rows"] == 1
    assert subject["mutation_caps"]["other_updates"] == 0
    assert subject["mutation_caps"]["deletes_during_activation"] == 0
    assert subject["publication_registry_update"]["primary_key"] == {
        "member_bioguide_id": "F000477",
        "issue_id": "EDUCATION_WORKFORCE",
    }
    assert subject["publication_registry_update"]["prior_row"] == subject[
        "stable_production_baseline"
    ]["prior_registry_row"]
    source_manifest = next(
        item["payload"] for item in subject["artifacts"]
        if item["artifact_type"] == "source_manifest"
    )
    paths = {item["path"] for item in source_manifest["source_files"]}
    assert source_manifest["complete_required_sources"] is True
    assert len(paths) == 10
    assert not any("screenshot" in path for path in paths)
    runtime = _load("public_runtime_manifest.json")
    runtime_paths = {item["path"] for item in runtime["subject"]["files"]}
    assert "frontend/lib/publicReceipt.mjs" in runtime_paths
    assert runtime["production_observation"]["deployment_required_before_activation"] is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("insert_registry_rows", 1),
        ("update_registry_rows", 2),
        ("other_updates", 1),
        ("deletes_during_activation", 1),
    ],
)
def test_write_envelope_expansion_fails_closed(field: str, value: int) -> None:
    write_set = _load("publication_replacement_write_set.json")
    write_set["subject"]["mutation_caps"][field] = value
    with pytest.raises(PublicationReplacementGovernanceError, match="mutation caps"):
        validate_write_set(write_set)


def test_partial_target_existence_and_prior_drift_fail_closed() -> None:
    write_set = _load("publication_replacement_write_set.json")
    partial = copy.deepcopy(write_set)
    partial["subject"]["stable_production_baseline"][
        "target_new_natural_keys_found"
    ] = [{"natural_key": PRESENTATION_KEY}]
    with pytest.raises(PublicationReplacementGovernanceError, match="partial existence"):
        validate_write_set(partial)
    drifted = copy.deepcopy(write_set)
    drifted["subject"]["publication_registry_update"]["prior_row"][
        "artifact_id"
    ] = 999
    with pytest.raises(PublicationReplacementGovernanceError, match="prior-row"):
        validate_write_set(drifted)


def test_unsealed_candidate_cannot_execute_and_candidate_drift_fails() -> None:
    write_set = _load("publication_replacement_write_set.json")
    template = _load("positive_replacement_activation_candidate.json")
    with pytest.raises(PublicationReplacementGovernanceError, match="sealed accepted"):
        validate_positive_authority(template, write_set=write_set, candidate=load_candidate())
    authority = _sealed_authority()
    drifted = copy.deepcopy(load_candidate())
    drifted["artifact_id"] = "drifted"
    with pytest.raises(PublicationReplacementGovernanceError, match="candidate drifted"):
        validate_positive_authority(authority, write_set=write_set, candidate=drifted)


def test_stale_preflight_and_runtime_drift_fail_closed() -> None:
    write_set = _load("publication_replacement_write_set.json")
    authority = _sealed_authority()
    baseline = write_set["subject"]["stable_production_baseline"]
    preflight = {
        "schema_version": REPLACEMENT_PREFLIGHT_SCHEMA_V2,
        "captured_at_utc": "2026-09-03T11:59:00Z",
        "transaction_read_only": True,
        **copy.deepcopy(baseline),
    }
    preflight["preflight_subject_sha256"] = canonical_digest(preflight)
    runtime = {
        "schema_version": RUNTIME_EVIDENCE_SCHEMA_V2,
        "captured_at_utc": "2026-09-03T11:59:00Z",
        "healthy": True,
        "deployed_commit": BASE_SHA,
        "health_commit": BASE_SHA,
        "current_runtime_manifest_sha256": write_set["subject"][
            "public_runtime_manifest_binding"
        ]["subject_sha256"],
        "deployment_required_before_activation": False,
    }
    runtime["runtime_health_proof_subject_sha256"] = canonical_digest(runtime)
    result = validate_execution(
        authority=authority,
        write_set=write_set,
        candidate=load_candidate(),
        runtime_evidence=runtime,
        production_preflight=preflight,
        now=datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc),
    )
    assert result["status"] == "VALID_FOR_EXECUTION"
    stale = copy.deepcopy(preflight)
    stale["captured_at_utc"] = "2026-09-03T10:00:00Z"
    stale["preflight_subject_sha256"] = canonical_digest(
        {key: value for key, value in stale.items() if key != "preflight_subject_sha256"}
    )
    with pytest.raises(PublicationReplacementGovernanceError, match="stale"):
        validate_execution(
            authority=authority, write_set=write_set, candidate=load_candidate(),
            runtime_evidence=runtime, production_preflight=stale,
            now=datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc),
        )
    drifted_runtime = copy.deepcopy(runtime)
    drifted_runtime["current_runtime_manifest_sha256"] = "0" * 64
    drifted_runtime["runtime_health_proof_subject_sha256"] = canonical_digest(
        {key: value for key, value in drifted_runtime.items() if key != "runtime_health_proof_subject_sha256"}
    )
    with pytest.raises(PublicationReplacementGovernanceError, match="runtime drift"):
        validate_execution(
            authority=authority, write_set=write_set, candidate=load_candidate(),
            runtime_evidence=drifted_runtime, production_preflight=preflight,
            now=datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc),
        )


def test_public_selector_accepts_m14g_only_with_sealed_v2r_authority() -> None:
    write_set = _load("publication_replacement_write_set.json")
    authority = _sealed_authority()
    presentation = next(
        item for item in write_set["subject"]["artifacts"]
        if item["natural_key"] == PRESENTATION_KEY
    )
    row = {
        **presentation,
        "payload_jsonb": presentation["payload"],
        "publication_metadata_jsonb": publication_metadata_for_activation(
            write_set, authority
        ),
        "publicly_active": True,
        "deactivated_at": None,
    }
    assert eligible_m14g_replacement(
        row, member_bioguide_id="F000477", allow_test_authority=True
    ) == load_candidate()
    for scope, expected in (("119", "reviewed_conclusion"), ("all", "reviewed_conclusion"), ("118", "receipts_only")):
        selected = select_public_presentations_v2r(
            [row],
            legislator_id="leg_valerie_p_foushee",
            member_bioguide_id="F000477",
            scope=scope,
            allow_test_activation_authority=True,
        )
        education = next(
            item for item in selected["presentations"]
            if item["issue_id"] == "EDUCATION_WORKFORCE"
        )
        assert education["tier"] == expected
        if scope == "all":
            assert "119th-Congress" in education["scope_boundary"]
    row["publication_metadata_jsonb"].pop("publication_replacement_activation_authority")
    assert eligible_m14g_replacement(
        row, member_bioguide_id="F000477", allow_test_authority=True
    ) is None


def test_preparation_package_contains_no_production_authority() -> None:
    authority = _load("publication_replacement_preparation_authority.json")
    template = _load("positive_replacement_activation_candidate.json")
    assert authority["subject"]["authorizations"]["production_database_write"] is False
    assert authority["subject"]["authorizations"]["publication_registry_mutation"] is False
    assert template["sealed"] is False and template["accepted"] is False
    assert template["subject"]["decision_recorded_at_utc"] is None
    assert template["subject"]["reviewer"] is None
