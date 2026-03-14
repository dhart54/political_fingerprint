import sys
from pathlib import Path

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
        "run_etl_and_persist_sources",
        lambda *, sources, as_of: type(
            "PersistResult",
            (),
            {
                "source": "+".join(sources),
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
    monkeypatch.setattr(
        live_pipeline,
        "run_etl_and_persist",
        lambda *, source, as_of: type(
            "PersistResult",
            (),
            {
                "source": source,
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
    monkeypatch.setattr(live_pipeline, "infer_house_bill_refs_from_cache", lambda **kwargs: set())
    monkeypatch.setattr(live_pipeline, "infer_senate_bill_refs_from_cache", lambda **kwargs: set())

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
        "infer_house_bill_refs_from_cache",
        lambda **kwargs: {(119, "hr", 121)},
    )
    monkeypatch.setattr(
        live_pipeline,
        "run_etl_and_persist_sources",
        lambda *, sources, as_of: type(
            "PersistResult",
            (),
            {
                "source": "+".join(sources),
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
        "infer_senate_bill_refs_from_cache",
        lambda **kwargs: set(),
    )
    monkeypatch.setattr(
        live_pipeline,
        "run_etl_and_persist",
        lambda *, source, as_of: type(
            "PersistResult",
            (),
            {
                "source": source,
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

    assert fetched == [
        (119, "hr", 120, "resolved-key"),
        (119, "hr", 121, "resolved-key"),
    ]
    assert result.congress_bills_fetched == 2


def test_run_live_pipeline_supports_mixed_house_and_senate_runs(monkeypatch) -> None:
    calls = {"sources": None}

    monkeypatch.setattr(live_pipeline, "fetch_house_clerk_members", lambda: None)
    monkeypatch.setattr(live_pipeline, "fetch_house_clerk_roll_calls", lambda **kwargs: [])
    monkeypatch.setattr(live_pipeline, "fetch_senate_members", lambda: None)
    monkeypatch.setattr(live_pipeline, "fetch_senate_vote_files", lambda **kwargs: [])
    monkeypatch.setattr(live_pipeline, "infer_house_bill_refs_from_cache", lambda **kwargs: set())
    monkeypatch.setattr(live_pipeline, "infer_senate_bill_refs_from_cache", lambda **kwargs: set())
    monkeypatch.setattr(
        live_pipeline,
        "run_etl_and_persist",
        lambda *, source, as_of: (_ for _ in ()).throw(AssertionError("single-source persist should not be used")),
    )
    monkeypatch.setattr(
        live_pipeline,
        "run_etl_and_persist_sources",
        lambda *, sources, as_of: calls.__setitem__("sources", sources) or type(
            "PersistResult",
            (),
            {
                "source": "+".join(sources),
                "legislators_seeded": 5,
                "bills_seeded": 8,
                "roll_calls_seeded": 8,
                "votes_seeded": 20,
                "classifications_seeded": 8,
                "fingerprints_seeded": 40,
                "chamber_medians_seeded": 48,
                "drift_scores_seeded": 5,
                "summaries_seeded": 5,
                "zip_mappings_seeded": 3,
            },
        )(),
    )

    result = live_pipeline.run_live_pipeline(
        house_year=2025,
        house_roll_numbers=[1],
        senate_congress=119,
        senate_session=1,
        senate_roll_numbers=[1],
        bill_refs=[],
        congress_api_key=None,
    )

    assert calls["sources"] == ["house_clerk_cache", "senate_xml_cache"]
    assert result.persisted_source == "house_clerk_cache+senate_xml_cache"


def test_infer_house_bill_refs_from_cache_reads_house_roll_xml(tmp_path: Path) -> None:
    source_dir = tmp_path / "house"
    source_dir.mkdir()
    (source_dir / "roll362.xml").write_text(
        """
        <rollcall-vote>
          <vote-metadata>
            <congress>119</congress>
            <legis-num>H R 498</legis-num>
          </vote-metadata>
        </rollcall-vote>
        """.strip()
    )

    refs = live_pipeline.infer_house_bill_refs_from_cache(
        roll_numbers=[362],
        source_dir=source_dir,
    )

    assert refs == {(119, "hr", 498)}


def test_infer_house_bill_refs_from_cache_ignores_unsupported_entries(tmp_path: Path) -> None:
    source_dir = tmp_path / "house"
    source_dir.mkdir()
    (source_dir / "roll362.xml").write_text(
        """
        <rollcall-vote>
          <vote-metadata>
            <congress>119</congress>
            <legis-num>H J RES 1</legis-num>
          </vote-metadata>
        </rollcall-vote>
        """.strip()
    )

    refs = live_pipeline.infer_house_bill_refs_from_cache(
        roll_numbers=[362],
        source_dir=source_dir,
    )

    assert refs == set()


def test_infer_senate_bill_refs_from_cache_reads_senate_vote_xml(tmp_path: Path) -> None:
    source_dir = tmp_path / "senate"
    source_dir.mkdir()
    (source_dir / "vote_372.xml").write_text(
        """
        <roll_call_vote>
          <congress>119</congress>
          <document>
            <document_type>H.R.</document_type>
            <document_number>1</document_number>
            <document_name>H.R. 1</document_name>
          </document>
        </roll_call_vote>
        """.strip()
    )

    refs = live_pipeline.infer_senate_bill_refs_from_cache(
        roll_numbers=[372],
        source_dir=source_dir,
    )

    assert refs == {(119, "hr", 1)}


def test_infer_senate_bill_refs_from_cache_ignores_unsupported_entries(tmp_path: Path) -> None:
    source_dir = tmp_path / "senate"
    source_dir.mkdir()
    (source_dir / "vote_372.xml").write_text(
        """
        <roll_call_vote>
          <congress>119</congress>
          <document>
            <document_type>PN</document_type>
            <document_number>12-43</document_number>
            <document_name>PN12-43</document_name>
          </document>
        </roll_call_vote>
        """.strip()
    )

    refs = live_pipeline.infer_senate_bill_refs_from_cache(
        roll_numbers=[372],
        source_dir=source_dir,
    )

    assert refs == set()


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
