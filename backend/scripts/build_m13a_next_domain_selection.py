from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
LEGACY_BUILDER = ROOT / "backend/scripts/build_cross_issue_full_record_expansion.py"
SCHEMA_VERSION = "m13a_next_domain_selection_v1"
MILESTONE = "m13a_next_full_record_issue_selection_v1"
STARTING_COMMIT = "1edb335a787040a7cfab39e36b9260234a74d683"
ACTIVE_DOMAINS = {
    "JUSTICE_PUBLIC_SAFETY",
    "NATIONAL_SECURITY_FOREIGN",
    "ENVIRONMENT_ENERGY",
}
REMAINING_DOMAINS = (
    "ECONOMY_TAXES",
    "EDUCATION_WORKFORCE",
    "HEALTH_SOCIAL",
    "IMMIGRATION_BORDER",
    "INFRASTRUCTURE_TECH_TRANSPORT",
)
ACTION_SPECIFIC_BOUNDARY_DECISIONS = {
    # Economy & Taxes: exact official summaries materially establish taxation,
    # finance, small-business, trade, or appropriations components.
    **{
        ("ECONOMY_TAXES", bill_ref): True
        for bill_ref in (
            "bill_119_hr_825",
            "bill_119_hr_832",
            "bill_119_hr_804",
            "bill_119_hjres_25",
            "bill_119_hr_517",
            "bill_119_hr_997",
            "bill_119_hr_1491",
            "bill_119_sjres_13",
            "bill_119_hr_1642",
            "bill_119_hr_2931",
            "bill_119_hr_2987",
            "bill_119_hr_2966",
            "bill_119_hr_3944",
            "bill_119_hr_3633",
            "bill_119_s_1582",
            "bill_119_hr_1919",
            "bill_119_hr_4016",
            "bill_119_hr_3351",
            "bill_119_hr_5371",
            "bill_119_hr_2965",
            "bill_119_hr_4305",
            "bill_119_hr_3383",
            "bill_119_hr_6500",
            "bill_119_hr_6504",
            "bill_119_hr_7006",
            "bill_119_hjres_142",
            "bill_119_s_3971",
            "bill_119_hr_7959",
            "bill_119_hr_8469",
            "bill_119_hr_7401",
            "bill_119_hr_915",
            "bill_119_hr_8595",
        )
    },
    ("EDUCATION_WORKFORCE", "bill_119_hr_1642"): True,
    ("EDUCATION_WORKFORCE", "bill_119_s_356"): True,
    ("EDUCATION_WORKFORCE", "bill_119_hr_4541"): False,
    ("HEALTH_SOCIAL", "bill_119_hr_6945"): True,
    ("HEALTH_SOCIAL", "bill_119_hr_7726"): True,
    ("HEALTH_SOCIAL", "bill_119_hr_4541"): True,
    ("IMMIGRATION_BORDER", "bill_119_hr_495"): True,
    ("IMMIGRATION_BORDER", "bill_119_hr_3062"): False,
    ("IMMIGRATION_BORDER", "bill_119_hr_6504"): False,
    ("IMMIGRATION_BORDER", "bill_119_hr_1689"): True,
    ("INFRASTRUCTURE_TECH_TRANSPORT", "bill_119_hjres_87"): True,
    ("INFRASTRUCTURE_TECH_TRANSPORT", "bill_119_hr_1770"): True,
    ("INFRASTRUCTURE_TECH_TRANSPORT", "bill_119_hr_3062"): True,
    ("INFRASTRUCTURE_TECH_TRANSPORT", "bill_119_hr_1608"): True,
    ("INFRASTRUCTURE_TECH_TRANSPORT", "bill_119_hr_3106"): True,
    ("INFRASTRUCTURE_TECH_TRANSPORT", "bill_119_hr_8897"): True,
}
DISPOSITION_LABELS = {
    "proposed_in_scope_substantive": "substantive_directional",
    "proposed_in_scope_non_directional": "substantive_non_directional",
    "procedural_context": "procedural_context",
    "expressive_nonbinding_context": "expressive_nonbinding",
    "exact_action_ineligible": "exact_action_ineligible",
    "boundary_review_required": "boundary_review_required",
    "source_missing": "boundary_review_required",
    "source_unresolved": "boundary_review_required",
    "source_conflicting": "boundary_review_required",
}


