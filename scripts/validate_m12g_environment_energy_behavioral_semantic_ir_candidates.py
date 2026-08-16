"""Independently validate detached M12G behavioral Semantic IR candidates."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_source_readiness import canonical_file_sha256  # noqa: E402
from backend.scripts.build_m12g_environment_energy_behavioral_semantic_ir_candidates import (  # noqa: E402
    AUTHORITY_PATH,
    DECISION_PATH,
    DECISION_SCHEMA_PATH,
    DOSSIER_PATH,
    GRAPH_PATH,
    GRAPH_SCHEMA_PATH,
    IMPLEMENTATION_PATH,
    M12F_AUTHORITY,
    M12F_IMPLEMENTATION,
    PARITY_PATH,
    PROPOSITIONS,
    build,
    digest,
)


EXPECTED_EVIDENCE = {
    row["proposition_id"]: row["evidence_episode_ids"] for row in PROPOSITIONS
}
EXPECTED_M11G_HASHES = {
    "behavioral_semantic_ir_candidate_graph.json": "b0bc182a5ef1bd860b78045696e0ff06919e21c104fa61840ece0d403f8168e7",
    "human_behavioral_semantic_ir_decision_template.json": "35d3763bd1d19c6a64c01e95a6759404a6868b46c933b90cfb15e2bdeffbcdb2",
    "human_review_dossier.md": "7121eeef5beb39cc04113338b5ad5d1aa9f2deb1f3c7d7d886332da112be60ed",
    "parity_manifest.json": "f701bd297249f17abf0cf8ec5a64339fadd9a0d53b238e7f57e1b3bca19cb425",
}
M11G_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_candidates/f000477_national_security_foreign_119_v1"
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_seal(value: dict[str, Any], field: str, label: str) -> None:
    require(
        value[field]
        == digest({key: child for key, child in value.items() if key != field}),
        f"{label} seal differs",
    )


def validate() -> dict[str, Any]:
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    graph_artifact = load(GRAPH_PATH)
    decision = load(DECISION_PATH)
    parity = load(PARITY_PATH)
    require(
        canonical_file_sha256(AUTHORITY_PATH) == M12F_AUTHORITY["file_sha256"],
        "M12F authority changed",
    )
    require(
        authority["authority_subject_sha256"]
        == M12F_AUTHORITY["authority_subject_sha256"],
        "M12F authority subject changed",
    )
    require(
        canonical_file_sha256(IMPLEMENTATION_PATH)
        == M12F_IMPLEMENTATION["file_sha256"],
        "M12F implementation changed",
    )
    require(
        implementation["implementation_subject_sha256"]
        == M12F_IMPLEMENTATION["implementation_subject_sha256"],
        "M12F implementation subject changed",
    )

    for artifact, schema_path, label in (
        (graph_artifact, GRAPH_SCHEMA_PATH, "candidate graph"),
        (decision, DECISION_SCHEMA_PATH, "decision template"),
    ):
        errors = sorted(
            Draft7Validator(load(schema_path)).iter_errors(artifact), key=str
        )
        require(
            not errors, f"{label} schema error: {errors[0].message if errors else ''}"
        )
    verify_seal(graph_artifact, "candidate_subject_sha256", "candidate graph")
    verify_seal(decision, "decision_template_subject_sha256", "decision template")
    verify_seal(parity, "parity_subject_sha256", "parity")

    graph = graph_artifact["compiled_candidate_ir"]
    propositions = graph["proposition_graph"]["propositions"]
    by_id = {row["proposition_id"]: row for row in propositions}
    require(len(by_id) == len(propositions) == 3, "candidate count differs")
    require(set(by_id) == set(EXPECTED_EVIDENCE), "candidate identities differ")
    require(
        Counter(row["proposition_type"] for row in propositions)
        == Counter({"repeated_pattern": 3}),
        "candidate types differ",
    )
    require(
        all(row["direction"] == "opposition" for row in propositions),
        "candidate direction differs",
    )
    require(
        all(row["trajectory_change"] is None for row in propositions),
        "trajectory leaked into M12G",
    )
    require(
        all(row["overlap_relationships"] == [] for row in propositions),
        "overlap differs",
    )
    for definition in PROPOSITIONS:
        candidate = by_id[definition["proposition_id"]]
        require(
            candidate["evidence_episode_ids"] == definition["evidence_episode_ids"],
            f"{candidate['proposition_id']}: evidence differs",
        )
        for field in (
            "proposition_type",
            "proposition",
            "direction",
            "rationale",
            "material_limitations",
            "competing_interpretations",
            "overlap_relationships",
            "relevant_contrasts",
            "trajectory_change",
            "conclusion_relevance",
        ):
            require(
                candidate[field] == definition[field],
                f"{candidate['proposition_id']}: {field} differs",
            )

    episodes = {
        row["episode_id"]: row
        for row in implementation["subject"]["implementation_records"]
    }
    ledger = {
        row["episode_id"]: row for row in graph_artifact["episode_evidence_ledger"]
    }
    require(
        len(episodes) == len(ledger) == 63 and set(episodes) == set(ledger),
        "episode ledger differs",
    )
    for episode_id, episode in episodes.items():
        row = ledger[episode_id]
        require(
            row["episode_record_id"] == episode["record_id"]
            and row["episode_record_subject_sha256"] == episode["record_subject_sha256"]
            and row["member_direction"] == episode["member_direction"]
            and row["policy_proposition"] == episode["policy_proposition"]
            and row["primary_action_ids"] == episode["primary_action_ids"],
            f"{episode_id}: accepted episode lineage differs",
        )

    accounting = graph["episode_accounting"]
    accounting_by_id = {row["episode_id"]: row for row in accounting}
    require(
        len(accounting) == len(accounting_by_id) == 63
        and set(accounting_by_id) == set(episodes),
        "episode accounting differs",
    )
    counts = Counter(row["disposition"] for row in accounting)
    require(
        counts
        == Counter(
            {
                "supports_proposed_repeated_pattern": 13,
                "retained_as_limit_or_contrast": 25,
                "no_safe_higher_level_behavioral_proposition": 24,
                "unused_non_directional_evidence": 1,
            }
        ),
        "episode disposition counts differ",
    )
    non_directional_id = "single-119-hr-6387-2-136"
    require(
        episodes[non_directional_id]["member_direction"] == "non_directional_not_voting"
        and accounting_by_id[non_directional_id]["primary_proposition_id"] is None
        and accounting_by_id[non_directional_id]["disposition"]
        == "unused_non_directional_evidence"
        and all(
            non_directional_id not in row["evidence_episode_ids"]
            for row in propositions
        ),
        "H.R. 6387 non-directional accounting differs",
    )
    package_episode_ids = {
        "single-119-hr-471-1-25",
        "single-119-hr-3898-1-330",
    }
    require(
        all(
            episodes[episode_id]["grouping_type"] == "single_action"
            and len(episodes[episode_id]["actions"]) == 1
            and accounting_by_id[episode_id]["primary_proposition_id"] is None
            for episode_id in package_episode_ids
        ),
        "whole-package boundary differs",
    )
    require(not graph["synthesis_propositions"], "synthesis leaked into M12G")
    require(
        not any(graph["downstream_authorizations"].values()),
        "compiled downstream authority leakage",
    )
    require(
        not graph_artifact["accepted_semantic_ir"]
        and not graph_artifact["canonical_semantic_ir"]
        and not graph_artifact["synthesis_included"]
        and not graph_artifact["public_wording_included"]
        and not graph_artifact["authorizing"],
        "candidate authority boundary differs",
    )
    require(
        decision["decision_state"] == "empty_not_authorizing"
        and decision["reviewer"] is None
        and decision["reviewed_at_utc"] is None
        and all(
            row["decision"] is None
            and row["bounded_revision"] is None
            and row["reviewer_notes"] is None
            for row in decision["decisions"]
        ),
        "human decision template is not empty",
    )
    require(len(parity["entries"]) == 3, "parity entry count differs")
    for entry in parity["entries"]:
        output_path = GRAPH_PATH.parent / entry["path"]
        require(
            canonical_file_sha256(output_path) == entry["file_sha256"],
            f"parity file differs: {output_path.name}",
        )

    historical_graph = load(M11G_ROOT / "behavioral_semantic_ir_candidate_graph.json")
    require(
        not list(
            Draft7Validator(load(GRAPH_SCHEMA_PATH)).iter_errors(historical_graph)
        ),
        "generic schema rejects M11G",
    )
    for name, expected in EXPECTED_M11G_HASHES.items():
        require(
            canonical_file_sha256(M11G_ROOT / name) == expected,
            f"historical M11G {name} changed",
        )

    state = load(ROOT / "docs/editorial/current_state_index.json")
    m12g = state["active_m12g_behavioral_semantic_ir_candidate_milestone"]
    accepted_downstream = (
        m12g["milestone_state"] == "completed_independently_accepted_merged"
    )
    downstream = m12g["downstream_authorizations"]
    require(
        m12g["milestone_state"]
        in {
            "complete_pending_independent_substantive_review",
            "completed_independently_accepted_merged",
        }
        and m12g["accepted_episode_count"] == 63
        and m12g["proposed_repeated_pattern_count"] == 3
        and m12g["proposed_trajectory_count"] == 0
        and m12g["proposed_notable_choice_count"] == 0
        and m12g["proposition_episode_count"] == 13
        and m12g["limit_or_contrast_episode_count"] == 25
        and m12g["no_safe_higher_level_proposition_episode_count"] == 24
        and m12g["unused_non_directional_episode_count"] == 1
        and m12g["overlapping_primary_owner_count"] == 0
        and m12g["candidate_identity"]["sha256"] == canonical_file_sha256(GRAPH_PATH)
        and m12g["candidate_identity"]["candidate_subject_sha256"]
        == graph_artifact["candidate_subject_sha256"]
        and m12g["decision_template_identity"]["all_decisions_empty"] is True
        and m12g["semantic_ir_acceptance_state"]
        == (
            "canonical_internal_by_m12h"
            if accepted_downstream
            else "not_started_not_authorized"
        )
        and downstream["semantic_ir_acceptance"] is accepted_downstream
        and not any(
            value
            for key, value in downstream.items()
            if key != "semantic_ir_acceptance"
        ),
        "M12G current-state boundary differs",
    )

    deterministic = build(check=True)
    return {
        "status": "pass",
        "artifact_id": graph_artifact["artifact_id"],
        "artifact_file_sha256": canonical_file_sha256(GRAPH_PATH),
        "candidate_subject_sha256": graph_artifact["candidate_subject_sha256"],
        "decision_template_file_sha256": canonical_file_sha256(DECISION_PATH),
        "decision_template_subject_sha256": decision[
            "decision_template_subject_sha256"
        ],
        "dossier_file_sha256": canonical_file_sha256(DOSSIER_PATH),
        "parity_file_sha256": canonical_file_sha256(PARITY_PATH),
        "parity_subject_sha256": parity["parity_subject_sha256"],
        "proposition_counts": dict(
            sorted(Counter(row["proposition_type"] for row in propositions).items())
        ),
        "episode_disposition_counts": dict(sorted(counts.items())),
        "evidence_episode_count": sum(
            len(row["evidence_episode_ids"]) for row in propositions
        ),
        "candidate_evidence": EXPECTED_EVIDENCE,
        "overlap_count": 0,
        "trajectory_count": 0,
        "notable_choice_count": 0,
        "historical_m11g_byte_compatibility": "pass",
        "deterministic_candidate_subject_sha256": deterministic["graph"][
            "candidate_subject_sha256"
        ],
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
