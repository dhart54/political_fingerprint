"""Deterministic, non-authorizing site-integration candidate support.

This module projects already accepted public wording into the production API
shape. It does not infer wording, direction, grouping, or publication state.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from .compiler import canonical_digest
from .selector import SUPPORTED_ISSUES, _fallback


M11M_PREVIEW_TOKEN = "m11m-national-security"
M11M_ARTIFACT_ID = "site-integration-candidate:f000477:national_security_foreign:119:v1"
M11M_SCHEMA_VERSION = "editorial_site_integration_candidate_v1"
BLOCKED_ACTION_ID = "house:119:2:278"


class SiteIntegrationCandidateError(ValueError):
    """Raised when an inactive integration candidate fails closed."""


def canonical_file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SiteIntegrationCandidateError(message)


def _unique_binding_values(item: dict[str, Any], field: str) -> list[str]:
    return sorted(
        {
            value
            for binding in item["semantic_source_bindings"]
            for value in binding[field]
        }
    )


def _compile_wording_item(item: dict[str, Any]) -> dict[str, Any]:
    direction = item["direction_display"]
    public_limitations = [
        treatment["public_copy"]
        for treatment in item["limitation_treatments"]
        if treatment["treatment"] == "retained_public_copy" and treatment["public_copy"]
    ]
    source_ids = sorted(
        {binding["source_id"] for binding in item["semantic_source_bindings"]}
    )
    return {
        "wording_item_id": item["wording_item_id"],
        "surface": item["surface"],
        "title": item["public_title"],
        "primary_sentence": item["primary_sentence"],
        "secondary_clarification": item["secondary_clarification"],
        "evidence_count_label": item["evidence_count_label"],
        "direction": direction["label"].lower() if direction else None,
        "direction_label": direction["label"] if direction else None,
        "direction_symbol": direction["symbol"] if direction else None,
        "show_direction": direction is not None,
        "action_ids": _unique_binding_values(item, "evidence_action_ids"),
        "episode_ids": _unique_binding_values(item, "evidence_episode_ids"),
        "semantic_source_ids": source_ids,
        "limitations": public_limitations,
        "mapping": {
            "wording_item_subject_sha256": item["wording_item_subject_sha256"],
            "semantic_binding_count": len(item["semantic_source_bindings"]),
            "statement_basis": item["semantic_guard"]["statement_basis"],
            "raw_yea_nay_maps_to_direction": item["semantic_guard"][
                "raw_yea_nay_maps_to_direction"
            ],
        },
    }


def compile_site_integration_candidate(
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
    """Compile exact accepted wording into a detached preview candidate."""

    records = implementation["subject"]["implementation_records"]
    _require(len(records) == 18, "M11L must contain exactly 18 wording records")
    compiled = [
        _compile_wording_item(record["implemented_reviewed_wording"])
        for record in records
    ]
    by_surface: dict[str, list[dict[str, Any]]] = {}
    for item in compiled:
        by_surface.setdefault(item["surface"], []).append(item)
    expected = {
        "issue_overview": 1,
        "synthesis": 2,
        "repeated_pattern": 8,
        "trajectory": 1,
        "notable_choice": 6,
    }
    _require(
        {key: len(value) for key, value in by_surface.items()} == expected,
        "M11L surface accounting differs",
    )
    all_action_ids = {
        action_id for item in compiled for action_id in item["action_ids"]
    }
    _require(
        BLOCKED_ACTION_ID not in all_action_ids,
        "blocked H.R. 8800 action entered public wording",
    )
    overview = by_surface["issue_overview"][0]
    presentation = {
        "issue_id": "NATIONAL_SECURITY_FOREIGN",
        "requested_scope": "119",
        "reviewed_scope": "119",
        "tier": "reviewed_conclusion",
        "tier_badge": "Full issue review",
        "teaser": overview["primary_sentence"],
        "coverage_text": overview["evidence_count_label"],
        "scope_boundary": (
            "This issue summary covers Valerie Foushee's 119th-Congress House "
            "record through July 23, 2026. It does not infer motive, ideology, "
            "character, future behavior, or voting advice."
        ),
        "conclusion": None,
        "overview": overview,
        "syntheses": by_surface["synthesis"],
        "repeated_patterns": by_surface["repeated_pattern"],
        "policy_trajectories": by_surface["trajectory"],
        "notable_choices": by_surface["notable_choice"],
        "limitations": [],
        "policy_episodes": [],
        "public_status_label": "Issue summary candidate",
        "review_state": {
            "review_scope": "full_defined_issue_record",
            "congress_scope": [119],
            "semantic_tier": "reviewed_conclusion",
            "public_claim_class": "full_issue_synthesis",
            "scope_bounded_teaser": {"text": overview["primary_sentence"]},
            "total_recorded_actions": 82,
            "complete_episode_count": 81,
            "procedural_context_actions": 0,
            "full_issue_synthesis_eligible": True,
            "candidate_preview": True,
        },
        "reviewed_action_ids": [],
        "noncounting_controls": [
            {
                "canonical_action_id": BLOCKED_ACTION_ID,
                "boundary_type": "source_blocked_uninterpreted",
                "detail": "No public analytical meaning is available for this action.",
            }
        ],
        "exact_action_receipts": [],
        "evidence_metadata": {
            "official_cutoff": {
                "end_date": "2026-07-23",
                "latest_action_id": "house:119:2:283",
            },
            "approved_universe_action_count": 82,
            "accepted_interpreted_action_count": 81,
            "blocked_action_ids": [BLOCKED_ACTION_ID],
            "display_action_ids": sorted(all_action_ids),
        },
        "provenance": {
            "artifact_id": M11M_ARTIFACT_ID,
            "artifact_version": 1,
            "reviewed_wording_sha256": implementation["implementation_subject_sha256"],
        },
    }
    candidate = {
        "schema_version": M11M_SCHEMA_VERSION,
        "artifact_id": M11M_ARTIFACT_ID,
        "subject": {
            "member_bioguide_id": "F000477",
            "member_slug": "leg_valerie_p_foushee",
            "issue_id": "NATIONAL_SECURITY_FOREIGN",
            "congress": 119,
            "accepted_base_sha": accepted_base_sha,
            "m11l_authority_binding": {
                "artifact_id": authority["artifact_id"],
                "file_sha256": authority_file_sha256,
                "subject_sha256": authority["authority_subject_sha256"],
            },
            "m11l_implementation_binding": {
                "artifact_id": implementation["artifact_id"],
                "file_sha256": implementation_file_sha256,
                "subject_sha256": implementation["implementation_subject_sha256"],
            },
            "m11l_parity_binding": {
                "artifact_id": parity["artifact_id"],
                "file_sha256": parity_file_sha256,
                "subject_sha256": parity["parity_subject_sha256"],
            },
            "surface_accounting": expected,
            "presentation": presentation,
            "preview_data": copy.deepcopy(preview_data),
            "controls": {
                "authorizing": False,
                "public": False,
                "production_selectable": False,
                "publication_active": False,
                "production_persistence": False,
                "database_writes": False,
                "deployment": False,
                "preview_requires_server_opt_in": True,
            },
        },
    }
    candidate["candidate_subject_sha256"] = canonical_digest(candidate["subject"])
    validate_site_integration_candidate(candidate)
    return candidate


def validate_site_integration_candidate(candidate: dict[str, Any]) -> None:
    _require(
        candidate.get("schema_version") == M11M_SCHEMA_VERSION
        and candidate.get("artifact_id") == M11M_ARTIFACT_ID,
        "M11M candidate identity differs",
    )
    subject = candidate["subject"]
    _require(
        candidate.get("candidate_subject_sha256") == canonical_digest(subject),
        "M11M candidate subject digest differs",
    )
    _require(
        subject["member_bioguide_id"] == "F000477"
        and subject["member_slug"] == "leg_valerie_p_foushee"
        and subject["issue_id"] == "NATIONAL_SECURITY_FOREIGN"
        and subject["congress"] == 119,
        "M11M subject differs",
    )
    _require(
        all(
            value is False
            for key, value in subject["controls"].items()
            if key != "preview_requires_server_opt_in"
        )
        and subject["controls"]["preview_requires_server_opt_in"] is True,
        "M11M downstream authority leaked",
    )
    presentation = subject["presentation"]
    surfaces = {
        "issue_overview": [presentation["overview"]],
        "synthesis": presentation["syntheses"],
        "repeated_pattern": presentation["repeated_patterns"],
        "trajectory": presentation["policy_trajectories"],
        "notable_choice": presentation["notable_choices"],
    }
    _require(
        {key: len(value) for key, value in surfaces.items()}
        == subject["surface_accounting"],
        "M11M presentation surface accounting differs",
    )
    items = [item for values in surfaces.values() for item in values]
    _require(
        len({item["wording_item_id"] for item in items}) == 18,
        "M11M wording item mapping is not one-to-one",
    )
    _require(
        all(
            item["mapping"]["statement_basis"]
            == "accepted_semantic_proposition_content"
            and item["mapping"]["raw_yea_nay_maps_to_direction"] is False
            and item["action_ids"]
            for item in items
        ),
        "M11M semantic mapping is incomplete",
    )
    all_actions = {action_id for item in items for action_id in item["action_ids"]}
    _require(BLOCKED_ACTION_ID not in all_actions, "blocked action entered M11M")
    preview_data = subject["preview_data"]
    evidence = preview_data["evidence_119"]
    evidence_ids = [row["canonical_action_id"] for row in evidence]
    _require(
        len(evidence_ids) == 82
        and len(set(evidence_ids)) == 82
        and set(evidence_ids) == set(preview_data["action_ids_119"])
        and BLOCKED_ACTION_ID in evidence_ids,
        "M11M preview evidence accounting differs",
    )
    blocked = next(
        row for row in evidence if row["canonical_action_id"] == BLOCKED_ACTION_ID
    )
    _require(
        blocked.get("governed_receipt_projection") is None
        and blocked["governed_receipt_control"]["status"] == "noncounting_control",
        "blocked action gained an interpretation projection",
    )
    _require(
        all(
            row.get("governed_receipt_projection")
            and row.get("interpretation_status") == "interpreted"
            for row in evidence
            if row["canonical_action_id"] != BLOCKED_ACTION_ID
        ),
        "accepted preview evidence projection is incomplete",
    )
    ukraine = next(
        item
        for item in presentation["repeated_patterns"]
        if item["wording_item_id"] == "wording:pattern:ukraine-assistance"
    )
    _require(
        ukraine["primary_sentence"]
        == "Opposed three proposals to restrict Ukraine aid and supported one measure authorizing support for Ukraine."
        and ukraine["evidence_count_label"] == "4 votes · 4 assistance choices"
        and ukraine["show_direction"] is False
        and ukraine["direction_symbol"] is None
        and ukraine["direction_label"] is None,
        "Ukraine public semantic guard differs",
    )


def load_site_integration_candidate(path: Path) -> dict[str, Any]:
    candidate = json.loads(path.read_text(encoding="utf-8"))
    validate_site_integration_candidate(candidate)
    return candidate


def select_site_integration_preview(
    candidate: dict[str, Any],
    *,
    legislator_id: str,
    member_bioguide_id: str,
    scope: str,
) -> dict[str, Any]:
    """Project a validated candidate to the real API envelope for local review."""

    validate_site_integration_candidate(candidate)
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


def merge_site_integration_preview_evidence(
    base_response: dict[str, Any],
    candidate: dict[str, Any],
    *,
    domain: str,
    scope: str,
) -> dict[str, Any]:
    """Replace only 119th-Congress preview rows with governed M11M receipts."""

    validate_site_integration_candidate(candidate)
    if domain.strip().upper() != "NATIONAL_SECURITY_FOREIGN" or scope not in {
        "119",
        "all",
    }:
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


def merge_site_integration_preview_positions(
    base_response: dict[str, Any],
    *,
    governed_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    """Recompute the one preview issue summary from visible governed receipts."""

    result = copy.deepcopy(base_response)
    rows = [
        row
        for row in governed_evidence
        if row.get("issue_domain") == "NATIONAL_SECURITY_FOREIGN"
    ]
    yea = sum(str(row.get("position", "")).lower() == "yea" for row in rows)
    nay = sum(str(row.get("position", "")).lower() == "nay" for row in rows)
    other = len(rows) - yea - nay
    accepted = [row for row in rows if row.get("governed_receipt_projection")]
    summary = {
        "domain": "NATIONAL_SECURITY_FOREIGN",
        "yea_count": yea,
        "nay_count": nay,
        "other_count": other,
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
    existing = [
        row
        for row in result.get("positions", [])
        if row.get("domain") != "NATIONAL_SECURITY_FOREIGN"
    ]
    result["positions"] = [*existing, summary]
    return result
