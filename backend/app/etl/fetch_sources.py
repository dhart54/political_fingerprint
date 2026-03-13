import argparse
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_USER_AGENT = "political-fingerprint/0.1"
BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_SOURCES_DIR = BACKEND_DIR / "data_sources"
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


def build_senate_vote_url(*, congress: int, session: int, roll_number: int) -> str:
    return (
        "https://www.senate.gov/legislative/LIS/roll_call_votes/"
        f"vote{congress}{session}/vote_{congress}_{session}_{roll_number:05d}.xml"
    )


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


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="source", required=True)

    house_parser = subparsers.add_parser("house")
    house_parser.add_argument("--year", type=int, required=True)
    house_parser.add_argument("--roll", type=int, action="append", dest="roll_numbers", required=True)
    house_parser.add_argument("--output-dir", type=Path, default=HOUSE_CLERK_CACHE_DIR)
    house_parser.add_argument("--overwrite", action="store_true")

    senate_parser = subparsers.add_parser("senate")
    senate_parser.add_argument("--congress", type=int, required=True)
    senate_parser.add_argument("--session", type=int, required=True)
    senate_parser.add_argument("--roll", type=int, action="append", dest="roll_numbers", required=True)
    senate_parser.add_argument("--output-dir", type=Path, default=SENATE_XML_CACHE_DIR)
    senate_parser.add_argument("--overwrite", action="store_true")

    args = parser.parse_args()

    if args.source == "house":
        results = fetch_house_clerk_roll_calls(
            year=args.year,
            roll_numbers=args.roll_numbers,
            output_dir=args.output_dir,
            overwrite=args.overwrite,
        )
    else:
        results = fetch_senate_vote_files(
            congress=args.congress,
            session=args.session,
            roll_numbers=args.roll_numbers,
            output_dir=args.output_dir,
            overwrite=args.overwrite,
        )

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
