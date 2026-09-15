"""Bounded READ ONLY snapshot for actual M15B persistence preparation."""
import argparse
import gzip
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
ROOT = BACKEND.parent
OUT = ROOT/'docs/editorial/publication_replacements/m15b_authorization'
from app.editorial_presentations.compiler import canonical_digest as digest
from app.editorial_artifacts.repository import EditorialArtifactRepository
from app.editorial_presentations.publication_replacement_store_v2r import bound_artifact, registry_row
from scripts.foushee_education_workforce_m14h_replacement import target_identity


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def capture(conn, identity):
    assert conn.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
    prepared=load(ROOT/'docs/editorial/publication_replacements/m15b_preparation/approved_semantics_preparation.json')
    def rows(query, args=()):
        return json.loads(json.dumps(conn.execute(query,args).fetchall(),default=str))
    registry=rows("SELECT * FROM editorial_publication_registry WHERE member_bioguide_id='F000477' ORDER BY issue_id")
    eligible=EditorialArtifactRepository(conn).publication_selector()
    assert len(registry)==4 and all(any(r['artifact_id']==e['artifact_id'] for e in eligible) for r in registry)
    verified={}
    for issue,item in prepared['replacements'].items():
        old=bound_artifact(conn,item['expected_old'],item['registry_key'])
        prior=registry_row(conn,item['registry_key'])
        assert prior['artifact_id']==old['artifact_id'], 'material old-pointer drift'
        verified[issue]={'registry_row':prior,'expected_old':item['expected_old']}
    tables={}
    tables['legislators']=rows("SELECT * FROM legislators WHERE bioguide_id='F000477'")
    member=tables['legislators'][0]['id']
    # Scope headers include the database-wide eligible roll count. Include those
    # source rows too, without acquiring another member's votes or interpretation.
    tables['roll_calls']=rows('''SELECT * FROM roll_calls WHERE
        id IN (SELECT roll_call_id FROM votes_cast WHERE legislator_id=%s)
        OR (congress IN (118,119) AND id IN (SELECT roll_call_id FROM vote_classifications WHERE is_eligible=TRUE))
        ORDER BY id''',(member,))
    roll_ids=[r['id'] for r in tables['roll_calls']]
    for table in ('votes_cast','vote_contexts'):
        tables[table]=rows(f'SELECT * FROM {table} WHERE legislator_id=%s AND roll_call_id=ANY(%s) ORDER BY roll_call_id',(member,roll_ids))
    for table in ('vote_classifications','vote_interpretations','senate_amendment_references'):
        tables[table]=rows(f'SELECT * FROM {table} WHERE roll_call_id=ANY(%s) ORDER BY roll_call_id',(roll_ids,))
    tables['bills']=rows('SELECT * FROM bills WHERE id=ANY(%s) ORDER BY id',([r['bill_id'] for r in tables['roll_calls'] if r['bill_id']],))
    tables['fingerprints']=rows('SELECT * FROM fingerprints WHERE legislator_id=%s ORDER BY id',(member,))
    roots=[r['artifact_id'] for r in registry]
    # Existing immutable supersedes/provenance graph only, not a global artifact dump.
    tables['editorial_artifact_versions']=rows('''WITH RECURSIVE ids(id) AS (
        SELECT unnest(%s::bigint[]) UNION SELECT edge.child FROM ids
        JOIN (SELECT parent_artifact_id AS parent,child_artifact_id AS child FROM editorial_artifact_relationships
              UNION SELECT artifact_id,supersedes_artifact_id FROM editorial_artifact_versions WHERE supersedes_artifact_id IS NOT NULL) edge ON edge.parent=ids.id)
        SELECT * FROM editorial_artifact_versions WHERE artifact_id IN (SELECT id FROM ids) ORDER BY artifact_id''',(roots,))
    artifact_ids=[r['artifact_id'] for r in tables['editorial_artifact_versions']]
    tables['editorial_artifact_relationships']=rows('SELECT * FROM editorial_artifact_relationships WHERE parent_artifact_id=ANY(%s) ORDER BY parent_artifact_id,relationship_type,ordinal,child_artifact_id',(artifact_ids,))
    tables['editorial_artifact_batches']=rows('SELECT * FROM editorial_artifact_batches WHERE batch_id=ANY(%s) ORDER BY batch_id',([r['batch_id'] for r in tables['editorial_artifact_versions']],))
    tables['editorial_publication_registry']=registry
    assert all(len(v)<=50000 for v in tables.values()), 'bounded snapshot cap exceeded'
    from scripts.foushee_m15a2_core_repair import public_reads_in_transaction
    from app.api import positions, editorial_presentations
    public={}
    with public_reads_in_transaction(conn):
        for scope in ('119','all'):
            public[scope]={'presentations':editorial_presentations.get_editorial_presentations('leg_valerie_p_foushee',scope,None),
                'discovery':positions.get_legislator_positions('leg_valerie_p_foushee',scope,None),
                'details':{r['issue_id']:positions.get_legislator_position_evidence('leg_valerie_p_foushee',r['issue_id'],scope,None) for r in registry}}
    public=json.loads(json.dumps(public,default=str))
    fixture={'tables':tables}
    absent={}
    for issue,item in prepared['replacements'].items():
        keys=[item['proposed_new']['natural_key'],*[v['natural_key'] for k,v in item['additive_graph'].items() if k!='relationships']]
        absent[issue]=rows('SELECT artifact_id,natural_key,artifact_version,content_sha256 FROM editorial_artifact_versions WHERE natural_key=ANY(%s)',(keys,))
    report={'captured_at_utc':datetime.now(timezone.utc).isoformat(),'transaction_read_only':True,
        'production_writes':False,'production_target_identity_sha256':identity,'verified':verified,
        'existing_proposed_artifacts':absent,'fixture_sha256':digest(fixture),
        'table_counts':{t:len(r) for t,r in tables.items()},'public_before_sha256':digest(public)}
    return report,fixture,public


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-path',type=Path,required=True)
    args=parser.parse_args()
    from dotenv import dotenv_values
    import psycopg
    from psycopg.rows import dict_row
    url=dotenv_values(args.env_path).get('DATABASE_URL')
    try:
        identity=target_identity(url,'production')
        with psycopg.connect(url,connect_timeout=15,options='-c default_transaction_read_only=on -c statement_timeout=20000',row_factory=dict_row) as conn:
            conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            report,fixture,public=capture(conn,identity)
    except Exception as error:
        # Connection errors can contain credentials/host details; report type only.
        raise SystemExit('Read-only capture failed: '+type(error).__name__) from None
    OUT.mkdir(parents=True,exist_ok=True)
    for name,value in [('production_baseline.json',report)]:
        (OUT/name).write_text(json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'disposable_baseline.json.gz').write_bytes(gzip.compress(json.dumps(fixture,sort_keys=True,ensure_ascii=False).encode(),mtime=0))
    (OUT/'public_before.json.gz').write_bytes(gzip.compress(json.dumps(public,sort_keys=True,ensure_ascii=False).encode(),mtime=0))
    print(json.dumps({k:report[k] for k in ('captured_at_utc','transaction_read_only','production_writes','fixture_sha256')}))


if __name__=='__main__': main()
