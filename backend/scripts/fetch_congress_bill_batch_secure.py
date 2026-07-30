from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.etl.fetch_sources import (  # noqa: E402
    fetch_congress_bill_actions,
    fetch_congress_bill_amendments,
    fetch_congress_bill_committees,
    fetch_congress_bill_metadata,
    fetch_congress_bill_subjects,
    fetch_congress_bill_summaries,
    fetch_congress_bill_text,
    resolve_congress_api_key,
)


FETCHERS = {
    "metadata": fetch_congress_bill_metadata,
    "summaries": fetch_congress_bill_summaries,
    "subjects": fetch_congress_bill_subjects,
    "actions": fetch_congress_bill_actions,
    "text": fetch_congress_bill_text,
    "amendments": fetch_congress_bill_amendments,
    "committees": fetch_congress_bill_committees,
}


def _parse_bill_ref(value: str) -> tuple[int, str, int]:
    parts = value.strip().lower().split("_")
    if len(parts) != 4 or parts[0] != "bill":
        raise argparse.ArgumentTypeError(
            "bill references must use bill_<congress>_<type>_<number>"
        )
    try:
        return int(parts[1]), parts[2], int(parts[3])
    except ValueError as exc:
        raise argparse.ArgumentTypeError("invalid bill reference") from exc


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Acquire a fixed batch of public Congress.gov bill records without "
            "printing credential-bearing source URLs."
        )
    )
    parser.add_argument(
        "--bill-ref",
        action="append",
        required=True,
        type=_parse_bill_ref,
        dest="bill_refs",
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--resource",
        action="append",
        choices=tuple(FETCHERS),
        default=None,
        dest="resources",
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    api_key = resolve_congress_api_key()
    resources = args.resources or ["metadata"]
    records: list[dict[str, object]] = []
    for congress, bill_type, bill_number in sorted(set(args.bill_refs)):
        for resource in resources:
            output_dir = args.output_dir / resource
            result = FETCHERS[resource](
                congress=congress,
                bill_type=bill_type,
                bill_number=bill_number,
                api_key=api_key,
                output_dir=output_dir,
                overwrite=args.overwrite,
            )
            records.append(
                {
                    "bill_ref": (
                        f"bill_{congress}_{bill_type}_{bill_number}"
                    ),
                    "resource": resource,
                    "path": str(result.destination),
                    "sha256": _sha256(result.destination),
                    "bytes": result.destination.stat().st_size,
                    "status": "cached" if result.skipped else "downloaded",
                }
            )

    print(
        json.dumps(
            {
                "bill_count": len(set(args.bill_refs)),
                "resource_count": len(records),
                "records": records,
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
