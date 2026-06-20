import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from app.db import get_connection
from app.etl.fetch_sources import SENATE_XML_CACHE_DIR
from app.etl.senate_xml_adapter import (
    SENATE_XML_SAMPLE_DIR,
    _parse_members,
    _parse_roll_call,
    _resolve_source_file,
)
from app.etl.vote_context import build_vote_contexts


SUPPORTED_FACT_CATEGORIES = {"bill-centered legislative vote"}
SUPPORTED_FACT_BILL_TYPES = {"s", "sres", "sjres", "sconres", "hr", "hres", "hjres", "hconres"}
PHASE_14_APPROVAL_PHRASE = (
    "Approve production import of Phase 14 Senate fact-only package, capped at 75 roll calls "
    "and 7,500 votes_cast rows, with no vote_interpretations writes, no support/opposition "
    "changes, no alignment changes, no PN nominations, and no Senate amendments."
)
PHASE_14_MAX_ROLL_CALLS = 75
PHASE_14_MAX_VOTES_CAST = 7500


@dataclass(frozen=True)
class SenateProductionState:
    existing_roll_numbers: set[int]
    existing_bill_keys: set[tuple[int, str, int]]
    legislator_bioguide_ids: set[str]
    roll_numbers_with_interpretations: set[int]
    existing_roll_keys: set[tuple[int, int]] | None = None
    roll_keys_with_interpretations: set[tuple[int, int]] | None = None


@dataclass(frozen=True)
class SenateFactDryRunResult:
    manifest_path: str
    candidate_roll_numbers: list[int]
    planned_bill_inserts: int
    planned_roll_call_inserts: int
    planned_votes_cast_inserts: int
    planned_vote_context_inserts: int
    planned_vote_interpretation_inserts: int
    planned_vote_interpretation_updates: int
    planned_vote_interpretation_deletes: int
    skipped_existing_roll_calls: list[int]
    unsupported_roll_numbers: list[int]
    parse_failures: list[dict[str, object]]
    member_mapping_failures: list[dict[str, object]]
    bill_mapping_failures: list[dict[str, object]]
    errors: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "manifest_path": self.manifest_path,
            "candidate_roll_numbers": self.candidate_roll_numbers,
            "planned_inserts": {
                "bills": self.planned_bill_inserts,
                "roll_calls": self.planned_roll_call_inserts,
                "votes_cast": self.planned_votes_cast_inserts,
                "vote_contexts": self.planned_vote_context_inserts,
                "vote_interpretations": self.planned_vote_interpretation_inserts,
            },
            "planned_vote_interpretation_updates": self.planned_vote_interpretation_updates,
            "planned_vote_interpretation_deletes": self.planned_vote_interpretation_deletes,
            "skipped_existing_roll_calls": self.skipped_existing_roll_calls,
            "unsupported_roll_numbers": self.unsupported_roll_numbers,
            "parse_failures": self.parse_failures,
            "member_mapping_failures": self.member_mapping_failures,
            "bill_mapping_failures": self.bill_mapping_failures,
            "errors": self.errors,
            "safe_to_request_import_approval": not self.errors,
        }


@dataclass(frozen=True)
class SenateFactImportResult:
    dry_run: SenateFactDryRunResult
    inserted_bills: int
    inserted_roll_calls: int
    inserted_votes_cast: int
    inserted_vote_contexts: int
    inserted_vote_interpretations: int
    updated_vote_interpretations: int
    deleted_vote_interpretations: int
    skipped_existing_roll_calls: list[int]

    def to_dict(self) -> dict[str, object]:
        return {
            "dry_run": self.dry_run.to_dict(),
            "actual_counts": {
                "inserted_bills": self.inserted_bills,
                "inserted_roll_calls": self.inserted_roll_calls,
                "inserted_votes_cast": self.inserted_votes_cast,
                "inserted_vote_contexts": self.inserted_vote_contexts,
                "inserted_vote_interpretations": self.inserted_vote_interpretations,
                "updated_vote_interpretations": self.updated_vote_interpretations,
                "deleted_vote_interpretations": self.deleted_vote_interpretations,
            },
            "skipped_existing_roll_calls": self.skipped_existing_roll_calls,
        }


