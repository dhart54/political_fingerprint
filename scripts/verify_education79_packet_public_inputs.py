"""Prove captured packet inputs duplicate already-committed public evidence."""
import gzip
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'docs/review_packets/education79_locator_v1'
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def zipped(path):return json.loads(gzip.decompress(path.read_bytes()))
def require(condition,message):
    if not condition:raise ValueError(message)
def normalize_time(row):
    row=dict(row)
    for key in ['created_at','activated_at','deactivated_at']:
        if row.get(key):row[key]=datetime.fromisoformat(row[key]).isoformat()
    return row

def build():
    audit_path=ROOT/'docs/editorial/publication_replacements/m15b_green_activation/production_audits.json.gz'
    old=zipped(audit_path)['after-justice']['editorial_rows']
    current=load(PACKET/'baseline/persisted-education.json')
    root=next(r for r in old['editorial_artifact_versions'] if r['artifact_id']==245)
    registry=next(r for r in old['editorial_publication_registry'] if r['issue_id']=='EDUCATION_WORKFORCE' and r['member_bioguide_id']=='F000477')
    require(normalize_time(root)==normalize_time(current['artifact']),'captured artifact contains new/unpublished fields')
    require(normalize_time(registry)==normalize_time(current['registry']),'captured registry contains new/unpublished fields')
    for child in load(PACKET/'baseline/persisted-provenance.json')['relationships']:
        prior=next(r for r in old['editorial_artifact_versions'] if r['artifact_id']==child['artifact_id'])
        for key in ['artifact_type','natural_key','artifact_version','content_sha256','payload_jsonb']:
            require(child[key]==prior[key],'captured provenance contains new/unpublished fields')
        require(any(r['parent_artifact_id']==245 and r['child_artifact_id']==child['artifact_id'] and
            all(r[k]==child[k] for k in ['relationship_type','ordinal','metadata_jsonb'])
            for r in old['editorial_artifact_relationships']), 'captured relationship contains new/unpublished fields')
    snapshot_path=ROOT/'docs/editorial/publication_replacements/m15b_green_activation_execution/after-justice-live.json.gz'
    snapshot=zipped(snapshot_path);live=zipped(PACKET/'baseline/live-education.json.gz')
    require(len(live)==9 and all(v['body']==snapshot[k]['body'] for k,v in live.items()),'captured public endpoint contains new/unpublished content')
    return {'baseline_main':'f895f1c316afea888816fd1fd8e9eb2bfe9c31e6',
        'existing_repository_evidence':[audit_path.relative_to(ROOT).as_posix(),snapshot_path.relative_to(ROOT).as_posix()],
        'existing_evidence_file_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [audit_path,snapshot_path]},
        'artifact245_all_fields_equal':True,'registry_all_fields_equal':True,'provenance246247_and_relationships_equal':True,
        'timestamp_comparison':'space versus T separator normalized to the same timezone-aware instant; no value change',
        'all_nine_anonymous_public_response_bodies_already_published':True,
        'new_database_or_response_payload_disclosure':False}

if __name__=='__main__':
    proof=build()
    (PACKET/'prepared/public-input-equivalence.json').write_text(json.dumps(proof,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS all captured artifact/registry/provenance fields and nine response bodies duplicate existing Git evidence; timestamp formatting only.')
