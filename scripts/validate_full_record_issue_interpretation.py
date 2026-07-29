"""Validate Full-Record Issue Interpretation V1 review-state manifests."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_issue_interpretation_v1.schema.json"
)
REVIEW_ROOT = ROOT / "docs/editorial/full_record_reviews"

INTERPRETED_DISPOSITIONS = {
    "interpreted_substantive_directional",
    "interpreted_substantive_non_directional",
}
UNRESOLVED_DISPOSITIONS = {
    "missing_evidence",
    "source_unresolved",
    "source_conflicting",
    "source_constraint_blocked",
}
OPEN_REVIEW_DISPOSITIONS = UNRESOLVED_DISPOSITIONS | {"pending_interpretation"}
FULL_SYNTHESIS_OUTCOMES = {
    "repeated_pattern",
    "mechanism_divide",
    "uniform_direction",
    "mixed_or_qualified",
    "no_common_throughline",
}


class FullRecordValidationError(ValueError):
    """Raised when a full-record review manifest violates the contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FullRecordValidationError(message)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def universe_digest_input(review: dict[str, Any]) -> dict[str, Any]:
    """Return the order-insensitive identity input for an issue universe."""

    return {
        "action_ids": sorted(review["issue_universe"]["action_ids"]),
        "congress_scope": sorted(review["subject"]["congress_scope"]),
        "issue_id": review["subject"]["issue_id"],
        "member_id": review["subject"]["member_id"],
        "review_scope": review["axes"]["review_scope"],
    }


def compute_universe_sha256(review: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(universe_digest_input(review))).hexdigest()


def _schema_errors(review: dict[str, Any]) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    validator = Draft7Validator(schema, format_checker=FormatChecker())
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: "
        f"{error.message}"
        for error in sorted(validator.iter_errors(review), key=lambda item: list(item.path))
    ]


def _expected_review_friendly(criteria: dict[str, Any]) -> bool:
    return (
        criteria["substantive_candidate"]
        and criteria["stable_canonical_action_identity"]
        and criteria["service_status"] == "in_service"
        and criteria["member_action"] in {"Yea", "Nay", "Present", "Not Voting"}
        and criteria["exact_action_issue_eligibility"] == "eligible"
        and criteria["action_meaning_evidence"] == "sufficient"
        and criteria["vote_provenance"] == "authoritative"
        and criteria["action_meaning_provenance"] == "authoritative"
        and criteria["source_conflict_state"] == "none"
    )


def _expected_non_interpreted_disposition(criteria: dict[str, Any]) -> str:
    if criteria["service_status"] in {"not_yet_serving", "no_longer_serving"}:
        return "outside_service"
    if criteria["exact_action_issue_eligibility"] == "procedural_context":
        return "procedural_context"
    if criteria["exact_action_issue_eligibility"] == "ineligible":
        return "exact_action_ineligible"
    if (
        criteria["source_conflict_state"] == "conflicting"
        or criteria["action_meaning_evidence"] == "conflicting"
        or criteria["vote_provenance"] == "conflicting"
        or criteria["action_meaning_provenance"] == "conflicting"
        or criteria["member_action"] == "Source Conflicting"
    ):
        return "source_conflicting"
    if (
        criteria["action_meaning_evidence"] == "constraint_blocked"
        or criteria["vote_provenance"] == "constraint_blocked"
        or criteria["action_meaning_provenance"] == "constraint_blocked"
    ):
        return "source_constraint_blocked"
    if (
        criteria["action_meaning_evidence"] == "missing"
        or criteria["vote_provenance"] == "missing"
        or criteria["action_meaning_provenance"] == "missing"
        or criteria["member_action"] == "Missing Evidence"
    ):
        return "missing_evidence"
    return "source_unresolved"


