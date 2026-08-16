"""Publication-inactive Environment & Energy site-integration candidate."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .compiler import canonical_digest
from .integration_candidate import _compile_wording_item
from .selector import SUPPORTED_ISSUES, _fallback

M12M_PREVIEW_TOKEN = "m12m-environment-energy"
M12M_ARTIFACT_ID = "site-integration-candidate:f000477:environment_energy:119:v1"
M12M_SCHEMA_VERSION = "editorial_site_integration_candidate_v1"


class EnvironmentSiteIntegrationCandidateError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EnvironmentSiteIntegrationCandidateError(message)


def compile_environment_site_integration_candidate(
    *,
    authority: dict[str, Any],
    implementation: dict[str, Any],
    parity: dict[str, Any],
    authority_file_sha256: str,
    implementation_file_sha256: str,
    parity_file_sha256: str,
    accepted_base_sha: str,
    preview_data: dict[str, Any],
) -> dict[str, Any]:
    records = implementation["subject"]["implementation_records"]
    _require(len(records) == 5, "M12L must contain exactly five wording records")
    compiled = [
        _compile_wording_item(row["implemented_reviewed_wording"]) for row in records
    ]
    by_surface: dict[str, list[dict[str, Any]]] = {}
    for item in compiled:
        by_surface.setdefault(item["surface"], []).append(item)
    expected = {
        "issue_overview": 1,
        "synthesis": 1,
        "repeated_pattern": 3,
        "trajectory": 0,
        "notable_choice": 0,
    }
    actual = {name: len(by_surface.get(name, [])) for name in expected}
    _require(actual == expected, "M12L surface accounting differs")
    _require(
        all(
            not item["show_direction"]
            and item["direction"] is None
            and item["direction_label"] is None
            and item["direction_symbol"] is None
            for item in compiled
        ),
        "directionless accepted wording gained a public direction",
    )
    all_actions = sorted(
        {action for item in compiled for action in item["semantic_lineage_action_ids"]}
    )
    all_episodes = sorted(
        {
            episode
            for item in compiled
            for episode in item["semantic_lineage_episode_ids"]
        }
    )
    _require(
        len(all_actions) == len(all_episodes) == 13,
        "accepted Environment semantic lineage differs",
    )
    overview = by_surface["issue_overview"][0]
    presentation = {
        "issue_id": "ENVIRONMENT_ENERGY",
        "requested_scope": "119",
        "reviewed_scope": "119",
        "tier": "reviewed_conclusion",
        "tier_badge": "Full issue review",
        "teaser": overview["primary_sentence"],
        "coverage_text": overview["evidence_count_label"],
        "scope_boundary": "This issue summary covers Valerie Foushee's reviewed 119th-Congress Environment & Energy record. It does not infer motive, ideology, character, future behavior, or voting advice.",
        "conclusion": None,
        "overview": overview,
        "syntheses": by_surface["synthesis"],
        "repeated_patterns": by_surface["repeated_pattern"],
        "policy_trajectories": [],
        "notable_choices": [],
        "limitations": [],
        "policy_episodes": [],
        "public_status_label": "Issue summary candidate",
        "review_state": {
            "review_scope": "full_defined_issue_record",
            "congress_scope": [119],
            "semantic_tier": "reviewed_conclusion",
            "public_claim_class": "full_issue_synthesis",
            "scope_bounded_teaser": {"text": overview["primary_sentence"]},
            "total_recorded_actions": 63,
            "complete_episode_count": 63,
            "procedural_context_actions": 0,
            "full_issue_synthesis_eligible": True,
            "candidate_preview": True,
        },
        "reviewed_action_ids": [],
        "noncounting_controls": [],
        "exact_action_receipts": [],
        "evidence_metadata": {
            "approved_universe_action_count": 63,
            "accepted_interpreted_action_count": 63,
            "blocked_action_ids": [],
            "display_action_ids": all_actions,
        },
        "provenance": {
            "artifact_id": M12M_ARTIFACT_ID,
            "artifact_version": 1,
            "reviewed_wording_sha256": implementation["implementation_subject_sha256"],
        },
    }
    candidate = {
        "schema_version": M12M_SCHEMA_VERSION,
        "artifact_id": M12M_ARTIFACT_ID,
        "subject": {
            "member_bioguide_id": "F000477",
            "member_slug": "leg_valerie_p_foushee",
            "issue_id": "ENVIRONMENT_ENERGY",
            "congress": 119,
            "accepted_base_sha": accepted_base_sha,
            "accepted_wording_authority_binding": {
                "artifact_id": authority["artifact_id"],
                "file_sha256": authority_file_sha256,
                "subject_sha256": authority["authority_subject_sha256"],
            },
            "accepted_wording_implementation_binding": {
                "artifact_id": implementation["artifact_id"],
                "file_sha256": implementation_file_sha256,
                "subject_sha256": implementation["implementation_subject_sha256"],
            },
            "accepted_wording_parity_binding": {
                "artifact_id": parity["artifact_id"],
                "file_sha256": parity_file_sha256,
                "subject_sha256": parity["parity_subject_sha256"],
            },
            "surface_accounting": expected,
            "semantic_lineage": {
                "unique_action_ids": all_actions,
                "unique_episode_ids": all_episodes,
            },
            "presentation": presentation,
            "preview_data": copy.deepcopy(preview_data),
            "controls": {
                "authorizing": False,
                "public": False,
                "production_selectable": False,
                "publication_active": False,
                "publication_eligibility": False,
                "production_persistence": False,
                "database_writes": False,
                "production_writes": False,
                "deployment": False,
                "preview_requires_server_opt_in": True,
            },
        },
    }
    candidate["candidate_subject_sha256"] = canonical_digest(candidate["subject"])
    validate_environment_site_integration_candidate(candidate)
    return candidate


def _items(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    p = candidate["subject"]["presentation"]
    return [
        p["overview"],
        *p["syntheses"],
        *p["repeated_patterns"],
        *p["policy_trajectories"],
        *p["notable_choices"],
    ]


def validate_environment_site_integration_candidate(candidate: dict[str, Any]) -> None:
    _require(
        candidate.get("schema_version") == M12M_SCHEMA_VERSION
        and candidate.get("artifact_id") == M12M_ARTIFACT_ID,
        "M12M identity differs",
    )
    subject = candidate["subject"]
    _require(
        candidate.get("candidate_subject_sha256") == canonical_digest(subject),
        "M12M subject digest differs",
    )
    _require(
        subject["member_bioguide_id"] == "F000477"
        and subject["issue_id"] == "ENVIRONMENT_ENERGY"
        and subject["congress"] == 119,
        "M12M subject differs",
    )
    controls = subject["controls"]
    _require(
        controls["preview_requires_server_opt_in"] is True
        and all(
            value is False
            for key, value in controls.items()
            if key != "preview_requires_server_opt_in"
        ),
        "M12M authority leaked",
    )
    items = _items(candidate)
    _require(
        len(items) == len({item["wording_item_id"] for item in items}) == 5,
        "M12M wording mapping differs",
    )
    _require(
        all(
            item["mapping"]["statement_basis"]
            == "accepted_semantic_proposition_content"
            and item["mapping"]["raw_yea_nay_maps_to_direction"] is False
            and not item["show_direction"]
            and item["direction"] is None
            and item["direction_label"] is None
            and item["direction_symbol"] is None
            for item in items
        ),
        "M12M invented direction or semantic source",
    )
    expected_counts = {
        "wording:synthesis:congressional-disapproval": 13,
        "wording:pattern:california-emissions-waivers": 2,
        "wording:pattern:doe-appliance-equipment-rules": 4,
        "wording:pattern:blm-land-decisions": 7,
    }
    for item in items:
        if item["wording_item_id"] in expected_counts:
            expected = expected_counts[item["wording_item_id"]]
            _require(
                len(item["semantic_lineage_action_ids"])
                == len(item["public_supporting_action_ids"])
                == expected,
                f"{item['wording_item_id']} support count differs",
            )
    forbidden = {"house:119:2:136"}
    _require(
        not forbidden
        & {action for item in items for action in item["semantic_lineage_action_ids"]},
        "non-directional H.R. 6387 entered M12M",
    )
    evidence = subject["preview_data"]["evidence_119"]
    _require(
        len(evidence) == 63
        and len({row["canonical_action_id"] for row in evidence}) == 63
        and all(row.get("governed_receipt_projection") for row in evidence),
        "M12M preview evidence differs",
    )


def load_environment_site_integration_candidate(path: Path) -> dict[str, Any]:
    candidate = json.loads(path.read_text(encoding="utf-8"))
    validate_environment_site_integration_candidate(candidate)
    return candidate


def select_environment_site_integration_preview(
    candidate: dict[str, Any],
    *,
    legislator_id: str,
    member_bioguide_id: str,
    scope: str,
) -> dict[str, Any]:
    validate_environment_site_integration_candidate(candidate)
    result = {issue_id: _fallback(issue_id, scope) for issue_id in SUPPORTED_ISSUES}
    subject = candidate["subject"]
    if (
        legislator_id == subject["member_slug"]
        and member_bioguide_id == subject["member_bioguide_id"]
        and scope in {"119", "all"}
    ):
        presentation = copy.deepcopy(subject["presentation"])
        presentation["requested_scope"] = scope
        if scope == "all":
            presentation["scope_boundary"] += (
                " The analytical summary remains bounded to the 119th-Congress record."
            )
        result[subject["issue_id"]] = presentation
    return {
        "schema_version": "editorial_public_presentations_api_v1",
        "legislator_id": legislator_id,
        "member_bioguide_id": member_bioguide_id,
        "scope": scope,
        "presentations": [result[issue_id] for issue_id in SUPPORTED_ISSUES],
    }


def merge_environment_preview_evidence(
    base_response: dict[str, Any], candidate: dict[str, Any], *, domain: str, scope: str
) -> dict[str, Any]:
    validate_environment_site_integration_candidate(candidate)
    if domain.strip().upper() != "ENVIRONMENT_ENERGY" or scope not in {"119", "all"}:
        return copy.deepcopy(base_response)
    accepted = copy.deepcopy(candidate["subject"]["preview_data"]["evidence_119"])
    retained = (
        [
            copy.deepcopy(row)
            for row in base_response.get("evidence", [])
            if int(row.get("congress", 0) or 0) != 119
        ]
        if scope == "all"
        else []
    )
    return {**copy.deepcopy(base_response), "evidence": [*accepted, *retained]}


def merge_environment_preview_positions(
    base_response: dict[str, Any], *, governed_evidence: list[dict[str, Any]]
) -> dict[str, Any]:
    """Recompute only the inactive Environment preview summary from governed rows."""

    result = copy.deepcopy(base_response)
    rows = [
        row
        for row in governed_evidence
        if row.get("issue_domain") == "ENVIRONMENT_ENERGY"
    ]
    yea = sum(str(row.get("position", "")).lower() == "yea" for row in rows)
    nay = sum(str(row.get("position", "")).lower() == "nay" for row in rows)
    accepted = [row for row in rows if row.get("governed_receipt_projection")]
    summary = {
        "domain": "ENVIRONMENT_ENERGY",
        "yea_count": yea,
        "nay_count": nay,
        "other_count": len(rows) - yea - nay,
        "total_votes": len(rows),
        "recorded_votes": len(rows),
        "interpreted_support_count": sum(
            row["governed_receipt_projection"]["exact_choice_position_effect"]
            == "supports_exact_choice"
            for row in accepted
        ),
        "interpreted_oppose_count": sum(
            row["governed_receipt_projection"]["exact_choice_position_effect"]
            == "opposes_exact_choice"
            for row in accepted
        ),
        "interpreted_other_count": 0,
        "interpreted_total": len(accepted),
    }
    result["positions"] = [
        row
        for row in result.get("positions", [])
        if row.get("domain") != "ENVIRONMENT_ENERGY"
    ] + [summary]
    return result
