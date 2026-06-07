from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


FOUSHEE_BIOGUIDE_ID = "F000477"
NDAA_AMENDMENT_ISSUE_FACET = "Defense authorization amendment"


@dataclass(frozen=True)
class HouseRollContext:
    rollcall_number: int
    question: str
    amendment_author: str
    vote_result: str
    member_vote: str | None
    source_url: str


def load_house_roll_context(
    roll_path: Path,
    *,
    member_bioguide_id: str = FOUSHEE_BIOGUIDE_ID,
) -> HouseRollContext:
    root = ElementTree.parse(roll_path).getroot()
    metadata = root.find("./vote-metadata")
    if metadata is None:
        raise ValueError(f"{roll_path} is missing vote metadata")

    rollcall_number = int(_require_text(metadata.find("rollcall-num")))
    member_vote = None
    for recorded_vote in root.findall("./vote-data/recorded-vote"):
        legislator = recorded_vote.find("legislator")
        if legislator is not None and legislator.attrib.get("name-id") == member_bioguide_id:
            member_vote = _normalize_member_vote(recorded_vote.findtext("vote"))
            break

    return HouseRollContext(
        rollcall_number=rollcall_number,
        question=_require_text(metadata.find("vote-question")),
        amendment_author=_require_text(metadata.find("amendment-author")),
        vote_result=_require_text(metadata.find("vote-result")),
        member_vote=member_vote,
        source_url=f"https://clerk.house.gov/evs/2025/roll{rollcall_number:03d}.xml",
    )


