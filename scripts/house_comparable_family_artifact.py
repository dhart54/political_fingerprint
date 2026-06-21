from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from psycopg.rows import dict_row


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db import get_connection  # noqa: E402
from scripts.house_comparable_policy_question_audit import (  # noqa: E402
    assign_roll_calls,
    interpreted_roll_calls,
    scalar,
)


ARTIFACT_VERSION = "house-comparable-policy-question-families-v1"
SCHEMA_VERSION = "1.0"
SOURCE_AUDIT_JSON = REPO_ROOT / "docs" / "analysis" / "house_comparable_policy_question_families.json"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "derived" / "house_comparable_policy_question_families_v1.json"
EXPECTED_TOTALS = {
    "target_interpreted_roll_calls": 306,
    "candidate_families_identified": 15,
    "common_families_identified": 13,
    "directly_comparable_common_families": 4,
    "conditionally_comparable_common_families": 7,
    "related_but_non_comparable_clusters": 4,
    "ungrouped_roll_calls": 225,
    "substantive_vote_rows_in_candidate_families": 33825,
    "substantive_vote_rows_covered_share": 0.2659,
}
ELIGIBLE_STATUSES = {"directly_comparable", "conditionally_comparable"}
VALID_STATUSES = ELIGIBLE_STATUSES | {"related_but_not_comparable"}
FORBIDDEN_LABEL_FIELDS = ("movement_label", "changed_position", "ideological_movement_label", "behavioral_movement_label")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and validate the versioned House comparable-family derived artifact.")
    parser.add_argument("--source-audit", type=Path, default=SOURCE_AUDIT_JSON)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    source_audit = load_json(args.source_audit)
    with get_connection() as connection:
        connection.read_only = True
        connection.autocommit = False
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            classification_version = scalar(
                cursor,
                """
                SELECT classification_version
                FROM vote_classifications
                ORDER BY created_at DESC, classification_version DESC
                LIMIT 1
                """,
            )
            roll_calls = interpreted_roll_calls(cursor, classification_version)
            grouped_roll_calls, ungrouped_roll_calls = assign_roll_calls(roll_calls)
            read_only = scalar(cursor, "SHOW transaction_read_only")

    artifact = build_artifact(
        source_audit=source_audit,
        grouped_roll_calls=grouped_roll_calls,
        ungrouped_roll_calls=ungrouped_roll_calls,
        current_roll_calls=roll_calls,
        read_only=read_only,
        source_audit_commit=git_head(),
    )
    errors = validate_artifact(artifact, source_audit)
    if errors:
        raise SystemExit("Artifact validation failed:\n" + "\n".join(f"- {error}" for error in errors))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2, sort_keys=True, default=json_default) + "\n", encoding="utf-8")
    print(json.dumps({"artifact": str(args.output), "artifact_version": artifact["artifact_version"]}, indent=2))


def build_artifact(
    *,
    source_audit: dict[str, Any],
    grouped_roll_calls: dict[str, list[dict[str, Any]]],
    ungrouped_roll_calls: list[dict[str, Any]],
    current_roll_calls: list[dict[str, Any]],
    read_only: str,
    source_audit_commit: str,
) -> dict[str, Any]:
    family_summaries = source_audit["family_summaries"]
    families = [
        build_family(summary, grouped_roll_calls.get(summary["family_id"], []))
        for summary in sorted(family_summaries, key=lambda row: row["family_id"])
    ]
    ungrouped = build_ungrouped(ungrouped_roll_calls)
    totals = derived_totals(families, ungrouped, source_audit["coverage_analysis"])
    validation_summary = {
        "read_only_transaction": read_only,
        "production_writes_performed": False,
        "production_schema_changed": False,
        "frontend_runtime_changed": False,
        "source_audit_totals_reconciled": totals_match_expected(totals),
        "artifact_roll_call_ids_exist_in_current_evidence_universe": True,
        "cross_congress_leakage_found": False,
        "not_voting_remains_non_counting": True,
        "procedural_and_limited_evidence_remain_non_counting": True,
    }
    return {
        "artifact_version": ARTIFACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at": now_utc(),
        "source_basis": {
            "source_pull_request": 44,
            "source_audit_commit": source_audit_commit,
            "source_audit_generated_at": source_audit.get("generated_at"),
            "source_artifacts": [
                "docs/review_packets/house_comparable_policy_question_audit.md",
                "docs/analysis/house_comparable_policy_question_families.json",
                "docs/analysis/house_comparable_policy_question_thresholds.csv",
                "docs/analysis/house_comparable_policy_question_profiles.csv",
                "scripts/house_comparable_policy_question_audit.py",
                "backend/tests/test_house_comparable_policy_question_audit.py",
            ],
        },
        "scope": {
            "chamber": "house",
            "congresses": [118, 119],
            "domains": source_audit["analysis_scope"]["domains"],
            "existing_interpreted_evidence_only": True,
            "production_schema_artifact": False,
        },
        "methodology_summary": (
            "Versioned derived artifact promoted from PR #44's reviewed comparable policy-question audit. "
            "Families are review artifacts based on source-grounded roll-call, bill, interpretation, and vote-context fields. "
            "Shared broad issue domain, sponsor, parent bill alone, or political theme alone is not sufficient for membership."
        ),
        "recommendations": {
            "family_model_recommendation": source_audit["recommendations"]["family_model_recommendation"],
            "product_framing_recommendation": "Record Across Congresses",
            "continuity_change_readiness_recommendation": source_audit["recommendations"]["continuity_change_readiness"],
            "persistence_recommendation": "Versioned derived artifact outside the production schema.",
            "next_milestone_recommendation": "Build a read-only backend/internal accessor for the derived artifact.",
        },
        "explicit_non_authorization": {
            "does_not_authorize_continuity_change_claims": True,
            "does_not_authorize_behavioral_movement_claims": True,
            "does_not_authorize_ideological_movement_claims": True,
            "does_not_authorize_causal_claims": True,
            "does_not_authorize_frontend_comparison_copy": True,
            "statement": (
                "This artifact may mark future limited Record Across Congresses eligibility, but it must not generate "
                "continuity/change conclusions or labels saying an official changed position."
            ),
        },
        "totals": totals,
        "families": families,
        "ungrouped": ungrouped,
        "representative_profiles": source_audit.get("representative_profiles", []),
        "validation_summary": validation_summary,
        "current_evidence_universe": {
            "target_interpreted_roll_call_ids": sorted(int(row["roll_call_id"]) for row in current_roll_calls),
            "target_interpreted_roll_call_count": len(current_roll_calls),
        },
    }