def _validate_actions(review: dict[str, Any]) -> dict[str, dict[str, Any]]:
    universe_ids = review["issue_universe"]["action_ids"]
    accounting = review["action_accounting"]
    accounting_ids = [item["action_id"] for item in accounting]
    _require(
        len(accounting_ids) == len(set(accounting_ids)),
        "every action must be accounted for exactly once",
    )
    _require(
        set(accounting_ids) == set(universe_ids),
        "action accounting must exactly equal the issue-universe snapshot",
    )

    by_id = {item["action_id"]: item for item in accounting}
    for action in accounting:
        action_id = action["action_id"]
        criteria = action["review_friendliness"]
        expected_friendly = _expected_review_friendly(criteria)
        _require(
            criteria["is_review_friendly"] is expected_friendly,
            f"{action_id}: review-friendly state does not match the closed criteria",
        )

        if expected_friendly:
            expected_disposition = (
                "interpreted_substantive_directional"
                if criteria["member_action"] in {"Yea", "Nay"}
                else "interpreted_substantive_non_directional"
            )
            if review["axes"]["review_completion_state"] == "complete":
                _require(
                    action["disposition"] == expected_disposition,
                    f"{action_id}: review-friendly action remains uninterpreted "
                    "in a complete review",
                )
            if action["disposition"] in INTERPRETED_DISPOSITIONS:
                _require(
                    action["disposition"] == expected_disposition,
                    f"{action_id}: directional disposition contradicts member action",
                )
            else:
                _require(
                    action["disposition"] == "pending_interpretation",
                    f"{action_id}: review-friendly action has an invalid "
                    "non-interpreted disposition",
                )
        else:
            _require(
                action["disposition"]
                == _expected_non_interpreted_disposition(criteria),
                f"{action_id}: disposition does not match governed evidence state",
            )

        interpretation = action["interpretation"]
        if action["disposition"] in INTERPRETED_DISPOSITIONS:
            _require(interpretation is not None, f"{action_id}: missing interpretation")
            _require(
                interpretation["member_action"] == criteria["member_action"],
                f"{action_id}: interpretation changes the official member action",
            )
            _require(
                interpretation["episode_id"] == action["episode_id"],
                f"{action_id}: interpretation changes episode identity",
            )
            _require(
                interpretation["service_status"] == criteria["service_status"],
                f"{action_id}: interpretation changes service status",
            )
        else:
            _require(
                interpretation is None,
                f"{action_id}: non-interpreted disposition has analytical meaning",
            )
    return by_id


def _validate_episodes(
    review: dict[str, Any], actions: dict[str, dict[str, Any]]
) -> None:
    episodes = review["episodes"]
    episode_ids = [episode["episode_id"] for episode in episodes]
    _require(
        len(episode_ids) == len(set(episode_ids)),
        "episode identities must be unique",
    )
    all_memberships: dict[str, str] = {}
    latest_dates: list[date] = []

    for episode in episodes:
        episode_id = episode["episode_id"]
        action_ids = episode["action_ids"]
        action_set = set(action_ids)
        _require(
            action_set <= set(actions),
            f"{episode_id}: episode references an action outside the issue universe",
        )
        _require(
            set(episode["chronological_action_ids"]) == action_set,
            f"{episode_id}: chronological order must contain every episode action once",
        )
        chronological_dates = [
            date.fromisoformat(actions[action_id]["action_date"])
            for action_id in episode["chronological_action_ids"]
        ]
        _require(
            chronological_dates == sorted(chronological_dates),
            f"{episode_id}: actions must be chronological oldest first",
        )
        latest = max(chronological_dates)
        _require(
            date.fromisoformat(episode["latest_action_date"]) == latest,
            f"{episode_id}: latest action date is incorrect",
        )
        latest_dates.append(latest)

        for action_id in action_ids:
            _require(
                action_id not in all_memberships,
                f"{action_id}: action belongs to more than one episode",
            )
            all_memberships[action_id] = episode_id
            _require(
                actions[action_id]["episode_id"] == episode_id,
                f"{action_id}: action and episode membership disagree",
            )

        meaning_ids = [item["action_id"] for item in episode["action_meanings"]]
        member_ids = [item["action_id"] for item in episode["member_record"]]
        _require(
            len(meaning_ids) == len(set(meaning_ids))
            and set(meaning_ids) == action_set,
            f"{episode_id}: action meanings do not cover exact episode membership",
        )
        _require(
            len(member_ids) == len(set(member_ids))
            and set(member_ids) == action_set,
            f"{episode_id}: member record does not cover exact episode membership",
        )
        for item in episode["member_record"]:
            _require(
                item["member_action"]
                == actions[item["action_id"]]["review_friendliness"]["member_action"],
                f"{episode_id}: member record changes an official action state",
            )

        unresolved = {
            action_id
            for action_id in action_ids
            if actions[action_id]["disposition"] in OPEN_REVIEW_DISPOSITIONS
        }
        _require(
            set(episode["unresolved_action_ids"]) == unresolved,
            f"{episode_id}: unresolved membership is incomplete",
        )
        if unresolved:
            _require(
                episode["completion_state"] == "partial",
                f"{episode_id}: unresolved actions require an explicit partial episode",
            )
            has_source_gap = any(
                actions[action_id]["disposition"] in UNRESOLVED_DISPOSITIONS
                for action_id in unresolved
            )
            _require(
                episode["source_completeness"]
                == ("partial" if has_source_gap else "complete"),
                f"{episode_id}: source completeness does not match unresolved state",
            )
        else:
            _require(
                episode["completion_state"] == "complete"
                and episode["source_completeness"] == "complete",
                f"{episode_id}: resolved membership must be a complete episode",
            )

    _require(
        latest_dates == sorted(latest_dates, reverse=True),
        "public episode order must be newest latest action first",
    )
    for action_id, action in actions.items():
        if action["episode_id"] is None:
            _require(
                action_id not in all_memberships,
                f"{action_id}: null episode action appears in an episode",
            )
        else:
            _require(
                all_memberships.get(action_id) == action["episode_id"],
                f"{action_id}: declared episode membership is missing",
            )
        if action["disposition"] in INTERPRETED_DISPOSITIONS:
            _require(
                action_id in all_memberships,
                f"{action_id}: interpreted action must belong to exactly one episode",
            )


