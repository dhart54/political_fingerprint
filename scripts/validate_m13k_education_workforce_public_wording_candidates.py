"""Independently validate exact M13K Education & Workforce wording candidates."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_public_wording_candidates import verify_seal  # noqa: E402
from backend.app.etl.full_record_source_readiness import canonical_file_sha256  # noqa: E402
from backend.scripts.build_m13k_education_workforce_public_wording_candidates import (  # noqa: E402
    ACCEPTED_M13I_HEAD,
    ACCEPTED_M13I_PR,
    DECISION_SCHEMA_PATH,
    DECISION_TEMPLATE_PATH,
    DOSSIER_PATH,
    M13H_AUTHORITY_PATH,
    M13H_IMPLEMENTATION_PATH,
    M13J_AUTHORITY_PATH,
    M13J_IMPLEMENTATION_PATH,
    PACKAGE_PATH,
    PACKAGE_SCHEMA_PATH,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    POST_M13J_MAIN,
    REVIEWED_BASE,
    build,
)
from scripts.m13k_public_wording_candidate_data import NOTABLE_ID, PATTERN_ID  # noqa: E402
from scripts.validate_public_wording_candidate_package_v1 import validate_paths  # noqa: E402

EXPECTED = {
    PACKAGE_PATH: "084ba053f23a925ec92e8b621366817232dcb5a5083e944c490d5813d99f59ec",
    DECISION_TEMPLATE_PATH: "87acea0f0f0ad83d956b5d7d9336575c670655e82f9a9c6534f4eba7452a890c",
    DOSSIER_PATH: "b9875087cfe768ddcabc7afddffb54d8a9deecbfdd7cfeae7e9c8110fdd77694",
    PARITY_PATH: "132389abd74a061985f2c25cf22a77e8298736a2f9da2ca7873b8da5564a6b3b",
}
EXPECTED_SUBJECTS = {
    "package": "1d6980cdc8c822de7e158b917eb6bc4f15d08f2ac31731cadcecb2d6f83f4a4c",
    "decision": "8b6e9d98222a84c43d4d1f62fe3371379455b7653b0909d8f2d46e5b86d271de",
    "parity": "463acc2dbf88f4b0e49353ddb20b4161218d4eefa0fca588006aac68d1bc12f8",
}
HISTORICAL_ROOTS = {
    ROOT
    / "docs/editorial/full_record_reviews/public_wording_candidates/f000477_national_security_foreign_119_v1": {
        "public_wording_candidate_package.json": "eef9c35e08fd0ccecf931c1a47d6f88793954f92a649386a2032b305b3cc24bb",
        "human_public_wording_decision_template.json": "6e96a461d2d052906b038a8ddf6d7d6fa92ba4309f292f45f88da9fcbf225def",
        "human_review_dossier.md": "fa51b451a6bd6710e3917db7fe5b079be8769aa187abe1a2ec39f8ab2f6c582c",
        "parity_manifest.json": "1d9f02eba933033e6b794d451f93603d826f1e3b0d6565b871ed1fd8512e541d",
    },
    ROOT
    / "docs/editorial/full_record_reviews/public_wording_candidates/f000477_environment_energy_119_v1": {
        "public_wording_candidate_package.json": "805ac5a3231d5a611037a59d9cb38b80875c746bb16a4c8db307dd36a090af00",
        "human_public_wording_decision_template.json": "34206d07fedcc0bf70e3bb207e5c4eb784c35c5377097582f5a1e4d612c2c3c2",
        "human_review_dossier.md": "d361d6b2be00f42935fb0a92d629e89cb10c4cd827c0a9619138e5caa154ec71",
        "parity_manifest.json": "774a415fc9ed0e46c78f7fa8cdff829af831fac685243d95bc20925b82019e07",
    },
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate() -> dict[str, Any]:
    deterministic = build(check=True)
    package, decision, parity = (
        load(PACKAGE_PATH),
        load(DECISION_TEMPLATE_PATH),
        load(PARITY_PATH),
    )
    generic = validate_paths(
        package_path=PACKAGE_PATH,
        decision_template_path=DECISION_TEMPLATE_PATH,
        parity_path=PARITY_PATH,
        behavioral_authority_path=M13H_AUTHORITY_PATH,
        behavioral_implementation_path=M13H_IMPLEMENTATION_PATH,
        synthesis_authority_path=M13J_AUTHORITY_PATH,
        synthesis_implementation_path=M13J_IMPLEMENTATION_PATH,
        package_schema_path=PACKAGE_SCHEMA_PATH,
        decision_schema_path=DECISION_SCHEMA_PATH,
        parity_schema_path=PARITY_SCHEMA_PATH,
    )
    subject, items = package["subject"], package["subject"]["wording_items"]
    require(
        subject["base_binding"]
        == {
            "accepted_m13i_pr": ACCEPTED_M13I_PR,
            "accepted_m13i_head": ACCEPTED_M13I_HEAD,
            "reviewed_base": REVIEWED_BASE,
            "post_m13j_main": POST_M13J_MAIN,
        },
        "PR #168 merge ancestry binding differs",
    )
    require(
        subject["wording_item_accounting"]
        == {"issue_overview": 1, "repeated_pattern": 1, "notable_choice": 1},
        "three-surface accounting differs",
    )
    require(
        subject["source_accounting"]
        == {
            "behavioral_proposition_count": 2,
            "synthesis_record_count": 0,
            "behavioral_primary_wording_count": 2,
            "synthesis_primary_wording_count": 0,
        },
        "no-safe source accounting differs",
    )
    require(
        len(items) == 3 and all(row["surface"] != "synthesis" for row in items),
        "synthesis card or wrong item count exists",
    )
    primary = [
        binding["source_id"]
        for row in items
        if row["surface"] in {"repeated_pattern", "notable_choice"}
        for binding in row["semantic_source_bindings"]
    ]
    require(
        Counter(primary) == Counter({PATTERN_ID, NOTABLE_ID}),
        "standalone primary ownership differs",
    )
    overview = next(row for row in items if row["surface"] == "issue_overview")
    require(
        {b["source_id"] for b in overview["semantic_source_bindings"]}
        == {PATTERN_ID, NOTABLE_ID},
        "overview source set differs",
    )
    require(
        "Separately" in overview["primary_sentence"]
        and "not one overall position" in overview["secondary_clarification"],
        "overview invents synthesis",
    )
    notable = next(row for row in items if row["surface"] == "notable_choice")
    require(
        notable["direction_display"] == {"label": "Mixed", "symbol": "±"},
        "mixed display differs",
    )
    require(
        all(
            row["direction_display"] is None
            for row in items
            if row["surface"] != "notable_choice"
        ),
        "issue-level or pattern badge added",
    )
    for item in items:
        require(
            all(
                binding["source_kind"] == "behavioral"
                for binding in item["semantic_source_bindings"]
            ),
            "fake synthesis source entered wording",
        )
        require(
            item["semantic_guard"]["raw_yea_nay_maps_to_direction"] is False
            and item["semantic_guard"][
                "direction_metadata_alone_establishes_public_meaning"
            ]
            is False,
            "raw vote or metadata determines wording",
        )
        require(
            len(item["limitation_treatments"])
            == sum(
                len(b["material_limitations"]) for b in item["semantic_source_bindings"]
            ),
            "limitation treatment count differs",
        )
    require(
        subject["blocked_action_boundaries"] == [] and subject["blocked_actions"] == [],
        "fake blocked action exists",
    )
    require(
        decision["decision_state"] == "empty_pending_human_substantive_wording_review"
        and len(decision["wording_decisions"]) == 3
        and all(
            row["decision"] is None
            and row["bounded_revision"] is None
            and row["reviewer_notes"] is None
            for row in decision["wording_decisions"]
        )
        and decision["reviewer"] is None
        and not any(decision["downstream_authorizations"].values()),
        "decision template is not empty and non-authorizing",
    )
    verify_seal(parity, "parity_subject_sha256", "M13K parity")
    require(
        all(
            canonical_file_sha256(path) == expected
            for path, expected in EXPECTED.items()
        ),
        "M13K governed file identity differs",
    )
    require(
        package["public_wording_candidate_package_subject_sha256"]
        == EXPECTED_SUBJECTS["package"]
        and decision["decision_template_subject_sha256"]
        == EXPECTED_SUBJECTS["decision"]
        and parity["parity_subject_sha256"] == EXPECTED_SUBJECTS["parity"],
        "M13K subject identity differs",
    )
    for root, hashes in HISTORICAL_ROOTS.items():
        for name, expected in hashes.items():
            require(
                canonical_file_sha256(root / name) == expected,
                f"historical wording bytes changed: {root.name}/{name}",
            )
    current = load(ROOT / "docs/editorial/current_state_index.json")[
        "active_m13k_public_wording_candidate_milestone"
    ]
    require(
        current["post_m13j_main"] == POST_M13J_MAIN
        and current["wording_item_count"] == 3
        and current["package"]["sha256"] == EXPECTED[PACKAGE_PATH]
        and current["decision_template"]["sha256"] == EXPECTED[DECISION_TEMPLATE_PATH]
        and current["dossier"]["sha256"] == EXPECTED[DOSSIER_PATH]
        and current["parity"]["sha256"] == EXPECTED[PARITY_PATH]
        and current["canonical_public_copy"] is False
        and current["production_selectable"] is False
        and not any(current["downstream_authorizations"].values()),
        "M13K current-state identity or authority boundary differs",
    )
    require(
        subject["accepted"] is False
        and subject["canonical_public_copy"] is False
        and not any(subject["downstream_authorizations"].values()),
        "later authority became true",
    )
    return {
        **deterministic,
        **generic,
        "status": "pass",
        "historical_m11k_m12k_byte_compatibility": "pass",
        "no_synthesis_card": True,
        "downstream_authorizations_false": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
