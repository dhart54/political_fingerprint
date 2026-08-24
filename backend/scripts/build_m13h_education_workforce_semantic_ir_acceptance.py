"""Build M13H accepted Education & Workforce Behavioral Semantic IR."""

from __future__ import annotations

import argparse
from collections import Counter
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
from backend.scripts.build_m11h_national_security_semantic_ir_acceptance import (  # noqa: E402
    schema,
    serialized,
    write_or_check,
)


ACCEPTED_M13G_PR = 167
ACCEPTED_M13G_HEAD = "bf436c7687deaf200a33d42637cb42b495140242"
POST_M13G_MERGE_MAIN = "38a1e6faa4d766104009129ee699f8ad323bd078"
REVIEWER_ID = "chatgpt:political_fingerprint_authority_thread"
REVIEWER_AUTHORITY = "full_record_behavioral_semantic_ir_review_authority_v1"
REVIEW_DECISION = "approved_all_behavioral_semantic_ir_candidates_as_written"
DECISION_TIMESTAMP = "2026-08-24T21:04:00Z"

CANDIDATE_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_candidates/f000477_education_workforce_119_v1"
)
CANDIDATE_PATH = CANDIDATE_ROOT / "behavioral_semantic_ir_candidate_graph.json"
TEMPLATE_PATH = CANDIDATE_ROOT / "human_behavioral_semantic_ir_decision_template.json"
CANDIDATE_PARITY_PATH = CANDIDATE_ROOT / "parity_manifest.json"
EPISODE_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_education_workforce_119_v1"
)
EPISODE_AUTHORITY_PATH = EPISODE_ROOT / "human_policy_episode_authority.json"
EPISODE_IMPLEMENTATION_PATH = (
    EPISODE_ROOT / "episode_decision_implementation_bundle.json"
)
ACTION_IMPLEMENTATION_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions/f000477_education_workforce_119_v1/decision_implementation_bundle.json"
)
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_education_workforce_119_v1"
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
M11H_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_national_security_foreign_119_v1"
)

CANDIDATE_ID = "behavioral-semantic-ir-candidates:f000477:education_workforce:119:v1"
CANDIDATE_FILE_SHA256 = (
    "ab5d26c92740ce9e28003ad5bfa38a2bf26277edfd5dcee0db76126cee520373"
)
CANDIDATE_SUBJECT_SHA256 = (
    "99411e738842f0eb15b73c21d600735fc485a56e6248c669a632fcc62c23812c"
)
TEMPLATE_ID = (
    "behavioral-semantic-ir-human-decision-template:f000477:education_workforce:119:v1"
)
TEMPLATE_FILE_SHA256 = (
    "401938203b27ea8dfac9f796fcc8f6dd052cdd57284a5fe7556d10e81e977648"
)
TEMPLATE_SUBJECT_SHA256 = (
    "aa620483b803bc26a0bfe360b6a1648e3165dd1c4238c43763df63be700312f4"
)
CANDIDATE_PARITY_ID = (
    "behavioral-semantic-ir-candidate-parity:f000477:education_workforce:119:v1"
)
CANDIDATE_PARITY_FILE_SHA256 = (
    "e14425d467feab2eb7bab5e85b1393fbad270aacac64c15e94252c3c68cd2a71"
)
CANDIDATE_PARITY_SUBJECT_SHA256 = (
    "efcd31ae040ad88317afd5add6ded4e9e01e5b14c08745f3429a74d1db8092bb"
)
EPISODE_AUTHORITY_FILE_SHA256 = (
    "dd84f769e2a2c7d547972d126f4aa5c5d272bd37a5308fbd2324a9926f91a299"
)
EPISODE_AUTHORITY_SUBJECT_SHA256 = (
    "6381c88b1ee7e7e085e0ac9779616b58b93a5037ed3b19b5af7c56adb113b8a1"
)
EPISODE_IMPLEMENTATION_FILE_SHA256 = (
    "74212c3a768d33bb223bba81fbe92471d2ac698a10538e46d46c7683b3586f6e"
)
EPISODE_IMPLEMENTATION_SUBJECT_SHA256 = (
    "1b11d068af95815952dee6877d8b97e5998539bfc56ddd0820e9b4b061688f3b"
)
ACTION_IMPLEMENTATION_FILE_SHA256 = (
    "074a3bd396a55f6c31b2f7acfacb63455e4b56e1cb2da522b7fa53c62523d656"
)
ACTION_IMPLEMENTATION_SUBJECT_SHA256 = (
    "d66bc98e456a0d3bdfca1326a6766681a98080c53dc781f6cd65a863f133a863"
)

