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
    validate_candidate_batch,
    verify_seal,
)
from backend.scripts.build_m13e_education_workforce_policy_episode_candidates import (  # noqa: E402
    AMENDMENT_ACTION_ID,
    BATCH_PATH,
    CANDIDATE_PATH,
    DECISION_PATH,
    DECISION_SCHEMA_PATH,
    DOSSIER_PATH,
    GENERIC_BATCH_SCHEMA_PATH,
    HR1048_EPISODE_ID,
    IMPLEMENTATION_PATH,
    M11_BATCH_PATH,
    M12_BATCH_PATH,
    PARITY_PATH,
    PASSAGE_ACTION_ID,
    PERMITTED_CROSS_MEASURE_SETS,
    PROHIBITED_GROUPED_SETS,
    build,
    file_sha256,
)
from scripts.validate_m11e_national_security_policy_episode_candidates import (  # noqa: E402
    validate_repository as validate_m11e,
)
from scripts.validate_m12e_environment_energy_policy_episode_candidates import (  # noqa: E402
    validate_repository as validate_m12e,
)
from scripts.validate_m13d_education_workforce_action_meaning_acceptance import (  # noqa: E402
    validate_repository as validate_m13d,
)

EXPECTED_BATCH_FILE_SHA256 = (
    "e66476bc01fe770bf9a79cdbcd9aca6461ecaf2958ab3fa04b9a0a2038c61b58"
)
EXPECTED_BATCH_SUBJECT_SHA256 = (
    "ea4bca6c4fa1bdef8381952aa4415b6e88292ec228e6950e5099c1a77c566398"
)
EXPECTED_DECISION_FILE_SHA256 = (
    "f3f4ce0a521be16f456b3ee82cd064744c3deec14fb19bf3860ee1281e04e6fa"
)
EXPECTED_DECISION_SUBJECT_SHA256 = (
    "a3fea9ac957614bd113718f23249f496ef3ae0fb5d153e23b2f418d946015ee5"
)
EXPECTED_DOSSIER_FILE_SHA256 = (
    "53135933c6ec6cab91b8aa16f2e3b2194c0fb632b27927755dfcf93c45969410"
)
EXPECTED_PARITY_FILE_SHA256 = (
    "4a18c1eb42c81cda11d8d8ac9e365fad8a15f353ef54ec36219182287360040b"
)
EXPECTED_PARITY_SUBJECT_SHA256 = (
    "a4409dc54e572941349323b6d9070d62197c6bdc739e945c604bde738f48e315"
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_repository() -> dict[str, Any]:
    m13d = validate_m13d()
    m11e = validate_m11e()
    m12e = validate_m12e()
    batch = load(BATCH_PATH)
    decision = load(DECISION_PATH)
    parity = load(PARITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    candidate = load(CANDIDATE_PATH)

    accounting = validate_candidate_batch(
        batch=batch,
        implementation=implementation,
        candidate_artifact=candidate,
        permitted_cross_measure_sets=PERMITTED_CROSS_MEASURE_SETS,
        prohibited_grouped_sets=PROHIBITED_GROUPED_SETS,
        blocked_action_id=None,
    )
    for schema_path, values in (
        (
            GENERIC_BATCH_SCHEMA_PATH,
            (load(M11_BATCH_PATH), load(M12_BATCH_PATH), batch),
        ),
        (DECISION_SCHEMA_PATH, (decision,)),
    ):
        validator = Draft7Validator(load(schema_path))
        for value in values:
            errors = list(validator.iter_errors(value))
            require(
                not errors, f"{schema_path.name}: {errors[0].message if errors else ''}"
            )

    require(
        file_sha256(BATCH_PATH) == EXPECTED_BATCH_FILE_SHA256
        and batch["episode_candidate_subject_sha256"] == EXPECTED_BATCH_SUBJECT_SHA256
        and file_sha256(DECISION_PATH) == EXPECTED_DECISION_FILE_SHA256
        and decision["decision_template_subject_sha256"]
        == EXPECTED_DECISION_SUBJECT_SHA256
        and file_sha256(DOSSIER_PATH) == EXPECTED_DOSSIER_FILE_SHA256
        and file_sha256(PARITY_PATH) == EXPECTED_PARITY_FILE_SHA256
        and parity["parity_subject_sha256"] == EXPECTED_PARITY_SUBJECT_SHA256,
        "M13E deterministic identities differ",
    )
    verify_seal(parity, "parity_subject_sha256", "M13E parity")
    for item in parity["referenced_artifacts"]:
        require(
            file_sha256(ROOT / item["path"]) == item["final_file_sha256"],
            f"M13E parity reference differs: {item['path']}",
        )

    require(
        accounting
        == {
            "assigned_action_count": 17,
            "episode_count": 16,
            "single_action_episode_count": 15,
            "multi_action_episode_count": 1,
            "cross_measure_episode_count": 1,
            "ambiguous_or_unassigned_count": 0,
            "blocked_count": 0,
        },
        "M13E complete accounting differs",
    )
    episodes = batch["subject"]["episodes"]
    episode_by_id = {row["episode_id"]: row for row in episodes}
    hr1048 = episode_by_id[HR1048_EPISODE_ID]
    require(
        hr1048["primary_action_ids"] == [AMENDMENT_ACTION_ID, PASSAGE_ACTION_ID]
        and hr1048["grouping_type"] == "cross_measure"
        and hr1048["member_direction_candidate"] == "mixed_on_episode_choices"
        and hr1048["direction_derivation"]["accepted_position_effects_by_action"]
        == {
            AMENDMENT_ACTION_ID: "supports_exact_choice",
            PASSAGE_ACTION_ID: "opposes_exact_choice",
        }
        and "h.amdt. 12 directly to h.r. 1048"
        in " ".join(hr1048["semantic_grouping_evidence"]).lower()
        and "whole-package" in hr1048["material_policy_differences"].lower()
        and hr1048["competing_plausible_groupings"],
        "H.Amdt. 12/H.R. 1048 grouping judgment differs",
    )
    require(
        all(
            len(row["primary_action_ids"]) == 1
            for row in episodes
            if row["episode_id"] != HR1048_EPISODE_ID
        ),
        "an unsupported second multi-action episode was introduced",
    )
    all_actions = [action for row in episodes for action in row["primary_action_ids"]]
    require(
        len(all_actions) == len(set(all_actions)) == 17
        and set(all_actions) == set(candidate["subject"]["action_ids"]),
        "accepted action assignment is not exact-once complete",
    )
    nondirectional = next(
        row for row in episodes if "house:119:1:312" in row["primary_action_ids"]
    )
    require(
        nondirectional["member_direction_candidate"] == "non_directional_not_voting"
        and nondirectional["primary_action_ids"] == ["house:119:1:312"],
        "roll 312 episode accounting became directional",
    )
    require(
        decision["decision_count"] == 16
        and decision["selected_batch_decision"] is None
        and all(
            row["selected_decision"] is None
            and row["bounded_revision"] is None
            and row["reviewer_id"] is None
            and row["reviewer_authority"] is None
            and row["decision_timestamp"] is None
            for row in decision["decisions"]
        ),
        "M13E decision template is not empty",
    )
    require(
        batch["candidate"] is True
        and batch["accepted"] is False
        and batch["canonical"] is False
        and batch["public"] is False
        and batch["authorizing"] is False
        and batch["production_selectable"] is False
        and all(
            value is False
            for value in batch["subject"]["downstream_authorizations"].values()
        ),
        "M13E candidate crossed its authority boundary",
    )

    state = load(ROOT / "docs/editorial/current_state_index.json")
    m13e = state["active_m13e_policy_episode_candidate_milestone"]
    require(
        m13e["milestone_state"] == "completed_independent_semantic_review_merged"
        and m13e["reviewed_pr"] == 166
        and m13e["reviewed_head"] == "9ec140b7b2c8eec46eb799ba958dbccd46bddea1"
        and m13e["post_merge_main"] == "641910bb0c8bb633a76fe95ef113d396d8db881b"
        and m13e["review_decision"]
        == "approved_all_policy_episode_candidates_as_written"
        and m13e["accepted_action_count"] == 17
        and m13e["episode_count"] == 16
        and m13e["single_action_episode_count"] == 15
        and m13e["multi_action_episode_count"] == 1
        and m13e["ambiguous_or_unassigned_action_ids"] == []
        and m13e["blocked_action_ids"] == []
        and m13e["candidate"]["sha256"] == EXPECTED_BATCH_FILE_SHA256
        and m13e["candidate"]["episode_candidate_subject_sha256"]
        == EXPECTED_BATCH_SUBJECT_SHA256
        and m13e["decision_template"]["sha256"] == EXPECTED_DECISION_FILE_SHA256
        and m13e["decision_template"]["all_decisions_empty"] is True
        and m13e["episode_acceptance_state"]
        == "accepted_as_written_implemented_by_m13f"
        and all(value is False for value in m13e["downstream_authorizations"].values()),
        "M13E current-state boundary differs",
    )
    regenerated = build(check=True)
    return {
        "status": "pass",
        **regenerated,
        "hr1048_episode_id": HR1048_EPISODE_ID,
        "hr1048_action_ids": [AMENDMENT_ACTION_ID, PASSAGE_ACTION_ID],
        "hr1048_direction": hr1048["member_direction_candidate"],
        "contrast_review_count": len(batch["subject"]["contrast_reviews"]),
        "m11e_episode_count": m11e["episode_accounting"]["episode_count"],
        "m12e_episode_count": m12e["episode_count"],
        "m13d_effect_counts": m13d["effect_counts"],
    }


def main() -> int:
    print(json.dumps(validate_repository(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
