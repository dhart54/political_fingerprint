from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
from typing import Any

from jsonschema import Draft7Validator, FormatChecker


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
ORIGINAL_ROOT = ROOT.parents[1]
sys.path.insert(0, str(BACKEND))

from app.etl.full_record_source_readiness import (  # noqa: E402
    build_readiness_artifact,
    canonical_file_sha256,
    load_json,
    sha256_file,
    validate_artifact,
    write_json,
)
from app.etl.fetch_sources import download_to_path  # noqa: E402
from app.etl.universe_discovery import load_house_clerk_member_actions  # noqa: E402
from scripts import build_m11b_national_security_source_readiness as source_tools  # noqa: E402


M13A_ROOT = Path("docs/editorial/cross_issue_full_record_expansion_m13a_v1")
PROPOSAL_PATH = M13A_ROOT / "selected_domain_universe_proposal.json"
INVENTORY_PATH = M13A_ROOT / "source_inventory.json"
SELECTION_PATH = M13A_ROOT / "domain_selection.json"
AUTHORITY_PATH = Path(
    "docs/editorial/full_record_reviews/"
    "f000477_education_workforce_119_full_issue_universe_authority_receipt_v1.json"
)
SCHEMA_PATH = Path(
    "docs/methodology/full_record_interpretation_source_readiness_v1.schema.json"
)
SOURCE_ROOT = Path("docs/editorial/full_record_reviews/source_readiness")
EVIDENCE_ROOT = SOURCE_ROOT / "evidence/f000477_education_119_v1"
ARTIFACT_PATH = (
    SOURCE_ROOT
    / "f000477_education_workforce_119_interpretation_source_readiness_v1.json"
)
REPORT_PATH = (
    SOURCE_ROOT
    / "f000477_education_workforce_119_interpretation_source_readiness_v1.md"
)
DEFAULT_CACHE = ROOT / ".local/m13b_education_workforce_source_readiness"
CLERK_DIRS = (
    ORIGINAL_ROOT / ".local/m11a_house_clerk/2025",
    ORIGINAL_ROOT / ".local/m11a_house_clerk/2026",
)
ARTIFACT_ID = "interpretation-source-readiness:f000477:education_workforce:119:v1"
EXPECTED_RECEIPT_SHA256 = (
    "491b6de2314788f1566f8366f95a66b2375ec6d1271790a18387ba33cad70ea3"
)
EXPECTED_ACTION_SET_SHA256 = (
    "83b7b129eaa32d114c72782c70cb06dac55f7cd01c8681c8dc2ae2dca986cf5b"
)
EXPECTED_UNIVERSE_SUBJECT_SHA256 = (
    "edc381362beb1e5700748ffe75fc12c31ae14f090887940197a50bf416aaac6d"
)
HR2262_RECORD_URL = (
    "https://www.congress.gov/119/crec/2026/01/13/172/9/"
    "CREC-2026-01-13-pt1-PgH676-4.pdf"
)


def copy_content_addressed(
    source: Path, *, logical_name: str, evidence_root: Path
) -> dict[str, str]:
    del logical_name
    digest = sha256_file(source)
    destination = evidence_root / f"{digest}{source.suffix.lower()}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copyfile(source, destination)
    if sha256_file(destination) != digest:
        raise ValueError(f"content-addressed evidence mismatch: {destination}")
    return {
        "governed_local_path": destination.relative_to(ROOT).as_posix(),
        "sha256": digest,
    }


def clerk_source(
    action: dict[str, Any],
    *,
    exact_identity: str,
    stage: str,
    evidence_root: Path,
) -> dict[str, Any]:
    source_dir = CLERK_DIRS[action["session"] - 1]
    source_path = source_dir / f"roll{action['rollcall_number']:03d}.xml"
    raw = copy_content_addressed(
        source_path,
        logical_name=(
            f"roll119_{action['session']}_{action['rollcall_number']:03d}.xml"
        ),
        evidence_root=evidence_root,
    )
    source_id = f"clerk:{action['canonical_action_id']}"
    projection = source_tools._projection(
        action=action,
        source_id=source_id,
        exact_identity=exact_identity,
        stage=stage,
        source_url=action["source_url"],
        text_version=action["vote_date"],
        raw_sha256=raw["sha256"],
        official_action_description=action["question"],
    )
    return source_tools._source(
        source_id=source_id,
        source_type="house_clerk_roll_call",
        source_subject=action["canonical_action_id"],
        content_class="member_action_record",
        source_url=action["source_url"],
        raw=raw,
        projection=projection,
    )


