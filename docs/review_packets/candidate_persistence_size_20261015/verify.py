"""Offline exact-Git receipt/input checks. No database or network connections."""
from pathlib import Path
import copy
import hashlib
import json
import subprocess
import sys
import time

PREFIX='docs/review_packets/candidate_persistence_size_20261015/'
PLAN='docs/plans/candidate_persistence_size_rehearsal.md'
BASE='af6cd6d78d6944d64a68a92653066c4c1625f96b'


def git(*args):return subprocess.check_output(['git',*args])
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()


def validate_measurement(r,a):
    assert r['selection']=='jsonb-compatible-subset'and not r['full_candidate_size_measured']
    assert not a['full_package_size_measured']and a['current_authorized_candidate_growth_bytes']==0
    assert 'error'not in r and r['server']['stopped']
    assert r['production_connections']==r['production_writes']==0
    for case,s in r['stages'].items():
        states=[s['baseline'],s['after_v1']]
        if 'after_retained_identical_v2'in s:states.append(s['after_retained_identical_v2'])
        for x in states:
            assert sum(row['total_bytes']for row in x['relations'])==x['store_total_bytes']
            assert all(row['total_bytes']==row['table_including_toast_bytes']+row['direct_index_bytes']for row in x['relations'])
            assert all(row['toast_heap_main_bytes']+row['toast_index_bytes']<=row['toast_total_bytes']for row in x['relations'])
            assert x['counts']['editorial_publication_registry']==0
        m=a['measured_compatible_subset'][case]
        assert m['artifact_table_delta_bytes']==s['after_v1']['store_total_bytes']-s['baseline']['store_total_bytes']
        assert m['database_delta_bytes']==s['after_v1']['database_bytes']-s['baseline']['database_bytes']
        for load in s['loads']:
            assert load['idempotent']['artifacts_inserted']==load['idempotent']['relationships_inserted']==0
        assert len(s['index_definitions'])==17
    assert r['stages']['combined']['after_v1']['counts']['editorial_artifact_versions']==sum(r['inputs'][d]['row_count']for d in ['immigration','health'])
    s=r['stages']['combined'];assert s['after_retained_identical_v2']['counts']['editorial_artifact_versions']==2*s['after_v1']['counts']['editorial_artifact_versions']
    base=a['baseline']['all_databases_bytes']
    for threshold,headroom in a['current_headroom_bytes'].items():assert int(threshold)-base==headroom
    canonical=sum(v['canonical_json_bytes']for v in a['full_generated_inventory'].values())
    for scenario in a['scenarios']:
        assert not scenario['complete_candidate_forecast']
        if 'copies'in scenario:expected=a['measured_compatible_subset']['combined']['database_delta_bytes']*scenario['copies']
        else:expected=round(canonical*scenario['retained_copies']*scenario['byte_factor'])
        assert scenario['increment_bytes']==expected and scenario['project_total_bytes']==base+expected


def main(ref):
    started=time.perf_counter()
    def blob(path):return git('show',(':'if ref=='INDEX'else ref+':')+path)
    manifest=json.loads(blob(PREFIX+'delivered_blobs.json'))
    changes=git('diff','--cached','--name-status',BASE)if ref=='INDEX'else git('diff','--name-status',BASE,ref)
    paths=[]
    for line in changes.decode().splitlines():
        status,path=line.split('\t');assert status=='A'and(path.startswith(PREFIX)or path==PLAN);paths.append(path)
    assert set(paths)==set(manifest['files'])|{PREFIX+'delivered_blobs.json'}
    files={}
    for path,x in manifest['files'].items():
        b=blob(path);assert x=={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob_oid':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()};files[path]=b
    load=lambda name:json.loads(files[PREFIX+name])
    r=load('measurement.json');a=load('capacity_analysis.json');inventory=load('package_inventory.json')
    validate_measurement(r,a)
    for variant in ['table_sum','false_complete','scenario_math']:
        bad=copy.deepcopy(r);budget=copy.deepcopy(a)
        if variant=='table_sum':bad['stages']['combined']['after_v1']['store_total_bytes']+=8192
        elif variant=='false_complete':bad['full_candidate_size_measured']=True
        else:budget['scenarios'][0]['project_total_bytes']+=1
        try:validate_measurement(bad,budget)
        except AssertionError:pass
        else:raise AssertionError('Corruption control not rejected: '+variant)
    module={};adapter=git('show',BASE+':backend/app/semantic_ir/adapters.py')
    exec(compile(adapter,'pinned_semantic_ir_adapters.py','exec'),module)
    guard_checks=0
    for x in inventory['files']:
        b=git('show',x['snapshot']+':'+x['path']);assert len(b)==x['raw_bytes']and hashlib.sha256(b).hexdigest()==x['raw_sha256']
        assert git('rev-parse',x['snapshot']+':'+x['path']).decode().strip()==x['git_blob_oid']
        obj=json.loads(b);c=canon(obj);assert len(c)==x['canonical_json_bytes']and hashlib.sha256(c).hexdigest()==x['canonical_sha256']
        found=[]
        def scan(v,p=''):
            if isinstance(v,str)and'\0'in v:found.append({'pointer':p,'nul_count':v.count('\0')})
            elif isinstance(v,list):
                for i,z in enumerate(v):scan(z,p+'/'+str(i))
            elif isinstance(v,dict):
                for k,z in v.items():scan(z,p+'/'+str(k).replace('~','~0').replace('/','~1'))
        scan(obj);assert found==x['nul_string_paths']and sum(q['nul_count']for q in found)==x['nul_count']
        if x['path'].endswith('/compiled_ir.json'):
            try:module['build_persistence_proposal'](obj)
            except ValueError as e:assert str(e)=='shared candidates cannot prepare persistence artifacts';guard_checks+=1
            else:raise AssertionError('Real candidate guard did not reject')
    assert guard_checks==2
    for x in r['source_code']:
        b=git('show',BASE+':'+x['path']);assert hashlib.sha256(b).hexdigest()==x['sha256'];assert git('rev-parse',BASE+':'+x['path']).decode().strip()==x['git_blob_oid']
    for x in inventory['files']:
        if x['domain']=='health':assert git('rev-parse','5a523f857cab9d47090c62d77f43804a5dde6b5a:'+x['path']).decode().strip()==x['git_blob_oid']
    assert load('local_cluster_cleanup.json')['owned_roots_live']==[]
    assert '\\u0000'in load('failed_jsonb_unicode_attempt.json')['error']
    print(json.dumps({'ref':ref,'outcome':'PASS','delivered_files':len(paths),'sealed_blobs':len(manifest['files']),
      'input_json_files':len(inventory['files']),'code_bindings':len(r['source_code']),'candidate_guard_checks':guard_checks,
      'receipt_corruption_negatives':3,'successful_subset_cases':list(r['stages']),'full_package_measured':False,
      'seconds':round(time.perf_counter()-started,6),'database_connections':0,'limits':'Offline source/receipt verification; does not independently rerun SQL or certify a complete future persistence package.'}))


if __name__=='__main__':main(sys.argv[1])
