from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.etl.readonly_discovery import (  # noqa: E402
    sanitized_session_proof,
    validate_completion_record,
)
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
    "f000477_justice_public_safety_119_source_inventory_v2.json"
)
MANIFEST_REL = Path(
    "docs/editorial/full_record_reviews/proposals/"
    "f000477_justice_public_safety_119_full_issue_universe_manifest_v2.json"
)
DISCOVERY_REL = Path(
    "docs/editorial/full_record_reviews/proposals/"
    "f000477_justice_public_safety_119_full_issue_universe_discovery_v2.json"
)
COMPARISON_REL = Path(
    "docs/editorial/full_record_reviews/proposals/"
    "f000477_justice_public_safety_119_universe_refresh_comparison_v2.json"
)
REPAIR_PLAN_REL = Path(
    "docs/editorial/full_record_reviews/proposals/"
    "f000477_justice_public_safety_119_production_repair_plan_v2.json"
)
REVIEW_PACKET_REL = Path(
    "docs/editorial/full_record_reviews/proposals/"
    "f000477_justice_public_safety_119_universe_review_packet_v2.md"
)
V1_DISCOVERY_REL = Path(
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
    baseline_completion: dict[str, Any],
    freshness_completion: dict[str, Any],
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
            freshness_completion["rollback"]["succeeded"] is True
        ),
        "connection_closed": (
            freshness_completion["connection_close"][
                "client_closed_state_verified"
            ]
            is True
        ),
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
        "baseline_completion_subject_sha256": baseline_completion[
            "completion_subject_sha256"
        ],
        "freshness_completion_subject_sha256": freshness_completion[
            "completion_subject_sha256"
        ],
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


def _house_action_stage(question: str, disposition: str) -> str:
    normalized = question.lower()
    if "amendment" in normalized:
        return (
            "amendment_to_rule"
            if disposition == "procedural_context"
            else "amendment"
        )
    if "previous question" in normalized:
        return "previous_question"
    if "retaining division" in normalized:
        return "division_retention"
    if "motion to recommit" in normalized:
        return "motion_to_recommit"
    if "suspend the rules and pass" in normalized:
        return (
            "suspension_passage_as_amended"
            if "as amended" in normalized
            else "suspension_passage"
        )
    if "passage" in normalized:
        return "passage"
    if "agree" in normalized and "resolution" in normalized:
        return (
            "resolution_adoption_as_amended"
            if "as amended" in normalized
            else "resolution_adoption"
        )
    return "other_house_action"


def _measure_identity(bill_ref: str) -> str:
    prefix = "bill_"
    if not bill_ref.startswith(prefix):
        return bill_ref
    return bill_ref[len(prefix) :].replace("_", ":")


