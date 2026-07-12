from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable


READY = "ready_single_current_voting_member"
NO_MATCH = "no_current_member_match"
DUPLICATE = "duplicate_current_member_matches"
CURRENTNESS_UNKNOWN = "member_currentness_unknown"
STALE = "member_metadata_stale"
VACANCY = "vacancy_or_unfilled_seat"
CHAMBER_MISMATCH = "chamber_mismatch"
STATE_MISMATCH = "state_mismatch"
DISTRICT_MISMATCH = "district_mismatch"
MISSING_IDENTIFIER = "missing_required_member_identifier"
DELEGATE_REVIEW = "nonvoting_delegate_review_required"
RESIDENT_COMMISSIONER_REVIEW = "resident_commissioner_review_required"
UNSUPPORTED_TERRITORY = "unsupported_territory"
SCHEMA_INSUFFICIENT = "schema_insufficient_for_currentness_gate"

TERRITORIES = {"AS", "GU", "MP", "PR", "VI"}
VOTING_AT_LARGE_STATES = {"AK", "DE", "ND", "SD", "VT", "WY"}
REQUIRED_CURRENTNESS_FIELDS = {
    "in_office",
    "congress",
    "term_start",
    "term_end",
    "seat_status",
    "member_type",
    "metadata_source_url",
    "metadata_retrieved_at",
    "metadata_currentness",
}


@dataclass(frozen=True)
class PairResult:
    state: str
    district: str
    status: str
    blockers: tuple[str, ...]
    matching_member_count: int
    current_matching_member_count: int
    member_ids: tuple[str, ...]
    at_large_type: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "district": self.district,
            "status": self.status,
            "blockers": list(self.blockers),
            "matching_member_count": self.matching_member_count,
            "current_matching_member_count": self.current_matching_member_count,
            "member_ids": list(self.member_ids),
            "at_large_type": self.at_large_type,
            "production_auto_select_eligible": False,
        }


def normalize_district(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    if text.isdigit() and len(text) <= 2:
        return text.zfill(2)
    return text


def evaluate_pair(
    *,
    state: str,
    district: str,
    members: Iterable[dict[str, Any]],
    schema_fields: set[str],
) -> PairResult:
    state = state.strip().upper()
    district = normalize_district(district)
    rows = [dict(row) for row in members]
    exact = [
        row for row in rows
        if str(row.get("state", "")).upper() == state and normalize_district(row.get("district")) == district
    ]
    house_exact = [row for row in exact if str(row.get("chamber", "")).lower() == "house"]
    current_exact = [row for row in house_exact if row.get("in_office") is True]
    ids = tuple(sorted(str(row.get("bioguide_id") or "") for row in current_exact))

    if state in TERRITORIES:
        status = RESIDENT_COMMISSIONER_REVIEW if state == "PR" else UNSUPPORTED_TERRITORY
        return _result(state, district, status, status, house_exact, current_exact, ids, _at_large_type(state, district))
    if state == "DC":
        return _result(state, district, DELEGATE_REVIEW, DELEGATE_REVIEW, house_exact, current_exact, ids, "dc_delegate")
    if exact and not house_exact:
        return _result(state, district, CHAMBER_MISMATCH, CHAMBER_MISMATCH, house_exact, current_exact, ids)
    if not house_exact:
        same_state_house = [
            row for row in rows
            if str(row.get("chamber", "")).lower() == "house"
            and str(row.get("state", "")).upper() == state
            and row.get("in_office") is True
        ]
        if same_state_house:
            return _result(state, district, DISTRICT_MISMATCH, DISTRICT_MISMATCH, house_exact, current_exact, ids)
        house_same_district = [
            row for row in rows
            if str(row.get("chamber", "")).lower() == "house"
            and normalize_district(row.get("district")) == district
            and row.get("in_office") is True
        ]
        if len(rows) == 1 and house_same_district:
            return _result(state, district, STATE_MISMATCH, STATE_MISMATCH, house_exact, current_exact, ids)
        return _result(state, district, NO_MATCH, NO_MATCH, house_exact, current_exact, ids)
    if not current_exact:
        return _result(state, district, NO_MATCH, NO_MATCH, house_exact, current_exact, ids)
    if len(current_exact) > 1:
        return _result(state, district, DUPLICATE, DUPLICATE, house_exact, current_exact, ids)

    member = current_exact[0]
    if not member.get("bioguide_id"):
        return _result(state, district, MISSING_IDENTIFIER, MISSING_IDENTIFIER, house_exact, current_exact, ids)
    if member.get("seat_status") == "vacant":
        return _result(state, district, VACANCY, VACANCY, house_exact, current_exact, ids)
    if not REQUIRED_CURRENTNESS_FIELDS.issubset(schema_fields):
        return _result(state, district, SCHEMA_INSUFFICIENT, SCHEMA_INSUFFICIENT, house_exact, current_exact, ids, _at_large_type(state, district))
    if any(member.get(field) in (None, "") for field in REQUIRED_CURRENTNESS_FIELDS):
        return _result(state, district, CURRENTNESS_UNKNOWN, CURRENTNESS_UNKNOWN, house_exact, current_exact, ids)
    if member.get("metadata_currentness") in (None, "", "unknown"):
        return _result(state, district, CURRENTNESS_UNKNOWN, CURRENTNESS_UNKNOWN, house_exact, current_exact, ids)
    if member.get("metadata_currentness") == "stale":
        return _result(state, district, STALE, STALE, house_exact, current_exact, ids)
    if member.get("member_type") != "voting_representative":
        return _result(state, district, DELEGATE_REVIEW, DELEGATE_REVIEW, house_exact, current_exact, ids, _at_large_type(state, district))
    return _result(state, district, READY, "", house_exact, current_exact, ids, _at_large_type(state, district))


def status_distribution(results: Iterable[PairResult]) -> dict[str, int]:
    return dict(sorted(Counter(result.status for result in results).items()))


def _result(
    state: str,
    district: str,
    status: str,
    blocker: str,
    matching: list[dict[str, Any]],
    current: list[dict[str, Any]],
    ids: tuple[str, ...],
    at_large_type: str | None = None,
) -> PairResult:
    return PairResult(
        state=state,
        district=district,
        status=status,
        blockers=(blocker,) if blocker else (),
        matching_member_count=len(matching),
        current_matching_member_count=len(current),
        member_ids=ids,
        at_large_type=at_large_type,
    )


def _at_large_type(state: str, district: str) -> str | None:
    if district != "00":
        return None
    if state in VOTING_AT_LARGE_STATES:
        return "voting_at_large_state"
    if state == "DC":
        return "dc_delegate"
    if state == "PR":
        return "resident_commissioner"
    if state in TERRITORIES:
        return "territorial_delegate"
    return "at_large_type_unknown"
