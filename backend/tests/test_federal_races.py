from datetime import date

from app.etl.federal_races import (
    LegislatorRecordMatch,
    RaceCandidate,
    _name_match_key,
    _with_legislator_match,
    build_federal_races_from_fec_rows,
)


def test_build_federal_races_from_fec_rows_groups_house_candidates() -> None:
    races = build_federal_races_from_fec_rows(
        [
            {
                "Cand_Name": "BEASLEY, AARON",
                "Cand_Id": "H6NC04001",
                "Cand_Office": "H",
                "Cand_Office_St": "NC",
                "Cand_Office_Dist": "4",
                "Cand_Party_Affiliation": "DEM",
                "Cand_Incumbent_Challenger_Open_Seat": "C",
            },
            {
                "Cand_Name": "DURHAM, CASEY",
                "Cand_Id": "H6NC04002",
                "Cand_Office": "H",
                "Cand_Office_St": "NC",
                "Cand_Office_Dist": "04",
                "Cand_Party_Affiliation": "REP",
                "Cand_Incumbent_Challenger_Open_Seat": "I",
            },
        ],
        cycle=2026,
        as_of=date(2026, 5, 17),
    )

    assert len(races) == 1
    assert races[0].race_key == "fec_2026_house_nc_04"
    assert races[0].election_date == date(2026, 11, 3)
    assert races[0].status == "upcoming"
    assert races[0].office_name == "U.S. House"
    assert races[0].district == "04"
    assert [candidate.party for candidate in races[0].candidates] == ["D", "R"]
    assert races[0].candidates[1].incumbent is True
    assert races[0].candidates[1].evidence_tier == "insufficient_evidence"


def test_build_federal_races_from_fec_rows_groups_senate_statewide() -> None:
    races = build_federal_races_from_fec_rows(
        [
            {
                "Cand_Name": "TILLIS, THOM",
                "Cand_Id": "S6NC00001",
                "Cand_Office": "S",
                "Cand_Office_St": "NC",
                "Cand_Office_Dist": "",
                "Cand_Party_Affiliation": "REP",
                "Cand_Incumbent_Challenger_Open_Seat": "I",
            },
            {
                "Cand_Name": "PRESIDENTIAL, PAT",
                "Cand_Id": "P60000001",
                "Cand_Office": "P",
                "Cand_Office_St": "US",
                "Cand_Office_Dist": "",
                "Cand_Party_Affiliation": "IND",
                "Cand_Incumbent_Challenger_Open_Seat": "C",
            },
        ],
        cycle=2026,
        as_of=date(2026, 5, 17),
    )

    assert len(races) == 1
    assert races[0].race_key == "fec_2026_senate_nc_statewide"
    assert races[0].district is None
    assert races[0].candidates[0].candidate_name == "Thom Tillis"
    assert races[0].candidates[0].source_url.endswith("/S6NC00001/")


def test_build_federal_races_from_fec_rows_marks_past_races() -> None:
    races = build_federal_races_from_fec_rows(
        [
            {
                "Cand_Name": "TILLIS, THOM",
                "Cand_Id": "S6NC00001",
                "Cand_Office": "S",
                "Cand_Office_St": "NC",
                "Cand_Office_Dist": "",
                "Cand_Party_Affiliation": "REP",
                "Cand_Incumbent_Challenger_Open_Seat": "I",
            },
        ],
        cycle=2026,
        election_date=date(2026, 11, 3),
        as_of=date(2026, 11, 4),
    )

    assert races[0].status == "past"


def test_name_match_key_allows_middle_initials_without_overmatching() -> None:
    assert _name_match_key("Valerie P. Foushee") == _name_match_key("FOUSHEE, VALERIE")
    assert _name_match_key("Thom Tillis") != _name_match_key("Thomas Massie")


def test_incumbent_candidate_can_match_current_legislator_record() -> None:
    race = build_federal_races_from_fec_rows(
        [
            {
                "Cand_Name": "FOUSHEE, VALERIE",
                "Cand_Id": "H2NC06114",
                "Cand_Office": "H",
                "Cand_Office_St": "NC",
                "Cand_Office_Dist": "04",
                "Cand_Party_Affiliation": "DEM",
                "Cand_Incumbent_Challenger_Open_Seat": "I",
            },
        ],
        cycle=2026,
        as_of=date(2026, 5, 17),
    )[0]
    candidate = race.candidates[0]

    matched = _with_legislator_match(
        candidate,
        race=race,
        legislator_matches={
            ("house", "NC", "04", "D", "valerie foushee"): LegislatorRecordMatch(
                legislator_id=101,
                in_office=True,
            )
        },
    )

    assert matched.legislator_id == 101
    assert matched.evidence_tier == "recorded_governing_behavior"
    assert "Recorded voting behavior is available" in matched.evidence_note


def test_non_incumbent_candidate_does_not_match_legislator_record() -> None:
    candidate = RaceCandidate(
        candidate_name="Valerie Foushee",
        party="D",
        incumbent=False,
        candidate_status="declared_candidate",
        evidence_tier="insufficient_evidence",
        evidence_note="FEC candidate-summary record loaded.",
        source_url="https://www.fec.gov/data/candidate/H2NC06114/",
        source_type="fec_candidate_summary",
        external_candidate_id="H2NC06114",
    )
    race = build_federal_races_from_fec_rows(
        [
            {
                "Cand_Name": "FOUSHEE, VALERIE",
                "Cand_Id": "H2NC06114",
                "Cand_Office": "H",
                "Cand_Office_St": "NC",
                "Cand_Office_Dist": "04",
                "Cand_Party_Affiliation": "DEM",
                "Cand_Incumbent_Challenger_Open_Seat": "I",
            },
        ],
        cycle=2026,
        as_of=date(2026, 5, 17),
    )[0]

    matched = _with_legislator_match(
        candidate,
        race=race,
        legislator_matches={
            ("house", "NC", "04", "D", "valerie foushee"): LegislatorRecordMatch(
                legislator_id=101,
                in_office=True,
            )
        },
    )

    assert matched.legislator_id is None
    assert matched.evidence_tier == "insufficient_evidence"


def test_prior_officeholder_candidate_can_match_past_voting_record() -> None:
    candidate = RaceCandidate(
        candidate_name="Casey Durham",
        party="R",
        incumbent=False,
        candidate_status="declared_candidate",
        evidence_tier="insufficient_evidence",
        evidence_note="FEC candidate-summary record loaded.",
        source_url="https://www.fec.gov/data/candidate/H6NC04002/",
        source_type="fec_candidate_summary",
        external_candidate_id="H6NC04002",
    )
    race = build_federal_races_from_fec_rows(
        [
            {
                "Cand_Name": "DURHAM, CASEY",
                "Cand_Id": "H6NC04002",
                "Cand_Office": "H",
                "Cand_Office_St": "NC",
                "Cand_Office_Dist": "04",
                "Cand_Party_Affiliation": "REP",
                "Cand_Incumbent_Challenger_Open_Seat": "C",
            },
        ],
        cycle=2026,
        as_of=date(2026, 5, 17),
    )[0]

    matched = _with_legislator_match(
        candidate,
        race=race,
        legislator_matches={
            ("house", "NC", "04", "R", "casey durham"): LegislatorRecordMatch(
                legislator_id=202,
                in_office=False,
            )
        },
    )

    assert matched.legislator_id == 202
    assert matched.evidence_tier == "recorded_governing_behavior"
    assert "prior officeholder" in matched.evidence_note
