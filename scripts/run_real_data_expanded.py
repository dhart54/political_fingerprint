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


DEFAULT_HOUSE_YEAR = 2025
DEFAULT_HOUSE_ROLLS = [347, 349, 351, 356, 358, 360, 362]
DEFAULT_SENATE_CONGRESS = 119
DEFAULT_SENATE_SESSION = 1
DEFAULT_SENATE_ROLLS = [127, 133, 318, 372, 480, 618]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--congress-api-key")
    parser.add_argument("--house-year", type=int, default=DEFAULT_HOUSE_YEAR)
    parser.add_argument("--house-roll", type=int, action="append", default=[])
    parser.add_argument("--senate-congress", type=int, default=DEFAULT_SENATE_CONGRESS)
    parser.add_argument("--senate-session", type=int, default=DEFAULT_SENATE_SESSION)
    parser.add_argument("--senate-roll", type=int, action="append", default=[])
    parser.add_argument("--skip-house", action="store_true")
    parser.add_argument("--skip-senate", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    house_rolls = [] if args.skip_house else (args.house_roll or list(DEFAULT_HOUSE_ROLLS))
    senate_rolls = [] if args.skip_senate else (args.senate_roll or list(DEFAULT_SENATE_ROLLS))
    api_key = args.congress_api_key or os.getenv("CONGRESS_API_KEY")

    if not args.dry_run and not api_key:
        raise SystemExit("CONGRESS_API_KEY is required. Set it in the environment or pass --congress-api-key.")

    expanded_plan = {
        "house_year": args.house_year,
        "house_rolls": house_rolls,
        "senate_congress": args.senate_congress,
        "senate_session": args.senate_session,
        "senate_rolls": senate_rolls,
        "bill_metadata": "inferred_from_downloaded_roll_xml",
    }
    print({"expanded_plan": expanded_plan})

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
