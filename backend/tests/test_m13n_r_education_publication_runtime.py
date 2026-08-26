from __future__ import annotations

import copy

import pytest

from app.api.positions import (
    _active_site_integration_publication,
    _merge_site_integration_evidence,
    _merge_site_integration_positions,
)
from app.editorial_artifacts.bundle import semantic_hash
from app.editorial_presentations.education_workforce_integration_candidate import (
    M13M_ARTIFACT_ID,
    M13M_SCHEMA_VERSION,
)
from app.editorial_presentations.selector import select_public_presentations
from app.editorial_presentations.site_publication import (
    ACTIVATION_AUTHORITY_SCHEMA_VERSION,
    ACTIVATION_REVIEWER_AUTHORITY,
    CANDIDATE_AUTHORITY_SCHEMA_VERSION,
    EDUCATION_ACTIVATION_AUTHORITY_ID,
    EDUCATION_AUTHORITY_ID,
    EDUCATION_FILE_SHA256,
    EDUCATION_SUBJECT_SHA256,
    POSITIVE_AUTHORIZATIONS,
    eligible_site_integration_candidate,
    select_site_integration_public,
    validate_education_candidate_preparation_authority,
    validate_preparation_authority,
)
from backend.scripts.build_m13m_education_workforce_site_integration import build


MEMBER_ID = "F000477"
ISSUE_ID = "EDUCATION_WORKFORCE"
COMMIT = "d" * 40
MANIFEST = "a" * 64


def _candidate() -> dict:
    return build(check=True)["candidate"]


def _preparation(candidate: dict) -> dict:
    subject = {
        "decision": (
            "approve_production_eligibility_and_publication_preparation_candidate"
        ),
        "member_bioguide_id": MEMBER_ID,
        "issue_id": ISSUE_ID,
        "congress": 119,
        "accepted_site_integration_binding": {
            "artifact_id": M13M_ARTIFACT_ID,
            "subject_sha256": EDUCATION_SUBJECT_SHA256,
            "file_sha256": EDUCATION_FILE_SHA256,
            "content_sha256": semantic_hash(candidate),
        },
        "authorizations": {
            "record_production_eligibility": True,
            "build_publication_activation_candidate": True,
            "production_database_write": False,
            "publication_registry_mutation": False,
            "publication_activation": False,
            "production_persistence": False,
            "deployment": False,
            "live_activation": False,
        },
    }
    return {
        "schema_version": CANDIDATE_AUTHORITY_SCHEMA_VERSION,
        "artifact_id": EDUCATION_AUTHORITY_ID,
        "immutable": True,
        "accepted": True,
        "subject": subject,
        "authority_subject_sha256": semantic_hash(subject),
    }


