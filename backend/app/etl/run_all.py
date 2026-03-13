import argparse
from datetime import date

from app.etl.compute import run_etl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", action="store_true")
    args = parser.parse_args()

    source = "fixtures" if args.fixtures else "fixtures"
    result = run_etl(source=source, as_of=date(2026, 3, 12))
    print(result)


if __name__ == "__main__":
    main()
