"""Independently validate exact M13F policy-episode acceptance."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_policy_episode_decisions import (  # noqa: E402
    digest,
    validate_authority,
    validate_implementation,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
)
from backend.scripts.build_m13f_education_workforce_policy_episode_acceptance import (  # noqa: E402
    AUTHORITY_PATH,
    AUTHORITY_SCHEMA_PATH,
    CANDIDATE_FILE_SHA256,
    CANDIDATE_PATH,
    CANDIDATE_SUBJECT_SHA256,
    DECISION_TEMPLATE_FILE_SHA256,
    DECISION_TEMPLATE_PATH,
    DECISION_TEMPLATE_SUBJECT_SHA256,
    DOSSIER_PATH,
    IMPLEMENTATION_PATH,
    IMPLEMENTATION_SCHEMA_PATH,
    INTERPRETATION_IMPLEMENTATION_FILE_SHA256,
    INTERPRETATION_IMPLEMENTATION_PATH,
    INTERPRETATION_IMPLEMENTATION_SUBJECT_SHA256,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    REVIEWER_AUTHORITY,
    REVIEWER_ID,
    build,
)


M11F_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_national_security_foreign_119_v1"
)
M11F_HASHES = {
    "human_policy_episode_authority.json": "bd3ee15f7cd4508a194df4bb093da673889d460b073af21d7235cf62d9f6f627",
    "episode_decision_implementation_bundle.json": "546441f951b1788f248520ee9cfef7f718c6ea8225f98818aa35c17220e60239",
    "implementation_dossier.md": "44b827374a2a7c29bdb22e4dbaeffdf48b1faa748a6540e63b327ce661c3d032",
    "implementation_parity_manifest.json": "e6233b158120358f70235d3795f30266b8da7e25970dd46736e7eba88d422c35",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha(path: Path) -> str:
    return canonical_file_sha256(path)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate() -> dict[str, Any]:
    candidate = load(CANDIDATE_PATH)
    template = load(DECISION_TEMPLATE_PATH)
    interpretation = load(INTERPRETATION_IMPLEMENTATION_PATH)
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    parity = load(PARITY_PATH)

    require(
        canonical_file_sha256(CANDIDATE_PATH) == CANDIDATE_FILE_SHA256,
        "M13E candidate changed",
    )
    require(
        candidate["episode_candidate_subject_sha256"] == CANDIDATE_SUBJECT_SHA256,
        "M13E candidate subject changed",
    )
    require(
        canonical_file_sha256(DECISION_TEMPLATE_PATH) == DECISION_TEMPLATE_FILE_SHA256,
        "M13E template changed",
    )
    require(
        template["decision_template_subject_sha256"]
        == DECISION_TEMPLATE_SUBJECT_SHA256,
        "M13E template subject changed",
    )
    require(
        all(row["selected_decision"] is None for row in template["decisions"]),
        "M13E template is not empty",
    )
    require(
        canonical_file_sha256(INTERPRETATION_IMPLEMENTATION_PATH)
        == INTERPRETATION_IMPLEMENTATION_FILE_SHA256,
        "M13D implementation changed",
    )
    require(
        interpretation["implementation_subject_sha256"]
        == INTERPRETATION_IMPLEMENTATION_SUBJECT_SHA256,
        "M13D implementation subject changed",
    )

    for path, artifact, schema_path in (
        (AUTHORITY_PATH, authority, AUTHORITY_SCHEMA_PATH),
        (IMPLEMENTATION_PATH, implementation, IMPLEMENTATION_SCHEMA_PATH),
        (PARITY_PATH, parity, PARITY_SCHEMA_PATH),
    ):
        errors = sorted(
            Draft7Validator(load(schema_path)).iter_errors(artifact), key=str
        )
        require(
            not errors,
            f"{path.name} schema error: {errors[0].message if errors else ''}",
        )

    candidate_by_id = {
        row["episode_id"]: row for row in candidate["subject"]["episodes"]
    }
    accepted_ids = set(candidate_by_id)
    validate_authority(
        authority,
        candidate=candidate,
        accepted_single_episode_ids=accepted_ids,
        rejected_episode_ids=set(),
    )
    decisions = authority["subject"]["episode_decisions"]
    require(
        len(decisions) == 16
        and {row["episode_id"] for row in decisions} == accepted_ids,
        "M13F decision coverage differs",
    )
    require(
        all(
            row["decision"] == "accept_candidate_as_written"
            and row["replacement_episode_ids"] == []
            and row["reviewer_id"] == REVIEWER_ID
            and row["reviewer_authority"] == REVIEWER_AUTHORITY
            and row["candidate_episode_subject_sha256"]
            == candidate_by_id[row["episode_id"]]["episode_subject_sha256"]
            for row in decisions
        ),
        "M13F authority decision differs from accepted review",
    )
    require(
        authority["subject"]["decision_accounting"]
        == {"accept_candidate_as_written": 16},
        "M13F decision counts differ",
    )

    records = interpretation["subject"]["implementation_records"]
    final = validate_implementation(
        implementation,
        authority=authority,
        accepted_interpretation_records=records,
        blocked_action_id=None,
        rejected_episode_ids=set(),
    )
    require(
        final
        == {
            "accepted_action_count": 17,
            "accepted_episode_count": 16,
            "single_action_episode_count": 15,
            "multi_action_episode_count": 1,
            "cross_measure_episode_count": 1,
            "ambiguous_or_unassigned_action_count": 0,
            "blocked_action_count": 0,
        },
        "M13F final accounting differs",
    )
    implemented_by_id = {
        row["episode_id"]: row
        for row in implementation["subject"]["implementation_records"]
    }
    require(
        set(implemented_by_id) == accepted_ids, "implemented episode identities differ"
    )
    exact_fields = (
        "policy_proposition",
        "grouping_type",
        "primary_action_ids",
        "actions",
        "grouping_rationale",
        "semantic_grouping_evidence",
        "relevant_contrast_ids",
        "material_policy_differences",
        "material_limitations",
        "confidence",
    )
    for episode_id, source in candidate_by_id.items():
        implemented = implemented_by_id[episode_id]
        require(
            all(implemented[field] == source[field] for field in exact_fields)
            and implemented["member_direction"] == source["member_direction_candidate"]
            and implemented["direction_derivation"] == source["direction_derivation"],
            f"{episode_id}: candidate changed during M13F implementation",
        )
    hr1005 = next(
        row
        for row in implemented_by_id.values()
        if row["primary_action_ids"] == ["house:119:1:312"]
    )
    require(
        hr1005["member_direction"] == "non_directional_not_voting",
        "H.R. 1005 direction differs",
    )
    hr1048 = implemented_by_id["hr-1048-amendment-and-final-passage"]
    require(
        hr1048["primary_action_ids"] == ["house:119:1:79", "house:119:1:83"]
        and hr1048["member_direction"] == "mixed_on_episode_choices"
        and hr1048["grouping_type"] == "cross_measure"
        and hr1048["legislative_event_continuity"]["state"] == "established"
        and {
            row["action_id"]: row["accepted_exact_choice_position_effect"]
            for row in hr1048["actions"]
        }
        == {
            "house:119:1:79": "supports_exact_choice",
            "house:119:1:83": "opposes_exact_choice",
        },
        "H.R. 1048 mixed episode boundary differs",
    )

    for name, expected in M11F_HASHES.items():
        require(
            canonical_file_sha256(M11F_ROOT / name) == expected,
            f"historical M11F {name} changed",
        )
    state = load(ROOT / "docs/editorial/current_state_index.json")
    m13f = state["active_m13f_policy_episode_decision_milestone"]
    require(
        m13f["milestone_state"] == "completed_mechanical_acceptance_validated"
        and m13f["post_m13e_merge_main"] == "641910bb0c8bb633a76fe95ef113d396d8db881b"
        and m13f["decision_accounting"] == {"accept_candidate_as_written": 16}
        and m13f["accepted_action_count"] == 17
        and m13f["accepted_episode_count"] == 16
        and m13f["single_action_episode_count"] == 15
        and m13f["multi_action_episode_count"] == 1
        and m13f["cross_measure_episode_count"] == 1
        and m13f["blocked_action_count"] == 0
        and m13f["authority"]["sha256"] == file_sha(AUTHORITY_PATH)
        and m13f["implementation"]["sha256"] == file_sha(IMPLEMENTATION_PATH)
        and m13f["canonical_internal_policy_episode_membership"] is True
        and m13f["canonical_semantic_ir_acceptance"] is False
        and not any(m13f["downstream_authorizations"].values()),
        "M13F current-state boundary differs",
    )
    require(
        not any(authority["subject"]["downstream_authorizations"].values()),
        "authority downstream leakage",
    )
    require(
        not any(implementation["subject"]["downstream_authorizations"].values()),
        "implementation downstream leakage",
    )
    require(
        parity["parity_subject_sha256"]
        == digest(
            {
                key: value
                for key, value in parity.items()
                if key != "parity_subject_sha256"
            }
        ),
        "parity seal differs",
    )

    deterministic = build(check=True)
    return {
        "status": "pass",
        "authority_id": authority["artifact_id"],
        "authority_file_sha256": file_sha(AUTHORITY_PATH),
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_id": implementation["artifact_id"],
        "implementation_file_sha256": file_sha(IMPLEMENTATION_PATH),
        "implementation_subject_sha256": implementation[
            "implementation_subject_sha256"
        ],
        "dossier_file_sha256": file_sha(DOSSIER_PATH),
        "parity_file_sha256": file_sha(PARITY_PATH),
        "parity_subject_sha256": parity["parity_subject_sha256"],
        "decision_count": len(decisions),
        "direction_counts": dict(
            sorted(
                Counter(
                    row["member_direction"] for row in implemented_by_id.values()
                ).items()
            )
        ),
        "final_accounting": final,
        "historical_m11f_byte_compatibility": "pass",
        "deterministic": deterministic,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
