from pathlib import Path

import pytest

from app.etl.legislator_contacts import _parse_record, load_legislator_contacts


SEED_PATH = Path(__file__).resolve().parents[2] / "docs" / "legislator_contacts" / "nc_federal_contacts_seed.json"


def test_load_legislator_contacts_accepts_nc_seed_records() -> None:
    records = load_legislator_contacts(SEED_PATH)

    assert len(records) == 3
    assert {record.bioguide_id for record in records} == {"F000477", "B001305", "T000476"}
    assert {record.source_type for record in records} == {
        "official_house_website",
        "official_senate_website",
    }
    assert all(record.source_retrieved_at == "2026-05-19" for record in records)


def test_load_legislator_contacts_requires_a_contact_field() -> None:
    with pytest.raises(ValueError, match="At least one contact field is required"):
        _parse_record(
            {
                "bioguide_id": "F000477",
                "source_url": "https://foushee.house.gov/",
                "source_type": "official_house_website",
                "source_retrieved_at": "2026-05-19",
            }
        )


def test_load_legislator_contacts_rejects_unofficial_source_type() -> None:
    with pytest.raises(ValueError, match="Unsupported source_type"):
        _parse_record(
            {
                "bioguide_id": "F000477",
                "official_website_url": "https://foushee.house.gov/",
                "source_url": "https://example.com/contact",
                "source_type": "third_party_directory",
                "source_retrieved_at": "2026-05-19",
            }
        )
