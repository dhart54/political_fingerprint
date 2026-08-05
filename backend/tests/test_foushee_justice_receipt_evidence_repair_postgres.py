from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from psycopg.types.json import Jsonb

from scripts.editorial_artifact_store import StoreSafetyError, _connect
from scripts.foushee_justice_receipt_evidence_repair import (
    WRITE_CAPS,
    _matches_post_state,
    _publication_guard,
    _target_state,
    apply,
    preflight,
    rollback,
    validate_bundle,
)


DATABASE_URL = os.getenv("RECEIPT_EVIDENCE_REPAIR_DISPOSABLE_DATABASE_URL")
ROOT = Path(__file__).resolve().parents[2]
BUNDLE_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/proposals"
    / "f000477_justice_public_safety_119_receipt_evidence_repair_bundle_v1.json"
)


def _load_bundle() -> dict:
    bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
    validate_bundle(bundle)
    return bundle


def _prepare_disposable(bundle: dict) -> None:
    with _connect(DATABASE_URL, autocommit=True) as conn:
        conn.execute("DROP SCHEMA public CASCADE")
        conn.execute("CREATE SCHEMA public")
        conn.execute(
            """DO $$ BEGIN
                 IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') THEN
                   CREATE ROLE anon;
                 END IF;
                 IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN
                   CREATE ROLE authenticated;
                 END IF;
               END $$"""
        )
        for migration in sorted((ROOT / "backend/migrations").glob("*.sql")):
            conn.execute(migration.read_text(encoding="utf-8-sig"))
        conn.execute(
            """INSERT INTO legislators
                   (id,bioguide_id,name_display,chamber,state,district,party,in_office)
                 VALUES (239,'F000477','Valerie P. Foushee','house','NC','04','D',true)"""
        )
        conn.execute(
            """INSERT INTO editorial_artifact_batches
                   (batch_id,deterministic_batch_key,source_commit_sha,manifest_sha256,
                    status,artifact_count,relationship_count)
                 VALUES (1,'receipt-evidence-disposable-proof',%s,%s,'applied',1,0)""",
            ("140f713f80ba650862dd321d6752cd4e5100b54d", "0" * 64),
        )
        artifact = bundle["publication_guard"]["rows"]["artifact"]
        conn.execute(
            """INSERT INTO editorial_artifact_versions
                   (artifact_id,artifact_type,natural_key,schema_version,
                    artifact_version,payload_jsonb,content_sha256,source_commit_sha,
                    batch_id,member_bioguide_id,issue_id,congress,chamber,
                    editorial_status,benchmark_status,production_eligible,review_route)
                 VALUES
                   (221,'issue_public_presentation',%s,
                    'approved_public_presentation_v1',1,%s,%s,%s,1,'F000477',
                    'JUSTICE_PUBLIC_SAFETY',119,'house','human_approved',
                    'gold_benchmark',true,'human_exception')""",
            (
                artifact["natural_key"],
                Jsonb({"blocking_findings": 0}),
                artifact["content_sha256"],
                "140f713f80ba650862dd321d6752cd4e5100b54d",
            ),
        )
        registry = bundle["publication_guard"]["rows"]["registry"]
        conn.execute(
            """ALTER TABLE editorial_publication_registry
                 DISABLE TRIGGER editorial_publication_registry_fail_closed"""
        )
        conn.execute(
            """INSERT INTO editorial_publication_registry
                   (member_bioguide_id,issue_id,artifact_id,publicly_active,
                    activated_at,publication_metadata_jsonb)
                 VALUES ('F000477','JUSTICE_PUBLIC_SAFETY',221,true,now(),%s)""",
            (Jsonb(registry["publication_metadata_jsonb"]),),
        )
        conn.execute(
            """ALTER TABLE editorial_publication_registry
                 ENABLE TRIGGER editorial_publication_registry_fail_closed"""
        )


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires a dedicated disposable PostgreSQL database",
)
def test_exact_apply_idempotency_postcheck_and_rollback() -> None:
    bundle = _load_bundle()
    _prepare_disposable(bundle)

    with _connect(DATABASE_URL) as conn:
        with conn.transaction():
            conn.execute("SELECT setval('bills_id_seq',7000,false)")
            conn.execute("SELECT setval('roll_calls_id_seq',8000,false)")
            conn.execute("SELECT setval('votes_cast_id_seq',9000,false)")
            before = preflight(conn, bundle)
            assert before["already_applied"] is False
            assert before["target_state_sha256"] == bundle["expected_baseline"]["sha256"]

        with conn.transaction():
            applied = apply(conn, bundle)
            assert applied["already_applied"] is False
            assert applied["writes"] == WRITE_CAPS

        with conn.transaction():
            repeated = apply(conn, bundle)
            assert repeated["already_applied"] is True
            assert repeated["writes"] == {key: 0 for key in WRITE_CAPS}
            state = _target_state(conn)
            assert len(state["rows"]["bills"]) == 4
            assert len(state["rows"]["roll_calls"]) == 8
            assert len(state["rows"]["votes_cast"]) == 8
            assert len(state["rows"]["vote_contexts"]) == 8
            assert state["rows"]["vote_classifications"] == []
            assert state["rows"]["vote_interpretations"] == []
            assert _publication_guard(conn) == bundle["publication_guard"]

        with conn.transaction():
            restored = rollback(conn, bundle)
            assert restored == {
                "deleted": {
                    "bills": 4,
                    "roll_calls": 8,
                    "votes_cast": 8,
                    "vote_contexts": 8,
                },
                "restored_baseline": True,
            }

        with conn.transaction():
            after = preflight(conn, bundle)
            assert after["already_applied"] is False
            assert after["target_state_sha256"] == bundle["expected_baseline"]["sha256"]


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires a dedicated disposable PostgreSQL database",
)
def test_preflight_rejects_any_target_baseline_drift() -> None:
    bundle = _load_bundle()
    _prepare_disposable(bundle)
    with _connect(DATABASE_URL) as conn:
        with conn.transaction():
            conn.execute(
                """INSERT INTO bills
                     (congress,bill_type,bill_number,title,summary,subjects)
                     VALUES (119,'hr',1181,'Conflicting baseline','',%s)""",
                (Jsonb([]),),
            )
        with conn.transaction():
            with pytest.raises(StoreSafetyError, match="baseline fingerprint drifted"):
                preflight(conn, bundle)


