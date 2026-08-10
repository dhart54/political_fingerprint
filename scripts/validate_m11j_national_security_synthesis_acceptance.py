"""Validate exact M11J synthesis authority, implementation, and state."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_source_readiness import canonical_file_sha256  # noqa: E402
from backend.app.etl.full_record_synthesis_decisions import verify_seal  # noqa: E402
from backend.scripts.build_m11j_national_security_synthesis_acceptance import (  # noqa: E402
    ACCEPTED_M11I_HEAD,
    ASSISTANCE_ID,
    AUTHORITY_PATH,
    AUTHORITY_SCHEMA_PATH,
    DOSSIER_PATH,
    IMPLEMENTATION_PATH,
    IMPLEMENTATION_SCHEMA_PATH,
    M11H_AUTHORITY_PATH,
    M11H_IMPLEMENTATION_PATH,
    PACKAGE_FILE_SHA256,
    PACKAGE_PATH,
    PACKAGE_SUBJECT_SHA256,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    POST_M11I_MERGE_MAIN,
    REVISED_ASSISTANCE_PROPOSITION,
    TEMPLATE_PATH,
    UKRAINE_DIRECTION_LIMITATION,
    WAR_POWERS_ID,
    build,
)
from scripts.validate_synthesis_decision_implementation_v1 import (  # noqa: E402
    validate_paths,
)


CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"
AUTHORITY_FILE_SHA256 = (
    "4fd4f7b1490415df3c1f10cc088fcc95d9f48f3eec3504b9312cb447b8e0a1cc"
)
AUTHORITY_SUBJECT_SHA256 = (
    "fdbf0b068e117322da5388c3ebc17c21d2b9a3bfbc81f4e7b92654972a9fe407"
)
IMPLEMENTATION_FILE_SHA256 = (
    "bd2a08caa9100cf3b5326cb739f0ce99db2f6c4650667df8087dc254d1509500"
)
IMPLEMENTATION_SUBJECT_SHA256 = (
    "d960dd7512b36c6b5b0d10c4cecc0c66251906ac624873e8618e7168bf50333f"
)
PARITY_FILE_SHA256 = "0405ef569cff277e861f1453707d22427b9191c2d3bad5033d4704625190211e"
PARITY_SUBJECT_SHA256 = (
    "e988811fd6d0a2d70a480cb9da8beab2912383d34ffa4b837cdc918a9ba88a95"
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_repository() -> dict[str, Any]:
    generated = build(check=True)
    generic = validate_paths(
        authority_path=AUTHORITY_PATH,
        implementation_path=IMPLEMENTATION_PATH,
        package_path=PACKAGE_PATH,
        decision_template_path=TEMPLATE_PATH,
        m11h_authority_path=M11H_AUTHORITY_PATH,
        m11h_implementation_path=M11H_IMPLEMENTATION_PATH,
        authority_schema_path=AUTHORITY_SCHEMA_PATH,
        implementation_schema_path=IMPLEMENTATION_SCHEMA_PATH,
    )
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    package = load(PACKAGE_PATH)
    parity = load(PARITY_PATH)
    Draft7Validator(load(PARITY_SCHEMA_PATH)).validate(parity)
    verify_seal(parity, "parity_subject_sha256", "M11J parity")
    require(
        canonical_file_sha256(PACKAGE_PATH) == PACKAGE_FILE_SHA256
        and package["synthesis_candidate_package_subject_sha256"]
        == PACKAGE_SUBJECT_SHA256,
        "immutable M11I package differs",
    )
    require(
        canonical_file_sha256(AUTHORITY_PATH) == AUTHORITY_FILE_SHA256
        and authority["authority_subject_sha256"] == AUTHORITY_SUBJECT_SHA256,
        "M11J authority identity differs",
    )
    require(
        canonical_file_sha256(IMPLEMENTATION_PATH) == IMPLEMENTATION_FILE_SHA256
        and implementation["implementation_subject_sha256"]
        == IMPLEMENTATION_SUBJECT_SHA256,
        "M11J implementation identity differs",
    )
    require(
        canonical_file_sha256(PARITY_PATH) == PARITY_FILE_SHA256
        and parity["parity_subject_sha256"] == PARITY_SUBJECT_SHA256,
        "M11J parity identity differs",
    )
    require(
        authority["subject"]["decision_accounting"]
        == {
            "accept_candidate_as_written": 1,
            "accept_with_bounded_revision": 1,
            "rejected": 0,
            "unresolved": 0,
        },
        "exact human decision accounting differs",
    )
    records = {
        row["synthesis_candidate_id"]: row
        for row in implementation["subject"]["implementation_records"]
    }
    require(
        records[WAR_POWERS_ID]["implemented_synthesis_content"]
        == records[WAR_POWERS_ID]["original_candidate_content"],
        "War Powers accepted-as-written content differs",
    )
    assistance = records[ASSISTANCE_ID]
    implemented = assistance["implemented_synthesis_content"]
    require(
        assistance["original_candidate_content"]["synthesis_candidate_subject_sha256"]
        == "59756705710182825d8da8154b82478475e481918a4018e31c509015e7ab61f2"
        and implemented["proposition"] == REVISED_ASSISTANCE_PROPOSITION
        and implemented["direction"] == "mixed"
        and implemented["synthesis_type"] == "interpretive_boundary"
        and UKRAINE_DIRECTION_LIMITATION in implemented["material_limitations"],
        "bounded assistance implementation differs",
    )
    roles = {
        row["proposition_id"]: row["relationship_role"]
        for row in implemented["input_bindings"]
    }
    require(
        roles
        == {
            "pattern-ukraine-assistance-mixed": "primary_support",
            "pattern-jordan-assistance-restriction-opposition": "primary_support",
            "notable-taiwan-security-cooperation-funding": "contextual_support",
            "notable-israel-foreign-military-financing-reduction": "contrast",
        },
        "assistance relationship roles differ",
    )
    require(
        implementation["subject"]["final_accounting"]
        == {
            "canonical_internal_synthesis_count": 2,
            "unique_behavioral_proposition_input_count": 8,
            "candidate_episode_reference_count": 18,
            "candidate_action_reference_count": 18,
            "cross_candidate_episode_overlap_count": 0,
            "cross_candidate_action_overlap_count": 0,
            "standalone_proposition_count": 7,
        },
        "non-inflated synthesis accounting differs",
    )
    require(
        all(
            row["source_direction_semantic_guard"]["semantic_claim_basis"]
            == "accepted_behavioral_proposition_content"
            and row["source_direction_semantic_guard"][
                "mixed_direction_alone_establishes_mixed_policy_orientation"
            ]
            is False
            for row in records.values()
        ),
        "source-direction semantic guard differs",
    )
    state = load(CURRENT_STATE_PATH)
    m11i = state["active_synthesis_candidate_milestone"]
    m11j = state["active_synthesis_decision_milestone"]
    require(
        m11i["accepted_head"] == ACCEPTED_M11I_HEAD
        and m11i["post_merge_main"] == POST_M11I_MERGE_MAIN
        and m11i["milestone_state"] == "completed_human_substantive_review_merged",
        "M11I accepted state differs",
    )
    require(
        m11j["post_m11i_merge_base"] == POST_M11I_MERGE_MAIN
        and m11j["milestone_state"] == "complete_pending_human_mechanical_review"
        and not any(m11j["downstream_authorizations"].values()),
        "M11J current-state boundary differs",
    )
    require(DOSSIER_PATH.is_file(), "M11J review dossier missing")
    require(
        state["production_publication_state"]["active_publication"]["issue_id"]
        == "JUSTICE_PUBLIC_SAFETY",
        "Justice publication state changed",
    )
    return {
        **generated,
        "generic_validation": generic,
        "authority_file_sha256": AUTHORITY_FILE_SHA256,
        "implementation_file_sha256": IMPLEMENTATION_FILE_SHA256,
        "parity_file_sha256": PARITY_FILE_SHA256,
        "immutable_m11i_package": True,
        "source_direction_semantic_guard": "pass",
        "downstream_authorizations_false": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate_repository(), indent=2, sort_keys=True))
