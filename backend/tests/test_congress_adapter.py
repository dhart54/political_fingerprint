from datetime import date
import json

from app.etl.compute import run_etl
from app.etl.congress_adapter import load_congress_bill_cache, load_congress_sample_bundle
from app.etl.house_clerk_adapter import load_house_clerk_bundle
from app.etl.senate_xml_adapter import _parse_senate_bill_reference
from app.etl.seed import build_seed_bundle


def test_load_congress_sample_bundle_normalizes_official_style_records() -> None:
    bundle = load_congress_sample_bundle()

    assert len(bundle.legislators) == 3
    assert bundle.legislators[0]["id"] == "leg_alex_morgan"
    assert len(bundle.bills) == 12
    assert bundle.roll_calls[0]["bill_ref"] == "bill_118_hr_101"
    assert bundle.votes_cast[0]["roll_call_id"] == "rc_house_001"


def test_run_etl_supports_congress_sample_source() -> None:
    result = run_etl(source="congress_sample", as_of=date(2026, 3, 12))

    assert result.records_loaded == 48
    assert result.records_classified == 12
    assert result.fingerprints_computed == 24
    assert result.drift_scores_computed == 3


def test_build_seed_bundle_supports_congress_sample_source() -> None:
    bundle = build_seed_bundle(source="congress_sample", as_of=date(2026, 3, 12))

    assert len(bundle.legislators) == 3
    assert len(bundle.vote_classifications) == 12
    assert len(bundle.summaries) == 3


