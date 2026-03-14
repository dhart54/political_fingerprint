from datetime import date
import json
from pathlib import Path

from app.etl.compute import run_etl
from app.etl.seed import build_seed_bundle
from app.etl.senate_xml_adapter import SENATE_XML_SAMPLE_DIR, load_senate_xml_bundle, load_senate_xml_sample_bundle


def test_load_senate_xml_sample_bundle_normalizes_senate_xml() -> None:
    bundle = load_senate_xml_sample_bundle()

    assert len(bundle.legislators) == 2
    assert bundle.legislators[0]["id"] == "leg_jordan_lee"
    assert len(bundle.bills) == 4
    assert bundle.roll_calls[0]["bill_ref"] == "bill_119_s_210"
    assert bundle.bills[0]["committee"] == "Homeland Security and Governmental Affairs"
    assert bundle.vote_subject_tags["bill_119_s_210"] == ["immigration", "border security", "visas"]
    assert bundle.votes_cast[0]["roll_call_id"] == "rc_senate_001"
    assert bundle.votes_cast[1]["position"] == "nay"


def test_run_etl_supports_senate_xml_sample_source() -> None:
    result = run_etl(source="senate_xml_sample", as_of=date(2026, 3, 12))

    assert result.records_loaded == 20
    assert result.records_classified == 4
    assert result.fingerprints_computed == 16
    assert result.drift_scores_computed == 2


def test_build_seed_bundle_supports_senate_xml_sample_source() -> None:
    bundle = build_seed_bundle(source="senate_xml_sample", as_of=date(2026, 3, 12))

    assert len(bundle.legislators) == 2
    assert len(bundle.vote_classifications) == 4
    assert len(bundle.summaries) == 2


def test_senate_xml_bundle_prefers_cached_congress_bill_metadata(tmp_path: Path) -> None:
    source_dir = tmp_path / "senate_cache"
    source_dir.mkdir()
    (source_dir / "vote_001.xml").write_text((SENATE_XML_SAMPLE_DIR / "vote_001.xml").read_text())

    congress_cache_dir = tmp_path / "congress" / "bills"
    congress_cache_dir.mkdir(parents=True)
    (congress_cache_dir / "119_s_210.json").write_text(
        json.dumps(
            {
                "bill": {
                    "congress": 119,
                    "type": "s",
                    "number": 210,
                    "title": "Cached Senate Bill Title",
                },
                "summaries": [{"text": "Cached Senate summary"}],
                "committees": [{"name": "Cached Senate Committee"}],
                "policyArea": {"name": "immigration"},
            }
        )
    )

    bundle = load_senate_xml_bundle(
        source_dir=source_dir,
        fallback_dir=SENATE_XML_SAMPLE_DIR,
        congress_cache_dir=congress_cache_dir,
    )

    bill = next(item for item in bundle.bills if item["id"] == "bill_119_s_210")
    assert bill["title"] == "Cached Senate Bill Title"
    assert bill["summary"] == "Cached Senate summary"
    assert bill["committee"] == "Cached Senate Committee"
    assert bill["subjects"] == ["immigration"]


def test_load_senate_xml_bundle_skips_unsupported_senate_reference(tmp_path: Path) -> None:
    source_dir = tmp_path / "senate_cache"
    source_dir.mkdir()
    for filename in ("members.xml", "bills.json", "zip_district_map.json"):
        (source_dir / filename).write_text((SENATE_XML_SAMPLE_DIR / filename).read_text())

    (source_dir / "vote_001.xml").write_text(
        """
        <roll_call_vote>
          <congress>119</congress>
          <session>1</session>
          <vote_number>1</vote_number>
          <vote_date>July 1, 2025,  11:56 AM</vote_date>
          <question>On the Nomination</question>
          <vote_title>Nomination test</vote_title>
          <document>
            <document_type>PN</document_type>
            <document_number>12-43</document_number>
            <document_name>PN12-43</document_name>
          </document>
          <members />
        </roll_call_vote>
        """.strip()
    )

    bundle = load_senate_xml_bundle(source_dir=source_dir, fallback_dir=SENATE_XML_SAMPLE_DIR)

    assert bundle.roll_calls == []