def run_senate_fact_dry_run(
    *,
    manifest_path: Path,
    senate_xml_dir: Path = SENATE_XML_CACHE_DIR,
    production_state: SenateProductionState | None = None,
    skip_existing: bool = False,
    include_vote_contexts: bool = True,
) -> SenateFactDryRunResult:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing Senate fact manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidates = manifest.get("included_candidate_roll_calls")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Manifest must include non-empty included_candidate_roll_calls.")

    member_tree = ElementTree.parse(_resolve_source_file(senate_xml_dir, "members.xml", SENATE_XML_SAMPLE_DIR))
    legislators_with_lis = _parse_members(member_tree)
    legislators_by_lis = {
        str(legislator["lis_member_id"]): dict(legislator)
        for legislator in legislators_with_lis
    }
    supplemental_legislators: list[dict[str, object]] = []
    bill_lookup: dict[tuple[int, str, int], dict[str, object]] = {}

    candidate_roll_numbers: list[int] = []
    skipped_existing: list[int] = []
    unsupported_roll_numbers: list[int] = []
    parse_failures: list[dict[str, object]] = []
    member_mapping_failures: list[dict[str, object]] = []
    bill_mapping_failures: list[dict[str, object]] = []
    errors: list[str] = []
    planned_bills: set[tuple[int, str, int]] = set()
    parsed_roll_calls: list[dict[str, object]] = []
    parsed_votes: list[dict[str, object]] = []

    for candidate in candidates:
        roll_number = int(candidate.get("roll_number") or 0)
        candidate_roll_numbers.append(roll_number)

        if candidate.get("category") not in SUPPORTED_FACT_CATEGORIES:
            unsupported_roll_numbers.append(roll_number)
            errors.append(f"Roll {roll_number} has unsupported category {candidate.get('category')!r}.")
            continue
        is_eligible = bool(
            candidate.get("eligible_for_phase_14_import")
            or candidate.get("eligible_for_phase_11_first_load")
        )
        if not is_eligible:
            unsupported_roll_numbers.append(roll_number)
            errors.append(f"Roll {roll_number} is not marked eligible for fact import.")
            continue

        congress = int(candidate.get("congress") or 0)
        vote_date = str(candidate.get("date") or "")
        roll_key = _candidate_roll_key(candidate)
        if congress != 119 or not vote_date.startswith("2025-"):
            unsupported_roll_numbers.append(roll_number)
            errors.append(f"Roll {roll_number} is outside the 119th Congress / 2025 scope.")
            continue

        manifest_bill_ref = (candidate.get("document") or {}).get("parsed_bill_ref") or {}
        manifest_bill_type = str(manifest_bill_ref.get("bill_type") or "").lower()
        if manifest_bill_type not in SUPPORTED_FACT_BILL_TYPES:
            unsupported_roll_numbers.append(roll_number)
            errors.append(f"Roll {roll_number} has unsupported fact-only bill type {manifest_bill_type!r}.")
            continue

        if production_state and roll_key in _roll_keys_with_interpretations(production_state):
            errors.append(f"Roll {roll_number} already has vote_interpretations rows; dry run fails closed.")
            continue

        if production_state and roll_key in _existing_roll_keys(production_state):
            if skip_existing:
                skipped_existing.append(roll_number)
                continue
            errors.append(f"Roll {roll_number} is already present in production; pass explicit skip-existing behavior.")
            continue

        vote_path = senate_xml_dir / f"vote_{roll_number:03d}.xml"
        if not vote_path.exists():
            parse_failures.append({"roll_number": roll_number, "error": f"Missing XML file: {vote_path}"})
            errors.append(f"Roll {roll_number} XML file is missing.")
            continue

        try:
            roll_call, bill, votes = _parse_roll_call(
                ElementTree.parse(vote_path),
                legislators_by_lis=legislators_by_lis,
                supplemental_legislators=supplemental_legislators,
                congress_bill_lookup=bill_lookup,
            )
        except Exception as error:
            parse_failures.append({"roll_number": roll_number, "error": str(error)})
            errors.append(f"Roll {roll_number} could not be parsed: {error}")
            continue

        bill_key = (int(bill["congress"]), str(bill["bill_type"]).lower(), int(bill["bill_number"]))
        if bill_key[0] != 119 or not str(roll_call["vote_date"]).startswith("2025-"):
            errors.append(f"Roll {roll_number} parsed outside the 119th Congress / 2025 scope.")
            continue
        if bill_key[1] not in SUPPORTED_FACT_BILL_TYPES:
            bill_mapping_failures.append({"roll_number": roll_number, "bill_key": list(bill_key)})
            errors.append(f"Roll {roll_number} parsed to unsupported bill key {bill_key}.")
            continue

        if production_state:
            missing_votes = _find_missing_production_legislators(
                votes=votes,
                legislators_by_lis=legislators_by_lis,
                production_bioguide_ids=production_state.legislator_bioguide_ids,
            )
            if missing_votes:
                member_mapping_failures.append(
                    {
                        "roll_number": roll_number,
                        "missing_bioguide_ids": sorted(missing_votes),
                    }
                )
                errors.append(f"Roll {roll_number} has member votes without production legislator mapping.")
                continue

        parsed_roll_calls.append(roll_call)
        parsed_votes.extend(votes)
        if not production_state or bill_key not in production_state.existing_bill_keys:
            planned_bills.add(bill_key)

    planned_contexts = (
        build_vote_contexts(
            legislators=[
                {
                    key: value
                    for key, value in legislator.items()
                    if key != "lis_member_id"
                }
                for legislator in legislators_by_lis.values()
            ],
            roll_calls=parsed_roll_calls,
            votes_cast=parsed_votes,
        )
        if include_vote_contexts and parsed_roll_calls
        else []
    )

    return SenateFactDryRunResult(
        manifest_path=str(manifest_path),
        candidate_roll_numbers=candidate_roll_numbers,
        planned_bill_inserts=len(planned_bills),
        planned_roll_call_inserts=len(parsed_roll_calls),
        planned_votes_cast_inserts=len(parsed_votes),
        planned_vote_context_inserts=len(planned_contexts),
        planned_vote_interpretation_inserts=0,
        planned_vote_interpretation_updates=0,
        planned_vote_interpretation_deletes=0,
        skipped_existing_roll_calls=skipped_existing,
        unsupported_roll_numbers=unsupported_roll_numbers,
        parse_failures=parse_failures,
        member_mapping_failures=member_mapping_failures,
        bill_mapping_failures=bill_mapping_failures,
        errors=errors,
    )


