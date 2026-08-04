"""Build detached M4B implementations of delegated-accepted episode candidates."""

from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.universe_authority import file_digest_matches  # noqa: E402


DECISION_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions/f000477_justice_public_safety_119_v1"
)
M4A_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_candidates/f000477_justice_public_safety_119_v1"
)
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_justice_public_safety_119_v1"
)
SCHEMA_ROOT = OUTPUT_ROOT / "schemas"
ACCEPTANCE_SOURCE = (
    DECISION_ROOT
    / "f000477_justice_public_safety_119_m4a_delegated_episode_acceptance_v1.json"
)
ACCEPTANCE_OUTPUT = OUTPUT_ROOT / "delegated_episode_candidate_acceptance.json"
CANDIDATE_PATH = M4A_ROOT / "frozen_episode_candidate_batch.json"
M4A_RISK_PATH = M4A_ROOT / "launch_review_risk_register.json"
M4A_CALIBRATION_PATH = M4A_ROOT / "episode_calibration_population.json"
M3BB_PATH = DECISION_ROOT / "decision_implementation_bundle.json"

ACCEPTANCE_ID = (
    "delegated-episode-candidate-acceptance:f000477:justice_public_safety:119:v1"
)
ACCEPTANCE_CONTENT_SHA256 = (
    "825a5dc71f08a9e174c17d7c96cfeb38024e55ec75eab05ec02d6192a9787e94"
)
ACCEPTANCE_FILE_SHA256 = (
    "0fb8f4dba0047434c7b570b92739c54ee38661ddbd2262670dbbb06eb55ef826"
)
CANDIDATE_ID = "policy-episode-candidates:f000477:justice_public_safety:119:v1"
CANDIDATE_CONTENT_SHA256 = (
    "c7d5c3567fa606420a9e49fd01b4dcef70a728295626b3b9c9d4dfad6ec097b6"
)
CANDIDATE_FILE_SHA256 = (
    "00c38f9d56caba927b40dcf52152c308fd8bd4538a4854dab6e4376bb503c391"
)
M3BB_ID = (
    "action-interpretation-decision-implementation:f000477:justice_public_safety:119:v1"
)
M3BB_CONTENT_SHA256 = "148fd8247b688ad17a751470471ce11e0dc1c7ae0ebef22876622c306ba617f0"
M3BB_FILE_SHA256 = "bfc94bc5a9aa3149dd3d62dd0486e613a1cbeedf263f7f9226969d5af16888c6"
IMPLEMENTATION_ID = (
    "policy-episode-decision-implementation:f000477:justice_public_safety:119:v1"
)

