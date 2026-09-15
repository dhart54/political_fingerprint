"""Exact production-data parity and scale proof, exclusively on loopback PostgreSQL."""
import copy
import gzip
import hashlib
import json
import os
import statistics
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

import psycopg
import pytest
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.etl import normalized_vote_storage as norm
from scripts.foushee_m15a2_core_repair import public_reads_in_transaction

BACKEND=Path(__file__).resolve().parents[1]
FIXTURE=BACKEND/'tests/fixtures/normalized_vote_storage_baseline.jsonl.gz'
MIGRATION=BACKEND/'migrations/staged/normalize_vote_storage.sql'
SEQUENCES=json.loads((BACKEND/'tests/fixtures/normalized_vote_storage_sequences.json').read_text(encoding='utf-8'))
DSN=os.getenv('NORMALIZED_STORAGE_DISPOSABLE_DATABASE_URL')
pytestmark=pytest.mark.skipif(not DSN,reason='dedicated loopback PostgreSQL required')


def load_fixture():
    tables={}
    with gzip.open(FIXTURE,'rt',encoding='utf-8') as stream:
        metadata=json.loads(next(stream))['metadata']
        for line in stream:
            header=json.loads(line);rows=[]
            for line in stream:
                row=json.loads(line)
                if row is None:break
                rows.append(row)
            tables[header['table']]={'columns':header['columns'],'rows':rows}
    return metadata,tables


def reset_database(conn,tables):
    conn.execute('DROP SCHEMA public CASCADE');conn.execute('CREATE SCHEMA public')
    conn.execute("DO $$ BEGIN IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='anon') THEN CREATE ROLE anon; END IF; IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='authenticated') THEN CREATE ROLE authenticated; END IF; END $$")
    for path in sorted((BACKEND/'migrations').glob('*.sql')):
        conn.execute(path.read_text(encoding='utf-8-sig'))
    shared_table=tables['shared_context_snapshot']
    shared={r[0]:dict(zip(shared_table['columns'],r)) for r in shared_table['rows']}
    with conn.transaction():
        conn.execute("SET LOCAL session_replication_role='replica'")
        for name,table in tables.items():
            if name=='shared_context_snapshot':continue
            columns=table['columns']
            if name=='vote_contexts':columns=[*columns,*norm.SHARED]
            json_cols={r['column_name'] for r in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s AND data_type IN ('json','jsonb')",(name,))}
            with conn.cursor().copy(sql.SQL('COPY public.{} ({}) FROM STDIN').format(sql.Identifier(name),sql.SQL(',').join(map(sql.Identifier,columns)))) as writer:
                for values in table['rows']:
                    if name=='vote_contexts':values=[*values,*[shared[values[0]][f] for f in norm.SHARED]]
                    writer.write_row([Jsonb(v) if c in json_cols and v is not None else v for c,v in zip(columns,values)])
    for name,value in SEQUENCES['sequences'].items():
        conn.execute('SELECT setval(%s,%s,%s)',('public.'+name,value['last_value'],value['is_called']))
    conn.execute('ANALYZE')


def sequence_state(conn):
    return {name:conn.execute(sql.SQL('SELECT last_value,is_called FROM public.{}').format(sql.Identifier(name))).fetchone() for name in SEQUENCES['sequences']}


def digest_tables(conn,tables):
    result={}
    for name,table in tables.items():
        if name=='shared_context_snapshot':continue
        columns=table['columns']
        if name=='vote_contexts':columns=[*columns,*norm.SHARED]
        # Compare every original column, including original timestamps. Added
        # normalized physical columns on roll_calls are not old logical fields.
        query=sql.SQL('COPY (SELECT {} FROM public.{} ORDER BY 1,2) TO STDOUT').format(sql.SQL(',').join(map(sql.Identifier,columns)),sql.Identifier(name))
        digest=hashlib.sha256()
        with conn.cursor().copy(query) as reader:
            for chunk in reader:digest.update(chunk)
        result[name]=digest.hexdigest()
    return result


def public_outputs(conn,member_names):
    from app.api import positions,editorial_presentations,precomputed
    from app.classification.classifier import ISSUE_DOMAINS
    outputs={}
    from fastapi import HTTPException
    def invoke(function,*args,**kwargs):
        try:return {'status':200,'body':function(*args,**kwargs)}
        except HTTPException as error:
            assert error.status_code<500, 'baseline/service failure must not masquerade as parity'
            return {'status':error.status_code,'body':{'detail':error.detail},'headers':error.headers}
    with public_reads_in_transaction(conn):
        for name in member_names:
            external=precomputed._to_external_legislator_id(name)
            for scope in ('119','118','all'):
                prefix=external+':'+scope
                outputs[prefix+':positions']=invoke(positions.get_legislator_positions,external,scope,None)
                outputs[prefix+':editorial']=invoke(editorial_presentations.get_editorial_presentations,external,scope,None)
                outputs[prefix+':fingerprint']=invoke(precomputed.get_fingerprint_response,legislator_id=external,comparison_party='ALL',scope=scope)
                for domain in ISSUE_DOMAINS:
                    outputs[prefix+':'+domain]=invoke(positions.get_legislator_position_evidence,external,domain,scope,None)
            outputs[external+':summary']=invoke(precomputed.get_summary_response,legislator_id=external)
            outputs[external+':drift']=invoke(precomputed.get_drift_response,legislator_id=external)
    # JSON-normalize types only. No fields (including timestamps) are removed.
    return json.loads(json.dumps(outputs,default=str,sort_keys=True))


def benchmark(conn,member):
    queries={
      'member_history':('SELECT vc.roll_call_id,vc.position,c.party_vote_totals,c.context_source_list,c.member_party FROM votes_cast vc JOIN vote_contexts c USING(roll_call_id,legislator_id) WHERE vc.legislator_id=%s',(member,)),
      'issue_evidence':("SELECT rc.id,vc.position,c.party_vote_totals,c.context_source_list FROM votes_cast vc JOIN roll_calls rc ON rc.id=vc.roll_call_id JOIN vote_contexts c USING(roll_call_id,legislator_id) JOIN vote_classifications f ON f.roll_call_id=rc.id WHERE vc.legislator_id=%s AND f.primary_domain='EDUCATION_WORKFORCE' AND f.is_eligible",(member,)),
      'fingerprint':('SELECT f.primary_domain,count(*) FROM votes_cast v JOIN roll_calls r ON r.id=v.roll_call_id JOIN vote_classifications f ON f.roll_call_id=r.id WHERE v.legislator_id=%s AND f.is_eligible GROUP BY f.primary_domain',(member,)),
      'roll_lookup':('SELECT party_vote_totals,context_source_list,member_position FROM vote_contexts WHERE roll_call_id=(SELECT min(roll_call_id) FROM votes_cast WHERE legislator_id=%s)',(member,)),
      'batch_analysis':('SELECT legislator_id,sum(pg_column_size(party_vote_totals)),count(*) FROM vote_contexts WHERE legislator_id=ANY(%s) GROUP BY legislator_id',([member,1,2,3,4,5,6,7,8,9],))}
    result={}
    for name,(query,args) in queries.items():
        plans=[conn.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+query,args).fetchone()['QUERY PLAN'][0] for _ in range(5)]
        result[name]={'median_ms':statistics.median(p['Execution Time'] for p in plans), 'plan':plans[-1]}
    return result


