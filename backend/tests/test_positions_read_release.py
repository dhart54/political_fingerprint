"""Ownership and failure boundaries for the positions publication handoff."""
from contextvars import copy_context
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest

from app import db
from app.api import positions, precomputed
from app.api.public_data import PublicDataUnavailable
from backend.tests.test_positions_read_scope import Connection


def test_release_is_lazy_and_later_read_uses_a_fresh_connection(monkeypatch):
    connections = []

    def connect():
        connection = Connection()
        connections.append(connection)
        return connection

    monkeypatch.setattr(precomputed, "get_connection", connect)
    db.release_precomputed_read_connection()
    with db.precomputed_read_scope():
        db.release_precomputed_read_connection()
        assert not connections
        precomputed._query_all_dicts("SELECT 7")
        assert connections[0].rollbacks == 1
        db.release_precomputed_read_connection()
        db.release_precomputed_read_connection()
        assert connections[0].closes == 1
        precomputed._query_all_dicts("SELECT 7")
        assert len(connections) == 2 and connections[1].closes == 0
    assert [c.closes for c in connections] == [1, 1]


def test_release_rejects_busy_foreign_and_retained_closed_contexts():
    connection = Connection()
    with db.precomputed_read_scope():
        with db.precomputed_read_connection(lambda: connection):
            with pytest.raises(RuntimeError, match="already borrowed"):
                db.release_precomputed_read_connection()
        context = copy_context()
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(context.run, db.release_precomputed_read_connection)
            with pytest.raises(RuntimeError, match="foreign"):
                future.result(timeout=3)
        assert connection.closes == 0
    with pytest.raises(RuntimeError, match="closed"):
        context.run(db.release_precomputed_read_connection)
    assert connection.closes == 1


def test_release_close_failure_is_sanitized_before_publication(monkeypatch):
    connection = Connection(fault="close")
    monkeypatch.setattr(precomputed, "get_connection", lambda: connection)

    def response(**kwargs):
        precomputed._query_all_dicts("SELECT 7")
        return {"positions": []}

    monkeypatch.setattr(positions, "get_position_response", response)
    monkeypatch.setattr(positions, "get_legislator_profile", lambda **kw: {"bioguide_id": "F000477"})
    publication = Mock()
    monkeypatch.setattr(positions, "_load_publication_rows", publication)
    with pytest.raises(PublicDataUnavailable) as error:
        positions.get_legislator_positions("test", "119", None)
    assert "private" not in str(error.value)
    assert connection.closes == 1
    publication.assert_not_called()
    # A close fault detaches the old handle and the outer finally resets scope.
    with db.precomputed_read_scope():
        db.release_precomputed_read_connection()


def test_reconnect_failure_after_release_preserves_cleanup(monkeypatch):
    connection = Connection()
    factory = Mock(side_effect=[connection, RuntimeError("private reconnect detail")])
    monkeypatch.setattr(precomputed, "get_connection", factory)
    with db.precomputed_read_scope():
        precomputed._query_all_dicts("SELECT 7")
        db.release_precomputed_read_connection()
        with pytest.raises(PublicDataUnavailable):
            precomputed._query_all_dicts("SELECT 7")
    assert connection.closes == 1 and factory.call_count == 2