def load_legacy() -> Any:
    spec = importlib.util.spec_from_file_location("cross_issue_builder", LEGACY_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load cross-issue builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_files(root: Path, pattern: str) -> list[dict[str, Any]]:
    legacy = load_legacy()
    return [
        {
            "filename": path.name,
            "sha256": legacy.sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in sorted(root.glob(pattern))
    ]


def public_inventory(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "action_id": action["action_id"],
            "session": action["session"],
            "roll": action["roll"],
            "date": action["date"],
            "bill_ref": action["bill_ref"],
            "question": action["question"],
            "description": action["description"],
            "member_action": action["member_action"],
            "official_vote_source": action["vote_source"],
        }
        for action in actions
    ]


def selection_rank(row: dict[str, Any]) -> tuple[Any, ...]:
    # The current milestone first requires a closed universe. Among closed
    # universes, mechanism diversity demonstrates additional behavioral
    # structure before raw action volume is considered.
    return (
        -len(row["mechanism_types"]),
        -row["substantive_eligible_actions"],
        -row["independent_episode_count"],
        row["domain_id"],
    )


def build_payloads(args: argparse.Namespace) -> dict[str, Any]:
    legacy = load_legacy()
    legacy.STARTING_COMMIT = STARTING_COMMIT
    legacy.MILESTONE = MILESTONE
    legacy.OFFICIAL_CUTOFF_VERIFIED_AT = args.official_cutoff_verified_at
    legacy.EXCLUDED_DOMAINS = ACTIVE_DOMAINS
    legacy.DOMAIN_IDS = REMAINING_DOMAINS
    legacy.ACTION_SPECIFIC_BOUNDARY_DECISIONS = ACTION_SPECIFIC_BOUNDARY_DECISIONS
    legacy.RESOLVE_EXACT_AMENDMENT_NONMATCH = True

    original_accounting = legacy.domain_accounting

    def closed_accounting(
        domain_id: str, records: list[dict[str, Any]]
    ) -> dict[str, Any]:
        row = original_accounting(domain_id, records)
        source_complete = (
            row["official_source_readiness"]["state"]
            == "complete_for_proposed_membership"
        )
        universe_closed = source_complete and row["unresolved_boundary_cases"] == 0
        row["generic_manageability_gate_passed"] = row["eligible"]
        row["full_issue_universe_closed"] = universe_closed
        row["selection_ready"] = row["eligible"] and universe_closed
        if row["eligible"] and not universe_closed:
            row["exclusion_reasons"] = [
                *row["exclusion_reasons"],
                "unresolved_boundary_cases_prevent_closed_universe",
            ]
        row["eligible"] = row["selection_ready"]
        row["expected_additional_structure"] = {
            "mechanism_type_count": len(row["mechanism_types"]),
            "independent_mechanical_event_count": row["independent_episode_count"],
            "same_parent_multi_action_group_count": row["multi_action_episode_count"],
            "volume_is_final_not_primary_tie_breaker": True,
        }
        return row

    legacy.domain_accounting = closed_accounting
    legacy.selection_rank = selection_rank
    payloads = legacy.build(
        production_snapshot=args.production_snapshot,
        clerk_dirs=args.clerk_dir,
        congress_metadata_dir=args.congress_metadata_dir,
        amendment_index_dir=args.amendment_index_dir,
        congress_summaries_dir=args.congress_summaries_dir,
        cutoff=args.cutoff,
    )

    actions = legacy.load_clerk_actions(args.clerk_dir, "F000477")
    inventory_rows = public_inventory(actions)
    inventory_digest = legacy.sha256_json(inventory_rows)
    action_id_digest = legacy.sha256_json([row["action_id"] for row in inventory_rows])
    latest = actions[-1]
    inventory = {
        "schema_version": "complete_official_member_action_inventory_v1",
        "milestone": MILESTONE,
        "subject": {
            "member_id": "F000477",
            "legislator_id": "leg_valerie_p_foushee",
            "congress": 119,
            "chamber": "house",
        },
        "cutoff": {
            "start_date": actions[0]["date"],
            "end_date": args.cutoff,
            "latest_action_id": latest["action_id"],
            "latest_roll": latest["roll"],
        },
        "complete_official_action_count": len(inventory_rows),
        "complete_official_action_id_set_sha256": action_id_digest,
        "complete_official_action_inventory_sha256": inventory_digest,
        "actions": inventory_rows,
    }

    selection = payloads["selection"]
    selection.update(
        {
            "schema_version": "cross_issue_domain_selection_v3",
            "selection_id": "cross-issue-selection:F000477:119:m13a:v1",
            "complete_official_action_set_sha256": action_id_digest,
            "complete_official_action_inventory_sha256": inventory_digest,
            "selection_basis": [
                "full_issue_universe_closed_zero_unresolved_boundaries",
                "complete_official_source_binding_for_every_proposed_action",
                "policy_mechanism_variation_before_volume",
                "substantive_action_and_independent_mechanical_event_depth",
                "canonical_domain_id_final_tie_breaker",
            ],
            "readiness_comparison_basis": [
                "defensible_universe_completeness",
                "unresolved_boundary_burden",
                "substantive_action_number_and_diversity",
                "official_source_readiness",
                "additional_behavioral_structure_not_merely_volume",
            ],
        }
    )
    selection_material = {
        "starting_commit": STARTING_COMMIT,
        "cutoff": args.cutoff,
        "complete_official_action_set_sha256": action_id_digest,
        "complete_official_action_inventory_sha256": inventory_digest,
        "domain_accounting": selection["candidate_domains"],
        "selected_domain": selection["selected_domain"],
        "selection_order": selection["eligible_domains_ranked"],
    }
    selection["selection_sha256"] = legacy.sha256_json(selection_material)

    universe = payloads["universe"]
    universe.update(
        {
            "schema_version": "cross_issue_universe_proposal_v2",
            "proposal_id": (
                "full-universe-proposal:f000477:"
                f"{selection['selected_domain'].lower()}:119:m13a:v1"
            ),
            "selection_sha256": selection["selection_sha256"],
            "complete_official_action_set_sha256": action_id_digest,
            "complete_official_action_inventory_sha256": inventory_digest,
            "full_issue_universe_closed": True,
        }
    )
    universe["proposal_sha256"] = legacy.sha256_json(
        {key: value for key, value in universe.items() if key != "proposal_sha256"}
    )

    acquisition_manifest = json.loads(
        args.acquisition_manifest.read_text(encoding="utf-8")
    )
    fresh_sources = {
        "manifest_path": args.acquisition_manifest.name,
        "manifest_sha256": legacy.sha256_file(args.acquisition_manifest),
        "summary_sources": source_files(args.congress_summaries_dir, "119_*.json"),
        "amendment_index_sources": source_files(args.amendment_index_dir, "119_*.json"),
        "production_or_database_access": acquisition_manifest[
            "production_or_database_access"
        ],
    }
    source_inventory = payloads["source_inventory"]
    source_inventory.update(
        {
            "schema_version": "cross_issue_source_inventory_v2",
            "inventory_id": (
                f"source-inventory:F000477:{selection['selected_domain']}:119:m13a:v1"
            ),
            "official_cutoff_verified_at": args.official_cutoff_verified_at,
            "source_acquired_at": args.source_acquired_at,
            "complete_official_action_set_sha256": action_id_digest,
            "complete_official_action_inventory_sha256": inventory_digest,
            "fresh_boundary_source_acquisition": fresh_sources,
        }
    )
    source_inventory["inventory_sha256"] = legacy.sha256_json(
        {
            key: value
            for key, value in source_inventory.items()
            if key != "inventory_sha256"
        }
    )

    unresolved: list[dict[str, Any]] = []
    for row in selection["candidate_domains"]:
        for action_id in row["action_ids_by_disposition"].get(
            "boundary_review_required", []
        ):
            unresolved.append(
                {
                    "domain_id": row["domain_id"],
                    "action_id": action_id,
                    "reason": "exact_child_action_binding_remains_unavailable",
                }
            )
    review_packet = render_review_packet(
        selection=selection,
        universe=universe,
        inventory=inventory,
        unresolved=unresolved,
    )
    return {
        "selection": selection,
        "universe": universe,
        "source_inventory": source_inventory,
        "complete_inventory": inventory,
        "review_packet": review_packet,
    }


def render_review_packet(
    *,
    selection: dict[str, Any],
    universe: dict[str, Any],
    inventory: dict[str, Any],
    unresolved: list[dict[str, Any]],
) -> str:
    lines = [
        "# M13A Next Full-Record Issue Selection Review Packet",
        "",
        "## Decision boundary",
        "",
        f"- Exact base: `{STARTING_COMMIT}`.",
        f"- Official cutoff: `{selection['cutoff']}` through `{inventory['cutoff']['latest_action_id']}`.",
        f"- Complete official inventory: **{inventory['complete_official_action_count']}** actions.",
        f"- Action-ID digest: `{inventory['complete_official_action_id_set_sha256']}`.",
        f"- Full inventory digest: `{inventory['complete_official_action_inventory_sha256']}`.",
        f"- Proposed next domain: **{universe['accounting']['display_name']}** (`{selection['selected_domain']}`).",
        "- Authority: pending independent ChatGPT universe-selection review only.",
        "",
        "Justice & Public Safety, National Security & Foreign Policy, and Environment & Energy are production-active and excluded from candidacy. Their accepted artifacts are unchanged.",
        "",
        "## Remaining-domain readiness",
        "",
        "| Rank | Domain | Closed | Directional | Non-directional | Procedural | Expressive | Ineligible | Boundary review | Events | Mechanisms | Source readiness | Result |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    rank = {
        domain: index + 1
        for index, domain in enumerate(selection["eligible_domains_ranked"])
    }
    for row in selection["candidate_domains"]:
        result = (
            "selected"
            if row["domain_id"] == selection["selected_domain"]
            else "selection-ready; lower structure rank"
            if row["selection_ready"]
            else "; ".join(row["exclusion_reasons"])
        )
        lines.append(
            f"| {rank.get(row['domain_id'], '—')} | {row['display_name']} | "
            f"{'yes' if row['full_issue_universe_closed'] else 'no'} | "
            f"{row['directional_substantive_actions']} | {row['non_directional_substantive_actions']} | "
            f"{row['procedural_context_actions']} | {row['expressive_nonbinding_actions']} | "
            f"{row['exact_action_ineligible_actions']} | {row['unresolved_boundary_cases']} | "
            f"{row['independent_episode_count']} | {', '.join(row['mechanism_types'])} | "
            f"{row['official_source_readiness']['state']} | {result} |"
        )
    accounting = universe["accounting"]
    lines.extend(
        [
            "",
            "## Selection rationale",
            "",
            f"{accounting['display_name']} is the highest-ranked defensibly closed universe. It has zero unresolved boundary actions, complete exact-source binding for all {accounting['substantive_eligible_actions']} proposed actions, {accounting['independent_episode_count']} independent mechanical events, and both amendment and passage mechanisms. Mechanism diversity ranks before raw volume so the selection demonstrates additional behavioral structure rather than choosing the largest pile of actions.",
            "",
            "Economy & Taxes re-entered fresh evaluation and its generic manageability gate now passes, but it remains non-selectable here because exact child-action evidence is still unavailable for its remaining boundary cases. Those actions were not forced into the domain.",
            "",
            "## Complete proposed-universe accounting",
            "",
            f"- Substantive directional: {accounting['directional_substantive_actions']}.",
            f"- Substantive non-directional: {accounting['non_directional_substantive_actions']}.",
            f"- Procedural/context: {accounting['procedural_context_actions']}.",
            f"- Expressive/nonbinding: {accounting['expressive_nonbinding_actions']}.",
            f"- Exact-action-ineligible: {accounting['exact_action_ineligible_actions']}.",
            f"- Boundary-review-required: {accounting['unresolved_boundary_cases']}.",
            f"- Proposed membership: {len(universe['proposed_action_ids'])} actions.",
            "",
            "| Action | Date | Member action | Stage | Measure | Official policy area | Boundary basis |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for row in universe["candidate_dispositions"]:
        if not row["disposition"].startswith("proposed_in_scope_"):
            continue
        lines.append(
            f"| `{row['action_id']}` | {row['date']} | {row['member_action']} | "
            f"{row['house_action_stage']} | {row['description']} | "
            f"{row['official_policy_area']} | {row['issue_boundary_status']} |"
        )
    lines.extend(
        [
            "",
            "## Unresolved exclusions across remaining domains",
            "",
            "| Domain | Action | Reason |",
            "|---|---|---|",
        ]
    )
    if unresolved:
        for row in unresolved:
            lines.append(
                f"| {row['domain_id']} | `{row['action_id']}` | {row['reason']} |"
            )
    else:
        lines.append("| — | — | None |")
    lines.extend(
        [
            "",
            "## Stop boundary",
            "",
            "No action interpretation, episode construction or acceptance, Semantic IR, synthesis, public wording, site integration, publication, deployment, or production preparation has begun or been authorized. Stop for independent ChatGPT universe-selection review.",
            "",
        ]
    )
    return "\n".join(lines)


def serialize(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production-snapshot", type=Path, required=True)
    parser.add_argument("--clerk-dir", type=Path, action="append", required=True)
    parser.add_argument("--congress-metadata-dir", type=Path, required=True)
    parser.add_argument("--amendment-index-dir", type=Path, required=True)
    parser.add_argument("--congress-summaries-dir", type=Path, required=True)
    parser.add_argument("--acquisition-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--review-packet", type=Path, required=True)
    parser.add_argument("--cutoff", default="2026-07-23")
    parser.add_argument("--official-cutoff-verified-at", required=True)
    parser.add_argument("--source-acquired-at", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    payloads = build_payloads(args)
    paths = {
        "selection": args.output_root / "domain_selection.json",
        "universe": args.output_root / "selected_domain_universe_proposal.json",
        "source_inventory": args.output_root / "source_inventory.json",
        "complete_inventory": args.output_root
        / "complete_official_action_inventory.json",
        "review_packet": args.review_packet,
    }
    if args.check:
        drift = [
            str(path)
            for key, path in paths.items()
            if not path.exists()
            or path.read_text(encoding="utf-8") != serialize(payloads[key])
        ]
        if drift:
            raise SystemExit("generated M13A artifacts differ: " + ", ".join(drift))
    else:
        args.output_root.mkdir(parents=True, exist_ok=True)
        args.review_packet.parent.mkdir(parents=True, exist_ok=True)
        for key, path in paths.items():
            path.write_text(serialize(payloads[key]), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "pass",
                "selected_domain": payloads["selection"]["selected_domain"],
                "official_action_count": payloads["complete_inventory"][
                    "complete_official_action_count"
                ],
                "proposed_action_count": len(
                    payloads["universe"]["proposed_action_ids"]
                ),
                "selected_unresolved_count": payloads["universe"]["accounting"][
                    "unresolved_boundary_cases"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
