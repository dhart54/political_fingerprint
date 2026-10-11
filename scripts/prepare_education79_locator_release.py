"""Offline locator release packet; never accepts, persists or activates artifacts."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.editorial_presentations.compiler import canonical_digest as digest
from app.editorial_presentations.publication_replacement_governance_v2 import PROJECTION_SCHEMA_V2R, artifact_identity, validate_projection
from app.editorial_presentations.publication_replacement_runtime_v2r import eligible_m14g_replacement, select_site_integration_public_v2r
from app.editorial_presentations.education_workforce_m14g_integration_candidate import _receipt_rows

PACKET = ROOT / 'docs/review_packets/education79_locator_v1'
SOURCE_ID = 'govinfo:CREC-2025-03-25-pt1-PgH1241:amendment-3'
SOURCE_SHA = 'eaafafb53de434c894f475a864a1cd951118a32f2f98e1e487109f7ef71f5b32'
OLD_URL = 'https://www.govinfo.gov/app/details/CREC-2025-03-25-pt1-PgH1241'
URL = 'https://www.govinfo.gov/content/pkg/CREC-2025-03-25/html/CREC-2025-03-25-pt1-PgH1241.htm'
ACTION = 'house:119:1:79'
KEY = 'public-issue-presentation:f000477:education_workforce:record-locator:v1'
CATALOG = 'docs/editorial/interpretability_candidates/house_119_v1/education_workforce_m14c_v1/source_catalog.json'

class LocatorPreparationError(ValueError):
    """A source or projection binding cannot be authenticated safely."""

def require(condition, message):
    if not condition:
        raise LocatorPreparationError(message)

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def delta(before, after, path=''):
    if type(before) is not type(after):
        return [{'path': path, 'before': before, 'after': after}]
    if isinstance(before, dict):
        require(before.keys() == after.keys(), f'fields changed at {path}')
        return [d for key in sorted(before) for d in delta(before[key], after[key], path+'/'+key)]
    if isinstance(before, list):
        require(len(before) == len(after), f'length changed at {path}')
        return [d for i, (a,b) in enumerate(zip(before,after)) for d in delta(a,b,path+'/'+str(i))]
    return [] if before == after else [{'path':path,'before':before,'after':after}]

def authenticate_source(catalog, core, raw_bytes):
    sources=[s for s in catalog['sources'] if s['source_id']==SOURCE_ID]
    require(len(sources)==1, 'source identity missing/duplicated')
    source=sources[0]
    action=next(a for a in core['actions'] if a['action_id']==ACTION)
    identity=action['operative_meaning_source_identities'][0]
    require(source['action_id']==ACTION and source['source_type']=='congressional_record', 'source action/type differs')
    require(source['source_url']==URL, 'unreviewed locator')
    require(identity['source_id']==SOURCE_ID and identity['source_type']==source['source_type'], 'source identity differs')
    require(source['raw_provenance']['sha256']==identity['raw_sha256']==identity['governed_bytes_sha256']==SOURCE_SHA, 'source hashes differ')
    require(hashlib.sha256(raw_bytes).hexdigest()==SOURCE_SHA, 'actual governed bytes differ')
    return source

def build():
    captured=load(PACKET/'baseline/persisted-education.json')
    old=captured['artifact']; prior=captured['registry']; candidate=old['payload_jsonb']
    require(old['artifact_id']==prior['artifact_id']==245, 'baseline root differs')
    require(digest(candidate)==old['content_sha256']=='76d06a43beb51c164a199c576c3d0aa539b6c05da2f8e4eff8fe54845547e4ec', 'baseline content differs')
    require(eligible_m14g_replacement({**old,**prior},member_bioguide_id='F000477') is not None, 'baseline eligibility differs')
    graph_observation=load(PACKET/'baseline/persisted-provenance.json')
    require(graph_observation['root_artifact_id']==245, 'baseline graph root differs')
    for child in graph_observation['relationships']:
        require(digest(child['payload_jsonb'])==child['content_sha256'], 'historical provenance payload drift')
        prefix={'uses_source_manifest':'source_manifest','has_validation':'validation'}[child['relationship_type']]
        for field in ['natural_key','artifact_version','content_sha256']:
            require(child[field]==prior['publication_metadata_jsonb'][prefix+'_'+field], 'historical provenance binding differs')
    catalog=load(ROOT/CATALOG)
    core=load(ROOT/'docs/editorial/shared_corpora/house_119_v2/shared_action_core.json')
    member=load(ROOT/'docs/editorial/shared_corpora/house_119_v2/member_projections/f000477.json')
    ledger=load(ROOT/'docs/editorial/analytical_candidates/f000477_education_workforce_m14d_v1/accepted_behavioral_findings.json')['subject']['accepted_episode_disposition_ledger']
    source=next(s for s in catalog['sources'] if s['source_id']==SOURCE_ID)
    raw_path=(ROOT/source['raw_provenance']['governed_local_path']).resolve()
    require(raw_path.is_relative_to(ROOT), 'governed source path leaves repository')
    authenticate_source(catalog,core,raw_path.read_bytes())
    receipts=candidate['subject']['receipt_projections']
    require(receipts==_receipt_rows(ledger,core,member), 'accepted receipts differ from governed inputs')
    prepared=_receipt_rows(ledger,core,member,source_catalog=catalog)
    receipt_delta=delta(receipts,prepared)
    require(len(receipt_delta)==2 and all(d['before']==OLD_URL and d['after']==URL for d in receipt_delta), 'receipt changes exceed exact locator fields')
    presentations={}
    for scope in ['119','all']:
        response=select_site_integration_public_v2r(candidate,legislator_id='leg_valerie_p_foushee',member_bioguide_id='F000477',scope=scope)
        presentations[scope]=next(p for p in response['presentations'] if p['issue_id']=='EDUCATION_WORKFORCE')
    before={'schema_version':PROJECTION_SCHEMA_V2R,'artifact_id':KEY,'subject':{
        'member_bioguide_id':'F000477','member_slug':'leg_valerie_p_foushee','issue_id':'EDUCATION_WORKFORCE','congress':119,
        'presentations':presentations,'receipt_projections':copy.deepcopy(receipts)}}
    after=copy.deepcopy(before); after['subject']['receipt_projections']=prepared
    for p in after['subject']['presentations'].values():
        row=next(r for r in p['exact_action_receipts'] if r['canonical_action_id']==ACTION)
        require(row['action_meaning_sources'][0]['url']==OLD_URL, 'prior public locator differs')
        row['action_meaning_sources'][0]['url']=URL
    public_delta=delta(before,after)
    require(len(public_delta)==4 and all(d['before']==OLD_URL and d['after']==URL for d in public_delta), 'public changes exceed exact locator copies')
    validate_projection(before); validate_projection(after)
    content_sha=digest(after)
    source_manifest={'schema_version':'editorial_publication_source_manifest_v1','complete_required_sources':True,
        'source_artifacts':[artifact_identity(old)],'presentation_content_sha256':content_sha,
        'source_locator_binding':{'source_id':SOURCE_ID,'governed_bytes_sha256':SOURCE_SHA,'url':URL,'catalog_file':CATALOG,
            'catalog_file_sha256':hashlib.sha256((ROOT/CATALOG).read_bytes().replace(b'\r\n',b'\n')).hexdigest()}}
    proof={'baseline_artifact_identity':artifact_identity(old),'projection_changes':public_delta,'receipt_changes':receipt_delta,
        'all_other_fields_equal':True,'reviewed_actions':len(receipts),'underlying_receipt_url_fields_changed':2,
        'meaning_vote_status_source_id_hash_version_coverage_counting_unchanged':True,
        'before_transport_projection_sha256':digest(before),'candidate_projection_sha256':content_sha,
        'public_presentation_sha256':{scope:{'before':digest(p),'after':digest(after['subject']['presentations'][scope])} for scope,p in presentations.items()},
        'production_execution_authorized':False}
    validation={'schema_version':'editorial_publication_validation_v1','successful':True,'current':True,'blocking_findings':0,
        'presentation_content_sha256':content_sha,'invariance_proof_sha256':digest(proof),
        'production_activation_authorized':False,'validation_scope':'offline contract and exact locator delta; not human authority'}
    graph={'schema_version':'education79_locator_persistence_preparation_v1','production_execution_authorized':False,
        'registry_key':{'member_bioguide_id':'F000477','issue_id':'EDUCATION_WORKFORCE'},'expected_old':artifact_identity(old),
        'candidate':{'natural_key':KEY,'artifact_version':1,'content_sha256':content_sha,'source_manifest_sha256':digest(source_manifest),'supersedes_artifact_id':245},
        'artifacts':[{'natural_key':KEY,'artifact_version':1,'artifact_type':'issue_public_presentation','payload_file':'candidate-projection.json','content_sha256':content_sha},
                     {'natural_key':KEY+':source','artifact_version':1,'artifact_type':'source_manifest','payload_file':'candidate-source-manifest.json','content_sha256':digest(source_manifest)},
                     {'natural_key':KEY+':validation','artifact_version':1,'artifact_type':'standardization_validation_result','payload_file':'candidate-validation.json','content_sha256':digest(validation)}],
        'relationships':[{'relationship_type':role,'ordinal':0,'child_natural_key':KEY+suffix,'metadata_jsonb':{'activation_bundle_id':KEY}} for role,suffix in [('uses_source_manifest',':source'),('has_validation',':validation')]],
        'proposed_review_status':'human_approval_pending','production_eligible_now':False,
        'production_target_identity_sha256':prior['publication_metadata_jsonb']['production_target_identity_sha256'],
        'later_persistence_caps':{'batches':1,'artifacts':3,'relationships':2,'registry_updates':0,'other_updates':0,'deletes':0},
        'later_activation_caps':{'registry_updates':1,'artifact_inserts':0,'batch_inserts':0,'relationship_inserts':0,'other_updates':0,'deletes':0},
        'unresolved':['explicit locator/persistence approval','real newly persisted IDs','sealed exact V2R write set and activation authority','fresh execution evidence','coordinated frontend card source rebind'],
        'existing_authority_must_not_be_reused':True}
    return {'baseline-public-projection.json':before,'candidate-projection.json':after,'invariance-proof.json':proof,
        'candidate-source-manifest.json':source_manifest,'candidate-validation.json':validation,'persistence-preparation.json':graph}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    outputs=build(); folder=PACKET/'prepared';folder.mkdir(parents=True,exist_ok=True)
    for name,value in outputs.items():
        text=json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n';path=folder/name
        if args.check: require(path.read_text(encoding='utf-8')==text, f'prepared file drift: {name}')
        else: path.write_text(text,encoding='utf-8',newline='\n')
    print(json.dumps({'status':'offline_preparation_passed','content_sha256':digest(outputs['candidate-projection.json']),
        'projection_url_changes':4,'production_execution_authorized':False}))
if __name__=='__main__': main()
