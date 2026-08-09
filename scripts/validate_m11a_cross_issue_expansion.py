"""Validate M11A selection, universe-boundary, and official-source artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "docs/editorial/cross_issue_full_record_expansion_v1"
SCHEMA_PATH = ROOT / "docs/methodology/cross_issue_full_record_expansion_v1.schema.json"
SELECTION_PATH = ARTIFACT_ROOT / "domain_selection.json"
UNIVERSE_PATH = ARTIFACT_ROOT / "selected_domain_universe_proposal.json"
INVENTORY_PATH = ARTIFACT_ROOT / "source_inventory.json"
UNRESOLVED = {
    "boundary_review_required",
    "source_missing",
    "source_unresolved",
    "source_conflicting",
}


class M11AValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise M11AValidationError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_schema(value: dict[str, Any], schema: dict[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda error: list(error.absolute_path),
    )
    require(not errors, "; ".join(error.message for error in errors))


def validate() -> None:
    selection = load(SELECTION_PATH)
    universe = load(UNIVERSE_PATH)
    inventory = load(INVENTORY_PATH)
    schema = load(SCHEMA_PATH)
    for value in (selection, universe, inventory):
        validate_schema(value, schema)

    require(
        selection["starting_commit"] == "f16bc73fb4e60d34fe75b17e58cb4f224e5b7fcd",
        "wrong starting checkpoint",
    )
    require(
        set(selection["excluded_domains"])
        == {"JUSTICE_PUBLIC_SAFETY", "ECONOMY_TAXES"},
        "excluded domains drifted",
    )
    require(
        selection["complete_official_action_count"] == 638,
        "official action cutoff is incomplete",
    )
    require(
        selection["production_snapshot"]["read_only"] is True,
        "production evidence was not read-only",
    )
    require(
        selection["production_snapshot"]["transaction_rolled_back"] is True,
        "production transaction was not rolled back",
    )

    expected_selection_material = {
        "starting_commit": selection["starting_commit"],
        "cutoff": selection["cutoff"],
        "complete_official_action_set_sha256": selection[
            "complete_official_action_set_sha256"
        ],
        "domain_accounting": selection["candidate_domains"],
        "selected_domain": selection["selected_domain"],
        "selection_order": selection["eligible_domains_ranked"],
    }
    require(
        selection["selection_sha256"] == sha256_json(expected_selection_material),
        "selection digest mismatch",
    )
    require(
        selection["selected_domain"] == "NATIONAL_SECURITY_FOREIGN",
        "deterministic winner drifted",
    )
    require(
        selection["eligible_domains_ranked"] == ["NATIONAL_SECURITY_FOREIGN"],
        "eligible ranking drifted",
    )
    require(
        selection["m11a_universe_discovery"] == {"permitted": True, "completed": True},
        "M11A discovery gate is ambiguous",
    )
    require(
        selection["human_universe_boundary_approval"] == "pending",
        "human universe approval was inferred",
    )
    require(
        set(selection["downstream_authorizations"].values()) == {False},
        "a downstream stage was authorized",
    )

    for domain in selection["candidate_domains"]:
        disposition_counts = sum(
            len(ids) for ids in domain["action_ids_by_disposition"].values()
        )
        require(
            disposition_counts == domain["total_candidate_actions"],
            f"{domain['domain_id']} accounting does not reconcile",
        )
        require(
            domain["substantive_eligible_actions"] >= 0, "negative substantive count"
        )
        if domain["eligible"]:
            require(
                domain["substantive_eligible_actions"] >= 5,
                "eligible domain has too few substantive actions",
            )
            require(
                domain["independent_episode_count"] >= 3,
                "eligible domain has too few episodes",
            )
            require(
                domain["multi_action_episode_count"] >= 1,
                "eligible domain lacks a multi-action episode",
            )

    records = universe["candidate_dispositions"]
    action_ids = [record["action_id"] for record in records]
    require(
        len(action_ids) == len(set(action_ids)), "duplicate selected candidate action"
    )
    proposed = [
        record
        for record in records
        if record["disposition"].startswith("proposed_in_scope_")
    ]
    unresolved = [record for record in records if record["disposition"] in UNRESOLVED]
    require(
        {record["action_id"] for record in proposed}
        == set(universe["proposed_action_ids"]),
        "proposed set mismatch",
    )
    require(
        {record["action_id"] for record in unresolved}
        == set(universe["unresolved_action_ids"]),
        "unresolved set mismatch",
    )
    require(
        not set(universe["proposed_action_ids"])
        & set(universe["unresolved_action_ids"]),
        "unresolved action entered proposed universe",
    )
    require(
        len(proposed) == 82 and len(unresolved) == 6,
        "selected universe accounting drifted",
    )
    require(
        universe["accounting"]["independent_episode_count"] == 50
        and universe["accounting"]["multi_action_episode_count"] == 5,
        "mechanical episode accounting drifted",
    )
    require(
        all(
            universe[field] is False
            for field in (
                "action_interpretation_authorized",
                "episode_acceptance_authorized",
                "synthesis_authorized",
                "publication_authorized",
            )
        ),
        "universe artifact authorizes a downstream stage",
    )

    for record in proposed:
        binding = record["exact_action_source_binding"]
        require(
            binding is not None, f"{record['action_id']} lacks exact-action binding"
        )
        require(
            binding["canonical_action_id"] == record["action_id"],
            f"{record['action_id']} binding identity mismatch",
        )
        require(
            binding["house_action_stage"] == record["house_action_stage"],
            f"{record['action_id']} stage mismatch",
        )
        require(
            record["member_action"] in {"yea", "nay", "present", "not_voting"},
            "unknown member action",
        )
        require(
            len(binding["sha256"]) == 64,
            f"{record['action_id']} source digest is malformed",
        )
        if (
            "amendment" in record["question"].lower()
            and "senate amendment" not in record["question"].lower()
        ):
            require(
                binding["source_type"] == "congress_gov_bill_amendment_index",
                f"{record['action_id']} inherited parent-measure meaning",
            )
        elif record["issue_boundary_status"] == "direct_target_policy_area":
            require(
                binding["source_type"] == "congress_gov_measure_metadata",
                f"{record['action_id']} direct policy-area authority drifted",
            )
        else:
            evidence = record["cross_domain_boundary_evidence"]
            require(
                evidence is not None and evidence["supports_target_domain"] is True,
                f"{record['action_id']} lacks explicit cross-domain support",
            )

    for record in unresolved:
        require(
            not record["disposition"].startswith("proposed_in_scope_"),
            "unresolved action is substantive",
        )
        if record["unresolved_reason"] == "missing_exact_child_action_binding":
            require(
                record["exact_action_source_binding"] is None,
                "unresolved child action inherited a parent binding",
            )

    by_id = {record["action_id"]: record for record in records}
    for action_id in ("house:119:1:63", "house:119:2:154"):
        require(
            by_id[action_id]["disposition"] == "exact_action_ineligible",
            f"{action_id} was auto-promoted from title vocabulary",
        )
        evidence = by_id[action_id]["cross_domain_boundary_evidence"]
        require(
            evidence["supports_target_domain"] is False,
            f"{action_id} failing boundary evidence is not explicit",
        )

    episode_by_id = {
        episode["episode_candidate_id"]: episode
        for episode in universe["accounting"]["episodes"]
    }
    for episode_id, episode in episode_by_id.items():
        bill_refs = {
            by_id[action_id]["bill_ref"] for action_id in episode["action_ids"]
        }
        require(len(bill_refs) == 1, f"{episode_id} combines separate parent measures")
        require(
            "war-powers" not in episode_id,
            "semantic War Powers episode entered accounting",
        )
    require(
        all(
            candidate["contributes_to_m11a_episode_accounting"] is False
            and candidate["authority_effect"] == "none"
            for candidate in universe["future_episode_review_candidates"]
        ),
        "future semantic episode candidate affects M11A authority",
    )

    boundary = universe["cross_domain_boundary_review"]
    require(
        boundary["direct_target_policy_area_action_count"] == 42
        and boundary["exact_amendment_action_specific_evidence_count"] == 23
        and boundary["retained_cross_domain_action_count"] == 17
        and boundary["moved_out_of_proposed_universe_count"] == 2,
        "cross-domain correction accounting drifted",
    )
    require(
        len(boundary["reviewed_actions"]) == 19,
        "cross-domain review table does not cover the reviewed-head cases",
    )
    require(
        all(
            record["cross_domain_boundary_evidence"] is not None
            for record in boundary["reviewed_actions"]
        ),
        "cross-domain review row lacks explicit evidence",
    )
    delta = universe["correction_delta_from_48dd78f"]
    require(
        delta["reviewed_head"] == "48dd78fa0c7d9b955b04bec333185fbbf0069c4e"
        and delta["previous_proposed_action_count"] == 84
        and delta["current_proposed_action_count"] == 82
        and delta["added_action_ids"] == []
        and delta["removed_action_ids"] == ["house:119:1:63", "house:119:2:154"],
        "reviewed-head correction delta drifted",
    )

    universe_material = {
        "subject": universe["subject"],
        "cutoff": selection["cutoff"],
        "candidate_records": records,
    }
    require(
        universe["universe_subject_sha256"] == sha256_json(universe_material),
        "universe digest mismatch",
    )
    inventory_material = {
        key: value for key, value in inventory.items() if key != "inventory_sha256"
    }
    require(
        inventory["inventory_sha256"] == sha256_json(inventory_material),
        "source inventory digest mismatch",
    )
    bindings = {
        row["action_id"]: row for row in inventory["selected_candidate_source_bindings"]
    }
    require(
        set(bindings) == set(action_ids),
        "source inventory does not cover every selected candidate",
    )
    for record in records:
        row = bindings[record["action_id"]]
        require(
            row["member_action"] == record["member_action"],
            "source inventory member-action mismatch",
        )
        require(
            row["house_action_stage"] == record["house_action_stage"],
            "source inventory stage mismatch",
        )
        require(
            row["issue_boundary_status"] == record["issue_boundary_status"]
            and row["cross_domain_boundary_evidence"]
            == record["cross_domain_boundary_evidence"],
            "source inventory boundary evidence mismatch",
        )


def main() -> int:
    validate()
    print("M11A cross-issue selection and universe artifacts: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
