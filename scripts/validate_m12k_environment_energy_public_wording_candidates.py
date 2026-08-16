"""Independently validate exact M12K Environment & Energy wording candidates."""

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
from backend.scripts.build_m12k_environment_energy_public_wording_candidates import (  # noqa: E402
    ACCEPTED_M12I_HEAD,
    ACCEPTED_M12I_PR,
    DECISION_SCHEMA_PATH,
    DECISION_TEMPLATE_PATH,
    DOSSIER_PATH,
    M12H_AUTHORITY_PATH,
    M12H_IMPLEMENTATION_PATH,
    M12J_AUTHORITY_PATH,
    M12J_IMPLEMENTATION_PATH,
    PACKAGE_PATH,
    PACKAGE_SCHEMA_PATH,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    POST_M12I_MAIN,
    REVIEWED_BASE,
    build,
)
from scripts.validate_public_wording_candidate_package_v1 import validate_paths  # noqa: E402


PACKAGE_FILE_SHA256 = "805ac5a3231d5a611037a59d9cb38b80875c746bb16a4c8db307dd36a090af00"
PACKAGE_SUBJECT_SHA256 = (
    "4729332d5481ee9d0ef28cc393a875de875d9d7ccea6160a77e53a1f7218b231"
)
TEMPLATE_FILE_SHA256 = (
    "34206d07fedcc0bf70e3bb207e5c4eb784c35c5377097582f5a1e4d612c2c3c2"
)
TEMPLATE_SUBJECT_SHA256 = (
    "a61523d4765794a71b3ae8d8b3b718bd56f56030d3946ae8f0094f2277296a6f"
)
DOSSIER_FILE_SHA256 = "d361d6b2be00f42935fb0a92d629e89cb10c4cd827c0a9619138e5caa154ec71"
PARITY_FILE_SHA256 = "774a415fc9ed0e46c78f7fa8cdff829af831fac685243d95bc20925b82019e07"
PARITY_SUBJECT_SHA256 = (
    "fbb3c0cfac631a53f4f9eec3ace2533af4ea8343677236f40cf0d617e27184bc"
)
EXPECTED_ACCOUNTING = {
    "issue_overview": 1,
    "synthesis": 1,
    "repeated_pattern": 3,
}
BEHAVIORAL_IDS = {
    "pattern-california-vehicle-emissions-waiver-disapproval-opposition",
    "pattern-doe-appliance-efficiency-rule-disapproval-opposition",
    "pattern-blm-land-decision-disapproval-opposition",
}
SYNTHESIS_ID = "synthesis-congressional-disapproval-uniform-opposition"
M11K_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/public_wording_candidates/f000477_national_security_foreign_119_v1"
)
M11K_HASHES = {
    "public_wording_candidate_package.json": "eef9c35e08fd0ccecf931c1a47d6f88793954f92a649386a2032b305b3cc24bb",
    "human_public_wording_decision_template.json": "6e96a461d2d052906b038a8ddf6d7d6fa92ba4309f292f45f88da9fcbf225def",
    "human_review_dossier.md": "fa51b451a6bd6710e3917db7fe5b079be8769aa187abe1a2ec39f8ab2f6c582c",
    "parity_manifest.json": "1d9f02eba933033e6b794d451f93603d826f1e3b0d6565b871ed1fd8512e541d",
}


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
    generic = validate_paths(
        package_path=PACKAGE_PATH,
        decision_template_path=DECISION_TEMPLATE_PATH,
        parity_path=PARITY_PATH,
        behavioral_authority_path=M12H_AUTHORITY_PATH,
        behavioral_implementation_path=M12H_IMPLEMENTATION_PATH,
        synthesis_authority_path=M12J_AUTHORITY_PATH,
        synthesis_implementation_path=M12J_IMPLEMENTATION_PATH,
        package_schema_path=PACKAGE_SCHEMA_PATH,
        decision_schema_path=DECISION_SCHEMA_PATH,
        parity_schema_path=PARITY_SCHEMA_PATH,
    )
    subject = package["subject"]
    require(
        subject["base_binding"]
        == {
            "accepted_m12i_pr": ACCEPTED_M12I_PR,
            "accepted_m12i_head": ACCEPTED_M12I_HEAD,
            "reviewed_base": REVIEWED_BASE,
            "post_m12i_main": POST_M12I_MAIN,
        },
        "PR #154 merge ancestry binding differs",
    )
    require(
        subject["wording_item_accounting"] == EXPECTED_ACCOUNTING,
        "five-item surface accounting differs",
    )
    require(
        subject["source_accounting"]
        == {
            "behavioral_proposition_count": 3,
            "synthesis_record_count": 1,
            "behavioral_primary_wording_count": 3,
            "synthesis_primary_wording_count": 1,
        },
        "primary semantic-source ownership differs",
    )
    require(
        subject["blocked_action_boundaries"] == [] and subject["blocked_actions"] == [],
        "fake Environment blocked action exists",
    )
    require(
        "blocked_action_boundary" not in subject,
        "legacy singular blocked boundary used",
    )
    require(
        "m11h_authority_binding" not in subject
        and "m11j_authority_binding" not in subject,
        "legacy milestone binding used",
    )
    items = subject["wording_items"]
    require(len(items) == 5, "wording item count differs")
    require(
        all(row["direction_display"] is None for row in items),
        "standalone direction display could obscure disapproval object",
    )
    primary_behavioral = [
        binding["source_id"]
        for row in items
        if row["surface"] == "repeated_pattern"
        for binding in row["semantic_source_bindings"]
    ]
    primary_synthesis = [
        binding["source_id"]
        for row in items
        if row["surface"] == "synthesis"
        for binding in row["semantic_source_bindings"]
    ]
    require(
        Counter(primary_behavioral) == Counter(BEHAVIORAL_IDS),
        "Behavioral Semantic IR primary owner differs",
    )
    require(primary_synthesis == [SYNTHESIS_ID], "synthesis primary owner differs")
    require(
        all(
            binding["source_kind"] in {"behavioral", "synthesis"}
            for row in items
            for binding in row["semantic_source_bindings"]
        ),
        "non-semantic source entered wording",
    )
    require(
        all(
            row["semantic_guard"]["statement_basis"]
            == "accepted_semantic_proposition_content"
            and row["semantic_guard"]["raw_yea_nay_maps_to_direction"] is False
            and row["semantic_guard"][
                "direction_metadata_alone_establishes_public_meaning"
            ]
            is False
            for row in items
        ),
        "raw vote or direction metadata determines wording",
    )
    require(
        all(
            "opposed congressional efforts to overturn" in row["primary_sentence"]
            for row in items
        ),
        "double-negative relationship changed",
    )
    for item in items:
        source_limitations = sum(
            len(binding["material_limitations"])
            for binding in item["semantic_source_bindings"]
        )
        require(
            len(item["limitation_treatments"]) == source_limitations,
            "limitation treatment count differs",
        )
        require(
            all(
                row["treatment"] in {"retained_public_copy", "compressed_or_omitted"}
                for row in item["limitation_treatments"]
            ),
            "limitation disappeared",
        )
    require(
        decision["decision_state"] == "empty_pending_human_substantive_wording_review"
        and len(decision["wording_decisions"]) == 5
        and all(
            row["decision"] is None
            and row["bounded_revision"] is None
            and row["reviewer_notes"] is None
            for row in decision["wording_decisions"]
        )
        and decision["reviewer"] is None
        and decision["reviewer_authority"] is None
        and decision["reviewed_at_utc"] is None
        and decision["authorizing"] is False
        and decision["production_selectable"] is False
        and not any(decision["downstream_authorizations"].values()),
        "decision template is not entirely empty and non-authorizing",
    )
    verify_seal(parity, "parity_subject_sha256", "M12K parity")
    require(
        canonical_file_sha256(PACKAGE_PATH) == PACKAGE_FILE_SHA256
        and package["public_wording_candidate_package_subject_sha256"]
        == PACKAGE_SUBJECT_SHA256
        and canonical_file_sha256(DECISION_TEMPLATE_PATH) == TEMPLATE_FILE_SHA256
        and decision["decision_template_subject_sha256"] == TEMPLATE_SUBJECT_SHA256
        and canonical_file_sha256(DOSSIER_PATH) == DOSSIER_FILE_SHA256
        and canonical_file_sha256(PARITY_PATH) == PARITY_FILE_SHA256
        and parity["parity_subject_sha256"] == PARITY_SUBJECT_SHA256,
        "M12K governed identity differs",
    )
    for name, expected in M11K_HASHES.items():
        require(
            canonical_file_sha256(M11K_ROOT / name) == expected,
            f"historical M11K bytes changed: {name}",
        )
    current = load(ROOT / "docs/editorial/current_state_index.json")[
        "active_m12k_public_wording_candidate_milestone"
    ]
    require(
        current["wording_item_count"] == 5
        and current["package"]["sha256"] == PACKAGE_FILE_SHA256
        and current["decision_template"]["sha256"] == TEMPLATE_FILE_SHA256
        and current["dossier"]["sha256"] == DOSSIER_FILE_SHA256
        and current["parity"]["sha256"] == PARITY_FILE_SHA256
        and current["canonical_public_copy"] is False
        and current["production_selectable"] is False
        and not any(current["downstream_authorizations"].values()),
        "M12K current-state identity or authority boundary differs",
    )
    require(
        subject["accepted"] is False
        and subject["canonical_public_copy"] is False
        and subject["production_selectable"] is False
        and not any(subject["downstream_authorizations"].values()),
        "later authority became true",
    )
    return {
        **deterministic,
        **generic,
        "status": "pass",
        "historical_m11k_byte_compatibility": "pass",
        "direction_displays": "all_omitted_to_keep_overturning_object_explicit",
        "downstream_authorizations_false": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
