"""Build review-only Justice cross-member evidence from official recorded actions."""

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

from backend.app.summaries.editorial_candidate_evaluation import evaluate_candidates
from backend.app.summaries.editorial_member_overlay import build_member_overlay

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
    "episode_set_id": "justice-public-safety-pr95-five-episodes", "version": "1.1.0",
    "episode_map_path": "docs/editorial/valerie_foushee_justice_public_safety_gold_v1/policy_episode_map.json",
    "expected_substantive_roll_ids": list(SUBSTANTIVE_ROLLS),
    "expected_control_roll_ids": list(CONTROL_ROLLS),
    "expected_independent_episode_ids": list(EPISODE_ROLLS),
    "episode_rolls": {key: list(value) for key, value in EPISODE_ROLLS.items()},
}
PUBLICATION = {"editorial_status": "human_approval_pending", "benchmark_status": "not_promoted", "production_eligible": False}
REVIEWED_PERIOD = "119th Congress, February 6-November 19, 2025"
SELECTED = {
    "F000477": ("reference_action_structure", "Reference action structure researched in PR #95."),
    "A000370": ("equivalent_action_structure", "Exact substantive action match tests structurally equivalent treatment."),
    "A000055": ("dominant_action_contrast", "Complete actions contrast with the reference on six of seven rolls and represent the most common complete action structure."),
    "M001184": ("fentanyl_police_action_split", "A distinct complete action structure separates the fentanyl episode from police-tool and authority episodes."),
    "B000490": ("national_dc_action_boundary", "Complete actions support both permanent fentanyl stages while opposing both D.C. proposals."),
    "G000586": ("cross_mechanism_opposition", "The all-Nay complete action structure tests one-directional actions without turning them into an ideology label."),
    "M001217": ("broad_support_with_exception", "The mostly-Yea complete action structure tests whether one safeguard-repeal opposition remains visible as contrary evidence."),
}

THEME_CATALOG = {
    "evidence-and-reporting-conditions": {"label": "Evidence and reporting conditions", "finding": "Supported evidence, certification, or reporting conditions across distinct episodes."},
    "limits-on-tools-authority-and-rollbacks": {"label": "Limits on tools, authority, and safeguard rollbacks", "finding": "Opposed reviewed tool or authority expansions and safeguard rollbacks."},
    "reviewed-enforcement-expansion": {"label": "Reviewed enforcement expansion", "finding": "Supported reviewed permanent enforcement, police-tool, or authority expansions."},
    "police-tools-and-authority": {"label": "Police tools and authority", "finding": "Supported reviewed police-tool and authority proposals."},
    "fentanyl-episode-opposition": {"label": "Fentanyl episode opposition", "finding": "Opposed all three actions within the single fentanyl episode."},
    "national-public-safety-mechanisms": {"label": "National public-safety mechanisms", "finding": "Supported reviewed national mechanisms across distinct policy tools."},
    "dc-policing-change-opposition": {"label": "D.C. policing change opposition", "finding": "Opposed both reviewed D.C. policing changes."},
    "cross-mechanism-opposition": {"label": "Cross-mechanism opposition", "finding": "Opposed reviewed actions across distinct mechanisms."},
    "cross-mechanism-support": {"label": "Cross-mechanism support", "finding": "Supported reviewed actions across distinct mechanisms."},
    "safeguard-repeal-opposition": {"label": "Safeguard-repeal opposition", "finding": "Opposed the reviewed repeal of most D.C. policing safeguards."},
}

