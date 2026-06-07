import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.etl.interpret import INTERPRETATION_VERSION
from app.etl.source_packets import (
    SourcePacketTarget,
    build_congressgov_source_packet,
    load_default_congressgov_cache,
    parse_house_amendment_hint,
)


WEAK_INTERPRETATION_STATUSES = {None, "", "ambiguous", "insufficient_evidence"}
AMENDMENT_ACTION_QUESTIONS = {
    "on agreeing to the amendment",
    "on agreeing to amendment",
    "on the amendment",
}


def load_packet_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_amendment_heavy_weak_sections(
    packets: list[dict[str, Any]],
    *,
    min_amendment_rows: int = 3,
) -> list[dict[str, Any]]:
    sections: dict[tuple[str, int, str, int], list[dict[str, Any]]] = defaultdict(list)
    for packet in packets:
        if not _is_weak_amendment_packet(packet):
            continue
        official_text = packet.get("official_text") or {}
        try:
            key = (
                str(packet.get("primary_domain") or "UNKNOWN"),
                int(official_text["bill_congress"]),
                str(official_text["bill_type"]).lower(),
                int(official_text["bill_number"]),
            )
        except (KeyError, TypeError, ValueError):
            continue
        sections[key].append(packet)

    summaries = []
    for (domain, bill_congress, bill_type, bill_number), rows in sections.items():
        if len(rows) < min_amendment_rows:
            continue
        first_text = rows[0].get("official_text") or {}
        rows_sorted = sorted(rows, key=lambda item: int(item.get("rollcall_number") or 0))
        summaries.append(
            {
                "section_id": f"{domain}:{bill_congress}:{bill_type}:{bill_number}",
                "primary_domain": domain,
                "bill": {
                    "bill_id": _format_bill_id(bill_congress, bill_type, bill_number),
                    "congress": bill_congress,
                    "bill_type": bill_type,
                    "bill_number": bill_number,
                    "title": first_text.get("bill_title"),
                },
                "weak_amendment_rows": len(rows_sorted),
                "roll_calls": [
                    {
                        "roll_call_id": row.get("roll_call_id"),
                        "rollcall_number": row.get("rollcall_number"),
                        "question": (row.get("official_text") or {}).get("question"),
                        "description": (row.get("official_text") or {}).get("description"),
                        "current_interpretation_status": _current_status(row),
                    }
                    for row in rows_sorted
                ],
                "recommended_next_step": "Build source packets and review-only candidate interpretations; do not import without explicit approval.",
            }
        )

    return sorted(
        summaries,
        key=lambda section: (-int(section["weak_amendment_rows"]), section["section_id"]),
    )


