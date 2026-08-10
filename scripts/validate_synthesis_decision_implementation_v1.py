"""Independent path-based validation for synthesis decisions."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_synthesis_decisions import validate_implementation  # noqa: E402
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_paths(
    *,
    authority_path: Path,
    implementation_path: Path,
    package_path: Path,
    decision_template_path: Path,
    m11h_authority_path: Path,
    m11h_implementation_path: Path,
    authority_schema_path: Path,
    implementation_schema_path: Path,
) -> dict[str, Any]:
    authority = load(authority_path)
    implementation = load(implementation_path)
    package = load(package_path)
    template = load(decision_template_path)
    Draft7Validator(load(authority_schema_path)).validate(authority)
    Draft7Validator(load(implementation_schema_path)).validate(implementation)
    subject = authority["subject"]
    expected_files = {
        package_path: subject["candidate_binding"]["file_sha256"],
        decision_template_path: subject["decision_template_binding"]["file_sha256"],
        m11h_authority_path: subject["m11h_authority_binding"]["file_sha256"],
        m11h_implementation_path: subject["m11h_implementation_binding"]["file_sha256"],
    }
    for path, expected_sha in expected_files.items():
        if canonical_file_sha256(path) != expected_sha:
            raise ValueError(f"bound input file differs: {path}")
    result = validate_implementation(
        implementation,
        authority=authority,
        package=package,
        decision_template=template,
        m11h_authority=load(m11h_authority_path),
        m11h_implementation=load(m11h_implementation_path),
    )
    return {
        "status": "valid",
        "authority_id": authority["artifact_id"],
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_id": implementation["artifact_id"],
        "implementation_subject_sha256": implementation[
            "implementation_subject_sha256"
        ],
        **result,
    }
