from app.etl.senate_118_amendment_enrichment import (
    _domain_from_text,
    _extract_amendment_number,
    _is_procedural_amendment_action,
    _purpose_is_generic,
)


def test_extracts_senate_amendment_number_from_loaded_roll_title() -> None:
    row = {
        "description": "Lee Motion to Concur in the House Amendment to the Senate Amendment to H.R. 4366 with an Amendment No. 1623",
        "bill_title": "Schumer Motion to Concur in the House Amendment to the Senate Amendment to H.R. 4366",
    }
    xml = {"amendment_number": None, "vote_title": None, "vote_question_text": None}

    assert _extract_amendment_number(row=row, xml=xml) == "S.Amdt. 1623"


def test_prefers_xml_amendment_number_when_available() -> None:
    row = {"description": "Cruz Amdt. No. 9", "bill_title": "S. 316"}
    xml = {"amendment_number": "S.Amdt. 9", "vote_title": "Cruz Amdt. No. 9", "vote_question_text": "On the Amendment S. 316"}

    assert _extract_amendment_number(row=row, xml=xml) == "S.Amdt. 9"


def test_generic_purpose_markers_remain_deferred() -> None:
    assert _purpose_is_generic("No Statement of Purpose on File.")
    assert _purpose_is_generic("To improve the bill.")
    assert not _purpose_is_generic("To establish the Office of the Special Inspector General for Ukraine Assistance.")


def test_domain_matching_uses_direct_amendment_purpose() -> None:
    domain, score = _domain_from_text("To establish the Office of the Special Inspector General for Ukraine Assistance.")

    assert domain == "NATIONAL_SECURITY_FOREIGN"
    assert "ukraine" in score["NATIONAL_SECURITY_FOREIGN"]["matched_terms"]


def test_motion_to_table_is_procedural_context() -> None:
    assert _is_procedural_amendment_action(
        "On the Motion to Table",
        "Motion to Table the Motion to Concur in the House Amendment to the Senate Amendment to H.R. 2882 with Cruz Amdt No. 1804",
    )
    assert not _is_procedural_amendment_action("On the Amendment", "Cruz Amdt. No. 9")
