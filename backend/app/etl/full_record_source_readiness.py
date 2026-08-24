from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
import os
from typing import Any, Iterable
from urllib.parse import urlparse
from xml.etree import ElementTree


SCHEMA_VERSION = "full_record_interpretation_source_readiness_v1"
PROJECTION_VERSION = "neutral_interpretation_source_projection_v1"
CRITERIA_VERSION = "full_record_interpretation_source_readiness_criteria_v1"

READINESS_STATES = (
    "ready_for_action_interpretation",
    "blocked_missing_operative_content",
    "blocked_stage_mismatch",
    "blocked_exact_action_identity",
    "blocked_source_conflict",
    "blocked_insufficient_context",
)
BLOCKER_PRECEDENCE = (
    "blocked_source_conflict",
    "blocked_exact_action_identity",
    "blocked_stage_mismatch",
    "blocked_missing_operative_content",
    "blocked_insufficient_context",
)
ALLOWED_SOURCE_TYPES = {
    "congressional_record",
    "congress_gov_amendment_index",
    "congress_gov_bill_actions",
    "congress_gov_bill_summary",
    "congress_gov_bill_text",
    "house_clerk_roll_call",
    "house_rules_committee_report",
}
ALLOWED_CONTENT_CLASSES = {
    "exact_amendment_purpose",
    "exact_house_action_record",
    "member_action_record",
    "operative_floor_text",
    "operative_measure_text",
    "operative_resolution_text",
    "pre_floor_house_rules_report_context",
    "supplemental_program_context",
    "stage_compatible_senate_origin_text",
}
ALLOWED_HOSTS = {
    "api.congress.gov",
    "clerk.house.gov",
    "docs.house.gov",
    "www.congress.gov",
    "www.govinfo.gov",
}
FORBIDDEN_PROJECTION_KEYS = {
    "accepted_interpretation",
    "benchmark_conclusion",
    "conclusion",
    "cosponsor",
    "cosponsors",
    "episode",
    "episode_id",
    "exact_action_meaning",
    "issue_meaning",
    "ideology",
    "member_party",
    "party",
    "policy_question",
    "proposition_ids",
    "public_wording",
    "recommended_public_wording",
    "sponsor",
    "sponsors",
    "support",
    "opposition",
    "support_opposition",
    "support_opposition_direction",
    "synthesis",
    "synthesis_relevance",
    "vote_direction_interpretation",
    "motive",
    "voting_advice",
}


class SourceReadinessError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(_filesystem_path(path).read_bytes()).hexdigest()


def canonical_file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _filesystem_path(path: Path) -> Path:
    if os.name == "nt" and not str(path).startswith("\\\\?\\"):
        return Path("\\\\?\\" + str(path.resolve()))
    return path


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        + b"\n"
    )


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def assert_neutral_projection(projection: dict[str, Any]) -> None:
    leaked = sorted(set(_walk_keys(projection)) & FORBIDDEN_PROJECTION_KEYS)
    if leaked:
        raise SourceReadinessError(
            f"forbidden neutral-projection fields present: {leaked}"
        )
    if projection.get("schema_version") != PROJECTION_VERSION:
        raise SourceReadinessError("neutral projection version mismatch")


def _resolve_governed_path(relative: str, *, repository_root: Path) -> Path:
    normalized = Path(relative)
    if normalized.is_absolute() or ".." in normalized.parts:
        raise SourceReadinessError("raw provenance path is not governed")
    path = (repository_root / normalized).resolve()
    governed = (
        repository_root / "docs/editorial/full_record_reviews/source_readiness/evidence"
    ).resolve()
    if governed not in path.parents:
        raise SourceReadinessError("raw provenance path is outside governed root")
    return _filesystem_path(path)


