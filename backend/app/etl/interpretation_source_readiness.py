from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from .fetch_sources import (
    download_to_path,
    fetch_congress_bill_metadata,
    resolve_congress_api_key,
)
from .universe_discovery import (
    load_congress_metadata,
    load_house_clerk_member_actions,
    sha256_file,
    sha256_json,
)


SCHEMA_VERSION = "full_issue_interpretation_source_readiness_v1"
SOURCE_MANIFEST_VERSION = "full_issue_interpretation_official_source_manifest_v1"
READINESS_ID = "interpretation-source-readiness:f000477:justice_public_safety:119:v1"
SOURCE_MANIFEST_ID = (
    "interpretation-source-manifest:f000477:justice_public_safety:119:v1"
)
CRITERIA_VERSION = "full_issue_interpretation_source_readiness_criteria_v1"

ALLOWED_SOURCE_TYPES = {
    "house_clerk_roll_call",
    "congress_gov_action_record",
    "congressional_record_pdf",
    "govinfo_bill_status",
    "govinfo_bill_text",
    "house_rules_committee_report",
}
ALLOWED_RAW_HOSTS = {
    "www.congress.gov",
    "www.govinfo.gov",
    "docs.house.gov",
}
GOVERNED_ROOTS = ("docs/editorial/full_record_reviews/source_readiness/evidence/",)
FORBIDDEN_KEYS = {
    "accepted_interpretation",
    "benchmark_conclusion",
    "conclusion",
    "episode_id",
    "exact_action_meaning",
    "party",
    "policy_question",
    "proposition_ids",
    "public_wording",
    "recommended_public_wording",
    "support_opposition_direction",
    "synthesis",
    "synthesis_relevance",
}
BLOCKER_PRECEDENCE = (
    "blocked_semantic_leakage",
    "blocked_exact_action_identity",
    "blocked_parent_only_source",
    "blocked_wrong_text_version",
    "blocked_source_digest",
    "blocked_source_conflict",
    "blocked_source_constraint",
    "blocked_cross_domain_scope",
    "blocked_missing_official_source",
)
ALLOWED_INPUT_CLASSES = [
    "approved_v2_universe_manifest",
    "detached_m1_universe_authority_receipt",
    "v2_universe_discovery",
    "v2_source_inventory",
    "v2_universe_discovery_configuration",
    "v2_universe_comparison",
    "governed_official_source_files_and_projections",
    "neutral_source_sufficiency_and_action_identity_methodology",
]
EXCLUDED_INPUT_CLASSES = [
    "member_party",
    "accepted_seven_action_interpretations",
    "benchmark_conclusion",
    "accepted_semantic_ir_propositions",
    "public_presentation_wording",
    "episode_outcomes",
    "desired_synthesis_outcomes",
    "other_action_interpretations",
    "secondary_or_partisan_descriptions",
]


class SourceReadinessError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        + b"\n"
    )


