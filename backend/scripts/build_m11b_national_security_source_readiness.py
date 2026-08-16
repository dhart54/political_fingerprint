from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from jsonschema import Draft7Validator, FormatChecker

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.etl.fetch_sources import download_to_path  # noqa: E402
from app.etl.full_record_source_readiness import (  # noqa: E402
    PROJECTION_VERSION,
    assert_neutral_projection,
    build_readiness_artifact,
    canonical_file_sha256,
    load_json,
    sha256_file,
    sha256_json,
    validate_artifact,
    write_json,
)
from app.etl.universe_discovery import load_house_clerk_member_actions  # noqa: E402


M11A_ROOT = Path("docs/editorial/cross_issue_full_record_expansion_v1")
PROPOSAL_PATH = M11A_ROOT / "selected_domain_universe_proposal.json"
INVENTORY_PATH = M11A_ROOT / "source_inventory.json"
SELECTION_PATH = M11A_ROOT / "domain_selection.json"
AUTHORITY_PATH = Path(
    "docs/editorial/full_record_reviews/"
    "f000477_national_security_foreign_119_full_issue_universe_authority_receipt_v1.json"
)
SCHEMA_PATH = Path(
    "docs/methodology/full_record_interpretation_source_readiness_v1.schema.json"
)
SOURCE_ROOT = Path("docs/editorial/full_record_reviews/source_readiness")
EVIDENCE_ROOT = SOURCE_ROOT / "evidence/f000477_national_security_foreign_119_v1"
ARTIFACT_PATH = (
    SOURCE_ROOT
    / "f000477_national_security_foreign_119_interpretation_source_readiness_v1.json"
)
REPORT_PATH = (
    SOURCE_ROOT
    / "f000477_national_security_foreign_119_interpretation_source_readiness_v1.md"
)
DEFAULT_CACHE = ROOT / ".local/m11b_national_security_source_readiness"
CLERK_DIRS = (
    ROOT / ".local/m11a_house_clerk/2025",
    ROOT / ".local/m11a_house_clerk/2026",
)
AMENDMENT_DIR = ROOT / ".local/m11a_national_security_congress/amendments"
RULES_REPORT_PATH = (
    ROOT / "docs/editorial/full_record_reviews/source_readiness/evidence/"
    "10371c5bbbd18827c0aa7b59c41fb9e7c5fc938a80388ef10ae5cafb3c5aebab.pdf"
)
RULES_REPORT_URL = (
    "https://docs.house.gov/billsthisweek/20260720/RulesReport07202026.pdf"
)

ARTIFACT_ID = "interpretation-source-readiness:f000477:national_security_foreign:119:v1"


