"""Offline candidate preparation through the existing corpus and IR pipeline.

Inputs are reviewed-as-candidates shared authoring, governed source captures,
and explicit member IDs. This command neither accepts nor publishes content.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import (
    adapt_to_semantic_ir_input, choice_effect, digest, sealed_digest,
    candidate_update_impact, validate_member_projection, SharedCorpusValidationError,
)
from backend.app.semantic_ir.pipeline import run_editorial_pipeline

CANDIDATE = "candidate_pending_external_semantic_review"


def identity(source):
    return {key: source[key] for key in (
        "source_id", "source_type", "text_version", "raw_sha256", "governed_bytes_sha256"
    )}


def validate_sources(sources):
    for source in sources.values():
        if sealed_digest(source, "governed_bytes_sha256") != source["governed_bytes_sha256"]:
            raise ValueError(f"governed source changed: {source['source_id']}")


def validate_universe_proposal(universe):
    """Use the existing universe contract without conferring boundary authority."""
    from jsonschema import Draft202012Validator
    schema = json.loads((ROOT / "docs/methodology/cross_issue_full_record_expansion_v2.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(universe)
    if sealed_digest(universe, "proposal_sha256") != universe["proposal_sha256"]:
        raise ValueError("universe proposal digest differs")
    material = {"subject": universe["subject"], "cutoff": universe["cutoff"],
                "candidate_records": universe["candidate_dispositions"]}
    if digest(material) != universe["universe_subject_sha256"]:
        raise ValueError("universe subject digest differs")
    if universe["full_record_claim"] or universe["publication_authorized"] or universe["approval_receipt"] is not None:
        raise ValueError("candidate proposal cannot confer full-record or publication authority")


def prepare(authoring, capture, member_ids):
    """No source acquisition, member branches, selection or output repair."""
    if authoring["review_state"] != CANDIDATE:
        raise ValueError("this command prepares candidates only")
    if authoring["policy_relationships"]:
        raise ValueError("new policy relationships require a reviewed shared mapping")
    sources = {s["source_id"]: s for s in capture["sources"]}
    if len(sources) != len(capture["sources"]):
        raise ValueError("duplicate source identity")
    validate_sources(sources)
    actions = []
    for proposed in authoring["actions"]:
        aid = proposed["action_id"]
        _, congress, session, roll = aid.split(":")
        clerk = sources[f"clerk:{congress}:{session}:{roll}"]
        meta = clerk["metadata"]
        if (int(meta["congress"]), int(meta["session"][0]), int(meta["rollcall-num"])) != (int(congress), int(session), int(roll)):
            raise ValueError("Clerk source does not match exact action")
        if meta["legis-num"] != f"H R {proposed['bill_number']}":
            raise ValueError("Clerk measure and proposed text differ")
        question = meta["vote-question"]
        valid_stage = {
            "final_passage": question == "On Passage",
            "amendment": question == "On Agreeing to the Amendment",
            "suspension_and_passage": question in {"On Motion to Suspend the Rules and Pass", "On Motion to Suspend the Rules and Pass, as Amended"},
        }
        if not valid_stage.get(proposed["stage"], False):
            raise ValueError("candidate stage differs from exact Clerk question")
        date = datetime.strptime(meta["action-date"], "%d-%b-%Y").date().isoformat()
        if date > authoring["interpretation_action_set_cutoff"]:
            raise ValueError("new raw action cannot extend declared interpretation cutoff")
        operative_sources = [sources[sid] for sid in [proposed["source_id"], *proposed.get("additional_source_ids", [])]]
        operative_by_id = {s["source_id"]: s for s in operative_sources}
        for claim in proposed["claim_source_map"]:
            if claim["source_id"] not in operative_by_id or claim["passage"] not in operative_by_id[claim["source_id"]]["text"]:
                raise ValueError(f"claim passage absent from bound source: {aid}")
        source_ids = [identity(clerk), *[identity(s) for s in operative_sources]]
        action = {
            "action_id": aid, "exact_action_identity": aid,
            "chamber": "house", "congress": int(congress), "session": int(session), "roll": int(roll),
            "legislative_stage": proposed["stage"], "action_date": date,
            "exact_question": question,
            "chamber_outcome": meta["vote-result"], "enactment_status": "not_inferred_from_house_outcome",
            "mechanism": proposed["short_description"], "mechanism_availability": "candidate_source_mapped",
            "candidate_exact_action_meaning": proposed["meaning"],
            "candidate_short_description": proposed["short_description"],
            "candidate_shared_limitations": proposed["limitations"],
            "choice_meanings": proposed["choice_meanings"], "claim_source_map": proposed["claim_source_map"],
            "action_meaning_ref": f"{authoring['snapshot_id']}:{aid}:candidate-v1",
            "governed_source_identities": source_ids, "governed_source_identity_sha256": digest(source_ids),
            "action_outcome_source_identities": [identity(clerk)],
            "operative_meaning_source_identities": [identity(s) for s in operative_sources],
            "semantic_ir_source_ids": [s["source_id"] for s in source_ids],
            "package_component_boundary": {
                "boundary_type": "exact_amendment" if proposed["stage"] == "amendment" else "whole_measure",
                "parent_package_meaning_projected": False,
                "basis": proposed["limitations"],
            },
            "source_contract_version": "shared_legislative_corpus_v1",
            "meaning_contract_version": "candidate-extension-v1",
        }
        action["action_core_sha256"] = digest(action)
        actions.append(action)
    core = {
        "schema_version": "shared_action_core_v1", "artifact_id": f"shared-action-core:house:{authoring['congress']}:v3",
        "identity_unit": "exact House legislative action and governed source version",
        "authoritative_for_new_editorial_work": False, "review_state": CANDIDATE,
        "historical_inputs_rewritten": False, "actions": actions, "corpus_sha256": digest(actions),
    }
    episodes = {}
    mappings = []
    for proposed in authoring["actions"]:
        eid = proposed["episode_id"]
        episode = episodes.setdefault(eid, {"episode_id": eid, "action_ids": [], "method_boundary_types": [], "policy_family_id": None})
        episode["action_ids"].append(proposed["action_id"])
        row = {"action_id": proposed["action_id"], "eligibility": {"decision": "proposed", "parent_context_used": False},
               "episode_id": eid, "policy_family_refs": [], "policy_trait_refs": [], "structural_metadata": {}}
        row["mapping_sha256"] = digest(row)
        mappings.append(row)
    blocked = [a for eid in authoring["blocked_episode_ids"] for a in episodes[eid]["action_ids"]]
    mapping = {
        "schema_version": "shared_issue_mapping_v1", "artifact_id": f"candidate:{authoring['domain_id']}:{authoring['snapshot_id']}",
        "domain_id": authoring["domain_id"], "scope_boundaries": [authoring["boundary"]],
        "authoritative_for_new_editorial_work": False, "review_state": CANDIDATE, "historical_inputs_rewritten": False,
        "semantic_ir_case_scope": "full_record",  # all declared inputs, never product-level full issue authority
        "action_mappings": mappings, "episodes": list(episodes.values()), "policy_families": [], "policy_traits": [],
        "trait_relationships": [], "shared_review_dependencies": [],
        "source_render_constraints": ([{"action_ids": blocked, "constraint_id": "candidate-episode-hold",
            "detail": authoring["blocked_reason"], "semantic_effect": "blocks_behavioral_propositions"}] if blocked else []),
    }
    mapping["mapping_sha256"] = digest(mapping)
    projections = []
    for member_id in member_ids:
        rows = []
        names, parties = set(), set()
        for action in actions:
            source = sources[action["action_outcome_source_identities"][0]["source_id"]]
            official = source["member_records"].get(member_id)
            if official is None:
                raise ValueError(f"source does not contain member {member_id}: {action['action_id']}")
            status = {"Aye": "Yea", "No": "Nay"}.get(official["official_label"], official["official_label"])
            names.add(official["name"])
            parties.add(official["party"])
            rows.append({"action_id": action["action_id"], "action_core_sha256": action["action_core_sha256"],
                "official_status": status, "service_status": "in_service", "evidence_status": "official_record_resolved",
                "exact_choice_effect": choice_effect(status), "member_action_source_identities": [identity(source)],
                "member_action_source_identity_sha256": digest([identity(source)])})
        projection = {
            "schema_version": "member_action_projection_v1",
            "artifact_id": f"member-action-projection:{member_id.lower()}:house:{authoring['congress']}:v3",
            "member_id": member_id, "party": "/".join(sorted(parties)),
            "context_metadata": {"display_name": "/".join(sorted(names)), "service_basis": "Named official Clerk member row at each listed action; no unobserved service interval inferred."},
            "authoritative_legislative_meaning": False, "actions": rows,
        }
        projection["projection_sha256"] = digest(projection)
        projections.append(projection)
    compiler_input = adapt_to_semantic_ir_input(ROOT, core, mapping, projections)
    result = run_editorial_pipeline(compiler_input)
    return core, mapping, projections, compiler_input, result


def readable_candidates(authoring, core, projections, result):
    """Render only exact choices already present in canonical behavioral IR."""
    from backend.app.semantic_ir.adapters import build_shared_candidate_readable
    return build_shared_candidate_readable(core, projections, result.compiled_ir, authoring["boundary"])


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def review_text(authoring, core, projections, result, capture):
    """Readable review appendix from the same shared forms and exact receipts."""
    readable = readable_candidates(authoring, core, projections, result)
    sources = {s["source_id"]: s for s in capture["sources"]}
    first = readable["members"][0]
    name = projections[0]["context_metadata"]["display_name"]
    lines = [f"## Generated {name} candidate findings", "", first["boundary"], "",
             "All wording below remains candidate copy. Qualifications apply at both compact and detailed levels.", ""]
    for finding in first["findings"]:
        lines.extend(["### " + finding["headline"], "", "**Compact:** " + finding["compact"], "", "**Detail:**", ""])
        lines.extend(finding["detail"] + [""])
        lines.extend("- " + limit for limit in finding["qualifications_on_both_levels"])
        lines.extend(["", "Evidence: " + ", ".join(finding["action_ids"]) + "; finding `" + finding["proposition_id"] + "`.", "",
            "Sources: " + "; ".join(f"[{sid}]({sources[sid]['url']})" for sid in finding["source_ids"]) + ".", ""])
    lines.extend(["### Shared choices for the held episode", "", authoring["blocked_reason"], ""])
    blocked = {row["action_id"] for row in first["non_proposition_accounting"] if row["reason_code"] == "source_constraint_blocks_behavioral_proposition"}
    for action in core["actions"]:
        if action["action_id"] not in blocked:
            continue
        lines.extend(["**" + action["action_id"] + ": " + action["candidate_short_description"] + "**", "",
                      action["candidate_exact_action_meaning"], ""])
        lines.extend("- " + limit for limit in action["candidate_shared_limitations"])
        lines.extend(["", "Yea: " + action["choice_meanings"]["Yea"] + ".", "Nay: " + action["choice_meanings"]["Nay"] + ".", ""])
    lines.extend(["### Both-choice source index", "", "| Action | Yea | Nay | Governed text |", "|---|---|---|---|"])
    for action in core["actions"]:
        lines.append("| " + " | ".join([action["action_id"], action["choice_meanings"]["Yea"], action["choice_meanings"]["Nay"],
            "; ".join(f"[{s['source_id']}]({sources[s['source_id']]['url']})" for s in action["operative_meaning_source_identities"])]) + " |")
    return "\n".join(lines) + "\n"


def reproducibility_proof(authoring, capture, member_ids):
    """Actual replay plus explicitly controlled, non-authorizing updates."""
    before = prepare(authoring, capture, member_ids)
    core, mapping, projections, inputs, result = before
    rendered = readable_candidates(authoring, core, projections, result)
    after = prepare(authoring, capture, member_ids)
    assert digest(result.compiled_ir) == digest(after[-1].compiled_ir)
    assert digest(rendered) == digest(readable_candidates(authoring, after[0], after[2], after[-1]))
    by_member = {p["member_id"]: {a["action_id"]: a for a in p["actions"]} for p in projections}
    reuse = []
    for action in core["actions"]:
        choices = []
        for mid, rows in by_member.items():
            row = rows[action["action_id"]]
            assert row["action_core_sha256"] == action["action_core_sha256"]
            choices.append({"member_id": mid, "status": row["official_status"],
                "effect": row["exact_choice_effect"], "selected_meaning": action["choice_meanings"].get(row["official_status"]),
                "source_id": row["member_action_source_identities"][0]["source_id"]})
        reuse.append({"action_id": action["action_id"], "shared_sha256": action["action_core_sha256"], "choices": choices})
    raw = copy.deepcopy(capture)
    extra = {"source_id": "synthetic:later-raw-record", "text": "Controlled raw-ledger addition, not historical or interpreted."}
    extra["governed_bytes_sha256"] = digest(extra); raw["sources"].append(extra)
    raw_result = prepare(authoring, raw, member_ids)
    assert core == raw_result[0] and result.compiled_ir == raw_result[-1].compiled_ir
    eligible = result.compiled_ir["members"][0]["action_accounting"]["behavioral_proposition_action_ids"]
    if not eligible:
        raise ValueError("update proof requires an independently compiled behavioral finding")
    differing = [r["action_id"] for r in reuse if r["action_id"] in eligible and
                 {c["status"] for c in r["choices"]} == {"Yea", "Nay"}]
    target = differing[0] if differing else eligible[0]
    correction = copy.deepcopy(core)
    corrected = next(a for a in correction["actions"] if a["action_id"] == target)
    corrected["candidate_shared_limitations"].append("CONTROLLED TEST: shared qualification correction; no real acceptance or publication.")
    corrected["action_core_sha256"] = sealed_digest(corrected, "action_core_sha256")
    correction["corpus_sha256"] = digest(correction["actions"])
    impact = candidate_update_impact(core, correction, projections, result.compiled_ir)
    rejected = []
    for projection in projections:
        try:
            validate_member_projection(ROOT, projection, correction)
        except SharedCorpusValidationError:
            rejected.append(projection["member_id"])
    assert len(rejected) == len(projections)
    # Explicitly admitted candidate input differs from an ignored raw record.
    prior = copy.deepcopy(authoring)
    prior["actions"] = [a for a in prior["actions"] if a["action_id"] != target]
    prior_result = prepare(prior, capture, member_ids)
    assert prior_result[-1].compiled_ir != result.compiled_ir
    return {
        "authority": "candidate proof only; no acceptance, historical authorized update or publication claimed",
        "rule_files_sha256": {name: digest((ROOT / name).read_text(encoding="utf-8")) for name in [
            "scripts/prepare_shared_domain_candidate.py", "backend/app/semantic_ir/shared_corpus.py",
            "backend/app/semantic_ir/compiler.py", "backend/app/semantic_ir/pipeline.py", "backend/app/semantic_ir/adapters.py",
            "backend/app/semantic_ir/validation.py", "docs/semantic_ir/shared_legislative_corpus_v1.schema.json"]},
        "input_sha256": digest(authoring), "source_capture_sha256": digest(capture),
        "core_sha256": core["corpus_sha256"], "compiled_sha256": digest(result.compiled_ir),
        "readable_sha256": digest(rendered), "identical_replay": True,
        "real_member_reuse": reuse,
        "differing_real_choices_exercised": bool(differing),
        "controlled_raw_update": {"interpretation_unchanged": True, "cutoff_unchanged": authoring["interpretation_action_set_cutoff"]},
        "controlled_new_interpretation_input": {"action_id": target, "requires_explicit_authoring_change": True, "acceptance_conferred": False},
        "controlled_shared_correction": {"impact": impact, "stale_projections_rejected": rejected, "historical_core_unchanged": True},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--member", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review-packet", type=Path)
    args = parser.parse_args()
    authoring = json.loads((args.input / "authoring.json").read_text(encoding="utf-8"))
    capture = json.loads((args.input / "sources.json").read_text(encoding="utf-8"))
    validate_universe_proposal(json.loads((args.input / "universe_proposal.json").read_text(encoding="utf-8")))
    core, mapping, projections, compiler_input, result = prepare(authoring, capture, args.member)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in {
        "shared_action_core": core, "shared_issue_mapping": mapping, "member_projections": projections,
        "compiler_input": compiler_input, "compiled_ir": result.compiled_ir,
        "readable_candidates": readable_candidates(authoring, core, projections, result),
        "reproducibility_proof": reproducibility_proof(authoring, capture, args.member),
    }.items():
        write_json(args.output / f"{name}.json", value)
    if args.review_packet:
        text = args.review_packet.read_text(encoding="utf-8")
        start, end = "<!-- GENERATED CANDIDATE START -->", "<!-- GENERATED CANDIDATE END -->"
        if text.count(start) != 1 or text.count(end) != 1:
            raise ValueError("review packet requires one generated candidate region")
        before, rest = text.split(start)
        _, after = rest.split(end)
        args.review_packet.write_text(before + start + "\n" + review_text(authoring, core, projections, result, capture) + end + after, encoding="utf-8")
    print(json.dumps({"review_state": CANDIDATE, "validation": result.validation,
        "core_sha256": core["corpus_sha256"], "compiled_sha256": digest(result.compiled_ir)}))


if __name__ == "__main__":
    main()
