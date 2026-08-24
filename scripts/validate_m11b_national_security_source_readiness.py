from __future__ import annotations

import json
import re
import sys
from pathlib import Path
import os
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    FORBIDDEN_PROJECTION_KEYS,
    SourceReadinessError,
    canonical_file_sha256,
    load_json,
    sha256_file,
    sha256_json,
    validate_artifact,
)
from backend.app.etl.universe_discovery import (  # noqa: E402
    load_house_clerk_member_actions,
)
from scripts.validate_m11a_universe_authority import (  # noqa: E402
    validate_repository as validate_m11a,
)


ARTIFACT_PATH = ROOT / (
    "docs/editorial/full_record_reviews/source_readiness/"
    "f000477_national_security_foreign_119_interpretation_source_readiness_v1.json"
)
SCHEMA_PATH = ROOT / (
    "docs/methodology/full_record_interpretation_source_readiness_v1.schema.json"
)
AUTHORITY_PATH = ROOT / (
    "docs/editorial/full_record_reviews/"
    "f000477_national_security_foreign_119_full_issue_universe_authority_receipt_v1.json"
)
PROPOSAL_PATH = ROOT / (
    "docs/editorial/cross_issue_full_record_expansion_v1/"
    "selected_domain_universe_proposal.json"
)
SELECTION_PATH = ROOT / (
    "docs/editorial/cross_issue_full_record_expansion_v1/domain_selection.json"
)
INVENTORY_PATH = ROOT / (
    "docs/editorial/cross_issue_full_record_expansion_v1/source_inventory.json"
)
CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"
CLERK_DIRS = (
    ROOT / ".local/m11a_house_clerk/2025",
    ROOT / ".local/m11a_house_clerk/2026",
)


EXPECTED_RECEIPT_SHA = (
    "89b7a27236ab0256b867c2525627408d84c6493c982c474ec4de3c2c36e79c87"
)
EXPECTED_ACTION_SET_SHA = (
    "190bda45c25cd32ae0a6847c862f85837eafc4a82dfda237746a66467c550400"
)
EXPECTED_UNIVERSE_SHA = (
    "b1e1a4588a4fcef6beb9dfd836ff5c2f32d8fdb340359f11453c6a0c947a17a5"
)
EXPECTED_SELECTION_SHA = (
    "a018b597705132f0e891c575af1dac4b880c31b0d98469f2f47001982dce0b81"
)


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


def _raw_path(source: dict[str, Any]) -> Path:
    relative = Path(source["raw_provenance"]["governed_local_path"])
    _require(
        not relative.is_absolute() and ".." not in relative.parts, "unsafe raw path"
    )
    path = (ROOT / relative).resolve()
    governed = (
        ROOT / "docs/editorial/full_record_reviews/source_readiness/evidence"
    ).resolve()
    _require(governed in path.parents, "raw source outside governed evidence")
    filesystem_path = (
        Path("\\\\?\\" + str(path))
        if os.name == "nt" and not str(path).startswith("\\\\?\\")
        else path
    )
    _require(filesystem_path.is_file(), f"raw source missing: {relative.as_posix()}")
    _require(
        sha256_file(filesystem_path) == source["raw_provenance"]["sha256"],
        f"raw source digest mismatch: {source['source_id']}",
    )
    return filesystem_path


