"""Domain-neutral eligibility for assigning an exact legislative action to an issue.

Parent-measure subjects, titles, and other stages are context. They cannot make
an exact action eligible when that action is not materially about the domain.
"""

from __future__ import annotations

import re
from copy import deepcopy


def evaluate_primary_domain_eligibility(
    *,
    primary_domain: str,
    exact_action_material_domains: list[str],
    parent_measure_domains: list[str] | None = None,
    measure_wide_domains: list[str] | None = None,
    other_division_domains: list[str] | None = None,
    title_domains: list[str] | None = None,
    earlier_stage_domains: list[str] | None = None,
    later_stage_domains: list[str] | None = None,
    exact_action_boundary: str,
) -> dict:
    """Return a deterministic eligibility decision grounded in the exact action."""
    domain = _required_domain(primary_domain)
    exact_domains = _normalized_domains(exact_action_material_domains)
    context = {
        "parent_measure_domains": _normalized_domains(parent_measure_domains or []),
        "measure_wide_domains": _normalized_domains(measure_wide_domains or []),
        "other_division_domains": _normalized_domains(other_division_domains or []),
        "title_domains": _normalized_domains(title_domains or []),
        "earlier_stage_domains": _normalized_domains(earlier_stage_domains or []),
        "later_stage_domains": _normalized_domains(later_stage_domains or []),
    }
    boundary = exact_action_boundary.strip() if isinstance(exact_action_boundary, str) else ""
    if not boundary:
        raise ValueError("exact_action_boundary is required")

    eligible = domain in exact_domains
    return {
        "schema_version": "editorial_primary_domain_eligibility_v1",
        "primary_domain": domain,
        "eligible": eligible,
        "decision": "accepted" if eligible else "rejected",
        "reason": (
            "exact_action_materially_in_primary_domain"
            if eligible
            else f"exact_action_not_materially_{_slug(domain)}"
        ),
        "exact_action_boundary": boundary,
        "exact_action_material_domains": exact_domains,
        "context_only": deepcopy(context),
        "context_cannot_override_exact_action": True,
    }


def assert_domain_eligible(decision: dict) -> None:
    """Reject use of an action outside its exact-action material domain."""
    if not decision.get("eligible"):
        raise ValueError(decision.get("reason", "exact_action_not_domain_eligible"))


def _required_domain(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("primary_domain is required")
    return value.strip().upper()


def _normalized_domains(values: list[str]) -> list[str]:
    if not isinstance(values, list):
        raise ValueError("domain collections must be lists")
    normalized = {_required_domain(value) for value in values}
    return sorted(normalized)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
