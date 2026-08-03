from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.etl.interpretation_source_readiness import (  # noqa: E402
    build_readiness_artifact,
    canonical_file_sha256,
    load_json,
    prepare_source_manifest,
    render_report,
    validate_source_manifest,
    write_json,
)


PROPOSALS = Path("docs/editorial/full_record_reviews/proposals")
REVIEW_ROOT = Path("docs/editorial/full_record_reviews")
SOURCE_ROOT = REVIEW_ROOT / "source_readiness"
MANIFEST_PATH = (
    PROPOSALS / "f000477_justice_public_safety_119_full_issue_universe_manifest_v2.json"
)
DISCOVERY_PATH = (
    PROPOSALS
    / "f000477_justice_public_safety_119_full_issue_universe_discovery_v2.json"
)
AUTHORITY_PATH = (
    REVIEW_ROOT
    / "f000477_justice_public_safety_119_full_issue_universe_authority_receipt_v2.json"
)
SOURCE_MANIFEST_PATH = (
    SOURCE_ROOT / "f000477_justice_public_safety_119_official_source_manifest_v1.json"
)
SOURCE_MANIFEST_SCHEMA_PATH = Path(
    "docs/methodology/full_issue_interpretation_official_source_manifest_v1.schema.json"
)
READINESS_SCHEMA_PATH = Path(
    "docs/methodology/full_issue_interpretation_source_readiness_v1.schema.json"
)
ARTIFACT_PATH = (
    SOURCE_ROOT
    / "f000477_justice_public_safety_119_interpretation_source_readiness_v1.json"
)
REPORT_PATH = (
    SOURCE_ROOT
    / "f000477_justice_public_safety_119_interpretation_source_readiness_v1.md"
)
EVIDENCE_PATH = SOURCE_ROOT / "evidence"


def _json_bytes(value: dict[str, object]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        + b"\n"
    )


def _check(path: Path, expected: bytes) -> None:
    if not path.is_file() or path.read_bytes() != expected:
        raise ValueError(f"generated output differs: {path.as_posix()}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-source-manifest", action="store_true")
    parser.add_argument("--acquire-missing", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--clerk-dir",
        action="append",
        type=Path,
        default=[],
        help="Official House Clerk cache directory used only to prepare the governed source manifest.",
    )
    parser.add_argument(
        "--congress-dir",
        action="append",
        type=Path,
        default=[],
        help="Official Congress.gov cache directory used only to prepare the governed source manifest.",
    )
    parser.add_argument(
        "--congress-actions-dir",
        action="append",
        type=Path,
        default=[],
        help="Official Congress.gov bill-action response directory used to prepare neutral exact-action projections.",
    )
    parser.add_argument(
        "--congress-text-dir",
        action="append",
        type=Path,
        default=[],
        help="Official Congress.gov text-version response directory used to select exact operative text.",
    )
    args = parser.parse_args()

    manifest = load_json(ROOT / MANIFEST_PATH)
    discovery = load_json(ROOT / DISCOVERY_PATH)
    authority = load_json(ROOT / AUTHORITY_PATH)

    source_path = ROOT / SOURCE_MANIFEST_PATH
    if args.prepare_source_manifest:
        clerk_dirs = args.clerk_dir or [
            ROOT / "backend/data_sources/house_clerk",
            ROOT / "backend/data_sources/house_clerk/2026",
        ]
        congress_dirs = args.congress_dir or [
            ROOT / "backend/data_sources/congress/bills"
        ]
        source_manifest = prepare_source_manifest(
            repository_root=ROOT,
            approved_manifest=manifest,
            discovery=discovery,
            clerk_dirs=clerk_dirs,
            congress_dirs=congress_dirs,
            congress_actions_dirs=args.congress_actions_dir,
            congress_text_dirs=args.congress_text_dir,
            evidence_dir=ROOT / EVIDENCE_PATH,
            acquire_missing=args.acquire_missing,
        )
        write_json(source_path, source_manifest)

    source_manifest = load_json(source_path)
    source_schema = load_json(ROOT / SOURCE_MANIFEST_SCHEMA_PATH)
    Draft7Validator.check_schema(source_schema)
    source_errors = sorted(
        Draft7Validator(source_schema).iter_errors(source_manifest),
        key=lambda error: list(error.path),
    )
    if source_errors:
        raise ValueError(
            f"source-manifest schema validation failed: {source_errors[0].message}"
        )
    validate_source_manifest(
        source_manifest,
        repository_root=ROOT,
        approved_manifest=manifest,
        discovery=discovery,
    )
    artifact = build_readiness_artifact(
        approved_manifest=manifest,
        authority_receipt=authority,
        authority_receipt_sha256=canonical_file_sha256(
            ROOT / AUTHORITY_PATH, text_line_endings="crlf"
        ),
        manifest_sha256=canonical_file_sha256(
            ROOT / MANIFEST_PATH, text_line_endings="crlf"
        ),
        source_manifest=source_manifest,
        source_manifest_sha256=canonical_file_sha256(
            source_path, text_line_endings="lf"
        ),
        discovery=discovery,
    )
    readiness_schema = load_json(ROOT / READINESS_SCHEMA_PATH)
    Draft7Validator.check_schema(readiness_schema)
    readiness_errors = sorted(
        Draft7Validator(readiness_schema).iter_errors(artifact),
        key=lambda error: list(error.path),
    )
    if readiness_errors:
        raise ValueError(
            f"readiness schema validation failed: {readiness_errors[0].message}"
        )
    report = render_report(artifact).encode("utf-8")
    artifact_bytes = _json_bytes(artifact)
    artifact_path = ROOT / ARTIFACT_PATH
    report_path = ROOT / REPORT_PATH
    if args.check:
        _check(artifact_path, artifact_bytes)
        _check(report_path, report)
    else:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_bytes(artifact_bytes)
        report_path.write_bytes(report)
    print(
        json.dumps(
            {
                "status": "pass",
                "mode": "check" if args.check else "write",
                "artifact_id": artifact["artifact_id"],
                **artifact["subject"]["aggregate"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
