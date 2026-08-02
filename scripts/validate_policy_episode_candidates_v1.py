"""Validate M4A episode candidates independently of asserted accounting."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_policy_episode_candidates_v1 import (  # noqa: E402
    ACCEPTANCE_CONTENT_SHA256,
    ACCEPTANCE_FILE_SHA256,
    ACCEPTANCE_OUTPUT,
    ACCEPTANCE_SOURCE,
    BATCH_ID,
    IMPLEMENTATION_CONTENT_SHA256,
    IMPLEMENTATION_PATH,
    JSON_NAMES,
    OUTPUT_ROOT,
    PRIOR_RISK_PATH,
    READINESS_PATH,
    SCHEMA_ROOT,
    build,
    digest,
    file_digest,
    load,
    preflight,
)


class EpisodeCandidateValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EpisodeCandidateValidationError(message)


def verify_seal(value: dict[str, Any], label: str) -> None:
    subject = {
        key: child for key, child in value.items() if key != "content_subject_sha256"
    }
    require(
        value.get("content_subject_sha256") == digest(subject),
        f"{label}: content digest differs",
    )


def expected_behavior(actions: list[dict[str, Any]]) -> str:
    if any(row["interpretation_status"] == "ambiguous" for row in actions):
        return "ambiguous"
    effects = {row["implemented_exact_choice_position_effect"] for row in actions}
    if effects == {"supports_exact_choice"}:
        return "supports_episode_direction"
    if effects == {"opposes_exact_choice"}:
        return "opposes_episode_direction"
    if effects <= {"supports_exact_choice", "opposes_exact_choice"}:
        return "mixed_actions"
    return "non_directional"


def validate_artifacts(values: dict[str, dict[str, Any]]) -> dict[str, Any]:
    implementation = load(IMPLEMENTATION_PATH)
    impl = {row["action_id"]: row for row in implementation["implementation_records"]}
    readiness = load(READINESS_PATH)
    ready = {row["action_id"]: row for row in readiness["subject"]["action_readiness"]}
    lineage = values["action_lineage_map.json"]
    initial = values["initial_episode_candidate_batch.json"]
    final = values["frozen_episode_candidate_batch.json"]

    require(
        lineage["neutral_no_episode_conclusions"] is True,
        "lineage map contains episode conclusions",
    )
    require(lineage["action_count"] == 37, "lineage action count differs")
    require(
        all(
            row["does_not_establish"] == "Episode membership or episode-level behavior."
            for row in lineage["relationships"]
        ),
        "lineage map is not neutral",
    )
    require(
        initial["frozen"] is False
        and initial["benchmark_evidence_used_in_construction"] is False,
        "benchmark exposed before freeze",
    )
    require(
        final["artifact_id"] == BATCH_ID
        and final["frozen"] is True
        and final["freeze_precedes_benchmark_access"] is True,
        "final freeze state differs",
    )
    require(
        final["benchmark_evidence_used_in_construction"] is False,
        "benchmark altered frozen candidates",
    )
    require(
        final["episode_count"] == len(final["episodes"]) == 32, "episode count differs"
    )
    require(
        final["single_action_episode_count"] == 30
        and final["multi_action_episode_count"] == 2,
        "single/multi episode accounting differs",
    )
    episode_ids = [row["episode_id"] for row in final["episodes"]]
    require(len(episode_ids) == len(set(episode_ids)), "duplicate episode ID")
    primary: dict[str, str] = {}
    for episode in final["episodes"]:
        verify_seal(episode, episode["episode_id"])
        action_ids = episode["primary_action_ids"]
        sequence = episode["chronological_action_sequence"]
        require(
            action_ids == [row["action_id"] for row in sequence],
            f"{episode['episode_id']}: chronology membership differs",
        )
        require(
            action_ids
            == sorted(
                action_ids,
                key=lambda action_id: (
                    ready[action_id]["official_action_date"],
                    ready[action_id]["session"],
                    ready[action_id]["roll_number"],
                ),
            ),
            f"{episode['episode_id']}: chronological order differs",
        )
        require(
            len(action_ids) == len(set(action_ids)),
            f"{episode['episode_id']}: duplicate action",
        )
        for row in sequence:
            action_id = row["action_id"]
            require(
                action_id not in primary,
                f"{action_id}: duplicate primary episode membership",
            )
            primary[action_id] = episode["episode_id"]
            source = impl[action_id]
            require(
                row["implementation_record_content_subject_sha256"]
                == source["content_subject_sha256"],
                f"{action_id}: interpretation hash differs",
            )
            require(
                row["implemented_exact_action_meaning"]
                == source["implemented_exact_action_meaning"]
                and row["official_member_action"] == source["official_member_action"],
                f"{action_id}: accepted action meaning or member action differs",
            )
            require(
                row["official_action_date"] == ready[action_id]["official_action_date"],
                f"{action_id}: action date differs",
            )
            if ready[action_id]["house_action_stage"] == "amendment":
                require(
                    row["action_role"] == "amendment",
                    f"{action_id}: amendment role differs",
                )
            if ready[action_id]["house_action_stage"].startswith("suspension"):
                require(
                    row["action_role"] == "suspension_passage",
                    f"{action_id}: suspension role differs",
                )
        require(
            episode["candidate_episode_level_behavior"] == expected_behavior(sequence),
            f"{episode['episode_id']}: behavior derivation differs",
        )
        require(
            episode["candidate"]
            and not episode["accepted"]
            and not episode["canonical"]
            and not episode["public"]
            and not episode["authorizing"],
            f"{episode['episode_id']}: candidate boundary differs",
        )
    accounting = final["action_accounting"]
    ids = [row["action_id"] for row in accounting]
    require(
        len(ids) == len(set(ids)) == 37 and set(ids) == set(impl),
        "37-action accounting differs",
    )
    by_action = {row["action_id"]: row for row in accounting}
    for action_id, row in by_action.items():
        verify_seal(row, action_id)
        state = row["primary_accounting_state"]
        if state == "assigned_primary_episode":
            require(
                primary.get(action_id) == row["primary_episode_id"],
                f"{action_id}: assigned primary episode differs",
            )
        else:
            require(
                action_id not in primary and row["primary_episode_id"] is None,
                f"{action_id}: non-primary state contributes to episode",
            )
    counts = dict(
        sorted(Counter(row["primary_accounting_state"] for row in accounting).items())
    )
    require(
        counts
        == {
            "assigned_primary_episode": 35,
            "retained_ambiguous_episode_assignment": 1,
            "unassigned_no_safe_interpretation": 1,
        },
        "primary-state accounting differs",
    )
    require(
        final["accounting_counts"] == counts,
        "asserted primary-state accounting differs",
    )
    require(
        by_action["house:119:2:155"]["primary_accounting_state"]
        == "retained_ambiguous_episode_assignment"
        and by_action["house:119:2:155"]["related_candidate_episode_ids"]
        == ["fisa-title-vii-short-term-extension"],
        "roll 155 ambiguity or relationship was normalized",
    )
    require(
        by_action["house:119:2:278"]["primary_accounting_state"]
        == "unassigned_no_safe_interpretation"
        and "house:119:2:278" not in primary,
        "roll 278 received episode meaning",
    )
    episode_by_id = {row["episode_id"]: row for row in final["episodes"]}
    require(
        episode_by_id["law-enforcement-concealed-carry-expansion"][
            "candidate_episode_level_behavior"
        ]
        == "ambiguous"
        and "house:119:1:128"
        in episode_by_id["law-enforcement-concealed-carry-expansion"][
            "primary_action_ids"
        ],
        "roll 128 ambiguity was normalized",
    )
    require(
        episode_by_id["halt-fentanyl-legislative-path"]["primary_action_ids"]
        == ["house:119:1:32", "house:119:1:33", "house:119:1:166"]
        and episode_by_id["halt-fentanyl-legislative-path"][
            "candidate_episode_level_behavior"
        ]
        == "mixed_actions",
        "HALT path undergrouped or behavior differs",
    )
    require(
        episode_by_id["laken-riley-detention-enforcement"]["primary_action_ids"]
        == ["house:119:1:6", "house:119:1:23"],
        "Laken Riley path undergrouped",
    )
    for action_id in (
        "house:119:2:259",
        "house:119:2:265",
        "house:119:2:273",
        "house:119:2:275",
    ):
        require(
            len(episode_by_id[primary[action_id]]["primary_action_ids"]) == 1,
            f"{action_id}: distinct H.R. 8800 amendment overgrouped",
        )

    correction = values["bounded_correction_diff.json"]
    require(
        correction["correction_cycle_count"] == 1
        and correction["pre_correction_severity_counts"] == {"critical": 0, "major": 2}
        and correction["post_correction_severity_counts"]
        == {"critical": 0, "major": 0},
        "bounded correction accounting differs",
    )
    require(
        correction["initial_batch_content_subject_sha256"]
        == initial["content_subject_sha256"]
        and correction["final_batch_content_subject_sha256"]
        == final["content_subject_sha256"],
        "correction diff binding differs",
    )
    expected_reviews = {
        "overgrouping_review.json": {"critical": 0, "major": 1, "none": 30},
        "undergrouping_review.json": {"critical": 0, "major": 0, "none": 31},
        "chronology_action_role_review.json": {"critical": 0, "major": 0, "none": 36},
        "behavior_derivation_review.json": {"critical": 0, "major": 0, "none": 31},
        "ambiguity_no_safe_review.json": {"critical": 0, "major": 1, "none": 1},
        "double_counting_review.json": {"critical": 0, "major": 0, "none": 37},
    }
    for name, expected in expected_reviews.items():
        require(
            values[name]["finding_counts"] == expected,
            f"{name}: review accounting differs",
        )
    benchmark = values["benchmark_comparison.json"]
    require(
        benchmark["benchmark_accessed_after_freeze"]
        and benchmark["frozen_batch_content_subject_sha256"]
        == final["content_subject_sha256"],
        "benchmark blindness/freeze binding differs",
    )
    require(
        benchmark["comparison_count"] == 5
        and all(
            row["membership_agreement"]
            and row["policy_question_agreement"]
            and row["action_role_agreement"]
            and row["material_scope_agreement"]
            and row["severity"] == "none"
            for row in benchmark["comparisons"]
        ),
        "benchmark comparison differs",
    )
    samples = values["sample_challenge_manifest.json"]
    expected_seed = hashlib.sha256(
        (
            final["content_subject_sha256"]
            + "*"
            + IMPLEMENTATION_CONTENT_SHA256
            + "*foushee-justice-policy-episode-audit-v1"
        ).encode()
    ).hexdigest()
    expected_sample = sorted(
        episode_ids,
        key=lambda episode_id: hashlib.sha256(
            (expected_seed + episode_id).encode()
        ).hexdigest(),
    )[:6]
    require(
        samples["selection_after_freeze"]
        and samples["seed_sha256"] == expected_seed
        and samples["episode_review_sample_ids"] == expected_sample,
        "deterministic sample differs",
    )
    require(
        set(samples["challenge_episode_ids"])
        >= {
            "halt-fentanyl-legislative-path",
            "laken-riley-detention-enforcement",
            "law-enforcement-concealed-carry-expansion",
            "fisa-title-vii-short-term-extension",
        },
        "mandatory challenge episode missing",
    )
    require(
        samples["no_safe_accounting_action_id"] == "house:119:2:278",
        "no-safe accounting missing from review",
    )
    prior_risk = load(PRIOR_RISK_PATH)
    risk = values["launch_review_risk_register.json"]
    require(
        risk["carried_entry_count"] == 7
        and risk["new_entry_count"] == 1
        and risk["entry_count"] == 8,
        "launch-risk accounting differs",
    )
    require(
        risk["entries"][:7] == prior_risk["entries"],
        "prior launch-risk entries changed",
    )
    require(
        risk["entries"][-1]["subject"]["episode_id"]
        == "fisa-title-vii-short-term-extension"
        and risk["entries"][-1]["current_status"] == "retained_ambiguous",
        "episode launch risk differs",
    )
    calibration = values["episode_calibration_population.json"]
    require(
        calibration["sample_selected"] is False
        and calibration["selected_sample"] == [],
        "episode calibration sample selected prematurely",
    )
    require(
        calibration["eligible_count"] == len(calibration["eligible_items"]) == 30,
        "episode calibration population differs",
    )
    require(
        not (
            {
                "law-enforcement-concealed-carry-expansion",
                "fisa-title-vii-short-term-extension",
            }
            & {row["episode_id"] for row in calibration["eligible_items"]}
        ),
        "ambiguous episode entered calibration population",
    )
    decision = values["delegated_authority_decision_template.json"]
    require(
        decision["decision_state"] == "awaiting_delegated_authority_decision"
        and decision["decision_count"] == 32
        and decision["selected_batch_decision"] is None,
        "empty delegated decision template differs",
    )
    require(
        all(
            row["selected_decision"] is None and row["reviewer_identity"] is None
            for row in decision["decisions"]
        ),
        "recommendation represented as delegated decision",
    )
    for value in values.values():
        verify_seal(value, value["artifact_id"])
        require(
            value.get("accepted") is False
            and value.get("canonical") is False
            and value.get("public") is False
            and value.get("authorizing") is False,
            f"{value['artifact_id']}: non-authorizing boundary differs",
        )
    corpus = json.dumps(
        values, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    require(
        "accepted_semantic_reference" not in corpus
        and '"accepted":true' not in corpus
        and '"canonical":true' not in corpus
        and '"public":true' not in corpus,
        "accepted/canonical/public state asserted",
    )
    return {
        "episode_count": 32,
        "single_action_episode_count": 30,
        "multi_action_episode_count": 2,
        "accounting": counts,
        "sample_count": 6,
        "challenge_count": len(samples["challenge_episode_ids"]),
        "risk_count": 8,
        "calibration_eligible_count": 30,
    }


def validate_parity(
    *,
    byte_overrides: dict[str, bytes] | None = None,
    markdown_override: str | None = None,
) -> None:
    overrides = byte_overrides or {}
    parity = load(OUTPUT_ROOT / "parity_manifest.json")
    verify_seal(parity, "parity manifest")
    require(
        parity["generated_last"] and parity["parity_state"] == "pass",
        "parity state differs",
    )
    for item in parity["referenced_artifacts"]:
        raw = overrides.get(item["path"], (ROOT / item["path"]).read_bytes())
        require(
            hashlib.sha256(raw).hexdigest() == item["final_file_sha256"],
            f"{item['path']}: stale final-file hash",
        )
        if "content_subject_sha256" in item:
            require(
                json.loads(raw)["content_subject_sha256"]
                == item["content_subject_sha256"],
                f"{item['path']}: stale content hash",
            )
    final = load(OUTPUT_ROOT / "frozen_episode_candidate_batch.json")
    markdown = (
        markdown_override
        if markdown_override is not None
        else (OUTPUT_ROOT / "review_dossier.md").read_text(encoding="utf-8")
    )
    for episode in final["episodes"]:
        require(
            episode["episode_id"] in markdown
            and episode["neutral_policy_question"] in markdown
            and episode["content_subject_sha256"] in markdown,
            f"{episode['episode_id']}: Markdown parity differs",
        )
    for row in final["action_accounting"]:
        require(
            row["action_id"] in markdown
            and row["primary_accounting_state"] in markdown,
            f"{row['action_id']}: Markdown accounting differs",
        )
    require(
        "delegated_authority_accepts_episode_candidates" in markdown,
        "delegated decision request missing from Markdown",
    )


def validate() -> dict[str, Any]:
    preflight()
    require(
        ACCEPTANCE_OUTPUT.read_bytes() == ACCEPTANCE_SOURCE.read_bytes(),
        "imported acceptance final bytes differ",
    )
    require(
        file_digest(ACCEPTANCE_OUTPUT) == ACCEPTANCE_FILE_SHA256
        and load(ACCEPTANCE_OUTPUT)["content_subject_sha256"]
        == ACCEPTANCE_CONTENT_SHA256,
        "imported acceptance hashes differ",
    )
    acceptance_schema = load(
        SCHEMA_ROOT / "delegated_implementation_acceptance_v1.schema.json"
    )
    errors = list(
        Draft7Validator(acceptance_schema).iter_errors(load(ACCEPTANCE_OUTPUT))
    )
    require(
        not errors, f"acceptance schema failure: {errors[0].message if errors else ''}"
    )
    values = {name: load(OUTPUT_ROOT / name) for name in JSON_NAMES}
    for name, value in values.items():
        schema = load(SCHEMA_ROOT / name.replace(".json", "_v1.schema.json"))
        Draft7Validator.check_schema(schema)
        errors = list(Draft7Validator(schema).iter_errors(value))
        require(
            not errors, f"{name}: schema failure: {errors[0].message if errors else ''}"
        )
    parity = load(OUTPUT_ROOT / "parity_manifest.json")
    parity_schema = load(SCHEMA_ROOT / "parity_manifest_v1.schema.json")
    errors = list(Draft7Validator(parity_schema).iter_errors(parity))
    require(not errors, f"parity schema failure: {errors[0].message if errors else ''}")
    result = validate_artifacts(values)
    validate_parity()
    build(check=True)
    tracked_runtime = subprocess.check_output(
        ["git", "ls-files", "backend/app", "frontend"], cwd=ROOT, text=True
    ).splitlines()
    require(
        not any(
            BATCH_ID.encode() in (ROOT / path).read_bytes()
            for path in tracked_runtime
            if Path(path).suffix in {".py", ".ts", ".tsx", ".js", ".json"}
        ),
        "episode candidates entered runtime/public selectors",
    )
    require(
        BATCH_ID.encode()
        not in (
            ROOT
            / "docs/editorial/full_record_reviews/f000477_justice_public_safety_119_review_state_v1.json"
        ).read_bytes(),
        "canonical review state changed",
    )
    return {
        "status": "pass",
        "batch_id": BATCH_ID,
        "batch_content_subject_sha256": values["frozen_episode_candidate_batch.json"][
            "content_subject_sha256"
        ],
        **result,
        "parity_state": "pass",
    }


def main() -> int:
    print(json.dumps(validate(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
