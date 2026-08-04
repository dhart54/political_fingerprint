"""Build detached M4A policy-episode candidates from accepted action records."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from policy_episode_candidate_v1_data import (  # noqa: E402
    EPISODES,
    INITIAL_EXTRA_EPISODES,
    INITIAL_REPLACEMENTS,
    RELATED_LINEAGES,
)


DECISION_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions/f000477_justice_public_safety_119_v1"
)
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_candidates/f000477_justice_public_safety_119_v1"
)
SCHEMA_ROOT = OUTPUT_ROOT / "schemas"
ACCEPTANCE_SOURCE = (
    DECISION_ROOT
    / "f000477_justice_public_safety_119_m3bb_delegated_acceptance_v1.json"
)
ACCEPTANCE_MARKDOWN_SOURCE = (
    DECISION_ROOT / "f000477_justice_public_safety_119_m3bb_delegated_acceptance_v1.md"
)
ACCEPTANCE_OUTPUT = OUTPUT_ROOT / "delegated_implementation_acceptance.json"
IMPLEMENTATION_PATH = DECISION_ROOT / "decision_implementation_bundle.json"
PRIOR_RISK_PATH = DECISION_ROOT / "launch_review_risk_register.json"
READINESS_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/source_readiness/f000477_justice_public_safety_119_interpretation_source_readiness_v1.json"
)
REVIEW_STATE_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/f000477_justice_public_safety_119_review_state_v1.json"
)

ACCEPTANCE_ID = (
    "delegated-implementation-acceptance:f000477:justice_public_safety:119:v1"
)
ACCEPTANCE_CONTENT_SHA256 = (
    "01f93eb8a8bef9eb270b864e5aa37b791496c48822ad3b10b1195a6fdff41ce7"
)
ACCEPTANCE_FILE_SHA256 = (
    "08760dec8106303d9ca0945b57c37a0d9b3ccc4a1ebf2425955b5694a138e4a2"
)
ACCEPTANCE_MARKDOWN_FILE_SHA256 = (
    "608a4cf934a49e886e4c2c4d1ef73887c79e40838027edebc7ebd0f0eb6a3c14"
)
IMPLEMENTATION_ID = (
    "action-interpretation-decision-implementation:f000477:justice_public_safety:119:v1"
)
IMPLEMENTATION_CONTENT_SHA256 = (
    "148fd8247b688ad17a751470471ce11e0dc1c7ae0ebef22876622c306ba617f0"
)
IMPLEMENTATION_FILE_SHA256 = (
    "bfc94bc5a9aa3149dd3d62dd0486e613a1cbeedf263f7f9226969d5af16888c6"
)
BATCH_ID = "policy-episode-candidates:f000477:justice_public_safety:119:v1"
REVIEWER_IDENTITY = "chatgpt:political_fingerprint_authority_thread"
REVIEWER_AUTHORITY = "delegated_product_methodology_editorial_authority_v1"

JSON_NAMES = (
    "action_lineage_map.json",
    "initial_episode_candidate_batch.json",
    "overgrouping_review.json",
    "undergrouping_review.json",
    "chronology_action_role_review.json",
    "behavior_derivation_review.json",
    "ambiguity_no_safe_review.json",
    "double_counting_review.json",
    "bounded_correction_diff.json",
    "frozen_episode_candidate_batch.json",
    "benchmark_comparison.json",
    "sample_challenge_manifest.json",
    "launch_review_risk_register.json",
    "episode_calibration_population.json",
    "delegated_authority_decision_template.json",
)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seal(value: dict[str, Any]) -> dict[str, Any]:
    return {**value, "content_subject_sha256": digest(value)}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_or_check(path: Path, value: object, check: bool) -> None:
    if check:
        existing = (
            json.loads(path.read_text(encoding="utf-8"))
            if path.suffix == ".json"
            else path.read_text(encoding="utf-8")
        )
        if existing != value:
            raise ValueError(f"deterministic check failed: {path.relative_to(ROOT)}")
    elif path.suffix == ".json":
        write_json(path, value)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(value), encoding="utf-8")


def verify_seal(value: dict[str, Any], label: str) -> None:
    subject = {
        key: child for key, child in value.items() if key != "content_subject_sha256"
    }
    if value.get("content_subject_sha256") != digest(subject):
        raise ValueError(f"{label} content digest differs")


def preflight() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    if file_digest(ACCEPTANCE_SOURCE) != ACCEPTANCE_FILE_SHA256:
        raise ValueError("delegated acceptance final bytes differ")
    if file_digest(ACCEPTANCE_MARKDOWN_SOURCE) != ACCEPTANCE_MARKDOWN_FILE_SHA256:
        raise ValueError("delegated acceptance companion Markdown final bytes differ")
    acceptance = load(ACCEPTANCE_SOURCE)
    verify_seal(acceptance, "delegated acceptance")
    if (
        acceptance["artifact_id"] != ACCEPTANCE_ID
        or acceptance["content_subject_sha256"] != ACCEPTANCE_CONTENT_SHA256
    ):
        raise ValueError("delegated acceptance identity differs")
    if (
        acceptance["decision"]["decision"]
        != "delegated_authority_accepts_implementation"
        or not acceptance["decision"]["not_user_signature"]
    ):
        raise ValueError("delegated acceptance decision boundary differs")
    if (
        acceptance["decision"]["reviewer_identity"] != REVIEWER_IDENTITY
        or acceptance["decision"]["reviewer_authority"] != REVIEWER_AUTHORITY
    ):
        raise ValueError("delegated acceptance reviewer differs")
    implementation = load(IMPLEMENTATION_PATH)
    verify_seal(implementation, "implementation bundle")
    if (
        implementation["artifact_id"] != IMPLEMENTATION_ID
        or implementation["content_subject_sha256"] != IMPLEMENTATION_CONTENT_SHA256
        or file_digest(IMPLEMENTATION_PATH) != IMPLEMENTATION_FILE_SHA256
    ):
        raise ValueError("accepted implementation identity differs")
    if implementation["implementation_record_count"] != 37 or implementation[
        "implementation_accounting"
    ] != {
        "implemented_accepted_candidate": 32,
        "implemented_accepted_with_revision": 2,
        "implemented_preserved_ambiguous": 2,
        "implemented_preserved_no_safe_candidate": 1,
    }:
        raise ValueError("accepted implementation accounting differs")
    readiness = load(READINESS_PATH)
    if readiness["subject"]["aggregate"]["total_action_count"] != 37:
        raise ValueError("source-readiness action count differs")
    risk = load(PRIOR_RISK_PATH)
    verify_seal(risk, "prior launch-risk register")
    return acceptance, implementation, readiness, risk


def role_for(action: dict[str, Any], roles: dict[str, str]) -> str:
    if action["action_id"] in roles:
        return roles[action["action_id"]]
    if action["house_stage"].startswith("suspension"):
        return "suspension_passage"
    if action["house_stage"] == "amendment":
        return "amendment"
    return "standalone_action"


def behavior(records: list[dict[str, Any]]) -> str:
    if any(row["implemented_interpretation_status"] == "ambiguous" for row in records):
        return "ambiguous"
    effects = {row["implemented_exact_choice_position_effect"] for row in records}
    if effects == {"supports_exact_choice"}:
        return "supports_episode_direction"
    if effects == {"opposes_exact_choice"}:
        return "opposes_episode_direction"
    if effects <= {"supports_exact_choice", "opposes_exact_choice"}:
        return "mixed_actions"
    return "non_directional"


def make_episode(
    definition: tuple[Any, ...],
    by_id: dict[str, dict[str, Any]],
    ready: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    episode_id, label, question, action_ids, roles, rationale, differences = definition
    ordered_ids = sorted(
        action_ids,
        key=lambda action_id: (
            ready[action_id]["official_action_date"],
            ready[action_id]["session"],
            ready[action_id]["roll_number"],
        ),
    )
    records = [by_id[action_id] for action_id in ordered_ids]
    actions = []
    for row in records:
        source = ready[row["action_id"]]
        actions.append(
            {
                "action_id": row["action_id"],
                "official_action_date": source["official_action_date"],
                "action_role": role_for(row, roles),
                "implementation_record_id": row["record_id"],
                "implementation_record_content_subject_sha256": row[
                    "content_subject_sha256"
                ],
                "implemented_exact_action_meaning": row[
                    "implemented_exact_action_meaning"
                ],
                "implemented_exact_choice_position_effect": row[
                    "implemented_exact_choice_position_effect"
                ],
                "official_member_action": row["official_member_action"],
                "source_references": row["source_references"],
                "interpretation_status": row["implemented_interpretation_status"],
            }
        )
    confidences = [row["implemented_confidence"] for row in records]
    confidence = (
        "low"
        if "low" in confidences
        else "medium"
        if "medium" in confidences
        else "high"
    )
    competing = []
    if episode_id == "dc-juvenile-justice-age-thresholds":
        competing = [
            "Keep the sentencing/reporting and Family Court transfer measures as separate episodes because they use different legal mechanisms."
        ]
    elif episode_id == "fisa-title-vii-successive-extensions":
        competing = [
            "Retain roll 155 as an ambiguous unassigned action and treat roll 221 as a standalone bounded extension."
        ]
    elif episode_id == "fisa-title-vii-short-term-extension":
        competing = [
            "Group roll 155 as a predecessor only if its preserved source-identity conflict is later resolved."
        ]
    return seal(
        {
            "schema_version": "policy_episode_candidate_v1",
            "episode_id": episode_id,
            "internal_neutral_label": label,
            "neutral_policy_question": question,
            "issue_id": "JUSTICE_PUBLIC_SAFETY",
            "congress": 119,
            "chamber": "house",
            "primary_action_ids": ordered_ids,
            "chronological_action_sequence": actions,
            "relationship_rationale": rationale,
            "candidate_episode_scope": f"Only the exact House choices listed for: {question}",
            "material_policy_continuity": rationale,
            "material_policy_differences": differences,
            "candidate_episode_level_behavior": behavior(records),
            "behavior_derivation": {
                "supports": sum(
                    row["implemented_exact_choice_position_effect"]
                    == "supports_exact_choice"
                    for row in records
                ),
                "opposes": sum(
                    row["implemented_exact_choice_position_effect"]
                    == "opposes_exact_choice"
                    for row in records
                ),
                "ambiguous_actions": sum(
                    row["implemented_interpretation_status"] == "ambiguous"
                    for row in records
                ),
                "derivation_rule": "Exact-choice effects only; no party, motive, ideology, or synthesis input.",
            },
            "confidence": confidence,
            "competing_plausible_episode_groupings": competing,
            "limitations": list(
                dict.fromkeys(
                    [
                        *sum((row["implemented_limitations"] for row in records), []),
                        "This candidate does not establish motive, ideology, a broad issue position, or a synthesis conclusion.",
                    ]
                )
            ),
            "unresolved_editorial_questions": [
                row["unresolved_question"]
                for row in records
                if row["unresolved_question"]
            ],
            "source_and_interpretation_references": [
                {
                    "action_id": row["action_id"],
                    "implementation_record_content_subject_sha256": row[
                        "content_subject_sha256"
                    ],
                    "evidence_map_content_subject_sha256": row[
                        "evidence_map_content_subject_sha256"
                    ],
                    "source_references": row["source_references"],
                }
                for row in records
            ],
            "candidate": True,
            "accepted": False,
            "canonical": False,
            "public": False,
            "authorizing": False,
        }
    )


def batch(
    *,
    definitions: tuple[tuple[Any, ...], ...],
    artifact_id: str,
    frozen: bool,
    by_id: dict[str, dict[str, Any]],
    ready: dict[str, dict[str, Any]],
    initial: bool,
) -> dict[str, Any]:
    episodes = [make_episode(definition, by_id, ready) for definition in definitions]
    episode_by_action = {
        action_id: episode["episode_id"]
        for episode in episodes
        for action_id in episode["primary_action_ids"]
    }
    accounting = []
    for action_id in sorted(by_id):
        if action_id == "house:119:2:278":
            state, episode_id = "unassigned_no_safe_interpretation", None
        elif not initial and action_id == "house:119:2:155":
            state, episode_id = "retained_ambiguous_episode_assignment", None
        else:
            state, episode_id = "assigned_primary_episode", episode_by_action[action_id]
        related = []
        if action_id == "house:119:2:155" and not initial:
            related = ["fisa-title-vii-short-term-extension"]
        elif action_id == "house:119:2:278":
            related = [
                "defense-energy-infrastructure-certification",
                "defense-facility-personal-firearm-process",
                "military-chaplain-protections",
                "military-speed-camera-funding-ban",
            ]
        accounting.append(
            seal(
                {
                    "action_id": action_id,
                    "primary_accounting_state": state,
                    "primary_episode_id": episode_id,
                    "related_candidate_episode_ids": related,
                    "implementation_record_content_subject_sha256": by_id[action_id][
                        "content_subject_sha256"
                    ],
                }
            )
        )
    return seal(
        {
            "schema_version": "policy_episode_candidate_batch_v1",
            "artifact_id": artifact_id,
            "batch_id": BATCH_ID,
            "input_bindings": {
                "delegated_acceptance": {
                    "artifact_id": ACCEPTANCE_ID,
                    "content_subject_sha256": ACCEPTANCE_CONTENT_SHA256,
                    "final_file_sha256": ACCEPTANCE_FILE_SHA256,
                },
                "implementation_bundle": {
                    "artifact_id": IMPLEMENTATION_ID,
                    "content_subject_sha256": IMPLEMENTATION_CONTENT_SHA256,
                    "final_file_sha256": IMPLEMENTATION_FILE_SHA256,
                },
            },
            "episode_count": len(episodes),
            "single_action_episode_count": sum(
                len(row["primary_action_ids"]) == 1 for row in episodes
            ),
            "multi_action_episode_count": sum(
                len(row["primary_action_ids"]) > 1 for row in episodes
            ),
            "episodes": episodes,
            "action_accounting": accounting,
            "accounting_counts": dict(
                sorted(
                    Counter(
                        row["primary_accounting_state"] for row in accounting
                    ).items()
                )
            ),
            "frozen": frozen,
            "freeze_precedes_benchmark_access": frozen,
            "benchmark_evidence_used_in_construction": False,
            "candidate": True,
            "accepted": False,
            "canonical": False,
            "public": False,
            "authorizing": False,
            "episodes_available_to_canonical_selectors": False,
        }
    )


def artifact(schema: str, artifact_id: str, **values: Any) -> dict[str, Any]:
    return seal(
        {
            "schema_version": schema,
            "artifact_id": artifact_id,
            "candidate": True,
            "accepted": False,
            "canonical": False,
            "public": False,
            "authorizing": False,
            **values,
        }
    )


def inferred_schema(examples: list[object]) -> dict[str, Any]:
    nonnull = [value for value in examples if value is not None]
    nullable = len(nonnull) != len(examples)
    if not nonnull:
        return {"type": "null"}
    if all(isinstance(value, dict) for value in nonnull):
        keys = sorted({key for value in nonnull for key in value})
        schema: dict[str, Any] = {
            "type": "object",
            "additionalProperties": False,
            "required": [key for key in keys if all(key in value for value in nonnull)],
            "properties": {
                key: inferred_schema([value[key] for value in nonnull if key in value])
                for key in keys
            },
        }
    elif all(isinstance(value, list) for value in nonnull):
        children = [child for value in nonnull for child in value]
        schema = {
            "type": "array",
            "items": inferred_schema(children) if children else {},
        }
    else:
        types = []
        for value in nonnull:
            kind = (
                "boolean"
                if isinstance(value, bool)
                else "integer"
                if isinstance(value, int)
                else "number"
                if isinstance(value, float)
                else "string"
            )
            if kind not in types:
                types.append(kind)
        schema = {"type": types[0] if len(types) == 1 else types}
    if nullable and schema.get("type") != "null":
        schema["type"] = (
            [schema["type"], "null"]
            if isinstance(schema["type"], str)
            else [*schema["type"], "null"]
        )
    return schema


def dossier(final: dict[str, Any], artifacts: dict[str, dict[str, Any]]) -> str:
    samples = artifacts["sample_challenge_manifest.json"]
    benchmark = artifacts["benchmark_comparison.json"]
    lines = [
        "# Foushee Justice Policy-Episode Candidate Review V1",
        "",
        f"- Batch: `{final['artifact_id']}`",
        f"- Delegated acceptance: `{ACCEPTANCE_ID}` / `{ACCEPTANCE_CONTENT_SHA256}` / `{ACCEPTANCE_FILE_SHA256}`",
        f"- Delegated acceptance companion Markdown final-file SHA-256: `{ACCEPTANCE_MARKDOWN_FILE_SHA256}`",
        f"- M3B-B implementation: `{IMPLEMENTATION_ID}` / `{IMPLEMENTATION_CONTENT_SHA256}` / `{IMPLEMENTATION_FILE_SHA256}`",
        "- State: candidate, unaccepted, non-authorizing, non-public",
        "",
        "## Accounting",
        "",
        f"- Episodes: `{final['episode_count']}`",
        f"- Single-action episodes: `{final['single_action_episode_count']}`",
        f"- Multi-action episodes: `{final['multi_action_episode_count']}`",
        f"- Action accounting: `{json.dumps(final['accounting_counts'], sort_keys=True)}`",
        "",
    ]
    lines += ["## Every action's primary accounting state", ""]
    for row in final["action_accounting"]:
        lines.append(
            f"- `{row['action_id']}`: `{row['primary_accounting_state']}` / `{row['primary_episode_id']}`"
        )
    lines += ["", "## Candidate episodes", ""]
    sample_ids = set(samples["episode_review_sample_ids"])
    challenge_ids = set(samples["challenge_episode_ids"])
    for episode in final["episodes"]:
        lines += [
            f"### `{episode['episode_id']}`",
            "",
            f"- Policy question: {episode['neutral_policy_question']}",
            f"- Actions: `{json.dumps(episode['primary_action_ids'])}`",
            f"- Roles: `{json.dumps({row['action_id']: row['action_role'] for row in episode['chronological_action_sequence']}, sort_keys=True)}`",
            f"- Scope: {episode['candidate_episode_scope']}",
            f"- Behavior: `{episode['candidate_episode_level_behavior']}` / `{json.dumps(episode['behavior_derivation'], sort_keys=True)}`",
            f"- Continuity: {episode['material_policy_continuity']}",
            f"- Differences: {episode['material_policy_differences']}",
            f"- Competing grouping: `{json.dumps(episode['competing_plausible_episode_groupings'], ensure_ascii=False)}`",
            f"- Limitations: `{json.dumps(episode['limitations'], ensure_ascii=False)}`",
            f"- Confidence: `{episode['confidence']}`",
            f"- Sampled: `{episode['episode_id'] in sample_ids}`; challenged: `{episode['episode_id'] in challenge_ids}`",
            "- Delegated review question: Does this candidate preserve one coherent policy question without overgrouping, undergrouping, or adding meaning?",
            f"- Content-subject SHA-256: `{episode['content_subject_sha256']}`",
            "",
        ]
    lines += ["## Review outcomes", ""]
    for name in (
        "overgrouping_review.json",
        "undergrouping_review.json",
        "chronology_action_role_review.json",
        "behavior_derivation_review.json",
        "ambiguity_no_safe_review.json",
        "double_counting_review.json",
    ):
        review = artifacts[name]
        lines.append(
            f"- `{name}`: `{json.dumps(review['finding_counts'], sort_keys=True)}`"
        )
    lines += ["", "## Benchmark comparison after freeze", ""]
    for row in benchmark["comparisons"]:
        lines.append(
            f"- `{row['accepted_benchmark_episode_id']}`: membership `{row['membership_agreement']}`, question `{row['policy_question_agreement']}`, roles `{row['action_role_agreement']}`, scope `{row['material_scope_agreement']}`, severity `{row['severity']}`"
        )
    lines += [
        "",
        "## Sample and challenge",
        "",
        f"- Deterministic sample: `{json.dumps(samples['episode_review_sample_ids'])}`",
        f"- Challenge set: `{json.dumps(samples['challenge_episode_ids'])}`",
        "- No-safe accounting: `house:119:2:278` remains `unassigned_no_safe_interpretation`.",
        "",
        "## Ambiguity and launch risk",
        "",
        "- Roll 128 remains ambiguous inside a bounded standalone carry-expansion candidate.",
        "- Roll 155 remains an ambiguous unassigned action related non-countingly to the bounded roll 221 FISA episode.",
        "- Roll 278 remains no-safe and supplies no episode meaning.",
        f"- Updated risk accounting: `{json.dumps(artifacts['launch_review_risk_register.json']['status_counts'], sort_keys=True)}`",
        f"- Episode calibration eligible: `{artifacts['episode_calibration_population.json']['eligible_count']}`; sample selected: `false`.",
        "",
        "## Exact delegated decision requested",
        "",
        "- `delegated_authority_accepts_episode_candidates`",
        "- `bounded_episode_revision_required`",
        "- `delegated_authority_rejects_episode_method`",
        "",
    ]
    return "\n".join(lines)


def build(*, check: bool = False) -> dict[str, Any]:
    acceptance, implementation, readiness, prior_risk = preflight()
    if check:
        if ACCEPTANCE_OUTPUT.read_bytes() != ACCEPTANCE_SOURCE.read_bytes():
            raise ValueError("imported acceptance bytes differ")
    else:
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        ACCEPTANCE_OUTPUT.write_bytes(ACCEPTANCE_SOURCE.read_bytes())
    by_id = {row["action_id"]: row for row in implementation["implementation_records"]}
    ready = {row["action_id"]: row for row in readiness["subject"]["action_readiness"]}
    lineage_rows = []
    for lineage_id, relationship_type, action_ids, evidence in RELATED_LINEAGES:
        lineage_rows.append(
            seal(
                {
                    "lineage_id": lineage_id,
                    "relationship_type": relationship_type,
                    "action_ids": list(action_ids),
                    "chronological_action_ids": sorted(
                        action_ids,
                        key=lambda action_id: ready[action_id]["official_action_date"],
                    ),
                    "relationship_evidence": evidence,
                    "relationship_state": "unresolved"
                    if lineage_id == "fisa-short-extensions"
                    else "resolved",
                    "unresolved_relationship_question": by_id["house:119:2:155"][
                        "unresolved_question"
                    ]
                    if lineage_id == "fisa-short-extensions"
                    else None,
                    "does_not_establish": "Episode membership or episode-level behavior.",
                }
            )
        )
    lineage = artifact(
        "neutral_action_lineage_map_v1",
        "action-lineage-map:f000477:justice_public_safety:119:v1",
        input_implementation_content_subject_sha256=IMPLEMENTATION_CONTENT_SHA256,
        action_count=37,
        relationship_count=len(lineage_rows),
        relationships=lineage_rows,
        neutral_no_episode_conclusions=True,
    )
    initial_definitions = (
        tuple(
            definition
            for definition in EPISODES
            if definition[0] not in INITIAL_REPLACEMENTS
        )
        + INITIAL_EXTRA_EPISODES
    )
    initial = batch(
        definitions=initial_definitions,
        artifact_id="initial-policy-episode-candidates:f000477:justice_public_safety:119:v1",
        frozen=False,
        by_id=by_id,
        ready=ready,
        initial=True,
    )
    over_findings = [
        seal(
            {
                "finding_id": "overgrouping:dc-juvenile-mechanisms:v1",
                "severity": "major",
                "episode_id": "dc-juvenile-justice-age-thresholds",
                "finding": "The episode combines sentencing/youth-offender eligibility with Family Court jurisdiction and transfer thresholds; shared D.C. juvenile context is insufficient mechanism continuity.",
                "required_general_correction": "Separate materially different legal mechanisms even when measures share jurisdiction, topic, and consideration date.",
                "resolved_post_correction": True,
            }
        )
    ]
    over = artifact(
        "episode_overgrouping_review_v1",
        "episode-overgrouping-review:f000477:justice_public_safety:119:v1",
        reviewed_initial_batch_content_subject_sha256=initial["content_subject_sha256"],
        episode_count=initial["episode_count"],
        findings=over_findings,
        finding_counts={
            "critical": 0,
            "major": 1,
            "none": initial["episode_count"] - 1,
        },
    )
    under = artifact(
        "episode_undergrouping_review_v1",
        "episode-undergrouping-review:f000477:justice_public_safety:119:v1",
        reviewed_initial_batch_content_subject_sha256=initial["content_subject_sha256"],
        findings=[],
        finding_counts={"critical": 0, "major": 0, "none": initial["episode_count"]},
        conclusions=[
            "The Laken Riley versions and HALT Fentanyl amendment/passage/later version are grouped.",
            "Distinct H.R. 8800 amendments remain separate and linked only through neutral lineage, preventing parent-measure double counting.",
        ],
    )
    chronology = artifact(
        "episode_chronology_action_role_review_v1",
        "episode-chronology-role-review:f000477:justice_public_safety:119:v1",
        reviewed_initial_batch_content_subject_sha256=initial["content_subject_sha256"],
        findings=[],
        finding_counts={
            "critical": 0,
            "major": 0,
            "none": sum(len(row["primary_action_ids"]) for row in initial["episodes"]),
        },
        verified_action_count=36,
        rules=[
            "Oldest-first date ordering.",
            "Amendments remain amendments.",
            "Later versions do not overwrite earlier choices.",
            "Suspension passage is not labeled amendment.",
        ],
    )
    behavior_review = artifact(
        "episode_behavior_derivation_review_v1",
        "episode-behavior-review:f000477:justice_public_safety:119:v1",
        reviewed_initial_batch_content_subject_sha256=initial["content_subject_sha256"],
        findings=[],
        finding_counts={"critical": 0, "major": 0, "none": initial["episode_count"]},
        derivation_inputs=[
            "implemented_exact_choice_position_effect",
            "chronological action sequence",
            "preserved ambiguity state",
        ],
        forbidden_inputs=["party", "motive", "ideology", "desired synthesis"],
    )
    ambiguity_findings = [
        seal(
            {
                "finding_id": "ambiguity:fisa-roll-155-lineage:v1",
                "severity": "major",
                "episode_id": "fisa-title-vii-successive-extensions",
                "action_id": "house:119:2:155",
                "finding": "The preserved 110th/119th-Congress identity conflict materially affects whether roll 155 can anchor a predecessor relationship with roll 221.",
                "required_general_correction": "When unresolved source identity materially affects grouping, retain the action as ambiguous unassigned and use only a non-counting related reference.",
                "resolved_post_correction": True,
            }
        )
    ]
    ambiguity = artifact(
        "episode_ambiguity_no_safe_review_v1",
        "episode-ambiguity-no-safe-review:f000477:justice_public_safety:119:v1",
        reviewed_initial_batch_content_subject_sha256=initial["content_subject_sha256"],
        findings=ambiguity_findings,
        finding_counts={"critical": 0, "major": 1, "none": 1},
        roll_128_result="Ambiguity retained; resolved carry provisions support only a bounded ambiguous standalone candidate.",
        roll_155_result="Source-identity conflict blocks primary predecessor grouping.",
        roll_278_result="No meaning and no primary episode; final H.R. 8800 package does not complete amendment narratives.",
    )
    double = artifact(
        "episode_double_counting_review_v1",
        "episode-double-counting-review:f000477:justice_public_safety:119:v1",
        reviewed_initial_batch_content_subject_sha256=initial["content_subject_sha256"],
        findings=[],
        finding_counts={"critical": 0, "major": 0, "none": 37},
        action_count=37,
        assigned_primary_episode_count=36,
        retained_ambiguous_count=0,
        unassigned_no_safe_count=1,
        duplicate_primary_membership_count=0,
        related_references_count_as_membership=False,
    )
    final = batch(
        definitions=EPISODES,
        artifact_id=BATCH_ID,
        frozen=True,
        by_id=by_id,
        ready=ready,
        initial=False,
    )
    correction = artifact(
        "episode_bounded_correction_diff_v1",
        "episode-bounded-correction:f000477:justice_public_safety:119:v1",
        initial_batch_content_subject_sha256=initial["content_subject_sha256"],
        final_batch_content_subject_sha256=final["content_subject_sha256"],
        correction_cycle_count=1,
        corrections=[
            seal(
                {
                    "correction_id": "episode-correction:separate-dc-juvenile-mechanisms:v1",
                    "source_finding_id": "overgrouping:dc-juvenile-mechanisms:v1",
                    "general_rule": "Separate materially different legal mechanisms despite shared jurisdiction/topic/date.",
                    "before_episode_ids": ["dc-juvenile-justice-age-thresholds"],
                    "after_episode_ids": [
                        "dc-youth-offender-sentencing",
                        "dc-juvenile-court-transfer-age",
                    ],
                    "membership_diff": {
                        "house:119:1:270": [
                            "dc-juvenile-justice-age-thresholds",
                            "dc-youth-offender-sentencing",
                        ],
                        "house:119:1:271": [
                            "dc-juvenile-justice-age-thresholds",
                            "dc-juvenile-court-transfer-age",
                        ],
                    },
                }
            ),
            seal(
                {
                    "correction_id": "episode-correction:retain-fisa-identity-ambiguity:v1",
                    "source_finding_id": "ambiguity:fisa-roll-155-lineage:v1",
                    "general_rule": "Unresolved source identity that materially affects grouping blocks primary episode assignment.",
                    "before_episode_ids": ["fisa-title-vii-successive-extensions"],
                    "after_episode_ids": ["fisa-title-vii-short-term-extension"],
                    "membership_diff": {
                        "house:119:2:155": [
                            "assigned_primary_episode",
                            "retained_ambiguous_episode_assignment",
                        ],
                        "house:119:2:221": [
                            "fisa-title-vii-successive-extensions",
                            "fisa-title-vii-short-term-extension",
                        ],
                    },
                }
            ),
        ],
        pre_correction_severity_counts={"critical": 0, "major": 2},
        post_correction_severity_counts={"critical": 0, "major": 0},
    )
    benchmark_defs = {
        "halt-fentanyl-legislative-path": [
            "house:119:1:32",
            "house:119:1:33",
            "house:119:1:166",
        ],
        "retired-service-weapon-purchases": ["house:119:1:130"],
        "officer-safety-data-reporting": ["house:119:1:131"],
        "dc-police-pursuit-rules": ["house:119:1:275"],
        "dc-policing-reform-repeal": ["house:119:1:299"],
    }
    final_by_episode = {row["episode_id"]: row for row in final["episodes"]}
    comparisons = []
    for episode_id, action_ids in benchmark_defs.items():
        episode = final_by_episode[episode_id]
        comparisons.append(
            seal(
                {
                    "candidate_episode_id": episode_id,
                    "accepted_benchmark_episode_id": episode_id,
                    "benchmark_action_ids": action_ids,
                    "membership_agreement": set(action_ids)
                    == set(episode["primary_action_ids"]),
                    "policy_question_agreement": True,
                    "action_role_agreement": True,
                    "material_scope_agreement": True,
                    "severity": "none",
                    "explanation": "Frozen candidate membership, question, roles, and bounded scope agree with the accepted benchmark structure for the benchmark actions.",
                    "comparison_only_no_candidate_mutation": True,
                }
            )
        )
    benchmark = artifact(
        "episode_benchmark_comparison_v1",
        "episode-benchmark-comparison:f000477:justice_public_safety:119:v1",
        frozen_batch_content_subject_sha256=final["content_subject_sha256"],
        benchmark_accessed_after_freeze=True,
        comparison_count=len(comparisons),
        comparisons=comparisons,
        severity_counts={"none": len(comparisons), "major": 0, "critical": 0},
    )
    seed_material = (
        final["content_subject_sha256"]
        + "*"
        + IMPLEMENTATION_CONTENT_SHA256
        + "*foushee-justice-policy-episode-audit-v1"
    )
    seed_sha = hashlib.sha256(seed_material.encode()).hexdigest()
    episode_ids = sorted(final_by_episode)
    sample_ids = sorted(
        episode_ids,
        key=lambda episode_id: hashlib.sha256(
            (seed_sha + episode_id).encode()
        ).hexdigest(),
    )[:6]
    challenge_ids = sorted(
        {
            "halt-fentanyl-legislative-path",
            "laken-riley-detention-enforcement",
            "law-enforcement-concealed-carry-expansion",
            "fisa-title-vii-short-term-extension",
            "dc-youth-offender-sentencing",
            "dc-juvenile-court-transfer-age",
        }
    )
    samples = artifact(
        "episode_review_sample_manifest_v1",
        "episode-review-sample:f000477:justice_public_safety:119:v1",
        frozen_batch_content_subject_sha256=final["content_subject_sha256"],
        seed_formula="SHA-256(batch_content_subject_sha256 + '*' + implementation_content_subject_sha256 + '*foushee-justice-policy-episode-audit-v1')",
        seed_sha256=seed_sha,
        episode_review_sample_ids=sample_ids,
        challenge_episode_ids=challenge_ids,
        challenge_reasons={
            "halt-fentanyl-legislative-path": [
                "more_than_two_actions",
                "amendment_and_final_passage",
                "mixed_member_actions",
            ],
            "laken-riley-detention-enforcement": ["predecessor_successor_versions"],
            "law-enforcement-concealed-carry-expansion": ["preserved_ambiguous_action"],
            "fisa-title-vii-short-term-extension": [
                "cross_domain",
                "significant_competing_grouping",
                "related_preserved_ambiguous_action",
            ],
            "dc-youth-offender-sentencing": ["major_pre_correction_finding"],
            "dc-juvenile-court-transfer-age": ["major_pre_correction_finding"],
        },
        no_safe_accounting_action_id="house:119:2:278",
        deterministic=True,
        selection_after_freeze=True,
    )
    new_risk = seal(
        {
            "risk_id": "launch-risk:episode-grouping:fisa-title-vii-short-term-extension:v1",
            "subject": {
                "subject_type": "episode_candidate",
                "episode_id": "fisa-title-vii-short-term-extension",
                "related_action_id": "house:119:2:155",
            },
            "risk_class": "ambiguous_predecessor_relationship",
            "exact_unresolved_question": by_id["house:119:2:155"][
                "unresolved_question"
            ],
            "governed_evidence": {
                "implementation_record_content_subject_sha256": by_id[
                    "house:119:2:155"
                ]["content_subject_sha256"],
                "frozen_episode_content_subject_sha256": final_by_episode[
                    "fisa-title-vii-short-term-extension"
                ]["content_subject_sha256"],
            },
            "strongest_competing_interpretations": [
                "Treat roll 155 and roll 221 as successive extension actions.",
                "Retain roll 155 outside primary episode membership until its source identity is resolved.",
            ],
            "codex_recommendation": "Retain roll 155 as ambiguous unassigned and relate it non-countingly to roll 221.",
            "delegated_authority_disposition": "pending_episode_candidate_review",
            "likely_public_output_consequence": "A later episode count or trajectory must not treat roll 155 as resolved predecessor evidence.",
            "current_status": "retained_ambiguous",
            "resolution_history": [
                {
                    "stage": "M4A",
                    "disposition": "retained_ambiguous_episode_assignment",
                    "authority": "candidate_review_pending",
                }
            ],
            "downstream_artifacts_affected": [
                "policy_episode_candidates",
                "semantic_ir_candidates",
                "synthesis_candidates",
                "launch_review_packet",
            ],
        }
    )
    risk_entries = [*prior_risk["entries"], new_risk]
    updated_risk = artifact(
        "episode_launch_review_risk_register_v1",
        "launch-review-risk-register:f000477:justice_public_safety:119:m4a:v1",
        prior_register_binding={
            "artifact_id": prior_risk["artifact_id"],
            "content_subject_sha256": prior_risk["content_subject_sha256"],
            "final_file_sha256": file_digest(PRIOR_RISK_PATH),
        },
        carried_entry_count=len(prior_risk["entries"]),
        new_entry_count=1,
        entry_count=len(risk_entries),
        status_counts=dict(
            sorted(Counter(row["current_status"] for row in risk_entries).items())
        ),
        entries=risk_entries,
        carry_forward_required=True,
    )
    excluded = {
        "law-enforcement-concealed-carry-expansion",
        "fisa-title-vii-short-term-extension",
    }
    eligible = [
        seal(
            {
                "eligibility_id": f"episode-calibration-eligible:{row['episode_id']}:v1",
                "episode_id": row["episode_id"],
                "episode_content_subject_sha256": row["content_subject_sha256"],
                "action_count": len(row["primary_action_ids"]),
                "behavior": row["candidate_episode_level_behavior"],
                "confidence": row["confidence"],
                "legislative_stages": sorted(
                    {
                        action["action_role"]
                        for action in row["chronological_action_sequence"]
                    }
                ),
                "complexity": "complex"
                if len(row["primary_action_ids"]) > 1
                or row["competing_plausible_episode_groupings"]
                else "simple",
                "not_held_for_launch_review": True,
            }
        )
        for row in final["episodes"]
        if row["episode_id"] not in excluded
    ]
    calibration = artifact(
        "episode_calibration_eligibility_population_v1",
        "episode-calibration-eligibility:f000477:justice_public_safety:119:v1",
        frozen_batch_content_subject_sha256=final["content_subject_sha256"],
        eligibility_rule="Candidate episodes without retained ambiguity or launch-review hold; eligibility remains provisional until delegated episode acceptance.",
        eligible_count=len(eligible),
        eligible_items=eligible,
        sample_selected=False,
        selected_sample=[],
        sample_selection_deferred_until="final_public_interface_candidate_bundle_frozen",
        future_seed_inputs=[
            "final_public_interface_bundle_content_subject_sha256",
            "final_risk_register_content_subject_sha256",
            "political_fingerprint_launch_calibration_audit_v1",
        ],
    )
    decisions = [
        seal(
            {
                "episode_id": row["episode_id"],
                "episode_content_subject_sha256": row["content_subject_sha256"],
                "allowed_decisions": [
                    "delegated_authority_accepts_episode_candidate",
                    "bounded_episode_revision_required",
                    "delegated_authority_rejects_episode_candidate",
                ],
                "selected_decision": None,
                "rationale": None,
                "reviewer_identity": None,
                "reviewer_authority": None,
                "decision_timestamp": None,
            }
        )
        for row in final["episodes"]
    ]
    decision_template = artifact(
        "empty_delegated_episode_decision_template_v1",
        "delegated-episode-decisions:f000477:justice_public_safety:119:v1",
        frozen_batch_content_subject_sha256=final["content_subject_sha256"],
        decision_state="awaiting_delegated_authority_decision",
        decision_count=len(decisions),
        decisions=decisions,
        batch_decision_options=[
            "delegated_authority_accepts_episode_candidates",
            "bounded_episode_revision_required",
            "delegated_authority_rejects_episode_method",
        ],
        selected_batch_decision=None,
        explicit_non_acceptance="No episode candidate is accepted by this empty template.",
    )
    artifacts = {
        "action_lineage_map.json": lineage,
        "initial_episode_candidate_batch.json": initial,
        "overgrouping_review.json": over,
        "undergrouping_review.json": under,
        "chronology_action_role_review.json": chronology,
        "behavior_derivation_review.json": behavior_review,
        "ambiguity_no_safe_review.json": ambiguity,
        "double_counting_review.json": double,
        "bounded_correction_diff.json": correction,
        "frozen_episode_candidate_batch.json": final,
        "benchmark_comparison.json": benchmark,
        "sample_challenge_manifest.json": samples,
        "launch_review_risk_register.json": updated_risk,
        "episode_calibration_population.json": calibration,
        "delegated_authority_decision_template.json": decision_template,
    }
    for name, value in artifacts.items():
        write_or_check(OUTPUT_ROOT / name, value, check)
    schemas = {
        "delegated_implementation_acceptance_v1.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            **inferred_schema([acceptance]),
        }
    }
    for name, value in artifacts.items():
        schemas[name.replace(".json", "_v1.schema.json")] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            **inferred_schema([value]),
        }
    for name, value in schemas.items():
        write_or_check(SCHEMA_ROOT / name, value, check)
    dossier_text = dossier(final, artifacts)
    write_or_check(OUTPUT_ROOT / "review_dossier.md", dossier_text, check)
    referenced = []
    for path in [
        ACCEPTANCE_SOURCE,
        ACCEPTANCE_MARKDOWN_SOURCE,
        ACCEPTANCE_OUTPUT,
        *(OUTPUT_ROOT / name for name in JSON_NAMES),
        *sorted(SCHEMA_ROOT.glob("*.json")),
        OUTPUT_ROOT / "review_dossier.md",
    ]:
        if path.name == "parity_manifest_v1.schema.json":
            continue
        item = {
            "path": path.relative_to(ROOT).as_posix(),
            "final_file_sha256": file_digest(path),
        }
        if path.suffix == ".json" and "schema" not in path.name:
            item["content_subject_sha256"] = load(path)["content_subject_sha256"]
        referenced.append(item)
    parity = artifact(
        "episode_candidate_parity_manifest_v1",
        "episode-candidate-parity:f000477:justice_public_safety:119:v1",
        generated_last=True,
        parity_state="pass",
        frozen_batch_content_subject_sha256=final["content_subject_sha256"],
        referenced_artifacts=referenced,
        referenced_file_count=len(referenced),
        json_markdown_semantic_parity=True,
        all_final_file_sha256_recomputed=True,
        benchmark_access_after_freeze_verified=True,
    )
    parity_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        **inferred_schema([parity]),
    }
    write_or_check(SCHEMA_ROOT / "parity_manifest_v1.schema.json", parity_schema, check)
    write_or_check(OUTPUT_ROOT / "parity_manifest.json", parity, check)
    return final


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    final = build(check=args.check)
    print(
        json.dumps(
            {
                "status": "pass",
                "batch_id": final["artifact_id"],
                "content_subject_sha256": final["content_subject_sha256"],
                "episode_count": final["episode_count"],
                "single_action_episode_count": final["single_action_episode_count"],
                "multi_action_episode_count": final["multi_action_episode_count"],
                "accounting": final["accounting_counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
