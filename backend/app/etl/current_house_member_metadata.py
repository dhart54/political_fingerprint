from __future__ import annotations

import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


PARSER_VERSION = "current_house_member_metadata_v1"
CONGRESS = 119
API_ROOT = "https://api.congress.gov/v3"
HOUSE_DIRECTORY_URL = "https://www.house.gov/representatives"
CLERK_VACANCIES_URL = "https://clerk.house.gov/Members/ViewVacancies"
MAX_LIST_PAGES = 3
MAX_CURRENT_MEMBERS = 700
MAX_DETAIL_REQUESTS = 600
SNAPSHOT_MAX_AGE_DAYS = 7
VOTING_AT_LARGE_STATES = {"AK","DE","ND","SD","VT","WY"}

STATE_NAMES = {
    "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO","Connecticut":"CT","Delaware":"DE","District of Columbia":"DC","Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY","American Samoa":"AS","Guam":"GU","Northern Mariana Islands":"MP","Puerto Rico":"PR","Virgin Islands":"VI"
}


class SourceContractError(RuntimeError):
    pass


@dataclass(frozen=True)
class Artifact:
    source: str
    path: Path
    status: int
    sha256: str
    size: int
    retrieved_at: str

    def as_dict(self, root: Path) -> dict[str, Any]:
        return {"source":self.source,"path":str(self.path.relative_to(root)).replace("\\","/"),"response_status":self.status,"sha256":self.sha256,"size_bytes":self.size,"retrieved_at":self.retrieved_at,"retry_count":0}


def list_url(offset: int) -> str:
    return f"{API_ROOT}/member/congress/{CONGRESS}?currentMember=true&limit=250&offset={offset}&format=json"


def detail_url(bioguide_id: str) -> str:
    return f"{API_ROOT}/member/{bioguide_id}?format=json"


def retrieve_official(*, api_key: str, output_dir: Path, timeout: int = 30) -> list[Artifact]:
    if not api_key:
        raise SourceContractError("blocked_no_api_key")
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts: list[Artifact] = []
    members: list[dict[str, Any]] = []
    for page, offset in enumerate(range(0, 750, 250)):
        if page >= MAX_LIST_PAGES:
            raise SourceContractError("Congress.gov pagination exceeded the three-page ceiling")
        path = output_dir / f"congress_119_current_{offset:03d}.json"
        artifacts.append(fetch(list_url(offset), path, api_key=api_key, timeout=timeout))
        payload = json.loads(path.read_text(encoding="utf-8"))
        page_rows = payload.get("members")
        if not isinstance(page_rows, list):
            raise SourceContractError("Congress.gov list layout missing members array")
        members.extend(page_rows)
        if not payload.get("pagination", {}).get("next"):
            break
    if len(members) > MAX_CURRENT_MEMBERS:
        raise SourceContractError("Congress.gov returned more than 700 current members")
    house_ids = sorted({str(row.get("bioguideId")) for row in members if is_house_list_row(row) and row.get("bioguideId")})
    if len(house_ids) > MAX_DETAIL_REQUESTS:
        raise SourceContractError("more than 600 member-detail requests would be required")
    details_dir = output_dir / "member_details"
    details_dir.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=8) as pool:
        pending = {pool.submit(fetch, detail_url(identifier), details_dir / f"{identifier}.json", api_key=api_key, timeout=timeout): identifier for identifier in house_ids}
        for future in as_completed(pending):
            artifacts.append(future.result())
    artifacts.append(fetch(HOUSE_DIRECTORY_URL, output_dir / "house_representatives.html", timeout=timeout))
    artifacts.append(fetch(CLERK_VACANCIES_URL, output_dir / "clerk_vacancies.html", timeout=timeout))
    return sorted(artifacts, key=lambda item: str(item.path))


