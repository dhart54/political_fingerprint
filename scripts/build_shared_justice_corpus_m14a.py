"""Build the parity-only M14A Justice shared-corpus pilot."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.pipeline import run_editorial_pipeline  # noqa: E402
from backend.app.semantic_ir.shared_corpus import (  # noqa: E402
    adapt_to_semantic_ir_input,
    choice_effect,
    digest,
    validate_member_projection,
    validate_shared_action_core,
    validate_shared_issue_mapping,
)


START_SHA = "d6ebf1e338aed358e4be29e55d686e1cca7c8026"
M0_PROOF = ROOT / "docs/architecture/m0_two_member_reuse_proof_v1.json"
LEGACY_INPUT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_justice_public_safety_119_v2/frozen_final_compiler_input.json"
)
LEGACY_OUTPUT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_justice_public_safety_119_v2/frozen_final_compiled_semantic_ir.json"
)
OUTPUT = ROOT / "docs/editorial/shared_corpora/justice_public_safety_119_v1"
CORE_PATH = OUTPUT / "shared_action_core.json"
MAPPING_PATH = OUTPUT / "shared_issue_mapping.json"
FOUSHEE_PATH = OUTPUT / "member_projections/f000477.json"
GROTHMAN_PATH = OUTPUT / "member_projections/g000576.json"
PROOF_PATH = OUTPUT / "m14a_parity_proof.json"
REPORT_PATH = OUTPUT / "implementation_report.md"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sealed(record: dict[str, Any], field: str) -> dict[str, Any]:
    value = copy.deepcopy(record)
    value[field] = digest({key: item for key, item in value.items() if key != field})
    return value


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str, binary: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return (
        result.stdout
        if binary
        else result.stdout.decode("utf-8", errors="replace").strip()
    )


def protected_parity() -> dict[str, Any]:
    tree_rows = str(git("ls-tree", "-r", START_SHA, "docs/editorial")).splitlines()
    tree = {row.split("\t", 1)[1]: row.split()[2] for row in tree_rows}
    names = list(tree)
    tokens = (
        "f000477_justice_public_safety",
        "f000477_education_workforce",
        "f000477_national_security_foreign",
        "f000477_environment_energy",
    )
    paths = sorted(
        path
        for path in names
        if any(token in path.lower() for token in tokens)
        and not path.startswith("docs/editorial/shared_corpora/")
    )
    changed = str(
        git("diff", "--name-only", START_SHA, "--", "docs/editorial")
    ).splitlines()
    mismatches = sorted(path for path in changed if path in set(paths))
    identities = {path: tree[path] for path in paths}
    return {
        "start_sha": START_SHA,
        "protected_file_count": len(paths),
        "protected_tree_sha256": digest(identities),
        "mismatched_paths": mismatches,
        "byte_identical": not mismatches,
    }


def official_clerk_status(action_id: str, member_id: str) -> str:
    _, congress, session, roll = action_id.split(":")
    path = (
        ROOT
        / f"docs/editorial/full_record_reviews/source_readiness/evidence/roll{congress}_{session}_{int(roll):03d}.xml"
    )
    xml = ET.parse(path).getroot()
    for recorded in xml.findall("./vote-data/recorded-vote"):
        legislator = recorded.find("legislator")
        vote = recorded.find("vote")
        if (
            legislator is not None
            and vote is not None
            and legislator.attrib.get("name-id") == member_id
        ):
            value = (vote.text or "").strip().lower()
            return {
                "yea": "Yea",
                "aye": "Yea",
                "nay": "Nay",
                "no": "Nay",
                "present": "Present",
                "not voting": "Not Voting",
            }.get(value, "Missing Evidence")
    return "Missing Evidence"


def build() -> tuple[
    dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any], str
]:
    m0 = load(M0_PROOF)
    legacy_input = load(LEGACY_INPUT)["compiler_input"]
    legacy_output = load(LEGACY_OUTPUT)["compiled_ir"]
    legacy_actions = {
        row["action_id"]: row for row in legacy_input["shared_semantics"]["actions"]
    }
    actions = []
    action_mappings = []
    members = {"F000477": [], "G000576": []}
    member_meta = {"F000477": m0["member_a"], "G000576": m0["member_b"]}
    m0_rows = {row["action_id"]: row for row in m0["complete_action_index"]}
    for legacy_action in legacy_input["shared_semantics"]["actions"]:
        row = m0_rows[legacy_action["action_id"]]
        action_id = row["action_id"]
        projected = row["shared_projection"]
        source = projected["shared_action_core"]
        governed_sources = []
        for item in projected["governed_source_identity_set"]:
            governed_bytes_sha256 = item["raw_sha256"]
            if governed_bytes_sha256 is None:
                governed_bytes_sha256 = row["current_artifact_digests"]["clerk_roll"]
            governed_sources.append(
                {**item, "governed_bytes_sha256": governed_bytes_sha256}
            )
        outcome_sources = [
            item
            for item in governed_sources
            if item["source_type"] == "house_clerk_roll_call"
        ]
        operative_sources = [
            item
            for item in governed_sources
            if item["source_type"] != "house_clerk_roll_call"
        ]
        core = {
            "action_id": action_id,
            "exact_action_identity": source["exact_action_identity"],
            "chamber": source["chamber"],
            "congress": source["congress"],
            "session": source["session"],
            "roll": source["roll"],
            "legislative_stage": source["legislative_stage"],
            "action_date": source["action_date"],
            "chamber_outcome": source["chamber_outcome"],
            "enactment_status": source["enactment_status"],
            "mechanism": source["mechanism_class"],
            "mechanism_availability": source["mechanism_availability"],
            "accepted_exact_action_meaning": source["accepted_exact_action_meaning"],
            "accepted_shared_limitations": source["accepted_shared_limitations"],
            "action_meaning_ref": source["action_meaning_ref"],
            "governed_source_identities": governed_sources,
            "governed_source_identity_sha256": digest(governed_sources),
            "action_outcome_source_identities": outcome_sources,
            "operative_meaning_source_identities": operative_sources,
            "semantic_ir_source_ids": legacy_actions[action_id]["source_ids"],
            "package_component_boundary": source["package_component_boundary"],
            "source_contract_version": source["source_contract_version"],
            "meaning_contract_version": source["meaning_contract_version"],
            "action_core_sha256": "",
        }
        actions.append(sealed(core, "action_core_sha256"))
        eligibility = projected["shared_issue_mapping"]["domain_eligibility"]
        mapping = {
            "action_id": action_id,
            "eligibility": {
                "decision": eligibility["decision"],
                "parent_context_used": eligibility["parent_context_used"],
            },
            "episode_id": legacy_actions[action_id]["episode_id"],
            "policy_family_refs": projected["shared_issue_mapping"][
                "policy_family_refs"
            ],
            "policy_trait_refs": legacy_actions[action_id].get("policy_trait_refs", []),
            "structural_metadata": legacy_actions[action_id]["structural_metadata"],
            "mapping_sha256": "",
        }
        action_mappings.append(sealed(mapping, "mapping_sha256"))
        for member_id, key in (("F000477", "member_a"), ("G000576", "member_b")):
            overlay = row[key]
            members[member_id].append(
                {
                    "action_id": action_id,
                    "action_core_sha256": actions[-1]["action_core_sha256"],
                    "shared_issue_mapping_sha256": action_mappings[-1][
                        "mapping_sha256"
                    ],
                    "official_status": overlay["official_status"],
                    "service_status": overlay["service_status"],
                    "evidence_status": overlay["evidence_status"],
                    "exact_choice_effect": choice_effect(overlay["official_status"]),
                    "member_action_source_identities": outcome_sources,
                    "member_action_source_identity_sha256": digest(outcome_sources),
                }
            )
    core_artifact = {
        "schema_version": "shared_action_core_v1",
        "artifact_id": "shared-action-core:justice-public-safety:119:v1",
        "identity_unit": "exact House legislative action and governed source version",
        "authoritative_for_new_editorial_work": True,
        "historical_inputs_rewritten": False,
        "actions": actions,
        "corpus_sha256": digest(actions),
    }
    shared = legacy_input["shared_semantics"]
    mapping_artifact = {
        "schema_version": "shared_issue_mapping_v1",
        "artifact_id": "shared-issue-mapping:justice-public-safety:119:v1",
        "domain_id": "JUSTICE_PUBLIC_SAFETY",
        "scope_boundaries": [
            "House 119th Congress exact actions in the accepted Justice pilot",
            "issue membership does not imply member coverage or direction",
        ],
        "authoritative_for_new_editorial_work": True,
        "historical_inputs_rewritten": False,
        "semantic_ir_case_scope": legacy_input["case_scope"],
        "action_mappings": action_mappings,
        "episodes": shared["episodes"],
        "policy_families": shared["policy_families"],
        "policy_traits": shared["policy_traits"],
        "trait_relationships": shared["trait_relationships"],
        "shared_review_dependencies": shared["shared_review_dependencies"],
        "source_render_constraints": shared["source_render_constraints"],
        "mapping_sha256": "",
    }
    mapping_artifact = sealed(mapping_artifact, "mapping_sha256")
    projections = []
    for member_id in ("F000477", "G000576"):
        meta = member_meta[member_id]
        projection = {
            "schema_version": "member_action_projection_v1",
            "artifact_id": f"member-action-projection:{member_id.lower()}:justice-public-safety:119:v1",
            "member_id": member_id,
            "party": meta["party"],
            "context_metadata": {
                key: meta[key] for key in ("name", "state") if key in meta
            },
            "authoritative_legislative_meaning": False,
            "actions": members[member_id],
            "projection_sha256": "",
        }
        projections.append(sealed(projection, "projection_sha256"))
    validate_shared_action_core(ROOT, core_artifact)
    validate_shared_issue_mapping(ROOT, mapping_artifact, core_artifact)
    for projection in projections:
        validate_member_projection(ROOT, projection, core_artifact, mapping_artifact)
    foushee_input = adapt_to_semantic_ir_input(
        ROOT, core_artifact, mapping_artifact, [projections[0]]
    )
    two_input = adapt_to_semantic_ir_input(
        ROOT, core_artifact, mapping_artifact, projections
    )
    foushee_result = run_editorial_pipeline(
        copy.deepcopy(foushee_input),
        prepare_persistence_proposal=False,
        public_presentation_authoring=None,
    ).compiled_ir
    two_result = run_editorial_pipeline(
        copy.deepcopy(two_input),
        prepare_persistence_proposal=False,
        public_presentation_authoring=None,
    ).compiled_ir
    compiled = {row["member_id"]: row for row in two_result["members"]}
    historical = protected_parity()
    clerk_reconciliation = {
        projection["member_id"]: all(
            row["official_status"]
            == official_clerk_status(row["action_id"], projection["member_id"])
            for row in projection["actions"]
        )
        for projection in projections
    }
    m0_action_ids = {row["action_id"] for row in m0["complete_action_index"]}
    proof = {
        "schema_version": "m14a_shared_corpus_parity_proof_v1",
        "starting_main_sha": START_SHA,
        "action_set_parity": {row["action_id"] for row in actions} == m0_action_ids,
        "action_count": len(actions),
        "unchanged_meaning_count": sum(
            action["accepted_exact_action_meaning"]
            == m0_rows[action["action_id"]]["accepted_meaning_unchanged"]
            for action in actions
        ),
        "changed_meaning_count": sum(
            action["accepted_exact_action_meaning"]
            != m0_rows[action["action_id"]]["accepted_meaning_unchanged"]
            for action in actions
        ),
        "source_binding_parity": all(
            [
                {
                    k: source[k]
                    for k in ("source_id", "source_type", "text_version", "raw_sha256")
                }
                for source in action["governed_source_identities"]
            ]
            == m0_rows[action["action_id"]]["shared_projection"][
                "governed_source_identity_set"
            ]
            for action in actions
        ),
        "issue_mapping_parity": foushee_input["shared_semantics"]["actions"]
        == legacy_input["shared_semantics"]["actions"],
        "episode_family_trait_parity": all(
            foushee_input["shared_semantics"][key]
            == legacy_input["shared_semantics"][key]
            for key in (
                "episodes",
                "policy_families",
                "policy_traits",
                "trait_relationships",
            )
        ),
        "foushee_compiler_input_parity": foushee_input == legacy_input,
        "foushee_compiled_output_parity": foushee_result == legacy_output,
        "member_overlap_count": len(
            set(row["action_id"] for row in projections[0]["actions"])
            & set(row["action_id"] for row in projections[1]["actions"])
        ),
        "shared_digest_parity_count": sum(
            a["action_core_sha256"] == b["action_core_sha256"]
            for a, b in zip(
                projections[0]["actions"], projections[1]["actions"], strict=True
            )
        ),
        "member_b_regenerated_meaning_count": 0,
        "member_projections_reconcile_to_official_clerk": clerk_reconciliation,
        "relationship_parity_counts": {
            "episode_action": sum(
                len(row["action_ids"]) for row in mapping_artifact["episodes"]
            ),
            "policy_family_episode": sum(
                len(row["episode_ids"]) for row in mapping_artifact["policy_families"]
            ),
            "policy_trait_action": sum(
                len(row.get("policy_trait_refs", []))
                for row in foushee_input["shared_semantics"]["actions"]
            ),
            "trait_relationship": len(mapping_artifact["trait_relationships"]),
        },
        "proposition_counts": {
            member_id: len(row["proposition_graph"]["propositions"])
            for member_id, row in compiled.items()
        },
        "synthesis_counts": {
            member_id: sum(
                p["semantic_role"] == "synthesis"
                for p in row["proposition_graph"]["propositions"]
            )
            for member_id, row in compiled.items()
        },
        "compiled_member_sha256": {
            member_id: digest(row) for member_id, row in compiled.items()
        },
        "member_input_action_difference_count": sum(
            a["official_status"] != b["official_status"]
            for a, b in zip(
                projections[0]["actions"], projections[1]["actions"], strict=True
            )
        ),
        "historical_artifact_byte_parity": historical,
        "production_write": False,
        "publication_change": False,
        "frontend_change": False,
        "proof_subject_sha256": "",
    }
    required = [
        proof["action_count"] == 37,
        proof["action_set_parity"],
        proof["changed_meaning_count"] == 0,
        proof["source_binding_parity"],
        proof["issue_mapping_parity"],
        proof["episode_family_trait_parity"],
        proof["foushee_compiler_input_parity"],
        proof["foushee_compiled_output_parity"],
        proof["member_overlap_count"] == 37,
        proof["shared_digest_parity_count"] == 37,
        all(clerk_reconciliation.values()),
        historical["byte_identical"],
    ]
    if not all(required):
        raise AssertionError(f"M14A parity failure: {proof}")
    proof["proof_subject_sha256"] = digest(
        {key: value for key, value in proof.items() if key != "proof_subject_sha256"}
    )
    report = "\n".join(
        [
            "# M14A Shared Corpus Boundary Refactor — Implementation Report",
            "",
            "Status: `IMPLEMENTED`",
            "",
            f"- Starting main: `{START_SHA}`",
            f"- Actions: `{proof['action_count']}`",
            f"- Unchanged/changed meanings: `{proof['unchanged_meaning_count']}` / `{proof['changed_meaning_count']}`",
            f"- Source, issue-mapping, and episode/family/trait parity: `{proof['source_binding_parity']}` / `{proof['issue_mapping_parity']}` / `{proof['episode_family_trait_parity']}`",
            f"- Foushee compiler input/output parity: `{proof['foushee_compiler_input_parity']}` / `{proof['foushee_compiled_output_parity']}`",
            f"- Foushee/Grothman overlap and shared digest parity: `{proof['member_overlap_count']}` / `{proof['shared_digest_parity_count']}`",
            f"- Official Clerk reconciliation: `{json.dumps(proof['member_projections_reconcile_to_official_clerk'], sort_keys=True)}`",
            f"- Episode/family/trait relationship counts: `{json.dumps(proof['relationship_parity_counts'], sort_keys=True)}`",
            f"- Member B regenerated meanings: `{proof['member_b_regenerated_meaning_count']}`",
            f"- Proposition counts: `{json.dumps(proof['proposition_counts'], sort_keys=True)}`",
            f"- Synthesis counts: `{json.dumps(proof['synthesis_counts'], sort_keys=True)}`",
            f"- Historical protected files byte-identical: `{historical['byte_identical']}` across `{historical['protected_file_count']}` files",
            f"- Proof digest: `{proof['proof_subject_sha256']}`",
            "",
            "No Education remediation, interpretability implementation, production write, publication, frontend change, deployment, or historical accepted-artifact rewrite occurred.",
            "",
        ]
    )
    return core_artifact, mapping_artifact, projections, proof, report


def write(path: Path, data: bytes, check: bool) -> None:
    checkout_bytes = path.read_bytes() if path.exists() else None
    if checkout_bytes is not None and checkout_bytes.replace(
        b"\r\n", b"\n"
    ) == data.replace(b"\r\n", b"\n"):
        return
    if check:
        raise AssertionError(
            f"generated artifact differs: {path.relative_to(ROOT).as_posix()}"
        )
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    core, mapping, projections, proof, report = build()
    for path, value in (
        (CORE_PATH, core),
        (MAPPING_PATH, mapping),
        (FOUSHEE_PATH, projections[0]),
        (GROTHMAN_PATH, projections[1]),
        (PROOF_PATH, proof),
    ):
        write(
            path,
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode(
                "utf-8"
            )
            + b"\n",
            args.check,
        )
    write(REPORT_PATH, report.encode("utf-8"), args.check)
    print(
        json.dumps(
            {
                "status": "ok",
                "check": args.check,
                "action_count": proof["action_count"],
                "proof_subject_sha256": proof["proof_subject_sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