def _source_integrity(
    source: dict[str, Any], *, repository_root: Path
) -> tuple[bool, bool]:
    host = (urlparse(source["source_url"]).hostname or "").casefold()
    allowed_classes_by_source_type = {
        "congressional_record": {"operative_floor_text"},
        "congress_gov_amendment_index": {"exact_amendment_purpose"},
        "congress_gov_bill_actions": {"exact_house_action_record"},
        "congress_gov_bill_summary": {"supplemental_program_context"},
        "congress_gov_bill_text": {
            "operative_measure_text",
            "operative_resolution_text",
            "stage_compatible_senate_origin_text",
        },
        "house_clerk_roll_call": {"member_action_record"},
        "house_rules_committee_report": {"pre_floor_house_rules_report_context"},
    }
    official = (
        source["source_type"] in ALLOWED_SOURCE_TYPES
        and source["content_class"] in ALLOWED_CONTENT_CLASSES
        and source["content_class"]
        in allowed_classes_by_source_type.get(source["source_type"], set())
        and host in ALLOWED_HOSTS
    )
    raw = source["raw_provenance"]
    path = _resolve_governed_path(
        raw["governed_local_path"], repository_root=repository_root
    )
    raw_valid = path.is_file() and sha256_file(path) == raw["sha256"]
    projection = source["neutral_projection"]
    assert_neutral_projection(projection)
    projection_valid = sha256_json(projection) == source["neutral_projection_sha256"]
    return official, raw_valid and projection_valid


def _xml_has_operative_body(path: Path) -> bool:
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError):
        return False
    return any(
        root.find(tag) is not None
        for tag in ("legis-body", "resolution-body", "engrossed-amendment-body")
    )


def _pdf_has_content(path: Path) -> bool:
    try:
        content = path.read_bytes()
    except OSError:
        return False
    return len(content) > 1_000 and content.startswith(b"%PDF")


