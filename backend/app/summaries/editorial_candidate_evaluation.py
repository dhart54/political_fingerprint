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

    evaluations = [_evaluate_candidate(candidate, evidence) for candidate in candidate_catalog]
    viable = [item for item in evaluations if item["eligible"]]
    if viable:
        selected = max(viable, key=lambda item: (item["score"], item["specificity"], item["candidate_id"]))
        candidate = next(item for item in candidate_catalog if item["candidate_id"] == selected["candidate_id"])
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
    return {
        "schema_version": "editorial_member_inference_v2", "member": deepcopy(overlay["member"]),
        "candidate_id": candidate["candidate_id"], "inference_level": candidate["inference_level"],
        "evidence_strength_label": candidate["evidence_strength_label"], "primary_conclusion": primary,
        "assessment": "candidate_weakened" if weakening_episodes else "candidate_supported_by_current_sample",
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
    }


def _evaluate_candidate(candidate: dict, evidence: dict) -> dict:
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
    return {"candidate_id": candidate["candidate_id"], "eligible": eligible, "score": score,
            "specificity": specificity, "supporting_themes": supporting, "conflicting_themes": conflicts}


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
    }
