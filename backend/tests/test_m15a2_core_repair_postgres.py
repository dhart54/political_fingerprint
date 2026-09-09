"""Real PostgreSQL proof using a bounded snapshot of public production facts."""
import copy
import gzip
import json
import os
from urllib.parse import urlsplit

import pytest
from psycopg import sql
from fastapi.testclient import TestClient

from scripts import foushee_m15a2_core_repair as repair
from scripts.editorial_artifact_store import StoreSafetyError, _connect

DSN=os.getenv('M15A2_DISPOSABLE_DATABASE_URL')
pytestmark=pytest.mark.skipif(not DSN,reason='dedicated M15A2 disposable PostgreSQL required')


def prepare_database():
    target=urlsplit(DSN)
    assert target.hostname in ('localhost','127.0.0.1') and target.path=='/pf_m15a2_repair'
    fixture=json.loads(gzip.decompress((repair.DIRECTORY/'disposable_baseline.json.gz').read_bytes()))
    with _connect(DSN,autocommit=True) as conn:
        conn.execute('DROP SCHEMA public CASCADE');conn.execute('CREATE SCHEMA public')
        conn.execute("""DO $$ BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='anon') THEN CREATE ROLE anon; END IF;
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='authenticated') THEN CREATE ROLE authenticated; END IF;
            END $$""")
        for path in sorted((repair.BACKEND/'migrations').glob('*.sql')):
            conn.execute(path.read_text(encoding='utf-8-sig'))
        tables=fixture['tables']
        order=('legislators','bills','roll_calls','votes_cast','vote_contexts','vote_classifications',
               'vote_interpretations','senate_amendment_references','fingerprints',
               'editorial_artifact_batches','editorial_artifact_versions',
               'editorial_artifact_relationships','editorial_publication_registry')
        with conn.transaction():
            conn.execute("SET LOCAL timezone='UTC'")
            # Replay existing accepted production rows, without synthesizing authority.
            for table in order:
                conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(sql.Identifier(table)))
                for row in tables[table]:repair.insert_row(conn,table,row)
                conn.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER USER').format(sql.Identifier(table)))
            for table in order:
                columns=conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s AND column_default LIKE 'nextval(%%)'",(table,)).fetchall()
                for c in columns:
                    column=c['column_name'];sequence=conn.execute('SELECT pg_get_serial_sequence(%s,%s) AS seq',(table,column)).fetchone()['seq']
                    maximum=conn.execute(sql.SQL('SELECT max({}) AS maximum FROM {}').format(sql.Identifier(column),sql.Identifier(table))).fetchone()['maximum']
                    conn.execute('SELECT setval(%s,%s,true)',(sequence,max(1,maximum or 1)))


@pytest.fixture(scope='module')
def database():
    prepare_database()
    yield


@pytest.fixture
def conn(database):
    with _connect(DSN,autocommit=True) as connection:
        connection.execute("SET timezone='UTC'")
        yield connection


@pytest.fixture
def bundle():
    return repair.load(repair.DIRECTORY/'repair_bundle.json')


def scoped_state(conn):
    return {t:repair.fingerprint(conn,t) for t in ('legislators','bills','roll_calls',*repair.LINKED,*repair.EDITORIAL)}


