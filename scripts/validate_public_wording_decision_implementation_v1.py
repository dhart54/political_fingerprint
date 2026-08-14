"""Validate a full-record public-wording authority and implementation."""

from __future__ import annotations

import argparse
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


PACKAGE_SCHEMA = (
    ROOT / "docs/methodology/full_record_public_wording_candidates_v1.schema.json"
)
TEMPLATE_SCHEMA = (
    ROOT
    / "docs/methodology/full_record_public_wording_decision_template_v1.schema.json"
)
CANDIDATE_PARITY_SCHEMA = (
    ROOT / "docs/methodology/full_record_public_wording_candidate_parity_v1.schema.json"
)
AUTHORITY_SCHEMA = (
    ROOT / "docs/methodology/full_record_public_wording_authority_v1.schema.json"
)
IMPLEMENTATION_SCHEMA = (
    ROOT
    / "docs/methodology/full_record_public_wording_decision_implementation_v1.schema.json"
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_direct_sources(
    *,
    authority: dict,
    package: dict,
    package_path: Path,
    decision_template: dict,
    decision_template_path: Path,
    candidate_parity: dict,
    candidate_parity_path: Path,
) -> None:
    sources = (
        (
            "candidate_binding",
            package,
            package_path,
            PACKAGE_SCHEMA,
            "public_wording_candidate_package_subject_sha256",
            "package_subject_sha256",
        ),
        (
            "decision_template_binding",
            decision_template,
            decision_template_path,
            TEMPLATE_SCHEMA,
            "decision_template_subject_sha256",
            "decision_template_subject_sha256",
        ),
        (
            "parity_binding",
            candidate_parity,
            candidate_parity_path,
            CANDIDATE_PARITY_SCHEMA,
            "parity_subject_sha256",
            "parity_subject_sha256",
        ),
    )
    for (
        binding_name,
        source,
        path,
        schema_path,
        seal_field,
        binding_digest_field,
    ) in sources:
        Draft7Validator(load(schema_path)).validate(source)
        verify_seal(source, seal_field, binding_name)
        binding = authority["subject"][binding_name]
        if (
            binding["artifact_id"] != source["artifact_id"]
            or binding[binding_digest_field] != source[seal_field]
            or binding["file_sha256"] != canonical_file_sha256(path)
        ):
            raise ValueError(f"{binding_name} direct-source identity differs")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--implementation", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--decision-template", type=Path, required=True)
    parser.add_argument("--candidate-parity", type=Path, required=True)
    args = parser.parse_args()
    authority = load(args.authority)
    implementation = load(args.implementation)
    package = load(args.package)
    template = load(args.decision_template)
    parity = load(args.candidate_parity)
    Draft7Validator(load(AUTHORITY_SCHEMA)).validate(authority)
    Draft7Validator(load(IMPLEMENTATION_SCHEMA)).validate(implementation)
    validate_direct_sources(
        authority=authority,
        package=package,
        package_path=args.package,
        decision_template=template,
        decision_template_path=args.decision_template,
        candidate_parity=parity,
        candidate_parity_path=args.candidate_parity,
    )
    result = validate_implementation(
        implementation,
        authority=authority,
        package=package,
        decision_template=template,
        parity=parity,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
