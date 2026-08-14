"""Independent path-based validation for public-wording candidate packages."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_public_wording_candidates import (  # noqa: E402
    validate_public_wording_candidate_package,
)
from backend.app.etl.full_record_source_readiness import canonical_file_sha256  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_paths(
    *,
    package_path: Path,
    decision_template_path: Path,
    parity_path: Path,
    behavioral_authority_path: Path,
    behavioral_implementation_path: Path,
    synthesis_authority_path: Path,
    synthesis_implementation_path: Path,
    package_schema_path: Path,
    decision_schema_path: Path,
    parity_schema_path: Path,
) -> dict[str, Any]:
    package = load(package_path)
    decision = load(decision_template_path)
    parity = load(parity_path)
    Draft7Validator(load(package_schema_path)).validate(package)
    Draft7Validator(load(decision_schema_path)).validate(decision)
    Draft7Validator(load(parity_schema_path)).validate(parity)
    result = validate_public_wording_candidate_package(
        package,
        behavioral_authority=load(behavioral_authority_path),
        behavioral_implementation=load(behavioral_implementation_path),
        synthesis_authority=load(synthesis_authority_path),
        synthesis_implementation=load(synthesis_implementation_path),
    )
    by_path = {row["path"]: row for row in parity["entries"]}
    for path in (package_path, decision_template_path):
        entry = by_path[path.relative_to(package_path.parent).as_posix()]
        if canonical_file_sha256(path) != entry["file_sha256"]:
            raise ValueError(f"parity file digest differs: {path}")
    if (
        decision["candidate_binding"]["public_wording_candidate_package_subject_sha256"]
        != package["public_wording_candidate_package_subject_sha256"]
    ):
        raise ValueError("decision template candidate binding differs")
    return {
        **result,
        "decision_template_id": decision["artifact_id"],
        "decision_template_subject_sha256": decision[
            "decision_template_subject_sha256"
        ],
        "parity_id": parity["artifact_id"],
        "parity_subject_sha256": parity["parity_subject_sha256"],
    }