CANDIDATE_CATALOG = [
    {"candidate_id": "conditional-guardrail-boundary", "inference_level": "bounded_selective_pattern", "evidence_strength_label": "Bounded selective pattern",
     "conclusion": "a selective boundary: support for evidence or reporting conditions alongside repeated limits on reviewed tool, authority, and safeguard changes",
     "why": "Five episodes establish a bounded pattern but do not explain motive or a comprehensive Justice philosophy.",
     "required_themes": [{"theme_id": "evidence-and-reporting-conditions", "minimum_episodes": 2, "minimum_mechanisms": 2}, {"theme_id": "limits-on-tools-authority-and-rollbacks", "minimum_episodes": 3, "minimum_mechanisms": 3}], "conflicting_themes": []},
    {"candidate_id": "reviewed-enforcement-expansion", "inference_level": "bounded_repeated_pattern", "evidence_strength_label": "Strong reviewed sample",
     "conclusion": "repeated support for the reviewed enforcement, police-tool, and authority expansions",
     "why": "The finding is limited to concrete mechanisms in five episodes and does not establish ideology or motive.",
     "required_themes": [{"theme_id": "reviewed-enforcement-expansion", "minimum_episodes": 4, "minimum_mechanisms": 4}], "conflicting_themes": ["limits-on-tools-authority-and-rollbacks"]},
    {"candidate_id": "police-authority-fentanyl-divide", "inference_level": "bounded_conditional_boundary", "evidence_strength_label": "Mixed but interpretable",
     "conclusion": "a policy-specific divide between support for reviewed police tools or authority and opposition within the fentanyl scheduling episode",
     "why": "The three fentanyl actions are one independent episode, so they cannot establish a broader drug-enforcement pattern.",
     "required_themes": [{"theme_id": "police-tools-and-authority", "minimum_episodes": 3, "minimum_mechanisms": 3}, {"theme_id": "fentanyl-episode-opposition", "minimum_episodes": 1, "minimum_mechanisms": 1}], "conflicting_themes": []},
    {"candidate_id": "national-action-dc-boundary", "inference_level": "bounded_conditional_boundary", "evidence_strength_label": "Mixed but interpretable",
     "conclusion": "support for several reviewed national public-safety mechanisms with a repeated boundary at the two reviewed D.C. policing changes",
     "why": "The two D.C. votes cover different mechanisms but one jurisdictional setting.",
     "required_themes": [{"theme_id": "national-public-safety-mechanisms", "minimum_episodes": 3, "minimum_mechanisms": 3}, {"theme_id": "dc-policing-change-opposition", "minimum_episodes": 2, "minimum_mechanisms": 2}], "conflicting_themes": []},
    {"candidate_id": "cross-mechanism-opposition", "inference_level": "bounded_repeated_pattern", "evidence_strength_label": "Strong reviewed sample",
     "conclusion": "a repeated cross-mechanism pattern of opposition across the reviewed policy mechanisms",
     "why": "One-directional actions do not identify a common rationale, ideology, or motive.",
     "required_themes": [{"theme_id": "cross-mechanism-opposition", "minimum_episodes": 5, "minimum_mechanisms": 5}], "conflicting_themes": []},
    {"candidate_id": "broad-support-safeguard-exception", "inference_level": "bounded_repeated_pattern", "evidence_strength_label": "Strong reviewed sample with contrary evidence",
     "conclusion": "broad support for the reviewed public-safety actions with a specific boundary around the safeguard-repeal proposal",
     "why": "The contrary episode is material, and five episodes cannot establish blanket support or a comprehensive Justice philosophy.",
     "required_themes": [{"theme_id": "cross-mechanism-support", "minimum_episodes": 4, "minimum_mechanisms": 4}, {"theme_id": "evidence-and-reporting-conditions", "minimum_episodes": 2, "minimum_mechanisms": 2}], "conflicting_themes": ["safeguard-repeal-opposition"]},
]


def _evidence(*theme_ids: str) -> list[dict]:
    return [{"theme_id": theme_id, "rationale": THEME_CATALOG[theme_id]["finding"]} for theme_id in theme_ids]


