"""Bounded batch2 evidence, nondirectional accounting, preservation and replay."""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import digest, sealed_digest
from scripts.prepare_shared_domain_candidate import (
    prepare, readable_candidates, reproducibility_proof, review_text,
    validate_universe_proposal,
)
from scripts.validate_infrastructure_candidate_seed import (
    assert_neutral, official_status, read, require,
)

DATA = ROOT / "docs/editorial/shared_candidates/house_119_infrastructure_batch2_20260916"
SEED = ROOT / "docs/editorial/shared_candidates/house_119_infrastructure_20260916"
NEW = {f"house:119:1:{r}" for r in [104, 136, 157, 191, 192, 196]}
HOLD = "house:119:1:111"


def versions(sources):
    rows = []
    for bill, sid, pages, btype in [
        (146, "record:2025-04-28-s146-infra2", [16, 17, 18], "s"),
        (1223, "record:2025-05-19-hr1223-infra2", [5, 6], "hr"),
        (2035, "record:2025-06-09-hr2035-infra2", [10, 11], "hr"),
        (1709, "record:2025-07-14-hr1709-infra2", [5, 6, 7], "hr"),
        (1770, "record:2025-07-14-hr1770-infra2", [8, 9, 10], "hr"),
        (1717, "record:2025-07-14-hr1717-infra2", [14, 15], "hr"),
    ]:
        source = sources[sid]
        extracts = {p["pdf_page"]: p["text"] for p in source["page_extracts"]}
        floor = " ".join("\n".join(extracts[p].splitlines()[1:]).split("VerDate")[0] for p in pages)
        name = ("S. " if btype == "s" else "H.R. ") + str(bill)
        start = floor.index("Be it enacted", floor.index(name))
        floor = floor[start:floor.index("The SPEAKER pro tempore.", start)]
        source_id = "govinfo:s146es" if btype == "s" else f"govinfo:hr{bill}eh"
        enacted = sources[source_id]
        require(enacted["text_version"] == ("ES" if btype == "s" else "EH"), "wrong exact text version")
        text = enacted["text"]
        body = text[text.index("Be it enacted"):text.index("Passed the")]
        normalized = lambda value: re.sub("[^a-z0-9]", "", value.lower())
        require(normalized(floor) == normalized(body), f"floor body differs: {name}")
        rows.append(dict(bill=name, text_source_id=source_id, floor_source_id=sid,
            matched=True, normalized_body_sha256=digest(normalized(body)),
            scope="Complete operative bodies under lowercase ASCII-alphanumeric comparison; original punctuation retained, legal equivalence not certified"))
    return rows


