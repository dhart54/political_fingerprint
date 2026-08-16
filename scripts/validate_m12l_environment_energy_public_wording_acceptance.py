"""Independently validate governed M12L Environment & Energy wording acceptance."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_public_wording_decisions import (  # noqa: E402
    digest,
    validate_implementation,
)
from backend.app.etl.full_record_source_readiness import canonical_file_sha256  # noqa: E402
from backend.scripts.build_m12l_environment_energy_public_wording_acceptance import (  # noqa: E402
    ACCEPTED_HEAD,
    AUTHORITY_PATH,
    CANDIDATE_PARITY_PATH,
    IMPLEMENTATION_PATH,
    PACKAGE_PATH,
    PARITY_PATH,
    TEMPLATE_PATH,
    build,
)

EXPECTED_ITEM_SUBJECTS = {
    "wording:issue-overview:environment-energy:119": "9dedaaada9cb469da2ce171efd57e2fdc823feef1be80fffb1382aac96ec8dfb",
    "wording:synthesis:congressional-disapproval": "b1218d6c753972cf80eade3714c482004db997e5e07d7fa09392ebe2a5a3453e",
    "wording:pattern:california-emissions-waivers": "ddeec074044b0c39e0b7487956001ffbc194106bf0f85418e3a1ee423d2790f9",
    "wording:pattern:doe-appliance-equipment-rules": "f954467fcee84537cbcc779e463e69d85ab6a1228cc770201dfd66247c383e50",
    "wording:pattern:blm-land-decisions": "a56e23d1d918cf6c309fb6db6bc001b7e4708c9a26ffb193d5112de0ecdc6772",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    build(check=True)
    package, template, candidate_parity = (
        load(PACKAGE_PATH),
        load(TEMPLATE_PATH),
        load(CANDIDATE_PARITY_PATH),
    )
    authority, implementation, parity = (
        load(AUTHORITY_PATH),
        load(IMPLEMENTATION_PATH),
        load(PARITY_PATH),
    )
    final = validate_implementation(
        implementation,
        authority=authority,
        package=package,
        decision_template=template,
        parity=candidate_parity,
    )
    candidates = {
        row["wording_item_id"]: row for row in package["subject"]["wording_items"]
    }
    records = {
        row["wording_item_id"]: row
        for row in implementation["subject"]["implementation_records"]
    }
    require(
        authority["subject"]["base_binding"]["accepted_m12k_head"] == ACCEPTED_HEAD,
        "accepted head differs",
    )
    require(
        set(candidates) == set(EXPECTED_ITEM_SUBJECTS) == set(records),
        "wording identity set differs",
    )
    for item_id, expected_subject in EXPECTED_ITEM_SUBJECTS.items():
        candidate, record = candidates[item_id], records[item_id]
        require(
            candidate["wording_item_subject_sha256"] == expected_subject,
            f"{item_id} subject differs",
        )
        require(
            record["decision"] == "accept_candidate_as_written"
            and record["bounded_revision"] is None,
            f"{item_id} decision differs",
        )
        require(
            record["original_candidate_content"]
            == candidate
            == record["implemented_reviewed_wording"],
            f"{item_id} copy or structure drift",
        )
        require(
            record["original_candidate_content_sha256"]
            == digest(candidate)
            == record["implemented_reviewed_wording_sha256"],
            f"{item_id} content digest differs",
        )
        require(
            candidate["direction_display"] is None,
            f"{item_id} direction display invented",
        )
    require(
        final["canonical_reviewed_wording_count"] == 5,
        "canonical wording count differs",
    )
    require(
        authority["subject"]["blocked_actions"]
        == authority["subject"]["blocked_action_boundaries"]
        == [],
        "Environment blocked action invented",
    )
    require(
        not any(authority["subject"]["downstream_authorizations"].values()),
        "authority leaked",
    )
    require(
        not any(implementation["subject"]["downstream_authorizations"].values()),
        "implementation leaked",
    )
    require(
        len(parity["entries"]) == 4 and canonical_file_sha256(PARITY_PATH),
        "parity differs",
    )
    print(
        "M12L validation passed: 5/5 exact accept-as-written; zero blocked actions; downstream authorities false"
    )


if __name__ == "__main__":
    main()