def _single_catalog(mechanism: str, description: str, yea_themes: tuple[str, ...], nay_themes: tuple[str, ...]) -> dict:
    def row(action: str, themes=()) -> dict:
        verb = {"Yea": "Supported", "Nay": "Opposed", "Present": "Voted Present on", "Not Voting": "Did not vote on", "missing": "No recorded action was supplied for"}[action]
        text = f"{verb} {description}."
        return {"member_trajectory": text, "practical_policy_direction": text, "theme_evidence": _evidence(*themes)}
    return {"mechanism_family": mechanism, "signatures": {"Yea": row("Yea", yea_themes), "Nay": row("Nay", nay_themes), "Present": row("Present"), "Not Voting": row("Not Voting"), "missing": row("missing")}, "non_counting": row("missing")}


EPISODE_ACTION_INTERPRETATIONS = {
    "retired-service-weapon-purchases": _single_catalog("firearm-access", "the reviewed retired-service-firearm purchase program", ("reviewed-enforcement-expansion", "police-tools-and-authority", "national-public-safety-mechanisms", "cross-mechanism-support"), ("limits-on-tools-authority-and-rollbacks", "cross-mechanism-opposition")),
    "officer-safety-data-reporting": _single_catalog("data-reporting", "the reviewed officer-safety and wellness reporting bill", ("evidence-and-reporting-conditions", "national-public-safety-mechanisms", "cross-mechanism-support"), ("cross-mechanism-opposition",)),
    "dc-police-pursuit-rules": _single_catalog("pursuit-authority", "the reviewed expansion of D.C. police-pursuit authority", ("reviewed-enforcement-expansion", "police-tools-and-authority", "cross-mechanism-support"), ("limits-on-tools-authority-and-rollbacks", "dc-policing-change-opposition", "cross-mechanism-opposition")),
    "dc-policing-reform-repeal": _single_catalog("safeguard-repeal", "the reviewed repeal of most D.C. policing safeguards", ("reviewed-enforcement-expansion", "police-tools-and-authority", "cross-mechanism-support"), ("limits-on-tools-authority-and-rollbacks", "dc-policing-change-opposition", "cross-mechanism-opposition", "safeguard-repeal-opposition")),
}


def _fentanyl_row(signature: tuple[str, str, str]) -> dict:
    verbs = {"Yea": "supported", "Nay": "opposed"}
    text = f"{verbs[signature[0]].capitalize()} the certification condition, {verbs[signature[1]]} the earlier House framework, and {verbs[signature[2]]} the later permanent framework."
    themes = []
    if signature[0] == "Yea": themes.append("evidence-and-reporting-conditions")
    if signature[1:] == ("Yea", "Yea"):
        themes.extend(("reviewed-enforcement-expansion", "national-public-safety-mechanisms", "cross-mechanism-support"))
    if signature == ("Nay", "Nay", "Nay"):
        themes.extend(("fentanyl-episode-opposition", "cross-mechanism-opposition"))
    return {"member_trajectory": text, "practical_policy_direction": f"One fentanyl trajectory with action signature {'/'.join(signature)}.", "theme_evidence": _evidence(*themes)}


EPISODE_ACTION_INTERPRETATIONS["halt-fentanyl-legislative-path"] = {
    "mechanism_family": "controlled-substance-scheduling",
    "relationship_to_repeated_stages": "Three related rolls are interpreted as one legislative trajectory and one independent episode.",
    "signatures": {"|".join(signature): _fentanyl_row(signature) for signature in __import__("itertools").product(("Yea", "Nay"), repeat=3)},
    "non_counting": {"member_trajectory": "The fentanyl trajectory is incomplete because at least one stage is Present, Not Voting, or missing.", "practical_policy_direction": "No support or opposition theme is inferred from an incomplete fentanyl signature.", "theme_evidence": []},
}


def _text(element) -> str:
    return (element.text or "").strip() if element is not None else ""