def validate(author, capture, universe, membership, *, check_files=True):
    validate_universe_proposal(universe, author, capture, membership)
    seed = {n: read(SEED / f"{n}.json") for n in ["authoring", "sources", "universe_proposal", "membership_review"]}
    by_id = {a["action_id"]: a for a in author["actions"]}
    require(set(by_id) == {a["action_id"] for a in seed["authoring"]["actions"]} | NEW,
            "batch interpretation set differs")
    for action in seed["authoring"]["actions"]:
        require(by_id[action["action_id"]] == action, "batch reinterpreted the corrected seed")
    for source in seed["sources"]["sources"]:
        require(source in capture["sources"], "batch changed a retained seed source")
    rows = {r["action_id"]: r for r in universe["candidate_dispositions"]}
    prior = seed["universe_proposal"]["candidate_dispositions"]
    fields = ["action_id", "session", "roll", "date", "measure", "question", "member_action"]
    require(len(rows) == 676 and [[r[k] for k in fields] for r in universe["candidate_dispositions"]] ==
            [[r[k] for k in fields] for r in prior], "676 discovery identities changed")
    require(dict(Counter(r["disposition"] for r in rows.values())) == {
        "interpreted_substantive_directional":8, "interpreted_substantive_non_directional":1,
        "procedural_context":2, "source_unresolved":665}, "disposition conservation differs")
    require(universe["accounting"]["action_ids_by_disposition"] == {
        kind:[r["action_id"] for r in universe["candidate_dispositions"] if r["disposition"] == kind]
        for kind in universe["accounting"]["counts"]}, "disposition identity buckets differ")
    ordinary = [r for r in rows.values() if r["unresolved_reason"] == "pending_research"]
    require(len(ordinary) == 664 and all(not r["review_progress"]["substantive_review_performed"]
        and not r["review_progress"]["required_evidence_unavailable"] and r["episode_candidate_id"] is None
        for r in ordinary), "ordinary pending misrepresented")
    require(rows[HOLD]["review_progress"]["required_evidence_unavailable"] and
        rows[HOLD]["episode_candidate_id"] is None and HOLD not in by_id and
        rows[HOLD]["unresolved_reason"] == "denied_material_waiver_source_no_retry",
        "denied waiver source hold lost")
    require(all(not universe[k] for k in ["full_record_claim", "synthesis_eligible",
        "full_issue_universe_closed", "publication_authorized", "publication_changes", "production_writes",
        "episode_acceptance_authorized", "synthesis_authorized"]) and universe["approval_receipt"] is None,
        "reserved boundary changed")
    sources = {s["source_id"]: s for s in capture["sources"]}
    require(all("unblock.federalregister.gov" not in s["url"] and
                "Federal Register :: Request Access" not in s.get("text", "") and
                "Page Not Found" not in s.get("text", "") for s in sources.values()),
            "denied/error response promoted to evidence")
    for record in membership["records"]:
        row = rows[record["action_id"]]
        clerk = sources[f"clerk:119:{row['session']}:{row['roll']}"]
        require(clerk["metadata"]["vote-question"] == row["question"], "exact Clerk question differs")
        status = official_status(clerk["member_records"]["F000477"]["official_label"])
        require(status.lower().replace(" ", "_") == row["member_action"], "official universe observation differs")
        if row["action_id"] in by_id:
            expected = "interpreted_substantive_non_directional" if status in ["Present", "Not Voting"] else "interpreted_substantive_directional"
            require(row["disposition"] == expected, "nondirectional disposition contradicts official status")
    assert_neutral(author["actions"])
    assert_neutral(membership["records"])
    for action in author["actions"]:
        prose = " ".join([action["meaning"], action["compact_description"], *action["limitations"]])
        require(re.search(r"\b(?:Health|Infrastructure|Immigration|Education)\s+(?:membership|inclusion|eligibility)\b",
                          prose, re.I) is None, "issue-specific membership conclusion in action core")
    for bill, needed in [(2035,"govinfo:46usc55305-2024-infra2"),
                         (1717,"govinfo:5usc1013-2024-operative")]:
        action = next(a for a in author["actions"] if a["bill_number"] == bill)
        require(needed in action["compact_source_refs"], "compact lost material baseline provenance")
    version_receipt = versions(sources)
    core, mapping, projections, inputs, result = prepare(author, capture, ["F000477", "M001184"])
    readable = readable_candidates(author, core, projections, result)
    proof = reproducibility_proof(author, capture, ["F000477", "M001184"])
    core_by_id = {a["action_id"]:a for a in core["actions"]}
    for member in readable["members"]:
        expected_count = 8 if member["member_id"] == "F000477" else 6
        require(len(member["findings"]) == expected_count, "finding count includes a nondirectional record")
        for finding in member["findings"]:
            for observation in finding["action_observations"]:
                action = core_by_id[observation["action_id"]]
                require(observation["status"] in ["Yea","Nay"] and
                    observation["detail"][1] == action["candidate_exact_action_meaning"] and
                    observation["qualifications"] == action["candidate_shared_limitations"],
                    "generated shared copy changed or nondirectional finding produced")
    for member in result.compiled_ir["members"]:
        expected_nv = 1 if member["member_id"] == "F000477" else 3
        require(member["coverage"]["not_voting_actions"] == expected_nv and
                member["coverage"]["directional_yes_no_positions"] == 9-expected_nv,
                "Not Voting counted directionally")
    products = dict(shared_action_core=core, shared_issue_mapping=mapping, member_projections=projections,
        compiler_input=inputs, compiled_ir=result.compiled_ir, readable_candidates=readable, reproducibility_proof=proof)
    if check_files:
        for name, value in products.items():
            expected = (json.dumps(value,ensure_ascii=False,indent=2)+"\n").replace("\n",os.linesep).encode()
            require((DATA/"generated"/f"{name}.json").read_bytes() == expected, f"generated replay differs: {name}")
        packet=(ROOT/"docs/review_packets/infrastructure_candidate_batch2.md").read_text(encoding="utf-8")
        region=packet.split("<!-- GENERATED CANDIDATE START -->\n",1)[1].split("<!-- GENERATED CANDIDATE END -->",1)[0]
        require(region == review_text(author,core,projections,result,capture),"readable packet replay differs")
    return dict(identity_count=676, new_screenings=7, new_meanings=6, combined_meanings=9,
        declared_member_dispositions=universe["accounting"]["counts"], ordinary_pending_count=664,
        examined_hold_ids=[HOLD], source_count=len(sources), member_observations=18,
        finding_counts={m["member_id"]:len(m["findings"]) for m in readable["members"]},
        not_voting_counts={m["member_id"]:m["coverage"]["not_voting_actions"] for m in result.compiled_ir["members"]},
        core_sha256=core["corpus_sha256"],compiled_sha256=digest(result.compiled_ir),floor_version_checks=version_receipt,
        member_neutral_prose=True,unchanged_corrected_seed=True,byte_identical_generated_replay=check_files,
        independent_batch_semantic_review="pending", full_issue_universe_closed=False,
        publication_authorized=False,production_writes=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--receipt",type=Path);args=parser.parse_args()
    result=validate(*[read(DATA/f"{n}.json") for n in ["authoring","sources","universe_proposal","membership_review"]])
    if args.receipt:args.receipt.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":main()
