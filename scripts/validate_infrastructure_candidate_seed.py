"""Offline checks for the bounded Infrastructure seed; confers no acceptance."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import digest, sealed_digest
from scripts.prepare_shared_domain_candidate import (
    prepare, readable_candidates, reproducibility_proof, review_text,
    validate_universe_proposal,
)

DATA = ROOT / "docs/editorial/shared_candidates/house_119_infrastructure_20260916"
HEALTH = ROOT / "docs/editorial/shared_candidates/house_119_health_20260916"
SEED = {"house:119:1:8", "house:119:1:64", "house:119:1:74"}
CONTROLS = {"house:119:1:105", "house:119:1:106"}
MEMBERS = ["F000477", "M001184"]
NEUTRAL = re.compile(r"\b(?:Foushee|Massie|F000477|M001184|Democrat\w*|Republican\w*)\b", re.I)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def official_status(label):
    return {"Aye": "Yea", "No": "Nay"}.get(label, label)


def assert_neutral(value):
    """Only authored shared prose; source quotations can name legislators."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key not in {"claim_source_map", "sources", "claim_source_map_ref"}:
                assert_neutral(child)
    elif isinstance(value, list):
        for child in value:
            assert_neutral(child)
    elif isinstance(value, str):
        require(NEUTRAL.search(value) is None, "member/party contamination in shared prose")


def floor_version_checks(sources):
    """Compare whole floor bill bodies, with a narrowly declared formatting view.

    This alphanumeric comparison is a version witness, not a universal claim of
    punctuation/legal equivalence; original text and PDF page extracts remain.
    """
    result = []
    for number, sid, pages in [
        (192, "record:2025-01-13-hr192-infra", [5]),
        (901, "record:2025-03-10-hr901-infra", None),
        (1534, "record:2025-03-24-hr1534-infra", [17, 18, 19]),
    ]:
        source = sources[sid]
        if pages is None:
            floor = source["text"]
        else:
            extracts = {p["pdf_page"]: p["text"] for p in source["page_extracts"]}
            # Remove only declared page headers and publishing footers.
            floor = " ".join("\n".join(extracts[p].splitlines()[1:]).split("VerDate")[0]
                             for p in pages)
        begin = floor.index("Be it enacted", floor.index(f"H.R. {number}"))
        floor = floor[begin:floor.index("The SPEAKER pro tempore.", begin)]
        eh = sources[f"govinfo:hr{number}eh"]
        require(eh["text_version"] == "EH", "wrong seed text version")
        body = eh["text"][eh["text"].index("Be it enacted"):eh["text"].index("Passed the House")]
        normalize = lambda text: re.sub("[^a-z0-9]", "", text.lower())
        require(normalize(floor) == normalize(body), f"floor/EH version differs: HR{number}")
        result.append(dict(bill=f"HR{number}", floor_source_id=sid,
            eh_source_id=eh["source_id"], normalized_characters=len(normalize(body)),
            normalized_body_sha256=digest(normalize(body)), matched=True,
            scope="Complete operative bill bodies under lowercase ASCII-alphanumeric comparison; original punctuation retained, legal equivalence not certified"))
    return result


def validate_inputs(author, capture, universe, membership):
    validate_universe_proposal(universe, author, capture, membership)
    baseline = read(HEALTH / "universe_proposal.json")
    fields = ("action_id", "session", "roll", "date", "measure", "question", "member_action")
    rows = universe["candidate_dispositions"]
    require(len(rows) == 676, "676 identity conservation failed")
    require([[r[k] for k in fields] for r in rows] ==
            [[r[k] for k in fields] for r in baseline["candidate_dispositions"]],
            "discovery identity or official observation differs")
    require(digest([r["action_id"] for r in rows]) ==
            "e1a0ecb12b1697b6c5bbc43147ea66d155ed1e10b543efb18eaa05d677be5d25",
            "ordered discovery identity digest differs")
    require(dict(Counter(r["session"] for r in rows)) == {1: 362, 2: 314},
            "session accounting differs")
    require(set(universe["interpretation_action_ids"]) == SEED,
            "bounded interpretation set differs")
    require({r["action_id"] for r in membership["records"]} == SEED | CONTROLS,
            "five-action membership set differs")
    require(dict(Counter(r["disposition"] for r in rows)) == {
        "interpreted_substantive_directional": 3, "procedural_context": 2,
        "source_unresolved": 671}, "candidate disposition conservation differs")
    for key in ["full_record_claim", "synthesis_eligible", "full_issue_universe_closed",
                "publication_authorized", "publication_changes", "production_writes",
                "episode_acceptance_authorized", "synthesis_authorized"]:
        require(universe[key] is False, f"unauthorized boundary: {key}")
    require(universe["approval_receipt"] is None, "approval manufactured")
    sources = {s["source_id"]: s for s in capture["sources"]}
    floor_version_checks(sources)
    for row in rows:
        if row["action_id"] not in SEED | CONTROLS:
            require(row["unresolved_reason"] == "pending_research" and
                    row["review_progress"]["substantive_review_performed"] is False and
                    row["review_progress"]["required_evidence_unavailable"] is False,
                    "ordinary unfinished research misrepresented")
            require("operative_source_id" not in row and row["episode_candidate_id"] is None,
                    "other-domain interpretation transferred")
            continue
        clerk = sources[f"clerk:119:{row['session']}:{row['roll']}"]
        meta = clerk["metadata"]
        require((int(meta["congress"]), int(meta["session"][0]), int(meta["rollcall-num"])) ==
                (119, row["session"], row["roll"]), "Clerk coordinate differs")
        require(meta["vote-question"] == row["question"] and
                datetime.strptime(meta["action-date"], "%d-%b-%Y").date().isoformat() == row["date"],
                "Clerk question/date differs")
        require(all(row["source"][k] == clerk[k] for k in
                    ["source_id", "url", "raw_sha256", "governed_bytes_sha256"]),
                "reviewed Clerk provenance differs")
        require(official_status(clerk["member_records"]["F000477"]["official_label"]).lower().replace(" ", "_") ==
                row["member_action"], "official observation differs")
    assert_neutral(author["actions"])
    assert_neutral(membership["records"])
    # The three baseline instruction mismatches must remain visible in meaning,
    # compact and limitations. The legislature's text is never silently repaired.
    hr901 = next(a for a in author["actions"] if a["bill_number"] == 901)
    require("(13)/(14)" in hr901["meaning"] and "duplicate numbering" in hr901["meaning"] and
            "paragraph (15)" in hr901["meaning"] and
            "amendment instructions conflict" in hr901["compact_description"],
            "DHS amendment-instruction qualification lost")
    return sources