def _date(value: str) -> str:
    for fmt in ("%d-%b-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"unsupported action date: {value}")


def _copy_content_addressed(
    source: Path, *, logical_name: str, evidence_root: Path
) -> dict[str, str]:
    digest = sha256_file(source)
    destination = evidence_root / f"{digest}_{logical_name}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copyfile(source, destination)
    if sha256_file(destination) != digest:
        raise ValueError(f"content-addressed evidence mismatch: {destination}")
    return {
        "governed_local_path": destination.relative_to(ROOT).as_posix(),
        "sha256": digest,
    }


def _projection(
    *,
    action: dict[str, Any],
    source_id: str,
    exact_identity: str,
    stage: str,
    source_url: str,
    text_version: str,
    raw_sha256: str,
    official_action_description: str | None = None,
    official_purpose: str | None = None,
    official_description: str | None = None,
) -> dict[str, Any]:
    value = {
        "schema_version": PROJECTION_VERSION,
        "action_id": action["canonical_action_id"],
        "source_id": source_id,
        "congress": action["congress"],
        "chamber": action["chamber"],
        "exact_action_identity": exact_identity,
        "house_action_stage": stage,
        "action_date": action["vote_date"],
        "roll_number": action["rollcall_number"],
        "member_action": action["member_action"],
        "official_action_description": official_action_description,
        "official_purpose": official_purpose,
        "official_description": official_description,
        "text_version": text_version,
        "source_url": source_url,
        "raw_provenance_sha256": raw_sha256,
    }
    assert_neutral_projection(value)
    return value


def _source(
    *,
    source_id: str,
    source_type: str,
    source_subject: str,
    content_class: str,
    source_url: str,
    raw: dict[str, str],
    projection: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_type": source_type,
        "source_subject": source_subject,
        "content_class": content_class,
        "source_url": source_url,
        "raw_provenance": raw,
        "neutral_projection": projection,
        "neutral_projection_sha256": sha256_json(projection),
    }


def _file_name(identity: str) -> str:
    congress, kind, number = identity.split(":")
    return f"{congress}_{kind}_{number}.json"


def _exact_house_action(
    payload: dict[str, Any], *, action_id: str, roll: int, action_date: str
) -> str:
    matches = {
        str(item.get("text") or "")
        for item in payload.get("actions", [])
        if item.get("actionDate") == action_date
        and re.search(rf"\bRoll no\. {roll}\b", str(item.get("text") or ""))
    }
    meaningful = sorted(text for text in matches if text)
    if not meaningful:
        raise ValueError(f"exact House action record missing: {action_id}")
    passed = [text for text in meaningful if "Passed/agreed to in House:" in text]
    failed = [
        text
        for text in meaningful
        if "Failed of passage/not agreed to in House" in text
    ]
    selected = passed or failed or meaningful
    if len(selected) != 1:
        raise ValueError(f"exact House action record is not unique: {action_id}")
    return selected[0]


def _formatted_xml(version: dict[str, Any]) -> str:
    urls = [
        item["url"]
        for item in version.get("formats", [])
        if item.get("type") == "Formatted XML" and item.get("url")
    ]
    if len(urls) != 1:
        raise ValueError("text version lacks one official formatted XML URL")
    return str(urls[0])


def _select_text_version(
    payload: dict[str, Any],
    *,
    identity: str,
    action_date: str,
    official_action_description: str,
) -> tuple[str, str, str]:
    _congress, measure_type, _number = identity.split(":")
    lowered = official_action_description.casefold()
    if measure_type in {"s", "sjres"}:
        wanted = (
            "Engrossed Amendment House"
            if "amendment in the nature of a substitute" in lowered
            else "Engrossed in Senate"
        )
    elif "failed of passage/not agreed to in house" in lowered:
        wanted = (
            "Committee Discharged House"
            if measure_type == "hr"
            else "Introduced in House"
        )
    else:
        wanted = "Engrossed in House"

    candidates = [
        version
        for version in payload.get("textVersions", [])
        if version.get("type") == wanted
    ]
    if measure_type not in {"s"} and wanted == "Engrossed in House":
        candidates = [
            version
            for version in candidates
            if str(version.get("date") or "")[:10] == action_date
        ]
    if wanted == "Engrossed Amendment House":
        candidates = [
            version
            for version in candidates
            if str(version.get("date") or "")[:10] == action_date
        ]
    if len(candidates) != 1:
        raise ValueError(
            f"stage-compatible text is not unique: {identity} {wanted} {action_date}"
        )
    url = _formatted_xml(candidates[0])
    match = re.search(
        r"BILLS-119(?:hr|s|hconres|hjres|hres|sconres|sjres)\d+([a-z]+)\.xml$",
        url,
    )
    if not match:
        raise ValueError(f"official text URL lacks version code: {url}")
    return wanted, match.group(1), url


def _acquire_xml(url: str, *, cache_root: Path, acquire_missing: bool) -> Path:
    name = Path(urlparse(url).path).name
    destination = cache_root / "operative_texts" / name
    if destination.is_file():
        return destination
    if not acquire_missing:
        raise ValueError(f"missing acquired operative text: {name}")
    download_to_path(url, destination)
    return destination


def _clerk_source(
    action: dict[str, Any],
    *,
    exact_identity: str,
    stage: str,
    evidence_root: Path,
) -> dict[str, Any]:
    year = 2024 + action["session"]
    source_path = (
        ROOT / f".local/m11a_house_clerk/{year}/roll{action['rollcall_number']:03d}.xml"
    )
    raw = _copy_content_addressed(
        source_path,
        logical_name=f"roll119_{action['session']}_{action['rollcall_number']:03d}.xml",
        evidence_root=evidence_root,
    )
    source_id = f"clerk:{action['canonical_action_id']}"
    projection = _projection(
        action=action,
        source_id=source_id,
        exact_identity=exact_identity,
        stage=stage,
        source_url=action["source_url"],
        text_version=action["vote_date"],
        raw_sha256=raw["sha256"],
        official_action_description=action["question"],
    )
    return _source(
        source_id=source_id,
        source_type="house_clerk_roll_call",
        source_subject=action["canonical_action_id"],
        content_class="member_action_record",
        source_url=action["source_url"],
        raw=raw,
        projection=projection,
    )


def _amendment_source(
    action: dict[str, Any],
    *,
    row: dict[str, Any],
    identity: str,
    evidence_root: Path,
) -> dict[str, Any]:
    _congress, _kind, number = identity.split(":")
    parent_name = row["bill_ref"].replace("bill_119_", "119_") + ".json"
    source_path = AMENDMENT_DIR / parent_name
    payload = load_json(source_path)
    matches = [item for item in payload["amendments"] if str(item["number"]) == number]
    if len(matches) != 1:
        raise ValueError(f"exact amendment record is not unique: {identity}")
    amendment = matches[0]
    latest = amendment.get("latestAction") or {}
    if str(latest.get("actionDate")) != action["vote_date"] or not re.search(
        rf"\bRoll no\. {action['rollcall_number']}\b", str(latest.get("text") or "")
    ):
        raise ValueError(f"amendment action binding mismatch: {identity}")
    raw = _copy_content_addressed(
        source_path, logical_name=parent_name, evidence_root=evidence_root
    )
    source_id = f"congress-amendment:{identity}"
    source_url = str(amendment["url"])
    projection = _projection(
        action=action,
        source_id=source_id,
        exact_identity=identity,
        stage="amendment",
        source_url=source_url,
        text_version="official_amendment_purpose_or_description_v3",
        raw_sha256=raw["sha256"],
        official_action_description=str(latest["text"]),
        official_purpose=amendment.get("purpose"),
        official_description=amendment.get("description"),
    )
    return _source(
        source_id=source_id,
        source_type="congress_gov_amendment_index",
        source_subject=identity,
        content_class="exact_amendment_purpose",
        source_url=source_url,
        raw=raw,
        projection=projection,
    )


def _whole_measure_sources(
    action: dict[str, Any],
    *,
    identity: str,
    stage: str,
    cache_root: Path,
    evidence_root: Path,
    acquire_missing: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    file_name = _file_name(identity)
    action_path = cache_root / "actions" / file_name
    text_index_path = cache_root / "text_indexes" / file_name
    action_payload = load_json(action_path)
    exact_description = _exact_house_action(
        action_payload,
        action_id=action["canonical_action_id"],
        roll=action["rollcall_number"],
        action_date=action["vote_date"],
    )
    action_raw = _copy_content_addressed(
        action_path,
        logical_name=f"{file_name.removesuffix('.json')}_actions.json",
        evidence_root=evidence_root,
    )
    action_source_id = f"congress-actions:{action['canonical_action_id']}"
    action_url = (
        "https://api.congress.gov/v3/bill/" + identity.replace(":", "/") + "/actions"
    )
    action_projection = _projection(
        action=action,
        source_id=action_source_id,
        exact_identity=identity,
        stage=stage,
        source_url=action_url,
        text_version="official_house_action_list_v3",
        raw_sha256=action_raw["sha256"],
        official_action_description=exact_description,
    )
    action_source = _source(
        source_id=action_source_id,
        source_type="congress_gov_bill_actions",
        source_subject=identity,
        content_class="exact_house_action_record",
        source_url=action_url,
        raw=action_raw,
        projection=action_projection,
    )

    if identity == "119:hr:8800":
        text_raw = {
            "governed_local_path": RULES_REPORT_PATH.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(RULES_REPORT_PATH),
        }
        text_source_id = "house-rules-report:119:hr:8800:pre-floor-context"
        text_projection = _projection(
            action=action,
            source_id=text_source_id,
            exact_identity=identity,
            stage=stage,
            source_url=RULES_REPORT_URL,
            text_version="RulesReport07202026-pre-floor",
            raw_sha256=text_raw["sha256"],
            official_action_description=exact_description,
        )
        text_source = _source(
            source_id=text_source_id,
            source_type="house_rules_committee_report",
            source_subject=identity,
            content_class="pre_floor_house_rules_report_context",
            source_url=RULES_REPORT_URL,
            raw=text_raw,
            projection=text_projection,
        )
        return action_source, text_source

    text_index = load_json(text_index_path)
    type_name, version_code, text_url = _select_text_version(
        text_index,
        identity=identity,
        action_date=action["vote_date"],
        official_action_description=exact_description,
    )
    xml_path = _acquire_xml(
        text_url, cache_root=cache_root, acquire_missing=acquire_missing
    )
    text_raw = _copy_content_addressed(
        xml_path, logical_name=xml_path.name, evidence_root=evidence_root
    )
    measure_type = identity.split(":")[1]
    if measure_type in {"s", "sjres"}:
        content_class = "stage_compatible_senate_origin_text"
    elif measure_type in {"hconres", "hjres", "hres"}:
        content_class = "operative_resolution_text"
    else:
        content_class = "operative_measure_text"
    text_source_id = f"congress-text:{identity}:{version_code}"
    text_projection = _projection(
        action=action,
        source_id=text_source_id,
        exact_identity=identity,
        stage=stage,
        source_url=text_url,
        text_version=version_code,
        raw_sha256=text_raw["sha256"],
        official_action_description=f"{type_name}; {exact_description}",
    )
    text_source = _source(
        source_id=text_source_id,
        source_type="congress_gov_bill_text",
        source_subject=identity,
        content_class=content_class,
        source_url=text_url,
        raw=text_raw,
        projection=text_projection,
    )
    return action_source, text_source


def build(
    *, cache_root: Path, evidence_root: Path, acquire_missing: bool
) -> dict[str, Any]:
    proposal = load_json(ROOT / PROPOSAL_PATH)
    inventory = load_json(ROOT / INVENTORY_PATH)
    selection = load_json(ROOT / SELECTION_PATH)
    authority = load_json(ROOT / AUTHORITY_PATH)
    approved_ids = authority["approval_binding"]["approved_action_ids"]
    if approved_ids != proposal["proposed_action_ids"] or len(approved_ids) != 82:
        raise ValueError("M11A approved action set changed")

    candidates = {
        row["action_id"]: row
        for row in proposal["candidate_dispositions"]
        if row["action_id"] in set(approved_ids)
    }
    official_rows = {
        row["canonical_action_id"]: row
        for row in load_house_clerk_member_actions(CLERK_DIRS, bioguide_id="F000477")
    }
    action_records = []
    for action_id in approved_ids:
        row = candidates[action_id]
        action = official_rows[action_id]
        identity = row["exact_action_source_binding"]["exact_identity"]
        stage = row["house_action_stage"]
        if action["vote_date"] != _date(row["date"]):
            raise ValueError(f"official action date mismatch: {action_id}")
        clerk = _clerk_source(
            action, exact_identity=identity, stage=stage, evidence_root=evidence_root
        )
        if stage == "amendment":
            operative = _amendment_source(
                action,
                row=row,
                identity=identity,
                evidence_root=evidence_root,
            )
            sources = [clerk, operative]
            identity_roles = [operative["source_id"]]
            operative_roles = [operative["source_id"]]
            mechanism = "amendment"
            limitations = [
                "Official Congress.gov amendment purpose or description is the operative neutral projection; separate full amendment text was not required or acquired."
            ]
        else:
            action_source, operative = _whole_measure_sources(
                action,
                identity=identity,
                stage=stage,
                cache_root=cache_root,
                evidence_root=evidence_root,
                acquire_missing=acquire_missing,
            )
            sources = [clerk, action_source, operative]
            identity_roles = [action_source["source_id"]]
            if identity != "119:hr:8800":
                identity_roles.append(operative["source_id"])
            operative_roles = [operative["source_id"]]
            mechanism = (
                "resolution" if stage == "resolution_adoption" else "whole_measure"
            )
            limitations = []
            official_description = action_source["neutral_projection"][
                "official_action_description"
            ].casefold()
            if (
                mechanism == "resolution"
                and "failed of passage" in official_description
            ):
                limitations.append(
                    "The failed resolution action uses exact introduced resolution text; the official action record proves that object was before the House."
                )
            if identity == "119:hr:9238":
                limitations.append(
                    "The failed suspension action uses the official committee-discharged House text available before the vote."
                )
            if identity == "119:hr:8800":
                limitations.append(
                    "Live Congress.gov and GovInfo checks did not expose an exact House-engrossed text. The July 20 House Rules Committee report predates later floor amendment dispositions and engrossment instructions, is retained only as contextual provenance, and cannot prove the final-passage operative object."
                )
            if identity == "119:hr:2721":
                limitations.append(
                    "House Clerk and Congress.gov actionDate establish the vote on 2025-09-16, while Congress.gov's source-native Congressional Record parenthetical says 09/16/2026. The discrepancy does not redefine the canonical action date or House-engrossed text identity."
                )
            if identity == "119:s:4465":
                limitations.append(
                    "The official XML Dublin Core title says 110, but its canonical 119th-Congress URL, file identity, exact action record, and Senate-engrossed version endpoint agree on S. 4465."
                )
        action_records.append(
            {
                "action_id": action_id,
                "approved_universe_member": True,
                "congress": 119,
                "session": action["session"],
                "roll_number": action["rollcall_number"],
                "official_action_date": action["vote_date"],
                "official_member_action": action["member_action"],
                "exact_action_identity": identity,
                "mechanism_class": mechanism,
                "house_action_stage": stage,
                "source_conflict": False,
                "material_limitations": limitations,
                "source_roles": {
                    "member_action_evidence": [clerk["source_id"]],
                    "exact_action_identity_and_stage_evidence": identity_roles,
                    "operative_content_interpretation_input": operative_roles,
                },
                "sources": sources,
            }
        )

    input_bindings = {
        "authority_receipt": {
            "artifact_id": authority["receipt_id"],
            "artifact_path": AUTHORITY_PATH.as_posix(),
            "sha256": canonical_file_sha256(ROOT / AUTHORITY_PATH),
        },
        "universe_proposal": {
            "artifact_id": authority["manifest_id"],
            "artifact_path": PROPOSAL_PATH.as_posix(),
            "sha256": canonical_file_sha256(ROOT / PROPOSAL_PATH),
            "universe_subject_sha256": proposal["universe_subject_sha256"],
        },
        "selection": {
            "artifact_path": SELECTION_PATH.as_posix(),
            "sha256": selection["selection_sha256"],
        },
        "source_inventory": {
            "artifact_id": authority["approval_binding"]["source_inventory"][
                "artifact_id"
            ],
            "artifact_path": INVENTORY_PATH.as_posix(),
            "sha256": canonical_file_sha256(ROOT / INVENTORY_PATH),
            "inventory_sha256": inventory["inventory_sha256"],
        },
    }
    subject = {
        "member_name": "Valerie Foushee",
        "member_id": "F000477",
        "legislator_id": "leg_valerie_p_foushee",
        "issue_id": "NATIONAL_SECURITY_FOREIGN",
        "chamber": "house",
        "congress": 119,
        "official_cutoff": {
            "end_date": "2026-07-23",
            "latest_action_id": "house:119:2:283",
        },
        "action_ids": approved_ids,
        "action_set_sha256": authority["action_set_sha256"],
        "universe_subject_sha256": authority["universe_subject_sha256"],
    }
    return build_readiness_artifact(
        artifact_id=ARTIFACT_ID,
        input_bindings=input_bindings,
        subject=subject,
        action_records=action_records,
        repository_root=ROOT,
    )


def render_report(artifact: dict[str, Any]) -> str:
    subject = artifact["subject"]
    aggregate = subject["aggregate"]
    blocked = [
        row
        for row in subject["action_readiness"]
        if row["readiness_state"] != "ready_for_action_interpretation"
    ]
    lines = [
        "# M11B National Security Full-Record Interpretation Source Readiness V1",
        "",
        "This packet evaluates official-source readiness only. It does not establish action meaning, support/opposition, episodes, propositions, Semantic IR, synthesis, public wording, publication, or persistence authority.",
        "",
        "## Bound universe",
        "",
        f"- Member: `{subject['member_id']}`",
        f"- Issue: `{subject['issue_id']}`",
        f"- Congress/chamber: `{subject['congress']}` / `{subject['chamber']}`",
        f"- Official cutoff: `{subject['official_cutoff']['end_date']}` through `{subject['official_cutoff']['latest_action_id']}`",
        f"- Approved actions: `{aggregate['total_action_count']}`",
        f"- Action-set digest: `{subject['action_set_sha256']}`",
        f"- Universe-subject digest: `{subject['universe_subject_sha256']}`",
        "",
        "## Readiness result",
        "",
        f"- Ready for action interpretation: `{aggregate['ready_count']}`",
        f"- Blocked: `{aggregate['blocked_count']}`",
        f"- Counts by state: `{json.dumps(aggregate['counts_by_readiness_state'], sort_keys=True)}`",
        f"- Source-readiness subject digest: `{artifact['source_readiness_subject_sha256']}`",
        "",
        "## Blocked actions",
        "",
    ]
    if blocked:
        lines.extend(
            f"- `{row['action_id']}`: `{row['readiness_state']}`" for row in blocked
        )
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Authorization boundary",
            "",
            "All downstream authorization flags are false. A later milestone must separately authorize action interpretation, and no episode or semantic conclusion may be inferred from this readiness packet.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--acquire-missing", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check and args.acquire_missing:
        raise ValueError("--check cannot acquire sources")

    artifact = build(
        cache_root=args.cache_root,
        evidence_root=ROOT / EVIDENCE_ROOT,
        acquire_missing=args.acquire_missing,
    )
    schema = load_json(ROOT / SCHEMA_PATH)
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(artifact),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise ValueError(f"readiness schema failed: {errors[0].message}")
    validate_artifact(artifact, repository_root=ROOT)
    artifact_bytes = (
        json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=2).encode(
            "utf-8"
        )
        + b"\n"
    )
    report_bytes = render_report(artifact).encode("utf-8")
    if args.check:
        if (ROOT / ARTIFACT_PATH).read_bytes().replace(
            b"\r\n", b"\n"
        ) != artifact_bytes:
            raise ValueError("generated readiness artifact differs")
        if (ROOT / REPORT_PATH).read_bytes().replace(b"\r\n", b"\n") != report_bytes:
            raise ValueError("generated readiness report differs")
    else:
        write_json(ROOT / ARTIFACT_PATH, artifact)
        (ROOT / REPORT_PATH).write_bytes(report_bytes)
    print(
        json.dumps(
            {
                "status": "pass",
                "mode": "check" if args.check else "write",
                "artifact_id": artifact["artifact_id"],
                "source_readiness_subject_sha256": artifact[
                    "source_readiness_subject_sha256"
                ],
                **artifact["subject"]["aggregate"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
