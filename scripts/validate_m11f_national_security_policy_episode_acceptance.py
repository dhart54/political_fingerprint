"""Independently validate M11F policy-episode authority and implementation."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_policy_episode_decisions import (  # noqa: E402
    validate_authority,
    validate_implementation,
)
from backend.app.etl.full_record_source_readiness import canonical_file_sha256  # noqa: E402
from backend.scripts.build_m11f_national_security_policy_episode_acceptance import (  # noqa: E402
    ACCEPTED_M11E_HEAD,
    ACCEPTED_M11E_PR,
    AUTHORITY_PATH,
    AUTHORITY_SCHEMA_PATH,
    BLOCKED_ACTION_ID,
    CANDIDATE_FILE_SHA256,
    CANDIDATE_PATH,
    CANDIDATE_SUBJECT_SHA256,
    DECISION_TEMPLATE_FILE_SHA256,
    DECISION_TEMPLATE_PATH,
    DECISION_TEMPLATE_SUBJECT_SHA256,
    IMPLEMENTATION_PATH,
    IMPLEMENTATION_SCHEMA_PATH,
    M11D_IMPLEMENTATION_FILE_SHA256,
    M11D_IMPLEMENTATION_PATH,
    M11D_IMPLEMENTATION_SUBJECT_SHA256,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    POST_M11E_MERGE_MAIN,
    REJECTED_EPISODE_IDS,
    build,
)
from scripts.validate_m11a_universe_authority import (  # noqa: E402
    validate_repository as validate_m11a,
)
from scripts.validate_m11b_national_security_source_readiness import (  # noqa: E402
    validate_repository as validate_m11b,
)
from scripts.validate_m11c_national_security_action_interpretation import (  # noqa: E402
    validate_repository as validate_m11c,
)
from scripts.validate_m11d_national_security_action_meaning_acceptance import (  # noqa: E402
    validate_repository as validate_m11d,
)
from scripts.validate_m11e_national_security_policy_episode_candidates import (  # noqa: E402
    validate_repository as validate_m11e,
)


CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_schema(path: Path, value: dict[str, Any]) -> None:
    schema = load(path)
    Draft7Validator.check_schema(schema)
    errors = list(Draft7Validator(schema).iter_errors(value))
    require(not errors, f"{path.name}: {errors[0].message if errors else ''}")


def validate_repository() -> dict[str, Any]:
    upstream = {
        "m11a": validate_m11a(),
        "m11b": validate_m11b(),
        "m11c": validate_m11c(),
        "m11d": validate_m11d(),
        "m11e": validate_m11e(),
    }
    candidate = load(CANDIDATE_PATH)
    template = load(DECISION_TEMPLATE_PATH)
    m11d = load(M11D_IMPLEMENTATION_PATH)
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    parity = load(PARITY_PATH)
    require(
        canonical_file_sha256(CANDIDATE_PATH) == CANDIDATE_FILE_SHA256
        and candidate["episode_candidate_subject_sha256"] == CANDIDATE_SUBJECT_SHA256,
        "accepted M11E candidate identity differs",
    )
    require(
        canonical_file_sha256(DECISION_TEMPLATE_PATH) == DECISION_TEMPLATE_FILE_SHA256
        and template["decision_template_subject_sha256"]
        == DECISION_TEMPLATE_SUBJECT_SHA256,
        "accepted M11E decision template differs",
    )
    require(
        canonical_file_sha256(M11D_IMPLEMENTATION_PATH)
        == M11D_IMPLEMENTATION_FILE_SHA256
        and m11d["implementation_subject_sha256"] == M11D_IMPLEMENTATION_SUBJECT_SHA256,
        "accepted M11D implementation differs",
    )
    accepted_single_ids = {
        row["episode_id"]
        for row in candidate["subject"]["episodes"]
        if row["episode_id"] not in REJECTED_EPISODE_IDS
    }
    decision_counts = validate_authority(
        authority,
        candidate=candidate,
        accepted_single_episode_ids=accepted_single_ids,
        rejected_episode_ids=REJECTED_EPISODE_IDS,
    )
    accounting = validate_implementation(
        implementation,
        authority=authority,
        m11d_records=m11d["subject"]["implementation_records"],
        blocked_action_id=BLOCKED_ACTION_ID,
        rejected_episode_ids=REJECTED_EPISODE_IDS,
    )
    validate_schema(AUTHORITY_SCHEMA_PATH, authority)
    validate_schema(IMPLEMENTATION_SCHEMA_PATH, implementation)
    validate_schema(PARITY_SCHEMA_PATH, parity)
    require(
        parity["parity_state"] == "pass" and parity["generated_last"] is True,
        "parity state differs",
    )
    for row in parity["referenced_artifacts"]:
        require(
            canonical_file_sha256(ROOT / row["path"]) == row["final_file_sha256"],
            "parity file digest differs",
        )
    binding = authority["subject"]["candidate_binding"]
    require(
        binding["accepted_pr"] == ACCEPTED_M11E_PR
        and binding["accepted_head"] == ACCEPTED_M11E_HEAD
        and binding["post_merge_main"] == POST_M11E_MERGE_MAIN,
        "accepted PR/head/base binding differs",
    )
    state = load(CURRENT_STATE_PATH)
    milestone = state["active_policy_episode_decision_milestone"]
    require(
        milestone["milestone_state"] == "complete_pending_human_mechanical_review"
        and milestone["accepted_episode_count"] == 81
        and milestone["single_action_episode_count"] == 81
        and milestone["multi_action_episode_count"] == 0
        and milestone["cross_measure_episode_count"] == 0
        and not any(milestone["downstream_authorizations"].values()),
        "current-state M11F boundary differs",
    )
    require(
        state["production_publication_state"]["active_publication"]["issue_id"]
        == "JUSTICE_PUBLIC_SAFETY",
        "Justice publication reference changed",
    )
    generated = build(check=True)
    return {
        "upstream": upstream,
        "decision_accounting": decision_counts,
        "episode_accounting": accounting,
        "authority_file_sha256": canonical_file_sha256(AUTHORITY_PATH),
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_file_sha256": canonical_file_sha256(IMPLEMENTATION_PATH),
        "implementation_subject_sha256": implementation[
            "implementation_subject_sha256"
        ],
        "parity_file_sha256": canonical_file_sha256(PARITY_PATH),
        "parity_subject_sha256": parity["parity_subject_sha256"],
        "deterministic": generated,
    }


if __name__ == "__main__":
    print(json.dumps(validate_repository(), sort_keys=True))
