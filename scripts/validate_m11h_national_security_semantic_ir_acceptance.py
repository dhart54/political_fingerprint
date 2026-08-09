"""Validate exact M11H identities, regeneration, state, and authority boundary."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.scripts.build_m11h_national_security_semantic_ir_acceptance import (  # noqa: E402
    ACCEPTED_M11G_HEAD,
    AUTHORITY_PATH,
    AUTHORITY_SCHEMA_PATH,
    BLOCKED_ACTION_ID,
    CANDIDATE_FILE_SHA256,
    CANDIDATE_PATH,
    IMPLEMENTATION_PATH,
    IMPLEMENTATION_SCHEMA_PATH,
    M11F_AUTHORITY_PATH,
    M11F_IMPLEMENTATION_PATH,
    M11D_IMPLEMENTATION_PATH,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    POST_M11G_MERGE_MAIN,
    build,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
)
from scripts.validate_behavioral_semantic_ir_decision_implementation_v1 import (  # noqa: E402
    validate_paths,
)


CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"


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
        candidate_path=CANDIDATE_PATH,
        m11f_authority_path=M11F_AUTHORITY_PATH,
        m11f_implementation_path=M11F_IMPLEMENTATION_PATH,
        m11d_implementation_path=M11D_IMPLEMENTATION_PATH,
        authority_schema_path=AUTHORITY_SCHEMA_PATH,
        implementation_schema_path=IMPLEMENTATION_SCHEMA_PATH,
        blocked_action_id=BLOCKED_ACTION_ID,
    )
    parity = load(PARITY_PATH)
    from jsonschema import Draft7Validator

    Draft7Validator(load(PARITY_SCHEMA_PATH)).validate(parity)
    state = load(CURRENT_STATE_PATH)
    milestone = state["active_behavioral_semantic_ir_decision_milestone"]
    require(milestone["accepted_m11g_head"] == ACCEPTED_M11G_HEAD, "M11G head differs")
    require(
        milestone["post_m11g_merge_base"] == POST_M11G_MERGE_MAIN,
        "M11G merge base differs",
    )
    require(
        canonical_file_sha256(CANDIDATE_PATH) == CANDIDATE_FILE_SHA256,
        "M11G candidate changed",
    )
    require(
        milestone["milestone_state"] == "complete_pending_human_mechanical_review",
        "M11H state differs",
    )
    require(milestone["accepted_decision_count"] == 15, "M11H decision count differs")
    require(milestone["accepted_episode_count"] == 81, "M11H episode count differs")
    require(
        milestone["source_blocked_action_ids"] == [BLOCKED_ACTION_ID],
        "blocked action differs",
    )
    require(
        not any(milestone["downstream_authorizations"].values()),
        "downstream state leaked",
    )
    require(
        state["production_publication_state"]["active_publication"]["issue_id"]
        == "JUSTICE_PUBLIC_SAFETY",
        "Justice publication changed",
    )
    return {
        **generated,
        "authority_file_sha256": canonical_file_sha256(AUTHORITY_PATH),
        "implementation_file_sha256": canonical_file_sha256(IMPLEMENTATION_PATH),
        "parity_file_sha256": canonical_file_sha256(PARITY_PATH),
        "generic_validation": generic,
        "candidate_immutable": True,
        "justice_publication_unchanged": True,
        "downstream_authorizations_false": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate_repository(), indent=2, sort_keys=True))
