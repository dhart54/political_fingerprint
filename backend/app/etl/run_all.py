import argparse
from datetime import date

from app.etl.compute import run_etl
from app.etl.seed import run_etl_and_persist


DEFAULT_AS_OF_DATE = date(2026, 3, 12)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", action="store_true")
    parser.add_argument(
        "--source",
        choices=(
            "fixtures",
            "congress_sample",
            "house_clerk_sample",
            "house_clerk_cache",
            "senate_xml_sample",
            "senate_xml_cache",
        ),
        default="fixtures",
    )
    parser.add_argument("--compute-only", action="store_true")
    args = parser.parse_args()

    source = "fixtures" if args.fixtures else args.source
    if args.compute_only:
        result = run_etl(source=source, as_of=DEFAULT_AS_OF_DATE)
    else:
        result = run_etl_and_persist(source=source, as_of=DEFAULT_AS_OF_DATE)
    print(result)


if __name__ == "__main__":
    main()
