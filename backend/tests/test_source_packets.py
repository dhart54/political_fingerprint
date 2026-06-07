from app.etl.source_packets import (
    SourcePacketTarget,
    build_congressgov_source_packet,
    classify_source_packet,
    find_matching_amendment,
    parse_house_amendment_hint,
)


def test_parse_house_amendment_hint_extracts_part_a_number_and_sponsor() -> None:
    hint = parse_house_amendment_hint("Mace of South Carolina Part A Amendment No. 14")

    assert hint == {
        "amendment_number": "14",
        "amendment_label": "Part A Amendment No. 14",
        "sponsor_text": "Mace of South Carolina",
    }


def test_build_source_packet_marks_matching_amendment_as_review_candidate() -> None:
    target = SourcePacketTarget(
        roll_call_id=226,
        chamber="house",
        congress=119,
        rollcall_number=246,
        question="On Agreeing to the Amendment",
        description="Mace of South Carolina Part A Amendment No. 14",
        source_url="https://clerk.house.gov/evs/2025/roll246.xml",
        bill_congress=119,
        bill_type="hr",
        bill_number=3838,
        bill_title="Defense Authorization Act",
        primary_domain="NATIONAL_SECURITY_FOREIGN",
        interpretation_status="insufficient_evidence",
        issue_facet="Defense authorization amendment",
        vote_type="amendment",
    )
    cache = {
        (119, "hr", 3838): {
            "summary": "The bill sets FY2026 defense policies and authorities.",
            "legislation_url": "https://www.congress.gov/bill/119th-congress/house-bill/3838",
            "latest_action": {"action_date": "2025-09-30", "text": "Received in the Senate."},
            "actions": [{"actionDate": "2025-09-10", "text": "House considered amendments."}],
            "text_versions": [{"type": "Engrossed in House", "formats": [{"type": "Formatted Text", "url": "https://example.com/text"}]}],
            "amendments": [
                {
                    "congress": 119,
                    "type": "hamdt",
                    "number": "14",
                    "purpose": "Requires a report on a specified defense acquisition program.",
                    "sponsor": {"fullName": "Mace, Nancy"},
                    "url": "https://api.congress.gov/v3/amendment/119/hamdt/14?format=json",
                }
            ],
            "committees": [{"name": "House Armed Services Committee"}],
            "committee_reports": [{"citation": "H. Rept. 119-231", "url": "https://example.com/report"}],
            "cbo_cost_estimates": [{"title": "CBO estimate", "url": "https://example.com/cbo"}],
            "source_subresources": {
                "amendments": {"count": 26, "url": "https://api.congress.gov/v3/bill/119/hr/3838/amendments?format=json"},
                "actions": {"count": 82, "url": "https://api.congress.gov/v3/bill/119/hr/3838/actions?format=json"},
            },
        }
    }

    packet = build_congressgov_source_packet(target, congress_cache=cache)

    assert packet["review_classification"] == "likely_upgrade_candidate"
    assert packet["interpretation_status"] == "insufficient_evidence"
    assert packet["source_availability"]["matched_amendment_purpose_or_description"] is True
    assert packet["amendment"]["purpose"] == "Requires a report on a specified defense acquisition program."
    assert packet["amendment"]["match_confidence"] == "medium"
    assert "interpretation_status is not changed" in " ".join(packet["review_notes"])


def test_build_source_packet_matches_congressgov_companion_by_printed_house_number() -> None:
    target = SourcePacketTarget(
        roll_call_id=224,
        chamber="house",
        congress=119,
        rollcall_number=244,
        question="On Agreeing to the Amendment",
        description="Meeks of New York Part A Amendment No. 34",
        source_url="https://clerk.house.gov/evs/2025/roll244.xml",
        bill_congress=119,
        bill_type="hr",
        bill_number=3838,
        bill_title="Defense Authorization Act",
        primary_domain="NATIONAL_SECURITY_FOREIGN",
        interpretation_status="insufficient_evidence",
        issue_facet="Defense authorization amendment",
        vote_type="amendment",
    )
    cache = {
        (119, "hr", 3838): {
            "summary": "The bill sets FY2026 defense policies and authorities.",
            "amendments": [
                {
                    "congress": 119,
                    "type": "HAMDT",
                    "number": "99",
                    "description": "An amendment numbered 34 printed in Part A of House Report 119-255 to repeal specified authorizations for use of military force.",
                    "purpose": "Amendment repeals the 2002 and 1991 Authorization for Use of Military Force.",
                    "latestAction": {
                        "actionDate": "2025-09-10",
                        "actionTime": "16:35:30",
                        "text": "On agreeing to the Meeks amendment (A023) Agreed to by recorded vote: 261 - 167 (Roll no. 244).",
                    },
                    "url": "https://api.congress.gov/v3/amendment/119/hamdt/99?format=json",
                }
            ],
            "source_subresources": {
                "amendments": {"count": 26, "url": "https://api.congress.gov/v3/bill/119/hr/3838/amendments?format=json"},
            },
        }
    }

    packet = build_congressgov_source_packet(target, congress_cache=cache)

    assert packet["review_classification"] == "likely_upgrade_candidate"
    assert packet["source_availability"]["matched_amendment"] is True
    assert packet["amendment"]["amendment_id"] == "119:hamdt:99"
    assert packet["amendment"]["amendment_number"] == "34"
    assert packet["amendment"]["type"] == "HAMDT"
    assert packet["amendment"]["match_confidence"] == "high"
    assert packet["amendment"]["match_reason"].startswith("Matched the printed House amendment number")
    assert packet["amendment"]["latest_action"]["text"].endswith("(Roll no. 244).")
    assert {
        "source_type": "congressgov_amendment",
        "url": "https://api.congress.gov/v3/amendment/119/hamdt/99?format=json",
    } in packet["source_context"]["congressgov_source_urls"]