def _load_member_directory(path: Path) -> dict[str, dict]:
    result = {}
    for member in ElementTree.parse(path).getroot().findall("./members/member"):
        info = member.find("member-info")
        if info is None or not _text(info.find("bioguideID")): continue
        state = info.find("state"); identifier = _text(info.find("bioguideID"))
        result[identifier] = {"bioguide_id": identifier, "display_name": _text(info.find("official-name")) or _text(info.find("namelist")), "formal_name": _text(info.find("formal-name")), "party": _text(info.find("party")), "state": state.attrib.get("postal-code") if state is not None else "", "district": _text(info.find("district"))}
    return result


def _normalize_action(value: str) -> str:
    normalized = {"Aye": "Yea", "No": "Nay"}.get(value, value)
    if normalized not in {"Yea", "Nay", "Present", "Not Voting"}: raise ValueError(f"unsupported House recorded action: {value}")
    return normalized


def _load_roll(path: Path) -> tuple[dict, dict[str, dict]]:
    root = ElementTree.parse(path).getroot(); metadata = root.find("vote-metadata")
    if metadata is None: raise ValueError(f"missing vote metadata in {path}")
    roll = int(_text(metadata.find("rollcall-num"))); actions = {}
    for row in root.findall("./vote-data/recorded-vote"):
        legislator = row.find("legislator"); identifier = legislator.attrib.get("name-id") if legislator is not None else None
        if not identifier: raise ValueError(f"missing member identifier in roll {roll}")
        actions[identifier] = {"action": _normalize_action(_text(row.find("vote"))), "fallback_name": legislator.attrib.get("unaccented-name") or _text(legislator), "party": legislator.attrib.get("party", ""), "state": legislator.attrib.get("state", "")}
    return {"roll": roll, "date": _text(metadata.find("action-date")), "source_url": f"https://clerk.house.gov/evs/2025/roll{roll:03d}.xml", "question": _text(metadata.find("vote-question"))}, actions


def _party_majorities(actions: dict[str, dict]) -> dict[str, str | None]:
    result = {}
    for party in sorted({item["party"] for item in actions.values()}):
        counts = {action: sum(item["party"] == party and item["action"] == action for item in actions.values()) for action in ("Yea", "Nay")}
        result[party] = max(counts, key=counts.get) if counts["Yea"] != counts["Nay"] else None
    return result


def build_overlay_from_actions(member: dict, actions_by_roll: dict[int, str], majorities: dict[int, dict] | None = None) -> dict:
    majorities = majorities or {roll: {} for roll in (*SUBSTANTIVE_ROLLS, *CONTROL_ROLLS)}
    rows = []
    for roll, action in actions_by_roll.items():
        expected_episode = next((episode_id for episode_id, rolls in EPISODE_ROLLS.items() if roll in rolls), None)
        party_majority = majorities.get(roll, {}).get(member.get("party"))
        rows.append({"roll": roll, "action": action, "counting": roll in SUBSTANTIVE_ROLLS, "episode_id": expected_episode,
                     "party_majority_action": party_majority, "aligned_with_party_majority": action == party_majority if action in {"Yea", "Nay"} and party_majority else None, "source_id": f"clerk_roll_{roll:03d}"})
    return build_member_overlay(member=member, reviewed_period=REVIEWED_PERIOD, shared_episode_set=SHARED_SET,
                                roll_actions=rows, episode_action_interpretations=EPISODE_ACTION_INTERPRETATIONS, publication=PUBLICATION)


def evaluate_overlay(overlay: dict, shared_episodes: list[dict]) -> dict:
    return evaluate_candidates(overlay=overlay, shared_episodes=shared_episodes, theme_catalog=THEME_CATALOG, candidate_catalog=CANDIDATE_CATALOG)


