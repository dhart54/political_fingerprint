from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from psycopg.rows import dict_row

from app.analysis.house_comparable_families import (
    ARTIFACT_VERSION,
    COMPARABLE_STATUSES,
    ComparableFamily,
    ComparableFamilyArtifact,
    load_house_comparable_family_artifact,
)
from app.db import get_connection


SUPPORTED_CONGRESSES = (118, 119)
SUBSTANTIVE_POSITIONS = {"yea", "nay"}
FORBIDDEN_OUTPUT_KEYS = {
    "continuity",
    "change",
    "movement",
    "movement_label",
    "changed_position",
    "ideological_movement",
    "behavioral_movement",
    "causal_claim",
}
NON_AUTHORIZATION_METADATA = {
    "record_type": "factual_record_across_congresses_availability",
    "does_not_authorize_continuity_change_claims": True,
    "does_not_authorize_behavioral_movement_claims": True,
    "does_not_authorize_ideological_movement_claims": True,
    "does_not_authorize_causal_claims": True,
    "does_not_authorize_frontend_comparison_copy": True,
    "display_flag_meaning": (
        "The official has reviewed family-level evidence in both Congresses "
        "that may be displayed with caveats. It does not mean continuity, "
        "change, consistency, shift, stronger support, weaker support, or "
        "ideological movement."
    ),
}


class HouseComparableFamilyLegislatorError(ValueError):
    """Raised when comparable-family evidence cannot be resolved safely."""


@dataclass(frozen=True)
class LegislatorReference:
    database_id: int
    legislator_identifier: str
    bioguide_id: str
    name: str
    chamber: str
    state: str
    district: str | None
    party: str


@dataclass(frozen=True)
class CongressFamilyCounts:
    congress: int
    roll_call_ids_considered: tuple[int, ...]
    cast_substantive_yes_count: int
    cast_substantive_no_count: int
    not_voting_count: int
    present_count: int
    missing_no_record_count: int
    total_artifact_roll_calls: int
    total_cast_substantive_yes_no_rows: int


@dataclass(frozen=True)
class LegislatorFamilyEvidence:
    family_id: str
    family_name: str
    issue_domain: str
    comparability_status: str
    governing_question: str
    caveats_and_limitations: str
    family_eligibility_flag: bool
    congresses_represented_in_artifact: tuple[int, ...]
    roll_call_ids_considered_by_congress: dict[int, tuple[int, ...]]
    counts_by_congress: dict[int, CongressFamilyCounts]
    has_family_vote_in_both_congresses: bool
    has_direct_family_vote_in_both_congresses: bool
    has_conditional_family_vote_in_both_congresses: bool
    record_across_congresses_display_eligible: bool
    non_authorization_metadata: dict[str, Any]


@dataclass(frozen=True)
class LegislatorComparableFamilyEvidenceResult:
    legislator_identifier: str
    artifact_version_used: str
    eligible_comparable_families_considered: int
    legislator: LegislatorReference
    families: tuple[LegislatorFamilyEvidence, ...]
    non_authorization_metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def get_house_comparable_family_legislator_evidence(
    legislator_identifier: str,
    *,
    artifact: ComparableFamilyArtifact | None = None,
    connection: Any | None = None,
) -> LegislatorComparableFamilyEvidenceResult:
    """Return factual family-level evidence availability for one House legislator.

    The result intentionally reports only counts and display-readiness flags.
    It does not generate continuity, change, movement, consistency, ideology,
    or causal labels.
    """

    family_artifact = artifact or load_house_comparable_family_artifact()
    owns_connection = connection is None
    db_connection = connection or get_connection()
    try:
        if owns_connection:
            db_connection.read_only = True
            db_connection.autocommit = False
        with db_connection.cursor(row_factory=dict_row) as cursor:
            if owns_connection:
                cursor.execute("SET TRANSACTION READ ONLY")
            legislator = _resolve_house_legislator(cursor, legislator_identifier)
            vote_rows = _fetch_vote_rows_for_artifact(cursor, legislator.database_id, family_artifact)
    finally:
        if owns_connection:
            db_connection.close()

    vote_rows_by_roll_call = {int(row["roll_call_id"]): row for row in vote_rows}
    families = tuple(
        _build_family_evidence(family, vote_rows_by_roll_call)
        for family in family_artifact.eligible_families()
    )
    result = LegislatorComparableFamilyEvidenceResult(
        legislator_identifier=legislator_identifier,
        artifact_version_used=family_artifact.artifact_version,
        eligible_comparable_families_considered=len(families),
        legislator=legislator,
        families=families,
        non_authorization_metadata=dict(NON_AUTHORIZATION_METADATA),
    )
    _assert_no_forbidden_output_keys(result.to_dict())
    return result


def _resolve_house_legislator(cursor: Any, legislator_identifier: str) -> LegislatorReference:
    cursor.execute(
        """
        SELECT id, bioguide_id, name_display, chamber, state, district, party
        FROM legislators
        ORDER BY id
        """
    )
    matches = []
    for row in cursor.fetchall():
        external_id = _to_external_legislator_id(str(row["name_display"]))
        identifiers = {external_id, str(row["bioguide_id"]), str(row["id"])}
        if legislator_identifier in identifiers:
            matches.append(row)
    if not matches:
        raise HouseComparableFamilyLegislatorError(f"Unknown legislator identifier: {legislator_identifier}")
    if len(matches) > 1:
        raise HouseComparableFamilyLegislatorError(f"Ambiguous legislator identifier: {legislator_identifier}")
    row = matches[0]
    if str(row["chamber"]) != "house":
        raise HouseComparableFamilyLegislatorError(f"Comparable family legislator helper is House-only: {legislator_identifier}")
    return LegislatorReference(
        database_id=int(row["id"]),
        legislator_identifier=_to_external_legislator_id(str(row["name_display"])),
        bioguide_id=str(row["bioguide_id"]),
        name=str(row["name_display"]),
        chamber=str(row["chamber"]),
        state=str(row["state"]),
        district=None if row.get("district") is None else str(row["district"]),
        party=str(row["party"]),
    )


