"""Generic theme-based candidate evaluation for member episode overlays."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy


def evaluate_candidates(*, overlay: dict, shared_episodes: list[dict], theme_catalog: dict,
                        candidate_catalog: list[dict], minimum_complete_episodes: int = 3) -> dict:
    """Select and synthesize a candidate without access to identity, party, or raw roll totals."""
    complete = [item for item in overlay["episode_trajectories"] if item["coverage_status"] == "complete"]
    if len(complete) < minimum_complete_episodes:
        return _insufficient(overlay, len(complete))
    shared_by_id = {item["episode_id"]: item for item in shared_episodes}
    evidence = defaultdict(list)
    for trajectory in complete:
        shared = shared_by_id.get(trajectory["episode_id"])
        if not shared:
            raise ValueError(f"overlay references unknown shared episode: {trajectory['episode_id']}")
        for item in trajectory["theme_evidence"]:
            evidence[item["theme_id"]].append({
                "episode_id": trajectory["episode_id"],
                "mechanism_family": shared["mechanism_family"],
                "rationale": item["rationale"],
            })

    archetype = next(
        (item for item in candidate_catalog
         if item.get("archetype_type") == "uniform_direction_without_common_policy_rationale"),
        None,
    )
    substantive_candidates = [item for item in candidate_catalog if not item.get("archetype_type")]
    evaluations = [_evaluate_candidate(candidate, evidence, theme_catalog) for candidate in substantive_candidates]
    viable = [item for item in evaluations if item["eligible"]]
    if viable:
        selected = max(viable, key=lambda item: (item["score"], item["specificity"], item["candidate_id"]))
        candidate = next(item for item in substantive_candidates if item["candidate_id"] == selected["candidate_id"])
    elif archetype and (uniform := _uniform_action_direction(overlay)):
        candidate = archetype
        selected = {
            "score": 0,
            "specificity": 0,
            "supporting_themes": [],
            "conflicting_themes": [],
            "uniform_action_direction": uniform,
        }
    else:
        candidate = {
            "candidate_id": "contested-mixed-record", "inference_level": "contested_candidate",
            "evidence_strength_label": "Mixed reviewed evidence",
            "conclusion": "the actions are mixed and do not yet establish a repeated cross-episode boundary",
            "why": "No candidate has enough independent, mechanism-diverse thematic support in the current overlay.",
            "required_themes": [], "conflicting_themes": [],
        }
        selected = {"score": 0, "supporting_themes": [], "conflicting_themes": []}

    repeated = []
    one_off = []
    for theme_id, rows in evidence.items():
        definition = theme_catalog[theme_id]
        if definition.get("basis_type") == "action_direction_only":
            continue
        output = {
            "theme_id": theme_id, "label": definition["label"], "finding": definition["finding"],
            "supporting_episodes": rows,
            "mechanism_families": sorted({row["mechanism_family"] for row in rows}),
            "editorially_defensible": len({row["episode_id"] for row in rows}) >= 2,
        }
        if output["editorially_defensible"]:
            repeated.append(output)
        else:
            output["not_repeated_reason"] = "Only one independent episode supplies this theme in the reviewed sample."
            one_off.append(output)

    selected_support = set(selected.get("supporting_themes", []))
    selected_conflicts = set(selected.get("conflicting_themes", []))
    supporting_episodes = _episodes_for(evidence, selected_support)
    weakening_episodes = _episodes_for(evidence, selected_conflicts)
    name = _short_name(overlay["member"])
    uniform = selected.get("uniform_action_direction")
    if uniform:
        primary = _uniform_primary(name, uniform, complete, candidate)
    else:
        primary = f"In this reviewed sample, {name}'s recorded actions indicate {candidate['conclusion']}."
    limitations = [
        {"episode_id": trajectory["episode_id"], "text": text}
        for trajectory in complete
        for text in [*trajectory.get("contrary_or_limiting_evidence", []), *trajectory.get("package_vote_limitations", [])]
    ]
    for theme_id in selected_conflicts:
        for row in evidence.get(theme_id, []):
            limitations.append({"episode_id": row["episode_id"], "text": theme_catalog[theme_id]["finding"]})
    trajectories = [{
        "episode_id": item["episode_id"],
        "relationship_to_repeated_stages": item.get("relationship_to_repeated_stages", ""),
        "member_trajectory": item["member_trajectory"],
        "practical_policy_direction": item["practical_policy_direction"],
    } for item in complete if item.get("relationship_to_repeated_stages")]
    notable = [{
        "episode_id": item["episode_id"], "mechanism_family": item["mechanism_family"],
        "practical_policy_direction": item["practical_policy_direction"],
    } for item in complete if any(e["theme_id"] in selected_conflicts for e in item["theme_evidence"])]
    if uniform:
        eligible_repeated = [
            item for item in repeated
            if theme_catalog[item["theme_id"]].get("uniform_repeated_pattern")
        ]
        repeated = eligible_repeated
        repeated_episode_ids = {
            row["episode_id"]
            for item in repeated
            for row in item["supporting_episodes"]
        }
        trajectory_episode_ids = {item["episode_id"] for item in trajectories}
        uniform_order = candidate.get("policy_area_order", [])
        ordered_complete = sorted(
            complete,
            key=lambda item: uniform_order.index(item["episode_id"])
            if item["episode_id"] in uniform_order else len(complete),
        )
        notable = [{
            "episode_id": item["episode_id"], "mechanism_family": item["mechanism_family"],
            "practical_policy_direction": item["practical_policy_direction"],
        } for item in ordered_complete
            if item["episode_id"] not in repeated_episode_ids | trajectory_episode_ids]
        supporting_episodes = [{
            "episode_id": item["episode_id"],
            "weight": 1,
            "rationale": f"Recorded {uniform['direction']} action in this complete reviewed episode; direction is descriptive, not a shared policy rationale.",
        } for item in complete]
    return {
        "schema_version": "editorial_member_inference_v2", "member": deepcopy(overlay["member"]),
        "candidate_id": candidate["candidate_id"], "inference_level": candidate["inference_level"],
        "evidence_strength_label": (
            ("Uniform opposition" if uniform["direction"] == "Nay" else "Uniform support")
            + " across the reviewed proposals"
            if uniform else candidate["evidence_strength_label"]
        ), "primary_conclusion": primary,
        "assessment": (
            "uniform_direction_without_common_policy_rationale"
            if uniform else "candidate_weakened" if weakening_episodes else "candidate_supported_by_current_sample"
        ),
        "support_balance": len(supporting_episodes) - len(weakening_episodes),
        "supporting_independent_episodes": supporting_episodes,
        "weakening_independent_episodes": weakening_episodes, "neutral_independent_episodes": [],
        "independent_episode_count": len(complete), "within_episode_trajectories": trajectories,
        "repeated_cross_episode_themes": sorted(repeated, key=lambda item: item["theme_id"]),
        "notable_one_off_choices": notable, "one_off_or_unproven_themes": sorted(one_off, key=lambda item: item["theme_id"]),
        "contrary_or_limiting_evidence": limitations,
        "why_conclusion_does_not_go_further": candidate["why"],
        "future_expansion_rule": "Recompute from expanded member actions and shared episode annotations; new independent episodes may strengthen, narrow, contest, or replace this candidate.",
        "reviewed_period": overlay["reviewed_period"], "human_review_status": "human_approval_pending",
        "coverage": deepcopy(overlay["coverage"]), "episode_references": [item["episode_id"] for item in complete],
        "candidate_evaluation": evaluations,
        "candidate_basis": {
            "basis_type": candidate.get("basis_type", candidate.get("archetype_type", "substantive_repeated_pattern")),
            "substantive_theme_ids": selected.get("supporting_themes", []),
            "uniform_action_direction": deepcopy(uniform),
        },
    }


def _evaluate_candidate(candidate: dict, evidence: dict, theme_catalog: dict) -> dict:
    supporting = []
    eligible = True
    specificity = 0
    for rule in candidate["required_themes"]:
        rows = evidence.get(rule["theme_id"], [])
        episodes = len({row["episode_id"] for row in rows})
        mechanisms = len({row["mechanism_family"] for row in rows})
        met = episodes >= rule.get("minimum_episodes", 1) and mechanisms >= rule.get("minimum_mechanisms", 1)
        eligible &= met
        specificity += rule.get("minimum_episodes", 1) + rule.get("minimum_mechanisms", 1)
        if met:
            supporting.append(rule["theme_id"])
    conflicts = [theme_id for theme_id in candidate.get("conflicting_themes", []) if evidence.get(theme_id)]
    score = sum(len({row["episode_id"] for row in evidence[theme_id]}) for theme_id in supporting) - len(conflicts)
    substantive_support = [
        theme_id for theme_id in supporting
        if theme_catalog[theme_id].get("basis_type", "shared_policy_dimension") != "action_direction_only"
    ]
    eligible &= bool(substantive_support)
    return {"candidate_id": candidate["candidate_id"], "eligible": eligible, "score": score,
            "specificity": specificity, "supporting_themes": supporting, "conflicting_themes": conflicts}


def _uniform_action_direction(overlay: dict) -> dict | None:
    actions = [
        item["action"] for item in overlay.get("roll_actions", [])
        if item.get("counting") and item.get("action") in {"Yea", "Nay"}
    ]
    if not actions:
        return None
    direction = max(("Yea", "Nay"), key=actions.count)
    count = actions.count(direction)
    if count / len(actions) < .85:
        return None
    return {
        "direction": direction,
        "count": count,
        "total": len(actions),
        "uniform": count == len(actions),
    }


def _uniform_primary(name: str, uniform: dict, complete: list[dict], candidate: dict) -> str:
    direction = uniform["direction"]
    count_label = {7: "seven"}.get(uniform["total"], str(uniform["total"]))
    count_phrase = (
        f"all {count_label}" if uniform["uniform"]
        else f"{uniform['count']} of {uniform['total']}"
    )
    action_phrase = "against" if direction == "Nay" else "for"
    direction_word = "oppositional" if direction == "Nay" else "supportive"
    areas = candidate.get("policy_area_phrases", {})
    concrete = []
    ordered = sorted(
        complete,
        key=lambda item: candidate.get("policy_area_order", []).index(item["episode_id"])
        if item["episode_id"] in candidate.get("policy_area_order", []) else len(complete),
    )
    for item in ordered:
        phrase = areas.get(item["episode_id"], item["mechanism_family"])
        prefix = "all three actions in " if len(item.get("rolls", [])) == 3 else ""
        concrete.append(f"{prefix}{phrase}")
    if len(concrete) > 1:
        concrete_text = ", ".join(concrete[:-1]) + f", and {concrete[-1]}"
    else:
        concrete_text = concrete[0]
    philosophy = candidate.get("philosophy_label", "policy philosophy")
    return (
        f"Across the reviewed record, {name} voted {action_phrase} {count_phrase} substantive proposals examined here. "
        f"That included {concrete_text}. "
        f"The vote direction is consistently {direction_word}, but the proposals span different—and sometimes "
        f"substantively contrasting—policy approaches, so this record does not establish one overarching {philosophy}."
    )


def _episodes_for(evidence: dict, themes: set[str]) -> list[dict]:
    rows = {}
    for theme_id in sorted(themes):
        for row in evidence.get(theme_id, []):
            rows[row["episode_id"]] = {"episode_id": row["episode_id"], "weight": 2, "rationale": row["rationale"]}
    return [rows[episode_id] for episode_id in sorted(rows)]


def _short_name(member: dict) -> str:
    formal = member.get("formal_name", "")
    for prefix in ("Mr. ", "Mrs. ", "Ms. ", "Miss ", "Dr. "):
        if formal.startswith(prefix):
            return formal[len(prefix):]
    return member["display_name"]


def _insufficient(overlay: dict, complete_count: int) -> dict:
    return {
        "schema_version": "editorial_member_inference_v2", "member": deepcopy(overlay["member"]),
        "candidate_id": "insufficient-evidence", "inference_level": "insufficient_evidence",
        "evidence_strength_label": "Not enough reviewed evidence",
        "primary_conclusion": f"The reviewed record for {_short_name(overlay['member'])} does not cover enough independent episodes to support a cross-episode conclusion.",
        "assessment": "insufficient_coverage", "support_balance": 0,
        "supporting_independent_episodes": [], "weakening_independent_episodes": [], "neutral_independent_episodes": [],
        "independent_episode_count": complete_count, "within_episode_trajectories": [],
        "repeated_cross_episode_themes": [], "notable_one_off_choices": [], "one_off_or_unproven_themes": [],
        "contrary_or_limiting_evidence": [],
        "why_conclusion_does_not_go_further": "Fewer than three independent episodes have complete Yes/No coverage.",
        "future_expansion_rule": "Recompute when additional complete episode actions are available.",
        "reviewed_period": overlay["reviewed_period"], "human_review_status": "human_approval_pending",
        "coverage": deepcopy(overlay["coverage"]), "episode_references": [], "candidate_evaluation": [],
        "candidate_basis": {
            "basis_type": "insufficient_evidence",
            "substantive_theme_ids": [],
            "uniform_action_direction": None,
        },
    }
