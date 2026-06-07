import json

from app.etl.amendment_companion_enrichment import (
    build_amendment_interpretation_candidate,
    build_review_batch_from_packets,
    find_amendment_heavy_weak_sections,
)


def _packet(
    roll_call_id: int,
    rollcall_number: int,
    amendment_number: int,
    *,
    status: str | None = "insufficient_evidence",
    member_vote: str = "nay",
) -> dict:
    return {
        "roll_call_id": roll_call_id,
        "chamber": "house",
        "congress": 119,
        "rollcall_number": rollcall_number,
        "primary_domain": "NATIONAL_SECURITY_FOREIGN",
        "classification_version": "v1",
        "current_interpretation": {
            "interpretation_status": status,
            "issue_facet": "Defense authorization amendment",
        },
        "official_text": {
            "bill_congress": 119,
            "bill_type": "hr",
            "bill_number": 3838,
            "bill_title": "Defense Authorization Act",
            "bill_summary": "",
            "question": "On Agreeing to the Amendment",
            "description": f"Member of State Part A Amendment No. {amendment_number}",
            "source_url": f"https://clerk.house.gov/evs/2025/roll{rollcall_number:03d}.xml",
        },
        "vote_context": {
            "member_vote": member_vote,
            "vote_type": "amendment",
            "final_result": "Failed",
        },
    }


def test_finds_amendment_heavy_weak_sections() -> None:
    packets = [
        _packet(1, 244, 34),
        _packet(2, 245, 35),
        _packet(3, 246, 36),
        _packet(4, 300, 1, status="interpreted"),
    ]

    sections = find_amendment_heavy_weak_sections(packets, min_amendment_rows=3)

    assert len(sections) == 1
    assert sections[0]["section_id"] == "NATIONAL_SECURITY_FOREIGN:119:hr:3838"
    assert sections[0]["weak_amendment_rows"] == 3
    assert [row["rollcall_number"] for row in sections[0]["roll_calls"]] == [244, 245, 246]
    assert "do not import" in sections[0]["recommended_next_step"].lower()


def test_build_review_batch_creates_source_packets_and_review_only_candidates() -> None:
    packets = [_packet(1, 244, 34, member_vote="nay")]
    cache = {
        (119, "hr", 3838): {
            "summary": "The bill sets defense policies.",
            "amendments": [
                {
                    "congress": 119,
                    "type": "HAMDT",
                    "number": "99",
                    "description": "An amendment numbered 34 printed in Part A of House Report 119-255.",
                    "purpose": "Amendment prohibits assistance to a specified program.",
                    "url": "https://api.congress.gov/v3/amendment/119/hamdt/99?format=json",
                }
            ],
            "source_subresources": {
                "amendments": {"count": 1, "url": "https://api.congress.gov/v3/bill/119/hr/3838/amendments?format=json"}
            },
        }
    }

    batch = build_review_batch_from_packets(packets, congress_cache=cache)

    assert batch["workflow_boundary"][0] == "Offline review artifact only."
    assert batch["source_packets"][0]["review_classification"] == "likely_upgrade_candidate"
    candidate = batch["candidate_interpretations"][0]
    assert candidate["interpretation_status"] == "interpreted"
    assert candidate["interpretation_status_recommendation"] == "review_candidate_only"
    assert candidate["support_position"] == "yea"
    assert candidate["oppose_position"] == "nay"
    assert "not final passage" in candidate["what_not_to_infer"]
    assert "voting recommendation" in candidate["what_not_to_infer"]


def test_candidate_stays_limited_without_yea_nay_member_vote() -> None:
    source_packet = {
        "roll_call_id": 1,
        "rollcall_number": 244,
        "vote_question": "On Agreeing to the Amendment",
        "bill": {"bill_id": "119:hr:3838"},
        "amendment": {
            "amendment_id": "119:hamdt:99",
            "purpose": "Amendment requires a report.",
            "matched_from_roll_description": True,
        },
    }
    manual_packet = {
        "vote_context": {"member_vote": "not_voting", "final_result": "Agreed to"},
        "classification_version": "v1",
    }

    candidate = build_amendment_interpretation_candidate(source_packet, manual_packet=manual_packet)

    assert candidate["interpretation_status"] == "insufficient_evidence"
    assert candidate["interpretation_status_recommendation"] == "keep_limited"
    assert candidate["support_position"] is None
    assert "recorded vote is missing or not a Yea/Nay vote" in candidate["uncertainty_note"]


def test_review_batch_payload_is_json_serializable() -> None:
    batch = build_review_batch_from_packets([_packet(1, 244, 34)], congress_cache={})

    json.dumps(batch)
