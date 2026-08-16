from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    SourceReadinessError,
    canonical_file_sha256,
    load_json,
    validate_artifact,
)
from backend.app.etl.universe_discovery import (  # noqa: E402
    load_house_clerk_member_actions,
)
from scripts.validate_m11b_national_security_source_readiness import (  # noqa: E402
    _validate_record,
    validate_repository as validate_m11b,
)
from scripts.validate_m12a_universe_authority import (  # noqa: E402
    validate_repository as validate_m12a,
)


ARTIFACT_PATH = ROOT / (
    "docs/editorial/full_record_reviews/source_readiness/"
    "f000477_environment_energy_119_interpretation_source_readiness_v1.json"
)
SCHEMA_PATH = ROOT / (
    "docs/methodology/full_record_interpretation_source_readiness_v1.schema.json"
)
AUTHORITY_PATH = ROOT / (
    "docs/editorial/full_record_reviews/"
    "f000477_environment_energy_119_full_issue_universe_authority_receipt_v1.json"
)
M12A_ROOT = ROOT / "docs/editorial/cross_issue_full_record_expansion_m12a_v1"
PROPOSAL_PATH = M12A_ROOT / "selected_domain_universe_proposal.json"
SELECTION_PATH = M12A_ROOT / "domain_selection.json"
INVENTORY_PATH = M12A_ROOT / "source_inventory.json"
CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"
CLERK_DIRS = (
    ROOT / ".local/m11a_house_clerk/2025",
    ROOT / ".local/m11a_house_clerk/2026",
)

