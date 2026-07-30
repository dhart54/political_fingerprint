"""Build the deterministic, non-authorizing public review-state catalog."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.editorial_presentations.review_state_catalog import (  # noqa: E402
    CATALOG_SCHEMA_VERSION,
    catalog_key,
    validate_public_catalog,
)
from scripts.validate_full_record_issue_interpretation import (  # noqa: E402
    REVIEW_ROOT,
    validate_review,
)


OUTPUT_PATH = (
    ROOT
    / "backend/app/editorial_presentations/public_review_state_catalog_v1.json"
)


def _public_status_label(review: dict[str, Any]) -> str:
    frontend = review["frontend_state"]
    claim_class = frontend["public_claim_class"]
    if (
        claim_class == "reviewed_sample_finding"
        and frontend["benchmark_sample_available"]
    ):
        label = "Reviewed benchmark sample"
    elif claim_class == "full_issue_synthesis":
        label = "Full issue interpretation available"
    elif claim_class == "full_review_no_common_throughline":
        label = "No common throughline found"
    elif claim_class == "full_review_no_safe_synthesis":
        label = "No safe synthesis available"
    elif (
        frontend["review_scope"] == "full_defined_issue_record"
        and frontend["review_completion_state"] == "complete"
    ):
        label = "Full review complete"
    else:
        label = "Vote receipts available"
    if label not in frontend["available_labels"]:
        raise ValueError(
            f"{review['review_id']}: derived public label is not declared available"
        )
    return label


def _entry(review: dict[str, Any]) -> dict[str, Any]:
    subject = review["subject"]
    frontend = review["frontend_state"]
    artifact_identity = review["historical_publication"]["artifact_id"]
    congress_scope = sorted(subject["congress_scope"])
    return {
        "catalog_key": catalog_key(
            member_id=subject["member_id"],
            issue_id=subject["issue_id"],
            congress_scope=congress_scope,
            published_artifact_identity=artifact_identity,
        ),
        "member_id": subject["member_id"],
        "issue_id": subject["issue_id"],
        "congress_scope": congress_scope,
        "published_artifact_identity": artifact_identity,
        "semantic_tier": review["axes"]["semantic_tier"],
        "review_scope": frontend["review_scope"],
        "review_completion_state": frontend["review_completion_state"],
        "public_claim_class": frontend["public_claim_class"],
        "total_recorded_actions": frontend["total_recorded_actions"],
        "review_friendly_actions": frontend["review_friendly_actions"],
        "interpreted_actions": frontend["interpreted_actions"],
        "unresolved_actions": frontend["unresolved_actions"],
        "procedural_context_actions": frontend["procedural_context_actions"],
        "present_actions": frontend["present_actions"],
        "not_voting_actions": frontend["not_voting_actions"],
        "complete_episode_count": frontend["complete_episode_count"],
        "partial_episode_count": frontend["partial_episode_count"],
        "full_issue_synthesis_eligible": frontend[
            "full_issue_synthesis_eligible"
        ],
        "benchmark_sample_available": frontend["benchmark_sample_available"],
        "scope_bounded_teaser": frontend["conclusion_teaser"],
        "public_status_label": _public_status_label(review),
    }


def build_catalog() -> dict[str, Any]:
    entries = []
    for path in sorted(REVIEW_ROOT.glob("*.json")):
        review = json.loads(path.read_text(encoding="utf-8"))
        validate_review(review)
        entries.append(_entry(review))
    catalog = {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "entries": sorted(entries, key=lambda item: item["catalog_key"]),
    }
    validate_public_catalog(catalog)
    return catalog


def catalog_bytes(catalog: dict[str, Any]) -> bytes:
    return (
        json.dumps(catalog, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        expected = catalog_bytes(build_catalog())
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.check:
        if not OUTPUT_PATH.is_file() or OUTPUT_PATH.read_bytes() != expected:
            print("ERROR: public review-state catalog is missing or stale", file=sys.stderr)
            return 1
        print("Public review-state catalog is deterministic and current.")
        return 0
    OUTPUT_PATH.write_bytes(expected)
    print(OUTPUT_PATH.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