def build(source_dir: Path) -> dict[str, object]:
    members = _load_member_directory(source_dir / "members.xml"); roll_metadata = {}; roll_actions = {}; majorities = {}
    for roll in (*SUBSTANTIVE_ROLLS, *CONTROL_ROLLS):
        metadata, actions = _load_roll(source_dir / f"roll{roll:03d}.xml"); roll_metadata[roll] = metadata; roll_actions[roll] = actions; majorities[roll] = _party_majorities(actions)
    all_member_ids = sorted({identifier for roll in SUBSTANTIVE_ROLLS for identifier in roll_actions[roll]}); considered = []
    for identifier in all_member_ids:
        actions = [roll_actions[roll].get(identifier, {}).get("action", "Missing") for roll in SUBSTANTIVE_ROLLS]
        directory = members.get(identifier, {}); fallback = next((roll_actions[roll][identifier] for roll in SUBSTANTIVE_ROLLS if identifier in roll_actions[roll]), {})
        considered.append({"bioguide_id": identifier, "display_name": directory.get("display_name") or fallback.get("fallback_name"), "party": directory.get("party") or fallback.get("party"), "state": directory.get("state") or fallback.get("state"), "vote_vector": actions, "yes_no_coverage": sum(action in {"Yea", "Nay"} for action in actions), "selected": identifier in SELECTED, "exclusion_reason": None if identifier in SELECTED else "Not needed after the small cohort covered the targeted completeness and action-structure variation cases."})
    shared_map = json.loads((ROOT / SHARED_SET["episode_map_path"]).read_text(encoding="utf-8")); overlays = []; inferences = []
    for identifier in SELECTED:
        actions_by_roll = {roll: roll_actions[roll][identifier]["action"] for roll in (*SUBSTANTIVE_ROLLS, *CONTROL_ROLLS)}
        overlay = build_overlay_from_actions(members[identifier], actions_by_roll, majorities); overlay["validation_case"], overlay["selection_rationale"] = SELECTED[identifier]
        inference = evaluate_overlay(overlay, shared_map["episodes"]); inference["publication"] = deepcopy(PUBLICATION); overlays.append(overlay); inferences.append(inference)
    selection = {"schema_version": "justice_cross_member_cohort_selection_v1", "source_retrieved_on": "2026-07-21", "selection_inputs": ["action completeness", "episode-level action differences", "within-episode trajectory differences", "diversity of observed action structures", "validation usefulness"], "excluded_inputs": ["party as a score", "ideology scores", "reputation", "fame", "caucus labels", "campaign statements", "external ratings"], "roll_order": list(SUBSTANTIVE_ROLLS), "eligible_definition": "Appeared in at least one reviewed substantive roll; yes_no_coverage records completeness.", "tie_break_rule": "After selecting an action structure for methodological value, use the lowest Bioguide ID within that structure unless the reference member is required.", "counts": {"all_considered": len(considered), "complete_yes_no": sum(item["yes_no_coverage"] == len(SUBSTANTIVE_ROLLS) for item in considered), "selected": len(SELECTED)}, "members_considered": considered}
    sources = {"schema_version": "justice_cross_member_official_action_sources_v1", "source_retrieved_on": "2026-07-21", "rolls": [{**roll_metadata[roll], "party_majority_actions": majorities[roll], "counting": roll in SUBSTANTIVE_ROLLS} for roll in (*SUBSTANTIVE_ROLLS, *CONTROL_ROLLS)]}
    comparison = _comparison(overlays, inferences)
    return {"cohort_selection.json": selection, "official_action_sources.json": sources, "episode_action_interpretations.json": {"schema_version": "justice_episode_action_interpretations_v1", "shared_episode_set": SHARED_SET, "interpretations": EPISODE_ACTION_INTERPRETATIONS}, "candidate_catalog.json": {"schema_version": "justice_candidate_catalog_v1", "themes": THEME_CATALOG, "candidates": CANDIDATE_CATALOG}, "member_overlays.json": {"schema_version": "justice_cross_member_overlays_v2", "publication": PUBLICATION, "overlays": overlays}, "inference_candidates.json": {"schema_version": "justice_cross_member_inferences_v2", "publication": PUBLICATION, "candidates": inferences}, "comparison_matrix.json": comparison}


