from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.classification.classifier import classify_vote
from app.classification.eligibility import evaluate_eligibility
from app.db import get_connection
from app.etl.fetch_sources import (
    HOUSE_CLERK_CACHE_DIR,
    SENATE_XML_CACHE_DIR,
    fetch_house_clerk_members,
    fetch_house_clerk_roll_calls,
    fetch_senate_members,
    fetch_senate_vote_files,
)
from app.etl.house_clerk_adapter import HOUSE_CLERK_SAMPLE_DIR, load_house_clerk_bundle
from app.etl.interpret import interpret_roll_call
from app.etl.senate_xml_adapter import SENATE_XML_SAMPLE_DIR, load_senate_xml_bundle
from app.etl.types import FixtureBundle
from app.etl.vote_context import build_vote_contexts


CURRENT_CONGRESS = 119
CLASSIFICATION_VERSION = "v1"
INTERPRETATION_VERSION = "interpretation_v1"
CONTEXT_VERSION = "vote_context_v1"
SENATE_LIS_BIOGUIDE_ALIASES = {
    # Senate 2026 vote XML uses LIS S419 for Markwayne Mullin, while production
    # and Bioguide identify him as M001190. The official Senate member file
    # omitted this LIS mapping during the refresh.
    "S419": "M001190",
}
APPROVAL_PHRASE = (
    "Approve current-Congress freshness refresh for supported 119th Congress 2026 House and Senate "
    "fact, classification, and deterministic interpretation rows, with session-aware roll-call identity, "
    "rollback generated before writes, unsupported categories deferred, procedural context non-counting, "
    "not-voting excluded, and no support/opposition/readiness/alignment methodology changes."
)


@dataclass(frozen=True)
class ProductionState:
    existing_roll_keys: set[tuple[str, int, int, int]]
    existing_bill_keys: set[tuple[int, str, int]]
    legislator_ids_by_bioguide: dict[str, int]
    existing_classification_roll_ids: set[int]
    existing_interpretation_roll_ids: set[int]


@dataclass(frozen=True)
class RefreshPlan:
    source_dirs: dict[str, str]
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
            "source_dirs": self.source_dirs,
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


def session_cache_dir(*, chamber: str, session: int) -> Path:
    if chamber == "house":
        year = 2025 if session == 1 else 2026
        return HOUSE_CLERK_CACHE_DIR / str(year)
    if chamber == "senate":
        return SENATE_XML_CACHE_DIR / f"{CURRENT_CONGRESS}_{session}"
    raise ValueError(f"Unsupported chamber: {chamber}")


def fetch_current_congress_sources(
    *,
    house_latest_roll: int,
    senate_latest_roll: int,
    house_session: int = 2,
    senate_session: int = 2,
    overwrite: bool = False,
) -> dict[str, object]:
    house_dir = session_cache_dir(chamber="house", session=house_session)
    senate_dir = session_cache_dir(chamber="senate", session=senate_session)
    house_dir.mkdir(parents=True, exist_ok=True)
    senate_dir.mkdir(parents=True, exist_ok=True)

    house_results = fetch_house_clerk_roll_calls(
        year=2025 if house_session == 1 else 2026,
        roll_numbers=list(range(1, house_latest_roll + 1)),
        output_dir=house_dir,
        overwrite=overwrite,
    )
    senate_results = fetch_senate_vote_files(
        congress=CURRENT_CONGRESS,
        session=senate_session,
        roll_numbers=list(range(1, senate_latest_roll + 1)),
        output_dir=senate_dir,
        overwrite=overwrite,
    )
    member_results = [
        fetch_house_clerk_members(output_dir=house_dir, overwrite=overwrite),
        fetch_senate_members(output_dir=senate_dir, overwrite=overwrite),
    ]
    return {
        "house_dir": str(house_dir),
        "senate_dir": str(senate_dir),
        "house": _download_summary(house_results),
        "senate": _download_summary(senate_results),
        "members": _download_summary(member_results),
    }


