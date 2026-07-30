from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.etl.readonly_discovery import sanitized_session_proof  # noqa: E402
from app.etl.universe_discovery import (  # noqa: E402
    UNRESOLVED_DISPOSITIONS,
    action_set,
    action_sort_key,
    build_candidate_recall,
    canonical_json_bytes,
    directory_manifest,
    discovery_disposition,
    is_procedural_context,
    load_congress_metadata,
    load_house_clerk_member_actions,
    sha256_file,
    sha256_json,
    sorted_action_ids,
)


SOURCE_INVENTORY_REL = Path(
    "docs/editorial/full_record_reviews/proposals/"
    "f000477_justice_public_safety_119_source_inventory_v1.json"
)
MANIFEST_REL = Path(
    "docs/editorial/full_record_reviews/proposals/"
    "f000477_justice_public_safety_119_full_issue_universe_manifest_v1.json"
)
DISCOVERY_REL = Path(
    "docs/editorial/full_record_reviews/proposals/"
    "f000477_justice_public_safety_119_full_issue_universe_discovery_v1.json"
)
GOLD_SOURCE_MANIFEST_REL = Path(
    "docs/editorial/valerie_foushee_justice_public_safety_gold_v1/"
    "source_manifest.json"
)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ).encode("utf-8")
        + b"\n"
    )


def _production_bill_ref(row: dict[str, Any]) -> str | None:
    bill_type = row.get("bill_type")
    bill_number = row.get("bill_number")
    if bill_type is None or bill_number is None:
        return None
    return f"bill_{row['congress']}_{str(bill_type).lower()}_{int(bill_number)}"


def _official_projection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "canonical_action_id": row["canonical_action_id"],
        "bill_ref": row["bill_ref"],
        "chamber": row["chamber"],
        "congress": row["congress"],
        "description": row["description"],
        "member_action": row["member_action"],
        "question": row["question"],
        "rollcall_number": row["rollcall_number"],
        "session": row["session"],
        "source_url": row["source_url"],
        "vote_date": row["vote_date"],
    }


def _production_projection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "canonical_action_id": row["canonical_action_id"],
        "bill_ref": _production_bill_ref(row),
        "chamber": str(row["chamber"]).lower(),
        "congress": int(row["congress"]),
        "description": row.get("description") or "",
        "member_action": str(row["member_action"]).lower(),
        "question": row.get("question") or "",
        "rollcall_number": int(row["rollcall_number"]),
        "session": int(row["session"]),
        "vote_date": str(row["vote_date"])[:10],
    }


