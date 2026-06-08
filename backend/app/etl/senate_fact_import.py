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
SUPPORTED_PHASE_12_BILL_TYPES = {"hjres", "hconres"}


@dataclass(frozen=True)
class SenateProductionState:
    existing_roll_numbers: set[int]
    existing_bill_keys: set[tuple[int, str, int]]
    legislator_bioguide_ids: set[str]
    roll_numbers_with_interpretations: set[int]


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
        if not candidate.get("eligible_for_phase_11_first_load"):
            unsupported_roll_numbers.append(roll_number)
            errors.append(f"Roll {roll_number} is not marked eligible for first-load fact import.")
            continue

        manifest_bill_ref = (candidate.get("document") or {}).get("parsed_bill_ref") or {}
        manifest_bill_type = str(manifest_bill_ref.get("bill_type") or "").lower()
        if manifest_bill_type not in SUPPORTED_PHASE_12_BILL_TYPES:
            unsupported_roll_numbers.append(roll_number)
            errors.append(f"Roll {roll_number} has unsupported Phase 12 bill type {manifest_bill_type!r}.")
            continue

        if production_state and roll_number in production_state.roll_numbers_with_interpretations:
            errors.append(f"Roll {roll_number} already has vote_interpretations rows; dry run fails closed.")
            continue

        if production_state and roll_number in production_state.existing_roll_numbers:
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
        if bill_key[1] not in SUPPORTED_PHASE_12_BILL_TYPES:
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
        existing_rolls = _fetch_existing_roll_numbers(connection, roll_numbers)
        existing_bills = _fetch_existing_bill_keys(connection, bill_keys)
        legislator_ids = _fetch_legislator_bioguide_ids(connection)
        interpreted_rolls = _fetch_roll_numbers_with_interpretations(connection, roll_numbers)
    finally:
        connection.close()

    return SenateProductionState(
        existing_roll_numbers=existing_rolls,
        existing_bill_keys=existing_bills,
        legislator_bioguide_ids=legislator_ids,
        roll_numbers_with_interpretations=interpreted_rolls,
    )


def _fetch_existing_roll_numbers(connection, roll_numbers: list[int]) -> set[int]:
    if not roll_numbers:
        return set()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT rollcall_number
            FROM roll_calls
            WHERE chamber = 'senate'
              AND congress = 119
              AND rollcall_number = ANY(%s)
            """,
            (roll_numbers,),
        )
        return {int(row[0]) for row in cursor.fetchall()}


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


def _fetch_roll_numbers_with_interpretations(connection, roll_numbers: list[int]) -> set[int]:
    if not roll_numbers:
        return set()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT rc.rollcall_number
            FROM roll_calls rc
            JOIN vote_interpretations vi
              ON vi.roll_call_id = rc.id
            WHERE rc.chamber = 'senate'
              AND rc.congress = 119
              AND rc.rollcall_number = ANY(%s)
            """,
            (roll_numbers,),
        )
        return {int(row[0]) for row in cursor.fetchall()}


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
    parser = argparse.ArgumentParser(description="Dry-run a bounded Senate fact-only import manifest.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--senate-xml-dir", type=Path, default=SENATE_XML_CACHE_DIR)
    parser.add_argument("--dry-run", action="store_true", required=True)
    parser.add_argument("--production-read-only", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--no-vote-contexts", action="store_true")
    args = parser.parse_args()

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
