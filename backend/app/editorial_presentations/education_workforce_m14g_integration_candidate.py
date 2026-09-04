"""Detached, non-authorizing M14G Education & Workforce preview adapter."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from .compiler import canonical_digest
from .integration_candidate import governed_position_summary
from .selector import SUPPORTED_ISSUES, _fallback


M14G_PREVIEW_TOKEN = "m14g-education-workforce"
M14G_ARTIFACT_ID = "site-integration-candidate:f000477:education_workforce:m14g:v1"
M14G_SCHEMA_VERSION = "m14g_site_integration_candidate_v1"
BASELINE_MAIN_SHA = "50777a5fd1ce84763e6a294db25578639aa5dce7"
ACCEPTED_PUBLIC_COPY_SUBJECT_SHA = (
    "4fed310450608f1465f2617721e7665670d855f70cbcd50471aa46fc7cac0810"
)
PUBLIC_WORDING_AUTHORITY_SUBJECT_SHA = (
    "9b1962e1d33dd144a609cd9cbcb5114f81c51a8ce4195bc24112ba9fb10d0cfb"
)
M14D_FINDINGS_SUBJECT_SHA = (
    "795027fdcf49a4956b99804be9d44ec7bd233877e4bc76caa4121f7b61df169d"
)
M14D_AUTHORITY_SUBJECT_SHA = (
    "456d9f6f9577e8604480cdb40a08cb1f92e443ab3e02ff33cb2ecd193ca16638"
)
EXPECTED_WORDING_SHAS = {
    "m14f:issue_overview:education_workforce": "57c3ac7a93b136e6057ffee961f6e3a0611d004b5e2fd7a0aeaa6a53002aeae1",
    "m14f:pattern:china_linked_education_funding": "45500355c675fc5330b61988fe2a5f24c3967cf7aaaff846464561198fd26120",
    "m14f:pattern:collective_bargaining_continuity": "eaec4f73c5bf2103f98ad8710a1330a98c239c163d3bc9f80ef1cfeb52a200cf",
    "m14f:notable:hr1048_substitute_final": "87caf258fdae8fadc4420402094f0ff763aee85acb2249296dc0a23d8865dc73",
}
EXPECTED_RENDERED_WORDING_DIGESTS = {
    "m14f:issue_overview:education_workforce": "c9e68ee7af052063293a621eec8a8d932b03a23a3c2d2e633845501e6ef67ed6",
    "m14f:pattern:china_linked_education_funding": "36a5dc3c5f330d75165922d90c109d49a1dbca26187426e910bccd6dff9d2396",
    "m14f:pattern:collective_bargaining_continuity": "746ac834b549b4b8a11d3eccc60a990fad84e96074289444e373654dfd509483",
    "m14f:notable:hr1048_substitute_final": "7a725a5fa482747b1238f816586b02933e29b79d0b632a36bf6702b71b11f30b",
}
EXPECTED_RECEIPT_SEMANTICS_DIGEST = (
    "f54231a1e24909fad7cfe4c6418a55195de24e1a915a8cf5188287701f520f11"
)
OLD_HR5408_MEANING = (
    "The House choice was whether to pass H.R. 5408, which would accelerate "
    "workplace time-to-contract under the National Labor Relations Act."
)


class EducationWorkforceM14GError(ValueError):
    """Raised when the detached candidate fails closed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EducationWorkforceM14GError(message)


def _retained_limitations(record: dict[str, Any]) -> list[str]:
    return [
        treatment["public_copy"]
        for treatment in record["limitation_treatments"]
        if treatment["treatment"] == "retained_public_copy"
    ]


def _compile_wording(record: dict[str, Any]) -> dict[str, Any]:
    direction = record["direction_display"]
    lineage = record["derived_lineage"]
    return {
        "wording_item_id": record["wording_item_id"],
        "surface": record["surface"],
        "title": record["public_title"],
        "public_title": record["public_title"],
        "primary_sentence": record["primary_sentence"],
        "secondary_clarification": "",
        "evidence_count_label": record["evidence_count_label"],
        "direction": direction["label"].lower() if direction else None,
        "direction_label": direction["label"] if direction else None,
        "direction_symbol": direction["symbol"] if direction else None,
        "show_direction": direction is not None,
        "action_ids": list(lineage["action_ids"]),
        "episode_ids": list(lineage["episode_ids"]),
        "public_supporting_action_ids": list(lineage["action_ids"]),
        "public_supporting_episode_ids": list(lineage["episode_ids"]),
        "semantic_lineage_action_ids": list(lineage["action_ids"]),
        "semantic_lineage_episode_ids": list(lineage["episode_ids"]),
        "semantic_source_ids": [record["semantic_source_id"]],
        "limitations": _retained_limitations(record),
        "mapping": {
            "wording_item_subject_sha256": record["wording_item_sha256"],
            "statement_basis": "accepted_m14f_public_copy",
            "raw_yea_nay_maps_to_direction": False,
        },
    }


