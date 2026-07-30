"""Build the deterministic, non-authorizing public review-state catalog."""

from __future__ import annotations

import argparse
import hashlib
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
    receipt_projection_key,
    validate_public_catalog,
)
from app.editorial_presentations.compiler import (  # noqa: E402
    validate_trusted_action_source_contract,
)
from scripts.validate_full_record_issue_interpretation import (  # noqa: E402
    REVIEW_ROOT,
    validate_review,
)


OUTPUT_PATH = (
    ROOT
    / "backend/app/editorial_presentations/public_review_state_catalog_v1.json"
)
SOURCE_CONTRACT_ROOT = ROOT / "docs/editorial/action_source_contracts"
PRESENTATION_ROOT = ROOT / "docs/editorial/presentations"


def _repository_sha256(path: Path) -> str:
    content = path.read_bytes()
    if path.suffix.lower() in {".json", ".md", ".sql", ".txt"}:
        content = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def _source_contract(review: dict[str, Any]) -> dict[str, Any]:
    contracts = []
    action_ids = set(review["issue_universe"]["action_ids"])
    for path in sorted(SOURCE_CONTRACT_ROOT.glob("*.json")):
        candidate = json.loads(path.read_text(encoding="utf-8"))
        validate_trusted_action_source_contract(candidate)
        if set(candidate["actions"]) == action_ids:
            contracts.append(candidate)
    if len(contracts) != 1:
        raise ValueError(
            f"{review['review_id']}: expected one exact-action source contract"
        )
    return contracts[0]


def _presentation_fixture(review: dict[str, Any]) -> dict[str, Any]:
    artifact_id = review["historical_publication"]["artifact_id"]
    matches = []
    for path in sorted(PRESENTATION_ROOT.glob("*_review_fixture.json")):
        candidate = json.loads(path.read_text(encoding="utf-8"))
        if candidate.get("artifact_identity", {}).get("artifact_id") == artifact_id:
            matches.append(candidate)
    if len(matches) != 1:
        raise ValueError(
            f"{review['review_id']}: expected one bound presentation fixture"
        )
    return matches[0]


def _source_index(contract: dict[str, Any]) -> tuple[dict[str, Any], str]:
    manifest_ref = contract["source_manifest"]
    manifest_path = ROOT / manifest_ref["path"]
    if (
        not manifest_path.is_file()
        or _repository_sha256(manifest_path) != manifest_ref["sha256"]
    ):
        raise ValueError(
            f"{contract['contract_id']}: source manifest is missing or stale"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources = {source["source_id"]: source for source in manifest["sources"]}
    if len(sources) != len(manifest["sources"]):
        raise ValueError(f"{contract['contract_id']}: duplicate source identity")
    return sources, manifest_ref["sha256"]


def _public_source(source: dict[str, Any]) -> dict[str, str]:
    return {
        "source_id": source["source_id"],
        "source_type": source["source_type"],
        "name": source["name"],
        "url": source["url"],
    }


def _mapped_action_ids(fixture: dict[str, Any]) -> set[str]:
    display = fixture["editorial_wording"]
    linked: set[str] = set()

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            action_ids = value.get("action_ids")
            if isinstance(action_ids, list):
                linked.update(
                    action_id for action_id in action_ids
                    if isinstance(action_id, str)
                )
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(display)
    if not linked:
        raise ValueError(
            f"{fixture['artifact_identity']['artifact_id']}: presentation has no action mappings"
        )
    return linked


def _exact_action_receipts(review: dict[str, Any]) -> list[dict[str, Any]]:
    contract = _source_contract(review)
    fixture = _presentation_fixture(review)
    sources, source_manifest_sha256 = _source_index(contract)
    subject = review["subject"]
    congress_scope = sorted(subject["congress_scope"])
    artifact_id = review["historical_publication"]["artifact_id"]
    if (
        fixture["artifact_identity"]["member_id"] != subject["member_id"]
        or fixture["artifact_identity"]["issue_id"] != subject["issue_id"]
        or fixture["artifact_identity"]["congress"] not in congress_scope
    ):
        raise ValueError(f"{review['review_id']}: presentation identity mismatch")
    published_action_ids = _mapped_action_ids(fixture)
    review_actions = {
        action["action_id"]: action for action in review["action_accounting"]
    }
    if set(review_actions) != published_action_ids or set(contract["actions"]) != published_action_ids:
        raise ValueError(
            f"{review['review_id']}: review, source contract, and published sample differ"
        )
    episodes = {episode["episode_id"]: episode for episode in review["episodes"]}
    receipts = []
    for action_id in sorted(published_action_ids):
        action = review_actions[action_id]
        interpretation = action["interpretation"]
        if interpretation is None:
            raise ValueError(f"{action_id}: published action lacks interpretation")
        contract_action = contract["actions"][action_id]
        if (
            interpretation["member_action"]
            != action["review_friendliness"]["member_action"]
            or interpretation["episode_id"] != action["episode_id"]
            or interpretation["vote_source_refs"]
            != contract_action["vote_source_refs"]
            or interpretation["action_meaning_source_refs"]
            != contract_action["action_meaning_source_refs"]
        ):
            raise ValueError(f"{action_id}: governed action sources or meaning conflict")
        episode = episodes.get(action["episode_id"])
        if episode is None or action_id not in episode["action_ids"]:
            raise ValueError(f"{action_id}: governed episode identity is missing")
        vote_sources = [
            _public_source(sources[source_id])
            for source_id in contract_action["vote_source_refs"]
        ]
        meaning_sources = [
            _public_source(sources[source_id])
            for source_id in contract_action["action_meaning_source_refs"]
        ]
        if [source["source_type"] for source in meaning_sources] != contract_action[
            "required_action_meaning_source_types"
        ]:
            raise ValueError(f"{action_id}: required action-meaning source type is missing")
        receipt = {
            "projection_key": receipt_projection_key(
                member_id=subject["member_id"],
                issue_id=subject["issue_id"],
                congress_scope=congress_scope,
                published_artifact_identity=artifact_id,
                canonical_action_id=action_id,
                action_interpretation_id=interpretation["interpretation_id"],
                action_interpretation_sha256=interpretation["interpretation_sha256"],
            ),
            "member_id": subject["member_id"],
            "issue_id": subject["issue_id"],
            "congress_scope": congress_scope,
            "published_artifact_identity": artifact_id,
            "canonical_action_id": action_id,
            "action_interpretation_id": interpretation["interpretation_id"],
            "action_interpretation_sha256": interpretation["interpretation_sha256"],
            "action_meaning_id": interpretation["action_meaning_id"],
            "member_action": interpretation["member_action"],
            "interpretation_disposition": action["disposition"],
            "interpretation_status": "interpreted",
            "exact_action_meaning": interpretation["exact_action_meaning"],
            "policy_question": episode["policy_question"],
            "episode_id": action["episode_id"],
            "vote_sources": vote_sources,
            "action_meaning_sources": meaning_sources,
            "interpretation_receipt_refs": interpretation[
                "interpretation_receipt_refs"
            ],
            "review_scope": review["frontend_state"]["review_scope"],
            "public_claim_class": review["frontend_state"]["public_claim_class"],
            "caveats": episode["contrary_or_limiting_evidence"],
            "projection_source": {
                "review_id": review["review_id"],
                "source_contract_id": contract["contract_id"],
                "source_manifest_sha256": source_manifest_sha256,
            },
        }
        receipts.append(receipt)
    return receipts


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
        "exact_action_receipts": _exact_action_receipts(review),
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
