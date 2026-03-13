import sys

from app.etl import live_pipeline


def test_parse_bill_ref_accepts_expected_shape() -> None:
    assert live_pipeline.parse_bill_ref("119:hr:120") == (119, "hr", 120)


def test_run_live_pipeline_fetches_house_flow(monkeypatch) -> None:
    calls = {"house_members": 0, "house_rolls": None, "persist": None}

    monkeypatch.setattr(
        live_pipeline,
        "fetch_house_clerk_members",
        lambda: calls.__setitem__("house_members", calls["house_members"] + 1),
    )
    monkeypatch.setattr(
        live_pipeline,
        "fetch_house_clerk_roll_calls",
        lambda *, year, roll_numbers, output_dir=None, overwrite=False: calls.__setitem__(
            "house_rolls",
            (year, roll_numbers),
        ),
    )
    monkeypatch.setattr(
        live_pipeline,
        "run_etl_and_persist",
        lambda *, source, as_of: type(
            "PersistResult",
            (),
            {
                "legislators_seeded": 3,
                "bills_seeded": 4,
                "roll_calls_seeded": 4,
                "votes_seeded": 12,
                "classifications_seeded": 4,
                "fingerprints_seeded": 24,
                "chamber_medians_seeded": 48,
                "drift_scores_seeded": 3,
                "summaries_seeded": 3,
                "zip_mappings_seeded": 3,
            },
        )(),
    )

    result = live_pipeline.run_live_pipeline(
        house_year=2025,
        house_roll_numbers=[1, 2],
        senate_congress=None,
        senate_session=None,
        senate_roll_numbers=[],
        bill_refs=[],
        congress_api_key=None,
    )

    assert calls["house_members"] == 1
    assert calls["house_rolls"] == (2025, [1, 2])
    assert result.house_rolls_fetched == 2
    assert result.persisted_source == "house_clerk_cache"


def test_run_live_pipeline_fetches_congress_bill_metadata(monkeypatch) -> None:
    fetched = []

    monkeypatch.setattr(live_pipeline, "fetch_house_clerk_members", lambda: None)
    monkeypatch.setattr(live_pipeline, "fetch_house_clerk_roll_calls", lambda **kwargs: [])
    monkeypatch.setattr(
        live_pipeline,
        "fetch_congress_bill_metadata",
        lambda *, congress, bill_type, bill_number, api_key: fetched.append(
            (congress, bill_type, bill_number, api_key)
        ),
    )
    monkeypatch.setattr(live_pipeline, "resolve_congress_api_key", lambda api_key: "resolved-key")
    monkeypatch.setattr(
        live_pipeline,
        "run_etl_and_persist",
        lambda *, source, as_of: type(
            "PersistResult",
            (),
            {
                "legislators_seeded": 3,
                "bills_seeded": 4,
                "roll_calls_seeded": 4,
                "votes_seeded": 12,
                "classifications_seeded": 4,
                "fingerprints_seeded": 24,
                "chamber_medians_seeded": 48,
                "drift_scores_seeded": 3,
                "summaries_seeded": 3,
                "zip_mappings_seeded": 3,
            },
        )(),
    )

    result = live_pipeline.run_live_pipeline(
        house_year=2025,
        house_roll_numbers=[1],
        senate_congress=None,
        senate_session=None,
        senate_roll_numbers=[],
        bill_refs=[(119, "hr", 120)],
        congress_api_key=None,
    )

    assert fetched == [(119, "hr", 120, "resolved-key")]
    assert result.congress_bills_fetched == 1


def test_run_live_pipeline_rejects_mixed_house_and_senate_runs() -> None:
    try:
        live_pipeline.run_live_pipeline(
            house_year=2025,
            house_roll_numbers=[1],
            senate_congress=119,
            senate_session=1,
            senate_roll_numbers=[1],
            bill_refs=[],
            congress_api_key=None,
        )
    except ValueError as error:
        assert "either House or Senate" in str(error)
    else:
        raise AssertionError("Expected ValueError for mixed House and Senate orchestration")


def test_main_supports_cli(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "live_pipeline.py",
            "--house-year",
            "2025",
            "--house-roll",
            "1",
            "--bill",
            "119:hr:120",
        ],
    )
    monkeypatch.setattr(
        live_pipeline,
        "run_live_pipeline",
        lambda **kwargs: {"status": "ok", "kwargs": kwargs},
    )

    live_pipeline.main()
    output = capsys.readouterr().out

    assert "status" in output
    assert "house_roll_numbers" in output
