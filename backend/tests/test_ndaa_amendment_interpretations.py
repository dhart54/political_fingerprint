from pathlib import Path

from app.etl.ndaa_amendment_interpretations import (
    HouseRollContext,
    build_ndaa_amendment_interpretation_candidate,
    candidate_to_manual_interpretation,
    load_house_roll_context,
)


def _source_packet(*, purpose: str | None = "Amendment repeals specified authorizations for use of military force.") -> dict:
    return {
        "roll_call_id": 224,
        "rollcall_number": 244,
        "amendment": {
            "amendment_id": "119:hamdt:99",
            "amendment_number": "34",
            "amendment_label": "Part A Amendment No. 34",
            "sponsor_text": "Meeks of New York",
            "purpose": purpose,
            "description": "An amendment numbered 34 printed in Part A of House Report 119-255.",
            "source_url": "https://api.congress.gov/v3/amendment/119/hamdt/99?format=json",
            "matched_from_roll_description": purpose is not None,
        },
    }


def _roll_context(*, question: str = "On Agreeing to the Amendment", member_vote: str | None = "yea") -> HouseRollContext:
    return HouseRollContext(
        rollcall_number=244,
        question=question,
        amendment_author="Meeks of New York Part A Amendment No. 34",
        vote_result="Agreed to",
        member_vote=member_vote,
        source_url="https://clerk.house.gov/evs/2025/roll244.xml",
    )


def test_builds_candidate_interpretation_from_matched_amendment_packet() -> None:
    candidate = build_ndaa_amendment_interpretation_candidate(_source_packet(), _roll_context())

    assert candidate["interpretation_status"] == "interpreted"
    assert candidate["interpretation_status_recommendation"] == "reviewed_interpretation"
    assert candidate["support_position"] == "yea"
    assert candidate["oppose_position"] == "nay"
    assert "H.R. 3838" in candidate["plain_english_summary"]
    assert "not final passage of the full NDAA" in candidate["why_it_mattered"]
    assert "not final passage of H.R. 3838" in candidate["what_not_to_infer"]
    assert candidate["source_basis"]
    assert "corrupt" not in candidate["what_not_to_infer"].lower()


def test_keeps_candidate_limited_when_vote_action_is_not_clear() -> None:
    candidate = build_ndaa_amendment_interpretation_candidate(
        _source_packet(),
        _roll_context(question="On Ordering the Previous Question"),
    )

    assert candidate["interpretation_status"] == "insufficient_evidence"
    assert candidate["interpretation_status_recommendation"] == "keep_limited"
    assert candidate["support_position"] is None
    assert "does not clearly show an amendment-adoption vote" in candidate["uncertainty_note"]


def test_keeps_candidate_limited_when_amendment_text_is_missing() -> None:
    candidate = build_ndaa_amendment_interpretation_candidate(_source_packet(purpose=None), _roll_context())

    assert candidate["interpretation_status"] == "insufficient_evidence"
    assert candidate["interpretation_status_recommendation"] == "keep_limited"
    assert "matched amendment purpose or description is missing or uncertain" in candidate["uncertainty_note"]


def test_manual_interpretation_record_preserves_source_basis_and_guardrails() -> None:
    candidate = build_ndaa_amendment_interpretation_candidate(_source_packet(), _roll_context(member_vote="nay"))

    record = candidate_to_manual_interpretation(candidate)

    assert record["interpretation_status"] == "interpreted"
    assert record["source_basis"]
    assert record["member_vote_context"] == "Foushee voted Nay, meaning she opposed agreeing to this amendment."
    assert "final passage" not in record["plain_english_summary"].lower()


def test_load_house_roll_context_reads_member_vote_from_house_clerk_xml(tmp_path: Path) -> None:
    roll_path = tmp_path / "roll244.xml"
    roll_path.write_text(
        """
        <rollcall-vote>
          <vote-metadata>
            <rollcall-num>244</rollcall-num>
            <vote-question>On Agreeing to the Amendment</vote-question>
            <amendment-author>Meeks of New York Part A Amendment No. 34</amendment-author>
            <vote-result>Agreed to</vote-result>
          </vote-metadata>
          <vote-data>
            <recorded-vote>
              <legislator name-id="F000477">Foushee</legislator>
              <vote>Aye</vote>
            </recorded-vote>
          </vote-data>
        </rollcall-vote>
        """,
        encoding="utf-8",
    )

    context = load_house_roll_context(roll_path)

    assert context.rollcall_number == 244
    assert context.member_vote == "yea"
