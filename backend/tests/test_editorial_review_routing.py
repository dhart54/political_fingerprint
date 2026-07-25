import pytest

from backend.app.summaries.editorial_review_routing import (
    MEMBER_REVIEW_ROUTES,
    normalize_shared_review_dependencies,
    route_member_review,
)


DEPENDENCY = {
    "dependency_id": "trait-value:combined-divisions",
    "kind": "policy_trait_value",
    "status": "human_review_pending",
    "summary": "Review the shared trait value once.",
    "references": {
        "trait_ids": ["combined_divisions"],
        "relationship_ids": [],
        "dossier_ids": [],
        "episode_ids": [],
    },
}


def test_shared_dependency_does_not_change_member_route() -> None:
    result = route_member_review(
        member_specific_findings=[],
        shared_review_dependencies=[DEPENDENCY, DEPENDENCY],
    )
    assert result["member_review_route"] == "standard_generation_pass"
    assert result["shared_review_dependencies"] == {
        "dependency_ids": ["trait-value:combined-divisions"],
        "publication_blocked_until_resolved": True,
    }


def test_exact_four_member_routes_are_supported() -> None:
    observed = {
        route_member_review(member_specific_findings=[], shared_review_dependencies=[])["member_review_route"],
        route_member_review(
            member_specific_findings=[], shared_review_dependencies=[], deterministic_audit=True
        )["member_review_route"],
        route_member_review(
            member_specific_findings=[{"finding_id": "coverage", "level": "human_exception"}],
            shared_review_dependencies=[],
        )["member_review_route"],
        route_member_review(
            member_specific_findings=[{"finding_id": "invalid", "level": "blocked"}],
            shared_review_dependencies=[],
        )["member_review_route"],
    }
    assert observed == MEMBER_REVIEW_ROUTES


def test_conflicting_duplicate_shared_dependency_is_rejected() -> None:
    with pytest.raises(ValueError, match="conflicting shared review dependency"):
        normalize_shared_review_dependencies([
            DEPENDENCY,
            {**DEPENDENCY, "summary": "Different meaning."},
        ])
