from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.etl.fetch_sources import (  # noqa: E402
    fetch_congress_bill_actions,
    fetch_congress_bill_text,
    resolve_congress_api_key,
)


PROPOSAL_PATH = (
    ROOT
    / "docs/editorial/cross_issue_full_record_expansion_v1/selected_domain_universe_proposal.json"
)
DEFAULT_OUTPUT = ROOT / ".local/m11b_national_security_source_readiness"


def _measure_identity(value: str) -> tuple[int, str, int]:
    congress, measure_type, number = value.split(":")
    return int(congress), measure_type, int(number)


def approved_whole_measure_identities(proposal: dict[str, object]) -> list[str]:
    approved = set(proposal["proposed_action_ids"])
    identities = {
        row["exact_action_source_binding"]["exact_identity"]
        for row in proposal["candidate_dispositions"]
        if row["action_id"] in approved and row["house_action_stage"] != "amendment"
    }
    return sorted(identities)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    proposal = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))
    identities = approved_whole_measure_identities(proposal)
    if len(identities) != 50:
        raise ValueError(
            f"expected 50 approved whole-measure identities, got {len(identities)}"
        )

    api_key = resolve_congress_api_key()
    actions_dir = args.output_root / "actions"
    text_index_dir = args.output_root / "text_indexes"
    downloaded = 0
    skipped = 0
    for identity in identities:
        congress, measure_type, number = _measure_identity(identity)
        results = (
            fetch_congress_bill_actions(
                congress=congress,
                bill_type=measure_type,
                bill_number=number,
                api_key=api_key,
                output_dir=actions_dir,
                overwrite=args.overwrite,
            ),
            fetch_congress_bill_text(
                congress=congress,
                bill_type=measure_type,
                bill_number=number,
                api_key=api_key,
                output_dir=text_index_dir,
                overwrite=args.overwrite,
            ),
        )
        for result in results:
            skipped += int(result.skipped)
            downloaded += int(not result.skipped)

    print(
        json.dumps(
            {
                "status": "pass",
                "approved_measure_count": len(identities),
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
