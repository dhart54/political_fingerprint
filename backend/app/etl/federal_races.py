import argparse
import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from app.db import get_connection


FEC_CANDIDATE_SUMMARY_URL = "https://www.fec.gov/data/browse-data/?tab=bulk-data"
FEC_PROFILE_URL_PREFIX = "https://www.fec.gov/data/candidate"
FEDERAL_GENERAL_ELECTION_DATES = {
    2026: date(2026, 11, 3),
    2028: date(2028, 11, 7),
}


@dataclass(frozen=True)
class RaceCandidate:
    candidate_name: str
    party: str | None
    incumbent: bool
    candidate_status: str
    evidence_tier: str
    evidence_note: str
    source_url: str
    source_type: str
    external_candidate_id: str


@dataclass(frozen=True)
class FederalRace:
    race_key: str
    election_date: date
    election_label: str
    office_name: str
    chamber: str
    state: str
    district: str | None
    source_url: str
    source_type: str
    candidates: tuple[RaceCandidate, ...]


@dataclass(frozen=True)
class FederalRacePersistResult:
    races_seen: int
    races_upserted: int
    candidates_seen: int
    candidates_upserted: int


def load_fec_candidate_summary(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def build_federal_races_from_fec_rows(
    rows: Iterable[dict[str, str]],
    *,
    cycle: int,
    election_date: date | None = None,
) -> list[FederalRace]:
    resolved_election_date = election_date or FEDERAL_GENERAL_ELECTION_DATES.get(cycle)
    if resolved_election_date is None:
        raise ValueError(f"No federal general election date configured for {cycle}")

    race_candidates: dict[str, list[RaceCandidate]] = {}
    race_fields: dict[str, dict[str, str | None]] = {}
    for row in rows:
        office = _normalize_office(_get(row, "Cand_Office", "candidate_office"))
        if office not in {"house", "senate"}:
            continue

        state = _get(row, "Cand_Office_St", "candidate_office_state").upper()
        if not state:
            continue

        district = None
        office_name = "U.S. Senate"
        if office == "house":
            district = _normalize_house_district(
                _get(row, "Cand_Office_Dist", "candidate_office_district"),
            )
            if district is None:
                continue
            office_name = "U.S. House"

        race_key = _race_key(cycle=cycle, chamber=office, state=state, district=district)
        race_fields[race_key] = {
            "office_name": office_name,
            "chamber": office,
            "state": state,
            "district": district,
        }
        race_candidates.setdefault(race_key, []).append(
            RaceCandidate(
                candidate_name=_format_candidate_name(_get(row, "Cand_Name", "candidate_name")),
                party=_normalize_party(_get(row, "Cand_Party_Affiliation", "candidate_party_affiliation")),
                incumbent=_is_incumbent(_get(row, "Cand_Incumbent_Challenger_Open_Seat", "candidate_ico")),
                candidate_status="declared_candidate",
                evidence_tier="insufficient_evidence",
                evidence_note=(
                    "FEC candidate-summary record loaded. No voting record or sourced issue-position "
                    "evidence is linked to this candidate yet."
                ),
                source_url=_candidate_source_url(_get(row, "Cand_Id", "candidate_id")),
                source_type="fec_candidate_summary",
                external_candidate_id=_get(row, "Cand_Id", "candidate_id"),
            )
        )

    return [
        FederalRace(
            race_key=race_key,
            election_date=resolved_election_date,
            election_label=f"{cycle} general election",
            office_name=str(fields["office_name"]),
            chamber=str(fields["chamber"]),
            state=str(fields["state"]),
            district=None if fields["district"] is None else str(fields["district"]),
            source_url=FEC_CANDIDATE_SUMMARY_URL,
            source_type="fec_candidate_summary",
            candidates=tuple(sorted(candidates, key=lambda item: (item.candidate_name, item.external_candidate_id))),
        )
        for race_key, candidates in sorted(race_candidates.items())
        for fields in [race_fields[race_key]]
    ]


def persist_federal_races(races: list[FederalRace]) -> FederalRacePersistResult:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        candidates_seen = 0
        for race in races:
            race_id = _upsert_race(cursor, race)
            for candidate in race.candidates:
                candidates_seen += 1
                _upsert_candidate(cursor, race_id, candidate)
        connection.commit()
        return FederalRacePersistResult(
            races_seen=len(races),
            races_upserted=len(races),
            candidates_seen=candidates_seen,
            candidates_upserted=candidates_seen,
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _upsert_race(cursor: Any, race: FederalRace) -> int:
    cursor.execute(
        """
        INSERT INTO upcoming_races (
            race_key,
            election_date,
            election_label,
            office_level,
            office_name,
            chamber,
            state,
            district,
            status,
            source_url,
            source_type,
            source_retrieved_at
        )
        VALUES (%s, %s, %s, 'federal', %s, %s, %s, %s, 'upcoming', %s, %s, NOW())
        ON CONFLICT (race_key) DO UPDATE SET
            election_date = EXCLUDED.election_date,
            election_label = EXCLUDED.election_label,
            office_name = EXCLUDED.office_name,
            chamber = EXCLUDED.chamber,
            state = EXCLUDED.state,
            district = EXCLUDED.district,
            status = EXCLUDED.status,
            source_url = EXCLUDED.source_url,
            source_type = EXCLUDED.source_type,
            source_retrieved_at = EXCLUDED.source_retrieved_at
        RETURNING id
        """,
        (
            race.race_key,
            race.election_date,
            race.election_label,
            race.office_name,
            race.chamber,
            race.state,
            race.district,
            race.source_url,
            race.source_type,
        ),
    )
    return int(cursor.fetchone()[0])


def _upsert_candidate(cursor: Any, race_id: int, candidate: RaceCandidate) -> None:
    cursor.execute(
        """
        INSERT INTO race_candidates (
            race_id,
            candidate_name,
            party,
            incumbent,
            candidate_status,
            evidence_tier,
            evidence_note,
            source_url,
            source_type,
            source_retrieved_at,
            external_candidate_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        ON CONFLICT (race_id, source_type, external_candidate_id)
            WHERE external_candidate_id IS NOT NULL
        DO UPDATE SET
            candidate_name = EXCLUDED.candidate_name,
            party = EXCLUDED.party,
            incumbent = EXCLUDED.incumbent,
            candidate_status = EXCLUDED.candidate_status,
            evidence_tier = EXCLUDED.evidence_tier,
            evidence_note = EXCLUDED.evidence_note,
            source_url = EXCLUDED.source_url,
            source_retrieved_at = EXCLUDED.source_retrieved_at
        """,
        (
            race_id,
            candidate.candidate_name,
            candidate.party,
            candidate.incumbent,
            candidate.candidate_status,
            candidate.evidence_tier,
            candidate.evidence_note,
            candidate.source_url,
            candidate.source_type,
            candidate.external_candidate_id,
        ),
    )


def _race_key(*, cycle: int, chamber: str, state: str, district: str | None) -> str:
    suffix = "statewide" if district is None else district
    return f"fec_{cycle}_{chamber}_{state}_{suffix}".lower()


def _get(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and value.strip():
            return value.strip()
    return ""


def _normalize_office(value: str) -> str:
    normalized = value.strip().upper()
    if normalized == "H":
        return "house"
    if normalized == "S":
        return "senate"
    if normalized in {"HOUSE", "SENATE"}:
        return normalized.lower()
    return ""


def _normalize_house_district(value: str) -> str | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        return f"{int(cleaned):02d}"
    except ValueError:
        return cleaned.zfill(2)


def _normalize_party(value: str) -> str | None:
    cleaned = value.strip().upper()
    if not cleaned:
        return None
    return {
        "DEM": "D",
        "DFL": "D",
        "REP": "R",
        "GOP": "R",
        "IND": "I",
        "LIB": "L",
        "GRE": "G",
    }.get(cleaned, cleaned)


def _is_incumbent(value: str) -> bool:
    return value.strip().upper().startswith("I")


def _format_candidate_name(value: str) -> str:
    cleaned = " ".join(value.replace(".", ". ").split())
    if "," not in cleaned:
        return cleaned.title()
    last, rest = [part.strip() for part in cleaned.split(",", 1)]
    return f"{rest.title()} {last.title()}".strip()


def _candidate_source_url(candidate_id: str) -> str:
    return f"{FEC_PROFILE_URL_PREFIX}/{candidate_id}/" if candidate_id else FEC_CANDIDATE_SUMMARY_URL


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fec-candidate-summary", type=Path, required=True)
    parser.add_argument("--cycle", type=int, default=2026)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    races = build_federal_races_from_fec_rows(
        load_fec_candidate_summary(args.fec_candidate_summary),
        cycle=args.cycle,
    )
    if args.dry_run:
        candidate_count = sum(len(race.candidates) for race in races)
        print(f"Parsed {len(races)} federal races and {candidate_count} candidates.")
        return

    print(persist_federal_races(races))


if __name__ == "__main__":
    main()
