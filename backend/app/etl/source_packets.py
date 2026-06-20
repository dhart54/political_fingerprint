import re
from dataclasses import dataclass
from typing import Any

from app.etl.amendment_evidence import parse_house_amendment_identity
from app.etl.fetch_sources import CONGRESS_BILL_CACHE_DIR
from app.etl.congress_adapter import load_congress_bill_cache


REVIEW_CLASSIFICATIONS = {
    "likely_upgrade_candidate",
    "still_limited",
    "no_useful_context_found",
    "source_missing_or_unavailable",
}


@dataclass(frozen=True)
class SourcePacketTarget:
    roll_call_id: int
    chamber: str
    congress: int
    rollcall_number: int
    question: str
    description: str
    source_url: str | None
    bill_congress: int
    bill_type: str
    bill_number: int
    bill_title: str
    bill_summary: str | None = None
    primary_domain: str | None = None
    interpretation_status: str | None = None
    issue_facet: str | None = None
    vote_type: str | None = None


def load_default_congressgov_cache() -> dict[tuple[int, str, int], dict[str, Any]]:
    return load_congress_bill_cache(CONGRESS_BILL_CACHE_DIR)


def build_congressgov_source_packet(
    target: SourcePacketTarget | dict[str, Any],
    *,
    congress_cache: dict[tuple[int, str, int], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    row = _coerce_target(target)
    cache = congress_cache if congress_cache is not None else load_default_congressgov_cache()
    bill_key = (row.bill_congress, row.bill_type.lower(), row.bill_number)
    cached_bill = cache.get(bill_key)
    amendment_hint = parse_house_amendment_hint(row.description)

    packet = {
        "roll_call_id": row.roll_call_id,
        "rollcall_number": row.rollcall_number,
        "chamber": row.chamber,
        "congress": row.congress,
        "vote_question": row.question,
        "vote_description": row.description,
        "vote_source_url": row.source_url,
        "primary_domain": row.primary_domain,
        "interpretation_status": row.interpretation_status,
        "issue_facet": row.issue_facet,
        "vote_type": row.vote_type,
        "bill": {
            "bill_id": _format_bill_id(row.bill_congress, row.bill_type, row.bill_number),
            "congress": row.bill_congress,
            "bill_type": row.bill_type.lower(),
            "bill_number": row.bill_number,
            "title": row.bill_title,
            "summary": _first_nonempty(
                cached_bill.get("summary") if cached_bill else None,
                row.bill_summary,
            ),
            "legislation_url": cached_bill.get("legislation_url") if cached_bill else None,
            "latest_action": cached_bill.get("latest_action") if cached_bill else None,
        },
        "amendment": {
            "amendment_id": None,
            "amendment_number": amendment_hint.get("amendment_number"),
            "amendment_label": amendment_hint.get("amendment_label"),
            "sponsor_text": amendment_hint.get("sponsor_text"),
            "purpose": None,
            "description": None,
            "latest_action": None,
            "type": None,
            "source_url": None,
            "match_confidence": None,
            "match_reason": None,
            "matched_from_roll_description": False,
        },
        "source_context": {
            "actions": [],
            "text_versions": [],
            "amendments": [],
            "committees": [],
            "committee_reports": [],
            "cbo_cost_estimates": [],
            "congressgov_source_urls": [],
            "cache_metadata": {
                "cache_key": _format_cache_key(row.bill_congress, row.bill_type, row.bill_number),
                "cache_hit": cached_bill is not None,
                "retrieval_timestamp": None,
            },
        },
        "source_availability": {},
        "review_classification": "source_missing_or_unavailable",
        "review_notes": [],
    }

    if cached_bill is None:
        packet["review_notes"].append("No Congress.gov bill cache record was available for this bill reference.")
        packet["source_availability"] = _build_source_availability(packet)
        return packet

    packet["source_context"]["actions"] = _summarize_actions(cached_bill.get("actions") or [], cached_bill.get("latest_action"))
    packet["source_context"]["text_versions"] = _summarize_text_versions(cached_bill.get("text_versions") or [])
    packet["source_context"]["amendments"] = _summarize_amendments(cached_bill.get("amendments") or [])
    packet["source_context"]["committees"] = _summarize_committees(cached_bill.get("committees") or [])
    packet["source_context"]["committee_reports"] = _summarize_committee_reports(cached_bill.get("committee_reports") or [])
    packet["source_context"]["cbo_cost_estimates"] = _summarize_cbo(cached_bill.get("cbo_cost_estimates") or [])
    packet["source_context"]["congressgov_source_urls"] = _collect_source_urls(cached_bill, packet)

    matched_amendment = find_matching_amendment(
        packet["source_context"]["amendments"],
        amendment_number=amendment_hint.get("amendment_number"),
        sponsor_text=amendment_hint.get("sponsor_text"),
    )
    if matched_amendment:
        packet["amendment"].update(
            {
                "amendment_id": matched_amendment.get("amendment_id"),
                "purpose": matched_amendment.get("purpose"),
                "description": matched_amendment.get("description"),
                "latest_action": matched_amendment.get("latest_action"),
                "type": matched_amendment.get("type"),
                "source_url": matched_amendment.get("source_url"),
                "match_confidence": matched_amendment.get("match_confidence"),
                "match_reason": matched_amendment.get("match_reason"),
                "matched_from_roll_description": True,
            }
        )

    packet["source_availability"] = _build_source_availability(packet)
    packet["review_classification"] = classify_source_packet(packet)
    packet["review_notes"] = build_review_notes(packet)
    return packet


def classify_source_packet(packet: dict[str, Any]) -> str:
    availability = packet.get("source_availability") or {}
    if not availability.get("bill_cache_hit"):
        return "source_missing_or_unavailable"

    if availability.get("matched_amendment_purpose_or_description"):
        return "likely_upgrade_candidate"

    if availability.get("bill_summary") or availability.get("actions") or availability.get("amendment_subresource_reference"):
        return "still_limited"

    return "no_useful_context_found"


def build_review_notes(packet: dict[str, Any]) -> list[str]:
    availability = packet.get("source_availability") or {}
    notes = []
    if packet.get("review_classification") == "likely_upgrade_candidate":
        notes.append("A Congress.gov amendment record appears to match the roll-call amendment hint and includes purpose or description text.")
        notes.append("This is a review candidate only; interpretation_status is not changed by this source packet.")
    elif availability.get("amendment_subresource_reference") and not availability.get("matched_amendment"):
        notes.append("Congress.gov indicates amendment records exist, but no fetched amendment detail matched this roll-call description.")
        notes.append("The row should remain limited until amendment-specific text or purpose is available.")
    elif availability.get("bill_summary"):
        notes.append("Bill-level summary is available, but bill-level context alone does not explain this amendment's practical effect.")
    elif not availability.get("bill_cache_hit"):
        notes.append("No Congress.gov cache record was found for this bill.")
    else:
        notes.append("Available Congress.gov context does not provide enough practical detail for review.")
    return notes


def parse_house_amendment_hint(description: str | None) -> dict[str, str | None]:
    identity = parse_house_amendment_identity(description=description, congress=0)
    return {
        "amendment_number": identity.amendment_number,
        "amendment_label": identity.label,
        "sponsor_text": identity.sponsor_text,
    }


def find_matching_amendment(
    amendments: list[dict[str, Any]],
    *,
    amendment_number: str | None,
    sponsor_text: str | None,
) -> dict[str, Any] | None:
    if not amendments:
        return None

    if amendment_number:
        printed_number_matches = [
            amendment
            for amendment in amendments
            if str(amendment.get("house_amendment_number") or "") == amendment_number
        ]
        if len(printed_number_matches) == 1:
            return _with_match_metadata(
                printed_number_matches[0],
                confidence="high",
                reason="Matched the printed House amendment number from the roll-call description to the Congress.gov amendment description.",
            )

        for amendment in amendments:
            if str(amendment.get("number") or "") == amendment_number:
                return _with_match_metadata(
                    amendment,
                    confidence="medium",
                    reason="Matched the roll-call amendment number to the Congress.gov amendment record number.",
                )

    if sponsor_text:
        sponsor_lower = sponsor_text.lower()
        for amendment in amendments:
            haystack = " ".join(
                str(value or "")
                for value in (
                    amendment.get("sponsor"),
                    amendment.get("description"),
                    amendment.get("purpose"),
                )
            ).lower()
            if sponsor_lower and sponsor_lower in haystack:
                return _with_match_metadata(
                    amendment,
                    confidence="low",
                    reason="Matched sponsor text from the roll-call description to Congress.gov amendment text.",
                )

    return None


def _summarize_actions(actions: list[Any], latest_action: Any) -> list[dict[str, Any]]:
    summarized = []
    for action in actions[:8]:
        if isinstance(action, dict):
            summarized.append(
                {
                    "action_date": action.get("actionDate") or action.get("action_date"),
                    "text": action.get("text") or action.get("actionCode"),
                    "source_url": action.get("url"),
                }
            )
    if not summarized and isinstance(latest_action, dict):
        summarized.append(
            {
                "action_date": latest_action.get("action_date") or latest_action.get("actionDate"),
                "text": latest_action.get("text"),
                "source_url": latest_action.get("url"),
            }
        )
    return summarized


def _summarize_text_versions(text_versions: list[Any]) -> list[dict[str, Any]]:
    summarized = []
    for version in text_versions[:6]:
        if not isinstance(version, dict):
            continue
        formats = [
            {
                "type": item.get("type"),
                "url": item.get("url"),
            }
            for item in version.get("formats", [])
            if isinstance(item, dict)
        ]
        summarized.append(
            {
                "date": version.get("date"),
                "type": version.get("type"),
                "formats": formats,
            }
        )
    return summarized


def _summarize_amendments(amendments: list[Any]) -> list[dict[str, Any]]:
    summarized = []
    for amendment in amendments[:50]:
        if not isinstance(amendment, dict):
            continue
        amendment_id = _format_amendment_id(amendment)
        summarized.append(
            {
                "amendment_id": amendment_id,
                "number": _first_nonempty(amendment.get("number"), amendment.get("amendmentNumber")),
                "house_amendment_number": _extract_house_amendment_number(amendment),
                "purpose": amendment.get("purpose"),
                "description": _first_nonempty(amendment.get("description"), amendment.get("title")),
                "latest_action": _extract_latest_amendment_action(amendment),
                "type": _first_nonempty(amendment.get("type"), amendment.get("amendmentType")),
                "sponsor": _extract_sponsor(amendment),
                "source_url": amendment.get("url"),
            }
        )
    return summarized


def _summarize_committees(committees: list[Any]) -> list[dict[str, Any]]:
    summarized = []
    for committee in committees[:12]:
        if isinstance(committee, dict):
            summarized.append(
                {
                    "name": committee.get("name"),
                    "system_code": committee.get("systemCode"),
                    "chamber": committee.get("chamber"),
                    "source_url": committee.get("url"),
                }
            )
    return summarized


def _summarize_committee_reports(reports: list[Any]) -> list[dict[str, Any]]:
    summarized = []
    for report in reports[:8]:
        if isinstance(report, dict):
            summarized.append(
                {
                    "citation": report.get("citation"),
                    "source_url": report.get("url"),
                }
            )
    return summarized


def _summarize_cbo(estimates: list[Any]) -> list[dict[str, Any]]:
    summarized = []
    for estimate in estimates[:8]:
        if isinstance(estimate, dict):
            summarized.append(
                {
                    "title": estimate.get("title"),
                    "description": estimate.get("description"),
                    "pub_date": estimate.get("pubDate") or estimate.get("pub_date"),
                    "source_url": estimate.get("url"),
                }
            )
    return summarized


def _build_source_availability(packet: dict[str, Any]) -> dict[str, bool]:
    bill = packet.get("bill") or {}
    context = packet.get("source_context") or {}
    amendment = packet.get("amendment") or {}
    source_urls = context.get("congressgov_source_urls") or []
    subresource_urls = {item.get("source_type"): item.get("url") for item in source_urls if isinstance(item, dict)}
    matched_amendment_text = bool(amendment.get("purpose") or amendment.get("description"))
    return {
        "bill_cache_hit": bool(context.get("cache_metadata", {}).get("cache_hit")),
        "bill_summary": bool(bill.get("summary")),
        "actions": bool(context.get("actions")),
        "text_versions": bool(context.get("text_versions")),
        "amendment_records": bool(context.get("amendments")),
        "amendment_subresource_reference": bool(subresource_urls.get("amendments")),
        "matched_amendment": bool(amendment.get("matched_from_roll_description")),
        "matched_amendment_purpose_or_description": matched_amendment_text,
        "committees": bool(context.get("committees")),
        "committee_reports": bool(context.get("committee_reports")),
        "cbo_cost_estimates": bool(context.get("cbo_cost_estimates")),
        "congressgov_source_urls": bool(source_urls),
    }


def _collect_source_urls(cached_bill: dict[str, Any], packet: dict[str, Any]) -> list[dict[str, str]]:
    urls = []
    if cached_bill.get("legislation_url"):
        urls.append({"source_type": "congressgov_bill", "url": cached_bill["legislation_url"]})

    for source_type, metadata in (cached_bill.get("source_subresources") or {}).items():
        if isinstance(metadata, dict) and metadata.get("url"):
            urls.append({"source_type": source_type, "url": str(metadata["url"])})

    for collection_name, source_type in (
        ("amendments", "congressgov_amendment"),
        ("committee_reports", "committee_report"),
        ("cbo_cost_estimates", "cbo_cost_estimate"),
    ):
        for item in packet.get("source_context", {}).get(collection_name, []):
            if isinstance(item, dict) and item.get("source_url"):
                urls.append({"source_type": source_type, "url": str(item["source_url"])})

    seen = set()
    unique_urls = []
    for item in urls:
        key = (item["source_type"], item["url"])
        if key in seen:
            continue
        seen.add(key)
        unique_urls.append(item)
    return unique_urls


def _coerce_target(target: SourcePacketTarget | dict[str, Any]) -> SourcePacketTarget:
    if isinstance(target, SourcePacketTarget):
        return target
    return SourcePacketTarget(
        roll_call_id=int(target["roll_call_id"]),
        chamber=str(target["chamber"]),
        congress=int(target["congress"]),
        rollcall_number=int(target["rollcall_number"]),
        question=str(target.get("question") or ""),
        description=str(target.get("description") or ""),
        source_url=target.get("source_url"),
        bill_congress=int(target["bill_congress"]),
        bill_type=str(target["bill_type"]).lower(),
        bill_number=int(target["bill_number"]),
        bill_title=str(target.get("bill_title") or target.get("title") or ""),
        bill_summary=target.get("bill_summary") or target.get("summary"),
        primary_domain=target.get("primary_domain") or target.get("domain"),
        interpretation_status=target.get("interpretation_status") or target.get("status"),
        issue_facet=target.get("issue_facet"),
        vote_type=target.get("vote_type"),
    )


def _format_bill_id(congress: int, bill_type: str, bill_number: int) -> str:
    return f"{congress}:{bill_type.lower()}:{bill_number}"


def _format_cache_key(congress: int, bill_type: str, bill_number: int) -> str:
    return f"{congress}_{bill_type.lower()}_{bill_number}.json"


def _format_amendment_id(amendment: dict[str, Any]) -> str | None:
    congress = amendment.get("congress")
    amendment_type = amendment.get("type") or amendment.get("amendmentType")
    number = amendment.get("number") or amendment.get("amendmentNumber")
    if congress and amendment_type and number:
        return f"{congress}:{str(amendment_type).lower()}:{number}"
    return amendment.get("amendment_id")


def _extract_house_amendment_number(amendment: dict[str, Any]) -> str | None:
    for value in (amendment.get("description"), amendment.get("purpose"), amendment.get("title")):
        match = re.search(
            r"(?:Amendment\s+No\.|amendment\s+numbered)\s*(\d+)",
            str(value or ""),
            re.IGNORECASE,
        )
        if match:
            return match.group(1)
    return None


def _extract_latest_amendment_action(amendment: dict[str, Any]) -> dict[str, Any] | None:
    latest_action = amendment.get("latestAction") or amendment.get("latest_action")
    if not isinstance(latest_action, dict):
        return None
    return {
        "action_date": latest_action.get("actionDate") or latest_action.get("action_date"),
        "action_time": latest_action.get("actionTime") or latest_action.get("action_time"),
        "text": latest_action.get("text"),
    }


def _extract_sponsor(amendment: dict[str, Any]) -> str | None:
    sponsor = amendment.get("sponsor")
    if isinstance(sponsor, dict):
        return _first_nonempty(sponsor.get("fullName"), sponsor.get("name"), sponsor.get("directOrderName"))
    if sponsor:
        return str(sponsor)
    sponsors = amendment.get("sponsors")
    if isinstance(sponsors, list) and sponsors:
        first = sponsors[0]
        if isinstance(first, dict):
            return _first_nonempty(first.get("fullName"), first.get("name"), first.get("directOrderName"))
        return str(first)
    return None


def _with_match_metadata(amendment: dict[str, Any], *, confidence: str, reason: str) -> dict[str, Any]:
    matched = dict(amendment)
    matched["match_confidence"] = confidence
    matched["match_reason"] = reason
    return matched


def _first_nonempty(*values: Any) -> Any:
    for value in values:
        if value is not None and str(value).strip():
            return value
    return None