def _governed_clerk_rows(
    records: list[dict[str, Any]],
    *,
    candidates: dict[str, dict[str, Any]],
    source_inventory_bindings: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for record in records:
        action_id = record["action_id"]
        governed_sources = [
            source
            for source in record["sources"]
            if source["source_type"] == "house_clerk_roll_call"
        ]
        approved_sources = [
            source
            for source in candidates[action_id]["sources"]
            if source["source_type"] == "house_clerk_roll_call_xml"
        ]
        inventory_sources = [
            source
            for source in source_inventory_bindings[action_id]["sources"]
            if source["source_type"] == "house_clerk_roll_call_xml"
        ]
        _require(
            len(governed_sources)
            == len(approved_sources)
            == len(inventory_sources)
            == 1,
            f"Clerk source count mismatch: {action_id}",
        )
        governed = governed_sources[0]
        approved = approved_sources[0]
        inventory = inventory_sources[0]
        _require(
            governed["raw_provenance"]["sha256"]
            == approved["sha256"]
            == inventory["sha256"],
            f"approved Clerk digest mismatch: {action_id}",
        )
        path = _raw_path(governed)
        parsed = load_house_clerk_member_actions(
            (), bioguide_id="F000477", source_paths=[path]
        )
        _require(
            len(parsed) == 1 and parsed[0]["canonical_action_id"] == action_id,
            f"governed Clerk action identity mismatch: {action_id}",
        )
        rows[action_id] = parsed[0]
    return rows


def _xml_title_and_body(path: Path) -> tuple[str, bool]:
    root = ElementTree.parse(path).getroot()
    title = ""
    for element in root.iter():
        if element.tag.endswith("title") and element.text:
            title = element.text
            break
    has_body = any(
        root.find(tag) is not None
        for tag in ("legis-body", "resolution-body", "engrossed-amendment-body")
    )
    return title, has_body


def _identity_title_signal(identity: str) -> str:
    _congress, kind, number = identity.split(":")
    title_kind = {
        "hconres": "HCON",
        "hjres": "HJ",
        "hres": "HRES",
        "sconres": "SCON",
        "sjres": "SJ",
        "sres": "SRES",
    }.get(kind, kind.upper())
    return f"119{title_kind}{number}"


def _validate_record(
    record: dict[str, Any],
    *,
    candidate: dict[str, Any],
    clerk: dict[str, Any],
) -> None:
    action_id = record["action_id"]
    identity = candidate["exact_action_source_binding"]["exact_identity"]
    _require(
        record["exact_action_identity"] == identity, f"identity mismatch: {action_id}"
    )
    _require(
        record["house_action_stage"] == candidate["house_action_stage"],
        f"stage mismatch: {action_id}",
    )
    _require(
        action_id == clerk["canonical_action_id"]
        and candidate["bill_ref"] == clerk["bill_ref"]
        and record["official_member_action"] == clerk["member_action"]
        and record["official_action_date"] == clerk["vote_date"]
        and record["roll_number"] == clerk["rollcall_number"],
        f"Clerk action mismatch: {action_id}",
    )
    sources = {source["source_id"]: source for source in record["sources"]}
    role_ids = [
        source_id for values in record["source_roles"].values() for source_id in values
    ]
    _require(
        all(source_id in sources for source_id in role_ids),
        f"role binding missing: {action_id}",
    )
    _require(
        len(record["source_roles"]["member_action_evidence"]) == 1,
        f"member role count: {action_id}",
    )

    for source in sources.values():
        path = _raw_path(source)
        projection = source["neutral_projection"]
        _require(
            sha256_json(projection) == source["neutral_projection_sha256"],
            f"projection digest mismatch: {source['source_id']}",
        )
        _require(
            not (set(_walk_keys(projection)) & FORBIDDEN_PROJECTION_KEYS),
            f"semantic or political leakage: {source['source_id']}",
        )
        _require(
            projection["action_id"] == action_id
            and projection["exact_action_identity"] == identity
            and projection["house_action_stage"] == record["house_action_stage"],
            f"projection identity/stage mismatch: {source['source_id']}",
        )
        _require(
            projection["raw_provenance_sha256"] == sha256_file(path),
            f"projection raw binding mismatch: {source['source_id']}",
        )
        _require(
            (urlparse(source["source_url"]).hostname or "")
            in {
                "api.congress.gov",
                "clerk.house.gov",
                "docs.house.gov",
                "www.congress.gov",
            },
            f"nonofficial source host: {source['source_id']}",
        )

    clerk_source = sources[record["source_roles"]["member_action_evidence"][0]]
    _require(
        clerk_source["source_type"] == "house_clerk_roll_call",
        f"member source type: {action_id}",
    )
    _require(
        sha256_file(_raw_path(clerk_source))
        == next(
            source["sha256"]
            for source in candidate["sources"]
            if source["source_type"] == "house_clerk_roll_call_xml"
        ),
        f"M11A Clerk binding changed: {action_id}",
    )

    operative_ids = record["source_roles"]["operative_content_interpretation_input"]
    _require(len(operative_ids) == 1, f"operative role count: {action_id}")
    operative = sources[operative_ids[0]]
    operative_path = _raw_path(operative)
    if record["mechanism_class"] == "amendment":
        _require(
            operative["source_type"] == "congress_gov_amendment_index",
            f"amendment source type: {action_id}",
        )
        payload = load_json(operative_path)
        number = identity.split(":")[2]
        matches = [row for row in payload["amendments"] if str(row["number"]) == number]
        _require(len(matches) == 1, f"exact amendment missing: {action_id}")
        amendment = matches[0]
        latest = amendment["latestAction"]
        _require(
            re.search(rf"\bRoll no\. {record['roll_number']}\b", latest["text"])
            and latest["actionDate"] == record["official_action_date"],
            f"amendment roll/date mismatch: {action_id}",
        )
        _require(
            bool(amendment.get("purpose") or amendment.get("description")),
            f"amendment operative purpose missing: {action_id}",
        )
        _require(
            operative["neutral_projection"]["official_purpose"]
            == amendment.get("purpose")
            and operative["neutral_projection"]["official_description"]
            == amendment.get("description"),
            f"amendment projection changed: {action_id}",
        )
        return

    action_sources = [
        source
        for source in sources.values()
        if source["source_type"] == "congress_gov_bill_actions"
    ]
    _require(len(action_sources) == 1, f"exact action-list source count: {action_id}")
    action_payload = load_json(_raw_path(action_sources[0]))
    action_matches = {
        str(item.get("text") or "")
        for item in action_payload["actions"]
        if item.get("actionDate") == record["official_action_date"]
        and re.search(
            rf"\bRoll no\. {record['roll_number']}\b", str(item.get("text") or "")
        )
    }
    _require(action_matches, f"official exact action absent: {action_id}")
    description = action_sources[0]["neutral_projection"]["official_action_description"]
    _require(
        description in action_matches,
        f"official action projection mismatch: {action_id}",
    )

    if operative["source_type"] == "house_rules_committee_report":
        _require(
            identity == "119:hr:8800"
            and operative["neutral_projection"]["text_version"]
            == "RulesReport07202026-pre-floor"
            and operative["content_class"] == "pre_floor_house_rules_report_context",
            f"unapproved Rules report context binding: {action_id}",
        )
        _require(
            record["readiness_state"] == "blocked_stage_mismatch"
            and not record["readiness_criteria"][
                "operative_text_version_stage_compatible"
            ]
            and not record["readiness_criteria"]["operative_context_sufficient"],
            f"pre-floor Rules report incorrectly satisfies final passage: {action_id}",
        )
        return
    _require(
        operative_path.suffix.lower() == ".xml",
        f"operative text is not XML: {action_id}",
    )
    title, has_body = _xml_title_and_body(operative_path)
    _require(has_body, f"operative XML body missing: {action_id}")
    _congress, identity_kind, identity_number = identity.split(":")
    file_identity = f"bills-119{identity_kind}{identity_number}"
    _require(
        _identity_title_signal(identity) in title.replace(" ", "").upper()
        or file_identity in operative_path.name.casefold(),
        f"operative XML identity mismatch: {action_id}",
    )
    version = operative["neutral_projection"]["text_version"]
    lowered = description.casefold()
    measure_type = identity.split(":")[1]
    if measure_type in {"s", "sjres"}:
        expected_version = (
            "eah" if "amendment in the nature of a substitute" in lowered else "es"
        )
    elif "failed of passage/not agreed to in house" in lowered:
        expected_version = "cdh" if measure_type == "hr" else "ih"
    else:
        expected_version = "eh"
    _require(
        version == expected_version, f"stage-incompatible text version: {action_id}"
    )
    _require(
        Path(urlparse(operative["source_url"]).path).name.endswith(f"{version}.xml"),
        f"text URL/version mismatch: {action_id}",
    )


def validate_repository() -> dict[str, Any]:
    m11a = validate_m11a()
    artifact = load_json(ARTIFACT_PATH)
    schema = load_json(SCHEMA_PATH)
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(artifact),
        key=lambda error: list(error.absolute_path),
    )
    _require(not errors, f"M11B schema failed: {errors[0].message if errors else ''}")

    authority = load_json(AUTHORITY_PATH)
    proposal = load_json(PROPOSAL_PATH)
    selection = load_json(SELECTION_PATH)
    inventory = load_json(INVENTORY_PATH)
    subject = artifact["subject"]
    approved = authority["approval_binding"]["approved_action_ids"]
    _require(
        canonical_file_sha256(AUTHORITY_PATH)
        == EXPECTED_RECEIPT_SHA
        == artifact["input_bindings"]["authority_receipt"]["sha256"],
        "authority receipt binding mismatch",
    )
    _require(
        approved == proposal["proposed_action_ids"] == subject["action_ids"]
        and len(approved) == 82,
        "82-action approved membership mismatch",
    )
    _require(
        subject["action_set_sha256"]
        == authority["action_set_sha256"]
        == EXPECTED_ACTION_SET_SHA,
        "approved action-set digest mismatch",
    )
    _require(
        subject["universe_subject_sha256"]
        == proposal["universe_subject_sha256"]
        == EXPECTED_UNIVERSE_SHA,
        "universe-subject digest mismatch",
    )
    _require(
        selection["selection_sha256"]
        == EXPECTED_SELECTION_SHA
        == artifact["input_bindings"]["selection"]["sha256"],
        "selection digest mismatch",
    )
    _require(
        artifact["input_bindings"]["source_inventory"]["inventory_sha256"]
        == inventory["inventory_sha256"]
        == authority["approval_binding"]["source_inventory"]["inventory_sha256"],
        "source inventory subject digest mismatch",
    )
    for name, path in (
        ("universe_proposal", PROPOSAL_PATH),
        ("source_inventory", INVENTORY_PATH),
    ):
        _require(
            artifact["input_bindings"][name]["sha256"] == canonical_file_sha256(path),
            f"{name} file digest mismatch",
        )
    _require(
        subject["member_id"] == "F000477"
        and subject["legislator_id"] == "leg_valerie_p_foushee"
        and subject["issue_id"] == "NATIONAL_SECURITY_FOREIGN"
        and subject["congress"] == 119
        and subject["chamber"] == "house"
        and subject["official_cutoff"]
        == {"end_date": "2026-07-23", "latest_action_id": "house:119:2:283"},
        "subject or cutoff identity mismatch",
    )

    candidate_rows = {
        row["action_id"]: row
        for row in proposal["candidate_dispositions"]
        if row["action_id"] in set(approved)
    }
    inventory_rows = {
        row["action_id"]: row for row in inventory["selected_candidate_source_bindings"]
    }
    clerk_rows = _governed_clerk_rows(
        subject["action_readiness"],
        candidates=candidate_rows,
        source_inventory_bindings=inventory_rows,
    )
    for record in subject["action_readiness"]:
        _validate_record(
            record,
            candidate=candidate_rows[record["action_id"]],
            clerk=clerk_rows[record["action_id"]],
        )
    aggregate = validate_artifact(artifact, repository_root=ROOT)
    records_by_id = {
        record["action_id"]: record for record in subject["action_readiness"]
    }
    _require(
        records_by_id["house:119:2:278"]["readiness_state"] == "blocked_stage_mismatch"
        and aggregate
        == {
            "total_action_count": 82,
            "ready_count": 81,
            "blocked_count": 1,
            "counts_by_readiness_state": {
                "blocked_stage_mismatch": 1,
                "ready_for_action_interpretation": 81,
            },
        },
        "roll 278 fail-closed accounting mismatch",
    )
    _require(
        all(
            record["readiness_state"] == "ready_for_action_interpretation"
            for action_id, record in records_by_id.items()
            if action_id != "house:119:2:278"
        ),
        "an unaffected M11B action changed readiness state",
    )
    hr2721 = records_by_id["house:119:1:269"]
    _require(
        hr2721["official_action_date"] == "2025-09-16"
        and any(
            "source-native Congressional Record parenthetical says 09/16/2026"
            in limitation
            for limitation in hr2721["material_limitations"]
        ),
        "H.R. 2721 date-text discrepancy limitation missing",
    )

    current = load_json(CURRENT_STATE_PATH)["completed_m11b_source_readiness_milestone"]
    identity = current["interpretation_source_readiness_identity"]
    accepted_state = current["milestone_state"] == "completed_human_accepted"
    _require(
        current["milestone"] == "m11b_national_security_source_readiness_v1"
        and current["milestone_state"]
        in {"complete_pending_human_review", "completed_human_accepted"}
        and current["interpretation_state"] == "not_started"
        and all(
            value is False for value in current["downstream_authorizations"].values()
        ),
        "current M11B state crosses source-readiness boundary",
    )
    if accepted_state:
        _require(
            current.get("human_review_decision") == "accepted"
            and current.get("accepted_pr") == 134
            and current.get("accepted_head")
            == "fcc988b867a49086d7545832f9575130aef0f8ea"
            and current.get("reviewed_base")
            == "434c972132e99628bddec4cc6392adc741e03205"
            and current.get("post_merge_main")
            == "13f8ad58f3aee32eb90369e8b454830cfbbf130b",
            "current M11B human-acceptance binding mismatch",
        )
    _require(
        identity
        == {
            "id": artifact["artifact_id"],
            "sha256": canonical_file_sha256(ARTIFACT_PATH),
            "source_readiness_subject_sha256": artifact[
                "source_readiness_subject_sha256"
            ],
            "ready_count": aggregate["ready_count"],
            "blocked_count": aggregate["blocked_count"],
            "authorizing": False,
        },
        "current-state readiness identity mismatch",
    )
    return {
        "status": "pass",
        "artifact_id": artifact["artifact_id"],
        "artifact_sha256": canonical_file_sha256(ARTIFACT_PATH),
        "source_readiness_subject_sha256": artifact["source_readiness_subject_sha256"],
        "m11a_receipt_sha256": m11a["receipt_file_sha256"],
        **aggregate,
    }


def main() -> int:
    try:
        print(json.dumps(validate_repository(), sort_keys=True))
    except (SourceReadinessError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