AUTHORITY_ID = (
    "human-behavioral-semantic-ir-authority:f000477:education_workforce:119:v1"
)
IMPLEMENTATION_ID = (
    "behavioral-semantic-ir-decision-implementation:f000477:education_workforce:119:v1"
)
PARITY_ID = (
    "behavioral-semantic-ir-implementation-parity:f000477:education_workforce:119:v1"
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def bindings() -> dict[str, dict[str, Any]]:
    return {
        "candidate_binding": {
            "artifact_id": CANDIDATE_ID,
            "file_sha256": CANDIDATE_FILE_SHA256,
            "candidate_subject_sha256": CANDIDATE_SUBJECT_SHA256,
            "accepted_pr": ACCEPTED_M13G_PR,
            "accepted_head": ACCEPTED_M13G_HEAD,
            "post_merge_main": POST_M13G_MERGE_MAIN,
        },
        "decision_template_binding": {
            "artifact_id": TEMPLATE_ID,
            "file_sha256": TEMPLATE_FILE_SHA256,
            "decision_template_subject_sha256": TEMPLATE_SUBJECT_SHA256,
        },
        "behavioral_semantic_ir_candidate_parity_binding": {
            "artifact_id": CANDIDATE_PARITY_ID,
            "file_sha256": CANDIDATE_PARITY_FILE_SHA256,
            "parity_subject_sha256": CANDIDATE_PARITY_SUBJECT_SHA256,
        },
        "policy_episode_authority_binding": {
            "artifact_id": "human-policy-episode-authority:f000477:education_workforce:119:v1",
            "file_sha256": EPISODE_AUTHORITY_FILE_SHA256,
            "authority_subject_sha256": EPISODE_AUTHORITY_SUBJECT_SHA256,
        },
        "policy_episode_implementation_binding": {
            "artifact_id": "policy-episode-decision-implementation:f000477:education_workforce:119:v1",
            "file_sha256": EPISODE_IMPLEMENTATION_FILE_SHA256,
            "implementation_subject_sha256": EPISODE_IMPLEMENTATION_SUBJECT_SHA256,
        },
        "action_interpretation_implementation_binding": {
            "artifact_id": "action-interpretation-decision-implementation:f000477:education_workforce:119:v1",
            "file_sha256": ACTION_IMPLEMENTATION_FILE_SHA256,
            "implementation_subject_sha256": ACTION_IMPLEMENTATION_SUBJECT_SHA256,
        },
    }


def episode_accounting(ledger: list[dict[str, Any]]) -> dict[str, int]:
    dispositions = Counter(row["disposition"] for row in ledger)
    return {
        "accepted_episode_count": len(ledger),
        "repeated_pattern_evidence_episode_count": dispositions[
            "supports_proposed_repeated_pattern"
        ],
        "trajectory_evidence_episode_count": dispositions[
            "supports_proposed_trajectory"
        ],
        "notable_choice_evidence_episode_count": dispositions[
            "supports_proposed_notable_choice"
        ],
        "contrast_only_episode_count": dispositions["retained_as_limit_or_contrast"],
        "no_safe_proposition_episode_count": dispositions[
            "no_safe_higher_level_behavioral_proposition"
        ],
        "unused_non_directional_evidence_episode_count": dispositions[
            "unused_non_directional_evidence"
        ],
        "primary_overlap_count": 0,
    }


def preflight() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    expected = {
        CANDIDATE_PATH: CANDIDATE_FILE_SHA256,
        TEMPLATE_PATH: TEMPLATE_FILE_SHA256,
        CANDIDATE_PARITY_PATH: CANDIDATE_PARITY_FILE_SHA256,
        EPISODE_AUTHORITY_PATH: EPISODE_AUTHORITY_FILE_SHA256,
        EPISODE_IMPLEMENTATION_PATH: EPISODE_IMPLEMENTATION_FILE_SHA256,
        ACTION_IMPLEMENTATION_PATH: ACTION_IMPLEMENTATION_FILE_SHA256,
    }
    for path, expected_sha in expected.items():
        if canonical_file_sha256(path) != expected_sha:
            raise ValueError(f"accepted input digest differs: {path.relative_to(ROOT)}")
    candidate = load(CANDIDATE_PATH)
    template = load(TEMPLATE_PATH)
    candidate_parity = load(CANDIDATE_PARITY_PATH)
    episode_authority = load(EPISODE_AUTHORITY_PATH)
    episode_implementation = load(EPISODE_IMPLEMENTATION_PATH)
    action_implementation = load(ACTION_IMPLEMENTATION_PATH)
    if not (
        candidate["artifact_id"] == CANDIDATE_ID
        and candidate["candidate_subject_sha256"] == CANDIDATE_SUBJECT_SHA256
        and template["artifact_id"] == TEMPLATE_ID
        and template["decision_template_subject_sha256"] == TEMPLATE_SUBJECT_SHA256
        and candidate_parity["artifact_id"] == CANDIDATE_PARITY_ID
        and candidate_parity["parity_subject_sha256"] == CANDIDATE_PARITY_SUBJECT_SHA256
        and episode_authority["authority_subject_sha256"]
        == EPISODE_AUTHORITY_SUBJECT_SHA256
        and episode_implementation["implementation_subject_sha256"]
        == EPISODE_IMPLEMENTATION_SUBJECT_SHA256
        and action_implementation["implementation_subject_sha256"]
        == ACTION_IMPLEMENTATION_SUBJECT_SHA256
    ):
        raise ValueError("accepted M13D/F/G identity differs")
    return candidate, episode_authority, episode_implementation, action_implementation


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
            "decision": REVIEW_DECISION,
            "decision_timestamp": DECISION_TIMESTAMP,
        },
        **bindings(),
        "proposition_decisions": decisions,
        "decision_accounting": {"accept_candidate_as_written": 2},
        "accepted_proposition_accounting": {
            "total": 2,
            "repeated_pattern": 1,
            "trajectory": 0,
            "notable_choice": 1,
            "primary_conclusion_relevance": 2,
            "limiting_conclusion_relevance": 0,
            "excluded_conclusion_relevance": 0,
        },
        "accepted_episode_disposition_ledger": ledger,
        "accepted_episode_disposition_accounting": episode_accounting(ledger),
        "blocked_actions": [],
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
    episode_authority: dict[str, Any],
    episode_implementation: dict[str, Any],
    action_implementation: dict[str, Any],
) -> dict[str, Any]:
    decisions = {
        row["proposition_id"]: row
        for row in authority["subject"]["proposition_decisions"]
    }
    episodes = {
        row["episode_id"]: row
        for row in episode_implementation["subject"]["implementation_records"]
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
                    "record_id": f"behavioral-semantic-ir-decision-implementation:{proposition['proposition_id']}:m13h:v1",
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
        "accepted_proposition_count": 2,
        "repeated_pattern_count": 1,
        "trajectory_count": 0,
        "notable_choice_count": 1,
        "primary_evidence_episode_count": 3,
        "primary_overlap_count": 0,
        "accepted_episode_count": 16,
        "contrast_only_episode_count": 1,
        "no_safe_proposition_episode_count": 11,
        "unused_non_directional_evidence_episode_count": 1,
        "blocked_action_count": 0,
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
        "blocked_actions": [],
        "canonical_internal_semantic_state": "human_authority_implemented_and_validated",
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
            "mechanical_review_state": "validated_by_independent_repository_validator",
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
        accepted_episode_authority=episode_authority,
        accepted_episode_implementation=episode_implementation,
        accepted_action_interpretation_implementation=action_implementation,
    )
    return implementation


