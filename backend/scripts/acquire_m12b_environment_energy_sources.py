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


PROPOSAL_PATH = ROOT / (
    "docs/editorial/cross_issue_full_record_expansion_m12a_v1/"
    "selected_domain_universe_proposal.json"
)
AUTHORITY_PATH = ROOT / (
    "docs/editorial/full_record_reviews/"
    "f000477_environment_energy_119_full_issue_universe_authority_receipt_v1.json"
)
DEFAULT_OUTPUT = ROOT / ".local/m12b_environment_energy_source_readiness"


def _measure_identity(value: str) -> tuple[int, str, int]:
    congress, measure_type, number = value.split(":")
    return int(congress), measure_type, int(number)


def approved_measure_identities(
    proposal: dict[str, object], authority: dict[str, object]
) -> list[str]:
    approved = set(authority["approval_binding"]["approved_action_ids"])
    rows = {
        row["action_id"]: row
        for row in proposal["candidate_dispositions"]
        if row["action_id"] in approved
    }
    if set(rows) != approved:
        raise ValueError("M12A authority action set does not resolve in proposal")
    if any(row["house_action_stage"] == "amendment" for row in rows.values()):
        raise ValueError("M12B whole-measure acquisition received an amendment")
    return sorted(
        {row["exact_action_source_binding"]["exact_identity"] for row in rows.values()}
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    proposal = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))
    authority = json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))
    identities = approved_measure_identities(proposal, authority)
    if len(identities) != 63:
        raise ValueError(f"expected 63 authority-bound measures, got {len(identities)}")

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
