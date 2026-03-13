import json
import re
from pathlib import Path
from xml.etree import ElementTree

from app.etl.congress_adapter import normalize_congress_bill_records
from app.etl.fetch_sources import HOUSE_CLERK_CACHE_DIR
from app.etl.types import FixtureBundle


FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"
HOUSE_CLERK_SAMPLE_DIR = FIXTURES_DIR / "house_clerk_sample"


def load_house_clerk_sample_bundle(source_dir: Path = HOUSE_CLERK_SAMPLE_DIR) -> FixtureBundle:
    return load_house_clerk_bundle(source_dir=source_dir)


def load_house_clerk_cache_bundle(source_dir: Path = HOUSE_CLERK_CACHE_DIR) -> FixtureBundle:
    return load_house_clerk_bundle(source_dir=source_dir, fallback_dir=HOUSE_CLERK_SAMPLE_DIR)


def load_house_clerk_bundle(
    *,
    source_dir: Path,
    fallback_dir: Path | None = None,
) -> FixtureBundle:
    member_tree = ElementTree.parse(_resolve_source_file(source_dir, "members.xml", fallback_dir))
    legislators = _parse_members(member_tree)
    legislators_by_bioguide = {
        str(legislator["bioguide_id"]): legislator
        for legislator in legislators
    }
    congress_bill_records = normalize_congress_bill_records(
        json.loads(_resolve_source_file(source_dir, "bills.json", fallback_dir).read_text())
    )
    congress_bill_lookup = {
        (int(bill["congress"]), str(bill["bill_type"]), int(bill["bill_number"])): bill
        for bill in congress_bill_records
    }

    roll_files = sorted(source_dir.glob("roll*.xml"))
    if not roll_files and fallback_dir is not None:
        roll_files = sorted(fallback_dir.glob("roll*.xml"))
    roll_calls = []
    votes_cast = []
    bills_by_id: dict[str, dict[str, object]] = {}

    for roll_file in roll_files:
        roll_call, bill, votes = _parse_roll_call(
            ElementTree.parse(roll_file),
            legislators_by_bioguide=legislators_by_bioguide,
            congress_bill_lookup=congress_bill_lookup,
        )
        bills_by_id[str(bill["id"])] = bill
        roll_calls.append(roll_call)
        votes_cast.extend(votes)

    zip_district_map = json.loads(
        _resolve_source_file(source_dir, "zip_district_map.json", fallback_dir).read_text()
    )

    return FixtureBundle(
        legislators=legislators,
        bills=list(bills_by_id.values()),
        roll_calls=roll_calls,
        votes_cast=votes_cast,
        vote_subject_tags={
            str(bill["id"]): list(bill.get("subjects", []))
            for bill in bills_by_id.values()
        },
        zip_district_map=zip_district_map,
    )


def _parse_members(tree: ElementTree.ElementTree) -> list[dict[str, object]]:
    root = tree.getroot()
    members: list[dict[str, object]] = []

    for member in root.findall("./members/member"):
        statedistrict = _require_text(member.find("statedistrict"))
        member_info = member.find("member-info")
        if member_info is None:
            raise ValueError("House Clerk sample member is missing member-info")

        official_name = _require_text(member_info.find("official-name"))
        bioguide_id = _require_text(member_info.find("bioguideID"))
        party = _require_text(member_info.find("party"))
        state = member_info.find("state")
        if state is None:
            raise ValueError("House Clerk sample member is missing state")

        state_code = state.attrib.get("postal-code")
        if not state_code:
            raise ValueError("House Clerk sample member state is missing postal-code")

        members.append(
            {
                "id": _to_legislator_id(official_name),
                "bioguide_id": bioguide_id,
                "name_display": official_name,
                "chamber": "house",
                "state": state_code,
                "district": statedistrict[-2:],
                "party": party,
                "in_office": True,
            }
        )

    return members


