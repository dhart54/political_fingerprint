"""Independently validate exact M13J no-safe-synthesis acceptance."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
)
from backend.app.etl.full_record_synthesis_decisions import (  # noqa: E402
    validate_authority,
    validate_implementation,
)
from backend.scripts.build_m13j_education_workforce_synthesis_acceptance import (  # noqa: E402
    AUTHORITY_PATH,
    AUTHORITY_SCHEMA_PATH,
    DECISION_TIMESTAMP,
    DOSSIER_PATH,
    IMPLEMENTATION_PATH,
    IMPLEMENTATION_SCHEMA_PATH,
    M13H_AUTHORITY_PATH,
    M13H_IMPLEMENTATION_PATH,
    PACKAGE_PATH,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    PROPOSITION_IDS,
    REVIEWER_AUTHORITY,
    REVIEWER_ID,
    REVIEW_DECISION,
    TEMPLATE_PATH,
    build,
)


EXPECTED = {
    AUTHORITY_PATH: "a048de2bbfca7cec6568177e01bbe8a00aab2fe66ec6fd919c563707794b9ce9",
    IMPLEMENTATION_PATH: "bf4189d585ff279fc295a2378468c686f5c23d1165fe1d1231cdc80f3c00f8be",
    PARITY_PATH: "8f30034672515c6ada5f3d9f82782e218d4932f66631ffeb18b27e69aabf258b",
    DOSSIER_PATH: "1009d7e595492490a063670891de7abd729806be61af66e2900c88ef38dc3a08",
}
M11J_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/synthesis_implementations/f000477_national_security_foreign_119_v1"
)
M12J_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/synthesis_implementations/f000477_environment_energy_119_v1"
)
HISTORICAL_HASHES = {
    M11J_ROOT: {
        "human_synthesis_authority.json": "4fd4f7b1490415df3c1f10cc088fcc95d9f48f3eec3504b9312cb447b8e0a1cc",
        "synthesis_decision_implementation.json": "bd2a08caa9100cf3b5326cb739f0ce99db2f6c4650667df8087dc254d1509500",
        "implementation_parity_manifest.json": "0405ef569cff277e861f1453707d22427b9191c2d3bad5033d4704625190211e",
    },
    M12J_ROOT: {
        "human_synthesis_authority.json": "edf92b4543376b94ccebbc87d3ec85ea734d0ab7a38952848062bfe7cc78be5c",
        "synthesis_decision_implementation.json": "74f573f40e8f26eadb6b126a0d0ecaa0b6abb5ca5ac539dd8c4a80d8851692cd",
        "implementation_parity_manifest.json": "4217db5b09a0c07031154fa8dc090c9d7640e37b98035aa82abfb1e919824f4b",
    },
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
    behavioral_authority = load(M13H_AUTHORITY_PATH)
    behavioral_implementation = load(M13H_IMPLEMENTATION_PATH)
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    parity = load(PARITY_PATH)

    for path, expected in EXPECTED.items():
        require(canonical_file_sha256(path) == expected, f"artifact differs: {path}")
    Draft7Validator(load(AUTHORITY_SCHEMA_PATH)).validate(authority)
    Draft7Validator(load(IMPLEMENTATION_SCHEMA_PATH)).validate(implementation)
    Draft7Validator(load(PARITY_SCHEMA_PATH)).validate(parity)
    decisions = validate_authority(
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
        authority["subject"]["authority_decision"]
        == {
            "reviewer_id": REVIEWER_ID,
            "reviewer_authority": REVIEWER_AUTHORITY,
            "decision": REVIEW_DECISION,
            "decision_timestamp": DECISION_TIMESTAMP,
        }
        and authority["subject"]["synthesis_decisions"] == []
        and decisions
        == {
            "accept_candidate_as_written": 0,
            "accept_with_bounded_revision": 0,
            "rejected": 0,
            "unresolved": 0,
        },
        "package-level no-safe authority differs",
    )
    accounting = authority["subject"]["accepted_proposition_role_accounting"]
    require(
        {row["proposition_id"] for row in accounting} == PROPOSITION_IDS
        and all(
            row["accounting_role"] == "intentionally_standalone_no_safe_synthesis"
            and row["candidate_relationships"] == []
            for row in accounting
        )
        and implementation["subject"]["implementation_records"] == []
        and implementation["subject"]["canonical_internal_synthesis_state"]
        == "human_accepted_no_safe_synthesis"
        and final["final_accounting"]
        == {
            "canonical_internal_synthesis_count": 0,
            "unique_behavioral_proposition_input_count": 0,
            "candidate_episode_reference_count": 0,
            "candidate_action_reference_count": 0,
            "cross_candidate_episode_overlap_count": 0,
            "cross_candidate_action_overlap_count": 0,
            "standalone_proposition_count": 2,
        },
        "accepted absence or standalone accounting differs",
    )
    dispositions = Counter(
        row["disposition"]
        for row in behavioral_implementation["subject"][
            "accepted_episode_disposition_ledger"
        ]
    )
    require(
        dispositions
        == {
            "supports_proposed_repeated_pattern": 2,
            "supports_proposed_notable_choice": 1,
            "retained_as_limit_or_contrast": 1,
            "unused_non_directional_evidence": 1,
            "no_safe_higher_level_behavioral_proposition": 11,
        },
        "complete 16-episode accounting differs",
    )
    for root, files in HISTORICAL_HASHES.items():
        for name, expected in files.items():
            require(
                canonical_file_sha256(root / name) == expected,
                f"historical synthesis artifact changed: {root.name}/{name}",
            )
    current = load(ROOT / "docs/editorial/current_state_index.json")[
        "active_m13j_synthesis_decision_milestone"
    ]
    require(
        current["post_m13i_merge_main"] == "b69dae58112adbf90db31c4037ddfaffe1a09551"
        and current["review_decision"] == REVIEW_DECISION
        and current["synthesis_record_count"] == 0
        and current["standalone_proposition_count"] == 2
        and current["authority"]["sha256"] == EXPECTED[AUTHORITY_PATH]
        and current["implementation"]["sha256"] == EXPECTED[IMPLEMENTATION_PATH]
        and current["parity"]["sha256"] == EXPECTED[PARITY_PATH]
        and current["production_selectable"] is False
        and not any(current["downstream_authorizations"].values()),
        "M13J current-state identity or authority boundary differs",
    )
    require(
        not any(authority["subject"]["downstream_authorizations"].values())
        and not any(implementation["subject"]["downstream_authorizations"].values()),
        "downstream authority leakage",
    )
    return {
        "status": "pass",
        "authority_file_sha256": EXPECTED[AUTHORITY_PATH],
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_file_sha256": EXPECTED[IMPLEMENTATION_PATH],
        "implementation_subject_sha256": implementation[
            "implementation_subject_sha256"
        ],
        "parity_file_sha256": EXPECTED[PARITY_PATH],
        "parity_subject_sha256": parity["parity_subject_sha256"],
        "decision": REVIEW_DECISION,
        "synthesis_candidate_count": 0,
        "standalone_proposition_ids": sorted(PROPOSITION_IDS),
        "episode_dispositions": dict(sorted(dispositions.items())),
        "historical_m11j_m12j_byte_compatibility": "pass",
        "deterministic": deterministic,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
