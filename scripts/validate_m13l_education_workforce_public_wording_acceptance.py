"""Independently validate governed M13L wording acceptance."""

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
from backend.scripts.build_m13l_education_workforce_public_wording_acceptance import (  # noqa: E402
    ACCEPTED_BASE,
    ACCEPTED_HEAD,
    AUTHORITY_PATH,
    CANDIDATE_PARITY_PATH,
    IMPLEMENTATION_PATH,
    PACKAGE_PATH,
    PARITY_PATH,
    TEMPLATE_PATH,
    build,
)

EXPECTED_ITEMS = {
    "wording:issue-overview:education-workforce:119": "e66035ae8ffe9cfe66d9e2166a76102dddbfa6f3f307f9a52a74ab1e79a111de",
    "wording:pattern:education-relationship-funding-restrictions": "850becb2b389b3584966d0c0e1d6f5f3c252b971d3fa476b273aa8a67f21a5ea",
    "wording:notable:hr1048-amendment-final-passage": "9a5dd2ddbf54b0295b1df89b0197790f89f898bc41e36112aa2f50a726675ca2",
}
EXPECTED_FILES = {
    AUTHORITY_PATH: "6ed581a482008132a5854f7bdde6bddae5fc103f069cb7eaa8cc785817fb6ebb",
    IMPLEMENTATION_PATH: "785b071651b0dff64dbebde1a809bce293b85cb1f73b7cf90898402f59883f33",
    PARITY_PATH: "06fc318328c03cff23ec8d6450b2f5e6e0b5bae35d54a789d48aff7daed4a364",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def validate() -> dict:
    built = build(check=True)
    package, template, candidate_parity = (
        load(PACKAGE_PATH),
        load(TEMPLATE_PATH),
        load(CANDIDATE_PARITY_PATH),
    )
    authority, implementation = load(AUTHORITY_PATH), load(IMPLEMENTATION_PATH)
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
        authority["subject"]["base_binding"]
        == {
            "accepted_m13k_pr": 169,
            "accepted_m13k_head": ACCEPTED_HEAD,
            "accepted_m13k_base": ACCEPTED_BASE,
        },
        "review binding differs",
    )
    require(
        set(candidates) == set(records) == set(EXPECTED_ITEMS),
        "wording item set differs",
    )
    for item_id, expected_subject in EXPECTED_ITEMS.items():
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
            f"{item_id} wording changed",
        )
        require(
            record["original_candidate_content_sha256"]
            == digest(candidate)
            == record["implemented_reviewed_wording_sha256"],
            f"{item_id} digest differs",
        )
    surfaces = final["surface_accounting"]
    require(
        surfaces == {"issue_overview": 1, "repeated_pattern": 1, "notable_choice": 1},
        "surface accounting differs",
    )
    require(
        all(row["surface"] != "synthesis" for row in candidates.values()),
        "synthesis surface exists",
    )
    require(
        candidates["wording:issue-overview:education-workforce:119"][
            "direction_display"
        ]
        is None,
        "overview direction exists",
    )
    require(
        candidates["wording:pattern:education-relationship-funding-restrictions"][
            "direction_display"
        ]
        is None,
        "pattern direction exists",
    )
    require(
        candidates["wording:notable:hr1048-amendment-final-passage"][
            "direction_display"
        ]
        == {"label": "Mixed", "symbol": "±"},
        "mixed display differs",
    )
    require(
        not any(authority["subject"]["downstream_authorizations"].values())
        and not any(implementation["subject"]["downstream_authorizations"].values()),
        "downstream authority leaked",
    )
    require(
        all(canonical_file_sha256(path) == sha for path, sha in EXPECTED_FILES.items()),
        "M13L file identity differs",
    )
    return {
        "status": "pass",
        "authority_file_sha256": EXPECTED_FILES[AUTHORITY_PATH],
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_file_sha256": EXPECTED_FILES[IMPLEMENTATION_PATH],
        "implementation_subject_sha256": implementation[
            "implementation_subject_sha256"
        ],
        "parity_file_sha256": EXPECTED_FILES[PARITY_PATH],
        "parity_subject_sha256": load(PARITY_PATH)["parity_subject_sha256"],
        "surface_accounting": surfaces,
        "deterministic": built["files"],
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
