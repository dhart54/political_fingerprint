from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.editorial_presentations.review_state_catalog import (
    CATALOG_PATH,
    PublicReviewStateCatalogError,
    public_review_state_entries,
    select_public_review_state,
    validate_public_catalog,
)
from app.editorial_presentations.selector import select_public_presentations
from backend.tests.test_api_editorial_presentations import _approved_artifact, _row
from scripts.build_public_review_state_catalog import build_catalog, catalog_bytes


ROOT = Path(__file__).resolve().parents[2]


def _justice(result: dict) -> dict:
    return next(
        item
        for item in result["presentations"]
        if item["issue_id"] == "JUSTICE_PUBLIC_SAFETY"
    )


def test_generated_catalog_is_deterministic_current_and_public_only() -> None:
    expected = catalog_bytes(build_catalog())
    assert CATALOG_PATH.read_bytes() == expected
    catalog = json.loads(expected)
    validate_public_catalog(catalog)
    assert len(catalog["entries"]) == 1
    entry = catalog["entries"][0]
    assert entry["semantic_tier"] == "reviewed_conclusion"
    assert entry["review_scope"] == "benchmark_sample"
    assert entry["review_completion_state"] == "complete"
    assert entry["public_claim_class"] == "reviewed_sample_finding"
    assert entry["public_status_label"] == "Reviewed benchmark sample"
    assert entry["total_recorded_actions"] == 7
    assert entry["complete_episode_count"] == 5
    assert entry["full_issue_synthesis_eligible"] is False
    assert "provenance" not in entry
    assert "external_authority" not in entry
    assert "historical_publication" not in entry


def test_catalog_is_closed_and_sample_cannot_acquire_full_record_label() -> None:
    catalog = {
        "schema_version": "public_review_state_catalog_v1",
        "entries": public_review_state_entries(),
    }
    changed = copy.deepcopy(catalog)
    changed["entries"][0]["extra_authority"] = True
    with pytest.raises(PublicReviewStateCatalogError):
        validate_public_catalog(changed)

    changed = copy.deepcopy(catalog)
    changed["entries"][0]["public_status_label"] = "Full review complete"
    with pytest.raises(PublicReviewStateCatalogError):
        validate_public_catalog(changed)
    assert (
        build_catalog()["entries"][0]["public_status_label"]
        == "Reviewed benchmark sample"
    )


def test_review_state_scope_selection_preserves_119_boundary() -> None:
    entry = public_review_state_entries()[0]
    identity = entry["published_artifact_identity"]
    for scope in ("119", "all"):
        selected = select_public_review_state(
            [entry],
            member_id="F000477",
            issue_id="JUSTICE_PUBLIC_SAFETY",
            requested_scope=scope,
            published_artifact_identity=identity,
        )
        assert selected is not None
        assert selected["congress_scope"] == [119]
    assert (
        select_public_review_state(
            [entry],
            member_id="F000477",
            issue_id="JUSTICE_PUBLIC_SAFETY",
            requested_scope="118",
            published_artifact_identity=identity,
        )
        is None
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("member_id", "X000001"),
        ("issue_id", "ECONOMY_TAXES"),
        ("published_artifact_identity", "different:artifact"),
    ],
)
def test_catalog_identity_mismatch_fails_closed(field: str, value: str) -> None:
    artifact = _approved_artifact()
    state = public_review_state_entries()[0]
    changed = copy.deepcopy(state)
    changed[field] = value
    if field != "published_artifact_identity":
        changed["catalog_key"] = (
            f"{changed['member_id']}:{changed['issue_id']}:119:"
            f"{changed['published_artifact_identity']}"
        )
    result = select_public_presentations(
        [_row(artifact)],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
        review_states=[changed],
    )
    assert _justice(result)["tier"] == "receipts_only"
    assert _justice(result)["review_state"] is None


def test_missing_catalog_entry_falls_back_to_basic_vote_evidence() -> None:
    result = select_public_presentations(
        [_row(_approved_artifact())],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
        review_states=[],
    )
    justice = _justice(result)
    assert justice["tier"] == "receipts_only"
    assert justice["public_status_label"] == "Vote receipts available"
    assert justice["conclusion"] is None


def test_catalog_cannot_authorize_copy_without_eligible_publication_row() -> None:
    result = select_public_presentations(
        [],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
        review_states=public_review_state_entries(),
    )
    assert _justice(result)["tier"] == "receipts_only"


def test_selector_exposes_sample_label_and_compiled_finding_direction() -> None:
    result = select_public_presentations(
        [_row(_approved_artifact())],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="all",
    )
    justice = _justice(result)
    assert justice["public_status_label"] == "Reviewed benchmark sample"
    assert justice["review_state"]["review_scope"] == "benchmark_sample"
    assert justice["review_state"]["full_issue_synthesis_eligible"] is False
    assert [item["direction"] for item in justice["repeated_patterns"]] == [
        "support",
        "opposition",
    ]
    assert justice["policy_trajectories"][0]["direction"] == "mixed"
    assert "119th-Congress" in justice["scope_boundary"]
