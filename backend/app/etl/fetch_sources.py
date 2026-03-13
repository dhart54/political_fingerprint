import argparse
from dataclasses import dataclass
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_USER_AGENT = "political-fingerprint/0.1"
BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_SOURCES_DIR = BACKEND_DIR / "data_sources"
CONGRESS_CACHE_DIR = DATA_SOURCES_DIR / "congress"
CONGRESS_BILL_CACHE_DIR = CONGRESS_CACHE_DIR / "bills"
HOUSE_CLERK_CACHE_DIR = DATA_SOURCES_DIR / "house_clerk"
SENATE_XML_CACHE_DIR = DATA_SOURCES_DIR / "senate_xml"


@dataclass(frozen=True)
class DownloadResult:
    source_url: str
    destination: Path
    bytes_written: int
    skipped: bool


def build_house_clerk_roll_url(*, year: int, roll_number: int) -> str:
    return f"https://clerk.house.gov/evs/{year}/roll{roll_number:03d}.xml"


def build_house_clerk_members_url() -> str:
    return "https://clerk.house.gov/xml/lists/MemberData.xml"


def build_senate_vote_url(*, congress: int, session: int, roll_number: int) -> str:
    return (
        "https://www.senate.gov/legislative/LIS/roll_call_votes/"
        f"vote{congress}{session}/vote_{congress}_{session}_{roll_number:05d}.xml"
    )


def build_senate_members_url(*, detailed: bool = False) -> str:
    if detailed:
        return "https://www.senate.gov/legislative/LIS_MEMBER/cvc_member_data.xml"
    return "https://www.senate.gov/general/contact_information/senators_cfm.xml"


def build_congress_bill_url(*, congress: int, bill_type: str, bill_number: int, api_key: str) -> str:
    query = urlencode({"format": "json", "api_key": api_key})
    return f"https://api.congress.gov/v3/bill/{congress}/{bill_type}/{bill_number}?{query}"


def fetch_house_clerk_roll_calls(
    *,
    year: int,
    roll_numbers: list[int],
    output_dir: Path,
    overwrite: bool = False,
) -> list[DownloadResult]:
    return [
        download_to_path(
            build_house_clerk_roll_url(year=year, roll_number=roll_number),
            output_dir / f"roll{roll_number:03d}.xml",
            overwrite=overwrite,
        )
        for roll_number in roll_numbers
    ]


def fetch_senate_vote_files(
    *,
    congress: int,
    session: int,
    roll_numbers: list[int],
    output_dir: Path,
    overwrite: bool = False,
) -> list[DownloadResult]:
    return [
        download_to_path(
            build_senate_vote_url(
                congress=congress,
                session=session,
                roll_number=roll_number,
            ),
            output_dir / f"vote_{roll_number:03d}.xml",
            overwrite=overwrite,
        )
        for roll_number in roll_numbers
    ]


def fetch_congress_bill_metadata(
    *,
    congress: int,
    bill_type: str,
    bill_number: int,
    api_key: str,
    output_dir: Path = CONGRESS_BILL_CACHE_DIR,
    overwrite: bool = False,
) -> DownloadResult:
    normalized_bill_type = bill_type.lower()
    return download_to_path(
        build_congress_bill_url(
            congress=congress,
            bill_type=normalized_bill_type,
            bill_number=bill_number,
            api_key=api_key,
        ),
        output_dir / f"{congress}_{normalized_bill_type}_{bill_number}.json",
        overwrite=overwrite,
    )


def fetch_house_clerk_members(
    *,
    output_dir: Path = HOUSE_CLERK_CACHE_DIR,
    overwrite: bool = False,
) -> DownloadResult:
    return download_to_path(
        build_house_clerk_members_url(),
        output_dir / "members.xml",
        overwrite=overwrite,
    )


def fetch_senate_members(
    *,
    detailed: bool = True,
    output_dir: Path = SENATE_XML_CACHE_DIR,
    overwrite: bool = False,
) -> DownloadResult:
    return download_to_path(
        build_senate_members_url(detailed=detailed),
        output_dir / "members.xml",
        overwrite=overwrite,
    )


