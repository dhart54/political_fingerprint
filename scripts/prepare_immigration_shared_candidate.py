"""Immigration-only candidate source binding over the established Semantic IR V1.

The common adapter and frozen Health proof remain unchanged. This module admits
only explicitly bound unamended or whole-replacement deemed concurrence. It
invents no House question, member observation, legislative meaning, acceptance
or publication authority.
"""
from __future__ import annotations
import argparse
import copy
import json
import re
import sys
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import prepare_shared_domain_candidate as common
from scripts.prepare_shared_domain_candidate import identity, readable_candidates, review_text, write_json
from backend.app.semantic_ir.shared_corpus import (
    adapt_to_semantic_ir_input, candidate_update_impact, choice_effect, digest,
    sealed_digest, validate_member_projection, SharedCorpusValidationError,
)
from backend.app.semantic_ir.pipeline import run_editorial_pipeline
CANDIDATE = common.CANDIDATE

def _extended(action):
    witness = action.get("deemed_concurrence")
    return (isinstance(witness, dict) and "senate_amendment_source_id" in witness
            or "deemed_replacement_concurrence" in action)


def _bind_replacement_concurrence(proposed, sources, congress, clerk):
    witness = proposed.get("deemed_replacement_concurrence")
    if (not isinstance(witness, dict)
            or set(witness) != {"underlying_bill_number", "source_id", "passage",
                                "replacement_text_source_id", "rules_committee_print_number"}
            or "deemed_concurrence" in proposed
            or proposed.get("stage") != "concurrence"
            or proposed.get("bill_type") != "hres"):
        raise ValueError("invalid whole-replacement concurrence binding")
    number = witness["underlying_bill_number"]
    print_number = witness["rules_committee_print_number"]
    if (not isinstance(number, str) or not number.isdigit() or int(number) <= 0
            or not isinstance(print_number, str) or not print_number.isdigit()
            or int(print_number) <= 0
            or proposed["episode_id"] != f"episode:hr{number}:{congress}"
            or witness["source_id"] != proposed["source_id"]):
        raise ValueError("replacement concurrence must bind the underlying bill episode and print")
    source = sources[witness["source_id"]]
    clause = witness["passage"]
    prefix = ("Resolved, That upon adoption of this resolution, the House shall be "
              "considered to have taken from the Speaker's table the bill "
              f"(H.R. {number}) ")
    suffix = (", with the Senate amendment thereto, and to have concurred in the "
              "Senate amendment with an amendment consisting of the text of "
              f"Rules Committee Print {congress}-{print_number}.")
    if (source["source_type"] != "official_bill_text" or source["text_version"] != "EH"
            or f"[H. Res. {proposed['bill_number']} Engrossed in House (EH)]" not in source["text"]
            or not isinstance(clause, str) or not clause.startswith(prefix)
            or not clause.endswith(suffix)
            or not source["text"].endswith(clause + " Attest: Clerk.")
            or source["text"].count("Resolved,") != 1
            or not any(c["source_id"] == source["source_id"] and c["passage"] == clause
                       for c in proposed["claim_source_map"])):
        raise ValueError("replacement concurrence requires the exact governed operative clause")
    replacement_id = witness["replacement_text_source_id"]
    if (replacement_id not in proposed.get("additional_source_ids", [])
            or replacement_id not in sources):
        raise ValueError("replacement concurrence requires the whole exact Rules print")
    replacement = sources[replacement_id]
    normalized = " ".join(replacement["text"].split())
    header = f"RULES COMMITTEE PRINT {congress}–{print_number}"
    try:
        house_choice = datetime.strptime(
            clerk["metadata"]["action-date"] + " " + clerk["metadata"]["action-time"],
            "%d-%b-%Y %I:%M %p",
        )
    except (KeyError, ValueError) as exc:
        raise ValueError("replacement concurrence requires the exact dated Clerk time") from exc
    dates = re.findall(r"([A-Za-z]+) (\d+), (\d{4}) \((\d+):(\d+) ([ap])\.m\.\)", normalized)
    if (replacement["source_type"] != "official_rules_committee_print"
            or header not in normalized
            or f"TEXT OF THE HOUSE AMENDMENT TO THE SENATE AMENDMENT TO H.R. {number}" not in normalized
            or "In lieu of the matter proposed to be inserted by the Senate amendment, insert the following:" not in normalized
            or not dates
            or not any(c["source_id"] == replacement_id and c["passage"] == replacement["text"]
                       for c in proposed["claim_source_map"])):
        raise ValueError("replacement concurrence requires the whole exact Rules print")
    timestamps = [datetime.strptime(
        " ".join(date[:3]) + " " + date[3] + ":" + date[4] + " " + date[5].upper() + "M",
        "%B %d %Y %I:%M %p",
    ) for date in dates]
    if any(stamp > house_choice for stamp in timestamps):
        raise ValueError("replacement concurrence Rules print follows the House choice")
    return True

