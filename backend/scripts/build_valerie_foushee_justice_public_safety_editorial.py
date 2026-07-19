"""Build the pending Foushee Justice & Public Safety editorial review artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/editorial/valerie_foushee_justice_public_safety_gold_v1"
PUBLIC = ROOT / "frontend/lib/valerieFousheeJusticePublicSafetyEditorialGold.mjs"
STATUS = "human_approval_pending"


def source(source_id: str) -> dict:
    manifest = json.loads((OUT / "source_manifest.json").read_text(encoding="utf-8"))
    item = next(value for value in manifest["sources"] if value["source_id"] == source_id)
    return {"name": item["name"], "locator": item["locator"], "group": item["source_type"], "url": item["url"]}


def argument(attribution: str, text: str) -> dict:
    return {"attribution": attribution, "argument": text}


def entry(roll, measure, stage, action, episode, headline, choice, result, baseline, mechanism,
          affected, timing, next_step, detail, supporters, opponents, boundary, history, caveats, source_ids):
    two = {
        "detail": detail,
        "supporter_argument": supporters,
        "argument_boundary": boundary,
        "later_history": history,
        "caveats": caveats,
        "sources": [source(value) for value in source_ids],
    }
    if opponents is not None:
        two["opponent_argument"] = opponents
    return {
        "roll": roll, "measure_id": measure, "stage": stage, "member_action": action,
        "episode_id": episode, "human_approval_status": STATUS,
        "ten_second": {"headline": headline, "practical_choice": choice, "member_action_and_result": result},
        "thirty_second": {"prior_baseline": baseline, "mechanism": mechanism, "affected": affected,
                           "scale_or_timing": timing, "what_happened_next": next_step},
        "two_minute": two,
        "comprehension": [
            {"question": "What was Congress deciding?", "expected": choice, "field": "ten_second.practical_choice"},
            {"question": "What did Foushee do?", "expected": action, "field": "ten_second.member_action_and_result"},
            {"question": "What was the status?", "expected": next_step, "field": "thirty_second.what_happened_next"},
        ],
    }


def build_packet() -> dict:
    fentanyl_support = argument("House and Senate bill supporters", "Supporters argued that permanent classwide scheduling would strengthen enforcement while preserving a research pathway.")
    fentanyl_oppose = argument("House floor opponents", "Opponents argued that permanent classwide scheduling and associated penalties could repeat harms of earlier drug policy and inadequately distinguish substances.")
    records = [
        entry(32, "119-hr-27-amdt-5", "Trahan amendment No. 2", "Yea", "halt-fentanyl-legislative-path",
              "Supported a certification condition for the earlier fentanyl bill",
              "Whether H.R. 27 should take effect only after HHS and DOJ jointly certified that it would reduce overdose deaths.",
              "Foushee voted Yea. The amendment failed 182-226.",
              "H.R. 27 would otherwise take effect without this certification step.",
              "The amendment would condition the bill's changes on a joint HHS-DOJ Federal Register certification.",
              "Federal agencies implementing the scheduling and enforcement changes, researchers, and people affected by the controlled-substance rules.",
              "The condition would apply before the bill's changes took effect.",
              "The amendment failed; the House then passed H.R. 27 without it.",
              "This was a substantive condition on implementation, not a generic procedural vote.",
              argument("Representative Trahan", "She argued that the certification was an evidence guardrail tied to overdose reduction."),
              argument("Representative Guthrie", "He argued that the certification could delay enforcement of needed fentanyl controls."),
              "These are attributed floor arguments and do not establish why Foushee voted Yea.",
              "A related Senate bill, S. 331, later passed the House and became law.",
              ["The amendment failed.", "This action and the later bill votes are one policy episode.", "The vote does not establish motive."],
              ["clerk_roll_032", "congress_hamdt5", "record_hr27_debate"]),
        entry(33, "119-hr-27", "House passage", "Nay", "halt-fentanyl-legislative-path",
              "Opposed the House's earlier permanent fentanyl-scheduling bill",
              "Whether to pass H.R. 27 after the certification amendment failed.",
              "Foushee voted Nay. The House passed the bill 312-108.",
              "Temporary classwide scheduling for fentanyl-related substances was already in place.",
              "The bill would make classwide Schedule I treatment permanent and set related penalty and research-registration rules.",
              "Federal enforcement and research agencies, researchers, defendants, and communities affected by fentanyl-related substances.",
              "This was the House's February version, not the later enacted bill.",
              "H.R. 27 passed the House but did not itself become law.",
              "The vote followed rejection of a proposed overdose-reduction certification condition.", fentanyl_support, fentanyl_oppose,
              "The arguments describe the bill-level dispute; they do not identify Foushee's reason for voting Nay.",
              "The Senate later sent the House the related S. 331, which became Public Law 119-26.",
              ["H.R. 27 and S. 331 are related but not identical actions.", "A Nay does not assign a reason."],
              ["clerk_roll_033", "congress_hr27", "record_hr27_debate"]),
        entry(166, "119-s-331", "House passage of Senate bill", "Yea", "halt-fentanyl-legislative-path",
              "Supported the later fentanyl bill that became law",
              "Whether to pass the Senate bill making classwide fentanyl-related-substance scheduling permanent with research provisions.",
              "Foushee voted Yea. The bill passed 321-104 and later became law.",
              "Temporary classwide scheduling remained in place while Congress considered a permanent framework.",
              "S. 331 made classwide Schedule I treatment permanent and included registration and rulemaking provisions for research.",
              "Federal enforcement and research agencies, researchers, defendants, and communities affected by fentanyl-related substances.",
              "The President signed Public Law 119-26 on July 16, 2025.",
              "The measure became law after this House vote.",
              "The enacted law combined permanent scheduling with provisions concerning research registration and agency rulemaking.", fentanyl_support, fentanyl_oppose,
              "The debate supplies competing policy arguments; it does not explain Foushee's change across related measures.",
              "Signed as Public Law 119-26.",
              ["The earlier H.R. 27 vote and this vote belong to one episode.", "The votes do not reveal why her position differed."],
              ["clerk_roll_166", "congress_s331", "public_law_119_26", "record_s331_debate", "cbo_s331"]),
        entry(130, "119-hr-2255", "House passage", "Nay", "retired-service-weapon-purchases",
              "Opposed a program for eligible officers to buy retired service firearms",
              "Whether to require a federal program allowing eligible current and retired officers to buy certain retired agency-issued firearms.",
              "Foushee voted Nay. The House passed the bill 234-182.",
              "No government-wide statutory purchase program with these terms was in place.",
              "GSA would establish a program for eligible officers in good standing to buy qualifying retired firearms at salvage value during a six-month window.",
              "Participating federal agencies and eligible current or retired law-enforcement officers.",
              "GSA would establish the program within one year; specified weapons would remain excluded.",
              "The bill went to the Senate and was not enacted as of review.",
              "Eligibility, transfer rules, exclusions, and agency participation were defined in the House-passed text.",
              argument("House bill supporters", "Supporters argued that officers could retain familiar service weapons while agencies avoided disposal costs."),
              argument("Committee dissenting views and floor opponents", "Opponents raised transfer, background-check, weapon-eligibility, and public-safety concerns."),
              "These attributed arguments do not establish which concern, if any, explains Foushee's Nay.",
              "Received in the Senate after House passage.",
              ["The bill covered eligible officers and qualifying firearms, not every officer or weapon.", "House passage did not create the program."],
              ["clerk_roll_130", "congress_hr2255_text", "hrpt_119_080", "record_hr2255_debate"]),
        entry(131, "119-hr-2240", "House passage", "Yea", "officer-safety-data-reporting",
              "Supported federal reporting on attacks and officer wellness",
              "Whether to require DOJ reports on attacks against law-enforcement officers, reporting-system feasibility, and mental-health and wellness resources.",
              "Foushee voted Yea. The House passed the bill 403-11.",
              "Federal data and reporting on these subjects were spread across existing systems and programs.",
              "DOJ would prepare reports on attacks, reporting feasibility, and officer mental-health and wellness resources.",
              "Law-enforcement agencies and officers, DOJ, and policymakers using the resulting reports.",
              "The bill set 270-day deadlines for the principal reports.",
              "The bill went to the Senate and was not enacted as of review.",
              "The House action authorized information gathering and reporting; it did not itself create a new criminal penalty.",
              argument("Bipartisan House floor supporters", "Supporters argued that better data could guide officer-safety and wellness policy."),
              None,
              "No adequate stage-specific opposing argument was found in the reviewed official materials; none is inferred from the 11 Nays.",
              "Received in the Senate after House passage.",
              ["The reviewed official materials did not provide a fair stage-specific opposing case.", "A Yea does not establish a position on policies Congress might later consider using the reports."],
              ["clerk_roll_131", "congress_hr2240", "hrpt_119_079", "record_hr2240_debate"]),
        entry(275, "119-hr-5143", "House passage of Rules Committee substitute", "Nay", "dc-police-pursuit-rules",
              "Opposed replacing D.C.'s police-pursuit restrictions",
              "Whether Congress should replace D.C.'s pursuit restrictions with a broader pursuit requirement and specified risk and effectiveness exceptions.",
              "Foushee voted Nay. The House passed the bill 245-182.",
              "D.C. law restricted when Metropolitan Police Department officers could initiate vehicle pursuits.",
              "The substitute would require pursuit in specified felony and violent-misdemeanor circumstances when other apprehension means were unavailable, subject to exceptions, and require a DOJ technology report.",
              "D.C. residents, drivers, police officers, local officials, and DOJ.",
              "The measure would alter local pursuit rules and require a federal report.",
              "The bill went to the Senate and was not enacted as of review.",
              "The vote was on the Rules Committee substitute, whose exceptions matter to describing the policy accurately.",
              argument("House bill supporters", "Supporters argued that broader pursuit authority would help police apprehend people suspected of serious offenses."),
              argument("House floor opponents and D.C. officials", "Opponents argued that Congress should respect D.C. home rule and that broader pursuits could increase public danger."),
              "The debate presents institutional and safety arguments; it does not establish Foushee's reason for voting Nay.",
              "Received in the Senate after House passage.",
              ["The substitute included exceptions; it was not an unconditional pursuit mandate.", "A Nay does not reveal which objection drove the vote."],
              ["clerk_roll_275", "congress_hr5143", "rules_print_119_11", "record_hr5143_debate"]),
        entry(299, "119-hr-5107", "House passage of committee substitute", "Nay", "dc-policing-reform-repeal",
              "Opposed repealing most of D.C.'s 2022 policing reform law",
              "Whether Congress should repeal most provisions of D.C.'s 2022 policing reform law and restore prior rules, subject to exceptions in the substitute.",
              "Foushee voted Nay. The House passed the bill 233-190.",
              "D.C.'s 2022 law governed police practices, disclosure, discipline, and oversight.",
              "The committee substitute would repeal most of that law and restore prior provisions while retaining specified exceptions.",
              "D.C. residents, police officers, oversight bodies, courts, and local government.",
              "The measure addressed neck restraints, body-camera access, disciplinary records, and other policing rules.",
              "The bill went to the Senate and was not enacted as of review.",
              "The exact committee substitute matters: describing it as repeal of the entire law would overstate its reach.",
              argument("House bill supporters", "Supporters argued that undoing the D.C. law's restrictions would improve recruitment, retention, and public safety."),
              argument("Committee minority and floor opponents", "Opponents argued that the bill displaced local self-government and weakened accountability and public protections."),
              "These are attributed arguments about the substitute and do not establish Foushee's motive.",
              "Received in the Senate after House passage.",
              ["The substitute repealed most, not necessarily every, provision.", "A vote on a package does not isolate a view on each component."],
              ["clerk_roll_299", "congress_hr5107", "hrpt_119_317", "record_hr5107_debate"]),
    ]
    controls = []
    control_info = {
        160: ("119-hres-489", "Previous-question vote on a multi-measure rule", "congress_hres489"),
        161: ("119-hres-489", "Rule adoption covering multiple measures", "congress_hres489"),
        267: ("119-hres-707", "Previous-question vote on a seven-bill rule", "congress_hres707"),
        268: ("119-hres-707", "Rule adoption covering Justice and non-Justice measures", "congress_hres707"),
        290: ("119-hres-879", "Previous-question vote on a multi-measure rule", "congress_hres879"),
        291: ("119-hres-879", "Rule adoption covering multiple unrelated measures", "congress_hres879"),
    }
    for roll, (measure, summary, resolution_source) in control_info.items():
        controls.append({"roll": roll, "measure_id": measure, "member_action": "No", "episode_id": f"context-roll-{roll}",
                         "context_summary": summary, "why_not_counted": "Indirect procedural action; retained as context and excluded from substantive and episode counts.",
                         "human_approval_status": STATUS, "sources": [source(f"clerk_roll_{roll:03d}"), source(resolution_source)]})
    return {
        "schema_version": "editorial_gold_review_packet_v2", "packet_id": "valerie_foushee_justice_public_safety_gold_v1",
        "member": {"name": "Valerie P. Foushee", "bioguide_id": "F000477"}, "domain": "Justice & Public Safety",
        "content_version": "justice_public_safety_gold_v1_candidate_2026-07-19", "editorial_status": STATUS,
        "review_tier": "full_gold", "public_copy_disclaimer": "Candidate source-checked draft. Human factual review, comprehension testing, and approval remain pending.",
        "slice_counts": {"substantive_rolls": 7, "policy_episodes": 5, "not_voting_records": 0, "context_controls": 6},
        "interpretations": records, "controls": controls,
        "argument_evidence_review": {"roll_131": {"status": "insufficient_official_evidence_after_review", "opponent_argument_omitted": True,
            "sources_reviewed": ["congress_hr2240", "hrpt_119_079", "record_hr2240_debate"],
            "limitation": "No adequate stage-specific opposing case appeared in the reviewed official materials."}},
        "human_approval_status": STATUS,
    }


def outputs() -> dict[Path, str]:
    packet = build_packet()
    manifest = json.loads((OUT / "source_manifest.json").read_text(encoding="utf-8"))
    claims = {"schema_version": "editorial_claim_source_map_v1", "human_approval_status": STATUS,
              "claims": [{"claim_id": f"roll_{item['roll']}_editorial", "roll": item["roll"],
                          "source_ids": [next(src["source_id"] for src in manifest["sources"] if src["url"] == value["url"]) for value in item["two_minute"]["sources"]],
                          "human_approval_status": STATUS} for item in packet["interpretations"]]}
    public = {key: packet[key] for key in ("schema_version", "member", "content_version", "slice_counts", "interpretations", "controls", "human_approval_status")}
    for item in public["interpretations"]:
        item.pop("comprehension", None)
    module = "// Generated review-only candidate; do not edit directly.\nexport const valerieFousheeJusticePublicSafetyEditorialGold = " + json.dumps(public, indent=2, ensure_ascii=False) + ";\n"
    docs = {
        "README.md": "# Valerie P. Foushee — Justice & Public Safety gold v1\n\nPending, review-only editorial slice built from official sources. It contains 7 substantive actions in 5 episodes and 6 non-counting procedural controls. Nothing here is production eligible.\n",
        "issue_synthesis.md": "# Issue synthesis\n\nIn this reviewed sample, Foushee took a mixed approach across five Justice & Public Safety policy episodes. She supported delaying an earlier fentanyl bill pending agency certification, opposed that House version, and later supported a related Senate bill that became law. She supported a bipartisan officer-safety reporting bill and opposed proposals for retired federal officers to buy agency firearms, to replace D.C. pursuit restrictions, and to repeal most of a broader D.C. policing reform law. These seven substantive votes show bounded choices across distinct mechanisms, not one overarching Justice philosophy.\n\nShe matched the majority of House Democrats on all seven substantive roll calls. The Democratic splits on the two fentanyl passage votes were close enough that this alignment context must not be treated as an explanation.\n",
        "comprehension_protocol.md": "# Comprehension protocol\n\nFor every substantive action, ask what Congress decided, what Foushee did, and what happened next. A response fails if it merges the three fentanyl actions, counts a procedural control, treats a Nay as motive, says H.R. 5107 repealed every provision, or invents an opposing case for H.R. 2240. Human comprehension testing remains pending.\n",
        "editorial_workflow_contract.md": "# Editorial workflow contract\n\nThe reusable contract accepted all records through explicit episode identity, optional argument sides, generic count indicators, source deduplication, and an empty additional-record list. This slice adds no domain-specific runtime branch. Registry status, source status, and record status remain `human_approval_pending`; production eligibility remains false.\n",
        "side_by_side_review.md": "# Side-by-side review\n\nGenerated from `review_packet.json`. Review the 10-second choice and action, 30-second mechanism and affected groups, then the 2-minute attributed arguments and caveats. Roll 131 intentionally omits an opponent argument after an official-source search found no adequate stage-specific case.\n",
    }
    dossier_data = {
        "halt_fentanyl.json": ("halt-fentanyl-legislative-path", [32, 33, 166], "Permanent classwide fentanyl scheduling, penalties, and research pathways across related House and Senate measures."),
        "hr2255.json": ("retired-service-weapon-purchases", [130], "A purchase program for eligible officers and qualifying retired agency firearms."),
        "hr2240.json": ("officer-safety-data-reporting", [131], "DOJ reporting on attacks, data-system feasibility, and officer wellness resources."),
        "hr5143.json": ("dc-police-pursuit-rules", [275], "A substitute replacing D.C. pursuit restrictions with a broader rule and exceptions."),
        "hr5107.json": ("dc-policing-reform-repeal", [299], "A substitute repealing most of D.C.'s 2022 policing reform law, with exceptions."),
    }
    result = {OUT / "review_packet.json": json.dumps(packet, indent=2, ensure_ascii=False) + "\n",
              OUT / "claim_source_map.json": json.dumps(claims, indent=2, ensure_ascii=False) + "\n", PUBLIC: module}
    result.update({OUT / name: text for name, text in docs.items()})
    for name, (episode, rolls, core) in dossier_data.items():
        dossier = {"schema_version": "editorial_measure_dossier_v1", "episode_id": episode, "rolls": rolls,
                   "factual_core": core, "member_independent": True, "human_approval_status": STATUS}
        result[OUT / "measures" / name] = json.dumps(dossier, indent=2, ensure_ascii=False) + "\n"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    drift = []
    for path, content in outputs().items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                drift.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if drift:
        print("Generated artifact drift: " + ", ".join(drift))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
