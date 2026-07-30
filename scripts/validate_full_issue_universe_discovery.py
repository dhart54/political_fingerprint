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
    "f000477_justice_public_safety_119_full_issue_universe_discovery_v2.json"
)
COMPARISON_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/proposals/"
    "f000477_justice_public_safety_119_universe_refresh_comparison_v2.json"
)
REPAIR_PLAN_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/proposals/"
    "f000477_justice_public_safety_119_production_repair_plan_v2.json"
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


def validate_source_completeness_statement(value: str) -> None:
    _require(
        value
        == (
            "Official evidence is sufficient for universe-boundary review "
            "through the declared cutoff; remaining stage-specific metadata "
            "gaps are explicit and do not imply interpretation, episode, or "
            "synthesis readiness."
        ),
        "source-completeness claim exceeds the approved boundary",
    )


def validate_action_source_bindings(
    discovery: dict[str, Any],
    source_inventory: dict[str, Any],
) -> None:
    inventory_sources = {
        source["source_id"]: source
        for source in source_inventory["action_meaning_sources"]
    }
    seen_binding_sources: set[str] = set()
    for row in discovery["candidate_dispositions"]:
        binding = row["exact_action_source_binding"]
        readiness = row["source_readiness"]
        _require(
            readiness["boundary_review_source_state"]
            in {"sufficient", "insufficient"},
            f"{row['action_id']} lacks boundary source readiness",
        )
        _require(
            readiness["action_interpretation_source_state"]
            != "ready"
            or readiness["boundary_review_source_state"] == "sufficient",
            "boundary-complete and interpretation-ready states are conflated",
        )
        if not row["disposition"].startswith("proposed_in_scope_"):
            if binding is not None:
                seen_binding_sources.update(
                    source["source_id"]
                    for source in binding[
                        "exact_action_meaning_source_bindings"
                    ]
                )
            continue
        _require(
            binding is not None,
            f"{row['action_id']} proposed action is Clerk-only",
        )
        _require(
            binding["canonical_action_id"] == row["action_id"],
            f"{row['action_id']} binds a source for another action",
        )
        _require(
            binding["boundary_review_sufficiency_state"] == "sufficient",
            f"{row['action_id']} exact-action source is insufficient",
        )
        vote_sources = binding["vote_source_bindings"]
        _require(
            any(
                source["source_type"] == "house_clerk_roll_call"
                and source["source_subject"] == row["action_id"]
                for source in vote_sources
            ),
            f"{row['action_id']} lacks its House Clerk vote source",
        )
        meaning_sources = binding["exact_action_meaning_source_bindings"]
        _require(
            meaning_sources
            and all(
                source["source_type"] != "house_clerk_roll_call"
                for source in meaning_sources
            ),
            f"{row['action_id']} lacks a non-Clerk meaning source",
        )
        exact_identity = binding[
            "exact_measure_or_amendment_identity"
        ]
        for source in meaning_sources:
            seen_binding_sources.add(source["source_id"])
            _require(
                source["source_id"] in inventory_sources,
                f"{row['action_id']} exact source is absent from inventory",
            )
            _require(
                inventory_sources[source["source_id"]] == source,
                f"{row['action_id']} source identity/digest mismatch",
            )
            subject_matches = (
                source["source_subject"] == exact_identity
                or exact_identity.startswith(
                    f"{source['source_subject']}:"
                )
                or source["source_subject"] == row["action_id"]
            )
            _require(
                subject_matches,
                f"{row['action_id']} exact source has wrong subject",
            )
            _require(
                len(source["source_content_sha256"]) == 64,
                f"{row['action_id']} exact source lacks content digest",
            )
        if binding["house_action_stage"] == "amendment":
            _require(
                any(
                    source["source_type"]
                    in {
                        "congress_gov_amendment",
                        "congressional_record_pdf",
                        "house_rules_committee_report",
                    }
                    and (
                        "amendment" in source["evidence_role"]
                        or ":hamdt:" in source["source_subject"]
                        or source["source_subject"] == row["action_id"]
                    )
                    for source in meaning_sources
                ),
                f"{row['action_id']} amendment has parent-only source",
            )
        if "passage" in binding["house_action_stage"]:
            _require(
                all(
                    source["text_version"] not in {"ih", "is"}
                    for source in meaning_sources
                    if source["source_type"]
                    in {"govinfo_bill_text", "govinfo_resolution_text"}
                ),
                f"{row['action_id']} binds the wrong text version",
            )
    _require(
        seen_binding_sources == set(inventory_sources),
        "source inventory contains an unbound or omitted action source",
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
    # Production ingestion is compared independently and cannot erase an
    # official exact action from the candidate or proposed universe.

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
    validate_action_source_bindings(discovery, source_inventory)

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
    if manifest["manifest_version"] >= 2:
        _require(
            manifest["official_member_action_snapshot"]
            == {
                key: discovery["complete_member_action_snapshot"][key]
                for key in (
                    "action_ids",
                    "action_count",
                    "action_set_sha256",
                )
            },
            "V2 manifest does not bind the complete official snapshot",
        )
        _require(
            manifest["substantive_action_set"]
            == discovery["proposed_universe_set"],
            "V2 manifest does not bind proposed substantive membership",
        )
        non_directional = sorted(
            row["action_id"]
            for row in dispositions
            if row["disposition"]
            == "proposed_in_scope_non_directional"
        )
        _require(
            set(
                manifest[
                    "non_directional_substantive_action_set"
                ]["action_ids"]
            )
            == set(non_directional),
            "V2 manifest non-directional binding mismatch",
        )
        disposition_sets = {
            "expressive_nonbinding_action_set": "expressive_nonbinding_context",
            "procedural_context_action_set": "procedural_context",
            "exact_action_ineligible_set": "proposed_exact_action_ineligible",
        }
        for field, disposition in disposition_sets.items():
            expected = sorted(
                row["action_id"]
                for row in dispositions
                if row["disposition"] == disposition
            )
            actual = manifest[field]
            _require(
                set(actual["action_ids"]) == set(expected)
                and actual["action_count"] == len(expected)
                and actual["action_set_sha256"]
                == sha256_json(expected),
                f"V2 manifest {field} binding mismatch",
            )
        _require(
            manifest["unresolved_candidate_set"]
            == discovery["unresolved_candidate_set"],
            "V2 manifest unresolved-set binding mismatch",
        )
        _require(
            manifest["source_inventory_binding"]["inventory_id"]
            == source_inventory["inventory_id"]
            and manifest["source_inventory_binding"]["sha256"]
            == source_ref["sha256"],
            "V2 manifest source-inventory binding mismatch",
        )
        _require(
            manifest["production_snapshot_identity"]["snapshot_id"]
            == discovery["cutoff"]["production_snapshot_id"]
            and manifest["production_snapshot_identity"][
                "raw_snapshot_sha256"
            ]
            == discovery["cutoff"]["production_snapshot_sha256"]
            and manifest["production_snapshot_identity"][
                "completion_subject_sha256"
            ]
            == discovery["final_freshness_check"][
                "baseline_completion_subject_sha256"
            ],
            "V2 manifest production snapshot binding mismatch",
        )
        cross_domain_rows = {
            row["action_id"]: row
            for row in dispositions
            if "issue_memberships" in row
        }
        _require(
            manifest["cross_domain_memberships"]
            == {
                action_id: row["issue_memberships"]
                for action_id, row in cross_domain_rows.items()
            }
            and manifest["cross_domain_scope_limitations"]
            == {
                action_id: row["cross_domain_scope_limitations"]
                for action_id, row in cross_domain_rows.items()
            },
            "V2 manifest cross-domain binding mismatch",
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
    if discovery["discovery_version"] >= 2:
        _require(
            not unresolved_ids,
            "V2 refresh must route every candidate to a resolved disposition",
        )
        comparison = _load_json(COMPARISON_PATH)
        repair_plan = _load_json(REPAIR_PLAN_PATH)
        new_ids = comparison["new_action_ids"]
        new_rows = comparison["new_action_dispositions"]
        _require(
            len(new_ids) == len(set(new_ids))
            and [row["action_id"] for row in new_rows] == new_ids,
            "newly observed actions are not dispositioned exactly once",
        )
        validate_source_completeness_statement(
            comparison["source_completeness_statement"]
        )
        corrected_rows = [
            row
            for row in comparison["boundary_diff"]
            if row["change_type"] == "review_correction"
        ]
        _require(
            len(corrected_rows) == 22
            and all(
                row["exact_source_ids"]
                and row["content_digests"]
                and row["evidence_roles"]
                and row["review_sufficiency_status"] == "sufficient"
                for row in corrected_rows
            ),
            "all 22 V1-to-V2 corrections must be source-bound",
        )
        gap_summary = source_inventory["stage_source_gap_summary"]
        _require(
            discovery["source_gaps"][0]["action_ids"]
            == gap_summary["action_ids"]
            and sum(gap_summary["counts_by_disposition"].values())
            == gap_summary["total_candidate_count"],
            "remaining stage-specific source gaps are not fully visible",
        )
        _require(
            comparison["authorizing"] is False
            and comparison["authority_receipt"] is None
            and comparison["interpretation_artifact"] is None
            and comparison["episode_artifact"] is None
            and comparison["semantic_ir_artifact"] is None
            and comparison["publication_artifact"] is None,
            "V2 comparison crossed an unauthorized downstream boundary",
        )
        _require(
            repair_plan["execution_authorized"] is False
            and repair_plan["production_writes_performed"] is False,
            "production repair plan must remain non-mutating",
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