EXPECTED_RECEIPT_SHA = (
    "58a0d7a4f59069d747629311fdf0680385d6d802b506d585699904859773a31e"
)
EXPECTED_ACTION_SET_SHA = (
    "843740a27ef191294bcf0cc3d2b29aeda1751351d775f8fadd7f44708e2312c8"
)
EXPECTED_UNIVERSE_SHA = (
    "29b42a593639a1c62745e959554596a40a8dbf8205e1b3a6af83234c8f49866e"
)
EXPECTED_SELECTION_SHA = (
    "e18fcf736f5febac352d823b35c5a81b2c18deb36fda26b41acbef0005755fa1"
)
EXPECTED_PROPOSAL_SHA = (
    "18967832549bd90353bc0d265f48793b6932bd7d57a49bcca95795820115f5ea"
)
EXPECTED_INVENTORY_SHA = (
    "e2b8d790cd9c16076241a8fb79215170718251eabf3b7b225280a7a5fe888ca8"
)
EXPECTED_COMPLETE_ACTION_SHA = (
    "a4d228a74004de61f78827ef85bd5a59cb4f5c3dddf9b55e9e3e154a44cd7fde"
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceReadinessError(message)


def validate_repository() -> dict[str, Any]:
    m12a = validate_m12a()
    m11b = validate_m11b()
    artifact = load_json(ARTIFACT_PATH)
    schema = load_json(SCHEMA_PATH)
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(artifact),
        key=lambda error: list(error.absolute_path),
    )
    _require(not errors, f"M12B schema failed: {errors[0].message if errors else ''}")

    authority = load_json(AUTHORITY_PATH)
    proposal = load_json(PROPOSAL_PATH)
    selection = load_json(SELECTION_PATH)
    inventory = load_json(INVENTORY_PATH)
    subject = artifact["subject"]
    approved = authority["approval_binding"]["approved_action_ids"]
    unresolved = set(
        authority["approval_binding"]["exclusion_categories"][
            "boundary_review_required"
        ]["action_ids"]
    )
    recorded = subject["action_ids"]

    _require(
        canonical_file_sha256(AUTHORITY_PATH)
        == EXPECTED_RECEIPT_SHA
        == artifact["input_bindings"]["authority_receipt"]["sha256"],
        "authority receipt binding mismatch",
    )
    _require(
        recorded == approved
        and len(recorded) == 63
        and len(set(recorded)) == 63
        and set(recorded) == set(proposal["proposed_action_ids"]),
        "63-action authority equality mismatch",
    )
    _require(
        not (set(recorded) & unresolved) and len(unresolved) == 25,
        "an unresolved M12A action entered M12B",
    )
    _require(
        subject["action_set_sha256"]
        == authority["action_set_sha256"]
        == m12a["approved_action_set_sha256"]
        == EXPECTED_ACTION_SET_SHA,
        "approved action-set digest mismatch",
    )
    _require(
        subject["universe_subject_sha256"]
        == proposal["universe_subject_sha256"]
        == m12a["universe_subject_sha256"]
        == EXPECTED_UNIVERSE_SHA,
        "universe-subject digest mismatch",
    )
    _require(
        selection["selection_sha256"]
        == m12a["selection_sha256"]
        == EXPECTED_SELECTION_SHA
        == artifact["input_bindings"]["selection"]["sha256"],
        "selection digest mismatch",
    )
    _require(
        m12a["proposal_sha256"] == EXPECTED_PROPOSAL_SHA,
        "proposal subject digest mismatch",
    )
    _require(
        inventory["inventory_sha256"]
        == authority["approval_binding"]["source_inventory"]["inventory_sha256"]
        == artifact["input_bindings"]["source_inventory"]["inventory_sha256"]
        == EXPECTED_INVENTORY_SHA,
        "source-inventory digest mismatch",
    )
    for name, path in (
        ("universe_proposal", PROPOSAL_PATH),
        ("source_inventory", INVENTORY_PATH),
    ):
        _require(
            artifact["input_bindings"][name]["sha256"] == canonical_file_sha256(path),
            f"{name} file digest mismatch",
        )
    _require(
        selection["complete_official_action_count"] == 638
        and inventory["complete_official_action_count"] == 638
        and selection["complete_official_action_set_sha256"]
        == inventory["complete_official_action_set_sha256"]
        == EXPECTED_COMPLETE_ACTION_SHA,
        "complete official action-set binding mismatch",
    )
    _require(
        subject["member_id"] == "F000477"
        and subject["legislator_id"] == "leg_valerie_p_foushee"
        and subject["issue_id"] == "ENVIRONMENT_ENERGY"
        and subject["congress"] == 119
        and subject["chamber"] == "house"
        and subject["official_cutoff"]
        == {"end_date": "2026-07-23", "latest_action_id": "house:119:2:283"},
        "subject or cutoff identity mismatch",
    )

    candidates = {
        row["action_id"]: row
        for row in proposal["candidate_dispositions"]
        if row["action_id"] in set(approved)
    }
    clerk_rows = {
        row["canonical_action_id"]: row
        for row in load_house_clerk_member_actions(CLERK_DIRS, bioguide_id="F000477")
    }
    records = subject["action_readiness"]
    _require(
        [record["action_id"] for record in records] == approved,
        "readiness record order or membership mismatch",
    )
    for record in records:
        _validate_record(
            record,
            candidate=candidates[record["action_id"]],
            clerk=clerk_rows[record["action_id"]],
        )

    aggregate = validate_artifact(artifact, repository_root=ROOT)
    _require(
        aggregate
        == {
            "total_action_count": 63,
            "ready_count": 63,
            "blocked_count": 0,
            "counts_by_readiness_state": {"ready_for_action_interpretation": 63},
        },
        "M12B readiness aggregate mismatch",
    )
    _require(
        m11b["total_action_count"] == 82
        and m11b["ready_count"] == 81
        and m11b["blocked_count"] == 1,
        "unchanged M11B backward-compatibility validation failed",
    )

    current = load_json(CURRENT_STATE_PATH)
    m11b_state = current["completed_m11b_source_readiness_milestone"]
    m12b_state = current["active_source_readiness_milestone"]
    _require(
        m11b_state["milestone"] == "m11b_national_security_source_readiness_v1"
        and m11b_state["accepted_head"] == "fcc988b867a49086d7545832f9575130aef0f8ea",
        "completed M11B state changed",
    )
    _require(
        m12b_state["milestone"] == "m12b_environment_energy_source_readiness_v1"
        and m12b_state["authority_effect"] == "source_readiness_only"
        and m12b_state["approved_universe_count"] == 63
        and m12b_state["interpretation_state"] == "not_started"
        and all(
            value is False for value in m12b_state["downstream_authorizations"].values()
        )
        and not m12b_state["publication_changes"]
        and not m12b_state["production_writes"],
        "M12B current state crossed the readiness-only boundary",
    )
    identity = m12b_state["interpretation_source_readiness_identity"]
    _require(
        identity
        == {
            "id": artifact["artifact_id"],
            "sha256": canonical_file_sha256(ARTIFACT_PATH),
            "source_readiness_subject_sha256": artifact[
                "source_readiness_subject_sha256"
            ],
            "ready_count": 63,
            "blocked_count": 0,
            "authorizing": False,
        },
        "M12B current-state artifact identity mismatch",
    )

    raw_paths = {
        ROOT / source["raw_provenance"]["governed_local_path"]
        for record in records
        for source in record["sources"]
    }
    return {
        "status": "pass",
        "artifact_id": artifact["artifact_id"],
        "artifact_sha256": canonical_file_sha256(ARTIFACT_PATH),
        "source_readiness_subject_sha256": artifact["source_readiness_subject_sha256"],
        "m12a_receipt_sha256": EXPECTED_RECEIPT_SHA,
        "unresolved_excluded_count": len(unresolved),
        "source_binding_count": sum(len(record["sources"]) for record in records),
        "unique_raw_source_count": len(raw_paths),
        "unique_raw_source_bytes": sum(path.stat().st_size for path in raw_paths),
        "m11b_backward_compatibility": "82_actions_81_ready_1_blocked_passed",
        **aggregate,
    }


def main() -> int:
    try:
        print(json.dumps(validate_repository(), sort_keys=True))
    except (SourceReadinessError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
