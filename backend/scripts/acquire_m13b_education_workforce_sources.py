from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.etl.fetch_sources import (  # noqa: E402
    fetch_congress_bill_actions,
    fetch_congress_bill_amendments,
    fetch_congress_bill_summaries,
    fetch_congress_bill_text,
    resolve_congress_api_key,
)


PROPOSAL_PATH = ROOT / (
    "docs/editorial/cross_issue_full_record_expansion_m13a_v1/"
    "selected_domain_universe_proposal.json"
)
AUTHORITY_PATH = ROOT / (
    "docs/editorial/full_record_reviews/"
    "f000477_education_workforce_119_full_issue_universe_authority_receipt_v1.json"
)
DEFAULT_OUTPUT = ROOT / ".local/m13b_education_workforce_source_readiness"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def measure_identity(value: str) -> tuple[int, str, int]:
    congress, measure_type, number = value.split(":")
    return int(congress), measure_type, int(number)


def authority_rows() -> list[dict[str, Any]]:
    proposal = load(PROPOSAL_PATH)
    authority = load(AUTHORITY_PATH)
    approved = authority["approval_binding"]["approved_action_ids"]
    rows_by_id = {row["action_id"]: row for row in proposal["candidate_dispositions"]}
    if set(approved) != set(proposal["proposed_action_ids"]) or len(approved) != 17:
        raise ValueError("M13A accepted action set differs")
    return [rows_by_id[action_id] for action_id in approved]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    rows = authority_rows()
    whole_measure_identities = sorted(
        {
            row["exact_action_source_binding"]["exact_identity"]
            for row in rows
            if row["house_action_stage"] != "amendment"
        }
    )
    amendment_parents = sorted(
        {
            row["bill_ref"].replace("bill_119_", "119:").replace("_", ":")
            for row in rows
            if row["house_action_stage"] == "amendment"
        }
    )
    if len(whole_measure_identities) != 16 or amendment_parents != ["119:hr:1048"]:
        raise ValueError("unexpected M13B measure or amendment inventory")

    api_key = resolve_congress_api_key()
    downloaded = 0
    skipped = 0
    for identity in whole_measure_identities:
        congress, measure_type, number = measure_identity(identity)
        for result in (
            fetch_congress_bill_actions(
                congress=congress,
                bill_type=measure_type,
                bill_number=number,
                api_key=api_key,
                output_dir=args.output_root / "actions",
                overwrite=args.overwrite,
            ),
            fetch_congress_bill_text(
                congress=congress,
                bill_type=measure_type,
                bill_number=number,
                api_key=api_key,
                output_dir=args.output_root / "text_indexes",
                overwrite=args.overwrite,
            ),
        ):
            skipped += int(result.skipped)
            downloaded += int(not result.skipped)
    for identity in amendment_parents:
        congress, measure_type, number = measure_identity(identity)
        result = fetch_congress_bill_amendments(
            congress=congress,
            bill_type=measure_type,
            bill_number=number,
            api_key=api_key,
            output_dir=args.output_root / "amendments",
            overwrite=args.overwrite,
        )
        skipped += int(result.skipped)
        downloaded += int(not result.skipped)
    summary_result = fetch_congress_bill_summaries(
        congress=119,
        bill_type="s",
        bill_number=356,
        api_key=api_key,
        output_dir=args.output_root / "summaries",
        overwrite=args.overwrite,
    )
    skipped += int(summary_result.skipped)
    downloaded += int(not summary_result.skipped)

    print(
        json.dumps(
            {
                "status": "pass",
                "accepted_action_count": len(rows),
                "whole_measure_count": len(whole_measure_identities),
                "amendment_parent_count": len(amendment_parents),
                "supplemental_summary_count": 1,
                "downloaded_artifact_count": downloaded,
                "skipped_artifact_count": skipped,
                "production_or_database_access": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
