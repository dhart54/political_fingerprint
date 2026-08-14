"""Independently validate the exact M11L public-wording decision milestone."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_public_wording_decisions import (  # noqa: E402
    validate_implementation,
    verify_seal,
)
from backend.app.etl.full_record_source_readiness import canonical_file_sha256  # noqa: E402
from backend.scripts.build_m11l_national_security_public_wording_acceptance import (  # noqa: E402
    ACCEPTED_M11K_HEAD,
    AUTHORITY_PATH,
    AUTHORITY_SCHEMA_PATH,
    DOSSIER_PATH,
    IMPLEMENTATION_PATH,
    IMPLEMENTATION_SCHEMA_PATH,
    M11H_AUTHORITY_PATH,
    M11H_IMPLEMENTATION_PATH,
    M11J_AUTHORITY_PATH,
    M11J_IMPLEMENTATION_PATH,
    M11K_PARITY_FILE_SHA256,
    M11K_PARITY_PATH,
    PACKAGE_FILE_SHA256,
    PACKAGE_PATH,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    POST_M11K_MAIN,
    TEMPLATE_FILE_SHA256,
    TEMPLATE_PATH,
)
from scripts.m11l_public_wording_decision_data import (  # noqa: E402
    ACCEPTED_AS_WRITTEN,
    REVISIONS,
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def raw_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_upstream(package: dict, authority: dict) -> None:
    sources = (
        ("m11h_authority_binding", M11H_AUTHORITY_PATH, "authority_subject_sha256"),
        (
            "m11h_implementation_binding",
            M11H_IMPLEMENTATION_PATH,
            "implementation_subject_sha256",
        ),
        ("m11j_authority_binding", M11J_AUTHORITY_PATH, "authority_subject_sha256"),
        (
            "m11j_implementation_binding",
            M11J_IMPLEMENTATION_PATH,
            "implementation_subject_sha256",
        ),
    )
    for key, path, digest_field in sources:
        actual = load(path)
        binding = package["subject"][key]
        if (
            actual["artifact_id"] != binding["artifact_id"]
            or actual[digest_field] != binding[digest_field]
        ):
            raise ValueError(f"{key} upstream identity differs")
        authority_binding = authority["subject"][key]
        if any(
            authority_binding.get(name) != value for name, value in binding.items()
        ) or authority_binding.get("file_sha256") != canonical_file_sha256(path):
            raise ValueError(f"{key} authority binding differs")


def main() -> int:
    package, template, candidate_parity = map(
        load, (PACKAGE_PATH, TEMPLATE_PATH, M11K_PARITY_PATH)
    )
    authority, implementation, parity = map(
        load, (AUTHORITY_PATH, IMPLEMENTATION_PATH, PARITY_PATH)
    )
    if (
        canonical_file_sha256(PACKAGE_PATH) != PACKAGE_FILE_SHA256
        or canonical_file_sha256(TEMPLATE_PATH) != TEMPLATE_FILE_SHA256
        or canonical_file_sha256(M11K_PARITY_PATH) != M11K_PARITY_FILE_SHA256
    ):
        raise ValueError("accepted M11K file identity differs")
    if authority["subject"]["base_binding"] != {
        "accepted_m11k_pr": 143,
        "accepted_m11k_head": ACCEPTED_M11K_HEAD,
        "post_m11k_main": POST_M11K_MAIN,
    }:
        raise ValueError("M11L base binding differs")
    validate_upstream(package, authority)
    Draft7Validator(load(AUTHORITY_SCHEMA_PATH)).validate(authority)
    Draft7Validator(load(IMPLEMENTATION_SCHEMA_PATH)).validate(implementation)
    Draft7Validator(load(PARITY_SCHEMA_PATH)).validate(parity)
    result = validate_implementation(
        implementation,
        authority=authority,
        package=package,
        decision_template=template,
        parity=candidate_parity,
    )
    decisions = {
        row["wording_item_id"]: row for row in authority["subject"]["wording_decisions"]
    }
    if {
        key
        for key, row in decisions.items()
        if row["decision"] == "accept_candidate_as_written"
    } != ACCEPTED_AS_WRITTEN or {
        key
        for key, row in decisions.items()
        if row["decision"] == "accept_with_bounded_revision"
    } != set(REVISIONS):
        raise ValueError("exact 18 human decisions differ")
    verify_seal(parity, "parity_subject_sha256", "M11L parity")
    files = {row["path"]: row for row in parity["entries"]}
    for path in (AUTHORITY_PATH, IMPLEMENTATION_PATH, DOSSIER_PATH):
        row = files[path.name]
        if raw_sha(path) != row["file_sha256"]:
            raise ValueError(f"M11L parity file differs: {path.name}")
    if parity["authority_binding"] != {
        "artifact_id": authority["artifact_id"],
        "authority_subject_sha256": authority["authority_subject_sha256"],
    } or parity["implementation_binding"] != {
        "artifact_id": implementation["artifact_id"],
        "implementation_subject_sha256": implementation[
            "implementation_subject_sha256"
        ],
    }:
        raise ValueError("M11L parity binding differs")
    state = load(ROOT / "docs/editorial/current_state_index.json")
    m11k = state["active_public_wording_candidate_milestone"]
    m11l = state["active_public_wording_decision_milestone"]
    if (
        m11k["milestone_state"] != "completed_human_substantive_review_merged"
        or m11k["post_merge_main"] != POST_M11K_MAIN
    ):
        raise ValueError("M11K closeout state differs")
    if (
        m11l["milestone_state"]
        != "human_decisions_implemented_pending_mechanical_review"
        or m11l["canonical_reviewed_wording_count"] != 18
        or any(m11l["downstream_authorizations"].values())
    ):
        raise ValueError("M11L current state differs")
    if (
        m11l["authority"]["sha256"] != canonical_file_sha256(AUTHORITY_PATH)
        or m11l["implementation"]["sha256"]
        != canonical_file_sha256(IMPLEMENTATION_PATH)
        or m11l["parity"]["sha256"] != canonical_file_sha256(PARITY_PATH)
    ):
        raise ValueError("M11L current-state file identity differs")
    if (
        state["production_publication_state"]["active_publication"]["issue_id"]
        != "JUSTICE_PUBLIC_SAFETY"
    ):
        raise ValueError("accepted Justice publication state changed")
    print(
        json.dumps(
            {
                "base": POST_M11K_MAIN,
                "authority": authority["authority_subject_sha256"],
                "implementation": implementation["implementation_subject_sha256"],
                "parity": parity["parity_subject_sha256"],
                "accounting": result,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
