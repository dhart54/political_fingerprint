from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import date
import json
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from app.db import get_connection
from app.etl.current_congress_refresh import (
    CLASSIFICATION_VERSION,
    ProductionState,
    _build_import_rows,
    _build_chamber_median_rows,
    _build_drift_rows,
    _build_fingerprint_rows,
    _build_summary_rows,
    _download_summary,
    _fetch_bill_id_map,
    _fetch_legislator_id_map,
    _fetch_production_eligible_votes,
    _fetch_production_legislators,
    _fetch_roll_call_id_map,
    _insert_bills,
    _insert_classifications,
    _insert_interpretations,
    _insert_legislators,
    _insert_roll_calls,
    _insert_vote_contexts,
    _insert_votes_cast,
    _upsert_chamber_medians,
    _upsert_drift_scores,
    _upsert_fingerprints,
    _upsert_summaries,
    build_precompute_plan,
    load_production_state,
)
from app.etl.fetch_sources import (
    CONGRESS_BILL_CACHE_DIR,
    CONGRESS_CACHE_DIR,
    HOUSE_CLERK_CACHE_DIR,
    SENATE_XML_CACHE_DIR,
    fetch_house_clerk_members,
    fetch_house_clerk_roll_calls,
    fetch_senate_members,
    fetch_senate_vote_files,
    resolve_congress_api_key,
)
from app.etl.house_clerk_adapter import load_house_clerk_bundle
from app.etl.senate_xml_adapter import load_senate_xml_bundle
from app.etl.vote_context import infer_vote_type
from app.etl.types import FixtureBundle


SUPPORTED_HISTORICAL_CONGRESSES = (118,)
OFFICIAL_ROLL_COVERAGE = {
    118: {
        "house": {1: {"year": 2023, "latest_roll": 724}, 2: {"year": 2024, "latest_roll": 517}},
        "senate": {1: {"year": 2023, "latest_roll": 352}, 2: {"year": 2024, "latest_roll": 339}},
    }
}
APPROVAL_PHRASE = (
    "Approve 118th Congress historical expansion for supported 2023-2024 House and Senate "
    "fact, classification, deterministic interpretation, and derived-output rows, with "
    "session-aware roll-call identity, rollback generated before writes, unsupported categories "
    "deferred, procedural context non-counting, not-voting excluded, and no support/opposition, "
    "readiness, alignment, or interpretation methodology changes."
)
CONGRESS_MEMBER_CACHE_DIR = CONGRESS_CACHE_DIR / "members"
STATE_ABBREVIATIONS = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}


@dataclass(frozen=True)
class HistoricalRefreshPlan:
    congress: int
    source_dirs: dict[str, dict[int, str]]
    source_audit: dict[str, object]
    roll_keys: list[tuple[str, int, int, int]]
    planned_bill_inserts: int
    planned_legislator_inserts: int
    planned_roll_call_inserts: int
    planned_votes_cast_inserts: int
    planned_vote_context_inserts: int
    planned_classification_inserts: int
    planned_interpretation_inserts: int
    deferred_rows: list[dict[str, object]]
    errors: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "congress": self.congress,
            "source_dirs": {
                chamber: {str(session): path for session, path in sessions.items()}
                for chamber, sessions in self.source_dirs.items()
            },
            "source_audit": self.source_audit,
            "roll_keys": [list(key) for key in self.roll_keys],
            "planned_inserts": {
                "bills": self.planned_bill_inserts,
                "legislators": self.planned_legislator_inserts,
                "roll_calls": self.planned_roll_call_inserts,
                "votes_cast": self.planned_votes_cast_inserts,
                "vote_contexts": self.planned_vote_context_inserts,
                "vote_classifications": self.planned_classification_inserts,
                "vote_interpretations": self.planned_interpretation_inserts,
            },
            "deferred_rows": self.deferred_rows,
            "errors": self.errors,
            "safe_to_write": not self.errors,
        }