JSON_NAMES = (
    "episode_implementation_bundle.json",
    "implementation_parity_report.json",
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
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def ratified_text_file_digest(path: Path) -> str:
    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return hashlib.sha256(content).hexdigest()


def seal(value: dict[str, Any]) -> dict[str, Any]:
    value["content_subject_sha256"] = digest(value)
    return value


def verify_seal(value: dict[str, Any], label: str) -> None:
    subject = {
        key: child for key, child in value.items() if key != "content_subject_sha256"
    }
    if value.get("content_subject_sha256") != digest(subject):
        raise ValueError(f"{label}: content-subject SHA-256 differs")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def serialized(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def write_bytes_or_check(path: Path, raw: bytes, *, check: bool) -> None:
    if check:
        if (
            not path.exists()
            or path.read_bytes().replace(b"\r\n", b"\n")
            != raw.replace(b"\r\n", b"\n")
        ):
            raise ValueError(
                f"{path.relative_to(ROOT)} differs from deterministic output"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def write_json_or_check(path: Path, value: object, *, check: bool) -> None:
    write_bytes_or_check(path, serialized(value), check=check)


def preflight() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if not file_digest_matches(ACCEPTANCE_SOURCE, ACCEPTANCE_FILE_SHA256):
        raise ValueError("delegated M4A acceptance final-file SHA-256 differs")
    acceptance = load(ACCEPTANCE_SOURCE)
    verify_seal(acceptance, "delegated M4A acceptance")
    if (
        acceptance["artifact_id"] != ACCEPTANCE_ID
        or acceptance["content_subject_sha256"] != ACCEPTANCE_CONTENT_SHA256
        or acceptance["reviewed_snapshot"]["reviewed_commit"]
        != "fab56892a5b0c2aa8ac7a889802b9dd5f9697dc7"
    ):
        raise ValueError("delegated M4A acceptance identity differs")
    decision = acceptance["decision"]
    if (
        decision["decision"] != "delegated_authority_accepts_episode_candidates"
        or decision["reviewer_identity"]
        != "chatgpt:political_fingerprint_authority_thread"
        or decision["reviewer_authority"]
        != "delegated_product_methodology_editorial_authority_v1"
        or decision["not_user_signature"] is not True
        or decision["blocking_findings"] != []
        or decision["episode_decision_accounting"]
        != {
            "accepted_episode_candidates": 32,
            "bounded_episode_revision_required": 0,
            "rejected_episode_candidates": 0,
        }
    ):
        raise ValueError("delegated M4A decision differs")
    decisions = decision["episode_decisions"]
    if len(decisions) != 32 or any(
        row["decision"] != "delegated_authority_accepts_episode_candidate"
        for row in decisions
    ):
        raise ValueError("delegated M4A episode decisions differ")

    if not file_digest_matches(CANDIDATE_PATH, CANDIDATE_FILE_SHA256):
        raise ValueError("frozen M4A candidate final-file SHA-256 differs")
    candidates = load(CANDIDATE_PATH)
    verify_seal(candidates, "frozen M4A candidates")
    if (
        candidates["artifact_id"] != CANDIDATE_ID
        or candidates["content_subject_sha256"] != CANDIDATE_CONTENT_SHA256
        or candidates["episode_count"] != 32
        or candidates["single_action_episode_count"] != 30
        or candidates["multi_action_episode_count"] != 2
        or not candidates["frozen"]
    ):
        raise ValueError("frozen M4A candidate identity or accounting differs")
    candidate_by_id = {row["episode_id"]: row for row in candidates["episodes"]}
    decision_by_id = {row["episode_id"]: row for row in decisions}
    if set(candidate_by_id) != set(decision_by_id) or any(
        decision_by_id[episode_id]["episode_content_subject_sha256"]
        != candidate["content_subject_sha256"]
        for episode_id, candidate in candidate_by_id.items()
    ):
        raise ValueError(
            "delegated episode decisions do not bind the frozen candidates"
        )

    if not file_digest_matches(M3BB_PATH, M3BB_FILE_SHA256):
        raise ValueError("M3B-B implementation final-file SHA-256 differs")
    action_implementation = load(M3BB_PATH)
    verify_seal(action_implementation, "M3B-B implementation")
    if (
        action_implementation["artifact_id"] != M3BB_ID
        or action_implementation["content_subject_sha256"] != M3BB_CONTENT_SHA256
        or len(action_implementation["implementation_records"]) != 37
    ):
        raise ValueError("M3B-B implementation identity differs")
    return acceptance, candidates, action_implementation


def implementation_record(
    candidate: dict[str, Any], decision: dict[str, Any]
) -> dict[str, Any]:
    return seal(
        {
            "schema_version": "policy_episode_decision_implementation_record_v1",
            "record_id": f"policy-episode-decision-implementation:{candidate['episode_id']}:v1",
            "episode_id": candidate["episode_id"],
            "candidate_episode_content_subject_sha256": candidate[
                "content_subject_sha256"
            ],
            "delegated_acceptance_artifact_id": ACCEPTANCE_ID,
            "delegated_acceptance_content_subject_sha256": ACCEPTANCE_CONTENT_SHA256,
            "delegated_acceptance_decision": decision["decision"],
            "internal_neutral_label": candidate["internal_neutral_label"],
            "neutral_policy_question": candidate["neutral_policy_question"],
            "issue_id": candidate["issue_id"],
            "congress": candidate["congress"],
            "chamber": candidate["chamber"],
            "primary_action_ids": copy.deepcopy(candidate["primary_action_ids"]),
            "chronological_action_sequence": copy.deepcopy(
                candidate["chronological_action_sequence"]
            ),
            "action_roles": [
                {"action_id": row["action_id"], "action_role": row["action_role"]}
                for row in candidate["chronological_action_sequence"]
            ],
            "exact_action_interpretation_references": copy.deepcopy(
                candidate["source_and_interpretation_references"]
            ),
            "relationship_rationale": candidate["relationship_rationale"],
            "material_policy_continuity": candidate["material_policy_continuity"],
            "material_policy_differences": candidate["material_policy_differences"],
            "implemented_episode_scope": candidate["candidate_episode_scope"],
            "implemented_episode_level_behavior": candidate[
                "candidate_episode_level_behavior"
            ],
            "behavior_derivation": copy.deepcopy(candidate["behavior_derivation"]),
            "confidence": candidate["confidence"],
            "limitations": copy.deepcopy(candidate["limitations"]),
            "competing_plausible_episode_groupings": copy.deepcopy(
                candidate["competing_plausible_episode_groupings"]
            ),
            "unresolved_editorial_questions": copy.deepcopy(
                candidate["unresolved_editorial_questions"]
            ),
            "implementation_state": "implemented_delegated_episode_candidate",
            "candidate_episode_delegated_accepted": True,
            "implementation_accepted": False,
            "canonical": False,
            "public": False,
            "published": False,
            "persisted": False,
            "authorizing": False,
        }
    )


def implementation_bundle(
    acceptance: dict[str, Any],
    candidates: dict[str, Any],
    action_implementation: dict[str, Any],
) -> dict[str, Any]:
    decision_by_id = {
        row["episode_id"]: row for row in acceptance["decision"]["episode_decisions"]
    }
    records = [
        implementation_record(row, decision_by_id[row["episode_id"]])
        for row in candidates["episodes"]
    ]
    record_by_id = {row["episode_id"]: row for row in records}
    action_impl_by_id = {
        row["action_id"]: row for row in action_implementation["implementation_records"]
    }
    accounting = []
    for source in candidates["action_accounting"]:
        episode = record_by_id.get(source["primary_episode_id"])
        accounting.append(
            seal(
                {
                    "schema_version": "policy_episode_action_accounting_implementation_v1",
                    "action_id": source["action_id"],
                    "candidate_accounting_content_subject_sha256": source[
                        "content_subject_sha256"
                    ],
                    "primary_accounting_state": source["primary_accounting_state"],
                    "primary_episode_id": source["primary_episode_id"],
                    "related_episode_ids": copy.deepcopy(
                        source["related_candidate_episode_ids"]
                    ),
                    "action_interpretation_record_content_subject_sha256": action_impl_by_id[
                        source["action_id"]
                    ]["content_subject_sha256"],
                    "implemented_episode_record_id": (
                        episode["record_id"] if episode is not None else None
                    ),
                    "implemented_episode_content_subject_sha256": (
                        episode["content_subject_sha256"]
                        if episode is not None
                        else None
                    ),
                    "counts_toward_episode_behavior": episode is not None,
                }
            )
        )
    counts = dict(
        sorted(Counter(row["primary_accounting_state"] for row in accounting).items())
    )
    return seal(
        {
            "schema_version": "policy_episode_decision_implementation_bundle_v1",
            "artifact_id": IMPLEMENTATION_ID,
            "input_bindings": {
                "delegated_episode_acceptance": {
                    "artifact_id": ACCEPTANCE_ID,
                    "content_subject_sha256": ACCEPTANCE_CONTENT_SHA256,
                    "final_file_sha256": ACCEPTANCE_FILE_SHA256,
                },
                "frozen_episode_candidates": {
                    "artifact_id": CANDIDATE_ID,
                    "content_subject_sha256": CANDIDATE_CONTENT_SHA256,
                    "final_file_sha256": CANDIDATE_FILE_SHA256,
                },
                "action_interpretation_implementation": {
                    "artifact_id": M3BB_ID,
                    "content_subject_sha256": M3BB_CONTENT_SHA256,
                    "final_file_sha256": M3BB_FILE_SHA256,
                },
            },
            "episode_count": len(records),
            "single_action_episode_count": sum(
                len(row["primary_action_ids"]) == 1 for row in records
            ),
            "multi_action_episode_count": sum(
                len(row["primary_action_ids"]) > 1 for row in records
            ),
            "implementation_state_counts": dict(
                sorted(Counter(row["implementation_state"] for row in records).items())
            ),
            "implemented_episodes": records,
            "action_accounting": accounting,
            "action_accounting_counts": counts,
            "delegated_internal_implementation_pending_acceptance": True,
            "accepted": False,
            "accepted_semantic_reference": False,
            "canonical": False,
            "public": False,
            "published": False,
            "persisted": False,
            "authorizing": False,
            "semantic_ir_exists": False,
            "synthesis_eligible": False,
        }
    )


def risk_successor(
    acceptance: dict[str, Any], bundle: dict[str, Any]
) -> dict[str, Any]:
    prior = load(M4A_RISK_PATH)
    verify_seal(prior, "M4A launch-risk register")
    entries = copy.deepcopy(prior["entries"])
    target = entries[-1]
    if (
        target["risk_id"]
        != "launch-risk:episode-grouping:fisa-title-vii-short-term-extension:v1"
    ):
        raise ValueError("M4A episode grouping risk identity differs")
    target.pop("content_subject_sha256")
    target["delegated_authority_disposition"] = (
        "delegated_authority_accepts_retained_ambiguous_assignment"
    )
    target["resolution_history"].append(
        {
            "stage": "M4B",
            "authority": acceptance["decision"]["reviewer_authority"],
            "disposition": "roll_155_outside_primary_membership_with_non_counting_roll_221_relationship_retained_ambiguous",
            "acceptance_content_subject_sha256": ACCEPTANCE_CONTENT_SHA256,
        }
    )
    seal(target)
    return seal(
        {
            "schema_version": "episode_implementation_launch_risk_register_v1",
            "artifact_id": "launch-review-risk-register:f000477:justice_public_safety:119:m4b:v1",
            "prior_register_binding": {
                "artifact_id": prior["artifact_id"],
                "content_subject_sha256": prior["content_subject_sha256"],
                "final_file_sha256": ratified_text_file_digest(M4A_RISK_PATH),
            },
            "implementation_bundle_content_subject_sha256": bundle[
                "content_subject_sha256"
            ],
            "entry_count": len(entries),
            "carried_entry_count": 8,
            "updated_entry_count": 1,
            "entries": entries,
            "compact_launch_risk_packet_eligible_count": len(entries),
            "accepted": False,
            "canonical": False,
            "public": False,
            "authorizing": False,
        }
    )


def calibration_successor(bundle: dict[str, Any]) -> dict[str, Any]:
    prior = load(M4A_CALIBRATION_PATH)
    verify_seal(prior, "M4A episode calibration population")
    by_id = {row["episode_id"]: row for row in bundle["implemented_episodes"]}
    items = []
    for source in prior["eligible_items"]:
        episode = by_id[source["episode_id"]]
        item = {
            key: copy.deepcopy(value)
            for key, value in source.items()
            if key != "content_subject_sha256"
        }
        item["candidate_episode_content_subject_sha256"] = item.pop(
            "episode_content_subject_sha256"
        )
        item["implemented_episode_record_id"] = episode["record_id"]
        item["implemented_episode_content_subject_sha256"] = episode[
            "content_subject_sha256"
        ]
        items.append(seal(item))
    return seal(
        {
            "schema_version": "episode_implementation_calibration_population_v1",
            "artifact_id": "episode-implementation-calibration-eligibility:f000477:justice_public_safety:119:v1",
            "prior_population_binding": {
                "artifact_id": prior["artifact_id"],
                "content_subject_sha256": prior["content_subject_sha256"],
                "final_file_sha256": ratified_text_file_digest(M4A_CALIBRATION_PATH),
            },
            "implementation_bundle_content_subject_sha256": bundle[
                "content_subject_sha256"
            ],
            "eligibility_rule": prior["eligibility_rule"],
            "eligible_count": len(items),
            "eligible_items": items,
            "sample_selected": False,
            "selected_sample": [],
            "sample_selection_deferred_until": prior["sample_selection_deferred_until"],
            "future_seed_inputs": copy.deepcopy(prior["future_seed_inputs"]),
            "accepted": False,
            "canonical": False,
            "public": False,
            "authorizing": False,
        }
    )


def parity_report(
    candidates: dict[str, Any],
    bundle: dict[str, Any],
    risk: dict[str, Any],
    calibration: dict[str, Any],
) -> dict[str, Any]:
    candidate_by_id = {row["episode_id"]: row for row in candidates["episodes"]}
    rows = []
    for implemented in bundle["implemented_episodes"]:
        source = candidate_by_id[implemented["episode_id"]]
        rows.append(
            {
                "episode_id": implemented["episode_id"],
                "candidate_content_subject_sha256": source["content_subject_sha256"],
                "implementation_content_subject_sha256": implemented[
                    "content_subject_sha256"
                ],
                "policy_question_match": True,
                "membership_match": True,
                "chronology_match": True,
                "action_roles_match": True,
                "scope_match": True,
                "behavior_and_derivation_match": True,
                "confidence_match": True,
                "limitations_and_ambiguity_match": True,
            }
        )
    return seal(
        {
            "schema_version": "policy_episode_implementation_parity_report_v1",
            "artifact_id": "policy-episode-implementation-parity:f000477:justice_public_safety:119:v1",
            "candidate_batch_content_subject_sha256": candidates[
                "content_subject_sha256"
            ],
            "implementation_bundle_content_subject_sha256": bundle[
                "content_subject_sha256"
            ],
            "episode_count": len(rows),
            "episode_parity": rows,
            "action_accounting_match": True,
            "risk_successor_entry_count": risk["entry_count"],
            "calibration_successor_eligible_count": calibration["eligible_count"],
            "reviewer_identity": "chatgpt:political_fingerprint_authority_thread",
            "not_user_signature": True,
            "parity_state": "pass",
            "accepted": False,
            "canonical": False,
            "public": False,
            "authorizing": False,
        }
    )


def decision_template(bundle: dict[str, Any]) -> dict[str, Any]:
    return seal(
        {
            "schema_version": "delegated_episode_implementation_decision_template_v1",
            "artifact_id": "delegated-episode-implementation-decisions:f000477:justice_public_safety:119:v1",
            "implementation_bundle": {
                "artifact_id": bundle["artifact_id"],
                "content_subject_sha256": bundle["content_subject_sha256"],
            },
            "decision_state": "awaiting_delegated_implementation_acceptance",
            "allowed_batch_decisions": [
                "delegated_authority_accepts_episode_implementation",
                "bounded_episode_implementation_correction_required",
                "delegated_authority_rejects_episode_implementation",
            ],
            "selected_batch_decision": None,
            "reviewer_identity": None,
            "reviewer_authority": None,
            "not_user_signature": None,
            "decision_timestamp": None,
            "episode_decisions": [
                {
                    "episode_id": row["episode_id"],
                    "implementation_content_subject_sha256": row[
                        "content_subject_sha256"
                    ],
                    "selected_decision": None,
                    "rationale": None,
                }
                for row in bundle["implemented_episodes"]
            ],
            "explicit_non_acceptance": "This empty template does not accept any episode implementation.",
            "accepted": False,
            "canonical": False,
            "public": False,
            "authorizing": False,
        }
    )


def inferred_schema(examples: list[object]) -> dict[str, Any]:
    def node(values: list[object]) -> dict[str, Any]:
        types = sorted(
            {
                "null"
                if value is None
                else "boolean"
                if isinstance(value, bool)
                else "integer"
                if isinstance(value, int)
                else "number"
                if isinstance(value, float)
                else "object"
                if isinstance(value, dict)
                else "array"
                if isinstance(value, list)
                else "string"
                for value in values
            }
        )
        result: dict[str, Any] = {"type": types[0] if len(types) == 1 else types}
        non_null = [value for value in values if value is not None]
        if non_null and all(isinstance(value, dict) for value in non_null):
            keys = sorted({key for value in non_null for key in value})
            result.update(
                {
                    "properties": {
                        key: node([value[key] for value in non_null if key in value])
                        for key in keys
                    },
                    "required": sorted(
                        set.intersection(*(set(value) for value in non_null))
                    ),
                    "additionalProperties": False,
                }
            )
        elif non_null and all(isinstance(value, list) for value in non_null):
            children = [child for value in non_null for child in value]
            result["items"] = node(children) if children else {}
        return result

    schema = node(examples)
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    return schema


def dossier(
    acceptance: dict[str, Any],
    bundle: dict[str, Any],
    risk: dict[str, Any],
    calibration: dict[str, Any],
) -> str:
    lines = [
        "# Foushee Justice Policy-Episode Decision Implementation V1",
        "",
        f"- Implementation bundle: `{bundle['artifact_id']}` / `{bundle['content_subject_sha256']}`",
        f"- Delegated acceptance: `{acceptance['artifact_id']}` / `{acceptance['content_subject_sha256']}` / `{ACCEPTANCE_FILE_SHA256}`",
        f"- Reviewer: `{acceptance['decision']['reviewer_identity']}` / `{acceptance['decision']['reviewer_authority']}` / not user signature `{acceptance['decision']['not_user_signature']}`",
        "- State: delegated candidate decisions implemented internally; implementation acceptance pending",
        "- Canonical, public, persistence, publication, Semantic IR, and synthesis authority: none",
        "",
        "## Accounting",
        "",
        f"- Episodes: `{bundle['episode_count']}`; single-action: `{bundle['single_action_episode_count']}`; multi-action: `{bundle['multi_action_episode_count']}`",
        f"- Action accounting: `{json.dumps(bundle['action_accounting_counts'], sort_keys=True)}`",
        "",
        "## Complete action accounting",
        "",
    ]
    for row in bundle["action_accounting"]:
        lines.append(
            f"- `{row['action_id']}`: `{row['primary_accounting_state']}` / `{row['primary_episode_id']}` / counts `{row['counts_toward_episode_behavior']}` / `{row['content_subject_sha256']}`"
        )
    lines.extend(["", "## Implemented episodes", ""])
    for row in bundle["implemented_episodes"]:
        lines.extend(
            [
                f"### `{row['episode_id']}`",
                "",
                f"- Policy question: {row['neutral_policy_question']}",
                f"- Actions: `{json.dumps(row['primary_action_ids'])}`",
                f"- Roles: `{json.dumps({item['action_id']: item['action_role'] for item in row['action_roles']}, sort_keys=True)}`",
                f"- Scope: {row['implemented_episode_scope']}",
                f"- Behavior: `{row['implemented_episode_level_behavior']}` / `{json.dumps(row['behavior_derivation'], sort_keys=True)}`",
                f"- Continuity: {row['material_policy_continuity']}",
                f"- Differences: {row['material_policy_differences']}",
                f"- Confidence: `{row['confidence']}`",
                f"- Limitations: `{json.dumps(row['limitations'], ensure_ascii=False)}`",
                f"- Competing groupings: `{json.dumps(row['competing_plausible_episode_groupings'], ensure_ascii=False)}`",
                f"- Unresolved questions: `{json.dumps(row['unresolved_editorial_questions'], ensure_ascii=False)}`",
                f"- Candidate digest: `{row['candidate_episode_content_subject_sha256']}`",
                f"- Implementation digest: `{row['content_subject_sha256']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Required boundary cases",
            "",
            "- Laken Riley remains one two-action House/Senate-version episode with the additional later-version offenses preserved.",
            "- HALT Fentanyl remains one three-action amendment/initial-passage/later-version episode with mixed behavior.",
            "- D.C. youth-offender sentencing and juvenile-court transfer remain separate episodes.",
            "- Roll 155 remains outside primary FISA membership and has only a non-counting relationship to roll 221.",
            "- Roll 278 remains no-safe and unassigned and supplies no parent-package meaning.",
            "",
            "## Risk and calibration continuation",
            "",
            f"- Risk entries: `{risk['entry_count']}`; updated: `{risk['updated_entry_count']}`; FISA status remains `retained_ambiguous`.",
            f"- Calibration eligible implementations: `{calibration['eligible_count']}`; sample selected: `{calibration['sample_selected']}`.",
            "",
            "## Delegated implementation decision requested",
            "",
            "- `delegated_authority_accepts_episode_implementation`",
            "- `bounded_episode_implementation_correction_required`",
            "- `delegated_authority_rejects_episode_implementation`",
            "",
        ]
    )
    return "\n".join(lines)


def build(*, check: bool = False) -> dict[str, Any]:
    acceptance, candidates, action_implementation = preflight()
    write_bytes_or_check(ACCEPTANCE_OUTPUT, ACCEPTANCE_SOURCE.read_bytes(), check=check)
    bundle = implementation_bundle(acceptance, candidates, action_implementation)
    risk = risk_successor(acceptance, bundle)
    calibration = calibration_successor(bundle)
    report = parity_report(candidates, bundle, risk, calibration)
    decision = decision_template(bundle)
    values = {
        "episode_implementation_bundle.json": bundle,
        "implementation_parity_report.json": report,
        "launch_review_risk_register.json": risk,
        "episode_calibration_population.json": calibration,
        "delegated_authority_decision_template.json": decision,
    }
    for name, value in values.items():
        write_json_or_check(OUTPUT_ROOT / name, value, check=check)
    schema_inputs = {
        "delegated_episode_candidate_acceptance.json": acceptance,
        **values,
    }
    for name, value in schema_inputs.items():
        schema_name = name.replace(".json", "_v1.schema.json")
        write_json_or_check(
            SCHEMA_ROOT / schema_name, inferred_schema([value]), check=check
        )
    markdown = dossier(acceptance, bundle, risk, calibration).encode("utf-8")
    write_bytes_or_check(
        OUTPUT_ROOT / "implementation_dossier.md", markdown, check=check
    )

    def make_final_byte_parity(paths: list[Path]) -> dict[str, Any]:
        parity_items = []
        for path in paths:
            item: dict[str, Any] = {
                "path": path.relative_to(ROOT).as_posix(),
                "final_file_sha256": file_digest(path),
            }
            if path.suffix == ".json":
                value = load(path)
                if "artifact_id" in value:
                    item["artifact_id"] = value["artifact_id"]
                if "content_subject_sha256" in value:
                    item["content_subject_sha256"] = value["content_subject_sha256"]
            parity_items.append(item)
        return seal(
            {
                "schema_version": "policy_episode_implementation_parity_manifest_v1",
                "artifact_id": "policy-episode-implementation-final-byte-parity:f000477:justice_public_safety:119:v1",
                "implementation_bundle_content_subject_sha256": bundle[
                    "content_subject_sha256"
                ],
                "generated_last": True,
                "referenced_file_count": len(parity_items),
                "referenced_artifacts": parity_items,
                "all_final_file_sha256_recomputed": True,
                "json_markdown_semantic_parity": True,
                "parity_state": "pass",
                "accepted": False,
                "canonical": False,
                "public": False,
                "authorizing": False,
            }
        )

    referenced_paths = [
        ACCEPTANCE_SOURCE,
        ACCEPTANCE_OUTPUT,
        *(OUTPUT_ROOT / name for name in JSON_NAMES),
        OUTPUT_ROOT / "implementation_dossier.md",
        *sorted(SCHEMA_ROOT.glob("*.json")),
    ]
    if not check:
        provisional_parity = make_final_byte_parity(referenced_paths)
        schema = inferred_schema([provisional_parity])
        write_json_or_check(
            SCHEMA_ROOT / "parity_manifest_v1.schema.json", schema, check=False
        )
        referenced_paths = [
            ACCEPTANCE_SOURCE,
            ACCEPTANCE_OUTPUT,
            *(OUTPUT_ROOT / name for name in JSON_NAMES),
            OUTPUT_ROOT / "implementation_dossier.md",
            *sorted(SCHEMA_ROOT.glob("*.json")),
        ]
    parity = make_final_byte_parity(referenced_paths)
    write_json_or_check(OUTPUT_ROOT / "parity_manifest.json", parity, check=check)
    return {
        "status": "pass",
        "bundle_id": bundle["artifact_id"],
        "content_subject_sha256": bundle["content_subject_sha256"],
        "episode_count": bundle["episode_count"],
        "single_action_episode_count": bundle["single_action_episode_count"],
        "multi_action_episode_count": bundle["multi_action_episode_count"],
        "action_accounting": bundle["action_accounting_counts"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(check=args.check), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