def build_family(summary: dict[str, Any], roll_calls: list[dict[str, Any]]) -> dict[str, Any]:
    status = summary["review_status"]
    common = set(summary["congresses_represented"]) == {118, 119}
    eligible = status in ELIGIBLE_STATUSES and common
    roll_calls_by_congress = roll_call_entries_by_congress(roll_calls)
    return {
        "family_id": summary["family_id"],
        "family_name": summary["family_name"],
        "issue_domain": summary["domain"],
        "comparability_status": status,
        "eligible_for_future_limited_record_across_congresses": eligible,
        "governing_question": summary["governing_question"],
        "inclusion_criteria": summary["inclusion_criteria"],
        "exclusion_criteria": summary["exclusion_criteria"],
        "source_grounded_rationale": summary["source_grounded_rationale"],
        "caveats_and_limitations": summary["known_comparability_limitations"],
        "congresses_represented": summary["congresses_represented"],
        "vote_types_represented": summary["vote_types_represented"],
        "vote_type_distribution": summary["vote_type_distribution"],
        "measures_and_amendments_represented": summary["measures_and_amendments_represented"],
        "roll_call_ids_by_congress": {
            congress: [entry["roll_call_id"] for entry in entries]
            for congress, entries in roll_calls_by_congress.items()
        },
        "roll_calls_by_congress": roll_calls_by_congress,
        "representative_examples": summary.get("sample_roll_calls", [])[:4],
        "does_not_authorize_continuity_change_claims": True,
    }


def build_ungrouped(ungrouped_roll_calls: list[dict[str, Any]]) -> dict[str, Any]:
    roll_calls_by_congress = roll_call_entries_by_congress(ungrouped_roll_calls)
    return {
        "comparability_status": "ungrouped",
        "eligible_for_future_limited_record_across_congresses": False,
        "roll_call_count": len(ungrouped_roll_calls),
        "roll_call_ids_by_congress": {
            congress: [entry["roll_call_id"] for entry in entries]
            for congress, entries in roll_calls_by_congress.items()
        },
        "roll_calls_by_congress": roll_calls_by_congress,
        "exclusion_reason": "No reviewed deterministic PR #44 family rule matched; excluded from future comparison eligibility.",
        "does_not_authorize_continuity_change_claims": True,
    }


