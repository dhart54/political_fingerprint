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
    GOVERNED_ROOTS,
    IDENTITY_STAGE_CONTENT_CLASSES,
    M3_ELIGIBLE_SOURCE_TYPES,
    OPERATIVE_CONTENT_CLASSES,
    RAW_PROVENANCE_ONLY_SOURCE_TYPES,
    SourceReadinessError,
    canonical_file_sha256,
    load_json,
    sha256_file,
    sha256_json,
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
SOURCE_MANIFEST_SCHEMA_PATH = Path(
    "docs/methodology/full_issue_interpretation_official_source_manifest_v1.schema.json"
)
SCHEMA_PATH = Path(
    "docs/methodology/full_issue_interpretation_source_readiness_v1.schema.json"
)
CURRENT_STATE_PATH = Path("docs/editorial/current_state_index.json")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceReadinessError(message)


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _resolve_path(relative: str, *, repository_root: Path) -> Path:
    _require(
        any(relative.startswith(root) for root in GOVERNED_ROOTS),
        "source path escapes governed root",
    )
    path = (repository_root / relative).resolve()
    root = repository_root.resolve()
    _require(root in path.parents, "source path escapes repository")
    _require(path.is_file(), "governed source file is missing")
    return path


def _find_exact_action_description(
    payload: dict[str, Any],
    *,
    action_date: str,
    roll_number: int,
    stage: str,
) -> str | None:
    results: list[str] = []
    for item in payload.get("actions", []):
        if item.get("actionDate") != action_date:
            continue
        if item.get("sourceSystem", {}).get("name") != "House floor actions":
            continue
        text = str(item.get("text") or "")
        lowered = text.casefold()
        if f"roll no. {roll_number}" not in lowered:
            continue
        if stage == "suspension_passage_as_amended":
            correct = (
                "suspend the rules and pass" in lowered and "as amended" in lowered
            )
        elif stage == "suspension_passage":
            correct = (
                "suspend the rules and pass" in lowered and "as amended" not in lowered
            )
        else:
            correct = "on passage passed" in lowered
        if correct:
            results.append(text)
    return results[0] if len(results) == 1 else None


def _projection_is_closed_and_neutral(projection: dict[str, Any]) -> bool:
    expected = {
        "schema_version",
        "action_id",
        "congress",
        "chamber",
        "measure_identity",
        "house_action_stage",
        "action_date",
        "roll_number",
        "member_action",
        "official_action_description",
        "text_version",
        "source_url",
        "raw_provenance_sha256",
        "operative_content_sha256",
    }
    return set(projection) == expected and not (
        set(_walk_keys(projection)) & FORBIDDEN_KEYS
    )