def run_senate_fact_import(
    *,
    manifest_path: Path,
    approval_phrase: str,
    senate_xml_dir: Path = SENATE_XML_CACHE_DIR,
    skip_existing: bool = False,
    include_vote_contexts: bool = True,
) -> SenateFactImportResult:
    if approval_phrase != PHASE_14_APPROVAL_PHRASE:
        raise ValueError("Approval phrase is missing or does not exactly match the Phase 14 approval gate.")

    production_state = load_production_state_for_manifest(manifest_path=manifest_path)
    dry_run = run_senate_fact_dry_run(
        manifest_path=manifest_path,
        senate_xml_dir=senate_xml_dir,
        production_state=production_state,
        skip_existing=skip_existing,
        include_vote_contexts=include_vote_contexts,
    )
    if dry_run.errors:
        raise ValueError(f"Dry-run validation failed; refusing production import: {dry_run.errors}")
    if dry_run.planned_roll_call_inserts > PHASE_14_MAX_ROLL_CALLS:
        raise ValueError("Dry-run exceeds the Phase 14 roll-call cap; refusing production import.")
    if dry_run.planned_votes_cast_inserts > PHASE_14_MAX_VOTES_CAST:
        raise ValueError("Dry-run exceeds the Phase 14 votes_cast cap; refusing production import.")
    if (
        dry_run.planned_vote_interpretation_inserts
        or dry_run.planned_vote_interpretation_updates
        or dry_run.planned_vote_interpretation_deletes
    ):
        raise ValueError("Dry-run planned vote_interpretations writes; refusing production import.")

    import_rows = _build_import_rows(
        manifest_path=manifest_path,
        senate_xml_dir=senate_xml_dir,
        production_state=production_state,
        skip_existing=skip_existing,
        include_vote_contexts=include_vote_contexts,
    )

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            inserted_bills = _insert_bills(cursor, import_rows["bills"])
            bill_id_map = _fetch_bill_id_map(cursor, list(import_rows["bill_keys"]))
            inserted_roll_calls = _insert_roll_calls(cursor, import_rows["roll_calls"], bill_id_map)
            roll_call_id_map = _fetch_roll_call_id_map(cursor, import_rows["roll_keys"])
            legislator_id_map = _fetch_legislator_id_map(cursor)
            inserted_votes_cast = _insert_votes_cast(
                cursor,
                import_rows["votes_cast"],
                import_rows["roll_keys_by_internal_id"],
                import_rows["bioguide_by_internal_legislator_id"],
                roll_call_id_map,
                legislator_id_map,
            )
            inserted_vote_contexts = _insert_vote_contexts(
                cursor,
                import_rows["vote_contexts"],
                import_rows["roll_keys_by_internal_id"],
                import_rows["bioguide_by_internal_legislator_id"],
                roll_call_id_map,
                legislator_id_map,
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return SenateFactImportResult(
        dry_run=dry_run,
        inserted_bills=inserted_bills,
        inserted_roll_calls=inserted_roll_calls,
        inserted_votes_cast=inserted_votes_cast,
        inserted_vote_contexts=inserted_vote_contexts,
        inserted_vote_interpretations=0,
        updated_vote_interpretations=0,
        deleted_vote_interpretations=0,
        skipped_existing_roll_calls=dry_run.skipped_existing_roll_calls,
    )


def load_production_state_for_manifest(*, manifest_path: Path) -> SenateProductionState:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    roll_numbers = [
        int(candidate["roll_number"])
        for candidate in manifest.get("included_candidate_roll_calls", [])
    ]
    bill_keys = [
        (
            int(candidate.get("congress") or 119),
            str(((candidate.get("document") or {}).get("parsed_bill_ref") or {}).get("bill_type") or "").lower(),
            int(((candidate.get("document") or {}).get("parsed_bill_ref") or {}).get("bill_number") or 0),
        )
        for candidate in manifest.get("included_candidate_roll_calls", [])
    ]

    connection = get_connection()
    try:
        connection.execute("SET default_transaction_read_only = on")
        roll_keys = [
            _candidate_roll_key(candidate)
            for candidate in manifest.get("included_candidate_roll_calls", [])
        ]
        existing_roll_keys = _fetch_existing_roll_keys(connection, roll_keys)
        existing_rolls = {roll_number for _, roll_number in existing_roll_keys}
        existing_bills = _fetch_existing_bill_keys(connection, bill_keys)
        legislator_ids = _fetch_legislator_bioguide_ids(connection)
        interpreted_roll_keys = _fetch_roll_keys_with_interpretations(connection, roll_keys)
        interpreted_rolls = {roll_number for _, roll_number in interpreted_roll_keys}
    finally:
        connection.close()

    return SenateProductionState(
        existing_roll_numbers=existing_rolls,
        existing_bill_keys=existing_bills,
        legislator_bioguide_ids=legislator_ids,
        roll_numbers_with_interpretations=interpreted_rolls,
        existing_roll_keys=existing_roll_keys,
        roll_keys_with_interpretations=interpreted_roll_keys,
    )


def _build_import_rows(
    *,
    manifest_path: Path,
    senate_xml_dir: Path,
    production_state: SenateProductionState,
    skip_existing: bool,
    include_vote_contexts: bool,
) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidates = manifest.get("included_candidate_roll_calls")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Manifest must include non-empty included_candidate_roll_calls.")

    member_tree = ElementTree.parse(_resolve_source_file(senate_xml_dir, "members.xml", SENATE_XML_SAMPLE_DIR))
    legislators_with_lis = _parse_members(member_tree)
    legislators_by_lis = {
        str(legislator["lis_member_id"]): dict(legislator)
        for legislator in legislators_with_lis
    }
    supplemental_legislators: list[dict[str, object]] = []
    parsed_roll_calls: list[dict[str, object]] = []
    parsed_votes: list[dict[str, object]] = []
    bills: dict[tuple[int, str, int], dict[str, object]] = {}
    roll_numbers_by_internal_id: dict[str, int] = {}
    roll_keys_by_internal_id: dict[str, tuple[int, int]] = {}
    bioguide_by_internal_legislator_id: dict[str, str] = {
        str(legislator["id"]): str(legislator["bioguide_id"])
        for legislator in legislators_by_lis.values()
    }

    for candidate in candidates:
        roll_number = int(candidate["roll_number"])
        roll_key = _candidate_roll_key(candidate)
        if roll_key in _existing_roll_keys(production_state):
            if skip_existing:
                continue
            raise ValueError(f"Roll {roll_number} is already present in production.")

        vote_path = senate_xml_dir / f"vote_{roll_number:03d}.xml"
        roll_call, bill, votes = _parse_roll_call(
            ElementTree.parse(vote_path),
            legislators_by_lis=legislators_by_lis,
            supplemental_legislators=supplemental_legislators,
            congress_bill_lookup={},
        )
        bill_key = (int(bill["congress"]), str(bill["bill_type"]).lower(), int(bill["bill_number"]))
        if bill_key[0] != 119 or not str(roll_call["vote_date"]).startswith("2025-"):
            raise ValueError(f"Roll {roll_number} parsed outside the 119th Congress / 2025 scope.")
        if bill_key[1] not in SUPPORTED_FACT_BILL_TYPES:
            raise ValueError(f"Roll {roll_number} parsed to unsupported bill key {bill_key}.")

        parsed_roll_calls.append(roll_call)
        parsed_votes.extend(votes)
        bills[bill_key] = bill
        roll_numbers_by_internal_id[str(roll_call["id"])] = roll_number
        roll_keys_by_internal_id[str(roll_call["id"])] = roll_key
        bioguide_by_internal_legislator_id.update(
            {
                str(legislator["id"]): str(legislator["bioguide_id"])
                for legislator in supplemental_legislators
            }
        )

    contexts = (
        build_vote_contexts(
            legislators=[
                {
                    key: value
                    for key, value in legislator.items()
                    if key != "lis_member_id"
                }
                for legislator in legislators_by_lis.values()
            ],
            roll_calls=parsed_roll_calls,
            votes_cast=parsed_votes,
        )
        if include_vote_contexts and parsed_roll_calls
        else []
    )

    return {
        "bills": list(bills.values()),
        "bill_keys": set(bills),
        "roll_calls": parsed_roll_calls,
        "roll_numbers": sorted(roll_numbers_by_internal_id.values()),
        "roll_keys": sorted(set(roll_keys_by_internal_id.values())),
        "roll_numbers_by_internal_id": roll_numbers_by_internal_id,
        "roll_keys_by_internal_id": roll_keys_by_internal_id,
        "bioguide_by_internal_legislator_id": bioguide_by_internal_legislator_id,
        "votes_cast": parsed_votes,
        "vote_contexts": contexts,
    }


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


def _insert_roll_calls(
    cursor,
    roll_calls: list[dict[str, object]],
    bill_id_map: dict[tuple[int, str, int], int],
) -> int:
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
                roll_call.get("session"),
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


def _insert_votes_cast(
    cursor,
    votes: list[dict[str, object]],
    roll_keys_by_internal_id: dict[str, tuple[int, int]],
    bioguide_by_internal_legislator_id: dict[str, str],
    roll_call_id_map: dict[tuple[int, int], int],
    legislator_id_map: dict[str, int],
) -> int:
    inserted = 0
    for vote in votes:
        roll_key = roll_keys_by_internal_id[str(vote["roll_call_id"])]
        bioguide_id = bioguide_by_internal_legislator_id[str(vote["legislator_id"])]
        cursor.execute(
            """
            INSERT INTO votes_cast (roll_call_id, legislator_id, position)
            VALUES (%s, %s, %s)
            ON CONFLICT (roll_call_id, legislator_id) DO NOTHING
            RETURNING id
            """,
            (
                roll_call_id_map[roll_key],
                legislator_id_map[bioguide_id],
                vote["position"],
            ),
        )
        if cursor.fetchone() is not None:
            inserted += 1
    return inserted


def _insert_vote_contexts(
    cursor,
    contexts: list[dict[str, object]],
    roll_keys_by_internal_id: dict[str, tuple[int, int]],
    bioguide_by_internal_legislator_id: dict[str, str],
    roll_call_id_map: dict[tuple[int, int], int],
    legislator_id_map: dict[str, int],
) -> int:
    inserted = 0
    for row in contexts:
        roll_key = roll_keys_by_internal_id[str(row["roll_call_id"])]
        bioguide_id = bioguide_by_internal_legislator_id[str(row["legislator_id"])]
        cursor.execute(
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
            RETURNING roll_call_id
            """,
            (
                roll_call_id_map[roll_key],
                legislator_id_map[bioguide_id],
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
                row["context_version"],
            ),
        )
        if cursor.fetchone() is not None:
            inserted += 1
    return inserted


def _fetch_bill_id_map(cursor, bill_keys: list[tuple[int, str, int]]) -> dict[tuple[int, str, int], int]:
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
    return {
        (int(row[1]), str(row[2]).lower(), int(row[3])): int(row[0])
        for row in cursor.fetchall()
    }


def _fetch_roll_call_id_map(cursor, roll_keys: list[tuple[int, int]]) -> dict[tuple[int, int], int]:
    if not roll_keys:
        return {}
    sessions = [key[0] for key in roll_keys]
    roll_numbers = [key[1] for key in roll_keys]
    cursor.execute(
        """
        SELECT id, session, rollcall_number
        FROM roll_calls
        WHERE chamber = 'senate'
          AND congress = 119
          AND (session, rollcall_number)
            IN (SELECT * FROM UNNEST(%s::int[], %s::int[]))
        """,
        (sessions, roll_numbers),
    )
    return {(int(row[1]), int(row[2])): int(row[0]) for row in cursor.fetchall()}


def _fetch_legislator_id_map(cursor) -> dict[str, int]:
    cursor.execute("SELECT id, bioguide_id FROM legislators WHERE chamber = 'senate'")
    return {str(row[1]): int(row[0]) for row in cursor.fetchall()}


def _bill_key_from_ref(bill_ref: str) -> tuple[int, str, int]:
    match = bill_ref.split("_")
    if len(match) != 4 or match[0] != "bill":
        raise ValueError(f"Unexpected bill_ref format: {bill_ref}")
    return int(match[1]), match[2].lower(), int(match[3])


def _fetch_existing_roll_keys(connection, roll_keys: list[tuple[int, int]]) -> set[tuple[int, int]]:
    if not roll_keys:
        return set()
    sessions = [key[0] for key in roll_keys]
    roll_numbers = [key[1] for key in roll_keys]
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT session, rollcall_number
            FROM roll_calls
            WHERE chamber = 'senate'
              AND congress = 119
              AND (session, rollcall_number)
                IN (SELECT * FROM UNNEST(%s::int[], %s::int[]))
            """,
            (sessions, roll_numbers),
        )
        return {(int(row[0]), int(row[1])) for row in cursor.fetchall()}


def _fetch_existing_bill_keys(connection, bill_keys: list[tuple[int, str, int]]) -> set[tuple[int, str, int]]:
    if not bill_keys:
        return set()
    congresses = [key[0] for key in bill_keys]
    bill_types = [key[1] for key in bill_keys]
    bill_numbers = [key[2] for key in bill_keys]
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT congress, bill_type, bill_number
            FROM bills
            WHERE (congress, bill_type, bill_number)
              IN (SELECT * FROM UNNEST(%s::int[], %s::text[], %s::int[]))
            """,
            (congresses, bill_types, bill_numbers),
        )
        return {(int(row[0]), str(row[1]).lower(), int(row[2])) for row in cursor.fetchall()}


def _fetch_legislator_bioguide_ids(connection) -> set[str]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT bioguide_id FROM legislators WHERE chamber = 'senate'")
        return {str(row[0]) for row in cursor.fetchall()}


def _fetch_roll_keys_with_interpretations(connection, roll_keys: list[tuple[int, int]]) -> set[tuple[int, int]]:
    if not roll_keys:
        return set()
    sessions = [key[0] for key in roll_keys]
    roll_numbers = [key[1] for key in roll_keys]
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT rc.session, rc.rollcall_number
            FROM roll_calls rc
            JOIN vote_interpretations vi
              ON vi.roll_call_id = rc.id
            WHERE rc.chamber = 'senate'
              AND rc.congress = 119
              AND (rc.session, rc.rollcall_number)
                IN (SELECT * FROM UNNEST(%s::int[], %s::int[]))
            """,
            (sessions, roll_numbers),
        )
        return {(int(row[0]), int(row[1])) for row in cursor.fetchall()}


