"""Build M11H human Behavioral Semantic IR authority and implementation."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_behavioral_semantic_ir_decisions import (  # noqa: E402
    DOWNSTREAM_AUTHORIZATIONS,
    digest,
    seal,
    validate_authority,
    validate_implementation,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
)


ACCEPTED_M11G_PR = 139
ACCEPTED_M11G_HEAD = "8ef00da6c0d92662c887874d015024a5b038d66a"
POST_M11G_MERGE_MAIN = "8bd2ec2da7c5da6828c28217cc035c651c7c6f76"
REVIEWER_ID = "dhart54"
REVIEWER_AUTHORITY = "full_record_behavioral_semantic_ir_review_authority_v1"
DECISION_TIMESTAMP = "2026-08-09T22:58:27Z"
BLOCKED_ACTION_ID = "house:119:2:278"

CANDIDATE_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_candidates/f000477_national_security_foreign_119_v1"
)
CANDIDATE_PATH = CANDIDATE_ROOT / "behavioral_semantic_ir_candidate_graph.json"
TEMPLATE_PATH = CANDIDATE_ROOT / "human_behavioral_semantic_ir_decision_template.json"
PARITY_SOURCE_PATH = CANDIDATE_ROOT / "parity_manifest.json"
M11F_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_national_security_foreign_119_v1"
)
M11F_AUTHORITY_PATH = M11F_ROOT / "human_policy_episode_authority.json"
M11F_IMPLEMENTATION_PATH = M11F_ROOT / "episode_decision_implementation_bundle.json"
M11D_IMPLEMENTATION_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions/f000477_national_security_foreign_119_v1/decision_implementation_bundle.json"
)
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_national_security_foreign_119_v1"
)
AUTHORITY_PATH = OUTPUT_ROOT / "human_behavioral_semantic_ir_authority.json"
IMPLEMENTATION_PATH = (
    OUTPUT_ROOT / "behavioral_semantic_ir_decision_implementation.json"
)
PARITY_PATH = OUTPUT_ROOT / "implementation_parity_manifest.json"
DOSSIER_PATH = OUTPUT_ROOT / "implementation_dossier.md"
AUTHORITY_SCHEMA_PATH = (
    ROOT
    / "docs/methodology/full_record_behavioral_semantic_ir_authority_v1.schema.json"
)
IMPLEMENTATION_SCHEMA_PATH = (
    ROOT
    / "docs/methodology/full_record_behavioral_semantic_ir_decision_implementation_v1.schema.json"
)
PARITY_SCHEMA_PATH = (
    ROOT
    / "docs/methodology/full_record_behavioral_semantic_ir_implementation_parity_v1.schema.json"
)

CANDIDATE_ID = (
    "behavioral-semantic-ir-candidates:f000477:national_security_foreign:119:v1"
)
CANDIDATE_FILE_SHA256 = (
    "b0bc182a5ef1bd860b78045696e0ff06919e21c104fa61840ece0d403f8168e7"
)
CANDIDATE_SUBJECT_SHA256 = (
    "6e9a690c3df001c94a8760e06481348589f0db31093ea9a42b841d37c58c0602"
)
TEMPLATE_ID = "behavioral-semantic-ir-human-decision-template:f000477:national_security_foreign:119:v1"
TEMPLATE_FILE_SHA256 = (
    "35d3763bd1d19c6a64c01e95a6759404a6868b46c933b90cfb15e2bdeffbcdb2"
)
TEMPLATE_SUBJECT_SHA256 = (
    "0df01398802c4484b16aa59eba17c57f41b58dd8a21792bc8f408258c042ccc2"
)
M11G_PARITY_ID = (
    "behavioral-semantic-ir-candidate-parity:f000477:national_security_foreign:119:v1"
)
M11G_PARITY_FILE_SHA256 = (
    "f701bd297249f17abf0cf8ec5a64339fadd9a0d53b238e7f57e1b3bca19cb425"
)
M11G_PARITY_SUBJECT_SHA256 = (
    "e7c6f87833e6eaaef73d005af03a947dfbdf286e4e982b4e6fe5dc8f890c799a"
)
M11F_AUTHORITY_ID = (
    "human-policy-episode-authority:f000477:national_security_foreign:119:v1"
)
M11F_AUTHORITY_FILE_SHA256 = (
    "bd3ee15f7cd4508a194df4bb093da673889d460b073af21d7235cf62d9f6f627"
)
M11F_AUTHORITY_SUBJECT_SHA256 = (
    "cc24113a101b68874d6e37869b4de4c8ec72e553687a11bab8d3abe7248a149f"
)
M11F_IMPLEMENTATION_ID = (
    "policy-episode-decision-implementation:f000477:national_security_foreign:119:v1"
)
M11F_IMPLEMENTATION_FILE_SHA256 = (
    "546441f951b1788f248520ee9cfef7f718c6ea8225f98818aa35c17220e60239"
)
M11F_IMPLEMENTATION_SUBJECT_SHA256 = (
    "0d4c9e65ae8e9432103b961a59f2816436cd51a7dae0448ce54b55d5bd94397d"
)
M11D_IMPLEMENTATION_ID = "action-interpretation-decision-implementation:f000477:national_security_foreign:119:v1"
M11D_IMPLEMENTATION_FILE_SHA256 = (
    "402928780286f98fec90242132a829058f57517328c532e60371afab3c2173ff"
)
M11D_IMPLEMENTATION_SUBJECT_SHA256 = (
    "360f0ce47d52cb5a0d0234a88026411e94697c38cac9fca8dc87a7db6ad9ad5b"
)
AUTHORITY_ID = (
    "human-behavioral-semantic-ir-authority:f000477:national_security_foreign:119:v1"
)
IMPLEMENTATION_ID = "behavioral-semantic-ir-decision-implementation:f000477:national_security_foreign:119:v1"
PARITY_ID = "behavioral-semantic-ir-implementation-parity:f000477:national_security_foreign:119:v1"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def serialized(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_or_check(path: Path, content: str, *, check: bool) -> None:
    if check:
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            raise ValueError(f"{path.relative_to(ROOT)} differs from regeneration")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def inferred_schema(value: object) -> dict[str, Any]:
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, list):
        items = merge_schemas([inferred_schema(item) for item in value])
        return {"type": "array", "items": items}
    if isinstance(value, dict):
        return {
            "type": "object",
            "additionalProperties": False,
            "required": sorted(value),
            "properties": {
                key: inferred_schema(child) for key, child in sorted(value.items())
            },
        }
    raise TypeError(type(value))


def merge_schemas(schemas: list[dict[str, Any]]) -> dict[str, Any]:
    unique = {
        json.dumps(item, sort_keys=True, separators=(",", ":")): item
        for item in schemas
    }
    values = list(unique.values())
    if not values:
        return {}
    if len(values) == 1:
        return values[0]
    if all(item.get("type") == "array" for item in values):
        return {
            "type": "array",
            "items": merge_schemas([item.get("items", {}) for item in values]),
        }
    if all(item.get("type") == "object" for item in values):
        required = values[0].get("required")
        property_keys = set(values[0].get("properties", {}))
        if all(
            item.get("required") == required
            and set(item.get("properties", {})) == property_keys
            for item in values
        ):
            return {
                "type": "object",
                "additionalProperties": False,
                "required": required,
                "properties": {
                    key: merge_schemas([item["properties"][key] for item in values])
                    for key in sorted(property_keys)
                },
            }
    return {"anyOf": values}


def schema(value: dict[str, Any], schema_id: str) -> dict[str, Any]:
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": schema_id,
        **inferred_schema(value),
    }


def preflight() -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    expected = {
        CANDIDATE_PATH: CANDIDATE_FILE_SHA256,
        TEMPLATE_PATH: TEMPLATE_FILE_SHA256,
        PARITY_SOURCE_PATH: M11G_PARITY_FILE_SHA256,
        M11F_AUTHORITY_PATH: M11F_AUTHORITY_FILE_SHA256,
        M11F_IMPLEMENTATION_PATH: M11F_IMPLEMENTATION_FILE_SHA256,
        M11D_IMPLEMENTATION_PATH: M11D_IMPLEMENTATION_FILE_SHA256,
    }
    for path, expected_sha in expected.items():
        if canonical_file_sha256(path) != expected_sha:
            raise ValueError(f"accepted input digest differs: {path.relative_to(ROOT)}")
    candidate, template, m11f_authority, m11f_implementation, m11d_implementation = (
        load(CANDIDATE_PATH),
        load(TEMPLATE_PATH),
        load(M11F_AUTHORITY_PATH),
        load(M11F_IMPLEMENTATION_PATH),
        load(M11D_IMPLEMENTATION_PATH),
    )
    if not (
        candidate["artifact_id"] == CANDIDATE_ID
        and candidate["candidate_subject_sha256"] == CANDIDATE_SUBJECT_SHA256
        and template["artifact_id"] == TEMPLATE_ID
        and template["decision_template_subject_sha256"] == TEMPLATE_SUBJECT_SHA256
        and m11f_authority["artifact_id"] == M11F_AUTHORITY_ID
        and m11f_authority["authority_subject_sha256"] == M11F_AUTHORITY_SUBJECT_SHA256
        and m11f_implementation["artifact_id"] == M11F_IMPLEMENTATION_ID
        and m11f_implementation["implementation_subject_sha256"]
        == M11F_IMPLEMENTATION_SUBJECT_SHA256
        and m11d_implementation["artifact_id"] == M11D_IMPLEMENTATION_ID
        and m11d_implementation["implementation_subject_sha256"]
        == M11D_IMPLEMENTATION_SUBJECT_SHA256
    ):
        raise ValueError("accepted M11F/M11G identity differs")
    return candidate, template, m11f_authority, m11f_implementation, m11d_implementation


def bindings() -> dict[str, dict[str, Any]]:
    return {
        "candidate_binding": {
            "artifact_id": CANDIDATE_ID,
            "file_sha256": CANDIDATE_FILE_SHA256,
            "candidate_subject_sha256": CANDIDATE_SUBJECT_SHA256,
            "accepted_pr": ACCEPTED_M11G_PR,
            "accepted_head": ACCEPTED_M11G_HEAD,
            "post_merge_main": POST_M11G_MERGE_MAIN,
        },
        "decision_template_binding": {
            "artifact_id": TEMPLATE_ID,
            "file_sha256": TEMPLATE_FILE_SHA256,
            "decision_template_subject_sha256": TEMPLATE_SUBJECT_SHA256,
        },
        "m11g_parity_binding": {
            "artifact_id": M11G_PARITY_ID,
            "file_sha256": M11G_PARITY_FILE_SHA256,
            "parity_subject_sha256": M11G_PARITY_SUBJECT_SHA256,
        },
        "m11f_authority_binding": {
            "artifact_id": M11F_AUTHORITY_ID,
            "file_sha256": M11F_AUTHORITY_FILE_SHA256,
            "authority_subject_sha256": M11F_AUTHORITY_SUBJECT_SHA256,
        },
        "m11f_implementation_binding": {
            "artifact_id": M11F_IMPLEMENTATION_ID,
            "file_sha256": M11F_IMPLEMENTATION_FILE_SHA256,
            "implementation_subject_sha256": M11F_IMPLEMENTATION_SUBJECT_SHA256,
        },
        "m11d_implementation_binding": {
            "artifact_id": M11D_IMPLEMENTATION_ID,
            "file_sha256": M11D_IMPLEMENTATION_FILE_SHA256,
            "implementation_subject_sha256": M11D_IMPLEMENTATION_SUBJECT_SHA256,
        },
    }


def episode_accounting(ledger: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        key: 0
        for key in [
            "supports_proposed_repeated_pattern",
            "supports_proposed_trajectory",
            "supports_proposed_notable_choice",
            "retained_as_limit_or_contrast",
            "no_safe_higher_level_behavioral_proposition",
        ]
    }
    for row in ledger:
        counts[row["disposition"]] += 1
    return {
        "accepted_episode_count": len(ledger),
        "repeated_pattern_evidence_episode_count": counts[
            "supports_proposed_repeated_pattern"
        ],
        "trajectory_evidence_episode_count": counts["supports_proposed_trajectory"],
        "notable_choice_evidence_episode_count": counts[
            "supports_proposed_notable_choice"
        ],
        "contrast_only_episode_count": counts["retained_as_limit_or_contrast"],
        "no_safe_proposition_episode_count": counts[
            "no_safe_higher_level_behavioral_proposition"
        ],
        "primary_overlap_count": 0,
    }


def build_authority(candidate: dict[str, Any]) -> dict[str, Any]:
    propositions = candidate["compiled_candidate_ir"]["proposition_graph"][
        "propositions"
    ]
    decisions = [
        seal(
            {
                "proposition_id": row["proposition_id"],
                "candidate_proposition_content_sha256": digest(row),
                "candidate_proposition_type": row["proposition_type"],
                "candidate_direction": row["direction"],
                "candidate_conclusion_relevance": row["conclusion_relevance"],
                "decision": "accept_candidate_as_written",
                "bounded_revision": None,
                "reviewer_id": REVIEWER_ID,
                "reviewer_authority": REVIEWER_AUTHORITY,
                "decision_timestamp": DECISION_TIMESTAMP,
            },
            "decision_subject_sha256",
        )
        for row in propositions
    ]
    ledger = deepcopy(candidate["compiled_candidate_ir"]["episode_accounting"])
    subject = {
        "subject": deepcopy(candidate["compiled_candidate_ir"]["subject"]),
        "authority_decision": {
            "reviewer_id": REVIEWER_ID,
            "reviewer_authority": REVIEWER_AUTHORITY,
            "decision": "approve_complete_behavioral_semantic_ir_as_reviewed",
            "decision_timestamp": DECISION_TIMESTAMP,
        },
        **bindings(),
        "proposition_decisions": decisions,
        "decision_accounting": {"accept_candidate_as_written": 15},
        "accepted_proposition_accounting": {
            "total": 15,
            "repeated_pattern": 8,
            "trajectory": 1,
            "notable_choice": 6,
            "primary_conclusion_relevance": 8,
            "limiting_conclusion_relevance": 1,
            "excluded_conclusion_relevance": 6,
        },
        "accepted_episode_disposition_ledger": ledger,
        "accepted_episode_disposition_accounting": episode_accounting(ledger),
        "blocked_actions": [
            {
                "action_id": BLOCKED_ACTION_ID,
                "disposition": "source_blocked_uninterpreted_outside_behavioral_semantic_ir",
            }
        ],
        "authority_effect": "canonical_internal_behavioral_semantic_ir_only",
        "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
    }
    authority = seal(
        {
            "schema_version": "full_record_behavioral_semantic_ir_authority_v1",
            "artifact_id": AUTHORITY_ID,
            "artifact_role": "immutable_human_behavioral_semantic_ir_authority",
            "subject": subject,
            "accepted": True,
            "immutable": True,
            "canonical_internal_behavioral_semantic_ir_authority": True,
            "synthesis_authorized": False,
            "public": False,
            "production_selectable": False,
            "authorizing": True,
        },
        "authority_subject_sha256",
    )
    validate_authority(authority, candidate=candidate)
    return authority


def build_implementation(
    candidate: dict[str, Any],
    authority: dict[str, Any],
    m11f_authority: dict[str, Any],
    m11f_implementation: dict[str, Any],
    m11d_implementation: dict[str, Any],
) -> dict[str, Any]:
    decisions = {
        row["proposition_id"]: row
        for row in authority["subject"]["proposition_decisions"]
    }
    episodes = {
        row["episode_id"]: row
        for row in m11f_implementation["subject"]["implementation_records"]
    }
    records = []
    for proposition in candidate["compiled_candidate_ir"]["proposition_graph"][
        "propositions"
    ]:
        lineage = []
        for episode_id in proposition["evidence_episode_ids"]:
            episode = episodes[episode_id]
            lineage.append(
                {
                    "episode_id": episode_id,
                    "episode_record_id": episode["record_id"],
                    "episode_record_subject_sha256": episode["record_subject_sha256"],
                    "member_direction": episode["member_direction"],
                    "accepted_action_lineage": [
                        {
                            "action_id": action["action_id"],
                            "accepted_interpretation_record_id": action[
                                "accepted_interpretation_record_id"
                            ],
                            "accepted_interpretation_record_subject_sha256": action[
                                "accepted_interpretation_record_subject_sha256"
                            ],
                        }
                        for action in episode["actions"]
                    ],
                }
            )
        records.append(
            seal(
                {
                    "schema_version": "full_record_behavioral_semantic_ir_decision_implementation_record_v1",
                    "record_id": f"behavioral-semantic-ir-decision-implementation:{proposition['proposition_id']}:m11h:v1",
                    "proposition_id": proposition["proposition_id"],
                    "implementation_state": "implemented_human_accepted_as_written",
                    "authority_artifact_id": AUTHORITY_ID,
                    "authority_subject_sha256": authority["authority_subject_sha256"],
                    "authority_decision_subject_sha256": decisions[
                        proposition["proposition_id"]
                    ]["decision_subject_sha256"],
                    "accepted_candidate_content_sha256": digest(proposition),
                    "accepted_candidate_content": deepcopy(proposition),
                    "evidence_lineage": lineage,
                    "canonical_internal_behavioral_semantic_ir": True,
                    "synthesis_authorized": False,
                    "public": False,
                    "production_selectable": False,
                    "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
                },
                "record_subject_sha256",
            )
        )
    ledger = deepcopy(candidate["compiled_candidate_ir"]["episode_accounting"])
    final_accounting = {
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
    subject = {
        "subject": deepcopy(candidate["compiled_candidate_ir"]["subject"]),
        "authority_binding": {
            "artifact_id": AUTHORITY_ID,
            "authority_subject_sha256": authority["authority_subject_sha256"],
        },
        **bindings(),
        "implementation_records": records,
        "accepted_episode_disposition_ledger": ledger,
        "accepted_episode_disposition_accounting": episode_accounting(ledger),
        "final_accounting": final_accounting,
        "blocked_actions": deepcopy(authority["subject"]["blocked_actions"]),
        "canonical_internal_semantic_state": "human_authority_implemented_pending_mechanical_review",
        "synthesis_state": "absent_not_authorized",
        "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
    }
    implementation = seal(
        {
            "schema_version": "full_record_behavioral_semantic_ir_decision_implementation_v1",
            "artifact_id": IMPLEMENTATION_ID,
            "artifact_role": "deterministic_human_behavioral_semantic_ir_decision_implementation",
            "subject": subject,
            "accepted_human_decisions_implemented": True,
            "canonical_internal_behavioral_semantic_ir": True,
            "mechanical_review_state": "pending_human_review",
            "synthesis_authorized": False,
            "public": False,
            "production_selectable": False,
        },
        "implementation_subject_sha256",
    )
    validate_implementation(
        implementation,
        authority=authority,
        candidate=candidate,
        m11f_authority=m11f_authority,
        m11f_implementation=m11f_implementation,
        m11d_implementation=m11d_implementation,
        blocked_action_id=BLOCKED_ACTION_ID,
    )
    return implementation


def dossier(authority: dict[str, Any], implementation: dict[str, Any]) -> str:
    return f"""# M11H Behavioral Semantic IR Acceptance Implementation

