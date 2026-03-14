import argparse
from urllib.error import HTTPError
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

from app.etl.fetch_sources import (
    HOUSE_CLERK_CACHE_DIR,
    SENATE_XML_CACHE_DIR,
    fetch_congress_bill_metadata,
    fetch_house_clerk_members,
    fetch_house_clerk_roll_calls,
    fetch_senate_members,
    fetch_senate_vote_files,
    resolve_congress_api_key,
)
from app.etl.house_clerk_adapter import _parse_house_bill_reference
from app.etl.run_all import DEFAULT_AS_OF_DATE
from app.etl.senate_xml_adapter import _parse_senate_bill_reference
from app.etl.seed import run_etl_and_persist, run_etl_and_persist_sources


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

    inferred_bill_refs: set[tuple[int, str, int]] = set()
    if house_roll_numbers:
        inferred_bill_refs.update(
            infer_house_bill_refs_from_cache(
                roll_numbers=house_roll_numbers,
            )
        )
    if senate_roll_numbers:
        inferred_bill_refs.update(
            infer_senate_bill_refs_from_cache(
                roll_numbers=senate_roll_numbers,
            )
        )

    resolved_bill_refs = sorted(set(bill_refs) | inferred_bill_refs)

    if resolved_bill_refs:
        api_key = resolve_congress_api_key(congress_api_key)
        for congress, bill_type, bill_number in resolved_bill_refs:
            try:
                fetch_congress_bill_metadata(
                    congress=congress,
                    bill_type=bill_type,
                    bill_number=bill_number,
                    api_key=api_key,
                )
            except HTTPError as exc:
                # Chamber feeds can reference bill identifiers that the Congress metadata
                # endpoint does not currently resolve; only skip true not-found responses.
                if exc.code != 404:
                    raise
                continue
            bill_fetch_count += 1

    persist_sources = [
        source
        for source, enabled in (
            ("house_clerk_cache", bool(house_roll_numbers)),
            ("senate_xml_cache", bool(senate_roll_numbers)),
        )
        if enabled
    ]
    if not persist_sources:
        raise ValueError("At least one House or Senate roll number is required")

    if len(persist_sources) == 1:
        persist_result = run_etl_and_persist(source=persist_sources[0], as_of=as_of)
    else:
        persist_result = run_etl_and_persist_sources(sources=persist_sources, as_of=as_of)

    return LivePipelineResult(
        house_rolls_fetched=house_fetch_count,
        senate_rolls_fetched=senate_fetch_count,
        congress_bills_fetched=bill_fetch_count,
        persisted_source=persist_result.source,
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


def infer_house_bill_refs_from_cache(
    *,
    roll_numbers: list[int],
    source_dir: Path = HOUSE_CLERK_CACHE_DIR,
) -> set[tuple[int, str, int]]:
    bill_refs: set[tuple[int, str, int]] = set()
    for roll_number in roll_numbers:
        roll_path = source_dir / f"roll{roll_number:03d}.xml"
        if not roll_path.exists():
            continue

        root = ElementTree.parse(roll_path).getroot()
        metadata = root.find("vote-metadata")
        if metadata is None:
            continue

        congress_text = _optional_text(metadata.find("congress"))
        legis_num = _optional_text(metadata.find("legis-num"))
        if not congress_text or not legis_num:
            continue

        try:
            bill_type, bill_number = _parse_house_bill_reference(legis_num)
        except ValueError:
            continue

        bill_refs.add((int(congress_text), bill_type, bill_number))

    return bill_refs


def infer_senate_bill_refs_from_cache(
    *,
    roll_numbers: list[int],
    source_dir: Path = SENATE_XML_CACHE_DIR,
) -> set[tuple[int, str, int]]:
    bill_refs: set[tuple[int, str, int]] = set()
    for roll_number in roll_numbers:
        vote_path = source_dir / f"vote_{roll_number:03d}.xml"
        if not vote_path.exists():
            continue

        root = ElementTree.parse(vote_path).getroot()
        congress_text = _optional_text(root.find("congress"))
        if not congress_text:
            continue

        document_type = _optional_text(root.find("document/document_type"))
        document_number = _optional_text(root.find("document/document_number"))
        document_name = _optional_text(root.find("document/document_name"))
        try:
            bill_type, bill_number = _parse_senate_bill_reference(
                document_type=document_type,
                document_number=document_number,
                document_name=document_name,
            )
        except ValueError:
            continue

        bill_refs.add((int(congress_text), bill_type, bill_number))

    return bill_refs


def parse_bill_ref(value: str) -> tuple[int, str, int]:
    parts = value.split(":")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("Bill refs must be in congress:bill_type:bill_number form")
    congress, bill_type, bill_number = parts
    return int(congress), bill_type.lower(), int(bill_number)


def _optional_text(element: ElementTree.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    value = element.text.strip()
    return value or None


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