def build_review_batch_from_packets(
    packets: list[dict[str, Any]],
    *,
    congress_cache: dict[tuple[int, str, int], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    cache = congress_cache if congress_cache is not None else load_default_congressgov_cache()
    amendment_packets = [packet for packet in packets if _is_weak_amendment_packet(packet)]
    source_packets = [
        build_congressgov_source_packet(_source_packet_target_from_manual_packet(packet), congress_cache=cache)
        for packet in amendment_packets
    ]
    manual_packets_by_roll = {packet.get("roll_call_id"): packet for packet in amendment_packets}
    candidates = [
        build_amendment_interpretation_candidate(
            source_packet,
            manual_packet=manual_packets_by_roll.get(source_packet.get("roll_call_id"), {}),
        )
        for source_packet in source_packets
    ]

    return {
        "schema_version": "amendment_companion_enrichment_phase2_v1",
        "workflow_boundary": [
            "Offline review artifact only.",
            "No production data is written by this workflow.",
            "Candidate interpretations require human review and a separate explicit import approval.",
        ],
        "section_candidates": find_amendment_heavy_weak_sections(packets),
        "source_packets": source_packets,
        "candidate_interpretations": candidates,
    }


def build_amendment_interpretation_candidate(
    source_packet: dict[str, Any],
    *,
    manual_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manual_packet = manual_packet or {}
    official_text = manual_packet.get("official_text") or {}
    vote_context = manual_packet.get("vote_context") or {}
    amendment = source_packet.get("amendment") or {}

    roll_call_id = source_packet.get("roll_call_id")
    rollcall_number = source_packet.get("rollcall_number")
    question = str(source_packet.get("vote_question") or official_text.get("question") or "")
    member_vote = _normalize_member_vote(vote_context.get("member_vote"))
    purpose = _clean_sentence(amendment.get("purpose") or amendment.get("description"))
    action_clear = _is_amendment_action_question(question)
    vote_clear = member_vote in {"yea", "nay"}
    amendment_clear = bool(purpose and amendment.get("matched_from_roll_description"))
    bill_label = _format_public_bill_label(source_packet.get("bill") or official_text)

    if not (action_clear and vote_clear and amendment_clear):
        return {
            "roll_call_id": roll_call_id,
            "rollcall_number": rollcall_number,
            "matched_amendment_id": amendment.get("amendment_id"),
            "interpretation_status": "insufficient_evidence",
            "interpretation_status_recommendation": "keep_limited",
            "support_position": None,
            "oppose_position": None,
            "source_basis": [],
            "uncertainty_note": _uncertainty_note(
                action_clear=action_clear,
                vote_clear=vote_clear,
                amendment_clear=amendment_clear,
            ),
        }

    vote_word = "Yea" if member_vote == "yea" else "Nay"
    member_vote_meaning = "supported" if member_vote == "yea" else "opposed"
    result_sentence = _format_result_sentence(vote_context.get("final_result"))
    amendment_clause = _format_amendment_clause(purpose)
    amendment_label = _first_nonempty(amendment.get("amendment_label"), official_text.get("description"), "the amendment")
    member_name = _first_nonempty(manual_packet.get("member_name"), vote_context.get("member_name"), "The selected member")

    return {
        "roll_call_id": roll_call_id,
        "rollcall_number": rollcall_number,
        "matched_amendment_id": amendment.get("amendment_id"),
        "amendment_number": amendment.get("amendment_number"),
        "amendment_label": amendment.get("amendment_label"),
        "amendment_sponsor": amendment.get("sponsor_text"),
        "amendment_purpose": purpose,
        "roll_call_question": question,
        "vote_result": vote_context.get("final_result"),
        "member_vote": member_vote,
        "support_position": "yea",
        "oppose_position": "nay",
        "interpretation_status": "interpreted",
        "interpretation_status_recommendation": "review_candidate_only",
        "interpretation_version": INTERPRETATION_VERSION,
        "classification_version": manual_packet.get("classification_version") or "v1",
        "confidence": "high",
        "issue_facet": _first_nonempty(source_packet.get("issue_facet"), "Amendment vote"),
        "source_url": source_packet.get("vote_source_url") or official_text.get("source_url"),
        "source_basis": [
            f"Official roll-call question and recorded member vote for Roll {rollcall_number}",
            f"Matched Congress.gov amendment record {amendment.get('amendment_id')} purpose/description for {bill_label}",
        ],
        "plain_english_summary": (
            f"This vote was on whether to agree to an amendment to {bill_label} that {amendment_clause}. "
            f"{member_name} voted {vote_word}, meaning they {member_vote_meaning} agreeing to this amendment."
        ),
        "what_happened": (
            f"The chamber voted on whether to agree to {amendment_label}. "
            f"The amendment {amendment_clause}. {result_sentence}"
        ),
        "why_it_mattered": (
            f"The vote decided whether that amendment would be adopted into {bill_label}. "
            f"It was not final passage of {bill_label}."
        ),
        "member_vote_context": (
            f"{member_name} voted {vote_word}, meaning they {member_vote_meaning} agreeing to this amendment."
        ),
        "what_not_to_infer": (
            "Do not infer motive, ideology, character, a voting recommendation, or a broad position on the issue from this amendment vote. "
            f"This was an amendment vote, not final passage of {bill_label}."
        ),
        "yea_meaning": "A Yea vote supported agreeing to the amendment.",
        "nay_meaning": "A Nay vote opposed agreeing to the amendment.",
        "policy_effect": f"If adopted, the amendment {amendment_clause}.",
        "uncertainty_note": None,
        "interpretation_reason": (
            "Review candidate used the official roll-call action and matched Congress.gov amendment purpose/description. "
            "It is not an import-ready production interpretation until separately reviewed."
        ),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _is_weak_amendment_packet(packet: dict[str, Any]) -> bool:
    if _current_status(packet) not in WEAK_INTERPRETATION_STATUSES:
        return False
    official_text = packet.get("official_text") or {}
    question = str(official_text.get("question") or "")
    description = str(official_text.get("description") or "")
    vote_context = packet.get("vote_context") or {}
    return (
        _is_amendment_action_question(question)
        or str(vote_context.get("vote_type") or "").lower() == "amendment"
        or bool(parse_house_amendment_hint(description).get("amendment_number"))
    )


def _source_packet_target_from_manual_packet(packet: dict[str, Any]) -> SourcePacketTarget:
    official_text = packet.get("official_text") or {}
    return SourcePacketTarget(
        roll_call_id=int(packet["roll_call_id"]),
        chamber=str(packet["chamber"]),
        congress=int(packet["congress"]),
        rollcall_number=int(packet["rollcall_number"]),
        question=str(official_text.get("question") or ""),
        description=str(official_text.get("description") or ""),
        source_url=official_text.get("source_url"),
        bill_congress=int(official_text["bill_congress"]),
        bill_type=str(official_text["bill_type"]).lower(),
        bill_number=int(official_text["bill_number"]),
        bill_title=str(official_text.get("bill_title") or ""),
        bill_summary=official_text.get("bill_summary"),
        primary_domain=packet.get("primary_domain"),
        interpretation_status=_current_status(packet),
        issue_facet=(packet.get("current_interpretation") or {}).get("issue_facet"),
        vote_type=(packet.get("vote_context") or {}).get("vote_type"),
    )


def _current_status(packet: dict[str, Any]) -> str | None:
    current = packet.get("current_interpretation") or {}
    status = current.get("interpretation_status")
    if status is None:
        return None
    return str(status)


def _is_amendment_action_question(question: str) -> bool:
    return " ".join(question.lower().split()) in AMENDMENT_ACTION_QUESTIONS


def _format_public_bill_label(bill: dict[str, Any]) -> str:
    bill_id = bill.get("bill_id")
    if bill_id:
        parts = str(bill_id).split(":")
        if len(parts) == 3:
            return f"{parts[1].upper()}. {parts[2]}"
    bill_type = bill.get("bill_type")
    bill_number = bill.get("bill_number")
    if bill_type and bill_number:
        return f"{str(bill_type).upper()}. {bill_number}"
    title = bill.get("title") or bill.get("bill_title")
    return str(title or "the bill")


def _format_bill_id(congress: int, bill_type: str, bill_number: int) -> str:
    return f"{congress}:{bill_type.lower()}:{bill_number}"


def _format_amendment_clause(purpose: str) -> str:
    subject = _format_amendment_subject(purpose)
    if subject.startswith("would "):
        return subject
    verb_rewrites = {
        "repeals ": "would repeal ",
        "prohibits ": "would prohibit ",
        "requires ": "would require ",
        "require ": "would require ",
        "eliminates ": "would eliminate ",
        "increases ": "would increase ",
        "restricts ": "would restrict ",
        "modifies ": "would modify ",
        "strike ": "would strike ",
        "prohibit ": "would prohibit ",
        "ban ": "would ban ",
    }
    for prefix, replacement in verb_rewrites.items():
        if subject.startswith(prefix):
            return replacement + subject[len(prefix):]
    if subject.startswith("to "):
        return "would " + subject[len("to "):]
    return subject


def _format_amendment_subject(purpose: str) -> str:
    lowered = purpose[:1].lower() + purpose[1:]
    if lowered.startswith("an amendment numbered "):
        marker = " to "
        marker_index = lowered.find(marker)
        if marker_index >= 0:
            return lowered[marker_index + len(marker):].rstrip(".")
    for prefix in ("amendment sought to ", "amendment would ", "amendment "):
        if lowered.startswith(prefix):
            return lowered[len(prefix):].rstrip(".")
    return lowered.rstrip(".")


def _format_result_sentence(final_result: Any) -> str:
    normalized = str(final_result or "").strip().lower()
    if normalized in {"agreed to", "passed", "passage"}:
        return "The amendment was agreed to."
    if normalized in {"failed", "rejected"}:
        return "The amendment failed."
    if normalized:
        return f"The recorded result was {final_result}."
    return "The available packet does not state the final result."


def _uncertainty_note(*, action_clear: bool, vote_clear: bool, amendment_clear: bool) -> str:
    missing = []
    if not action_clear:
        missing.append("the roll-call action does not clearly show an amendment-adoption vote")
    if not vote_clear:
        missing.append("the member's recorded vote is missing or not a Yea/Nay vote")
    if not amendment_clear:
        missing.append("the matched amendment purpose or description is missing or uncertain")
    return "The row remains limited because " + "; ".join(missing) + "."


def _normalize_member_vote(value: Any) -> str | None:
    normalized = str(value or "").strip().lower()
    if normalized in {"aye", "yea", "yes"}:
        return "yea"
    if normalized in {"no", "nay"}:
        return "nay"
    if normalized in {"present", "not_voting"}:
        return normalized
    if normalized == "not voting":
        return "not_voting"
    return None


def _clean_sentence(value: Any) -> str:
    text = " ".join(str(value or "").split())
    if text and not text.endswith("."):
        return text + "."
    return text


def _first_nonempty(*values: Any) -> Any:
    for value in values:
        if value is not None and str(value).strip():
            return value
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Build review-only amendment companion enrichment artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover_parser = subparsers.add_parser("discover")
    discover_parser.add_argument("--packets", required=True)
    discover_parser.add_argument("--output", required=True)
    discover_parser.add_argument("--min-amendment-rows", type=int, default=3)

    build_parser = subparsers.add_parser("build-review-batch")
    build_parser.add_argument("--packets", required=True)
    build_parser.add_argument("--output", required=True)

    args = parser.parse_args()
    payload = load_packet_payload(Path(args.packets))
    packets = payload.get("packets") or []

    if args.command == "discover":
        result = {
            "schema_version": "amendment_companion_discovery_v1",
            "sections": find_amendment_heavy_weak_sections(
                packets,
                min_amendment_rows=args.min_amendment_rows,
            ),
            "workflow_boundary": "Discovery only; no source fetch, production write, import, or interpretation promotion.",
        }
    else:
        result = build_review_batch_from_packets(packets)

    write_json(Path(args.output), result)
    print(json.dumps({"output_path": args.output, "section_count": len(result.get("sections", result.get("section_candidates", [])))}, sort_keys=True))


if __name__ == "__main__":
    main()