def limitations(action_id: str) -> list[str]:
    by_action = {
        "house:119:1:79": [
            "Exact Congress.gov H.Amdt. 12 identity, recorded-roll binding, and amendment purpose are required; parent H.R. 1048 evidence alone is insufficient.",
            "H.R. 1048 passage at roll 83 is a separate accepted action; no episode semantics are established by this packet.",
        ],
        "house:119:1:146": [
            "Commerce remains the official primary policy area. The packet preserves the Small Business Act mechanism and the material career-and-technical-education, workforce-hiring, and career-opportunity component; it does not classify H.R. 1642 as exclusively or primarily education policy.",
        ],
        "house:119:1:315": [
            "Public Lands and Natural Resources remains the official primary policy area. The packet preserves the exact Secure Rural Schools extension within a federal-land and county-payment program, including school, road, community, and resource-project context; it cannot establish a general education-funding position.",
        ],
        "house:119:1:312": [
            "The Clerk records Not Voting. Source readiness preserves the exact action and absence status, but later position effect must remain non-directional and cannot infer support or opposition.",
        ],
        "house:119:2:19": [
            "Congress.gov exposes no House-engrossed bill text for the failed passage. The official Congressional Record packet is the operative-content source because it records adoption of the modified committee substitute and prints the exact bill text considered.",
        ],
    }
    return by_action.get(action_id, [])