def build_refresh_plan(
    *,
    house_source_dir: Path,
    senate_source_dir: Path,
    production_state: ProductionState | None = None,
) -> RefreshPlan:
    production_state = production_state or load_production_state()
    house_bundle = load_house_clerk_bundle(source_dir=house_source_dir, fallback_dir=HOUSE_CLERK_SAMPLE_DIR)
    senate_bundle = load_senate_xml_bundle(source_dir=senate_source_dir, fallback_dir=SENATE_XML_SAMPLE_DIR)
    bundle = _merge_bundles(house_bundle, senate_bundle)
    import_rows = _build_import_rows(bundle=bundle, production_state=production_state)
    return RefreshPlan(
        source_dirs={"house": str(house_source_dir), "senate": str(senate_source_dir)},
        roll_keys=sorted(import_rows["roll_keys"]),
        planned_bill_inserts=len(import_rows["bills"]),
        planned_legislator_inserts=len(import_rows["legislators"]),
        planned_roll_call_inserts=len(import_rows["roll_calls"]),
        planned_votes_cast_inserts=len(import_rows["votes_cast"]),
        planned_vote_context_inserts=len(import_rows["vote_contexts"]),
        planned_classification_inserts=len(import_rows["vote_classifications"]),
        planned_interpretation_inserts=len(import_rows["vote_interpretations"]),
        deferred_rows=import_rows["deferred_rows"],
        errors=import_rows["errors"],
    )


def write_refresh(
    *,
    house_source_dir: Path,
    senate_source_dir: Path,
    approval_phrase: str,
) -> dict[str, object]:
    if approval_phrase != APPROVAL_PHRASE:
        raise ValueError("Approval phrase does not match the current-Congress refresh gate.")
    production_state = load_production_state()
    bundle = _merge_bundles(
        load_house_clerk_bundle(source_dir=house_source_dir, fallback_dir=HOUSE_CLERK_SAMPLE_DIR),
        load_senate_xml_bundle(source_dir=senate_source_dir, fallback_dir=SENATE_XML_SAMPLE_DIR),
    )
    import_rows = _build_import_rows(bundle=bundle, production_state=production_state)
    if import_rows["errors"]:
        raise ValueError(f"Refresh preflight failed: {import_rows['errors']}")

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


def load_production_state() -> ProductionState:
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT chamber, congress, session, rollcall_number FROM roll_calls")
            roll_keys = {(str(row[0]), int(row[1]), int(row[2]), int(row[3])) for row in cursor.fetchall()}
            cursor.execute("SELECT congress, bill_type, bill_number FROM bills")
            bill_keys = {(int(row[0]), str(row[1]).lower(), int(row[2])) for row in cursor.fetchall()}
            cursor.execute("SELECT bioguide_id, id FROM legislators")
            legislators = {str(row[0]): int(row[1]) for row in cursor.fetchall()}
            cursor.execute("SELECT roll_call_id FROM vote_classifications")
            classifications = {int(row[0]) for row in cursor.fetchall()}
            cursor.execute("SELECT roll_call_id FROM vote_interpretations")
            interpretations = {int(row[0]) for row in cursor.fetchall()}
    finally:
        connection.close()
    return ProductionState(
        existing_roll_keys=roll_keys,
        existing_bill_keys=bill_keys,
        legislator_ids_by_bioguide=legislators,
        existing_classification_roll_ids=classifications,
        existing_interpretation_roll_ids=interpretations,
    )


