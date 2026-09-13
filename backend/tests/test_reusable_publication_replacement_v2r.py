import copy
from datetime import datetime, timezone

import pytest

from app.editorial_presentations.compiler import canonical_digest as digest
from app.editorial_presentations.publication_replacement_governance_v2 import (
    PROJECTION_SCHEMA_V2R, REPLACEMENT_AUTHORITY_SCHEMA_V2, REVIEWER_AUTHORITY_V2R,
    POSITIVE_AUTHORIZATIONS_V2R, RUNTIME_EVIDENCE_SCHEMA_V2, validate_positive_authority,
    PublicationReplacementGovernanceError, validate_execution,
)
from app.editorial_presentations.publication_replacement_store_v2r import prepare_write_set, publication_metadata


def runtime():
    files=[{'path':'synthetic-runtime.py','file_sha256':'a'*64}]
    sub={'files':files,'submanifest_sha256':digest({'files':files}),
         'verification_method':'immutable_git_object_read','deployed_commit_sha':'a'*40}
    result={'schema_version':RUNTIME_EVIDENCE_SCHEMA_V2,'captured_at_utc':datetime.now(timezone.utc).isoformat(),
        'healthy':True,'deployment_required_before_activation':False,
        'backend_deployment':{**sub,'health_commit_sha':'a'*40},
        'frontend_deployment':{**sub,'deployment_source_identity':'synthetic-disposable'}}
    result['runtime_health_proof_subject_sha256']=digest(result)
    return result


def seal(write_set):
    s=write_set['subject']
    subject={'decision':'approve_exact_publication_replacement_v2','reviewer':'synthetic disposable test',
        'reviewer_authority':REVIEWER_AUTHORITY_V2R,'decision_recorded_at_utc':'2026-09-12T00:00:00+00:00',
        'registry_key':s['registry_key'],'expected_old':s['expected_old'],'proposed_new':s['proposed_new'],
        'semantic_authority_binding':s['replacement_authority_binding'],'rollback_target':s['rollback_target'],
        'production_target_identity_sha256':s['production_target_identity_sha256'],
        'exact_write_set_subject_sha256':write_set['write_set_subject_sha256'],'authorizations':POSITIVE_AUTHORIZATIONS_V2R}
    return {'schema_version':REPLACEMENT_AUTHORITY_SCHEMA_V2,'artifact_id':'synthetic-authority:'+write_set['artifact_id'],
        'immutable':True,'accepted':True,'sealed':True,'test_only_synthetic':True,
        'subject':subject,'activation_authority_subject_sha256':digest(subject)}


def sample(issue='NATIONAL_SECURITY_FOREIGN', *, payload=None, prior=None, old=None, new_id=999, metadata=None):
    if payload is None:
        row={'canonical_action_id':'house:119:1:1','position':'yea','governed_receipt_projection':{
            'canonical_action_id':'house:119:1:1','exact_action_meaning':'Synthetic reviewed choice.',
            'caveats':['Synthetic test only.'],'member_action':'Yea'}}
        payload={'schema_version':PROJECTION_SCHEMA_V2R,'artifact_id':'synthetic:'+issue,'subject':{
            'member_bioguide_id':'F000477','member_slug':'leg_valerie_p_foushee','issue_id':issue,'congress':119,
            'presentations':{scope:{'issue_id':issue,'requested_scope':scope,'tier':'reviewed_conclusion',
                'limitations':[],'repeated_patterns':[],'policy_trajectories':[],'review_state':{}} for scope in ('119','all')},
            'receipt_projections':[row]}}
    key={'member_bioguide_id':payload['subject']['member_bioguide_id'],'issue_id':issue}
    old=old or {'artifact_id':100,'natural_key':'old:'+issue,'artifact_version':1,'content_sha256':'b'*64}
    prior=prior or {**key,'artifact_id':old['artifact_id'],'publicly_active':True,'deactivated_at':None,
                   'activated_at':'2026-01-01T00:00:00+00:00','publication_metadata_jsonb':{}}
    new={'artifact_id':new_id,'natural_key':payload['artifact_id'],'artifact_version':1,'content_sha256':digest(payload)}
    rt=runtime()
    metadata=metadata or {'presentation_natural_key':new['natural_key'],'presentation_artifact_version':1,
        'active_artifact_sha256':new['content_sha256'],'source_manifest_content_sha256':'c'*64,'validation_content_sha256':'d'*64,
        'source_manifest_natural_key':'synthetic:source','source_manifest_artifact_version':1,
        'validation_natural_key':'synthetic:validation','validation_artifact_version':1,
        'relationship_metadata':{'activation_bundle_id':'synthetic'}}
    ws=prepare_write_set(registry_key=key,prior_row=prior,expected_old=old,proposed_new=new,
        semantic_authority_binding={'artifact_id':'synthetic-human-decision','subject_sha256':'e'*64},
        publication_metadata=metadata,production_target_identity_sha256='f'*64,
        public_runtime_manifest_binding={f'{side}_submanifest_sha256':rt[f'{side}_deployment']['submanifest_sha256'] for side in ('backend','frontend')})
    return payload,ws,seal(ws),rt