def _bind_concurrence(proposed, sources, congress, clerk):
    witness = proposed["deemed_concurrence"]
    if proposed.get("stage") != "concurrence":
        raise ValueError("invalid deemed-concurrence candidate binding")
    if (set(witness) != {"underlying_bill_number", "source_id", "passage",
                        "senate_amendment_source_id"}
            or proposed.get("bill_type") != "hres" or clerk is None):
        raise ValueError("invalid deemed-concurrence candidate binding")
    number = witness["underlying_bill_number"]
    if (not isinstance(number, str) or not number.isdigit() or int(number) <= 0
            or proposed["episode_id"] != f"episode:hr{number}:{congress}"
            or witness["source_id"] != proposed["source_id"]):
        raise ValueError("deemed concurrence must bind the underlying bill episode")
    source = sources[witness["source_id"]]
    clause = witness["passage"]
    prefix = (
        "Resolved, That upon adoption of this resolution, the House shall be "
        "considered to have taken from the Speaker's table the bill "
        f"(H.R. {number}) "
    )
    suffix = (", with the Senate amendment thereto, and to have concurred "
              "in the Senate amendment.")
    if (source["source_type"] != "official_bill_text" or source["text_version"] != "EH"
            or f"[H. Res. {proposed['bill_number']} Engrossed in House (EH)]" not in source["text"]
            or not isinstance(clause, str) or not clause.startswith(prefix)
            or not clause.endswith(suffix)
            or not source["text"].endswith(clause + " Attest: Clerk.")
            or source["text"].count("Resolved,") != 1
            or not any(c["source_id"] == source["source_id"] and c["passage"] == clause
                       for c in proposed["claim_source_map"])):
        raise ValueError("deemed concurrence requires the exact governed operative clause")
    amendment_id = witness["senate_amendment_source_id"]
    if amendment_id not in proposed.get("additional_source_ids", []):
        raise ValueError("deemed concurrence requires the exact Senate amendment")
    amendment = sources[amendment_id]
    senate_date = re.search(
        r"In the Senate of the United States, ([A-Za-z]+) (\d+)(?: \([^)]*\))?, (\d{4})\.",
        amendment["text"],
    )
    if (amendment["source_type"] != "official_bill_text" or amendment["text_version"] != "EAS"
            or f"[H.R. {number} Engrossed Amendment Senate (EAS)]" not in amendment["text"]
            or not any(c["source_id"] == amendment_id and c["passage"] == amendment["text"]
                       for c in proposed["claim_source_map"])
            or senate_date is None):
        raise ValueError("deemed concurrence requires the exact Senate amendment")
    dated = datetime.strptime(" ".join(senate_date.groups()), "%B %d %Y").date()
    house_date = datetime.strptime(clerk["metadata"]["action-date"], "%d-%b-%Y").date()
    if dated > house_date:
        raise ValueError("deemed concurrence Senate amendment follows the House choice")
    return True

