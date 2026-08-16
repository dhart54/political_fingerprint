from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.etl.full_record_source_readiness import (  # noqa: E402
    build_readiness_artifact,
    canonical_file_sha256,
    load_json,
    validate_artifact,
    write_json,
)
from app.etl.universe_discovery import load_house_clerk_member_actions  # noqa: E402
from scripts.build_m11b_national_security_source_readiness import (  # noqa: E402
    _clerk_source,
    _date,
    _whole_measure_sources,
)


M12A_ROOT = Path("docs/editorial/cross_issue_full_record_expansion_m12a_v1")
PROPOSAL_PATH = M12A_ROOT / "selected_domain_universe_proposal.json"
INVENTORY_PATH = M12A_ROOT / "source_inventory.json"
SELECTION_PATH = M12A_ROOT / "domain_selection.json"
AUTHORITY_PATH = Path(
    "docs/editorial/full_record_reviews/"
    "f000477_environment_energy_119_full_issue_universe_authority_receipt_v1.json"
)
SCHEMA_PATH = Path(
    "docs/methodology/full_record_interpretation_source_readiness_v1.schema.json"
)
SOURCE_ROOT = Path("docs/editorial/full_record_reviews/source_readiness")
EVIDENCE_ROOT = SOURCE_ROOT / "evidence/f000477_environment_energy_119_v1"
ARTIFACT_PATH = (
    SOURCE_ROOT
    / "f000477_environment_energy_119_interpretation_source_readiness_v1.json"
)
REPORT_PATH = (
    SOURCE_ROOT / "f000477_environment_energy_119_interpretation_source_readiness_v1.md"
)
DEFAULT_CACHE = ROOT / ".local/m12b_environment_energy_source_readiness"
CLERK_DIRS = (
    ROOT / ".local/m11a_house_clerk/2025",
    ROOT / ".local/m11a_house_clerk/2026",
)
ARTIFACT_ID = "interpretation-source-readiness:f000477:environment_energy:119:v1"

EXPECTED_RECEIPT_SHA256 = (
    "58a0d7a4f59069d747629311fdf0680385d6d802b506d585699904859773a31e"
)
EXPECTED_ACTION_SET_SHA256 = (
    "843740a27ef191294bcf0cc3d2b29aeda1751351d775f8fadd7f44708e2312c8"
)
EXPECTED_UNIVERSE_SUBJECT_SHA256 = (
    "29b42a593639a1c62745e959554596a40a8dbf8205e1b3a6af83234c8f49866e"
)


def build(
    *, cache_root: Path, evidence_root: Path, acquire_missing: bool
) -> dict[str, Any]:
    proposal = load_json(ROOT / PROPOSAL_PATH)
    inventory = load_json(ROOT / INVENTORY_PATH)
    selection = load_json(ROOT / SELECTION_PATH)
    authority = load_json(ROOT / AUTHORITY_PATH)
    if canonical_file_sha256(ROOT / AUTHORITY_PATH) != EXPECTED_RECEIPT_SHA256:
        raise ValueError("M12A authority receipt changed")
    approved_ids = authority["approval_binding"]["approved_action_ids"]
    if (
        len(approved_ids) != 63
        or authority["action_set_sha256"] != EXPECTED_ACTION_SET_SHA256
        or authority["universe_subject_sha256"] != EXPECTED_UNIVERSE_SUBJECT_SHA256
    ):
        raise ValueError("M12A authority identity changed")
    proposed_ids = proposal["proposed_action_ids"]
    if len(proposed_ids) != len(approved_ids) or set(approved_ids) != set(proposed_ids):
        raise ValueError("M12A approved action membership changed")

    candidates = {
        row["action_id"]: row
        for row in proposal["candidate_dispositions"]
        if row["action_id"] in set(approved_ids)
    }
    if set(candidates) != set(approved_ids):
        raise ValueError("approved action does not resolve exactly once")
    if any(row["house_action_stage"] == "amendment" for row in candidates.values()):
        raise ValueError("M12B unexpectedly received an amendment")

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
        if stage != "final_passage_or_suspension_passage":
            raise ValueError(f"unexpected M12B House stage: {action_id} {stage}")
        if action["vote_date"] != _date(row["date"]):
            raise ValueError(f"official action date mismatch: {action_id}")

        clerk = _clerk_source(
            action, exact_identity=identity, stage=stage, evidence_root=evidence_root
        )
        action_source, operative = _whole_measure_sources(
            action,
            identity=identity,
            stage=stage,
            cache_root=cache_root,
            evidence_root=evidence_root,
            acquire_missing=acquire_missing,
        )
        identity_roles = [action_source["source_id"], operative["source_id"]]
        measure_type = identity.split(":")[1]
        mechanism = (
            "resolution"
            if measure_type in {"hconres", "hjres", "hres", "sconres", "sjres"}
            else "whole_measure"
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
                "material_limitations": [],
                "source_roles": {
                    "member_action_evidence": [clerk["source_id"]],
                    "exact_action_identity_and_stage_evidence": identity_roles,
                    "operative_content_interpretation_input": [operative["source_id"]],
                },
                "sources": [clerk, action_source, operative],
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
        "issue_id": "ENVIRONMENT_ENERGY",
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
        "# M12B Environment & Energy Interpretation Source Readiness V1",
        "",
        "This packet evaluates official-source readiness only. It does not establish action meaning, Support/Opposition, episodes, Semantic IR, synthesis, public wording, publication, or persistence authority.",
        "",
        "## Authority-bound universe",
        "",
        f"- Authority receipt: `{artifact['input_bindings']['authority_receipt']['artifact_id']}`",
        f"- Approved actions: `{aggregate['total_action_count']}`",
        f"- Action-set digest: `{subject['action_set_sha256']}`",
        f"- Universe-subject digest: `{subject['universe_subject_sha256']}`",
        f"- Official cutoff: `{subject['official_cutoff']['end_date']}` through `{subject['official_cutoff']['latest_action_id']}`",
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
        for row in blocked:
            lines.append(
                f"- `{row['action_id']}`: `{row['readiness_state']}`; "
                f"limitations: `{json.dumps(row['material_limitations'])}`"
            )
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Authorization boundary",
            "",
            "All downstream authorization flags are false. Readiness does not authorize interpretation and does not alter the accepted M12A membership.",
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