def validate_generated(author, capture, universe, membership, *, check_files=True):
    sources = validate_inputs(author, capture, universe, membership)
    core, mapping, projections, inputs, result = prepare(author, capture, MEMBERS)
    readable = readable_candidates(author, core, projections, result)
    proof = reproducibility_proof(author, capture, MEMBERS)
    assert_neutral([{k: a[k] for k in ["candidate_exact_action_meaning",
        "candidate_short_description", "candidate_compact_description",
        "candidate_shared_limitations", "choice_meanings"]} for a in core["actions"]])
    by_id = {a["action_id"]: a for a in core["actions"]}
    for projection in projections:
        for row in projection["actions"]:
            action = by_id[row["action_id"]]
            require(row["action_core_sha256"] == action["action_core_sha256"],
                    "member projection reinterpreted shared core")
            clerk = sources[action["action_outcome_source_identities"][0]["source_id"]]
            require(row["official_status"] == official_status(clerk["member_records"][projection["member_id"]]["official_label"]),
                    "projected official choice differs")
    for member in readable["members"]:
        require(len(member["findings"]) == 3, "expected three bounded findings per member")
        for finding in member["findings"]:
            for observation in finding["action_observations"]:
                action = by_id[observation["action_id"]]
                require(observation["detail"][1] == action["candidate_exact_action_meaning"] and
                        observation["qualifications"] == action["candidate_shared_limitations"],
                        "readable copy changed shared meaning/qualifications")
    products = dict(shared_action_core=core, shared_issue_mapping=mapping,
        member_projections=projections, compiler_input=inputs, compiled_ir=result.compiled_ir,
        readable_candidates=readable, reproducibility_proof=proof)
    if check_files:
        for name, value in products.items():
            # Match the existing generator's native text-mode serialization.
            expected = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").replace("\n", os.linesep).encode("utf-8")
            require((DATA / "generated" / f"{name}.json").read_bytes() == expected,
                    f"generated bytes differ: {name}")
        packet = (ROOT / "docs/review_packets/infrastructure_candidate_seed.md").read_text(encoding="utf-8")
        actual = packet.split("<!-- GENERATED CANDIDATE START -->\n", 1)[1].split("<!-- GENERATED CANDIDATE END -->", 1)[0]
        require(actual == review_text(author, core, projections, result, capture),
                "review packet replay differs")
    return dict(identity_count=676,session_counts={"1":362,"2":314},
        ordered_identity_sha256=universe["complete_official_action_id_set_sha256"],
        dispositions=universe["accounting"]["counts"],source_count=len(sources),
        claim_bindings=sum(len(a["claim_source_map"]) for a in author["actions"]),
        floor_version_checks=floor_version_checks(sources),
        core_sha256=core["corpus_sha256"],compiled_sha256=digest(result.compiled_ir),
        member_observations=6,member_finding_counts={m["member_id"]:len(m["findings"]) for m in readable["members"]},
        byte_identical_generated_replay=check_files,member_neutral_prose=True,
        independent_semantic_review="pending",full_universe_boundary_review="pending",
        publication_authorized=False,production_writes=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    values = [read(DATA / f"{name}.json") for name in
              ["authoring", "sources", "universe_proposal", "membership_review"]]
    report = validate_generated(*values)
    if args.receipt:
        args.receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