def _build_import_rows(*, bundle: FixtureBundle, production_state: ProductionState) -> dict[str, object]:
    roll_keys_by_internal_id: dict[str, tuple[str, int, int, int]] = {}
    bioguide_by_internal_legislator_id = {
        str(legislator["id"]): _normalized_bioguide_id(legislator)
        for legislator in bundle.legislators
    }
    legislators_by_bioguide = {
        _normalized_bioguide_id(legislator): {**legislator, "bioguide_id": _normalized_bioguide_id(legislator)}
        for legislator in bundle.legislators
    }
    bills_by_id = {str(bill["id"]): bill for bill in bundle.bills}
    candidate_roll_calls = []
    deferred_rows: list[dict[str, object]] = []
    errors: list[str] = []

    for roll_call in bundle.roll_calls:
        key = _roll_key(roll_call)
        if key in production_state.existing_roll_keys:
            continue
        bill = bills_by_id[str(roll_call["bill_ref"])]
        if _is_deferred_vote_type(roll_call):
            deferred_rows.append({"roll_key": list(key), "reason": "unsupported_or_deferred_vote_type"})
            continue
        candidate_roll_calls.append(roll_call)
        roll_keys_by_internal_id[str(roll_call["id"])] = key

    candidate_roll_ids = {str(row["id"]) for row in candidate_roll_calls}
    candidate_bill_refs = {str(row["bill_ref"]) for row in candidate_roll_calls}
    bills = [
        bill
        for bill in bundle.bills
        if str(bill["id"]) in candidate_bill_refs
        and (int(bill["congress"]), str(bill["bill_type"]).lower(), int(bill["bill_number"])) not in production_state.existing_bill_keys
    ]
    votes = [vote for vote in bundle.votes_cast if str(vote["roll_call_id"]) in candidate_roll_ids]
    missing_members = sorted(
        {
            bioguide_by_internal_legislator_id[str(vote["legislator_id"])]
            for vote in votes
            if bioguide_by_internal_legislator_id[str(vote["legislator_id"])] not in production_state.legislator_ids_by_bioguide
        }
    )
    new_legislators = [legislators_by_bioguide[bioguide_id] for bioguide_id in missing_members]

    contexts = build_vote_contexts(
        legislators=bundle.legislators,
        roll_calls=candidate_roll_calls,
        votes_cast=votes,
    )
    classifications = [
        _classify_roll_call(roll_call=roll_call, bill=bills_by_id[str(roll_call["bill_ref"])])
        for roll_call in candidate_roll_calls
    ]
    interpretations = [
        interpret_roll_call(
            roll_call=roll_call,
            classification=classification,
            interpretation_version=INTERPRETATION_VERSION,
        )
        for roll_call, classification in zip(candidate_roll_calls, classifications, strict=True)
    ]
    return {
        "roll_keys": set(roll_keys_by_internal_id.values()),
        "roll_keys_by_internal_id": roll_keys_by_internal_id,
        "bioguide_by_internal_legislator_id": bioguide_by_internal_legislator_id,
        "bill_keys": {
            (int(bill["congress"]), str(bill["bill_type"]).lower(), int(bill["bill_number"]))
            for bill in bundle.bills
            if str(bill["id"]) in candidate_bill_refs
        },
        "bills": bills,
        "legislators": new_legislators,
        "roll_calls": candidate_roll_calls,
        "votes_cast": votes,
        "vote_contexts": contexts,
        "vote_classifications": classifications,
        "vote_interpretations": interpretations,
        "deferred_rows": deferred_rows,
        "errors": errors,
    }


def _classify_roll_call(*, roll_call: dict[str, object], bill: dict[str, object]):
    eligibility = evaluate_eligibility(roll_call.get("question"), roll_call.get("description"))
    if not eligibility.is_eligible:
        return _Classification(
            roll_call_id=str(roll_call["id"]),
            is_eligible=False,
            eligibility_reason=eligibility.eligibility_reason,
            primary_domain=None,
            score_breakdown={},
            classification_version=CLASSIFICATION_VERSION,
        )
    classification = classify_vote(
        committee=bill.get("committee"),
        title=str(bill["title"]),
        summary=str(bill.get("summary") or ""),
        subject_tags=list(bill.get("subjects") or []),
        classification_version=CLASSIFICATION_VERSION,
    )
    return _Classification(
        roll_call_id=str(roll_call["id"]),
        is_eligible=classification.is_eligible,
        eligibility_reason=classification.eligibility_reason,
        primary_domain=classification.primary_domain,
        score_breakdown=classification.score_breakdown,
        classification_version=classification.classification_version,
    )


@dataclass(frozen=True)
class _Classification:
    roll_call_id: str
    is_eligible: bool
    eligibility_reason: str
    primary_domain: str | None
    score_breakdown: dict[str, dict[str, int]]
    classification_version: str


def _insert_bills(cursor, bills: list[dict[str, object]]) -> int:
    inserted = 0
    for bill in bills:
        cursor.execute(
            """
            INSERT INTO bills (congress, bill_type, bill_number, title, summary, committee, subjects)
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (congress, bill_type, bill_number) DO NOTHING
            RETURNING id
            """,
            (
                bill["congress"],
                bill["bill_type"],
                bill["bill_number"],
                bill["title"],
                bill.get("summary") or "",
                bill.get("committee"),
                json.dumps(bill.get("subjects") or []),
            ),
        )
        if cursor.fetchone() is not None:
            inserted += 1
    return inserted


def _insert_legislators(cursor, legislators: list[dict[str, object]]) -> int:
    inserted = 0
    for legislator in legislators:
        cursor.execute(
            """
            INSERT INTO legislators (bioguide_id, name_display, chamber, state, district, party, in_office)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (bioguide_id) DO NOTHING
            RETURNING id
            """,
            (
                legislator["bioguide_id"],
                legislator["name_display"],
                legislator["chamber"],
                legislator["state"],
                legislator["district"],
                legislator["party"],
                legislator["in_office"],
            ),
        )
        if cursor.fetchone() is not None:
            inserted += 1
    return inserted


