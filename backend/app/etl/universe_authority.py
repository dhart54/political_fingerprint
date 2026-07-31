from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[3]
MANIFEST_SCHEMA = ROOT / "docs/methodology/full_issue_universe_manifest_v1.schema.json"
RECEIPT_SCHEMA = (
    ROOT / "docs/methodology/full_issue_universe_authority_receipt_v1.schema.json"
)
TEXT_SUFFIXES = {".json", ".md", ".sql", ".txt"}


class UniverseAuthorityError(ValueError):
    """Raised when detached issue-universe authority is not content-bound."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise UniverseAuthorityError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def canonical_file_sha256(path: Path) -> str:
    content = path.read_bytes()
    if path.suffix.lower() in TEXT_SUFFIXES:
        content = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def file_digest_matches(path: Path, expected: str) -> bool:
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() == expected:
        return True
    return (
        path.suffix.lower() in TEXT_SUFFIXES
        and hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest() == expected
    )


def _validate_schema(value: dict[str, Any], path: Path, label: str) -> None:
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda error: list(error.absolute_path),
    )
    _require(
        not errors,
        f"{label} schema validation failed: "
        + "; ".join(error.message for error in errors),
    )


def _resolve(root: Path, relative: str, label: str) -> Path:
    resolved_root = root.resolve()
    path = (resolved_root / relative).resolve()
    _require(path.is_relative_to(resolved_root), f"{label} path escapes authority root")
    _require(path.is_file(), f"missing {label}: {relative}")
    return path


def verify_manifest_and_receipt(
    manifest: dict[str, Any],
    receipt: dict[str, Any],
    *,
    manifest_path: Path,
    authority_root: Path = ROOT,
    expected_reviewer_id: str | None = None,
) -> dict[str, Any]:
    """Independently verify a closed manifest and detached authority receipt."""

    _validate_schema(manifest, MANIFEST_SCHEMA, "universe manifest")
    _validate_schema(receipt, RECEIPT_SCHEMA, "universe authority receipt")
    manifest_file_sha256 = canonical_file_sha256(manifest_path)
    _require(
        file_digest_matches(manifest_path, receipt["manifest_sha256"]),
        "receipt manifest digest does not match canonical manifest content",
    )

    action_ids = sorted(manifest["action_ids"])
    _require(
        len(action_ids) == len(set(action_ids)),
        "universe manifest contains duplicate action membership",
    )
    action_set_sha256 = sha256_json(action_ids)
    _require(
        manifest["action_count"] == len(action_ids),
        "universe manifest action count mismatch",
    )
    _require(
        manifest["action_set_sha256"] == action_set_sha256,
        "universe manifest action-set digest mismatch",
    )
    subject = {
        key: value
        for key, value in manifest.items()
        if key != "universe_subject_sha256"
    }
    universe_subject_sha256 = sha256_json(subject)
    _require(
        manifest["universe_subject_sha256"] == universe_subject_sha256,
        "universe manifest subject digest mismatch",
    )
    boundary_sha256 = sha256_json(manifest["boundary"])

    source_manifest_identities: list[str] = []
    for source in manifest["source_manifests"]:
        source_path = _resolve(
            authority_root,
            source["path"],
            "acquisition/governed source manifest",
        )
        _require(
            file_digest_matches(source_path, source["sha256"]),
            f"governed source digest mismatch: {source['path']}",
        )
        source_manifest_identities.append(source["artifact_id"])

    _require(
        receipt["manifest_id"] == manifest["manifest_id"],
        "universe authority receipt authorizes another universe",
    )
    _require(
        receipt["member_id"] == manifest["subject"]["member_id"],
        "receipt member mismatch",
    )
    _require(
        receipt["issue_id"] == manifest["subject"]["issue_id"], "receipt issue mismatch"
    )
    _require(receipt["boundary"] == manifest["boundary"], "receipt boundary mismatch")
    _require(
        receipt["boundary_sha256"] == boundary_sha256,
        "receipt boundary digest mismatch",
    )
    _require(
        receipt["action_count"] == len(action_ids), "receipt action count mismatch"
    )
    _require(
        receipt["action_set_sha256"] == action_set_sha256,
        "receipt action-set digest mismatch",
    )
    _require(
        receipt["source_manifest_identities"] == source_manifest_identities,
        "receipt source-manifest identities mismatch",
    )
    _require(
        receipt["universe_subject_sha256"] == universe_subject_sha256,
        "receipt universe-subject digest mismatch",
    )
    if expected_reviewer_id is not None:
        _require(
            receipt["reviewer"]["reviewer_id"] == expected_reviewer_id,
            "receipt reviewer identity mismatch",
        )

    return {
        "manifest_file_sha256": manifest_file_sha256,
        "action_ids": action_ids,
        "action_count": len(action_ids),
        "action_set_sha256": action_set_sha256,
        "boundary_sha256": boundary_sha256,
        "universe_subject_sha256": universe_subject_sha256,
        "source_manifest_identities": source_manifest_identities,
    }
