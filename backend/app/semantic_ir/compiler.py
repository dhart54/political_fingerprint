"""Deterministic, file-agnostic Editorial Semantic IR V1 compiler.

The compiler accepts reviewed shared semantics and exact member action states.
It does not read reference artifacts, dossiers, expected graphs, or rendered
prose. Shared legislative meaning remains an authoritative input; this module
only applies the accepted structural rules to that meaning.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections import defaultdict
from typing import Any, Iterable


DIRECTIONAL_STATUS = {"Yea": "support", "Nay": "opposition"}
NON_DIRECTIONAL_REASONS = {
    "Present": "non_directional_status",
    "Not Voting": "non_directional_status",
    "Missing Evidence": "missing_evidence",
}
OUTPUT_FIELDS = {
    "action_accounting",
    "composition",
    "coverage",
    "external_review_decisions",
    "proposition_graph",
    "review_route",
}
VERIFIED_OUTSIDE_SERVICE = {"not_yet_serving", "no_longer_serving"}
SOURCE_SEMANTIC_EFFECTS = {
    "blocks_behavioral_propositions",
    "limits_argument_rendering",
    "bounds_cross_domain_attribution",
}


class SemanticCompilerInputError(ValueError):
    """Raised when an input-only payload violates the compiler boundary."""


def project_compiler_input(reference_case: dict[str, Any]) -> dict[str, Any]:
    """Project an accepted reference case to reviewed, input-only evidence."""

    members = []
    for member in reference_case["member_semantics"]["members"]:
        members.append(
            {
                "member_id": member["member_id"],
                "party": member["party"],
                "actions": copy.deepcopy(member["actions"]),
            }
        )
    projected = {
        "case_scope": reference_case["case_scope"],
        "shared_semantics": copy.deepcopy(reference_case["shared_semantics"]),
        "members": members,
    }
    if "compiler_scope" in reference_case:
        projected["compiler_scope"] = copy.deepcopy(reference_case["compiler_scope"])
    return projected


def _assert_input_only(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        dependency_prefix = "$.shared_semantics.shared_review_dependencies["
        dependency_index = (
            path[len(dependency_prefix) : -1]
            if path.startswith(dependency_prefix) and path.endswith("]")
            else ""
        )
        forbidden = {
            key
            for key in OUTPUT_FIELDS.intersection(value)
            if not (
                key == "review_route"
                and dependency_index.isdigit()
            )
        }
        if forbidden:
            names = ", ".join(sorted(forbidden))
            raise SemanticCompilerInputError(
                f"{path} contains expected-output field(s): {names}"
            )
        for key, child in value.items():
            _assert_input_only(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_input_only(child, f"{path}[{index}]")


def _validate_shared_semantics(shared: dict[str, Any]) -> None:
    actions = {action["action_id"]: action for action in shared["actions"]}
    if len(actions) != len(shared["actions"]):
        raise SemanticCompilerInputError("shared action identities must be unique")
    accepted_ids = {
        action_id
        for action_id, action in actions.items()
        if action["eligibility"]["decision"] == "accepted"
    }
    for action_id, action in actions.items():
        if action["eligibility"].get("parent_context_used") is not False:
            raise SemanticCompilerInputError(
                f"parent context cannot establish eligibility for {action_id}"
            )
    episode_ids = set()
    assigned_actions = set()
    for episode in shared["episodes"]:
        episode_id = episode["episode_id"]
        if episode_id in episode_ids:
            raise SemanticCompilerInputError("episode identities must be unique")
        episode_ids.add(episode_id)
        action_ids = set(episode["action_ids"])
        if not action_ids <= accepted_ids:
            raise SemanticCompilerInputError(
                f"episode {episode_id} contains a non-accepted action"
            )
        if assigned_actions & action_ids:
            raise SemanticCompilerInputError(
                "an accepted action cannot belong to multiple episodes"
            )
        assigned_actions.update(action_ids)
    if assigned_actions != accepted_ids:
        raise SemanticCompilerInputError(
            "every accepted action must belong to exactly one episode"
        )
    for family in shared.get("policy_families", []):
        if not set(family["episode_ids"]) <= episode_ids:
            raise SemanticCompilerInputError(
                f"policy family {family['policy_family_id']} has an unknown episode"
            )
    for trait in shared.get("policy_traits", []):
        if not set(trait["action_ids"]) <= accepted_ids:
            raise SemanticCompilerInputError(
                f"policy trait {trait['trait_id']} has a non-accepted action"
            )
    for constraint in shared.get("source_render_constraints", []):
        if constraint.get("semantic_effect") not in SOURCE_SEMANTIC_EFFECTS:
            raise SemanticCompilerInputError(
                f"source constraint {constraint.get('constraint_id')} "
                "has an invalid semantic effect"
            )


def _stable_id(prefix: str, payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"{prefix}:{hashlib.sha256(encoded).hexdigest()[:16]}"


def _ordered_unique(values: Iterable[str]) -> list[str]:
    return sorted(set(values))


def _direction(statuses: Iterable[str]) -> str:
    directions = {DIRECTIONAL_STATUS[status] for status in statuses}
    if len(directions) == 1:
        return next(iter(directions))
    return "mixed"


def _proposition(
    *,
    semantic_role: str,
    proposition_type: str,
    direction: str,
    action_ids: Iterable[str],
    episode_ids: Iterable[str],
    trait_refs: Iterable[str],
    presentation_target: str,
) -> dict[str, Any]:
    base = {
        "semantic_role": semantic_role,
        "proposition_type": proposition_type,
        "direction": direction,
        "evidence_action_ids": _ordered_unique(action_ids),
        "evidence_episode_ids": _ordered_unique(episode_ids),
        "mechanism_or_trait_refs": _ordered_unique(trait_refs),
        "presentation_target": presentation_target,
    }
    return {
        "proposition_id": _stable_id("prop", base),
        **base,
        "conclusion_relevance": "excluded",
        "relationships": {"supported_by": [], "limited_by": []},
    }


def _coverage(
    shared: dict[str, Any], member_actions: dict[str, dict[str, Any]]
) -> dict[str, int]:
    accepted = [
        action
        for action in shared["actions"]
        if action["eligibility"]["decision"] == "accepted"
    ]
    controls = [
        action
        for action in shared["actions"]
        if action["eligibility"]["decision"] != "accepted"
    ]
    in_service = [
        action
        for action in accepted
        if member_actions.get(action["action_id"], {}).get("service_status")
        == "in_service"
    ]
    resolved = [
        action
        for action in accepted
        if member_actions.get(action["action_id"], {}).get("evidence_status")
        == "official_record_resolved"
        and member_actions[action["action_id"]]["status"] != "Missing Evidence"
    ]

    statuses = [
        member_actions[action["action_id"]]["status"]
        for action in in_service
        if action["action_id"] in member_actions
    ]
    complete_episodes = 0
    partial_episodes = 0
    for episode in shared["episodes"]:
        action_ids = [
            action_id
            for action_id in episode["action_ids"]
            if any(
                action["action_id"] == action_id
                and action["eligibility"]["decision"] == "accepted"
                for action in shared["actions"]
            )
        ]
        if not action_ids:
            continue
        complete = all(
            action_id in member_actions
            and member_actions[action_id]["service_status"] == "in_service"
            and member_actions[action_id]["evidence_status"]
            == "official_record_resolved"
            and member_actions[action_id]["status"] != "Missing Evidence"
            for action_id in action_ids
        )
        complete_episodes += int(complete)
        partial_episodes += int(not complete)

    return {
        "eligible_substantive_actions": len(accepted),
        "context_only_control_actions": len(controls),
        "in_service_eligible_actions": len(in_service),
        "resolved_eligible_actions": len(resolved),
        "directional_yes_no_positions": sum(
            status in DIRECTIONAL_STATUS for status in statuses
        ),
        "present_actions": statuses.count("Present"),
        "not_voting_actions": statuses.count("Not Voting"),
        "missing_evidence_actions": sum(
            member_actions.get(action["action_id"], {}).get("evidence_status")
            != "official_record_resolved"
            or member_actions.get(action["action_id"], {}).get("status")
            == "Missing Evidence"
            for action in accepted
        ),
        "unresolved_service_actions": sum(
            member_actions.get(action["action_id"], {}).get("service_status")
            == "unresolved"
            for action in accepted
        ),
        "outside_service_actions": sum(
            member_actions.get(action["action_id"], {}).get("service_status")
            in VERIFIED_OUTSIDE_SERVICE
            for action in accepted
        ),
        "complete_episodes": complete_episodes,
        "partial_episodes": partial_episodes,
    }


def _coverage_boundaries(
    coverage: dict[str, int],
    accepted_ids: set[str],
    member_actions: dict[str, dict[str, Any]],
    episodes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    status_groups = {
        status: sorted(
            action_id
            for action_id, action in member_actions.items()
            if action_id in accepted_ids and action["status"] == status
        )
        for status in ("Present", "Not Voting")
    }
    if status_groups["Present"]:
        result.append(
            _boundary(
                "coverage",
                "present",
                status_groups["Present"],
                "coverage_note",
                "Resolved Present actions are non-directional.",
            )
        )
    if status_groups["Not Voting"]:
        heavy = (
            len(status_groups["Not Voting"]) >= 2
            and coverage["not_voting_actions"]
            > coverage["directional_yes_no_positions"]
        )
        result.append(
            _boundary(
                "coverage",
                "not_voting_heavy" if heavy else "not_voting",
                status_groups["Not Voting"],
                "coverage_note",
                "Resolved Not Voting actions are non-directional.",
            )
        )
    missing = sorted(
        action_id
        for action_id, action in member_actions.items()
        if action_id in accepted_ids
        and (
            action["status"] == "Missing Evidence"
            or action["evidence_status"] != "official_record_resolved"
        )
    )
    if missing:
        result.append(
            _boundary(
                "coverage",
                "missing_evidence",
                missing,
                "coverage_note",
                "These accepted actions lack resolved official evidence.",
            )
        )
    outside = sorted(
        action_id
        for action_id, action in member_actions.items()
        if action_id in accepted_ids
        and action["service_status"] in VERIFIED_OUTSIDE_SERVICE
    )
    if outside:
        result.append(
            _boundary(
                "coverage",
                "outside_service",
                outside,
                "coverage_note",
                "These accepted actions fall outside the member's service window.",
            )
        )
    unresolved_service = sorted(
        action_id
        for action_id, action in member_actions.items()
        if action_id in accepted_ids and action["service_status"] == "unresolved"
    )
    if unresolved_service:
        result.append(
            _boundary(
                "coverage",
                "service_unresolved",
                unresolved_service,
                "coverage_note",
                "Service status is unresolved for these accepted actions.",
            )
        )
    partial_ids = []
    for episode in episodes:
        episode_ids = set(episode["action_ids"]) & accepted_ids
        known_ids = {
            action_id
            for action_id in episode_ids
            if action_id in member_actions
            and member_actions[action_id]["service_status"] == "in_service"
            and member_actions[action_id]["evidence_status"]
            == "official_record_resolved"
            and member_actions[action_id]["status"] != "Missing Evidence"
        }
        if known_ids and known_ids != episode_ids:
            partial_ids.extend(episode_ids)
    if partial_ids:
        result.append(
            _boundary(
                "coverage",
                "partial_episode",
                partial_ids,
                "coverage_note",
                "At least one reviewed episode is only partially resolved.",
            )
        )
    return result


def _boundary(
    prefix: str,
    boundary_type: str,
    action_ids: Iterable[str],
    presentation_target: str,
    detail: str,
) -> dict[str, Any]:
    action_ids = _ordered_unique(action_ids)
    identity = {"boundary_type": boundary_type, "action_ids": action_ids}
    return {
        "boundary_id": _stable_id(prefix, identity),
        "boundary_type": boundary_type,
        "action_ids": action_ids,
        "presentation_target": presentation_target,
        "detail": detail,
    }


def _method_boundaries(shared: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    context_ids = [
        action["action_id"]
        for action in shared["actions"]
        if action["eligibility"]["decision"] == "context_only"
    ]
    if context_ids:
        result.append(
            _boundary(
                "method",
                "context_only_control_exclusion",
                context_ids,
                "method_note",
                "Context-only controls do not enter substantive coverage.",
            )
        )
    rejected_ids = [
        action["action_id"]
        for action in shared["actions"]
        if action["eligibility"]["decision"] == "rejected"
    ]
    if rejected_ids:
        result.append(
            _boundary(
                "method",
                "exact_action_eligibility",
                rejected_ids,
                "method_note",
                "Rejected exact actions remain outside substantive coverage.",
            )
        )
    for episode in shared["episodes"]:
        if "episode_counting" in episode.get("method_boundary_types", []):
            result.append(
                _boundary(
                    "method",
                    "episode_counting",
                    episode["action_ids"],
                    "method_note",
                    "Multiple legislative actions count as one reviewed episode.",
                )
            )
    return result


def _compile_member(
    payload: dict[str, Any], member: dict[str, Any]
) -> dict[str, Any]:
    shared = payload["shared_semantics"]
    actions = {action["action_id"]: action for action in shared["actions"]}
    episodes = {episode["episode_id"]: episode for episode in shared["episodes"]}
    episode_for_action = {
        action_id: episode["episode_id"]
        for episode in shared["episodes"]
        for action_id in episode["action_ids"]
    }
    member_actions = {action["action_id"]: action for action in member["actions"]}

    def first_stage(action_ids: Iterable[str]) -> str:
        return min(
            action_ids,
            key=lambda action_id: (
                actions[action_id]
                .get("structural_metadata", {})
                .get("stage_order", 1),
                action_id,
            ),
        )

    accepted_ids = {
        action_id
        for action_id, action in actions.items()
        if action["eligibility"]["decision"] == "accepted"
    }
    blocked_action_ids = {
        action_id
        for constraint in shared.get("source_render_constraints", [])
        if constraint["semantic_effect"] == "blocks_behavioral_propositions"
        for action_id in constraint["action_ids"]
        if action_id in accepted_ids
    }
    directional_ids = {
        action_id
        for action_id in accepted_ids
        if action_id in member_actions
        and member_actions[action_id]["service_status"] == "in_service"
        and member_actions[action_id]["evidence_status"]
        == "official_record_resolved"
        and member_actions[action_id]["status"] in DIRECTIONAL_STATUS
        and action_id not in blocked_action_ids
    }
    traits = {
        trait["trait_id"]: trait
        for trait in shared.get("policy_traits", [])
        if trait["review_state"] == "reviewed_reusable_input"
    }
    focused = payload["case_scope"] == "focused_invariant_fixture"
    included_traits = set(
        payload.get("compiler_scope", {}).get("included_policy_trait_refs", [])
    )
    limiting_traits = set(
        payload.get("compiler_scope", {}).get("limiting_policy_trait_refs", [])
    )

    behavioral: list[dict[str, Any]] = []
    if not focused:
        for episode_id, episode in sorted(episodes.items()):
            evidence_ids = sorted(set(episode["action_ids"]) & directional_ids)
            if len(evidence_ids) < 2:
                continue
            refs = [
                trait_id
                for trait_id, trait in traits.items()
                if set(trait["action_ids"]) & set(evidence_ids)
            ]
            behavioral.append(
                _proposition(
                    semantic_role="behavioral",
                    proposition_type="trajectory",
                    direction=_direction(
                        member_actions[action_id]["status"]
                        for action_id in evidence_ids
                    ),
                    action_ids=evidence_ids,
                    episode_ids=[episode_id],
                    trait_refs=refs,
                    presentation_target="policy_trajectories",
                )
            )

    for trait_id, trait in sorted(traits.items()):
        if focused and trait_id not in included_traits:
            continue
        evidence_ids = sorted(set(trait["action_ids"]) & directional_ids)
        evidence_episodes = {
            episode_for_action[action_id]
            for action_id in evidence_ids
            if action_id in episode_for_action
        }
        if len(evidence_episodes) < 2 or not evidence_ids:
            continue
        statuses = [member_actions[action_id]["status"] for action_id in evidence_ids]
        if len({_direction([status]) for status in statuses}) != 1:
            continue
        behavioral.append(
            _proposition(
                semantic_role="behavioral",
                proposition_type="repeated_pattern",
                direction=_direction(statuses),
                action_ids=evidence_ids,
                episode_ids=evidence_episodes,
                trait_refs=[trait_id],
                presentation_target="repeated_patterns",
            )
        )

    if not focused:
        covered_ids = {
            action_id
            for proposition in behavioral
            for action_id in proposition["evidence_action_ids"]
        }
        for action_id in sorted(directional_ids - covered_ids):
            action_traits = [
                trait_id
                for trait_id, trait in traits.items()
                if action_id in trait["action_ids"]
            ]
            behavioral.append(
                _proposition(
                    semantic_role="behavioral",
                    proposition_type="notable_choice",
                    direction=DIRECTIONAL_STATUS[member_actions[action_id]["status"]],
                    action_ids=[action_id],
                    episode_ids=[episode_for_action[action_id]],
                    trait_refs=action_traits
                    or actions[action_id].get("policy_trait_refs", []),
                    presentation_target="other_notable_choices",
                )
            )

    synthesis: list[dict[str, Any]] = []
    pending_shared_review = False
    mechanism: dict[str, Any] | None = None
    for relationship in shared.get("trait_relationships", []):
        if relationship.get("review_state") == "human_review_pending":
            pending_shared_review = True
            continue
        if relationship["relationship"] != "contrasts":
            continue
        left = next(
            (
                proposition
                for proposition in behavioral
                if relationship["left"]
                in proposition["mechanism_or_trait_refs"]
                and proposition["proposition_type"] == "repeated_pattern"
            ),
            None,
        )
        right = next(
            (
                proposition
                for proposition in behavioral
                if relationship["right"]
                in proposition["mechanism_or_trait_refs"]
                and proposition["proposition_type"] == "repeated_pattern"
            ),
            None,
        )
        if left and right and left["direction"] != right["direction"]:
            supporters = [left, right]
            representative_actions = []
            for proposition in supporters:
                for episode_id in proposition["evidence_episode_ids"]:
                    candidates = set(
                        proposition["evidence_action_ids"]
                    ) & set(episodes[episode_id]["action_ids"])
                    representative_actions.append(first_stage(candidates))
            mechanism = _proposition(
                semantic_role="synthesis",
                proposition_type="mechanism_divide",
                direction="mixed",
                action_ids=representative_actions,
                episode_ids=[
                    episode_id
                    for proposition in supporters
                    for episode_id in proposition["evidence_episode_ids"]
                ],
                trait_refs=[relationship["left"], relationship["right"]],
                presentation_target="conclusion_only",
            )
            mechanism["relationships"]["supported_by"] = [
                proposition["proposition_id"] for proposition in supporters
            ]
            synthesis.append(mechanism)

    interpretive_boundary: dict[str, Any] | None = None
    if focused and limiting_traits:
        boundary_ids = {
            action_id
            for trait_id in limiting_traits
            for action_id in traits[trait_id]["action_ids"]
            if action_id in directional_ids
        }
        if boundary_ids:
            interpretive_boundary = _proposition(
                semantic_role="synthesis",
                proposition_type="interpretive_boundary",
                direction=_direction(
                    member_actions[action_id]["status"]
                    for action_id in boundary_ids
                ),
                action_ids=boundary_ids,
                episode_ids=[
                    episode_for_action[action_id] for action_id in boundary_ids
                ],
                trait_refs=limiting_traits,
                presentation_target="conclusion_only",
            )
            synthesis.append(interpretive_boundary)
    elif not mechanism:
        for relationship in shared.get("trait_relationships", []):
            if relationship["relationship"] != "later_related_framework":
                continue
            trajectory = next(
                (
                    proposition
                    for proposition in behavioral
                    if proposition["proposition_type"] == "trajectory"
                    and proposition["direction"] == "mixed"
                    and relationship["from"] in proposition["evidence_action_ids"]
                    and relationship["to"] in proposition["evidence_action_ids"]
                ),
                None,
            )
            if trajectory:
                interpretive_boundary = _proposition(
                    semantic_role="synthesis",
                    proposition_type="interpretive_boundary",
                    direction="non_directional",
                    action_ids=[relationship["from"], relationship["to"]],
                    episode_ids=trajectory["evidence_episode_ids"],
                    trait_refs=[],
                    presentation_target="conclusion_only",
                )
                synthesis.append(interpretive_boundary)
                break

    coverage = _coverage(shared, member_actions)
    directional_directions = {
        DIRECTIONAL_STATUS[member_actions[action_id]["status"]]
        for action_id in directional_ids
    }
    uniform: dict[str, Any] | None = None
    no_throughline: dict[str, Any] | None = None
    independent_episodes = {
        episode_for_action[action_id]
        for action_id in directional_ids
        if action_id in episode_for_action
    }
    if (
        not focused
        and not mechanism
        and not interpretive_boundary
        and len(behavioral) > 1
        and len(independent_episodes) > 1
        and len(directional_directions) == 1
        and coverage["not_voting_actions"]
        <= coverage["directional_yes_no_positions"]
    ):
        uniform = _proposition(
            semantic_role="synthesis",
            proposition_type="uniform_direction",
            direction=next(iter(directional_directions)),
            action_ids=[
                action_id
                for proposition in behavioral
                for action_id in proposition["evidence_action_ids"]
            ],
            episode_ids=[
                episode_id
                for proposition in behavioral
                for episode_id in proposition["evidence_episode_ids"]
            ],
            trait_refs=[],
            presentation_target="conclusion_only",
        )
        representative_actions = [
            first_stage(proposition["evidence_action_ids"])
            for proposition in behavioral
        ]
        representative_episodes = [
            episode_for_action[action_id] for action_id in representative_actions
        ]
        no_throughline = _proposition(
            semantic_role="synthesis",
            proposition_type="no_common_throughline",
            direction="non_directional",
            action_ids=representative_actions,
            episode_ids=representative_episodes,
            trait_refs=[],
            presentation_target="conclusion_only",
        )
        synthesis.extend([uniform, no_throughline])

    mixed_trajectories = [
        proposition
        for proposition in behavioral
        if proposition["proposition_type"] == "trajectory"
        and proposition["direction"] == "mixed"
    ]
    patterns = [
        proposition
        for proposition in behavioral
        if proposition["proposition_type"] == "repeated_pattern"
    ]
    if mechanism:
        mechanism["conclusion_relevance"] = "primary"
        mechanism["relationships"]["limited_by"] = [
            proposition["proposition_id"] for proposition in mixed_trajectories
        ]
        for proposition in patterns:
            proposition["conclusion_relevance"] = "primary"
        for proposition in mixed_trajectories:
            proposition["conclusion_relevance"] = "limiting"
    elif uniform and no_throughline:
        uniform["conclusion_relevance"] = "primary"
        uniform["relationships"]["supported_by"] = [
            proposition["proposition_id"] for proposition in behavioral
        ]
        uniform["relationships"]["limited_by"] = [no_throughline["proposition_id"]]
        no_throughline["conclusion_relevance"] = "limiting"
        no_throughline["relationships"]["supported_by"] = [
            proposition["proposition_id"] for proposition in behavioral
        ]
        for proposition in behavioral:
            proposition["conclusion_relevance"] = "supporting"
    elif interpretive_boundary:
        interpretive_boundary["conclusion_relevance"] = "limiting"
        if focused:
            for proposition in patterns:
                proposition["conclusion_relevance"] = "primary"
                proposition["relationships"]["limited_by"] = [
                    interpretive_boundary["proposition_id"]
                ]
            interpretive_boundary["relationships"]["supported_by"] = [
                proposition["proposition_id"] for proposition in patterns
            ]
        else:
            trajectory = mixed_trajectories[0]
            trajectory["conclusion_relevance"] = "primary"
            trajectory["relationships"]["limited_by"] = [
                interpretive_boundary["proposition_id"]
            ]
            interpretive_boundary["relationships"]["supported_by"] = [
                trajectory["proposition_id"]
            ]
    elif patterns:
        pattern_directions = {proposition["direction"] for proposition in patterns}
        for proposition in patterns:
            proposition["conclusion_relevance"] = "primary"
        for proposition in behavioral:
            if proposition in patterns:
                continue
            proposition["conclusion_relevance"] = (
                "limiting"
                if len(pattern_directions) == 1
                and proposition["direction"] not in pattern_directions
                else "supporting"
            )
    elif len(behavioral) == 1 and behavioral[0]["proposition_type"] == "trajectory":
        behavioral[0]["conclusion_relevance"] = "primary"
    else:
        for proposition in behavioral:
            proposition["conclusion_relevance"] = "supporting"

    propositions = behavioral + synthesis
    primary_ids = [
        proposition["proposition_id"]
        for proposition in propositions
        if proposition["conclusion_relevance"] == "primary"
    ]
    limiting_ids = [
        proposition["proposition_id"]
        for proposition in propositions
        if proposition["conclusion_relevance"] == "limiting"
    ]
    ownership: dict[str, list[str]] = defaultdict(list)
    for proposition in propositions:
        ownership[proposition["presentation_target"]].append(
            proposition["proposition_id"]
        )

    behavioral_ids = {
        action_id
        for proposition in behavioral
        for action_id in proposition["evidence_action_ids"]
    }
    reasons = []
    for action_id in sorted(accepted_ids - behavioral_ids):
        action = member_actions.get(action_id)
        if focused:
            reason_code = "outside_focused_fixture"
        elif not action:
            reason_code = "missing_evidence"
        elif (
            action["status"] == "Missing Evidence"
            or action["evidence_status"] != "official_record_resolved"
        ):
            reason_code = "missing_evidence"
        elif action["service_status"] in VERIFIED_OUTSIDE_SERVICE:
            reason_code = "outside_service"
        elif action["service_status"] == "unresolved":
            reason_code = "service_unresolved"
        elif action_id in blocked_action_ids:
            reason_code = "source_constraint_blocks_behavioral_proposition"
        elif action["status"] in NON_DIRECTIONAL_REASONS:
            reason_code = NON_DIRECTIONAL_REASONS[action["status"]]
        else:
            raise SemanticCompilerInputError(
                f"directional accepted action {action_id} was not represented"
            )
        reasons.append(
            {
                "action_id": action_id,
                "reason_code": reason_code,
                "detail": "The action is explicitly excluded from behavioral evidence.",
            }
        )

    has_nonaccepted_actions = any(
        action["eligibility"]["decision"] != "accepted"
        for action in shared["actions"]
    )
    if (
        coverage["missing_evidence_actions"]
        or coverage["unresolved_service_actions"]
        or blocked_action_ids
    ):
        review_route = "blocked"
    elif (
        coverage["present_actions"]
        or coverage["not_voting_actions"]
        or coverage["outside_service_actions"]
        or has_nonaccepted_actions
        or shared.get("source_render_constraints")
        or mixed_trajectories
        or pending_shared_review
        or len(independent_episodes) <= 1
    ):
        review_route = "human_exception_required"
    elif focused:
        review_route = "standard_generation_pass"
    elif uniform:
        review_route = "sampled_audit_candidate"
    elif mechanism:
        review_route = "standard_generation_pass"
    else:
        review_route = "human_exception_required"

    return {
        "member_id": member["member_id"],
        "party": member["party"],
        "coverage": coverage,
        "proposition_graph": {"propositions": propositions},
        "composition": {
            "conclusion_plan": {
                "primary_proposition_ids": primary_ids,
                "limiting_proposition_ids": limiting_ids,
            },
            "presentation_ownership": dict(ownership),
            "coverage_boundaries": _coverage_boundaries(
                coverage, accepted_ids, member_actions, list(episodes.values())
            ),
            "method_boundaries": _method_boundaries(shared),
        },
        "action_accounting": {
            "behavioral_proposition_action_ids": sorted(behavioral_ids),
            "non_proposition_reasons": reasons,
        },
        "review_route": review_route,
    }


def compile_semantic_ir(payload: dict[str, Any]) -> dict[str, Any]:
    """Compile reviewed shared inputs into member Semantic IR results."""

    _assert_input_only(payload)
    required = {"case_scope", "shared_semantics", "members"}
    missing = required - payload.keys()
    if missing:
        raise SemanticCompilerInputError(
            f"compiler input missing: {', '.join(sorted(missing))}"
        )
    _validate_shared_semantics(payload["shared_semantics"])
    results = [_compile_member(payload, member) for member in payload["members"]]
    return {
        "members": results,
        "source_render_constraints": copy.deepcopy(
            payload["shared_semantics"].get("source_render_constraints", [])
        ),
    }