@pytest.mark.parametrize('issue',['NATIONAL_SECURITY_FOREIGN','JUSTICE_PUBLIC_SAFETY'])
def test_same_v2r_validator_accepts_exact_non_education_request(issue):
    payload,ws,authority,_=sample(issue)
    validate_positive_authority(authority,write_set=ws,candidate=payload)
    assert ws['subject']['mutation_caps']['update_registry_rows']==1
    assert sum(ws['subject']['mutation_caps'].values())==1


@pytest.mark.parametrize('field',['registry_key','expected_old','proposed_new','rollback_target','exact_write_set_subject_sha256'])
def test_rehashed_authority_cannot_substitute_exact_bound_request(field):
    payload,ws,authority,_=sample()
    authority['subject'][field]='different'
    authority['activation_authority_subject_sha256']=digest(authority['subject'])
    with pytest.raises(PublicationReplacementGovernanceError):
        validate_positive_authority(authority,write_set=ws,candidate=payload)


@pytest.mark.parametrize('change',[lambda p:p['subject'].update(member_bioguide_id='OTHER'),
    lambda p:p['subject'].update(issue_id='JUSTICE_PUBLIC_SAFETY'),lambda p:p.update(artifact_id='other')])
def test_wrong_member_domain_or_replacement_cannot_reuse_authority(change):
    payload,ws,authority,_=sample();change(payload)
    with pytest.raises(PublicationReplacementGovernanceError):
        validate_positive_authority(authority,write_set=ws,candidate=payload)


def test_approved_m15b_inputs_express_both_future_replacements_without_persistence():
    from scripts.prepare_m15b_replacement_artifacts import build, justice_presentations
    prepared=build()
    for issue,item in prepared['replacements'].items():
        payload,ws,authority,_=sample(issue,payload=item['payload'],old=item['expected_old'])
        ws['subject']['replacement_authority_binding']=item['semantic_authority_binding']
        # Rebuild after substituting the one real human semantic-decision binding.
        from app.editorial_presentations.publication_replacement_governance_v2 import replacement_write_set_subject_sha256
        ws['write_set_subject_sha256']=replacement_write_set_subject_sha256(ws)
        ws['subject']['publication_registry_update']['publication_metadata_jsonb']['v2r_write_set_subject_sha256']=ws['write_set_subject_sha256']
        validate_positive_authority(seal(ws),write_set=ws,candidate=payload)
    justice=prepared['replacements']['JUSTICE_PUBLIC_SAFETY']['payload']['subject']
    original=justice_presentations()
    for scope,p in justice['presentations'].items():
        assert {k:v for k,v in p.items() if k!='exact_action_receipts'}=={k:v for k,v in original[scope].items() if k!='exact_action_receipts'}
    assert sum('limitation_treatments' in (r.get('governed_receipt_projection') or {}) for r in justice['receipt_projections'])==35
    assert sum('governed_receipt_control' in r for r in justice['receipt_projections'])==2
    assert prepared['production_execution_authorized'] is False


