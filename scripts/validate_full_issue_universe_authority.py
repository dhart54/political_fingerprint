"""Verify the detached Foushee Justice V2 universe authority receipt."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.universe_authority import (  # noqa: E402
    UniverseAuthorityError,
    canonical_file_sha256,
    file_digest_matches,
    sha256_json,
    verify_manifest_and_receipt,
)
from backend.app.etl.universe_discovery import (  # noqa: E402
    UNRESOLVED_DISPOSITIONS,
)


BASE = Path("docs/editorial/full_record_reviews")
PROPOSALS = BASE / "proposals"
RECEIPT_PATH = BASE / (
    "f000477_justice_public_safety_119_full_issue_universe_authority_receipt_v2.json"
)
MANIFEST_PATH = PROPOSALS / (
    "f000477_justice_public_safety_119_full_issue_universe_manifest_v2.json"
)
DISCOVERY_PATH = PROPOSALS / (
    "f000477_justice_public_safety_119_full_issue_universe_discovery_v2.json"
)
INVENTORY_PATH = PROPOSALS / (
    "f000477_justice_public_safety_119_source_inventory_v2.json"
)
CONFIG_PATH = PROPOSALS / (
    "f000477_justice_public_safety_119_universe_discovery_config_v2.json"
)
COMPARISON_PATH = PROPOSALS / (
    "f000477_justice_public_safety_119_universe_refresh_comparison_v2.json"
)
CURRENT_STATE_PATH = Path("docs/editorial/current_state_index.json")
BENCHMARK_STATE_PATH = BASE / ("f000477_justice_public_safety_119_review_state_v1.json")

EXPECTED = {
    "manifest_id": "full-universe:f000477:justice_public_safety:119:proposed:v2",
    "manifest_sha256": "17cc2d30c51dadc0e1d6afe3eb927fb8a3f798b909d6558abb116108c46cd88c",
    "action_set_sha256": "51fff89a65e8fb869e4072a8b91c1301f0bc07ee8ba6bf090ee9a23450a94ba5",
    "universe_subject_sha256": "d778bff4019e893f378fbd38a76b4cf108967784a4829d58b7004e2b3a578077",
    "member_id": "F000477",
    "issue_id": "JUSTICE_PUBLIC_SAFETY",
    "congress_scope": [119],
    "chambers": ["house"],
    "cutoff": "2026-07-23",
    "latest_roll": 283,
    "complete_actions": 638,
    "candidates": 172,
    "substantive": 37,
    "expressive": 7,
    "procedural": 69,
    "ineligible": 59,
    "unresolved": 0,
}
FISA_ACTIONS = {"house:119:2:155", "house:119:2:221"}
FISA_MEMBERSHIPS = ["JUSTICE_PUBLIC_SAFETY", "NATIONAL_SECURITY"]
FISA_LIMITATIONS = [
    "surveillance_authority",
    "fisc_and_court_authority",
    "civil_liberty_protections",
]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise UniverseAuthorityError(message)


def _load(path: Path, *, root: Path = ROOT) -> dict[str, Any]:
    return json.loads((root / path).read_text(encoding="utf-8"))


def _set(value: dict[str, Any], name: str) -> set[str]:
    action_ids = value[name]["action_ids"]
    _require(
        len(action_ids) == len(set(action_ids)), f"{name} contains duplicate actions"
    )
    _require(value[name]["action_count"] == len(action_ids), f"{name} count mismatch")
    _require(
        value[name]["action_set_sha256"] == sha256_json(sorted(action_ids)),
        f"{name} digest mismatch",
    )
    return set(action_ids)


def validate_authority_values(
    *,
    receipt: dict[str, Any],
    manifest: dict[str, Any],
    discovery: dict[str, Any],
    inventory: dict[str, Any],
    config: dict[str, Any],
    comparison: dict[str, Any],
    manifest_path: Path,
    authority_root: Path = ROOT,
    receipt_path: Path = RECEIPT_PATH,
) -> dict[str, Any]:
    _require(
        "proposals" not in receipt_path.parts,
        "authority receipt must be detached from proposals",
    )
    verified = verify_manifest_and_receipt(
        manifest,
        receipt,
        manifest_path=manifest_path,
        authority_root=authority_root,
        expected_reviewer_id="dhart54",
    )
    _require(
        manifest["manifest_id"] == EXPECTED["manifest_id"],
        "approved manifest ID mismatch",
    )
    _require(
        receipt["receipt_id"]
        == "universe-authority:f000477:justice_public_safety:119:v2",
        "receipt ID mismatch",
    )
    _require(
        receipt["manifest_sha256"] == EXPECTED["manifest_sha256"],
        "approved manifest digest mismatch",
    )
    _require(
        verified["action_set_sha256"] == EXPECTED["action_set_sha256"],
        "approved action-set digest mismatch",
    )
    _require(
        verified["universe_subject_sha256"] == EXPECTED["universe_subject_sha256"],
        "approved universe-subject digest mismatch",
    )
    _require(
        manifest["subject"] == config["subject"] == discovery["subject"],
        "subject sources disagree",
    )
    _require(
        manifest["subject"]["member_id"] == EXPECTED["member_id"],
        "approved member mismatch",
    )
    _require(
        manifest["subject"]["issue_id"] == EXPECTED["issue_id"],
        "approved issue mismatch",
    )
    _require(
        manifest["subject"]["congress_scope"] == EXPECTED["congress_scope"],
        "approved Congress mismatch",
    )
    _require(
        manifest["boundary"] == config["boundary"] == discovery["cutoff"]["boundary"],
        "canonical boundaries disagree",
    )
    _require(
        manifest["boundary"]["chambers"] == EXPECTED["chambers"],
        "approved chamber mismatch",
    )
    _require(
        manifest["boundary"]["end_date"] == EXPECTED["cutoff"],
        "approved inclusion cutoff mismatch",
    )
    _require(
        manifest["rules"]["inclusion"] == config["inclusion_rules"],
        "inclusion rules disagree",
    )
    _require(
        manifest["rules"]["exclusion"] == config["exclusion_rules"],
        "exclusion rules disagree",
    )

    proposed_ref = discovery["proposed_manifest"]
    _require(
        proposed_ref["manifest_id"] == manifest["manifest_id"],
        "discovery manifest ID mismatch",
    )
    _require(
        proposed_ref["sha256"] == verified["manifest_file_sha256"],
        "discovery manifest digest mismatch",
    )
    _require(
        proposed_ref["universe_subject_sha256"] == verified["universe_subject_sha256"],
        "discovery universe subject mismatch",
    )
    inventory_ref = discovery["source_inventory"]
    _require(
        inventory_ref["inventory_id"] == inventory["inventory_id"],
        "source inventory ID mismatch",
    )
    inventory_path = authority_root / inventory_ref["path"]
    _require(
        file_digest_matches(inventory_path, inventory_ref["sha256"]),
        "source inventory digest mismatch",
    )
    _require(
        inventory["subject"] == manifest["subject"], "source inventory subject mismatch"
    )
    _require(
        inventory["snapshot_source_commit"]
        == manifest["snapshot_source_commit"]
        == config["snapshot_source_commit"],
        "snapshot source commit mismatch",
    )

    complete = _set(discovery, "complete_member_action_snapshot")
    candidates = _set(discovery, "candidate_recall_set")
    substantive = _set(discovery, "proposed_universe_set")
    unresolved = _set(discovery, "unresolved_candidate_set")
    _require(
        len(complete) == EXPECTED["complete_actions"],
        "complete official action count mismatch",
    )
    _require(len(candidates) == EXPECTED["candidates"], "candidate count mismatch")
    _require(
        substantive == set(verified["action_ids"]),
        "discovery substantive membership mismatch",
    )
    _require(
        not unresolved and EXPECTED["unresolved"] == 0,
        "unresolved candidates must be zero",
    )

    dispositions = discovery["candidate_dispositions"]
    disposition_ids = [row["action_id"] for row in dispositions]
    _require(
        len(disposition_ids) == len(set(disposition_ids)),
        "candidate dispositions contain duplicates",
    )
    _require(
        set(disposition_ids) == candidates,
        "candidate dispositions do not cover recall set",
    )
    counts = Counter(row["disposition"] for row in dispositions)
    expected_counts = {
        "proposed_in_scope_substantive": EXPECTED["substantive"],
        "expressive_nonbinding_context": EXPECTED["expressive"],
        "procedural_context": EXPECTED["procedural"],
        "proposed_exact_action_ineligible": EXPECTED["ineligible"],
    }
    _require(dict(counts) == expected_counts, "candidate accounting mismatch")
    _require(
        sum(counts.values()) == EXPECTED["candidates"],
        "candidate accounting does not reconcile",
    )
    _require(
        not (set(counts) & UNRESOLVED_DISPOSITIONS),
        "unresolved candidate disposition present",
    )

    expressive = _set(manifest, "expressive_nonbinding_action_set")
    procedural = _set(manifest, "procedural_context_action_set")
    ineligible = _set(manifest, "exact_action_ineligible_set")
    by_id = {row["action_id"]: row for row in dispositions}
    _require(
        expressive.isdisjoint(substantive),
        "expressive actions entered substantive universe",
    )
    _require(
        all(
            by_id[action]["disposition"] == "expressive_nonbinding_context"
            for action in expressive
        ),
        "expressive action represented as substantive",
    )
    _require(len(expressive) == EXPECTED["expressive"], "expressive count mismatch")
    _require(len(procedural) == EXPECTED["procedural"], "procedural count mismatch")
    _require(len(ineligible) == EXPECTED["ineligible"], "ineligible count mismatch")

    latest_roll = max(
        int(action_id.rsplit(":", 1)[1])
        for action_id in complete
        if action_id.startswith("house:119:2:")
    )
    _require(
        latest_roll == EXPECTED["latest_roll"],
        "latest included official House roll mismatch",
    )
    _require(
        discovery["cutoff"]["latest_included_vote_date"] == EXPECTED["cutoff"],
        "discovery cutoff mismatch",
    )

    for action_id in FISA_ACTIONS:
        _require(
            manifest["cross_domain_memberships"].get(action_id) == FISA_MEMBERSHIPS,
            f"{action_id}: cross-domain membership mismatch",
        )
        _require(
            config["cross_domain_memberships"].get(action_id) == FISA_MEMBERSHIPS,
            f"{action_id}: config cross-domain membership mismatch",
        )
        _require(
            comparison["cross_domain_memberships"].get(action_id) == FISA_MEMBERSHIPS,
            f"{action_id}: comparison cross-domain membership mismatch",
        )
        _require(
            manifest["cross_domain_scope_limitations"].get(action_id)
            == FISA_LIMITATIONS,
            f"{action_id}: Justice scope limitation mismatch",
        )
        _require(
            config["cross_domain_scope_limitations"].get(action_id) == FISA_LIMITATIONS,
            f"{action_id}: config Justice scope limitation mismatch",
        )

    refresh = comparison["refresh_v2"]
    derived_refresh = {
        "complete_action_count": len(complete),
        "candidate_count": len(candidates),
        "proposed_count": len(substantive),
        "expressive_nonbinding_count": len(expressive),
        "procedural_count": len(procedural),
        "ineligible_count": len(ineligible),
        "unresolved_count": len(unresolved),
        "cutoff": manifest["boundary"]["end_date"],
    }
    _require(
        all(refresh[key] == value for key, value in derived_refresh.items()),
        "V1/V2 comparison accounting mismatch",
    )
    _require(
        receipt["reviewer"]["authority"] == "full_issue_universe_review_authority_v1",
        "reviewer authority mismatch",
    )
    _require(
        receipt["decision"] == "approved_complete_issue_universe",
        "approval decision mismatch",
    )

    return {
        **verified,
        "complete_action_count": len(complete),
        "candidate_count": len(candidates),
        "expressive_count": len(expressive),
        "procedural_count": len(procedural),
        "ineligible_count": len(ineligible),
        "unresolved_count": len(unresolved),
        "latest_included_roll": latest_roll,
        "inclusion_cutoff": manifest["boundary"]["end_date"],
    }


def validate_current_state(
    state: dict[str, Any],
    *,
    receipt_path: Path,
    receipt_sha256: str,
) -> None:
    current = state["full_record_issue_interpretation"]
    expected = {
        "f000477_justice_119_full_defined_issue_record_established": True,
        "f000477_justice_119_external_universe_authority": "approved_content_bound",
        "f000477_justice_119_universe_discovery_state": "complete",
        "f000477_justice_119_action_interpretation_state": "not_started",
        "f000477_justice_119_policy_episode_state": "not_started",
        "f000477_justice_119_full_record_semantic_ir": "absent",
        "f000477_justice_119_full_record_synthesis": "absent",
        "f000477_justice_119_production_persistence": "not_authorized",
        "f000477_justice_119_publication_state": "unchanged_reviewed_benchmark_sample_active",
    }
    _require(
        all(current.get(key) == value for key, value in expected.items()),
        "current-state authority boundaries are inaccurate",
    )
    _require(
        current["f000477_justice_119_universe_authority_receipt"]
        == receipt_path.as_posix(),
        "current-state receipt path mismatch",
    )
    identity = current["f000477_justice_119_universe_authority_receipt_identity"]
    _require(
        identity["id"] == "universe-authority:f000477:justice_public_safety:119:v2",
        "current-state receipt ID mismatch",
    )
    _require(
        identity["sha256"] == receipt_sha256, "current-state receipt digest mismatch"
    )
    _require(
        current["f000477_justice_119_review_scope"] == "benchmark_sample",
        "benchmark review scope changed",
    )
    _require(
        current["f000477_justice_119_public_claim_class"] == "reviewed_sample_finding",
        "benchmark public claim changed",
    )
    _require(
        current["f000477_justice_119_full_issue_synthesis_eligible"] is False,
        "state claims full synthesis authority",
    )


def validate_repository_authority(*, root: Path = ROOT) -> dict[str, Any]:
    paths = {
        "receipt": RECEIPT_PATH,
        "manifest": MANIFEST_PATH,
        "discovery": DISCOVERY_PATH,
        "inventory": INVENTORY_PATH,
        "config": CONFIG_PATH,
        "comparison": COMPARISON_PATH,
    }
    values = {name: _load(path, root=root) for name, path in paths.items()}
    result = validate_authority_values(
        **values,
        manifest_path=root / MANIFEST_PATH,
        authority_root=root,
        receipt_path=RECEIPT_PATH,
    )
    receipt_sha256 = canonical_file_sha256(root / RECEIPT_PATH)
    validate_current_state(
        _load(CURRENT_STATE_PATH, root=root),
        receipt_path=RECEIPT_PATH,
        receipt_sha256=receipt_sha256,
    )
    from scripts.validate_full_record_issue_interpretation import validate_review

    benchmark = _load(BENCHMARK_STATE_PATH, root=root)
    validate_review(benchmark)
    _require(
        benchmark["axes"]["review_scope"] == "benchmark_sample",
        "public benchmark scope changed",
    )
    _require(
        benchmark["axes"]["public_claim_class"] == "reviewed_sample_finding",
        "public benchmark claim changed",
    )
    _require(
        len(benchmark["issue_universe"]["action_ids"]) == 7,
        "public benchmark action membership changed",
    )
    _require(
        benchmark["historical_publication"]["state"] == "active",
        "public benchmark publication changed",
    )
    _require(
        all(value is None for value in benchmark["external_authority"].values()),
        "benchmark was improperly given full-record authority",
    )
    result["receipt_file_sha256"] = receipt_sha256
    return result


def main() -> int:
    try:
        result = validate_repository_authority()
    except (UniverseAuthorityError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "pass", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
