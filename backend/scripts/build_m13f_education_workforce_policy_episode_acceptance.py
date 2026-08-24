"""Build exact M13F policy-episode authority and deterministic implementation."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_policy_episode_decisions import (  # noqa: E402
    DOWNSTREAM_AUTHORIZATIONS,
    seal,
    validate_authority,
    validate_implementation,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
)


ACCEPTED_M13E_PR = 166
ACCEPTED_M13E_HEAD = "9ec140b7b2c8eec46eb799ba958dbccd46bddea1"
POST_M13E_MERGE_MAIN = "641910bb0c8bb633a76fe95ef113d396d8db881b"
CANDIDATE_ID = "policy-episode-candidates:f000477:education_workforce:119:v1"
CANDIDATE_FILE_SHA256 = (
    "e66476bc01fe770bf9a79cdbcd9aca6461ecaf2958ab3fa04b9a0a2038c61b58"
)
CANDIDATE_SUBJECT_SHA256 = (
    "ea4bca6c4fa1bdef8381952aa4415b6e88292ec228e6950e5099c1a77c566398"
)
DECISION_TEMPLATE_ID = (
    "policy-episode-human-decisions:f000477:education_workforce:119:v1"
)
DECISION_TEMPLATE_FILE_SHA256 = (
    "f3f4ce0a521be16f456b3ee82cd064744c3deec14fb19bf3860ee1281e04e6fa"
)
DECISION_TEMPLATE_SUBJECT_SHA256 = (
    "a3fea9ac957614bd113718f23249f496ef3ae0fb5d153e23b2f418d946015ee5"
)
INTERPRETATION_IMPLEMENTATION_ID = (
    "action-interpretation-decision-implementation:f000477:education_workforce:119:v1"
)
INTERPRETATION_IMPLEMENTATION_FILE_SHA256 = (
    "074a3bd396a55f6c31b2f7acfacb63455e4b56e1cb2da522b7fa53c62523d656"
)
INTERPRETATION_IMPLEMENTATION_SUBJECT_SHA256 = (
    "d66bc98e456a0d3bdfca1326a6766681a98080c53dc781f6cd65a863f133a863"
)
AUTHORITY_ID = "human-policy-episode-authority:f000477:education_workforce:119:v1"
IMPLEMENTATION_ID = (
    "policy-episode-decision-implementation:f000477:education_workforce:119:v1"
)
REVIEWER_ID = "chatgpt:political_fingerprint_authority_thread"
REVIEWER_AUTHORITY = "full_record_policy_episode_review_authority_v1"
DECISION_TIMESTAMP = "2026-08-24T20:05:56Z"

CANDIDATE_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_candidates/f000477_education_workforce_119_v1"
)
CANDIDATE_PATH = CANDIDATE_ROOT / "policy_episode_candidate_batch.json"
DECISION_TEMPLATE_PATH = CANDIDATE_ROOT / "human_episode_decision_template.json"
INTERPRETATION_IMPLEMENTATION_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions/f000477_education_workforce_119_v1/decision_implementation_bundle.json"
)
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_education_workforce_119_v1"
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


def preflight() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    expected = {
        CANDIDATE_PATH: CANDIDATE_FILE_SHA256,
        DECISION_TEMPLATE_PATH: DECISION_TEMPLATE_FILE_SHA256,
        INTERPRETATION_IMPLEMENTATION_PATH: INTERPRETATION_IMPLEMENTATION_FILE_SHA256,
    }
    for path, expected_sha in expected.items():
        if canonical_file_sha256(path) != expected_sha:
            raise ValueError(f"accepted input digest differs: {path.relative_to(ROOT)}")
    candidate = load(CANDIDATE_PATH)
    template = load(DECISION_TEMPLATE_PATH)
    implementation = load(INTERPRETATION_IMPLEMENTATION_PATH)
    if not (
        candidate["artifact_id"] == CANDIDATE_ID
        and candidate["episode_candidate_subject_sha256"] == CANDIDATE_SUBJECT_SHA256
        and template["artifact_id"] == DECISION_TEMPLATE_ID
        and template["decision_template_subject_sha256"]
        == DECISION_TEMPLATE_SUBJECT_SHA256
        and implementation["artifact_id"] == INTERPRETATION_IMPLEMENTATION_ID
        and implementation["implementation_subject_sha256"]
        == INTERPRETATION_IMPLEMENTATION_SUBJECT_SHA256
    ):
        raise ValueError("accepted M13D/M13E identity differs")
    if any(row["selected_decision"] is not None for row in template["decisions"]):
        raise ValueError("M13E decision template is not empty")
    return candidate, template, implementation


def build_authority(
    candidate: dict[str, Any], interpretation: dict[str, Any]
) -> dict[str, Any]:
    decisions = [
        seal(
            {
                "episode_id": episode["episode_id"],
                "candidate_episode_subject_sha256": episode["episode_subject_sha256"],
                "decision": "accept_candidate_as_written",
                "replacement_episode_ids": [],
                "decision_rationale": (
                    "Independent semantic review accepts the H.Amdt. 12 and H.R. "
                    "1048 mixed episode exactly as written, preserving both distinct "
                    "choices and the whole-package/component attribution limitation."
                    if episode["episode_id"] == "hr-1048-amendment-and-final-passage"
                    else "Independent semantic review accepts this bounded singleton "
                    "policy episode exactly as written."
                ),
                "reviewer_id": REVIEWER_ID,
                "reviewer_authority": REVIEWER_AUTHORITY,
                "decision_timestamp": DECISION_TIMESTAMP,
            },
            "decision_subject_sha256",
        )
        for episode in candidate["subject"]["episodes"]
    ]
    subject = {
        "subject": {
            "member_name": candidate["subject"]["member_name"],
            "member_id": candidate["subject"]["member_id"],
            "legislator_id": candidate["subject"]["legislator_id"],
            "issue_id": candidate["subject"]["issue_id"],
            "congress": candidate["subject"]["congress"],
            "chamber": candidate["subject"]["chamber"],
            "official_cutoff": deepcopy(interpretation["subject"]["official_cutoff"]),
        },
        "authority_decision": {
            "reviewer_id": REVIEWER_ID,
            "reviewer_authority": REVIEWER_AUTHORITY,
            "decision": "approved_all_policy_episode_candidates_as_written",
            "decision_timestamp": DECISION_TIMESTAMP,
        },
        "candidate_binding": {
            "artifact_id": CANDIDATE_ID,
            "file_sha256": CANDIDATE_FILE_SHA256,
            "episode_candidate_subject_sha256": CANDIDATE_SUBJECT_SHA256,
            "accepted_pr": ACCEPTED_M13E_PR,
            "accepted_head": ACCEPTED_M13E_HEAD,
            "post_merge_main": POST_M13E_MERGE_MAIN,
        },
        "decision_template_binding": {
            "artifact_id": DECISION_TEMPLATE_ID,
            "file_sha256": DECISION_TEMPLATE_FILE_SHA256,
            "decision_template_subject_sha256": DECISION_TEMPLATE_SUBJECT_SHA256,
        },
        "interpretation_implementation_binding": {
            "artifact_id": INTERPRETATION_IMPLEMENTATION_ID,
            "file_sha256": INTERPRETATION_IMPLEMENTATION_FILE_SHA256,
            "implementation_subject_sha256": INTERPRETATION_IMPLEMENTATION_SUBJECT_SHA256,
        },
        "episode_decisions": decisions,
        "decision_accounting": {"accept_candidate_as_written": len(decisions)},
        "resulting_episode_accounting": {
            "accepted_action_count": 17,
            "accepted_episode_count": 16,
            "single_action_episode_count": 15,
            "multi_action_episode_count": 1,
            "cross_measure_episode_count": 1,
            "ambiguous_or_unassigned_action_count": 0,
            "replacement_singleton_episode_count": 0,
        },
        "blocked_actions": [],
        "authority_effect": "canonical_internal_policy_episode_membership_only",
        "semantic_ir_state": "absent_not_authorized",
        "synthesis_state": "absent_not_authorized",
        "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
    }
    authority = seal(
        {
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
        },
        "authority_subject_sha256",
    )
    episode_ids = {row["episode_id"] for row in candidate["subject"]["episodes"]}
    validate_authority(
        authority,
        candidate=candidate,
        accepted_single_episode_ids=episode_ids,
        rejected_episode_ids=set(),
    )
    return authority


def build_implementation(
    candidate: dict[str, Any],
    authority: dict[str, Any],
    interpretation: dict[str, Any],
) -> dict[str, Any]:
    decisions = {
        row["episode_id"]: row for row in authority["subject"]["episode_decisions"]
    }
    records = []
    for source in sorted(
        candidate["subject"]["episodes"], key=lambda row: row["episode_id"]
    ):
        decision = decisions[source["episode_id"]]
        record = {
            "schema_version": "full_record_policy_episode_decision_implementation_record_v1",
            "record_id": f"policy-episode-decision-implementation:{source['episode_id']}:m13f:v1",
            "episode_id": source["episode_id"],
            "implementation_state": "implemented_human_accepted_as_written",
            "authority_artifact_id": AUTHORITY_ID,
            "authority_subject_sha256": authority["authority_subject_sha256"],
            "authority_decision_subject_sha256": decision["decision_subject_sha256"],
            "source_candidate_episode_id": source["episode_id"],
            "source_candidate_episode_subject_sha256": source["episode_subject_sha256"],
            "policy_proposition": source["policy_proposition"],
            "member_direction": source["member_direction_candidate"],
            "direction_derivation": deepcopy(source["direction_derivation"]),
            "grouping_type": source["grouping_type"],
            "primary_action_ids": deepcopy(source["primary_action_ids"]),
            "actions": deepcopy(source["actions"]),
            "grouping_rationale": source["grouping_rationale"],
            "semantic_grouping_evidence": deepcopy(
                source["semantic_grouping_evidence"]
            ),
            **(
                {
                    "legislative_event_continuity": {
                        "state": "established",
                        "same_legislative_path_or_event": True,
                        "evidence": deepcopy(source["semantic_grouping_evidence"]),
                    }
                }
                if source["grouping_type"] == "cross_measure"
                else {}
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
    by_action = {
        row["action_id"]: row
        for row in interpretation["subject"]["implementation_records"]
    }
    episode_by_action = {
        action_id: row for row in records for action_id in row["primary_action_ids"]
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
                "accepted_interpretation_record_id": by_action[action_id]["record_id"],
                "accepted_interpretation_record_subject_sha256": by_action[action_id][
                    "record_subject_sha256"
                ],
                "primary_membership_count": 1,
            },
            "accounting_subject_sha256",
        )
        for action_id in sorted(by_action)
    ]
    subject = {
        "subject": deepcopy(authority["subject"]["subject"]),
        "authority_binding": {
            "artifact_id": AUTHORITY_ID,
            "authority_subject_sha256": authority["authority_subject_sha256"],
        },
        "interpretation_implementation_binding": deepcopy(
            authority["subject"]["interpretation_implementation_binding"]
        ),
        "policy_episode_candidate_binding": deepcopy(
            authority["subject"]["candidate_binding"]
        ),
        "implementation_records": records,
        "action_accounting": accounting,
        "non_primary_relationship_evidence": [],
        "final_accounting": {
            "accepted_action_count": 17,
            "accepted_episode_count": 16,
            "single_action_episode_count": 15,
            "multi_action_episode_count": 1,
            "cross_measure_episode_count": 1,
            "ambiguous_or_unassigned_action_count": 0,
            "blocked_action_count": 0,
        },
        "blocked_actions": [],
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
        accepted_interpretation_records=list(by_action.values()),
        blocked_action_id=None,
        rejected_episode_ids=set(),
    )
    return bundle


def dossier(authority: dict[str, Any], bundle: dict[str, Any]) -> str:
    counts = Counter(
        row["member_direction"] for row in bundle["subject"]["implementation_records"]
    )
    return "\n".join(
        [
            "# M13F Education & Workforce Policy-Episode Acceptance",
            "",
            "M13F implements the independently accepted M13E semantic decision exactly as written.",
            "",
            "## Mechanical accounting",
            "",
            "- 16 candidate decisions encoded as `accept_candidate_as_written`.",
            "- 17 accepted actions and 16 accepted episodes: 15 singleton and one multi-action cross-identity episode.",
            "- Zero ambiguous, unassigned, blocked, rejected, or replacement episodes.",
            f"- Direction accounting: {dict(sorted(counts.items()))}.",
            "- H.R. 1005 remains a non-directional Not Voting singleton.",
            "- H.Amdt. 12 and H.R. 1048 remain one mixed episode with support for the amendment and opposition to final passage preserved as distinct choices.",
            "- The H.R. 1048 episode retains its whole-package/component attribution limitation.",
            "- The four accepted M13E contrast reviews remain review evidence only and create no episode authority.",
            "",
            "Behavioral Semantic IR acceptance, synthesis, public wording, publication, persistence, database writes, production, and deployment remain unauthorized.",
            "",
        ]
    )


def build(*, check: bool = False) -> dict[str, Any]:
    candidate, _, interpretation = preflight()
    authority = build_authority(candidate, interpretation)
    bundle = build_implementation(candidate, authority, interpretation)
    schemas = {
        AUTHORITY_PATH: load(AUTHORITY_SCHEMA_PATH),
        IMPLEMENTATION_PATH: load(IMPLEMENTATION_SCHEMA_PATH),
    }
    for path, value in {AUTHORITY_PATH: authority, IMPLEMENTATION_PATH: bundle}.items():
        errors = sorted(Draft7Validator(schemas[path]).iter_errors(value), key=str)
        if errors:
            raise ValueError(f"{path.name} schema error: {errors[0].message}")
        write_or_check(path, serialized(value), check=check)
    write_or_check(DOSSIER_PATH, dossier(authority, bundle), check=check)
    references = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "final_file_sha256": canonical_file_sha256(path),
        }
        for path in [
            AUTHORITY_PATH,
            IMPLEMENTATION_PATH,
            DOSSIER_PATH,
            AUTHORITY_SCHEMA_PATH,
            IMPLEMENTATION_SCHEMA_PATH,
        ]
    ]
    parity = seal(
        {
            "schema_version": "full_record_policy_episode_implementation_parity_v1",
            "artifact_id": "policy-episode-implementation-parity:f000477:education_workforce:119:v1",
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
    errors = sorted(
        Draft7Validator(load(PARITY_SCHEMA_PATH)).iter_errors(parity), key=str
    )
    if errors:
        raise ValueError(f"parity schema error: {errors[0].message}")
    write_or_check(PARITY_PATH, serialized(parity), check=check)
    return {
        "authority_id": AUTHORITY_ID,
        "authority_file_sha256": hashlib.sha256(
            serialized(authority).encode()
        ).hexdigest(),
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_id": IMPLEMENTATION_ID,
        "implementation_file_sha256": hashlib.sha256(
            serialized(bundle).encode()
        ).hexdigest(),
        "implementation_subject_sha256": bundle["implementation_subject_sha256"],
        "dossier_file_sha256": canonical_file_sha256(DOSSIER_PATH),
        "parity_file_sha256": hashlib.sha256(serialized(parity).encode()).hexdigest(),
        "parity_subject_sha256": parity["parity_subject_sha256"],
        **bundle["subject"]["final_accounting"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(check=args.check), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
