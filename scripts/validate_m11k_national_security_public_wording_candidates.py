"""Validate exact M11K wording candidates, upstream identities, and state."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_public_wording_candidates import verify_seal  # noqa: E402
from backend.app.etl.full_record_source_readiness import canonical_file_sha256  # noqa: E402
from backend.scripts.build_m11k_national_security_public_wording_candidates import (  # noqa: E402
    DECISION_SCHEMA_PATH,
    DECISION_TEMPLATE_PATH,
    DOSSIER_PATH,
    M11H_AUTHORITY_FILE_SHA256,
    M11H_AUTHORITY_PATH,
    M11H_IMPLEMENTATION_FILE_SHA256,
    M11H_IMPLEMENTATION_PATH,
    M11J_AUTHORITY_FILE_SHA256,
    M11J_AUTHORITY_PATH,
    M11J_IMPLEMENTATION_FILE_SHA256,
    M11J_IMPLEMENTATION_PATH,
    PACKAGE_PATH,
    PACKAGE_SCHEMA_PATH,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    POST_M11J_MAIN,
    build,
)
from scripts.validate_public_wording_candidate_package_v1 import validate_paths  # noqa: E402


CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_repository() -> dict[str, Any]:
    build(check=True)
    package = load(PACKAGE_PATH)
    decision = load(DECISION_TEMPLATE_PATH)
    parity = load(PARITY_PATH)
    generic = validate_paths(
        package_path=PACKAGE_PATH,
        decision_template_path=DECISION_TEMPLATE_PATH,
        parity_path=PARITY_PATH,
        behavioral_authority_path=M11H_AUTHORITY_PATH,
        behavioral_implementation_path=M11H_IMPLEMENTATION_PATH,
        synthesis_authority_path=M11J_AUTHORITY_PATH,
        synthesis_implementation_path=M11J_IMPLEMENTATION_PATH,
        package_schema_path=PACKAGE_SCHEMA_PATH,
        decision_schema_path=DECISION_SCHEMA_PATH,
        parity_schema_path=PARITY_SCHEMA_PATH,
    )
    verify_seal(parity, "parity_subject_sha256", "M11K parity")
    require(
        canonical_file_sha256(M11H_AUTHORITY_PATH) == M11H_AUTHORITY_FILE_SHA256
        and canonical_file_sha256(M11H_IMPLEMENTATION_PATH)
        == M11H_IMPLEMENTATION_FILE_SHA256
        and canonical_file_sha256(M11J_AUTHORITY_PATH) == M11J_AUTHORITY_FILE_SHA256
        and canonical_file_sha256(M11J_IMPLEMENTATION_PATH)
        == M11J_IMPLEMENTATION_FILE_SHA256,
        "accepted M11H/M11J files changed",
    )
    subject = package["subject"]
    require(
        subject["base_binding"]["post_m11j_main"] == POST_M11J_MAIN,
        "post-M11J base differs",
    )
    require(
        subject["wording_item_accounting"]
        == {
            "issue_overview": 1,
            "synthesis": 2,
            "repeated_pattern": 8,
            "trajectory": 1,
            "notable_choice": 6,
        },
        "wording item accounting differs",
    )
    require(
        subject["source_accounting"]
        == {
            "behavioral_proposition_count": 15,
            "synthesis_record_count": 2,
            "behavioral_primary_wording_count": 15,
            "synthesis_primary_wording_count": 2,
        },
        "semantic source accounting differs",
    )
    require(
        len(subject["complete_behavioral_synthesis_role_accounting"]) == 15,
        "15-proposition synthesis-role accounting differs",
    )
    require(
        subject["blocked_actions"]
        == [
            {
                "action_id": "house:119:2:278",
                "disposition": "source_blocked_uninterpreted_outside_behavioral_semantic_ir",
            }
        ],
        "blocked-action boundary differs",
    )
    items = {row["wording_item_id"]: row for row in subject["wording_items"]}
    ukraine = items["wording:pattern:ukraine-assistance"]
    require(
        ukraine["primary_sentence"]
        == "Opposed three proposals to restrict Ukraine aid and supported one measure authorizing support for Ukraine."
        and ukraine["direction_display"] is None
        and ukraine["semantic_source_bindings"][0]["source_direction"] == "mixed"
        and "Mixed on Ukraine aid" in ukraine["prohibited_inference_risks"],
        "Ukraine semantic guard differs",
    )
    require(
        all(
            not any(row["downstream_authorizations"].values())
            and row["accepted"] is False
            and row["canonical_public_copy"] is False
            for row in items.values()
        ),
        "wording authority leaked",
    )
    require(
        decision["authorizing"] is False
        and decision["production_selectable"] is False
        and all(row["decision"] is None for row in decision["wording_decisions"]),
        "decision template self-authorized",
    )
    state = load(CURRENT_STATE_PATH)
    require(
        state["active_synthesis_decision_milestone"]["milestone_state"]
        == "completed_human_mechanical_review_merged"
        and state["active_synthesis_decision_milestone"]["post_merge_main"]
        == POST_M11J_MAIN,
        "M11J closeout state differs",
    )
    m11k = state["active_public_wording_candidate_milestone"]
    require(
        m11k["milestone_state"]
        == "candidate_package_complete_pending_human_substantive_wording_review"
        and m11k["wording_item_count"] == 18
        and not any(m11k["downstream_authorizations"].values()),
        "M11K current state differs",
    )
    require(DOSSIER_PATH.is_file(), "M11K dossier missing")
    require(
        state["production_publication_state"]["active_publication"]["issue_id"]
        == "JUSTICE_PUBLIC_SAFETY",
        "Justice publication state changed",
    )
    return {
        **generic,
        "package_file_sha256": canonical_file_sha256(PACKAGE_PATH),
        "decision_template_file_sha256": canonical_file_sha256(DECISION_TEMPLATE_PATH),
        "parity_file_sha256": canonical_file_sha256(PARITY_PATH),
        "package_subject_sha256": package[
            "public_wording_candidate_package_subject_sha256"
        ],
        "decision_template_subject_sha256": decision[
            "decision_template_subject_sha256"
        ],
        "parity_subject_sha256": parity["parity_subject_sha256"],
        "ukraine_semantic_guard": "pass",
        "downstream_authorizations_false": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate_repository(), indent=2, sort_keys=True))
