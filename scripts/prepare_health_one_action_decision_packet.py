"""Prepare a documentary pending owner packet and the existing IR review payload.

No acceptance builder, full-record authority wrapper, public compiler or storage
path is invoked. Inputs remain byte/content-bound to the reviewed PR237 merge.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import prepare_health_one_action_review as review
from backend.app.semantic_ir.adapters import build_review_payload, semantic_digest
from backend.app.semantic_ir.pipeline import run_editorial_pipeline

BASE = "a0605e4e3e3a81751bf273155f1cf5e0cfa4d21a"
INPUT = "docs/editorial/review_packages/health_s2393_one_action_v1/"
OUTPUT = ROOT / "docs/editorial/review_packages/health_s2393_owner_decision_v1"
REPORT = "docs/review_packets/health_one_action_acceptance_admission_report.md"
NAMES = (
    "shared_action_core.json", "shared_issue_mapping.json", "member_projections.json",
    "governed_sources.json", "claim_source_map.json", "membership_evidence.json",
    "compiler_input.json", "compiled_ir.json", "presentation_payload.json",
    "presentation_inputs.json", "review_source_contract.json", "provenance.json",
)
RAW_ROOT = "docs/editorial/full_record_reviews/source_readiness/evidence/f000477_national_security_foreign_119_v1/"
RAW_EVIDENCE = (
    ("congress-text:119:s:2393:es", "04f063befa42e8b335fc14539b218401408cfb806c3e734438a67d944db10689_BILLS-119s2393es.xml"),
    ("clerk:house:119:2:180", "d52d940529fbb4eab886c5c32ad6e712097829f93c886d5adb8cd171541c5e52_roll119_2_180.xml"),
    ("congress-actions:house:119:2:180", "a143f675f626923c67e3b3b50b242be832f4daab6389caed725b3f70ccef7bc0_119_s_2393_actions.json"),
)


@lru_cache(maxsize=None)
def git_bytes(path):
    return subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT)


def git_blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def read_products():
    return {name: json.loads((ROOT / INPUT / name).read_text(encoding="utf-8")) for name in NAMES}


def validate_frozen_products(products):
    review.require(set(products) == set(NAMES), "frozen Health file set differs")
    for name in NAMES:
        review.require(products[name] == json.loads(git_bytes(INPUT + name)), "frozen Health object differs: " + name)
    packet = (ROOT / INPUT / "DECISION-PACKET.md").read_bytes()
    review.require(packet == git_bytes(INPUT + "DECISION-PACKET.md"), "original packet bytes differ")
    wording = review.packet_wording(packet)
    review.validate_presentation_inputs(products["presentation_inputs.json"], products["compiled_ir.json"], products["review_source_contract.json"], wording)


def validate_review_payload(payload, compiled):
    review.require(payload == build_review_payload(compiled), "pending review payload differs")
    review.require(payload["approval_conferred"] is False, "review cannot confer approval")
    review.require(payload["review_state"] == review.CANDIDATE, "candidate review state required")


def validate_raw_evidence(raw_sources):
    review.require(set(raw_sources) == {source_id for source_id, _ in RAW_EVIDENCE}, "additional raw source set differs")
    for source_id, name in RAW_EVIDENCE:
        review.require(review.sha(raw_sources[source_id]) == name[:64], "additional raw bytes differ: " + source_id)
    bill = ElementTree.fromstring(raw_sources[RAW_EVIDENCE[0][0]])
    review.require(bill.get("bill-stage") == "Engrossed-in-Senate" and bill.findtext("form/legis-num") == "S. 2393", "additional ES identity differs")
    text = " ".join(" ".join(bill.itertext()).split()).lower()
    for phrase in ("1,762,668,000", "new bed tower", "clinical building expansion", "consolidated administrative building and warehouse", "utility plant", "parking garages", "fiscal year 2026"):
        review.require(phrase in text, "additional ES provision differs: " + phrase)
    clerk = ElementTree.fromstring(raw_sources[RAW_EVIDENCE[1][0]])
    for tag, value in {"congress": "119", "session": "2nd", "rollcall-num": "180", "legis-num": "S 2393", "vote-question": "On Motion to Suspend the Rules and Pass", "action-date": "20-May-2026"}.items():
        review.require(clerk.findtext("vote-metadata/" + tag) == value, "additional Clerk identity/stage differs")
    votes = {row.find("legislator").get("name-id"): row.findtext("vote") for row in clerk.iter("recorded-vote")}
    review.require(votes.get("F000477") == "Yea" and votes.get("M001184") == "Not Voting", "additional raw member status differs")
    actions = json.loads(raw_sources[RAW_EVIDENCE[2][0]])["actions"]
    matching = [row for row in actions if row.get("actionDate") == "2026-05-20" and any(v.get("rollNumber") == 180 and v.get("sessionNumber") == 2 and v.get("congress") == 119 and v.get("chamber") == "House" for v in row.get("recordedVotes", []))]
    review.require(any("On motion to suspend the rules and pass the bill Agreed to" in row["text"] for row in matching), "additional raw House passage stage differs")


def code(value):
    return "```json\n" + review.encoded(value).decode("utf-8").rstrip() + "\n```\n"


def render_packet(products, payload, raw_sources):
    compiled = products["compiled_ir.json"]
    lines = [
        "# S.2393 Health: pending owner decision packet\n",
        "Decision status: **pending; no new approval recorded**.\n",
        "This is an inert documentary decision subject and worksheet, accompanied by the existing typed IR review payload. It is **not an executable formal acceptance-chain subject**. `approval_conferred=false`; executable acceptance-chain admission is unresolved.\n",
        "Review scope: `bounded_partial_record`. Exactly `house:119:2:180`, singleton `episode:s2393:119`, F000477 and M001184. This does not assess either member's complete Health record. Compiler `case_scope=full_record` accounts for supplied inputs only.\n",
        "Bundle decision: __________  Reviewer: __________  Reviewed at (UTC): __________\n",
        "An owner may accept, request revision or reject the exact documentary subject below. This blank worksheet records no decision. A later decision must identify this exact subject and its limits; it does not execute acceptance, production eligibility, storage or publication.\n",
        "## Prior decision and current subject\n",
        "The [earlier documentary receipt](../../../review_packets/health_one_action_owner_decision_receipt_draft.md) records Dylan's 19 October 2026 Accept for selection/scope, exact interpretation and qualifications, Health membership/singleton episode, and exact packet wording/accounting. That decision does not accept this new graph, review payload or mapping implementation. Original historical blank fields remain unchanged.\n",
        "The [original packet](../health_s2393_one_action_v1/DECISION-PACKET.md) SHA-256 remains `" + review.PACKET_SHA + "`. Original ZIP remains **unverified**. Original normalized Health sources and hashes remain unchanged; no fresh acquisition or archive authentication is claimed.\n",
        "Pinned input Git origin: `" + BASE + "` (PR237 merge). Full compiled IR canonical subject SHA-256: `" + semantic_digest(compiled) + "`. The [review payload](review_payload.json) binds that entire IR, including both members; its approval flag remains false.\n",
        "## Complete two-member disposition and pending decisions\n",
        "| Member | Official action | Candidate disposition | Owner decision |\n|---|---|---|---|",
        "| F000477 (Foushee) | Yea | Exact-choice support; one notable choice `prop:75edca987585935c`; singleton `episode:s2393:119` | Pending |",
        "| M001184 (Massie) | Not Voting | Resolved nondirectional; zero behavioral propositions; `non_directional_status` accounting | Pending |\n",
        "Foushee's existing `conclusion_relevance=supporting` and `presentation_target=other_notable_choices` are preserved. No relabeling to `primary`, full-issue synthesis or extra proposition is proposed. Massie is neither opposition nor missing evidence. His accounting mapping retains the actual Not Voting boundary and no episode IDs.\n",
    ]
    for member in compiled["members"]:
        lines += ["### " + member["member_id"] + ": exact candidate objects\n", code({key: member[key] for key in ("proposition_graph", "coverage", "action_accounting")})]
    lines += ["## Seven unchanged presentation records\n", "All exact text, qualifications and complete mapping objects below are preserved from the reviewed candidate. They are typed review fragments, not a compiled public presentation. The complete original presentation-input file is separately hash-bound.\n"]
    for member in products["presentation_inputs.json"]["members"]:
        for field, record in member["records"].items():
            lines += ["### " + member["member_id"] + " / " + field + "\n", code(record)]
    lines += [
        "## Exact frozen input identities\n",
        "Hashes below are actual pinned Git blob bytes, independent of working-checkout CRLF conversion. JSON objects are also compared in full with those pinned inputs. No original input is rewritten.\n",
        "| Input (in original package) | Git blob | Raw Git bytes SHA-256 |\n|---|---|---|",
    ]
    for name in ("DECISION-PACKET.md", *NAMES):
        raw = git_bytes(INPUT + name)
        lines.append("| [" + name + "](../health_s2393_one_action_v1/" + name + ") | `" + git_blob(raw) + "` | `" + review.sha(raw) + "` |")
    lines += [
        "\n## Additional retained raw preparation evidence\n",
        "The following existing raw objects are read from pinned Git origin `" + BASE + "`, validated by their actual SHA-256, parsed and checked for S.2393 ES provisions, roll180 member observations and the recorded House suspension/pass stage. These are **additional preparation evidence only**. Their historical National Security acceptance, issue membership and episode identity do not transfer. They do not replace the original normalized Health sources, their different recorded raw hashes, source maps or governed-object seals. Later entries in the raw actions feed add no claim to this bounded packet.\n",
    ]
    for source_id, name in RAW_EVIDENCE:
        raw = raw_sources[source_id]
        lines += ["- Existing source identity `" + source_id + "`: `" + RAW_ROOT + name + "`; SHA-256 `" + review.sha(raw) + "`; Git blob `" + git_blob(raw) + "`.\n"]
    lines += [
        "## Executable admission remains unresolved\n",
        "The optional full-record receipt requires `review_scope=full_defined_issue_record` and `decision=approved_complete_issue_universe`. Those constants are incompatible with this bounded pilot. This packet carries no such receipt and makes no full-universe claim. A schema-valid null decision fragment is not proof of complete acceptance-chain admission.\n",
        "No Health full-record source-readiness/candidate/evidence-map/decision-template chain, accepted action implementation, accepted policy-episode implementation, or opt-in behavioral candidate envelope is asserted. Required missing artifact IDs and hashes are not fabricated. No National Security authority is substituted. The [admission report](../../../review_packets/health_one_action_acceptance_admission_report.md) identifies exact contracts, evidence requirements, alternatives and limits.\n",
        "The existing pipeline, public compiler and persistence guards remain intact. Completing this documentary review does not accept/promote a graph, authorize public authoring, approve a release artifact, confer benchmark/production eligibility, change a runtime manifest, write a database or publication registry, or deploy. Any later executable acceptance path must first resolve its applicable bounded admission and truthful content-bound prerequisites under separately applicable authority.\n",
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_packet(products=None, *, raw_sources=None):
    products = read_products() if products is None else products
    validate_frozen_products(products)
    compiled = run_editorial_pipeline(products["compiler_input.json"]).compiled_ir
    review.require(compiled == products["compiled_ir.json"], "canonical candidate replay differs")
    payload = build_review_payload(compiled)
    validate_review_payload(payload, compiled)
    raw_sources = {source_id: git_bytes(RAW_ROOT + name) for source_id, name in RAW_EVIDENCE} if raw_sources is None else raw_sources
    validate_raw_evidence(raw_sources)
    return {"review_payload.json": review.encoded(payload), "OWNER-DECISION-PACKET.md": render_packet(products, payload, raw_sources).encode("utf-8")}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    outputs = build_packet()
    if not args.check:
        OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, raw in outputs.items():
        path = OUTPUT / name
        if args.check:
            review.require(path.is_file() and path.read_text(encoding="utf-8").replace("\r\n", "\n") == raw.decode("utf-8"), "documentary packet drift: " + name)
        else:
            path.write_bytes(raw)
    print(json.dumps({"files": len(outputs), "check_only": args.check, "approval_conferred": False, "executable_acceptance_chain_ready": False, "database_accessed": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
