"""Independently validate the M11E National Security episode candidates."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_policy_episode_candidates import (  # noqa: E402
    DOWNSTREAM_AUTHORIZATIONS,
    validate_candidate_batch,
    verify_seal,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
)
from backend.scripts.build_m11e_national_security_policy_episode_candidates import (  # noqa: E402
    ACCEPTED_M11D_HEAD,
    BATCH_ID,
    BATCH_PATH,
    BATCH_SCHEMA_PATH,
    CANDIDATE_PATH,
    DECISION_PATH,
    DECISION_SCHEMA_PATH,
    DOSSIER_PATH,
    IMPLEMENTATION_PATH,
    M11C_CANDIDATE_FILE_SHA256,
    M11C_CANDIDATE_ID,
    M11C_CANDIDATE_SUBJECT_SHA256,
    M11D_AUTHORITY_FILE_SHA256,
    M11D_AUTHORITY_ID,
    M11D_AUTHORITY_SUBJECT_SHA256,
    M11D_IMPLEMENTATION_FILE_SHA256,
    M11D_IMPLEMENTATION_ID,
    M11D_IMPLEMENTATION_SUBJECT_SHA256,
    MULTI_ACTION_DEFINITIONS,
    PARITY_PATH,
    PERMITTED_CROSS_MEASURE_SETS,
    POST_M11D_MERGE_MAIN,
    PROHIBITED_GROUPED_SETS,
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


CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"
EXPECTED_BATCH_FILE_SHA256 = (
    "907fe610aa859ae9ea43f1febd0f0e824bf081ccdeab6193ce4355989871df8b"
)
EXPECTED_BATCH_SUBJECT_SHA256 = (
    "3d2d14f2d9a9e76624a97202fbe648b70a3f71d20076ba76e9966f277954d7af"
)
EXPECTED_DECISION_FILE_SHA256 = (
    "bbc01ac460e410c9b7c1cd61964fd8e7d961b39c36b0d7174ef375686e2d8ca6"
)
EXPECTED_DECISION_SUBJECT_SHA256 = (
    "68d17d415851cf0e16bad5f1d787014004f88f2e5c50f4055b847d6854fec543"
)
EXPECTED_PARITY_FILE_SHA256 = (
    "a5a0d2bf7ee830b0062c8fc940a23184e1f68e947fc217525f17b0b49ab74ffb"
)
EXPECTED_PARITY_SUBJECT_SHA256 = (
    "d5a487792b5637ed8f5df3674f3ae875af4591d11956e27c2c54dae2b1b2b3ab"
)


class M11EValidationError(ValueError):
    """Raised when the M11E package fails an independent gate."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise M11EValidationError(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_schema(schema_path: Path, value: dict[str, Any]) -> None:
    schema = load(schema_path)
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema).iter_errors(value), key=lambda e: list(e.path)
    )
    require(not errors, f"{schema_path.name}: {errors[0].message if errors else ''}")


def validate_parity(parity: dict[str, Any]) -> None:
    verify_seal(parity, "parity_subject_sha256", "M11E parity")
    require(
        parity["parity_subject_sha256"] == EXPECTED_PARITY_SUBJECT_SHA256
        and canonical_file_sha256(PARITY_PATH) == EXPECTED_PARITY_FILE_SHA256,
        "parity identity differs",
    )
    require(
        parity["generated_last"] is True and parity["parity_state"] == "pass",
        "parity state differs",
    )
    for item in parity["referenced_artifacts"]:
        path = ROOT / item["path"]
        require(path.is_file(), f"missing parity artifact: {item['path']}")
        require(
            canonical_file_sha256(path) == item["final_file_sha256"],
            f"stale parity file digest: {item['path']}",
        )
        if "episode_candidate_subject_sha256" in item:
            require(
                load(path)["episode_candidate_subject_sha256"]
                == item["episode_candidate_subject_sha256"],
                "stale candidate subject in parity",
            )
        if "decision_template_subject_sha256" in item:
            require(
                load(path)["decision_template_subject_sha256"]
                == item["decision_template_subject_sha256"],
                "stale decision subject in parity",
            )


