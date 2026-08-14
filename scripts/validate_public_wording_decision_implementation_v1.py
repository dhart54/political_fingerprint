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
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
    Draft7Validator(
        load(
            ROOT
            / "docs/methodology/full_record_public_wording_authority_v1.schema.json"
        )
    ).validate(authority)
    Draft7Validator(
        load(
            ROOT
            / "docs/methodology/full_record_public_wording_decision_implementation_v1.schema.json"
        )
    ).validate(implementation)
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