def _display_identity(identity: str, action_id: str) -> str:
    if action_id == "house:119:1:79":
        return "H.Amdt. 12 to H.R. 1048"
    match = re.fullmatch(r"119:(hr|s|hamdt):(\d+)", identity)
    _require(match is not None, f"unsupported exact action identity: {identity}")
    prefix = {"hr": "H.R.", "s": "S.", "hamdt": "H.Amdt."}[match.group(1)]
    return f"{prefix} {match.group(2)}"


def _source_url(identity: dict[str, Any], *, action_date: str) -> str | None:
    source_id = identity["source_id"]
    source_type = identity["source_type"]
    if source_type == "house_clerk_roll_call":
        roll = int(source_id.rsplit(":", 1)[1])
        year = action_date[:4]
        return f"https://clerk.house.gov/evs/{year}/roll{roll:03d}.xml"
    if source_type == "congress_gov_bill_text":
        _, congress, kind, number, version = source_id.split(":")
        return (
            f"https://www.congress.gov/{congress}/bills/{kind}{number}/"
            f"BILLS-{congress}{kind}{number}{version}.xml"
        )
    if source_type == "congressional_record":
        package = source_id.split(":", 2)[1]
        return f"https://www.govinfo.gov/app/details/{package}"
    governed_locators = {
        "govinfo:FR-2025-04-03:2025-05836:EO14251": (
            "https://www.govinfo.gov/content/pkg/FR-2025-04-03/html/2025-05836.htm"
        ),
        "govinfo:FR-2025-01-30:2025-02090:EO14168": (
            "https://www.govinfo.gov/content/pkg/FR-2025-01-30/html/2025-02090.htm"
        ),
        "govinfo:USCODE-2024-title20:sec1094:e2Bii": (
            "https://www.govinfo.gov/content/pkg/USCODE-2024-title20/html/"
            "USCODE-2024-title20-chap28-subchapIV-partG-sec1094.htm"
        ),
    }
    if source_type in {
        "federal_register_executive_order",
        "united_states_code",
    }:
        return governed_locators.get(source_id)
    return None


def _source_label(identity: dict[str, Any], *, fallback: str) -> str:
    return {
        "house_clerk_roll_call": "Official House vote",
        "congress_gov_bill_text": "Bill or amendment text",
        "congressional_record": "Congressional Record",
        "federal_register_executive_order": "Executive order",
        "united_states_code": "U.S. Code",
    }.get(identity["source_type"], fallback)


def _source_links(
    identities: list[dict[str, Any]], *, action_date: str, label: str
) -> list[dict[str, str]]:
    links = []
    for identity in identities:
        url = _source_url(identity, action_date=action_date)
        if url:
            source_label = _source_label(identity, fallback=label)
            links.append(
                {"label": source_label, "url": url, "public_label": source_label}
            )
    return links