def session_cache_dir(*, congress: int, chamber: str, session: int) -> Path:
    _require_supported_congress(congress)
    if chamber == "house":
        year = int(OFFICIAL_ROLL_COVERAGE[congress]["house"][session]["year"])
        return HOUSE_CLERK_CACHE_DIR / str(year)
    if chamber == "senate":
        return SENATE_XML_CACHE_DIR / f"{congress}_{session}"
    raise ValueError(f"Unsupported chamber: {chamber}")


def fetch_historical_congress_sources(*, congress: int = 118, overwrite: bool = False) -> dict[str, object]:
    _require_supported_congress(congress)
    results: dict[str, object] = {"congress": congress, "sessions": {}}
    for session in (1, 2):
        house_meta = OFFICIAL_ROLL_COVERAGE[congress]["house"][session]
        senate_meta = OFFICIAL_ROLL_COVERAGE[congress]["senate"][session]
        house_dir = session_cache_dir(congress=congress, chamber="house", session=session)
        senate_dir = session_cache_dir(congress=congress, chamber="senate", session=session)
        house_dir.mkdir(parents=True, exist_ok=True)
        senate_dir.mkdir(parents=True, exist_ok=True)
        house_results = fetch_house_clerk_roll_calls(
            year=int(house_meta["year"]),
            roll_numbers=list(range(1, int(house_meta["latest_roll"]) + 1)),
            output_dir=house_dir,
            overwrite=overwrite,
        )
        senate_results = fetch_senate_vote_files(
            congress=congress,
            session=session,
            roll_numbers=list(range(1, int(senate_meta["latest_roll"]) + 1)),
            output_dir=senate_dir,
            overwrite=overwrite,
        )
        member_results = [
            fetch_house_clerk_members(output_dir=house_dir, overwrite=overwrite),
            fetch_senate_members(output_dir=senate_dir, overwrite=overwrite),
        ]
        congress_member_result = fetch_congress_members(congress=congress, overwrite=overwrite)
        results["sessions"][str(session)] = {
            "house_dir": str(house_dir),
            "senate_dir": str(senate_dir),
            "house": _download_summary(house_results),
            "senate": _download_summary(senate_results),
            "members": _download_summary(member_results),
            "congress_members": {
                "cached": int(congress_member_result.skipped),
                "downloaded": int(not congress_member_result.skipped),
                "total": 1,
                "destination": str(congress_member_result.destination),
            },
        }
    return results


def build_historical_refresh_plan(
    *,
    congress: int = 118,
    production_state: ProductionState | None = None,
) -> HistoricalRefreshPlan:
    _require_supported_congress(congress)
    production_state = production_state or load_production_state()
    bundle = load_historical_bundle(congress=congress)
    import_rows = _build_import_rows(bundle=bundle, production_state=production_state)
    errors = list(import_rows["errors"])
    errors.extend(_identity_errors(bundle))
    source_dirs = _source_dirs(congress)
    source_audit = audit_historical_sources(congress=congress)
    errors.extend(_coverage_errors(source_audit))
    return HistoricalRefreshPlan(
        congress=congress,
        source_dirs=source_dirs,
        source_audit=source_audit,
        roll_keys=sorted(import_rows["roll_keys"]),
        planned_bill_inserts=len(import_rows["bills"]),
        planned_legislator_inserts=len(import_rows["legislators"]),
        planned_roll_call_inserts=len(import_rows["roll_calls"]),
        planned_votes_cast_inserts=len(import_rows["votes_cast"]),
        planned_vote_context_inserts=len(import_rows["vote_contexts"]),
        planned_classification_inserts=len(import_rows["vote_classifications"]),
        planned_interpretation_inserts=len(import_rows["vote_interpretations"]),
        deferred_rows=import_rows["deferred_rows"],
        errors=errors,
    )