def _future_row(*, synthetic: bool = True) -> tuple[dict, dict, dict]:
    candidate = _candidate()
    preparation = _preparation(candidate)
    preparation_binding = {
        "artifact_id": EDUCATION_AUTHORITY_ID,
        "authority_subject_sha256": preparation["authority_subject_sha256"],
        "authority_file_sha256": "b" * 64,
    }
    write_set_binding = {
        "artifact_id": (
            "publication-activation-write-set:f000477:education_workforce:119:v1"
        ),
        "write_set_subject_sha256": "c" * 64,
        "write_set_file_sha256": "e" * 64,
    }
    preflight_binding = {
        "preflight_subject_sha256": "f" * 64,
        "state_fingerprint_sha256": "1" * 64,
    }
    rollback_binding = {
        "delete_registry_primary_key": {
            "member_bioguide_id": MEMBER_ID,
            "issue_id": ISSUE_ID,
        },
        "restore_state_fingerprint_sha256": "1" * 64,
    }
    runtime = {
        "reviewed_runtime_manifest_sha256": MANIFEST,
        "reviewed_commit": COMMIT,
        "deployed_commit": COMMIT,
        "health_commit": COMMIT,
    }
    metadata = {
        "production_eligibility_publication_authority": preparation,
        "accepted_site_integration_subject_sha256": EDUCATION_SUBJECT_SHA256,
        "accepted_site_integration_file_sha256": EDUCATION_FILE_SHA256,
        "presentation_natural_key": M13M_ARTIFACT_ID,
        "presentation_artifact_version": 1,
        "active_artifact_sha256": semantic_hash(candidate),
        "candidate_preparation_authority_binding": preparation_binding,
        "activation_write_set_binding": write_set_binding,
        "preflight_binding": preflight_binding,
        "rollback_binding": rollback_binding,
        "reviewed_runtime_binding": runtime,
        "production_target_identity_sha256": "2" * 64,
        "authority_subject_sha256": preparation["authority_subject_sha256"],
    }
    activation_subject = {
        "decision": "approve_exact_publication_activation",
        "decision_recorded_at_utc": "2026-08-25T02:00:00Z",
        "reviewer": "synthetic-disposable-reviewer",
        "reviewer_authority": ACTIVATION_REVIEWER_AUTHORITY,
        "product_owner": "dhart54",
        "member_bioguide_id": MEMBER_ID,
        "issue_id": ISSUE_ID,
        "congress": 119,
        "accepted_site_integration_binding": preparation["subject"][
            "accepted_site_integration_binding"
        ],
        "candidate_preparation_authority_binding": preparation_binding,
        "activation_write_set_binding": write_set_binding,
        "publication_registry_target": {
            "member_bioguide_id": MEMBER_ID,
            "issue_id": ISSUE_ID,
            "presentation_natural_key": M13M_ARTIFACT_ID,
            "presentation_artifact_version": 1,
        },
        "presentation_content_sha256": semantic_hash(candidate),
        "preflight_binding": preflight_binding,
        "rollback_binding": rollback_binding,
        "runtime_binding": runtime,
        "ratification_runtime_evidence_binding": {
            "runtime_health_proof_subject_sha256": "3" * 64,
            "captured_at_utc": "2026-08-25T01:59:00Z",
            "reviewed_runtime_manifest_sha256": MANIFEST,
            "deployed_commit": COMMIT,
            "health_commit": COMMIT,
        },
        "production_target_identity_sha256": "2" * 64,
        "authorizations": copy.deepcopy(POSITIVE_AUTHORIZATIONS),
    }
    activation = {
        "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        "artifact_id": EDUCATION_ACTIVATION_AUTHORITY_ID,
        "immutable": True,
        "sealed": True,
        "accepted": True,
        "subject": activation_subject,
        "activation_authority_subject_sha256": semantic_hash(activation_subject),
    }
    if synthetic:
        activation["test_only_synthetic"] = True
    metadata["publication_activation_authority"] = activation
    metadata["activation_authority_subject_sha256"] = activation[
        "activation_authority_subject_sha256"
    ]
    row = {
        "member_bioguide_id": MEMBER_ID,
        "issue_id": ISSUE_ID,
        "publicly_active": True,
        "deactivated_at": None,
        "editorial_status": "human_approved",
        "benchmark_status": "gold_benchmark",
        "production_eligible": True,
        "schema_version": M13M_SCHEMA_VERSION,
        "artifact_version": 1,
        "natural_key": M13M_ARTIFACT_ID,
        "content_sha256": semantic_hash(candidate),
        "payload_jsonb": candidate,
        "publication_metadata_jsonb": metadata,
    }
    return row, preparation, activation


def _education(response: dict) -> dict:
    return next(
        item for item in response["presentations"] if item["issue_id"] == ISSUE_ID
    )


def test_education_is_inactive_without_a_publication_registry_row() -> None:
    for scope in ("119", "all", "118"):
        response = select_public_presentations(
            [],
            legislator_id="leg_valerie_p_foushee",
            member_bioguide_id=MEMBER_ID,
            scope=scope,
        )
        assert _education(response)["tier"] == "receipts_only"
    existing_domain_rows = [
        {"issue_id": "JUSTICE_PUBLIC_SAFETY"},
        {"issue_id": "NATIONAL_SECURITY_FOREIGN"},
        {"issue_id": "ENVIRONMENT_ENERGY"},
    ]
    assert (
        _active_site_integration_publication(
            member_bioguide_id=MEMBER_ID,
            issue_id=ISSUE_ID,
            publication_rows=existing_domain_rows,
        )
        is None
    )


def test_exact_future_education_row_is_selectable_without_wording_changes() -> None:
    row, _, _ = _future_row()
    assert (
        eligible_site_integration_candidate(
            row,
            member_bioguide_id=MEMBER_ID,
            allow_test_authority=True,
        )
        == _candidate()
    )
    for scope in ("119", "all", "118"):
        response = select_public_presentations(
            [row],
            legislator_id="leg_valerie_p_foushee",
            member_bioguide_id=MEMBER_ID,
            scope=scope,
            allow_test_activation_authority=True,
        )
        presentation = _education(response)
        assert presentation["tier"] == (
            "reviewed_conclusion" if scope in {"119", "all"} else "receipts_only"
        )
        if scope in {"119", "all"}:
            accepted = _candidate()["subject"]["presentation"]
            assert presentation["overview"] == accepted["overview"]
            assert presentation["repeated_patterns"] == accepted["repeated_patterns"]
            assert presentation["notable_choices"] == accepted["notable_choices"]
            assert (
                presentation["syntheses"] == presentation["policy_trajectories"] == []
            )
            assert presentation["overview"]["show_direction"] is False
            assert presentation["repeated_patterns"][0]["show_direction"] is False
            notable = presentation["notable_choices"][0]
            assert (notable["direction_label"], notable["direction_symbol"]) == (
                "Mixed",
                "±",
            )
            if scope == "all":
                assert "119th-Congress record" in presentation["scope_boundary"]


