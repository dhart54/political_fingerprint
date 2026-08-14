from __future__ import annotations

import copy
import os

import pytest

from app.editorial_artifacts.publication_activation import load_activation_bundle
from scripts.editorial_artifact_store import StoreSafetyError, _connect
from scripts.foushee_justice_full_record_activation import (
    _apply as apply_justice_full_record,
    build_bundle as build_justice_full_record_bundle,
    preflight as justice_full_record_preflight,
)
from scripts.foushee_justice_publication_activation import (
    _apply as apply_justice_compact,
)
from scripts.foushee_national_security_publication_activation import (
    ISSUE_ID,
    POST_M11M_MAIN,
    _apply,
    _counts,
    _registry_rows,
    _rollback,
    _selector_state,
    _state_fingerprint,
    build_authority,
    build_write_set,
    capture_preflight,
)


DATABASE_URL = os.getenv("M11N_DISPOSABLE_DATABASE_URL")


pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="M11N_DISPOSABLE_DATABASE_URL is required",
)


def _prepare_current_justice_state(conn) -> None:
    compact = load_activation_bundle()
    with conn.transaction():
        apply_justice_compact(conn, compact)
    justice_preflight = justice_full_record_preflight(conn, POST_M11M_MAIN)
    justice_bundle = build_justice_full_record_bundle(justice_preflight, POST_M11M_MAIN)
    with conn.transaction():
        apply_justice_full_record(conn, justice_bundle)


def test_m11n_apply_idempotency_drift_guard_and_exact_rollback() -> None:
    assert DATABASE_URL is not None
    with _connect(DATABASE_URL, autocommit=False) as conn:
        _prepare_current_justice_state(conn)
        preflight = capture_preflight(conn, deployed_commit=POST_M11M_MAIN)
        authority = build_authority(preflight)
        write_set = build_write_set(preflight, authority)
        before_counts = _counts(conn)
        before_fingerprint = _state_fingerprint(conn)
        before_registry = _registry_rows(conn)
        before_selector = _selector_state(conn)

        drifted = copy.deepcopy(write_set)
        drifted["preflight_binding"]["state_fingerprint_sha256"] = "0" * 64
        with pytest.raises(StoreSafetyError, match="drifted from M11N preflight"):
            with conn.transaction(force_rollback=True):
                _apply(conn, drifted)

        with conn.transaction():
            first = _apply(conn, write_set)
        assert first["already_applied"] is False
        assert first["postcheck"]["counts"] == write_set["expected_counts"]["after"]
        assert len(first["artifact_ids"]) == 3

        with conn.transaction():
            second = _apply(conn, write_set)
        assert second["already_applied"] is True
        assert second["postcheck"]["counts"] == write_set["expected_counts"]["after"]
        registry = _registry_rows(conn)
        assert len(registry) == 2
        assert (
            next(row for row in registry if row["issue_id"] == ISSUE_ID)["natural_key"]
            == write_set["publication_registry"]["presentation_natural_key"]
        )

        with conn.transaction():
            rolled_back = _rollback(conn, write_set)
        assert rolled_back["counts"] == before_counts
        assert rolled_back["state_fingerprint_sha256"] == before_fingerprint
        assert _registry_rows(conn) == before_registry
        assert _selector_state(conn) == before_selector