def dossier(authority: dict[str, Any], implementation: dict[str, Any]) -> str:
    return f"""# M13H Education & Workforce Behavioral Semantic IR Acceptance

- Human authority: `{AUTHORITY_ID}`
- Authority subject: `{authority["authority_subject_sha256"]}`
- Deterministic implementation: `{IMPLEMENTATION_ID}`
- Implementation subject: `{implementation["implementation_subject_sha256"]}`
- Decisions: 2 `accept_candidate_as_written`
- Propositions: 1 repeated pattern, 0 trajectories, 1 notable choice
- Episode dispositions: 2 repeated-pattern evidence, 1 notable-choice evidence, 1 contrast-only, 11 no-safe, 1 unused non-directional
- Primary overlaps: 0
- Blocked actions: 0

H.R. 1005 remains non-directional, has no proposition owner, and supplies no
directional evidence. The H.R. 1048 episode preserves support for H.Amdt. 12
and opposition to final passage of the distinct whole package without component
attribution; it is mixed and not a trajectory.

This package establishes canonical internal Behavioral Semantic IR only.
Synthesis acceptance, public wording, publication, persistence, database or
production writes, and deployment remain unauthorized.
"""


def ensure_generic_schemas(*, check: bool) -> None:
    historical_authority = load(
        M11H_ROOT / "human_behavioral_semantic_ir_authority.json"
    )
    historical_implementation = load(
        M11H_ROOT / "behavioral_semantic_ir_decision_implementation.json"
    )
    historical_parity = load(M11H_ROOT / "implementation_parity_manifest.json")
    schemas = {
        AUTHORITY_SCHEMA_PATH: schema(
            historical_authority,
            "https://politicalfingerprint.org/schemas/full_record_behavioral_semantic_ir_authority_v1",
        ),
        IMPLEMENTATION_SCHEMA_PATH: schema(
            historical_implementation,
            "https://politicalfingerprint.org/schemas/full_record_behavioral_semantic_ir_decision_implementation_v1",
        ),
        PARITY_SCHEMA_PATH: schema(
            historical_parity,
            "https://politicalfingerprint.org/schemas/full_record_behavioral_semantic_ir_implementation_parity_v1",
        ),
    }
    for path, value in schemas.items():
        Draft7Validator.check_schema(value)
        write_or_check(path, serialized(value), check=check)