def storage(conn):
    return conn.execute("SELECT pg_database_size(current_database()) database_bytes,pg_total_relation_size('vote_context_members') member_bytes,pg_relation_size('vote_context_members') member_heap,pg_indexes_size('vote_context_members') member_indexes,pg_total_relation_size('roll_calls') roll_bytes,pg_relation_size('roll_calls') roll_heap,pg_indexes_size('roll_calls') roll_indexes").fetchone()


def test_actual_full_population_parity_and_scale(monkeypatch):
    target=urlsplit(DSN)
    assert target.hostname in ('127.0.0.1','localhost') and target.path=='/pf_normalized_storage'
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()=='5c3bbf50327d3a531cec21518b9165b68f8d05a7866a20e3c3d421260a916f7d'
    monkeypatch.setenv('ENABLE_FIXTURE_FALLBACK','0')
    metadata,tables=load_fixture()
    assert len(tables['votes_cast']['rows'])==len(tables['vote_contexts']['rows'])==814963
    assert len(tables['shared_context_snapshot']['rows'])==2298 and metadata['shared_conflicts']==0
    with psycopg.connect(DSN,autocommit=True,row_factory=dict_row) as conn:
        conn.execute("SET timezone='UTC'")
        reset_database(conn,tables)
        print('BASELINE_RESTORED',flush=True)
        before=digest_tables(conn,tables)
        # A conflicting source value must abort before schema/data conversion.
        conn.execute('BEGIN')
        conn.execute("UPDATE vote_contexts SET party_vote_totals=party_vote_totals || '{\"normalization_conflict\":true}'::jsonb WHERE (roll_call_id,legislator_id)=(SELECT roll_call_id,min(legislator_id) FROM vote_contexts GROUP BY roll_call_id HAVING count(*)>1 ORDER BY roll_call_id LIMIT 1)")
        with pytest.raises(psycopg.errors.RaiseException,match='roll-level context ambiguity'):
            conn.execute(MIGRATION.read_text(encoding='utf-8'))
        conn.rollback()
        assert conn.execute("SELECT relkind FROM pg_class WHERE oid='vote_contexts'::regclass").fetchone()['relkind']=='r'
        assert digest_tables(conn,tables)==before
        names=[r['name_display'] for r in conn.execute("SELECT name_display FROM legislators WHERE bioguide_id IN (SELECT DISTINCT member_bioguide_id FROM editorial_artifact_versions WHERE member_bioguide_id IS NOT NULL) OR id IN (SELECT min(id) FROM legislators GROUP BY chamber,party) ORDER BY name_display")]
        member=conn.execute("SELECT id FROM legislators WHERE bioguide_id='F000477'").fetchone()['id']
        api_before=public_outputs(conn,names)
        performance_before=benchmark(conn,member)
        print('BASELINE_PARITY_CAPTURED',len(api_before),flush=True)
        shared_bytes=conn.execute(sql.SQL('SELECT {} FROM vote_contexts').format(sql.SQL(',').join(sql.SQL('sum(coalesce(pg_column_size({}),0)) AS {}').format(sql.Identifier(f),sql.Identifier(f)) for f in norm.SHARED))).fetchone()
        legacy_size=conn.execute("SELECT pg_database_size(current_database()) database_bytes,pg_total_relation_size('vote_contexts') context_bytes,pg_total_relation_size('roll_calls') roll_bytes").fetchone()
        from scripts.normalize_vote_storage import apply_disposable
        assert apply_disposable(conn)['status']=='NORMALIZED'
        assert apply_disposable(conn)['status']=='ALREADY_NORMALIZED'
        conn.execute('ANALYZE')
        after=digest_tables(conn,tables)
        assert before==after, 'complete original table/column parity'
        assert sequence_state(conn)==SEQUENCES['sequences']
        assert public_outputs(conn,names)==api_before, 'complete API JSON parity'
        physical=storage(conn)
        assert physical['database_bytes']<400000000
        # Preserve the source's other relation allocation conservatively instead
        # of attributing compacted votes_cast indexes to context normalization.
        projected_source_bytes=metadata['database_bytes']-510492672-1056768+physical['member_bytes']+physical['roll_bytes']
        assert projected_source_bytes<400000000
        assert conn.execute('SELECT count(*) n FROM vote_context_members').fetchone()['n']==814963
        assert conn.execute('SELECT count(*) n FROM votes_cast v LEFT JOIN roll_calls r ON r.id=v.roll_call_id LEFT JOIN legislators l ON l.id=v.legislator_id WHERE r.id IS NULL OR l.id IS NULL').fetchone()['n']==0
        assert conn.execute('SELECT count(*) n FROM roll_calls WHERE context_context_version IS NOT NULL').fetchone()['n']==2298
        assert not conn.execute("SELECT column_name FROM information_schema.columns WHERE table_name='vote_context_members' AND column_name=ANY(%s)",(list(norm.SHARED),)).fetchall()
        assert conn.execute('SELECT count(*) n FROM vote_context_members m LEFT JOIN roll_calls r ON r.id=m.roll_call_id WHERE r.context_context_version IS NULL').fetchone()['n']==0
        assert conn.execute("SELECT relrowsecurity FROM pg_class WHERE oid='vote_context_members'::regclass").fetchone()['relrowsecurity']
        for role in ('anon','authenticated'):
            assert not conn.execute("SELECT has_table_privilege(%s,'vote_context_members','SELECT') allowed",(role,)).fetchone()['allowed']
        sample=conn.execute('SELECT * FROM vote_contexts WHERE legislator_id=%s ORDER BY roll_call_id',(member,)).fetchall()
        monkeypatch.setenv('NORMALIZED_VOTE_STORAGE','1')
        with conn.transaction():
            with conn.cursor() as cursor:
                assert norm.write_contexts(cursor,sample)==0
                assert norm.write_contexts(cursor,sample)==0
        assert digest_tables(conn,tables)==after
        for field in ('party_vote_totals','context_source_list'):
            bad=copy.deepcopy(sample[:1]);bad[0][field]={'drift':True} if field=='party_vote_totals' else [{'drift':True}]
            with pytest.raises(ValueError,match='shared context drift'):
                with conn.transaction(),conn.cursor() as cursor:norm.write_contexts(cursor,bad)
        # New ingestion, repeated ingestion, compatibility CRUD and transaction
        # failure all exercise real normalized storage, not only the no-op path.
        with conn.transaction(force_rollback=True):
            raw=dict(conn.execute('SELECT * FROM roll_calls WHERE id=%s',(sample[0]['roll_call_id'],)).fetchone())
            raw={k:v for k,v in raw.items() if not k.startswith('context_')}
            raw['id']=-188;raw['rollcall_number']=999999
            with conn.cursor() as cursor:
                cursor.execute(sql.SQL('INSERT INTO roll_calls ({}) VALUES ({})').format(sql.SQL(',').join(map(sql.Identifier,raw)),sql.SQL(',').join(sql.Placeholder() for _ in raw)),tuple(raw.values()))
                incoming=conn.execute('SELECT * FROM vote_contexts WHERE roll_call_id=%s ORDER BY legislator_id LIMIT 3',(sample[0]['roll_call_id'],)).fetchall()
                incoming=[dict(row,roll_call_id=-188) for row in incoming]
                from app.etl import current_congress_refresh,senate_fact_import,senate_amendment_facts,seed
                roll_keys={'-188':'new'}
                bioguides={str(row['legislator_id']):str(row['legislator_id']) for row in incoming}
                member_ids={str(row['legislator_id']):row['legislator_id'] for row in incoming}
                args=(cursor,incoming,roll_keys,bioguides,{'new':-188},member_ids)
                assert current_congress_refresh._insert_vote_contexts(*args)==len(incoming)
                for producer in (current_congress_refresh,senate_fact_import,senate_amendment_facts):
                    assert producer._insert_vote_contexts(*args)==0
                seed._write_rows(cursor,insert_statement='',copy_statement='COPY vote_contexts (',rows=[tuple(row[k] for k in norm.LOGICAL) for row in incoming])
                assert conn.execute('SELECT count(*) n FROM roll_calls WHERE id=-188 AND context_context_version IS NOT NULL').fetchone()['n']==1
                actual=conn.execute('SELECT * FROM vote_contexts WHERE roll_call_id=-188 ORDER BY legislator_id').fetchall()
                for expected,got in zip(incoming,actual):
                    assert {k:got[k] for k in norm.LOGICAL}=={k:expected[k] for k in norm.LOGICAL}
                # Legacy one-row operators compose through the same governed view.
                conn.execute('DELETE FROM vote_contexts WHERE roll_call_id=-188 AND legislator_id=%s',(incoming[0]['legislator_id'],))
                row=incoming[0]
                cursor.execute(sql.SQL('INSERT INTO vote_contexts ({}) VALUES ({})').format(sql.SQL(',').join(map(sql.Identifier,norm.LOGICAL)),sql.SQL(',').join(sql.Placeholder() for _ in norm.LOGICAL)),tuple(Jsonb(row[k]) if k in ('party_vote_totals','context_source_list') else row[k] for k in norm.LOGICAL))
        assert digest_tables(conn,tables)==after, 'rollback restores complete original state'
        performance_after=benchmark(conn,member)
        # Absolute and relative bounds prevent tiny millisecond noise failing a
        # sound join while rejecting a major practical regression.
        for name in performance_before:
            assert performance_after[name]['median_ms']<=max(50,performance_before[name]['median_ms']*3), name
        # A fresh restore proves the proposed compact green end-state, including
        # functions/views/constraints, rather than assuming dump portability.
        restore_dsn=DSN.rsplit('/',1)[0]+'/pf_normalized_restore'
        subprocess.run(['createdb','--maintenance-db='+DSN,'pf_normalized_restore'],check=True,capture_output=True,timeout=30)
        with tempfile.TemporaryDirectory(prefix='normalized-storage-restore-') as directory:
            dump=Path(directory)/'normalized.dump'
            subprocess.run(['pg_dump','--dbname='+DSN,'--format=custom','--file='+str(dump)],check=True,capture_output=True,timeout=180)
            subprocess.run(['pg_restore','--dbname='+restore_dsn,'--clean','--if-exists','--no-owner',str(dump)],check=True,capture_output=True,timeout=180)
        with psycopg.connect(restore_dsn,autocommit=True,row_factory=dict_row) as restored:
            restored.execute("SET timezone='UTC'")
            restored.execute('ANALYZE')
            assert digest_tables(restored,tables)==after
            assert sequence_state(restored)==SEQUENCES['sequences']
            assert public_outputs(restored,names)==api_before
            restored_size=storage(restored)
            assert restored_size['database_bytes']<400000000
        report={'postgresql_version':conn.execute("SELECT current_setting('server_version') version").fetchone()['version'],'shared_field_datum_bytes':shared_bytes,'sequences_preserved':len(SEQUENCES['sequences']),'restore':restored_size,'source':metadata,'original_table_hashes':before,'table_count':len(before),'members':names,'complete_api_outputs':len(api_before),'api_sha256':hashlib.sha256(json.dumps(api_before,sort_keys=True).encode()).hexdigest(),'legacy':legacy_size,'normalized':physical,'projected_source_bytes':projected_source_bytes,'before_queries':performance_before,'after_queries':performance_after,'production_writes':False}
        print('NORMALIZED_STORAGE_PROOF '+json.dumps(report,default=str,sort_keys=True),flush=True)