def roll_call_entries_by_congress(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_congress: dict[str, list[dict[str, Any]]] = {"118": [], "119": []}
    for row in rows:
        congress = str(row["congress"])
        by_congress.setdefault(congress, []).append(
            {
                "roll_call_id": int(row["roll_call_id"]),
                "chamber": "house",
                "congress": int(row["congress"]),
                "session": int(row["session"]) if row.get("session") is not None else None,
                "rollcall_number": int(row["rollcall_number"]),
                "vote_date": row.get("vote_date"),
                "vote_type": row.get("vote_type"),
                "bill": row.get("bill"),
                "bill_title": row.get("bill_title"),
                "amendment_identity_signal": row.get("amendment_identity_signal"),
            }
        )
    for entries in by_congress.values():
        entries.sort(key=lambda row: (row["congress"], row["session"] or 0, row["rollcall_number"], row["roll_call_id"]))
    return by_congress


def derived_totals(families: list[dict[str, Any]], ungrouped: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    direct_common = [family for family in families if family["comparability_status"] == "directly_comparable" and both_congresses(family)]
    conditional_common = [family for family in families if family["comparability_status"] == "conditionally_comparable" and both_congresses(family)]
    related = [family for family in families if family["comparability_status"] == "related_but_not_comparable"]
    return {
        "target_interpreted_roll_calls": coverage["target_interpreted_roll_calls"],
        "candidate_families_identified": len(families),
        "common_families_identified": sum(1 for family in families if both_congresses(family)),
        "directly_comparable_common_families": len(direct_common),
        "conditionally_comparable_common_families": len(conditional_common),
        "related_but_non_comparable_clusters": len(related),
        "ungrouped_roll_calls": ungrouped["roll_call_count"],
        "substantive_vote_rows_in_candidate_families": coverage["substantive_vote_rows_in_candidate_families"],
        "substantive_vote_rows_covered_share": coverage["substantive_vote_rows_covered_share"],
    }


def validate_artifact(artifact: dict[str, Any], source_audit: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []
    if artifact.get("artifact_version") != ARTIFACT_VERSION:
        errors.append("Unexpected artifact version.")
    if artifact.get("schema_version") != SCHEMA_VERSION:
        errors.append("Unexpected schema version.")
    if artifact.get("recommendations", {}).get("product_framing_recommendation") != "Record Across Congresses":
        errors.append("Product framing recommendation changed.")
    if not artifact.get("explicit_non_authorization", {}).get("does_not_authorize_continuity_change_claims"):
        errors.append("Missing explicit continuity/change non-authorization.")
    serialized = json.dumps(artifact, sort_keys=True, default=json_default).lower()
    for term in FORBIDDEN_LABEL_FIELDS:
        if term in serialized:
            errors.append(f"Forbidden movement field or label found: {term}")

    families = artifact.get("families", [])
    if len({family["family_id"] for family in families}) != len(families):
        errors.append("Family IDs are not unique.")
    for family in families:
        status = family.get("comparability_status")
        if status not in VALID_STATUSES:
            errors.append(f"Invalid family status for {family.get('family_id')}: {status}")
        if status in ELIGIBLE_STATUSES and not both_congresses(family):
            errors.append(f"Comparable family lacks both Congresses: {family.get('family_id')}")
        if status == "related_but_not_comparable" and family.get("eligible_for_future_limited_record_across_congresses"):
            errors.append(f"Related family is incorrectly eligible: {family.get('family_id')}")
        for congress, entries in family.get("roll_calls_by_congress", {}).items():
            for entry in entries:
                if str(entry.get("congress")) != str(congress):
                    errors.append(f"Cross-Congress leakage in {family.get('family_id')}: slot {congress}, row {entry}")
                if entry.get("chamber") != "house":
                    errors.append(f"Non-House roll call in {family.get('family_id')}: {entry}")
                if entry.get("session") is None or entry.get("rollcall_number") is None:
                    errors.append(f"Missing session-aware roll identity in {family.get('family_id')}: {entry}")

    ungrouped = artifact.get("ungrouped", {})
    if ungrouped.get("eligible_for_future_limited_record_across_congresses"):
        errors.append("Ungrouped rows are incorrectly eligible.")

    target_ids = set(artifact.get("current_evidence_universe", {}).get("target_interpreted_roll_call_ids", []))
    artifact_ids = artifact_roll_call_ids(artifact)
    missing = sorted(artifact_ids - target_ids)
    if missing:
        errors.append(f"Artifact roll-call IDs missing from current evidence universe: {missing[:10]}")
    if len(target_ids) != artifact["totals"]["target_interpreted_roll_calls"]:
        errors.append("Target universe count does not match artifact totals.")
    if target_ids != artifact_ids:
        errors.append("Grouped plus ungrouped roll-call IDs do not equal the target universe.")

    for key, expected in EXPECTED_TOTALS.items():
        actual = artifact["totals"].get(key)
        if actual != expected:
            errors.append(f"PR #44 total mismatch for {key}: expected {expected}, got {actual}")
    if source_audit is not None:
        source_ids = {family["family_id"] for family in source_audit.get("family_summaries", [])}
        artifact_family_ids = {family["family_id"] for family in families}
        if source_ids != artifact_family_ids:
            errors.append("Artifact family IDs differ from PR #44 source audit.")
    return errors


def artifact_roll_call_ids(artifact: dict[str, Any]) -> set[int]:
    ids: set[int] = set()
    for family in artifact.get("families", []):
        for entries in family.get("roll_calls_by_congress", {}).values():
            ids.update(int(entry["roll_call_id"]) for entry in entries)
    for entries in artifact.get("ungrouped", {}).get("roll_calls_by_congress", {}).values():
        ids.update(int(entry["roll_call_id"]) for entry in entries)
    return ids


def both_congresses(family: dict[str, Any]) -> bool:
    return bool(family.get("roll_call_ids_by_congress", {}).get("118")) and bool(
        family.get("roll_call_ids_by_congress", {}).get("119")
    )


def totals_match_expected(totals: dict[str, Any]) -> bool:
    return all(totals.get(key) == expected for key, expected in EXPECTED_TOTALS.items())


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_head() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def json_default(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


if __name__ == "__main__":
    main()
