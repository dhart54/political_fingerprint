from datetime import date

from app.etl.seed import build_seed_bundle, persist_seed_bundle, seed_fixture_database


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