def build(*, check: bool = False) -> dict[str, Any]:
    candidate, episode_authority, episode_implementation, action_implementation = (
        preflight()
    )
    ensure_generic_schemas(check=check)
    authority = build_authority(candidate)
    implementation = build_implementation(
        candidate,
        authority,
        episode_authority,
        episode_implementation,
        action_implementation,
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
    Draft7Validator(load(AUTHORITY_SCHEMA_PATH)).validate(authority)
    Draft7Validator(load(IMPLEMENTATION_SCHEMA_PATH)).validate(implementation)
    Draft7Validator(load(PARITY_SCHEMA_PATH)).validate(parity)
    outputs = {
        AUTHORITY_PATH: serialized(authority),
        IMPLEMENTATION_PATH: serialized(implementation),
        PARITY_PATH: serialized(parity),
        DOSSIER_PATH: dossier(authority, implementation),
    }
    for path, content in outputs.items():
        write_or_check(path, content, check=check)
    return {
        "authority_id": AUTHORITY_ID,
        "authority_file_sha256": canonical_file_sha256(AUTHORITY_PATH),
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_id": IMPLEMENTATION_ID,
        "implementation_file_sha256": canonical_file_sha256(IMPLEMENTATION_PATH),
        "implementation_subject_sha256": implementation[
            "implementation_subject_sha256"
        ],
        "dossier_file_sha256": canonical_file_sha256(DOSSIER_PATH),
        "parity_file_sha256": canonical_file_sha256(PARITY_PATH),
        "parity_subject_sha256": parity["parity_subject_sha256"],
        **implementation["subject"]["final_accounting"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(check=args.check), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