def prepare(authoring, capture, member_ids):
    if authoring.get("domain_id") != "IMMIGRATION_BORDER":
        raise ValueError("Immigration candidate adapter cannot prepare another domain")
    sources = {s["source_id"]: s for s in capture["sources"]}
    for proposed in authoring["actions"]:
        # Reject known incompatible ordinary bill stages before the common
        # adapter. This is not a full vote-time reconstruction: later corrected
        # EH witnesses still require explicit contemporaneous claim bindings.
        # Direct/nested replacement resolutions have their own clause guards.
        if _extended(proposed) or proposed.get("deemed_concurrence") or proposed.get("nested_concurrence"):
            continue
        version = sources[proposed["source_id"]]["text_version"]
        passage_stages = {"final_passage", "suspension_and_passage", "division_retention", "veto_override"}
        if ((version == "EAS" and proposed["stage"] in passage_stages)
                or (version == "EH" and proposed["stage"] in {"concurrence", "suspension_and_concurrence"})):
            raise ValueError("primary bill version differs from exact legislative stage")
    additions = [a for a in authoring["actions"] if _extended(a)]
    ordinary = copy.deepcopy(authoring)
    ordinary["actions"] = [a for a in ordinary["actions"] if not _extended(a)]
    ordinary_episodes = {a["episode_id"] for a in ordinary["actions"]}
    ordinary["blocked_episode_ids"] = [e for e in ordinary["blocked_episode_ids"] if e in ordinary_episodes]
    core, mapping, projections, inputs, result = common.prepare(ordinary, capture, member_ids)
    if not additions:
        return core, mapping, projections, inputs, result
    sources = {s["source_id"]: s for s in capture["sources"]}
    for proposed in additions:
        aid = proposed["action_id"]
        _, congress, session, roll = aid.split(":")
        clerk = sources[f"clerk:{congress}:{session}:{roll}"]
        meta = clerk["metadata"]
        if (int(meta["congress"]), int(meta["session"][0]), int(meta["rollcall-num"])) != (int(congress), int(session), int(roll)):
            raise ValueError("Clerk source does not match exact action")
        if meta["legis-num"] != f"H RES {proposed['bill_number']}":
            raise ValueError("Clerk measure and proposed text differ")
        if meta["vote-question"] != "On Agreeing to the Resolution":
            raise ValueError("deemed concurrence differs from exact Clerk question")
        date = datetime.strptime(meta["action-date"], "%d-%b-%Y").date().isoformat()
        if date > authoring["interpretation_action_set_cutoff"]:
            raise ValueError("new raw action cannot extend declared interpretation cutoff")
        if "deemed_replacement_concurrence" in proposed:
            _bind_replacement_concurrence(proposed, sources, congress, clerk)
        else:
            _bind_concurrence(proposed, sources, congress, clerk)
        operative = [sources[sid] for sid in [proposed["source_id"], *proposed.get("additional_source_ids", [])]]
        by_id = {s["source_id"]: s for s in operative}
        if not proposed["compact_source_refs"] or not set(proposed["compact_source_refs"]) <= set(by_id):
            raise ValueError("compact meaning must reference its governed operative sources")
        for claim in proposed["claim_source_map"]:
            if claim["source_id"] not in by_id or claim["passage"] not in by_id[claim["source_id"]]["text"]:
                raise ValueError(f"claim passage absent from bound source: {aid}")
        source_ids = [identity(clerk), *[identity(s) for s in operative]]
        witness = proposed.get("deemed_replacement_concurrence", proposed.get("deemed_concurrence"))
        relationship = (f"H.Res.{proposed['bill_number']} directly deems concurrence in the Senate amendment "
                        f"for H.R.{witness['underlying_bill_number']}")
        if "deemed_replacement_concurrence" in proposed:
            relationship += f" with the whole House replacement in Rules Committee Print {congress}-{witness['rules_committee_print_number']}"
        relationship += "; distinct exact action within the underlying bill episode"
        action = {
            "action_id": aid, "exact_action_identity": aid,
            "chamber": "house", "congress": int(congress), "session": int(session), "roll": int(roll),
            "legislative_stage": "concurrence", "action_date": date,
            "exact_question": meta["vote-question"], "chamber_outcome": meta["vote-result"],
            "enactment_status": "not_inferred_from_house_outcome",
            "mechanism": proposed["short_description"], "mechanism_availability": "candidate_source_mapped",
            "candidate_exact_action_meaning": proposed["meaning"], "candidate_short_description": proposed["short_description"],
            "candidate_compact_description": proposed["compact_description"], "compact_source_refs": proposed["compact_source_refs"],
            "candidate_shared_limitations": proposed["limitations"], "choice_meanings": proposed["choice_meanings"],
            "claim_source_map": proposed["claim_source_map"], "action_meaning_ref": f"{authoring['snapshot_id']}:{aid}:candidate-v1",
            "governed_source_identities": source_ids, "governed_source_identity_sha256": digest(source_ids),
            "action_outcome_source_identities": [identity(clerk)], "operative_meaning_source_identities": [identity(s) for s in operative],
            "semantic_ir_source_ids": [s["source_id"] for s in source_ids],
            "package_component_boundary": {"boundary_type": "whole_measure", "parent_package_meaning_projected": False,
                "basis": proposed["limitations"], "governed_component_relationships": [relationship]},
            "source_contract_version": "shared_legislative_corpus_v1", "meaning_contract_version": "candidate-extension-v1",
        }
        action["action_core_sha256"] = digest(action)
        core["actions"].append(action)
        row = {"action_id": aid, "eligibility": {"decision": "proposed", "parent_context_used": False},
            "episode_id": proposed["episode_id"], "policy_family_refs": [], "policy_trait_refs": [],
            "structural_metadata": {"stage_order": int(session) * 10000 + int(roll)}}
        row["mapping_sha256"] = digest(row)
        mapping["action_mappings"].append(row)
        episode = next((e for e in mapping["episodes"] if e["episode_id"] == proposed["episode_id"]), None)
        if episode is None:
            episode = {"episode_id": proposed["episode_id"], "action_ids": [], "method_boundary_types": [], "policy_family_id": None}
            mapping["episodes"].append(episode)
        episode["action_ids"].append(aid)
    if len({a["action_id"] for a in core["actions"]}) != len(core["actions"]):
        raise ValueError("duplicate exact action in candidate inputs")
    core["actions"].sort(key=lambda a: (a["session"], a["roll"]))
    core["corpus_sha256"] = digest(core["actions"])
    mapping["action_mappings"].sort(key=lambda a: a["structural_metadata"]["stage_order"])
    for episode in mapping["episodes"]:
        episode["action_ids"].sort(key=lambda aid: tuple(map(int, aid.split(":")[2:])))
    mapping["episodes"].sort(key=lambda e: tuple(map(int, e["action_ids"][0].split(":")[2:])))
    blocked = [a for e in mapping["episodes"] if e["episode_id"] in authoring["blocked_episode_ids"] for a in e["action_ids"]]
    mapping["source_render_constraints"] = ([{"action_ids": blocked, "constraint_id": "candidate-episode-hold",
        "detail": authoring["blocked_reason"], "semantic_effect": "blocks_behavioral_propositions"}] if blocked else [])
    mapping["mapping_sha256"] = sealed_digest(mapping, "mapping_sha256")
    for projection in projections:
        rows = []
        names, parties = set(), set()
        for action in core["actions"]:
            source = sources[action["action_outcome_source_identities"][0]["source_id"]]
            official = source["member_records"].get(projection["member_id"])
            if official is None:
                raise ValueError(f"source does not contain member {projection['member_id']}: {action['action_id']}")
            status = {"Aye": "Yea", "No": "Nay"}.get(official["official_label"], official["official_label"])
            names.add(official["name"]); parties.add(official["party"])
            rows.append({"action_id": action["action_id"], "action_core_sha256": action["action_core_sha256"],
                "official_status": status, "service_status": "in_service", "evidence_status": "official_record_resolved",
                "exact_choice_effect": choice_effect(status), "member_action_source_identities": [identity(source)],
                "member_action_source_identity_sha256": digest([identity(source)])})
        projection["actions"] = rows; projection["party"] = "/".join(sorted(parties))
        projection["context_metadata"]["display_name"] = "/".join(sorted(names))
        projection["projection_sha256"] = sealed_digest(projection, "projection_sha256")
    inputs = adapt_to_semantic_ir_input(ROOT, core, mapping, projections)
    result = run_editorial_pipeline(inputs)
    return core, mapping, projections, inputs, result