def hr2262_sources(
    action: dict[str, Any],
    *,
    identity: str,
    stage: str,
    cache_root: Path,
    evidence_root: Path,
    acquire_missing: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    action_path = cache_root / "actions/119_hr_2262.json"
    action_payload = load_json(action_path)
    exact_description = source_tools._exact_house_action(
        action_payload,
        action_id=action["canonical_action_id"],
        roll=action["rollcall_number"],
        action_date=action["vote_date"],
    )
    action_raw = copy_content_addressed(
        action_path,
        logical_name="119_hr_2262_actions.json",
        evidence_root=evidence_root,
    )
    action_source_id = f"congress-actions:{action['canonical_action_id']}"
    action_url = "https://api.congress.gov/v3/bill/119/hr/2262/actions"
    action_projection = source_tools._projection(
        action=action,
        source_id=action_source_id,
        exact_identity=identity,
        stage=stage,
        source_url=action_url,
        text_version="official_house_action_list_v3",
        raw_sha256=action_raw["sha256"],
        official_action_description=exact_description,
    )
    action_source = source_tools._source(
        source_id=action_source_id,
        source_type="congress_gov_bill_actions",
        source_subject=identity,
        content_class="exact_house_action_record",
        source_url=action_url,
        raw=action_raw,
        projection=action_projection,
    )

    record_path = cache_root / "operative_texts/CREC-2026-01-13-pt1-PgH676-4.pdf"
    if not record_path.is_file():
        if not acquire_missing:
            raise ValueError("missing official H.R. 2262 Congressional Record packet")
        download_to_path(HR2262_RECORD_URL, record_path)
    record_raw = copy_content_addressed(
        record_path, logical_name=record_path.name, evidence_root=evidence_root
    )
    record_source_id = "congressional-record:2026-01-13:house:H677-H693:hr2262"
    record_projection = source_tools._projection(
        action=action,
        source_id=record_source_id,
        exact_identity=identity,
        stage=stage,
        source_url=HR2262_RECORD_URL,
        text_version="official_house_record_H677-H693",
        raw_sha256=record_raw["sha256"],
        official_action_description=(
            "Official Congressional Record floor packet prints the modified "
            "committee substitute considered for H.R. 2262 and records roll 19."
        ),
    )
    record_source = source_tools._source(
        source_id=record_source_id,
        source_type="congressional_record",
        source_subject=identity,
        content_class="operative_floor_text",
        source_url=HR2262_RECORD_URL,
        raw=record_raw,
        projection=record_projection,
    )
    return action_source, record_source


def s356_summary_source(
    action: dict[str, Any], *, evidence_root: Path, cache_root: Path
) -> dict[str, Any]:
    summary_path = cache_root / "summaries/119_s_356.json"
    payload = load_json(summary_path)
    matches = [
        row for row in payload["summaries"] if str(row.get("versionCode")) == "49"
    ]
    if len(matches) != 1:
        raise ValueError("official S. 356 public-law summary is not unique")
    summary = matches[0]
    raw = copy_content_addressed(
        summary_path, logical_name=summary_path.name, evidence_root=evidence_root
    )
    source_id = "congress-summary:119:s:356:public-law-v49"
    source_url = "https://api.congress.gov/v3/bill/119/s/356/summaries"
    projection = source_tools._projection(
        action=action,
        source_id=source_id,
        exact_identity="119:s:356",
        stage="final_passage_or_suspension_passage",
        source_url=source_url,
        text_version="official_crs_public_law_summary_v49",
        raw_sha256=raw["sha256"],
        official_action_description=str(summary["actionDesc"]),
        official_description=str(summary["text"]),
    )
    return source_tools._source(
        source_id=source_id,
        source_type="congress_gov_bill_summary",
        source_subject="119:s:356",
        content_class="supplemental_program_context",
        source_url=source_url,
        raw=raw,
        projection=projection,
    )


def build(
    *, cache_root: Path, evidence_root: Path, acquire_missing: bool
) -> dict[str, Any]:
    evidence_root.mkdir(parents=True, exist_ok=True)
    proposal = load_json(ROOT / PROPOSAL_PATH)
    inventory = load_json(ROOT / INVENTORY_PATH)
    selection = load_json(ROOT / SELECTION_PATH)
    authority = load_json(ROOT / AUTHORITY_PATH)
    if canonical_file_sha256(ROOT / AUTHORITY_PATH) != EXPECTED_RECEIPT_SHA256:
        raise ValueError("M13A authority receipt changed")
    approved_ids = authority["approval_binding"]["approved_action_ids"]
    if (
        len(approved_ids) != 17
        or set(approved_ids) != set(proposal["proposed_action_ids"])
        or authority["action_set_sha256"] != EXPECTED_ACTION_SET_SHA256
        or authority["universe_subject_sha256"] != EXPECTED_UNIVERSE_SUBJECT_SHA256
    ):
        raise ValueError("M13A authority identity or membership changed")

    candidates = {
        row["action_id"]: row
        for row in proposal["candidate_dispositions"]
        if row["action_id"] in set(approved_ids)
    }
    if set(candidates) != set(approved_ids):
        raise ValueError("accepted action does not resolve exactly once")
    official_rows = {
        row["canonical_action_id"]: row
        for row in load_house_clerk_member_actions(CLERK_DIRS, bioguide_id="F000477")
    }

    source_tools.ROOT = ROOT
    source_tools.AMENDMENT_DIR = cache_root / "amendments"
    source_tools._copy_content_addressed = copy_content_addressed
    action_records = []
    for action_id in approved_ids:
        row = candidates[action_id]
        action = official_rows[action_id]
        identity = row["exact_action_source_binding"]["exact_identity"]
        stage = row["house_action_stage"]
        if action["vote_date"] != source_tools._date(row["date"]):
            raise ValueError(f"official action date mismatch: {action_id}")
        clerk = clerk_source(
            action,
            exact_identity=identity,
            stage=stage,
            evidence_root=evidence_root,
        )
        if stage == "amendment":
            operative = source_tools._amendment_source(
                action,
                row=row,
                identity=identity,
                evidence_root=evidence_root,
            )
            sources = [clerk, operative]
            identity_roles = [operative["source_id"]]
            operative_roles = [operative["source_id"]]
            mechanism = "amendment"
        elif stage == "final_passage_or_suspension_passage":
            source_builder = (
                hr2262_sources
                if identity == "119:hr:2262"
                else source_tools._whole_measure_sources
            )
            action_source, operative = source_builder(
                action,
                identity=identity,
                stage=stage,
                cache_root=cache_root,
                evidence_root=evidence_root,
                acquire_missing=acquire_missing,
            )
            sources = [clerk, action_source, operative]
            identity_roles = [action_source["source_id"], operative["source_id"]]
            operative_roles = [operative["source_id"]]
            mechanism = "whole_measure"
        else:
            raise ValueError(f"unexpected M13B House stage: {action_id} {stage}")
        source_roles = {
            "member_action_evidence": [clerk["source_id"]],
            "exact_action_identity_and_stage_evidence": identity_roles,
            "operative_content_interpretation_input": operative_roles,
        }
        if action_id == "house:119:1:315":
            context = s356_summary_source(
                action, evidence_root=evidence_root, cache_root=cache_root
            )
            sources.append(context)
            source_roles["material_limitation_context_evidence"] = [
                context["source_id"]
            ]
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
                "material_limitations": limitations(action_id),
                "source_roles": source_roles,
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
            "artifact_id": proposal["proposal_id"],
            "artifact_path": PROPOSAL_PATH.as_posix(),
            "sha256": canonical_file_sha256(ROOT / PROPOSAL_PATH),
            "universe_subject_sha256": proposal["universe_subject_sha256"],
        },
        "selection": {
            "artifact_path": SELECTION_PATH.as_posix(),
            "sha256": selection["selection_sha256"],
        },
        "source_inventory": {
            "artifact_id": inventory["inventory_id"],
            "artifact_path": INVENTORY_PATH.as_posix(),
            "sha256": canonical_file_sha256(ROOT / INVENTORY_PATH),
            "inventory_sha256": inventory["inventory_sha256"],
        },
    }
    subject = {
        "member_name": "Valerie Foushee",
        "member_id": "F000477",
        "legislator_id": "leg_valerie_p_foushee",
        "issue_id": "EDUCATION_WORKFORCE",
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
    records = {row["action_id"]: row for row in subject["action_readiness"]}
    lines = [
        "# M13B Education & Workforce Interpretation Source Readiness V1",
        "",
        "This packet evaluates role-bound official-source readiness only. It does not establish action meaning, position effects, episodes, Semantic IR, synthesis, public wording, site integration, publication, deployment, or production authority.",
        "",
        "## Authority-bound universe",
        "",
        f"- Authority receipt: `{artifact['input_bindings']['authority_receipt']['artifact_id']}`",
        f"- Accepted actions: `{aggregate['total_action_count']}`",
        f"- Action-set digest: `{subject['action_set_sha256']}`",
        f"- Universe-subject digest: `{subject['universe_subject_sha256']}`",
        f"- Official cutoff: `{subject['official_cutoff']['end_date']}` through `{subject['official_cutoff']['latest_action_id']}`",
        "",
        "## Readiness result",
        "",
        f"- Ready for later independent action interpretation: `{aggregate['ready_count']}`",
        f"- Blocked: `{aggregate['blocked_count']}`",
        f"- Source-readiness subject digest: `{artifact['source_readiness_subject_sha256']}`",
        "",
        "Every action has separate role bindings for the Clerk member-action record, exact action identity/stage, and operative official content.",
        "",
        "## Required stress cases",
        "",
    ]
    for action_id, heading in (
        ("house:119:1:79", "Roll 79 — H.R. 1048 amendment"),
        ("house:119:1:146", "Roll 146 — H.R. 1642"),
        ("house:119:1:315", "Roll 315 — S. 356"),
        ("house:119:1:312", "Roll 312 — CLASS Act / Not Voting"),
    ):
        record = records[action_id]
        lines.extend(
            [
                f"### {heading}",
                "",
                f"- Readiness: `{record['readiness_state']}`.",
                f"- Member-action role: `{', '.join(record['source_roles']['member_action_evidence'])}`.",
                f"- Exact-action role: `{', '.join(record['source_roles']['exact_action_identity_and_stage_evidence'])}`.",
                f"- Operative-content role: `{', '.join(record['source_roles']['operative_content_interpretation_input'])}`.",
            ]
        )
        lines.extend(f"- Limitation: {item}" for item in record["material_limitations"])
        lines.append("")
    blocked = [
        row
        for row in subject["action_readiness"]
        if row["readiness_state"] != "ready_for_action_interpretation"
    ]
    lines.extend(["## Blocked actions", ""])
    if blocked:
        lines.extend(
            f"- `{row['action_id']}`: `{row['readiness_state']}`; blockers: `{json.dumps(row['blocker_codes'])}`"
            for row in blocked
        )
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Authorization boundary",
            "",
            "All downstream authorization flags are false. Readiness does not authorize interpretation and does not alter the accepted M13A membership.",
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
