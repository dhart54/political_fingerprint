from app.etl.current_congress_refresh import (
    ProductionState,
    _build_import_rows,
    _roll_key,
)
from app.etl.types import FixtureBundle


def test_roll_key_includes_session_to_distinguish_overlapping_roll_numbers() -> None:
    assert _roll_key(
        {
            "chamber": "house",
            "congress": 119,
            "session": 1,
            "rollcall_number": 4,
        }
    ) != _roll_key(
        {
            "chamber": "house",
            "congress": 119,
            "session": 2,
            "rollcall_number": 4,
        }
    )


def test_refresh_planner_does_not_skip_session_two_roll_when_session_one_exists() -> None:
    bundle = FixtureBundle(
        legislators=[
            {
                "id": "leg_a",
                "bioguide_id": "A000001",
                "name_display": "Example Member",
                "chamber": "house",
                "state": "NC",
                "district": "01",
                "party": "D",
                "in_office": True,
            }
        ],
        bills=[
            {
                "id": "bill_119_hr_1",
                "congress": 119,
                "bill_type": "hr",
                "bill_number": 1,
                "title": "Example Budget Bill",
                "summary": "Budget and tax measure.",
                "committee": "Budget",
                "subjects": ["budget"],
            }
        ],
        roll_calls=[
            {
                "id": "rc_house_2026_004",
                "chamber": "house",
                "congress": 119,
                "session": 2,
                "rollcall_number": 4,
                "vote_date": "2026-01-07T00:00:00+00:00",
                "question": "On Passage",
                "description": "Example Budget Bill",
                "bill_ref": "bill_119_hr_1",
                "source_url": "https://clerk.house.gov/evs/2026/roll004.xml",
            }
        ],
        votes_cast=[
            {
                "roll_call_id": "rc_house_2026_004",
                "legislator_id": "leg_a",
                "position": "yea",
            }
        ],
        vote_subject_tags={"bill_119_hr_1": ["budget"]},
        zip_district_map=[],
    )
    state = ProductionState(
        existing_roll_keys={("house", 119, 1, 4)},
        existing_bill_keys={(119, "hr", 1)},
        legislator_ids_by_bioguide={"A000001": 1},
        existing_classification_roll_ids=set(),
        existing_interpretation_roll_ids=set(),
    )

    rows = _build_import_rows(bundle=bundle, production_state=state)

    assert rows["errors"] == []
    assert rows["roll_keys"] == {("house", 119, 2, 4)}
    assert len(rows["roll_calls"]) == 1
    assert len(rows["votes_cast"]) == 1
