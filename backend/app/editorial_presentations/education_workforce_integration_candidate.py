"""Publication-inactive Education & Workforce site-integration candidate."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .compiler import canonical_digest
from .integration_candidate import _compile_wording_item, governed_position_summary
from .selector import SUPPORTED_ISSUES, _fallback

M13M_PREVIEW_TOKEN = "m13m-education-workforce"
M13M_ARTIFACT_ID = "site-integration-candidate:f000477:education_workforce:119:v1"
M13M_SCHEMA_VERSION = "editorial_site_integration_candidate_v1"


class EducationWorkforceSiteIntegrationCandidateError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EducationWorkforceSiteIntegrationCandidateError(message)


def compile_education_workforce_site_integration_candidate(
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
    _require(len(records) == 3, "M13L must contain exactly three wording records")
    compiled = [
        _compile_wording_item(row["implemented_reviewed_wording"]) for row in records
    ]
    by_surface: dict[str, list[dict[str, Any]]] = {}
    for item in compiled:
        by_surface.setdefault(item["surface"], []).append(item)
    expected = {
        "issue_overview": 1,
        "synthesis": 0,
        "repeated_pattern": 1,
        "trajectory": 0,
        "notable_choice": 1,
    }
    actual = {name: len(by_surface.get(name, [])) for name in expected}
    _require(actual == expected, "M13L surface accounting differs")

    overview = by_surface["issue_overview"][0]
    pattern = by_surface["repeated_pattern"][0]
    notable = by_surface["notable_choice"][0]
    _require(
        not overview["show_direction"]
        and not pattern["show_direction"]
        and notable["show_direction"]
        and notable["direction"] == "mixed"
        and notable["direction_label"] == "Mixed"
        and notable["direction_symbol"] == "±",
        "only the H.R. 1048 notable may display Mixed",
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
        len(all_actions) == 4 and len(all_episodes) == 3,
        "accepted Education & Workforce semantic lineage differs",
    )
    presentation = {
        "issue_id": "EDUCATION_WORKFORCE",
        "requested_scope": "119",
        "reviewed_scope": "119",
        "tier": "reviewed_conclusion",
        "tier_badge": "Full issue review",
        "teaser": overview["primary_sentence"],
        "coverage_text": overview["evidence_count_label"],
        "scope_boundary": "This issue summary covers Valerie Foushee's reviewed 119th-Congress Education & Workforce record. The two findings remain separate and do not establish an overall position on education, China, foreign influence, education restrictions, or funding conditions. It does not infer motive, ideology, character, future behavior, or voting advice.",
        "conclusion": None,
        "overview": overview,
        "syntheses": [],
        "repeated_patterns": [pattern],
        "policy_trajectories": [],
        "notable_choices": [notable],
        "limitations": [],
        "policy_episodes": [],
        "public_status_label": "Issue summary candidate",
        "review_state": {
            "review_scope": "full_defined_issue_record",
            "congress_scope": [119],
            "semantic_tier": "reviewed_conclusion",
            "public_claim_class": "bounded_separate_findings",
            "scope_bounded_teaser": {"text": overview["primary_sentence"]},
            "total_recorded_actions": 17,
            "complete_episode_count": 16,
            "procedural_context_actions": 0,
            "full_issue_synthesis_eligible": False,
            "candidate_preview": True,
        },
        "reviewed_action_ids": [],
        "noncounting_controls": [],
        "exact_action_receipts": [],
        "evidence_metadata": {
            "approved_universe_action_count": 17,
            "accepted_interpreted_action_count": 17,
            "accepted_episode_count": 16,
            "blocked_action_ids": [],
            "display_action_ids": all_actions,
        },
        "provenance": {
            "artifact_id": M13M_ARTIFACT_ID,
            "artifact_version": 1,
            "reviewed_wording_sha256": implementation["implementation_subject_sha256"],
        },
    }
    candidate = {
        "schema_version": M13M_SCHEMA_VERSION,
        "artifact_id": M13M_ARTIFACT_ID,
        "subject": {
            "member_bioguide_id": "F000477",
            "member_slug": "leg_valerie_p_foushee",
            "issue_id": "EDUCATION_WORKFORCE",
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
    validate_education_workforce_site_integration_candidate(candidate)
    return candidate


def _items(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    presentation = candidate["subject"]["presentation"]
    return [
        presentation["overview"],
        *presentation["syntheses"],
        *presentation["repeated_patterns"],
        *presentation["policy_trajectories"],
        *presentation["notable_choices"],
    ]


def validate_education_workforce_site_integration_candidate(
    candidate: dict[str, Any],
) -> None:
    _require(
        candidate.get("schema_version") == M13M_SCHEMA_VERSION
        and candidate.get("artifact_id") == M13M_ARTIFACT_ID,
        "M13M identity differs",
    )
    subject = candidate["subject"]
    _require(
        candidate.get("candidate_subject_sha256") == canonical_digest(subject),
        "M13M subject digest differs",
    )
    _require(
        subject["member_bioguide_id"] == "F000477"
        and subject["issue_id"] == "EDUCATION_WORKFORCE"
        and subject["congress"] == 119,
        "M13M subject differs",
    )
    controls = subject["controls"]
    _require(
        controls["preview_requires_server_opt_in"] is True
        and all(
            value is False
            for key, value in controls.items()
            if key != "preview_requires_server_opt_in"
        ),
        "M13M authority leaked",
    )
    items = _items(candidate)
    _require(
        len(items) == len({item["wording_item_id"] for item in items}) == 3,
        "M13M wording mapping differs",
    )
    overview, pattern, notable = items
    _require(
        all(
            item["mapping"]["statement_basis"]
            == "accepted_semantic_proposition_content"
            and item["mapping"]["raw_yea_nay_maps_to_direction"] is False
            for item in items
        )
        and not overview["show_direction"]
        and not pattern["show_direction"]
        and notable["show_direction"]
        and notable["direction"] == "mixed",
        "M13M invented direction or semantic source",
    )
    _require(
        len(pattern["semantic_lineage_action_ids"]) == 2
        and len(pattern["semantic_lineage_episode_ids"]) == 2
        and len(notable["semantic_lineage_action_ids"]) == 2
        and len(notable["semantic_lineage_episode_ids"]) == 1,
        "M13M finding support differs",
    )
    evidence = subject["preview_data"]["evidence_119"]
    _require(
        len(evidence) == 17
        and len({row["canonical_action_id"] for row in evidence}) == 17
        and len({row["governed_receipt_projection"]["episode_id"] for row in evidence})
        == 16
        and all(row.get("governed_receipt_projection") for row in evidence),
        "M13M preview evidence differs",
    )
    hr1005 = next(
        row for row in evidence if row["canonical_action_id"] == "house:119:1:312"
    )
    _require(
        hr1005["governed_receipt_projection"]["exact_choice_position_effect"]
        == "non_directional_not_voting",
        "H.R. 1005 became directional",
    )


def load_education_workforce_site_integration_candidate(path: Path) -> dict[str, Any]:
    candidate = json.loads(path.read_text(encoding="utf-8"))
    validate_education_workforce_site_integration_candidate(candidate)
    return candidate


def select_education_workforce_site_integration_preview(
    candidate: dict[str, Any],
    *,
    legislator_id: str,
    member_bioguide_id: str,
    scope: str,
) -> dict[str, Any]:
    validate_education_workforce_site_integration_candidate(candidate)
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


def merge_education_workforce_preview_evidence(
    base_response: dict[str, Any], candidate: dict[str, Any], *, domain: str, scope: str
) -> dict[str, Any]:
    validate_education_workforce_site_integration_candidate(candidate)
    if domain.strip().upper() != "EDUCATION_WORKFORCE" or scope not in {"119", "all"}:
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


def merge_education_workforce_preview_positions(
    base_response: dict[str, Any], *, governed_evidence: list[dict[str, Any]]
) -> dict[str, Any]:
    result = copy.deepcopy(base_response)
    summary = governed_position_summary(governed_evidence, domain="EDUCATION_WORKFORCE")
    result["positions"] = [
        row
        for row in result.get("positions", [])
        if row.get("domain") != "EDUCATION_WORKFORCE"
    ] + [summary]
    return result
