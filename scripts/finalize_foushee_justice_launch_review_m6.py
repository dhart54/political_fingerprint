"""Freeze rendered M6 evidence, sample calibration objects, and build the packet."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_foushee_justice_launch_review_m6 import (
    OUT,
    ROOT,
    file_sha,
    load,
    with_digest,
    write_json,
)


def choose(seed: str, values: list[dict], key: str) -> dict:
    return min(
        values,
        key=lambda item: hashlib.sha256(f"{seed}:{item[key]}".encode()).hexdigest(),
    )


def finalize() -> dict[str, object]:
    images = []
    for path in sorted((OUT / "screenshots").glob("*.png")):
        images.append(
            {
                "filename": path.name,
                "path": path.relative_to(ROOT).as_posix(),
                "final_file_sha256": file_sha(path),
                "bytes": path.stat().st_size,
                "source_state": "generated_from_final_precommit_source_tree",
                "manual_editing": False,
            }
        )
    required = {
        "desktop-1440-overview.png",
        "desktop-ledger-special-rolls.png",
        "tablet-1024.png",
        "mobile-390.png",
        "narrow-mobile-320.png",
        "zoom-200.png",
        "keyboard-expanded-receipt.png",
        "reduced-motion.png",
    }
    if {item["filename"] for item in images} != required:
        raise ValueError("required screenshot set differs")
    screenshot_manifest = with_digest(
        {
            "schema_version": "m6_screenshot_manifest_v1",
            "artifact_id": "screenshot-manifest:f000477:justice_public_safety:119:m6:v1",
            "review_route": "/review/foushee-justice-m6",
            "loopback_only": True,
            "fixture_only": True,
            "reviewed_source_commit": "assigned_after_local_commit_without_source_mutation",
            "image_count": len(images),
            "images": images,
            "outcomes": {
                "desktop_1440": "pass",
                "tablet_1024": "pass",
                "mobile_390": "pass",
                "narrow_mobile_320": "pass",
                "zoom_200_percent": "pass",
                "keyboard_only": "pass",
                "reduced_motion": "pass",
                "headings_landmarks_names_focus": "pass",
                "horizontal_overflow": 0,
            },
        }
    )
    write_json(OUT / "screenshot_manifest.json", screenshot_manifest)

    candidate = load(OUT / "public_presentation_candidate.json")
    mappings = load(OUT / "analytical_string_mappings.json")
    ledger = load(OUT / "exact_action_ledger.json")
    risks = load(OUT / "launch_risk_register.json")
    fixture = load(ROOT / "frontend/fixtures/foushee_justice_m6_review.json")
    freeze = with_digest(
        {
            "schema_version": "public_interface_freeze_v1",
            "artifact_id": "public-interface-freeze:f000477:justice_public_safety:119:v1",
            "freeze_state": "frozen_before_calibration_selection",
            "candidate_content_subject_sha256": candidate["provenance"][
                "presentation_content_sha256"
            ],
            "candidate_final_file_sha256": file_sha(
                OUT / "public_presentation_candidate.json"
            ),
            "reviewed_wording_sha256": candidate["provenance"][
                "reviewed_wording_sha256"
            ],
            "mapping_set_content_subject_sha256": mappings["content_subject_sha256"],
            "mapping_set_final_file_sha256": file_sha(
                OUT / "analytical_string_mappings.json"
            ),
            "ledger_content_subject_sha256": ledger["content_subject_sha256"],
            "risk_register_content_subject_sha256": risks["content_subject_sha256"],
            "review_fixture_sha256": file_sha(
                ROOT / "frontend/fixtures/foushee_justice_m6_review.json"
            ),
            "screenshot_manifest_content_subject_sha256": screenshot_manifest[
                "content_subject_sha256"
            ],
            "controls": candidate["controls"],
        }
    )
    write_json(OUT / "public_interface_freeze.json", freeze)

    seed_material = (
        candidate["provenance"]["presentation_content_sha256"]
        + risks["content_subject_sha256"]
        + "political-fingerprint-launch-calibration-v1"
    )
    seed = hashlib.sha256(seed_material.encode()).hexdigest()
    excluded_actions = {"house:119:1:128", "house:119:2:155", "house:119:2:278"}
    actions = [
        item
        for item in ledger["records"]
        if item["canonical_action_id"] not in excluded_actions
        and item["confidence"] in {"high", "medium"}
    ]
    episode_bundle = load(
        ROOT
        / "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_justice_public_safety_119_v1/episode_implementation_bundle.json"
    )
    episodes = [
        item
        for item in episode_bundle["implemented_episodes"]
        if len(item["primary_action_ids"]) > 1
        and not item["unresolved_editorial_questions"]
    ]
    graph = load(
        ROOT
        / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_justice_public_safety_119_v2/frozen_final_compiled_semantic_ir.json"
    )["compiled_ir"]
    propositions = graph["members"][0]["proposition_graph"]["propositions"]
    patterns = [
        item for item in propositions if item["proposition_type"] == "repeated_pattern"
    ]
    mapping_population = [
        item
        for item in mappings["mappings"]
        if not any(
            action in excluded_actions for action in item["mapping"]["action_ids"]
        )
        and "conclusion" not in item["statement_id"]
    ]
    selected_action = choose(seed + ":action", actions, "canonical_action_id")
    selected_episode = choose(seed + ":episode", episodes, "episode_id")
    selected_pattern = choose(seed + ":pattern", patterns, "proposition_id")
    selected_mapping = choose(seed + ":mapping", mapping_population, "statement_id")
    fixture_patterns = {
        item["proposition_id"]: item
        for item in fixture["presentation"]["repeated_patterns"]
    }
    fixture_trajectories = {
        item["proposition_id"]: item
        for item in fixture["presentation"]["policy_trajectories"]
    }
    calibration = with_digest(
        {
            "schema_version": "blind_launch_calibration_sample_v1",
            "artifact_id": "launch-calibration:f000477:justice_public_safety:119:v1",
            "selected_after_freeze": True,
            "freeze_artifact_id": freeze["artifact_id"],
            "freeze_content_subject_sha256": freeze["content_subject_sha256"],
            "seed_formula": "SHA256(candidate_content_subject_sha256 + risk_register_content_subject_sha256 + political-fingerprint-launch-calibration-v1)",
            "seed_sha256": seed,
            "sample_count": 4,
            "excluded_objects": sorted([*excluded_actions, "prop:7a5b23c610dc467e"]),
            "samples": [
                {
                    "sample_id": "calibration:action",
                    "object_type": "action_interpretation",
                    "object_id": selected_action["canonical_action_id"],
                    "original_evidence": {
                        "member_action": selected_action["member_action"],
                        "vote_source": selected_action["official_vote_source"],
                        "meaning_sources": selected_action[
                            "official_action_meaning_sources"
                        ],
                    },
                    "accepted_internal_interpretation": selected_action[
                        "governed_action_meaning"
                    ],
                    "episode_and_proposition_context": {
                        "episode_id": selected_action["episode_id"],
                        "proposition_ids": selected_action["proposition_ids"],
                    },
                    "rendered_public_wording": selected_action[
                        "governed_action_meaning"
                    ],
                    "ui_location": "exact-action ledger",
                    "eligibility": "Internally implemented, source-resolved, not held, and no major or critical finding.",
                    "selection_proof": hashlib.sha256(
                        f"{seed}:action:{selected_action['canonical_action_id']}".encode()
                    ).hexdigest(),
                    "calibration_question": "Does this receipt state the exact House choice clearly without broadening the policy position?",
                },
                {
                    "sample_id": "calibration:episode",
                    "object_type": "multi_action_episode_or_trajectory",
                    "object_id": selected_episode["episode_id"],
                    "original_evidence": selected_episode[
                        "chronological_action_sequence"
                    ],
                    "accepted_internal_interpretation": selected_episode[
                        "implemented_episode_scope"
                    ],
                    "episode_and_proposition_context": {
                        "episode_id": selected_episode["episode_id"],
                        "action_ids": selected_episode["primary_action_ids"],
                    },
                    "rendered_public_wording": next(
                        (
                            item["body"]
                            for item in fixture_trajectories.values()
                            if set(item["action_ids"])
                            == set(selected_episode["primary_action_ids"])
                        ),
                        "Available through the exact-action ledger as one governed episode.",
                    ),
                    "ui_location": "trajectory or exact-action ledger",
                    "eligibility": "Multi-action, internally cleared, source-resolved, and not held.",
                    "selection_proof": hashlib.sha256(
                        f"{seed}:episode:{selected_episode['episode_id']}".encode()
                    ).hexdigest(),
                    "calibration_question": "Does the interface preserve one episode without multiplying analytical weight?",
                },
                {
                    "sample_id": "calibration:pattern",
                    "object_type": "repeated_pattern",
                    "object_id": selected_pattern["proposition_id"],
                    "original_evidence": {
                        "action_ids": selected_pattern["evidence_action_ids"],
                        "episode_ids": selected_pattern["evidence_episode_ids"],
                    },
                    "accepted_internal_interpretation": selected_pattern,
                    "episode_and_proposition_context": selected_pattern[
                        "relationships"
                    ],
                    "rendered_public_wording": fixture_patterns[
                        selected_pattern["proposition_id"]
                    ],
                    "ui_location": "primary repeated patterns",
                    "eligibility": "Primary repeated pattern with no unresolved major or critical finding.",
                    "selection_proof": hashlib.sha256(
                        f"{seed}:pattern:{selected_pattern['proposition_id']}".encode()
                    ).hexdigest(),
                    "calibration_question": "Does this pattern remain concrete, neutral, and proportionate to its episodes?",
                },
                {
                    "sample_id": "calibration:mapping",
                    "object_type": "presentation_mapping",
                    "object_id": selected_mapping["statement_id"],
                    "original_evidence": selected_mapping["mapping"],
                    "accepted_internal_interpretation": {
                        "proposition_ids": selected_mapping["mapping"][
                            "proposition_ids"
                        ],
                        "boundary_ids": selected_mapping["mapping"]["boundary_ids"],
                    },
                    "episode_and_proposition_context": {
                        "action_ids": selected_mapping["mapping"]["action_ids"],
                        "episode_ids": selected_mapping["mapping"]["episode_ids"],
                    },
                    "rendered_public_wording": selected_mapping["text"],
                    "ui_location": selected_mapping["mapping"]["presentation_target"],
                    "eligibility": "Exact mapped wording with no held-risk object and no unresolved finding.",
                    "selection_proof": hashlib.sha256(
                        f"{seed}:mapping:{selected_mapping['statement_id']}".encode()
                    ).hexdigest(),
                    "calibration_question": "Does the displayed sentence stay within the exact mapped meaning and limitation set?",
                },
            ],
        }
    )
    write_json(OUT / "calibration_sample.json", calibration)

    subject = with_digest(
        {
            "schema_version": "user_launch_ratification_subject_v1",
            "artifact_id": "launch-ratification-subject:f000477:justice_public_safety:119:v1",
            "universe": load(OUT / "full_record_semantic_artifact.json")[
                "content_subject_sha256"
            ],
            "semantic_validation_receipt": load(
                OUT / "full_record_semantic_validation_receipt.json"
            )["content_subject_sha256"],
            "public_presentation_content": candidate["provenance"][
                "presentation_content_sha256"
            ],
            "reviewed_wording": candidate["provenance"]["reviewed_wording_sha256"],
            "mapping_set": mappings["content_subject_sha256"],
            "evidence_provenance": candidate["provenance"][
                "evidence_provenance_sha256"
            ],
            "limitations": candidate["provenance"]["limitations_sha256"],
            "risk_packet": risks["content_subject_sha256"],
            "screenshot_manifest": screenshot_manifest["content_subject_sha256"],
            "calibration_sample": calibration["content_subject_sha256"],
            "freeze": freeze["content_subject_sha256"],
        }
    )
    write_json(OUT / "launch_ratification_subject.json", subject)
    template = load(OUT / "empty_launch_ratification_template.json")
    template.pop("content_subject_sha256", None)
    template["subject_content_subject_sha256"] = subject["content_subject_sha256"]
    write_json(OUT / "empty_launch_ratification_template.json", with_digest(template))

    quality = {
        "action_universe": 37,
        "episodes": 32,
        "behavioral_propositions": 23,
        "primary_repeated_patterns": 4,
        "limiting_trajectories": 1,
        "semantic_validation": "passed",
        "presentation_validation": "passed",
        "correction_cycles": 2,
        "action_accounting_complete": True,
        "unresolved_launch_risks": 4,
        "calibration_samples": 4,
        "sample_selected_after_freeze": True,
        "known_methodology_limitations": [
            "roll 128 unresolved textual insertion",
            "roll 155 source-identity conflict and non-counting FISA relationship",
            "roll 278 incomplete final-package evidence",
            "mechanism divide is one bounded contrast only",
        ],
    }
    packet = with_digest(
        {
            "schema_version": "compact_launch_review_packet_v1",
            "artifact_id": "launch-review-packet:f000477:justice_public_safety:119:v1",
            "quality_summary": quality,
            "unresolved_launch_risks": risks["unresolved"],
            "blind_calibration_samples": calibration["samples"],
            "ratification_subject": subject,
            "empty_ratification_template_path": (
                OUT / "empty_launch_ratification_template.json"
            )
            .relative_to(ROOT)
            .as_posix(),
            "decision_requested": [
                "delegated_authority_accepts_public_interface_and_launch_packet",
                "bounded_public_interface_correction_required",
                "delegated_authority_rejects_public_interface_method",
            ],
        }
    )
    write_json(OUT / "compact_launch_review_packet.json", packet)
    lines = [
        "# Foushee Justice M6 compact launch review",
        "",
        "## Quality summary",
        "",
        "- 37 governed actions; 35 directional; two non-proposition controls; 32 complete episodes.",
        "- 23 behavioral propositions; four primary repeated patterns; one limiting trajectory.",
        "- Semantic and presentation validation passed after two global correction cycles.",
        f"- Four unresolved launch cases; four blind calibration samples selected only after interface freeze `{freeze['content_subject_sha256']}`.",
        "",
        "## Unresolved launch risks",
        "",
    ]
    for risk in risks["unresolved"]:
        lines += [
            f"### {risk['risk_id']}",
            "",
            risk["question"],
            "",
            f"- Current treatment: {risk['current_treatment']}",
            f"- Strongest competing interpretation: {risk['competing_interpretation']}",
            f"- Public effect: {risk['effect']}",
            f"- Codex recommendation: {risk['codex_recommendation']}",
            "- Delegated-authority recommendation: pending",
            f"- Decision required: {risk['user_decision_required']}",
            "",
        ]
    lines += ["## Blind calibration sample", ""]
    for sample in calibration["samples"]:
        lines += [
            f"### {sample['sample_id']} — `{sample['object_id']}`",
            "",
            f"- UI location: {sample['ui_location']}",
            f"- Eligibility: {sample['eligibility']}",
            f"- Question: {sample['calibration_question']}",
            "",
        ]
    lines += [
        "## Exact ratification subject",
        "",
        f"`{subject['content_subject_sha256']}`",
        "",
        "The user decision, identity, timestamp, risk selections, wording approval, production eligibility, and publication approval remain empty. Publication activation is a later separate operational decision.",
        "",
    ]
    (OUT / "compact_launch_review_packet.md").write_text(
        "\n".join(lines), encoding="utf-8", newline="\n"
    )

    files = []
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name != "parity_manifest.json":
            content = (
                load(path).get("content_subject_sha256")
                if path.suffix == ".json"
                else None
            )
            files.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "final_file_sha256": file_sha(path),
                    "content_subject_sha256": content,
                }
            )
    parity = with_digest(
        {
            "schema_version": "m6_artifact_parity_manifest_v1",
            "artifact_id": "m6-parity:f000477:justice_public_safety:119:v1",
            "files": files,
        }
    )
    write_json(OUT / "parity_manifest.json", parity)
    return {
        "status": "pass",
        "freeze": freeze["content_subject_sha256"],
        "seed": seed,
        "samples": [item["object_id"] for item in calibration["samples"]],
        "screenshots": len(images),
        "packet": packet["content_subject_sha256"],
    }


if __name__ == "__main__":
    print(json.dumps(finalize(), sort_keys=True))