def _insert_roll_calls(cursor, roll_calls: list[dict[str, object]], bill_id_map: dict[tuple[int, str, int], int]) -> int:
    inserted = 0
    for roll_call in roll_calls:
        bill_key = _bill_key_from_ref(str(roll_call["bill_ref"]))
        cursor.execute(
            """
            INSERT INTO roll_calls (
                chamber, congress, session, rollcall_number, vote_date,
                question, description, bill_id, source_url
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (chamber, congress, session, rollcall_number) DO NOTHING
            RETURNING id
            """,
            (
                roll_call["chamber"],
                roll_call["congress"],
                roll_call["session"],
                roll_call["rollcall_number"],
                roll_call["vote_date"],
                roll_call["question"],
                roll_call["description"],
                bill_id_map[bill_key],
                roll_call.get("source_url"),
            ),
        )
        if cursor.fetchone() is not None:
            inserted += 1
    return inserted


def _insert_votes_cast(cursor, votes, roll_keys_by_internal_id, bioguide_by_internal_legislator_id, roll_call_id_map, legislator_id_map) -> int:
    rows = [
        (
            roll_call_id_map[roll_keys_by_internal_id[str(vote["roll_call_id"])]],
            legislator_id_map[bioguide_by_internal_legislator_id[str(vote["legislator_id"])]],
            vote["position"],
        )
        for vote in votes
    ]
    cursor.executemany(
        """
        INSERT INTO votes_cast (roll_call_id, legislator_id, position)
        VALUES (%s, %s, %s)
        ON CONFLICT (roll_call_id, legislator_id) DO NOTHING
        """,
        rows,
    )
    return max(cursor.rowcount, 0)


def _insert_vote_contexts(cursor, contexts, roll_keys_by_internal_id, bioguide_by_internal_legislator_id, roll_call_id_map, legislator_id_map) -> int:
    rows = [
        (
            roll_call_id_map[roll_keys_by_internal_id[str(row["roll_call_id"])]],
            legislator_id_map[bioguide_by_internal_legislator_id[str(row["legislator_id"])]],
            row["chamber_session"],
            row["vote_type"],
            row["member_position"],
            row["final_result"],
            row["vote_margin"],
            row["winning_position"],
            json.dumps(row["party_vote_totals"]),
            row["member_party"],
            row["member_party_majority_position"],
            row["member_voted_with_party_majority"],
            row["member_voted_with_winning_side"],
            row["bipartisan_majority"],
            row["sponsor_party"],
            json.dumps(row["context_source_list"]),
            CONTEXT_VERSION,
        )
        for row in contexts
    ]
    cursor.executemany(
        """
        INSERT INTO vote_contexts (
            roll_call_id, legislator_id, chamber_session, vote_type, member_position,
            final_result, vote_margin, winning_position, party_vote_totals, member_party,
            member_party_majority_position, member_voted_with_party_majority,
            member_voted_with_winning_side, bipartisan_majority, sponsor_party,
            context_source_list, context_version
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
        ON CONFLICT (roll_call_id, legislator_id) DO NOTHING
        """,
        rows,
    )
    return max(cursor.rowcount, 0)


def _insert_classifications(cursor, classifications, roll_keys_by_internal_id, roll_call_id_map) -> int:
    rows = [
        (
            roll_call_id_map[roll_keys_by_internal_id[row.roll_call_id]],
            row.is_eligible,
            row.eligibility_reason,
            row.primary_domain,
            json.dumps(row.score_breakdown),
            row.classification_version,
        )
        for row in classifications
    ]
    cursor.executemany(
        """
        INSERT INTO vote_classifications (
            roll_call_id, is_eligible, eligibility_reason, primary_domain,
            score_breakdown, classification_version
        )
        VALUES (%s, %s, %s, %s, %s::jsonb, %s)
        ON CONFLICT (roll_call_id) DO NOTHING
        """,
        rows,
    )
    return max(cursor.rowcount, 0)


def _insert_interpretations(cursor, interpretations, roll_keys_by_internal_id, roll_call_id_map) -> int:
    rows = [
        (
            roll_call_id_map[roll_keys_by_internal_id[row.roll_call_id]],
            row.interpretation_status,
            row.support_position,
            row.oppose_position,
            row.interpretation_reason,
            row.source_url,
            row.interpretation_version,
            row.classification_version,
        )
        for row in interpretations
    ]
    cursor.executemany(
        """
        INSERT INTO vote_interpretations (
            roll_call_id, interpretation_status, support_position, oppose_position,
            interpretation_reason, source_url, interpretation_version, classification_version
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (roll_call_id) DO NOTHING
        """,
        rows,
    )
    return max(cursor.rowcount, 0)


