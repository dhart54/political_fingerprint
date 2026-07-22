"""Build review-only Justice cross-member overlays from official recorded actions."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.summaries.editorial_member_overlay import build_member_inference, build_member_overlay


SUBSTANTIVE_ROLLS = (32, 33, 130, 131, 166, 275, 299)
CONTROL_ROLLS = (160, 161, 267, 268, 290, 291)
EPISODE_ROLLS = {
    "halt-fentanyl-legislative-path": (32, 33, 166),
    "retired-service-weapon-purchases": (130,),
    "officer-safety-data-reporting": (131,),
    "dc-police-pursuit-rules": (275,),
    "dc-policing-reform-repeal": (299,),
}
SHARED_SET = {
    "episode_set_id": "justice-public-safety-pr95-five-episodes",
    "version": "1.0.0",
    "episode_map_path": "docs/editorial/valerie_foushee_justice_public_safety_gold_v1/policy_episode_map.json",
}
PUBLICATION = {
    "editorial_status": "human_approval_pending",
    "benchmark_status": "not_promoted",
    "production_eligible": False,
}
REVIEWED_PERIOD = "119th Congress, February 6-November 19, 2025"
SELECTED = {
    "F000477": ("reference_member", "Reference record researched in PR #95."),
    "A000370": ("equivalent_vector", "Exact substantive vector match tests structurally equivalent treatment."),
    "A000055": ("dominant_contrast", "Complete vector contrasts with the reference vector on six of seven rolls and represents the most common complete vector."),
    "M001184": ("republican_outlier", "Unique complete Republican vector separates the fentanyl episode from police-tool and authority episodes."),
    "B000490": ("different_fentanyl_and_dc_boundary", "Complete Democratic vector supports both permanent fentanyl stages while opposing both D.C. proposals."),
    "G000586": ("cross_mechanism_opposition", "Unique all-Nay complete vector tests one-directional actions without turning them into an ideology label."),
    "M001217": ("broad_support_with_exception", "Unique mostly-Yea complete vector tests whether one safeguard-repeal opposition remains visible as contrary evidence."),
}


def _text(element) -> str:
    return (element.text or "").strip() if element is not None else ""


def _load_member_directory(path: Path) -> dict[str, dict]:
    root = ElementTree.parse(path).getroot()
    result = {}
    for member in root.findall("./members/member"):
        info = member.find("member-info")
        if info is None:
            continue
        identifier = _text(info.find("bioguideID"))
        if not identifier:
            continue
        state = info.find("state")
        result[identifier] = {
            "bioguide_id": identifier,
            "display_name": _text(info.find("official-name")) or _text(info.find("namelist")),
            "formal_name": _text(info.find("formal-name")),
            "party": _text(info.find("party")),
            "state": state.attrib.get("postal-code") if state is not None else "",
            "district": _text(info.find("district")),
        }
    return result


def _load_roll(path: Path) -> tuple[dict, dict[str, dict]]:
    root = ElementTree.parse(path).getroot()
    metadata = root.find("vote-metadata")
    if metadata is None:
        raise ValueError(f"missing vote metadata in {path}")
    roll = int(_text(metadata.find("rollcall-num")))
    actions = {}
    for row in root.findall("./vote-data/recorded-vote"):
        legislator = row.find("legislator")
        identifier = legislator.attrib.get("name-id") if legislator is not None else None
        if not identifier:
            raise ValueError(f"missing member identifier in roll {roll}")
        actions[identifier] = {
            "action": _normalize_action(_text(row.find("vote"))),
            "fallback_name": legislator.attrib.get("unaccented-name") or _text(legislator),
            "party": legislator.attrib.get("party", ""),
            "state": legislator.attrib.get("state", ""),
        }
    return {
        "roll": roll,
        "date": _text(metadata.find("action-date")),
        "source_url": f"https://clerk.house.gov/evs/2025/roll{roll:03d}.xml",
        "question": _text(metadata.find("vote-question")),
    }, actions


def _normalize_action(value: str) -> str:
    normalized = {"Aye": "Yea", "No": "Nay"}.get(value, value)
    if normalized not in {"Yea", "Nay", "Present", "Not Voting"}:
        raise ValueError(f"unsupported House recorded action: {value}")
    return normalized


def _party_majorities(actions: dict[str, dict]) -> dict[str, str | None]:
    result = {}
    parties = sorted({item["party"] for item in actions.values()})
    for party in parties:
        counts = {"Yea": 0, "Nay": 0}
        for item in actions.values():
            if item["party"] == party and item["action"] in counts:
                counts[item["action"]] += 1
        result[party] = max(counts, key=counts.get) if counts["Yea"] != counts["Nay"] else None
    return result


def _short_name(member: dict) -> str:
    formal = member.get("formal_name", "")
    for prefix in ("Mr. ", "Mrs. ", "Ms. ", "Miss ", "Dr. "):
        if formal.startswith(prefix):
            return formal[len(prefix):]
    return member["display_name"]


def _action_word(action: str) -> str:
    return {"Yea": "supported", "Nay": "opposed", "Not Voting": "did not vote on", "Present": "voted Present on"}[action]


def _coverage(actions: list[str]) -> str:
    yes_no = sum(action in {"Yea", "Nay"} for action in actions)
    if yes_no == len(actions):
        return "complete"
    return "partial" if yes_no else "missing"


def _base_trajectory(episode_id: str, actions_by_roll: dict[int, str]) -> dict:
    rolls = EPISODE_ROLLS[episode_id]
    actions = [actions_by_roll[roll] for roll in rolls]
    coverage = _coverage(actions)
    if episode_id == "halt-fentanyl-legislative-path":
        member_trajectory = (
            f"{_action_word(actions[0]).capitalize()} the certification condition, "
            f"{_action_word(actions[1])} the earlier House framework, and "
            f"{_action_word(actions[2])} the later permanent framework."
        )
        practical = "The three stages remain one fentanyl policy episode; the action sequence is " + "/".join(actions) + "."
    else:
        descriptions = {
            "retired-service-weapon-purchases": "the reviewed retired-service-firearm purchase program",
            "officer-safety-data-reporting": "the reviewed officer-safety and wellness reporting bill",
            "dc-police-pursuit-rules": "the reviewed expansion of D.C. police-pursuit authority",
            "dc-policing-reform-repeal": "the reviewed repeal of most D.C. policing safeguards",
        }
        member_trajectory = f"{_action_word(actions[0]).capitalize()} {descriptions[episode_id]}."
        practical = member_trajectory
    return {
        "episode_id": episode_id,
        "rolls": list(rolls),
        "action_signature": actions,
        "coverage_status": coverage,
        "member_trajectory": member_trajectory,
        "practical_policy_direction": practical,
        "candidate_theme_tags": [],
        "theme_evidence": [],
        "contrary_or_limiting_evidence": [],
        "package_vote_limitations": [],
        "notable_one_off": False,
    }


def _select_pattern(actions: dict[int, str]) -> str:
    # These conditions use episode-specific actions only. Member identity and party
    # are intentionally unavailable to this decision function.
    vector = tuple(actions[roll] for roll in SUBSTANTIVE_ROLLS)
    if vector == ("Yea", "Nay", "Nay", "Yea", "Yea", "Nay", "Nay"):
        return "conditional_guardrail_boundary"
    if vector == ("Nay", "Yea", "Yea", "Yea", "Yea", "Yea", "Yea"):
        return "enforcement_expansion"
    if vector == ("Nay", "Nay", "Yea", "Yea", "Nay", "Yea", "Yea"):
        return "police_authority_fentanyl_divide"
    if vector == ("Nay", "Yea", "Yea", "Yea", "Yea", "Nay", "Nay"):
        return "national_action_dc_boundary"
    if vector == ("Nay", "Nay", "Nay", "Nay", "Nay", "Nay", "Nay"):
        return "cross_mechanism_opposition"
    if vector == ("Yea", "Yea", "Yea", "Yea", "Yea", "Yea", "Nay"):
        return "broad_support_safeguard_exception"
    return "contested_mixed_record"


def _pattern_spec(pattern: str, member: dict) -> dict:
    name = _short_name(member)
    common = {
        "reviewed_period": REVIEWED_PERIOD,
        "human_review_status": "human_approval_pending",
        "future_expansion_rule": "Recompute from expanded member actions and shared episode annotations; new independent episodes may strengthen, narrow, contest, or replace this candidate.",
        "minimum_independent_episodes": 3,
        "insufficient_evidence_conclusion": f"The reviewed record for {name} does not cover enough independent episodes to support a cross-episode conclusion.",
        "insufficient_evidence_reason": "Fewer than three independent episodes have complete Yes/No coverage.",
        "global_limitations": ["This conclusion is bounded to five researched episodes and does not infer motive, ideology, or future behavior."],
        "weakening_episodes": {},
        "notable_episodes": (),
    }
    specs = {
        "conditional_guardrail_boundary": {
            "candidate_id": "conditional-guardrail-boundary",
            "inference_level": "bounded_selective_pattern",
            "evidence_strength_label": "Bounded selective pattern",
            "primary_conclusion": f"In this reviewed sample, {name} supported reporting, a fentanyl certification condition, and the later permanent fentanyl framework while opposing the earlier framework and three proposals involving police tools, operational authority, or safeguard rollbacks. Across these episodes, the record supports a selective boundary around enforcement expansion rather than blanket support or opposition.",
            "why_conclusion_does_not_go_further": "The five episodes show a repeated boundary, but they do not establish a comprehensive Justice philosophy or explain why the actions differed.",
            "themes": {
                "guardrail-and-information-actions": ("Evidence and information conditions", "Supported evidence, research, or reporting mechanisms across the fentanyl and officer-reporting episodes."),
                "limits-on-tools-authority-and-rollbacks": ("Limits on tools, authority, and safeguard rollbacks", "Opposed reviewed expansions or rollbacks across the firearm, pursuit, and policing-safeguard episodes."),
            },
            "theme_membership": {
                "halt-fentanyl-legislative-path": ("guardrail-and-information-actions",),
                "officer-safety-data-reporting": ("guardrail-and-information-actions",),
                "retired-service-weapon-purchases": ("limits-on-tools-authority-and-rollbacks",),
                "dc-police-pursuit-rules": ("limits-on-tools-authority-and-rollbacks",),
                "dc-policing-reform-repeal": ("limits-on-tools-authority-and-rollbacks",),
            },
        },
        "enforcement_expansion": {
            "candidate_id": "reviewed-enforcement-expansion",
            "inference_level": "bounded_repeated_pattern",
            "evidence_strength_label": "Strong reviewed sample",
            "primary_conclusion": f"In this reviewed sample, {name} supported both permanent fentanyl frameworks, the retired-service-firearm program, broader D.C. pursuit authority, repeal of most reviewed D.C. policing safeguards, and officer-safety reporting, while opposing the fentanyl certification condition. The repeated record favors the reviewed expansions and permanent enforcement mechanisms, with reporting support but no opposing final-passage action in these five episodes.",
            "why_conclusion_does_not_go_further": "This describes concrete mechanisms in five episodes; it does not establish a broad ideology, motive, or position on every public-safety policy.",
            "themes": {
                "support-for-reviewed-enforcement-mechanisms": ("Support for reviewed enforcement mechanisms", "Supported permanent fentanyl rules and reviewed police-tool or authority expansions across distinct mechanisms."),
            },
            "theme_membership": {
                "halt-fentanyl-legislative-path": ("support-for-reviewed-enforcement-mechanisms",),
                "retired-service-weapon-purchases": ("support-for-reviewed-enforcement-mechanisms",),
                "dc-police-pursuit-rules": ("support-for-reviewed-enforcement-mechanisms",),
                "dc-policing-reform-repeal": ("support-for-reviewed-enforcement-mechanisms",),
            },
        },
        "police_authority_fentanyl_divide": {
            "candidate_id": "police-authority-fentanyl-divide",
            "inference_level": "bounded_conditional_boundary",
            "evidence_strength_label": "Mixed but interpretable",
            "primary_conclusion": f"In this reviewed sample, {name} supported the retired-service-firearm program, broader D.C. pursuit authority, repeal of most reviewed D.C. policing safeguards, and officer-safety reporting, while opposing the certification condition and both permanent fentanyl frameworks. The record draws a policy-specific divide between the reviewed police tool and authority proposals and the fentanyl scheduling episode.",
            "why_conclusion_does_not_go_further": "The fentanyl opposition is one independent episode despite three stages, so the sample does not support a broader claim about drug enforcement or public safety overall.",
            "themes": {
                "support-for-police-tools-and-authority": ("Support for reviewed police tools and authority", "Supported reviewed police-tool, pursuit-authority, and safeguard-repeal proposals across three distinct mechanisms."),
                "opposition-within-fentanyl-episode": ("Opposition within the fentanyl episode", "Opposed the certification condition and both permanent frameworks within the single reviewed fentanyl episode."),
            },
            "theme_membership": {
                "halt-fentanyl-legislative-path": ("opposition-within-fentanyl-episode",),
                "retired-service-weapon-purchases": ("support-for-police-tools-and-authority",),
                "dc-police-pursuit-rules": ("support-for-police-tools-and-authority",),
                "dc-policing-reform-repeal": ("support-for-police-tools-and-authority",),
            },
            "notable_episodes": ("officer-safety-data-reporting",),
        },
        "national_action_dc_boundary": {
            "candidate_id": "national-action-dc-boundary",
            "inference_level": "bounded_conditional_boundary",
            "evidence_strength_label": "Mixed but interpretable",
            "primary_conclusion": f"In this reviewed sample, {name} supported both permanent fentanyl frameworks, the retired-service-firearm program, and officer-safety reporting while opposing broader D.C. pursuit authority and repeal of most reviewed D.C. policing safeguards. The record supports several national public-safety mechanisms but sets a repeated boundary at the two reviewed D.C. policing changes.",
            "why_conclusion_does_not_go_further": "The two D.C. votes cover different mechanisms but one jurisdictional setting, so the record does not establish opposition to police authority generally.",
            "themes": {
                "support-for-national-mechanisms": ("Support for reviewed national mechanisms", "Supported permanent fentanyl rules, reporting, and a retired-service-firearm program across distinct mechanisms."),
                "opposition-to-reviewed-dc-changes": ("Opposition to reviewed D.C. policing changes", "Opposed both broader pursuit authority and repeal of most reviewed policing safeguards in D.C."),
            },
            "theme_membership": {
                "halt-fentanyl-legislative-path": ("support-for-national-mechanisms",),
                "retired-service-weapon-purchases": ("support-for-national-mechanisms",),
                "officer-safety-data-reporting": ("support-for-national-mechanisms",),
                "dc-police-pursuit-rules": ("opposition-to-reviewed-dc-changes",),
                "dc-policing-reform-repeal": ("opposition-to-reviewed-dc-changes",),
            },
        },
        "cross_mechanism_opposition": {
            "candidate_id": "cross-mechanism-opposition",
            "inference_level": "bounded_repeated_pattern",
            "evidence_strength_label": "Strong reviewed sample",
            "primary_conclusion": f"In this reviewed sample, {name} opposed every reviewed action: the fentanyl certification condition and both permanent frameworks, the retired-service-firearm program, officer-safety reporting, broader D.C. pursuit authority, and repeal of most reviewed D.C. policing safeguards. The actions form a repeated cross-mechanism pattern of opposition in this sample, but the vote record alone does not identify a common rationale.",
            "why_conclusion_does_not_go_further": "One-directional actions across five episodes do not by themselves establish an ideology, motive, or opposition to the policy goals named in the measures.",
            "themes": {
                "opposition-across-reviewed-mechanisms": ("Opposition across reviewed mechanisms", "Opposed reviewed proposals across scheduling, firearm access, reporting, pursuit authority, and safeguard repeal mechanisms."),
            },
            "theme_membership": {episode_id: ("opposition-across-reviewed-mechanisms",) for episode_id in EPISODE_ROLLS},
        },
        "broad_support_safeguard_exception": {
            "candidate_id": "broad-support-safeguard-exception",
            "inference_level": "bounded_repeated_pattern",
            "evidence_strength_label": "Strong reviewed sample with contrary evidence",
            "primary_conclusion": f"In this reviewed sample, {name} supported the fentanyl certification condition and both permanent frameworks, the retired-service-firearm program, officer-safety reporting, and broader D.C. pursuit authority, while opposing repeal of most reviewed D.C. policing safeguards. The record mostly supports the reviewed public-safety actions but preserves a specific boundary around the safeguard-repeal proposal.",
            "why_conclusion_does_not_go_further": "The single contrary episode is material, and five episodes cannot establish blanket support for enforcement or a comprehensive Justice philosophy.",
            "themes": {
                "support-across-reviewed-mechanisms": ("Support across reviewed mechanisms", "Supported reviewed action across fentanyl, firearm access, reporting, and pursuit-authority mechanisms."),
            },
            "theme_membership": {
                "halt-fentanyl-legislative-path": ("support-across-reviewed-mechanisms",),
                "retired-service-weapon-purchases": ("support-across-reviewed-mechanisms",),
                "officer-safety-data-reporting": ("support-across-reviewed-mechanisms",),
                "dc-police-pursuit-rules": ("support-across-reviewed-mechanisms",),
            },
            "weakening_episodes": {
                "dc-policing-reform-repeal": "Opposition to repealing most reviewed D.C. policing safeguards is material contrary evidence against blanket support across the sample.",
            },
            "notable_episodes": ("dc-policing-reform-repeal",),
        },
        "contested_mixed_record": {
            "candidate_id": "contested-mixed-record",
            "inference_level": "contested_candidate",
            "evidence_strength_label": "Mixed reviewed evidence",
            "primary_conclusion": f"The reviewed actions for {name} are mixed across the five episodes and do not yet establish a repeated cross-episode boundary.",
            "why_conclusion_does_not_go_further": "No proposed theme has enough independent, mechanism-diverse support in the current overlay.",
            "themes": {},
            "theme_membership": {},
        },
    }
    return {**common, **deepcopy(specs[pattern])}


def _apply_candidate_evidence(trajectories: list[dict], conclusion: dict) -> list[dict]:
    theme_membership = conclusion.pop("theme_membership")
    themes = conclusion.pop("themes")
    weakening_episodes = conclusion.pop("weakening_episodes", {})
    notable_episodes = set(conclusion.pop("notable_episodes", ()))
    conclusion["theme_candidates"] = [
        {
            "theme_id": theme_id,
            "label": label,
            "finding": finding,
            "editorially_defensible": True,
            "minimum_mechanism_diversity": 2,
        }
        for theme_id, (label, finding) in themes.items()
    ]
    candidate_id = conclusion["candidate_id"]
    result = []
    for trajectory in trajectories:
        item = deepcopy(trajectory)
        memberships = theme_membership.get(item["episode_id"], ())
        item["candidate_theme_tags"] = list(memberships)
        item["theme_evidence"] = [
            {"theme_id": theme_id, "rationale": f"This member-specific trajectory supplies episode-level evidence for {themes[theme_id][0].lower()}."}
            for theme_id in memberships
        ]
        weakens = item["episode_id"] in weakening_episodes
        direction = "weakens" if weakens else "strengthens" if memberships else "neutral"
        weight = 2 if memberships or weakens else 0
        if weakens:
            item["contrary_or_limiting_evidence"].append(weakening_episodes[item["episode_id"]])
        item["notable_one_off"] = item["episode_id"] in notable_episodes
        item["conclusion_effect"] = {
            "candidate_id": candidate_id,
            "direction": direction,
            "weight": weight,
            "rationale": weakening_episodes[item["episode_id"]] if weakens else "The member-specific episode trajectory supports this candidate." if memberships else "This episode is retained as relevant context but is not load-bearing for this candidate.",
        }
        result.append(item)
    return result


def _build_overlay(member: dict, actions_by_roll: dict[int, str], roll_metadata: dict[int, dict], majorities: dict[int, dict]) -> tuple[dict, dict]:
    trajectories = [_base_trajectory(episode_id, actions_by_roll) for episode_id in EPISODE_ROLLS]
    pattern = _select_pattern(actions_by_roll)
    conclusion = _pattern_spec(pattern, member)
    trajectories = _apply_candidate_evidence(trajectories, conclusion)
    roll_actions = []
    for roll in (*SUBSTANTIVE_ROLLS, *CONTROL_ROLLS):
        action = actions_by_roll[roll]
        party_majority = majorities[roll].get(member["party"])
        roll_actions.append({
            "roll": roll,
            "action": action,
            "counting": roll in SUBSTANTIVE_ROLLS,
            "episode_id": next((episode_id for episode_id, rolls in EPISODE_ROLLS.items() if roll in rolls), None),
            "party_majority_action": party_majority,
            "aligned_with_party_majority": action == party_majority if action in {"Yea", "Nay"} and party_majority else None,
            "source_id": f"clerk_roll_{roll:03d}",
        })
    overlay = build_member_overlay(
        member=member,
        reviewed_period=REVIEWED_PERIOD,
        shared_episode_set=SHARED_SET,
        roll_actions=roll_actions,
        episode_trajectories=trajectories,
        publication=PUBLICATION,
    )
    overlay["validation_case"] = SELECTED[member["bioguide_id"]][0]
    overlay["selection_rationale"] = SELECTED[member["bioguide_id"]][1]
    overlay["candidate_pattern"] = pattern
    return overlay, conclusion


def build(source_dir: Path) -> dict[str, object]:
    members = _load_member_directory(source_dir / "members.xml")
    roll_metadata = {}
    roll_actions = {}
    majorities = {}
    for roll in (*SUBSTANTIVE_ROLLS, *CONTROL_ROLLS):
        metadata, actions = _load_roll(source_dir / f"roll{roll:03d}.xml")
        roll_metadata[roll] = metadata
        roll_actions[roll] = actions
        majorities[roll] = _party_majorities(actions)

    all_member_ids = sorted({identifier for roll in SUBSTANTIVE_ROLLS for identifier in roll_actions[roll]})
    considered = []
    for identifier in all_member_ids:
        actions = [roll_actions[roll].get(identifier, {}).get("action", "Missing") for roll in SUBSTANTIVE_ROLLS]
        directory = members.get(identifier, {})
        fallback = next((roll_actions[roll][identifier] for roll in SUBSTANTIVE_ROLLS if identifier in roll_actions[roll]), {})
        considered.append({
            "bioguide_id": identifier,
            "display_name": directory.get("display_name") or fallback.get("fallback_name"),
            "party": directory.get("party") or fallback.get("party"),
            "state": directory.get("state") or fallback.get("state"),
            "vote_vector": actions,
            "yes_no_coverage": sum(action in {"Yea", "Nay"} for action in actions),
            "selected": identifier in SELECTED,
            "exclusion_reason": None if identifier in SELECTED else "Not needed after the small cohort covered the targeted completeness and vote-vector variation cases.",
        })

    shared_map = json.loads((ROOT / SHARED_SET["episode_map_path"]).read_text(encoding="utf-8"))
    overlays = []
    inferences = []
    conclusions = {}
    for identifier in SELECTED:
        member = members[identifier]
        actions_by_roll = {
            roll: roll_actions[roll][identifier]["action"]
            for roll in (*SUBSTANTIVE_ROLLS, *CONTROL_ROLLS)
        }
        overlay, conclusion = _build_overlay(member, actions_by_roll, roll_metadata, majorities)
        inference = build_member_inference(overlay=overlay, shared_episodes=shared_map["episodes"], conclusion=conclusion)
        inference["publication"] = deepcopy(PUBLICATION)
        overlays.append(overlay)
        inferences.append(inference)
        conclusions[identifier] = conclusion

    selection = {
        "schema_version": "justice_cross_member_cohort_selection_v1",
        "source_retrieved_on": "2026-07-21",
        "selection_inputs": ["vote completeness", "episode-level action differences", "within-episode trajectory differences", "diversity of observed vote vectors", "validation usefulness"],
        "excluded_inputs": ["party as a score", "ideology scores", "reputation", "fame", "caucus labels", "campaign statements", "external ratings"],
        "roll_order": list(SUBSTANTIVE_ROLLS),
        "eligible_definition": "Appeared in at least one reviewed substantive roll; yes_no_coverage records completeness.",
        "tie_break_rule": "After selecting a vector for methodological value, use the lowest Bioguide ID within that vector unless the reference member is required.",
        "counts": {
            "all_considered": len(considered),
            "complete_yes_no": sum(item["yes_no_coverage"] == len(SUBSTANTIVE_ROLLS) for item in considered),
            "selected": len(SELECTED),
        },
        "members_considered": considered,
    }
    sources = {
        "schema_version": "justice_cross_member_official_action_sources_v1",
        "source_retrieved_on": "2026-07-21",
        "rolls": [
            {**roll_metadata[roll], "party_majority_actions": majorities[roll], "counting": roll in SUBSTANTIVE_ROLLS}
            for roll in (*SUBSTANTIVE_ROLLS, *CONTROL_ROLLS)
        ],
    }
    comparison = _comparison(overlays, inferences)
    return {
        "cohort_selection.json": selection,
        "official_action_sources.json": sources,
        "member_overlays.json": {"schema_version": "justice_cross_member_overlays_v1", "publication": PUBLICATION, "overlays": overlays},
        "inference_candidates.json": {"schema_version": "justice_cross_member_inferences_v1", "publication": PUBLICATION, "candidates": inferences},
        "comparison_matrix.json": comparison,
    }


def _comparison(overlays: list[dict], inferences: list[dict]) -> dict:
    inference_by_member = {item["member"]["bioguide_id"]: item for item in inferences}
    members = []
    themes = {}
    theme_review_rows = []
    for overlay in overlays:
        identifier = overlay["member"]["bioguide_id"]
        inference = inference_by_member[identifier]
        actions = {item["roll"]: item["action"] for item in overlay["roll_actions"]}
        members.append({
            "member": overlay["member"],
            "validation_case": overlay["validation_case"],
            "vote_vector": [actions[roll] for roll in SUBSTANTIVE_ROLLS],
            "episode_trajectories": [{"episode_id": item["episode_id"], "action_signature": item["action_signature"], "member_trajectory": item["member_trajectory"]} for item in overlay["episode_trajectories"]],
            "coverage": overlay["coverage"],
            "assessment": inference["assessment"],
            "evidence_strength_label": inference["evidence_strength_label"],
            "primary_conclusion": inference["primary_conclusion"],
            "repeated_themes": inference.get("repeated_cross_episode_themes", []),
            "notable_one_offs": inference.get("notable_one_off_choices", []),
            "contrary_evidence": inference.get("contrary_or_limiting_evidence", []),
            "party_alignment": [{"roll": item["roll"], "aligned": item.get("aligned_with_party_majority")} for item in overlay["roll_actions"] if item["counting"]],
            "publication": overlay["publication"],
        })
        theme_review_rows.append({
            "member_id": identifier,
            "candidate_id": inference["candidate_id"],
            "proposed_themes": [item["theme_id"] for item in inference.get("repeated_cross_episode_themes", [])],
            "episode_effects": [
                {
                    "episode_id": trajectory["episode_id"],
                    "effect": trajectory["conclusion_effect"]["direction"],
                    "weight": trajectory["conclusion_effect"]["weight"],
                }
                for trajectory in overlay["episode_trajectories"]
            ],
        })
        for trajectory in overlay["episode_trajectories"]:
            for evidence in trajectory.get("theme_evidence", []):
                themes.setdefault(evidence["theme_id"], {}).setdefault(identifier, []).append({"episode_id": trajectory["episode_id"], "effect": trajectory["conclusion_effect"]["direction"]})
    return {
        "schema_version": "justice_cross_member_comparison_v1",
        "not_a_ranking": True,
        "roll_order": list(SUBSTANTIVE_ROLLS),
        "shared_episode_set": SHARED_SET,
        "members": members,
        "theme_by_member": themes,
        "candidate_theme_review_matrix": theme_review_rows,
        "publication": PUBLICATION,
    }


def _serialize(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def _frontend_module(outputs: dict[str, object]) -> str:
    payload = {
        "overlays": outputs["member_overlays.json"]["overlays"],
        "inferences": outputs["inference_candidates.json"]["candidates"],
    }
    return (
        "// Generated by backend/scripts/build_justice_cross_member_validation.py.\n"
        "// Review-only member-varying data; shared measure facts remain in the PR #95 source.\n"
        f"export const justiceCrossMemberValidationData = Object.freeze({json.dumps(payload, indent=2, ensure_ascii=False)});\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=ROOT / "_analysis_house_votes")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/editorial/justice_cross_member_validation_v1")
    parser.add_argument("--frontend-output", type=Path, default=ROOT / "frontend/lib/justiceCrossMemberValidationData.mjs")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build(args.source_dir)
    if args.check:
        mismatches = [name for name, value in outputs.items() if not (args.output_dir / name).exists() or (args.output_dir / name).read_text(encoding="utf-8") != _serialize(value)]
        if not args.frontend_output.exists() or args.frontend_output.read_text(encoding="utf-8") != _frontend_module(outputs):
            mismatches.append(args.frontend_output.name)
        if mismatches:
            raise SystemExit("generated artifacts differ: " + ", ".join(mismatches))
        print("Justice cross-member artifacts are deterministic.")
        return 0
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in outputs.items():
        (args.output_dir / name).write_text(_serialize(value), encoding="utf-8")
    args.frontend_output.parent.mkdir(parents=True, exist_ok=True)
    args.frontend_output.write_text(_frontend_module(outputs), encoding="utf-8")
    print(f"Wrote {len(outputs)} review artifacts and {args.frontend_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