def _receipt_rows(
    ledger: list[dict[str, Any]],
    core: dict[str, Any],
    member_projection: dict[str, Any],
) -> list[dict[str, Any]]:
    episode_by_action = {
        action_id: episode["episode_id"]
        for episode in ledger
        for action_id in episode["action_ids"]
    }
    cores = {row["action_id"]: row for row in core["actions"]}
    projections = {row["action_id"]: row for row in member_projection["actions"]}
    action_ids = sorted(episode_by_action)
    _require(len(action_ids) == 17, "M14D ledger must contain exactly 17 actions")
    rows = []
    for action_id in action_ids:
        action_core = cores.get(action_id)
        projection = projections.get(action_id)
        _require(action_core is not None, f"missing V2 core for {action_id}")
        _require(projection is not None, f"missing V2 member projection for {action_id}")
        _require(
            projection["action_core_sha256"] == action_core["action_core_sha256"],
            f"V2 core/projection mismatch for {action_id}",
        )
        vote_sources = _source_links(
            projection["member_action_source_identities"],
            action_date=action_core["action_date"],
            label="Official House vote",
        )
        meaning_sources = _source_links(
            action_core["operative_meaning_source_identities"],
            action_date=action_core["action_date"],
            label="Official action meaning source",
        )
        member_action = projection["official_status"]
        meaning = action_core["accepted_exact_action_meaning"]
        caveats = list(action_core["accepted_shared_limitations"])
        session, roll = (int(value) for value in action_id.split(":")[-2:])
        rows.append(
            {
                "canonical_action_id": action_id,
                "roll_call_id": action_id,
                "chamber": action_core["chamber"],
                "congress": action_core["congress"],
                "session": session,
                "rollcall_number": roll,
                "vote_date": action_core["action_date"],
                "vote_type": action_core["legislative_stage"],
                "description": _display_identity(
                    action_core["exact_action_identity"], action_id
                ),
                "issue_domain": "EDUCATION_WORKFORCE",
                "position": member_action.lower().replace(" ", "_"),
                "interpretation_status": "interpreted",
                "plain_english_summary": meaning,
                "question": meaning,
                "uncertainty_note": " ".join(caveats),
                "source_url": vote_sources[0]["url"] if vote_sources else None,
                "source_basis": meaning_sources,
                "action_core_sha256": action_core["action_core_sha256"],
                "member_projection_action_core_sha256": projection[
                    "action_core_sha256"
                ],
                "source_identity_bindings": {
                    "governed_action_meaning": copy.deepcopy(
                        action_core["operative_meaning_source_identities"]
                    ),
                    "official_member_action": copy.deepcopy(
                        projection["member_action_source_identities"]
                    ),
                },
                "governed_receipt_projection": {
                    "canonical_action_id": action_id,
                    "episode_id": episode_by_action[action_id],
                    "exact_action_meaning": meaning,
                    "policy_question": meaning,
                    "member_action": member_action,
                    "exact_choice_position_effect": projection["exact_choice_effect"],
                    "caveats": caveats,
                    "action_meaning_sources": meaning_sources,
                    "vote_sources": vote_sources,
                    "episode_relationship": "This action is independently expandable in the reviewed record.",
                },
                "governed_receipt_control": None,
            }
        )
    return sorted(
        rows,
        key=lambda row: (row["vote_date"], row["rollcall_number"]),
        reverse=True,
    )