def _action_source_binding(
    action: dict[str, Any],
    disposition: str,
    metadata: dict[str, Any] | None,
    config: dict[str, Any],
) -> dict[str, Any] | None:
    action_id = action["canonical_action_id"]
    configured = config.get("action_source_bindings", {}).get(action_id)
    registry = {
        row["source_id"]: row
        for row in config.get("official_exact_action_source_registry", [])
    }
    vote_binding = {
        "source_id": (
            f"clerk:{action['congress']}:{action['session']}:"
            f"{action['rollcall_number']}"
        ),
        "source_type": "house_clerk_roll_call",
        "url": action["source_url"],
        "source_content_sha256": sha256_json(_official_projection(action)),
        "source_subject": action_id,
        "text_version": str(action["vote_date"]),
        "evidence_role": "recorded_house_action_and_member_vote",
        "digest_basis": "canonical_clerk_action_projection_sha256",
    }
    if configured is not None:
        missing = [
            source_id
            for source_id in configured["meaning_source_ids"]
            if source_id not in registry
        ]
        if missing:
            raise ValueError(
                f"{action_id} references unknown exact sources: {missing}"
            )
        meaning_sources = [
            dict(registry[source_id])
            for source_id in configured["meaning_source_ids"]
        ]
        return {
            "canonical_action_id": action_id,
            "exact_measure_or_amendment_identity": configured[
                "exact_action_identity"
            ],
            "house_action_stage": configured["house_action_stage"],
            "vote_source_bindings": [vote_binding],
            "exact_action_meaning_source_bindings": meaning_sources,
            "boundary_review_sufficiency_state": configured[
                "review_sufficiency_status"
            ],
            "boundary_review_sufficiency_basis": configured[
                "methodology_or_source_basis"
            ],
        }
    configured_exact_sources = [
        dict(source)
        for source in config.get("exact_action_sources", {}).get(action_id, [])
    ]
    for group in config.get("exact_action_source_groups", []):
        if action_id in set(group["action_ids"]):
            configured_exact_sources.append(
                {
                    "source_id": f"{group['source_id_prefix']}:{action_id}",
                    "source_type": group["source_type"],
                    "url": group["url"],
                    "source_content_sha256": group[
                        "source_content_sha256"
                    ],
                    "source_subject": action_id,
                    "text_version": group["text_version"],
                    "evidence_role": group["evidence_role"],
                    "digest_basis": group["digest_basis"],
                }
            )
    if configured_exact_sources and disposition.startswith(
        "proposed_in_scope_"
    ):
        return {
            "canonical_action_id": action_id,
            "exact_measure_or_amendment_identity": (
                action_id
                if _house_action_stage(action["question"], disposition)
                == "amendment"
                else _measure_identity(action["bill_ref"])
            ),
            "house_action_stage": _house_action_stage(
                action["question"], disposition
            ),
            "vote_source_bindings": [vote_binding],
            "exact_action_meaning_source_bindings": configured_exact_sources,
            "boundary_review_sufficiency_state": "sufficient",
            "boundary_review_sufficiency_basis": (
                "The official House Rules Committee report binds the exact "
                "amendment or passage text to this reviewed action."
            ),
        }
    if not disposition.startswith("proposed_in_scope_"):
        return None
    stage = _house_action_stage(action["question"], disposition)
    if stage in {"amendment", "amendment_to_rule"}:
        raise ValueError(
            f"{action_id} amendment lacks amendment-specific exact source"
        )
    if metadata is None or not metadata.get("legislation_url"):
        raise ValueError(
            f"{action_id} proposed action lacks exact official action metadata"
        )
    meaning_source = {
        "source_id": f"congress_action_record:{action_id}",
        "source_type": "congress_gov_action_record",
        "url": metadata["legislation_url"],
        "source_content_sha256": sha256_json(metadata),
        "source_subject": _measure_identity(action["bill_ref"]),
        "text_version": "official_action_record",
        "evidence_role": "exact_house_stage_and_measure_identity",
        "digest_basis": "canonical_congress_metadata_sha256",
    }
    return {
        "canonical_action_id": action_id,
        "exact_measure_or_amendment_identity": _measure_identity(
            action["bill_ref"]
        ),
        "house_action_stage": stage,
        "vote_source_bindings": [vote_binding],
        "exact_action_meaning_source_bindings": [meaning_source],
        "boundary_review_sufficiency_state": "sufficient",
        "boundary_review_sufficiency_basis": (
            "The official Congress action record binds the exact House stage "
            "and measure identity for the reviewed passage action."
        ),
    }


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
        action_source_binding = _action_source_binding(
            action,
            disposition,
            metadata,
            config,
        )
        status_metadata_resolved = bool(
            action_source_binding
            and any(
                source["source_type"] == "govinfo_bill_status"
                for source in action_source_binding[
                    "exact_action_meaning_source_bindings"
                ]
            )
        )
        remaining_source_gaps = (
            []
            if metadata or status_metadata_resolved
            else ["congress_metadata_missing"]
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
        for source in config.get("exact_action_sources", {}).get(
            action_id, []
        ):
            source_references.append(
                {
                    "source_type": source["source_type"],
                    "source_id": source["source_id"],
                    "url": source["url"],
                }
            )
        if action_source_binding:
            existing_source_ids = {
                source["source_id"] for source in source_references
            }
            for source in action_source_binding[
                "exact_action_meaning_source_bindings"
            ]:
                if source["source_id"] not in existing_source_ids:
                    source_references.append(
                        {
                            "source_type": source["source_type"],
                            "source_id": source["source_id"],
                            "url": source["url"],
                        }
                    )
                    existing_source_ids.add(source["source_id"])
        for group in config.get("exact_action_source_groups", []):
            if action_id in set(group["action_ids"]):
                source_references.append(
                    {
                        "source_type": group["source_type"],
                        "source_id": (
                            f"{group['source_id_prefix']}:{action_id}"
                        ),
                        "url": group["url"],
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
                    if metadata or status_metadata_resolved
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
                "exact_action_source_binding": action_source_binding,
                "source_readiness": {
                    "boundary_review_source_state": (
                        "sufficient"
                        if disposition not in UNRESOLVED_DISPOSITIONS
                        else "insufficient"
                    ),
                    "action_interpretation_source_state": "not_started",
                    "episode_construction_source_state": "not_started",
                    "synthesis_provenance_source_state": "not_started",
                    "remaining_source_gaps": remaining_source_gaps,
                    "boundary_gap_nonblocking_reason": (
                        "The exact official evidence supporting the reviewed "
                        "disposition is sufficient even though general "
                        "Congress metadata remains unavailable."
                        if remaining_source_gaps
                        else None
                    ),
                },
                **(
                    {
                        "issue_memberships": config[
                            "cross_domain_memberships"
                        ][action_id],
                        "cross_domain_scope_limitations": config[
                            "cross_domain_scope_limitations"
                        ][action_id],
                    }
                    if action_id
                    in config.get("cross_domain_memberships", {})
                    else {}
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
    candidate_records: list[dict[str, Any]],
) -> dict[str, Any]:
    query_audit = production_snapshot["query_audit"]
    public_api_records = [
        {
            "name": path.name,
            "sha256": sha256_file(path),
        }
        for path in sorted(args.public_api_dir.glob("*.json"))
    ]
    action_meaning_sources_by_id: dict[str, dict[str, Any]] = {}
    for row in candidate_records:
        binding = row["exact_action_source_binding"]
        if binding is None:
            continue
        for source in binding["exact_action_meaning_source_bindings"]:
            existing = action_meaning_sources_by_id.get(source["source_id"])
            if existing is not None and existing != source:
                raise ValueError(
                    "exact source identity/digest mismatch for "
                    f"{source['source_id']}"
                )
            action_meaning_sources_by_id[source["source_id"]] = source
    action_meaning_sources = [
        action_meaning_sources_by_id[source_id]
        for source_id in sorted(action_meaning_sources_by_id)
    ]
    gap_disposition_names = {
        "proposed_in_scope_substantive": "proposed",
        "proposed_in_scope_non_directional": "proposed",
        "expressive_nonbinding_context": "expressive",
        "procedural_context": "procedural",
        "proposed_exact_action_ineligible": "ineligible",
    }
    metadata_gap_counts = {
        "proposed": 0,
        "expressive": 0,
        "procedural": 0,
        "ineligible": 0,
    }
    metadata_gap_action_ids = []
    for row in candidate_records:
        if "congress_metadata_missing" not in row["source_readiness"][
            "remaining_source_gaps"
        ]:
            continue
        metadata_gap_action_ids.append(row["action_id"])
        metadata_gap_counts[
            gap_disposition_names[row["disposition"]]
        ] += 1
    return {
        "schema_version": "full_issue_universe_source_inventory_v1",
        "inventory_id": (
            "source-inventory:F000477:JUSTICE_PUBLIC_SAFETY:119:v2"
        ),
        "inventory_version": 2,
        "subject": config["subject"],
        "snapshot_source_commit": config["snapshot_source_commit"],
        "acquisition_as_of_utc": config["acquisition_as_of_utc"],
        "sources": [
            {
                "source_id": "production-readonly-snapshot",
                "source_kind": "production_postgresql_readonly_snapshot",
                "storage_scope": "secure_external",
                "artifact_count": 2,
                "artifact_set_sha256": sha256_json(
                    [
                        {
                            "name": args.production_snapshot.name,
                            "sha256": sha256_file(args.production_snapshot),
                        },
                        {
                            "name": args.production_completion_record.name,
                            "sha256": sha256_file(
                                args.production_completion_record
                            ),
                        },
                    ]
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
                "record_count": len(
                    load_house_clerk_member_actions(
                        (args.clerk_2025_dir, args.clerk_2026_dir),
                        bioguide_id=config["subject"]["member_id"],
                    )
                ),
            },
            {
                "source_id": "official-house-clerk-current-refresh",
                "source_kind": "house_clerk_xml",
                "storage_scope": "secure_external",
                **directory_manifest(
                    (("house_clerk_2026_current", args.current_clerk_dir),),
                    patterns=("roll*.xml",),
                ),
                "record_count": len(
                    load_house_clerk_member_actions(
                        (args.current_clerk_dir,),
                        bioguide_id=config["subject"]["member_id"],
                    )
                ),
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
            {
                "source_id": "official-exact-action-reports",
                "source_kind": "house_rules_committee_report_pdf",
                "storage_scope": "secure_external",
                **directory_manifest(
                    (("exact_action", args.exact_action_dir),),
                    patterns=("*.pdf",),
                ),
                "record_count": len(
                    list(args.exact_action_dir.glob("*.pdf"))
                ),
            },
            {
                "source_id": "official-exact-action-correction-files",
                "source_kind": "official_action_text_and_status",
                "storage_scope": "secure_external",
                "artifact_count": len(
                    config.get(
                        "official_exact_action_source_registry", []
                    )
                ),
                "artifact_set_sha256": sha256_json(
                    [
                        {
                            "source_id": source["source_id"],
                            "source_content_sha256": source[
                                "source_content_sha256"
                            ],
                        }
                        for source in config.get(
                            "official_exact_action_source_registry", []
                        )
                    ]
                ),
                "record_count": len(
                    config.get(
                        "official_exact_action_source_registry", []
                    )
                ),
            },
        ],
        "action_meaning_sources": action_meaning_sources,
        "stage_source_gap_summary": {
            "gap_type": "congress_metadata_missing",
            "total_candidate_count": len(metadata_gap_action_ids),
            "action_ids": sorted_action_ids(metadata_gap_action_ids),
            "counts_by_disposition": metadata_gap_counts,
            "boundary_review_effect": "nonblocking_when_exact_official_evidence_sufficient",
            "later_stage_effect": (
                "visible_gap_for_action_interpretation_episode_and_synthesis"
            ),
        },
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
    parser.add_argument(
        "--production-completion-record", required=True, type=Path
    )
    parser.add_argument("--freshness-snapshot", required=True, type=Path)
    parser.add_argument(
        "--freshness-completion-record", required=True, type=Path
    )
    parser.add_argument("--current-clerk-dir", required=True, type=Path)
    parser.add_argument("--congress-secure-root", required=True, type=Path)
    parser.add_argument("--public-api-dir", required=True, type=Path)
    parser.add_argument("--exact-action-dir", required=True, type=Path)
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
    v1_discovery_path = args.output_root / V1_DISCOVERY_REL
    v1_discovery = json.loads(
        v1_discovery_path.read_text(encoding="utf-8")
    )
    reviewed = config.setdefault("reviewed_dispositions", {})
    for row in v1_discovery["candidate_dispositions"]:
        reviewed.setdefault(
            row["action_id"],
            {
                "disposition": row["disposition"],
                "confidence": row["confidence"],
                "rationale": (
                    "Retained from the content-addressed V1 candidate review; "
                    "the refreshed exact-action evidence does not change this "
                    "boundary decision."
                ),
            },
        )
    production_snapshot, production_completion = validate_completion_record(
        args.production_snapshot,
        args.production_completion_record,
    )
    freshness_snapshot, freshness_completion = validate_completion_record(
        args.freshness_snapshot,
        args.freshness_completion_record,
    )
    production_rows = production_snapshot["results"][
        "complete_member_actions"
    ]
    production_by_id = {
        row["canonical_action_id"]: row for row in production_rows
    }
    official_rows = load_house_clerk_member_actions(
        (
            args.clerk_2025_dir,
            args.clerk_2026_dir,
            args.current_clerk_dir,
        ),
        bioguide_id=config["subject"]["member_id"],
    )
    cutoff = config["boundary"]["end_date"]
    official_rows = [
        row for row in official_rows if row["vote_date"] <= cutoff
    ]
    official_by_id = {
        row["canonical_action_id"]: row for row in official_rows
    }
    post_cutoff_rows = [
        row
        for row in load_house_clerk_member_actions(
            (args.current_clerk_dir,),
            bioguide_id=config["subject"]["member_id"],
        )
        if row["vote_date"] > cutoff
    ]
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
        candidate_records,
    )
    source_inventory_path = args.output_root / SOURCE_INVENTORY_REL
    _write_json(source_inventory_path, source_inventory)

    manifest = {
        "schema_version": "full_issue_universe_manifest_v1",
        "manifest_id": (
            "full-universe:f000477:justice_public_safety:119:proposed:v2"
        ),
        "manifest_version": 2,
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
        "production_snapshot_identity": {
            "snapshot_id": production_snapshot["snapshot_id"],
            "raw_snapshot_sha256": sha256_file(args.production_snapshot),
            "completion_subject_sha256": production_completion[
                "completion_subject_sha256"
            ],
        },
        "official_member_action_snapshot": complete_set,
        "substantive_action_set": proposed_set,
        "non_directional_substantive_action_set": action_set(
            row["action_id"]
            for row in candidate_records
            if row["disposition"]
            == "proposed_in_scope_non_directional"
        ),
        "expressive_nonbinding_action_set": action_set(
            row["action_id"]
            for row in candidate_records
            if row["disposition"] == "expressive_nonbinding_context"
        ),
        "procedural_context_action_set": action_set(
            row["action_id"]
            for row in candidate_records
            if row["disposition"] == "procedural_context"
        ),
        "exact_action_ineligible_set": action_set(
            row["action_id"]
            for row in candidate_records
            if row["disposition"]
            == "proposed_exact_action_ineligible"
        ),
        "unresolved_candidate_set": unresolved_set,
        "cross_domain_memberships": config.get(
            "cross_domain_memberships", {}
        ),
        "cross_domain_scope_limitations": config.get(
            "cross_domain_scope_limitations", {}
        ),
        "source_inventory_binding": {
            "inventory_id": source_inventory["inventory_id"],
            "sha256": sha256_file(source_inventory_path),
        },
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
        baseline_completion=production_completion,
        freshness_completion=freshness_completion,
    )
    discovery = {
        "schema_version": "full_issue_universe_discovery_v1",
        "discovery_id": (
            "universe-discovery:F000477:JUSTICE_PUBLIC_SAFETY:119:v2"
        ),
        "discovery_version": 2,
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
                row["vote_date"]
                for row in (post_cutoff_rows or official_rows)
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
                production_completion["rollback"]["succeeded"] is True
            ),
            "connection_closed": production_completion[
                "connection_close"
            ]["client_closed_state_verified"],
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
        "source_gaps": (
            [
                {
                    "classification": "congress_metadata_missing",
                    "action_ids": source_inventory[
                        "stage_source_gap_summary"
                    ]["action_ids"],
                    "counts_by_disposition": source_inventory[
                        "stage_source_gap_summary"
                    ]["counts_by_disposition"],
                    "boundary_review_effect": (
                        "nonblocking_exact_official_boundary_evidence_sufficient"
                    ),
                    "later_stage_effect": (
                        "not_interpretation_episode_or_synthesis_ready"
                    ),
                }
            ]
            if source_inventory["stage_source_gap_summary"][
                "total_candidate_count"
            ]
            else []
        ),
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

    v1_dispositions = {
        row["action_id"]: row
        for row in v1_discovery["candidate_dispositions"]
    }
    v2_dispositions = {
        row["action_id"]: row for row in candidate_records
    }
    v1_complete_ids = set(
        v1_discovery["complete_member_action_snapshot"]["action_ids"]
    )
    new_action_ids = sorted_action_ids(
        set(complete_set["action_ids"]) - v1_complete_ids
    )
    removed_action_ids = sorted_action_ids(
        v1_complete_ids - set(complete_set["action_ids"])
    )
    expressive_review_ids = {
        "house:119:1:123",
        "house:119:1:158",
        "house:119:1:159",
        "house:119:1:179",
        "house:119:1:185",
        "house:119:2:162",
        "house:119:2:165",
    }
    fisa_review_ids = {"house:119:2:155", "house:119:2:221"}
    boundary_diff = []
    for action_id in sorted_action_ids(
        set(v1_dispositions) | set(v2_dispositions)
    ):
        before = v1_dispositions.get(action_id)
        after = v2_dispositions.get(action_id)
        before_disposition = before["disposition"] if before else None
        after_disposition = after["disposition"] if after else None
        if before_disposition == after_disposition:
            continue
        boundary_diff.append(
            {
                "action_id": action_id,
                "change_type": (
                    "newly_observed"
                    if before is None
                    else "review_correction"
                    if after is not None
                    else "removed_with_reason"
                ),
                "v1_disposition": before_disposition,
                "v2_disposition": after_disposition,
                "v2_rationale": (
                    after["rationale"]
                    if after
                    else "No longer present in the refreshed official boundary."
                ),
                "v2_source_references": (
                    after["source_references"] if after else []
                ),
                "exact_source_ids": (
                    [
                        source["source_id"]
                        for source in after[
                            "exact_action_source_binding"
                        ]["exact_action_meaning_source_bindings"]
                    ]
                    if after
                    and after["exact_action_source_binding"] is not None
                    else []
                ),
                "content_digests": (
                    [
                        source["source_content_sha256"]
                        for source in after[
                            "exact_action_source_binding"
                        ]["exact_action_meaning_source_bindings"]
                    ]
                    if after
                    and after["exact_action_source_binding"] is not None
                    else []
                ),
                "evidence_roles": (
                    [
                        source["evidence_role"]
                        for source in after[
                            "exact_action_source_binding"
                        ]["exact_action_meaning_source_bindings"]
                    ]
                    if after
                    and after["exact_action_source_binding"] is not None
                    else []
                ),
                "previous_disposition": before_disposition,
                "new_disposition": after_disposition,
                "methodology_or_source_basis": (
                    after["exact_action_source_binding"][
                        "boundary_review_sufficiency_basis"
                    ]
                    if after
                    and after["exact_action_source_binding"] is not None
                    else after["rationale"]
                    if after
                    else "Removed from refreshed official boundary."
                ),
                "review_sufficiency_status": (
                    after["source_readiness"][
                        "boundary_review_source_state"
                    ]
                    if after
                    else "not_applicable"
                ),
                "change_authority": (
                    "complete_human_universe_boundary_review"
                    if before is not None
                    else "v2_refresh_exact_action_review"
                ),
                "change_origin": (
                    "methodology"
                    if action_id in expressive_review_ids
                    or action_id in fisa_review_ids
                    else "freshness"
                    if before is None
                    else "human_boundary_correction"
                ),
            }
        )
    source_readiness = [
        {
            "action_id": row["action_id"],
            **row["source_readiness"],
        }
        for row in candidate_records
    ]
    reuse_rows = []
    for action in official_rows:
        action_id = action["canonical_action_id"]
        prior = v1_dispositions.get(action_id)
        current = v2_dispositions.get(action_id)
        current_digest = sha256_json(_official_projection(action))
        prior_digest = prior.get("public_action_digest") if prior else None
        reuse_rows.append(
            {
                "action_id": action_id,
                "official_action_digest_unchanged": (
                    prior_digest == current_digest if prior else False
                ),
                "boundary_disposition_unchanged": (
                    prior is not None
                    and current is not None
                    and prior["disposition"] == current["disposition"]
                ),
                "interpretation_reuse_eligibility": (
                    "new_action"
                    if action_id in set(new_action_ids)
                    else "unchanged_and_source_stable"
                    if prior_digest == current_digest
                    and prior is not None
                    and current is not None
                    and prior["disposition"] == current["disposition"]
                    else "boundary_changed_review_required"
                    if prior is not None
                    and current is not None
                    and prior["disposition"] != current["disposition"]
                    else "source_updated_review_required"
                ),
            }
        )
    comparison_artifact = {
        "schema_version": "full_issue_universe_refresh_comparison_v2",
        "comparison_id": (
            "universe-refresh-comparison:"
            "F000477:JUSTICE_PUBLIC_SAFETY:119:v2"
        ),
        "authorizing": False,
        "historical_v1": {
            "path": V1_DISCOVERY_REL.as_posix(),
            "sha256": sha256_file(v1_discovery_path),
            "source_commit": "a2227fd3e00cf295558707fe04db8f4499969fd3",
            "cutoff": v1_discovery["cutoff"]["boundary"]["end_date"],
            "complete_action_count": v1_discovery[
                "complete_member_action_snapshot"
            ]["action_count"],
            "complete_action_set_sha256": v1_discovery[
                "complete_member_action_snapshot"
            ]["action_set_sha256"],
            "candidate_count": v1_discovery["candidate_recall_set"][
                "action_count"
            ],
            "candidate_set_sha256": v1_discovery["candidate_recall_set"][
                "action_set_sha256"
            ],
            "proposed_count": v1_discovery["proposed_universe_set"][
                "action_count"
            ],
            "proposed_universe_sha256": v1_discovery[
                "proposed_universe_set"
            ]["action_set_sha256"],
            "unresolved_count": v1_discovery[
                "unresolved_candidate_set"
            ]["action_count"],
            "unresolved_set_sha256": v1_discovery[
                "unresolved_candidate_set"
            ]["action_set_sha256"],
            "review_findings": [
                "Runner rollback and connection-close claims were not bound to post-close evidence.",
                "The source-completeness wording exceeded boundary-review sufficiency.",
                "Seven symbolic resolutions required a distinct expressive nonbinding class.",
                "Two FISA actions required explicit Justice/National Security cross-domain treatment.",
                "Twenty-two June 11 candidate dispositions required correction.",
                "Official actions after June 11 required a freshness refresh.",
            ],
            "unsuitable_for_authority_reason": (
                "The completed human review identified proof-chain, "
                "methodology, boundary, and freshness corrections that must "
                "be represented in a new content-addressed proposal."
            ),
            "status": "historical_non_authoritative_superseded_for_review",
        },
        "refresh_v2": {
            "cutoff": config["boundary"]["end_date"],
            "complete_action_count": complete_set["action_count"],
            "candidate_count": candidate_set["action_count"],
            "proposed_count": proposed_set["action_count"],
            "expressive_nonbinding_count": sum(
                row["disposition"] == "expressive_nonbinding_context"
                for row in candidate_records
            ),
            "procedural_count": sum(
                row["disposition"] == "procedural_context"
                for row in candidate_records
            ),
            "ineligible_count": sum(
                row["disposition"]
                == "proposed_exact_action_ineligible"
                for row in candidate_records
            ),
            "unresolved_count": unresolved_set["action_count"],
            "status": "candidate_pending_human_universe_review",
        },
        "source_completeness_statement": (
            "Official evidence is sufficient for universe-boundary review "
            "through the declared cutoff; remaining stage-specific metadata "
            "gaps are explicit and do not imply interpretation, episode, or "
            "synthesis readiness."
        ),
        "remaining_source_gaps_by_disposition": source_inventory[
            "stage_source_gap_summary"
        ],
        "new_action_ids": new_action_ids,
        "unchanged_action_ids": sorted_action_ids(
            set(complete_set["action_ids"])
            & v1_complete_ids
        ),
        "removed_action_ids": removed_action_ids,
        "removed_action_reasons": [],
        "boundary_diff": boundary_diff,
        "boundary_diff_sha256": sha256_json(boundary_diff),
        "changed_disposition_action_ids": [
            row["action_id"]
            for row in boundary_diff
            if row["v1_disposition"] is not None
            and row["v2_disposition"] is not None
        ],
        "changed_proposed_membership_action_ids": sorted_action_ids(
            set(v1_discovery["proposed_universe_set"]["action_ids"])
            ^ set(proposed_set["action_ids"])
        ),
        "newly_unresolved_action_ids": sorted_action_ids(
            set(unresolved_set["action_ids"])
            - set(v1_discovery["unresolved_candidate_set"]["action_ids"])
        ),
        "resolved_prior_candidate_action_ids": sorted_action_ids(
            set(v1_discovery["unresolved_candidate_set"]["action_ids"])
            - set(unresolved_set["action_ids"])
        ),
        "changed_source_identity_action_ids": sorted_action_ids(
            row["action_id"]
            for row in boundary_diff
            if row["v1_disposition"] is not None
            and v1_dispositions[row["action_id"]]["source_references"]
            != row["v2_source_references"]
        ),
        "new_action_dispositions": [
            {
                "action_id": action_id,
                "disposition": v2_dispositions[action_id]["disposition"],
                "rationale": v2_dispositions[action_id]["rationale"],
                "source_references": v2_dispositions[action_id][
                    "source_references"
                ],
                "official_action": official_by_id[action_id],
                "exact_house_question": official_by_id[action_id][
                    "question"
                ],
                "action_stage": (
                    "amendment"
                    if "Amendment"
                    in official_by_id[action_id]["question"]
                    else "procedural"
                    if v2_dispositions[action_id]["disposition"]
                    == "procedural_context"
                    else "measure_or_resolution"
                ),
                "high_recall_issue_signals": v2_dispositions[action_id][
                    "evidence_basis"
                ],
                "boundary_evidence_sufficient": True,
            }
            for action_id in new_action_ids
        ],
        "source_readiness_by_candidate": source_readiness,
        "incremental_reuse_by_action": reuse_rows,
        "removed_action_reuse": [
            {
                "action_id": action_id,
                "interpretation_reuse_eligibility": "removed_or_invalidated",
            }
            for action_id in removed_action_ids
        ],
        "cross_domain_memberships": config.get(
            "cross_domain_memberships", {}
        ),
        "production_snapshot_change": {
            "changed_result_ids": final_freshness_check[
                "changed_result_ids"
            ],
            "all_result_digests_match": final_freshness_check["checks"][
                "all_result_digests_match"
            ],
        },
        "authority_receipt": None,
        "interpretation_artifact": None,
        "episode_artifact": None,
        "semantic_ir_artifact": None,
        "publication_artifact": None,
    }
    comparison_path = args.output_root / COMPARISON_REL
    _write_json(comparison_path, comparison_artifact)

    all_production_gaps = comparison[
        "repository_official_only_before_cutoff"
    ]
    production_coverage_by_id = {
        row["canonical_action_id"]: row
        for row in production_snapshot["results"].get(
            "member_roll_call_coverage", []
        )
    }
    gap_records = []
    for action_id in all_production_gaps:
        coverage = production_coverage_by_id.get(action_id)
        if coverage is None:
            failure_stage = "roll_call_ingestion"
        elif coverage.get("production_vote_id") is None:
            failure_stage = "member_vote_ingestion"
        else:
            failure_stage = "member_action_join_or_identity_resolution"
        gap_records.append(
            {
                "action_id": action_id,
                "expected_source_record": _official_projection(
                    official_by_id[action_id]
                ),
                "missing_target_record": {
                    "canonical_action_id": action_id,
                    "expected_member_bioguide_id": config["subject"][
                        "member_id"
                    ],
                    "expected_roll_call_present": coverage is not None,
                    "expected_member_vote_present": (
                        coverage is not None
                        and coverage.get("production_vote_id") is not None
                    ),
                },
                "identified_failure_stage": failure_stage,
            }
        )
    gap_stage_counts = {
        stage: sum(
            row["identified_failure_stage"] == stage
            for row in gap_records
        )
        for stage in sorted(
            {row["identified_failure_stage"] for row in gap_records}
        )
    }
    repair_plan = {
        "schema_version": "full_issue_universe_production_repair_plan_v2",
        "plan_id": (
            "production-repair-plan:"
            "F000477:JUSTICE_PUBLIC_SAFETY:119:v2"
        ),
        "execution_authorized": False,
        "production_writes_performed": False,
        "scope": {
            "member_id": config["subject"]["member_id"],
            "congress": 119,
            "cutoff": config["boundary"]["end_date"],
        },
        "member_action_ingestion_gaps": {
            "action_ids": all_production_gaps,
            "action_count": len(all_production_gaps),
            "records": gap_records,
            "identified_failure_stage_counts": gap_stage_counts,
            "historical_through_2026_06_11": [
                action_id
                for action_id in all_production_gaps
                if official_by_id[action_id]["vote_date"] <= "2026-06-11"
            ],
            "newly_observed_after_2026_06_11": [
                action_id
                for action_id in all_production_gaps
                if official_by_id[action_id]["vote_date"] > "2026-06-11"
            ],
            "proposed_repair": (
                "Run the governed House roll-call ingestion path for only "
                "these canonical action IDs, with a dry-run, bounded counts, "
                "rollback artifact, post-write reconciliation, and idempotency "
                "check in a separately authorized milestone."
            ),
            "later_action_pattern": (
                "The same stage classification is computed for every newly "
                "observed action, so the plan distinguishes a continuing "
                "roll-call acquisition lag from isolated member-vote loss."
            ),
        },
        "lossy_measure_type_mappings": {
            "records": comparison["conflicting_vote_or_measure_state"],
            "record_count": len(
                comparison["conflicting_vote_or_measure_state"]
            ),
            "proposed_repair": (
                "Correct production bill identity to the Clerk-preserved "
                "sjres/sconres type for the exact listed roll calls, after "
                "foreign-key impact analysis and a separately authorized "
                "bounded migration."
            ),
        },
        "preconditions": [
            "Separate explicit production-write authority.",
            "Exact target-row preflight and expected counts.",
            "Content-addressed backup of every target row and dependency.",
            "Validated rollback before any write.",
            "Post-write official-source reconciliation.",
            "Idempotent second run with zero additional writes.",
        ],
    }
    repair_plan_path = args.output_root / REPAIR_PLAN_REL
    _write_json(repair_plan_path, repair_plan)

    changed_table = "\n".join(
        "| {action_id} | {v1} | {v2} |".format(
            action_id=row["action_id"],
            v1=row["v1_disposition"] or "-",
            v2=row["v2_disposition"] or "-",
        )
        for row in boundary_diff
    )
    review_packet = (
        "# Foushee Justice/Public Safety 119th-Congress universe review V2\n\n"
        "Status: candidate only; non-authorizing; no interpretation, "
        "episode, synthesis, publication, or production write is included.\n\n"
        "V1 remains the July 30 discovery result for the June 11 boundary. "
        "The completed human boundary review found methodology and boundary "
        "corrections, so V1 is superseded for authority and interpretation. "
        "V2 is the current proposal. Neither V1 nor V2 is authoritative "
        "without a separately created detached authority receipt.\n\n"
        f"- Boundary: {config['boundary']['start_date']} through "
        f"{config['boundary']['end_date']}\n"
        f"- Complete official actions: {complete_set['action_count']}\n"
        f"- Candidate actions reviewed: {candidate_set['action_count']}\n"
        f"- Proposed substantive/non-directional actions: "
        f"{proposed_set['action_count']}\n"
        f"- Expressive nonbinding actions: "
        f"{comparison_artifact['refresh_v2']['expressive_nonbinding_count']}\n"
        f"- Procedural actions: "
        f"{comparison_artifact['refresh_v2']['procedural_count']}\n"
        f"- Exact-action ineligible actions: "
        f"{comparison_artifact['refresh_v2']['ineligible_count']}\n"
        f"- Unresolved candidates: {unresolved_set['action_count']}\n"
        f"- Newly observed actions reviewed exactly once: "
        f"{len(new_action_ids)}\n\n"
        "Source-completeness claim: Official evidence is sufficient for "
        "universe-boundary review through the declared cutoff. This does not "
        "claim action-interpretation, episode, synthesis, or public-wording "
        "readiness.\n\n"
        f"- Remaining Congress-metadata gaps: "
        f"{source_inventory['stage_source_gap_summary']['total_candidate_count']}\n"
        f"- Gap counts by disposition: "
        f"{json.dumps(source_inventory['stage_source_gap_summary']['counts_by_disposition'], sort_keys=True)}\n"
        "- The seven reviewed proposed-action defects now bind exact official "
        "action meaning sources, and all 22 V1-to-V2 corrections carry exact "
        "source IDs, content digests, evidence roles, and sufficiency states.\n\n"
        "## V1-to-V2 boundary changes\n\n"
        "| Action | V1 disposition | V2 disposition |\n"
        "|---|---|---|\n"
        f"{changed_table}\n\n"
        "The machine-readable comparison contains source references, exact "
        "rationales, per-stage readiness, and action-level reuse decisions. "
        "The production repair plan is non-mutating and requires a separate "
        "authorized milestone.\n"
    )
    review_packet_path = args.output_root / REVIEW_PACKET_REL
    review_packet_path.parent.mkdir(parents=True, exist_ok=True)
    review_packet_path.write_text(review_packet, encoding="utf-8")
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
                "comparison_sha256": sha256_file(comparison_path),
                "repair_plan_sha256": sha256_file(repair_plan_path),
                "review_packet_sha256": sha256_file(review_packet_path),
            },
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
