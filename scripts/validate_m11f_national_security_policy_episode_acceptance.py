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

CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"
M11A_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/f000477_national_security_foreign_119_full_issue_universe_authority_receipt_v1.json"
)
M11B_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/source_readiness/f000477_national_security_foreign_119_interpretation_source_readiness_v1.json"
)
M11C_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_candidates/f000477_national_security_foreign_119_v1/candidate_batch.json"
)
M11D_AUTHORITY_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions/f000477_national_security_foreign_119_v1/human_action_meaning_authority.json"
)

UPSTREAM_IDENTITIES = {
    "m11a": {
        "path": M11A_PATH,
        "identity_field": "receipt_id",
        "artifact_id": "universe-authority:f000477:national_security_foreign:119:v1",
        "file_sha256": "89b7a27236ab0256b867c2525627408d84c6493c982c474ec4de3c2c36e79c87",
        "subject_field": "universe_subject_sha256",
        "subject_sha256": "b1e1a4588a4fcef6beb9dfd836ff5c2f32d8fdb340359f11453c6a0c947a17a5",
    },
    "m11b": {
        "path": M11B_PATH,
        "identity_field": "artifact_id",
        "artifact_id": "interpretation-source-readiness:f000477:national_security_foreign:119:v1",
        "file_sha256": "acfd656ccce57e8ef0668bcedeb5c51b0ea6342097310db13236ffc5d16bf86c",
        "subject_field": "source_readiness_subject_sha256",
        "subject_sha256": "53af365c4b06d4cc96fdeba17a1d65c80d89ae960d8cf986b7a5bf9599ec51bd",
    },
    "m11c": {
        "path": M11C_PATH,
        "identity_field": "artifact_id",
        "artifact_id": "action-interpretation-candidates:f000477:national_security_foreign:119:v1",
        "file_sha256": "6d3c0c26d56b7ace999debbc45efc0945f27320425b0f2bda55aca013630543d",
        "subject_field": "interpretation_subject_sha256",
        "subject_sha256": "db88b7e4e5f180fa72f901132b56e8f41b975a5e12d102600b45a7df766ad840",
    },
    "m11d_authority": {
        "path": M11D_AUTHORITY_PATH,
        "identity_field": "artifact_id",
        "artifact_id": "human-action-interpretation-authority:f000477:national_security_foreign:119:v1",
        "file_sha256": "b67fc818a59e441055a6b6ca32ee0f09cc91c0eec1ec99e6d4f6cd61499cc544",
        "subject_field": "authority_subject_sha256",
        "subject_sha256": "cde23f35cf8f876909dc5e7b779dbb600f919dc4aaa36dcd37cd08aecbacfa82",
    },
}


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
    upstream = {}
    for stage, expected in UPSTREAM_IDENTITIES.items():
        value = load(expected["path"])
        require(
            canonical_file_sha256(expected["path"]) == expected["file_sha256"]
            and value[expected["identity_field"]] == expected["artifact_id"]
            and value[expected["subject_field"]] == expected["subject_sha256"],
            f"{stage} committed identity differs",
        )
        upstream[stage] = {
            "artifact_id": expected["artifact_id"],
            "file_sha256": expected["file_sha256"],
            expected["subject_field"]: expected["subject_sha256"],
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
        milestone["milestone_state"] == "completed_human_mechanically_accepted"
        and milestone["human_mechanical_review"] == "accepted"
        and milestone["accepted_pr"] == 138
        and milestone["accepted_head"] == "326baa61ec44c5a560b98e3208ec990ff9bd2308"
        and milestone["post_merge_main"] == "43caaf4b0087ab473ee771ed9c8c4acde68be554"
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
