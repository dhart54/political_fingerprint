"""Independently validate a Behavioral Semantic IR authority/implementation pair."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_behavioral_semantic_ir_decisions import (  # noqa: E402
    validate_authority,
    validate_implementation,
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_paths(
    *,
    authority_path: Path,
    implementation_path: Path,
    candidate_path: Path,
    m11f_authority_path: Path,
    m11f_implementation_path: Path,
    m11d_implementation_path: Path,
    authority_schema_path: Path,
    implementation_schema_path: Path,
    blocked_action_id: str,
) -> dict[str, Any]:
    authority = load(authority_path)
    implementation = load(implementation_path)
    candidate = load(candidate_path)
    m11f_authority = load(m11f_authority_path)
    m11f_implementation = load(m11f_implementation_path)
    m11d_implementation = load(m11d_implementation_path)
    Draft7Validator(load(authority_schema_path)).validate(authority)
    Draft7Validator(load(implementation_schema_path)).validate(implementation)
    decisions = validate_authority(authority, candidate=candidate)
    accounting = validate_implementation(
        implementation,
        authority=authority,
        candidate=candidate,
        m11f_authority=m11f_authority,
        m11f_implementation=m11f_implementation,
        m11d_implementation=m11d_implementation,
        blocked_action_id=blocked_action_id,
    )
    return {
        "status": "valid",
        "authority_id": authority["artifact_id"],
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_id": implementation["artifact_id"],
        "implementation_subject_sha256": implementation[
            "implementation_subject_sha256"
        ],
        "decision_accounting": decisions,
        "final_accounting": accounting,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--implementation", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--m11f-authority", type=Path, required=True)
    parser.add_argument("--m11f-implementation", type=Path, required=True)
    parser.add_argument("--m11d-implementation", type=Path, required=True)
    parser.add_argument("--authority-schema", type=Path, required=True)
    parser.add_argument("--implementation-schema", type=Path, required=True)
    parser.add_argument("--blocked-action-id", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            validate_paths(
                authority_path=args.authority,
                implementation_path=args.implementation,
                candidate_path=args.candidate,
                m11f_authority_path=args.m11f_authority,
                m11f_implementation_path=args.m11f_implementation,
                m11d_implementation_path=args.m11d_implementation,
                authority_schema_path=args.authority_schema,
                implementation_schema_path=args.implementation_schema,
                blocked_action_id=args.blocked_action_id,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