def _contract_proof(authoring, capture, member_ids):
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


def reproducibility_proof(authoring, capture, member_ids):
    proof = _contract_proof(authoring, capture, member_ids)
    proof["rule_files_sha256"]["scripts/prepare_immigration_shared_candidate.py"] = digest(Path(__file__).read_text(encoding="utf-8"))
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--member", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review-packet", type=Path)
    args = parser.parse_args()
    authoring = json.loads((args.input / "authoring.json").read_text(encoding="utf-8"))
    capture = json.loads((args.input / "sources.json").read_text(encoding="utf-8"))
    common.validate_universe_proposal(json.loads((args.input / "universe_proposal.json").read_text(encoding="utf-8")), authoring,
        capture, json.loads((args.input / "membership_review.json").read_text(encoding="utf-8")))
    core, mapping, projections, inputs, result = prepare(authoring, capture, args.member)
    args.output.mkdir(parents=True, exist_ok=True)
    values = {"shared_action_core": core, "shared_issue_mapping": mapping, "member_projections": projections,
        "compiler_input": inputs, "compiled_ir": result.compiled_ir,
        "readable_candidates": readable_candidates(authoring, core, projections, result),
        "reproducibility_proof": reproducibility_proof(authoring, capture, args.member)}
    for name, value in values.items():write_json(args.output / f"{name}.json", value)
    if args.review_packet:
        text = args.review_packet.read_text(encoding="utf-8")
        start, end = "<!-- GENERATED CANDIDATE START -->", "<!-- GENERATED CANDIDATE END -->"
        if text.count(start) != 1 or text.count(end) != 1:raise ValueError("review packet requires one generated candidate region")
        before, rest = text.split(start); _, after = rest.split(end)
        args.review_packet.write_text(before + start + "\n" + review_text(authoring, core, projections, result, capture) + end + after, encoding="utf-8")
    print(json.dumps({"review_state": CANDIDATE, "validation": result.validation,
        "core_sha256": core["corpus_sha256"], "compiled_sha256": digest(result.compiled_ir)}))

if __name__ == "__main__":main()