def _inspect_manifest_row(
    row: dict[str, Any],
    *,
    canonical: dict[str, Any],
    repository_root: Path,
) -> tuple[dict[str, Any], dict[str, bool], dict[str, dict[str, Any]]]:
    action_id = row["action_id"]
    sources = {source["source_id"]: source for source in row["sources"]}
    _require(len(sources) == len(row["sources"]), f"duplicate source: {action_id}")
    role_sources: dict[str, list[dict[str, Any]]] = {}
    digest_valid = True
    path_valid = True
    type_valid = True
    projection_valid = True
    for source in row["sources"]:
        source_type = source["source_type"]
        type_valid = type_valid and source_type in ALLOWED_SOURCE_TYPES
        projection = source["neutral_projection"]
        if source["m3_input_eligible"]:
            type_valid = type_valid and source_type in M3_ELIGIBLE_SOURCE_TYPES
            projection_valid = projection_valid and isinstance(projection, dict)
            if isinstance(projection, dict):
                projection_valid = (
                    projection_valid
                    and _projection_is_closed_and_neutral(projection)
                    and sha256_json(projection) == source["neutral_projection_sha256"]
                    and projection["action_id"] == action_id
                    and projection["measure_identity"]
                    == canonical["exact_measure_or_amendment_identity"]
                    and projection["house_action_stage"]
                    == canonical["house_action_stage"]
                )
        else:
            projection_valid = projection_valid and projection is None
        raw = source["raw_provenance"]
        if raw is not None:
            try:
                path = _resolve_path(
                    raw["governed_local_path"], repository_root=repository_root
                )
            except SourceReadinessError:
                path_valid = False
                digest_valid = False
                continue
            raw_digest = sha256_file(path)
            digest_valid = digest_valid and raw_digest == raw["sha256"]
            if projection is not None:
                digest_valid = (
                    digest_valid and projection["raw_provenance_sha256"] == raw_digest
                )
            content_class = source["content_class"]
            if content_class == "operative_legislative_text":
                payload = path.read_bytes()
                mechanism = (
                    path.suffix.casefold() == ".xml"
                    and b"<legis-body" in payload
                    and b"</legis-body>" in payload
                )
                digest_valid = (
                    digest_valid
                    and mechanism
                    and projection["operative_content_sha256"] == raw_digest
                )
                stage = canonical["house_action_stage"]
                version = source["text_version"]
                if stage == "suspension_passage_as_amended":
                    projection_valid = projection_valid and version == "eh"
                elif stage in {"passage", "suspension_passage"}:
                    projection_valid = projection_valid and version in {
                        "eh",
                        "enr",
                        "cdh",
                        "es",
                    }
            elif content_class == "exact_amendment_or_rule_text":
                digest_valid = (
                    digest_valid
                    and path.suffix.casefold() == ".pdf"
                    and path.read_bytes().startswith(b"%PDF")
                    and projection["operative_content_sha256"] == raw_digest
                )
            elif content_class == "exact_house_action_record":
                raw_payload = load_json(path)
                description = _find_exact_action_description(
                    raw_payload,
                    action_date=projection["action_date"],
                    roll_number=projection["roll_number"],
                    stage=projection["house_action_stage"],
                )
                projection_valid = (
                    projection_valid
                    and description is not None
                    and description == projection["official_action_description"]
                )
        elif source["content_class"] != "member_action_record":
            path_valid = False
    for role, ids in row["role_bindings"].items():
        _require(len(ids) == len(set(ids)), f"duplicate role source: {action_id}")
        _require(all(source_id in sources for source_id in ids), "unknown role source")
        role_sources[role] = [sources[source_id] for source_id in ids]
    member = role_sources["member_action_evidence"]
    identity = role_sources["exact_action_identity_and_stage_evidence"]
    operative = role_sources["operative_content_interpretation_input"]
    _require(
        all(source["content_class"] == "member_action_record" for source in member),
        "non-member source used as member-action evidence",
    )
    _require(
        all(
            source["content_class"] in IDENTITY_STAGE_CONTENT_CLASSES
            for source in identity
        ),
        "source-role escalation into identity/stage evidence",
    )
    _require(
        all(
            source["content_class"] in OPERATIVE_CONTENT_CLASSES for source in operative
        ),
        "identity-only source represented as operative content",
    )
    raw_only_valid = True
    for source in row["raw_provenance_only_sources"]:
        raw_only_valid = (
            raw_only_valid
            and source["source_type"] in RAW_PROVENANCE_ONLY_SOURCE_TYPES
            and not source["m3_input_eligible"]
        )
        path = _resolve_path(
            source["raw_provenance"]["governed_local_path"],
            repository_root=repository_root,
        )
        raw_only_valid = (
            raw_only_valid and sha256_file(path) == source["raw_provenance"]["sha256"]
        )
    all_role_sources = [*member, *identity, *operative]
    identities = {
        (
            source["neutral_projection"]["measure_identity"],
            source["neutral_projection"]["house_action_stage"],
            source["neutral_projection"]["action_date"],
        )
        for source in [*identity, *operative]
        if source["neutral_projection"] is not None
    }
    conflict = len(identities) > 1
    constrained = any(source["constraint_codes"] for source in all_role_sources)
    raw_count = sum(source["raw_provenance"] is not None for source in all_role_sources)
    raw_state = (
        "complete"
        if raw_count == len(all_role_sources)
        else "partial"
        if raw_count
        else "projection_only"
    )
    state = {
        "member_action_evidence_state": "available" if member else "missing",
        "identity_and_stage_source_state": "available" if identity else "missing",
        "operative_content_source_state": "available" if operative else "missing",
        "neutral_m3_projection_state": ("available" if projection_valid else "missing"),
        "raw_provenance_state": raw_state,
        "source_availability_state": (
            "available"
            if member and identity and operative and projection_valid
            else "missing"
        ),
        "source_conflict_state": "conflicting" if conflict else "none",
        "source_constraint_state": "blocked" if constrained else "none",
    }
    criteria = {
        "vote_source_present": bool(member),
        "exact_action_source_present": bool(identity),
        "operative_content_source_present": bool(operative),
        "governed_source_exists": path_valid,
        "text_version_explicit": all(
            bool(source["text_version"]) for source in all_role_sources
        ),
        "all_source_digests_valid": digest_valid
        and projection_valid
        and raw_only_valid,
        "no_source_conflict": not conflict,
        "no_source_constraint": not constrained,
        "all_paths_governed": path_valid,
        "approved_source_types_only": type_valid,
    }
    return state, criteria, sources


