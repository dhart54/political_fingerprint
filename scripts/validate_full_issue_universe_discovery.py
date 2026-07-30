"""Validate proposed full-issue-universe discovery evidence without authorizing it."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_SCHEMA = (
    ROOT / "docs/methodology/full_issue_universe_discovery_v1.schema.json"
)
SOURCE_SCHEMA = (
    ROOT
    / "docs/methodology/full_issue_universe_source_inventory_v1.schema.json"
)
MANIFEST_SCHEMA = (
    ROOT / "docs/methodology/full_issue_universe_manifest_v1.schema.json"
)
DISCOVERY_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/proposals/"
    "f000477_justice_public_safety_119_full_issue_universe_discovery_v1.json"
)

UNRESOLVED_DISPOSITIONS = {
    "source_missing",
    "source_unresolved",
    "source_conflicting",
    "boundary_review_required",
}


class UniverseDiscoveryValidationError(ValueError):
    """Raised when proposed discovery evidence violates its closed contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise UniverseDiscoveryValidationError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _file_digest_matches(path: Path, expected: str) -> bool:
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() == expected:
        return True
    if path.suffix.lower() in {".json", ".md", ".sql", ".txt"}:
        return (
            hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()
            == expected
        )
    return False


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_validate(value: dict[str, Any], schema_path: Path) -> None:
    schema = _load_json(schema_path)
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(
            schema, format_checker=FormatChecker()
        ).iter_errors(value),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = "; ".join(
            f"{'/'.join(str(part) for part in error.absolute_path)}: "
            f"{error.message}"
            for error in errors
        )
        raise UniverseDiscoveryValidationError(
            f"{schema_path.name} validation failed: {details}"
        )


def _validate_action_set(
    value: dict[str, Any],
    *,
    label: str,
) -> list[str]:
    action_ids = value["action_ids"]
    _require(
        action_ids
        == sorted(
            action_ids,
            key=lambda item: tuple(
                int(part) if index else part
                for index, part in enumerate(item.split(":"))
            ),
        ),
        f"{label} action IDs are not in canonical order",
    )
    _require(
        len(action_ids) == len(set(action_ids)),
        f"{label} contains duplicate action IDs",
    )
    _require(
        value["action_count"] == len(action_ids),
        f"{label} action count mismatch",
    )
    _require(
        value["action_set_sha256"] == sha256_json(sorted(action_ids)),
        f"{label} action-set digest mismatch",
    )
    return action_ids


def validate_candidate_accounting(discovery: dict[str, Any]) -> None:
    candidate_ids = discovery["candidate_recall_set"]["action_ids"]
    proposed_ids = discovery["proposed_universe_set"]["action_ids"]
    unresolved_ids = discovery["unresolved_candidate_set"]["action_ids"]
    dispositions = discovery["candidate_dispositions"]
    disposition_ids = [row["action_id"] for row in dispositions]
    _require(
        len(disposition_ids) == len(set(disposition_ids)),
        "candidate dispositions contain duplicate action IDs",
    )
    _require(
        set(disposition_ids) == set(candidate_ids),
        "each recalled candidate must be accounted for exactly once",
    )
    derived_proposed = {
        row["action_id"]
        for row in dispositions
        if row["disposition"].startswith("proposed_in_scope_")
    }
    _require(
        derived_proposed == set(proposed_ids),
        "proposed universe does not match candidate dispositions",
    )
    derived_unresolved = {
        row["action_id"]
        for row in dispositions
        if row["disposition"] in UNRESOLVED_DISPOSITIONS
    }
    _require(
        derived_unresolved == set(unresolved_ids),
        "unresolved candidates are not fully visible",
    )