def canonical_file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _source_binding(binding: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {
        "source_id": binding["source_id"],
        "source_type": binding["source_type"],
        "source_subject": binding["source_subject"],
        "url": binding["url"],
        "text_version": binding["text_version"],
        "evidence_role": binding["evidence_role"],
        "digest_basis": binding["digest_basis"],
        "source_content_sha256": binding["source_content_sha256"],
        **extra,
    }


def _raw_suffix(url: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix not in {".xml", ".pdf", ".json", ".txt"}:
        raise SourceReadinessError("official source URL has unsupported file type")
    return suffix


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def assert_no_semantic_leakage(value: Any) -> None:
    leaked = sorted(set(_walk_keys(value)) & FORBIDDEN_KEYS)
    if leaked:
        raise SourceReadinessError(f"forbidden semantic fields present: {leaked}")


def prepare_source_manifest(
    *,
    repository_root: Path,
    approved_manifest: dict[str, Any],
    discovery: dict[str, Any],
    clerk_dirs: list[Path],
    congress_dirs: list[Path],
    evidence_dir: Path,
    acquire_missing: bool,
) -> dict[str, Any]:
    approved = approved_manifest["action_ids"]
    rows = {row["action_id"]: row for row in discovery["candidate_dispositions"]}
    official = {
        row["canonical_action_id"]: row
        for row in load_house_clerk_member_actions(
            clerk_dirs, bioguide_id=approved_manifest["subject"]["member_id"]
        )
    }
    congress = load_congress_metadata(congress_dirs)
    action_sources: list[dict[str, Any]] = []
    for action_id in approved:
        if action_id not in rows:
            raise SourceReadinessError(f"approved action source missing: {action_id}")
        candidate = rows[action_id]
        exact = candidate.get("exact_action_source_binding")
        if exact is None:
            raise SourceReadinessError(
                f"approved action lacks exact binding: {action_id}"
            )
        vote = exact["vote_source_bindings"][0]
        acquired_vote_file: dict[str, str] = {}
        if action_id not in official:
            if not acquire_missing:
                raise SourceReadinessError(
                    f"official Clerk action missing: {action_id}"
                )
            _chamber, congress_number, session_number, roll_number = action_id.split(
                ":"
            )
            relative = Path(
                "docs/editorial/full_record_reviews/source_readiness/evidence"
            ) / (f"roll{congress_number}_{session_number}_{int(roll_number):03d}.xml")
            destination = repository_root / relative
            download_to_path(vote["url"], destination)
            loaded = load_house_clerk_member_actions(
                [destination.parent],
                bioguide_id=approved_manifest["subject"]["member_id"],
            )
            official.update({row["canonical_action_id"]: row for row in loaded})
            if action_id not in official:
                raise SourceReadinessError(
                    f"acquired Clerk action missing member vote: {action_id}"
                )
            acquired_vote_file = {
                "governed_local_path": relative.as_posix(),
                "raw_file_sha256": sha256_file(destination),
            }
        projection = _official_projection(official[action_id])
        if sha256_json(projection) != vote["source_content_sha256"]:
            raise SourceReadinessError(f"vote projection digest mismatch: {action_id}")
        vote_record = _source_binding(
            vote,
            canonical_projection=projection,
            **acquired_vote_file,
        )

        exact_records: list[dict[str, Any]] = []
        bindings = exact["exact_action_meaning_source_bindings"]
        for binding in bindings:
            basis = binding["digest_basis"]
            if basis == "canonical_official_page_projection_sha256":
                # The same amendment has a raw official Congressional Record
                # source. Avoid relying on an unreproducible web-page projection.
                continue
            if basis == "canonical_congress_metadata_sha256":
                key = "bill_" + binding["source_subject"].replace(":", "_")
                projection = congress.get(key)
                if (
                    projection is not None
                    and sha256_json(projection) == binding["source_content_sha256"]
                ):
                    exact_records.append(
                        _source_binding(binding, canonical_projection=projection)
                    )
                    continue
                if not acquire_missing:
                    raise SourceReadinessError(
                        f"Congress projection digest mismatch: {binding['source_id']}"
                    )
                congress_number, measure_type, measure_number = binding[
                    "source_subject"
                ].split(":")
                result = fetch_congress_bill_metadata(
                    congress=int(congress_number),
                    bill_type=measure_type,
                    bill_number=int(measure_number),
                    api_key=resolve_congress_api_key(),
                    output_dir=evidence_dir,
                )
                destination = result.destination
                relative = destination.relative_to(repository_root)
                exact_records.append(
                    {
                        **_source_binding(binding),
                        "text_version": "congress_api_v3_acquired_2026-07-31",
                        "digest_basis": "raw_official_file_sha256",
                        "source_content_sha256": sha256_file(destination),
                        "governed_local_path": relative.as_posix(),
                        "acquisition_authority": "api.congress.gov/v3/bill",
                        "v2_projection_sha256": binding["source_content_sha256"],
                        "v2_projection_digest_basis": binding["digest_basis"],
                    }
                )
                continue
            if basis != "raw_official_file_sha256":
                raise SourceReadinessError(f"unsupported digest basis: {basis}")
            host = (urlparse(binding["url"]).hostname or "").lower()
            if host not in ALLOWED_RAW_HOSTS:
                raise SourceReadinessError(
                    "raw official source host is not allowlisted"
                )
            suffix = _raw_suffix(binding["url"])
            relative = (
                Path("docs/editorial/full_record_reviews/source_readiness/evidence")
                / f"{binding['source_content_sha256']}{suffix}"
            )
            destination = repository_root / relative
            if not destination.exists():
                if not acquire_missing:
                    raise SourceReadinessError(
                        f"official source file missing: {binding['source_id']}"
                    )
                download_to_path(binding["url"], destination)
            if sha256_file(destination) != binding["source_content_sha256"]:
                raise SourceReadinessError(
                    f"official source digest mismatch: {binding['source_id']}"
                )
            exact_records.append(
                _source_binding(binding, governed_local_path=relative.as_posix())
            )
        if not exact_records:
            raise SourceReadinessError(f"no reproducible exact source: {action_id}")
        action_sources.append(
            {
                "action_id": action_id,
                "vote_source": vote_record,
                "exact_action_sources": exact_records,
            }
        )

    subject = {
        "member_id": approved_manifest["subject"]["member_id"],
        "issue_id": approved_manifest["subject"]["issue_id"],
        "congress": approved_manifest["subject"]["congress_scope"][0],
        "action_set_sha256": approved_manifest["action_set_sha256"],
        "action_sources": action_sources,
    }
    result = {
        "schema_version": SOURCE_MANIFEST_VERSION,
        "source_manifest_id": SOURCE_MANIFEST_ID,
        "allowlisted_source_types": sorted(ALLOWED_SOURCE_TYPES),
        "governed_roots": list(GOVERNED_ROOTS),
        "subject": subject,
        "source_manifest_subject_sha256": sha256_json(subject),
    }
    assert_no_semantic_leakage(result)
    return result


def validate_source_manifest(
    value: dict[str, Any],
    *,
    repository_root: Path,
    approved_manifest: dict[str, Any],
    discovery: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    assert_no_semantic_leakage(value)
    if value["schema_version"] != SOURCE_MANIFEST_VERSION:
        raise SourceReadinessError("source manifest version mismatch")
    subject = value["subject"]
    if sha256_json(subject) != value["source_manifest_subject_sha256"]:
        raise SourceReadinessError("source manifest subject digest mismatch")
    if subject["action_set_sha256"] != approved_manifest["action_set_sha256"]:
        raise SourceReadinessError("source manifest action-set digest mismatch")
    expected = approved_manifest["action_ids"]
    actual = [row["action_id"] for row in subject["action_sources"]]
    if actual != expected or len(actual) != len(set(actual)):
        raise SourceReadinessError("source manifest action membership mismatch")
    candidates = {row["action_id"]: row for row in discovery["candidate_dispositions"]}
    result: dict[str, dict[str, Any]] = {}
    for row in subject["action_sources"]:
        action_id = row["action_id"]
        canonical = candidates[action_id]["exact_action_source_binding"]
        vote = row["vote_source"]
        if vote["source_type"] not in ALLOWED_SOURCE_TYPES:
            raise SourceReadinessError("unapproved vote source type")
        if sha256_json(vote["canonical_projection"]) != vote["source_content_sha256"]:
            raise SourceReadinessError(f"vote digest mismatch: {action_id}")
        if "governed_local_path" in vote:
            path = repository_root / vote["governed_local_path"]
            if not path.is_file() or sha256_file(path) != vote["raw_file_sha256"]:
                raise SourceReadinessError(
                    f"raw vote file digest mismatch: {action_id}"
                )
        expected_vote = canonical["vote_source_bindings"][0]
        if any(vote[key] != expected_vote[key] for key in expected_vote):
            raise SourceReadinessError(f"vote source binding mismatch: {action_id}")
        canonical_exact = {
            source["source_id"]: source
            for source in canonical["exact_action_meaning_source_bindings"]
        }
        for source in row["exact_action_sources"]:
            if source["source_type"] not in ALLOWED_SOURCE_TYPES:
                raise SourceReadinessError("unapproved exact source type")
            expected_source = canonical_exact.get(source["source_id"])
            if expected_source is None:
                raise SourceReadinessError(
                    f"exact source binding mismatch: {source['source_id']}"
                )
            if "v2_projection_sha256" in source:
                stable_keys = {
                    "source_id",
                    "source_type",
                    "source_subject",
                    "url",
                    "evidence_role",
                }
                if any(source[key] != expected_source[key] for key in stable_keys):
                    raise SourceReadinessError(
                        f"exact source identity mismatch: {source['source_id']}"
                    )
                if (
                    source["v2_projection_sha256"]
                    != expected_source["source_content_sha256"]
                    or source["v2_projection_digest_basis"]
                    != expected_source["digest_basis"]
                ):
                    raise SourceReadinessError(
                        f"V2 source projection binding mismatch: {source['source_id']}"
                    )
            elif any(source[key] != expected_source[key] for key in expected_source):
                raise SourceReadinessError(
                    f"exact source binding mismatch: {source['source_id']}"
                )
            if "canonical_projection" in source:
                digest = sha256_json(source["canonical_projection"])
            else:
                relative = source["governed_local_path"]
                if not any(relative.startswith(root) for root in GOVERNED_ROOTS):
                    raise SourceReadinessError("source path escapes governed root")
                path = (repository_root / relative).resolve()
                if repository_root.resolve() not in path.parents:
                    raise SourceReadinessError("source path escapes repository")
                if not path.is_file():
                    raise SourceReadinessError("governed source file is missing")
                digest = sha256_file(path)
            if digest != source["source_content_sha256"]:
                raise SourceReadinessError(
                    f"exact source digest mismatch: {source['source_id']}"
                )
        if not row["exact_action_sources"]:
            raise SourceReadinessError(f"missing exact source: {action_id}")
        result[action_id] = row
    return result


def _derive_blockers(record: dict[str, Any]) -> list[str]:
    criteria = record["readiness_criteria"]
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


def build_readiness_artifact(
    *,
    approved_manifest: dict[str, Any],
    authority_receipt: dict[str, Any],
    authority_receipt_sha256: str,
    manifest_sha256: str,
    source_manifest: dict[str, Any],
    source_manifest_sha256: str,
    discovery: dict[str, Any],
) -> dict[str, Any]:
    source_rows = {
        row["action_id"]: row for row in source_manifest["subject"]["action_sources"]
    }
    candidates = {row["action_id"]: row for row in discovery["candidate_dispositions"]}
    records: list[dict[str, Any]] = []
    for action_id in approved_manifest["action_ids"]:
        candidate = candidates[action_id]
        canonical = candidate["exact_action_source_binding"]
        source_row = source_rows[action_id]
        projection = source_row["vote_source"]["canonical_projection"]
        memberships = approved_manifest["cross_domain_memberships"].get(
            action_id, [approved_manifest["subject"]["issue_id"]]
        )
        limitations = approved_manifest["cross_domain_scope_limitations"].get(
            action_id, []
        )
        criteria = {
            "approved_universe_member": True,
            "stable_action_identity": bool(action_id),
            "official_member_action_resolved": projection["member_action"]
            in {"yea", "nay", "present", "not_voting"},
            "exact_action_identity": bool(
                canonical["exact_measure_or_amendment_identity"]
            ),
            "house_stage_resolved": bool(canonical["house_action_stage"]),
            "vote_source_present": bool(source_row["vote_source"]),
            "exact_action_source_present": bool(source_row["exact_action_sources"]),
            "exact_action_not_parent_only": all(
                source["source_subject"]
                in {canonical["exact_measure_or_amendment_identity"], action_id}
                or canonical["house_action_stage"]
                not in {"amendment", "amendment_to_rule"}
                for source in source_row["exact_action_sources"]
            ),
            "governed_source_exists": True,
            "text_version_explicit": all(
                bool(source["text_version"])
                for source in [
                    source_row["vote_source"],
                    *source_row["exact_action_sources"],
                ]
            ),
            "all_source_digests_valid": True,
            "no_source_conflict": True,
            "no_source_constraint": True,
            "all_paths_governed": True,
            "approved_source_types_only": True,
            "cross_domain_scope_complete": (
                action_id not in {"house:119:2:155", "house:119:2:221"}
                or (
                    memberships == ["JUSTICE_PUBLIC_SAFETY", "NATIONAL_SECURITY"]
                    and limitations
                    == [
                        "surveillance_authority",
                        "fisc_and_court_authority",
                        "civil_liberty_protections",
                    ]
                )
            ),
            "no_semantic_leakage": True,
        }
        record = {
            "action_id": action_id,
            "official_action_date": projection["vote_date"],
            "congress": projection["congress"],
            "session": projection["session"],
            "roll_number": projection["rollcall_number"],
            "official_member_action": projection["member_action"],
            "exact_action_identity": canonical["exact_measure_or_amendment_identity"],
            "house_action_stage": canonical["house_action_stage"],
            "vote_source_bindings": [
                {
                    key: value
                    for key, value in source_row["vote_source"].items()
                    if key != "canonical_projection"
                }
            ],
            "exact_action_source_bindings": [
                {
                    key: value
                    for key, value in source.items()
                    if key != "canonical_projection"
                }
                for source in source_row["exact_action_sources"]
            ],
            "source_availability_state": "available",
            "source_conflict_state": "none",
            "source_constraint_state": "none",
            "cross_domain_memberships": memberships,
            "cross_domain_scope_limitations": limitations,
            "readiness_criteria": criteria,
        }
        blockers = _derive_blockers(record)
        record["blocker_codes"] = blockers
        record["readiness_state"] = blockers[0] if blockers else "ready"
        record["source_packet_sha256"] = sha256_json(record)
        records.append(record)

    counts = Counter(record["readiness_state"] for record in records)
    aggregate = {
        "total_action_count": len(records),
        "ready_count": counts["ready"],
        "blocked_count": len(records) - counts["ready"],
        "counts_by_readiness_state": dict(sorted(counts.items())),
        "counts_by_blocker": dict(
            sorted(
                Counter(
                    code for row in records for code in row["blocker_codes"]
                ).items()
            )
        ),
    }
    subject = {
        "member_id": approved_manifest["subject"]["member_id"],
        "issue_id": approved_manifest["subject"]["issue_id"],
        "chamber": approved_manifest["boundary"]["chambers"][0],
        "congress": approved_manifest["subject"]["congress_scope"][0],
        "approved_manifest_id": approved_manifest["manifest_id"],
        "approved_manifest_sha256": manifest_sha256,
        "universe_subject_sha256": approved_manifest["universe_subject_sha256"],
        "authority_receipt_id": authority_receipt["receipt_id"],
        "authority_receipt_sha256": authority_receipt_sha256,
        "action_ids": approved_manifest["action_ids"],
        "action_set_sha256": approved_manifest["action_set_sha256"],
        "source_manifest_id": source_manifest["source_manifest_id"],
        "source_manifest_sha256": source_manifest_sha256,
        "criteria_version": CRITERIA_VERSION,
        "action_readiness": records,
        "aggregate": aggregate,
    }
    artifact = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": READINESS_ID,
        "artifact_role": "detached_non_authorizing_source_readiness_metadata",
        "result": "complete_ready"
        if aggregate["blocked_count"] == 0
        else "complete_blocked",
        "subject": subject,
        "source_readiness_subject_sha256": sha256_json(subject),
        "authorizations": {
            "action_interpretation": False,
            "episode_authority": False,
            "semantic_authority": False,
            "synthesis_eligibility": False,
            "persistence_eligibility": False,
            "publication_eligibility": False,
        },
        "input_contract": {
            "allowlisted_input_classes": ALLOWED_INPUT_CLASSES,
            "excluded_input_classes": EXCLUDED_INPUT_CLASSES,
        },
    }
    assert_no_semantic_leakage(artifact)
    return artifact


def render_report(artifact: dict[str, Any]) -> str:
    subject = artifact["subject"]
    aggregate = subject["aggregate"]
    lines = [
        "# Foushee Justice 119th-Congress Interpretation-Source Readiness V1",
        "",
        f"- Artifact: `{artifact['artifact_id']}`",
        f"- Approved universe: `{subject['approved_manifest_id']}`",
        f"- M1 authority receipt: `{subject['authority_receipt_id']}`",
        f"- Actions: `{aggregate['total_action_count']}`",
        f"- Ready: `{aggregate['ready_count']}`",
        f"- Blocked: `{aggregate['blocked_count']}`",
        f"- Blockers: `{json.dumps(aggregate['counts_by_blocker'], sort_keys=True)}`",
        "",
        "No action interpretations were generated. This report does not authorize M3.",
        "",
        "| Action ID | Stage | Vote source | Exact-action source | Text version | Cross-domain constraints | Readiness | Blockers |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in subject["action_readiness"]:
        constraints = (
            ", ".join(row["cross_domain_scope_limitations"]) or "not applicable"
        )
        blockers = ", ".join(row["blocker_codes"]) or "none"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['action_id']}`",
                    row["house_action_stage"],
                    "available",
                    "available",
                    "explicit",
                    constraints,
                    row["readiness_state"],
                    blockers,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "The packet is source and identity metadata only. It grants no interpretation, episode, semantic, synthesis, persistence, or publication authority.",
            "",
        ]
    )
    return "\n".join(lines)


def verify_packet_digests(artifact: dict[str, Any]) -> None:
    for record in artifact["subject"]["action_readiness"]:
        expected = record["source_packet_sha256"]
        subject = {
            key: value for key, value in record.items() if key != "source_packet_sha256"
        }
        if sha256_json(subject) != expected:
            raise SourceReadinessError(
                f"source packet digest mismatch: {record['action_id']}"
            )
