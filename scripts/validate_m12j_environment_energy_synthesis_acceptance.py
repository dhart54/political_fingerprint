"""Independently validate exact M12J synthesis acceptance."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_source_readiness import canonical_file_sha256  # noqa: E402
from backend.app.etl.full_record_synthesis_decisions import (  # noqa: E402
    digest,
    validate_authority,
    validate_implementation,
    verify_seal,
)
from backend.scripts.build_m12j_environment_energy_synthesis_acceptance import (  # noqa: E402
    ACCEPTED_M12I_HEAD,
    ACCEPTED_M12I_PR,
    AUTHORITY_PATH,
    AUTHORITY_SCHEMA_PATH,
    CANDIDATE_ID,
    DOSSIER_PATH,
    IMPLEMENTATION_PATH,
    IMPLEMENTATION_SCHEMA_PATH,
    M12H_AUTHORITY_PATH,
    M12H_IMPLEMENTATION_PATH,
    PACKAGE_FILE_SHA256,
    PACKAGE_PATH,
    PACKAGE_SUBJECT_SHA256,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    POST_M12I_MERGE_MAIN,
    REVIEWED_BASE,
    REVIEWER_AUTHORITY,
    REVIEWER_ID,
    TEMPLATE_FILE_SHA256,
    TEMPLATE_PATH,
    TEMPLATE_SUBJECT_SHA256,
    build,
)


AUTHORITY_FILE_SHA256 = (
    "edf92b4543376b94ccebbc87d3ec85ea734d0ab7a38952848062bfe7cc78be5c"
)
AUTHORITY_SUBJECT_SHA256 = (
    "060386625bebf6095bd91e20c7a63578b170cd94ced89a0d58996adbf606a187"
)
IMPLEMENTATION_FILE_SHA256 = (
    "74f573f40e8f26eadb6b126a0d0ecaa0b6abb5ca5ac539dd8c4a80d8851692cd"
)
IMPLEMENTATION_SUBJECT_SHA256 = (
    "bd7a786523fb2e969f44c1374edc96ea59d0885a4d83ceafb5ff14d9cb135a72"
)
PARITY_FILE_SHA256 = "4217db5b09a0c07031154fa8dc090c9d7640e37b98035aa82abfb1e919824f4b"
PARITY_SUBJECT_SHA256 = (
    "7be6d35570088bbaaa377be09a03112e186238c63962aab8cab0c88e55661dae"
)
DOSSIER_FILE_SHA256 = "4f6a5fc694bd164308fc96816916959bf7f80acfe5d3c3b1adb6f438c34089cc"
PROPOSITION_IDS = {
    "pattern-california-vehicle-emissions-waiver-disapproval-opposition",
    "pattern-doe-appliance-efficiency-rule-disapproval-opposition",
    "pattern-blm-land-decision-disapproval-opposition",
}
M11J_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/synthesis_implementations/f000477_national_security_foreign_119_v1"
)
M11J_HASHES = {
    "human_synthesis_authority.json": "4fd4f7b1490415df3c1f10cc088fcc95d9f48f3eec3504b9312cb447b8e0a1cc",
    "synthesis_decision_implementation.json": "bd2a08caa9100cf3b5326cb739f0ce99db2f6c4650667df8087dc254d1509500",
    "implementation_parity_manifest.json": "0405ef569cff277e861f1453707d22427b9191c2d3bad5033d4704625190211e",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate() -> dict[str, Any]:
    deterministic = build(check=True)
    package = load(PACKAGE_PATH)
    template = load(TEMPLATE_PATH)
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    parity = load(PARITY_PATH)
    behavioral_authority = load(M12H_AUTHORITY_PATH)
    behavioral_implementation = load(M12H_IMPLEMENTATION_PATH)
    Draft7Validator(load(AUTHORITY_SCHEMA_PATH)).validate(authority)
    Draft7Validator(load(IMPLEMENTATION_SCHEMA_PATH)).validate(implementation)
    Draft7Validator(load(PARITY_SCHEMA_PATH)).validate(parity)
    decision_accounting = validate_authority(
        authority, package=package, decision_template=template
    )
    final = validate_implementation(
        implementation,
        authority=authority,
        package=package,
        decision_template=template,
        accepted_behavioral_semantic_ir_authority=behavioral_authority,
        accepted_behavioral_semantic_ir_implementation=behavioral_implementation,
    )
    require(
        canonical_file_sha256(PACKAGE_PATH) == PACKAGE_FILE_SHA256
        and package["synthesis_candidate_package_subject_sha256"]
        == PACKAGE_SUBJECT_SHA256
        and canonical_file_sha256(TEMPLATE_PATH) == TEMPLATE_FILE_SHA256
        and template["decision_template_subject_sha256"] == TEMPLATE_SUBJECT_SHA256,
        "accepted M12I package or template identity differs",
    )
    binding = authority["subject"]["candidate_binding"]
    require(
        binding["accepted_pr"] == ACCEPTED_M12I_PR
        and binding["accepted_head"] == ACCEPTED_M12I_HEAD
        and binding["reviewed_base"] == REVIEWED_BASE
        and binding["post_merge_main"] == POST_M12I_MERGE_MAIN,
        "PR #154 merge binding differs",
    )
    require(
        authority["subject"]["authority_decision"]
        == {
            "reviewer_id": REVIEWER_ID,
            "reviewer_authority": REVIEWER_AUTHORITY,
            "decision": "approved_all_synthesis_candidates_as_written",
            "decision_timestamp": "2026-08-16T03:40:00Z",
        },
        "review authority differs",
    )
    decision = authority["subject"]["synthesis_decisions"][0]
    original = package["subject"]["synthesis_candidates"][0]
    record = implementation["subject"]["implementation_records"][0]
    require(
        decision_accounting
        == {
            "accept_candidate_as_written": 1,
            "accept_with_bounded_revision": 0,
            "rejected": 0,
            "unresolved": 0,
        }
        and decision["synthesis_candidate_id"] == CANDIDATE_ID
        and decision["decision"] == "accept_candidate_as_written"
        and decision["bounded_revision"] is None
        and decision["original_candidate_content_sha256"] == digest(original),
        "exact synthesis decision differs",
    )
    require(
        record["original_candidate_content"] == original
        and record["implemented_synthesis_content"] == original
        and record["original_candidate_content_sha256"] == digest(original)
        and record["implemented_synthesis_content_sha256"] == digest(original)
        and record["original_candidate_subject_sha256"]
        == original["synthesis_candidate_subject_sha256"],
        "accepted synthesis candidate changed during implementation",
    )
    require(
        set(row["proposition_id"] for row in record["behavioral_proposition_lineage"])
        == PROPOSITION_IDS
        and all(
            row["relationship_role"] == "primary_support"
            for row in record["behavioral_proposition_lineage"]
        ),
        "Behavioral Semantic IR lineage differs",
    )
    evidence = record["underlying_evidence"]
    require(
        evidence["unique_episode_count"] == 13
        and evidence["unique_action_count"] == 13
        and len(evidence["unique_episode_ids"])
        == len(set(evidence["unique_episode_ids"]))
        and len(evidence["unique_action_ids"])
        == len(set(evidence["unique_action_ids"])),
        "deduplicated 13/13 lineage differs",
    )
    dispositions = implementation["subject"]["accepted_episode_disposition_accounting"]
    require(
        dispositions
        == {
            "accepted_episode_count": 63,
            "contrast_only_episode_count": 25,
            "no_safe_proposition_episode_count": 24,
            "notable_choice_evidence_episode_count": 0,
            "primary_overlap_count": 0,
            "repeated_pattern_evidence_episode_count": 13,
            "trajectory_evidence_episode_count": 0,
            "unused_non_directional_evidence_episode_count": 1,
        },
        "complete 63-episode disposition accounting differs",
    )
    require(
        final["final_accounting"]
        == {
            "canonical_internal_synthesis_count": 1,
            "unique_behavioral_proposition_input_count": 3,
            "candidate_episode_reference_count": 13,
            "candidate_action_reference_count": 13,
            "cross_candidate_episode_overlap_count": 0,
            "cross_candidate_action_overlap_count": 0,
            "standalone_proposition_count": 0,
        },
        "M12J final accounting differs",
    )
    require(
        original["unresolved_ambiguity"]
        == record["implemented_synthesis_content"]["unresolved_ambiguity"]
        and original["candidate_state"]
        == record["implemented_synthesis_content"]["candidate_state"]
        and original["accepted"] is False
        and original["canonical"] is False
        and original["authorizing"] is False,
        "candidate-era fields changed during layered acceptance",
    )
    require(
        not any(authority["subject"]["downstream_authorizations"].values())
        and not any(implementation["subject"]["downstream_authorizations"].values()),
        "downstream authority leakage",
    )
    verify_seal(parity, "parity_subject_sha256", "M12J parity")
    require(
        canonical_file_sha256(AUTHORITY_PATH) == AUTHORITY_FILE_SHA256
        and authority["authority_subject_sha256"] == AUTHORITY_SUBJECT_SHA256
        and canonical_file_sha256(IMPLEMENTATION_PATH) == IMPLEMENTATION_FILE_SHA256
        and implementation["implementation_subject_sha256"]
        == IMPLEMENTATION_SUBJECT_SHA256
        and canonical_file_sha256(PARITY_PATH) == PARITY_FILE_SHA256
        and parity["parity_subject_sha256"] == PARITY_SUBJECT_SHA256
        and canonical_file_sha256(DOSSIER_PATH) == DOSSIER_FILE_SHA256,
        "M12J governed identity differs",
    )
    for name, expected in M11J_HASHES.items():
        require(
            canonical_file_sha256(M11J_ROOT / name) == expected,
            f"historical M11J bytes changed: {name}",
        )
    current = load(ROOT / "docs/editorial/current_state_index.json")[
        "active_m12j_synthesis_decision_milestone"
    ]
    require(
        current["accepted_m12i_pr"] == ACCEPTED_M12I_PR
        and current["accepted_m12i_head"] == ACCEPTED_M12I_HEAD
        and current["reviewed_base"] == REVIEWED_BASE
        and current["post_m12i_main"] == POST_M12I_MERGE_MAIN
        and current["authority"]["sha256"] == AUTHORITY_FILE_SHA256
        and current["implementation"]["sha256"] == IMPLEMENTATION_FILE_SHA256
        and current["parity"]["sha256"] == PARITY_FILE_SHA256
        and current["canonical_internal_synthesis_count"] == 1
        and not any(current["downstream_authorizations"].values()),
        "M12J current-state identity or authority boundary differs",
    )
    return {
        **deterministic,
        "status": "pass",
        "candidate_subject_sha256": original["synthesis_candidate_subject_sha256"],
        "proposition_ids": sorted(PROPOSITION_IDS),
        "episode_disposition_accounting": dispositions,
        "historical_m11j_byte_compatibility": "pass",
        "downstream_authorizations_false": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