def compile_m14g_candidate(
    *,
    accepted_public_copy: dict[str, Any],
    public_wording_authority: dict[str, Any],
    accepted_findings: dict[str, Any],
    behavioral_authority: dict[str, Any],
    shared_core: dict[str, Any],
    member_projection: dict[str, Any],
    promotion_manifest: dict[str, Any],
    file_bindings: dict[str, dict[str, str]],
) -> dict[str, Any]:
    _require(
        accepted_public_copy["accepted_public_copy_subject_sha256"]
        == ACCEPTED_PUBLIC_COPY_SUBJECT_SHA,
        "M14F accepted-public-copy subject differs",
    )
    _require(
        public_wording_authority["authority_subject_sha256"]
        == PUBLIC_WORDING_AUTHORITY_SUBJECT_SHA,
        "M14F wording authority subject differs",
    )
    _require(
        accepted_public_copy["subject"]["authority_effect"]
        == "canonical_internal_public_copy_and_main_takeaway_selection_only",
        "M14F authority effect differs",
    )
    _require(
        accepted_findings["findings_subject_sha256"] == M14D_FINDINGS_SUBJECT_SHA,
        "M14D accepted findings subject differs",
    )
    _require(
        behavioral_authority["authority_subject_sha256"]
        == M14D_AUTHORITY_SUBJECT_SHA
        and accepted_findings["subject"]["human_authority"][
            "authority_subject_sha256"
        ]
        == M14D_AUTHORITY_SUBJECT_SHA,
        "M14D human authority differs",
    )
    records = accepted_public_copy["subject"]["accepted_wording_records"]
    _require(len(records) == 4, "M14F must contain exactly four accepted records")
    actual_shas = {row["wording_item_id"]: row["wording_item_sha256"] for row in records}
    _require(actual_shas == EXPECTED_WORDING_SHAS, "M14F wording SHAs differ")
    _require(
        promotion_manifest["v2_core_sha256"] == shared_core["corpus_sha256"]
        and promotion_manifest["member_projection_sha256"]
        == member_projection["projection_sha256"],
        "V2 promotion binding differs",
    )

    ledger = accepted_findings["subject"]["accepted_episode_disposition_ledger"]
    _require(len(ledger) == 16, "M14D ledger must contain exactly 16 episodes")
    compiled = [_compile_wording(row) for row in records]
    by_id = {row["wording_item_id"]: row for row in compiled}
    overview = by_id["m14f:issue_overview:education_workforce"]
    patterns = [
        by_id["m14f:pattern:china_linked_education_funding"],
        by_id["m14f:pattern:collective_bargaining_continuity"],
    ]
    notable = by_id["m14f:notable:hr1048_substitute_final"]
    receipts = _receipt_rows(ledger, shared_core, member_projection)
    display_actions = sorted(
        {action_id for item in [*patterns, notable] for action_id in item["action_ids"]}
    )
    overview_limitation = _retained_limitations(records[0])
    _require(len(overview_limitation) == 1, "overview limitation treatment differs")
    overview["limitations"] = []
    presentation = {
        "issue_id": "EDUCATION_WORKFORCE",
        "requested_scope": "119",
        "reviewed_scope": "119",
        "tier": "reviewed_conclusion",
        "tier_badge": "Full issue review",
        "teaser": overview["primary_sentence"],
        "coverage_text": overview["evidence_count_label"],
        "scope_boundary": "This preview covers Valerie Foushee's reviewed 119th-Congress Education & Workforce record.",
        "conclusion": None,
        "overview": overview,
        "syntheses": [],
        "repeated_patterns": patterns,
        "policy_trajectories": [],
        "notable_choices": [notable],
        "limitations": [
            {"heading": "Final H.R. 1048 vote", "body": overview_limitation[0]}
        ],
        "policy_episodes": [],
        "public_status_label": "Detached review preview",
        "review_state": {
            "review_scope": "full_defined_issue_record",
            "congress_scope": [119],
            "total_recorded_actions": 17,
            "complete_episode_count": 16,
            "semantic_tier": "reviewed_conclusion",
            "candidate_preview": True,
            "full_issue_synthesis_eligible": False,
        },
        "reviewed_action_ids": sorted(row["canonical_action_id"] for row in receipts),
        "noncounting_controls": [],
        "exact_action_receipts": [
            copy.deepcopy(row["governed_receipt_projection"]) for row in receipts
        ],
        "evidence_metadata": {
            "approved_universe_action_count": 17,
            "accepted_interpreted_action_count": 17,
            "accepted_episode_count": 16,
            "blocked_action_ids": [],
            "display_action_ids": display_actions,
        },
        "provenance": {
            "artifact_id": M14G_ARTIFACT_ID,
            "artifact_version": 1,
            "reviewed_wording_sha256": ACCEPTED_PUBLIC_COPY_SUBJECT_SHA,
        },
    }
    controls = {
        "accepted": False,
        "authorizing": False,
        "public": False,
        "production_selectable": False,
        "publication_eligible": False,
        "publication_active": False,
        "database_writes": False,
        "production_writes": False,
        "deployment": False,
        "preview_requires_server_opt_in": True,
        "preview_requires_explicit_candidate": True,
    }
    subject = {
        "member_bioguide_id": "F000477",
        "member_slug": "leg_valerie_p_foushee",
        "issue_id": "EDUCATION_WORKFORCE",
        "congress": 119,
        "baseline_main_sha": BASELINE_MAIN_SHA,
        "input_bindings": file_bindings,
        "accepted_wording_item_sha256s": actual_shas,
        "presentation": presentation,
        "receipt_projections": receipts,
        "preview_token": M14G_PREVIEW_TOKEN,
        "preview_isolation": {
            "server_environment": "EDITORIAL_PRESENTATION_PREVIEW=1",
            "frontend_environment": f"NEXT_PUBLIC_EDITORIAL_PRESENTATION_PREVIEW={M14G_PREVIEW_TOKEN}",
            "supported_scopes": ["119", "all"],
        },
        "controls": controls,
    }
    candidate = {
        "schema_version": M14G_SCHEMA_VERSION,
        "artifact_id": M14G_ARTIFACT_ID,
        **{key: controls[key] for key in (
            "accepted", "authorizing", "public", "production_selectable",
            "publication_eligible", "publication_active", "database_writes",
            "production_writes", "deployment",
        )},
        "subject": subject,
    }
    candidate["candidate_subject_sha256"] = canonical_digest(subject)
    validate_m14g_candidate(candidate)
    return candidate