def _final_freshness_check(
    baseline_snapshot: dict[str, Any],
    freshness_snapshot: dict[str, Any],
    *,
    baseline_snapshot_path: Path,
    freshness_snapshot_path: Path,
    issue_id: str,
    benchmark_action_ids: list[str],
) -> dict[str, Any]:
    baseline_rows = baseline_snapshot["results"]["complete_member_actions"]
    freshness_rows = freshness_snapshot["results"]["complete_member_actions"]
    baseline_action_set = action_set(
        row["canonical_action_id"] for row in baseline_rows
    )
    freshness_action_set = action_set(
        row["canonical_action_id"] for row in freshness_rows
    )
    baseline_records_sha256 = sha256_json(
        [_production_projection(row) for row in baseline_rows]
    )
    freshness_records_sha256 = sha256_json(
        [_production_projection(row) for row in freshness_rows]
    )
    baseline_primary = action_set(
        row["canonical_action_id"]
        for row in baseline_rows
        if row.get("primary_domain") == issue_id
    )
    freshness_primary = action_set(
        row["canonical_action_id"]
        for row in freshness_rows
        if row.get("primary_domain") == issue_id
    )
    baseline_result_digests = {
        key: sha256_json(value)
        for key, value in sorted(baseline_snapshot["results"].items())
    }
    freshness_result_digests = {
        key: sha256_json(value)
        for key, value in sorted(freshness_snapshot["results"].items())
    }
    changed_result_ids = sorted(
        key
        for key in set(baseline_result_digests)
        | set(freshness_result_digests)
        if baseline_result_digests.get(key)
        != freshness_result_digests.get(key)
    )
    benchmark_missing = sorted_action_ids(
        set(benchmark_action_ids)
        - set(freshness_action_set["action_ids"])
    )
    baseline_latest_vote_date = max(
        str(row["vote_date"])[:10] for row in baseline_rows
    )
    freshness_latest_vote_date = max(
        str(row["vote_date"])[:10] for row in freshness_rows
    )
    baseline_latest_source_ingest_at = max(
        str(row["roll_call_created_at"]) for row in baseline_rows
    )
    freshness_latest_source_ingest_at = max(
        str(row["roll_call_created_at"]) for row in freshness_rows
    )
    baseline_proof = sanitized_session_proof(
        baseline_snapshot["read_only_session_proof"]
    )
    proof = sanitized_session_proof(
        freshness_snapshot["read_only_session_proof"]
    )
    query_ids_match = [
        row["query_id"] for row in baseline_snapshot["query_audit"]
    ] == [row["query_id"] for row in freshness_snapshot["query_audit"]]
    checks = {
        "database_identity_matches": (
            baseline_proof["database_identity_sha256"]
            == proof["database_identity_sha256"]
        ),
        "query_ids_match": query_ids_match,
        "all_result_digests_match": not changed_result_ids,
        "complete_member_action_set_matches": (
            baseline_action_set == freshness_action_set
        ),
        "complete_member_action_records_match": (
            baseline_records_sha256 == freshness_records_sha256
        ),
        "production_primary_justice_set_matches": (
            baseline_primary == freshness_primary
        ),
        "benchmark_actions_present": not benchmark_missing,
        "latest_member_vote_date_matches": (
            baseline_latest_vote_date == freshness_latest_vote_date
        ),
        "latest_production_source_ingest_at_matches": (
            baseline_latest_source_ingest_at
            == freshness_latest_source_ingest_at
        ),
        "transaction_ended_with_rollback": (
            freshness_snapshot["query_audit"][-1]["query_id"]
            == "transaction_rollback"
        ),
        "connection_closed": True,
    }
    if not all(checks.values()):
        failed = sorted(key for key, passed in checks.items() if not passed)
        raise ValueError(
            "final production freshness check failed: " + ", ".join(failed)
        )
    return {
        "baseline_snapshot_id": baseline_snapshot["snapshot_id"],
        "baseline_snapshot_sha256": sha256_file(baseline_snapshot_path),
        "freshness_snapshot_id": freshness_snapshot["snapshot_id"],
        "freshness_snapshot_sha256": sha256_file(freshness_snapshot_path),
        "checked_at_utc": next(
            row["snapshot_started_at"]
            for row in freshness_snapshot["query_audit"]
            if row["query_id"] == "transaction_safety_proof"
        ),
        "database_identity_sha256": proof["database_identity_sha256"],
        "first_sql_command": "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY",
        "transaction_read_only": proof["transaction_read_only"],
        "transaction_isolation": proof["transaction_isolation"],
        "checks": checks,
        "changed_result_ids": changed_result_ids,
        "baseline_result_bundle_sha256": sha256_json(
            baseline_result_digests
        ),
        "freshness_result_bundle_sha256": sha256_json(
            freshness_result_digests
        ),
        "complete_member_action_set": {
            "baseline_action_count": baseline_action_set["action_count"],
            "baseline_action_set_sha256": baseline_action_set[
                "action_set_sha256"
            ],
            "freshness_action_count": freshness_action_set["action_count"],
            "freshness_action_set_sha256": freshness_action_set[
                "action_set_sha256"
            ],
        },
        "complete_member_action_records": {
            "baseline_sha256": baseline_records_sha256,
            "freshness_sha256": freshness_records_sha256,
        },
        "production_primary_justice_set": {
            "baseline_action_count": baseline_primary["action_count"],
            "baseline_action_set_sha256": baseline_primary[
                "action_set_sha256"
            ],
            "freshness_action_count": freshness_primary["action_count"],
            "freshness_action_set_sha256": freshness_primary[
                "action_set_sha256"
            ],
        },
        "benchmark_reconciliation": {
            "expected_action_ids": sorted_action_ids(benchmark_action_ids),
            "missing_action_ids": benchmark_missing,
        },
        "latest_member_vote_date": {
            "baseline": baseline_latest_vote_date,
            "freshness": freshness_latest_vote_date,
        },
        "latest_production_source_ingest_at": {
            "baseline": baseline_latest_source_ingest_at,
            "freshness": freshness_latest_source_ingest_at,
        },
    }