def _derive_criteria(
    record: dict[str, Any], *, repository_root: Path
) -> dict[str, bool]:
    sources = {source["source_id"]: source for source in record["sources"]}
    roles = record["source_roles"]
    all_source_ids = [source_id for ids in roles.values() for source_id in ids]
    bindings_exist = all(source_id in sources for source_id in all_source_ids)

    official = True
    integrity = True
    for source in sources.values():
        source_official, source_integrity = _source_integrity(
            source, repository_root=repository_root
        )
        official = official and source_official
        integrity = integrity and source_integrity

    member_sources = [
        sources[source_id]
        for source_id in roles["member_action_evidence"]
        if source_id in sources
    ]
    identity_sources = [
        sources[source_id]
        for source_id in roles["exact_action_identity_and_stage_evidence"]
        if source_id in sources
    ]
    operative_sources = [
        sources[source_id]
        for source_id in roles["operative_content_interpretation_input"]
        if source_id in sources
    ]

    expected_identity = record["exact_action_identity"]
    expected_stage = record["house_action_stage"]
    identity_values = {
        source["neutral_projection"].get("exact_action_identity")
        for source in identity_sources + operative_sources
        if source["neutral_projection"].get("exact_action_identity")
    }
    source_conflict = record["source_conflict"] or len(identity_values) > 1
    identity_exact = bool(identity_sources) and all(
        source["neutral_projection"].get("action_id") == record["action_id"]
        and source["neutral_projection"].get("exact_action_identity")
        == expected_identity
        and source["neutral_projection"].get("roll_number") == record["roll_number"]
        and source["neutral_projection"].get("action_date")
        == record["official_action_date"]
        for source in identity_sources
    )
    stage_compatible = bool(identity_sources) and all(
        source["neutral_projection"].get("house_action_stage") == expected_stage
        for source in identity_sources
    )
    member_action_exact = len(member_sources) == 1 and (
        member_sources[0]["neutral_projection"].get("member_action")
        == record["official_member_action"]
    )

    operative_present = bool(operative_sources)
    operative_context_sufficient = operative_present
    operative_text_version_stage_compatible = operative_present
    for source in operative_sources:
        projection = source["neutral_projection"]
        content_class = source["content_class"]
        raw_path = _resolve_governed_path(
            source["raw_provenance"]["governed_local_path"],
            repository_root=repository_root,
        )
        if record["mechanism_class"] == "amendment":
            operative_context_sufficient = operative_context_sufficient and (
                content_class == "exact_amendment_purpose"
                and bool(
                    projection.get("official_purpose")
                    or projection.get("official_description")
                )
            )
            operative_text_version_stage_compatible = (
                operative_text_version_stage_compatible
                and projection.get("text_version")
                == "official_amendment_purpose_or_description_v3"
            )
        else:
            accepted_classes = {
                "operative_floor_text",
                "operative_measure_text",
                "operative_resolution_text",
                "stage_compatible_senate_origin_text",
            }
            content_ok = content_class in accepted_classes
            if content_class == "operative_floor_text":
                content_ok = (
                    content_ok
                    and source["source_type"] == "congressional_record"
                    and raw_path.suffix.lower() == ".pdf"
                    and _pdf_has_content(raw_path)
                )
            else:
                content_ok = (
                    content_ok
                    and source["source_type"] == "congress_gov_bill_text"
                    and raw_path.suffix.lower() == ".xml"
                    and _xml_has_operative_body(raw_path)
                )
            operative_context_sufficient = operative_context_sufficient and content_ok
            allowed_versions = {
                "operative_floor_text": {"official_house_record_H677-H693"},
                "operative_measure_text": {"eh", "cdh"},
                "operative_resolution_text": {"eh", "ih"},
                "stage_compatible_senate_origin_text": {"es", "eah"},
            }
            operative_text_version_stage_compatible = (
                operative_text_version_stage_compatible
                and projection.get("text_version")
                in allowed_versions.get(content_class, set())
            )

    return {
        "approved_universe_member": bool(record["approved_universe_member"]),
        "all_role_bindings_resolve": bindings_exist,
        "official_source_types_and_hosts": official,
        "raw_and_projection_digests_valid": integrity,
        "neutral_projection_closed": all(
            not (
                set(_walk_keys(source["neutral_projection"]))
                & FORBIDDEN_PROJECTION_KEYS
            )
            for source in sources.values()
        ),
        "member_action_exact": member_action_exact,
        "exact_action_identity": identity_exact,
        "house_stage_compatible": stage_compatible,
        "operative_text_version_stage_compatible": operative_text_version_stage_compatible,
        "operative_content_present": operative_present,
        "operative_context_sufficient": operative_context_sufficient,
        "no_source_conflict": not source_conflict,
    }


def derive_readiness(
    record: dict[str, Any], *, repository_root: Path
) -> tuple[dict[str, bool], list[str], str]:
    criteria = _derive_criteria(record, repository_root=repository_root)
    blockers: list[str] = []
    if not criteria["no_source_conflict"]:
        blockers.append("blocked_source_conflict")
    if not (
        criteria["approved_universe_member"]
        and criteria["all_role_bindings_resolve"]
        and criteria["official_source_types_and_hosts"]
        and criteria["raw_and_projection_digests_valid"]
        and criteria["neutral_projection_closed"]
        and criteria["member_action_exact"]
        and criteria["exact_action_identity"]
    ):
        blockers.append("blocked_exact_action_identity")
    if not criteria["house_stage_compatible"] or (
        criteria["operative_content_present"]
        and not criteria["operative_text_version_stage_compatible"]
    ):
        blockers.append("blocked_stage_mismatch")
    if not criteria["operative_content_present"]:
        blockers.append("blocked_missing_operative_content")
    elif not criteria["operative_context_sufficient"]:
        blockers.append("blocked_insufficient_context")
    blockers = [code for code in BLOCKER_PRECEDENCE if code in blockers]
    state = blockers[0] if blockers else "ready_for_action_interpretation"
    return criteria, blockers, state


