"""Domain-neutral aggregation for editorially researched policy episodes.

This module does not classify bills or invent themes. It validates and aggregates
human/agent-reviewed episode annotations into a reviewer-visible inference
candidate that can be recomputed as the reviewed record grows.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy

VALID_DIRECTIONS = {"strengthens", "weakens", "neutral"}


def build_editorial_inference(episodes: list[dict], conclusion: dict) -> dict:
    """Aggregate structured episode evidence for one editorial conclusion candidate."""
    candidate_id = required(conclusion, "candidate_id")
    normalized = [normalize_episode(item, candidate_id) for item in episodes]
    independent = unique_by_id(item for item in normalized if item["independent"])

    effects = {"strengthens": [], "weakens": [], "neutral": []}
    weights = {"strengthens": 0, "weakens": 0}
    for item in independent:
        effect = item["conclusion_effect"]
        effects[effect["direction"]].append({
            "episode_id": item["episode_id"],
            "weight": effect["weight"],
            "rationale": effect["rationale"],
        })
        if effect["direction"] in weights:
            weights[effect["direction"]] += effect["weight"]

    repeated_themes, one_off_themes = aggregate_themes(independent, conclusion.get("theme_candidates", []))
    trajectories = [
        {
            "episode_id": item["episode_id"],
            "relationship_to_repeated_stages": item["relationship_to_repeated_stages"],
            "member_trajectory": item["member_trajectory"],
            "practical_policy_direction": item["practical_policy_direction"],
        }
        for item in independent
        if item["relationship_to_repeated_stages"]
    ]
    notable_choices = [
        {
            "episode_id": item["episode_id"],
            "mechanism_family": item["mechanism_family"],
            "practical_policy_direction": item["practical_policy_direction"],
        }
        for item in independent
        if item.get("notable_one_off")
    ]
    limitations = []
    for item in independent:
        for text in [*item["contrary_or_limiting_evidence"], *item["package_vote_limitations"]]:
            limitations.append({"episode_id": item["episode_id"], "text": text})
    limitations.extend({"episode_id": None, "text": text} for text in conclusion.get("global_limitations", []))

    support_balance = weights["strengthens"] - weights["weakens"]
    return {
        "schema_version": "editorial_episode_inference_v1",
        "candidate_id": candidate_id,
        "inference_level": required(conclusion, "inference_level"),
        "evidence_strength_label": required(conclusion, "evidence_strength_label"),
        "primary_conclusion": required(conclusion, "primary_conclusion"),
        "assessment": assess_candidate(weights),
        "support_balance": support_balance,
        "supporting_independent_episodes": effects["strengthens"],
        "weakening_independent_episodes": effects["weakens"],
        "neutral_independent_episodes": effects["neutral"],
        "independent_episode_count": len(independent),
        "within_episode_trajectories": trajectories,
        "repeated_cross_episode_themes": repeated_themes,
        "notable_one_off_choices": notable_choices,
        "one_off_or_unproven_themes": one_off_themes,
        "contrary_or_limiting_evidence": limitations,
        "why_conclusion_does_not_go_further": required(conclusion, "why_conclusion_does_not_go_further"),
        "future_expansion_rule": required(conclusion, "future_expansion_rule"),
        "reviewed_period": required(conclusion, "reviewed_period"),
        "human_review_status": required(conclusion, "human_review_status"),
        "episode_annotations": normalized,
    }


def assess_candidate(weights: dict[str, int]) -> str:
    support = weights["strengthens"]
    weakening = weights["weakens"]
    if not support:
        return "insufficient_support"
    if weakening > support:
        return "candidate_not_supported_by_current_sample"
    if weakening == support and weakening:
        return "candidate_contested"
    if weakening * 2 >= support and weakening:
        return "candidate_weakened"
    return "candidate_supported_by_current_sample"


def aggregate_themes(episodes: list[dict], theme_candidates: list[dict]) -> tuple[list[dict], list[dict]]:
    membership = defaultdict(list)
    by_id = {item["episode_id"]: item for item in episodes}
    for item in episodes:
        for evidence in item["theme_evidence"]:
            membership[evidence["theme_id"]].append({
                "episode_id": item["episode_id"],
                "mechanism_family": item["mechanism_family"],
                "rationale": evidence["rationale"],
            })

    repeated = []
    one_off = []
    for theme in deepcopy(theme_candidates):
        theme_id = required(theme, "theme_id")
        evidence = membership.get(theme_id, [])
        independent_ids = {item["episode_id"] for item in evidence if item["episode_id"] in by_id}
        mechanisms = {item["mechanism_family"] for item in evidence}
        minimum_mechanisms = int(theme.get("minimum_mechanism_diversity", 2))
        output = {
            "theme_id": theme_id,
            "label": required(theme, "label"),
            "finding": required(theme, "finding"),
            "supporting_episodes": evidence,
            "mechanism_families": sorted(mechanisms),
            "editorially_defensible": bool(theme.get("editorially_defensible")),
        }
        if output["editorially_defensible"] and len(independent_ids) >= 2 and len(mechanisms) >= minimum_mechanisms:
            repeated.append(output)
        else:
            output["not_repeated_reason"] = (
                theme.get("not_repeated_reason")
                or "The reviewed annotations do not yet establish a defensible cross-episode theme with sufficient independent and mechanism-diverse evidence."
            )
            one_off.append(output)
    return repeated, one_off


def normalize_episode(item: dict, candidate_id: str) -> dict:
    result = deepcopy(item)
    for key in (
        "episode_id", "mechanism_family", "member_trajectory", "practical_policy_direction",
        "source_confidence", "reviewed_period",
    ):
        required(result, key)
    result["independent"] = bool(result.get("independent"))
    result["relationship_to_repeated_stages"] = result.get("relationship_to_repeated_stages", "")
    result["candidate_theme_tags"] = list(result.get("candidate_theme_tags", []))
    result["theme_evidence"] = list(result.get("theme_evidence", []))
    result["contrary_or_limiting_evidence"] = list(result.get("contrary_or_limiting_evidence", []))
    result["package_vote_limitations"] = list(result.get("package_vote_limitations", []))
    effect = result.get("conclusion_effect", {})
    if effect.get("candidate_id") != candidate_id:
        raise ValueError(f"episode {result['episode_id']} does not address conclusion {candidate_id}")
    if effect.get("direction") not in VALID_DIRECTIONS:
        raise ValueError(f"episode {result['episode_id']} has invalid conclusion direction")
    weight = effect.get("weight")
    if not isinstance(weight, int) or not 0 <= weight <= 3:
        raise ValueError(f"episode {result['episode_id']} weight must be an integer from 0 to 3")
    required(effect, "rationale")
    result["conclusion_effect"] = effect
    return result


def unique_by_id(items) -> list[dict]:
    result = []
    seen = set()
    for item in items:
        episode_id = item["episode_id"]
        if episode_id in seen:
            raise ValueError(f"duplicate independent episode_id: {episode_id}")
        seen.add(episode_id)
        result.append(item)
    return result


def required(value: dict, key: str):
    if value.get(key) in (None, ""):
        raise ValueError(f"missing required inference field: {key}")
    return value[key]
