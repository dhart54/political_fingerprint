"""Build detached M14G Education & Workforce site-integration review artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.editorial_presentations.education_workforce_m14g_integration_candidate import (  # noqa: E402
    BASELINE_MAIN_SHA,
    M14G_PREVIEW_TOKEN,
    OLD_HR5408_MEANING,
    compile_m14g_candidate,
)
from backend.app.editorial_presentations.integration_candidate import (  # noqa: E402
    canonical_file_sha256,
)


M14F = ROOT / "docs/editorial/public_wording_candidates/f000477_education_workforce_m14f_v1"
M14D = ROOT / "docs/editorial/analytical_candidates/f000477_education_workforce_m14d_v1"
V2 = ROOT / "docs/editorial/shared_corpora/house_119_v2"
INPUTS = {
    "m14f_accepted_public_copy": M14F / "accepted_public_copy.json",
    "m14f_human_authority": M14F / "human_public_wording_prominence_authority.json",
    "m14d_accepted_ledger": M14D / "accepted_behavioral_findings.json",
    "m14d_human_authority": M14D / "human_behavioral_candidate_authority.json",
    "v2_shared_action_core": V2 / "shared_action_core.json",
    "v2_member_projection": V2 / "member_projections/f000477.json",
    "v2_promotion_manifest": V2 / "promotion_manifest.json",
}
OUTPUT = ROOT / "docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1"
SCREENSHOTS = [
    {
        "name": "desktop_overview.png",
        "viewport": {"width": 1440, "height": 1600},
        "route": "/?representative=leg_valerie_p_foushee&issue=EDUCATION_WORKFORCE&scope=119",
        "state": "overview and repeated patterns",
    },
    {
        "name": "desktop_notable_expanded.png",
        "viewport": {"width": 1440, "height": 1600},
        "route": "/?representative=leg_valerie_p_foushee&issue=EDUCATION_WORKFORCE&scope=119",
        "state": "Other notable choices expanded; H.R. 1048 boundaries expanded",
    },
    {
        "name": "desktop_hr5408_receipt.png",
        "viewport": {"width": 1440, "height": 1600},
        "route": "/?representative=leg_valerie_p_foushee&issue=EDUCATION_WORKFORCE&scope=119",
        "state": "collective-bargaining supporting votes; H.R. 5408 receipt expanded",
    },
    {
        "name": "mobile_overview.png",
        "viewport": {"width": 390, "height": 844},
        "route": "/?representative=leg_valerie_p_foushee&issue=EDUCATION_WORKFORCE&scope=119",
        "state": "mobile overview and beginning of patterns",
    },
]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_or_check(path: Path, content: str, *, check: bool) -> None:
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            raise ValueError(f"deterministic M14G artifact differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _binding(name: str, payload: dict[str, Any]) -> dict[str, str]:
    path = INPUTS[name]
    subject_sha = next(
        (
            str(payload[key])
            for key in (
                "accepted_public_copy_subject_sha256",
                "authority_subject_sha256",
                "findings_subject_sha256",
                "corpus_sha256",
                "projection_sha256",
                "manifest_sha256",
            )
            if payload.get(key)
        ),
        "",
    )
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "file_sha256": canonical_file_sha256(path),
        "subject_sha256": subject_sha,
    }


def screenshot_manifest() -> dict[str, Any]:
    screenshot_root = OUTPUT / "screenshots"
    captures = []
    for definition in SCREENSHOTS:
        path = screenshot_root / definition["name"]
        captures.append(
            {
                "repo_path": (
                    OUTPUT.relative_to(ROOT) / "screenshots" / definition["name"]
                ).as_posix(),
                "viewport": definition["viewport"],
                "route": definition["route"],
                "requested_scope": "119",
                "preview_candidate": M14G_PREVIEW_TOKEN,
                "open_expanded_state": definition["state"],
                "file_sha256": sha256(path) if path.exists() else None,
                "source_commit": BASELINE_MAIN_SHA,
            }
        )
    return {
        "schema_version": "m14g_screenshot_manifest_v1",
        "artifact_id": "screenshot-manifest:f000477:education_workforce:m14g:v1",
        "source_head_at_capture": BASELINE_MAIN_SHA,
        "captures": captures,
    }


def build(*, check: bool = False) -> dict[str, Any]:
    payloads = {name: load(path) for name, path in INPUTS.items()}
    bindings = {name: _binding(name, payload) for name, payload in payloads.items()}
    candidate = compile_m14g_candidate(
        accepted_public_copy=payloads["m14f_accepted_public_copy"],
        public_wording_authority=payloads["m14f_human_authority"],
        accepted_findings=payloads["m14d_accepted_ledger"],
        behavioral_authority=payloads["m14d_human_authority"],
        shared_core=payloads["v2_shared_action_core"],
        member_projection=payloads["v2_member_projection"],
        promotion_manifest=payloads["v2_promotion_manifest"],
        file_bindings=bindings,
    )
    presentation = candidate["subject"]["presentation"]
    receipts = candidate["subject"]["receipt_projections"]
    hr5408 = next(
        row for row in receipts if row["canonical_action_id"] == "house:119:2:216"
    )["governed_receipt_projection"]
    hr1005 = next(
        row for row in receipts if row["canonical_action_id"] == "house:119:1:312"
    )["governed_receipt_projection"]
    manifest = screenshot_manifest()
    records = payloads["m14f_accepted_public_copy"]["subject"]["accepted_wording_records"]
    review = {
        "schema_version": "m14g_site_integration_review_package_v1",
        "artifact_id": "site-integration-review-package:f000477:education_workforce:m14g:v1",
        "candidate_binding": {
            "artifact_id": candidate["artifact_id"],
            "candidate_subject_sha256": candidate["candidate_subject_sha256"],
        },
        "rendered_hierarchy": {
            "main_takeaway": {
                "wording_item_id": presentation["overview"]["wording_item_id"],
                "public_title": presentation["overview"]["public_title"],
                "primary_sentence": presentation["overview"]["primary_sentence"],
                "evidence_count_label": presentation["overview"]["evidence_count_label"],
            },
            "repeated_patterns": [
                {
                    "wording_item_id": item["wording_item_id"],
                    "public_title": item["public_title"],
                    "primary_sentence": item["primary_sentence"],
                    "evidence_count_label": item["evidence_count_label"],
                }
                for item in presentation["repeated_patterns"]
            ],
            "notable_choice": {
                "wording_item_id": presentation["notable_choices"][0]["wording_item_id"],
                "public_title": presentation["notable_choices"][0]["public_title"],
                "primary_sentence": presentation["notable_choices"][0]["primary_sentence"],
                "evidence_count_label": presentation["notable_choices"][0]["evidence_count_label"],
                "direction_label": presentation["notable_choices"][0]["direction_label"],
            },
            "counts": {
                "overviews": 1,
                "repeated_patterns": 2,
                "notable_choices": 1,
                "syntheses": 0,
                "trajectories": 0,
                "findings": 3,
            },
        },
        "rendered_limitations_by_surface": {
            "overview_top_level": [row["body"] for row in presentation["limitations"]],
            "china_linked_pattern": presentation["repeated_patterns"][0]["limitations"],
            "collective_bargaining_pattern": presentation["repeated_patterns"][1]["limitations"],
            "hr1048_notable_choice": presentation["notable_choices"][0]["limitations"],
            "treatment_instance_count": 7,
        },
        "wording_item_sha256s": {
            row["wording_item_id"]: row["wording_item_sha256"] for row in records
        },
        "receipt_accounting": {
            "actions": 17,
            "episodes": 16,
            "finding_supporting_action_ids": presentation["evidence_metadata"]["display_action_ids"],
            "main_takeaway_action_ids": presentation["overview"]["action_ids"],
        },
        "hr1005_non_directional_proof": {
            "canonical_action_id": "house:119:1:312",
            "official_status": hr1005["member_action"],
            "exact_choice_effect": hr1005["exact_choice_position_effect"],
            "supports_finding": False,
        },
        "hr1048_one_episode_proof": {
            "episode_id": "hr-1048-amendment-and-final-passage",
            "action_ids": ["house:119:1:79", "house:119:1:83"],
        },
        "hr5408_governed_receipt": {
            "canonical_action_id": "house:119:2:216",
            "exact_action_meaning": hr5408["exact_action_meaning"],
            "old_m13m_semantic_regression": {
                "old_sentence": OLD_HR5408_MEANING,
                "old_sentence_absent": OLD_HR5408_MEANING
                not in hr5408["exact_action_meaning"],
                "equals_v2_accepted_exact_action_meaning": True,
            },
        },
        "preview_contract": {
            "token": M14G_PREVIEW_TOKEN,
            "server_environment": "EDITORIAL_PRESENTATION_PREVIEW=1",
            "frontend_environment": f"NEXT_PUBLIC_EDITORIAL_PRESENTATION_PREVIEW={M14G_PREVIEW_TOKEN}",
            "routes": [
                "/legislators/{legislator_id}/editorial-presentations",
                "/legislators/{legislator_id}/positions",
                "/legislators/{legislator_id}/positions/{domain}/evidence",
            ],
        },
        "screenshot_inventory": manifest["captures"],
        "downstream_denials": {
            "accepted": False,
            "authorizing": False,
            "public": False,
            "production_selectable": False,
            "publication_eligible": False,
            "publication_active": False,
            "database_writes": False,
            "production_writes": False,
            "deployment": False,
            "merge": False,
        },
    }
    write_or_check(OUTPUT / "site_integration_candidate.json", json_text(candidate), check=check)
    write_or_check(OUTPUT / "review_package.json", json_text(review), check=check)
    write_or_check(OUTPUT / "screenshot_manifest.json", json_text(manifest), check=check)
    return {"candidate": candidate, "review_package": review, "manifest": manifest}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build(check=args.check)
    print(
        json.dumps(
            {
                "candidate_subject_sha256": result["candidate"]["candidate_subject_sha256"],
                "receipt_count": len(result["candidate"]["subject"]["receipt_projections"]),
                "screenshot_count": len(result["manifest"]["captures"]),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