def download_to_path(
    source_url: str,
    destination: Path,
    *,
    overwrite: bool = False,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> DownloadResult:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not overwrite:
        return DownloadResult(
            source_url=source_url,
            destination=destination,
            bytes_written=destination.stat().st_size,
            skipped=True,
        )

    request = Request(source_url, headers={"User-Agent": DEFAULT_USER_AGENT})
    with urlopen(request, timeout=timeout_seconds) as response:
        payload = response.read()

    with NamedTemporaryFile(delete=False, dir=destination.parent) as temp_file:
        temp_file.write(payload)
        temp_path = Path(temp_file.name)

    temp_path.replace(destination)

    return DownloadResult(
        source_url=source_url,
        destination=destination,
        bytes_written=len(payload),
        skipped=False,
    )


def resolve_congress_api_key(explicit_api_key: str | None = None) -> str:
    if explicit_api_key:
        return explicit_api_key
    api_key = os.getenv("CONGRESS_API_KEY")
    if api_key:
        return api_key
    raise ValueError("Congress API key is required. Set CONGRESS_API_KEY or pass --api-key.")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="source", required=True)

    house_parser = subparsers.add_parser("house")
    house_parser.add_argument("--year", type=int, required=True)
    house_parser.add_argument("--roll", type=int, action="append", dest="roll_numbers", required=True)
    house_parser.add_argument("--output-dir", type=Path, default=HOUSE_CLERK_CACHE_DIR)
    house_parser.add_argument("--overwrite", action="store_true")

    house_members_parser = subparsers.add_parser("house-members")
    house_members_parser.add_argument("--output-dir", type=Path, default=HOUSE_CLERK_CACHE_DIR)
    house_members_parser.add_argument("--overwrite", action="store_true")

    senate_parser = subparsers.add_parser("senate")
    senate_parser.add_argument("--congress", type=int, required=True)
    senate_parser.add_argument("--session", type=int, required=True)
    senate_parser.add_argument("--roll", type=int, action="append", dest="roll_numbers", required=True)
    senate_parser.add_argument("--output-dir", type=Path, default=SENATE_XML_CACHE_DIR)
    senate_parser.add_argument("--overwrite", action="store_true")

    senate_members_parser = subparsers.add_parser("senate-members")
    senate_members_parser.add_argument("--output-dir", type=Path, default=SENATE_XML_CACHE_DIR)
    senate_members_parser.add_argument("--overwrite", action="store_true")
    senate_members_parser.add_argument("--contact-only", action="store_true")

    congress_parser = subparsers.add_parser("congress-bill")
    congress_parser.add_argument("--congress", type=int, required=True)
    congress_parser.add_argument("--bill-type", required=True)
    congress_parser.add_argument("--bill-number", type=int, required=True)
    congress_parser.add_argument("--api-key")
    congress_parser.add_argument("--output-dir", type=Path, default=CONGRESS_BILL_CACHE_DIR)
    congress_parser.add_argument("--overwrite", action="store_true")

    args = parser.parse_args()

    if args.source == "house":
        results = fetch_house_clerk_roll_calls(
            year=args.year,
            roll_numbers=args.roll_numbers,
            output_dir=args.output_dir,
            overwrite=args.overwrite,
        )
    elif args.source == "house-members":
        results = [
            fetch_house_clerk_members(
                output_dir=args.output_dir,
                overwrite=args.overwrite,
            )
        ]
    elif args.source == "senate":
        results = fetch_senate_vote_files(
            congress=args.congress,
            session=args.session,
            roll_numbers=args.roll_numbers,
            output_dir=args.output_dir,
            overwrite=args.overwrite,
        )
    elif args.source == "senate-members":
        results = [
            fetch_senate_members(
                detailed=not args.contact_only,
                output_dir=args.output_dir,
                overwrite=args.overwrite,
            )
        ]
    else:
        results = [
            fetch_congress_bill_metadata(
                congress=args.congress,
                bill_type=args.bill_type,
                bill_number=args.bill_number,
                api_key=resolve_congress_api_key(args.api_key),
                output_dir=args.output_dir,
                overwrite=args.overwrite,
            )
        ]

    for result in results:
        status = "skipped" if result.skipped else "downloaded"
        print(
            {
                "status": status,
                "source_url": result.source_url,
                "destination": str(result.destination),
                "bytes_written": result.bytes_written,
            }
        )


if __name__ == "__main__":
    main()