def validate_m14g_candidate(candidate: dict[str, Any]) -> None:
    _require(candidate["artifact_id"] == M14G_ARTIFACT_ID, "M14G identity differs")
    _require(
        candidate["candidate_subject_sha256"] == canonical_digest(candidate["subject"]),
        "M14G subject digest differs",
    )
    _require(
        all(candidate[key] is False for key in (
            "accepted", "authorizing", "public", "production_selectable",
            "publication_eligible", "publication_active", "database_writes",
            "production_writes", "deployment",
        )),
        "M14G authority leaked",
    )
    presentation = candidate["subject"]["presentation"]
    items = [
        presentation["overview"],
        *presentation["repeated_patterns"],
        *presentation["notable_choices"],
    ]
    wording_fields = (
        "wording_item_id",
        "public_title",
        "primary_sentence",
        "evidence_count_label",
        "direction",
        "direction_label",
        "direction_symbol",
        "show_direction",
        "action_ids",
        "episode_ids",
        "limitations",
    )
    actual_wording_digests = {
        item["wording_item_id"]: canonical_digest(
            {field: item[field] for field in wording_fields}
        )
        for item in items
    }
    _require(
        actual_wording_digests == EXPECTED_RENDERED_WORDING_DIGESTS,
        "M14G rendered M14F wording differs",
    )
    _require(
        len(presentation["repeated_patterns"]) == 2
        and len(presentation["notable_choices"]) == 1
        and presentation["syntheses"] == []
        and presentation["policy_trajectories"] == [],
        "M14G presentation hierarchy differs",
    )
    _require(
        all(not row["show_direction"] for row in presentation["repeated_patterns"])
        and presentation["notable_choices"][0]["direction"] == "mixed"
        and presentation["notable_choices"][0]["show_direction"] is True,
        "M14G direction display differs",
    )
    rendered_limitations = [
        *(value for item in presentation["repeated_patterns"] for value in item["limitations"]),
        *(value for item in presentation["notable_choices"] for value in item["limitations"]),
    ]
    _require(len(rendered_limitations) == 6, "finding limitation count differs")
    _require(len(presentation["limitations"]) == 1, "top-level limitation count differs")
    receipts = candidate["subject"]["receipt_projections"]
    _require(
        len(receipts) == 17
        and len({row["canonical_action_id"] for row in receipts}) == 17
        and len({row["governed_receipt_projection"]["episode_id"] for row in receipts}) == 16,
        "M14G receipt accounting differs",
    )
    receipt_fields = (
        "canonical_action_id",
        "episode_id",
        "exact_action_meaning",
        "member_action",
        "exact_choice_position_effect",
        "caveats",
    )
    receipt_semantics = []
    for row in sorted(receipts, key=lambda value: value["canonical_action_id"]):
        projection = row["governed_receipt_projection"]
        receipt_semantics.append(
            {
                **{field: projection[field] for field in receipt_fields},
                "action_core_sha256": row["action_core_sha256"],
                "member_projection_action_core_sha256": row[
                    "member_projection_action_core_sha256"
                ],
            }
        )
    _require(
        canonical_digest(receipt_semantics) == EXPECTED_RECEIPT_SEMANTICS_DIGEST,
        "M14G governed V2 receipt semantics differ",
    )
    hr5408 = next(row for row in receipts if row["canonical_action_id"] == "house:119:2:216")
    _require(
        hr5408["governed_receipt_projection"]["exact_action_meaning"].startswith(
            "Current wages, hours, and employment terms would have to be maintained"
        )
        and OLD_HR5408_MEANING not in json.dumps(candidate, ensure_ascii=False),
        "H.R. 5408 regressed to historical M13 semantics",
    )
    hr1005 = next(row for row in receipts if row["canonical_action_id"] == "house:119:1:312")
    _require(
        hr1005["governed_receipt_projection"]["member_action"] == "Not Voting"
        and hr1005["governed_receipt_projection"]["exact_choice_position_effect"]
        == "resolved_non_directional",
        "H.R. 1005 became directional",
    )


def load_m14g_candidate(path: Path) -> dict[str, Any]:
    candidate = json.loads(path.read_text(encoding="utf-8"))
    validate_m14g_candidate(candidate)
    return candidate


def select_m14g_preview(
    candidate: dict[str, Any], *, legislator_id: str, member_bioguide_id: str, scope: str
) -> dict[str, Any]:
    validate_m14g_candidate(candidate)
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


def merge_m14g_preview_evidence(
    base_response: dict[str, Any], candidate: dict[str, Any], *, domain: str, scope: str
) -> dict[str, Any]:
    validate_m14g_candidate(candidate)
    if domain.strip().upper() != "EDUCATION_WORKFORCE" or scope not in {"119", "all"}:
        return copy.deepcopy(base_response)
    accepted = copy.deepcopy(candidate["subject"]["receipt_projections"])
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


def merge_m14g_preview_positions(
    base_response: dict[str, Any], *, governed_evidence: list[dict[str, Any]]
) -> dict[str, Any]:
    result = copy.deepcopy(base_response)
    summary = governed_position_summary(governed_evidence, domain="EDUCATION_WORKFORCE")
    result["positions"] = [
        row for row in result.get("positions", []) if row.get("domain") != "EDUCATION_WORKFORCE"
    ] + [summary]
    return result
