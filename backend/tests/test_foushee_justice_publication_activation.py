from __future__ import annotations

import copy
from pathlib import Path

import pytest

from app.editorial_artifacts.publication_activation import (
    ACTIVE_ARTIFACT_SHA256,
    BUNDLE_ID,
    PRESENTATION_KEY,
    SOURCE_COMMIT,
    build_activation_bundle,
    load_activation_bundle,
    validate_activation_bundle,
)
from scripts.editorial_artifact_store import StoreSafetyError
from scripts.foushee_justice_publication_activation import (
    _exact_deployed_commit,
    main,
)


def test_checked_activation_bundle_is_deterministic_and_exact() -> None:
    bundle = load_activation_bundle()
    assert bundle == build_activation_bundle()
    assert bundle["bundle_id"] == BUNDLE_ID
    assert bundle["expected_counts"]["before"] == {
        "batches": 1,
        "artifacts": 71,
        "relationships": 95,
        "publication_registry": 0,
    }
    assert bundle["expected_counts"]["after"] == {
        "batches": 2,
        "artifacts": 74,
        "relationships": 97,
        "publication_registry": 1,
    }


def test_active_presentation_is_exact_approved_candidate() -> None:
    bundle = load_activation_bundle()
    presentation = next(
        item
        for item in bundle["artifacts"]
        if item["natural_key"] == PRESENTATION_KEY
    )
    assert presentation["content_sha256"] == ACTIVE_ARTIFACT_SHA256
    assert presentation["payload"]["controls"]["editorial"][
        "human_approval_status"
    ] == "human_approved"
    assert presentation["payload"]["controls"]["benchmark"][
        "status"
    ] == "gold_benchmark"
    assert presentation["payload"]["controls"]["production"]["eligible"] is True
    assert presentation["payload"]["controls"]["publication"]["active"] is True


@pytest.mark.parametrize(
    "mutate",
    [
        lambda bundle: bundle["expected_counts"]["after"].update(
            {"publication_registry": 2}
        ),
        lambda bundle: bundle["artifacts"][0].update(
            {"content_sha256": "0" * 64}
        ),
        lambda bundle: bundle["relationships"].pop(),
        lambda bundle: bundle["publication_registry"]["publication_metadata"][
            "approval_receipt"
        ].update({"receipt_id": "approval-receipt:substituted"}),
    ],
)
def test_activation_bundle_fails_closed_on_mutation(mutate) -> None:
    bundle = copy.deepcopy(build_activation_bundle())
    mutate(bundle)
    with pytest.raises(ValueError):
        validate_activation_bundle(bundle)


def test_tool_rejects_wrong_bundle_digest_and_schema_expectation() -> None:
    with pytest.raises(StoreSafetyError, match="bundle digest"):
        main(["verify-bundle", "--bundle-sha256", "0" * 64])
    with pytest.raises(StoreSafetyError, match="migration 0016"):
        main(["verify-bundle", "--required-schema", "0017"])


def test_tool_rejects_unproven_deployed_commit() -> None:
    with pytest.raises(StoreSafetyError, match="not proven"):
        _exact_deployed_commit("0" * 40)


def test_exact_compatible_deployed_commit_is_accepted() -> None:
    assert _exact_deployed_commit(SOURCE_COMMIT) == {
        "required_ancestor": SOURCE_COMMIT,
        "supplied_identity": SOURCE_COMMIT,
        "compatible": True,
        "verification_method": "git_merge_base_is_ancestor",
    }


@pytest.mark.parametrize(
    "identity",
    [
        "",
        "unknown",
        "f" * 39,
        "88d6f3446f54b07735e084cbc958c1614b190fab",
    ],
)
def test_missing_malformed_placeholder_or_incompatible_deployment_fails(
    identity: str,
) -> None:
    if not identity:
        with pytest.raises(StoreSafetyError, match="deployed backend commit"):
            main(["preflight", "--bundle-id", BUNDLE_ID])
    else:
        with pytest.raises(StoreSafetyError):
            _exact_deployed_commit(identity)


def test_wrong_bundle_id_fails_before_database_access() -> None:
    with pytest.raises(StoreSafetyError, match="bundle ID"):
        main(
            [
                "preflight",
                "--bundle-id",
                "substituted-bundle",
                "--deployed-commit",
                SOURCE_COMMIT,
            ]
        )


def test_wrong_confirmed_bundle_digest_fails_before_mutation() -> None:
    with pytest.raises(StoreSafetyError, match="confirm-bundle-digest"):
        main(
            [
                "apply",
                "--bundle-id",
                BUNDLE_ID,
                "--confirm-bundle-digest",
                "0" * 64,
                "--deployed-commit",
                SOURCE_COMMIT,
                "--database-url",
                "postgresql://unused@127.0.0.1:1/unused",
            ]
        )


def test_runbook_distinguishes_semantic_availability_and_cosmetic_failures() -> None:
    runbook = (
        Path(__file__).resolve().parents[2]
        / "docs/workflows/foushee-justice-publication-activation.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(runbook.split())
    assert "Rollback immediately after any semantic or identity failure" in normalized
    assert "two confirmed attempts within 60 seconds" in normalized
    assert (
        "One transient availability failure alone does not meet the rollback threshold"
        in normalized
    )
    assert "cosmetic-only defect" in normalized
    assert "all seven row inserts" in normalized
    assert "all five inserts" not in normalized


def test_db_modes_require_explicit_bundle_id_at_argument_boundary() -> None:
    with pytest.raises(SystemExit):
        main(["preflight", "--deployed-commit", "0" * 40])


def test_preflight_rejects_unproven_deployment_before_database_access() -> None:
    with pytest.raises(StoreSafetyError, match="not proven"):
        main(
            [
                "preflight",
                "--bundle-id",
                BUNDLE_ID,
                "--deployed-commit",
                "0" * 40,
                "--database-url",
                "postgresql://unused:unused@127.0.0.1:1/unused",
            ]
        )
