"""Exact, user-supplied PR178 decisions; not a generic acceptance mechanism."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess

from backend.app.semantic_ir.shared_corpus import digest

BASE = "582f785074d9380f2949571627f1afdc72466b44"
REVIEWED = "5bfe5656c5024be648362de68100c02634eed5ee"
CORRECTION_REVIEWED = "9fd689b76c8ae06bc5806ad69c93a0078330b38e"
OUT = "docs/editorial/analytical_candidates/f000477_education_workforce_m14d_v1"
AUTHORITY_PATH = f"{OUT}/human_behavioral_candidate_authority.json"
FINDINGS_PATH = f"{OUT}/accepted_behavioral_findings.json"
BARGAINING = "m14d:continuity_of_collective_bargaining"
ANALYTICAL_VALUE = "Identifies a bounded cross-system relationship: Foushee supported keeping collective bargaining in force through two different kinds of disruption—restoring bargaining coverage and preserving existing federal union agreements in one system, and requiring continued bargaining and unchanged employment terms during first-contract negotiations in another—while preserving the different workers, statutes, remedies, and whole-measure limits."
SUMMARY = "Across two different labor systems, Foushee supported keeping collective bargaining in force during potential disruptions. She voted to restore bargaining coverage and preserve existing agreements for specified federal workers, and separately voted to require continued bargaining and unchanged employment terms while newly represented workers pursued a first contract."
BOUNDED_CHOICE = "Keep bargaining in force across distinct disruptions: H.R.2550 restores statutory bargaining coverage affected by EO14251 and preserves specified existing federal union agreements; H.R.5408 maintains employment terms and bargaining duties while an agreement is pending and adds first-contract bargaining, mediation and arbitration requirements. These are distinct statutory mechanisms, not identical contract protections."
ACCOUNTING_REASON = "Human review accepted the bounded bargaining relationship after preserving the different labor systems, workers, statutes, remedies and legal tools, H.R.5408's additional first-contract requirements, and the limits of whole-measure votes."
DENIED = {key: False for key in (
    "synthesis", "main_takeaway", "public_wording", "frontend_changes", "publication",
    "production_persistence", "database_writes", "deployment", "shared_issue_mapping_acceptance",
    "merge", "m14e",
)}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def reviewed_json(root: Path, name: str, revision: str = REVIEWED) -> dict:
    return json.loads(subprocess.check_output(["git", "show", f"{revision}:{name}"], cwd=root))


def validate_closure_scope(root: Path) -> None:
    allowed = {
        "scripts/build_m14d_education_reanalysis.py", "scripts/m14d_education_candidate_data.py",
        "scripts/m14d_human_decision_closure.py", "backend/tests/test_m14d_education_reanalysis.py",
        "docs/plans/m14d_education_reanalysis.md", AUTHORITY_PATH, FINDINGS_PATH,
        f"{OUT}/compiler_input.json", f"{OUT}/behavioral_candidate_graph.json", f"{OUT}/review_package.json",
    }
    changed = set(subprocess.check_output(["git", "diff", "--name-only", REVIEWED], cwd=root, text=True).splitlines())
    changed.update(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=root, text=True).splitlines())
    require(changed <= allowed, f"human closure changed protected paths: {sorted(changed - allowed)}")


def validate_revision(root: Path, payload: dict, graph: dict) -> dict:
    """Compare entire artifacts to the reviewed head plus only prescribed edits."""
    before = reviewed_json(root, f"{OUT}/behavioral_candidate_graph.json")
    expected_graph = copy.deepcopy(before)
    expected_input = reviewed_json(root, f"{OUT}/compiler_input.json")
    for rows in (expected_graph["proposition_graph"]["propositions"], expected_input["proposition_candidates"]):
        for row in rows:
            if row["proposition_id"] == BARGAINING:
                row["summary"] = SUMMARY
                row["analytical_value"] = ANALYTICAL_VALUE
    expected_input["relationship_evidence_by_proposition"][BARGAINING]["shared_bounded_choice"] = BOUNDED_CHOICE
    for artifact in (expected_graph, expected_input):
        for row in artifact["episode_accounting"]:
            if row["primary_proposition_id"] == BARGAINING:
                row["reason"] = ACCOUNTING_REASON
    require(graph == expected_graph, "candidate graph differs from exact human-approved revision")
    require(payload == expected_input, "compiler input differs from exact human-approved revision")
    for name, actual in (
        ("behavioral_candidate_graph.json", graph),
        ("compiler_input.json", payload),
    ):
        # The final correction authorizes exactly one field, not another semantic revision.
        prior = reviewed_json(root, f"{OUT}/{name}", CORRECTION_REVIEWED)
        prior_rows = prior["proposition_graph"]["propositions"] if "proposition_graph" in prior else prior["proposition_candidates"]
        for row in prior_rows:
            if row["proposition_id"] == BARGAINING:
                row["analytical_value"] = ANALYTICAL_VALUE
        require(actual == prior, f"{name} differs from analytical-value-only correction")
    return before


def expected_authority(root: Path, payload: dict, graph: dict) -> dict:
    before = validate_revision(root, payload, graph)
    old = {r["proposition_id"]: r for r in before["proposition_graph"]["propositions"]}
    subject = {
        "pr_number": 178, "baseline_main_sha": BASE, "reviewed_pre_decision_head": REVIEWED,
        "decision_source": "user_supplied_M14D_human_product_review_PR178",
        "final_candidate_graph": {"path": f"{OUT}/behavioral_candidate_graph.json",
                                  "content_sha256": digest(graph), "file_lf_sha256": hashlib.sha256(json_bytes(graph)).hexdigest()},
        "final_compiler_input_sha256": digest(payload),
        "relationship_evidence_sha256": digest(payload["relationship_evidence_by_proposition"]),
        "decisions": [{"proposition_id": r["proposition_id"],
                       "decision": "accepted_after_exact_bounded_revision" if r["proposition_id"] == BARGAINING else "accepted_as_written",
                       "reviewed_record_sha256": digest(old[r["proposition_id"]]),
                       "accepted_record_sha256": digest(r)} for r in graph["proposition_graph"]["propositions"]],
        "approved_revision": {"proposition_id": BARGAINING, "summary": SUMMARY,
                              "analytical_value": ANALYTICAL_VALUE,
                              "correction_reviewed_head": CORRECTION_REVIEWED,
                              "prior_authority_subject_sha256": reviewed_json(root, AUTHORITY_PATH, CORRECTION_REVIEWED)["authority_subject_sha256"],
                              "shared_bounded_choice": BOUNDED_CHOICE, "supporting_accounting_reason": ACCOUNTING_REASON},
        "accepted_episode_disposition_ledger": copy.deepcopy(graph["episode_accounting"]),
        "episode_disposition_ledger_sha256": digest(graph["episode_accounting"]),
        "authority_scope": "internal_analytical_findings_only",
        "downstream_authorizations": DENIED,
    }
    return {"schema_version": "m14d_human_behavioral_candidate_authority_v1",
            "artifact_id": "human-behavioral-candidate-authority:f000477:education_workforce:m14d:v1",
            "artifact_role": "immutable_user_supplied_human_decision", "immutable": True,
            "subject": subject, "authority_subject_sha256": digest(subject)}


def record_authority(root: Path, authority: dict) -> None:
    """One-time materialization; never overwrite or infer a new decision."""
    with (root / AUTHORITY_PATH).open("xb") as stream:
        stream.write(json_bytes(authority))


def validate_authority(root: Path, authority: dict, payload: dict, graph: dict) -> None:
    require(authority == expected_authority(root, payload, graph), "immutable M14D human authority differs")


def accepted_findings(authority: dict, payload: dict, graph: dict) -> dict:
    subject = {
        "human_authority": {"path": AUTHORITY_PATH, "artifact_id": authority["artifact_id"],
                            "authority_subject_sha256": authority["authority_subject_sha256"]},
        "candidate_graph_sha256": digest(graph),
        "accepted_proposition_records": copy.deepcopy(graph["proposition_graph"]["propositions"]),
        "accepted_episode_disposition_ledger": copy.deepcopy(graph["episode_accounting"]),
        "relationship_evidence_by_proposition": copy.deepcopy(payload["relationship_evidence_by_proposition"]),
        "record_provenance_note": "Exact candidate records retain their original non-authorizing flags and pre-decision rationale. Acceptance is conferred only by the separately bound human authority, not by compiler output or those provenance fields.",
        "synthesis_propositions": [], "downstream_authorizations": DENIED,
    }
    return {"schema_version": "m14d_accepted_behavioral_findings_v1",
            "artifact_id": "accepted-behavioral-findings:f000477:education_workforce:m14d:v1",
            "artifact_role": "human_accepted_internal_behavioral_findings",
            "internal_analytical_authority": True, "public": False, "production_selectable": False,
            "subject": subject, "findings_subject_sha256": digest(subject)}
