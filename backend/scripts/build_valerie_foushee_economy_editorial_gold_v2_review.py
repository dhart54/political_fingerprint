"""Build the deterministic Markdown review for the Foushee editorial gold V2 packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUNDLE_DIR = REPO_ROOT / "docs" / "editorial" / "valerie_foushee_economy_gold_v2"
PACKET_PATH = BUNDLE_DIR / "review_packet.json"
CLAIM_MAP_PATH = BUNDLE_DIR / "claim_source_map.json"
SOURCE_MANIFEST_PATH = BUNDLE_DIR / "source_manifest.json"
OUTPUT_PATH = BUNDLE_DIR / "side_by_side_review.md"


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def _append_receipts(
    lines: list[str], claim_ids: list[str], claims: dict[str, dict], sources: dict[str, dict]
) -> None:
    lines.extend(
        [
            "#### Material claim receipts",
            "",
            "| Claim | Official source and locator | Support status | Uncertainty |",
            "| --- | --- | --- | --- |",
        ]
    )
    for claim_id in claim_ids:
        claim = claims[claim_id]
        source_links = "; ".join(
            f"[{source_id}]({sources[source_id]['url']})" for source_id in claim["source_ids"]
        )
        lines.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in (
                    f"{claim_id}: {claim['claim']}",
                    f"{source_links}; {claim['locator']}",
                    claim["claim_support_status"],
                    claim["uncertainty"] or "None recorded",
                )
            )
            + " |"
        )
    lines.append("")


def _append_field_decisions(lines: list[str], item: dict) -> None:
    fields = [
        "ten_second.headline",
        "ten_second.practical_choice",
        "ten_second.member_action_and_result",
        "thirty_second.prior_baseline",
        "thirty_second.mechanism",
        "thirty_second.affected",
        "thirty_second.scale_or_timing",
        "thirty_second.what_happened_next",
        "two_minute.detail",
        "two_minute.supporter_argument",
        "two_minute.opponent_argument",
        "two_minute.argument_boundary",
        "two_minute.later_history",
        "two_minute.caveats",
        "member_action",
        "claim_receipts",
        "comprehension_answers",
    ]
    lines.extend(
        [
            "#### Field decisions",
            "",
            "| Field | Approve | Reject | Request changes | Notes |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    lines.extend(f"| `{field}` | [ ] | [ ] | [ ] | |" for field in fields)
    lines.extend(["", "Roll decision: [ ] approve [ ] reject [ ] request changes.", ""])


def render(packet: dict, claim_map: dict, source_manifest: dict) -> str:
    claims = {claim["claim_id"]: claim for claim in claim_map["claims"]}
    sources = {source["source_id"]: source for source in source_manifest["sources"]}
    lines = [
        "# Valerie Foushee Economy & Taxes: side-by-side editorial review",
        "",
        f"Content version: `{packet['content_version']}`",
        f"Status: `{packet['editorial_status']}`",
        "",
        "> Candidate copy remains an agent-source-checked machine draft. Human factual review, editorial scoring, reader testing, and approval are pending. The public-field column is a `public_field_availability_proxy`, not an exact runtime rendering.",
        "",
        "## Interpretation candidates",
        "",
    ]
    for item in packet["interpretations"]:
        proposed = item["proposed"]
        two_minute = proposed["two_minute"]
        supporter = two_minute["supporter_argument"]
        opponent = two_minute["opponent_argument"]
        lines.extend(
            [
                f"### House roll {item['roll']} — {item['measure_id']} — {item['stage']}",
                "",
                "| Review surface | Copy |",
                "| --- | --- |",
                f"| Current stored copy | {_cell(item['current_stored_copy'])} |",
                f"| Public field availability proxy | {_cell(item['public_field_availability_proxy']['proxy_text'])} |",
                f"| Proposed 10-second headline | **{_cell(proposed['ten_second']['headline'])}** |",
                f"| Proposed practical choice | {_cell(proposed['ten_second']['practical_choice'])} |",
                f"| Proposed action and result | {_cell(proposed['ten_second']['member_action_and_result'])} |",
                f"| 30-second baseline | {_cell(proposed['thirty_second']['prior_baseline'])} |",
                f"| 30-second mechanism | {_cell(proposed['thirty_second']['mechanism'])} |",
                f"| 30-second affected group | {_cell(proposed['thirty_second']['affected'])} |",
                f"| 30-second scale/timing | {_cell(proposed['thirty_second']['scale_or_timing'])} |",
                f"| What happened next | {_cell(proposed['thirty_second']['what_happened_next'])} |",
                f"| Two-minute detail | {_cell(proposed['two_minute']['detail'])} |",
                f"| Documented supporter argument | **{_cell(supporter['attribution'])}:** {_cell(supporter['argument'])} (`{_cell(supporter['claim_id'])}`) |",
                f"| Documented opponent argument | **{_cell(opponent['attribution'])}:** {_cell(opponent['argument'])} (`{_cell(opponent['claim_id'])}`) |",
                f"| Argument evidence boundary | {_cell(two_minute['argument_boundary'])} |",
                f"| Later history | {_cell(proposed['two_minute']['later_history'])} |",
                f"| Caveats | {_cell('; '.join(proposed['two_minute']['caveats']))} |",
                f"| Verified Foushee action | `{_cell(item['member_action']['recorded'])}` — {_cell(item['member_action']['plain_language'])} |",
                f"| Why materially better | {_cell(item['material_improvement'])} |",
                f"| Unresolved questions | {_cell('; '.join(item['unresolved_questions']) or 'None recorded')} |",
                f"| Confidence / approval | `{item['agent_confidence']}` / `{item['human_approval_status']}` |",
                "",
                "#### Comprehension review",
                "",
                "| Question | Expected answer | Acceptable equivalent | Likely misconception | Supplying field |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for check in item["comprehension"]:
            lines.append(
                "| "
                + " | ".join(
                    _cell(value)
                    for value in (
                        check["question"],
                        check["expected"],
                        "; ".join(check["acceptable"]),
                        check["misconception"],
                        check["field"],
                    )
                )
                + " |"
            )
        lines.append("")
        _append_receipts(lines, proposed["two_minute"]["claim_ids"], claims, sources)
        _append_field_decisions(lines, item)

    lines.extend(["## Ambiguity and procedural controls", ""])
    for item in packet["controls"]:
        lines.extend(
            [
                f"### House roll {item['roll']} — {item['control_type']}",
                "",
                f"- Current stored copy: {item['current_stored_copy'] or 'No substantive interpretation.'}",
                f"- Public field availability proxy: {item['public_field_availability_proxy']['proxy_text']}",
                f"- Known: {item['known']}",
                f"- Still unknown or bounded: {item['substantive_effect_still_unknown']}",
                f"- Why a single policy translation is unsafe: {item['why_single_policy_translation_is_unsafe']}",
                f"- Additional evidence needed: {item['additional_evidence_needed']}",
                f"- Proposed control copy: **{item['proposed_control_copy']}**",
                f"- Verified Foushee action: `{item['member_action']['recorded']}` — {item['member_action']['plain_language']}",
                f"- Why materially better: {item['material_improvement']}",
                f"- Confidence / approval / synthesis: `{item['agent_confidence']}` / `{item['human_approval_status']}` / `{item['issue_synthesis_counting']}`",
                "",
                "Reviewer decision: control copy [ ] approve [ ] reject [ ] request changes; exclusion [ ] approve [ ] reject [ ] request changes.",
                "",
            ]
        )
        _append_receipts(lines, item["claim_ids"], claims, sources)
        lines.extend(
            [
                "| Control field | Approve | Reject | Request changes | Notes |",
                "| --- | --- | --- | --- | --- |",
                "| Known action | [ ] | [ ] | [ ] | |",
                "| Unknown/bounded effect | [ ] | [ ] | [ ] | |",
                "| Safety rationale | [ ] | [ ] | [ ] | |",
                "| Proposed control copy | [ ] | [ ] | [ ] | |",
                "| Claim receipts | [ ] | [ ] | [ ] | |",
                "",
            ]
        )

    lines.extend(
        [
            "## Packet-level decision",
            "",
            "- [ ] Approve all source mappings.",
            "- [ ] Approve policy-episode deduplication.",
            "- [ ] Approve issue-synthesis proposal.",
            "- [ ] Reader protocol completed and results attached.",
            "- [ ] Human editorial scoring completed.",
            "- [ ] Human approval granted in a future authorized workflow.",
            "",
            "Until every required human step is complete, this packet remains `human_approval_pending`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if the checked-in review is stale.")
    args = parser.parse_args()
    packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    claim_map = json.loads(CLAIM_MAP_PATH.read_text(encoding="utf-8"))
    source_manifest = json.loads(SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    rendered = render(packet, claim_map, source_manifest)
    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text(encoding="utf-8") != rendered:
            raise SystemExit(f"stale generated review: {OUTPUT_PATH}")
        return 0
    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
