from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_policy_episode_candidates import (  # noqa: E402
    DOWNSTREAM_AUTHORIZATIONS,
    validate_candidate_batch,
    verify_seal,
)
from backend.scripts.build_m12e_environment_energy_policy_episode_candidates import (  # noqa: E402
    ACCEPTED_CANDIDATE_FILE_SHA256,
    ACCEPTED_CANDIDATE_SUBJECT_SHA256,
    ACCEPTED_HEAD,
    ACCEPTED_PR,
    AUTHORITY_ID,
    BATCH_ID,
    BATCH_PATH,
    CANDIDATE_PATH,
    CONTRAST_GROUPS,
    DECISION_PATH,
    DOSSIER_PATH,
    GENERIC_BATCH_SCHEMA_PATH,
    IMPLEMENTATION_ID,
    IMPLEMENTATION_PATH,
    M11_BATCH_PATH,
    M12D_AUTHORITY_FILE_SHA256,
    M12D_AUTHORITY_SUBJECT_SHA256,
    M12D_IMPLEMENTATION_FILE_SHA256,
    M12D_IMPLEMENTATION_SUBJECT_SHA256,
    PARITY_PATH,
    PERMITTED_CROSS_MEASURE_SETS,
    POST_M12C_MERGE_MAIN,
    PROHIBITED_GROUPED_SETS,
    build,
    file_sha256,
)
from scripts.validate_m12d_environment_energy_action_meaning_acceptance import (  # noqa: E402
    validate_repository as validate_m12d_repository,
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_repository() -> dict[str, Any]:
    validate_m12d_repository()
    implementation = load(IMPLEMENTATION_PATH)
    candidate = load(CANDIDATE_PATH)
    batch = load(BATCH_PATH)
    decision = load(DECISION_PATH)
    parity = load(PARITY_PATH)

    accounting = validate_candidate_batch(
        batch=batch,
        implementation=implementation,
        candidate_artifact=candidate,
        permitted_cross_measure_sets=PERMITTED_CROSS_MEASURE_SETS,
        prohibited_grouped_sets=PROHIBITED_GROUPED_SETS,
        blocked_action_id=None,
    )
    schema = load(GENERIC_BATCH_SCHEMA_PATH)
    for name, value in (("historical M11E", load(M11_BATCH_PATH)), ("M12E", batch)):
        errors = list(Draft7Validator(schema).iter_errors(value))
        require(
            not errors,
            f"{name} generic schema failure: {errors[0].message if errors else ''}",
        )

    require(batch["artifact_id"] == BATCH_ID, "M12E artifact id differs")
    subject = batch["subject"]
    require(
        subject["input_bindings"]
        == {
            "accepted_action_interpretation_review_pr": ACCEPTED_PR,
            "accepted_action_interpretation_head": ACCEPTED_HEAD,
            "post_candidate_merge_main": POST_M12C_MERGE_MAIN,
            "action_interpretation_authority": {
                "artifact_id": AUTHORITY_ID,
                "final_file_sha256": M12D_AUTHORITY_FILE_SHA256,
                "authority_subject_sha256": M12D_AUTHORITY_SUBJECT_SHA256,
            },
            "action_interpretation_implementation": {
                "artifact_id": IMPLEMENTATION_ID,
                "final_file_sha256": M12D_IMPLEMENTATION_FILE_SHA256,
                "implementation_subject_sha256": M12D_IMPLEMENTATION_SUBJECT_SHA256,
            },
            "action_interpretation_candidate": {
                "artifact_id": candidate["artifact_id"],
                "final_file_sha256": ACCEPTED_CANDIDATE_FILE_SHA256,
                "interpretation_subject_sha256": ACCEPTED_CANDIDATE_SUBJECT_SHA256,
            },
        },
        "M12E accepted-interpretation input binding differs",
    )
    require(
        file_sha256(IMPLEMENTATION_PATH) == M12D_IMPLEMENTATION_FILE_SHA256
        and implementation["implementation_subject_sha256"]
        == M12D_IMPLEMENTATION_SUBJECT_SHA256,
        "M12D implementation identity differs",
    )
    require(
        file_sha256(CANDIDATE_PATH) == ACCEPTED_CANDIDATE_FILE_SHA256
        and candidate["interpretation_subject_sha256"]
        == ACCEPTED_CANDIDATE_SUBJECT_SHA256,
        "M12C candidate identity differs",
    )

    episodes = subject["episodes"]
    require(
        accounting
        == {
            "episode_count": 63,
            "single_action_episode_count": 63,
            "multi_action_episode_count": 0,
            "cross_measure_episode_count": 0,
            "assigned_action_count": 63,
            "ambiguous_or_unassigned_count": 0,
            "blocked_count": 0,
        },
        "exact M12E accounting differs",
    )
    require(
        len({row["episode_id"] for row in episodes}) == 63
        and len(
            {
                action["exact_action_identity"]
                for row in episodes
                for action in row["actions"]
            }
        )
        == 63,
        "episode or measure uniqueness differs",
    )
    require(
        all(
            row["grouping_type"] == "single_action"
            and len(row["primary_action_ids"]) == 1
            for row in episodes
        ),
        "non-singleton episode entered M12E",
    )
    by_action = {row["primary_action_ids"][0]: row for row in episodes}
    nondirectional = by_action["house:119:2:136"]
    require(
        nondirectional["member_direction_candidate"] == "non_directional_not_voting"
        and nondirectional["direction_derivation"][
            "accepted_position_effects_by_action"
        ]
        == {"house:119:2:136": "non_directional_not_voting"},
        "Not Voting episode became directional",
    )
    candidate_by_id = {
        row["action_id"]: row for row in candidate["subject"]["candidates"]
    }
    for action_id in ("house:119:1:25", "house:119:1:330"):
        episode = by_action[action_id]
        require(
            episode["primary_action_ids"] == [action_id]
            and episode["actions"][0]["accepted_limitations"]
            == candidate_by_id[action_id]["limitations"]
            and episode["policy_proposition"]
            == "Whether to "
            + candidate_by_id[action_id]["proposed_exact_action_meaning"].removeprefix(
                "The House choice was whether to "
            ),
            f"{action_id}: broad-package boundary differs",
        )
    require(
        subject["contrast_reviews"] == CONTRAST_GROUPS,
        "contrast review set differs",
    )
    require(
        subject["ambiguous_or_unassigned_action_ids"] == []
        and subject["blocked_actions"] == []
        and subject["episode_acceptance_state"] == "not_started_not_authorized"
        and subject["downstream_authorizations"] == DOWNSTREAM_AUTHORIZATIONS,
        "M12E authority boundary differs",
    )

    verify_seal(decision, "decision_template_subject_sha256", "decision template")
    require(
        decision["decision_count"] == 63
        and decision["decision_state"] == "awaiting_human_policy_episode_review"
        and decision["selected_batch_decision"] is None
        and decision["accepted"] is False
        and decision["canonical"] is False
        and decision["authorizing"] is False
        and all(
            row["selected_decision"] is None
            and row["bounded_revision"] is None
            and row["reviewer_id"] is None
            and row["reviewer_authority"] is None
            and row["decision_timestamp"] is None
            for row in decision["decisions"]
        ),
        "M12E decision template is not empty/non-authorizing",
    )
    verify_seal(parity, "parity_subject_sha256", "M12E parity")
    entries = {row["path"]: row for row in parity["referenced_artifacts"]}
    for path in (BATCH_PATH, DECISION_PATH, DOSSIER_PATH, GENERIC_BATCH_SCHEMA_PATH):
        relative = path.relative_to(ROOT).as_posix()
        require(
            relative in entries
            and entries[relative]["final_file_sha256"] == file_sha256(path),
            f"M12E parity differs: {relative}",
        )
    state = load(ROOT / "docs/editorial/current_state_index.json")
    m12e = state["active_m12e_policy_episode_candidate_milestone"]
    require(
        m12e["milestone_state"] == "complete_pending_independent_semantic_review"
        and m12e["accepted_action_count"] == 63
        and m12e["episode_count"] == 63
        and m12e["single_action_episode_count"] == 63
        and m12e["multi_action_episode_count"] == 0
        and m12e["cross_measure_episode_count"] == 0
        and m12e["ambiguous_or_unassigned_action_ids"] == []
        and m12e["candidate"]["sha256"] == file_sha256(BATCH_PATH)
        and m12e["candidate"]["episode_candidate_subject_sha256"]
        == batch["episode_candidate_subject_sha256"]
        and m12e["decision_template"]["sha256"] == file_sha256(DECISION_PATH)
        and m12e["decision_template"]["all_decisions_empty"] is True
        and m12e["episode_acceptance_state"] == "not_started_not_authorized"
        and all(value is False for value in m12e["downstream_authorizations"].values()),
        "M12E current state differs",
    )
    deterministic = build(check=True)
    return {
        "status": "pass",
        **deterministic,
        "multi_action_candidates": [],
        "cross_measure_candidates": [],
        "ambiguous_or_competing_groupings": [],
        "non_directional_action_id": "house:119:2:136",
        "contrast_review_count": len(CONTRAST_GROUPS),
        "generic_schema_accepts": ["M11E", "M12E"],
    }


def main() -> int:
    print(json.dumps(validate_repository(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
