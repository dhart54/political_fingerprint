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
    "f000477_national_security_foreign_119_full_issue_universe_authority_receipt_v1.json"
)
SELECTION_PATH = (
    ROOT / "docs/editorial/cross_issue_full_record_expansion_v1/domain_selection.json"
)
UNIVERSE_PATH = (
    ROOT / "docs/editorial/cross_issue_full_record_expansion_v1/"
    "selected_domain_universe_proposal.json"
)
INVENTORY_PATH = (
    ROOT / "docs/editorial/cross_issue_full_record_expansion_v1/source_inventory.json"
)
CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"

EXPECTED = {
    "receipt_id": "universe-authority:f000477:national_security_foreign:119:v1",
    "reviewer_id": "dhart54",
    "decision_timestamp": "2026-08-09T03:45:32.2350019Z",
    "accepted_pr": 133,
    "accepted_head": "1860ef0fab3f65ffb303c5b74b380f41fe929421",
    "selection_sha256": (
        "a018b597705132f0e891c575af1dac4b880c31b0d98469f2f47001982dce0b81"
    ),
    "universe_subject_sha256": (
        "b1e1a4588a4fcef6beb9dfd836ff5c2f32d8fdb340359f11453c6a0c947a17a5"
    ),
    "approved_action_set_sha256": (
        "190bda45c25cd32ae0a6847c862f85837eafc4a82dfda237746a66467c550400"
    ),
    "complete_action_set_sha256": (
        "a4d228a74004de61f78827ef85bd5a59cb4f5c3dddf9b55e9e3e154a44cd7fde"
    ),
    "inventory_sha256": (
        "c0e568396793f7fcca7fd5c70a6ad82fa32de4e289362568b785d02fc92124b5"
    ),
}
EXCLUSION_KEYS = (
    "procedural_context",
    "expressive_nonbinding_context",
    "exact_action_ineligible",
    "boundary_review_required",
)
EXPECTED_COUNTS = {
    "proposed_in_scope_substantive": 82,
    "procedural_context": 33,
    "expressive_nonbinding_context": 2,
    "exact_action_ineligible": 26,
    "boundary_review_required": 6,
}
EXPECTED_UNRESOLVED = [
    "house:119:1:245",
    "house:119:1:247",
    "house:119:1:253",
    "house:119:1:254",
    "house:119:1:256",
    "house:119:1:285",
]
EXPECTED_JUSTICE_STATE = {
    "f000477_justice_119_action_interpretation_state": (
        "complete_37_actions_35_substantive_2_controls"
    ),
    "f000477_justice_119_policy_episode_state": "complete_32_episodes",
    "f000477_justice_119_full_record_semantic_ir": "accepted_compiled_v2",
    "f000477_justice_119_full_record_synthesis": "accepted_full_issue_synthesis",
    "f000477_justice_119_production_persistence": ("completed_and_read_only_verified"),
    "f000477_justice_119_publication_state": "full_record_publication_active",
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise UniverseAuthorityError(message)


def _validate_schema(receipt: dict[str, Any]) -> None:
    schema = _load(SCHEMA_PATH)
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(receipt),
        key=lambda error: list(error.absolute_path),
    )
    _require(
        not errors,
        "M11A authority receipt schema validation failed: "
        + "; ".join(error.message for error in errors),
    )