def validate_repository() -> dict[str, Any]:
    m11a = validate_m11a()
    m11b = validate_m11b()
    m11c = validate_m11c()
    m11d = validate_m11d()
    batch = load(BATCH_PATH)
    decision = load(DECISION_PATH)
    parity = load(PARITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    candidate = load(CANDIDATE_PATH)

    require(
        canonical_file_sha256(CANDIDATE_PATH) == M11C_CANDIDATE_FILE_SHA256
        and candidate["artifact_id"] == M11C_CANDIDATE_ID
        and candidate["interpretation_subject_sha256"] == M11C_CANDIDATE_SUBJECT_SHA256,
        "M11C input identity differs",
    )
    require(
        canonical_file_sha256(IMPLEMENTATION_PATH) == M11D_IMPLEMENTATION_FILE_SHA256
        and implementation["artifact_id"] == M11D_IMPLEMENTATION_ID
        and implementation["implementation_subject_sha256"]
        == M11D_IMPLEMENTATION_SUBJECT_SHA256,
        "M11D implementation identity differs",
    )
    bindings = batch["subject"]["input_bindings"]
    require(
        bindings["accepted_m11d_pr"] == 136
        and bindings["accepted_m11d_head"] == ACCEPTED_M11D_HEAD
        and bindings["post_m11d_merge_main"] == POST_M11D_MERGE_MAIN
        and bindings["m11d_authority"]
        == {
            "artifact_id": M11D_AUTHORITY_ID,
            "final_file_sha256": M11D_AUTHORITY_FILE_SHA256,
            "authority_subject_sha256": M11D_AUTHORITY_SUBJECT_SHA256,
        }
        and bindings["m11d_implementation"]
        == {
            "artifact_id": M11D_IMPLEMENTATION_ID,
            "final_file_sha256": M11D_IMPLEMENTATION_FILE_SHA256,
            "implementation_subject_sha256": M11D_IMPLEMENTATION_SUBJECT_SHA256,
        },
        "accepted M11D authority binding differs",
    )
    require(
        batch["artifact_id"] == BATCH_ID
        and batch["episode_candidate_subject_sha256"] == EXPECTED_BATCH_SUBJECT_SHA256
        and canonical_file_sha256(BATCH_PATH) == EXPECTED_BATCH_FILE_SHA256,
        "candidate identity differs",
    )
    accounting = validate_candidate_batch(
        batch=batch,
        implementation=implementation,
        candidate_artifact=candidate,
        permitted_cross_measure_sets=PERMITTED_CROSS_MEASURE_SETS,
        prohibited_grouped_sets=PROHIBITED_GROUPED_SETS,
        blocked_action_id="house:119:2:278",
    )
    require(
        accounting
        == {
            "episode_count": 74,
            "single_action_episode_count": 70,
            "multi_action_episode_count": 4,
            "cross_measure_episode_count": 4,
            "assigned_action_count": 81,
            "ambiguous_or_unassigned_count": 0,
            "blocked_count": 1,
        },
        "episode accounting differs",
    )
    expected_cross = {
        definition["episode_id"]: definition["action_ids"]
        for definition in MULTI_ACTION_DEFINITIONS
    }
    actual_cross = {
        row["episode_id"]: row["primary_action_ids"]
        for row in batch["subject"]["episodes"]
        if row["grouping_type"] == "cross_measure"
    }
    require(actual_cross == expected_cross, "cross-measure candidates differ")
    require(
        all(
            row["human_review_priority"] == "cross_measure_high"
            and row["competing_plausible_groupings"]
            and row["semantic_grouping_evidence"]
            for row in batch["subject"]["episodes"]
            if row["grouping_type"] == "cross_measure"
        ),
        "cross-measure human-review evidence differs",
    )
    implementation_ids = {
        row["action_id"] for row in implementation["subject"]["implementation_records"]
    }
    episode_ids = {
        action_id
        for episode in batch["subject"]["episodes"]
        for action_id in episode["primary_action_ids"]
    }
    accounting_ids = {row["action_id"] for row in batch["subject"]["action_accounting"]}
    require(
        implementation_ids == episode_ids == accounting_ids
        and len(episode_ids) == 81
        and "house:119:2:278" not in episode_ids,
        "81-action equality or blocked exclusion differs",
    )
    require(
        batch["subject"]["downstream_authorizations"] == DOWNSTREAM_AUTHORIZATIONS
        and all(
            value is False
            for value in batch["subject"]["downstream_authorizations"].values()
        ),
        "downstream authorization differs",
    )

    verify_seal(decision, "decision_template_subject_sha256", "decision template")
    require(
        canonical_file_sha256(DECISION_PATH) == EXPECTED_DECISION_FILE_SHA256
        and decision["decision_template_subject_sha256"]
        == EXPECTED_DECISION_SUBJECT_SHA256
        and decision["decision_state"] == "awaiting_human_policy_episode_review"
        and decision["decision_count"] == 74
        and decision["selected_batch_decision"] is None
        and all(
            row["selected_decision"] is None
            and row["reviewer_id"] is None
            and row["reviewer_authority"] is None
            for row in decision["decisions"]
        ),
        "empty human decision boundary differs",
    )
    require(
        {row["episode_id"] for row in decision["decisions"]}
        == {row["episode_id"] for row in batch["subject"]["episodes"]},
        "decision/episode equality differs",
    )
    validate_schema(BATCH_SCHEMA_PATH, batch)
    validate_schema(DECISION_SCHEMA_PATH, decision)
    validate_parity(parity)
    result = build(check=True)
    require(
        result["episode_candidate_subject_sha256"] == EXPECTED_BATCH_SUBJECT_SHA256,
        "deterministic regeneration differs",
    )
    dossier = DOSSIER_PATH.read_text(encoding="utf-8")
    require(
        all(episode_id in dossier for episode_id in expected_cross)
        and "Ambiguous or unassigned accepted actions: 0" in dossier
        and "H.R. 8800" in dossier,
        "human review dossier coverage differs",
    )

    current = load(CURRENT_STATE_PATH)
    m11d_state = current["active_action_interpretation_decision_milestone"]
    m11e_state = current["active_policy_episode_candidate_milestone"]
    require(
        m11d_state["milestone_state"] == "completed_human_accepted"
        and m11d_state["accepted_pr"] == 136
        and m11d_state["accepted_head"] == ACCEPTED_M11D_HEAD
        and m11d_state["post_merge_main"] == POST_M11D_MERGE_MAIN,
        "current-state M11D closeout differs",
    )
    require(
        m11e_state["post_m11d_merge_base"] == POST_M11D_MERGE_MAIN
        and m11e_state["milestone_state"]
        == "complete_pending_human_policy_episode_review"
        and m11e_state["proposed_episode_count"] == 74
        and m11e_state["single_action_episode_count"] == 70
        and m11e_state["multi_action_episode_count"] == 4
        and m11e_state["cross_measure_episode_count"] == 4
        and m11e_state["ambiguous_or_unassigned_action_count"] == 0
        and m11e_state["source_blocked_action_ids"] == ["house:119:2:278"]
        and m11e_state["candidate_identity"]
        == {
            "id": BATCH_ID,
            "sha256": EXPECTED_BATCH_FILE_SHA256,
            "episode_candidate_subject_sha256": EXPECTED_BATCH_SUBJECT_SHA256,
            "accepted": False,
            "canonical": False,
            "authorizing": False,
        }
        and all(
            value is False for value in m11e_state["downstream_authorizations"].values()
        ),
        "current-state M11E boundary differs",
    )

    tracked_runtime = subprocess.check_output(
        ["git", "ls-files", "backend/app/api", "frontend"], cwd=ROOT, text=True
    ).splitlines()
    require(
        not any(
            BATCH_ID.encode() in (ROOT / path).read_bytes()
            for path in tracked_runtime
            if Path(path).suffix in {".py", ".ts", ".tsx", ".js", ".json"}
        ),
        "M11E candidates entered runtime/public selectors",
    )
    return {
        "status": "pass",
        "artifact_id": BATCH_ID,
        "artifact_file_sha256": EXPECTED_BATCH_FILE_SHA256,
        "episode_candidate_subject_sha256": EXPECTED_BATCH_SUBJECT_SHA256,
        "episode_accounting": accounting,
        "cross_measure_episode_action_counts": dict(
            sorted(
                Counter(
                    len(row["primary_action_ids"])
                    for row in batch["subject"]["episodes"]
                    if row["grouping_type"] == "cross_measure"
                ).items()
            )
        ),
        "cross_measure_episode_ids": sorted(expected_cross),
        "ambiguous_or_unassigned_action_ids": [],
        "blocked_action_ids": ["house:119:2:278"],
        "decision_template_file_sha256": EXPECTED_DECISION_FILE_SHA256,
        "decision_template_subject_sha256": EXPECTED_DECISION_SUBJECT_SHA256,
        "parity_file_sha256": EXPECTED_PARITY_FILE_SHA256,
        "parity_subject_sha256": EXPECTED_PARITY_SUBJECT_SHA256,
        "downstream_authorizations": batch["subject"]["downstream_authorizations"],
        "m11a": m11a,
        "m11b": m11b,
        "m11c": m11c,
        "m11d": m11d,
    }


def main() -> int:
    print(json.dumps(validate_repository(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
