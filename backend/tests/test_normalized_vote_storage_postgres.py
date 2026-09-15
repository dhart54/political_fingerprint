"""Exact production-data parity and scale proof, exclusively on loopback PostgreSQL."""
import copy
import gzip
import hashlib
import json
import os
import statistics
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
    conn.execute('ANALYZE')


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
    with public_reads_in_transaction(conn):
        for name in member_names:
            external=precomputed._to_external_legislator_id(name)
            for scope in ('119','118','all'):
                prefix=external+':'+scope
                outputs[prefix+':positions']=positions.get_legislator_positions(external,scope,None)
                outputs[prefix+':editorial']=editorial_presentations.get_editorial_presentations(external,scope,None)
                outputs[prefix+':fingerprint']=precomputed.get_fingerprint_response(legislator_id=external,comparison_party='ALL',scope=scope)
                for domain in ISSUE_DOMAINS:
                    outputs[prefix+':'+domain]=positions.get_legislator_position_evidence(external,domain,scope,None)
            outputs[external+':summary']=precomputed.get_summary_response(legislator_id=external)
            outputs[external+':drift']=precomputed.get_drift_response(legislator_id=external)
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
    return conn.execute("SELECT pg_database_size(current_database()) database_bytes,pg_total_relation_size('vote_context_members') member_bytes,pg_total_relation_size('roll_calls') roll_bytes").fetchone()


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
        names=[r['name_display'] for r in conn.execute("SELECT name_display FROM legislators WHERE bioguide_id IN (SELECT DISTINCT member_bioguide_id FROM editorial_artifact_versions WHERE member_bioguide_id IS NOT NULL) OR id IN (SELECT min(id) FROM legislators GROUP BY chamber,party) ORDER BY name_display")]
        member=conn.execute("SELECT id FROM legislators WHERE bioguide_id='F000477'").fetchone()['id']
        api_before=public_outputs(conn,names)
        performance_before=benchmark(conn,member)
        print('BASELINE_PARITY_CAPTURED',len(api_before),flush=True)
        legacy_size=conn.execute("SELECT pg_database_size(current_database()) database_bytes,pg_total_relation_size('vote_contexts') context_bytes,pg_total_relation_size('roll_calls') roll_bytes").fetchone()
        from scripts.normalize_vote_storage import apply_disposable
        assert apply_disposable(conn)['status']=='NORMALIZED'
        assert apply_disposable(conn)['status']=='ALREADY_NORMALIZED'
        conn.execute('ANALYZE')
        after=digest_tables(conn,tables)
        assert before==after, 'complete original table/column parity'
        assert public_outputs(conn,names)==api_before, 'complete API JSON parity'
        physical=storage(conn)
        assert physical['database_bytes']<400000000
        assert conn.execute('SELECT count(*) n FROM vote_context_members').fetchone()['n']==814963
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
        performance_after=benchmark(conn,member)
        # Absolute and relative bounds prevent tiny millisecond noise failing a
        # sound join while rejecting a major practical regression.
        for name in performance_before:
            assert performance_after[name]['median_ms']<=max(50,performance_before[name]['median_ms']*3), name
        report={'source':metadata,'original_table_hashes':before,'table_count':len(before),'members':names,'complete_api_outputs':len(api_before),'api_sha256':hashlib.sha256(json.dumps(api_before,sort_keys=True).encode()).hexdigest(),'legacy':legacy_size,'normalized':physical,'before_queries':performance_before,'after_queries':performance_after,'production_writes':False}
        print('NORMALIZED_STORAGE_PROOF '+json.dumps(report,default=str,sort_keys=True),flush=True)
