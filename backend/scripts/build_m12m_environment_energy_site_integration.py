"""Build detached M12M Environment & Energy site-integration review artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.editorial_presentations.environment_integration_candidate import (  # noqa: E402
    compile_environment_site_integration_candidate,
    validate_environment_site_integration_candidate,
)
from backend.app.editorial_presentations.integration_candidate import (  # noqa: E402
    canonical_file_sha256,
)
from backend.app.etl.full_record_public_wording_decisions import seal  # noqa: E402

BASE_SHA = "fef90fd33aa1d3e838f2ac2a6cc366d3e5ef32cb"
M12L_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/public_wording_implementations/f000477_environment_energy_119_v1"
)
AUTHORITY = M12L_ROOT / "human_public_wording_authority.json"
IMPLEMENTATION = M12L_ROOT / "reviewed_wording_decision_implementation.json"
M12L_PARITY = M12L_ROOT / "implementation_parity_manifest.json"
M12C = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_candidates/f000477_environment_energy_119_v1/candidate_batch.json"
)
M12D = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions/f000477_environment_energy_119_v1/decision_implementation_bundle.json"
)
M12F = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_environment_energy_119_v1/episode_decision_implementation_bundle.json"
)
OUTPUT = (
    ROOT
    / "docs/editorial/full_record_reviews/site_integration_candidates/f000477_environment_energy_119_v1"
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_or_check(path: Path, content: str, check: bool) -> None:
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            raise ValueError(f"deterministic M12M artifact differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def preview_data(
    m12c: dict[str, Any], m12d: dict[str, Any], m12f: dict[str, Any]
) -> dict[str, Any]:
    candidates = {row["action_id"]: row for row in m12c["subject"]["candidates"]}
    maps = {row["action_id"]: row for row in m12c["subject"]["evidence_maps"]}
    decisions = {
        row["action_id"]: row for row in m12d["subject"]["implementation_records"]
    }
    episodes = {
        row["action_id"]: row["primary_episode_id"]
        for row in m12f["subject"]["action_accounting"]
    }
    if not (len(candidates) == len(maps) == len(decisions) == len(episodes) == 63):
        raise ValueError("M12C/D/F action accounting differs")
    rows = []
    for action_id in sorted(decisions):
        source, evidence_map, decision = (
            candidates[action_id],
            maps[action_id],
            decisions[action_id],
        )
        clerk = next(
            row
            for row in evidence_map["source_bindings"]
            if row["source_type"] == "house_clerk_roll_call"
        )
        meaning_sources = [
            {"label": "Official measure source", "url": row["source_url"]}
            for row in evidence_map["source_bindings"]
            if row["source_type"] != "house_clerk_roll_call"
        ]
        session, roll = (int(value) for value in action_id.split(":")[-2:])
        member_action = source["official_member_action"].title()
        rows.append(
            {
                "canonical_action_id": action_id,
                "roll_call_id": action_id,
                "chamber": "house",
                "congress": 119,
                "session": session,
                "rollcall_number": roll,
                "vote_date": source["official_action_date"],
                "vote_type": source["house_action_stage"],
                "description": source["official_title_or_purpose"]["wording"],
                "issue_domain": "ENVIRONMENT_ENERGY",
                "position": source["official_member_action"],
                "interpretation_status": "interpreted",
                "plain_english_summary": decision["accepted_exact_action_meaning"],
                "question": decision["accepted_exact_action_meaning"],
                "uncertainty_note": " ".join(decision["accepted_limitations"]),
                "source_url": clerk["source_url"],
                "source_basis": meaning_sources,
                "governed_receipt_projection": {
                    "canonical_action_id": action_id,
                    "exact_action_meaning": decision["accepted_exact_action_meaning"],
                    "policy_question": decision["accepted_exact_action_meaning"],
                    "member_action": member_action,
                    "exact_choice_position_effect": decision[
                        "accepted_exact_choice_position_effect"
                    ],
                    "episode_id": episodes[action_id],
                    "episode_relationship": "This action is independently expandable in the reviewed record.",
                    "caveats": decision["accepted_limitations"],
                    "vote_sources": [
                        {"label": "Official House vote", "url": clerk["source_url"]}
                    ],
                    "action_meaning_sources": meaning_sources,
                },
                "governed_receipt_control": None,
            }
        )
    return {
        "action_ids_119": sorted(decisions),
        "evidence_119": sorted(
            rows,
            key=lambda row: (row["vote_date"], row["rollcall_number"]),
            reverse=True,
        ),
    }


def mapping_rows(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    p = candidate["subject"]["presentation"]
    items = [p["overview"], *p["syntheses"], *p["repeated_patterns"]]
    return [
        {
            "wording_item_id": item["wording_item_id"],
            "surface": item["surface"],
            "title": item["title"],
            "evidence_count_label": item["evidence_count_label"],
            "direction_displayed": item["show_direction"],
            "semantic_lineage_action_count": len(item["semantic_lineage_action_ids"]),
            "semantic_lineage_action_ids": item["semantic_lineage_action_ids"],
            "semantic_lineage_episode_count": len(item["semantic_lineage_episode_ids"]),
            "semantic_lineage_episode_ids": item["semantic_lineage_episode_ids"],
            "public_supporting_action_count": len(item["public_supporting_action_ids"]),
            "public_supporting_action_ids": item["public_supporting_action_ids"],
            "wording_item_subject_sha256": item["mapping"][
                "wording_item_subject_sha256"
            ],
        }
        for item in items
    ]


def screenshot_manifest() -> dict[str, Any] | None:
    root = OUTPUT / "screenshots"
    definitions = [
        ("desktop-1440.png", 1440, 1000, "100%"),
        ("desktop-1024.png", 1024, 900, "100%"),
        ("mobile-390.png", 390, 844, "100%"),
        ("mobile-320.png", 320, 720, "100%"),
        ("zoom-200-percent.png", 1024, 900, "200%"),
    ]
    if not all((root / name).exists() for name, *_ in definitions):
        return None
    return {
        "schema_version": "m12m_site_integration_screenshot_manifest_v1",
        "artifact_id": "site-integration-screenshot-manifest:f000477:environment_energy:119:v1",
        "candidate_artifact_id": "site-integration-candidate:f000477:environment_energy:119:v1",
        "captures": [
            {
                "path": f"docs/editorial/full_record_reviews/site_integration_candidates/f000477_environment_energy_119_v1/screenshots/{name}",
                "viewport_width": width,
                "viewport_height": height,
                "zoom": zoom,
                "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest(),
            }
            for name, width, height, zoom in definitions
        ],
    }


def markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# M12M Environment & Energy Site-Integration Review Packet",
        "",
        "- State: detached, non-authorizing, publication inactive, production unselectable",
        "- Preview token: `m12m-environment-energy` plus server-side opt-in",
        "- Scope: 119th Congress; `all` retains an explicit 119th-Congress analytical boundary",
        "- Directions: no visible badge or fallback on any of the five items",
        "",
        "## Exact accepted wording mapping",
        "",
        "| Surface | Public title | Evidence label | Public actions | Lineage actions |",
        "|---|---|---|---:|---:|",
    ]
    for row in packet["mapping_rows"]:
        lines.append(
            f"| {row['surface']} | {row['title']} | {row['evidence_count_label']} | {row['public_supporting_action_count']} | {row['semantic_lineage_action_count']} |"
        )
    lines += [
        "",
        "The overview reuses the 13-action synthesis support set and is not an additional finding. H.R. 6387, H.R. 471, H.R. 3898, contrast-only evidence, and no-safe-proposition evidence do not enter any finding.",
        "",
        "Publication eligibility, activation, persistence, database/production writes, and deployment remain false.",
        "",
    ]
    return "\n".join(lines)


def build(check: bool = False) -> dict[str, Any]:
    authority, implementation, parity = (
        load(AUTHORITY),
        load(IMPLEMENTATION),
        load(M12L_PARITY),
    )
    m12c, m12d, m12f = load(M12C), load(M12D), load(M12F)
    candidate = compile_environment_site_integration_candidate(
        authority=authority,
        implementation=implementation,
        parity=parity,
        authority_file_sha256=canonical_file_sha256(AUTHORITY),
        implementation_file_sha256=canonical_file_sha256(IMPLEMENTATION),
        parity_file_sha256=canonical_file_sha256(M12L_PARITY),
        accepted_base_sha=BASE_SHA,
        preview_data=preview_data(m12c, m12d, m12f),
    )
    validate_environment_site_integration_candidate(candidate)
    mappings = mapping_rows(candidate)
    packet = {
        "schema_version": "m12m_site_integration_review_packet_v1",
        "artifact_id": "site-integration-review-packet:f000477:environment_energy:119:v1",
        "candidate_binding": {
            "artifact_id": candidate["artifact_id"],
            "candidate_subject_sha256": candidate["candidate_subject_sha256"],
        },
        "base_sha": BASE_SHA,
        "accounting": {
            "wording_items": 5,
            "semantic_lineage_unique_actions": 13,
            "semantic_lineage_unique_episodes": 13,
            "accepted_interpreted_actions": 63,
            "accepted_episodes": 63,
            "blocked_actions": 0,
        },
        "mapping_rows": mappings,
        "semantic_proofs": {
            "exact_accepted_wording_projection": True,
            "raw_vote_direction_inference": False,
            "no_direction_items_have_no_public_status": True,
            "semantic_lineage_and_public_projection_separate": True,
            "excluded_material_cannot_enter_findings": True,
        },
        "scope_behavior": {
            "119": "candidate_available_with_explicit_server_preview_opt_in",
            "all": "candidate_available_with_explicit_119th_congress_boundary",
            "118": "receipts_only_fail_closed",
            "other": "request_validation_failure",
        },
        "controls": candidate["subject"]["controls"],
    }
    candidate_text = json_text(candidate)
    packet["candidate_binding"]["file_sha256"] = text_sha(candidate_text)
    manifest = screenshot_manifest()
    if manifest:
        packet["screenshot_manifest"] = {
            "artifact_id": manifest["artifact_id"],
            "capture_count": 5,
            "file_sha256": text_sha(json_text(manifest)),
        }
    packet_text = json_text(packet)
    state = {
        "milestone": "M12M",
        "m12l_wording_canonical_internal": True,
        "site_integration_candidate": True,
        "public": False,
        "production_selectable": False,
        "publication_eligibility": False,
        "publication_activation": False,
        "persistence": False,
        "database_writes": False,
        "production_writes": False,
        "deployment": False,
    }
    state_text, markdown_text = json_text(state), markdown(packet)
    artifact_parity = seal(
        {
            "schema_version": "m12m_site_integration_parity_v1",
            "artifact_id": "site-integration-parity:f000477:environment_energy:119:v1",
            "candidate_binding": packet["candidate_binding"],
            "entries": [
                {
                    "path": "site_integration_candidate.json",
                    "file_sha256": text_sha(candidate_text),
                    "content_subject_sha256": candidate["candidate_subject_sha256"],
                },
                {
                    "path": "review_packet.json",
                    "file_sha256": text_sha(packet_text),
                    "content_subject_sha256": None,
                },
                {
                    "path": "review_packet.md",
                    "file_sha256": text_sha(markdown_text),
                    "content_subject_sha256": None,
                },
                {
                    "path": "current_state.json",
                    "file_sha256": text_sha(state_text),
                    "content_subject_sha256": None,
                },
            ],
        },
        "parity_subject_sha256",
    )
    outputs = (
        (OUTPUT / "site_integration_candidate.json", candidate_text),
        (OUTPUT / "review_packet.json", packet_text),
        (OUTPUT / "review_packet.md", markdown_text),
        (OUTPUT / "current_state.json", state_text),
        (OUTPUT / "parity_manifest.json", json_text(artifact_parity)),
    )
    for path, content in outputs:
        write_or_check(path, content, check)
    if manifest:
        write_or_check(OUTPUT / "screenshot_manifest.json", json_text(manifest), check)
    return {"candidate": candidate, "review_packet": packet, "parity": artifact_parity}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build(check=args.check)
    print(
        json.dumps(
            {
                "artifact_id": result["candidate"]["artifact_id"],
                "candidate_subject_sha256": result["candidate"][
                    "candidate_subject_sha256"
                ],
                "wording_items": 5,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
