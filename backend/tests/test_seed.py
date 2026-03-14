from datetime import date

from app.etl.seed import (
    build_seed_bundle,
    build_seed_bundle_for_sources,
    persist_seed_bundle,
    run_etl_and_persist,
    run_etl_and_persist_sources,
    seed_fixture_database,
)


def test_build_seed_bundle_contains_expected_fixture_counts() -> None:
    bundle = build_seed_bundle(as_of=date(2026, 3, 12))

    assert len(bundle.legislators) == 3
    assert len(bundle.bills) == 12
    assert len(bundle.roll_calls) == 14
    assert len(bundle.votes_cast) == 21
    assert len(bundle.vote_classifications) == 14
    assert len(bundle.fingerprints) == 24
    assert len(bundle.chamber_medians) == 48
    assert len(bundle.drift_scores) == 3
    assert len(bundle.summaries) == 3
    assert len(bundle.zip_district_map) == 2


def test_build_seed_bundle_generates_deterministic_summaries() -> None:
    bundle = build_seed_bundle(as_of=date(2026, 3, 12))

    assert bundle.summaries[0]["generation_method"] == "deterministic_fallback"
    assert "eligible votes" in bundle.summaries[0]["summary_text"]
    assert bundle.summaries[0]["created_at"] == "2026-03-12T00:00:00+00:00"


def test_persist_seed_bundle_replaces_tables_and_commits(monkeypatch) -> None:
    executed = []

    class FakeCursor:
        def execute(self, query, params=None):
            executed.append((query.strip(), params))

        def executemany(self, query, params_seq):
            params_list = list(params_seq)
            executed.append((query.strip(), params_list))

    class FakeConnection:
        def __init__(self):
            self.cursor_instance = FakeCursor()
            self.committed = False
            self.rolled_back = False
            self.closed = False

        def cursor(self):
            return self.cursor_instance

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rolled_back = True

        def close(self):
            self.closed = True

    fake_connection = FakeConnection()
    monkeypatch.setattr("app.etl.seed.get_connection", lambda: fake_connection)

    bundle = build_seed_bundle(as_of=date(2026, 3, 12))
    persist_seed_bundle(bundle)

    assert any(statement.startswith("DELETE FROM summaries") for statement, _ in executed)
    assert any(statement.startswith("INSERT INTO legislators") for statement, _ in executed)
    assert any(statement.startswith("INSERT INTO summaries") for statement, _ in executed)
    assert fake_connection.committed is True
    assert fake_connection.rolled_back is False
    assert fake_connection.closed is True


def test_seed_fixture_database_returns_seed_counts(monkeypatch) -> None:
    monkeypatch.setattr("app.etl.seed.persist_seed_bundle", lambda bundle: None)

    result = seed_fixture_database(as_of=date(2026, 3, 12))

    assert result.source == "fixtures"
    assert result.legislators_seeded == 3
    assert result.summaries_seeded == 3


def test_run_etl_and_persist_uses_source_and_returns_seed_counts(monkeypatch) -> None:
    monkeypatch.setattr("app.etl.seed.persist_seed_bundle", lambda bundle: None)

    result = run_etl_and_persist(source="fixtures", as_of=date(2026, 3, 12))

    assert result.source == "fixtures"
    assert result.fingerprints_seeded == 24


def test_build_seed_bundle_for_sources_combines_house_and_senate_cache_inputs(monkeypatch) -> None:
    from app.etl.ingest import run_ingest

    def fake_run_ingest(*, source):
        source_map = {
            "house_clerk_cache": "house_clerk_sample",
            "senate_xml_cache": "senate_xml_sample",
        }
        return run_ingest(source=source_map.get(source, source))

    monkeypatch.setattr("app.etl.seed.run_ingest", fake_run_ingest)

    bundle = build_seed_bundle_for_sources(
        sources=["house_clerk_cache", "senate_xml_cache"],
        as_of=date(2026, 3, 12),
    )

    assert len(bundle.legislators) == 5
    assert len(bundle.bills) == 8
    assert len(bundle.roll_calls) == 8
    assert len(bundle.votes_cast) == 20
    assert len(bundle.vote_classifications) == 8
    assert len(bundle.fingerprints) == 40
    assert len(bundle.chamber_medians) == 48
    assert len(bundle.drift_scores) == 5
    assert len(bundle.summaries) == 5
    assert len(bundle.zip_district_map) == 4


def test_run_etl_and_persist_sources_returns_combined_seed_counts(monkeypatch) -> None:
    from app.etl.ingest import run_ingest

    def fake_run_ingest(*, source):
        source_map = {
            "house_clerk_cache": "house_clerk_sample",
            "senate_xml_cache": "senate_xml_sample",
        }
        return run_ingest(source=source_map.get(source, source))

    monkeypatch.setattr("app.etl.seed.run_ingest", fake_run_ingest)
    monkeypatch.setattr("app.etl.seed.persist_seed_bundle", lambda bundle: None)

    result = run_etl_and_persist_sources(
        sources=["house_clerk_cache", "senate_xml_cache"],
        as_of=date(2026, 3, 12),
    )

    assert result.source == "house_clerk_cache+senate_xml_cache"
    assert result.legislators_seeded == 5
    assert result.roll_calls_seeded == 8