- Human authority: `{AUTHORITY_ID}`
- Authority subject: `{authority["authority_subject_sha256"]}`
- Deterministic implementation: `{IMPLEMENTATION_ID}`
- Implementation subject: `{implementation["implementation_subject_sha256"]}`
- Decisions: 15 `accept_candidate_as_written`
- Propositions: 8 repeated patterns, 1 limiting trajectory, 6 excluded notable choices
- Episode dispositions: 24 repeated-pattern evidence, 2 trajectory evidence, 6 notable-choice evidence, 24 contrast-only, 25 no-safe
- Primary overlaps: 0
- Blocked: `{BLOCKED_ACTION_ID}`

This package establishes canonical internal Behavioral Semantic IR only. Synthesis,
public wording, publication, persistence, database writes, production, and
deployment remain unauthorized. It is pending human mechanical review.
"""


def build(*, check: bool = False) -> dict[str, Any]:
    candidate, _template, m11f_authority, m11f_implementation, m11d_implementation = (
        preflight()
    )
    authority = build_authority(candidate)
    implementation = build_implementation(
        candidate,
        authority,
        m11f_authority,
        m11f_implementation,
        m11d_implementation,
    )
    parity = seal(
        {
            "schema_version": "full_record_behavioral_semantic_ir_implementation_parity_v1",
            "artifact_id": PARITY_ID,
            "authority_binding": {
                "artifact_id": AUTHORITY_ID,
                "authority_subject_sha256": authority["authority_subject_sha256"],
            },
            "implementation_binding": {
                "artifact_id": IMPLEMENTATION_ID,
                "implementation_subject_sha256": implementation[
                    "implementation_subject_sha256"
                ],
            },
            "candidate_file_sha256_before": CANDIDATE_FILE_SHA256,
            "candidate_file_sha256_after": canonical_file_sha256(CANDIDATE_PATH),
            "candidate_immutable": canonical_file_sha256(CANDIDATE_PATH)
            == CANDIDATE_FILE_SHA256,
            "proposition_content_parity": True,
            "episode_disposition_parity": True,
            "evidence_lineage_validated": True,
            "blocked_action_excluded": True,
            "downstream_authority_leakage": False,
        },
        "parity_subject_sha256",
    )
    outputs = {
        AUTHORITY_PATH: serialized(authority),
        IMPLEMENTATION_PATH: serialized(implementation),
        PARITY_PATH: serialized(parity),
        DOSSIER_PATH: dossier(authority, implementation),
        AUTHORITY_SCHEMA_PATH: serialized(
            schema(
                authority,
                "https://politicalfingerprint.org/schemas/full_record_behavioral_semantic_ir_authority_v1",
            )
        ),
        IMPLEMENTATION_SCHEMA_PATH: serialized(
            schema(
                implementation,
                "https://politicalfingerprint.org/schemas/full_record_behavioral_semantic_ir_decision_implementation_v1",
            )
        ),
        PARITY_SCHEMA_PATH: serialized(
            schema(
                parity,
                "https://politicalfingerprint.org/schemas/full_record_behavioral_semantic_ir_implementation_parity_v1",
            )
        ),
    }
    for path, content in outputs.items():
        write_or_check(path, content, check=check)
    Draft7Validator.check_schema(json.loads(outputs[AUTHORITY_SCHEMA_PATH]))
    return {
        "authority_id": AUTHORITY_ID,
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_id": IMPLEMENTATION_ID,
        "implementation_subject_sha256": implementation[
            "implementation_subject_sha256"
        ],
        "parity_subject_sha256": parity["parity_subject_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(check=args.check), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