def _fetch_vote_rows_for_artifact(
    cursor: Any,
    legislator_db_id: int,
    artifact: ComparableFamilyArtifact,
) -> list[dict[str, Any]]:
    roll_call_ids = sorted(
        {
            roll_call_id
            for family in artifact.eligible_families()
            for roll_call_ids_by_congress in family.roll_call_ids_by_congress.values()
            for roll_call_id in roll_call_ids_by_congress
        }
    )
    if not roll_call_ids:
        return []
    cursor.execute(
        """
        SELECT
            rc.id AS roll_call_id,
            rc.congress,
            vc.position,
            vcf.is_eligible,
            vcf.primary_domain,
            vi.interpretation_status,
            vi.support_position,
            vi.oppose_position
        FROM roll_calls rc
        LEFT JOIN votes_cast vc
          ON vc.roll_call_id = rc.id
         AND vc.legislator_id = %s
        LEFT JOIN vote_classifications vcf
          ON vcf.roll_call_id = rc.id
        LEFT JOIN vote_interpretations vi
          ON vi.roll_call_id = rc.id
        WHERE rc.chamber = 'house'
          AND rc.congress IN (118, 119)
          AND rc.id = ANY(%s)
        """,
        (legislator_db_id, roll_call_ids),
    )
    return [dict(row) for row in cursor.fetchall()]


def _build_family_evidence(
    family: ComparableFamily,
    vote_rows_by_roll_call: dict[int, dict[str, Any]],
) -> LegislatorFamilyEvidence:
    counts_by_congress = {
        congress: _build_congress_counts(
            congress=congress,
            roll_call_ids=family.roll_call_ids_by_congress.get(congress, ()),
            vote_rows_by_roll_call=vote_rows_by_roll_call,
        )
        for congress in SUPPORTED_CONGRESSES
    }
    has_vote_both = all(
        counts.total_cast_substantive_yes_no_rows > 0
        for counts in counts_by_congress.values()
    )
    is_direct = family.comparability_status == "directly_comparable"
    is_conditional = family.comparability_status == "conditionally_comparable"
    return LegislatorFamilyEvidence(
        family_id=family.family_id,
        family_name=family.family_name,
        issue_domain=family.issue_domain,
        comparability_status=family.comparability_status,
        governing_question=family.governing_question,
        caveats_and_limitations=family.caveats_and_limitations,
        family_eligibility_flag=(
            family.eligible_for_future_limited_record_across_congresses
            and family.comparability_status in COMPARABLE_STATUSES
        ),
        congresses_represented_in_artifact=family.congresses_represented,
        roll_call_ids_considered_by_congress=dict(family.roll_call_ids_by_congress),
        counts_by_congress=counts_by_congress,
        has_family_vote_in_both_congresses=has_vote_both,
        has_direct_family_vote_in_both_congresses=has_vote_both and is_direct,
        has_conditional_family_vote_in_both_congresses=has_vote_both and is_conditional,
        record_across_congresses_display_eligible=(
            family.eligible_for_future_limited_record_across_congresses
            and has_vote_both
            and family.comparability_status in COMPARABLE_STATUSES
        ),
        non_authorization_metadata=dict(NON_AUTHORIZATION_METADATA),
    )


def _build_congress_counts(
    *,
    congress: int,
    roll_call_ids: tuple[int, ...],
    vote_rows_by_roll_call: dict[int, dict[str, Any]],
) -> CongressFamilyCounts:
    yes_count = 0
    no_count = 0
    not_voting_count = 0
    present_count = 0
    missing_count = 0
    for roll_call_id in roll_call_ids:
        row = vote_rows_by_roll_call.get(roll_call_id)
        if row is None or int(row["congress"]) != congress or row.get("position") is None:
            missing_count += 1
            continue
        position = str(row["position"])
        if position == "not_voting":
            not_voting_count += 1
            continue
        if position == "present":
            present_count += 1
            continue
        if _is_counting_substantive_yes_no(row):
            if position == "yea":
                yes_count += 1
            elif position == "nay":
                no_count += 1
        else:
            missing_count += 1
    return CongressFamilyCounts(
        congress=congress,
        roll_call_ids_considered=tuple(roll_call_ids),
        cast_substantive_yes_count=yes_count,
        cast_substantive_no_count=no_count,
        not_voting_count=not_voting_count,
        present_count=present_count,
        missing_no_record_count=missing_count,
        total_artifact_roll_calls=len(roll_call_ids),
        total_cast_substantive_yes_no_rows=yes_count + no_count,
    )


def _is_counting_substantive_yes_no(row: dict[str, Any]) -> bool:
    return (
        row.get("position") in SUBSTANTIVE_POSITIONS
        and row.get("is_eligible") is True
        and row.get("interpretation_status") == "interpreted"
        and row.get("support_position") in SUBSTANTIVE_POSITIONS
        and row.get("oppose_position") in SUBSTANTIVE_POSITIONS
    )


def _to_external_legislator_id(name_display: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name_display.lower()).strip("_")
    return f"leg_{slug}"


def _assert_no_forbidden_output_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_OUTPUT_KEYS:
                raise HouseComparableFamilyLegislatorError(f"Forbidden output field: {key}")
            _assert_no_forbidden_output_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _assert_no_forbidden_output_keys(child)
