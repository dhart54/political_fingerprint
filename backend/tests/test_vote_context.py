from app.etl.vote_context import build_vote_contexts, infer_vote_type


def test_build_vote_contexts_derives_party_and_result_baselines() -> None:
    legislators = [
        {
            "id": "leg_d_1",
            "party": "D",
        },
        {
            "id": "leg_d_2",
            "party": "D",
        },
        {
            "id": "leg_r_1",
            "party": "R",
        },
    ]
    roll_calls = [
        {
            "id": "rc_1",
            "session": 1,
            "question": "On Passage",
            "description": "A bill to fund testing grants",
            "source_url": "https://example.com/roll-call/1",
        }
    ]
    votes_cast = [
        {"roll_call_id": "rc_1", "legislator_id": "leg_d_1", "position": "yea"},
        {"roll_call_id": "rc_1", "legislator_id": "leg_d_2", "position": "nay"},
        {"roll_call_id": "rc_1", "legislator_id": "leg_r_1", "position": "yea"},
    ]

    contexts = build_vote_contexts(
        legislators=legislators,
        roll_calls=roll_calls,
        votes_cast=votes_cast,
    )

    first_democrat = next(row for row in contexts if row["legislator_id"] == "leg_d_1")
    second_democrat = next(row for row in contexts if row["legislator_id"] == "leg_d_2")

    assert len(contexts) == 3
    assert first_democrat["chamber_session"] == 1
    assert first_democrat["vote_type"] == "final_passage"
    assert first_democrat["final_result"] == "passed"
    assert first_democrat["vote_margin"] == 1
    assert first_democrat["winning_position"] == "yea"
    assert first_democrat["party_vote_totals"] == {
        "D": {"yea": 1, "nay": 1, "present": 0, "not_voting": 0},
        "R": {"yea": 1, "nay": 0, "present": 0, "not_voting": 0},
    }
    assert first_democrat["member_party_majority_position"] is None
    assert first_democrat["member_voted_with_party_majority"] is None
    assert first_democrat["member_voted_with_winning_side"] is True
    assert first_democrat["bipartisan_majority"] is True
    assert first_democrat["context_source_list"] == [
        {"source_type": "official_roll_call", "url": "https://example.com/roll-call/1"}
    ]
    assert second_democrat["member_voted_with_winning_side"] is False


def test_infer_vote_type_uses_question_and_description_text() -> None:
    assert infer_vote_type(question="On Agreeing to the Amendment", description="") == "amendment"
    assert infer_vote_type(question="On the Nomination", description="confirmation vote") == "nomination"
    assert infer_vote_type(question="On Motion to Suspend the Rules", description="") == "motion"
    assert infer_vote_type(question="On Passage", description="making appropriations") == "appropriations"
    assert infer_vote_type(question="On Agreeing to the Resolution", description="chapter 8 of title 5") == "cra_disapproval"


def test_infer_vote_type_does_not_treat_confirmation_act_title_as_nomination() -> None:
    assert (
        infer_vote_type(
            question="On Motion to Suspend the Rules and Pass",
            description="Puyallup Tribe of Indians Land Into Trust Confirmation Act",
        )
        == "motion"
    )
