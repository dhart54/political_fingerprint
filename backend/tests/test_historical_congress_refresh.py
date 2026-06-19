import pytest

from app.etl.historical_congress_refresh import (
    APPROVAL_PHRASE,
    _coverage_errors,
    session_cache_dir,
    write_historical_refresh,
)


def test_historical_session_cache_dirs_are_congress_aware() -> None:
    house_dir = session_cache_dir(congress=118, chamber="house", session=1)
    senate_dir = session_cache_dir(congress=118, chamber="senate", session=2)

    assert house_dir.parts[-2:] == ("house_clerk", "2023")
    assert senate_dir.parts[-2:] == ("senate_xml", "118_2")


def test_historical_write_requires_exact_approval_phrase_before_database_access() -> None:
    with pytest.raises(ValueError, match="historical Congress refresh gate"):
        write_historical_refresh(approval_phrase=APPROVAL_PHRASE.lower())


def test_coverage_errors_report_incomplete_chamber_session() -> None:
    audit = {
        "sessions": {
            "1": {
                "house": {
                    "coverage_complete": False,
                    "cached_roll_files": 723,
                    "expected_roll_files": 724,
                },
                "senate": {
                    "coverage_complete": True,
                    "cached_roll_files": 352,
                    "expected_roll_files": 352,
                },
            }
        }
    }

    assert _coverage_errors(audit) == [
        "house session 1 source coverage incomplete: cached 723 of 724."
    ]


def test_unsupported_historical_congress_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported historical Congress"):
        session_cache_dir(congress=117, chamber="house", session=1)
