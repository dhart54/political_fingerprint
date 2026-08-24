from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.etl.fetch_sources import (  # noqa: E402
    _read_dotenv_value,
    fetch_congress_bill_amendments,
    fetch_congress_bill_summaries,
)


SELECTOR_PATH = ROOT / "backend/scripts/build_cross_issue_full_record_expansion.py"
DEFAULT_OUTPUT = ROOT / ".local/m13a_domain_selection_sources"
ACTIVE_DOMAINS = {
    "JUSTICE_PUBLIC_SAFETY",
    "NATIONAL_SECURITY_FOREIGN",
    "ENVIRONMENT_ENERGY",
}
REMAINING_DOMAINS = (
    "ECONOMY_TAXES",
    "EDUCATION_WORKFORCE",
    "HEALTH_SOCIAL",
    "IMMIGRATION_BORDER",
    "INFRASTRUCTURE_TECH_TRANSPORT",
)


def load_selector() -> Any:
    spec = importlib.util.spec_from_file_location("m12a_selector", SELECTOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load cross-issue selector")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity(bill_ref: str) -> tuple[int, str, int]:
    _, congress, bill_type, number = bill_ref.split("_", 3)
    return int(congress), bill_type, int(number)


def candidate_source_targets(
    *,
    selector: Any,
    production_snapshot: Path,
    clerk_dirs: list[Path],
    metadata_dir: Path,
) -> tuple[list[str], list[str], int]:
    production, _ = selector.load_production_snapshot(production_snapshot)
    actions = selector.load_clerk_actions(clerk_dirs, "F000477")
    metadata = selector.load_congress_metadata(metadata_dir)
    summary_refs: set[str] = set()
    amendment_refs: set[str] = set()

    for domain_id in REMAINING_DOMAINS:
        for action in actions:
            item = metadata.get(action["bill_ref"])
            record = selector.build_candidate_record(
                domain_id,
                action,
                item,
                production.get(action["action_id"]),
                None,
                None,
            )
            if record is None or selector.is_procedural(action):
                continue
            question = action["question"].lower()
            if "amendment" in question and "senate amendment" not in question:
                amendment_refs.add(action["bill_ref"])
                continue
            if record["issue_boundary_status"] == "cross_domain_evidence_missing":
                summary_refs.add(action["bill_ref"])

    return sorted(summary_refs), sorted(amendment_refs), len(actions)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production-snapshot", type=Path, required=True)
    parser.add_argument("--clerk-dir", type=Path, action="append", required=True)
    parser.add_argument("--congress-metadata-dir", type=Path, required=True)
    parser.add_argument("--env-path", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    api_key = _read_dotenv_value(args.env_path, "CONGRESS_API_KEY")
    if not api_key:
        raise ValueError("Congress API key is unavailable at the supplied env path")

    selector = load_selector()
    summary_refs, amendment_refs, action_count = candidate_source_targets(
        selector=selector,
        production_snapshot=args.production_snapshot,
        clerk_dirs=args.clerk_dir,
        metadata_dir=args.congress_metadata_dir,
    )
    summaries_dir = args.output_root / "summaries"
    amendments_dir = args.output_root / "amendments"
    results = []
    for bill_ref in summary_refs:
        congress, bill_type, number = identity(bill_ref)
        results.append(
            fetch_congress_bill_summaries(
                congress=congress,
                bill_type=bill_type,
                bill_number=number,
                api_key=api_key,
                output_dir=summaries_dir,
                overwrite=args.overwrite,
            )
        )
    for bill_ref in amendment_refs:
        congress, bill_type, number = identity(bill_ref)
        results.append(
            fetch_congress_bill_amendments(
                congress=congress,
                bill_type=bill_type,
                bill_number=number,
                api_key=api_key,
                output_dir=amendments_dir,
                overwrite=args.overwrite,
            )
        )

    manifest = {
        "schema_version": "m13a_domain_selection_source_acquisition_v1",
        "active_domains_excluded": sorted(ACTIVE_DOMAINS),
        "remaining_domains": list(REMAINING_DOMAINS),
        "complete_official_action_count": action_count,
        "summary_measure_refs": summary_refs,
        "amendment_parent_measure_refs": amendment_refs,
        "summary_source_count": len(summary_refs),
        "amendment_index_source_count": len(amendment_refs),
        "downloaded_count": sum(not result.skipped for result in results),
        "skipped_count": sum(result.skipped for result in results),
        "production_or_database_access": False,
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "acquisition_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
