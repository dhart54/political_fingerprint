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
