"""Promote accepted action records and compile detached M14D review candidates.

Offline deterministic builder. No source fetch, mapping acceptance, public output,
database operation, or automatic notable-choice generation is available here.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.shared_corpus import (  # noqa: E402
    canonical_bytes, choice_effect, digest, sealed_digest,
    validate_member_projection, validate_shared_action_core,
)
from backend.app.semantic_ir.compiler import (  # noqa: E402
    INSUFFICIENT_PATTERN_BASES, compile_behavioral_candidate_ir,
)
from backend.app.semantic_ir.m14c_source_hold_closure import validate_closure  # noqa: E402
from scripts.m14d_education_candidate_data import NOTABLE, PATTERNS, REMAINDER, SEARCH_REVIEW  # noqa: E402
from scripts import m14d_human_decision_closure as closure  # noqa: E402

BASE = "582f785074d9380f2949571627f1afdc72466b44"
V1 = "docs/editorial/shared_corpora/house_119_v1"
V2 = "docs/editorial/shared_corpora/house_119_v2"
ACCEPTED = "docs/editorial/interpretability_candidates/house_119_v1/education_workforce_m14c_v1"
EPISODES = "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_education_workforce_119_v1"
OUT = "docs/editorial/analytical_candidates/f000477_education_workforce_m14d_v1"
OVERLAP = "house:119:1:68"
V1_DIGEST = "8267cd0cee5771045847387ae870f34c446c4c29d1781417d0e504252c79237e"
ALLOWED_FILES = {
    ".github/workflows/backend-tests.yml",
    "scripts/build_m14d_education_reanalysis.py",
    "scripts/m14d_education_candidate_data.py",
    "scripts/m14d_human_decision_closure.py",
    "backend/tests/test_m14d_education_reanalysis.py",
    "docs/plans/m14d_education_reanalysis.md",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def file_binding(path: str) -> dict:
    # JSON source bindings use canonical content to be stable across Git EOLs.
    return {"path": path, "content_sha256": digest(load(path))}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8").strip()


def validate_scope() -> None:
    changed = set(git("diff", "--name-only", BASE).splitlines())
    changed.update(git("ls-files", "--others", "--exclude-standard").splitlines())
    forbidden = sorted(p for p in changed if p not in ALLOWED_FILES
                       and not p.startswith((V2 + "/", OUT + "/")))
    require(not forbidden, f"M14D scope violation: {forbidden}")
    # Compare V1 blobs using Git's clean conversion, byte for byte. No rewrite.
    require(not git("diff", BASE, "--", V1), "frozen House V1 corpus changed")


def seal(record: dict, field: str) -> dict:
    record[field] = sealed_digest(record, field)
    return record


def acceptance_index(candidates: list[dict], authorities: list[dict]) -> dict:
    index = {}
    for authority in authorities:
        require(authority["authority_subject_sha256"] == digest(authority["subject"]), "authority seal differs")
        require(authority["subject"]["authorizations"]["later_canonical_semantic_promotion_of_exact_accepted_records"] is True,
                "authority does not permit later semantic promotion")
        for record in authority["subject"]["accepted_records"]:
            require(record["action_id"] not in index, "duplicate human decision")
            require(record["decision"] == "accept_as_written", "semantic promotion lacks human acceptance")
            index[record["action_id"]] = {**record, "authority_artifact_id": authority["artifact_id"],
                                         "authority_subject_sha256": authority["authority_subject_sha256"]}
    require(set(index) == {c["action_id"] for c in candidates}, "acceptance does not cover exactly the candidate set")
    for c in candidates:
        decision = index[c["action_id"]]
        require(decision["candidate_id"] == c["candidate_id"] and decision["candidate_record_sha256"] == digest(c),
                f"accepted candidate changed: {c['action_id']}")
    return index


def governed_identity(source: dict) -> dict:
    source_id = source["source_id"]
    if source["source_type"] == "house_clerk_roll_call":
        source_id = source_id.replace("clerk:house:", "clerk:")
    return {"source_id": source_id, "source_type": source["source_type"],
            "text_version": source["neutral_projection"].get("text_version"),
            "raw_sha256": source["raw_provenance"]["sha256"],
            "governed_bytes_sha256": source["raw_provenance"]["sha256"]}


def official_status(path: Path, member_id: str = "F000477") -> str:
    votes = [r.findtext("vote", "").strip().lower()
             for r in ET.parse(path).getroot().findall("./vote-data/recorded-vote")
             if r.find("legislator") is not None and r.find("legislator").get("name-id") == member_id]
    require(len(votes) == 1, f"official record must contain member exactly once: {path.name}")
    statuses = {"yea": "Yea", "aye": "Yea", "nay": "Nay", "no": "Nay", "present": "Present", "not voting": "Not Voting"}
    require(votes[0] in statuses, "unrepresentable official status")
    return statuses[votes[0]]


def project_action(c: dict, readiness: dict) -> tuple[dict, list[dict], str]:
    sources = {s["source_id"]: s for s in readiness["sources"]}
    operative_ids = readiness["source_roles"]["operative_content_interpretation_input"]
    clerk_ids = readiness["source_roles"]["member_action_evidence"]
    require(len(clerk_ids) == 1, "expected one governed Clerk source")
    require({m["source_id"] for m in c["claim_source_mappings"]} <= set(operative_ids),
            "accepted semantic claims lack operative source roles")
    bound = []
    for original in c["governed_sources"]:
        s = sources[original["source_id"]]
        raw = (ROOT / s["raw_provenance"]["governed_local_path"]).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == original["raw_sha256"], "governed source bytes differ")
        require(digest(s["neutral_projection"]) == original["neutral_projection_sha256"], "source projection differs")
        role = "operative_meaning" if s["source_id"] in operative_ids else (
            "action_outcome_and_member_status" if s["source_id"] in clerk_ids else "retained_identity_stage_context")
        bound.append({"accepted_source_identity": original,
                      "core_source_identity": governed_identity(s) if role != "retained_identity_stage_context" else None,
                      "role": role, "raw_path": s["raw_provenance"]["governed_local_path"], "url": s["source_url"]})
    outcome = [governed_identity(sources[s]) for s in clerk_ids]
    operative = [governed_identity(sources[s]) for s in operative_ids]
    governed = outcome + operative
    _, congress, session, roll = c["action_id"].split(":")
    boundary = c["exact_action_boundary"]
    core = {
        "action_id": c["action_id"], "exact_action_identity": c["exact_action_identity"],
        "chamber": "house", "congress": int(congress), "session": int(session), "roll": int(roll),
        "legislative_stage": c["legislative_stage"], "action_date": c["action_date"],
        "chamber_outcome": boundary["house_action_outcome"],
        "enactment_status": "not_inferred_from_house_outcome",
        "mechanism": c["mechanism"]["description"], "mechanism_availability": "supported_by_accepted_action_interpretability",
        "accepted_exact_action_meaning": c["plain_language_meaning"],
        "accepted_shared_limitations": copy.deepcopy(c["limitations"]), "action_meaning_ref": c["candidate_id"],
        "governed_source_identities": governed, "governed_source_identity_sha256": digest(governed),
        "action_outcome_source_identities": outcome, "operative_meaning_source_identities": operative,
        "semantic_ir_source_ids": [s["source_id"] for s in governed],
        "package_component_boundary": {"boundary_type": boundary["boundary_type"],
                                       "parent_package_meaning_projected": False,
                                       "basis": c["policy_choice"]},
        "source_contract_version": "action_interpretability_v1",
        "meaning_contract_version": "action_interpretability_v1",
    }
    clerk = sources[clerk_ids[0]]
    status = official_status(ROOT / clerk["raw_provenance"]["governed_local_path"])
    return seal(core, "action_core_sha256"), bound, status


def promote(candidates: list[dict], overlay: dict, authorities: list[dict]) -> tuple[dict, dict, dict]:
    decisions = acceptance_index(candidates, authorities)
    old = load(f"{V1}/shared_action_core.json")
    require(old["corpus_sha256"] == V1_DIGEST, "inherited V1 digest changed")
    validate_shared_action_core(ROOT, old)
    inherited = {a["action_id"]: a for a in old["actions"]}
    rows = copy.deepcopy(inherited)
    member = load(f"{V1}/member_projections/f000477.json")
    member_rows = {a["action_id"]: copy.deepcopy(a) for a in member["actions"]}
    readiness = {r["action_id"]: r for r in overlay["subject"]["action_readiness"]}
    promoted = []
    for c in candidates:
        action, sources, status = project_action(c, readiness[c["action_id"]])
        aid = c["action_id"]
        rows[aid] = action
        evidence = action["action_outcome_source_identities"]
        if aid in member_rows:
            require(status == member_rows[aid]["official_status"], "overlap member status changed")
            require(evidence == member_rows[aid]["member_action_source_identities"], "overlap Clerk binding changed")
            member_rows[aid]["action_core_sha256"] = action["action_core_sha256"]
        else:
            member_rows[aid] = {"action_id": aid, "action_core_sha256": action["action_core_sha256"],
                                "official_status": status, "service_status": "in_service",
                                "evidence_status": "official_record_resolved", "exact_choice_effect": choice_effect(status),
                                "member_action_source_identities": evidence, "member_action_source_identity_sha256": digest(evidence)}
        promoted.append({**decisions[aid], "v2_action_core_sha256": action["action_core_sha256"],
                         "promotion_kind": "approved_overlap_revision" if aid in inherited else "new_shared_identity",
                         "v1_action_core_sha256": inherited[aid]["action_core_sha256"] if aid in inherited else None,
                         "governed_sources": sources})
    # Preserve inherited order and full records; append only genuinely new identities.
    core = {**old, "artifact_id": "shared-action-core:house:119:v2", "actions": list(rows.values())}
    core["corpus_sha256"] = digest(core["actions"])
    member.update(artifact_id="member-action-projection:f000477:house:119:v2", actions=list(member_rows.values()))
    seal(member, "projection_sha256")
    validate_shared_action_core(ROOT, core)
    validate_member_projection(ROOT, member, core)
    require(len(rows) == 53 and len(rows.keys() - inherited.keys()) == 16, "V2 action membership differs")
    require(set(inherited) & {c["action_id"] for c in candidates} == {OVERLAP}, "unexpected overlap")
    unchanged = [aid for aid in inherited if canonical_bytes(rows[aid]) == canonical_bytes(inherited[aid])]
    require(len(unchanged) == 36, "inherited semantic record changed")
    manifest = {
        "schema_version": "m14d_semantic_promotion_manifest_v1", "baseline_main_sha": BASE,
        "new_human_decision": False, "normalization_only": True,
        "projection_rule": "Exact plain_language_meaning; mechanism.description; all limitations; exact boundary and candidate identity. Rich candidate remains immutable authority.",
        "v1_inherited_corpus": {**file_binding(f"{V1}/shared_action_core.json"), "corpus_sha256": V1_DIGEST,
                                "git_tree": git("rev-parse", f"{BASE}:{V1}"),
                                "acceptance_provenance": file_binding(f"{V1}/issue_mappings/justice_public_safety_v1/m14a_parity_proof.json")},
        "acceptance_authorities": [file_binding(f"{ACCEPTED}/{name}") | {"authority_artifact_id": a["artifact_id"], "authority_subject_sha256": a["authority_subject_sha256"]}
                                  for name, a in zip(("human_acceptance_authority.json", "human_acceptance_authority_enriched3.json"), authorities, strict=True)],
        "accepted_candidates": file_binding(f"{ACCEPTED}/action_interpretability_candidates.json"),
        "unchanged_inherited_records": [{"action_id": aid, "v1_and_v2_action_core_sha256": rows[aid]["action_core_sha256"],
                                        "inherited_accepted_meaning_ref": rows[aid]["action_meaning_ref"]} for aid in unchanged],
        "semantic_promotions": promoted,
        "new_action_ids": sorted(rows.keys() - inherited.keys()), "overlap_action_ids": [OVERLAP],
        "v2_core_count": len(rows), "v2_core_sha256": core["corpus_sha256"],
        "member_projection_count": len(member_rows), "member_projection_sha256": member["projection_sha256"],
        "downstream_acceptance_or_publication_authority": False,
    }
    return core, member, seal(manifest, "manifest_sha256")


def candidate_episodes(candidates: list[dict], member: dict, bundle: dict) -> list[dict]:
    """Read only the allowlisted M13F structure/direction fields, never its prose."""
    c_by_id = {c["action_id"]: c for c in candidates}
    members = {m["action_id"]: m for m in member["actions"]}
    result = []
    for old in bundle["subject"]["implementation_records"]:
        actions = []
        for structural in old["actions"]:
            aid = structural["action_id"]
            c, m = c_by_id[aid], members[aid]
            inherited_effect = structural["accepted_exact_choice_position_effect"]
            if inherited_effect == "non_directional_not_voting":
                require(m["official_status"] == "Not Voting", "Not Voting lineage changed")
                inherited_effect = "resolved_non_directional"
            elif inherited_effect == "non_directional_present":
                require(m["official_status"] == "Present", "Present lineage changed")
                inherited_effect = "resolved_non_directional"
            require(m["exact_choice_effect"] == inherited_effect, "M13F direction lineage differs from Clerk")
            require(c["action_date"] == structural["official_action_date"] and c["exact_action_identity"] == structural["exact_action_identity"], "M13F exact action lineage differs")
            actions.append({"action_id": aid, "action_role": structural["action_role"],
                            "official_action_date": c["action_date"], "exact_action_identity": c["exact_action_identity"],
                            "official_status": m["official_status"], "exact_choice_effect": m["exact_choice_effect"],
                            "action_meaning_ref": c["candidate_id"], "accepted_candidate_record_sha256": digest(c),
                            "action_core_sha256": m["action_core_sha256"]})
        effects = {a["exact_choice_effect"] for a in actions}
        direction = ({"supports_exact_choice": "supports_policy_proposition", "opposes_exact_choice": "opposes_policy_proposition"}.get(next(iter(effects)))
                     if len(effects) == 1 else "mixed_on_episode_choices")
        if direction is None:
            require(len(actions) == 1 and actions[0]["official_status"] in {"Present", "Not Voting"}, "unsupported non-directional episode")
            direction = "non_directional_not_voting" if actions[0]["official_status"] == "Not Voting" else "non_directional_present"
        require(direction == old["member_direction"], "accepted episode direction differs")
        require(set(old["primary_action_ids"]) == {a["action_id"] for a in actions}, "episode membership differs")
        result.append(seal({"episode_id": old["episode_id"], "primary_action_ids": old["primary_action_ids"],
                            "actions": actions, "member_direction": direction,
                            "canonical_internal_policy_episode": True,
                            "canonical_flag_scope": "M13F membership only; no new episode prose or behavioral acceptance",
                            "m13f_structure_record_id": old["record_id"],
                            "m13f_structure_record_sha256": old["record_subject_sha256"]}, "record_subject_sha256"))
    accounted = [aid for e in result for aid in e["primary_action_ids"]]
    require(len(result) == 16 and len(accounted) == 17 and set(accounted) == set(c_by_id), "Education episode accounting differs")
    return result


def analytical_input(candidates: list[dict], episodes: list[dict]) -> dict:
    c_by_id = {c["action_id"]: c for c in candidates}
    e_by_action = {aid: e["episode_id"] for e in episodes for aid in e["primary_action_ids"]}
    proposals, relationships, owners = [], {}, {}
    for draft in [*PATTERNS, NOTABLE]:
        pid = "m14d:" + draft["key"]
        eids = list(dict.fromkeys(e_by_action[aid] for aid in draft["actions"]))
        pattern = draft is not NOTABLE
        semantic = {eid: "\n".join(c_by_id[aid]["plain_language_meaning"] for e in episodes if e["episode_id"] == eid for aid in e["primary_action_ids"]) for eid in eids}
        proposals.append({"proposition_id": pid, "proposition_type": "repeated_pattern" if pattern else "notable_choice",
                          "summary": draft["summary"], "direction": "mixed" if not pattern else (
                              "support" if draft["key"] == "continuity_of_collective_bargaining" else "opposition"),
                          "evidence_episode_ids": eids, "episode_semantic_evidence": semantic,
                          "material_limitations": draft["differences"], "analytical_value": draft["value"]})
        for eid in eids:
            require(eid not in owners, "unreviewed overlapping ownership")
            owners[eid] = (pid, "supports_proposed_repeated_pattern" if pattern else "supports_proposed_notable_choice")
        if pattern:
            relationships[pid] = {"shared_bounded_choice": draft["bounded_choice"],
                                  "episode_support": dict(zip(eids, draft["support"], strict=True)),
                                  "insufficient_bases_rejected": sorted(INSUFFICIENT_PATTERN_BASES),
                                  "material_differences_preserved": draft["differences"]}
    accounting = []
    for e in episodes:
        eid = e["episode_id"]
        if eid in owners:
            owner, disposition = owners[eid]
            reason = next(p["analytical_value"] for p in proposals if p["proposition_id"] == owner)
            if owner == closure.BARGAINING:
                reason = closure.ACCOUNTING_REASON
        else:
            require(len(e["primary_action_ids"]) == 1, "missing explicit multi-action disposition")
            owner = None
            disposition, reason = REMAINDER[e["primary_action_ids"][0]]
        accounting.append({"episode_id": eid, "action_ids": e["primary_action_ids"],
                           "primary_proposition_id": owner, "disposition": disposition, "reason": reason,
                           "interpretability_state": "human_approved_action_meanings"})
    return {"subject": {"member_id": "F000477", "domain_id": "EDUCATION_WORKFORCE", "congress": 119,
                        "artifact_role": "detached_non_authorizing_m14d_behavioral_review"},
            "episodes": episodes, "proposition_candidates": proposals, "episode_accounting": accounting,
            "blocked_action_ids": [], "relationship_evidence_by_proposition": relationships}


def validate_analytical(payload: dict, graph: dict) -> None:
    require(graph == compile_behavioral_candidate_ir(payload), "candidate graph differs from explicit compiler input")
    require(graph["synthesis_propositions"] == [] and not any(graph["downstream_authorizations"].values()), "candidate authority or synthesis escaped")
    for p in graph["proposition_graph"]["propositions"]:
        require(p["candidate_state"] == "proposed_not_accepted" and p["authorizing"] is False and p["canonical"] is False, "candidate accepted automatically")
        if p["proposition_type"] == "repeated_pattern":
            require(p["direction"] in {"support", "opposition"}, "repeated pattern requires consistent direction")
    categories = {"supports_proposed_repeated_pattern", "supports_proposed_trajectory", "supports_proposed_notable_choice",
                  "retained_as_useful_contrast", "non_directional_receipt", "receipt_only_no_elevation"}
    for row in graph["episode_accounting"]:
        require(row["disposition"] in categories and bool(row["reason"]), "missing explicit episode disposition")
        require(row["disposition"].startswith("supports_proposed_") == (row["primary_proposition_id"] is not None), "disposition and ownership differ")
    require(len(graph["episode_accounting"]) == 16, "incomplete episode accounting")


def build_outputs(*, record_human_decisions: bool = False) -> dict[str, bytes]:
    accepted = load(f"{ACCEPTED}/action_interpretability_candidates.json")
    authorities = [load(f"{ACCEPTED}/{name}") for name in ("human_acceptance_authority.json", "human_acceptance_authority_enriched3.json")]
    overlay = load(f"{ACCEPTED}/source_overlay.json")
    validate_closure(ROOT, accepted, authorities[0], load(f"{ACCEPTED}/source_catalog.json"), overlay)
    candidates = accepted["candidates"]
    core, member, manifest = promote(candidates, overlay, authorities)
    bundle = load(f"{EPISODES}/episode_decision_implementation_bundle.json")
    episodes = candidate_episodes(candidates, member, bundle)
    payload = analytical_input(candidates, episodes)
    graph = compile_behavioral_candidate_ir(payload)
    validate_analytical(payload, graph)
    expected_authority = closure.expected_authority(ROOT, payload, graph)
    if record_human_decisions:
        closure.record_authority(ROOT, expected_authority)
    authority = load(closure.AUTHORITY_PATH)
    closure.validate_authority(ROOT, authority, payload, graph)
    findings = closure.accepted_findings(authority, payload, graph)
    # Historical output is accessed only after new candidate compilation.
    comparison = historical_comparison(graph)
    projected_meanings = [{k: copy.deepcopy(c[k]) for k in (
        "action_id", "candidate_id", "action_date", "exact_action_identity", "legislative_stage",
        "plain_language_meaning", "mechanism", "limitations", "exact_action_boundary", "governed_sources")}
        | {"accepted_candidate_record_sha256": digest(c),
           "source_claim_locators": [{k: row[k] for k in ("mapping_id", "field", "source_id", "locator")}
                                     for row in c["claim_source_mappings"]]}
        for c in candidates]
    review = {
        "schema_version": "m14d_analytical_review_package_v1", "artifact_role": "detached_non_authorizing_behavioral_review",
        "accepted": False, "authorizing": False, "public": False, "production_selectable": False,
        "review_decisions_available": ["ACCEPT", "REVISE", "OMIT"],
        "acceptance_authority": findings["subject"]["human_authority"],
        "review_status": "human_decisions_complete_internal_findings_only",
        "accepted_findings": {"path": closure.FINDINGS_PATH, "findings_subject_sha256": findings["findings_subject_sha256"]},
        "review_questions_status": "Historical review prompts, resolved by the bound user-supplied decisions; this review packet remains non-authorizing.",
        "scope": "17 approved actions in 16 accepted episodes; analytical candidates only, no issue-wide conclusion or public wording",
        "semantic_inputs": {"candidates": file_binding(f"{ACCEPTED}/action_interpretability_candidates.json"),
                            "promotion_manifest_sha256": manifest["manifest_sha256"],
                            "episode_structure": file_binding(f"{EPISODES}/episode_decision_implementation_bundle.json"),
                            "episode_authority": file_binding(f"{EPISODES}/human_policy_episode_authority.json")},
        "proposed_findings": graph["proposition_graph"]["propositions"],
        "approved_action_meanings": projected_meanings,
        "relationship_evidence_by_proposition": payload["relationship_evidence_by_proposition"],
        "evidence_bindings_by_proposition": {
            p["proposition_id"]: [{"action_id": c["action_id"], "candidate_id": c["candidate_id"],
                                   "accepted_candidate_record_sha256": digest(c),
                                   "claim_mapping_ids": [r["mapping_id"] for r in c["claim_source_mappings"]]}
                                  for c in candidates if c["action_id"] in p["evidence_action_ids"]]
            for p in graph["proposition_graph"]["propositions"]},
        "episode_accounting": graph["episode_accounting"],
        "episode_disposition_counts": dict(sorted(Counter(a["disposition"] for a in graph["episode_accounting"]).items())),
        "search_review": SEARCH_REVIEW,
        "non_elevation_definition": "Understood and preserved with receipts, but insufficient added analytical value for elevation; not evidence failure.",
        "historical_comparison_after_generation": comparison,
        "synthesis_propositions": [], "downstream_authorizations": graph["downstream_authorizations"],
        "review_questions": ["Is each proposed relationship explanatory beyond the listed votes?",
                             "Do stated material differences require revising or omitting the bargaining-continuity candidate?",
                             "Does each statement stay within the approved meanings and exact whole-package choices?",
                             "Are the non-elevated episode dispositions justified without implying evidence failure?"],
    }
    return {f"{V2}/shared_action_core.json": json_bytes(core),
            f"{V2}/member_projections/f000477.json": json_bytes(member),
            f"{V2}/promotion_manifest.json": json_bytes(manifest),
            f"{OUT}/compiler_input.json": json_bytes(payload),
            f"{OUT}/behavioral_candidate_graph.json": json_bytes(graph),
            f"{OUT}/review_package.json": json_bytes(seal(review, "review_package_sha256")),
            closure.FINDINGS_PATH: json_bytes(findings)}


def historical_comparison(graph: dict) -> dict:
    path = "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_education_workforce_119_v1/behavioral_semantic_ir_decision_implementation.json"
    old = load(path)
    records = old["subject"]["implementation_records"]
    old_propositions = [r["accepted_candidate_content"] for r in records]
    new = {p["proposition_id"]: p for p in graph["proposition_graph"]["propositions"]}
    changes = []
    for record, previous in zip(records, old_propositions, strict=True):
        match = next((p for p in new.values() if set(p["evidence_action_ids"]) == set(previous["evidence_action_ids"])), None)
        changes.append({"historical_proposition_id": previous["proposition_id"],
                        "historical_record_sha256": record["record_subject_sha256"],
                        "m14d_proposition_id": match["proposition_id"] if match else None,
                        "status": "materially_changed_semantic_basis" if match else "removed",
                        "detail": ("Same two funding-exclusion episodes, now bounded by named covered relationships, distinct funding streams and distinct waiver conditions; no inherited behavioral acceptance."
                                   if previous["proposition_type"] == "repeated_pattern" else
                                   "Same single mixed episode, now explains the substitute's actual thresholds, exceptions, sanctions and negotiated rules versus the whole final package. Prior vague Section 117 wording is not reused.")})
    for p in new.values():
        if not any(set(p["evidence_action_ids"]) == set(old_p["evidence_action_ids"]) for old_p in old_propositions):
            changes.append({"historical_proposition_id": None, "m14d_proposition_id": p["proposition_id"],
                            "status": "new", "detail": "Bargaining-continuity relationship proposed from the approved concrete H.R.2550 and H.R.5408 meanings. Both episodes previously remained outside higher-level findings."})
    old_ledger = {r["episode_id"]: r for r in old["subject"]["accepted_episode_disposition_ledger"]}
    return {"input_to_candidate_generation": False, "historical_artifact": file_binding(path),
            "historical_counts": dict(Counter(p["proposition_type"] for p in old_propositions)),
            "new_counts": dict(Counter(p["proposition_type"] for p in graph["proposition_graph"]["propositions"])),
            "changes": changes, "removed_findings": [],
            "trajectory_count": 0, "synthesis_count": 0,
            "episode_disposition_comparison": [{"episode_id": r["episode_id"],
                                                "historical_disposition": old_ledger[r["episode_id"]]["disposition"],
                                                "m14d_disposition": r["disposition"]} for r in graph["episode_accounting"]],
            "accounting_change": "Eight understood episodes are explicitly receipt_only_no_elevation, not evidence failures; training-pay exclusion is retained as distinct labor context. No historical artifact or authority is changed."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="offline no-write exact reproduction")
    parser.add_argument("--check-scope", action="store_true", help="reject any change outside M14D")
    parser.add_argument("--record-human-decisions", action="store_true", help="one-time materialization of the supplied PR178 human decisions; refuses overwrite")
    args = parser.parse_args()
    require(not (args.check and args.record_human_decisions), "check mode cannot record authority")
    if args.check_scope:
        validate_scope()
        closure.validate_closure_scope(ROOT)
    outputs = build_outputs(record_human_decisions=args.record_human_decisions)
    for name, content in outputs.items():
        path = ROOT / name
        if args.check:
            require(path.exists() and path.read_bytes().replace(b"\r\n", b"\n") == content, f"generated M14D artifact differs: {name}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists() or path.read_bytes().replace(b"\r\n", b"\n") != content:
                path.write_bytes(content)
    core = json.loads(outputs[f"{V2}/shared_action_core.json"])
    member = json.loads(outputs[f"{V2}/member_projections/f000477.json"])
    review = json.loads(outputs[f"{OUT}/review_package.json"])
    print(json.dumps({"mode": "check" if args.check else "build", "core_count": len(core["actions"]),
                      "core_sha256": core["corpus_sha256"], "member_count": len(member["actions"]),
                      "member_sha256": member["projection_sha256"], "episode_dispositions": review["episode_disposition_counts"],
                      "proposed_findings": len(review["proposed_findings"]), "synthesis": 0}, indent=2))


if __name__ == "__main__":
    main()