def _derive_blockers(criteria: dict[str, bool]) -> list[str]:
    blockers: list[str] = []
    if not criteria["stable_action_identity"] or not criteria["exact_action_identity"]:
        blockers.append("blocked_exact_action_identity")
    if (
        not criteria["vote_source_present"]
        or not criteria["exact_action_source_present"]
    ):
        blockers.append("blocked_missing_official_source")
    if not criteria["operative_content_source_present"]:
        blockers.append("blocked_missing_operative_content_source")
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


def _artifact_binding(source: dict[str, Any]) -> dict[str, Any]:
    raw = source["raw_provenance"]
    return {
        "source_id": source["source_id"],
        "source_type": source["source_type"],
        "source_subject": source["source_subject"],
        "content_class": source["content_class"],
        "text_version": source["text_version"],
        "raw_provenance_sha256": raw["sha256"] if raw else None,
        "neutral_projection_sha256": source["neutral_projection_sha256"],
        "m3_input_eligible": source["m3_input_eligible"],
    }


def validate_values(
    *,
    artifact: dict[str, Any],
    source_manifest: dict[str, Any],
    approved_manifest: dict[str, Any],
    authority: dict[str, Any],
    discovery: dict[str, Any],
    schema: dict[str, Any],
    source_manifest_schema: dict[str, Any],
    current_state: dict[str, Any],
    repository_root: Path = ROOT,
) -> dict[str, Any]:
    for contract, value, label in (
        (source_manifest_schema, source_manifest, "source manifest"),
        (schema, artifact, "readiness artifact"),
    ):
        Draft7Validator.check_schema(contract)
        errors = sorted(
            Draft7Validator(contract).iter_errors(value),
            key=lambda error: list(error.path),
        )
        _require(
            not errors, f"{label} schema failed: {errors[0].message if errors else ''}"
        )
    _require(
        source_manifest["allowlisted_source_types"] == sorted(ALLOWED_SOURCE_TYPES),
        "source allowlist mismatch",
    )
    _require(
        source_manifest["m3_eligible_source_types"] == sorted(M3_ELIGIBLE_SOURCE_TYPES),
        "M3 source allowlist mismatch",
    )
    _require(
        sha256_json(source_manifest["subject"])
        == source_manifest["source_manifest_subject_sha256"],
        "source manifest subject digest mismatch",
    )
    subject = artifact["subject"]
    _require(
        artifact["input_contract"]["allowlisted_input_classes"]
        == ALLOWED_INPUT_CLASSES,
        "input allowlist mismatch",
    )
    _require(
        artifact["input_contract"]["excluded_input_classes"] == EXCLUDED_INPUT_CLASSES,
        "excluded input contract mismatch",
    )
    _require(
        subject["approved_manifest_id"] == approved_manifest["manifest_id"]
        and subject["approved_manifest_sha256"]
        == canonical_file_sha256(
            repository_root / MANIFEST_PATH, text_line_endings="crlf"
        ),
        "approved manifest binding mismatch",
    )
    _require(
        subject["authority_receipt_id"] == authority["receipt_id"]
        and subject["authority_receipt_sha256"]
        == canonical_file_sha256(
            repository_root / AUTHORITY_PATH, text_line_endings="crlf"
        ),
        "authority receipt binding mismatch",
    )
    _require(
        subject["universe_subject_sha256"]
        == approved_manifest["universe_subject_sha256"],
        "universe subject mismatch",
    )
    _require(
        subject["source_manifest_sha256"]
        == canonical_file_sha256(
            repository_root / SOURCE_MANIFEST_PATH, text_line_endings="lf"
        ),
        "source manifest file digest mismatch",
    )
    _require(
        subject["action_ids"] == approved_manifest["action_ids"]
        and subject["action_set_sha256"]
        == approved_manifest["action_set_sha256"]
        == sha256_json(sorted(subject["action_ids"])),
        "action-set binding mismatch",
    )
    source_rows = {
        row["action_id"]: row for row in source_manifest["subject"]["action_sources"]
    }
    _require(
        list(source_rows) == approved_manifest["action_ids"] and len(source_rows) == 37,
        "source manifest action membership mismatch",
    )
    candidates = {row["action_id"]: row for row in discovery["candidate_dispositions"]}
    records = subject["action_readiness"]
    _require(
        [record["action_id"] for record in records] == approved_manifest["action_ids"]
        and len({record["action_id"] for record in records}) == 37,
        "readiness action membership mismatch",
    )
    expected_fisa_memberships = ["JUSTICE_PUBLIC_SAFETY", "NATIONAL_SECURITY"]
    expected_fisa_limits = [
        "surveillance_authority",
        "fisc_and_court_authority",
        "civil_liberty_protections",
    ]
    for record in records:
        action_id = record["action_id"]
        canonical = candidates[action_id]["exact_action_source_binding"]
        manifest_row = source_rows[action_id]
        state, source_criteria, sources = _inspect_manifest_row(
            manifest_row,
            canonical=canonical,
            repository_root=repository_root,
        )
        _require(record["source_state"] == state, f"asserted source state: {action_id}")
        expected_bindings = {
            role: [_artifact_binding(sources[source_id]) for source_id in ids]
            for role, ids in manifest_row["role_bindings"].items()
        }
        _require(
            record["role_source_bindings"] == expected_bindings,
            f"role binding mismatch: {action_id}",
        )
        expected_raw_only = [
            {
                "source_id": source["source_id"],
                "source_type": source["source_type"],
                "source_subject": source["source_subject"],
                "raw_provenance_sha256": source["raw_provenance"]["sha256"],
                "m3_input_eligible": False,
                "exclusion_reason": source["exclusion_reason"],
            }
            for source in manifest_row["raw_provenance_only_sources"]
        ]
        _require(
            record["raw_provenance_only_bindings"] == expected_raw_only,
            f"raw-only provenance binding mismatch: {action_id}",
        )
        member_ids = manifest_row["role_bindings"]["member_action_evidence"]
        _require(len(member_ids) == 1, f"member source count mismatch: {action_id}")
        member_projection = sources[member_ids[0]]["neutral_projection"]
        operative_ids = manifest_row["role_bindings"][
            "operative_content_interpretation_input"
        ]
        operative_sources = [sources[source_id] for source_id in operative_ids]
        expected_memberships = (
            expected_fisa_memberships
            if action_id in {"house:119:2:155", "house:119:2:221"}
            else ["JUSTICE_PUBLIC_SAFETY"]
        )
        expected_limits = (
            expected_fisa_limits
            if action_id in {"house:119:2:155", "house:119:2:221"}
            else []
        )
        criteria = {
            "approved_universe_member": action_id in approved_manifest["action_ids"],
            "stable_action_identity": bool(action_id),
            "official_member_action_resolved": member_projection["member_action"]
            in {"yea", "nay", "present", "not_voting"},
            "exact_action_identity": bool(
                canonical["exact_measure_or_amendment_identity"]
            ),
            "house_stage_resolved": bool(canonical["house_action_stage"]),
            **source_criteria,
            "exact_action_not_parent_only": all(
                source["source_subject"]
                in {canonical["exact_measure_or_amendment_identity"], action_id}
                for source in operative_sources
            ),
            "cross_domain_scope_complete": (
                record["cross_domain_memberships"] == expected_memberships
                and record["cross_domain_scope_limitations"] == expected_limits
            ),
            "no_semantic_leakage": all(
                not (set(_walk_keys(source["neutral_projection"])) & FORBIDDEN_KEYS)
                for source in manifest_row["sources"]
                if source["neutral_projection"] is not None
            ),
        }
        _require(
            record["readiness_criteria"] == criteria,
            f"asserted readiness criteria: {action_id}",
        )
        blockers = _derive_blockers(criteria)
        _require(record["blocker_codes"] == blockers, f"blocker mismatch: {action_id}")
        _require(
            record["readiness_state"] == (blockers[0] if blockers else "ready"),
            f"readiness state mismatch: {action_id}",
        )
        expected_versions = sorted(
            {source["text_version"] for source in operative_sources}
        )
        _require(
            record["operative_text_versions"] == expected_versions,
            f"operative text versions mismatch: {action_id}",
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
        blocker for record in records for blocker in record["blocker_codes"]
    )
    aggregate = {
        "total_action_count": len(records),
        "ready_count": readiness_counts["ready"],
        "blocked_count": len(records) - readiness_counts["ready"],
        "counts_by_readiness_state": dict(sorted(readiness_counts.items())),
        "counts_by_blocker": dict(sorted(blocker_counts.items())),
    }
    _require(subject["aggregate"] == aggregate, "aggregate mismatch")
    _require(
        artifact["result"]
        == (
            "complete_ready" if aggregate["blocked_count"] == 0 else "complete_blocked"
        ),
        "artifact result mismatch",
    )
    _require(
        sha256_json(subject) == artifact["source_readiness_subject_sha256"],
        "readiness subject digest mismatch",
    )
    current = current_state["full_record_issue_interpretation"]
    _require(
        current["f000477_justice_119_interpretation_source_readiness"]
        == artifact["result"],
        "current-state readiness mismatch",
    )
    current_identity = current[
        "f000477_justice_119_interpretation_source_readiness_identity"
    ]
    _require(
        current_identity
        == {
            "id": artifact["artifact_id"],
            "sha256": canonical_file_sha256(
                repository_root / ARTIFACT_PATH, text_line_endings="lf"
            ),
            "ready_count": aggregate["ready_count"],
            "blocked_count": aggregate["blocked_count"],
            "authorizing": False,
        },
        "current-state readiness identity mismatch",
    )
    _require(
        current["f000477_justice_119_action_interpretation_state"] == "not_started"
        and current["f000477_justice_119_policy_episode_state"] == "not_started"
        and current["f000477_justice_119_full_record_semantic_ir"] == "absent"
        and current["f000477_justice_119_full_record_synthesis"] == "absent"
        and current["f000477_justice_119_production_persistence"] == "not_authorized",
        "current state crosses M2 boundary",
    )
    return {
        **aggregate,
        "artifact_sha256": canonical_file_sha256(
            repository_root / ARTIFACT_PATH, text_line_endings="lf"
        ),
    }


def validate_repository(*, repository_root: Path = ROOT) -> dict[str, Any]:
    authority_result = validate_repository_authority(root=repository_root)
    result = validate_values(
        artifact=load_json(repository_root / ARTIFACT_PATH),
        source_manifest=load_json(repository_root / SOURCE_MANIFEST_PATH),
        approved_manifest=load_json(repository_root / MANIFEST_PATH),
        authority=load_json(repository_root / AUTHORITY_PATH),
        discovery=load_json(repository_root / DISCOVERY_PATH),
        schema=load_json(repository_root / SCHEMA_PATH),
        source_manifest_schema=load_json(repository_root / SOURCE_MANIFEST_SCHEMA_PATH),
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