def build_readiness_artifact(
    *,
    artifact_id: str,
    input_bindings: dict[str, Any],
    subject: dict[str, Any],
    action_records: list[dict[str, Any]],
    repository_root: Path,
) -> dict[str, Any]:
    actions = []
    for source_record in action_records:
        record = dict(source_record)
        criteria, blockers, state = derive_readiness(
            record, repository_root=repository_root
        )
        record["readiness_criteria"] = criteria
        record["blocker_codes"] = blockers
        record["readiness_state"] = state
        record["source_packet_sha256"] = sha256_json(record)
        actions.append(record)

    counts = Counter(record["readiness_state"] for record in actions)
    aggregate = {
        "total_action_count": len(actions),
        "ready_count": counts["ready_for_action_interpretation"],
        "blocked_count": len(actions) - counts["ready_for_action_interpretation"],
        "counts_by_readiness_state": dict(sorted(counts.items())),
    }
    artifact_subject = {
        **subject,
        "criteria_version": CRITERIA_VERSION,
        "action_readiness": actions,
        "aggregate": aggregate,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "artifact_role": "non_authorizing_source_readiness_only",
        "input_bindings": input_bindings,
        "input_contract": {
            "allowlisted_input_classes": [
                "approved_full_issue_universe_authority_receipt",
                "approved_universe_proposal",
                "approved_universe_source_inventory",
                "governed_official_raw_provenance",
                "closed_neutral_source_projections",
                "source_readiness_methodology",
            ],
            "excluded_input_classes": [
                "action_interpretations",
                "party_or_sponsor_context",
                "support_or_opposition_meaning",
                "policy_episodes",
                "semantic_ir",
                "synthesis",
                "public_wording",
                "publication_or_persistence_state_changes",
            ],
        },
        "subject": artifact_subject,
        "source_readiness_subject_sha256": sha256_json(artifact_subject),
        "authorizations": {
            "action_interpretation": False,
            "episode_authority": False,
            "semantic_ir": False,
            "synthesis": False,
            "public_wording": False,
            "publication": False,
            "production_persistence": False,
        },
    }


def validate_artifact(
    artifact: dict[str, Any], *, repository_root: Path
) -> dict[str, Any]:
    subject = artifact["subject"]
    records = subject["action_readiness"]
    if subject["action_ids"] != [record["action_id"] for record in records]:
        raise SourceReadinessError("readiness action order or membership mismatch")
    if len(set(subject["action_ids"])) != len(subject["action_ids"]):
        raise SourceReadinessError("duplicate action readiness record")
    if sha256_json(sorted(subject["action_ids"])) != subject["action_set_sha256"]:
        raise SourceReadinessError("action-set digest mismatch")

    counts: Counter[str] = Counter()
    for record in records:
        stored_packet_sha = record["source_packet_sha256"]
        packet = {
            key: value for key, value in record.items() if key != "source_packet_sha256"
        }
        if sha256_json(packet) != stored_packet_sha:
            raise SourceReadinessError(
                f"source packet digest mismatch: {record['action_id']}"
            )
        criteria, blockers, state = derive_readiness(
            packet, repository_root=repository_root
        )
        if criteria != record["readiness_criteria"]:
            raise SourceReadinessError(
                f"asserted readiness criteria: {record['action_id']}"
            )
        if blockers != record["blocker_codes"] or state != record["readiness_state"]:
            raise SourceReadinessError(
                f"asserted readiness state: {record['action_id']}"
            )
        counts[state] += 1

    aggregate = {
        "total_action_count": len(records),
        "ready_count": counts["ready_for_action_interpretation"],
        "blocked_count": len(records) - counts["ready_for_action_interpretation"],
        "counts_by_readiness_state": dict(sorted(counts.items())),
    }
    if aggregate != subject["aggregate"]:
        raise SourceReadinessError("readiness aggregate mismatch")
    if sha256_json(subject) != artifact["source_readiness_subject_sha256"]:
        raise SourceReadinessError("source-readiness subject digest mismatch")
    if any(artifact["authorizations"].values()):
        raise SourceReadinessError("source readiness cannot authorize downstream work")
    return aggregate