def validate_bundle(
    discovery_path: Path = DISCOVERY_PATH,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    discovery = _load_json(discovery_path)
    _schema_validate(discovery, DISCOVERY_SCHEMA)

    complete_ids = _validate_action_set(
        discovery["complete_member_action_snapshot"],
        label="complete member-action snapshot",
    )
    candidate_ids = _validate_action_set(
        discovery["candidate_recall_set"],
        label="candidate recall set",
    )
    proposed_ids = _validate_action_set(
        discovery["proposed_universe_set"],
        label="proposed universe",
    )
    unresolved_ids = _validate_action_set(
        discovery["unresolved_candidate_set"],
        label="unresolved candidate set",
    )
    dispositions = discovery["candidate_dispositions"]
    validate_candidate_accounting(discovery)
    _require(
        set(proposed_ids) <= set(complete_ids),
        "proposed universe contains an action outside the complete snapshot",
    )
    _require(
        all(
            row["production_classification_state"]["present"]
            for row in dispositions
            if row["action_id"] in set(proposed_ids)
        ),
        "proposed manifest and production snapshot do not agree on membership presence",
    )

    benchmark = discovery["benchmark_reconciliation"]
    _require(
        not benchmark["missing_action_ids"],
        "a governed benchmark action is missing",
    )
    _require(
        set(benchmark["expected_action_ids"]) <= set(complete_ids),
        "benchmark is outside the complete snapshot",
    )
    _require(
        set(benchmark["expected_action_ids"]) <= set(proposed_ids),
        "benchmark is outside the proposed universe",
    )

    source_ref = discovery["source_inventory"]
    source_path = (root / source_ref["path"]).resolve()
    _require(
        source_path.is_relative_to(root.resolve()),
        "source inventory path escapes repository root",
    )
    _require(source_path.is_file(), "source inventory is missing")
    _require(
        _file_digest_matches(source_path, source_ref["sha256"]),
        "source inventory digest mismatch",
    )
    source_inventory = _load_json(source_path)
    _schema_validate(source_inventory, SOURCE_SCHEMA)
    _require(
        source_inventory["inventory_id"] == source_ref["inventory_id"],
        "source inventory identity mismatch",
    )

    manifest_ref = discovery["proposed_manifest"]
    manifest_path = (root / manifest_ref["path"]).resolve()
    _require(
        manifest_path.is_relative_to(root.resolve()),
        "proposed manifest path escapes repository root",
    )
    _require(manifest_path.is_file(), "proposed manifest is missing")
    _require(
        _file_digest_matches(manifest_path, manifest_ref["sha256"]),
        "proposed manifest digest mismatch",
    )
    manifest = _load_json(manifest_path)
    _schema_validate(manifest, MANIFEST_SCHEMA)
    _require(
        manifest["manifest_id"] == manifest_ref["manifest_id"],
        "proposed manifest identity mismatch",
    )
    _require(
        manifest["subject"] == discovery["subject"],
        "proposed manifest subject mismatch",
    )
    _require(
        manifest["boundary"] == discovery["cutoff"]["boundary"],
        "proposed manifest boundary mismatch",
    )
    _require(
        manifest["action_ids"] == proposed_ids,
        "proposed manifest membership mismatch",
    )
    _require(
        manifest["action_count"] == len(proposed_ids),
        "proposed manifest count mismatch",
    )
    _require(
        manifest["action_set_sha256"] == sha256_json(sorted(proposed_ids)),
        "proposed manifest action-set digest mismatch",
    )
    subject_input = {
        key: value
        for key, value in manifest.items()
        if key != "universe_subject_sha256"
    }
    _require(
        manifest["universe_subject_sha256"] == sha256_json(subject_input),
        "proposed manifest subject digest mismatch",
    )
    _require(
        manifest_ref["universe_subject_sha256"]
        == manifest["universe_subject_sha256"],
        "discovery does not bind the proposed manifest subject",
    )
    for source in manifest["source_manifests"]:
        path = (root / source["path"]).resolve()
        _require(
            path.is_relative_to(root.resolve()),
            "manifest source path escapes repository root",
        )
        _require(path.is_file(), f"missing manifest source: {source['path']}")
        _require(
            _file_digest_matches(path, source["sha256"]),
            f"manifest source digest mismatch: {source['path']}",
        )

    _require(
        discovery["authority_status"] == "pending_human_universe_review",
        "discovery must remain pending human universe review",
    )
    _require(
        discovery["universe_authority_receipt"] is None,
        "discovery cannot carry a universe authority receipt",
    )
    _require(
        not discovery["full_record_claim"]
        and not discovery["synthesis_eligible"],
        "discovery cannot claim full-record authority or synthesis eligibility",
    )
    authority_receipts = list(
        discovery_path.parent.glob("*full_issue_universe_authority_receipt*.json")
    )
    _require(
        not authority_receipts,
        "proposal directory must not contain a universe authority receipt",
    )
    _require(
        discovery["read_only_session_proof"][
            "all_production_queries_inside_single_proven_transaction"
        ]
        and discovery["read_only_session_proof"][
            "transaction_ended_with_rollback"
        ],
        "production snapshot lacks a complete read-only transaction proof",
    )
    freshness = discovery["final_freshness_check"]
    _require(
        not freshness["changed_result_ids"]
        and freshness["baseline_result_bundle_sha256"]
        == freshness["freshness_result_bundle_sha256"],
        "final production freshness query results differ from baseline",
    )
    _require(
        freshness["complete_member_action_set"]["baseline_action_count"]
        == freshness["complete_member_action_set"]["freshness_action_count"]
        and freshness["complete_member_action_set"][
            "baseline_action_set_sha256"
        ]
        == freshness["complete_member_action_set"][
            "freshness_action_set_sha256"
        ],
        "final production member-action set differs from baseline",
    )
    _require(
        freshness["complete_member_action_records"]["baseline_sha256"]
        == freshness["complete_member_action_records"]["freshness_sha256"],
        "final production member-action records differ from baseline",
    )
    _require(
        freshness["production_primary_justice_set"]["baseline_action_count"]
        == freshness["production_primary_justice_set"][
            "freshness_action_count"
        ]
        and freshness["production_primary_justice_set"][
            "baseline_action_set_sha256"
        ]
        == freshness["production_primary_justice_set"][
            "freshness_action_set_sha256"
        ],
        "final production Justice membership differs from baseline",
    )
    return discovery


def main() -> int:
    discovery = validate_bundle()
    print(
        json.dumps(
            {
                "status": "valid",
                "discovery_id": discovery["discovery_id"],
                "complete_member_action_count": discovery[
                    "complete_member_action_snapshot"
                ]["action_count"],
                "candidate_recall_count": discovery[
                    "candidate_recall_set"
                ]["action_count"],
                "proposed_universe_count": discovery[
                    "proposed_universe_set"
                ]["action_count"],
                "unresolved_candidate_count": discovery[
                    "unresolved_candidate_set"
                ]["action_count"],
                "authority_status": discovery["authority_status"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
