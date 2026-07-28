from __future__ import annotations

import copy

import pytest

from app.editorial_artifacts.publication_activation import (
    ACTIVE_ARTIFACT_SHA256,
    BUNDLE_ID,
    PRESENTATION_KEY,
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
