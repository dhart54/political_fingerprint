from unittest.mock import patch
import hashlib,json
from pathlib import Path
import pytest
from scripts import green_vote_storage as g

BLUE='postgresql://postgres.wfhnmuxlbfpweupisfao:dummy@aws-1-us-east-1.pooler.supabase.com:5432/postgres'
GREEN='postgresql://postgres.yalpfkaxkxebwolhorha:dummy@aws-0-us-east-1.pooler.supabase.com:5432/postgres'

def test_distinct_targets_are_exact():
    g.require_targets(BLUE,GREEN)
    for bad in (BLUE,GREEN.replace('yalpfkaxkxebwolhorha','unknown'),GREEN.replace('aws-0','aws-1'),GREEN.replace(':5432',':6543')):
        with pytest.raises(ValueError):g.require_targets(BLUE,bad)

def test_confirmation_precedes_any_connection_or_manifest_read():
    with patch.object(g,'read_manifest') as read,patch.object(g,'preflight') as pre:
        with pytest.raises(ValueError,match='explicit green-load confirmation required'):
            g.execute('load',BLUE,GREEN,Path('absent'),'bad',Path('absent'))
        read.assert_not_called();pre.assert_not_called()

def test_preflight_and_exact_retry_never_execute_write():
    for operation,status in [('preflight','EMPTY_GREEN'),('load','EXACT_NORMALIZED_STATE')]:
        with patch.object(g,'read_manifest',return_value={}),patch.object(g,'preflight',return_value={'status':status}),patch.object(g.subprocess,'run') as run:
            assert g.execute(operation,BLUE,GREEN,Path('m'),'hash',Path('pg'),True)['writes']==0
            run.assert_not_called()

def test_mismatched_package_rejected(tmp_path):
    m={'main_sha':g.MAIN,'blue_ref':g.BLUE,'green_ref':g.GREEN,'mode':g.MODE,'files':{}}
    for name in ['capture.json','normalized.dump','normalized.sql','load-guard.sql','permissions.sql']:
        (tmp_path/name).write_text('bound');m['files'][name]=g.sha(tmp_path/name)
    (tmp_path/'capture.json').write_text('{}');m['files']['capture.json']=g.sha(tmp_path/'capture.json');m['source']={'blue_dump_sha256':'dump'}
    (tmp_path/'capture.json').write_text(json.dumps(m['source']));m['files']['capture.json']=g.sha(tmp_path/'capture.json')
    (tmp_path/'source-schema.json').write_text(json.dumps({'source_dump_sha256':'dump','schema':{}}));m['files']['source-schema.json']=g.sha(tmp_path/'source-schema.json');m['source_schema_digest']=g.digest({})
    p=tmp_path/'manifest.json';p.write_text(json.dumps(m));sealed=g.sha(p)
    assert g.read_manifest(p,sealed)==m
    (tmp_path/'normalized.sql').write_text('changed')
    with pytest.raises(ValueError,match='package digest mismatch'):g.read_manifest(p,sealed)
    with pytest.raises(ValueError,match='manifest digest mismatch'):g.read_manifest(p,'wrong')

def test_conflicting_state_aborts_before_psql():
    with patch.object(g,'read_manifest',return_value={}),patch.object(g,'preflight',side_effect=ValueError('partial state')),patch.object(g.subprocess,'run') as run:
        with pytest.raises(ValueError,match='partial state'):g.execute('load',BLUE,GREEN,Path('m'),'hash',Path('pg'),True)
        run.assert_not_called()


def test_validator_cannot_write_blue():
    from scripts.validate_green_vote_storage import validate
    with patch('psycopg.connect') as connect:
        with pytest.raises(ValueError,match='green identity mismatch'):validate(BLUE,{}, {})
        connect.assert_not_called()
