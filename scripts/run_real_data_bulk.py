from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.etl.live_pipeline import run_live_pipeline  # noqa: E402


def expand_rolls(*, explicit_rolls: list[int], range_pairs: list[tuple[int, int]]) -> list[int]:
    roll_numbers = set(explicit_rolls)
    for start, end in range_pairs:
        if end < start:
            raise SystemExit(f"Invalid roll range: end {end} is less than start {start}.")
        roll_numbers.update(range(start, end + 1))
    return sorted(roll_numbers)


def parse_range(value: str) -> tuple[int, int]:
    parts = value.split(":")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("Roll ranges must use start:end format.")
    start, end = parts
    return int(start), int(end)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--congress-api-key")
    parser.add_argument("--house-year", type=int, default=2025)
    parser.add_argument("--house-roll", type=int, action="append", default=[])
    parser.add_argument("--house-roll-range", type=parse_range, action="append", default=[])
    parser.add_argument("--senate-congress", type=int, default=119)
    parser.add_argument("--senate-session", type=int, default=1)
    parser.add_argument("--senate-roll", type=int, action="append", default=[])
    parser.add_argument("--senate-roll-range", type=parse_range, action="append", default=[])
    parser.add_argument("--skip-house", action="store_true")
    parser.add_argument("--skip-senate", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    house_rolls = [] if args.skip_house else expand_rolls(
        explicit_rolls=args.house_roll,
        range_pairs=args.house_roll_range,
    )
    senate_rolls = [] if args.skip_senate else expand_rolls(
        explicit_rolls=args.senate_roll,
        range_pairs=args.senate_roll_range,
    )
    api_key = args.congress_api_key or os.getenv("CONGRESS_API_KEY")

    if not house_rolls and not senate_rolls:
        raise SystemExit("Provide at least one --house-roll, --house-roll-range, --senate-roll, or --senate-roll-range value.")

    if not args.dry_run and not api_key:
        raise SystemExit("CONGRESS_API_KEY is required. Set it in the environment or pass --congress-api-key.")

    bulk_plan = {
        "house_year": args.house_year,
        "house_rolls": house_rolls,
        "senate_congress": args.senate_congress,
        "senate_session": args.senate_session,
        "senate_rolls": senate_rolls,
        "bill_metadata": "inferred_from_downloaded_roll_xml",
    }
    print({"bulk_plan": bulk_plan})

    if args.dry_run:
        return

    result = run_live_pipeline(
        house_year=args.house_year if house_rolls else None,
        house_roll_numbers=house_rolls,
        senate_congress=args.senate_congress if senate_rolls else None,
        senate_session=args.senate_session if senate_rolls else None,
        senate_roll_numbers=senate_rolls,
        bill_refs=[],
        congress_api_key=api_key,
    )
    print(result)


if __name__ == "__main__":
    main()
