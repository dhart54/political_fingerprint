"""New operator candidate in its own fresh dedicated fixture, never production."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
from contextlib import closing
from time import monotonic

import pytest
import psycopg
from psycopg import Cursor, sql

from scripts import education79_locator_operator as operator
from scripts import education79_locator_preparation as prep
from scripts.editorial_artifact_store import _connect, StoreSafetyError
from test_education79_locator_preparation import synthetic_candidate_approval
from test_education79_locator_operator import fixture_authority
from test_education79_locator_disposable_postgres import seed_fixture, public
from test_reusable_publication_replacement_v2r import runtime
from test_education79_locator_stream_model import model_cursor,table_scales,RTT_SECONDS,PAYLOAD_BYTES_PER_SECOND,TOTAL_STREAM_BYTES

DSN = os.getenv('EDUCATION79_OPERATOR_DATABASE_URL')
pytestmark = pytest.mark.skipif(not DSN, reason='separate dedicated PostgreSQL17 operator fixture required')


def legacy_protected_state(conn, *, exclude_batch_id=None, deadline=None, scan_timings=None):
    """Frozen128-row reader from reviewed577ce1ff, independent hash oracle."""
    result = {}
    for row in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").fetchall():
        operator.require_budget(deadline)
        table = row['tablename'];condition = sql.SQL('');params = ()
        if exclude_batch_id is not None:
            if table in ('editorial_artifact_batches','editorial_artifact_versions'):
                condition = sql.SQL(' WHERE batch_id <> %s');params = (exclude_batch_id,)
            elif table == 'editorial_artifact_relationships':
                condition = sql.SQL(' WHERE parent_artifact_id NOT IN (SELECT artifact_id FROM editorial_artifact_versions WHERE batch_id=%s) AND child_artifact_id NOT IN (SELECT artifact_id FROM editorial_artifact_versions WHERE batch_id=%s)')
                params = (exclude_batch_id,exclude_batch_id)
        statement = sql.SQL('SELECT to_jsonb(t)::text AS row_text FROM {} t{} ORDER BY row_text').format(sql.Identifier(table),condition)
        checksum = hashlib.sha256();count = 0
        with conn.cursor(name='education79_legacy_rows') as cursor:
            cursor.itersize = 128;cursor.execute(statement,params)
            for item in cursor:
                operator.require_budget(deadline)
                checksum.update(item['row_text'].encode('utf-8'));checksum.update(b'\n');count += 1
        result[table] = {'count':count,'sha256':checksum.hexdigest()}
    return result


def prove_volume_transport(conn, bundle, monkeypatch):
    """Synthetic production-scale rows in the guarded disposable database only."""
    prep.require_fixture_endpoint(conn, DSN)
    conn.rollback()
    tables = ('education79_transport_context', 'education79_transport_votes', 'education79_transport_wide')
    with conn.transaction():
        conn.execute('''CREATE TABLE education79_transport_context AS
            SELECT g::bigint AS roll_call_id,(g % 637)::bigint AS legislator_id,
            'Yea'::text AS member_position,'Democrat'::text AS member_party,
            'Yea'::text AS member_party_majority_position,true AS member_voted_with_party_majority,
            false AS member_voted_with_winning_side,
            '2026-01-01T00:00:00Z'::timestamptz AS created_at,
            '2026-01-01T00:00:00Z'::timestamptz AS updated_at
            FROM generate_series(1,815000) g''')
        conn.execute('''CREATE TABLE education79_transport_wide AS
            SELECT g::bigint AS id,repeat('é雪',2048)::text AS wide_text,
            NULL::text AS missing,'duplicate'::text AS repeated
            FROM generate_series(1,8193) g''')
        conn.execute('''CREATE TABLE education79_transport_votes AS
            SELECT g::bigint AS id,(g % 2298)::bigint AS roll_call_id,
            (g % 637)::bigint AS legislator_id,'Yea'::text AS position,
            '2026-01-01T00:00:00Z'::timestamptz AS created_at
            FROM generate_series(1,815000) g''')
    metrics = {'modeled_bytes':0.0,'largest_decoded_object_bytes_estimate':0}
    previous_factory = conn.cursor_factory
    proof = {'disposable_only': True, 'production_execution_authorized': False,
             'synthetic_row_counts': dict(zip(tables, (815000,815000,8193))),
             'wide_payload_characters': 4096, 'synthetic_tables': list(tables),
             'client_libpq_version':psycopg.pq.version(),'stream_size':1,
             'modeled_rtt_seconds':RTT_SECONDS,'modeled_payload_bytes_per_second':PAYLOAD_BYTES_PER_SECOND,
             'modeled_payload_bytes_per_full_scan':TOTAL_STREAM_BYTES,'bandwidth_emulated':True,
             'model_is_not_production_clearance':True,
             'execution_limits': operator.LIMITS, 'scan_timings_are_sidecar_only': True}
    try:
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        with monkeypatch.context() as patch:
            patch.setattr(operator, 'protected_state', legacy_protected_state)
            old = operator.capture_preflight(conn, bundle, fixture_url=DSN)
        conn.rollback()
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        unmodeled_timings=[]
        unmodeled=operator.capture_preflight(conn,bundle,fixture_url=DSN,scan_timings=unmodeled_timings)
        assert old['state']==unmodeled['state']
        conn.rollback()
        conn.cursor_factory = model_cursor(table_scales(unmodeled_timings),metrics)
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        timings = []; started = monotonic()
        baseline = operator.capture_preflight(conn, bundle, fixture_url=DSN, scan_timings=timings)
        proof['new_preflight_seconds'] = monotonic() - started
        assert old['state'] == baseline['state']
        assert old['stable_preflight_sha256'] == baseline['stable_preflight_sha256']
        assert all(baseline['state']['public_tables'][t]['count'] == n for t, n in proof['synthetic_row_counts'].items())
        proof['complete_old_new_counts_hashes_equal'] = True
        proof['preflight_scan_timings'] = timings
        conn.rollback()
        authority = fixture_authority(bundle, baseline)
        persistence_timings = []; started = monotonic()
        with pytest.raises(StoreSafetyError, match='injected'):
            with conn.transaction():
                conn.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
                operator.persist(conn, bundle, baseline, authority, confirm=True, fixture_url=DSN,
                                 fault_after=True, scan_timings=persistence_timings)
        proof['two_scan_persistence_seconds'] = monotonic() - started
        assert proof['two_scan_persistence_seconds'] <= operator.LIMITS['observation_budget_seconds']
        assert prep.owned_state(conn, bundle) is None
        assert prep.registry_row(conn, bundle['registry_key']) == baseline['state']['registry_row']
        assert all(t['status'] == 'COMPLETE' for t in persistence_timings)
        assert len(persistence_timings) == 2 * len(baseline['state']['public_tables'])
        assert sum(t['rows'] for t in persistence_timings if t['table'] in tables) == 2 * sum(proof['synthetic_row_counts'].values())
        assert {t['excludes_owned_batch'] for t in persistence_timings} == {False, True}
        assert metrics['largest_decoded_object_bytes_estimate'] < 16 * 1024 * 1024
        proof.update({'persistence_scan_timings': persistence_timings, 'transport_metrics': metrics,
                      'serializable_two_scan_rollback_verified': True, 'actual_guarded_insert_caps': operator.CAPS,
                      'status': 'PROVED_COMPLETE_TWO_SCAN_ROLLBACK'})
        if Path('/proc/self/status').exists():
            proof['process_peak_resident_memory'] = next(line for line in Path('/proc/self/status').read_text().splitlines()
                                                       if line.startswith('VmHWM:'))
    finally:
        conn.cursor_factory = previous_factory
        conn.rollback()
        # This cleanup is guarded loopback fixture DDL, never a production path.
        prep.require_fixture_endpoint(conn, DSN)
        conn.execute('DROP TABLE education79_transport_context,education79_transport_votes,education79_transport_wide')
        conn.commit()
        if folder := os.getenv('EDUCATION79_OPERATOR_PROOF_DIR'):
            path = Path(folder);path.mkdir(parents=True, exist_ok=True)
            (path / 'scan-transport-proof.json').write_text(json.dumps(proof, sort_keys=True, indent=2) + '\n', encoding='utf-8')


def prove_stream_failures(conn,bundle,baseline,authority,monkeypatch):
    """Actual stream cancellation/rollback; every target is the named loopback fixture."""
    prep.require_fixture_connection(conn,DSN)
    original_factory=conn.cursor_factory;events=[]
    class RejectedText(str):
        def encode(self,*args,**kwargs):raise StoreSafetyError('injected hash rejection')
    class FailureCursor(Cursor):
        failure='hash'
        def stream(self,statement,params=None,*,size=1,**kwargs):
            assert size==1
            text=statement.as_string()
            if self.failure=='sql':
                # Guaranteed real SQL failure, only inside this disposable adapter.
                yield from super().stream('SELECT 1/0 AS row_text',size=1)
                return
            if self.failure=='timeout':
                yield from super().stream('SELECT pg_sleep(1)::text AS row_text',size=1)
                return
            with closing(super().stream(statement,params,size=1,**kwargs)) as rows:
                for row in rows:
                    if self.failure=='hash' and ' WHERE batch_id <> %s' in text:
                        yield {'row_text':RejectedText(row['row_text'])}
                    elif self.failure=='interrupt':raise KeyboardInterrupt()
                    elif self.failure=='deadline':
                        clock[0]+=0.01;yield row
                    else:yield row
    try:
        conn.rollback();conn.cursor_factory=FailureCursor
        # Rejection during the post-insert scan must unwind the active result and
        # abort all3 artifacts/2 relationships, never reach a successful commit.
        with pytest.raises(StoreSafetyError,match='hash rejection'):
            with conn.transaction():
                conn.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
                operator.persist(conn,bundle,baseline,authority,confirm=True,fixture_url=DSN,scan_timings=events)
        assert conn.pgconn.transaction_status!=psycopg.pq.TransactionStatus.ACTIVE
        assert conn.execute('SELECT 1 AS n').fetchone()['n']==1
        assert prep.owned_state(conn,bundle) is None
        conn.rollback()
        for failure,error in (('sql',psycopg.errors.DivisionByZero),('timeout',psycopg.errors.QueryCanceled),
                              ('interrupt',KeyboardInterrupt),('deadline',StoreSafetyError)):
            FailureCursor.failure=failure;clock=[0.0]
            if failure=='timeout':conn.execute("SET LOCAL statement_timeout='10ms'")  # Negative fixture only.
            with monkeypatch.context() as patch:
                if failure=='deadline':patch.setattr(operator,'monotonic',lambda:clock[0])
                with pytest.raises(error):
                    operator.protected_state(conn,deadline=0.025 if failure=='deadline' else None)
            assert conn.pgconn.transaction_status!=psycopg.pq.TransactionStatus.ACTIVE
            conn.rollback();assert conn.execute('SELECT 1 AS n').fetchone()['n']==1;conn.rollback()
    finally:
        conn.cursor_factory=original_factory;conn.rollback()

    # Terminate ONLY the test connection's own backend to emulate a real lost
    # socket after INSERT. An unusable connection is closed; a new handle checks
    # that the server aborted its transaction and retained the prior graph.
    with _connect(DSN,autocommit=True) as control:
        prep.require_fixture_endpoint(control,DSN)
        class LostSocketCursor(Cursor):
            def stream(self,statement,params=None,*,size=1,**kwargs):
                with closing(super().stream(statement,params,size=1,**kwargs)) as rows:
                    for row in rows:
                        if ' WHERE batch_id <> %s' in statement.as_string():
                            control.execute('SELECT pg_terminate_backend(%s)',(self.connection.info.backend_pid,))
                            raise psycopg.OperationalError('injected fixture socket loss')
                        yield row
        broken=_connect(DSN,autocommit=False)
        try:
            prep.require_fixture_connection(broken,DSN)
            with pytest.raises(psycopg.OperationalError):
                with broken:
                    broken.cursor_factory=LostSocketCursor
                    broken.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
                    broken.execute("SET LOCAL timezone='UTC'")
                    operator.persist(broken,bundle,baseline,authority,confirm=True,fixture_url=DSN)
        finally:broken.close()
        assert broken.closed
    assert prep.owned_state(conn,bundle) is None
    assert prep.registry_row(conn,bundle['registry_key'])==bundle['prior_registry_row']
    conn.rollback()
    return {'deadline_between_real_rows_cleanup':True,'hash_rejection_after_insert_rollback':True,
            'sql_error_cleanup':True,'whole_statement_timeout_cleanup':True,'early_interrupt_cleanup':True,
            'lost_socket_connection_closed_transaction_aborted':True,'connection_reusable_after_nonfatal_rollback':True}


def test_candidate_bounded_persistence_capture_drift_idempotency_and_failed_transaction(monkeypatch):
    monkeypatch.setenv('NORMALIZED_VOTE_STORAGE', '1')
    monkeypatch.setenv('ENABLE_FIXTURE_FALLBACK', '0')
    seed_fixture(DSN)  # Same exact guarded DB name, separate CI job/service.
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=prep.ROOT, text=True).strip()
    bundle = prep.build_bundle(synthetic_candidate_approval(), source_commit_sha=head)
    with _connect(DSN, autocommit=False) as conn:
        before = public(conn)
        initial = operator.protected_state(conn)
        conn.rollback()
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        baseline = operator.capture_preflight(conn, bundle, fixture_url=DSN)
        assert conn.execute('SHOW lock_timeout').fetchone()['lock_timeout'] == '5s'
        assert conn.execute('SHOW statement_timeout').fetchone()['statement_timeout'] in ('1min', '60s')
        assert baseline['captured_at_utc'] == baseline['observed_started_at_utc']
        binding = {f'{s}_submanifest_sha256': runtime()[f'{s}_deployment']['submanifest_sha256'] for s in ('backend', 'frontend')}
        with pytest.raises(StoreSafetyError, match='IDs'):
            operator.resolve_ids(conn, bundle, binding, fixture_url=DSN)
        conn.rollback()
        authority = fixture_authority(bundle, baseline)
        with pytest.raises(StoreSafetyError, match='synthetic'):
            operator.persist(conn, bundle, baseline, authority, confirm=True)
        assert operator.protected_state(conn) == initial
        with pytest.raises(StoreSafetyError, match='injected'):
            with conn.transaction():
                operator.persist(conn, bundle, baseline, authority, confirm=True, fixture_url=DSN, fault_after=True)
        assert operator.protected_state(conn) == initial
        with conn.transaction(force_rollback=True):
            conn.execute("UPDATE editorial_publication_registry SET publication_metadata_jsonb=publication_metadata_jsonb || '{\"operator_drift\":true}'::jsonb WHERE issue_id='EDUCATION_WORKFORCE'")
            with pytest.raises(StoreSafetyError, match='registry drift'):
                operator.persist(conn, bundle, baseline, authority, confirm=True, fixture_url=DSN)
        prove_volume_transport(conn, bundle, monkeypatch)
        failures=prove_stream_failures(conn,bundle,baseline,authority,monkeypatch)
        result = operator.persist(conn, bundle, baseline, authority, confirm=True, fixture_url=DSN)
        assert result['writes'] == operator.CAPS and result['registry_unchanged'] is True
        assert operator.protected_state(conn, exclude_batch_id=result['batch_id']) == initial
        assert public(conn) == before
        repeat = operator.persist(conn, bundle, baseline, authority, confirm=True, fixture_url=DSN)
        assert repeat['status'] == 'ALREADY_PERSISTED' and not any(repeat['writes'].values())
        with conn.transaction(force_rollback=True):
            conn.execute('UPDATE editorial_artifact_batches SET manifest_sha256=%s WHERE batch_id=%s', ('0' * 64, result['batch_id']))
            with pytest.raises(StoreSafetyError, match='ownership differs'):
                operator.persist(conn, bundle, baseline, authority, confirm=True, fixture_url=DSN)
        conn.commit()
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        ws = operator.resolve_ids(conn, bundle, binding, fixture_url=DSN)
        assert ws['subject']['proposed_new']['artifact_id'] == result['artifact_ids'][bundle['proposed_new']['natural_key']]
        assert ws['subject']['expected_old']['artifact_id'] == 245
        assert ws['subject']['stable_production_baseline']['prior_registry_row'] == bundle['prior_registry_row']
        assert public(conn) == before
        proof = {'code_head': head, 'disposable_only': True, 'production_execution_authorized': False,
                 'candidate_approval': bundle['candidate_approval'], 'persistence_authority': authority,
                 'preflight': baseline, 'persistence': result, 'id_capture_write_set': ws,
                 'idempotent_repeat': repeat, 'before': before, 'after_persistence': public(conn),
                 'registry_unchanged': True, 'failed_transaction_rollback': True,
                 'synthetic_default_rejected': True, 'execution_limits': operator.LIMITS,
                 'observation_window_preserved': True, 'transaction_wait_limits_verified': True}
        proof['stream_failure_cleanup']=failures
        proof['client_libpq_version']=psycopg.pq.version()
        if folder := os.getenv('EDUCATION79_OPERATOR_PROOF_DIR'):
            path = Path(folder);path.mkdir(parents=True, exist_ok=True)
            (path / 'operator-proof.json').write_text(json.dumps(proof, sort_keys=True, indent=2) + '\n', encoding='utf-8')
