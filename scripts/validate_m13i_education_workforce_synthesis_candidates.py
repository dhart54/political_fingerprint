"""Independently validate the M13I Education & Workforce no-safe-synthesis state."""

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
from backend.app.etl.full_record_synthesis_candidates import (  # noqa: E402
    validate_synthesis_candidate_package,
)
from backend.scripts.build_m13h_education_workforce_semantic_ir_acceptance import (  # noqa: E402
    AUTHORITY_PATH,
    IMPLEMENTATION_PATH,
    POST_M13G_MERGE_MAIN,
)
from backend.scripts.build_m13i_education_workforce_synthesis_candidates import (  # noqa: E402
    DECISION_SCHEMA_PATH,
    DECISION_TEMPLATE_PATH,
    DOSSIER_PATH,
    PACKAGE_PATH,
    PACKAGE_SCHEMA_PATH,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    PROPOSITION_IDS,
    build,
)


EXPECTED_HASHES = {
    PACKAGE_PATH: "09f18212828e9dcbb31f75c1d80acfdee849519fb314fbd1cd64a426aebdefd3",
    DECISION_TEMPLATE_PATH: "867194246dce032fa73274224e5433d3222bce93245f68b3311fbc8354850d82",
    DOSSIER_PATH: "30610ff927512f1fdc810c2de05fc182b7c79ad4f21a5c46e2b5a177bfb7346b",
    PARITY_PATH: "170feeca382335c87ce41d3591978a02c6365380fbdaefcfed6d0c396024c7c3",
}
PACKAGE_SUBJECT_SHA256 = (
    "4c2d5270f4795b26ceca287f654a2e8973c022dfbcb983326f19a77c90a1406e"
)
PARITY_SUBJECT_SHA256 = (
    "83f8c44f7b85021e4af90e40f42eb5e856a4cbab22500be787b6b399ab0f771f"
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate() -> dict[str, Any]:
    deterministic = build(check=True)
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    package = load(PACKAGE_PATH)
    decision = load(DECISION_TEMPLATE_PATH)
    parity = load(PARITY_PATH)
    current_state = load(ROOT / "docs/editorial/current_state_index.json")

    for path, expected in EXPECTED_HASHES.items():
        require(canonical_file_sha256(path) == expected, f"artifact differs: {path}")
    Draft7Validator(load(PACKAGE_SCHEMA_PATH)).validate(package)
    Draft7Validator(load(DECISION_SCHEMA_PATH)).validate(decision)
    Draft7Validator(load(PARITY_SCHEMA_PATH)).validate(parity)
    generic = validate_synthesis_candidate_package(
        package, authority=authority, implementation=implementation
    )

    subject = package["subject"]
    accounting = subject["complete_proposition_accounting"]
    require(
        subject["source_behavioral_proposition_count"] == 2
        and subject["synthesis_candidate_count"] == 0
        and subject["synthesis_candidates"] == []
        and subject["candidate_overlap_accounting"] == [],
        "M13I must remain an explicit zero-candidate state",
    )
    require(
        {row["proposition_id"] for row in accounting} == set(PROPOSITION_IDS)
        and subject["proposition_accounting_counts"]
        == {"intentionally_standalone_no_safe_synthesis": 2}
        and all(
            row["accounting_role"] == "intentionally_standalone_no_safe_synthesis"
            and row["candidate_relationships"] == []
            for row in accounting
        ),
        "complete standalone proposition accounting differs",
    )
    ledger = implementation["subject"]["accepted_episode_disposition_ledger"]
    dispositions = Counter(row["disposition"] for row in ledger)
    require(
        len(ledger) == 16
        and dispositions
        == {
            "supports_proposed_repeated_pattern": 2,
            "supports_proposed_notable_choice": 1,
            "retained_as_limit_or_contrast": 1,
            "unused_non_directional_evidence": 1,
            "no_safe_higher_level_behavioral_proposition": 11,
        },
        "accepted 16-episode accounting changed during synthesis",
    )
    ledger_by_id = {row["episode_id"]: row for row in ledger}
    require(
        ledger_by_id["single-119-hr-1005-1-312"]["disposition"]
        == "unused_non_directional_evidence"
        and ledger_by_id["single-119-hr-1049-1-314"]["disposition"]
        == "retained_as_limit_or_contrast",
        "H.R. 1005 or H.R. 1049 boundary differs",
    )
    require(
        package["synthesis_candidate_package_subject_sha256"] == PACKAGE_SUBJECT_SHA256
        and parity["parity_subject_sha256"] == PARITY_SUBJECT_SHA256
        and decision["candidate_decisions"] == []
        and decision["decision_state"]
        == "empty_pending_human_substantive_synthesis_review"
        and decision["authorizing"] is False
        and not any(decision["downstream_authorizations"].values())
        and not any(subject["downstream_authorizations"].values()),
        "identity, empty review state, or authority boundary differs",
    )
    state = current_state["active_m13i_synthesis_candidate_milestone"]
    require(
        state["post_m13g_merge_main"] == POST_M13G_MERGE_MAIN
        and state["synthesis_candidate_count"] == 0
        and set(state["intentionally_standalone_proposition_ids"])
        == set(PROPOSITION_IDS)
        and state["package_identity"]["sha256"] == EXPECTED_HASHES[PACKAGE_PATH]
        and state["synthesis_acceptance"] is False
        and not any(state["downstream_authorizations"].values()),
        "M13I current-state identity or authority boundary differs",
    )
    return {
        "status": "valid",
        "candidate_count": generic["candidate_count"],
        "package_file_sha256": EXPECTED_HASHES[PACKAGE_PATH],
        "package_subject_sha256": PACKAGE_SUBJECT_SHA256,
        "decision_template_file_sha256": EXPECTED_HASHES[DECISION_TEMPLATE_PATH],
        "dossier_file_sha256": EXPECTED_HASHES[DOSSIER_PATH],
        "parity_file_sha256": EXPECTED_HASHES[PARITY_PATH],
        "parity_subject_sha256": PARITY_SUBJECT_SHA256,
        "intentionally_standalone_proposition_ids": PROPOSITION_IDS,
        "episode_dispositions": dict(sorted(dispositions.items())),
        "deterministic": deterministic,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