def _apply_then_mutate(bundle: dict, statement: str, params: tuple = ()) -> None:
    _prepare_disposable(bundle)
    with _connect(DATABASE_URL) as conn:
        with conn.transaction():
            assert apply(conn, bundle)["writes"] == WRITE_CAPS
        with conn.transaction():
            conn.execute(statement, params)
        with conn.transaction():
            assert _matches_post_state(_target_state(conn), bundle) is False
            with pytest.raises(StoreSafetyError, match="baseline fingerprint drifted"):
                preflight(conn, bundle)
        with conn.transaction():
            with pytest.raises(StoreSafetyError, match="does not exactly match"):
                rollback(conn, bundle)


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires a dedicated disposable PostgreSQL database",
)
def test_exact_post_state_rejects_mutated_bill_field() -> None:
    _apply_then_mutate(
        _load_bundle(),
        """UPDATE bills SET title='Altered title'
             WHERE congress=119 AND bill_type='hr' AND bill_number=1181""",
    )


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires a dedicated disposable PostgreSQL database",
)
def test_exact_post_state_rejects_mutated_roll_source_url() -> None:
    _apply_then_mutate(
        _load_bundle(),
        """UPDATE roll_calls
              SET source_url='https://example.invalid/altered.xml'
            WHERE chamber='house' AND congress=119 AND rollcall_number=227""",
    )


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires a dedicated disposable PostgreSQL database",
)
def test_exact_post_state_rejects_mutated_vote_to_roll_identity() -> None:
    bundle = _load_bundle()
    _prepare_disposable(bundle)
    with _connect(DATABASE_URL) as conn:
        with conn.transaction():
            assert apply(conn, bundle)["writes"] == WRITE_CAPS
        with conn.transaction():
            rows = conn.execute(
                """SELECT v.id,r.id AS roll_call_id,r.rollcall_number,v.position
                     FROM votes_cast v JOIN roll_calls r ON r.id=v.roll_call_id
                    WHERE v.legislator_id=239 AND r.rollcall_number=ANY(%s)
                    ORDER BY r.rollcall_number""",
                ([227, 240],),
            ).fetchall()
            assert [(row["rollcall_number"], row["position"]) for row in rows] == [
                (227, "yea"), (240, "nay")
            ]
            vote_by_roll = {int(row["rollcall_number"]): row for row in rows}
            conn.execute(
                "DELETE FROM votes_cast WHERE id=%s",
                (int(vote_by_roll[227]["id"]),),
            )
            conn.execute(
                "UPDATE votes_cast SET roll_call_id=%s WHERE id=%s",
                (
                    int(vote_by_roll[227]["roll_call_id"]),
                    int(vote_by_roll[240]["id"]),
                ),
            )
            conn.execute(
                """INSERT INTO votes_cast (roll_call_id,legislator_id,position)
                     VALUES (%s,239,%s)""",
                (int(vote_by_roll[240]["roll_call_id"]), vote_by_roll[227]["position"]),
            )
        with conn.transaction():
            assert _matches_post_state(_target_state(conn), bundle) is False
            with pytest.raises(StoreSafetyError, match="baseline fingerprint drifted"):
                preflight(conn, bundle)
        with conn.transaction():
            with pytest.raises(StoreSafetyError, match="does not exactly match"):
                rollback(conn, bundle)


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires a dedicated disposable PostgreSQL database",
)
def test_exact_post_state_rejects_mutated_vote_context_field() -> None:
    _apply_then_mutate(
        _load_bundle(),
        """UPDATE vote_contexts c SET vote_margin=vote_margin+1
             FROM roll_calls r
            WHERE c.roll_call_id=r.id AND c.legislator_id=239 AND r.rollcall_number=227""",
    )