def _parse_roll_call(
    tree: ElementTree.ElementTree,
    *,
    legislators_by_bioguide: dict[str, dict[str, object]],
    congress_bill_lookup: dict[tuple[int, str, int], dict[str, object]],
) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    root = tree.getroot()
    metadata = root.find("vote-metadata")
    if metadata is None:
        raise ValueError("House Clerk sample roll call is missing vote-metadata")

    congress = int(_require_text(metadata.find("congress")))
    session = int(_require_text(metadata.find("session")))
    roll_number = int(_require_text(metadata.find("rollcall-num")))
    bill_number_text = _require_text(metadata.find("legis-num"))
    vote_question = _require_text(metadata.find("vote-question"))
    vote_description = _require_text(metadata.find("vote-desc"))
    action_date = _require_text(metadata.find("action-date"))

    bill_type, bill_number = _parse_house_bill_reference(bill_number_text)
    bill_key = (congress, bill_type, bill_number)
    bill_id = _to_bill_id(
        congress=congress,
        bill_type=bill_type,
        bill_number=bill_number,
    )
    congress_bill = congress_bill_lookup.get(bill_key)

    roll_call = {
        "id": f"rc_house_{roll_number:03d}",
        "chamber": "house",
        "congress": congress,
        "rollcall_number": roll_number,
        "vote_date": action_date,
        "question": vote_question,
        "description": vote_description,
        "bill_ref": bill_id,
        "source_url": _build_house_clerk_source_url(session=session, roll_number=roll_number),
    }
    bill = {
        "id": bill_id,
        "congress": congress,
        "bill_type": bill_type,
        "bill_number": bill_number,
        "title": str(congress_bill["title"]) if congress_bill is not None else vote_description,
        "summary": str(congress_bill["summary"]) if congress_bill is not None else "",
        "committee": congress_bill.get("committee") if congress_bill is not None else None,
        "subjects": list(congress_bill.get("subjects", [])) if congress_bill is not None else [],
    }

    votes: list[dict[str, object]] = []
    for recorded_vote in root.findall("./vote-data/recorded-vote"):
        legislator_element = recorded_vote.find("legislator")
        if legislator_element is None:
            raise ValueError("House Clerk sample vote is missing legislator")
        bioguide_id = legislator_element.attrib.get("bioguide-id")
        if not bioguide_id or bioguide_id not in legislators_by_bioguide:
            raise ValueError("House Clerk sample vote references unknown bioguide-id")

        votes.append(
            {
                "roll_call_id": roll_call["id"],
                "legislator_id": legislators_by_bioguide[bioguide_id]["id"],
                "position": _normalize_vote_position(_require_text(recorded_vote.find("vote"))),
            }
        )

    return roll_call, bill, votes


def _parse_house_bill_reference(value: str) -> tuple[str, int]:
    normalized = re.sub(r"[^A-Z0-9]+", " ", value.upper()).strip()
    if normalized.startswith("H RES "):
        return "hres", int(normalized.split()[-1])
    if normalized.startswith("H R "):
        return "hr", int(normalized.split()[-1])
    raise ValueError(f"Unsupported House bill reference: {value}")


def _normalize_vote_position(value: str) -> str:
    normalized = value.strip().lower()
    mapping = {
        "yea": "yea",
        "aye": "yea",
        "nay": "nay",
        "no": "nay",
        "present": "present",
        "not voting": "not_voting",
    }
    if normalized not in mapping:
        raise ValueError(f"Unsupported House Clerk vote position: {value}")
    return mapping[normalized]


def _build_house_clerk_source_url(*, session: int, roll_number: int) -> str:
    year = "2025" if session == 1 else "2026"
    return f"https://clerk.house.gov/evs/{year}/roll{roll_number:03d}.xml"


def _to_legislator_id(name_display: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name_display.lower()).strip("_")
    return f"leg_{slug}"


def _to_bill_id(*, congress: int, bill_type: str, bill_number: int) -> str:
    return f"bill_{congress}_{bill_type}_{bill_number}"


def _resolve_source_file(source_dir: Path, filename: str, fallback_dir: Path | None) -> Path:
    primary_path = source_dir / filename
    if primary_path.exists():
        return primary_path
    if fallback_dir is not None:
        fallback_path = fallback_dir / filename
        if fallback_path.exists():
            return fallback_path
    raise FileNotFoundError(f"Missing required House Clerk source file: {filename}")


def _require_text(element: ElementTree.Element | None) -> str:
    if element is None or element.text is None:
        raise ValueError("Expected XML element text in House Clerk sample source")
    return element.text.strip()
