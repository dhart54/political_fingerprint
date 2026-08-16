"""Independently validate detached M12I Environment & Energy synthesis candidates."""

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
    verify_seal,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
)
from backend.app.etl.full_record_synthesis_candidates import (  # noqa: E402
    validate_synthesis_candidate_package,
)
from backend.scripts.build_m12h_environment_energy_semantic_ir_acceptance import (  # noqa: E402
    AUTHORITY_PATH as M12H_AUTHORITY_PATH,
    IMPLEMENTATION_PATH as M12H_IMPLEMENTATION_PATH,
)
from backend.scripts.build_m12i_environment_energy_synthesis_candidates import (  # noqa: E402
    CANDIDATE_DEFINITIONS,
    DECISION_SCHEMA_PATH,
    DECISION_TEMPLATE_PATH,
    DOSSIER_PATH,
    M12H_AUTHORITY_FILE_SHA256,
    M12H_AUTHORITY_SUBJECT_SHA256,
    M12H_IMPLEMENTATION_FILE_SHA256,
    M12H_IMPLEMENTATION_SUBJECT_SHA256,
    PACKAGE_PATH,
    PACKAGE_SCHEMA_PATH,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    PROPOSITION_IDS,
    build,
)


M11I_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/synthesis_candidates/f000477_national_security_foreign_119_v1"
)
M11I_HASHES = {
    "synthesis_candidate_package.json": "e5cfd7305babb5690d496a02b3c1dcc056d4368d980f0d25e5dd1c8d988345c8",
    "human_synthesis_decision_template.json": "9727717a17b5cbf48786f8eee0f1ece71f347dff1d9fceec983eaa060f2f3a11",
    "human_review_dossier.md": "a89e849ce41e6b2e83542b2497e36d8882a37715eddeb94f12c8765796135d3c",
    "parity_manifest.json": "412103e7c380c6da506b9a03512626cd35b613af9782676572a87f7c3757b7e0",
}
EXPECTED_CANDIDATE_ID = "synthesis-congressional-disapproval-uniform-opposition"
EXCLUDED_EPISODE_IDS = {
    "single-119-hr-6387-2-136",
    "single-119-hr-471-1-25",
    "single-119-hr-3898-1-330",
}
EXCLUDED_ACTION_IDS = {"house:119:2:136", "house:119:1:25", "house:119:1:330"}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate() -> dict[str, Any]:
    deterministic = build(check=True)
    package = load(PACKAGE_PATH)
    decision = load(DECISION_TEMPLATE_PATH)
    parity = load(PARITY_PATH)
    authority = load(M12H_AUTHORITY_PATH)
    implementation = load(M12H_IMPLEMENTATION_PATH)
    current_state = load(ROOT / "docs/editorial/current_state_index.json")
    Draft7Validator(load(PACKAGE_SCHEMA_PATH)).validate(package)
    Draft7Validator(load(DECISION_SCHEMA_PATH)).validate(decision)
    Draft7Validator(load(PARITY_SCHEMA_PATH)).validate(parity)
    generic = validate_synthesis_candidate_package(
        package, authority=authority, implementation=implementation
    )

    require(
        canonical_file_sha256(M12H_AUTHORITY_PATH) == M12H_AUTHORITY_FILE_SHA256
        and authority["authority_subject_sha256"] == M12H_AUTHORITY_SUBJECT_SHA256
        and canonical_file_sha256(M12H_IMPLEMENTATION_PATH)
        == M12H_IMPLEMENTATION_FILE_SHA256
        and implementation["implementation_subject_sha256"]
        == M12H_IMPLEMENTATION_SUBJECT_SHA256,
        "accepted M12H identity differs",
    )
    subject = package["subject"]
    require(
        subject["source_behavioral_proposition_count"] == 3
        and subject["synthesis_candidate_count"] == 1
        and len(subject["synthesis_candidates"]) == 1,
        "M12I candidate count differs",
    )
    candidate = subject["synthesis_candidates"][0]
    require(
        candidate["synthesis_candidate_id"] == EXPECTED_CANDIDATE_ID
        and candidate["synthesis_type"] == "uniform_direction"
        and candidate["direction"] == "opposition"
        and candidate["conclusion_relevance"] == "primary"
        and candidate["proposition"] == CANDIDATE_DEFINITIONS[0]["proposition"],
        "bounded uniform-direction candidate differs",
    )
    bindings = candidate["input_bindings"]
    require(
        [row["proposition_id"] for row in bindings] == PROPOSITION_IDS
        and all(row["relationship_role"] == "primary_support" for row in bindings)
        and candidate["relationships"]
        == {
            "supported_by": PROPOSITION_IDS,
            "contextualized_by": [],
            "contrasted_by": [],
            "limited_by": [],
        },
        "accepted M12H input relationships differ",
    )
    accepted_records = {
        row["proposition_id"]: row
        for row in implementation["subject"]["implementation_records"]
    }
    require(
        all(
            row["implementation_record_id"]
            == accepted_records[row["proposition_id"]]["record_id"]
            and row["implementation_record_subject_sha256"]
            == accepted_records[row["proposition_id"]]["record_subject_sha256"]
            and row["accepted_candidate_content_sha256"]
            == accepted_records[row["proposition_id"]][
                "accepted_candidate_content_sha256"
            ]
            for row in bindings
        ),
        "synthesis input content binding differs",
    )
    evidence = candidate["underlying_evidence"]
    require(
        evidence["behavioral_proposition_input_count"] == 3
        and evidence["unique_episode_count"] == 13
        and evidence["unique_action_count"] == 13
        and len(evidence["unique_episode_ids"])
        == len(set(evidence["unique_episode_ids"]))
        and len(evidence["unique_action_ids"])
        == len(set(evidence["unique_action_ids"]))
        and evidence["independent_evidence_unit"]
        == "accepted_behavioral_semantic_ir_underlying_episode"
        and evidence["pattern_nodes_and_episodes_are_not_additive"] is True,
        "deduplicated synthesis lineage differs",
    )
    require(
        not EXCLUDED_EPISODE_IDS.intersection(evidence["unique_episode_ids"])
        and not EXCLUDED_ACTION_IDS.intersection(evidence["unique_action_ids"]),
        "excluded episode or action material entered synthesis",
    )
    accounting = subject["complete_proposition_accounting"]
    require(
        len(accounting) == 3
        and {row["proposition_id"] for row in accounting} == set(PROPOSITION_IDS)
        and all(row["accounting_role"] == "primary_input" for row in accounting)
        and subject["proposition_accounting_counts"] == {"primary_input": 3}
        and subject["candidate_overlap_accounting"] == [],
        "complete proposition or overlap accounting differs",
    )
    ledger = subject["accepted_episode_disposition_ledger"]
    dispositions = Counter(row["disposition"] for row in ledger)
    require(
        len(ledger) == 63
        and dispositions
        == {
            "supports_proposed_repeated_pattern": 13,
            "retained_as_limit_or_contrast": 25,
            "no_safe_higher_level_behavioral_proposition": 24,
            "unused_non_directional_evidence": 1,
        }
        and subject["episode_disposition_accounting"]
        == implementation["subject"]["accepted_episode_disposition_accounting"],
        "accepted episode ledger changed during synthesis",
    )
    definition = CANDIDATE_DEFINITIONS[0]
    require(
        candidate["relationship_basis"] == definition["relationship_basis"]
        and candidate["relationship_rationale"] == definition["relationship_rationale"]
        and candidate["material_limitations"] == definition["material_limitations"]
        and candidate["competing_interpretation"]
        == definition["competing_interpretation"]
        and candidate["unresolved_ambiguity"] == definition["unresolved_ambiguity"]
        and candidate["prohibited_inferences"] == definition["prohibited_inferences"],
        "synthesis judgment boundaries differ",
    )
    require(
        decision["candidate_binding"]["synthesis_candidate_package_subject_sha256"]
        == package["synthesis_candidate_package_subject_sha256"]
        and len(decision["candidate_decisions"]) == 1
        and decision["candidate_decisions"][0]["decision"] is None
        and decision["reviewer"] is None
        and decision["reviewer_authority"] is None
        and decision["reviewed_at_utc"] is None
        and decision["authorizing"] is False
        and not any(decision["downstream_authorizations"].values())
        and not any(subject["downstream_authorizations"].values()),
        "empty non-authorizing decision boundary differs",
    )
    state = current_state["active_m12i_synthesis_candidate_milestone"]
    require(
        state["synthesis_candidate_count"] == 1
        and state["candidate_ids"] == [EXPECTED_CANDIDATE_ID]
        and state["package_identity"]["sha256"] == canonical_file_sha256(PACKAGE_PATH)
        and state["decision_template_identity"]["sha256"]
        == canonical_file_sha256(DECISION_TEMPLATE_PATH)
        and state["dossier_identity"]["sha256"] == canonical_file_sha256(DOSSIER_PATH)
        and state["parity_identity"]["sha256"] == canonical_file_sha256(PARITY_PATH)
        and state["intentionally_standalone_proposition_ids"] == []
        and state["synthesis_acceptance"] is False
        and not any(state["downstream_authorizations"].values()),
        "M12I current-state identity or authority boundary differs",
    )
    verify_seal(parity, "parity_subject_sha256", "M12I parity")
    expected_paths = {PACKAGE_PATH, DECISION_TEMPLATE_PATH, DOSSIER_PATH}
    require(
        {PACKAGE_PATH.parent / row["path"] for row in parity["entries"]}
        == expected_paths,
        "M12I parity file set differs",
    )
    for row in parity["entries"]:
        path = PACKAGE_PATH.parent / row["path"]
        require(
            canonical_file_sha256(path) == row["file_sha256"],
            f"M12I parity digest differs: {path.name}",
        )
    for name, expected in M11I_HASHES.items():
        require(
            canonical_file_sha256(M11I_ROOT / name) == expected,
            f"historical M11I bytes changed: {name}",
        )
    return {
        **generic,
        "package_file_sha256": canonical_file_sha256(PACKAGE_PATH),
        "package_subject_sha256": package["synthesis_candidate_package_subject_sha256"],
        "candidate_id": EXPECTED_CANDIDATE_ID,
        "candidate_subject_sha256": candidate["synthesis_candidate_subject_sha256"],
        "input_proposition_ids": PROPOSITION_IDS,
        "unique_episode_count": 13,
        "unique_action_count": 13,
        "intentionally_standalone_proposition_ids": [],
        "decision_template_file_sha256": canonical_file_sha256(DECISION_TEMPLATE_PATH),
        "decision_template_subject_sha256": decision[
            "decision_template_subject_sha256"
        ],
        "dossier_file_sha256": canonical_file_sha256(DOSSIER_PATH),
        "parity_file_sha256": canonical_file_sha256(PARITY_PATH),
        "parity_subject_sha256": parity["parity_subject_sha256"],
        "historical_m11i_byte_compatibility": "pass",
        "downstream_authorizations_false": True,
        "deterministic": deterministic,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