def test_production_shaped_lifecycle_and_http(conn,bundle,monkeypatch):
    monkeypatch.setenv('ENABLE_FIXTURE_FALLBACK','0')
    assert repair.preflight(conn,bundle)=='READY'
    baseline=scoped_state(conn);before=repair.public_state(conn,False)
    assert before['119']['details'][repair.EDU]['review_accounting']==dict(available_action_count=25,reviewed_action_count=17,not_yet_reviewed_action_count=8)
    from app.main import app
    with repair.public_reads_in_transaction(conn),TestClient(app) as client:
        assert client.get(f'/legislators/{repair.EXTERNAL_MEMBER}/positions/{repair.NS}/evidence?scope=119').status_code==503
        assert client.get(f'/legislators/{repair.EXTERNAL_MEMBER}/positions/{repair.ENV}/evidence?scope=all').status_code==503
    receipt=repair.apply(conn,bundle)
    assert receipt['writes']==repair.CAPS
    after=repair.public_state(conn,True);repair.invariant_public(before,after)
    with repair.public_reads_in_transaction(conn),TestClient(app) as client:
        for scope in ('119','all'):
            assert client.get(f'/legislators/{repair.EXTERNAL_MEMBER}/positions?scope={scope}').status_code==200
            for domain in (repair.NS,repair.ENV):
                assert client.get(f'/legislators/{repair.EXTERNAL_MEMBER}/positions/{domain}/evidence?scope={scope}').status_code==200
    stable=scoped_state(conn);repeat=repair.apply(conn,bundle)
    assert repeat=={'status':'ALREADY_APPLIED','writes':{k:0 for k in repair.CAPS}}
    assert scoped_state(conn)==stable
    result=repair.rollback(conn,bundle,receipt)
    assert result['restored_baseline'] and scoped_state(conn)==baseline
    assert repair.public_state(conn,False)==before


@pytest.mark.parametrize('stage',['bills','roll_calls','votes_cast','vote_contexts','public_postconditions','ownership_receipt'])
def test_each_fault_restores_baseline(conn,bundle,stage):
    before=scoped_state(conn)
    with pytest.raises(StoreSafetyError,match='injected failure'):
        repair.apply(conn,bundle,fault_after=stage)
    assert scoped_state(conn)==before
    assert repair.preflight(conn,bundle)=='READY'


@pytest.mark.parametrize('kind',['core','core_and_vote','conflicting_vote','bill','collision','collision_vote','dependency','publication','member','schema'])
def test_partial_conflicting_and_protected_drift(conn,bundle,kind):
    before=scoped_state(conn)
    with conn.transaction(force_rollback=True):
        if kind in ('core','core_and_vote','conflicting_vote'):
            r=next(r for r in bundle['facts']['roll_calls'] if r['bill_ref'].endswith('_hjres_35'))
            b=next(b for b in bundle['baseline']['guard']['reused_bills'] if b['bill_type']=='hjres' and b['bill_number']==35)
            record={k:r[k] for k in ('chamber','congress','session','rollcall_number','vote_date','question','description','source_url')}
            record['bill_id']=b['id'];inserted=repair.insert_row(conn,'roll_calls',record)
            if kind!='core':repair.insert_row(conn,'votes_cast',dict(roll_call_id=inserted['id'],legislator_id=bundle['baseline']['guard']['member']['id'],position='yea' if kind=='conflicting_vote' else 'nay'))
        elif kind=='bill':
            b=bundle['facts']['bills'][0];repair.insert_row(conn,'bills',{k:v for k,v in b.items() if k!='id'})
        elif kind=='collision':
            conn.execute("UPDATE roll_calls SET description=description||' drift' WHERE id=%s",(bundle['baseline']['guard']['protected_other_session_rows'][0]['id'],))
        elif kind=='dependency':
            conn.execute("UPDATE bills SET title=title||' drift' WHERE id=%s",(bundle['baseline']['guard']['reused_bills'][0]['id'],))
        elif kind=='collision_vote':
            conn.execute("UPDATE votes_cast SET position=CASE WHEN position='yea' THEN 'nay'::vote_position ELSE 'yea'::vote_position END WHERE id=(SELECT id FROM votes_cast WHERE roll_call_id=%s ORDER BY id LIMIT 1)",
                         (bundle['baseline']['guard']['protected_other_session_rows'][0]['id'],))
        elif kind=='member':
            conn.execute("UPDATE legislators SET name_display=name_display||' drift' WHERE id=%s",(bundle['baseline']['guard']['member']['id'],))
        elif kind=='schema':
            conn.execute('CREATE TABLE unexpected_dependents (roll_id bigint REFERENCES roll_calls(id) ON DELETE CASCADE)')
        else:
            conn.execute('ALTER TABLE editorial_publication_registry DISABLE TRIGGER USER')
            conn.execute("UPDATE editorial_publication_registry SET deactivated_at=now() WHERE member_bioguide_id='F000477' AND issue_id=%s",(repair.NS,))
            conn.execute('ALTER TABLE editorial_publication_registry ENABLE TRIGGER USER')
        with pytest.raises(StoreSafetyError,match='PARTIAL_OR_DRIFTED'):repair.apply(conn,bundle)
    assert scoped_state(conn)==before


