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
EXPECTED_AUTHORITY_FILE_SHA256 = (
    "d1de0f28a09a01ea9b5bbe5607128564daa6aedb929a2be1255cb50f1a99fc93"
)
EXPECTED_AUTHORITY_SUBJECT_SHA256 = (
    "22262c77622df938b3ab3642bf49452005b549706bb20160dd7c91a88ba29714"
)
EXPECTED_IMPLEMENTATION_FILE_SHA256 = (
    "13927cade21c85f95c097acf7afe831e55bdb0de79c93e54646e14640d444ecc"
)
EXPECTED_IMPLEMENTATION_SUBJECT_SHA256 = (
    "6113be3d0fad4d8da21a47ed76c089f5a7d96becd45abb9c888cf2a437bf8d67"
)
EXPECTED_PARITY_SUBJECT_SHA256 = (
    "fcd319db713eb15d65c5cef380d9800db51a3ab1d578925a6131ed63ae78859e"
)
ACCEPTED_M11H_HEAD = "211691c367f653539146b9b52931093f93def3a0"
POST_M11H_MERGE_MAIN = "21ea1a201cdfb58ff66af0abf98fb1ea49b1b9f6"
EXPECTED_PROPOSITION_ACCOUNTING = {
    "total": 15,
    "repeated_pattern": 8,
    "trajectory": 1,
    "notable_choice": 6,
    "primary_conclusion_relevance": 8,
    "limiting_conclusion_relevance": 1,
    "excluded_conclusion_relevance": 6,
}
EXPECTED_EPISODE_ACCOUNTING = {
    "accepted_episode_count": 81,
    "repeated_pattern_evidence_episode_count": 24,
    "trajectory_evidence_episode_count": 2,
    "notable_choice_evidence_episode_count": 6,
    "contrast_only_episode_count": 24,
    "no_safe_proposition_episode_count": 25,
    "primary_overlap_count": 0,
}
EXPECTED_FINAL_ACCOUNTING = {
    "accepted_proposition_count": 15,
    "repeated_pattern_count": 8,
    "trajectory_count": 1,
    "notable_choice_count": 6,
    "primary_evidence_episode_count": 32,
    "primary_overlap_count": 0,
    "accepted_episode_count": 81,
    "contrast_only_episode_count": 24,
    "no_safe_proposition_episode_count": 25,
    "blocked_action_count": 1,
}


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
    )
    parity = load(PARITY_PATH)
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    candidate = load(CANDIDATE_PATH)
    from jsonschema import Draft7Validator

    Draft7Validator(load(PARITY_SCHEMA_PATH)).validate(parity)
    require(
        canonical_file_sha256(AUTHORITY_PATH) == EXPECTED_AUTHORITY_FILE_SHA256
        and authority["authority_subject_sha256"] == EXPECTED_AUTHORITY_SUBJECT_SHA256,
        "accepted M11H authority identity differs",
    )
    require(
        canonical_file_sha256(IMPLEMENTATION_PATH)
        == EXPECTED_IMPLEMENTATION_FILE_SHA256
        and implementation["implementation_subject_sha256"]
        == EXPECTED_IMPLEMENTATION_SUBJECT_SHA256,
        "accepted M11H implementation identity differs",
    )
    require(
        parity["parity_subject_sha256"] == EXPECTED_PARITY_SUBJECT_SHA256,
        "accepted M11H parity identity differs",
    )
    require(
        authority["subject"]["decision_accounting"]
        == {"accept_candidate_as_written": 15}
        and authority["subject"]["accepted_proposition_accounting"]
        == EXPECTED_PROPOSITION_ACCOUNTING,
        "exact M11H proposition accounting differs",
    )
    require(
        authority["subject"]["accepted_episode_disposition_accounting"]
        == EXPECTED_EPISODE_ACCOUNTING
        and implementation["subject"]["accepted_episode_disposition_accounting"]
        == EXPECTED_EPISODE_ACCOUNTING
        and implementation["subject"]["final_accounting"] == EXPECTED_FINAL_ACCOUNTING,
        "exact M11H episode/final accounting differs",
    )
    blocked = {row["action_id"] for row in authority["subject"]["blocked_actions"]}
    require(blocked == {BLOCKED_ACTION_ID}, "exact M11H blocked set differs")
    propositions = candidate["compiled_candidate_ir"]["proposition_graph"][
        "propositions"
    ]
    ukraine = next(
        row
        for row in propositions
        if row["proposition_id"] == "pattern-ukraine-assistance-mixed"
    )
    trajectory = next(
        row
        for row in propositions
        if row["proposition_id"]
        == "trajectory-milcon-va-appropriations-direction-change"
    )
    require(ukraine["direction"] == "mixed", "Ukraine direction differs")
    require(
        trajectory["direction"] == "mixed"
        and trajectory["conclusion_relevance"] == "limiting",
        "MilCon/VA trajectory state differs",
    )
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
        milestone["milestone_state"] == "completed_human_reviewed_accepted_merged",
        "M11H state differs",
    )
    require(milestone["accepted_pr"] == 140, "M11H accepted PR differs")
    require(
        milestone["accepted_head"] == ACCEPTED_M11H_HEAD,
        "M11H accepted head differs",
    )
    require(
        milestone["post_merge_main"] == POST_M11H_MERGE_MAIN,
        "M11H post-merge main differs",
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
    synthesis = state["active_synthesis_candidate_milestone"]
    require(
        synthesis["post_m11h_merge_base"] == POST_M11H_MERGE_MAIN
        and synthesis["accepted_m11h_head"] == ACCEPTED_M11H_HEAD,
        "M11I upstream M11H binding differs",
    )
    require(
        synthesis["milestone_state"] == "completed_human_substantive_review_merged"
        and synthesis["authority_effect"]
        == "detached_non_authorizing_synthesis_candidates_only",
        "M11I candidate state differs",
    )
    require(
        synthesis["accepted_head"] == "8535163aee1d2a548ec7d0c23935b1322a05b863"
        and synthesis["post_merge_main"] == "e9e771b23eb65629e0a3ed7ecb6c32748d7ebf59",
        "accepted M11I merge identity differs",
    )
    require(
        not any(synthesis["downstream_authorizations"].values()),
        "M11I downstream state leaked",
    )
    require(
        state["production_publication_state"]["active_publication"]["issue_id"]
        == "JUSTICE_PUBLIC_SAFETY",
        "Justice publication changed",
    )
    return {
        **generated,
        "authority_file_sha256": EXPECTED_AUTHORITY_FILE_SHA256,
        "implementation_file_sha256": EXPECTED_IMPLEMENTATION_FILE_SHA256,
        "parity_file_sha256": canonical_file_sha256(PARITY_PATH),
        "generic_validation": generic,
        "candidate_immutable": True,
        "justice_publication_unchanged": True,
        "downstream_authorizations_false": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate_repository(), indent=2, sort_keys=True))