def build_ndaa_amendment_interpretation_candidate(
    source_packet: dict[str, Any],
    roll_context: HouseRollContext,
    *,
    member_name: str = "Foushee",
) -> dict[str, Any]:
    amendment = source_packet.get("amendment") or {}
    roll_call_id = source_packet.get("roll_call_id")
    purpose = _clean_sentence(amendment.get("purpose") or amendment.get("description"))
    action_clear = roll_context.question.strip().lower() in {
        "on agreeing to the amendment",
        "on agreeing to amendment",
    }
    vote_clear = roll_context.member_vote in {"yea", "nay"}
    amendment_clear = bool(purpose and amendment.get("matched_from_roll_description"))

    if not (action_clear and vote_clear and amendment_clear):
        return {
            "roll_call_id": roll_call_id,
            "rollcall_number": roll_context.rollcall_number,
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

    vote_word = "Yea" if roll_context.member_vote == "yea" else "Nay"
    member_vote_meaning = "supported" if roll_context.member_vote == "yea" else "opposed"
    result_sentence = _format_result_sentence(roll_context.vote_result)
    amendment_clause = _format_amendment_clause(purpose)

    return {
        "roll_call_id": roll_call_id,
        "rollcall_number": roll_context.rollcall_number,
        "matched_amendment_id": amendment.get("amendment_id"),
        "amendment_number": amendment.get("amendment_number"),
        "amendment_label": amendment.get("amendment_label"),
        "amendment_sponsor": amendment.get("sponsor_text"),
        "amendment_purpose": purpose,
        "roll_call_question": roll_context.question,
        "vote_result": roll_context.vote_result,
        "member_vote": roll_context.member_vote,
        "support_position": "yea",
        "oppose_position": "nay",
        "interpretation_status": "interpreted",
        "interpretation_status_recommendation": "reviewed_interpretation",
        "interpretation_version": "interpretation_v1",
        "classification_version": "v1",
        "confidence": "high",
        "issue_facet": NDAA_AMENDMENT_ISSUE_FACET,
        "source_url": roll_context.source_url,
        "source_basis": [
            f"House Clerk roll-call question, amendment author, result, and {member_name} recorded vote for Roll {roll_context.rollcall_number}",
            f"Congress.gov amendment record {amendment.get('amendment_id')} purpose/description for H.R. 3838",
        ],
        "plain_english_summary": (
            "This vote was on whether to agree to an amendment to H.R. 3838, the FY2026 defense authorization bill, "
            f"that {amendment_clause}."
        ),
        "what_happened": (
            f"The House voted on whether to agree to {roll_context.amendment_author}. "
            f"The amendment {amendment_clause}. {result_sentence}"
        ),
        "why_it_mattered": (
            "The vote decided whether that amendment would be adopted into the House's FY2026 defense authorization bill. "
            "It was not final passage of the full NDAA."
        ),
        "member_vote_context": (
            f"{member_name} voted {vote_word}, meaning she {member_vote_meaning} agreeing to this amendment."
        ),
        "what_not_to_infer": (
            "Do not infer motive, ideology, character, a voting recommendation, or a broad position on national security from this amendment vote. "
            "This was an amendment vote, not final passage of H.R. 3838."
        ),
        "yea_meaning": "A Yea vote supported agreeing to the amendment.",
        "nay_meaning": "A Nay vote opposed agreeing to the amendment.",
        "policy_effect": f"If adopted, the amendment {amendment_clause}.",
        "uncertainty_note": None,
        "interpretation_reason": (
            "Manual review used the House Clerk roll-call action and matched Congress.gov amendment purpose/description for a source-grounded amendment interpretation."
        ),
    }


def candidate_to_manual_interpretation(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "roll_call_id": candidate["roll_call_id"],
        "classification_version": candidate.get("classification_version", "v1"),
        "interpretation_version": candidate.get("interpretation_version", "interpretation_v1"),
        "interpretation_status": candidate["interpretation_status"],
        "plain_english_summary": candidate.get("plain_english_summary"),
        "yea_meaning": candidate.get("yea_meaning"),
        "nay_meaning": candidate.get("nay_meaning"),
        "policy_effect": candidate.get("policy_effect"),
        "issue_facet": candidate.get("issue_facet"),
        "support_position": candidate.get("support_position"),
        "oppose_position": candidate.get("oppose_position"),
        "confidence": candidate.get("confidence"),
        "source_basis": candidate.get("source_basis", []),
        "source_url": candidate.get("source_url"),
        "uncertainty_note": candidate.get("uncertainty_note"),
        "interpretation_reason": candidate.get("interpretation_reason"),
        "what_happened": candidate.get("what_happened"),
        "why_it_mattered": candidate.get("why_it_mattered"),
        "member_vote_context": candidate.get("member_vote_context"),
        "what_not_to_infer": candidate.get("what_not_to_infer"),
    }


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
            return _polish_clause(replacement + subject[len(prefix):])
    if subject.startswith("to "):
        return _polish_clause("would " + subject[len("to "):])
    return _polish_clause(subject)


def _polish_clause(clause: str) -> str:
    return (
        clause.replace(", and requires ", ", and would require ")
        .replace(" and requires ", " and would require ")
    )


def _format_result_sentence(vote_result: str) -> str:
    normalized = vote_result.strip().lower()
    if normalized == "agreed to":
        return "The amendment was agreed to."
    if normalized == "failed":
        return "The amendment failed."
    return f"The recorded result was {vote_result}."


def _uncertainty_note(*, action_clear: bool, vote_clear: bool, amendment_clear: bool) -> str:
    missing = []
    if not action_clear:
        missing.append("the roll-call action does not clearly show an amendment-adoption vote")
    if not vote_clear:
        missing.append("the member's recorded vote is missing or not a Yea/Nay vote")
    if not amendment_clear:
        missing.append("the matched amendment purpose or description is missing or uncertain")
    return "The row remains limited because " + "; ".join(missing) + "."


def _normalize_member_vote(value: str | None) -> str | None:
    normalized = str(value or "").strip().lower()
    if normalized in {"aye", "yea", "yes"}:
        return "yea"
    if normalized in {"no", "nay"}:
        return "nay"
    if normalized == "present":
        return "present"
    if normalized == "not voting":
        return "not_voting"
    return None


def _clean_sentence(value: Any) -> str:
    text = " ".join(str(value or "").split())
    if text and not text.endswith("."):
        return text + "."
    return text


def _require_text(element: ElementTree.Element | None) -> str:
    if element is None or element.text is None or not element.text.strip():
        raise ValueError("Expected non-empty XML text")
    return element.text.strip()
