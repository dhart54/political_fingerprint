import json
import re
from pathlib import Path
from xml.etree import ElementTree

from app.etl.congress_adapter import load_congress_bill_cache, normalize_congress_bill_records
from app.etl.fetch_sources import CONGRESS_BILL_CACHE_DIR, SENATE_XML_CACHE_DIR
from app.etl.types import FixtureBundle


FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"
SENATE_XML_SAMPLE_DIR = FIXTURES_DIR / "senate_xml_sample"


def load_senate_xml_sample_bundle(source_dir: Path = SENATE_XML_SAMPLE_DIR) -> FixtureBundle:
    return load_senate_xml_bundle(source_dir=source_dir)


def load_senate_xml_cache_bundle(
    source_dir: Path = SENATE_XML_CACHE_DIR,
    *,
    congress_cache_dir: Path = CONGRESS_BILL_CACHE_DIR,
) -> FixtureBundle:
    return load_senate_xml_bundle(
        source_dir=source_dir,
        fallback_dir=SENATE_XML_SAMPLE_DIR,
        congress_cache_dir=congress_cache_dir,
    )


def load_senate_xml_bundle(
    *,
    source_dir: Path,
    fallback_dir: Path | None = None,
    congress_cache_dir: Path | None = None,
) -> FixtureBundle:
    member_tree = ElementTree.parse(_resolve_source_file(source_dir, "members.xml", fallback_dir))
    legislators = _parse_members(member_tree)
    legislators_by_lis = {
        str(legislator["lis_member_id"]): legislator
        for legislator in legislators
    }
    congress_bill_records = normalize_congress_bill_records(
        json.loads(_resolve_source_file(source_dir, "bills.json", fallback_dir).read_text())
    )
    congress_bill_lookup = {
        (int(bill["congress"]), str(bill["bill_type"]), int(bill["bill_number"])): bill
        for bill in congress_bill_records
    }
    if congress_cache_dir is not None:
        congress_bill_lookup.update(load_congress_bill_cache(congress_cache_dir))

    vote_files = sorted(source_dir.glob("vote_*.xml"))
    if not vote_files and fallback_dir is not None:
        vote_files = sorted(fallback_dir.glob("vote_*.xml"))
    bills_by_id: dict[str, dict[str, object]] = {}
    roll_calls = []
    votes_cast = []

    for vote_file in vote_files:
        roll_call, bill, votes = _parse_roll_call(
            ElementTree.parse(vote_file),
            legislators_by_lis=legislators_by_lis,
            congress_bill_lookup=congress_bill_lookup,
        )
        bills_by_id[str(bill["id"])] = bill
        roll_calls.append(roll_call)
        votes_cast.extend(votes)

    zip_district_map = json.loads(
        _resolve_source_file(source_dir, "zip_district_map.json", fallback_dir).read_text()
    )

    return FixtureBundle(
        legislators=[
            {
                key: value
                for key, value in legislator.items()
                if key != "lis_member_id"
            }
            for legislator in legislators
        ],
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
    legislators: list[dict[str, object]] = []

    for member in root.findall("./members/member"):
        full_name = _require_text(member.find("full_name"))
        legislators.append(
            {
                "id": _to_legislator_id(full_name),
                "lis_member_id": _require_text(member.find("lis_member_id")),
                "bioguide_id": _require_text(member.find("bioguide_id")),
                "name_display": full_name,
                "chamber": "senate",
                "state": _require_text(member.find("state")),
                "district": "Statewide",
                "party": _require_text(member.find("party")),
                "in_office": _require_text(member.find("in_office")).lower() == "true",
            }
        )

    return legislators


def _parse_roll_call(
    tree: ElementTree.ElementTree,
    *,
    legislators_by_lis: dict[str, dict[str, object]],
    congress_bill_lookup: dict[tuple[int, str, int], dict[str, object]],
) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    root = tree.getroot()
    congress = int(_require_text(root.find("congress")))
    session = int(_require_text(root.find("session")))
    roll_number = int(_require_text(root.find("vote_number")))
    vote_date = _require_text(root.find("vote_date"))
    question = _require_text(root.find("question"))
    description = _require_text(root.find("vote_title"))
    document_text = _require_text(root.find("document/document_number"))

    bill_type, bill_number = _parse_senate_bill_reference(document_text)
    bill_key = (congress, bill_type, bill_number)
    bill_id = _to_bill_id(congress=congress, bill_type=bill_type, bill_number=bill_number)
    congress_bill = congress_bill_lookup.get(bill_key)

    roll_call = {
        "id": f"rc_senate_{roll_number:03d}",
        "chamber": "senate",
        "congress": congress,
        "rollcall_number": roll_number,
        "vote_date": vote_date,
        "question": question,
        "description": description,
        "bill_ref": bill_id,
        "source_url": _build_senate_source_url(congress=congress, session=session, roll_number=roll_number),
    }
    bill = {
        "id": bill_id,
        "congress": congress,
        "bill_type": bill_type,
        "bill_number": bill_number,
        "title": str(congress_bill["title"]) if congress_bill is not None else description,
        "summary": str(congress_bill["summary"]) if congress_bill is not None else "",
        "committee": congress_bill.get("committee") if congress_bill is not None else None,
        "subjects": list(congress_bill.get("subjects", [])) if congress_bill is not None else [],
    }

    votes: list[dict[str, object]] = []
    for member_vote in root.findall("./members/member"):
        lis_member_id = _require_text(member_vote.find("lis_member_id"))
        if lis_member_id not in legislators_by_lis:
            raise ValueError("Senate XML sample vote references unknown lis_member_id")
        votes.append(
            {
                "roll_call_id": roll_call["id"],
                "legislator_id": legislators_by_lis[lis_member_id]["id"],
                "position": _normalize_vote_position(_require_text(member_vote.find("vote_cast"))),
            }
        )

    return roll_call, bill, votes


def _parse_senate_bill_reference(value: str) -> tuple[str, int]:
    normalized = re.sub(r"[^A-Z0-9]+", " ", value.upper()).strip()
    if normalized.startswith("S RES "):
        return "sres", int(normalized.split()[-1])
    if normalized.startswith("S "):
        return "s", int(normalized.split()[-1])
    raise ValueError(f"Unsupported Senate bill reference: {value}")


def _normalize_vote_position(value: str) -> str:
    normalized = value.strip().lower()
    mapping = {
        "yea": "yea",
        "nay": "nay",
        "present": "present",
        "not voting": "not_voting",
    }
    if normalized not in mapping:
        raise ValueError(f"Unsupported Senate XML vote position: {value}")
    return mapping[normalized]


def _build_senate_source_url(*, congress: int, session: int, roll_number: int) -> str:
    return f"https://www.senate.gov/legislative/LIS/roll_call_votes/vote{congress}{session}/vote_{congress}_{session}_{roll_number:05d}.xml"


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
    raise FileNotFoundError(f"Missing required Senate XML source file: {filename}")


def _require_text(element: ElementTree.Element | None) -> str:
    if element is None or element.text is None:
        raise ValueError("Expected XML element text in Senate XML sample source")
    return element.text.strip()