def fetch(url: str, path: Path, *, api_key: str | None = None, timeout: int = 30) -> Artifact:
    headers = {"User-Agent":"political-fingerprint/0.1"}
    if api_key:
        headers["X-Api-Key"] = api_key
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        payload = response.read()
        status = int(response.status)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return Artifact(source=url,path=path,status=status,sha256=hashlib.sha256(payload).hexdigest(),size=len(payload),retrieved_at=datetime.now(timezone.utc).isoformat())


def is_house_list_row(row: dict[str, Any]) -> bool:
    terms = row.get("terms", {}).get("item", [])
    return any(term.get("chamber") == "House of Representatives" for term in terms)


def parse_congress_details(detail_dir: Path, *, retrieved_on: date) -> list[dict[str, Any]]:
    rows=[]
    for path in sorted(detail_dir.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        member=payload.get("member")
        if not isinstance(member,dict) or not member.get("bioguideId") or "currentMember" not in member:
            raise SourceContractError(f"Congress.gov detail layout invalid: {path.name}")
        terms_container=member.get("terms")
        if isinstance(terms_container,list):
            all_terms=terms_container
        elif isinstance(terms_container,dict) and isinstance(terms_container.get("item"),list):
            all_terms=terms_container["item"]
        else:
            raise SourceContractError(f"Congress.gov detail terms layout invalid: {path.name}")
        terms=[term for term in all_terms if term.get("congress")==CONGRESS and term.get("chamber")=="House of Representatives"]
        if not terms:
            continue
        if len(terms)!=1:
            raise SourceContractError(f"multiple 119th House terms for {member['bioguideId']}")
        term=terms[0]
        member_type=normalize_member_type(term.get("memberType"))
        state=str(term.get("stateCode") or "").upper()
        raw_district=term.get("district", member.get("district"))
        if raw_district is None and (member_type in {"delegate","resident_commissioner"} or state in VOTING_AT_LARGE_STATES):
            canonical="00"
            raw_district_text=""
        else:
            canonical=normalize_district(raw_district)
            raw_district_text=str(raw_district)
        rows.append({
            "bioguide_id":member["bioguideId"],"name":member.get("directOrderName") or member.get("invertedOrderName"),"congress":CONGRESS,"chamber":"house","source_state":state,"source_district":raw_district_text,"canonical_state":state,"canonical_district":canonical,"normalization_rule":"house_member_district_v1","member_type":member_type,"current_member":member.get("currentMember") is True,"service_start_year":term.get("startYear"),"service_end_year":term.get("endYear"),"service_date_precision":"year","party":term.get("partyCode") or term.get("partyName") or ((member.get("partyHistory") or [{}])[-1].get("partyAbbreviation")),"official_url":member.get("officialWebsiteUrl") or member.get("officialUrl"),"source_update_date":member.get("updateDate"),"source_name":"Congress.gov API","source_type":"official_api","source_url":detail_url(member["bioguideId"]),"source_retrieved_at":retrieved_on.isoformat(),"source_checksum":sha256_file(path),"parser_version":PARSER_VERSION,
        })
    return rows


def normalize_member_type(value: Any) -> str:
    mapping={"Representative":"voting_representative","Delegate":"delegate","Resident Commissioner":"resident_commissioner"}
    if value not in mapping:
        raise SourceContractError(f"unsupported House memberType: {value!r}")
    return mapping[value]


def normalize_district(value: Any) -> str:
    text=str(value).strip()
    if not text.isdigit() or int(text)>99:
        raise SourceContractError(f"invalid House district: {value!r}")
    return text.zfill(2)


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_tr=False; self.in_cell=False; self.cell=[]; self.row=[]; self.rows=[]
    def handle_starttag(self,tag,attrs):
        if tag=="tr": self.in_tr=True; self.row=[]
        if self.in_tr and tag in {"td","th"}: self.in_cell=True; self.cell=[]
    def handle_data(self,data):
        if self.in_cell: self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in {"td","th"} and self.in_cell:
            self.row.append(" ".join("".join(self.cell).split())); self.in_cell=False
        if tag=="tr" and self.in_tr:
            if self.row:self.rows.append(self.row)
            self.in_tr=False


def parse_house_directory(html: str) -> list[dict[str, Any]]:
    if "Directory of Representatives" not in html or "Resident Commissioner" not in html or "Delegate" not in html:
        raise SourceContractError("House directory required layout markers missing")
    parser=_TableParser(); parser.feed(html)
    records=[]
    for cells in parser.rows:
        joined=" | ".join(cells)
        location=next((cell for cell in cells if parse_house_location(cell)),None)
        if not location: continue
        state,district,seat_type=parse_house_location(location)
        records.append({"canonical_state":state,"canonical_district":district,"seat_type":seat_type,"vacant":"Vacancy" in joined,"display":joined})
    unique={(r["canonical_state"],r["canonical_district"]):r for r in records}
    if len(unique)<435:
        raise SourceContractError(f"House directory parser found only {len(unique)} seats")
    return list(unique.values())


def parse_house_location(text: str) -> tuple[str,str,str] | None:
    compact=" ".join(text.split())
    for name,code in sorted(STATE_NAMES.items(),key=lambda item:-len(item[0])):
        if not compact.startswith(name+" "): continue
        rest=compact[len(name)+1:]
        if rest=="At Large": return code,"00","voting_at_large"
        if rest=="Delegate": return code,"00","delegate"
        if rest=="Resident Commissioner": return code,"00","resident_commissioner"
        match=re.match(r"(\d+)(?:st|nd|rd|th)$",rest)
        if match:return code,match.group(1).zfill(2),"voting_district"
    return None


def parse_clerk_vacancies(html: str) -> list[dict[str, Any]]:
    if "Vacancies of the 119th Congress" not in html or "vacancy_release" not in html:
        raise SourceContractError("Clerk vacancy layout markers missing")
    events=[]
    for match in re.finditer(r'href="/members/([A-Z]{2})(\d{1,2})/vacancy"',html):
        state,district=match.group(1),match.group(2).zfill(2)
        window=html[match.start():match.start()+4000]
        if re.search(r"(?:Took the Oath|Oath of Office|Sworn in)",window,re.IGNORECASE):
            continue
        date_match=re.search(r"(?:Resigned|Died) ([A-Z][a-z]+ \d{1,2}, \d{4})",window)
        events.append({"canonical_state":state,"canonical_district":district,"seat_status":"vacant","vacancy_effective_text":date_match.group(0) if date_match else None})
    unique={(e["canonical_state"],e["canonical_district"]):e for e in events}
    return list(unique.values())


def reconcile_seats(members: list[dict[str, Any]], house_records: list[dict[str, Any]], clerk_events: list[dict[str, Any]]) -> dict[tuple[str,str], str]:
    members_by_seat: dict[tuple[str,str], list[dict[str, Any]]] = {}
    for row in members:
        members_by_seat.setdefault((row["canonical_state"],row["canonical_district"]),[]).append(row)
    clerk={(row["canonical_state"],row["canonical_district"]) for row in clerk_events}
    statuses={}
    for seat in house_records:
        key=(seat["canonical_state"],seat["canonical_district"]); candidates=members_by_seat.get(key,[]); vacant=seat.get("vacant") is True or key in clerk
        if vacant and candidates:statuses[key]="source_conflict"
        elif vacant:statuses[key]="vacant_officially_confirmed"
        elif len(candidates)==1:statuses[key]="current_cross_source_confirmed"
        elif len(candidates)>1:statuses[key]="source_conflict"
        else:statuses[key]="unknown"
    return statuses


def metadata_currentness(*, retrieved_on: date, today: date, cross_source_confirmed: bool) -> str:
    if (today-retrieved_on).days > SNAPSHOT_MAX_AGE_DAYS:return "stale_snapshot"
    return "current_cross_source_confirmed" if cross_source_confirmed else "current_primary_source_only"


def sha256_file(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""):digest.update(chunk)
    return digest.hexdigest()