def _candidate_roll_key(candidate: dict[str, object]) -> tuple[int, int]:
    return (_candidate_session(candidate), int(candidate.get("roll_number") or 0))


def _candidate_session(candidate: dict[str, object]) -> int:
    if candidate.get("session") is not None:
        return int(candidate["session"])
    vote_date = str(candidate.get("date") or "")
    if vote_date.startswith("2025-"):
        return 1
    if vote_date.startswith("2026-"):
        return 2
    raise ValueError(f"Cannot infer official Senate session for candidate date {vote_date!r}.")


def _existing_roll_keys(production_state: SenateProductionState) -> set[tuple[int, int]]:
    if production_state.existing_roll_keys is not None:
        return set(production_state.existing_roll_keys)
    return {(1, roll_number) for roll_number in production_state.existing_roll_numbers}


def _roll_keys_with_interpretations(production_state: SenateProductionState) -> set[tuple[int, int]]:
    if production_state.roll_keys_with_interpretations is not None:
        return set(production_state.roll_keys_with_interpretations)
    return {(1, roll_number) for roll_number in production_state.roll_numbers_with_interpretations}


def _find_missing_production_legislators(
    *,
    votes: list[dict[str, object]],
    legislators_by_lis: dict[str, dict[str, object]],
    production_bioguide_ids: set[str],
) -> set[str]:
    missing: set[str] = set()
    legislators_by_id = {
        str(legislator["id"]): legislator
        for legislator in legislators_by_lis.values()
    }
    for vote in votes:
        legislator = legislators_by_id.get(str(vote["legislator_id"]))
        if not legislator:
            missing.add(str(vote["legislator_id"]))
            continue
        bioguide_id = str(legislator.get("bioguide_id") or "")
        if bioguide_id not in production_bioguide_ids:
            missing.add(bioguide_id)
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry-run or import a bounded Senate fact-only manifest.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--senate-xml-dir", type=Path, default=SENATE_XML_CACHE_DIR)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--write-production", action="store_true")
    parser.add_argument("--production-read-only", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--no-vote-contexts", action="store_true")
    parser.add_argument("--approval-phrase")
    args = parser.parse_args()

    if args.write_production:
        result = run_senate_fact_import(
            manifest_path=args.manifest,
            senate_xml_dir=args.senate_xml_dir,
            approval_phrase=args.approval_phrase or "",
            skip_existing=args.skip_existing,
            include_vote_contexts=not args.no_vote_contexts,
        )
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return

    production_state = (
        load_production_state_for_manifest(manifest_path=args.manifest)
        if args.production_read_only
        else None
    )
    result = run_senate_fact_dry_run(
        manifest_path=args.manifest,
        senate_xml_dir=args.senate_xml_dir,
        production_state=production_state,
        skip_existing=args.skip_existing,
        include_vote_contexts=not args.no_vote_contexts,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    if result.errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
