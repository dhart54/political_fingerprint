"""Separate member-specific review routing from shared-review dependencies."""

from __future__ import annotations

from copy import deepcopy


MEMBER_REVIEW_ROUTES = {
    "standard_generation_pass",
    "sampled_audit_candidate",
    "human_exception_required",
    "blocked",
}
MEMBER_FINDING_LEVELS = {"audit", "human_exception", "blocked"}
SHARED_DEPENDENCY_KINDS = {
    "action_boundary",
    "policy_trait_value",
    "trait_relationship",
}


def normalize_shared_review_dependencies(dependencies: list[dict]) -> list[dict]:
    """Validate and deduplicate shared decisions into one stable review queue."""
    by_id: dict[str, dict] = {}
    for dependency in dependencies:
        item = deepcopy(dependency)
        identifier = item.get("dependency_id")
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError("shared review dependency requires dependency_id")
        if item.get("kind") not in SHARED_DEPENDENCY_KINDS:
            raise ValueError(f"unsupported shared review dependency kind: {item.get('kind')}")
        if item.get("status") != "human_review_pending":
            raise ValueError("shared review dependency must remain human_review_pending")
        if not isinstance(item.get("summary"), str) or not item["summary"].strip():
            raise ValueError("shared review dependency requires summary")
        references = item.get("references", {})
        expected_reference_keys = {
            "trait_ids", "relationship_ids", "dossier_ids", "episode_ids"
        }
        if set(references) != expected_reference_keys:
            raise ValueError(
                "shared review dependency requires typed references"
            )
        if any(not isinstance(references[key], list) for key in references):
            raise ValueError("shared review dependency references must be lists")
        item["dependency_id"] = identifier.strip()
        item["scope"] = "shared_corpus"
        item["review_route"] = "human_exception_required"
        if identifier in by_id and by_id[identifier] != item:
            raise ValueError(f"conflicting shared review dependency: {identifier}")
        by_id[identifier] = item
    return [by_id[key] for key in sorted(by_id)]


def route_member_review(
    *,
    member_specific_findings: list[dict],
    shared_review_dependencies: list[dict],
    deterministic_audit: bool = False,
) -> dict:
    """Route only member findings while retaining shared publication blockers."""
    dependencies = normalize_shared_review_dependencies(shared_review_dependencies)
    findings = [deepcopy(item) for item in member_specific_findings]
    for finding in findings:
        if finding.get("level") not in MEMBER_FINDING_LEVELS:
            raise ValueError(f"unsupported member finding level: {finding.get('level')}")
        if not isinstance(finding.get("finding_id"), str) or not finding["finding_id"].strip():
            raise ValueError("member-specific finding requires finding_id")

    levels = {item["level"] for item in findings}
    if "blocked" in levels:
        route = "blocked"
    elif "human_exception" in levels:
        route = "human_exception_required"
    elif "audit" in levels or deterministic_audit:
        route = "sampled_audit_candidate"
    else:
        route = "standard_generation_pass"
    return {
        "schema_version": "editorial_review_routing_v2",
        "member_review_route": route,
        "member_specific_findings": findings,
        "shared_review_dependencies": {
            "dependency_ids": [item["dependency_id"] for item in dependencies],
            "publication_blocked_until_resolved": bool(dependencies),
        },
    }
