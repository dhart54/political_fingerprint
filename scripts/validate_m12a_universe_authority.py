from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.universe_authority import (  # noqa: E402
    UniverseAuthorityError,
    canonical_file_sha256,
    sha256_json,
)


SCHEMA_PATH = (
    ROOT / "docs/methodology/full_issue_universe_authority_receipt_v1.schema.json"
)
RECEIPT_PATH = (
    ROOT / "docs/editorial/full_record_reviews/"
    "f000477_environment_energy_119_full_issue_universe_authority_receipt_v1.json"
)
ARTIFACT_ROOT = ROOT / "docs/editorial/cross_issue_full_record_expansion_m12a_v1"
SELECTION_PATH = ARTIFACT_ROOT / "domain_selection.json"
UNIVERSE_PATH = ARTIFACT_ROOT / "selected_domain_universe_proposal.json"
INVENTORY_PATH = ARTIFACT_ROOT / "source_inventory.json"
CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"

EXPECTED = {
    "receipt_id": "universe-authority:f000477:environment_energy:119:v1",
    "reviewer_id": "chatgpt:political_fingerprint_authority_thread",
    "decision_timestamp": "2026-08-15T23:39:59.4841583Z",
    "accepted_pr": 149,
    "accepted_head": "3d031790a072ed0194720931aef0c587ecf0d8b6",
    "selection_id": "cross-issue-selection:F000477:119:m12a:v1",
    "selection_sha256": (
        "e18fcf736f5febac352d823b35c5a81b2c18deb36fda26b41acbef0005755fa1"
    ),
    "proposal_id": "full-universe-proposal:f000477:environment_energy:119:m12a:v1",
    "proposal_sha256": (
        "18967832549bd90353bc0d265f48793b6932bd7d57a49bcca95795820115f5ea"
    ),
    "universe_subject_sha256": (
        "29b42a593639a1c62745e959554596a40a8dbf8205e1b3a6af83234c8f49866e"
    ),
    "approved_action_set_sha256": (
        "843740a27ef191294bcf0cc3d2b29aeda1751351d775f8fadd7f44708e2312c8"
    ),
    "complete_action_set_sha256": (
        "a4d228a74004de61f78827ef85bd5a59cb4f5c3dddf9b55e9e3e154a44cd7fde"
    ),
    "inventory_id": "source-inventory:F000477:ENVIRONMENT_ENERGY:119:m12a:v1",
    "inventory_sha256": (
        "e2b8d790cd9c16076241a8fb79215170718251eabf3b7b225280a7a5fe888ca8"
    ),
}
EXCLUSION_KEYS = (
    "procedural_context",
    "expressive_nonbinding_context",
    "exact_action_ineligible",
    "boundary_review_required",
)
EXPECTED_COUNTS = {
    "proposed_in_scope_substantive": 62,
    "proposed_in_scope_non_directional": 1,
    "procedural_context": 64,
    "expressive_nonbinding_context": 1,
    "exact_action_ineligible": 0,
    "boundary_review_required": 25,
}
EXPECTED_UNRESOLVED = [
    "house:119:1:111",
    "house:119:1:215",
    "house:119:1:227",
    "house:119:1:228",
    "house:119:1:229",
    "house:119:1:230",
    "house:119:1:231",
    "house:119:1:232",
    "house:119:1:233",
    "house:119:1:234",
    "house:119:1:235",
    "house:119:1:236",
    "house:119:1:237",
    "house:119:1:239",
    "house:119:1:277",
    "house:119:1:315",
    "house:119:1:352",
    "house:119:1:353",
    "house:119:1:354",
    "house:119:2:109",
    "house:119:2:134",
    "house:119:2:223",
    "house:119:2:5",
    "house:119:2:6",
    "house:119:2:7",
]
EXPECTED_PROJECT_STATE = {
    "active_full_record_publications": [
        "JUSTICE_PUBLIC_SAFETY",
        "NATIONAL_SECURITY_FOREIGN",
        "ENVIRONMENT_ENERGY",
    ],
    "active_publication_count": 3,
    "national_security_full_record_state": "production_active_live_verified",
    "national_security_downstream_chain_complete": True,
    "national_security_production_database_write_completed": True,
    "national_security_receipts_only": False,
    "justice_full_record_state": "production_active_live_verified",
    "environment_energy_full_record_state": "production_active_live_verified",
}
EXPECTED_JUSTICE_STATE = {
    "f000477_justice_119_action_interpretation_state": (
        "complete_37_actions_35_substantive_2_controls"
    ),
    "f000477_justice_119_policy_episode_state": "complete_32_episodes",
    "f000477_justice_119_full_record_semantic_ir": "accepted_compiled_v2",
    "f000477_justice_119_full_record_synthesis": "accepted_full_issue_synthesis",
    "f000477_justice_119_production_persistence": "completed_and_read_only_verified",
    "f000477_justice_119_publication_state": "full_record_publication_active",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise UniverseAuthorityError(message)


def bound_path(root: Path, relative: str) -> Path:
    resolved_root = root.resolve()
    path = (resolved_root / relative).resolve()
    require(path.is_relative_to(resolved_root), "authority binding escapes repository")
    require(path.is_file(), f"missing authority-bound artifact: {relative}")
    return path


def validate_values(
    *,
    receipt: dict[str, Any],
    selection: dict[str, Any],
    universe: dict[str, Any],
    inventory: dict[str, Any],
    current_state: dict[str, Any],
    receipt_path: Path = RECEIPT_PATH,
    authority_root: Path = ROOT,
) -> dict[str, Any]:
    schema = load(SCHEMA_PATH)
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(receipt),
        key=lambda error: list(error.absolute_path),
    )
    require(
        not errors,
        "M12A authority receipt schema validation failed: "
        + "; ".join(error.message for error in errors),
    )
    require(
        receipt_path.resolve()
        not in {SELECTION_PATH.resolve(), UNIVERSE_PATH.resolve()},
        "authority receipt is not detached from the reviewed proposal",
    )
    binding = receipt["approval_binding"]

    selection_material = {
        "starting_commit": selection["starting_commit"],
        "cutoff": selection["cutoff"],
        "complete_official_action_set_sha256": selection[
            "complete_official_action_set_sha256"
        ],
        "domain_accounting": selection["candidate_domains"],
        "selected_domain": selection["selected_domain"],
        "selection_order": selection["eligible_domains_ranked"],
    }
    selection_sha256 = sha256_json(selection_material)
    require(
        selection["selection_id"] == EXPECTED["selection_id"]
        and selection_sha256
        == selection["selection_sha256"]
        == binding["selection"]["sha256"]
        == EXPECTED["selection_sha256"],
        "selection identity or digest mismatch",
    )

    universe_material = {
        "subject": universe["subject"],
        "cutoff": universe["cutoff"]["end_date"],
        "candidate_records": universe["candidate_dispositions"],
    }
    universe_subject_sha256 = sha256_json(universe_material)
    proposal_sha256 = sha256_json(
        {key: value for key, value in universe.items() if key != "proposal_sha256"}
    )
    proposal_path = bound_path(
        authority_root, binding["universe_proposal"]["artifact_path"]
    )
    require(
        receipt["manifest_id"] == universe["proposal_id"] == EXPECTED["proposal_id"]
        and proposal_sha256
        == universe["proposal_sha256"]
        == EXPECTED["proposal_sha256"],
        "proposal identity or digest mismatch",
    )
    require(
        universe_subject_sha256
        == universe["universe_subject_sha256"]
        == receipt["universe_subject_sha256"]
        == binding["universe_proposal"]["universe_subject_sha256"]
        == EXPECTED["universe_subject_sha256"],
        "universe-subject digest mismatch",
    )
    require(
        canonical_file_sha256(proposal_path)
        == receipt["manifest_sha256"]
        == binding["universe_proposal"]["file_sha256"],
        "proposal file digest mismatch",
    )

    rows = universe["candidate_dispositions"]
    rows_by_id = {row["action_id"]: row for row in rows}
    require(len(rows_by_id) == len(rows) == 153, "candidate identity mismatch")
    derived_sets = {
        disposition: sorted(
            row["action_id"] for row in rows if row["disposition"] == disposition
        )
        for disposition in EXPECTED_COUNTS
    }
    for disposition, expected_count in EXPECTED_COUNTS.items():
        require(
            derived_sets[disposition]
            == sorted(
                universe["accounting"]["action_ids_by_disposition"].get(disposition, [])
            )
            and len(derived_sets[disposition]) == expected_count,
            f"{disposition} accounting mismatch",
        )

    approved = sorted(
        derived_sets["proposed_in_scope_substantive"]
        + derived_sets["proposed_in_scope_non_directional"]
    )
    approved_sha256 = sha256_json(approved)
    require(
        approved
        == sorted(universe["proposed_action_ids"])
        == sorted(binding["approved_action_ids"])
        and len(approved) == len(set(approved)) == receipt["action_count"] == 63
        and approved_sha256
        == receipt["action_set_sha256"]
        == EXPECTED["approved_action_set_sha256"],
        "approved 63-action membership mismatch",
    )
    for category in EXCLUSION_KEYS:
        action_ids = derived_sets[category]
        category_binding = binding["exclusion_categories"][category]
        require(
            sorted(category_binding["action_ids"]) == action_ids
            and category_binding["action_count"] == len(action_ids)
            and category_binding["action_set_sha256"] == sha256_json(action_ids),
            f"{category} receipt binding mismatch",
        )
    partition = approved + [
        action_id for category in EXCLUSION_KEYS for action_id in derived_sets[category]
    ]
    require(
        len(partition) == len(set(partition)) == len(rows),
        "candidate accounting is not an exact one-time partition",
    )
    require(
        sorted(universe["unresolved_action_ids"])
        == derived_sets["boundary_review_required"]
        == EXPECTED_UNRESOLVED
        and set(approved).isdisjoint(EXPECTED_UNRESOLVED),
        "unresolved set entered or differs from authority boundary",
    )
    unresolved_rows = [rows_by_id[action_id] for action_id in EXPECTED_UNRESOLVED]
    child_rows = [
        row
        for row in unresolved_rows
        if row["unresolved_reason"] == "missing_exact_child_action_binding"
    ]
    require(
        len(child_rows) == 16
        and sum(row["house_action_stage"] == "amendment" for row in child_rows) == 14
        and sum(row["house_action_stage"] == "division_retention" for row in child_rows)
        == 2,
        "exact-child unresolved accounting is not 14 amendments plus 2 divisions",
    )

    inventory_material = {
        key: value for key, value in inventory.items() if key != "inventory_sha256"
    }
    inventory_binding = binding["source_inventory"]
    inventory_path = bound_path(authority_root, inventory_binding["artifact_path"])
    require(
        inventory["inventory_id"]
        == inventory_binding["artifact_id"]
        == EXPECTED["inventory_id"]
        and sha256_json(inventory_material)
        == inventory["inventory_sha256"]
        == inventory_binding["inventory_sha256"]
        == EXPECTED["inventory_sha256"]
        and canonical_file_sha256(inventory_path) == inventory_binding["file_sha256"]
        and receipt["source_manifest_identities"] == [inventory["inventory_id"]],
        "source-inventory identity or digest mismatch",
    )
    source_rows = inventory["selected_candidate_source_bindings"]
    source_by_id = {row["action_id"]: row for row in source_rows}
    require(
        len(source_by_id) == len(source_rows) == len(rows)
        and set(source_by_id) == set(rows_by_id),
        "source inventory does not bind every candidate",
    )
    for action_id, row in rows_by_id.items():
        source_row = source_by_id[action_id]
        require(
            source_row["disposition"] == row["disposition"]
            and source_row["sources"] == row["sources"],
            f"source binding mismatch: {action_id}",
        )
        if action_id in approved:
            require(
                source_row["exact_action_source_binding"]
                == row["exact_action_source_binding"]
                and source_row["exact_action_source_binding"] is not None,
                f"approved action lacks exact source binding: {action_id}",
            )

    expected_subject = {
        "member_name": "Valerie Foushee",
        "member_id": "F000477",
        "legislator_id": "leg_valerie_p_foushee",
        "chamber": "house",
        "congress": 119,
        "issue_id": "ENVIRONMENT_ENERGY",
    }
    require(
        binding["subject"] == expected_subject
        and receipt["member_id"] == "F000477"
        and receipt["issue_id"]
        == binding["selected_domain"]
        == selection["selected_domain"]
        == "ENVIRONMENT_ENERGY",
        "authority subject mismatch",
    )
    require(
        binding["official_cutoff"]
        == {"end_date": "2026-07-23", "latest_action_id": "house:119:2:283"}
        and receipt["boundary"]["end_date"]
        == selection["cutoff"]
        == universe["cutoff"]["end_date"]
        == inventory["cutoff"],
        "official cutoff mismatch",
    )
    complete_ids = inventory["complete_official_action_ids"]
    require(
        len(complete_ids)
        == len(set(complete_ids))
        == binding["complete_house_action_set"]["action_count"]
        == selection["complete_official_action_count"]
        == universe["complete_member_action_count"]
        == inventory["complete_official_action_count"]
        == 638
        and sha256_json(complete_ids)
        == binding["complete_house_action_set"]["action_set_sha256"]
        == selection["complete_official_action_set_sha256"]
        == inventory["complete_official_action_set_sha256"]
        == EXPECTED["complete_action_set_sha256"],
        "complete official action-set identity mismatch",
    )
    require(
        receipt["boundary_sha256"] == sha256_json(receipt["boundary"]),
        "receipt boundary digest mismatch",
    )
    require(
        receipt["receipt_id"] == EXPECTED["receipt_id"]
        and receipt["reviewer"]
        == {
            "reviewer_id": EXPECTED["reviewer_id"],
            "authority": "full_issue_universe_review_authority_v1",
        }
        and receipt["decision_timestamp"] == EXPECTED["decision_timestamp"]
        and receipt["decision"] == "approved_complete_issue_universe"
        and binding["accepted_pull_request"]
        == {
            "number": EXPECTED["accepted_pr"],
            "head_sha": EXPECTED["accepted_head"],
        },
        "reviewer provenance or accepted head mismatch",
    )
    require(
        binding["authority_effect"] == "universe_membership_only"
        and all(
            value is False for value in binding["downstream_authorizations"].values()
        ),
        "receipt authorizes downstream work",
    )
    require(
        universe["authority_status"] == "pending_human_universe_boundary_review"
        and all(
            universe[key] is False
            for key in (
                "action_interpretation_started",
                "action_interpretation_authorized",
                "episode_acceptance_authorized",
                "semantic_ir_started",
                "synthesis_authorized",
                "publication_authorized",
                "publication_changes",
                "production_writes",
            )
        ),
        "reviewed proposal was mutated or gained downstream authority",
    )

    milestone = current_state["active_scaling_milestone"]
    receipt_file_sha256 = canonical_file_sha256(receipt_path)
    require(
        milestone["milestone"] == "m12a_next_full_record_issue_selection_v1"
        and milestone["milestone_state"] == "completed_independent_review_approved"
        and milestone["authority_status"] == "approved_content_bound"
        and milestone["approved_action_count"] == 63
        and milestone["approved_action_set_sha256"] == approved_sha256
        and milestone["unresolved_actions_outside_approved_universe"] is True
        and milestone["independent_governance_universe_boundary_approval"] == "approved"
        and all(
            value is False for value in milestone["downstream_authorizations"].values()
        ),
        "canonical M12A authority state mismatch",
    )
    require(
        milestone["universe_authority_receipt"]
        == RECEIPT_PATH.relative_to(ROOT).as_posix()
        and milestone["universe_authority_receipt_identity"]
        == {
            "id": EXPECTED["receipt_id"],
            "sha256": receipt_file_sha256,
            "reviewer_id": EXPECTED["reviewer_id"],
            "reviewer_authority": "full_issue_universe_review_authority_v1",
            "decision": "approved_complete_issue_universe",
            "decision_timestamp": EXPECTED["decision_timestamp"],
            "accepted_pr": EXPECTED["accepted_pr"],
            "accepted_head": EXPECTED["accepted_head"],
        },
        "canonical M12A receipt identity mismatch",
    )
    project_state = current_state["current_project_state"]
    require(
        all(
            project_state.get(key) == value
            for key, value in EXPECTED_PROJECT_STATE.items()
        ),
        "Justice or National Security production state changed",
    )
    justice = current_state["full_record_issue_interpretation"]
    require(
        all(justice.get(key) == value for key, value in EXPECTED_JUSTICE_STATE.items()),
        "accepted Justice state changed",
    )

    return {
        "status": "passed",
        "receipt_id": receipt["receipt_id"],
        "receipt_file_sha256": receipt_file_sha256,
        "selection_sha256": selection_sha256,
        "proposal_sha256": proposal_sha256,
        "universe_subject_sha256": universe_subject_sha256,
        "approved_action_count": len(approved),
        "approved_action_set_sha256": approved_sha256,
        "candidate_count": len(rows),
        "exclusion_counts": {
            category: len(derived_sets[category]) for category in EXCLUSION_KEYS
        },
        "unresolved_action_ids": EXPECTED_UNRESOLVED,
        "exact_child_unresolved": {
            "total": len(child_rows),
            "amendments": 14,
            "division_retentions": 2,
        },
        "source_binding_count": len(source_rows),
        "accepted_head": EXPECTED["accepted_head"],
        "downstream_authorizations": binding["downstream_authorizations"],
    }


def validate_repository() -> dict[str, Any]:
    return validate_values(
        receipt=load(RECEIPT_PATH),
        selection=load(SELECTION_PATH),
        universe=load(UNIVERSE_PATH),
        inventory=load(INVENTORY_PATH),
        current_state=load(CURRENT_STATE_PATH),
    )


def main() -> int:
    try:
        print(json.dumps(validate_repository(), indent=2))
    except (UniverseAuthorityError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