@pytest.mark.parametrize('issue',['NATIONAL_SECURITY_FOREIGN','JUSTICE_PUBLIC_SAFETY'])
@pytest.mark.parametrize('scope',['119','all'])
def test_replacement_evidence_preserves_current_ledger_controls_and_approved_copy(monkeypatch, issue, scope):
    from app.api import positions
    from app.editorial_presentations.publication_replacement_runtime_v2r import install_publication_replacement_runtime_v2r
    from scripts.prepare_m15b_replacement_artifacts import build, current_receipt_rows, PUBLIC_COPY
    install_publication_replacement_runtime_v2r()
    payload=build()['replacements'][issue]['payload']
    raw=[{k:copy.deepcopy(v) for k,v in row.items() if k not in {
        'governed_receipt_projection','governed_receipt_control','interpretation_review_state','raw_evidence'}}
        for row in current_receipt_rows(issue)]
    raw.append({'canonical_action_id':'house:119:2:99999','position':'present','congress':119})
    monkeypatch.setattr(positions,'get_legislator_profile',lambda **kw:{'bioguide_id':'F000477'})
    monkeypatch.setattr(positions,'_load_publication_rows',lambda:[])
    monkeypatch.setattr(positions,'_active_site_integration_publication',lambda **kw:payload)
    monkeypatch.setattr(positions,'get_position_evidence_response',lambda **kw:{'domain':issue,'evidence':copy.deepcopy(raw)})
    monkeypatch.setattr(positions,'get_governed_position_evidence_rows',lambda **kw:copy.deepcopy(raw[:-1]))
    result=positions.get_legislator_position_evidence('leg_valerie_p_foushee',issue,scope,None)
    assert [(r['canonical_action_id'],r['position']) for r in result['evidence']]==[(r['canonical_action_id'],r['position']) for r in raw]
    assert result['review_accounting']=={'available_action_count':len(raw),'reviewed_action_count':len(raw)-1,'not_yet_reviewed_action_count':1}
    assert sum(bool(r.get('governed_receipt_control')) for r in result['evidence'])==(2 if issue=='JUSTICE_PUBLIC_SAFETY' else 1)
    if issue=='JUSTICE_PUBLIC_SAFETY':
        assert sum(PUBLIC_COPY in (r.get('governed_receipt_projection') or {}).get('public_caveats',[]) for r in result['evidence'])==35


def test_runtime_uses_exact_member_key_and_rejects_unbound_selection():
    from app.editorial_presentations.publication_replacement_runtime_v2r import eligible_persisted_replacement
    payload,_,_,_=sample()
    payload['subject']['member_bioguide_id']='SYNTHETIC'
    payload,ws,authority,_=sample(payload=payload)
    row={**ws['subject']['registry_key'],**ws['subject']['proposed_new'],'payload_jsonb':payload,
        'schema_version':PROJECTION_SCHEMA_V2R,'publicly_active':True,'deactivated_at':None,
        'editorial_status':'human_approved','benchmark_status':'gold_benchmark','production_eligible':True,
        'publication_metadata_jsonb':publication_metadata(ws,authority)}
    assert eligible_persisted_replacement(row,member_bioguide_id='SYNTHETIC',allow_test_authority=True)==payload
    assert eligible_persisted_replacement(row,member_bioguide_id='F000477',allow_test_authority=True) is None
    assert eligible_persisted_replacement(row,member_bioguide_id='SYNTHETIC') is None
    row['artifact_id']+=1
    assert eligible_persisted_replacement(row,member_bioguide_id='SYNTHETIC',allow_test_authority=True) is None
