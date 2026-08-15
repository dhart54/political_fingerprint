from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "docs/editorial/cross_issue_full_record_expansion_m12a_v1"
SCHEMA = ROOT / "docs/methodology/cross_issue_full_record_expansion_v2.schema.json"
SELECTION = ARTIFACT_ROOT / "domain_selection.json"
UNIVERSE = ARTIFACT_ROOT / "selected_domain_universe_proposal.json"
INVENTORY = ARTIFACT_ROOT / "source_inventory.json"
EXPECTED_DOMAINS = {
    "ECONOMY_TAXES",
    "EDUCATION_WORKFORCE",
    "ENVIRONMENT_ENERGY",
    "HEALTH_SOCIAL",
    "IMMIGRATION_BORDER",
    "INFRASTRUCTURE_TECH_TRANSPORT",
}
UNRESOLVED = {
    "boundary_review_required",
    "source_missing",
    "source_unresolved",
    "source_conflicting",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    schema = load(SCHEMA)
    selection = load(SELECTION)
    universe = load(UNIVERSE)
    inventory = load(INVENTORY)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for path, payload in (
        (SELECTION, selection),
        (UNIVERSE, universe),
        (INVENTORY, inventory),
    ):
        errors = sorted(
            validator.iter_errors(payload), key=lambda error: list(error.path)
        )
        require(not errors, f"{path.name}: {errors[0].message if errors else ''}")

    require(
        selection["starting_commit"] == "44d966a7b3c36494b4965db6d4b00d6ba6d6a332",
        "starting commit differs",
    )
    require(
        set(selection["excluded_domains"])
        == {"JUSTICE_PUBLIC_SAFETY", "NATIONAL_SECURITY_FOREIGN"},
        "completed-domain exclusion differs",
    )
    by_domain = {row["domain_id"]: row for row in selection["candidate_domains"]}
    require(set(by_domain) == EXPECTED_DOMAINS, "candidate taxonomy differs")
    require(selection["selected_domain"] == "ENVIRONMENT_ENERGY", "winner differs")
    require(
        selection["eligible_domains_ranked"][0] == "ENVIRONMENT_ENERGY", "rank differs"
    )
    require(
        "legitimate_multi_action_episode" not in selection["selection_basis"],
        "multi-action episode leaked into ranking",
    )
    require(
        selection["selection_exclusions"]["multi_action_episode_requirement_or_reward"],
        "multi-action exclusion assertion absent",
    )
    for row in by_domain.values():
        require(
            "no_legitimate_multi_action_episode" not in row["exclusion_reasons"],
            f"multi-action eligibility leaked for {row['domain_id']}",
        )
        disposition_total = sum(
            len(ids) for ids in row["action_ids_by_disposition"].values()
        )
        require(
            disposition_total == row["total_candidate_actions"],
            f"accounting gap for {row['domain_id']}",
        )
        require(
            row["directional_substantive_actions"]
            + row["non_directional_substantive_actions"]
            == row["substantive_eligible_actions"],
            f"substantive accounting differs for {row['domain_id']}",
        )
    require(
        by_domain["ECONOMY_TAXES"]["exclusion_reasons"]
        == ["unresolved_boundary_set_exceeds_substantive_set"],
        "Economy eligibility rationale differs",
    )

    records = universe["candidate_dispositions"]
    counts = Counter(record["disposition"] for record in records)
    proposed = [
        record
        for record in records
        if record["disposition"].startswith("proposed_in_scope_")
    ]
    unresolved = [record for record in records if record["disposition"] in UNRESOLVED]
    require(len(records) == 153, "selected high-recall count differs")
    require(len(proposed) == 63, "proposed universe count differs")
    require(counts["proposed_in_scope_substantive"] == 62, "directional count differs")
    require(
        counts["proposed_in_scope_non_directional"] == 1,
        "non-directional count differs",
    )
    require(counts["procedural_context"] == 64, "procedural count differs")
    require(counts["expressive_nonbinding_context"] == 1, "expressive count differs")
    require(counts["exact_action_ineligible"] == 0, "ineligible count differs")
    require(len(unresolved) == 25, "unresolved count differs")
    require(
        set(universe["proposed_action_ids"]).isdisjoint(
            universe["unresolved_action_ids"]
        ),
        "unresolved action entered proposal",
    )
    require(
        set(universe["unresolved_action_ids"])
        == {record["action_id"] for record in unresolved},
        "unresolved identity differs",
    )
    for record in proposed:
        require(
            record["exact_action_source_binding"] is not None,
            f"missing binding: {record['action_id']}",
        )
    for record in unresolved:
        if record["unresolved_reason"] == "missing_exact_child_action_binding":
            require(
                record["exact_action_source_binding"] is None,
                f"parent evidence leaked: {record['action_id']}",
            )
    boundary = universe["cross_domain_boundary_review"]["reviewed_actions"]
    expected_boundary = [
        record
        for record in records
        if record["issue_boundary_status"] != "direct_target_policy_area"
    ]
    require(
        [row["action_id"] for row in boundary]
        == [row["action_id"] for row in expected_boundary],
        "cross-domain review table is incomplete",
    )
    require(
        universe["future_episode_review_candidates"] == [],
        "semantic episode inference leaked",
    )
    require(
        universe["multi_action_episode_count"] == 0
        if "multi_action_episode_count" in universe
        else True,
        "unexpected universe multi-action field",
    )
    for key in (
        "action_interpretation_started",
        "action_interpretation_authorized",
        "episode_acceptance_authorized",
        "synthesis_authorized",
        "publication_authorized",
        "semantic_ir_started",
        "publication_changes",
        "production_writes",
    ):
        require(universe[key] is False, f"downstream authority leaked: {key}")
    require(
        digest(
            {key: value for key, value in universe.items() if key != "proposal_sha256"}
        )
        == universe["proposal_sha256"],
        "proposal digest differs",
    )

    require(
        inventory["complete_official_action_count"] == 638, "official count differs"
    )
    require(
        len(inventory["complete_official_action_ids"]) == 638, "official ID set differs"
    )
    require(
        inventory["complete_official_action_set_sha256"]
        == selection["complete_official_action_set_sha256"]
        == "a4d228a74004de61f78827ef85bd5a59cb4f5c3dddf9b55e9e3e154a44cd7fde",
        "official action-set digest differs",
    )
    require(
        inventory["governed_ingestion"]["member_action_count"] == 563,
        "ingestion count differs",
    )
    require(
        inventory["governed_ingestion"]["newer_than_official_cutoff"] is False,
        "cutoff mismatch",
    )
    require(
        inventory["governed_ingestion"]["transaction_rolled_back"] is True,
        "read-only rollback absent",
    )
    require(
        digest(
            {
                key: value
                for key, value in inventory.items()
                if key != "inventory_sha256"
            }
        )
        == inventory["inventory_sha256"],
        "inventory digest differs",
    )
    require(
        len(inventory["selected_candidate_source_bindings"]) == len(records),
        "selected source inventory is incomplete",
    )
    print(
        json.dumps(
            {
                "status": "passed",
                "selected_domain": selection["selected_domain"],
                "candidate_domains": len(by_domain),
                "official_action_count": inventory["complete_official_action_count"],
                "selected_candidate_count": len(records),
                "proposed_count": len(proposed),
                "unresolved_count": len(unresolved),
                "selection_sha256": selection["selection_sha256"],
                "proposal_sha256": universe["proposal_sha256"],
                "inventory_sha256": inventory["inventory_sha256"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
