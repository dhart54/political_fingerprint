"""Independently validate M12H accepted Environment & Energy Semantic IR."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_behavioral_semantic_ir_decisions import (  # noqa: E402
    digest,
    validate_authority,
    validate_implementation,
    verify_seal,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
)
from backend.scripts.build_m12h_environment_energy_semantic_ir_acceptance import (  # noqa: E402
    ACCEPTED_M12G_HEAD,
    ACCEPTED_M12G_PR,
    ACTION_IMPLEMENTATION_PATH,
    AUTHORITY_PATH,
    AUTHORITY_SCHEMA_PATH,
    CANDIDATE_PATH,
    CANDIDATE_SUBJECT_SHA256,
    DOSSIER_PATH,
    EPISODE_AUTHORITY_PATH,
    EPISODE_IMPLEMENTATION_PATH,
    IMPLEMENTATION_PATH,
    IMPLEMENTATION_SCHEMA_PATH,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    POST_M12G_MERGE_MAIN,
    REVIEWER_AUTHORITY,
    REVIEWER_ID,
    TEMPLATE_PATH,
    build,
)


M11H_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_national_security_foreign_119_v1"
)
M11H_HASHES = {
    "human_behavioral_semantic_ir_authority.json": "d1de0f28a09a01ea9b5bbe5607128564daa6aedb929a2be1255cb50f1a99fc93",
    "behavioral_semantic_ir_decision_implementation.json": "13927cade21c85f95c097acf7afe831e55bdb0de79c93e54646e14640d444ecc",
    "implementation_parity_manifest.json": "c797e00d3aa13825361c878e84ed7b3607d5a705d64674ca3a01cada9952a8b9",
    "implementation_dossier.md": "14f5115c7e92c76c5a1dfb1f6959a0fbca30a1dc51a76b0c6d193a39574b5ca4",
}
ACCEPTED_PROPOSITION_IDS = {
    "pattern-california-vehicle-emissions-waiver-disapproval-opposition",
    "pattern-doe-appliance-efficiency-rule-disapproval-opposition",
    "pattern-blm-land-decision-disapproval-opposition",
}
NON_DIRECTIONAL_EPISODE_ID = "single-119-hr-6387-2-136"
WHOLE_PACKAGE_EPISODE_IDS = {
    "single-119-hr-471-1-25",
    "single-119-hr-3898-1-330",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate() -> dict[str, Any]:
    deterministic = build(check=True)
    candidate = load(CANDIDATE_PATH)
    template = load(TEMPLATE_PATH)
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    parity = load(PARITY_PATH)
    episode_authority = load(EPISODE_AUTHORITY_PATH)
    episode_implementation = load(EPISODE_IMPLEMENTATION_PATH)
    action_implementation = load(ACTION_IMPLEMENTATION_PATH)
    current_state = load(ROOT / "docs/editorial/current_state_index.json")

    Draft7Validator(load(AUTHORITY_SCHEMA_PATH)).validate(authority)
    Draft7Validator(load(IMPLEMENTATION_SCHEMA_PATH)).validate(implementation)
    Draft7Validator(load(PARITY_SCHEMA_PATH)).validate(parity)
    decision_counts = validate_authority(authority, candidate=candidate)
    final = validate_implementation(
        implementation,
        authority=authority,
        candidate=candidate,
        accepted_episode_authority=episode_authority,
        accepted_episode_implementation=episode_implementation,
        accepted_action_interpretation_implementation=action_implementation,
    )

    candidate_props = {
        row["proposition_id"]: row
        for row in candidate["compiled_candidate_ir"]["proposition_graph"][
            "propositions"
        ]
    }
    decisions = {
        row["proposition_id"]: row
        for row in authority["subject"]["proposition_decisions"]
    }
    records = {
        row["proposition_id"]: row
        for row in implementation["subject"]["implementation_records"]
    }
    require(
        set(candidate_props)
        == set(decisions)
        == set(records)
        == ACCEPTED_PROPOSITION_IDS,
        "exact accepted proposition set differs",
    )
    require(
        decision_counts == {"accept_candidate_as_written": 3},
        "M12H decision accounting differs",
    )
    for proposition_id, source in candidate_props.items():
        decision = decisions[proposition_id]
        record = records[proposition_id]
        require(
            decision["decision"] == "accept_candidate_as_written"
            and decision["candidate_proposition_content_sha256"] == digest(source)
            and record["accepted_candidate_content"] == source
            and record["accepted_candidate_content_sha256"] == digest(source),
            f"accepted proposition changed: {proposition_id}",
        )
        require(
            source["proposition_type"] == "repeated_pattern"
            and source["direction"] == "opposition",
            f"accepted proposition type or direction differs: {proposition_id}",
        )

    ledger = candidate["compiled_candidate_ir"]["episode_accounting"]
    require(
        authority["subject"]["accepted_episode_disposition_ledger"] == ledger
        and implementation["subject"]["accepted_episode_disposition_ledger"] == ledger,
        "complete 63-episode ledger differs",
    )
    ledger_by_id = {row["episode_id"]: row for row in ledger}
    dispositions = Counter(row["disposition"] for row in ledger)
    require(
        len(ledger) == len(ledger_by_id) == 63
        and dispositions
        == {
            "supports_proposed_repeated_pattern": 13,
            "retained_as_limit_or_contrast": 25,
            "no_safe_higher_level_behavioral_proposition": 24,
            "unused_non_directional_evidence": 1,
        },
        "exact episode disposition accounting differs",
    )
    require(
        ledger_by_id[NON_DIRECTIONAL_EPISODE_ID]
        == {
            "episode_id": NON_DIRECTIONAL_EPISODE_ID,
            "disposition": "unused_non_directional_evidence",
            "primary_proposition_id": None,
            "reason": "Not Voting is resolved but non-directional and cannot support a directional behavioral proposition.",
        },
        "H.R. 6387 non-directional disposition differs",
    )
    evidence_episode_ids = {
        episode_id
        for row in candidate_props.values()
        for episode_id in row["evidence_episode_ids"]
    }
    evidence_action_ids = {
        action_id
        for row in candidate_props.values()
        for action_id in row["evidence_action_ids"]
    }
    require(
        NON_DIRECTIONAL_EPISODE_ID not in evidence_episode_ids
        and "house:119:2:136" not in evidence_action_ids,
        "non-directional evidence entered a directional proposition",
    )
    require(
        not WHOLE_PACKAGE_EPISODE_IDS.intersection(evidence_episode_ids)
        and not {"house:119:1:25", "house:119:1:330"}.intersection(evidence_action_ids),
        "whole-package component evidence was promoted",
    )
    require(
        final
        == {
            "accepted_proposition_count": 3,
            "repeated_pattern_count": 3,
            "trajectory_count": 0,
            "notable_choice_count": 0,
            "primary_evidence_episode_count": 13,
            "primary_overlap_count": 0,
            "accepted_episode_count": 63,
            "contrast_only_episode_count": 25,
            "no_safe_proposition_episode_count": 24,
            "unused_non_directional_evidence_episode_count": 1,
            "blocked_action_count": 0,
        },
        "M12H final accounting differs",
    )
    authority_decision = authority["subject"]["authority_decision"]
    require(
        authority_decision
        == {
            "reviewer_id": REVIEWER_ID,
            "reviewer_authority": REVIEWER_AUTHORITY,
            "decision": "approved_all_behavioral_semantic_ir_candidates_as_written",
            "decision_timestamp": "2026-08-16T02:58:00Z",
        },
        "review authority differs",
    )
    binding = authority["subject"]["candidate_binding"]
    require(
        binding["accepted_pr"] == ACCEPTED_M12G_PR
        and binding["accepted_head"] == ACCEPTED_M12G_HEAD
        and binding["post_merge_main"] == POST_M12G_MERGE_MAIN
        and binding["candidate_subject_sha256"] == CANDIDATE_SUBJECT_SHA256,
        "accepted PR #153 binding differs",
    )
    require(
        template["decision_state"] == "empty_not_authorizing"
        and all(row["decision"] is None for row in template["decisions"])
        and template["authorizing"] is False,
        "accepted M12G decision template was not empty and non-authorizing",
    )
    require(
        not any(authority["subject"]["downstream_authorizations"].values())
        and not any(implementation["subject"]["downstream_authorizations"].values()),
        "downstream authority leakage",
    )
    state = current_state["active_m12h_behavioral_semantic_ir_decision_milestone"]
    require(
        state["post_m12g_merge_main"] == POST_M12G_MERGE_MAIN
        and state["decision_accounting"] == {"accept_candidate_as_written": 3}
        and state["authority_identity"]["sha256"]
        == canonical_file_sha256(AUTHORITY_PATH)
        and state["implementation_identity"]["sha256"]
        == canonical_file_sha256(IMPLEMENTATION_PATH)
        and state["parity_identity"]["sha256"] == canonical_file_sha256(PARITY_PATH)
        and state["unused_non_directional_evidence_episode_count"] == 1
        and state["synthesis_acceptance"] is False
        and not any(state["downstream_authorizations"].values()),
        "M12H current-state identity or authority boundary differs",
    )
    verify_seal(parity, "parity_subject_sha256", "M12H parity")
    require(
        parity["candidate_immutable"] is True
        and parity["proposition_content_parity"] is True
        and parity["episode_disposition_parity"] is True
        and parity["evidence_lineage_validated"] is True
        and parity["downstream_authority_leakage"] is False,
        "M12H parity state differs",
    )
    for name, expected in M11H_HASHES.items():
        require(
            canonical_file_sha256(M11H_ROOT / name) == expected,
            f"historical M11H bytes changed: {name}",
        )
    return {
        "status": "pass",
        "authority_file_sha256": canonical_file_sha256(AUTHORITY_PATH),
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_file_sha256": canonical_file_sha256(IMPLEMENTATION_PATH),
        "implementation_subject_sha256": implementation[
            "implementation_subject_sha256"
        ],
        "dossier_file_sha256": canonical_file_sha256(DOSSIER_PATH),
        "parity_file_sha256": canonical_file_sha256(PARITY_PATH),
        "parity_subject_sha256": parity["parity_subject_sha256"],
        "accepted_proposition_ids": sorted(ACCEPTED_PROPOSITION_IDS),
        "episode_dispositions": dict(sorted(dispositions.items())),
        "historical_m11h_byte_compatibility": "pass",
        "deterministic": deterministic,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
