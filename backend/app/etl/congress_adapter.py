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
        subject_name
        for subject_name in (_coerce_subject(subject) for subject in _iter_subject_entries(subjects))
        if subject_name
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

    summaries_dir = cache_dir.parent / "bill_summaries"
    subjects_dir = cache_dir.parent / "bill_subjects"
    actions_dir = cache_dir.parent / "bill_actions"
    texts_dir = cache_dir.parent / "bill_texts"
    amendments_dir = cache_dir.parent / "bill_amendments"
    committees_dir = cache_dir.parent / "bill_committees"
    lookup: dict[tuple[int, str, int], dict[str, Any]] = {}
    for path in sorted(cache_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        _merge_companion_payload(payload, summaries_dir / path.name, "summaries")
        _merge_companion_payload(payload, subjects_dir / path.name, "subjects")
        _merge_companion_payload(payload, actions_dir / path.name, "actions")
        _merge_companion_payload(payload, texts_dir / path.name, "textVersions")
        _merge_companion_payload(payload, amendments_dir / path.name, "amendments")
        _merge_companion_payload(payload, committees_dir / path.name, "committees")
        normalized = normalize_congress_bill_response(payload)
        bill = payload.get("bill", payload)
        normalized["latest_action"] = _extract_latest_action(bill)
        normalized["introduced_date"] = bill.get("introducedDate")
        normalized["origin_chamber"] = bill.get("originChamber")
        normalized["laws"] = _coerce_list(bill.get("laws"))
        normalized["cbo_cost_estimates"] = _coerce_list(bill.get("cboCostEstimates"))
        normalized["text_versions"] = _extract_text_versions(bill.get("textVersions"))
        normalized["actions"] = _coerce_list(bill.get("actions"))
        normalized["amendments"] = _coerce_list(bill.get("amendments"))
        normalized["committees"] = _coerce_list(bill.get("committees"))
        normalized["legislation_url"] = bill.get("legislationUrl")
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
    if isinstance(summaries, dict):
        summaries = summaries.get("summaries") or summaries.get("items") or []
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


def _iter_subject_entries(subjects: Any) -> list[Any]:
    if isinstance(subjects, list):
        return subjects
    if isinstance(subjects, dict):
        entries: list[Any] = []
        legislative_subjects = subjects.get("legislativeSubjects")
        if isinstance(legislative_subjects, list):
            entries.extend(legislative_subjects)
        policy_area = subjects.get("policyArea")
        if policy_area:
            entries.append(policy_area)
        return entries
    return []


def _merge_companion_payload(payload: dict[str, Any], path: Path, field_name: str) -> None:
    if not path.exists():
        return

    companion = json.loads(path.read_text(encoding="utf-8"))
    values = companion.get(field_name)
    if values is None:
        return

    bill = payload.setdefault("bill", {})
    bill[field_name] = values
    payload[field_name] = values


def _extract_latest_action(bill: dict[str, Any]) -> dict[str, str] | None:
    latest_action = bill.get("latestAction")
    if isinstance(latest_action, dict):
        return {
            "action_date": str(latest_action.get("actionDate") or ""),
            "text": str(latest_action.get("text") or ""),
        }
    actions = bill.get("actions")
    if isinstance(actions, list) and actions:
        action = actions[0]
        if isinstance(action, dict):
            return {
                "action_date": str(action.get("actionDate") or ""),
                "text": str(action.get("text") or action.get("actionCode") or ""),
            }
    return None


def _extract_text_versions(text_versions: Any) -> list[dict[str, Any]]:
    if isinstance(text_versions, dict):
        text_versions = text_versions.get("textVersions") or text_versions.get("items") or []
    if not isinstance(text_versions, list):
        return []
    extracted = []
    for version in text_versions:
        if not isinstance(version, dict):
            continue
        formats = [
            {
                "type": str(text_format.get("type") or ""),
                "url": str(text_format.get("url") or ""),
            }
            for text_format in _coerce_list(version.get("formats"))
            if isinstance(text_format, dict)
        ]
        extracted.append(
            {
                "date": version.get("date"),
                "type": version.get("type"),
                "formatted_text": version.get("formattedText"),
                "formats": formats,
            }
        )
    return extracted


def _coerce_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("items", "actions", "amendments", "committees", "cboCostEstimates"):
            if isinstance(value.get(key), list):
                return value[key]
    return []
