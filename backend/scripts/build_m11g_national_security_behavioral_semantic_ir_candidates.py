"""Build the detached M11G behavioral Semantic IR candidate review package."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.compiler import compile_behavioral_candidate_ir  # noqa: E402
from scripts.m11g_behavioral_semantic_ir_candidate_data import (  # noqa: E402
    CORRECTED_PROPOSITIONS,
)


POST_M11F_MERGE_MAIN = "43caaf4b0087ab473ee771ed9c8c4acde68be554"
ACCEPTED_M11F_HEAD = "326baa61ec44c5a560b98e3208ec990ff9bd2308"
M11F_AUTHORITY = {
    "artifact_id": "human-policy-episode-authority:f000477:national_security_foreign:119:v1",
    "file_sha256": "bd3ee15f7cd4508a194df4bb093da673889d460b073af21d7235cf62d9f6f627",
    "authority_subject_sha256": "cc24113a101b68874d6e37869b4de4c8ec72e553687a11bab8d3abe7248a149f",
}
M11F_IMPLEMENTATION = {
    "artifact_id": "policy-episode-decision-implementation:f000477:national_security_foreign:119:v1",
    "file_sha256": "546441f951b1788f248520ee9cfef7f718c6ea8225f98818aa35c17220e60239",
    "implementation_subject_sha256": "0d4c9e65ae8e9432103b961a59f2816436cd51a7dae0448ce54b55d5bd94397d",
}
M11F_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_national_security_foreign_119_v1"
)
AUTHORITY_PATH = M11F_ROOT / "human_policy_episode_authority.json"
IMPLEMENTATION_PATH = M11F_ROOT / "episode_decision_implementation_bundle.json"
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_candidates/f000477_national_security_foreign_119_v1"
)
GRAPH_PATH = OUTPUT_ROOT / "behavioral_semantic_ir_candidate_graph.json"
DECISION_PATH = OUTPUT_ROOT / "human_behavioral_semantic_ir_decision_template.json"
DOSSIER_PATH = OUTPUT_ROOT / "human_review_dossier.md"
PARITY_PATH = OUTPUT_ROOT / "parity_manifest.json"
GRAPH_ID = "behavioral-semantic-ir-candidates:f000477:national_security_foreign:119:v1"
DECISION_ID = "behavioral-semantic-ir-human-decision-template:f000477:national_security_foreign:119:v1"

REVIEWED_HEAD_PROPOSITIONS = [
    {
        "proposition_id": "pattern-fisa-title-vii-extension-opposition",
        "source_relationship_id": "fisa-title-vii-extension-attempts",
        "proposition_type": "repeated_pattern",
        "proposition": "Across two separate measures, Foushee opposed extending the authorities of title VII of the Foreign Intelligence Surveillance Act of 1978.",
        "direction": "opposition",
        "rationale": "Both accepted episode meanings state the same bounded operative extension choice, and both accepted episode directions oppose it.",
        "material_limitations": [
            "The measures are separate legislative events; this is a repeated behavioral proposition, not one policy episode.",
            "Matching top-level purposes do not establish that every provision or extension duration was identical.",
        ],
        "competing_interpretations": [
            "Retain the two choices only as separate episodes because their full texts may differ beyond the shared operative purpose."
        ],
        "overlap_relationships": [],
        "relevant_contrasts": [
            {
                "episode_ids": ["single-119-s-1318-2-142"],
                "reason": "S. 1318 was a multi-title package that included a title VII extension provision; opposition to the whole package cannot establish a position on that component.",
            }
        ],
        "trajectory_change": None,
    },
    {
        "proposition_id": "pattern-iran-war-powers-removal-support",
        "source_relationship_id": "iran-war-powers-hostilities-removal",
        "proposition_type": "repeated_pattern",
        "proposition": "Across five separate resolutions, Foushee supported directing removal of United States Armed Forces from hostilities with or against Iran under the War Powers Resolution.",
        "direction": "support",
        "rationale": "Each accepted episode meaning independently states the same removal mechanism and Iran-hostilities target, and all five accepted episode directions support it.",
        "material_limitations": [
            "The resolutions are separate events with small wording differences, including with, against, and unauthorized hostilities.",
            "The pattern does not establish that the factual hostilities or legal posture were unchanged across dates.",
        ],
        "competing_interpretations": [
            "Treat wording and timing differences as too material for one repeated-pattern proposition."
        ],
        "overlap_relationships": [],
        "relevant_contrasts": [
            {
                "episode_ids": [
                    "single-119-hconres-61-1-345",
                    "single-119-hamdt-99-1-244",
                ],
                "reason": "Removal from hostilities involving presidentially designated terrorist organizations and repeal of earlier AUMFs use different targets or mechanisms and do not enlarge the Iran pattern.",
            }
        ],
        "trajectory_change": None,
    },
    {
        "proposition_id": "pattern-lebanon-war-powers-removal-support",
        "source_relationship_id": "lebanon-war-powers-hostilities-removal",
        "proposition_type": "repeated_pattern",
        "proposition": "Across two separate resolutions, Foushee supported directing removal of United States Armed Forces from hostilities in Lebanon under the War Powers Resolution.",
        "direction": "support",
        "rationale": "Both accepted episode meanings state the same Lebanon-hostilities removal mechanism, and both accepted episode directions support it.",
        "material_limitations": [
            "The resolutions are separate legislative events; recurrence does not establish a single episode or motive."
        ],
        "competing_interpretations": [
            "Retain the two choices only as separate episodes because each resolution may reflect a distinct factual context."
        ],
        "overlap_relationships": [],
        "relevant_contrasts": [
            {
                "episode_ids": ["single-119-hamdt-60-1-210"],
                "reason": "Prohibiting assistance to the Lebanese Armed Forces is a funding choice, not the War Powers removal proposition.",
            }
        ],
        "trajectory_change": None,
    },
    {
        "proposition_id": "pattern-venezuela-war-powers-removal-support",
        "source_relationship_id": "venezuela-war-powers-hostilities-removal",
        "proposition_type": "repeated_pattern",
        "proposition": "Across two separate resolutions, Foushee supported directing removal of United States Armed Forces from unauthorized hostilities within or against Venezuela.",
        "direction": "support",
        "rationale": "Both accepted episode meanings state the same unauthorized-hostilities removal choice, and both accepted episode directions support it.",
        "material_limitations": [
            "The resolutions occurred in different House sessions and use within-or-against versus from-Venezuela wording."
        ],
        "competing_interpretations": [
            "Treat the wording and session difference as too material for a repeated-pattern proposition."
        ],
        "overlap_relationships": [],
        "relevant_contrasts": [
            {
                "episode_ids": [
                    "single-119-hconres-61-1-345",
                    "single-119-hconres-38-2-85",
                ],
                "reason": "Other War Powers resolutions concern different targets; shared mechanism alone does not merge country-specific propositions.",
            }
        ],
        "trajectory_change": None,
    },
]

# Preserve the reviewed-head definitions above as correction history while the
# deterministic build uses the bounded human-corrected candidate set.
PROPOSITIONS = CORRECTED_PROPOSITIONS

REVIEW_CONTRAST_ACTIONS = {
    "same-parent-amendments": {
        "house:119:1:208",
        "house:119:1:209",
        "house:119:1:210",
        "house:119:1:212",
        "house:119:1:244",
        "house:119:1:246",
        "house:119:1:248",
        "house:119:1:249",
        "house:119:1:250",
        "house:119:1:251",
        "house:119:1:252",
        "house:119:1:255",
        "house:119:1:257",
        "house:119:1:258",
        "house:119:1:259",
        "house:119:1:260",
        "house:119:1:262",
        "house:119:2:174",
        "house:119:2:175",
        "house:119:2:243",
        "house:119:2:244",
        "house:119:2:247",
        "house:119:2:256",
        "house:119:2:259",
        "house:119:2:260",
        "house:119:2:261",
        "house:119:2:262",
        "house:119:2:263",
        "house:119:2:264",
        "house:119:2:265",
        "house:119:2:266",
        "house:119:2:268",
        "house:119:2:269",
        "house:119:2:273",
        "house:119:2:275",
        "house:119:2:276",
    },
    "ukraine-scope": {
        "house:119:1:209",
        "house:119:1:255",
        "house:119:2:207",
        "house:119:2:264",
    },
    "jordan-scope": {"house:119:1:208", "house:119:2:244"},
    "military-sex-gender-mechanisms": {
        "house:119:1:246",
        "house:119:1:248",
        "house:119:1:249",
        "house:119:2:266",
        "house:119:2:268",
    },
    "defense-energy-mechanisms": {
        "house:119:1:250",
        "house:119:1:251",
        "house:119:1:259",
        "house:119:2:259",
        "house:119:2:260",
        "house:119:2:261",
        "house:119:2:262",
    },
    "package-component-boundary": {"house:119:2:142"},
    "distinct-war-powers-or-aumf-mechanisms": {"house:119:1:244", "house:119:1:345"},
}


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sealed(value: dict[str, Any], field: str) -> dict[str, Any]:
    value = dict(value)
    value[field] = digest(value)
    return value


def write_or_check(path: Path, content: str, check: bool) -> None:
    if check:
        if path.read_text(encoding="utf-8") != content:
            raise ValueError(
                f"{path.relative_to(ROOT)} differs from deterministic regeneration"
            )
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def preflight() -> dict[str, Any]:
    if file_digest(AUTHORITY_PATH) != M11F_AUTHORITY["file_sha256"]:
        raise ValueError("M11F authority digest differs")
    if file_digest(IMPLEMENTATION_PATH) != M11F_IMPLEMENTATION["file_sha256"]:
        raise ValueError("M11F implementation digest differs")
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    if (
        authority["artifact_id"] != M11F_AUTHORITY["artifact_id"]
        or authority["authority_subject_sha256"]
        != M11F_AUTHORITY["authority_subject_sha256"]
    ):
        raise ValueError("M11F authority identity differs")
    if (
        implementation["artifact_id"] != M11F_IMPLEMENTATION["artifact_id"]
        or implementation["implementation_subject_sha256"]
        != M11F_IMPLEMENTATION["implementation_subject_sha256"]
    ):
        raise ValueError("M11F implementation identity differs")
    return implementation


def build_input(
    implementation: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    subject = implementation["subject"]
    episodes = subject["implementation_records"]
    episodes_by_id = {row["episode_id"]: row for row in episodes}
    relationships = {
        row["relationship_id"]: row
        for row in subject["non_primary_relationship_evidence"]
    }
    candidates = []
    owners: dict[str, str] = {}
    owner_types: dict[str, str] = {}
    for definition in PROPOSITIONS:
        episode_ids = definition["evidence_episode_ids"]
        relationship_id = definition["source_relationship_id"]
        if relationship_id is not None:
            relationship = relationships[relationship_id]
            if episode_ids != relationship["replacement_primary_episode_ids"]:
                raise ValueError(f"relationship evidence differs for {relationship_id}")
            relationship_binding = {
                "relationship_subject_sha256": relationship[
                    "relationship_subject_sha256"
                ],
                "inherited_authority": False,
                "use": "review_hint_retested_against_accepted_episode_meanings_and_directions",
            }
        else:
            relationship_binding = {
                "relationship_subject_sha256": None,
                "inherited_authority": False,
                "use": "none_independently_derived_from_accepted_m11f_episodes",
            }
        candidate = {
            **definition,
            "source_relationship_binding": relationship_binding,
            "episode_semantic_evidence": {
                episode_id: episodes_by_id[episode_id]["policy_proposition"]
                for episode_id in episode_ids
            },
        }
        candidates.append(candidate)
        for episode_id in episode_ids:
            if episode_id in owners:
                raise ValueError(f"inflated primary ownership for {episode_id}")
            owners[episode_id] = definition["proposition_id"]
            owner_types[episode_id] = definition["proposition_type"]

    relationship_episode_ids = {
        episode_id
        for relationship in relationships.values()
        for episode_id in relationship["replacement_primary_episode_ids"]
    }
    if not relationship_episode_ids <= set(owners):
        raise ValueError("preserved relationship evidence lacks corrected disposition")
    accounting = []
    for episode in sorted(episodes, key=lambda row: row["episode_id"]):
        episode_id = episode["episode_id"]
        action_ids = set(episode["primary_action_ids"])
        contrast_ids = sorted(
            contrast_id
            for contrast_id, contrast_action_ids in REVIEW_CONTRAST_ACTIONS.items()
            if action_ids & contrast_action_ids
        )
        if episode_id in owners:
            disposition = {
                "repeated_pattern": "supports_proposed_repeated_pattern",
                "trajectory": "supports_proposed_trajectory",
                "notable_choice": "supports_proposed_notable_choice",
            }[owner_types[episode_id]]
            reason = "Accepted episode meaning, direction, and lineage independently satisfy the bounded candidate proposition."
        elif contrast_ids:
            disposition = "retained_as_limit_or_contrast"
            reason = (
                "Retained as non-pattern contrast evidence for: "
                + ", ".join(contrast_ids)
                + ". Shared topic, parent, or mechanism does not establish one bounded behavioral proposition."
            )
        else:
            disposition = "no_safe_higher_level_behavioral_proposition"
            reason = "This singleton is retained without promotion: recurrence, independent notability, or substantive chronological change was not safely established."
        accounting.append(
            {
                "episode_id": episode_id,
                "primary_proposition_id": owners.get(episode_id),
                "disposition": disposition,
                "reason": reason,
            }
        )
    compiler_input = {
        "subject": subject["subject"],
        "episodes": episodes,
        "blocked_action_ids": ["house:119:2:278"],
        "proposition_candidates": candidates,
        "episode_accounting": accounting,
    }
    return compiler_input, list(relationships.values())


def concise(value: str, limit: int = 220) -> str:
    compact = " ".join(value.split())
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


def dossier(graph: dict[str, Any], relationships: list[dict[str, Any]]) -> str:
    propositions = graph["proposition_graph"]["propositions"]
    counts = Counter(row["disposition"] for row in graph["episode_accounting"])
    type_counts = Counter(row["proposition_type"] for row in propositions)
    lines = [
        "# M11G Behavioral Semantic IR Candidate Review",
        "",
        "This is a detached, non-authorizing review package. It proposes 15 selective behavioral propositions from accepted M11F episodes. It accepts no Semantic IR, creates no synthesis, and contains no public wording.",
        "",
        "## Accounting",
        "",
        f"- Accepted M11F episodes accounted for: {len(graph['episode_accounting'])} of 81.",
        f"- Proposed repeated patterns: {type_counts['repeated_pattern']}.",
        f"- Proposed notable choices: {type_counts['notable_choice']}.",
        f"- Proposed trajectories: {type_counts['trajectory']}.",
        f"- Episodes supporting a proposed pattern: {counts['supports_proposed_repeated_pattern']}.",
        f"- Episodes supporting a proposed trajectory: {counts['supports_proposed_trajectory']}.",
        f"- Episodes supporting a proposed notable choice: {counts['supports_proposed_notable_choice']}.",
        f"- Episodes retained as limits or contrasts: {counts['retained_as_limit_or_contrast']}.",
        f"- Episodes retained without a safe higher-level proposition: {counts['no_safe_higher_level_behavioral_proposition']}.",
        "- Overlapping primary evidence owners: 0.",
        "- H.R. 8800 / `house:119:2:278` remains source-blocked, uninterpreted, and unavailable.",
        "",
        "## Proposed behavioral conclusions",
        "",
    ]
    episodes = {
        row["episode_id"]: row
        for row in preflight()["subject"]["implementation_records"]
    }
    for proposition in propositions:
        lines.extend(
            [
                f"### `{proposition['proposition_id']}`",
                "",
                f"- Candidate: {proposition['proposition']}",
                f"- Type/direction: `{proposition['proposition_type']}` / `{proposition['direction']}`.",
                f"- Episode evidence: `{', '.join(proposition['evidence_episode_ids'])}`.",
                f"- Rationale: {proposition['rationale']}",
                f"- Limitations: {'; '.join(proposition['material_limitations'])}",
                f"- Competing interpretation: {'; '.join(proposition['competing_interpretations'])}",
                f"- Relevant contrasts: {'; '.join(contrast['reason'] for contrast in proposition['relevant_contrasts']) or 'None identified beyond the recorded limitations.'}",
                f"- Conclusion relevance: `{proposition['conclusion_relevance']}`.",
                "- Chronology and accepted choices:",
                "",
            ]
        )
        for episode_id in sorted(
            proposition["evidence_episode_ids"],
            key=lambda value: episodes[value]["actions"][0]["official_action_date"],
        ):
            episode = episodes[episode_id]
            action = episode["actions"][0]
            lines.append(
                f"  - {action['official_action_date']} — `{episode_id}` / `{action['action_id']}` — {concise(action['accepted_exact_action_meaning'])}"
            )
        lines.extend(
            [
                "",
                "This candidate has no synthesis effect.",
                "",
            ]
        )
    lines.extend(
        [
            "## Four prior relationship-hint dispositions",
            "",
        ]
    )
    for relationship in sorted(relationships, key=lambda row: row["relationship_id"]):
        lines.append(
            f"- `{relationship['relationship_id']}`: proposed as a repeated-pattern candidate only after independent episode-meaning and direction checks. The M11F relationship record contributes no inherited authority and remains non-primary evidence."
        )
    lines.extend(
        [
            "",
            "## Non-proposition ledger",
            "",
            "The governed JSON retains all 49 non-proposition episode IDs and the reason for each. They are not silently omitted: each remains a canonical internal episode but is not promoted merely for sharing a topic, parent package, vocabulary, date sequence, or broad policy area.",
            "",
            "The corrected Ukraine, Jordan, and military/DoD sex-and-gender candidates remain bounded across their expressly enumerated mechanisms. The defense/energy group remains too heterogeneous, and remaining same-parent relationships do not become patterns automatically. Broad package votes do not supply component positions.",
            "",
            "## Human decisions required",
            "",
            "Review each of the 15 candidates as accept, revise, or reject: eight repeated patterns, one trajectory, and six notable choices. No additional routine or lower-signal singleton is proposed.",
            "",
            "Semantic IR acceptance, synthesis, public wording, publication, persistence, database writes, production, and deployment remain unauthorized.",
            "",
        ]
    )
    return "\n".join(lines)


def build(check: bool = False) -> dict[str, Any]:
    implementation = preflight()
    compiler_input, relationships = build_input(implementation)
    compiled = compile_behavioral_candidate_ir(compiler_input)
    episode_evidence_ledger = [
        {
            "episode_id": episode["episode_id"],
            "episode_record_id": episode["record_id"],
            "episode_record_subject_sha256": episode["record_subject_sha256"],
            "member_direction": episode["member_direction"],
            "policy_proposition": episode["policy_proposition"],
            "primary_action_ids": episode["primary_action_ids"],
            "material_limitations": episode["material_limitations"],
            "actions": [
                {
                    "action_id": action["action_id"],
                    "official_action_date": action["official_action_date"],
                    "accepted_exact_action_meaning": action[
                        "accepted_exact_action_meaning"
                    ],
                    "accepted_interpretation_record_id": action[
                        "accepted_interpretation_record_id"
                    ],
                    "accepted_interpretation_record_subject_sha256": action[
                        "accepted_interpretation_record_subject_sha256"
                    ],
                    "source_references": action["source_references"],
                }
                for action in episode["actions"]
            ],
        }
        for episode in compiler_input["episodes"]
    ]
    graph = sealed(
        {
            "schema_version": "full_record_behavioral_semantic_ir_candidate_package_v1",
            "artifact_id": GRAPH_ID,
            "candidate_state": "complete_pending_human_substantive_review",
            "base_binding": {
                "post_m11f_merge_main": POST_M11F_MERGE_MAIN,
                "accepted_m11f_head": ACCEPTED_M11F_HEAD,
            },
            "m11f_authority_binding": M11F_AUTHORITY,
            "m11f_implementation_binding": M11F_IMPLEMENTATION,
            "blocked_action_ids": ["house:119:2:278"],
            "episode_evidence_ledger": episode_evidence_ledger,
            "compiled_candidate_ir": compiled,
            "accepted_semantic_ir": False,
            "canonical_semantic_ir": False,
            "synthesis_included": False,
            "public_wording_included": False,
            "authorizing": False,
        },
        "candidate_subject_sha256",
    )
    decision = sealed(
        {
            "schema_version": "full_record_behavioral_semantic_ir_human_decision_template_v1",
            "artifact_id": DECISION_ID,
            "candidate_artifact_id": GRAPH_ID,
            "candidate_subject_sha256": graph["candidate_subject_sha256"],
            "decision_state": "empty_not_authorizing",
            "decisions": [
                {
                    "proposition_id": row["proposition_id"],
                    "decision": None,
                    "bounded_revision": None,
                    "reviewer_notes": None,
                }
                for row in graph["compiled_candidate_ir"]["proposition_graph"][
                    "propositions"
                ]
            ],
            "reviewer": None,
            "reviewed_at_utc": None,
            "authorizing": False,
        },
        "decision_template_subject_sha256",
    )
    dossier_text = dossier(graph["compiled_candidate_ir"], relationships)
    write_or_check(GRAPH_PATH, json_text(graph), check)
    write_or_check(DECISION_PATH, json_text(decision), check)
    write_or_check(DOSSIER_PATH, dossier_text, check)
    entries = []
    for path, subject_digest in (
        (GRAPH_PATH, graph["candidate_subject_sha256"]),
        (DECISION_PATH, decision["decision_template_subject_sha256"]),
        (DOSSIER_PATH, None),
    ):
        entries.append(
            {
                "path": path.relative_to(OUTPUT_ROOT).as_posix(),
                "file_sha256": hashlib.sha256(
                    (
                        json_text(graph)
                        if path == GRAPH_PATH
                        else json_text(decision)
                        if path == DECISION_PATH
                        else dossier_text
                    ).encode()
                ).hexdigest(),
                "content_subject_sha256": subject_digest,
            }
        )
    parity = sealed(
        {
            "schema_version": "full_record_behavioral_semantic_ir_candidate_parity_v1",
            "artifact_id": "behavioral-semantic-ir-candidate-parity:f000477:national_security_foreign:119:v1",
            "entries": entries,
        },
        "parity_subject_sha256",
    )
    write_or_check(PARITY_PATH, json_text(parity), check)
    return {
        "graph": graph,
        "decision": decision,
        "parity": parity,
        "counts": Counter(
            row["proposition_type"]
            for row in compiled["proposition_graph"]["propositions"]
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build(args.check)
    print(
        json.dumps(
            {
                "artifact_id": GRAPH_ID,
                "candidate_subject_sha256": result["graph"]["candidate_subject_sha256"],
                "proposition_counts": result["counts"],
                "episode_count": len(
                    result["graph"]["compiled_candidate_ir"]["episode_accounting"]
                ),
                "parity_subject_sha256": result["parity"]["parity_subject_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