def _bound_path(root: Path, relative: str) -> Path:
    resolved_root = root.resolve()
    path = (resolved_root / relative).resolve()
    _require(path.is_relative_to(resolved_root), "authority binding escapes repository")
    _require(path.is_file(), f"missing authority-bound artifact: {relative}")
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
    _validate_schema(receipt)
    _require(
        receipt_path.resolve()
        not in {SELECTION_PATH.resolve(), UNIVERSE_PATH.resolve()},
        "authority receipt is not detached from the proposed universe",
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
    _require(
        selection_sha256
        == selection["selection_sha256"]
        == EXPECTED["selection_sha256"],
        "selection digest mismatch",
    )
    _require(
        binding["selection"]["sha256"] == selection_sha256,
        "receipt selection digest mismatch",
    )

    universe_material = {
        "subject": universe["subject"],
        "cutoff": universe["cutoff"]["end_date"],
        "candidate_records": universe["candidate_dispositions"],
    }
    universe_subject_sha256 = sha256_json(universe_material)
    _require(
        universe_subject_sha256
        == universe["universe_subject_sha256"]
        == EXPECTED["universe_subject_sha256"],
        "universe-subject digest mismatch",
    )
    _require(
        receipt["universe_subject_sha256"]
        == binding["universe_proposal"]["universe_subject_sha256"]
        == universe_subject_sha256,
        "receipt universe-subject binding mismatch",
    )

    proposal_path = _bound_path(
        authority_root, binding["universe_proposal"]["artifact_path"]
    )
    proposal_file_sha256 = canonical_file_sha256(proposal_path)
    _require(
        receipt["manifest_sha256"]
        == binding["universe_proposal"]["file_sha256"]
        == proposal_file_sha256,
        "universe proposal file digest mismatch",
    )

    approved = sorted(universe["proposed_action_ids"])
    receipt_approved = sorted(binding["approved_action_ids"])
    action_set_sha256 = sha256_json(approved)
    _require(len(approved) == len(set(approved)) == 82, "approved membership is not 82")
    _require(
        approved == receipt_approved,
        "receipt approved membership differs from the proposed action set",
    )
    _require(
        action_set_sha256
        == receipt["action_set_sha256"]
        == EXPECTED["approved_action_set_sha256"],
        "approved action-set digest mismatch",
    )
    _require(receipt["action_count"] == len(approved), "receipt action count mismatch")

    rows = universe["candidate_dispositions"]
    rows_by_id = {row["action_id"]: row for row in rows}
    _require(len(rows_by_id) == len(rows) == 149, "candidate action identity mismatch")
    derived_sets = {
        disposition: sorted(
            row["action_id"] for row in rows if row["disposition"] == disposition
        )
        for disposition in EXPECTED_COUNTS
    }
    accounting_sets = universe["accounting"]["action_ids_by_disposition"]
    for disposition, expected_count in EXPECTED_COUNTS.items():
        _require(
            derived_sets[disposition] == sorted(accounting_sets[disposition])
            and len(derived_sets[disposition]) == expected_count,
            f"{disposition} accounting mismatch",
        )
    _require(
        derived_sets["proposed_in_scope_substantive"] == approved,
        "approved action membership does not match substantive dispositions",
    )

    for category in EXCLUSION_KEYS:
        category_binding = binding["exclusion_categories"][category]
        action_ids = derived_sets[category]
        _require(
            sorted(category_binding["action_ids"]) == action_ids,
            f"{category} receipt membership mismatch",
        )
        _require(
            category_binding["action_count"] == len(action_ids),
            f"{category} receipt count mismatch",
        )
        _require(
            category_binding["action_set_sha256"] == sha256_json(action_ids),
            f"{category} receipt digest mismatch",
        )

    all_partitioned = approved + [
        action_id for category in EXCLUSION_KEYS for action_id in derived_sets[category]
    ]
    _require(
        len(all_partitioned) == len(set(all_partitioned)) == len(rows),
        "candidate accounting is not an exact one-time partition",
    )
    _require(
        sorted(universe["unresolved_action_ids"])
        == derived_sets["boundary_review_required"]
        == EXPECTED_UNRESOLVED,
        "unresolved boundary set mismatch",
    )

    inventory_material = {
        key: value for key, value in inventory.items() if key != "inventory_sha256"
    }
    inventory_sha256 = sha256_json(inventory_material)
    inventory_binding = binding["source_inventory"]
    inventory_path = _bound_path(authority_root, inventory_binding["artifact_path"])
    _require(
        inventory_sha256
        == inventory["inventory_sha256"]
        == inventory_binding["inventory_sha256"]
        == EXPECTED["inventory_sha256"],
        "source inventory subject digest mismatch",
    )
    _require(
        canonical_file_sha256(inventory_path) == inventory_binding["file_sha256"],
        "source inventory file digest mismatch",
    )
    _require(
        receipt["source_manifest_identities"] == [inventory_binding["artifact_id"]],
        "source inventory identity mismatch",
    )

    source_rows = inventory["selected_candidate_source_bindings"]
    source_by_id = {row["action_id"]: row for row in source_rows}
    _require(
        len(source_by_id) == len(source_rows) == len(rows)
        and set(source_by_id) == set(rows_by_id),
        "source inventory does not bind the complete candidate set",
    )
    for action_id, row in rows_by_id.items():
        source_row = source_by_id[action_id]
        _require(
            source_row["disposition"] == row["disposition"],
            f"source disposition mismatch: {action_id}",
        )
        _require(
            source_row["sources"] == row["sources"],
            f"source binding mismatch: {action_id}",
        )
        if action_id in approved:
            _require(
                source_row["exact_action_source_binding"]
                == row["exact_action_source_binding"]
                and source_row["exact_action_source_binding"] is not None,
                f"approved action lacks exact official source binding: {action_id}",
            )

    expected_subject = {
        "member_name": "Valerie Foushee",
        "member_id": "F000477",
        "legislator_id": "leg_valerie_p_foushee",
        "chamber": "house",
        "congress": 119,
        "issue_id": "NATIONAL_SECURITY_FOREIGN",
    }
    _require(binding["subject"] == expected_subject, "receipt subject mismatch")
    _require(
        selection["subject"]
        == {
            "member_id": "F000477",
            "legislator_id": "leg_valerie_p_foushee",
            "congress": 119,
            "chamber": "house",
        }
        and universe["subject"]
        == {
            "member_id": "F000477",
            "issue_id": "NATIONAL_SECURITY_FOREIGN",
            "congress": 119,
        }
        and inventory["subject"] == universe["subject"],
        "source artifacts disagree on subject identity",
    )
    _require(
        receipt["member_id"] == "F000477"
        and receipt["issue_id"]
        == binding["selected_domain"]
        == selection["selected_domain"]
        == "NATIONAL_SECURITY_FOREIGN",
        "selected-domain identity mismatch",
    )
    _require(
        binding["official_cutoff"]
        == {"end_date": "2026-07-23", "latest_action_id": "house:119:2:283"}
        and receipt["boundary"]["end_date"]
        == selection["cutoff"]
        == universe["cutoff"]["end_date"]
        == inventory["cutoff"],
        "official cutoff mismatch",
    )
    _require(
        binding["complete_house_action_set"]["action_count"]
        == selection["complete_official_action_count"]
        == universe["complete_member_action_count"]
        == inventory["complete_official_action_count"]
        == 638,
        "complete House action count mismatch",
    )
    _require(
        binding["complete_house_action_set"]["action_set_sha256"]
        == selection["complete_official_action_set_sha256"]
        == EXPECTED["complete_action_set_sha256"],
        "complete House action-set identity mismatch",
    )
    _require(
        receipt["boundary_sha256"] == sha256_json(receipt["boundary"]),
        "receipt boundary digest mismatch",
    )
    _require(
        receipt["receipt_id"] == EXPECTED["receipt_id"]
        and receipt["reviewer"]["reviewer_id"] == EXPECTED["reviewer_id"]
        and receipt["decision_timestamp"] == EXPECTED["decision_timestamp"],
        "reviewer or stable approval identity mismatch",
    )
    _require(
        binding["accepted_pull_request"]
        == {
            "number": EXPECTED["accepted_pr"],
            "head_sha": EXPECTED["accepted_head"],
        },
        "accepted PR head mismatch",
    )
    _require(
        binding["authority_effect"] == "universe_membership_only"
        and all(
            value is False for value in binding["downstream_authorizations"].values()
        ),
        "receipt self-authorizes downstream work",
    )
    _require(
        universe["authority_status"] == "pending_human_universe_boundary_review"
        and universe["action_interpretation_started"] is False
        and universe["action_interpretation_authorized"] is False
        and universe["episode_acceptance_authorized"] is False
        and universe["semantic_ir_started"] is False
        and universe["synthesis_authorized"] is False
        and universe["publication_authorized"] is False
        and universe["production_writes"] is False,
        "historical proposal boundary changed or authorizes downstream work",
    )

    milestone = current_state["active_scaling_milestone"]
    _require(
        milestone["milestone"] == "m11a_cross_issue_full_record_expansion_v1"
        and milestone["milestone_state"] == "completed_human_approved"
        and milestone["authority_status"] == "approved_content_bound"
        and milestone["approved_substantive_count"] == 82
        and milestone["approved_action_set_sha256"] == action_set_sha256
        and milestone["unresolved_actions_outside_approved_universe"] is True,
        "canonical M11A approval state mismatch",
    )
    _require(
        milestone["interpretation_state"] == "not_started"
        and milestone["policy_episode_state"] == "not_accepted"
        and milestone["semantic_ir_state"] == "absent"
        and milestone["synthesis_state"] == "absent"
        and milestone["publication_state"] == "inactive"
        and milestone["production_persistence"] == "not_authorized"
        and all(
            value is False for value in milestone["downstream_authorizations"].values()
        ),
        "canonical M11A state crosses the universe-only approval boundary",
    )
    justice = current_state["full_record_issue_interpretation"]
    _require(
        all(justice.get(key) == value for key, value in EXPECTED_JUSTICE_STATE.items()),
        "accepted Justice state changed",
    )
    receipt_file_sha256 = canonical_file_sha256(receipt_path)
    identity = milestone["universe_authority_receipt_identity"]
    _require(
        milestone["universe_authority_receipt"]
        == RECEIPT_PATH.relative_to(ROOT).as_posix()
        and identity
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
        "canonical authority receipt identity mismatch",
    )

    return {
        "status": "pass",
        "receipt_id": receipt["receipt_id"],
        "receipt_file_sha256": receipt_file_sha256,
        "selection_sha256": selection_sha256,
        "universe_subject_sha256": universe_subject_sha256,
        "approved_action_count": len(approved),
        "approved_action_set_sha256": action_set_sha256,
        "candidate_count": len(rows),
        "exclusion_counts": {
            category: len(derived_sets[category]) for category in EXCLUSION_KEYS
        },
        "unresolved_action_ids": EXPECTED_UNRESOLVED,
        "source_binding_count": len(source_rows),
        "accepted_head": EXPECTED["accepted_head"],
        "downstream_authorizations": binding["downstream_authorizations"],
    }


def validate_repository() -> dict[str, Any]:
    return validate_values(
        receipt=_load(RECEIPT_PATH),
        selection=_load(SELECTION_PATH),
        universe=_load(UNIVERSE_PATH),
        inventory=_load(INVENTORY_PATH),
        current_state=_load(CURRENT_STATE_PATH),
    )


def main() -> int:
    try:
        print(json.dumps(validate_repository(), sort_keys=True))
    except (UniverseAuthorityError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
