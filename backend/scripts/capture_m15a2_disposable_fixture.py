"""Read-only, bounded public-data snapshot for the M15A.2 disposable proof."""
import gzip
import json
from pathlib import Path
from scripts.foushee_m15a2_core_repair import (
    MEMBER, IDS, DIRECTORY, rows, require, load, _bill_key_from_ref, source_facts,
)


def capture(conn):
    require(conn.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on', 'fixture capture requires READ ONLY')
    data={}
    data['legislators']=rows(conn,'SELECT * FROM legislators ORDER BY id')
    mid=next(r['id'] for r in data['legislators'] if r['bioguide_id']==MEMBER)
    data['roll_calls']=rows(conn,"""SELECT rc.* FROM roll_calls rc
        WHERE rc.id IN (SELECT roll_call_id FROM votes_cast WHERE legislator_id=%s)
        OR (rc.chamber='house' AND rc.congress=119 AND rc.rollcall_number=ANY(%s)) ORDER BY rc.id""",
        (mid,sorted({int(a.rsplit(':',1)[1]) for a in IDS})))
    roll_ids=[r['id'] for r in data['roll_calls']]
    collision_ids=[r['id'] for r in data['roll_calls'] if r['congress']==119 and r['rollcall_number'] in {int(a.rsplit(':',1)[1]) for a in IDS}]
    for table in ('votes_cast','vote_contexts'):
        data[table]=rows(conn,f'SELECT * FROM {table} WHERE (legislator_id=%s AND roll_call_id=ANY(%s)) OR roll_call_id=ANY(%s) ORDER BY roll_call_id,legislator_id',(mid,roll_ids,collision_ids))
    for table in ('vote_classifications','vote_interpretations','senate_amendment_references'):
        data[table]=rows(conn,f'SELECT * FROM {table} WHERE roll_call_id=ANY(%s) ORDER BY roll_call_id',(roll_ids,))
    facts=source_facts(load(DIRECTORY/'source_manifest.json'),DIRECTORY/'official_sources.zip')
    keys=sorted({_bill_key_from_ref(r['bill_ref']) for r in facts['roll_calls']})
    placeholders=','.join(['(%s,%s,%s)']*len(keys))
    data['bills']=rows(conn,f'SELECT * FROM bills WHERE id=ANY(%s) OR (congress,bill_type,bill_number) IN ({placeholders}) ORDER BY id',
                       ([r['bill_id'] for r in data['roll_calls'] if r['bill_id'] is not None],*(x for k in keys for x in k)))
    data['fingerprints']=rows(conn,'SELECT * FROM fingerprints WHERE legislator_id=%s ORDER BY id',(mid,))
    data['editorial_publication_registry']=rows(conn,'SELECT * FROM editorial_publication_registry WHERE member_bioguide_id=%s ORDER BY issue_id',(MEMBER,))
    roots=[r['artifact_id'] for r in data['editorial_publication_registry']]
    data['editorial_artifact_relationships']=rows(conn,'SELECT * FROM editorial_artifact_relationships WHERE parent_artifact_id=ANY(%s) ORDER BY parent_artifact_id,relationship_type,ordinal,child_artifact_id',(roots,))
    artifact_ids=sorted(set(roots+[r['child_artifact_id'] for r in data['editorial_artifact_relationships']]))
    data['editorial_artifact_versions']=rows(conn,'''WITH RECURSIVE required AS (
        SELECT * FROM editorial_artifact_versions WHERE artifact_id=ANY(%s)
        UNION SELECT a.* FROM editorial_artifact_versions a JOIN required r
          ON a.artifact_id=r.supersedes_artifact_id)
        SELECT * FROM required ORDER BY artifact_id''',(artifact_ids,))
    batches=sorted({r['batch_id'] for r in data['editorial_artifact_versions']})
    data['editorial_artifact_batches']=rows(conn,'SELECT * FROM editorial_artifact_batches WHERE batch_id=ANY(%s) ORDER BY batch_id',(batches,))
    require(all(len(v)<=50000 for v in data.values()),'fixture exceeds bounded row cap')
    return {'schema_version':'m15a2_disposable_public_data_v1','production_database_write':False,'tables':data}


def write_fixture(path,body):
    raw=(json.dumps(body,sort_keys=True,separators=(',',':'))+'\n').encode()
    Path(path).write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
