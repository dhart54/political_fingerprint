from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from .fetch_sources import download_to_path
from .universe_discovery import (
    load_house_clerk_member_actions,
    sha256_file,
    sha256_json,
)


SCHEMA_VERSION = "full_issue_interpretation_source_readiness_v1"
SOURCE_MANIFEST_VERSION = "full_issue_interpretation_official_source_manifest_v1"
PROJECTION_VERSION = "neutral_m3_source_projection_v1"
READINESS_ID = "interpretation-source-readiness:f000477:justice_public_safety:119:v1"
SOURCE_MANIFEST_ID = (
    "interpretation-source-manifest:f000477:justice_public_safety:119:v1"
)
CRITERIA_VERSION = "full_issue_interpretation_source_readiness_criteria_v2"

ALLOWED_SOURCE_TYPES = {
    "congress_gov_bill_actions",
    "congress_gov_bill_metadata",
    "congress_gov_bill_text",
    "congressional_record_pdf",
    "govinfo_bill_status",
    "govinfo_bill_text",
    "house_clerk_roll_call",
    "house_rules_committee_report",
}
M3_ELIGIBLE_SOURCE_TYPES = ALLOWED_SOURCE_TYPES - {"congress_gov_bill_metadata"}
RAW_PROVENANCE_ONLY_SOURCE_TYPES = {"congress_gov_bill_metadata"}
OPERATIVE_CONTENT_CLASSES = {
    "exact_amendment_or_rule_text",
    "operative_legislative_text",
}
IDENTITY_STAGE_CONTENT_CLASSES = {
    "exact_house_action_record",
    "exact_amendment_or_rule_text",
    "official_status_record",
    "operative_legislative_text",
}
ALLOWED_RAW_HOSTS = {
    "api.congress.gov",
    "www.congress.gov",
    "www.govinfo.gov",
    "docs.house.gov",
}
GOVERNED_ROOTS = ("docs/editorial/full_record_reviews/source_readiness/evidence/",)
FORBIDDEN_KEYS = {
    "accepted_interpretation",
    "benchmark_conclusion",
    "conclusion",
    "cosponsor",
    "cosponsors",
    "episode_id",
    "exact_action_meaning",
    "member_party",
    "party",
    "policy_question",
    "proposition_ids",
    "public_wording",
    "recommended_public_wording",
    "sponsor",
    "sponsors",
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
    "blocked_missing_operative_content_source",
    "blocked_missing_official_source",
)
ALLOWED_INPUT_CLASSES = [
    "approved_v2_universe_manifest",
    "detached_m1_universe_authority_receipt",
    "v2_universe_discovery",
    "v2_source_inventory",
    "v2_universe_discovery_configuration",
    "v2_universe_comparison",
    "governed_official_raw_provenance",
    "closed_neutral_m3_source_projections",
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
RAW_METADATA_FILES = {
    "house:119:2:227": "119_hr_2478.json",
    "house:119:2:234": "119_hr_3106.json",
    "house:119:2:240": "119_hr_1181.json",
}


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
        raise SourceReadinessError(f"forbidden M3 projection fields present: {leaked}")


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


def _raw_suffix(url: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix not in {".xml", ".pdf", ".json", ".txt"}:
        raise SourceReadinessError("official source URL has unsupported file type")
    return suffix


def _governed_raw(path: Path, *, repository_root: Path) -> dict[str, str]:
    relative = path.relative_to(repository_root).as_posix()
    return {"governed_local_path": relative, "sha256": sha256_file(path)}


def _neutral_projection(
    *,
    action_id: str,
    canonical: dict[str, Any],
    vote_projection: dict[str, Any],
    text_version: str,
    source_url: str,
    raw_sha256: str | None,
    official_action_description: str | None,
    operative_content_sha256: str | None,
) -> dict[str, Any]:
    projection = {
        "schema_version": PROJECTION_VERSION,
        "action_id": action_id,
        "congress": vote_projection["congress"],
        "chamber": "house",
        "measure_identity": canonical["exact_measure_or_amendment_identity"],
        "house_action_stage": canonical["house_action_stage"],
        "action_date": vote_projection["vote_date"],
        "roll_number": vote_projection["rollcall_number"],
        "member_action": vote_projection["member_action"],
        "official_action_description": official_action_description,
        "text_version": text_version,
        "source_url": source_url,
        "raw_provenance_sha256": raw_sha256,
        "operative_content_sha256": operative_content_sha256,
    }
    assert_no_semantic_leakage(projection)
    return projection


def _source_record(
    *,
    source_id: str,
    source_type: str,
    source_subject: str,
    url: str,
    text_version: str,
    content_class: str,
    raw_provenance: dict[str, str] | None,
    neutral_projection: dict[str, Any] | None,
    m3_input_eligible: bool,
    constraint_codes: list[str] | None = None,
) -> dict[str, Any]:
    if source_type not in ALLOWED_SOURCE_TYPES:
        raise SourceReadinessError(f"unapproved source type: {source_type}")
    if m3_input_eligible and neutral_projection is None:
        raise SourceReadinessError("M3-eligible source requires a neutral projection")
    if neutral_projection is not None:
        assert_no_semantic_leakage(neutral_projection)
    return {
        "source_id": source_id,
        "source_type": source_type,
        "source_subject": source_subject,
        "url": url,
        "text_version": text_version,
        "content_class": content_class,
        "raw_provenance": raw_provenance,
        "neutral_projection": neutral_projection,
        "neutral_projection_sha256": (
            sha256_json(neutral_projection) if neutral_projection is not None else None
        ),
        "m3_input_eligible": m3_input_eligible,
        "constraint_codes": sorted(constraint_codes or []),
    }


def _copy_content_addressed(
    source: Path,
    *,
    evidence_dir: Path,
    suffix: str | None = None,
) -> Path:
    digest = sha256_file(source)
    destination = evidence_dir / f"{digest}{suffix or source.suffix.lower()}"
    if not destination.exists():
        destination.write_bytes(source.read_bytes())
    if sha256_file(destination) != digest:
        raise SourceReadinessError("content-addressed evidence copy mismatch")
    return destination


def _measure_file_name(source_subject: str) -> str:
    congress, measure_type, number = source_subject.split(":")
    return f"{congress}_{measure_type}_{number}.json"


def _exact_house_action(
    payload: dict[str, Any],
    *,
    action_id: str,
    action_date: str,
    roll_number: int,
    stage: str,
) -> str:
    candidates = []
    for action in payload.get("actions", []):
        if action.get("actionDate") != action_date:
            continue
        if action.get("sourceSystem", {}).get("name") != "House floor actions":
            continue
        text = str(action.get("text") or "")
        if f"Roll no. {roll_number}" not in text:
            continue
        lowered = text.casefold()
        if stage == "suspension_passage_as_amended":
            matches = (
                "suspend the rules and pass" in lowered and "as amended" in lowered
            )
        elif stage == "suspension_passage":
            matches = (
                "suspend the rules and pass" in lowered and "as amended" not in lowered
            )
        else:
            matches = "on passage passed" in lowered
        if matches:
            candidates.append(text)
    if len(candidates) != 1:
        raise SourceReadinessError(
            f"exact House action record is not unique: {action_id}"
        )
    return candidates[0]


def _select_operative_text(
    payload: dict[str, Any],
    *,
    source_subject: str,
    action_date: str,
    stage: str,
    exact_action_description: str,
) -> tuple[str, str]:
    _congress, measure_type, _number = source_subject.split(":")
    versions = payload.get("textVersions", [])
    if measure_type == "s":
        if stage != "passage" or "as amended" in exact_action_description.casefold():
            raise SourceReadinessError(
                "Senate measure lacks a stage-equivalent House operative version"
            )
        wanted_type = "Enrolled Bill"
    else:
        wanted_type = "Engrossed in House"
    matching = []
    for version in versions:
        if version.get("type") != wanted_type:
            continue
        version_date = str(version.get("date") or "")[:10]
        if measure_type != "s" and version_date != action_date:
            continue
        xml_urls = [
            item.get("url")
            for item in version.get("formats", [])
            if item.get("type") == "Formatted XML" and item.get("url")
        ]
        if len(xml_urls) == 1:
            matching.append(str(xml_urls[0]))
    if len(matching) != 1:
        raise SourceReadinessError(
            f"stage-compatible operative text is not unique: {source_subject}"
        )
    match = re.search(r"BILLS-119(?:hr|s)\d+([a-z]+)\.xml$", matching[0])
    if not match:
        raise SourceReadinessError("operative text URL lacks a version code")
    return match.group(1), matching[0]


def _acquire_operative_xml(
    url: str,
    *,
    evidence_dir: Path,
    acquire_missing: bool,
) -> Path:
    host = (urlparse(url).hostname or "").casefold()
    if host not in ALLOWED_RAW_HOSTS:
        raise SourceReadinessError("operative text host is not allowlisted")
    name = Path(urlparse(url).path).name
    cached = sorted(evidence_dir.glob(f"*_{name}"))
    if cached:
        return cached[0]
    if not acquire_missing:
        raise SourceReadinessError(f"operative text evidence missing: {name}")
    temporary = evidence_dir / f"acquiring_{name}"
    download_to_path(url, temporary, overwrite=True)
    digest = sha256_file(temporary)
    destination = evidence_dir / f"{digest}_{name}"
    temporary.replace(destination)
    return destination


def _prepare_congress_action_and_text_sources(
    *,
    action_id: str,
    canonical: dict[str, Any],
    vote_projection: dict[str, Any],
    congress_actions_dirs: list[Path],
    congress_text_dirs: list[Path],
    evidence_dir: Path,
    repository_root: Path,
    acquire_missing: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    source_subject = canonical["exact_measure_or_amendment_identity"]
    file_name = _measure_file_name(source_subject)
    action_paths = [path / file_name for path in congress_actions_dirs]
    text_paths = [path / file_name for path in congress_text_dirs]
    action_path = next((path for path in action_paths if path.is_file()), None)
    text_path = next((path for path in text_paths if path.is_file()), None)
    if action_path is None or text_path is None:
        raise SourceReadinessError(
            f"Congress action/text acquisition is missing: {action_id}"
        )
    action_payload = load_json(action_path)
    text_payload = load_json(text_path)
    exact_description = _exact_house_action(
        action_payload,
        action_id=action_id,
        action_date=vote_projection["vote_date"],
        roll_number=vote_projection["rollcall_number"],
        stage=canonical["house_action_stage"],
    )
    action_raw_path = _copy_content_addressed(
        action_path, evidence_dir=evidence_dir, suffix=".json"
    )
    action_raw = _governed_raw(action_raw_path, repository_root=repository_root)
    action_url = (
        "https://api.congress.gov/v3/bill/"
        + source_subject.replace(":", "/")
        + "/actions"
    )
    action_projection = _neutral_projection(
        action_id=action_id,
        canonical=canonical,
        vote_projection=vote_projection,
        text_version="official_house_action_list_v3",
        source_url=action_url,
        raw_sha256=action_raw["sha256"],
        official_action_description=exact_description,
        operative_content_sha256=None,
    )
    action_source = _source_record(
        source_id=f"congress_actions:{action_id}",
        source_type="congress_gov_bill_actions",
        source_subject=source_subject,
        url=action_url,
        text_version="official_house_action_list_v3",
        content_class="exact_house_action_record",
        raw_provenance=action_raw,
        neutral_projection=action_projection,
        m3_input_eligible=True,
    )

    text_version, text_url = _select_operative_text(
        text_payload,
        source_subject=source_subject,
        action_date=vote_projection["vote_date"],
        stage=canonical["house_action_stage"],
        exact_action_description=exact_description,
    )
    xml_path = _acquire_operative_xml(
        text_url,
        evidence_dir=evidence_dir,
        acquire_missing=acquire_missing,
    )
    text_raw = _governed_raw(xml_path, repository_root=repository_root)
    text_projection = _neutral_projection(
        action_id=action_id,
        canonical=canonical,
        vote_projection=vote_projection,
        text_version=text_version,
        source_url=text_url,
        raw_sha256=text_raw["sha256"],
        official_action_description=exact_description,
        operative_content_sha256=text_raw["sha256"],
    )
    text_source = _source_record(
        source_id=f"congress_text:{source_subject}:{text_version}",
        source_type="congress_gov_bill_text",
        source_subject=source_subject,
        url=text_url,
        text_version=text_version,
        content_class="operative_legislative_text",
        raw_provenance=text_raw,
        neutral_projection=text_projection,
        m3_input_eligible=True,
    )

    raw_only = None
    metadata_name = RAW_METADATA_FILES.get(action_id)
    if metadata_name:
        metadata_path = evidence_dir / metadata_name
        if not metadata_path.is_file():
            raise SourceReadinessError(
                f"preserved generic bill metadata is missing: {action_id}"
            )
        metadata_raw = _governed_raw(metadata_path, repository_root=repository_root)
        raw_only = {
            "source_id": f"congress_bill_metadata:{source_subject}",
            "source_type": "congress_gov_bill_metadata",
            "source_subject": source_subject,
            "url": (
                "https://api.congress.gov/v3/bill/" + source_subject.replace(":", "/")
            ),
            "raw_provenance": metadata_raw,
            "m3_input_eligible": False,
            "exclusion_reason": "generic_bill_metadata_contains_non_allowlisted_fields",
        }
    return [action_source, text_source], raw_only


def _prepare_existing_source(
    binding: dict[str, Any],
    *,
    action_id: str,
    canonical: dict[str, Any],
    vote_projection: dict[str, Any],
    evidence_dir: Path,
    repository_root: Path,
    acquire_missing: bool,
) -> dict[str, Any]:
    host = (urlparse(binding["url"]).hostname or "").casefold()
    if host not in ALLOWED_RAW_HOSTS:
        raise SourceReadinessError("raw official source host is not allowlisted")
    suffix = _raw_suffix(binding["url"])
    path = evidence_dir / f"{binding['source_content_sha256']}{suffix}"
    if not path.exists():
        if not acquire_missing:
            raise SourceReadinessError(
                f"official source file missing: {binding['source_id']}"
            )
        download_to_path(binding["url"], path)
    if sha256_file(path) != binding["source_content_sha256"]:
        raise SourceReadinessError(
            f"official source digest mismatch: {binding['source_id']}"
        )
    raw = _governed_raw(path, repository_root=repository_root)
    source_type = binding["source_type"]
    if source_type == "govinfo_bill_status":
        content_class = "official_status_record"
        operative_sha = None
    elif source_type in {"govinfo_bill_text"}:
        content_class = "operative_legislative_text"
        operative_sha = raw["sha256"]
    else:
        content_class = "exact_amendment_or_rule_text"
        operative_sha = raw["sha256"]
    projection = _neutral_projection(
        action_id=action_id,
        canonical=canonical,
        vote_projection=vote_projection,
        text_version=binding["text_version"],
        source_url=binding["url"],
        raw_sha256=raw["sha256"],
        official_action_description=vote_projection["question"],
        operative_content_sha256=operative_sha,
    )
    return _source_record(
        source_id=binding["source_id"],
        source_type=source_type,
        source_subject=binding["source_subject"],
        url=binding["url"],
        text_version=binding["text_version"],
        content_class=content_class,
        raw_provenance=raw,
        neutral_projection=projection,
        m3_input_eligible=True,
    )


def prepare_source_manifest(
    *,
    repository_root: Path,
    approved_manifest: dict[str, Any],
    discovery: dict[str, Any],
    clerk_dirs: list[Path],
    congress_dirs: list[Path],
    evidence_dir: Path,
    acquire_missing: bool,
    congress_actions_dirs: list[Path] | None = None,
    congress_text_dirs: list[Path] | None = None,
) -> dict[str, Any]:
    del congress_dirs  # Generic bill metadata is provenance-only in corrected M2.
    evidence_dir.mkdir(parents=True, exist_ok=True)
    actions_dirs = congress_actions_dirs or []
    text_dirs = congress_text_dirs or []
    approved = approved_manifest["action_ids"]
    rows = {row["action_id"]: row for row in discovery["candidate_dispositions"]}
    official = {
        row["canonical_action_id"]: row
        for row in load_house_clerk_member_actions(
            clerk_dirs, bioguide_id=approved_manifest["subject"]["member_id"]
        )
    }
    action_sources: list[dict[str, Any]] = []
    for action_id in approved:
        candidate = rows.get(action_id)
        if candidate is None or candidate.get("exact_action_source_binding") is None:
            raise SourceReadinessError(f"approved action source missing: {action_id}")
        canonical = candidate["exact_action_source_binding"]
        vote_binding = canonical["vote_source_bindings"][0]
        acquired_vote_file: dict[str, str] | None = None
        if action_id not in official:
            if not acquire_missing:
                raise SourceReadinessError(
                    f"official Clerk action missing: {action_id}"
                )
            _chamber, congress_number, session_number, roll_number = action_id.split(
                ":"
            )
            path = evidence_dir / (
                f"roll{congress_number}_{session_number}_{int(roll_number):03d}.xml"
            )
            download_to_path(vote_binding["url"], path)
            loaded = load_house_clerk_member_actions(
                [path.parent],
                bioguide_id=approved_manifest["subject"]["member_id"],
            )
            official.update({row["canonical_action_id"]: row for row in loaded})
            if action_id not in official:
                raise SourceReadinessError(
                    f"acquired Clerk action missing member vote: {action_id}"
                )
            acquired_vote_file = _governed_raw(path, repository_root=repository_root)
        vote_projection = _official_projection(official[action_id])
        if sha256_json(vote_projection) != vote_binding["source_content_sha256"]:
            raise SourceReadinessError(f"vote projection digest mismatch: {action_id}")
        member_projection = _neutral_projection(
            action_id=action_id,
            canonical=canonical,
            vote_projection=vote_projection,
            text_version=vote_binding["text_version"],
            source_url=vote_binding["url"],
            raw_sha256=(acquired_vote_file or {}).get("sha256"),
            official_action_description=vote_projection["question"],
            operative_content_sha256=None,
        )
        member_source = _source_record(
            source_id=vote_binding["source_id"],
            source_type="house_clerk_roll_call",
            source_subject=action_id,
            url=vote_binding["url"],
            text_version=vote_binding["text_version"],
            content_class="member_action_record",
            raw_provenance=acquired_vote_file,
            neutral_projection=member_projection,
            m3_input_eligible=True,
        )

        bindings = canonical["exact_action_meaning_source_bindings"]
        if any(
            binding["source_type"] == "congress_gov_action_record"
            for binding in bindings
        ):
            exact_sources, raw_only = _prepare_congress_action_and_text_sources(
                action_id=action_id,
                canonical=canonical,
                vote_projection=vote_projection,
                congress_actions_dirs=actions_dirs,
                congress_text_dirs=text_dirs,
                evidence_dir=evidence_dir,
                repository_root=repository_root,
                acquire_missing=acquire_missing,
            )
        else:
            exact_sources = []
            for binding in bindings:
                if (
                    binding["digest_basis"]
                    == "canonical_official_page_projection_sha256"
                ):
                    continue
                exact_sources.append(
                    _prepare_existing_source(
                        binding,
                        action_id=action_id,
                        canonical=canonical,
                        vote_projection=vote_projection,
                        evidence_dir=evidence_dir,
                        repository_root=repository_root,
                        acquire_missing=acquire_missing,
                    )
                )
            raw_only = None
        identity_ids = [
            source["source_id"]
            for source in exact_sources
            if source["content_class"] in IDENTITY_STAGE_CONTENT_CLASSES
        ]
        operative_ids = [
            source["source_id"]
            for source in exact_sources
            if source["content_class"] in OPERATIVE_CONTENT_CLASSES
        ]
        action_sources.append(
            {
                "action_id": action_id,
                "role_bindings": {
                    "member_action_evidence": [member_source["source_id"]],
                    "exact_action_identity_and_stage_evidence": identity_ids,
                    "operative_content_interpretation_input": operative_ids,
                },
                "sources": [member_source, *exact_sources],
                "raw_provenance_only_sources": [raw_only] if raw_only else [],
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
        "projection_schema_version": PROJECTION_VERSION,
        "allowlisted_source_types": sorted(ALLOWED_SOURCE_TYPES),
        "m3_eligible_source_types": sorted(M3_ELIGIBLE_SOURCE_TYPES),
        "raw_provenance_only_source_types": sorted(RAW_PROVENANCE_ONLY_SOURCE_TYPES),
        "governed_roots": list(GOVERNED_ROOTS),
        "subject": subject,
        "source_manifest_subject_sha256": sha256_json(subject),
    }
    assert_no_semantic_leakage(
        [
            source["neutral_projection"]
            for row in action_sources
            for source in row["sources"]
            if source["neutral_projection"] is not None
        ]
    )
    return result


def _resolve_governed_path(relative: str, *, repository_root: Path) -> Path:
    if not any(relative.startswith(root) for root in GOVERNED_ROOTS):
        raise SourceReadinessError("source path escapes governed root")
    path = (repository_root / relative).resolve()
    root = repository_root.resolve()
    if root not in path.parents or not path.is_file():
        raise SourceReadinessError("governed source path is missing or unsafe")
    return path


def _xml_has_operative_body(path: Path) -> bool:
    sample = path.read_bytes()
    return b"<legis-body" in sample and b"</legis-body>" in sample


def validate_source_manifest(
    value: dict[str, Any],
    *,
    repository_root: Path,
    approved_manifest: dict[str, Any],
    discovery: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    if value["schema_version"] != SOURCE_MANIFEST_VERSION:
        raise SourceReadinessError("source manifest version mismatch")
    if value["allowlisted_source_types"] != sorted(ALLOWED_SOURCE_TYPES):
        raise SourceReadinessError("source manifest allowlist mismatch")
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
        source_by_id = {source["source_id"]: source for source in row["sources"]}
        if len(source_by_id) != len(row["sources"]):
            raise SourceReadinessError(f"duplicate source identity: {action_id}")
        for role, source_ids in row["role_bindings"].items():
            if len(source_ids) != len(set(source_ids)):
                raise SourceReadinessError(f"duplicate role binding: {action_id}")
            if any(source_id not in source_by_id for source_id in source_ids):
                raise SourceReadinessError(f"unknown role source: {action_id}")
            if role == "operative_content_interpretation_input":
                if any(
                    source_by_id[source_id]["content_class"]
                    not in OPERATIVE_CONTENT_CLASSES
                    for source_id in source_ids
                ):
                    raise SourceReadinessError(
                        f"identity-only source escalated to operative content: {action_id}"
                    )
        for source in row["sources"]:
            if source["source_type"] not in ALLOWED_SOURCE_TYPES:
                raise SourceReadinessError("unapproved source type")
            if source["m3_input_eligible"]:
                if source["source_type"] not in M3_ELIGIBLE_SOURCE_TYPES:
                    raise SourceReadinessError("raw metadata exposed as M3 input")
                projection = source["neutral_projection"]
                assert_no_semantic_leakage(projection)
                if sha256_json(projection) != source["neutral_projection_sha256"]:
                    raise SourceReadinessError("neutral projection digest mismatch")
                if projection["action_id"] != action_id:
                    raise SourceReadinessError("neutral projection action mismatch")
                if (
                    projection["measure_identity"]
                    != canonical["exact_measure_or_amendment_identity"]
                    or projection["house_action_stage"]
                    != canonical["house_action_stage"]
                ):
                    raise SourceReadinessError("neutral projection identity mismatch")
            raw = source["raw_provenance"]
            if raw is not None:
                path = _resolve_governed_path(
                    raw["governed_local_path"], repository_root=repository_root
                )
                if sha256_file(path) != raw["sha256"]:
                    raise SourceReadinessError("raw provenance digest mismatch")
                projection = source["neutral_projection"]
                if projection and projection["raw_provenance_sha256"] != raw["sha256"]:
                    raise SourceReadinessError("projection/raw provenance mismatch")
                if source["content_class"] == "operative_legislative_text":
                    if path.suffix.casefold() != ".xml" or not _xml_has_operative_body(
                        path
                    ):
                        raise SourceReadinessError(
                            "operative legislative text is not mechanism-bearing XML"
                        )
                    if projection["operative_content_sha256"] != raw["sha256"]:
                        raise SourceReadinessError("operative content digest mismatch")
                elif source["content_class"] == "exact_amendment_or_rule_text":
                    if (
                        path.suffix.casefold() != ".pdf"
                        or not path.read_bytes().startswith(b"%PDF")
                    ):
                        raise SourceReadinessError(
                            "exact amendment/rule evidence is not an official PDF"
                        )
                    if projection["operative_content_sha256"] != raw["sha256"]:
                        raise SourceReadinessError(
                            "exact amendment content digest mismatch"
                        )
                elif source["content_class"] == "exact_house_action_record":
                    payload = load_json(path)
                    exact = _exact_house_action(
                        payload,
                        action_id=action_id,
                        action_date=projection["action_date"],
                        roll_number=projection["roll_number"],
                        stage=projection["house_action_stage"],
                    )
                    if exact != projection["official_action_description"]:
                        raise SourceReadinessError(
                            "exact action projection differs from raw record"
                        )
            if source["content_class"] == "operative_legislative_text":
                version = source["text_version"]
                stage = canonical["house_action_stage"]
                if stage == "suspension_passage_as_amended" and version != "eh":
                    raise SourceReadinessError(
                        "as-amended suspension uses wrong text version"
                    )
                if stage in {"passage", "suspension_passage"} and version not in {
                    "eh",
                    "enr",
                    "cdh",
                    "es",
                }:
                    raise SourceReadinessError("passage uses incompatible text version")
        for raw_only in row["raw_provenance_only_sources"]:
            if (
                raw_only["source_type"] not in RAW_PROVENANCE_ONLY_SOURCE_TYPES
                or raw_only["m3_input_eligible"]
            ):
                raise SourceReadinessError("raw-only provenance became M3 eligible")
            raw = raw_only["raw_provenance"]
            path = _resolve_governed_path(
                raw["governed_local_path"], repository_root=repository_root
            )
            if sha256_file(path) != raw["sha256"]:
                raise SourceReadinessError("raw-only provenance digest mismatch")
        result[action_id] = row
    return result


def _source_binding_projection(source: dict[str, Any]) -> dict[str, Any]:
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


def _derive_source_state_builder(
    row: dict[str, Any], *, canonical: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, bool]]:
    source_by_id = {source["source_id"]: source for source in row["sources"]}
    roles = row["role_bindings"]
    member = [source_by_id[source_id] for source_id in roles["member_action_evidence"]]
    identity = [
        source_by_id[source_id]
        for source_id in roles["exact_action_identity_and_stage_evidence"]
    ]
    operative = [
        source_by_id[source_id]
        for source_id in roles["operative_content_interpretation_input"]
    ]
    all_role_sources = [*member, *identity, *operative]
    projection_ready = all(
        source["m3_input_eligible"]
        and source["neutral_projection"] is not None
        and source["neutral_projection_sha256"]
        == sha256_json(source["neutral_projection"])
        for source in all_role_sources
    )
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
        "neutral_m3_projection_state": "available" if projection_ready else "missing",
        "raw_provenance_state": raw_state,
        "source_availability_state": (
            "available"
            if member and identity and operative and projection_ready
            else "missing"
        ),
        "source_conflict_state": "conflicting" if conflict else "none",
        "source_constraint_state": "blocked" if constrained else "none",
    }
    criteria = {
        "vote_source_present": bool(member),
        "exact_action_source_present": bool(identity),
        "operative_content_source_present": bool(operative),
        "governed_source_exists": all(
            source["raw_provenance"] is not None
            or source["neutral_projection"] is not None
            for source in all_role_sources
        ),
        "text_version_explicit": all(
            source["text_version"] for source in all_role_sources
        ),
        "all_source_digests_valid": projection_ready,
        "no_source_conflict": not conflict,
        "no_source_constraint": not constrained,
        "all_paths_governed": all(
            source["raw_provenance"] is None
            or any(
                source["raw_provenance"]["governed_local_path"].startswith(root)
                for root in GOVERNED_ROOTS
            )
            for source in all_role_sources
        ),
        "approved_source_types_only": all(
            source["source_type"] in M3_ELIGIBLE_SOURCE_TYPES
            for source in all_role_sources
        ),
    }
    return state, criteria


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
        canonical = candidates[action_id]["exact_action_source_binding"]
        source_row = source_rows[action_id]
        source_by_id = {source["source_id"]: source for source in source_row["sources"]}
        member_source = source_by_id[
            source_row["role_bindings"]["member_action_evidence"][0]
        ]
        projection = member_source["neutral_projection"]
        memberships = approved_manifest["cross_domain_memberships"].get(
            action_id, [approved_manifest["subject"]["issue_id"]]
        )
        limitations = approved_manifest["cross_domain_scope_limitations"].get(
            action_id, []
        )
        state, source_criteria = _derive_source_state_builder(
            source_row, canonical=canonical
        )
        operative_sources = [
            source_by_id[source_id]
            for source_id in source_row["role_bindings"][
                "operative_content_interpretation_input"
            ]
        ]
        criteria = {
            "approved_universe_member": action_id in approved_manifest["action_ids"],
            "stable_action_identity": bool(action_id),
            "official_member_action_resolved": projection["member_action"]
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
            "no_semantic_leakage": all(
                not (set(_walk_keys(source["neutral_projection"])) & FORBIDDEN_KEYS)
                for source in source_row["sources"]
                if source["neutral_projection"] is not None
            ),
        }
        role_source_bindings = {
            role: [
                _source_binding_projection(source_by_id[source_id])
                for source_id in source_ids
            ]
            for role, source_ids in source_row["role_bindings"].items()
        }
        raw_only = [
            {
                "source_id": source["source_id"],
                "source_type": source["source_type"],
                "source_subject": source["source_subject"],
                "raw_provenance_sha256": source["raw_provenance"]["sha256"],
                "m3_input_eligible": False,
                "exclusion_reason": source["exclusion_reason"],
            }
            for source in source_row["raw_provenance_only_sources"]
        ]
        record = {
            "action_id": action_id,
            "official_action_date": projection["action_date"],
            "congress": projection["congress"],
            "session": int(action_id.split(":")[2]),
            "roll_number": projection["roll_number"],
            "official_member_action": projection["member_action"],
            "exact_action_identity": canonical["exact_measure_or_amendment_identity"],
            "house_action_stage": canonical["house_action_stage"],
            "role_source_bindings": role_source_bindings,
            "raw_provenance_only_bindings": raw_only,
            "source_state": state,
            "operative_text_versions": sorted(
                {source["text_version"] for source in operative_sources}
            ),
            "cross_domain_memberships": memberships,
            "cross_domain_scope_limitations": limitations,
            "readiness_criteria": criteria,
        }
        blockers = _derive_blockers(criteria)
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
        "result": (
            "complete_ready" if aggregate["blocked_count"] == 0 else "complete_blocked"
        ),
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
        "| Action ID | Stage | Member action | Identity/stage | Operative content | Operative version | Neutral M3 projection | Raw provenance | Readiness | Blockers |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in subject["action_readiness"]:
        state = row["source_state"]
        blockers = ", ".join(row["blocker_codes"]) or "none"
        versions = ", ".join(row["operative_text_versions"]) or "missing"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['action_id']}`",
                    row["house_action_stage"],
                    state["member_action_evidence_state"],
                    state["identity_and_stage_source_state"],
                    state["operative_content_source_state"],
                    versions,
                    state["neutral_m3_projection_state"],
                    state["raw_provenance_state"],
                    row["readiness_state"],
                    blockers,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Raw official provenance is bound separately from closed neutral M3 projections. Raw metadata that contains excluded fields is not M3-input eligible.",
            "",
            "The packet grants no interpretation, episode, semantic, synthesis, persistence, or publication authority.",
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