def test_exact_future_row_enables_governed_positions_and_evidence_only() -> None:
    row, _, _ = _future_row(synthetic=False)
    candidate = _active_site_integration_publication(
        member_bioguide_id=MEMBER_ID,
        issue_id=ISSUE_ID,
        publication_rows=[row],
    )
    assert candidate == _candidate()
    base = {"positions": [{"domain": "JUSTICE_PUBLIC_SAFETY", "marker": "unchanged"}]}
    evidence = candidate["subject"]["preview_data"]["evidence_119"]
    positions = _merge_site_integration_positions(
        base, candidate, governed_evidence=evidence
    )
    education = next(
        item for item in positions["positions"] if item["domain"] == ISSUE_ID
    )
    assert (
        education["interpreted_support_count"],
        education["interpreted_oppose_count"],
        education["interpreted_other_count"],
    ) == (6, 10, 1)
    merged = _merge_site_integration_evidence(
        {"domain": ISSUE_ID, "evidence": []},
        candidate,
        domain=ISSUE_ID,
        scope="119",
    )
    assert len(merged["evidence"]) == 17
    assert len({item["canonical_action_id"] for item in merged["evidence"]}) == 17


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("member_bioguide_id",), "X000001"),
        (("issue_id",), "NATIONAL_SECURITY_FOREIGN"),
        (("publicly_active",), False),
        (("production_eligible",), False),
        (("natural_key",), "unknown"),
        (("content_sha256",), "0" * 64),
        (("publication_metadata_jsonb", "presentation_natural_key"), "unknown"),
        (("publication_metadata_jsonb", "active_artifact_sha256"), "0" * 64),
        (("publication_metadata_jsonb", "authority_subject_sha256"), "0" * 64),
        (
            ("publication_metadata_jsonb", "activation_authority_subject_sha256"),
            "0" * 64,
        ),
    ],
)
def test_education_row_mismatches_fail_closed(path: tuple[str, ...], value) -> None:
    row, _, _ = _future_row()
    target = row
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert (
        eligible_site_integration_candidate(
            row,
            member_bioguide_id=MEMBER_ID,
            allow_test_authority=True,
        )
        is None
    )


def test_missing_or_unsealed_authorities_and_runtime_drift_fail_closed() -> None:
    row, _, _ = _future_row()
    for mutation in (
        lambda value: value["publication_metadata_jsonb"].pop(
            "production_eligibility_publication_authority"
        ),
        lambda value: value["publication_metadata_jsonb"].pop(
            "publication_activation_authority"
        ),
        lambda value: value["publication_metadata_jsonb"][
            "production_eligibility_publication_authority"
        ].__setitem__("accepted", False),
        lambda value: value["publication_metadata_jsonb"][
            "publication_activation_authority"
        ].__setitem__("sealed", False),
        lambda value: value["publication_metadata_jsonb"][
            "publication_activation_authority"
        ]["subject"].__setitem__("issue_id", "ENVIRONMENT_ENERGY"),
        lambda value: value["publication_metadata_jsonb"][
            "publication_activation_authority"
        ]["subject"]["runtime_binding"].__setitem__("health_commit", "e" * 40),
    ):
        changed = copy.deepcopy(row)
        mutation(changed)
        assert (
            eligible_site_integration_candidate(
                changed,
                member_bioguide_id=MEMBER_ID,
                allow_test_authority=True,
            )
            is None
        )


def test_preparation_authority_is_exact_nonactivating_and_not_synthetic() -> None:
    candidate = _candidate()
    authority = _preparation(candidate)
    validate_education_candidate_preparation_authority(authority, candidate=candidate)
    for mutation in (
        lambda value: value.__setitem__("accepted", False),
        lambda value: value.__setitem__("test_only_synthetic", True),
        lambda value: value["subject"]["authorizations"].__setitem__(
            "publication_activation", True
        ),
    ):
        changed = copy.deepcopy(authority)
        mutation(changed)
        changed["authority_subject_sha256"] = semantic_hash(changed["subject"])
        with pytest.raises(ValueError, match="Education candidate-preparation"):
            validate_education_candidate_preparation_authority(
                changed, candidate=candidate
            )


def test_unknown_identity_never_falls_through_to_national_security() -> None:
    unknown = {"artifact_id": "site-integration-candidate:unknown"}
    assert (
        eligible_site_integration_candidate(
            {"payload_jsonb": unknown}, member_bioguide_id=MEMBER_ID
        )
        is None
    )
    with pytest.raises(ValueError, match="unknown site-integration candidate"):
        validate_preparation_authority({}, candidate=unknown)
    with pytest.raises(ValueError, match="unknown site-integration candidate"):
        select_site_integration_public(
            unknown,
            legislator_id="leg_valerie_p_foushee",
            member_bioguide_id=MEMBER_ID,
            scope="119",
        )