def _fetch_bill_id_map(cursor, bill_keys: set[tuple[int, str, int]]) -> dict[tuple[int, str, int], int]:
    if not bill_keys:
        return {}
    congresses = [key[0] for key in bill_keys]
    bill_types = [key[1] for key in bill_keys]
    bill_numbers = [key[2] for key in bill_keys]
    cursor.execute(
        """
        SELECT id, congress, bill_type, bill_number
        FROM bills
        WHERE (congress, bill_type, bill_number)
          IN (SELECT * FROM UNNEST(%s::int[], %s::text[], %s::int[]))
        """,
        (congresses, bill_types, bill_numbers),
    )
    return {(int(row[1]), str(row[2]).lower(), int(row[3])): int(row[0]) for row in cursor.fetchall()}


def _fetch_roll_call_id_map(cursor, roll_keys: set[tuple[str, int, int, int]]) -> dict[tuple[str, int, int, int], int]:
    if not roll_keys:
        return {}
    chambers = [key[0] for key in roll_keys]
    congresses = [key[1] for key in roll_keys]
    sessions = [key[2] for key in roll_keys]
    roll_numbers = [key[3] for key in roll_keys]
    cursor.execute(
        """
        SELECT id, chamber, congress, session, rollcall_number
        FROM roll_calls
        WHERE (chamber, congress, session, rollcall_number)
          IN (SELECT * FROM UNNEST(%s::chamber[], %s::int[], %s::int[], %s::int[]))
        """,
        (chambers, congresses, sessions, roll_numbers),
    )
    return {(str(row[1]), int(row[2]), int(row[3]), int(row[4])): int(row[0]) for row in cursor.fetchall()}


def _fetch_legislator_id_map(cursor) -> dict[str, int]:
    cursor.execute("SELECT bioguide_id, id FROM legislators")
    return {str(row[0]): int(row[1]) for row in cursor.fetchall()}


def _merge_bundles(left: FixtureBundle, right: FixtureBundle) -> FixtureBundle:
    return FixtureBundle(
        legislators=_dedupe(left.legislators + right.legislators, key="bioguide_id"),
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


def _bill_key_from_ref(bill_ref: str) -> tuple[int, str, int]:
    parts = bill_ref.split("_")
    if len(parts) != 4 or parts[0] != "bill":
        raise ValueError(f"Unexpected bill_ref: {bill_ref}")
    return int(parts[1]), parts[2].lower(), int(parts[3])


def _roll_key(roll_call: dict[str, object]) -> tuple[str, int, int, int]:
    return (
        str(roll_call["chamber"]),
        int(roll_call["congress"]),
        int(roll_call["session"]),
        int(roll_call["rollcall_number"]),
    )


def _is_deferred_vote_type(roll_call: dict[str, object]) -> bool:
    text = f"{roll_call.get('question') or ''} {roll_call.get('description') or ''}".lower()
    return "pn" in text or "nomination" in text or "treaty" in text


def _normalized_bioguide_id(legislator: dict[str, object]) -> str:
    value = str(legislator["bioguide_id"])
    if str(legislator.get("chamber")) == "senate":
        return SENATE_LIS_BIOGUIDE_ALIASES.get(value, value)
    return value


def _download_summary(results) -> dict[str, int]:
    return {
        "total": len(results),
        "downloaded": sum(1 for result in results if not result.skipped),
        "cached": sum(1 for result in results if result.skipped),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bounded current-Congress freshness refresh.")
    parser.add_argument("--house-latest-roll", type=int, required=True)
    parser.add_argument("--senate-latest-roll", type=int, required=True)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write-production", action="store_true")
    parser.add_argument("--approval-phrase")
    args = parser.parse_args()

    house_dir = session_cache_dir(chamber="house", session=2)
    senate_dir = session_cache_dir(chamber="senate", session=2)
    output: dict[str, object] = {}
    if args.fetch:
        output["fetch"] = fetch_current_congress_sources(
            house_latest_roll=args.house_latest_roll,
            senate_latest_roll=args.senate_latest_roll,
        )
    if args.dry_run:
        output["dry_run"] = build_refresh_plan(house_source_dir=house_dir, senate_source_dir=senate_dir).to_dict()
    if args.write_production:
        output["write"] = write_refresh(
            house_source_dir=house_dir,
            senate_source_dir=senate_dir,
            approval_phrase=args.approval_phrase or "",
        )
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
