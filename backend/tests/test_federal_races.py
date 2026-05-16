from datetime import date

from app.etl.federal_races import build_federal_races_from_fec_rows


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
    )

    assert len(races) == 1
    assert races[0].race_key == "fec_2026_house_nc_04"
    assert races[0].election_date == date(2026, 11, 3)
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
    )

    assert len(races) == 1
    assert races[0].race_key == "fec_2026_senate_nc_statewide"
    assert races[0].district is None
    assert races[0].candidates[0].candidate_name == "Thom Tillis"
    assert races[0].candidates[0].source_url.endswith("/S6NC00001/")