def write_historical_refresh(*, congress: int = 118, approval_phrase: str) -> dict[str, object]:
    if approval_phrase != APPROVAL_PHRASE:
        raise ValueError("Approval phrase does not match the historical Congress refresh gate.")
    production_state = load_production_state()
    bundle = load_historical_bundle(congress=congress)
    import_rows = _build_import_rows(bundle=bundle, production_state=production_state)
    errors = list(import_rows["errors"])
    errors.extend(_identity_errors(bundle))
    errors.extend(_coverage_errors(audit_historical_sources(congress=congress)))
    if errors:
        raise ValueError(f"Historical refresh preflight failed: {errors}")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            inserted_bills = _insert_bills(cursor, import_rows["bills"])
            inserted_legislators = _insert_legislators(cursor, import_rows["legislators"])
            legislator_id_map = _fetch_legislator_id_map(cursor)
            bill_id_map = _fetch_bill_id_map(cursor, import_rows["bill_keys"])
            inserted_roll_calls = _insert_roll_calls(cursor, import_rows["roll_calls"], bill_id_map)
            roll_call_id_map = _fetch_roll_call_id_map(cursor, import_rows["roll_keys"])
            inserted_votes = _insert_votes_cast(
                cursor,
                import_rows["votes_cast"],
                import_rows["roll_keys_by_internal_id"],
                import_rows["bioguide_by_internal_legislator_id"],
                roll_call_id_map,
                legislator_id_map,
            )
            inserted_contexts = _insert_vote_contexts(
                cursor,
                import_rows["vote_contexts"],
                import_rows["roll_keys_by_internal_id"],
                import_rows["bioguide_by_internal_legislator_id"],
                roll_call_id_map,
                legislator_id_map,
            )
            inserted_classifications = _insert_classifications(
                cursor,
                import_rows["vote_classifications"],
                import_rows["roll_keys_by_internal_id"],
                roll_call_id_map,
            )
            inserted_interpretations = _insert_interpretations(
                cursor,
                import_rows["vote_interpretations"],
                import_rows["roll_keys_by_internal_id"],
                roll_call_id_map,
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {
        "congress": congress,
        "inserted": {
            "bills": inserted_bills,
            "legislators": inserted_legislators,
            "roll_calls": inserted_roll_calls,
            "votes_cast": inserted_votes,
            "vote_contexts": inserted_contexts,
            "vote_classifications": inserted_classifications,
            "vote_interpretations": inserted_interpretations,
        },
        "deferred_rows": import_rows["deferred_rows"],
    }


def write_historical_precomputed_outputs(*, as_of: date, approval_phrase: str) -> dict[str, object]:
    if approval_phrase != APPROVAL_PHRASE:
        raise ValueError("Approval phrase does not match the historical Congress refresh gate.")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            legislators = _fetch_production_legislators(cursor)
            eligible_votes = _fetch_production_eligible_votes(cursor)
            fingerprint_rows = _build_fingerprint_rows(
                legislators=legislators,
                eligible_votes=eligible_votes,
                as_of=as_of,
            )
            chamber_median_rows = _build_chamber_median_rows(
                legislators=legislators,
                fingerprint_rows=fingerprint_rows,
                as_of=as_of,
            )
            drift_rows = _build_drift_rows(
                legislators=legislators,
                eligible_votes=eligible_votes,
                as_of=as_of,
            )
            summary_rows = _build_summary_rows(
                legislators=legislators,
                fingerprint_rows=fingerprint_rows,
                drift_rows=drift_rows,
                as_of=as_of,
            )
            updated = {
                "fingerprints": _upsert_fingerprints(cursor, fingerprint_rows),
                "chamber_medians": _upsert_chamber_medians(cursor, chamber_median_rows),
                "drift_scores": _upsert_drift_scores(cursor, drift_rows),
                "summaries": _upsert_summaries(cursor, summary_rows),
            }
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {"as_of": as_of.isoformat(), "updated_or_inserted": updated}


def build_historical_rollback_sql(*, congress: int = 118) -> str:
    _require_supported_congress(congress)
    production_state = load_production_state()
    bundle = load_historical_bundle(congress=congress)
    import_rows = _build_import_rows(bundle=bundle, production_state=production_state)
    roll_keys = sorted(import_rows["roll_keys"])
    bill_keys = sorted(
        (int(bill["congress"]), str(bill["bill_type"]).lower(), int(bill["bill_number"]))
        for bill in import_rows["bills"]
    )
    legislator_bioguides = sorted(str(row["bioguide_id"]) for row in import_rows["legislators"])

    lines = [
        "-- Rollback for 118th Congress historical expansion fact/classification/interpretation import.",
        "-- Generated before production write. Deletes only roll calls absent at preflight time.",
        "BEGIN;",
        "",
        "CREATE TEMP TABLE _pf_rollback_rolls (",
        "    chamber chamber NOT NULL,",
        "    congress INTEGER NOT NULL,",
        "    session INTEGER NOT NULL,",
        "    rollcall_number INTEGER NOT NULL",
        ") ON COMMIT DROP;",
        "",
    ]
    if roll_keys:
        values = ",\n".join(
            f"    ('{chamber}', {key_congress}, {session}, {roll_number})"
            for chamber, key_congress, session, roll_number in roll_keys
        )
        lines.extend(["INSERT INTO _pf_rollback_rolls VALUES", f"{values};", ""])
    lines.extend(
        [
            "DO $$",
            "DECLARE",
            "    expected_count INTEGER := %d;" % len(roll_keys),
            "    actual_count INTEGER;",
            "BEGIN",
            "    SELECT COUNT(*) INTO actual_count",
            "    FROM roll_calls rc",
            "    JOIN _pf_rollback_rolls tr",
            "      ON tr.chamber = rc.chamber",
            "     AND tr.congress = rc.congress",
            "     AND tr.session = rc.session",
            "     AND tr.rollcall_number = rc.rollcall_number;",
            "    IF actual_count <> expected_count THEN",
            "        RAISE EXCEPTION 'Rollback target mismatch: expected %, found %', expected_count, actual_count;",
            "    END IF;",
            "END $$;",
            "",
            "WITH target_roll_ids AS (",
            "    SELECT rc.id",
            "    FROM roll_calls rc",
            "    JOIN _pf_rollback_rolls tr",
            "      ON tr.chamber = rc.chamber",
            "     AND tr.congress = rc.congress",
            "     AND tr.session = rc.session",
            "     AND tr.rollcall_number = rc.rollcall_number",
            ")",
            "DELETE FROM vote_contexts WHERE roll_call_id IN (SELECT id FROM target_roll_ids);",
            "",
            "WITH target_roll_ids AS (",
            "    SELECT rc.id",
            "    FROM roll_calls rc",
            "    JOIN _pf_rollback_rolls tr",
            "      ON tr.chamber = rc.chamber",
            "     AND tr.congress = rc.congress",
            "     AND tr.session = rc.session",
            "     AND tr.rollcall_number = rc.rollcall_number",
            ")",
            "DELETE FROM votes_cast WHERE roll_call_id IN (SELECT id FROM target_roll_ids);",
            "",
            "WITH target_roll_ids AS (",
            "    SELECT rc.id",
            "    FROM roll_calls rc",
            "    JOIN _pf_rollback_rolls tr",
            "      ON tr.chamber = rc.chamber",
            "     AND tr.congress = rc.congress",
            "     AND tr.session = rc.session",
            "     AND tr.rollcall_number = rc.rollcall_number",
            ")",
            "DELETE FROM vote_interpretations WHERE roll_call_id IN (SELECT id FROM target_roll_ids);",
            "",
            "WITH target_roll_ids AS (",
            "    SELECT rc.id",
            "    FROM roll_calls rc",
            "    JOIN _pf_rollback_rolls tr",
            "      ON tr.chamber = rc.chamber",
            "     AND tr.congress = rc.congress",
            "     AND tr.session = rc.session",
            "     AND tr.rollcall_number = rc.rollcall_number",
            ")",
            "DELETE FROM vote_classifications WHERE roll_call_id IN (SELECT id FROM target_roll_ids);",
            "",
            "DELETE FROM roll_calls rc",
            "USING _pf_rollback_rolls tr",
            "WHERE tr.chamber = rc.chamber",
            "  AND tr.congress = rc.congress",
            "  AND tr.session = rc.session",
            "  AND tr.rollcall_number = rc.rollcall_number;",
            "",
            "CREATE TEMP TABLE _pf_rollback_bills (",
            "    congress INTEGER NOT NULL,",
            "    bill_type TEXT NOT NULL,",
            "    bill_number INTEGER NOT NULL",
            ") ON COMMIT DROP;",
            "",
        ]
    )
    if bill_keys:
        values = ",\n".join(
            f"    ({key_congress}, '{bill_type}', {bill_number})"
            for key_congress, bill_type, bill_number in bill_keys
        )
        lines.extend(["INSERT INTO _pf_rollback_bills VALUES", f"{values};", ""])
    lines.extend(
        [
            "DELETE FROM bills b",
            "USING _pf_rollback_bills tb",
            "WHERE tb.congress = b.congress",
            "  AND tb.bill_type = b.bill_type",
            "  AND tb.bill_number = b.bill_number",
            "  AND NOT EXISTS (SELECT 1 FROM roll_calls rc WHERE rc.bill_id = b.id);",
            "",
            "CREATE TEMP TABLE _pf_rollback_legislators (",
            "    bioguide_id TEXT NOT NULL",
            ") ON COMMIT DROP;",
            "",
        ]
    )
    if legislator_bioguides:
        values = ",\n".join(f"    ('{bioguide_id}')" for bioguide_id in legislator_bioguides)
        lines.extend(["INSERT INTO _pf_rollback_legislators VALUES", f"{values};", ""])
    lines.extend(
        [
            "DELETE FROM legislators l",
            "USING _pf_rollback_legislators tl",
            "WHERE tl.bioguide_id = l.bioguide_id",
            "  AND NOT EXISTS (SELECT 1 FROM votes_cast vc WHERE vc.legislator_id = l.id);",
            "",
            "COMMIT;",
            "",
        ]
    )
    return "\n".join(lines)


def load_historical_bundle(*, congress: int = 118) -> FixtureBundle:
    _require_supported_congress(congress)
    bundles = []
    for session in (1, 2):
        bundles.append(
            load_house_clerk_bundle(
                source_dir=session_cache_dir(congress=congress, chamber="house", session=session),
                congress_cache_dir=CONGRESS_BILL_CACHE_DIR,
            )
        )
        bundles.append(
            load_senate_xml_bundle(
                source_dir=session_cache_dir(congress=congress, chamber="senate", session=session),
                congress_cache_dir=CONGRESS_BILL_CACHE_DIR,
            )
        )
    merged = bundles[0]
    for bundle in bundles[1:]:
        merged = _merge_historical_bundles(merged, bundle)
    return _apply_historical_senate_bioguide_mapping(bundle=merged, congress=congress)


def fetch_congress_members(*, congress: int, overwrite: bool = False):
    from app.etl.fetch_sources import DownloadResult

    destination = CONGRESS_MEMBER_CACHE_DIR / f"{congress}_members.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not overwrite:
        return DownloadResult(
            source_url=_congress_members_url(congress=congress, offset=0, api_key="REDACTED"),
            destination=destination,
            bytes_written=destination.stat().st_size,
            skipped=True,
        )

    api_key = resolve_congress_api_key()
    members = []
    offset = 0
    limit = 250
    while True:
        url = _congress_members_url(congress=congress, offset=offset, limit=limit, api_key=api_key)
        with urlopen(Request(url, headers={"User-Agent": "political-fingerprint/0.1"}), timeout=30) as response:
            payload = json.loads(response.read())
        page_members = payload.get("members") or []
        members.extend(page_members)
        if len(page_members) < limit:
            break
        offset += limit

    destination.write_text(
        json.dumps({"congress": congress, "members": members}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return DownloadResult(
        source_url=_congress_members_url(congress=congress, offset=0, api_key="REDACTED"),
        destination=destination,
        bytes_written=destination.stat().st_size,
        skipped=False,
    )


def _congress_members_url(*, congress: int, offset: int, api_key: str, limit: int = 250) -> str:
    query = urlencode({"format": "json", "limit": limit, "offset": offset, "api_key": api_key})
    return f"https://api.congress.gov/v3/member/congress/{congress}?{query}"


def _apply_historical_senate_bioguide_mapping(*, bundle: FixtureBundle, congress: int) -> FixtureBundle:
    lookup = _load_congress_senator_lookup(congress=congress)
    if not lookup:
        return bundle

    legislators = []
    for legislator in bundle.legislators:
        if str(legislator.get("chamber")) != "senate":
            legislators.append(legislator)
            continue
        bioguide_id = str(legislator.get("bioguide_id") or "")
        if not re.fullmatch(r"S\d{3}", bioguide_id):
            legislators.append(legislator)
            continue
        mapped = lookup.get(_senator_lookup_key(str(legislator.get("name_display") or ""), str(legislator.get("state") or "")))
        if mapped is None:
            mapped = lookup.get(_senator_last_state_key(str(legislator.get("name_display") or ""), str(legislator.get("state") or "")))
        if mapped is None:
            legislators.append(legislator)
            continue
        legislators.append(
            {
                **legislator,
                "bioguide_id": mapped["bioguide_id"],
                "name_display": mapped["name_display"],
            }
        )

    return FixtureBundle(
        legislators=legislators,
        bills=bundle.bills,
        roll_calls=bundle.roll_calls,
        votes_cast=bundle.votes_cast,
        vote_subject_tags=bundle.vote_subject_tags,
        zip_district_map=bundle.zip_district_map,
    )


def _load_congress_senator_lookup(*, congress: int) -> dict[tuple[str, str], dict[str, str]]:
    path = CONGRESS_MEMBER_CACHE_DIR / f"{congress}_members.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    lookup = {}
    last_state_values: dict[tuple[str, str], list[dict[str, str]]] = {}
    for member in payload.get("members", []):
        terms = member.get("terms") or {}
        term_items = terms.get("item") if isinstance(terms, dict) else []
        if not any(isinstance(term, dict) and term.get("chamber") == "Senate" for term in term_items or []):
            continue
        state = STATE_ABBREVIATIONS.get(str(member.get("state") or ""), str(member.get("state") or ""))
        name_display = _congress_member_display_name(str(member.get("name") or ""))
        key = _senator_lookup_key(name_display, state)
        mapped = {
            "bioguide_id": str(member["bioguideId"]),
            "name_display": name_display,
        }
        lookup[key] = mapped
        last_state_values.setdefault(_senator_last_state_key(name_display, state), []).append(mapped)
    for key, values in last_state_values.items():
        if len(values) == 1:
            lookup[key] = values[0]
    return lookup


def _congress_member_display_name(value: str) -> str:
    if "," not in value:
        return value.strip()
    last, first = [part.strip() for part in value.split(",", 1)]
    return f"{first} {last}".strip()


def _senator_lookup_key(name_display: str, state: str) -> tuple[str, str]:
    name = re.sub(r"\([^)]*\)", "", name_display)
    normalized_name = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    return normalized_name, state.strip().upper()


def _senator_last_state_key(name_display: str, state: str) -> tuple[str, str]:
    name = re.sub(r"\([^)]*\)", "", name_display)
    tokens = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip().split()
    last = tokens[-1] if tokens else ""
    return f"last:{last}", state.strip().upper()


def _merge_historical_bundles(left: FixtureBundle, right: FixtureBundle) -> FixtureBundle:
    return FixtureBundle(
        legislators=_dedupe(left.legislators + right.legislators, key="id"),
        bills=_dedupe(left.bills + right.bills, key="id"),
        roll_calls=left.roll_calls + right.roll_calls,
        votes_cast=left.votes_cast + right.votes_cast,
        vote_subject_tags={**left.vote_subject_tags, **right.vote_subject_tags},
        zip_district_map=_dedupe(left.zip_district_map + right.zip_district_map, key="zip"),
    )


def _dedupe(rows: list[dict[str, object]], *, key: str) -> list[dict[str, object]]:
    values = {}
    for row in rows:
        values[row[key]] = row
    return list(values.values())


def audit_historical_sources(*, congress: int = 118) -> dict[str, object]:
    _require_supported_congress(congress)
    return {
        "congress": congress,
        "official_roll_coverage": OFFICIAL_ROLL_COVERAGE[congress],
        "sessions": {
            str(session): {
                "house": _audit_house_session(congress=congress, session=session),
                "senate": _audit_senate_session(congress=congress, session=session),
            }
            for session in (1, 2)
        },
    }


def _audit_house_session(*, congress: int, session: int) -> dict[str, object]:
    source_dir = session_cache_dir(congress=congress, chamber="house", session=session)
    expected = int(OFFICIAL_ROLL_COVERAGE[congress]["house"][session]["latest_roll"])
    files = sorted(source_dir.glob("roll*.xml"))
    vote_types = Counter()
    unsupported = Counter()
    for path in files:
        metadata = ElementTree.parse(path).getroot().find("vote-metadata")
        if metadata is None:
            unsupported["malformed_xml"] += 1
            continue
        question = _optional_text(metadata.find("vote-question"))
        description = _optional_text(metadata.find("vote-desc")) or _optional_text(metadata.find("amendment-author"))
        vote_types[infer_vote_type(question=question or "", description=description or "")] += 1
        if not _optional_text(metadata.find("legis-num")):
            unsupported["missing_bill_reference"] += 1
    return _audit_result(expected=expected, files=files, vote_types=vote_types, unsupported=unsupported)


def _audit_senate_session(*, congress: int, session: int) -> dict[str, object]:
    source_dir = session_cache_dir(congress=congress, chamber="senate", session=session)
    expected = int(OFFICIAL_ROLL_COVERAGE[congress]["senate"][session]["latest_roll"])
    files = sorted(source_dir.glob("vote_*.xml"))
    vote_types = Counter()
    unsupported = Counter()
    for path in files:
        root = ElementTree.parse(path).getroot()
        question = _optional_text(root.find("question")) or ""
        description = _optional_text(root.find("vote_title")) or ""
        document_type = _optional_text(root.find("document/document_type")) or ""
        document_name = _optional_text(root.find("document/document_name")) or ""
        text = f"{question} {description} {document_type} {document_name}".lower()
        vote_type = infer_vote_type(question=question, description=description)
        vote_types[vote_type] += 1
        if "pn" in text or "nomination" in text or "confirmation" in text:
            unsupported["pn_nomination"] += 1
        elif "treaty" in text:
            unsupported["treaty_or_executive"] += 1
        elif not _supported_senate_document(document_type=document_type, document_name=document_name):
            unsupported["unsupported_bill_reference"] += 1
    return _audit_result(expected=expected, files=files, vote_types=vote_types, unsupported=unsupported)


def _audit_result(*, expected: int, files: list[Path], vote_types: Counter, unsupported: Counter) -> dict[str, object]:
    return {
        "expected_roll_files": expected,
        "cached_roll_files": len(files),
        "coverage_complete": len(files) == expected,
        "vote_types": dict(sorted(vote_types.items())),
        "unsupported_or_deferred": dict(sorted(unsupported.items())),
    }


def _supported_senate_document(*, document_type: str, document_name: str) -> bool:
    value = re.sub(r"[^A-Z0-9]+", " ", f"{document_type} {document_name}".upper()).strip()
    return any(
        token in value
        for token in ("H R", "H RES", "H J RES", "H CON RES", "S ", "S RES", "S J RES", "S CON RES")
    )


def _coverage_errors(source_audit: dict[str, object]) -> list[str]:
    errors = []
    sessions = source_audit.get("sessions", {})
    if not isinstance(sessions, dict):
        return ["Source audit did not return session coverage."]
    for session, chambers in sessions.items():
        if not isinstance(chambers, dict):
            errors.append(f"Session {session} source audit is malformed.")
            continue
        for chamber, result in chambers.items():
            if not isinstance(result, dict) or not result.get("coverage_complete"):
                cached = result.get("cached_roll_files") if isinstance(result, dict) else "unknown"
                expected = result.get("expected_roll_files") if isinstance(result, dict) else "unknown"
                errors.append(f"{chamber} session {session} source coverage incomplete: cached {cached} of {expected}.")
    return errors


def _identity_errors(bundle: FixtureBundle) -> list[str]:
    unresolved = sorted(
        {
            str(legislator["bioguide_id"])
            for legislator in bundle.legislators
            if str(legislator.get("chamber")) == "senate"
            and re.fullmatch(r"S\d{3}", str(legislator.get("bioguide_id") or ""))
        }
    )
    if not unresolved:
        return []
    return [
        "Historical Senate source mapping has unresolved LIS member ids without Bioguide identity: "
        + ", ".join(unresolved[:20])
        + ("..." if len(unresolved) > 20 else "")
    ]


def _source_dirs(congress: int) -> dict[str, dict[int, str]]:
    return {
        chamber: {
            session: str(session_cache_dir(congress=congress, chamber=chamber, session=session))
            for session in (1, 2)
        }
        for chamber in ("house", "senate")
    }


def _require_supported_congress(congress: int) -> None:
    if congress not in SUPPORTED_HISTORICAL_CONGRESSES:
        raise ValueError(f"Unsupported historical Congress: {congress}")


def _optional_text(element: ElementTree.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    value = element.text.strip()
    return value or None


def main() -> None:
    parser = argparse.ArgumentParser(description="Bounded historical Congress refresh.")
    parser.add_argument("--congress", type=int, default=118)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write-production", action="store_true")
    parser.add_argument("--precompute-dry-run", action="store_true")
    parser.add_argument("--write-precompute", action="store_true")
    parser.add_argument("--rollback-sql", type=Path)
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--approval-phrase")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    as_of = date.fromisoformat(args.as_of)
    output: dict[str, object] = {}
    if args.fetch:
        output["fetch"] = fetch_historical_congress_sources(congress=args.congress, overwrite=args.overwrite)
    if args.dry_run:
        output["dry_run"] = build_historical_refresh_plan(congress=args.congress).to_dict()
    if args.write_production:
        output["write"] = write_historical_refresh(
            congress=args.congress,
            approval_phrase=args.approval_phrase or "",
        )
    if args.rollback_sql:
        args.rollback_sql.write_text(build_historical_rollback_sql(congress=args.congress), encoding="utf-8")
        output["rollback_sql"] = str(args.rollback_sql)
    if args.precompute_dry_run:
        output["precompute_dry_run"] = build_precompute_plan(as_of=as_of).to_dict()
    if args.write_precompute:
        output["write_precompute"] = write_historical_precomputed_outputs(
            as_of=as_of,
            approval_phrase=args.approval_phrase or "",
        )
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