def _derived_blockers(review: dict[str, Any]) -> set[str]:
    axes = review["axes"]
    actions = review["action_accounting"]
    synthesis = review["synthesis"]
    blockers: set[str] = set()
    if not review["issue_universe"]["action_ids"]:
        blockers.add("issue_universe_not_defined")
    if axes["review_scope"] != "full_defined_issue_record":
        blockers.add("review_scope_not_full_defined_issue_record")
    if axes["review_completion_state"] != "complete":
        blockers.add("review_completion_not_complete")
    if synthesis["full_record_action_accounting"] != "passed":
        blockers.add("action_accounting_incomplete")
    if any(
        action["review_friendliness"]["is_review_friendly"]
        and action["disposition"] not in INTERPRETED_DISPOSITIONS
        for action in actions
    ):
        blockers.add("review_friendly_action_uninterpreted")
    if any(episode["completion_state"] == "partial" for episode in review["episodes"]):
        blockers.add("partial_episode")
    dispositions = {action["disposition"] for action in actions}
    if "source_unresolved" in dispositions or "missing_evidence" in dispositions:
        blockers.add("source_unresolved")
    if "source_conflicting" in dispositions:
        blockers.add("source_conflicting")
    if "source_constraint_blocked" in dispositions:
        blockers.add("source_constraint_blocked")
    if not synthesis["all_interpreted_episode_outcomes_supplied"]:
        blockers.add("episode_outcomes_not_supplied")
    if not synthesis["contradictory_and_mixed_evidence_retained"]:
        blockers.add("contradictory_or_mixed_evidence_not_retained")
    if synthesis["semantic_validation"] != "passed":
        blockers.add("semantic_validation_not_passed")
    if synthesis["human_editorial_review"] != "approved":
        blockers.add("human_editorial_review_not_approved")
    if synthesis["source_boundaries"] != "resolved":
        blockers.add("source_unresolved")
    if synthesis["outcome"] == "no_safe_synthesis":
        blockers.add("no_safe_synthesis")
    return blockers


