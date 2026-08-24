"""Build detached M13G Education & Workforce behavioral Semantic IR candidates."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.compiler import compile_behavioral_candidate_ir  # noqa: E402
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
)
from backend.scripts.m13g_education_workforce_behavioral_semantic_ir_candidate_data import (  # noqa: E402
    CONTRAST_ACTIONS,
    PROPOSITIONS,
)


POST_M13E_MERGE_MAIN = "641910bb0c8bb633a76fe95ef113d396d8db881b"
M13F_AUTHORITY = {
    "artifact_id": "human-policy-episode-authority:f000477:education_workforce:119:v1",
    "file_sha256": "dd84f769e2a2c7d547972d126f4aa5c5d272bd37a5308fbd2324a9926f91a299",
    "authority_subject_sha256": "6381c88b1ee7e7e085e0ac9779616b58b93a5037ed3b19b5af7c56adb113b8a1",
}
M13F_IMPLEMENTATION = {
    "artifact_id": "policy-episode-decision-implementation:f000477:education_workforce:119:v1",
    "file_sha256": "74212c3a768d33bb223bba81fbe92471d2ac698a10538e46d46c7683b3586f6e",
    "implementation_subject_sha256": "1b11d068af95815952dee6877d8b97e5998539bfc56ddd0820e9b4b061688f3b",
}
M13F_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_education_workforce_119_v1"
)
AUTHORITY_PATH = M13F_ROOT / "human_policy_episode_authority.json"
IMPLEMENTATION_PATH = M13F_ROOT / "episode_decision_implementation_bundle.json"
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_candidates/f000477_education_workforce_119_v1"
)
GRAPH_PATH = OUTPUT_ROOT / "behavioral_semantic_ir_candidate_graph.json"
DECISION_PATH = OUTPUT_ROOT / "human_behavioral_semantic_ir_decision_template.json"
DOSSIER_PATH = OUTPUT_ROOT / "human_review_dossier.md"
PARITY_PATH = OUTPUT_ROOT / "parity_manifest.json"
GRAPH_SCHEMA_PATH = (
    ROOT
    / "docs/methodology/full_record_behavioral_semantic_ir_candidate_package_v1.schema.json"
)
DECISION_SCHEMA_PATH = (
    ROOT
    / "docs/methodology/full_record_behavioral_semantic_ir_human_decision_v1.schema.json"
)
GRAPH_ID = "behavioral-semantic-ir-candidates:f000477:education_workforce:119:v1"
DECISION_ID = (
    "behavioral-semantic-ir-human-decision-template:f000477:education_workforce:119:v1"
)

INSUFFICIENT_BASES = [
    "shared_topic",
    "shared_agency",
    "shared_statute",
    "shared_cra_mechanism",
    "shared_vote_direction",
    "party",
    "sponsor",
    "ideology",
]


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sealed(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = dict(value)
    result[field] = digest(result)
    return result


def write_or_check(path: Path, content: str, *, check: bool) -> None:
    if check:
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            raise ValueError(f"{path.relative_to(ROOT)} differs from regeneration")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def preflight() -> dict[str, Any]:
    if canonical_file_sha256(AUTHORITY_PATH) != M13F_AUTHORITY["file_sha256"]:
        raise ValueError("M13F authority digest differs")
    if canonical_file_sha256(IMPLEMENTATION_PATH) != M13F_IMPLEMENTATION["file_sha256"]:
        raise ValueError("M13F implementation digest differs")
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    if not (
        authority["artifact_id"] == M13F_AUTHORITY["artifact_id"]
        and authority["authority_subject_sha256"]
        == M13F_AUTHORITY["authority_subject_sha256"]
        and implementation["artifact_id"] == M13F_IMPLEMENTATION["artifact_id"]
        and implementation["implementation_subject_sha256"]
        == M13F_IMPLEMENTATION["implementation_subject_sha256"]
    ):
        raise ValueError("M13F accepted identity differs")
    return implementation


def build_input(implementation: dict[str, Any]) -> dict[str, Any]:
    subject = implementation["subject"]
    episodes = subject["implementation_records"]
    episodes_by_id = {row["episode_id"]: row for row in episodes}
    candidates = []
    relationship_evidence = {}
    owners: dict[str, str] = {}
    owner_types: dict[str, str] = {}
    for definition in PROPOSITIONS:
        episode_ids = definition["evidence_episode_ids"]
        candidate = {
            **definition,
            "source_relationship_binding": {
                "relationship_subject_sha256": None,
                "inherited_authority": False,
                "use": "independently_derived_from_accepted_m13f_episode_meanings_and_directions",
            },
            "episode_semantic_evidence": {
                episode_id: episodes_by_id[episode_id]["policy_proposition"]
                for episode_id in episode_ids
            },
        }
        candidates.append(candidate)
        if definition["proposition_type"] == "repeated_pattern":
            relationship_evidence[definition["proposition_id"]] = {
                "shared_bounded_choice": definition["rationale"],
                "episode_support": {
                    episode_id: episodes_by_id[episode_id]["policy_proposition"]
                    for episode_id in episode_ids
                },
                "insufficient_bases_rejected": INSUFFICIENT_BASES,
                "material_differences_preserved": definition["material_limitations"],
            }
        for episode_id in episode_ids:
            if episode_id in owners:
                raise ValueError(f"multiple primary owners for {episode_id}")
            owners[episode_id] = definition["proposition_id"]
            owner_types[episode_id] = definition["proposition_type"]

    accounting = []
    for episode in sorted(episodes, key=lambda row: row["episode_id"]):
        episode_id = episode["episode_id"]
        action_ids = set(episode["primary_action_ids"])
        contrast_ids = sorted(
            contrast_id
            for contrast_id, action_set in CONTRAST_ACTIONS.items()
            if action_ids & action_set
        )
        if episode_id in owners:
            owner_type = owner_types[episode_id]
            disposition = f"supports_proposed_{owner_type}"
            reason = (
                "Accepted episode meaning and direction independently support the "
                f"bounded {owner_type.replace('_', '-')} proposition."
            )
        elif episode["member_direction"] == "non_directional_not_voting":
            disposition = "unused_non_directional_evidence"
            reason = "Not Voting is resolved but non-directional and cannot support a directional behavioral proposition."
        elif contrast_ids:
            disposition = "retained_as_limit_or_contrast"
            reason = (
                "Retained as contrast evidence for "
                + ", ".join(contrast_ids)
                + "; shared topic, agency, statute, mechanism, or direction does not establish one bounded behavioral proposition."
            )
        else:
            disposition = "no_safe_higher_level_behavioral_proposition"
            reason = "No recurring bounded choice, structured direction change, or independently selective notable-choice basis was established."
        accounting.append(
            {
                "episode_id": episode_id,
                "primary_proposition_id": owners.get(episode_id),
                "disposition": disposition,
                "reason": reason,
            }
        )
    return {
        "subject": subject["subject"],
        "episodes": episodes,
        "blocked_action_ids": [],
        "proposition_candidates": candidates,
        "episode_accounting": accounting,
        "relationship_evidence_by_proposition": relationship_evidence,
    }


def concise(value: str, limit: int = 240) -> str:
    compact = " ".join(value.split())
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


def dossier(graph: dict[str, Any], episodes: dict[str, Any]) -> str:
    propositions = graph["proposition_graph"]["propositions"]
    counts = Counter(row["disposition"] for row in graph["episode_accounting"])
    lines = [
        "# M13G Education & Workforce Behavioral Semantic IR Candidate Review",
        "",
        "This detached package proposes one repeated pattern and one notable mixed choice from the 16 accepted M13F episodes. It accepts no Semantic IR, creates no synthesis, and contains no public wording.",
        "",
        "## Review summary",
        "",
        "- Repeated-pattern candidates: 1.",
        "- Trajectory candidates: 0; no two accepted episodes establish a strictly chronological, substantively comparable direction change. The two H.R. 1048 choices remain one accepted mixed episode and are not split to manufacture a trajectory.",
        "- Notable-choice candidates: 1; the accepted H.R. 1048 mixed episode preserves support for H.Amdt. 12 and opposition to the distinct whole package.",
        f"- Episodes supporting candidates: {counts['supports_proposed_repeated_pattern']}.",
        f"- Episodes supporting notable choices: {counts['supports_proposed_notable_choice']}.",
        f"- Episodes retained as contrasts: {counts['retained_as_limit_or_contrast']}.",
        f"- Episodes retained without a safe higher-level proposition: {counts['no_safe_higher_level_behavioral_proposition']}.",
        f"- Non-directional unused episodes: {counts['unused_non_directional_evidence']}.",
        "- Primary overlaps: 0.",
        "",
        "## Proposed candidates",
        "",
    ]
    for proposition in propositions:
        lines.extend(
            [
                f"### `{proposition['proposition_id']}`",
                "",
                f"- Type/direction: `{proposition['proposition_type']}` / `{proposition['direction']}`.",
                f"- Candidate: {proposition['proposition']}",
                f"- Evidence episodes: `{', '.join(proposition['evidence_episode_ids'])}`.",
                f"- Rationale: {proposition['rationale']}",
                f"- Material limitations: {'; '.join(proposition['material_limitations'])}",
                f"- Competing interpretation: {'; '.join(proposition['competing_interpretations'])}",
                f"- Relevant contrasts: {'; '.join(item['reason'] for item in proposition['relevant_contrasts']) or 'None beyond the recorded limitations.'}",
                "- Overlap relationships: none.",
                "- Episode-level evidence:",
                "",
            ]
        )
        for episode_id in proposition["evidence_episode_ids"]:
            episode = episodes[episode_id]
            for action in episode["actions"]:
                lines.append(
                    f"  - {action['official_action_date']} — `{episode_id}` / `{action['action_id']}` — {concise(action['accepted_exact_action_meaning'])}"
                )
        lines.extend(["", "This candidate has no synthesis effect.", ""])
    lines.extend(
        [
            "## Compact non-proposition accounting",
            "",
            "H.R. 1005 / `single-119-hr-1005-1-312` remains `non_directional_not_voting` and is explicitly unused as directional evidence.",
            "",
            "H.R. 1049 is retained as contrast evidence: its parent-awareness purpose differs from the bounded federal-funding restriction mechanism in the proposed H.R. 881 / H.R. 1069 pattern.",
            "",
            "The remaining eleven episodes are explicit no-safe-aggregation cases. Higher Education Act references, foreign-source or China subject matter, school setting, labor/workforce wording, party direction, and shared vote direction were rejected as sufficient grouping bases.",
            "",
            "The H.R. 1048 notable candidate remains mixed: it attributes support only to H.Amdt. 12 and opposition only to final passage of the whole package. It does not attribute the final-passage choice to any package component.",
            "",
            "## Complete episode-role accounting",
            "",
        ]
    )
    for row in sorted(graph["episode_accounting"], key=lambda item: item["episode_id"]):
        owner = row["primary_proposition_id"] or "none"
        lines.append(
            f"- `{row['episode_id']}` — `{row['disposition']}` — owner `{owner}` — {row['reason']}"
        )
    lines.extend(
        [
            "",
            "Semantic IR acceptance, synthesis, public wording, publication, persistence, database writes, production, and deployment remain unauthorized.",
            "",
        ]
    )
    return "\n".join(lines)


def build(*, check: bool = False) -> dict[str, Any]:
    implementation = preflight()
    compiler_input = build_input(implementation)
    compiled = compile_behavioral_candidate_ir(compiler_input)
    episodes = {row["episode_id"]: row for row in compiler_input["episodes"]}
    ledger = [
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
            "base_binding": {"post_m13e_merge_main": POST_M13E_MERGE_MAIN},
            "accepted_policy_episode_authority_binding": M13F_AUTHORITY,
            "accepted_policy_episode_implementation_binding": M13F_IMPLEMENTATION,
            "blocked_action_ids": [],
            "episode_evidence_ledger": ledger,
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
                for row in compiled["proposition_graph"]["propositions"]
            ],
            "reviewer": None,
            "reviewed_at_utc": None,
            "authorizing": False,
        },
        "decision_template_subject_sha256",
    )
    dossier_text = dossier(compiled, episodes)
    for path, value, schema_path in (
        (GRAPH_PATH, graph, GRAPH_SCHEMA_PATH),
        (DECISION_PATH, decision, DECISION_SCHEMA_PATH),
    ):
        errors = sorted(Draft7Validator(load(schema_path)).iter_errors(value), key=str)
        if errors:
            raise ValueError(f"{path.name} schema error: {errors[0].message}")
        write_or_check(path, json_text(value), check=check)
    write_or_check(DOSSIER_PATH, dossier_text, check=check)
    entries = [
        {
            "path": path.relative_to(OUTPUT_ROOT).as_posix(),
            "file_sha256": hashlib.sha256(content.encode()).hexdigest(),
            "content_subject_sha256": subject_sha,
        }
        for path, content, subject_sha in (
            (GRAPH_PATH, json_text(graph), graph["candidate_subject_sha256"]),
            (
                DECISION_PATH,
                json_text(decision),
                decision["decision_template_subject_sha256"],
            ),
            (DOSSIER_PATH, dossier_text, None),
        )
    ]
    parity = sealed(
        {
            "schema_version": "full_record_behavioral_semantic_ir_candidate_parity_v1",
            "artifact_id": "behavioral-semantic-ir-candidate-parity:f000477:education_workforce:119:v1",
            "entries": entries,
        },
        "parity_subject_sha256",
    )
    write_or_check(PARITY_PATH, json_text(parity), check=check)
    return {
        "graph": graph,
        "decision": decision,
        "parity": parity,
        "counts": Counter(
            row["proposition_type"]
            for row in compiled["proposition_graph"]["propositions"]
        ),
        "accounting": Counter(
            row["disposition"] for row in compiled["episode_accounting"]
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build(check=args.check)
    print(
        json.dumps(
            {
                "artifact_id": GRAPH_ID,
                "candidate_subject_sha256": result["graph"]["candidate_subject_sha256"],
                "proposition_counts": result["counts"],
                "episode_accounting": result["accounting"],
                "episode_count": len(
                    result["graph"]["compiled_candidate_ir"]["episode_accounting"]
                ),
                "parity_subject_sha256": result["parity"]["parity_subject_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