def test_load_congress_bill_cache_merges_summary_and_subject_subresources(tmp_path) -> None:
    bills_dir = tmp_path / "congress" / "bills"
    summaries_dir = tmp_path / "congress" / "bill_summaries"
    subjects_dir = tmp_path / "congress" / "bill_subjects"
    actions_dir = tmp_path / "congress" / "bill_actions"
    texts_dir = tmp_path / "congress" / "bill_texts"
    bills_dir.mkdir(parents=True)
    summaries_dir.mkdir()
    subjects_dir.mkdir()
    actions_dir.mkdir()
    texts_dir.mkdir()

    (bills_dir / "119_hr_120.json").write_text(
        json.dumps(
            {
                "bill": {
                    "congress": 119,
                    "type": "HR",
                    "number": "120",
                    "title": "Test Act",
                    "introducedDate": "2025-01-03",
                    "originChamber": "House",
                    "latestAction": {"actionDate": "2025-02-01", "text": "Passed House."},
                    "summaries": {
                        "count": 1,
                        "url": "https://api.congress.gov/v3/bill/119/hr/120/summaries",
                    },
                    "subjects": {
                        "count": 1,
                        "url": "https://api.congress.gov/v3/bill/119/hr/120/subjects",
                    },
                    "actions": {
                        "count": 1,
                        "url": "https://api.congress.gov/v3/bill/119/hr/120/actions",
                    },
                    "textVersions": {
                        "count": 1,
                        "url": "https://api.congress.gov/v3/bill/119/hr/120/text",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (summaries_dir / "119_hr_120.json").write_text(
        json.dumps({"summaries": [{"text": "CRS says the bill expands a grant program."}]}),
        encoding="utf-8",
    )
    (subjects_dir / "119_hr_120.json").write_text(
        json.dumps({"subjects": [{"name": "Education programs"}]}),
        encoding="utf-8",
    )
    (actions_dir / "119_hr_120.json").write_text(
        json.dumps({"actions": [{"actionDate": "2025-02-01", "text": "Passed House."}]}),
        encoding="utf-8",
    )
    (texts_dir / "119_hr_120.json").write_text(
        json.dumps(
            {
                "textVersions": [
                    {
                        "date": "2025-02-01",
                        "type": "Engrossed in House",
                        "formats": [{"type": "Formatted Text", "url": "https://example.com/text.htm"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    cache = load_congress_bill_cache(bills_dir)

    bill = cache[(119, "hr", 120)]
    assert bill["summary"] == "CRS says the bill expands a grant program."
    assert bill["subjects"] == ["Education programs"]
    assert bill["latest_action"] == {"action_date": "2025-02-01", "text": "Passed House."}
    assert bill["introduced_date"] == "2025-01-03"
    assert bill["origin_chamber"] == "House"
    assert bill["actions"] == [{"actionDate": "2025-02-01", "text": "Passed House."}]
    assert bill["text_versions"][0]["type"] == "Engrossed in House"
    assert bill["source_subresources"]["summaries"]["count"] == 1
    assert bill["source_subresources"]["actions"]["count"] == 1


def test_load_congress_bill_cache_flattens_nested_subject_subresource(tmp_path) -> None:
    bills_dir = tmp_path / "congress" / "bills"
    subjects_dir = tmp_path / "congress" / "bill_subjects"
    bills_dir.mkdir(parents=True)
    subjects_dir.mkdir()

    (bills_dir / "119_hr_498.json").write_text(
        json.dumps(
            {
                "bill": {
                    "congress": 119,
                    "type": "HR",
                    "number": "498",
                    "title": "Do No Harm in Medicaid Act",
                }
            }
        ),
        encoding="utf-8",
    )
    (subjects_dir / "119_hr_498.json").write_text(
        json.dumps(
            {
                "subjects": {
                    "legislativeSubjects": [{"name": "Medicaid"}],
                    "policyArea": {"name": "Health"},
                }
            }
        ),
        encoding="utf-8",
    )

    cache = load_congress_bill_cache(bills_dir)

    assert cache[(119, "hr", 498)]["subjects"] == ["Medicaid", "Health"]


def test_load_congress_bill_cache_preserves_unfetched_subresource_references(tmp_path) -> None:
    bills_dir = tmp_path / "congress" / "bills"
    bills_dir.mkdir(parents=True)

    (bills_dir / "119_hr_3838.json").write_text(
        json.dumps(
            {
                "bill": {
                    "congress": 119,
                    "type": "HR",
                    "number": "3838",
                    "title": "Defense Authorization Act",
                    "actions": {
                        "count": 82,
                        "url": "https://api.congress.gov/v3/bill/119/hr/3838/actions?format=json",
                    },
                    "amendments": {
                        "count": 26,
                        "url": "https://api.congress.gov/v3/bill/119/hr/3838/amendments?format=json",
                    },
                    "committeeReports": [
                        {
                            "citation": "H. Rept. 119-231",
                            "url": "https://api.congress.gov/v3/committee-report/119/HRPT/231?format=json",
                        }
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    cache = load_congress_bill_cache(bills_dir)

    bill = cache[(119, "hr", 3838)]
    assert bill["source_subresources"]["actions"]["count"] == 82
    assert bill["source_subresources"]["amendments"]["url"].endswith("/amendments?format=json")
    assert bill["committee_reports"] == [
        {
            "citation": "H. Rept. 119-231",
            "url": "https://api.congress.gov/v3/committee-report/119/HRPT/231?format=json",
        }
    ]


def test_load_congress_bill_cache_merges_amendment_companion_payload(tmp_path) -> None:
    congress_dir = tmp_path / "congress"
    bills_dir = congress_dir / "bills"
    amendments_dir = congress_dir / "bill_amendments"
    bills_dir.mkdir(parents=True)
    amendments_dir.mkdir(parents=True)

    (bills_dir / "119_hr_3838.json").write_text(
        json.dumps(
            {
                "bill": {
                    "congress": 119,
                    "type": "HR",
                    "number": "3838",
                    "title": "Defense Authorization Act",
                    "amendments": {
                        "count": 26,
                        "url": "https://api.congress.gov/v3/bill/119/hr/3838/amendments?format=json",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (amendments_dir / "119_hr_3838.json").write_text(
        json.dumps(
            {
                "amendments": [
                    {
                        "congress": 119,
                        "type": "HAMDT",
                        "number": "99",
                        "description": "An amendment numbered 34 printed in Part A of House Report 119-255.",
                        "purpose": "Amendment repeals specified authorizations for use of military force.",
                        "latestAction": {
                            "actionDate": "2025-09-10",
                            "text": "On agreeing to the Meeks amendment Agreed to by recorded vote.",
                        },
                        "url": "https://api.congress.gov/v3/amendment/119/hamdt/99?format=json",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    cache = load_congress_bill_cache(bills_dir)

    amendment = cache[(119, "hr", 3838)]["amendments"][0]
    assert amendment["number"] == "99"
    assert amendment["purpose"].startswith("Amendment repeals")
    assert amendment["latestAction"]["actionDate"] == "2025-09-10"
    assert cache[(119, "hr", 3838)]["source_subresources"]["amendments"]["count"] == 26


def test_house_clerk_bundle_uses_congress_session_ids_and_historical_source_urls(tmp_path) -> None:
    source_dir = tmp_path / "house"
    source_dir.mkdir()
    (source_dir / "members.xml").write_text(
        """
        <MemberData>
          <members>
            <member>
              <member-info>
                <bioguideID>A000001</bioguideID>
                <official-name>Example Member</official-name>
                <party>D</party>
                <state postal-code="NC" />
                <district>4</district>
              </member-info>
            </member>
          </members>
        </MemberData>
        """,
        encoding="utf-8",
    )
    (source_dir / "roll001.xml").write_text(
        """
        <rollcall-vote>
          <vote-metadata>
            <congress>118</congress>
            <session>1st</session>
            <rollcall-num>1</rollcall-num>
            <legis-num>H R 1</legis-num>
            <vote-question>On Passage</vote-question>
            <vote-desc>Example Act</vote-desc>
            <action-date>2023-01-09</action-date>
          </vote-metadata>
          <vote-data>
            <recorded-vote>
              <legislator bioguide-id="A000001">Example Member</legislator>
              <vote>Yea</vote>
            </recorded-vote>
          </vote-data>
        </rollcall-vote>
        """,
        encoding="utf-8",
    )

    bundle = load_house_clerk_bundle(source_dir=source_dir)

    assert bundle.roll_calls[0]["id"] == "rc_house_118_1_001"
    assert bundle.votes_cast[0]["roll_call_id"] == "rc_house_118_1_001"
    assert bundle.roll_calls[0]["source_url"] == "https://clerk.house.gov/evs/2023/roll001.xml"


def test_senate_bill_reference_supports_concurrent_resolutions() -> None:
    assert _parse_senate_bill_reference(
        document_type="S. Con. Res.",
        document_number="41",
        document_name=None,
    ) == ("sconres", 41)