def _validate_synthesis(review: dict[str, Any]) -> None:
    axes = review["axes"]
    synthesis = review["synthesis"]
    has_partial_or_unresolved = any(
        episode["completion_state"] == "partial" for episode in review["episodes"]
    ) or any(
        action["disposition"] in UNRESOLVED_DISPOSITIONS
        for action in review["action_accounting"]
    )
    if axes["review_completion_state"] == "complete" and has_partial_or_unresolved:
        _require(
            synthesis["source_boundaries"] == "synthesis_blocking",
            "completed accounting with unresolved evidence requires an explicit "
            "synthesis-blocking boundary",
        )
    _require(
        synthesis["full_record_action_accounting"]
        == (
            "passed"
            if axes["review_scope"] == "full_defined_issue_record"
            and axes["review_completion_state"] == "complete"
            else "not_passed"
        ),
        "sample or partial review cannot claim full-record action accounting",
    )
    blockers = _derived_blockers(review)
    _require(
        set(synthesis["eligibility_blockers"]) == blockers,
        "full-synthesis eligibility blockers do not match governed state",
    )
    expected_eligible = (
        not blockers
        and synthesis["outcome"] in FULL_SYNTHESIS_OUTCOMES
    )
    _require(
        synthesis["full_issue_synthesis_eligible"] is expected_eligible,
        "full_issue_synthesis_eligible is not the derived gate result",
    )
    claim_class = axes["public_claim_class"]
    outcome = synthesis["outcome"]
    if claim_class == "reviewed_sample_finding":
        _require(
            axes["review_scope"] in {"benchmark_sample", "bounded_partial_record"}
            and axes["semantic_tier"] == "reviewed_conclusion",
            "reviewed sample finding requires a bounded reviewed conclusion",
        )
    elif claim_class == "full_issue_synthesis":
        _require(
            expected_eligible
            and outcome
            in {
                "repeated_pattern",
                "mechanism_divide",
                "uniform_direction",
                "mixed_or_qualified",
            },
            "full issue synthesis lacks full-record eligibility",
        )
    elif claim_class == "full_review_no_common_throughline":
        _require(
            expected_eligible and outcome == "no_common_throughline",
            "no-common-throughline claim lacks a complete eligible review",
        )
    elif claim_class == "full_review_no_safe_synthesis":
        _require(
            axes["review_scope"] == "full_defined_issue_record"
            and axes["review_completion_state"] == "complete"
            and outcome == "no_safe_synthesis"
            and synthesis["semantic_validation"] == "passed"
            and synthesis["human_editorial_review"] == "approved",
            "no-safe-synthesis claim lacks a completed reviewed full record",
        )


def _validate_frontend(review: dict[str, Any]) -> None:
    axes = review["axes"]
    synthesis = review["synthesis"]
    benchmark = review["benchmark"]
    frontend = review["frontend_state"]
    actions = review["action_accounting"]
    episodes = review["episodes"]
    expected = {
        "review_scope": axes["review_scope"],
        "review_completion_state": axes["review_completion_state"],
        "public_claim_class": axes["public_claim_class"],
        "total_recorded_actions": len(actions),
        "review_friendly_actions": sum(
            action["review_friendliness"]["is_review_friendly"] for action in actions
        ),
        "interpreted_actions": sum(
            action["disposition"] in INTERPRETED_DISPOSITIONS for action in actions
        ),
        "unresolved_actions": sum(
            action["disposition"] in OPEN_REVIEW_DISPOSITIONS for action in actions
        ),
        "procedural_context_actions": sum(
            action["disposition"] == "procedural_context" for action in actions
        ),
        "present_actions": sum(
            action["review_friendliness"]["member_action"] == "Present"
            for action in actions
        ),
        "not_voting_actions": sum(
            action["review_friendliness"]["member_action"] == "Not Voting"
            for action in actions
        ),
        "complete_episode_count": sum(
            episode["completion_state"] == "complete" for episode in episodes
        ),
        "partial_episode_count": sum(
            episode["completion_state"] == "partial" for episode in episodes
        ),
        "full_issue_synthesis_eligible": synthesis[
            "full_issue_synthesis_eligible"
        ],
        "benchmark_sample_available": benchmark["benchmark_sample_available"],
    }
    for field, value in expected.items():
        _require(
            frontend[field] == value,
            f"frontend state field {field} does not match governed state",
        )

    teaser = frontend["conclusion_teaser"]
    if teaser is not None:
        _require(
            teaser["valid_scope"] == axes["review_scope"],
            "conclusion teaser broadens its reviewed scope",
        )
        _require(
            axes["public_claim_class"] != "vote_record_only",
            "vote-record-only state cannot expose a conclusion teaser",
        )

    labels = set(frontend["available_labels"])
    _require("Vote receipts available" in labels, "vote receipts label is required")
    if axes["review_scope"] == "benchmark_sample":
        _require(
            "Reviewed benchmark sample" in labels,
            "benchmark sample requires its truthful public label",
        )
    else:
        _require(
            "Reviewed benchmark sample" not in labels,
            "non-benchmark scope cannot use the benchmark-sample label",
        )
    if (
        axes["review_scope"] == "full_defined_issue_record"
        and axes["review_completion_state"] == "complete"
    ):
        _require("Full review complete" in labels, "completed full review label missing")
    else:
        _require(
            "Full review complete" not in labels,
            "partial or sample review cannot use the full-review label",
        )
    if axes["public_claim_class"] == "full_issue_synthesis":
        _require(
            "Full issue interpretation available" in labels,
            "eligible full synthesis label missing",
        )
    else:
        _require(
            "Full issue interpretation available" not in labels,
            "non-synthesis claim cannot use the full-interpretation label",
        )
    if axes["public_claim_class"] == "full_review_no_common_throughline":
        _require(
            "No common throughline found" in labels,
            "no-common-throughline label missing",
        )
    else:
        _require(
            "No common throughline found" not in labels,
            "unrelated claim cannot use the no-common-throughline label",
        )
    if axes["public_claim_class"] == "full_review_no_safe_synthesis":
        _require(
            "No safe synthesis available" in labels,
            "no-safe-synthesis label missing",
        )
    else:
        _require(
            "No safe synthesis available" not in labels,
            "unrelated claim cannot use the no-safe-synthesis label",
        )