def test_rollback_rejects_changed_ownership_and_new_dependents(conn,bundle):
    baseline=scoped_state(conn)
    receipt=repair.apply(conn,bundle)
    altered=copy.deepcopy(receipt)
    altered['inserted']['bills'][0]=bundle['baseline']['guard']['reused_bills'][0]
    repair.seal(altered,'receipt_sha256')
    with pytest.raises(StoreSafetyError,match='ownership target differs'):
        repair.rollback(conn,bundle,altered)
    with conn.transaction(force_rollback=True):
        conn.execute("UPDATE roll_calls SET description=description||' changed' WHERE id=%s",(receipt['inserted']['roll_calls'][0]['id'],))
        with pytest.raises(StoreSafetyError):repair.rollback(conn,bundle,receipt)
    with conn.transaction(force_rollback=True):
        conn.execute("INSERT INTO vote_classifications(roll_call_id,is_eligible,eligibility_reason,classification_version) VALUES (%s,false,'test','test')",(receipt['inserted']['roll_calls'][0]['id'],))
        with pytest.raises(StoreSafetyError):repair.rollback(conn,bundle,receipt)
    repair.rollback(conn,bundle,receipt)
    assert scoped_state(conn)==baseline


def test_receipt_persistence_failure_aborts_before_commit(conn,bundle):
    baseline=scoped_state(conn)
    def fail(_):raise OSError('receipt storage unavailable')
    with pytest.raises(OSError,match='receipt storage'):
        repair.apply(conn,bundle,persist_receipt=fail)
    assert scoped_state(conn)==baseline


def test_durable_receipt_precedes_commit_and_owns_rollback(conn,bundle,tmp_path):
    baseline=scoped_state(conn);path=tmp_path/'ownership.json'
    def persist(receipt):
        with _connect(DSN,autocommit=True) as observer:
            assert repair.target_rolls(observer)==[]  # Inserts are not committed yet.
        repair.durable_receipt(path,receipt)
    receipt=repair.apply(conn,bundle,persist_receipt=persist)
    assert repair.load(path)==receipt
    with pytest.raises(FileExistsError):repair.durable_receipt(path,receipt)
    repair.rollback(conn,bundle,repair.load(path))
    assert scoped_state(conn)==baseline


def test_unrelated_append_does_not_freeze_production(conn,bundle):
    with conn.transaction(force_rollback=True):
        repair.insert_row(conn,'bills',dict(congress=120,bill_type='hr',bill_number=99999,title='Unrelated append',summary='',committee=None,subjects=[]))
        baseline=scoped_state(conn)
        assert repair.preflight(conn,bundle)=='READY'
        receipt=repair.apply(conn,bundle)
        repair.rollback(conn,bundle,receipt)
        assert scoped_state(conn)==baseline


def test_disposable_cli_reuses_receipt_for_idempotency(conn,bundle,monkeypatch,tmp_path,capsys):
    monkeypatch.setenv('M15A2_DISPOSABLE_DATABASE_URL',DSN)
    baseline=scoped_state(conn);path=tmp_path/'cli-receipt.json'
    args=['--target','disposable','--confirm-bundle-digest',bundle['bundle_sha256'],'--receipt',str(path)]
    assert repair.main(['apply',*args])==0
    first=path.read_bytes()
    assert json.loads(capsys.readouterr().out)['status']=='APPLIED'
    assert repair.main(['apply',*args])==0
    assert json.loads(capsys.readouterr().out)['status']=='ALREADY_APPLIED'
    assert path.read_bytes()==first
    assert repair.main(['rollback',*args])==0
    assert json.loads(capsys.readouterr().out)['status']=='ROLLED_BACK'
    assert scoped_state(conn)==baseline
