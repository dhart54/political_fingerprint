"""Build the public-safe staged content bundle for the Foushee economy gold slice."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUNDLE_DIR = REPO_ROOT / "docs" / "editorial" / "valerie_foushee_economy_gold_v2"
PACKET_PATH = BUNDLE_DIR / "review_packet.json"
CLAIM_MAP_PATH = BUNDLE_DIR / "claim_source_map.json"
SOURCE_MANIFEST_PATH = BUNDLE_DIR / "source_manifest.json"
OUTPUT_PATH = REPO_ROOT / "frontend" / "lib" / "valerieFousheeEconomyEditorialGold.mjs"
SOURCE_COMMIT = "db7eb324136866c360a68a2f996e91907eb3d76d"


SOURCE_TYPE_LABELS = {
    "cbo_cost_estimate": "Congressional Budget Office",
    "congress_gov_actions": "Congress.gov actions",
    "congress_gov_crs_summary": "Congress.gov summary",
    "congress_gov_measure_text": "Congress.gov measure text",
    "congressional_record": "Congressional Record",
    "crs_report": "Congressional Research Service",
    "house_clerk_roll_call_xml": "House Clerk roll call",
    "house_committee_report": "House committee report",
    "house_floor_document": "House floor document",
    "govinfo_public_law": "Public law text",
    "public_law_text": "Public law text",
}

SOURCE_GROUPS = {
    "house_clerk_roll_call_xml": "Vote and legislative status",
    "congress_gov_actions": "Vote and legislative status",
    "congress_gov_measure_text": "Bill or resolution text",
    "govinfo_public_law": "Bill or resolution text",
    "public_law_text": "Bill or resolution text",
    "cbo_cost_estimate": "Nonpartisan analysis",
    "congress_gov_crs_summary": "Nonpartisan analysis",
    "crs_report": "Nonpartisan analysis",
    "house_committee_report": "Competing arguments",
    "congressional_record": "Competing arguments",
    "house_floor_document": "Competing arguments",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


SOURCE_NAME_OVERRIDES = {
    "crs_r48765": "CRS Report R48765",
    "crs_in12622": "CRS Insight IN12622",
    "govinfo_pl119_37": "Public Law 119-37",
    "record_hr5371_initial_debate": "September H.R. 5371 House debate",
    "record_hr5371_final_debate": "November H.R. 5371 House debate",
    "record_roll263_instruction": "Roll 263 House debate",
    "record_roll180_en_bloc": "Roll 180 House debate",
    "record_hconres14_initial_debate": "February H.Con.Res. 14 House debate",
    "record_hconres14_concurrence_debate": "April H.Con.Res. 14 concurrence debate",
}


def public_source_name(source_id: str, source_type: str) -> str:
    if source_id in SOURCE_NAME_OVERRIDES:
        return SOURCE_NAME_OVERRIDES[source_id]
    if match := re.fullmatch(r"clerk_roll_0*(\d+)", source_id):
        return f"House Clerk roll call {match.group(1)}"
    if match := re.fullmatch(r"hrpt_(\d+)_(\d+)", source_id):
        return f"H. Rept. {match.group(1)}-{int(match.group(2))}"
    if match := re.fullmatch(r"congress_(hr|hconres)(\d+)_(.+)", source_id):
        measure_type, number, suffix = match.groups()
        measure = f"H.R. {number}" if measure_type == "hr" else f"H.Con.Res. {number}"
        suffix_label = {
            "actions": "actions",
            "summary": "summary",
            "text": "measure text",
            "house_text": "House text",
            "house_passed_text": "House-passed text",
            "enrolled_text": "enrolled text",
        }.get(suffix, suffix.replace("_", " "))
        return f"{measure} {suffix_label}"
    if match := re.fullmatch(r"cbo_(hr)(\d+)(?:_(.+))?", source_id):
        _, number, suffix = match.groups()
        suffix_label = f" — {suffix.replace('_', ' ')}" if suffix else ""
        return f"CBO analysis of H.R. {number}{suffix_label}"
    return SOURCE_TYPE_LABELS.get(source_type, "Official source")


def public_source(source_id: str, source: dict) -> dict:
    source_type = source["source_type"]
    name = public_source_name(source_id, source_type)
    locator = str(source["locator"])
    locator = locator.replace(
        "vote-metadata; recorded-vote for bioguide F000477",
        "member vote and roll-call totals",
    ).replace(
        "recorded-vote for bioguide F000477",
        "member vote and roll-call totals",
    )
    return {
        "name": name,
        "locator": locator,
        "group": SOURCE_GROUPS.get(source_type, "Additional official evidence"),
        "url": source["url"],
    }


def public_sources(claim_ids: list[str], claims: dict[str, dict], sources: dict[str, dict]) -> list[dict]:
    result: list[dict] = []
    seen_source_ids: set[str] = set()
    seen_urls: set[str] = set()
    for claim_id in claim_ids:
        for source_id in claims[claim_id]["source_ids"]:
            if source_id in seen_source_ids:
                continue
            seen_source_ids.add(source_id)
            source = sources[source_id]
            canonical_url = str(source["url"]).rstrip("/")
            if canonical_url in seen_urls:
                continue
            seen_urls.add(canonical_url)
            result.append(public_source(source_id, source))
    return result


def build_public_bundle(packet: dict, claim_map: dict, source_manifest: dict) -> dict:
    claims = {claim["claim_id"]: claim for claim in claim_map["claims"]}
    sources = {source["source_id"]: source for source in source_manifest["sources"]}
    interpretations = []

    for item in packet["interpretations"]:
        proposed = item["proposed"]
        two_minute = proposed["two_minute"]
        interpretations.append(
            {
                "roll": item["roll"],
                "measure_id": item["measure_id"],
                "stage": item["stage"],
                "member_action": item["member_action"]["recorded"],
                "human_approval_status": item["human_approval_status"],
                "ten_second": {
                    "headline": proposed["ten_second"]["headline"],
                    "practical_choice": proposed["ten_second"]["practical_choice"],
                    "member_action_and_result": proposed["ten_second"]["member_action_and_result"],
                },
                "thirty_second": {
                    "prior_baseline": proposed["thirty_second"]["prior_baseline"],
                    "mechanism": proposed["thirty_second"]["mechanism"],
                    "affected": proposed["thirty_second"]["affected"],
                    "scale_or_timing": proposed["thirty_second"]["scale_or_timing"],
                    "what_happened_next": proposed["thirty_second"]["what_happened_next"],
                },
                "two_minute": {
                    "detail": two_minute["detail"],
                    "supporter_argument": {
                        "attribution": two_minute["supporter_argument"]["attribution"],
                        "argument": two_minute["supporter_argument"]["argument"],
                    },
                    "opponent_argument": {
                        "attribution": two_minute["opponent_argument"]["attribution"],
                        "argument": two_minute["opponent_argument"]["argument"],
                    },
                    "argument_boundary": two_minute["argument_boundary"],
                    "later_history": two_minute["later_history"],
                    "caveats": two_minute["caveats"],
                    "sources": public_sources(two_minute["claim_ids"], claims, sources),
                },
            }
        )

    controls = []
    for item in packet["controls"]:
        controls.append(
            {
                "roll": item["roll"],
                "measure_id": item["measure_id"],
                "member_action": item["member_action"]["recorded"],
                "human_approval_status": item["human_approval_status"],
                "context_summary": item["proposed_control_copy"],
                "why_not_counted": item["why_single_policy_translation_is_unsafe"],
                "sources": public_sources(item["claim_ids"], claims, sources),
            }
        )

    return {
        "schema_version": "foushee_economy_staged_public_v1",
        "source_commit": SOURCE_COMMIT,
        "member": {"bioguide_id": packet["member"]["bioguide_id"], "name": packet["member"]["name"]},
        "domain": "ECONOMY_TAXES",
        "human_approval_status": packet["editorial_status"],
        "slice_counts": {
            "substantive_rolls": 6,
            "policy_episodes": 4,
            "not_voting_records": 1,
            "context_controls": 2,
        },
        "interpretations": interpretations,
        "controls": controls,
    }


def render(bundle: dict) -> str:
    serialized = json.dumps(bundle, indent=2, ensure_ascii=False)
    return (
        "// Generated from the approved Foushee Economy & Taxes editorial packet.\n"
        "// Run backend/scripts/build_valerie_foushee_economy_staged_content.py to update.\n"
        f"export const valerieFousheeEconomyEditorialGold = {serialized};\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail when the generated public bundle is stale.")
    args = parser.parse_args()
    rendered = render(
        build_public_bundle(
            load_json(PACKET_PATH),
            load_json(CLAIM_MAP_PATH),
            load_json(SOURCE_MANIFEST_PATH),
        )
    )
    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text(encoding="utf-8") != rendered:
            raise SystemExit(f"stale generated staged content: {OUTPUT_PATH}")
        return 0
    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
