from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
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


ARTIFACT_ROOT = ROOT / "docs/editorial/cross_issue_full_record_expansion_m13a_v1"
SELECTION_PATH = ARTIFACT_ROOT / "domain_selection.json"
UNIVERSE_PATH = ARTIFACT_ROOT / "selected_domain_universe_proposal.json"
SOURCE_INVENTORY_PATH = ARTIFACT_ROOT / "source_inventory.json"
COMPLETE_INVENTORY_PATH = ARTIFACT_ROOT / "complete_official_action_inventory.json"
RECEIPT_PATH = ROOT / (
    "docs/editorial/full_record_reviews/"
    "f000477_education_workforce_119_full_issue_universe_authority_receipt_v1.json"
)
SCHEMA_PATH = (
    ROOT / "docs/methodology/full_issue_universe_authority_receipt_v1.schema.json"
)
CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"
BASE = "1edb335a787040a7cfab39e36b9260234a74d683"
EXPECTED = {
    "accepted_head": "45e3c572f1824d2e3b06292ba75c67dd6e46cfc0",
    "selection_sha256": "e877adf1cd5a1bff08c08ecb4ee1ee6acc1bbdff6d93899171e13480f6473f5a",
    "proposal_sha256": "9802afc93b06196ec3329a40dade7b5d0b111bd663141d53417d7442d8572169",
    "universe_subject_sha256": "edc381362beb1e5700748ffe75fc12c31ae14f090887940197a50bf416aaac6d",
    "action_set_sha256": "83b7b129eaa32d114c72782c70cb06dac55f7cd01c8681c8dc2ae2dca986cf5b",
    "complete_action_set_sha256": "a4d228a74004de61f78827ef85bd5a59cb4f5c3dddf9b55e9e3e154a44cd7fde",
    "complete_inventory_sha256": "a21331a187b37d019e05df4e6be480aab22a9a0f213ce9e49f17556d2537c135",
    "source_inventory_sha256": "66070d29ebe29e6ef3c17dc67c888b522d7043b36e5fd694d0093b4ce5be6fe7",
    "receipt_sha256": "491b6de2314788f1566f8366f95a66b2375ec6d1271790a18387ba33cad70ea3",
}
APPROVED = [
    "house:119:1:68",
    "house:119:1:79",
    "house:119:1:83",
    "house:119:1:120",
    "house:119:1:146",
    "house:119:1:312",
    "house:119:1:313",
    "house:119:1:314",
    "house:119:1:315",
    "house:119:1:332",
    "house:119:2:19",
    "house:119:2:31",
    "house:119:2:47",
    "house:119:2:82",
    "house:119:2:184",
    "house:119:2:216",
    "house:119:2:217",
]
ECONOMY_HELD = [
    "house:119:1:100",
    "house:119:1:190",
    "house:119:1:285",
    "house:119:2:5",
    "house:119:2:6",
    "house:119:2:53",
]
PROTECTED_PATHS = (
    "docs/editorial/cross_issue_full_record_expansion_v1",
    "docs/editorial/cross_issue_full_record_expansion_m12a_v1",
    "docs/editorial/full_record_reviews/f000477_justice_public_safety_119_full_issue_universe_authority_receipt_v2.json",
    "docs/editorial/full_record_reviews/f000477_national_security_foreign_119_full_issue_universe_authority_receipt_v1.json",
    "docs/editorial/full_record_reviews/f000477_environment_energy_119_full_issue_universe_authority_receipt_v1.json",
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise UniverseAuthorityError(message)


def validate_repository() -> dict[str, Any]:
    receipt = load(RECEIPT_PATH)
    selection = load(SELECTION_PATH)
    universe = load(UNIVERSE_PATH)
    source_inventory = load(SOURCE_INVENTORY_PATH)
    complete_inventory = load(COMPLETE_INVENTORY_PATH)
    current = load(CURRENT_STATE_PATH)
    schema = load(SCHEMA_PATH)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(receipt),
        key=lambda error: list(error.absolute_path),
    )
    require(
        not errors, f"authority schema failed: {errors[0].message if errors else ''}"
    )
    require(
        RECEIPT_PATH.resolve()
        not in {SELECTION_PATH.resolve(), UNIVERSE_PATH.resolve()},
        "authority is not detached from candidate",
    )
    binding = receipt["approval_binding"]

    require(
        receipt["receipt_id"] == "universe-authority:f000477:education_workforce:119:v1"
        and receipt["decision"] == "approved_complete_issue_universe"
        and receipt["decision_timestamp"] == "2026-08-24T02:26:23Z"
        and receipt["reviewer"]
        == {
            "reviewer_id": "chatgpt:political_fingerprint_authority_thread",
            "authority": "full_issue_universe_review_authority_v1",
        },
        "review authority identity differs",
    )
    require(
        canonical_file_sha256(RECEIPT_PATH) == EXPECTED["receipt_sha256"],
        "authority file digest differs",
    )
    require(
        selection["starting_commit"] == BASE
        and selection["selected_domain"] == "EDUCATION_WORKFORCE"
        and selection["selection_sha256"]
        == binding["selection"]["sha256"]
        == EXPECTED["selection_sha256"],
        "selection binding differs",
    )
    calculated_proposal = sha256_json(
        {key: value for key, value in universe.items() if key != "proposal_sha256"}
    )
    require(
        calculated_proposal
        == universe["proposal_sha256"]
        == binding["universe_proposal"]["proposal_sha256"]
        == EXPECTED["proposal_sha256"],
        "proposal digest differs",
    )
    require(
        receipt["manifest_id"] == universe["proposal_id"]
        and receipt["manifest_sha256"]
        == binding["universe_proposal"]["file_sha256"]
        == canonical_file_sha256(UNIVERSE_PATH),
        "candidate file provenance differs",
    )
    require(
        receipt["universe_subject_sha256"]
        == universe["universe_subject_sha256"]
        == binding["universe_proposal"]["universe_subject_sha256"]
        == EXPECTED["universe_subject_sha256"],
        "authority subject digest differs",
    )

    approved = sorted(APPROVED)
    require(
        approved
        == sorted(universe["proposed_action_ids"])
        == sorted(binding["approved_action_ids"])
        and receipt["action_count"] == 17
        and receipt["action_set_sha256"]
        == sha256_json(approved)
        == EXPECTED["action_set_sha256"],
        "accepted 17-action set differs",
    )
    counts = Counter(row["disposition"] for row in universe["candidate_dispositions"])
    require(
        counts
        == {
            "proposed_in_scope_substantive": 16,
            "proposed_in_scope_non_directional": 1,
            "procedural_context": 26,
            "exact_action_ineligible": 7,
        }
        and not universe["unresolved_action_ids"],
        "accepted universe accounting differs",
    )
    for category, category_binding in binding["exclusion_categories"].items():
        ids = sorted(
            row["action_id"]
            for row in universe["candidate_dispositions"]
            if row["disposition"] == category
        )
        require(
            ids == sorted(category_binding["action_ids"])
            and category_binding["action_count"] == len(ids)
            and category_binding["action_set_sha256"] == sha256_json(ids),
            f"{category} authority accounting differs",
        )

    require(
        complete_inventory["complete_official_action_count"] == 638
        and complete_inventory["cutoff"]["latest_action_id"] == "house:119:2:283"
        and complete_inventory["complete_official_action_id_set_sha256"]
        == binding["complete_house_action_set"]["action_set_sha256"]
        == EXPECTED["complete_action_set_sha256"]
        and complete_inventory["complete_official_action_inventory_sha256"]
        == binding["complete_official_inventory"]["inventory_sha256"]
        == EXPECTED["complete_inventory_sha256"]
        and canonical_file_sha256(COMPLETE_INVENTORY_PATH)
        == binding["complete_official_inventory"]["file_sha256"],
        "complete official inventory binding differs",
    )
    require(
        source_inventory["inventory_sha256"]
        == binding["source_inventory"]["inventory_sha256"]
        == EXPECTED["source_inventory_sha256"]
        and canonical_file_sha256(SOURCE_INVENTORY_PATH)
        == binding["source_inventory"]["file_sha256"],
        "source inventory binding differs",
    )
    require(
        binding["accepted_pull_request"]
        == {"number": 162, "head_sha": EXPECTED["accepted_head"]},
        "reviewed PR identity differs",
    )
    constraints = binding["accepted_boundary_constraints"]
    require(
        not constraints["house:119:1:79"]["parent_measure_inference_sufficient"]
        and constraints["house:119:1:79"]["separate_same_parent_action"]
        == "house:119:1:83"
        and constraints["house:119:1:146"]["primary_policy_area"] == "Commerce"
        and not constraints["house:119:1:146"][
            "exclusive_or_primary_education_classification"
        ]
        and constraints["house:119:1:315"]["primary_policy_area"]
        == "Public Lands and Natural Resources"
        and not constraints["house:119:1:315"][
            "general_education_funding_position_authorized"
        ],
        "accepted cross-domain constraints differ",
    )
    economy = binding["held_domain_boundaries"]["ECONOMY_TAXES"]
    require(
        economy["action_ids"] == ECONOMY_HELD
        and economy["action_set_sha256"] == sha256_json(ECONOMY_HELD)
        and not economy["selection_ready"],
        "Economy hold differs",
    )
    require(
        all(value is False for value in binding["downstream_authorizations"].values()),
        "authority grants downstream authorization",
    )

    state = current["active_universe_selection_milestone"]
    identity = state["universe_authority_receipt_identity"]
    require(
        state["milestone_state"] == "completed_independent_review_approved"
        and state["authority_status"] == "approved_content_bound"
        and identity["id"] == receipt["receipt_id"]
        and identity["sha256"] == EXPECTED["receipt_sha256"]
        and identity["universe_subject_sha256"] == EXPECTED["universe_subject_sha256"]
        and identity["approved_action_set_sha256"] == EXPECTED["action_set_sha256"],
        "current-state authority parity differs",
    )
    protected = subprocess.run(
        ["git", "diff", "--quiet", BASE, "--", *PROTECTED_PATHS],
        cwd=ROOT,
        check=False,
    )
    require(protected.returncode == 0, "protected accepted-domain artifact changed")
    return {
        "status": "pass",
        "receipt_id": receipt["receipt_id"],
        "receipt_sha256": EXPECTED["receipt_sha256"],
        "universe_subject_sha256": EXPECTED["universe_subject_sha256"],
        "accepted_action_set_sha256": EXPECTED["action_set_sha256"],
        "accepted_action_count": 17,
        "economy_held_count": 6,
        "protected_active_domain_regressions": 0,
    }


def main() -> int:
    try:
        print(json.dumps(validate_repository(), sort_keys=True))
    except (UniverseAuthorityError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