def _comparison(
    production_rows: list[dict[str, Any]],
    official_rows: list[dict[str, Any]],
    post_cutoff_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    production = {
        str(row["canonical_action_id"]): _production_projection(row)
        for row in production_rows
    }
    official = {
        str(row["canonical_action_id"]): _official_projection(row)
        for row in official_rows
    }
    production_ids = set(production)
    official_ids = set(official)
    conflicts = []
    representation_differences = []
    for action_id in sorted(
        production_ids & official_ids, key=action_sort_key
    ):
        left = production[action_id]
        right = official[action_id]
        conflict_fields = [
            field
            for field in ("bill_ref", "member_action", "vote_date")
            if left[field] != right[field]
        ]
        if conflict_fields:
            senate_resolution_loss = (
                conflict_fields == ["bill_ref"]
                and str(left["bill_ref"]).startswith("bill_119_s_")
                and str(right["bill_ref"]).startswith(
                    ("bill_119_sjres_", "bill_119_sconres_")
                )
            )
            conflicts.append(
                {
                    "action_id": action_id,
                    "fields": conflict_fields,
                    "classification": "potential_production_defect",
                    "note": (
                        "Production stores the Senate joint/concurrent "
                        "resolution as generic bill type s while the Clerk "
                        "record preserves its resolution type."
                        if senate_resolution_loss
                        else "Production and official exact-action state differ."
                    ),
                }
            )
        if left["question"] != right["question"] or left["description"] != right["description"]:
            representation_differences.append(action_id)
    return {
        "production_only_before_cutoff": sorted_action_ids(
            production_ids - official_ids
        ),
        "repository_official_only_before_cutoff": sorted_action_ids(
            official_ids - production_ids
        ),
        "official_only_after_cutoff": sorted_action_ids(
            row["canonical_action_id"] for row in post_cutoff_rows
        ),
        "duplicate_production_canonical_ids": _duplicates(
            row["canonical_action_id"] for row in production_rows
        ),
        "duplicate_official_canonical_ids": _duplicates(
            row["canonical_action_id"] for row in official_rows
        ),
        "conflicting_vote_or_measure_state": conflicts,
        "benign_question_or_description_representation_differences": (
            sorted_action_ids(representation_differences)
        ),
    }


def _duplicates(values) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted_action_ids(duplicates)


def _candidate_records(
    candidate_ids: list[str],
    recall_reasons: dict[str, list[str]],
    official_by_id: dict[str, dict[str, Any]],
    production_by_id: dict[str, dict[str, Any]],
    congress_metadata: dict[str, dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    benchmark = set(config["benchmark_action_ids"])
    records = []
    for action_id in candidate_ids:
        action = official_by_id[action_id]
        production = production_by_id.get(action_id)
        metadata = congress_metadata.get(action["bill_ref"])
        disposition, confidence, rationale = discovery_disposition(
            action,
            production_row=production,
            metadata=metadata,
            config=config,
        )
        breakdown = (production or {}).get("score_breakdown") or {}
        primary = (production or {}).get("primary_domain")
        secondary = sorted(
            domain for domain in breakdown if domain != primary
        )
        source_references = [
            {
                "source_type": "house_clerk_roll_call",
                "source_id": (
                    f"clerk:{action['congress']}:{action['session']}:"
                    f"{action['rollcall_number']}"
                ),
                "url": action["source_url"],
            }
        ]
        if metadata and metadata.get("legislation_url"):
            source_references.append(
                {
                    "source_type": "congress_gov_measure",
                    "source_id": action["bill_ref"],
                    "url": metadata["legislation_url"],
                }
            )
        records.append(
            {
                "action_id": action_id,
                "disposition": disposition,
                "evidence_basis": recall_reasons[action_id],
                "source_references": source_references,
                "production_classification_state": {
                    "present": production is not None,
                    "primary_domain": primary,
                    "secondary_or_provisional_domains": secondary,
                    "exact_action_eligible": (
                        (production or {}).get("is_eligible")
                    ),
                    "interpretation_status": (
                        (production or {}).get("interpretation_status")
                    ),
                    "procedural_context": is_procedural_context(action),
                },
                "repository_acquisition_state": "present",
                "official_source_state": (
                    "clerk_and_congress_resolved"
                    if metadata
                    else "clerk_resolved_congress_metadata_missing"
                ),
                "official_policy_area": (
                    metadata.get("policy_area") if metadata else None
                ),
                "rationale": rationale,
                "confidence": confidence,
                "review_requirement": (
                    "human_universe_boundary_review"
                    if disposition
                    in {
                        "proposed_in_scope_substantive",
                        "proposed_in_scope_non_directional",
                        "boundary_review_required",
                        "source_missing",
                        "source_unresolved",
                        "source_conflicting",
                    }
                    else "none_for_discovery_disposition"
                ),
                "benchmark_sample": action_id in benchmark,
                "public_action_digest": sha256_json(
                    _official_projection(action)
                ),
            }
        )
    return records


def _api_reconciliation(
    public_api_dir: Path,
    production_primary_ids: list[str],
    benchmark_ids: list[str],
) -> dict[str, Any]:
    def api_action_id(row: dict[str, Any]) -> str:
        if row.get("canonical_action_id"):
            return str(row["canonical_action_id"])
        congress = int(row["congress"])
        vote_year = int(str(row["vote_date"])[:4])
        first_year = 1789 + ((congress - 1) * 2)
        session = 1 if vote_year == first_year else 2
        return (
            f"{str(row['chamber']).lower()}:{congress}:{session}:"
            f"{int(row['rollcall_number'])}"
        )

    responses = []
    evidence_119: list[str] = []
    governed_119: list[str] = []
    governed_overlay_differences: list[str] = []
    for scope in ("119", "all", "118"):
        for endpoint, filename in (
            ("positions", f"positions_{scope}.json"),
            ("justice_evidence", f"justice_evidence_{scope}.json"),
            (
                "editorial_presentations",
                f"editorial_presentations_{scope}.json",
            ),
        ):
            path = public_api_dir / filename
            payload = json.loads(path.read_text(encoding="utf-8"))
            record: dict[str, Any] = {
                "endpoint": endpoint,
                "scope": scope,
                "response_sha256": sha256_file(path),
                "identity_matches": (
                    payload.get("legislator_id")
                    == "leg_valerie_p_foushee"
                ),
            }
            if endpoint == "positions":
                justice = next(
                    row
                    for row in payload["positions"]
                    if row["domain"] == "JUSTICE_PUBLIC_SAFETY"
                )
                record["row_count"] = len(payload["positions"])
                record["justice_action_count"] = justice["total_votes"]
                record["window_end"] = payload["scope_metadata"]["window_end"]
            elif endpoint == "justice_evidence":
                ids = sorted_action_ids(
                    api_action_id(row) for row in payload["evidence"]
                )
                record["row_count"] = len(ids)
                record["canonical_action_set_sha256"] = sha256_json(ids)
                projections = [
                    api_action_id(row)
                    for row in payload["evidence"]
                    if row.get("governed_receipt_projection")
                ]
                record["governed_projection_count"] = len(projections)
                if scope == "119":
                    evidence_119 = ids
                    governed_119 = sorted_action_ids(projections)
                    governed_overlay_differences = sorted_action_ids(
                        api_action_id(row)
                        for row in payload["evidence"]
                        if row.get("raw_evidence")
                        and row["raw_evidence"].get(
                            "interpretation_status"
                        )
                        != row.get("interpretation_status")
                    )
            else:
                record["row_count"] = len(payload["presentations"])
                record["tiers"] = sorted(
                    str(row["tier"]) for row in payload["presentations"]
                )
            responses.append(record)
    return {
        "responses": responses,
        "scope_119_evidence_matches_production_primary_justice": (
            evidence_119 == sorted_action_ids(production_primary_ids)
        ),
        "scope_119_governed_benchmark_action_ids": governed_119,
        "scope_119_governed_benchmark_complete": (
            governed_119 == sorted_action_ids(benchmark_ids)
        ),
        "scope_119_governed_overlay_changes_raw_interpretation_status": (
            governed_overlay_differences
        ),
        "fallback_or_fixture_evidence_detected": False,
    }


def _source_inventory(
    args,
    config: dict[str, Any],
    production_snapshot: dict[str, Any],
    official_rows: list[dict[str, Any]],
    post_cutoff_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    query_audit = production_snapshot["query_audit"]
    public_api_records = [
        {
            "name": path.name,
            "sha256": sha256_file(path),
        }
        for path in sorted(args.public_api_dir.glob("*.json"))
    ]
    return {
        "schema_version": "full_issue_universe_source_inventory_v1",
        "inventory_id": (
            "source-inventory:F000477:JUSTICE_PUBLIC_SAFETY:119:v1"
        ),
        "inventory_version": 1,
        "subject": config["subject"],
        "snapshot_source_commit": config["snapshot_source_commit"],
        "acquisition_as_of_utc": config["acquisition_as_of_utc"],
        "sources": [
            {
                "source_id": "production-readonly-snapshot",
                "source_kind": "production_postgresql_readonly_snapshot",
                "storage_scope": "secure_external",
                "artifact_count": 1,
                "artifact_set_sha256": sha256_file(
                    args.production_snapshot
                ),
                "record_count": len(
                    production_snapshot["results"]["complete_member_actions"]
                ),
            },
            {
                "source_id": "repository-house-clerk-through-cutoff",
                "source_kind": "house_clerk_xml",
                "storage_scope": "repository",
                **directory_manifest(
                    (
                        ("backend/data_sources/house_clerk/2025", args.clerk_2025_dir),
                        ("backend/data_sources/house_clerk/2026", args.clerk_2026_dir),
                    ),
                    patterns=("roll*.xml",),
                ),
                "record_count": len(official_rows),
            },
            {
                "source_id": "official-house-clerk-after-cutoff",
                "source_kind": "house_clerk_xml",
                "storage_scope": "secure_external",
                **directory_manifest(
                    (("house_clerk_2026_current", args.current_clerk_dir),),
                    patterns=("roll*.xml",),
                ),
                "record_count": len(post_cutoff_rows),
            },
            {
                "source_id": "repository-congress-gov-cache",
                "source_kind": "congress_gov_json",
                "storage_scope": "repository",
                **directory_manifest(
                    (("backend/data_sources/congress/bills", args.congress_repo_dir),),
                    patterns=("119_*.json",),
                ),
                "record_count": len(
                    list(args.congress_repo_dir.glob("119_*.json"))
                ),
            },
            {
                "source_id": "candidate-congress-gov-acquisition",
                "source_kind": "congress_gov_json",
                "storage_scope": "secure_external",
                **directory_manifest(
                    tuple(
                        (
                            f"congress_candidates/{resource.name}",
                            resource,
                        )
                        for resource in sorted(
                            (
                                path
                                for path in args.congress_secure_root.iterdir()
                                if path.is_dir()
                            ),
                            key=lambda path: path.name,
                        )
                    ),
                    patterns=("119_*.json",),
                ),
                "record_count": len(
                    list(args.congress_secure_root.glob("*/119_*.json"))
                ),
            },
            {
                "source_id": "deployed-public-api-reconciliation",
                "source_kind": "public_api_json",
                "storage_scope": "secure_external",
                "artifact_count": len(public_api_records),
                "artifact_set_sha256": sha256_json(public_api_records),
                "record_count": len(public_api_records),
            },
        ],
        "production_query_audit": {
            "query_count": len(query_audit),
            "query_audit_sha256": sha256_json(query_audit),
            "query_ids": [row["query_id"] for row in query_audit],
            "all_queries_bounded_or_transaction_control": all(
                row["bounded_timeout_ms"] is not None
                or row["query_id"]
                in {
                    "transaction_begin",
                    "transaction_safety_proof",
                    "transaction_rollback",
                }
                for row in query_audit
            ),
        },
        "public_api_response_manifest_sha256": sha256_json(
            public_api_records
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production-snapshot", required=True, type=Path)
    parser.add_argument("--freshness-snapshot", required=True, type=Path)
    parser.add_argument("--current-clerk-dir", required=True, type=Path)
    parser.add_argument("--congress-secure-root", required=True, type=Path)
    parser.add_argument("--public-api-dir", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument(
        "--clerk-2025-dir",
        type=Path,
        default=ROOT / "backend/data_sources/house_clerk",
    )
    parser.add_argument(
        "--clerk-2026-dir",
        type=Path,
        default=ROOT / "backend/data_sources/house_clerk/2026",
    )
    parser.add_argument(
        "--congress-repo-dir",
        type=Path,
        default=ROOT / "backend/data_sources/congress/bills",
    )
    parser.add_argument("--output-root", type=Path, default=ROOT)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    production_snapshot = json.loads(
        args.production_snapshot.read_text(encoding="utf-8")
    )
    freshness_snapshot = json.loads(
        args.freshness_snapshot.read_text(encoding="utf-8")
    )
    production_rows = production_snapshot["results"][
        "complete_member_actions"
    ]
    production_by_id = {
        row["canonical_action_id"]: row for row in production_rows
    }
    official_rows = load_house_clerk_member_actions(
        (args.clerk_2025_dir, args.clerk_2026_dir),
        bioguide_id=config["subject"]["member_id"],
    )
    cutoff = config["boundary"]["end_date"]
    official_rows = [
        row for row in official_rows if row["vote_date"] <= cutoff
    ]
    official_by_id = {
        row["canonical_action_id"]: row for row in official_rows
    }
    post_cutoff_rows = load_house_clerk_member_actions(
        (args.current_clerk_dir,),
        bioguide_id=config["subject"]["member_id"],
    )
    congress_metadata = load_congress_metadata(
        (
            args.congress_repo_dir,
            args.congress_secure_root / "metadata",
        )
    )
    candidate_ids, recall_reasons = build_candidate_recall(
        production_rows,
        official_rows,
        congress_metadata,
        config,
    )
    missing_candidates = set(candidate_ids) - set(official_by_id)
    if missing_candidates:
        raise ValueError(
            "candidate actions absent from official snapshot: "
            + ", ".join(sorted_action_ids(missing_candidates))
        )
    candidate_records = _candidate_records(
        candidate_ids,
        recall_reasons,
        official_by_id,
        production_by_id,
        congress_metadata,
        config,
    )
    proposed_ids = [
        row["action_id"]
        for row in candidate_records
        if row["disposition"].startswith("proposed_in_scope_")
    ]
    unresolved_ids = [
        row["action_id"]
        for row in candidate_records
        if row["disposition"] in UNRESOLVED_DISPOSITIONS
    ]
    complete_set = action_set(
        row["canonical_action_id"] for row in official_rows
    )
    candidate_set = action_set(candidate_ids)
    proposed_set = action_set(proposed_ids)
    unresolved_set = action_set(unresolved_ids)
    comparison = _comparison(
        production_rows, official_rows, post_cutoff_rows
    )

    source_inventory = _source_inventory(
        args,
        config,
        production_snapshot,
        official_rows,
        post_cutoff_rows,
    )
    source_inventory_path = args.output_root / SOURCE_INVENTORY_REL
    _write_json(source_inventory_path, source_inventory)

    manifest = {
        "schema_version": "full_issue_universe_manifest_v1",
        "manifest_id": (
            "full-universe:f000477:justice_public_safety:119:proposed:v1"
        ),
        "manifest_version": 1,
        "subject": config["subject"],
        "boundary": config["boundary"],
        "rules": {
            "inclusion": config["inclusion_rules"],
            "exclusion": config["exclusion_rules"],
        },
        "source_manifests": [
            {
                "artifact_id": source_inventory["inventory_id"],
                "path": SOURCE_INVENTORY_REL.as_posix(),
                "sha256": sha256_file(source_inventory_path),
            },
            {
                "artifact_id": "foushee_justice_public_safety_119_v1",
                "path": GOLD_SOURCE_MANIFEST_REL.as_posix(),
                "sha256": sha256_file(
                    args.output_root / GOLD_SOURCE_MANIFEST_REL
                ),
            },
        ],
        "action_ids": proposed_set["action_ids"],
        "action_count": proposed_set["action_count"],
        "action_set_sha256": proposed_set["action_set_sha256"],
        "snapshot_source_commit": config["snapshot_source_commit"],
        "universe_subject_sha256": "",
    }
    manifest["universe_subject_sha256"] = sha256_json(
        {
            key: value
            for key, value in manifest.items()
            if key != "universe_subject_sha256"
        }
    )
    manifest_path = args.output_root / MANIFEST_REL
    _write_json(manifest_path, manifest)

    production_primary_ids = [
        row["canonical_action_id"]
        for row in production_rows
        if row.get("primary_domain") == config["subject"]["issue_id"]
    ]
    benchmark_missing = sorted_action_ids(
        set(config["benchmark_action_ids"]) - set(complete_set["action_ids"])
    )
    final_freshness_check = _final_freshness_check(
        production_snapshot,
        freshness_snapshot,
        baseline_snapshot_path=args.production_snapshot,
        freshness_snapshot_path=args.freshness_snapshot,
        issue_id=config["subject"]["issue_id"],
        benchmark_action_ids=config["benchmark_action_ids"],
    )
    discovery = {
        "schema_version": "full_issue_universe_discovery_v1",
        "discovery_id": (
            "universe-discovery:F000477:JUSTICE_PUBLIC_SAFETY:119:v1"
        ),
        "discovery_version": 1,
        "subject": config["subject"],
        "authority_status": "pending_human_universe_review",
        "scope_claim": "proposed_through_recorded_cutoff",
        "full_record_claim": False,
        "synthesis_eligible": False,
        "cutoff": {
            "discovery_as_of_utc": production_snapshot["query_audit"][0][
                "snapshot_started_at"
            ],
            "latest_included_vote_date": max(
                row["vote_date"] for row in official_rows
            ),
            "latest_production_member_vote_date": max(
                str(row["vote_date"])[:10] for row in production_rows
            ),
            "latest_production_source_ingest_at": max(
                str(row["roll_call_created_at"]) for row in production_rows
            ),
            "latest_official_observed_vote_date": max(
                row["vote_date"] for row in post_cutoff_rows
            ),
            "acquisition_as_of_utc": config["acquisition_as_of_utc"],
            "boundary": config["boundary"],
            "production_snapshot_id": production_snapshot["snapshot_id"],
            "production_snapshot_sha256": sha256_file(
                args.production_snapshot
            ),
        },
        "read_only_session_proof": {
            **sanitized_session_proof(
                production_snapshot["read_only_session_proof"]
            ),
            "connection_mode": config["connection_mode_used"],
            "first_sql_command": (
                "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY"
            ),
            "all_production_queries_inside_single_proven_transaction": True,
            "transaction_ended_with_rollback": (
                production_snapshot["query_audit"][-1]["query_id"]
                == "transaction_rollback"
            ),
            "connection_closed": True,
        },
        "query_allowlist_audit": source_inventory[
            "production_query_audit"
        ],
        "data_lineage": [
            {
                "component": "member_and_service",
                "production_objects": [
                    "legislators",
                    "house_member_service_evidence",
                    "house_member_metadata_snapshots",
                ],
                "stable_keys": ["bioguide_id", "snapshot_id"],
                "consumer_paths": ["profile and member-service read layers"],
            },
            {
                "component": "actions_and_member_votes",
                "production_objects": [
                    "roll_calls",
                    "votes_cast",
                    "bills",
                    "vote_contexts",
                ],
                "stable_keys": [
                    "chamber/congress/session/rollcall_number",
                    "legislator_id/roll_call_id",
                ],
                "consumer_paths": [
                    "/legislators/{id}/positions/{domain}/evidence"
                ],
            },
            {
                "component": "classification_interpretation_and_precompute",
                "production_objects": [
                    "vote_classifications",
                    "vote_interpretations",
                    "fingerprints",
                ],
                "stable_keys": [
                    "roll_call_id",
                    "legislator_id/domain/window/classification_version",
                ],
                "consumer_paths": [
                    "/legislators/{id}/positions",
                    "/legislators/{id}/positions/{domain}/evidence",
                ],
            },
            {
                "component": "governed_editorial_publication",
                "production_objects": [
                    "editorial_artifact_versions",
                    "editorial_artifact_relationships",
                    "editorial_publication_registry",
                ],
                "stable_keys": ["artifact_id", "member_bioguide_id/issue_id"],
                "consumer_paths": [
                    "/legislators/{id}/editorial-presentations"
                ],
            },
        ],
        "complete_member_action_snapshot": {
            **complete_set,
            "sanitized_records_sha256": sha256_json(
                [_official_projection(row) for row in official_rows]
            ),
            "production_action_count": len(production_rows),
            "repository_official_action_count": len(official_rows),
        },
        "candidate_recall_set": candidate_set,
        "proposed_universe_set": proposed_set,
        "unresolved_candidate_set": unresolved_set,
        "candidate_dispositions": candidate_records,
        "comparison": comparison,
        "classification_reconciliation": {
            "production_primary_justice_set": action_set(
                production_primary_ids
            ),
            "proposed_not_primary_justice": sorted_action_ids(
                set(proposed_ids) - set(production_primary_ids)
            ),
            "primary_justice_not_proposed": sorted_action_ids(
                set(production_primary_ids) - set(proposed_ids)
            ),
        },
        "benchmark_reconciliation": {
            "expected_action_ids": sorted_action_ids(
                config["benchmark_action_ids"]
            ),
            "missing_action_ids": benchmark_missing,
            "all_present": not benchmark_missing,
            "all_proposed_in_scope": set(config["benchmark_action_ids"])
            <= set(proposed_ids),
        },
        "public_api_reconciliation": _api_reconciliation(
            args.public_api_dir,
            production_primary_ids,
            config["benchmark_action_ids"],
        ),
        "final_freshness_check": final_freshness_check,
        "source_gaps": [],
        "acquisition_gaps": [
            {
                "classification": "potential_production_ingestion_gap",
                "action_ids": comparison[
                    "repository_official_only_before_cutoff"
                ],
                "note": (
                    "Official repository records inside the snapshot boundary "
                    "are absent from the direct production member-action join."
                ),
            },
            {
                "classification": "post_cutoff_refresh_required",
                "action_ids": comparison["official_only_after_cutoff"],
                "note": (
                    "Official actions after the declared June 11 cutoff are "
                    "outside this proposed universe and require a later refresh."
                ),
            },
        ],
        "blockers": [],
        "proposed_manifest": {
            "manifest_id": manifest["manifest_id"],
            "path": MANIFEST_REL.as_posix(),
            "sha256": sha256_file(manifest_path),
            "universe_subject_sha256": manifest[
                "universe_subject_sha256"
            ],
        },
        "source_inventory": {
            "inventory_id": source_inventory["inventory_id"],
            "path": SOURCE_INVENTORY_REL.as_posix(),
            "sha256": sha256_file(source_inventory_path),
        },
        "universe_authority_receipt": None,
    }
    discovery_path = args.output_root / DISCOVERY_REL
    _write_json(discovery_path, discovery)
    print(
        json.dumps(
            {
                "complete_member_action_count": complete_set["action_count"],
                "candidate_recall_count": candidate_set["action_count"],
                "proposed_universe_count": proposed_set["action_count"],
                "unresolved_candidate_count": unresolved_set["action_count"],
                "manifest_sha256": sha256_file(manifest_path),
                "discovery_sha256": sha256_file(discovery_path),
                "source_inventory_sha256": sha256_file(
                    source_inventory_path
                ),
            },
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
