"""Build the fail-closed cross-issue domain inventory and selection record."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STARTING_COMMIT = "88d6f3446f54b07735e084cbc958c1614b190fab"
OUTPUT_DIR = ROOT / "docs/editorial/cross_issue_editorial_generality_v1"
JSON_OUTPUT = OUTPUT_DIR / "domain_selection.json"
MARKDOWN_OUTPUT = ROOT / "docs/review_packets/cross_issue_editorial_generality_v1.md"

SOURCE_INVENTORY = [
    "docs/benchmarks/legislative_interpretation_quality_v1.json",
    "docs/interpretation_batches/batch_002_valerie_national_security_packets.json",
    "docs/interpretation_batches/batch_003_valerie_national_security_remaining_packets.json",
    "docs/interpretation_batches/batch_006_valerie_economy_gold_packets_so_what.json",
    "docs/interpretation_batches/batch_008_valerie_justice_packets_so_what.json",
    "docs/interpretation_batches/batch_009_valerie_visible_domains_packets_so_what.json",
]


def action(roll: int, parent_measure: str, action_type: str) -> dict:
    return {"roll": roll, "parent_measure": parent_measure, "action_type": action_type}


def exclusion(action_id: int | str, reason: str) -> dict:
    return {"action_id": action_id, "reason": reason}


CANDIDATES = {
    "EDUCATION_WORKFORCE": {
        "display_name": "Education & Workforce",
        "substantive_actions": [
            action(312, "hr1005", "final_passage"),
            action(314, "hr1049", "final_passage"),
            action(332, "hr2550", "final_passage"),
        ],
        "episodes": ["hr1005-class-act", "hr1049-trace-act", "hr2550-protect-americas-workforce"],
        "multi_action_episode": False,
        "excluded_context": [
            exclusion(276, "motion_to_table_member_discipline_not_a_domain_policy_position"),
            exclusion(308, "rule_or_procedural_control"),
            exclusion(309, "rule_or_procedural_control"),
            exclusion("senate-119-1-358", "senate_action_out_of_scope"),
        ],
        "source_note": "The benchmark contains only two House substantive Education rows; the stored packet inventory adds roll 332, still leaving three actions.",
    },
    "ENVIRONMENT_ENERGY": {
        "display_name": "Environment & Energy",
        "substantive_actions": [action(334, "hr3668", "final_passage")],
        "episodes": ["hr3668-pipeline-reviews"],
        "multi_action_episode": False,
        "excluded_context": [
            exclusion(46, "rule_or_procedural_control"),
            exclusion(47, "rule_or_procedural_control"),
        ],
        "source_note": "Only one stored substantive House action is native to this domain.",
    },
    "HEALTH_SOCIAL": {
        "display_name": "Health & Social Policy",
        "substantive_actions": [
            action(349, "hr6703", "final_passage"),
            action(362, "hr498", "final_passage"),
        ],
        "episodes": ["hr6703-health-care-premiums", "hr498-medicaid-payment-restriction"],
        "multi_action_episode": False,
        "excluded_context": [
            exclusion(343, "rule_or_procedural_control"),
            exclusion(344, "rule_or_procedural_control"),
        ],
        "benchmark_cross_domain_rows": [
            {"roll": 131, "stored_primary_domain": "JUSTICE_PUBLIC_SAFETY", "parent_measure": "hr2240"},
            {"roll": 182, "stored_primary_domain": "ECONOMY_TAXES", "parent_measure": "hr3944"},
            {"roll": 262, "stored_primary_domain": "NATIONAL_SECURITY_FOREIGN", "parent_measure": "hr3838"},
            {"roll": 281, "stored_primary_domain": "ECONOMY_TAXES", "parent_measure": "hr5371"},
            {"roll": 285, "stored_primary_domain": "ECONOMY_TAXES", "parent_measure": "hr5371"},
        ],
        "source_note": "Six benchmark rows carry a Health stratum label, but five belong to other stored primary domains and cannot be repurposed into a new Health ontology.",
    },
    "IMMIGRATION_BORDER": {
        "display_name": "Immigration & Border",
        "substantive_actions": [action(171, "hr2056", "final_passage")],
        "episodes": ["hr2056-dc-immigration-compliance"],
        "multi_action_episode": False,
        "excluded_context": [],
        "source_note": "Only one stored substantive House action is native to this domain.",
    },
    "INFRASTRUCTURE_TECH_TRANSPORT": {
        "display_name": "Infrastructure, Technology & Transportation",
        "substantive_actions": [],
        "episodes": [],
        "multi_action_episode": False,
        "excluded_context": [
            exclusion("senate-119-1-266", "senate_procedural_control"),
            exclusion("senate-119-1-267", "senate_procedural_control"),
            exclusion("senate-119-1-268", "senate_procedural_control"),
            exclusion("senate-119-1-269", "senate_procedural_control"),
        ],
        "source_note": "The benchmark inventory is Senate-only and procedural-dominated for this domain.",
    },
    "NATIONAL_SECURITY_FOREIGN": {
        "display_name": "National Security & Foreign Policy",
        "substantive_actions": [
            *[action(roll, "hr3838", "amendment") for roll in range(244, 261)],
            action(262, "hr3838", "final_passage"),
            action(319, "s1071", "motion_to_commit"),
            action(320, "s1071", "final_passage"),
        ],
        "episodes": ["hr3838-ndaa-fy2026", "s1071-cota-disinterment"],
        "multi_action_episode": True,
        "excluded_context": [
            exclusion(242, "rule_or_procedural_control"),
            exclusion(243, "rule_or_procedural_control"),
        ],
        "source_note": "The stored actions are numerous but collapse to two Congress-bounded parent-measure episodes; no five- or six-action subset can supply three independent episodes.",
    },
}


def build() -> dict:
    candidates = []
    for domain_id in sorted(CANDIDATES):
        raw = CANDIDATES[domain_id]
        actions = raw["substantive_actions"]
        episodes = raw["episodes"]
        action_types = sorted({item["action_type"] for item in actions})
        eligible_action_count = len(actions)
        episode_count = len(episodes)
        exclusion_reasons = []
        if eligible_action_count < 5:
            exclusion_reasons.append("fewer_than_five_suitable_substantive_house_actions")
        if episode_count < 3:
            exclusion_reasons.append("fewer_than_three_independent_policy_episodes")
        if not raw["multi_action_episode"]:
            exclusion_reasons.append("no_multi_action_episode")
        if domain_id == "NATIONAL_SECURITY_FOREIGN":
            exclusion_reasons.append("five_or_six_action_subset_cannot_span_three_independent_episodes")
        if domain_id == "HEALTH_SOCIAL":
            exclusion_reasons.append("benchmark_stratum_rows_cannot_replace_native_domain_identity")
        if domain_id == "INFRASTRUCTURE_TECH_TRANSPORT":
            exclusion_reasons.append("house_inventory_is_synthetic_or_procedural_only")

        components = {
            "official_source_completeness": 2 if actions else 0,
            "member_action_source_availability": 2 if actions else 0,
            "five_or_six_action_feasibility": 2 if eligible_action_count >= 5 else 0,
            "three_to_five_episode_feasibility": 2 if 3 <= episode_count <= 5 else 0,
            "multi_action_episode": 2 if raw["multi_action_episode"] else 0,
            "action_type_diversity": 2 if len(action_types) >= 2 else 0,
            "structural_novelty": 2 if raw["multi_action_episode"] and len(action_types) >= 2 else 1 if actions else 0,
            "trait_contrast_evidence": 0,
            "bounded_research_cost": 2 if 5 <= eligible_action_count <= 6 else 1 if actions else 0,
            "complete_vector_feasibility": 2 if 5 <= eligible_action_count <= 6 and episode_count >= 3 else 0,
        }
        record = {
            "domain_id": domain_id,
            "display_name": raw["display_name"],
            "eligible": not exclusion_reasons,
            "exclusion_reasons": exclusion_reasons,
            "score_components": components,
            "score_total": sum(components.values()),
            "native_substantive_house_action_count": eligible_action_count,
            "native_independent_episode_count": episode_count,
            "action_types": action_types,
            "has_multi_action_episode": raw["multi_action_episode"],
            "substantive_actions": actions,
            "episodes": episodes,
            "excluded_context": raw["excluded_context"],
            "source_note": raw["source_note"],
        }
        if raw.get("benchmark_cross_domain_rows"):
            record["benchmark_cross_domain_rows"] = raw["benchmark_cross_domain_rows"]
        candidates.append(record)

    eligible = [item for item in candidates if item["eligible"]]
    selected = sorted(eligible, key=lambda item: (-item["score_total"], item["domain_id"]))
    selection_basis = {
        "eligibility_precedes_score": True,
        "score_order": "descending score_total",
        "stable_tie_breaker": "canonical domain_id ascending",
    }
    lock_material = {
        "starting_commit": STARTING_COMMIT,
        "candidate_results": [
            {
                "domain_id": item["domain_id"],
                "eligible": item["eligible"],
                "exclusion_reasons": item["exclusion_reasons"],
                "score_components": item["score_components"],
            }
            for item in candidates
        ],
        "selected_domain": selected[0]["domain_id"] if selected else None,
        "selection_basis": selection_basis,
    }
    return {
        "schema_version": "cross_issue_domain_selection_v1",
        "milestone": "cross_issue_editorial_generality_v1",
        "starting_commit": STARTING_COMMIT,
        "congress": 119,
        "chamber": "house",
        "excluded_domains": ["JUSTICE_PUBLIC_SAFETY", "ECONOMY_TAXES"],
        "source_inventory": SOURCE_INVENTORY,
        "candidate_domains": candidates,
        "selected_domain": selected[0]["domain_id"] if selected else None,
        "selection_state": "blocked_no_eligible_domain" if not selected else "selected",
        "stop_condition_triggered": not selected,
        "selection_basis": selection_basis,
        "deterministic_selection_lock": {
            "locked": True,
            "sha256": sha256(canonical_json(lock_material).encode("utf-8")).hexdigest(),
        },
        "publication": {
            "editorial_status": "human_approval_pending",
            "benchmark_status": "not_promoted",
            "productionEligible": False,
        },
        "production_registry_entries": [],
        "next_stage_authorized": bool(selected),
    }


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def markdown(payload: dict) -> str:
    rows = []
    for item in payload["candidate_domains"]:
        rows.append(
            f"| {item['display_name']} | {item['native_substantive_house_action_count']} | "
            f"{item['native_independent_episode_count']} | {'yes' if item['has_multi_action_episode'] else 'no'} | "
            f"{item['score_total']} | {', '.join(item['exclusion_reasons'])} |"
        )
    return "\n".join([
        "# Cross-Issue Editorial Generality V1 — Domain Inventory",
        "",
        "## Result",
        "",
        "**Blocked at deterministic domain selection.** No non-Justice, non-Economy domain can supply five or six substantive House actions across at least three independent 119th-Congress episodes, including one multi-action episode.",
        "",
        "This is the milestone's required fail-closed result. The action cap, chamber boundary, source standard, and episode-independence rule were not relaxed.",
        "",
        "## Candidate inventory",
        "",
        "| Domain | Native substantive House actions | Independent episodes | Multi-action episode | Score / 20 | Exclusion reasons |",
        "|---|---:|---:|---|---:|---|",
        *rows,
        "",
        "## Critical findings",
        "",
        "- National Security has ample actions but only two parent-measure episodes: H.R. 3838 and S. 1071. Repeated amendments and final passage do not become independent policy positions.",
        "- Health has two native substantive House actions. Five additional Health-stratum benchmark rows retain stored primary identities in Justice, Economy, or National Security and cannot be relabeled to manufacture a Health ontology.",
        "- Education has three native substantive final-passage actions but no multi-action episode. Environment and Immigration each have one. Infrastructure is Senate/procedural-only in the reviewed benchmark inventory.",
        "",
        "## Scope reconciliation",
        "",
        "- Selected domain: none.",
        "- Member selection, blind generation, complete-vector evaluation, property transformations, renderer anchors, and rendered inspection: not started because Part I forbids proceeding after this stop condition.",
        "- Generalized correction passes: zero.",
        "- Production writes, registry changes, publication promotion, merge, and deployment: none.",
        "- All milestone artifacts remain `human_approval_pending`, `not_promoted`, and `productionEligible: false`.",
        "",
        "## Validation",
        "",
        "- Focused backend selection, proposition/property, and benchmark tests: 42 passed.",
        "- Frontend Node tests: 136 passed, including four semantic references, 48 rules, and 32 malformed mutations.",
        "- Selection generator drift: pass. Blind and Justice generators: pass.",
        "- Existing editorial-standardization report drift: failed at the verified starting commit; no unrelated report regeneration was included.",
        "- ESLint: pass with eight pre-existing hook warnings.",
        "- Production build: compilation and type validation passed; local page-data collection then failed on the known missing `/_document` module condition.",
        "- Existing rendered suite under a cross-worktree dependency junction: 11 passed, 1 failed, 12 skipped; the failure followed a Next dev-server client-manifest path error. No new renderer surface exists in this stopped milestone.",
        "- Full backend suite: 680 passed; 14 failed and 41 errored because ignored Senate source files were absent, the shared pytest temp root was inaccessible, and a pre-existing pinned ZIP manifest checksum differed.",
        "",
        "## Recommendation",
        "",
        "Run one additional bounded domain validation only after the repository contains a source-grounded candidate with five or six native substantive House actions across at least three independent episodes. Do not broaden this milestone to create that inventory.",
        "",
    ])


def outputs() -> dict[Path, str]:
    payload = build()
    return {
        JSON_OUTPUT: json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        MARKDOWN_OUTPUT: markdown(payload),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = outputs()
    if args.check:
        mismatches = [
            str(path.relative_to(ROOT))
            for path, content in generated.items()
            if not path.exists() or path.read_text(encoding="utf-8") != content
        ]
        if mismatches:
            raise SystemExit("cross-issue selection artifacts differ: " + ", ".join(mismatches))
        print("Cross-issue domain inventory is deterministic and blocked with no eligible domain.")
        return 0
    for path, content in generated.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print("Wrote blocked cross-issue domain selection and review packet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
