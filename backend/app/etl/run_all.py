import argparse
from datetime import date

from app.etl.compute import run_etl
from app.etl.seed import seed_fixture_database


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", action="store_true")
    parser.add_argument("--seed-db", action="store_true")
    args = parser.parse_args()

    source = "fixtures" if args.fixtures else "fixtures"
    if args.seed_db:
        result = seed_fixture_database(as_of=date(2026, 3, 12))
    else:
        result = run_etl(source=source, as_of=date(2026, 3, 12))
    print(result)


if __name__ == "__main__":
    main()