def _validate_benchmark_and_history(review: dict[str, Any]) -> None:
    benchmark = review["benchmark"]
    _require(
        benchmark["benchmark_sample_available"]
        == bool(benchmark["benchmark_refs"]),
        "benchmark availability must match immutable benchmark references",
    )
    _require(
        benchmark["role"]
        == ("immutable_reference" if benchmark["benchmark_refs"] else "no_benchmark"),
        "benchmark role must match benchmark references",
    )
    publication = review["historical_publication"]
    if publication["state"] == "active":
        _require(
            publication["artifact_id"] is not None
            and publication["effective_semantic_tier"] is not None
            and publication["publication_receipt_refs"],
            "active historical publication requires artifact, tier, and receipt",
        )


def _validate_provenance(review: dict[str, Any]) -> None:
    for source_ref in review["provenance"]["source_refs"]:
        if source_ref.startswith("docs/"):
            _require((ROOT / source_ref).is_file(), f"missing source ref: {source_ref}")
    protected = review["provenance"]["protected_files"]
    paths = [item["path"] for item in protected]
    _require(len(paths) == len(set(paths)), "protected file paths must be unique")
    for item in protected:
        path = ROOT / item["path"]
        _require(path.is_file(), f"protected file is missing: {item['path']}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        _require(
            actual == item["sha256"],
            f"protected historical file changed: {item['path']}",
        )


def validate_review(review: dict[str, Any]) -> dict[str, int]:
    """Validate one manifest and return deterministic summary counts."""

    errors = _schema_errors(review)
    _require(not errors, "schema validation failed:\n" + "\n".join(errors))
    _require(
        compute_universe_sha256(review)
        == review["issue_universe"]["snapshot_sha256"],
        "issue-universe content digest does not match its action membership",
    )
    actions = _validate_actions(review)
    _validate_episodes(review, actions)
    _validate_synthesis(review)
    _validate_frontend(review)
    _validate_benchmark_and_history(review)
    _validate_provenance(review)
    return {
        "action_count": len(actions),
        "episode_count": len(review["episodes"]),
        "review_friendly_action_count": sum(
            action["review_friendliness"]["is_review_friendly"]
            for action in actions.values()
        ),
    }


def main() -> int:
    paths = sorted(REVIEW_ROOT.glob("*.json"))
    if not paths:
        print("ERROR: no full-record review manifests found", file=sys.stderr)
        return 1
    results: dict[str, dict[str, int]] = {}
    try:
        for path in paths:
            review = json.loads(path.read_text(encoding="utf-8"))
            results[path.relative_to(ROOT).as_posix()] = validate_review(review)
    except (FullRecordValidationError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": "pass",
                "schema": "full_record_issue_interpretation_v1",
                "manifests": results,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
