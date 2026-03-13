import json
import re
from pathlib import Path
from typing import Any

from app.etl.types import FixtureBundle


FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"
CONGRESS_SAMPLE_DIR = FIXTURES_DIR / "congress_sample"


def load_congress_sample_bundle(source_dir: Path = CONGRESS_SAMPLE_DIR) -> FixtureBundle:
    members = _load_json(source_dir / "members.json")
    bills = _load_json(source_dir / "bills.json")
    roll_calls = _load_json(source_dir / "roll_calls.json")
    votes = _load_json(source_dir / "votes.json")
    zip_map = _load_json(source_dir / "zip_district_map.json")

    bill_records = normalize_congress_bill_records(bills)
    bill_id_by_lookup = {
        (bill["congress"], bill["bill_type"], bill["bill_number"]): bill["id"]
        for bill in bill_records
    }

    return FixtureBundle(
        legislators=[_normalize_member(member) for member in members],
        bills=bill_records,
        roll_calls=[
            _normalize_roll_call(roll_call, bill_id_by_lookup=bill_id_by_lookup)
            for roll_call in roll_calls
        ],
        votes_cast=[_normalize_vote(vote) for vote in votes],
        vote_subject_tags={
            bill["id"]: list(bill["subjects"])
            for bill in bill_records
        },
        zip_district_map=list(zip_map),
    )


def normalize_congress_bill_records(bills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_normalize_bill(bill) for bill in bills]


def normalize_congress_bill_response(payload: dict[str, Any]) -> dict[str, Any]:
    bill = payload.get("bill", payload)
    congress = int(bill["congress"])
    bill_type = str(bill.get("type") or bill.get("billType")).lower()
    bill_number = int(bill.get("number") or bill.get("billNumber"))

    summaries = payload.get("summaries") or bill.get("summaries") or []
    committees = payload.get("committees") or bill.get("committees") or []
    subjects = payload.get("subjects") or bill.get("subjects") or []
    policy_area = payload.get("policyArea") or bill.get("policyArea") or {}

    normalized_subjects = [
        _coerce_subject(subject)
        for subject in subjects
        if _coerce_subject(subject)
    ]
    policy_area_name = _coerce_subject(policy_area)
    if policy_area_name and policy_area_name not in normalized_subjects:
        normalized_subjects.append(policy_area_name)

    return {
        "id": _to_bill_id(congress=congress, bill_type=bill_type, bill_number=bill_number),
        "congress": congress,
        "bill_type": bill_type,
        "bill_number": bill_number,
        "title": _extract_bill_title(bill),
        "summary": _extract_latest_summary(summaries),
        "committee": _extract_committee_name(committees),
        "subjects": normalized_subjects,
    }


def load_congress_bill_cache(cache_dir: Path) -> dict[tuple[int, str, int], dict[str, Any]]:
    if not cache_dir.exists():
        return {}

    lookup: dict[tuple[int, str, int], dict[str, Any]] = {}
    for path in sorted(cache_dir.glob("*.json")):
        normalized = normalize_congress_bill_response(json.loads(path.read_text()))
        lookup[
            (
                int(normalized["congress"]),
                str(normalized["bill_type"]),
                int(normalized["bill_number"]),
            )
        ] = normalized
    return lookup


def _normalize_member(member: dict[str, Any]) -> dict[str, Any]:
    name_display = str(member["directOrderName"])
    return {
        "id": _to_legislator_id(name_display),
        "bioguide_id": member["bioguideId"],
        "name_display": name_display,
        "chamber": member["chamber"],
        "state": member["state"],
        "district": member["district"],
        "party": member["partyCode"],
        "in_office": bool(member["currentMember"]),
    }


def _normalize_bill(bill: dict[str, Any]) -> dict[str, Any]:
    congress = int(bill["congress"])
    bill_type = str(bill["type"]).lower()
    bill_number = int(bill["number"])
    return {
        "id": _to_bill_id(congress=congress, bill_type=bill_type, bill_number=bill_number),
        "congress": congress,
        "bill_type": bill_type,
        "bill_number": bill_number,
        "title": bill["title"],
        "summary": bill.get("summary", ""),
        "committee": bill.get("committee"),
        "subjects": bill.get("subjects", []),
    }


def _normalize_roll_call(
    roll_call: dict[str, Any],
    *,
    bill_id_by_lookup: dict[tuple[int, str, int], str],
) -> dict[str, Any]:
    bill_ref = bill_id_by_lookup[
        (
            int(roll_call["bill"]["congress"]),
            str(roll_call["bill"]["type"]).lower(),
            int(roll_call["bill"]["number"]),
        )
    ]
    chamber = str(roll_call["chamber"])
    roll_number = int(roll_call["rollNumber"])
    return {
        "id": f"rc_{chamber}_{roll_number:03d}",
        "chamber": chamber,
        "congress": int(roll_call["congress"]),
        "rollcall_number": roll_number,
        "vote_date": roll_call["date"],
        "question": roll_call["question"],
        "description": roll_call.get("description", ""),
        "bill_ref": bill_ref,
        "source_url": roll_call.get("url"),
    }


def _normalize_vote(vote: dict[str, Any]) -> dict[str, Any]:
    chamber = str(vote["chamber"])
    roll_number = int(vote["rollNumber"])
    return {
        "roll_call_id": f"rc_{chamber}_{roll_number:03d}",
        "legislator_id": _to_legislator_id(str(vote["memberName"])),
        "position": vote["position"],
    }


def _to_legislator_id(name_display: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name_display.lower()).strip("_")
    return f"leg_{slug}"


def _to_bill_id(*, congress: int, bill_type: str, bill_number: int) -> str:
    return f"bill_{congress}_{bill_type}_{bill_number}"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def _extract_bill_title(bill: dict[str, Any]) -> str:
    if bill.get("title"):
        return str(bill["title"])
    titles = bill.get("titles") or []
    for title in titles:
        if isinstance(title, dict) and title.get("title"):
            return str(title["title"])
    raise ValueError("Congress bill payload is missing title")


def _extract_latest_summary(summaries: list[Any]) -> str:
    for summary in summaries:
        if isinstance(summary, dict):
            text = summary.get("text") or summary.get("summary")
            if text:
                return str(text)
    return ""


def _extract_committee_name(committees: list[Any]) -> str | None:
    for committee in committees:
        if isinstance(committee, dict):
            name = committee.get("name") or committee.get("systemCode")
            if name:
                return str(name)
    return None


def _coerce_subject(subject: Any) -> str | None:
    if isinstance(subject, str) and subject.strip():
        return subject.strip()
    if isinstance(subject, dict):
        value = subject.get("name")
        if value:
            return str(value).strip()
    return None
