import argparse
from dataclasses import dataclass
from datetime import date

from app.etl.fetch_sources import (
    fetch_congress_bill_metadata,
    fetch_house_clerk_members,
    fetch_house_clerk_roll_calls,
    fetch_senate_members,
    fetch_senate_vote_files,
    resolve_congress_api_key,
)
from app.etl.run_all import DEFAULT_AS_OF_DATE
from app.etl.seed import run_etl_and_persist


@dataclass(frozen=True)
class LivePipelineResult:
    house_rolls_fetched: int
    senate_rolls_fetched: int
    congress_bills_fetched: int
    persisted_source: str
    persisted_rows: dict[str, int]


def run_live_pipeline(
    *,
    house_year: int | None,
    house_roll_numbers: list[int],
    senate_congress: int | None,
    senate_session: int | None,
    senate_roll_numbers: list[int],
    bill_refs: list[tuple[int, str, int]],
    congress_api_key: str | None,
    as_of: date = DEFAULT_AS_OF_DATE,
) -> LivePipelineResult:
    if house_roll_numbers and senate_roll_numbers:
        raise ValueError("run_live_pipeline currently supports either House or Senate cache persistence per run")

    house_fetch_count = 0
    senate_fetch_count = 0
    bill_fetch_count = 0

    if house_roll_numbers:
        if house_year is None:
            raise ValueError("house_year is required when house_roll_numbers are provided")
        fetch_house_clerk_members()
        fetch_house_clerk_roll_calls(year=house_year, roll_numbers=house_roll_numbers)
        house_fetch_count = len(house_roll_numbers)

    if senate_roll_numbers:
        if senate_congress is None or senate_session is None:
            raise ValueError("senate_congress and senate_session are required when senate_roll_numbers are provided")
        fetch_senate_members()
        fetch_senate_vote_files(
            congress=senate_congress,
            session=senate_session,
            roll_numbers=senate_roll_numbers,
        )
        senate_fetch_count = len(senate_roll_numbers)

    if bill_refs:
        api_key = resolve_congress_api_key(congress_api_key)
        for congress, bill_type, bill_number in bill_refs:
            fetch_congress_bill_metadata(
                congress=congress,
                bill_type=bill_type,
                bill_number=bill_number,
                api_key=api_key,
            )
        bill_fetch_count = len(bill_refs)

    persist_source = "house_clerk_cache" if house_roll_numbers else "senate_xml_cache"
    persist_result = run_etl_and_persist(source=persist_source, as_of=as_of)

    return LivePipelineResult(
        house_rolls_fetched=house_fetch_count,
        senate_rolls_fetched=senate_fetch_count,
        congress_bills_fetched=bill_fetch_count,
        persisted_source=persist_source,
        persisted_rows={
            "legislators": persist_result.legislators_seeded,
            "bills": persist_result.bills_seeded,
            "roll_calls": persist_result.roll_calls_seeded,
            "votes_cast": persist_result.votes_seeded,
            "vote_classifications": persist_result.classifications_seeded,
            "fingerprints": persist_result.fingerprints_seeded,
            "chamber_medians": persist_result.chamber_medians_seeded,
            "drift_scores": persist_result.drift_scores_seeded,
            "summaries": persist_result.summaries_seeded,
            "zip_district_map": persist_result.zip_mappings_seeded,
        },
    )


def parse_bill_ref(value: str) -> tuple[int, str, int]:
    parts = value.split(":")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("Bill refs must be in congress:bill_type:bill_number form")
    congress, bill_type, bill_number = parts
    return int(congress), bill_type.lower(), int(bill_number)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--house-year", type=int)
    parser.add_argument("--house-roll", type=int, action="append", default=[])
    parser.add_argument("--senate-congress", type=int)
    parser.add_argument("--senate-session", type=int)
    parser.add_argument("--senate-roll", type=int, action="append", default=[])
    parser.add_argument("--bill", type=parse_bill_ref, action="append", default=[])
    parser.add_argument("--congress-api-key")
    args = parser.parse_args()

    result = run_live_pipeline(
        house_year=args.house_year,
        house_roll_numbers=args.house_roll,
        senate_congress=args.senate_congress,
        senate_session=args.senate_session,
        senate_roll_numbers=args.senate_roll,
        bill_refs=args.bill,
        congress_api_key=args.congress_api_key,
    )
    print(result)


if __name__ == "__main__":
    main()