def _comparison(overlays: list[dict], inferences: list[dict]) -> dict:
    inference_by_member = {item["member"]["bioguide_id"]: item for item in inferences}; members = []; themes = {}; theme_review_rows = []
    for overlay in overlays:
        identifier = overlay["member"]["bioguide_id"]; inference = inference_by_member[identifier]; actions = {item["roll"]: item["action"] for item in overlay["roll_actions"]}
        members.append({"member": overlay["member"], "validation_case": overlay["validation_case"], "vote_vector": [actions[roll] for roll in SUBSTANTIVE_ROLLS], "episode_trajectories": [{"episode_id": item["episode_id"], "action_signature": item["action_signature"], "member_trajectory": item["member_trajectory"]} for item in overlay["episode_trajectories"]], "coverage": overlay["coverage"], "assessment": inference["assessment"], "evidence_strength_label": inference["evidence_strength_label"], "primary_conclusion": inference["primary_conclusion"], "repeated_themes": inference.get("repeated_cross_episode_themes", []), "notable_one_offs": inference.get("notable_one_off_choices", []), "contrary_evidence": inference.get("contrary_or_limiting_evidence", []), "party_alignment": [{"roll": item["roll"], "aligned": item.get("aligned_with_party_majority")} for item in overlay["roll_actions"] if item["counting"]], "publication": overlay["publication"]})
        theme_review_rows.append({"member_id": identifier, "candidate_id": inference["candidate_id"], "proposed_themes": [item["theme_id"] for item in inference.get("repeated_cross_episode_themes", [])], "episode_effects": inference["candidate_evaluation"]})
        for trajectory in overlay["episode_trajectories"]:
            for evidence in trajectory.get("theme_evidence", []): themes.setdefault(evidence["theme_id"], {}).setdefault(identifier, []).append({"episode_id": trajectory["episode_id"]})
    return {"schema_version": "justice_cross_member_comparison_v2", "not_a_ranking": True, "roll_order": list(SUBSTANTIVE_ROLLS), "shared_episode_set": SHARED_SET, "members": members, "theme_by_member": themes, "candidate_theme_review_matrix": theme_review_rows, "publication": PUBLICATION}


def _serialize(value: object) -> str: return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def _frontend_module(outputs: dict[str, object]) -> str:
    payload = {"overlays": outputs["member_overlays.json"]["overlays"], "inferences": outputs["inference_candidates.json"]["candidates"]}
    return "// Generated by backend/scripts/build_justice_cross_member_validation.py.\n// Review-only member-varying data; shared measure facts remain in the PR #95 source.\n" + f"export const justiceCrossMemberValidationData = Object.freeze({json.dumps(payload, indent=2, ensure_ascii=False)});\n"


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--source-dir", type=Path, default=ROOT / "_analysis_house_votes"); parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/editorial/justice_cross_member_validation_v1"); parser.add_argument("--frontend-output", type=Path, default=ROOT / "frontend/lib/justiceCrossMemberValidationData.mjs"); parser.add_argument("--check", action="store_true"); args = parser.parse_args(); outputs = build(args.source_dir)
    if args.check:
        mismatches = [name for name, value in outputs.items() if not (args.output_dir / name).exists() or (args.output_dir / name).read_text(encoding="utf-8") != _serialize(value)]
        if not args.frontend_output.exists() or args.frontend_output.read_text(encoding="utf-8") != _frontend_module(outputs): mismatches.append(args.frontend_output.name)
        if mismatches: raise SystemExit("generated artifacts differ: " + ", ".join(mismatches))
        print("Justice cross-member artifacts are deterministic."); return 0
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in outputs.items(): (args.output_dir / name).write_text(_serialize(value), encoding="utf-8")
    args.frontend_output.parent.mkdir(parents=True, exist_ok=True); args.frontend_output.write_text(_frontend_module(outputs), encoding="utf-8"); print(f"Wrote {len(outputs)} review artifacts and {args.frontend_output}"); return 0


if __name__ == "__main__": raise SystemExit(main())
