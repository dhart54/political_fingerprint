from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.universe_authority import (  # noqa: E402
    canonical_file_sha256,
    sha256_json,
)


ARTIFACT_ROOT = ROOT / "docs/editorial/cross_issue_full_record_expansion_m13a_v1"
SELECTION_PATH = ARTIFACT_ROOT / "domain_selection.json"
UNIVERSE_PATH = ARTIFACT_ROOT / "selected_domain_universe_proposal.json"
INVENTORY_PATH = ARTIFACT_ROOT / "source_inventory.json"
COMPLETE_INVENTORY_PATH = ARTIFACT_ROOT / "complete_official_action_inventory.json"
RECEIPT_PATH = ROOT / (
    "docs/editorial/full_record_reviews/"
    "f000477_education_workforce_119_full_issue_universe_authority_receipt_v1.json"
)

ACCEPTED_PR = 162
ACCEPTED_HEAD = "45e3c572f1824d2e3b06292ba75c67dd6e46cfc0"
DECISION_TIMESTAMP = "2026-08-24T02:26:23Z"
REVIEWER_ID = "chatgpt:political_fingerprint_authority_thread"
REVIEWER_AUTHORITY = "full_issue_universe_review_authority_v1"
RECEIPT_ID = "universe-authority:f000477:education_workforce:119:v1"
EXCLUSION_CATEGORIES = (
    "procedural_context",
    "expressive_nonbinding_context",
    "exact_action_ineligible",
    "boundary_review_required",
)
ECONOMY_HELD_ACTIONS = [
    "house:119:1:100",
    "house:119:1:190",
    "house:119:1:285",
    "house:119:2:5",
    "house:119:2:6",
    "house:119:2:53",
]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_receipt() -> dict[str, Any]:
    selection = load(SELECTION_PATH)
    universe = load(UNIVERSE_PATH)
    inventory = load(INVENTORY_PATH)
    complete_inventory = load(COMPLETE_INVENTORY_PATH)
    rows = universe["candidate_dispositions"]
    ids_by_disposition = {
        disposition: sorted(
            row["action_id"] for row in rows if row["disposition"] == disposition
        )
        for disposition in EXCLUSION_CATEGORIES
    }
    approved_action_ids = sorted(universe["proposed_action_ids"])
    boundary = {
        "sessions": [1, 2],
        "start_date": "2025-01-03",
        "end_date": "2026-07-23",
        "as_of_date": "2026-08-24",
        "chambers": ["house"],
        "service_boundary": (
            "Valerie Foushee (F000477) is represented as the serving NC-04 "
            "House member throughout the included 119th-Congress action dates; "
            "the governed official record covers House actions through July 23, "
            "2026."
        ),
    }
    return {
        "schema_version": "full_issue_universe_authority_receipt_v1",
        "receipt_id": RECEIPT_ID,
        "manifest_id": universe["proposal_id"],
        "manifest_sha256": canonical_file_sha256(UNIVERSE_PATH),
        "member_id": "F000477",
        "issue_id": "EDUCATION_WORKFORCE",
        "review_scope": "full_defined_issue_record",
        "boundary": boundary,
        "boundary_sha256": sha256_json(boundary),
        "action_set_sha256": sha256_json(approved_action_ids),
        "action_count": len(approved_action_ids),
        "source_manifest_identities": [inventory["inventory_id"]],
        "universe_subject_sha256": universe["universe_subject_sha256"],
        "reviewer": {
            "reviewer_id": REVIEWER_ID,
            "authority": REVIEWER_AUTHORITY,
        },
        "decision_timestamp": DECISION_TIMESTAMP,
        "decision": "approved_complete_issue_universe",
        "approval_binding": {
            "authority_effect": "universe_membership_only",
            "subject": {
                "member_name": "Valerie Foushee",
                "member_id": "F000477",
                "legislator_id": "leg_valerie_p_foushee",
                "chamber": "house",
                "congress": 119,
                "issue_id": "EDUCATION_WORKFORCE",
            },
            "selected_domain": "EDUCATION_WORKFORCE",
            "official_cutoff": {
                "end_date": "2026-07-23",
                "latest_action_id": "house:119:2:283",
            },
            "complete_house_action_set": {
                "artifact_id": "house-action-set:F000477:119:through-house:119:2:283:v1",
                "action_count": complete_inventory["complete_official_action_count"],
                "action_set_sha256": complete_inventory[
                    "complete_official_action_id_set_sha256"
                ],
            },
            "complete_official_inventory": {
                "artifact_path": COMPLETE_INVENTORY_PATH.relative_to(ROOT).as_posix(),
                "inventory_sha256": complete_inventory[
                    "complete_official_action_inventory_sha256"
                ],
                "file_sha256": canonical_file_sha256(COMPLETE_INVENTORY_PATH),
            },
            "selection": {
                "artifact_path": SELECTION_PATH.relative_to(ROOT).as_posix(),
                "sha256": selection["selection_sha256"],
            },
            "universe_proposal": {
                "artifact_path": UNIVERSE_PATH.relative_to(ROOT).as_posix(),
                "file_sha256": canonical_file_sha256(UNIVERSE_PATH),
                "proposal_sha256": universe["proposal_sha256"],
                "universe_subject_sha256": universe["universe_subject_sha256"],
            },
            "approved_action_ids": approved_action_ids,
            "exclusion_categories": {
                category: {
                    "artifact_id": (
                        f"action-set:f000477:education_workforce:119:{category}:v1"
                    ),
                    "action_count": len(action_ids),
                    "action_set_sha256": sha256_json(action_ids),
                    "action_ids": action_ids,
                }
                for category, action_ids in ids_by_disposition.items()
            },
            "accepted_boundary_constraints": {
                "house:119:1:79": {
                    "constraint": "exact_amendment_identity_and_purpose_required",
                    "parent_measure_inference_sufficient": False,
                    "separate_same_parent_action": "house:119:1:83",
                    "episode_semantics_approved": False,
                },
                "house:119:1:146": {
                    "primary_policy_area": "Commerce",
                    "membership_basis": (
                        "career and technical education students and graduates, "
                        "workforce hiring, and career opportunities"
                    ),
                    "exclusive_or_primary_education_classification": False,
                },
                "house:119:1:315": {
                    "primary_policy_area": "Public Lands and Natural Resources",
                    "membership_basis": (
                        "Secure Rural Schools payments materially fund schools within "
                        "a broader county and federal-land program"
                    ),
                    "required_context": [
                        "county_payment_and_federal_land_program",
                        "school_funding_component",
                        "roads_community_and_resource_project_context",
                        "exact_extension_choice",
                    ],
                    "general_education_funding_position_authorized": False,
                },
            },
            "held_domain_boundaries": {
                "ECONOMY_TAXES": {
                    "selection_ready": False,
                    "reason": "missing_exact_child_action_binding",
                    "action_ids": ECONOMY_HELD_ACTIONS,
                    "action_set_sha256": sha256_json(ECONOMY_HELD_ACTIONS),
                }
            },
            "source_inventory": {
                "artifact_id": inventory["inventory_id"],
                "artifact_path": INVENTORY_PATH.relative_to(ROOT).as_posix(),
                "file_sha256": canonical_file_sha256(INVENTORY_PATH),
                "inventory_sha256": inventory["inventory_sha256"],
            },
            "accepted_pull_request": {
                "number": ACCEPTED_PR,
                "head_sha": ACCEPTED_HEAD,
            },
            "downstream_authorizations": {
                "source_readiness": False,
                "action_interpretation": False,
                "episode_acceptance": False,
                "semantic_ir": False,
                "synthesis": False,
                "public_wording": False,
                "site_integration": False,
                "publication": False,
                "deployment": False,
                "production_persistence": False,
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(build_receipt(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if (
            not RECEIPT_PATH.exists()
            or RECEIPT_PATH.read_text(encoding="utf-8") != rendered
        ):
            raise SystemExit("M13A universe-authority receipt drift detected")
    else:
        RECEIPT_PATH.write_text(rendered, encoding="utf-8")
    print(RECEIPT_PATH.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