def test_build_source_packet_keeps_bill_level_only_amendment_limited() -> None:
    target = {
        "roll_call_id": 224,
        "chamber": "house",
        "congress": 119,
        "rollcall_number": 244,
        "question": "On Agreeing to the Amendment",
        "description": "Meeks of New York Part A Amendment No. 34",
        "source_url": "https://clerk.house.gov/evs/2025/roll244.xml",
        "bill_congress": 119,
        "bill_type": "hr",
        "bill_number": 3838,
        "bill_title": "Defense Authorization Act",
        "primary_domain": "NATIONAL_SECURITY_FOREIGN",
        "interpretation_status": "insufficient_evidence",
        "issue_facet": "Defense authorization amendment",
        "vote_type": "amendment",
    }
    cache = {
        (119, "hr", 3838): {
            "summary": "The bill sets FY2026 defense policies and authorities.",
            "legislation_url": "https://www.congress.gov/bill/119th-congress/house-bill/3838",
            "latest_action": {"action_date": "2025-09-30", "text": "Received in the Senate."},
            "actions": [],
            "amendments": [],
            "source_subresources": {
                "amendments": {"count": 26, "url": "https://api.congress.gov/v3/bill/119/hr/3838/amendments?format=json"},
            },
        }
    }

    packet = build_congressgov_source_packet(target, congress_cache=cache)

    assert packet["review_classification"] == "still_limited"
    assert packet["source_availability"]["bill_summary"] is True
    assert packet["source_availability"]["amendment_subresource_reference"] is True
    assert packet["source_availability"]["matched_amendment"] is False


def test_build_source_packet_keeps_uncertain_amendment_match_limited() -> None:
    target = {
        "roll_call_id": 240,
        "chamber": "house",
        "congress": 119,
        "rollcall_number": 260,
        "question": "On Agreeing to the Amendment",
        "description": "Rose of Tennessee Part A Amendment No. 253",
        "source_url": "https://clerk.house.gov/evs/2025/roll260.xml",
        "bill_congress": 119,
        "bill_type": "hr",
        "bill_number": 3838,
        "bill_title": "Defense Authorization Act",
        "interpretation_status": "insufficient_evidence",
        "issue_facet": "Defense authorization amendment",
        "vote_type": "amendment",
    }
    cache = {
        (119, "hr", 3838): {
            "summary": "The bill sets FY2026 defense policies and authorities.",
            "amendments": [
                {
                    "congress": 119,
                    "type": "HAMDT",
                    "number": "80",
                    "description": "An amendment numbered 252 printed in Part A of House Report 119-255.",
                    "url": "https://api.congress.gov/v3/amendment/119/hamdt/80?format=json",
                }
            ],
            "source_subresources": {
                "amendments": {"count": 26, "url": "https://api.congress.gov/v3/bill/119/hr/3838/amendments?format=json"},
            },
        }
    }

    packet = build_congressgov_source_packet(target, congress_cache=cache)

    assert packet["review_classification"] == "still_limited"
    assert packet["source_availability"]["matched_amendment"] is False
    assert packet["amendment"]["match_confidence"] is None


def test_build_source_packet_marks_missing_cache_without_promoting() -> None:
    target = SourcePacketTarget(
        roll_call_id=1,
        chamber="house",
        congress=119,
        rollcall_number=1,
        question="On Agreeing to the Amendment",
        description="Member Part A Amendment No. 1",
        source_url=None,
        bill_congress=119,
        bill_type="hr",
        bill_number=9999,
        bill_title="Missing Bill",
        interpretation_status="insufficient_evidence",
    )

    packet = build_congressgov_source_packet(target, congress_cache={})

    assert classify_source_packet(packet) == "source_missing_or_unavailable"
    assert packet["review_classification"] == "source_missing_or_unavailable"
    assert packet["source_availability"]["bill_cache_hit"] is False


def test_find_matching_amendment_can_match_by_sponsor_when_number_absent() -> None:
    amendment = find_matching_amendment(
        [
            {
                "sponsor": "Meeks of New York",
                "purpose": "Adds reporting requirements.",
            }
        ],
        amendment_number=None,
        sponsor_text="Meeks of New York",
    )

    assert amendment["purpose"] == "Adds reporting requirements."
