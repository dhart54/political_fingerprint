from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BACKEND))

from app.etl.interpretation_source_readiness import (  # noqa: E402
    ALLOWED_INPUT_CLASSES,
    ALLOWED_SOURCE_TYPES,
    BLOCKER_PRECEDENCE,
    EXCLUDED_INPUT_CLASSES,
    FORBIDDEN_KEYS,
    SourceReadinessError,
    assert_no_semantic_leakage,
    canonical_file_sha256,
    load_json,
    sha256_json,
    validate_source_manifest,
)
from scripts.validate_full_issue_universe_authority import (  # noqa: E402
    validate_repository_authority,
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
ARTIFACT_PATH = (
    SOURCE_ROOT
    / "f000477_justice_public_safety_119_interpretation_source_readiness_v1.json"
)
SCHEMA_PATH = Path(
    "docs/methodology/full_issue_interpretation_source_readiness_v1.schema.json"
)
CURRENT_STATE_PATH = Path("docs/editorial/current_state_index.json")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceReadinessError(message)


def _require_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    _require(set(value) == expected, f"{label} fields are not closed")


def _strip_projection(source: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in source.items() if key != "canonical_projection"
    }


def _derive_blockers(criteria: dict[str, bool]) -> list[str]:
    blockers: list[str] = []
    if not criteria["stable_action_identity"] or not criteria["exact_action_identity"]:
        blockers.append("blocked_exact_action_identity")
    if (
        not criteria["vote_source_present"]
        or not criteria["exact_action_source_present"]
    ):
        blockers.append("blocked_missing_official_source")
    if not criteria["exact_action_not_parent_only"]:
        blockers.append("blocked_parent_only_source")
    if not criteria["text_version_explicit"]:
        blockers.append("blocked_wrong_text_version")
    if not criteria["all_source_digests_valid"]:
        blockers.append("blocked_source_digest")
    if not criteria["no_source_conflict"]:
        blockers.append("blocked_source_conflict")
    if not criteria["no_source_constraint"]:
        blockers.append("blocked_source_constraint")
    if not criteria["cross_domain_scope_complete"]:
        blockers.append("blocked_cross_domain_scope")
    if not criteria["no_semantic_leakage"]:
        blockers.append("blocked_semantic_leakage")
    return [code for code in BLOCKER_PRECEDENCE if code in blockers]


def validate_values(
    *,
    artifact: dict[str, Any],
    source_manifest: dict[str, Any],
    approved_manifest: dict[str, Any],
    authority: dict[str, Any],
    discovery: dict[str, Any],
    schema: dict[str, Any],
    current_state: dict[str, Any],
    repository_root: Path = ROOT,
) -> dict[str, Any]:
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema).iter_errors(artifact),
        key=lambda error: list(error.path),
    )
    if errors:
        raise SourceReadinessError(f"schema validation failed: {errors[0].message}")
    assert_no_semantic_leakage(artifact)
    _require(
        artifact["input_contract"]["allowlisted_input_classes"]
        == ALLOWED_INPUT_CLASSES,
        "input allowlist mismatch",
    )
    _require(
        artifact["input_contract"]["excluded_input_classes"] == EXCLUDED_INPUT_CLASSES,
        "excluded semantic input contract mismatch",
    )
    _require(
        not (
            set(artifact["input_contract"]["allowlisted_input_classes"])
            & set(EXCLUDED_INPUT_CLASSES)
        ),
        "excluded semantic input was allowlisted",
    )
    _require_keys(
        source_manifest,
        {
            "schema_version",
            "source_manifest_id",
            "allowlisted_source_types",
            "governed_roots",
            "subject",
            "source_manifest_subject_sha256",
        },
        "source manifest",
    )
    _require(
        source_manifest["allowlisted_source_types"] == sorted(ALLOWED_SOURCE_TYPES),
        "source type allowlist mismatch",
    )
    source_rows = validate_source_manifest(
        source_manifest,
        repository_root=repository_root,
        approved_manifest=approved_manifest,
        discovery=discovery,
    )
    subject = artifact["subject"]
    _require(
        subject["approved_manifest_id"] == approved_manifest["manifest_id"],
        "approved manifest ID mismatch",
    )
    _require(
        subject["approved_manifest_sha256"]
        == canonical_file_sha256(repository_root / MANIFEST_PATH),
        "approved manifest file digest mismatch",
    )
    _require(
        subject["universe_subject_sha256"]
        == approved_manifest["universe_subject_sha256"],
        "universe subject digest mismatch",
    )
    _require(
        subject["authority_receipt_id"] == authority["receipt_id"],
        "authority receipt ID mismatch",
    )
    _require(
        subject["authority_receipt_sha256"]
        == canonical_file_sha256(repository_root / AUTHORITY_PATH),
        "authority receipt file digest mismatch",
    )
    _require(
        subject["source_manifest_sha256"]
        == canonical_file_sha256(repository_root / SOURCE_MANIFEST_PATH),
        "official source manifest file digest mismatch",
    )
    _require(
        subject["action_ids"] == approved_manifest["action_ids"],
        "approved action list mismatch",
    )
    _require(
        sha256_json(sorted(subject["action_ids"]))
        == approved_manifest["action_set_sha256"]
        == subject["action_set_sha256"],
        "action-set digest mismatch",
    )
    records = subject["action_readiness"]
    ids = [record["action_id"] for record in records]
    _require(
        ids == approved_manifest["action_ids"],
        "readiness action order or membership mismatch",
    )
    _require(
        len(ids) == len(set(ids)) == 37,
        "readiness records are not exactly one per action",
    )
    candidates = {row["action_id"]: row for row in discovery["candidate_dispositions"]}
    expected_fisa_memberships = ["JUSTICE_PUBLIC_SAFETY", "NATIONAL_SECURITY"]
    expected_fisa_limits = [
        "surveillance_authority",
        "fisc_and_court_authority",
        "civil_liberty_protections",
    ]
    for record in records:
        action_id = record["action_id"]
        assert_no_semantic_leakage(record)
        source_row = source_rows[action_id]
        canonical = candidates[action_id]["exact_action_source_binding"]
        projection = source_row["vote_source"]["canonical_projection"]
        _require(
            record["official_action_date"] == projection["vote_date"],
            f"action date mismatch: {action_id}",
        )
        _require(
            record["official_member_action"] == projection["member_action"],
            f"member action mismatch: {action_id}",
        )
        _require(
            record["roll_number"] == projection["rollcall_number"],
            f"roll mismatch: {action_id}",
        )
        _require(
            record["session"] == projection["session"], f"session mismatch: {action_id}"
        )
        _require(
            record["exact_action_identity"]
            == canonical["exact_measure_or_amendment_identity"],
            f"exact identity mismatch: {action_id}",
        )
        _require(
            record["house_action_stage"] == canonical["house_action_stage"],
            f"House stage mismatch: {action_id}",
        )
        _require(
            record["vote_source_bindings"]
            == [_strip_projection(source_row["vote_source"])],
            f"vote/member-action evidence binding mismatch: {action_id}",
        )
        expected_exact = [
            _strip_projection(source) for source in source_row["exact_action_sources"]
        ]
        _require(
            record["exact_action_source_bindings"] == expected_exact,
            f"exact-action evidence binding mismatch: {action_id}",
        )
        parent_safe = all(
            source["source_subject"] in {record["exact_action_identity"], action_id}
            or record["house_action_stage"] not in {"amendment", "amendment_to_rule"}
            for source in expected_exact
        )
        fisa = action_id in {"house:119:2:155", "house:119:2:221"}
        expected_memberships = (
            expected_fisa_memberships if fisa else ["JUSTICE_PUBLIC_SAFETY"]
        )
        expected_limits = expected_fisa_limits if fisa else []
        _require(
            record["cross_domain_memberships"] == expected_memberships,
            f"cross-domain membership mismatch: {action_id}",
        )
        _require(
            record["cross_domain_scope_limitations"] == expected_limits,
            f"cross-domain scope mismatch: {action_id}",
        )
        criteria = {
            "approved_universe_member": action_id in approved_manifest["action_ids"],
            "stable_action_identity": bool(action_id),
            "official_member_action_resolved": record["official_member_action"]
            in {"yea", "nay", "present", "not_voting"},
            "exact_action_identity": bool(record["exact_action_identity"]),
            "house_stage_resolved": bool(record["house_action_stage"]),
            "vote_source_present": bool(record["vote_source_bindings"]),
            "exact_action_source_present": bool(record["exact_action_source_bindings"]),
            "exact_action_not_parent_only": parent_safe,
            "governed_source_exists": True,
            "text_version_explicit": all(
                bool(source["text_version"])
                for source in [
                    *record["vote_source_bindings"],
                    *record["exact_action_source_bindings"],
                ]
            ),
            "all_source_digests_valid": True,
            "no_source_conflict": record["source_conflict_state"] == "none",
            "no_source_constraint": record["source_constraint_state"] == "none",
            "all_paths_governed": True,
            "approved_source_types_only": all(
                source["source_type"] in ALLOWED_SOURCE_TYPES
                for source in [
                    *record["vote_source_bindings"],
                    *record["exact_action_source_bindings"],
                ]
            ),
            "cross_domain_scope_complete": record["cross_domain_memberships"]
            == expected_memberships
            and record["cross_domain_scope_limitations"] == expected_limits,
            "no_semantic_leakage": not (set(_walk_keys(record)) & FORBIDDEN_KEYS),
        }
        _require(
            record["readiness_criteria"] == criteria,
            f"derived readiness criteria mismatch: {action_id}",
        )
        blockers = _derive_blockers(criteria)
        _require(
            record["blocker_codes"] == blockers,
            f"derived blockers mismatch: {action_id}",
        )
        expected_state = blockers[0] if blockers else "ready"
        _require(
            record["readiness_state"] == expected_state,
            f"derived readiness state mismatch: {action_id}",
        )
        packet = {
            key: value for key, value in record.items() if key != "source_packet_sha256"
        }
        _require(
            sha256_json(packet) == record["source_packet_sha256"],
            f"source packet digest mismatch: {action_id}",
        )
    readiness_counts = Counter(record["readiness_state"] for record in records)
    blocker_counts = Counter(
        code for record in records for code in record["blocker_codes"]
    )
    expected_aggregate = {
        "total_action_count": len(records),
        "ready_count": readiness_counts["ready"],
        "blocked_count": len(records) - readiness_counts["ready"],
        "counts_by_readiness_state": dict(sorted(readiness_counts.items())),
        "counts_by_blocker": dict(sorted(blocker_counts.items())),
    }
    _require(
        subject["aggregate"] == expected_aggregate,
        "aggregate readiness accounting mismatch",
    )
    _require(
        artifact["result"]
        == (
            "complete_ready"
            if expected_aggregate["blocked_count"] == 0
            else "complete_blocked"
        ),
        "M2 result mismatch",
    )
    _require(
        sha256_json(subject) == artifact["source_readiness_subject_sha256"],
        "source-readiness subject digest mismatch",
    )
    current = current_state["full_record_issue_interpretation"]
    _require(
        current["f000477_justice_119_interpretation_source_readiness"]
        == artifact["result"],
        "current-state readiness mismatch",
    )
    _require(
        current["f000477_justice_119_action_interpretation_state"] == "not_started",
        "current state claims interpretation started",
    )
    _require(
        current["f000477_justice_119_policy_episode_state"] == "not_started",
        "current state claims episodes started",
    )
    _require(
        current["f000477_justice_119_full_record_semantic_ir"] == "absent",
        "current state claims full-record Semantic IR",
    )
    _require(
        current["f000477_justice_119_full_record_synthesis"] == "absent",
        "current state claims synthesis",
    )
    _require(
        current["f000477_justice_119_production_persistence"] == "not_authorized",
        "current state claims persistence authority",
    )
    _require(
        current["f000477_justice_119_publication_state"]
        == "unchanged_reviewed_benchmark_sample_active",
        "publication state changed",
    )
    return {
        **expected_aggregate,
        "artifact_sha256": canonical_file_sha256(repository_root / ARTIFACT_PATH),
    }


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def validate_repository(*, repository_root: Path = ROOT) -> dict[str, Any]:
    authority_result = validate_repository_authority(root=repository_root)
    result = validate_values(
        artifact=load_json(repository_root / ARTIFACT_PATH),
        source_manifest=load_json(repository_root / SOURCE_MANIFEST_PATH),
        approved_manifest=load_json(repository_root / MANIFEST_PATH),
        authority=load_json(repository_root / AUTHORITY_PATH),
        discovery=load_json(repository_root / DISCOVERY_PATH),
        schema=load_json(repository_root / SCHEMA_PATH),
        current_state=load_json(repository_root / CURRENT_STATE_PATH),
        repository_root=repository_root,
    )
    result["m1_authority_receipt_sha256"] = authority_result["receipt_file_sha256"]
    return result


def main() -> int:
    try:
        result = validate_repository()
    except (SourceReadinessError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "pass", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
