"""Build M11F human episode authority and deterministic accepted implementation."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_policy_episode_candidates import (  # noqa: E402
    build_candidate_batch,
)
from backend.app.etl.full_record_policy_episode_decisions import (  # noqa: E402
    DOWNSTREAM_AUTHORIZATIONS,
    seal,
    validate_authority,
    validate_implementation,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
)
from backend.scripts.build_m11e_national_security_policy_episode_candidates import (  # noqa: E402
    BATCH_PATH as CANDIDATE_PATH,
    CANDIDATE_PATH as M11C_CANDIDATE_PATH,
    CONTRAST_GROUPS,
    DECISION_PATH as DECISION_TEMPLATE_PATH,
    IMPLEMENTATION_PATH as M11D_IMPLEMENTATION_PATH,
)


ACCEPTED_M11E_PR = 137
ACCEPTED_M11E_HEAD = "1256bb84603305c6f2da037a80d5c167e805a503"
POST_M11E_MERGE_MAIN = "bf2f6f7f9c132c06b614f1d0bf59e50b21817c2a"
CANDIDATE_ID = "policy-episode-candidates:f000477:national_security_foreign:119:v1"
CANDIDATE_FILE_SHA256 = (
    "907fe610aa859ae9ea43f1febd0f0e824bf081ccdeab6193ce4355989871df8b"
)
CANDIDATE_SUBJECT_SHA256 = (
    "3d2d14f2d9a9e76624a97202fbe648b70a3f71d20076ba76e9966f277954d7af"
)
DECISION_TEMPLATE_ID = (
    "policy-episode-human-decision-template:f000477:national_security_foreign:119:v1"
)
DECISION_TEMPLATE_FILE_SHA256 = (
    "bbc01ac460e410c9b7c1cd61964fd8e7d961b39c36b0d7174ef375686e2d8ca6"
)
DECISION_TEMPLATE_SUBJECT_SHA256 = (
    "68d17d415851cf0e16bad5f1d787014004f88f2e5c50f4055b847d6854fec543"
)
M11D_IMPLEMENTATION_ID = "action-interpretation-decision-implementation:f000477:national_security_foreign:119:v1"
M11D_IMPLEMENTATION_FILE_SHA256 = (
    "402928780286f98fec90242132a829058f57517328c532e60371afab3c2173ff"
)
M11D_IMPLEMENTATION_SUBJECT_SHA256 = (
    "360f0ce47d52cb5a0d0234a88026411e94697c38cac9fca8dc87a7db6ad9ad5b"
)
AUTHORITY_ID = "human-policy-episode-authority:f000477:national_security_foreign:119:v1"
IMPLEMENTATION_ID = (
    "policy-episode-decision-implementation:f000477:national_security_foreign:119:v1"
)
REVIEWER_ID = "dhart54"
REVIEWER_AUTHORITY = "full_record_policy_episode_review_authority_v1"
DECISION_TIMESTAMP = "2026-08-09T19:37:33Z"
BLOCKED_ACTION_ID = "house:119:2:278"

REJECTED_EPISODE_IDS = {
    "iran-war-powers-hostilities-removal",
    "lebanon-war-powers-hostilities-removal",
    "venezuela-war-powers-hostilities-removal",
    "fisa-title-vii-extension-attempts",
}

OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_national_security_foreign_119_v1"
)
AUTHORITY_PATH = OUTPUT_ROOT / "human_policy_episode_authority.json"
IMPLEMENTATION_PATH = OUTPUT_ROOT / "episode_decision_implementation_bundle.json"
DOSSIER_PATH = OUTPUT_ROOT / "implementation_dossier.md"
PARITY_PATH = OUTPUT_ROOT / "implementation_parity_manifest.json"
AUTHORITY_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_policy_episode_authority_v1.schema.json"
)
IMPLEMENTATION_SCHEMA_PATH = (
    ROOT
    / "docs/methodology/full_record_policy_episode_decision_implementation_v1.schema.json"
)
PARITY_SCHEMA_PATH = (
    ROOT
    / "docs/methodology/full_record_policy_episode_implementation_parity_v1.schema.json"
)


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
        return {"type": "array", "items": inferred_schema(value[0]) if value else {}}
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


def schema(value: dict[str, Any], schema_id: str) -> dict[str, Any]:
    result = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": schema_id,
        **inferred_schema(value),
    }

    def relax_dynamic_maps(node: object) -> None:
        if not isinstance(node, dict):
            return
        properties = node.get("properties")
        if isinstance(properties, dict):
            effects = properties.get("accepted_position_effects_by_action")
            if isinstance(effects, dict):
                effects["additionalProperties"] = {"type": "string"}
                effects["required"] = []
                effects["properties"] = {}
        for child in node.values():
            if isinstance(child, dict):
                relax_dynamic_maps(child)

    relax_dynamic_maps(result)
    return result


def preflight() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    expected = {
        CANDIDATE_PATH: CANDIDATE_FILE_SHA256,
        DECISION_TEMPLATE_PATH: DECISION_TEMPLATE_FILE_SHA256,
        M11D_IMPLEMENTATION_PATH: M11D_IMPLEMENTATION_FILE_SHA256,
    }
    for path, expected_sha in expected.items():
        if canonical_file_sha256(path) != expected_sha:
            raise ValueError(f"accepted input digest differs: {path.relative_to(ROOT)}")
    candidate = load(CANDIDATE_PATH)
    template = load(DECISION_TEMPLATE_PATH)
    m11d = load(M11D_IMPLEMENTATION_PATH)
    m11c = load(M11C_CANDIDATE_PATH)
    if not (
        candidate["artifact_id"] == CANDIDATE_ID
        and candidate["episode_candidate_subject_sha256"] == CANDIDATE_SUBJECT_SHA256
        and template["artifact_id"] == DECISION_TEMPLATE_ID
        and template["decision_template_subject_sha256"]
        == DECISION_TEMPLATE_SUBJECT_SHA256
        and m11d["artifact_id"] == M11D_IMPLEMENTATION_ID
        and m11d["implementation_subject_sha256"] == M11D_IMPLEMENTATION_SUBJECT_SHA256
    ):
        raise ValueError("accepted M11D/M11E identity differs")
    return candidate, template, m11d, m11c


def all_singletons(m11d: dict[str, Any], m11c: dict[str, Any]) -> dict[str, Any]:
    return build_candidate_batch(
        artifact_id="internal-m11f-all-singleton-reconstruction",
        subject={
            "member_name": "Valerie Foushee",
            "member_id": "F000477",
            "legislator_id": "leg_valerie_p_foushee",
            "issue_id": "NATIONAL_SECURITY_FOREIGN",
            "congress": 119,
            "chamber": "house",
            "official_cutoff": "2026-07-23",
        },
        input_bindings={
            "purpose": "deterministic_m11e_singleton_naming_reconstruction"
        },
        implementation=m11d,
        candidate_artifact=m11c,
        multi_action_definitions=[],
        contrast_groups=CONTRAST_GROUPS,
        blocked_action={
            "action_id": BLOCKED_ACTION_ID,
            "state": "source_blocked_uninterpreted_unavailable_for_episode_construction",
            "primary_episode_id": None,
        },
    )


def build_authority(
    candidate: dict[str, Any], singleton_batch: dict[str, Any]
) -> dict[str, Any]:
    singleton_by_action = {
        row["primary_action_ids"][0]: row
        for row in singleton_batch["subject"]["episodes"]
    }
    accepted_single_ids = {
        row["episode_id"]
        for row in candidate["subject"]["episodes"]
        if row["episode_id"] not in REJECTED_EPISODE_IDS
    }
    decisions = []
    for episode in candidate["subject"]["episodes"]:
        rejected = episode["episode_id"] in REJECTED_EPISODE_IDS
        replacements = (
            [
                singleton_by_action[action_id]["episode_id"]
                for action_id in episode["primary_action_ids"]
            ]
            if rejected
            else []
        )
        decisions.append(
            seal(
                {
                    "episode_id": episode["episode_id"],
                    "candidate_episode_subject_sha256": episode[
                        "episode_subject_sha256"
                    ],
                    "decision": "reject_and_reassign_actions"
                    if rejected
                    else "accept_candidate_as_written",
                    "replacement_episode_ids": replacements,
                    "decision_rationale": (
                        "The repeated measures share a proposition but do not establish genuine legislative-path or event continuity; preserve each House event as a distinct singleton episode."
                        if rejected
                        else "Human review accepts the bounded singleton candidate as written."
                    ),
                    "reviewer_id": REVIEWER_ID,
                    "reviewer_authority": REVIEWER_AUTHORITY,
                    "decision_timestamp": DECISION_TIMESTAMP,
                },
                "decision_subject_sha256",
            )
        )
    subject = {
        "subject": {
            "member_name": "Valerie Foushee",
            "member_id": "F000477",
            "legislator_id": "leg_valerie_p_foushee",
            "issue_id": "NATIONAL_SECURITY_FOREIGN",
            "congress": 119,
            "chamber": "house",
            "official_cutoff": {
                "end_date": "2026-07-23",
                "latest_action_id": "house:119:2:283",
            },
        },
        "authority_decision": {
            "reviewer_id": REVIEWER_ID,
            "reviewer_authority": REVIEWER_AUTHORITY,
            "decision": "approve_policy_episodes_with_rejected_group_reassignments",
            "decision_timestamp": DECISION_TIMESTAMP,
        },
        "candidate_binding": {
            "artifact_id": CANDIDATE_ID,
            "file_sha256": CANDIDATE_FILE_SHA256,
            "episode_candidate_subject_sha256": CANDIDATE_SUBJECT_SHA256,
            "accepted_pr": ACCEPTED_M11E_PR,
            "accepted_head": ACCEPTED_M11E_HEAD,
            "post_merge_main": POST_M11E_MERGE_MAIN,
        },
        "decision_template_binding": {
            "artifact_id": DECISION_TEMPLATE_ID,
            "file_sha256": DECISION_TEMPLATE_FILE_SHA256,
            "decision_template_subject_sha256": DECISION_TEMPLATE_SUBJECT_SHA256,
        },
        "m11d_implementation_binding": {
            "artifact_id": M11D_IMPLEMENTATION_ID,
            "file_sha256": M11D_IMPLEMENTATION_FILE_SHA256,
            "implementation_subject_sha256": M11D_IMPLEMENTATION_SUBJECT_SHA256,
        },
        "episode_decisions": decisions,
        "decision_accounting": {
            "accept_candidate_as_written": 70,
            "reject_and_reassign_actions": 4,
        },
        "resulting_episode_accounting": {
            "accepted_action_count": 81,
            "accepted_episode_count": 81,
            "single_action_episode_count": 81,
            "multi_action_episode_count": 0,
            "cross_measure_episode_count": 0,
            "ambiguous_or_unassigned_action_count": 0,
            "replacement_singleton_episode_count": 11,
        },
        "blocked_actions": [
            {
                "action_id": BLOCKED_ACTION_ID,
                "disposition": "source_blocked_uninterpreted_outside_episode_acceptance",
            }
        ],
        "authority_effect": "canonical_internal_policy_episode_membership_only",
        "semantic_ir_state": "absent_not_authorized",
        "synthesis_state": "absent_not_authorized",
        "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
    }
    authority = {
        "schema_version": "full_record_policy_episode_authority_v1",
        "artifact_id": AUTHORITY_ID,
        "artifact_role": "immutable_human_policy_episode_authority",
        "subject": subject,
        "accepted": True,
        "immutable": True,
        "canonical_internal_episode_authority": True,
        "canonical_semantic_acceptance": False,
        "public": False,
        "production_selectable": False,
        "authorizing": True,
    }
    authority = seal(authority, "authority_subject_sha256")
    validate_authority(
        authority,
        candidate=candidate,
        accepted_single_episode_ids=accepted_single_ids,
        rejected_episode_ids=REJECTED_EPISODE_IDS,
    )
    return authority


def build_implementation(
    candidate: dict[str, Any],
    singleton_batch: dict[str, Any],
    authority: dict[str, Any],
    m11d: dict[str, Any],
) -> dict[str, Any]:
    original = {row["episode_id"]: row for row in candidate["subject"]["episodes"]}
    singleton_by_action = {
        row["primary_action_ids"][0]: row
        for row in singleton_batch["subject"]["episodes"]
    }
    decision_by_id = {
        row["episode_id"]: row for row in authority["subject"]["episode_decisions"]
    }
    accepted_rows = [
        row
        for row in original.values()
        if row["episode_id"] not in REJECTED_EPISODE_IDS
    ]
    replacement_actions = sorted(
        action_id
        for episode_id in REJECTED_EPISODE_IDS
        for action_id in original[episode_id]["primary_action_ids"]
    )
    sources = accepted_rows + [
        singleton_by_action[action_id] for action_id in replacement_actions
    ]
    replacement_parent = {
        action_id: episode_id
        for episode_id in REJECTED_EPISODE_IDS
        for action_id in original[episode_id]["primary_action_ids"]
    }
    records = []
    for source in sorted(sources, key=lambda row: row["episode_id"]):
        action_id = source["primary_action_ids"][0]
        parent_id = replacement_parent.get(action_id)
        decision = decision_by_id[parent_id or source["episode_id"]]
        record = {
            "schema_version": "full_record_policy_episode_decision_implementation_record_v1",
            "record_id": f"policy-episode-decision-implementation:{source['episode_id']}:m11f:v1",
            "episode_id": source["episode_id"],
            "implementation_state": "implemented_human_accepted_singleton_reassignment"
            if parent_id
            else "implemented_human_accepted_as_written",
            "authority_artifact_id": AUTHORITY_ID,
            "authority_subject_sha256": authority["authority_subject_sha256"],
            "authority_decision_subject_sha256": decision["decision_subject_sha256"],
            "source_candidate_episode_id": parent_id or source["episode_id"],
            "source_candidate_episode_subject_sha256": original[
                parent_id or source["episode_id"]
            ]["episode_subject_sha256"],
            "policy_proposition": source["policy_proposition"],
            "member_direction": source["member_direction_candidate"],
            "direction_derivation": deepcopy(source["direction_derivation"]),
            "grouping_type": "single_action",
            "primary_action_ids": deepcopy(source["primary_action_ids"]),
            "actions": deepcopy(source["actions"]),
            "grouping_rationale": source["grouping_rationale"],
            "semantic_grouping_evidence": deepcopy(
                source["semantic_grouping_evidence"]
            ),
            "relevant_contrast_ids": deepcopy(source["relevant_contrast_ids"]),
            "material_policy_differences": source["material_policy_differences"],
            "material_limitations": deepcopy(source["material_limitations"]),
            "confidence": source["confidence"],
            "canonical_internal_policy_episode": True,
            "canonical_semantic_acceptance": False,
            "public": False,
            "publication_authorized": False,
            "production_selectable": False,
            "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
        }
        records.append(seal(record, "record_subject_sha256"))
    episode_by_action = {row["primary_action_ids"][0]: row for row in records}
    m11d_by_action = {
        row["action_id"]: row for row in m11d["subject"]["implementation_records"]
    }
    accounting = [
        seal(
            {
                "action_id": action_id,
                "primary_episode_id": episode_by_action[action_id]["episode_id"],
                "implementation_record_id": episode_by_action[action_id]["record_id"],
                "implementation_record_subject_sha256": episode_by_action[action_id][
                    "record_subject_sha256"
                ],
                "accepted_interpretation_record_id": m11d_by_action[action_id][
                    "record_id"
                ],
                "accepted_interpretation_record_subject_sha256": m11d_by_action[
                    action_id
                ]["record_subject_sha256"],
                "primary_membership_count": 1,
            },
            "accounting_subject_sha256",
        )
        for action_id in sorted(m11d_by_action)
    ]
    relationships = []
    for episode_id in sorted(REJECTED_EPISODE_IDS):
        source = original[episode_id]
        relationships.append(
            seal(
                {
                    "relationship_id": episode_id,
                    "relationship_type": "repeated_policy_proposition_without_legislative_event_continuity",
                    "action_ids": deepcopy(source["primary_action_ids"]),
                    "replacement_primary_episode_ids": [
                        episode_by_action[action_id]["episode_id"]
                        for action_id in source["primary_action_ids"]
                    ],
                    "shared_policy_proposition": source["policy_proposition"],
                    "preserved_rationale": source["grouping_rationale"],
                    "disposition": "rejected_as_primary_grouping_preserved_as_non_authorizing_relationship_evidence",
                    "primary_authority_effect": False,
                    "may_inform_later_pattern_review": True,
                    "semantic_ir_authority": False,
                    "synthesis_authority": False,
                },
                "relationship_subject_sha256",
            )
        )
    subject = {
        "subject": deepcopy(authority["subject"]["subject"]),
        "authority_binding": {
            "artifact_id": AUTHORITY_ID,
            "authority_subject_sha256": authority["authority_subject_sha256"],
        },
        "m11d_implementation_binding": deepcopy(
            authority["subject"]["m11d_implementation_binding"]
        ),
        "m11e_candidate_binding": deepcopy(authority["subject"]["candidate_binding"]),
        "implementation_records": records,
        "action_accounting": accounting,
        "non_primary_relationship_evidence": relationships,
        "final_accounting": {
            "accepted_action_count": 81,
            "accepted_episode_count": 81,
            "single_action_episode_count": 81,
            "multi_action_episode_count": 0,
            "cross_measure_episode_count": 0,
            "ambiguous_or_unassigned_action_count": 0,
            "blocked_action_count": 1,
        },
        "blocked_actions": deepcopy(authority["subject"]["blocked_actions"]),
        "internal_episode_state": "human_accepted_canonical_internal_organization",
        "semantic_ir_state": "absent_not_authorized",
        "synthesis_state": "absent_not_authorized",
        "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
    }
    bundle = seal(
        {
            "schema_version": "full_record_policy_episode_decision_implementation_v1",
            "artifact_id": IMPLEMENTATION_ID,
            "artifact_role": "deterministic_human_policy_episode_decision_implementation",
            "subject": subject,
            "accepted_human_decisions_implemented": True,
            "canonical_internal_policy_episodes": True,
            "canonical_semantic_acceptance": False,
            "public": False,
            "publication_authorized": False,
            "production_selectable": False,
        },
        "implementation_subject_sha256",
    )
    validate_implementation(
        bundle,
        authority=authority,
        m11d_records=m11d["subject"]["implementation_records"],
        blocked_action_id=BLOCKED_ACTION_ID,
        rejected_episode_ids=REJECTED_EPISODE_IDS,
    )
    return bundle


def dossier(authority: dict[str, Any], bundle: dict[str, Any]) -> str:
    lines = [
        "# M11F National Security Policy-Episode Acceptance Review",
        "",
        "M11F implements the human M11E episode decision as canonical internal episode organization only.",
        "",
        "## Mechanical accounting",
        "",
        "- M11E decisions encoded: 74 (70 accepted as written; four rejected and reassigned).",
        "- Accepted M11D actions: 81.",
        "- Accepted primary episodes: 81, all singleton.",
        "- Multi-action or cross-measure primary episodes: 0.",
        "- Ambiguous or unassigned actions: 0.",
        "- H.R. 8800 (`house:119:2:278`) remains source-blocked and outside episode acceptance.",
        "",
        "## Rejected primary groupings and replacements",
        "",
    ]
    for relationship in bundle["subject"]["non_primary_relationship_evidence"]:
        lines.extend(
            [
                f"- `{relationship['relationship_id']}`: rejected as a primary episode; `{len(relationship['action_ids'])}` actions became `{len(relationship['replacement_primary_episode_ids'])}` singleton episodes.",
                f"  Replacements: `{', '.join(relationship['replacement_primary_episode_ids'])}`.",
            ]
        )
    lines.extend(
        [
            "",
            "The rejected groupings remain non-primary relationship evidence with zero authority over episode accounting. Shared proposition alone is insufficient; future cross-measure primary grouping requires explicit legislative-path or event continuity.",
            "",
            "Semantic IR, synthesis, public wording, publication, persistence, database writes, production, and deployment remain unauthorized. Stop for human mechanical review.",
            "",
        ]
    )
    return "\n".join(lines)


def build(*, check: bool = False) -> dict[str, Any]:
    candidate, _, m11d, m11c = preflight()
    singleton_batch = all_singletons(m11d, m11c)
    authority = build_authority(candidate, singleton_batch)
    bundle = build_implementation(candidate, singleton_batch, authority, m11d)
    artifacts = {
        AUTHORITY_PATH: authority,
        IMPLEMENTATION_PATH: bundle,
    }
    schemas = {
        AUTHORITY_SCHEMA_PATH: schema(
            authority,
            "https://politicalfingerprint.example/schemas/full_record_policy_episode_authority_v1",
        ),
        IMPLEMENTATION_SCHEMA_PATH: schema(
            bundle,
            "https://politicalfingerprint.example/schemas/full_record_policy_episode_decision_implementation_v1",
        ),
    }
    for path, value in {**artifacts, **schemas}.items():
        Draft7Validator.check_schema(
            value
            if path in schemas
            else schemas[
                AUTHORITY_SCHEMA_PATH
                if path == AUTHORITY_PATH
                else IMPLEMENTATION_SCHEMA_PATH
            ]
        )
        write_or_check(path, serialized(value), check=check)
    write_or_check(DOSSIER_PATH, dossier(authority, bundle), check=check)
    references = []
    for path in [
        AUTHORITY_PATH,
        IMPLEMENTATION_PATH,
        DOSSIER_PATH,
        AUTHORITY_SCHEMA_PATH,
        IMPLEMENTATION_SCHEMA_PATH,
    ]:
        references.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "final_file_sha256": canonical_file_sha256(path),
            }
        )
    parity = seal(
        {
            "schema_version": "full_record_policy_episode_implementation_parity_v1",
            "artifact_id": "policy-episode-implementation-parity:f000477:national_security_foreign:119:v1",
            "authority_subject_sha256": authority["authority_subject_sha256"],
            "implementation_subject_sha256": bundle["implementation_subject_sha256"],
            "referenced_artifacts": references,
            "parity_state": "pass",
            "generated_last": True,
            "public": False,
            "authorizing": False,
        },
        "parity_subject_sha256",
    )
    parity_schema = schema(
        parity,
        "https://politicalfingerprint.example/schemas/full_record_policy_episode_implementation_parity_v1",
    )
    Draft7Validator.check_schema(parity_schema)
    write_or_check(PARITY_SCHEMA_PATH, serialized(parity_schema), check=check)
    write_or_check(PARITY_PATH, serialized(parity), check=check)
    return {
        "authority_id": AUTHORITY_ID,
        "authority_file_sha256": hashlib.sha256(
            serialized(authority).encode("utf-8")
        ).hexdigest(),
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_id": IMPLEMENTATION_ID,
        "implementation_file_sha256": hashlib.sha256(
            serialized(bundle).encode("utf-8")
        ).hexdigest(),
        "implementation_subject_sha256": bundle["implementation_subject_sha256"],
        "parity_file_sha256": hashlib.sha256(
            serialized(parity).encode("utf-8")
        ).hexdigest(),
        "parity_subject_sha256": parity["parity_subject_sha256"],
        **bundle["subject"]["final_accounting"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(check=args.check), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
