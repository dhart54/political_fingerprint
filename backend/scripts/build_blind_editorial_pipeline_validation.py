"""Build the locked selection and first generic Justice candidate generation."""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.summaries.editorial_candidate_selection import (
    assert_selection_locked,
    select_blind_candidate,
    select_featured_episode_ids,
)
from backend.scripts.build_justice_cross_member_validation import (
    EPISODE_ROLLS,
    PUBLICATION,
    build_overlay_from_actions,
    evaluate_overlay,
)


STARTING_COMMIT = "7bce7467cebfde4fd2f164bdcecb596ba0fd1e91"
BUILD_IDENTIFIER = f"blind-editorial-pipeline-validation-v1@{STARTING_COMMIT}"
REFERENCE_MEMBER_IDS = ("F000477", "M001184")
SOURCE_DIR = ROOT / "docs/editorial/justice_cross_member_validation_v1"
OUTPUT_DIR = ROOT / "docs/editorial/blind_editorial_pipeline_validation_v1"
FRONTEND_OUTPUT = ROOT / "frontend/lib/blindEditorialPipelineValidationData.mjs"


def build() -> tuple[dict, dict]:
    overlays = _read_json(SOURCE_DIR / "member_overlays.json")["overlays"]
    selection = select_blind_candidate(
        overlays=overlays,
        reference_member_ids=REFERENCE_MEMBER_IDS,
        episode_rolls=EPISODE_ROLLS,
        starting_commit=STARTING_COMMIT,
        build_identifier=BUILD_IDENTIFIER,
    )
    selected_id = selection["selected_member"]["member_id"]
    source_overlay = next(item for item in overlays if item["member"]["bioguide_id"] == selected_id)
    actions_by_roll = {item["roll"]: item["action"] for item in source_overlay["roll_actions"]}
    majorities = {
        item["roll"]: {source_overlay["member"].get("party"): item.get("party_majority_action")}
        for item in source_overlay["roll_actions"]
    }
    overlay = build_overlay_from_actions(deepcopy(source_overlay["member"]), actions_by_roll, majorities)
    shared_episodes = _read_json(
        ROOT / overlay["shared_episode_set"]["episode_map_path"]
    )["episodes"]
    inference = evaluate_overlay(overlay, shared_episodes)
    inference["publication"] = deepcopy(PUBLICATION)
    featured_episode_ids = select_featured_episode_ids(overlay=overlay, inference=inference)
    generated = {
        "schema_version": "blind_editorial_generated_candidate_v1",
        "starting_commit": STARTING_COMMIT,
        "deterministic_build_identifier": BUILD_IDENTIFIER,
        "selection_lock": selection["selection_lock"],
        "selected_member": deepcopy(selection["selected_member"]),
        "generation_order": [
            "locked_candidate_selection",
            "generic_member_overlay",
            "coverage",
            "episode_trajectories",
            "generic_theme_candidate_evaluation",
            "bounded_issue_synthesis",
            "upstream_featured_episode_selection",
        ],
        "overlay": overlay,
        "inference": inference,
        "featured_episode_ids": featured_episode_ids,
        "shared_evidence_identity": _shared_evidence_identity(),
        "publication": deepcopy(PUBLICATION),
    }
    assert_selection_locked(selection, generated)
    return selection, generated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    selection, generated = build()
    outputs = {
        OUTPUT_DIR / "candidate_selection.json": _serialize(selection),
        OUTPUT_DIR / "final_generated_candidate.json": _serialize(generated),
        FRONTEND_OUTPUT: _frontend_module(generated),
    }
    if args.check:
        first_path = OUTPUT_DIR / "first_generated_candidate.json"
        if not first_path.exists():
            raise SystemExit("first generated candidate is missing")
        assert_selection_locked(selection, _read_json(first_path))
        mismatches = [
            str(path.relative_to(ROOT))
            for path, content in outputs.items()
            if not path.exists() or path.read_text(encoding="utf-8") != content
        ]
        if mismatches:
            raise SystemExit("blind editorial artifacts differ: " + ", ".join(mismatches))
        print("Blind selection and first candidate generation are deterministic and locked.")
        return 0
    first_path = OUTPUT_DIR / "first_generated_candidate.json"
    if not first_path.exists():
        first_path.parent.mkdir(parents=True, exist_ok=True)
        first_path.write_text(_serialize(generated), encoding="utf-8")
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(
        f"Selected {generated['selected_member']['member_display_name']} "
        f"({generated['selected_member']['member_id']}) and wrote the locked selection and current generation."
    )
    return 0


def _shared_evidence_identity() -> dict:
    paths = [
        Path("docs/editorial/valerie_foushee_justice_public_safety_gold_v1/policy_episode_map.json"),
        Path("docs/editorial/valerie_foushee_justice_public_safety_gold_v1/source_manifest.json"),
        *[
            path.relative_to(ROOT)
            for path in sorted(
                (ROOT / "docs/editorial/valerie_foushee_justice_public_safety_gold_v1/measures").glob("*.json")
            )
        ],
    ]
    files = []
    for relative in paths:
        value = _read_json(ROOT / relative)
        files.append({
            "path": relative.as_posix(),
            "semantic_sha256": sha256(
                json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            ).hexdigest(),
        })
    return {
        "contract": "The candidate references the unchanged member-neutral Justice dossier; it does not copy or rewrite it.",
        "files": files,
    }


def _frontend_module(generated: dict) -> str:
    payload = {
        "schemaVersion": generated["schema_version"],
        "startingCommit": generated["starting_commit"],
        "deterministicBuildIdentifier": generated["deterministic_build_identifier"],
        "selectionLock": generated["selection_lock"],
        "selectedMember": generated["selected_member"],
        "overlay": generated["overlay"],
        "inference": generated["inference"],
        "featuredEpisodeIds": generated["featured_episode_ids"],
        "publication": generated["publication"],
    }
    return (
        "// Generated by backend/scripts/build_blind_editorial_pipeline_validation.py.\n"
        "// Review-only member overlay and inference; shared legislative facts remain in the Justice dossier.\n"
        f"export const blindEditorialPipelineValidationData = Object.freeze({json.dumps(payload, indent=2, ensure_ascii=False)});\n"
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _serialize(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
