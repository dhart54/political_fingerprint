"""Build the detached M11M National Security site-integration candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.editorial_presentations.integration_candidate import (  # noqa: E402
    BLOCKED_ACTION_ID,
    canonical_file_sha256,
    compile_site_integration_candidate,
    validate_site_integration_candidate,
)


BASE_SHA = "55dd4a2e05bdd3d61a328793b8349a952df000d6"
M11L = (
    ROOT
    / "docs/editorial/full_record_reviews/public_wording_implementations/f000477_national_security_foreign_119_v1"
)
M11D = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions/f000477_national_security_foreign_119_v1/decision_implementation_bundle.json"
)
M11C = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_candidates/f000477_national_security_foreign_119_v1/candidate_batch.json"
)
M11F = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_national_security_foreign_119_v1/episode_decision_implementation_bundle.json"
)
M11B = (
    ROOT
    / "docs/editorial/full_record_reviews/source_readiness/f000477_national_security_foreign_119_interpretation_source_readiness_v1.json"
)
OUTPUT = (
    ROOT
    / "docs/editorial/full_record_reviews/site_integration_candidates/f000477_national_security_foreign_119_v1"
)
AUTHORITY = M11L / "human_public_wording_authority.json"
IMPLEMENTATION = M11L / "reviewed_wording_decision_implementation.json"
PARITY = M11L / "implementation_parity_manifest.json"

EXPECTED = {
    AUTHORITY: (
        "5c0c888c6c3569b2434fa6057d8be9290b22b7ed019e25e9a245150feaf5fffb",
        "human-public-wording-authority:f000477:national_security_foreign:119:v1",
        "authority_subject_sha256",
        "43e83cd72a7af1124854cfcc0830442210d45276201ef39ca5e5fe5134492c89",
    ),
    IMPLEMENTATION: (
        "42c4888fbc48eef65fb8038d89006fed225ded40361686561f893885902a285b",
        "reviewed-wording-decision-implementation:f000477:national_security_foreign:119:v1",
        "implementation_subject_sha256",
        "57b042e1c36250683ce57820088123f34fb221c438f41aca076156751e3335f9",
    ),
    PARITY: (
        "3798d412ffc782759f15dc5d5f5a961f08c4a56897a07a50fd6d37bca4696686",
        "public-wording-implementation-parity:f000477:national_security_foreign:119:v1",
        "parity_subject_sha256",
        "824692a57894175b9c09e7af73a21d194a4facae68c466eb40a9e6704e3bc5c1",
    ),
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def write_or_check(path: Path, content: str, check: bool) -> None:
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            raise ValueError(f"deterministic M11M artifact differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def preflight() -> tuple[dict[str, Any], ...]:
    artifacts = []
    for path, (file_sha, artifact_id, subject_field, subject_sha) in EXPECTED.items():
        artifact = load(path)
        if not (
            canonical_file_sha256(path) == file_sha
            and artifact["artifact_id"] == artifact_id
            and artifact[subject_field] == subject_sha
        ):
            raise ValueError(f"accepted M11L identity differs: {path}")
        artifacts.append(artifact)
    m11d = load(M11D)
    m11f = load(M11F)
    if not (
        m11d["artifact_id"]
        == "action-interpretation-decision-implementation:f000477:national_security_foreign:119:v1"
        and m11d["subject"]["implementation_record_count"] == 81
        and [item["action_id"] for item in m11d["subject"]["source_blocked_actions"]]
        == [BLOCKED_ACTION_ID]
        and m11f["artifact_id"]
        == "policy-episode-decision-implementation:f000477:national_security_foreign:119:v1"
        and m11f["subject"]["final_accounting"]["accepted_episode_count"] == 81
        and m11f["subject"]["final_accounting"]["blocked_action_count"] == 1
    ):
        raise ValueError("accepted M11D/M11F accounting differs")
    return (*artifacts, m11d, m11f)


def mapping_rows(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    presentation = candidate["subject"]["presentation"]
    items = [
        presentation["overview"],
        *presentation["syntheses"],
        *presentation["repeated_patterns"],
        *presentation["policy_trajectories"],
        *presentation["notable_choices"],
    ]
    return [
        {
            "wording_item_id": item["wording_item_id"],
            "surface": item["surface"],
            "title": item["title"],
            "action_count": len(item["action_ids"]),
            "episode_count": len(item["episode_ids"]),
            "action_ids": item["action_ids"],
            "episode_ids": item["episode_ids"],
            "public_supporting_action_count": len(item["public_supporting_action_ids"]),
            "public_supporting_action_ids": item["public_supporting_action_ids"],
            "semantic_lineage_action_count": len(item["semantic_lineage_action_ids"]),
            "semantic_lineage_action_ids": item["semantic_lineage_action_ids"],
            "semantic_lineage_episode_count": len(item["semantic_lineage_episode_ids"]),
            "semantic_lineage_episode_ids": item["semantic_lineage_episode_ids"],
            "semantic_source_ids": item["semantic_source_ids"],
            "wording_item_subject_sha256": item["mapping"][
                "wording_item_subject_sha256"
            ],
        }
        for item in items
    ]


def preview_data(m11d: dict[str, Any], m11f: dict[str, Any]) -> dict[str, Any]:
    m11c = load(M11C)
    m11b = load(M11B)
    candidates = {row["action_id"]: row for row in m11c["subject"]["candidates"]}
    evidence_maps = {row["action_id"]: row for row in m11c["subject"]["evidence_maps"]}
    accepted = {
        row["action_id"]: row for row in m11d["subject"]["implementation_records"]
    }
    episode_by_action = {
        row["action_id"]: row["primary_episode_id"]
        for row in m11f["subject"]["action_accounting"]
    }
    rows = []
    for action_id in sorted(accepted):
        decision = accepted[action_id]
        source = candidates[action_id]
        source_map = evidence_maps[action_id]
        source_bindings = source_map["source_bindings"]
        clerk = next(
            binding
            for binding in source_bindings
            if binding["source_type"] == "house_clerk_roll_call"
        )
        meaning_sources = [
            {
                "label": "Official measure source",
                "url": binding["source_url"],
            }
            for binding in source_bindings
            if binding["source_type"] != "house_clerk_roll_call"
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
                "issue_domain": "NATIONAL_SECURITY_FOREIGN",
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
                    "episode_id": episode_by_action[action_id],
                    "episode_relationship": (
                        "This action is independently expandable in the reviewed record."
                    ),
                    "caveats": decision["accepted_limitations"],
                    "vote_sources": [
                        {"label": "Official House vote", "url": clerk["source_url"]}
                    ],
                    "action_meaning_sources": meaning_sources,
                },
                "governed_receipt_control": None,
            }
        )
    blocked = next(
        row
        for row in m11b["subject"]["action_readiness"]
        if row["action_id"] == BLOCKED_ACTION_ID
    )
    rows.append(
        {
            "canonical_action_id": BLOCKED_ACTION_ID,
            "roll_call_id": BLOCKED_ACTION_ID,
            "chamber": "house",
            "congress": 119,
            "session": blocked["session"],
            "rollcall_number": blocked["roll_number"],
            "vote_date": blocked["official_action_date"],
            "vote_type": blocked["house_action_stage"],
            "description": "H.R. 8800 final passage after amendments",
            "issue_domain": "NATIONAL_SECURITY_FOREIGN",
            "position": blocked["official_member_action"],
            "interpretation_status": "insufficient_evidence",
            "plain_english_summary": (
                "No safe public analytical meaning is available for this action."
            ),
            "question": (
                "The complete final House-passed package is not established by "
                "the reviewed source set."
            ),
            "uncertainty_note": blocked["material_limitations"][0],
            "source_url": "https://clerk.house.gov/evs/2026/roll278.xml",
            "source_basis": [
                {
                    "label": "Official House vote",
                    "url": "https://clerk.house.gov/evs/2026/roll278.xml",
                }
            ],
            "governed_receipt_projection": None,
            "governed_receipt_control": {
                "status": "noncounting_control",
                "boundary_type": "source_blocked_uninterpreted",
                "detail": (
                    "No safe public analytical meaning is available for this action."
                ),
            },
        }
    )
    return {
        "action_ids_119": sorted(row["canonical_action_id"] for row in rows),
        "evidence_119": sorted(
            rows,
            key=lambda row: (row["vote_date"], row["rollcall_number"]),
            reverse=True,
        ),
    }


def review_packet(
    candidate: dict[str, Any],
    m11d: dict[str, Any],
    m11f: dict[str, Any],
) -> dict[str, Any]:
    mappings = mapping_rows(candidate)
    accepted_actions = {
        row["action_id"] for row in m11d["subject"]["implementation_records"]
    }
    accepted_episodes = {
        row["primary_episode_id"] for row in m11f["subject"]["action_accounting"]
    }
    mapped_actions = {action_id for row in mappings for action_id in row["action_ids"]}
    mapped_episodes = {
        episode_id for row in mappings for episode_id in row["episode_ids"]
    }
    lineage_actions = {
        action_id
        for row in mappings
        for action_id in row["semantic_lineage_action_ids"]
    }
    lineage_episodes = {
        episode_id
        for row in mappings
        for episode_id in row["semantic_lineage_episode_ids"]
    }
    if not (
        mapped_actions <= accepted_actions
        and mapped_episodes <= accepted_episodes
        and lineage_actions <= accepted_actions
        and lineage_episodes <= accepted_episodes
    ):
        raise ValueError("M11M mapping exceeds accepted M11D/M11F evidence")
    return {
        "schema_version": "m11m_site_integration_review_packet_v1",
        "artifact_id": "site-integration-review-packet:f000477:national_security_foreign:119:v1",
        "candidate_binding": {
            "artifact_id": candidate["artifact_id"],
            "candidate_subject_sha256": candidate["candidate_subject_sha256"],
        },
        "base_sha": BASE_SHA,
        "artifact_bindings": {
            "m11l_authority": candidate["subject"]["m11l_authority_binding"],
            "m11l_implementation": candidate["subject"]["m11l_implementation_binding"],
            "m11l_parity": candidate["subject"]["m11l_parity_binding"],
            "m11d_implementation": {
                "artifact_id": m11d["artifact_id"],
                "subject_sha256": m11d["implementation_subject_sha256"],
                "file_sha256": canonical_file_sha256(M11D),
            },
            "m11f_implementation": {
                "artifact_id": m11f["artifact_id"],
                "subject_sha256": m11f["implementation_subject_sha256"],
                "file_sha256": canonical_file_sha256(M11F),
            },
        },
        "accounting": {
            "wording_items": len(mappings),
            "mapped_unique_actions": len(mapped_actions),
            "mapped_unique_episodes": len(mapped_episodes),
            "semantic_lineage_unique_actions": len(lineage_actions),
            "semantic_lineage_unique_episodes": len(lineage_episodes),
            "accepted_interpreted_actions": len(accepted_actions),
            "accepted_episodes": len(accepted_episodes),
            "blocked_actions": [BLOCKED_ACTION_ID],
        },
        "mapping_rows": mappings,
        "semantic_proofs": {
            "every_mapping_uses_accepted_semantic_content": True,
            "raw_vote_direction_inference": False,
            "mapped_actions_subset_of_m11d": mapped_actions <= accepted_actions,
            "mapped_episodes_subset_of_m11f": mapped_episodes <= accepted_episodes,
            "semantic_lineage_actions_subset_of_m11d": (
                lineage_actions <= accepted_actions
            ),
            "semantic_lineage_episodes_subset_of_m11f": (
                lineage_episodes <= accepted_episodes
            ),
            "blocked_action_excluded": BLOCKED_ACTION_ID not in mapped_actions,
            "ukraine_public_mixed_label_suppressed": True,
            "no_direction_items_have_no_public_status": True,
            "public_support_may_be_narrower_than_semantic_lineage": True,
        },
        "scope_behavior": {
            "119": "candidate_available_with_explicit_server_preview_opt_in",
            "all": "candidate_available_with_explicit_119th_congress_boundary",
            "118": "receipts_only_fail_closed",
            "other": "request_validation_failure",
        },
        "controls": candidate["subject"]["controls"],
    }


def packet_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# M11M National Security Site-Integration Review Packet",
        "",
        f"- Base: `{packet['base_sha']}`",
        f"- Candidate: `{packet['candidate_binding']['artifact_id']}`",
        f"- Candidate subject SHA-256: `{packet['candidate_binding']['candidate_subject_sha256']}`",
        "- State: detached, non-authorizing, publication inactive, production unselectable",
        "- Scope: 119th Congress through July 23, 2026",
        "- Blocked action: `house:119:2:278` remains excluded from every finding",
        "",
        "## Exact 18-item mapping",
        "",
        "| Surface | Public title | Public actions | Lineage actions | Episodes |",
        "|---|---|---:|---:|---:|",
    ]
    for row in packet["mapping_rows"]:
        lines.append(
            f"| {row['surface']} | {row['title']} | {row['action_count']} | "
            f"{row['semantic_lineage_action_count']} | {row['episode_count']} |"
        )
    lines.extend(
        [
            "",
            "## Review boundaries",
            "",
            "The candidate is available only when the server-side preview flag and exact M11M preview token are both present. The default API path and production selector remain unchanged. `scope=all` keeps an explicit 119th-Congress analytical boundary; `scope=118` fails closed to vote receipts.",
            "",
            "The detailed governed mappings and hashes remain in the JSON packet. The frontend receives only public wording, public limitations, evidence counts, directions explicitly accepted by M11L, and supporting action identities.",
            "",
            "No publication, database, production persistence, deployment, or protected-ZIP operation is performed.",
            "",
        ]
    )
    return "\n".join(lines)


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
        "schema_version": "m11m_site_integration_screenshot_manifest_v1",
        "artifact_id": "site-integration-screenshot-manifest:f000477:national_security_foreign:119:v1",
        "candidate_artifact_id": (
            "site-integration-candidate:f000477:national_security_foreign:119:v1"
        ),
        "captures": [
            {
                "path": (
                    "docs/editorial/full_record_reviews/site_integration_candidates/"
                    "f000477_national_security_foreign_119_v1/screenshots/"
                    f"{name}"
                ),
                "viewport_width": width,
                "viewport_height": height,
                "zoom": zoom,
                "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest(),
            }
            for name, width, height, zoom in definitions
        ],
    }


def build(check: bool = False) -> dict[str, Any]:
    authority, implementation, parity, m11d, m11f = preflight()
    candidate = compile_site_integration_candidate(
        authority=authority,
        implementation=implementation,
        parity=parity,
        authority_file_sha256=EXPECTED[AUTHORITY][0],
        implementation_file_sha256=EXPECTED[IMPLEMENTATION][0],
        parity_file_sha256=EXPECTED[PARITY][0],
        accepted_base_sha=BASE_SHA,
        preview_data=preview_data(m11d, m11f),
    )
    validate_site_integration_candidate(candidate)
    packet = review_packet(candidate, m11d, m11f)
    candidate_text = json_text(candidate)
    packet["candidate_binding"]["file_sha256"] = hashlib.sha256(
        candidate_text.encode("utf-8")
    ).hexdigest()
    manifest = screenshot_manifest()
    if manifest is not None:
        packet["screenshot_manifest"] = {
            "artifact_id": manifest["artifact_id"],
            "capture_count": len(manifest["captures"]),
            "file_sha256": hashlib.sha256(
                json_text(manifest).encode("utf-8")
            ).hexdigest(),
        }
    write_or_check(OUTPUT / "site_integration_candidate.json", candidate_text, check)
    write_or_check(OUTPUT / "review_packet.json", json_text(packet), check)
    write_or_check(OUTPUT / "review_packet.md", packet_markdown(packet), check)
    if manifest is not None:
        write_or_check(OUTPUT / "screenshot_manifest.json", json_text(manifest), check)
    return {"candidate": candidate, "review_packet": packet}


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
                "wording_items": result["review_packet"]["accounting"]["wording_items"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
