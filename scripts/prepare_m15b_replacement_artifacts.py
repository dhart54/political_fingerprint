"""Offline data preparation for the already-approved M15B semantics. No executor."""
import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT))
from app.editorial_presentations.compiler import canonical_digest as digest
from app.editorial_presentations.publication_replacement_governance_v2 import PROJECTION_SCHEMA_V2R, validate_projection
from app.editorial_presentations.selector import select_public_presentations
from scripts.build_m15b_review import inputs, ns_removal_candidate, NS, LIMIT, PUBLIC_COPY

OUT = ROOT / 'docs/editorial/publication_replacements/m15b_preparation'
BASE = '18069621de39c67fad7d5e642a151ceb333b2c0c'
REVIEWED = 'aa6ee7b2610e94a69035affd8d4b97679ce7cfe0'
JUSTICE = 'JUSTICE_PUBLIC_SAFETY'


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def justice_presentations():
    folder = ROOT/'docs/editorial/full_record_reviews/publication_preparations/f000477_justice_public_safety_119_v1'
    payload = load(folder/'approved_public_presentation_projection.json')
    row = {'member_bioguide_id':'F000477', 'issue_id':JUSTICE, 'payload_jsonb':payload,
           'natural_key':payload['artifact_identity']['artifact_id'], 'artifact_version':1,
           'schema_version':payload['schema_version'], 'content_sha256':digest(payload),
           'publicly_active':True, 'deactivated_at':None, 'editorial_status':'human_approved',
           'benchmark_status':'gold_benchmark', 'production_eligible':True,
           'publication_metadata_jsonb':{
               'approval_receipt':load(folder/'full_record_publication_approval_projection.json'),
               'semantic_review_exception_resolution':load(folder/'semantic_review_exception_resolution.json')}}
    return {scope:next(p for p in select_public_presentations([row], member_bioguide_id='F000477',
                legislator_id='leg_valerie_p_foushee',scope=scope)['presentations'] if p['issue_id']==JUSTICE)
            for scope in ('119','all')}


def current_receipt_rows(issue):
    """Materialize the existing receipt adapter, including resolved controls."""
    _, evidence = inputs()
    if issue != JUSTICE:
        return copy.deepcopy(evidence[issue])
    from app.editorial_presentations.receipt_projection import attach_governed_receipt_projections
    frozen = load(ROOT/'docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_justice_public_safety_119_v2/frozen_final_compiler_input.json')
    actions = frozen['compiler_input']['members'][0]['actions']
    statuses = {a['action_id']:a['status'] for a in actions}
    presentation = justice_presentations()['119']
    raw = [{'canonical_action_id':action, 'congress':119, 'position':statuses[action].lower().replace(' ', '_')}
           for action in presentation['reviewed_action_ids']]
    return attach_governed_receipt_projections({'domain':issue,'evidence':raw}, presentation)['evidence']


def build():
    review_root = ROOT/'docs/reviews/m15b_interpretive_trust'
    review = load(review_root/'before_after_public_review.json')
    limits = load(review_root/'active_limitation_treatment_review.json')
    trajectories = load(review_root/'trajectory_review.json')
    mapping = limits['authored_public_copy_changes'][0]
    assert mapping['source_text']==LIMIT and mapping['proposed_public_copy']==PUBLIC_COPY
    assert len(mapping['occurrences'])==35
    authority = {'artifact_id':'human-semantic-authority:m15b:approved:v1', 'accepted':True,
        'reviewed_pr_head':REVIEWED, 'approval_source':'User approval in M15B IMPLEMENT APPROVED SEMANTICS request',
        'national_security_review_sha256':digest(review['national_security']['after_candidate']),
        'national_security_operation':trajectories['national_security_remediation_candidate'],
        'justice_limitation_mapping':mapping, 'justice_trajectory_unchanged':'prop:53cda8d886a88f12',
        'execution_in_this_preparation_authorized':False}
    authority['subject_sha256']=digest(authority)
    paths, evidence = inputs()
    before_ns = review['national_security']['before']
    after_ns = ns_removal_candidate(before_ns)
    assert after_ns == review['national_security']['after_candidate']
    # All-scope wording is the existing selector's approved scope boundary only.
    from app.editorial_presentations.site_publication import select_site_integration_public
    ns_all = next(p for p in select_site_integration_public(load(paths[NS]), member_bioguide_id='F000477',
        legislator_id='leg_valerie_p_foushee',scope='all')['presentations'] if p['issue_id']==NS)
    projections = {NS:{'119':after_ns,'all':ns_removal_candidate(ns_all)}, JUSTICE:justice_presentations()}
    target_ids = {o['canonical_action_id'] for o in mapping['occurrences']}
    receipts = {issue:current_receipt_rows(issue) for issue in (NS, JUSTICE)}
    changed = set()
    for row in receipts[JUSTICE]:
        if row['canonical_action_id'] in target_ids:
            r = row['governed_receipt_projection']
            assert r['caveats'].count(LIMIT)==1
            r['limitation_treatments']=[{'source_text':c,'treatment':'public','public_copy':PUBLIC_COPY if c==LIMIT else c}
                                      for c in r['caveats']]
            changed.add(row['canonical_action_id'])
    assert changed == target_ids
    # Justice's selected receipts and evidence endpoint must agree; other fields stay exact.
    receipt_index = {r['canonical_action_id']:r.get('governed_receipt_projection') for r in receipts[JUSTICE]}
    for p in projections[JUSTICE].values():
        p['exact_action_receipts']=[copy.deepcopy(receipt_index[r['canonical_action_id']])
                                  if r['canonical_action_id'] in target_ids else r for r in p['exact_action_receipts']]
    baseline=load(ROOT/'docs/editorial/publication_replacements/f000477_education_workforce_m14h_v1/production_baseline.json')
    products={}
    for issue in (NS,JUSTICE):
        prior=next(r for r in baseline['existing_registry_identities'] if r['issue_id']==issue)
        key=f'public-issue-presentation:f000477:{issue.lower()}:m15b:v1'
        payload={'schema_version':PROJECTION_SCHEMA_V2R,'artifact_id':key,'subject':{
            'member_bioguide_id':'F000477','member_slug':'leg_valerie_p_foushee','issue_id':issue,'congress':119,
            'presentations':projections[issue],'receipt_projections':receipts[issue]}}
        validate_projection(payload)
        source = {'schema_version':'editorial_publication_source_manifest_v1',
            'source_artifacts':[{'artifact_id':prior['artifact_id'],'natural_key':prior['presentation_natural_key'],
                'artifact_version':prior['artifact_version'],'content_sha256':prior['content_sha256']}],
            'semantic_authority_binding':{'artifact_id':authority['artifact_id'],'subject_sha256':authority['subject_sha256']},
            'presentation_content_sha256':digest(payload)}
        validation = {'schema_version':'editorial_publication_validation_v1','status':'PASS','blockers':[],
                      'presentation_content_sha256':digest(payload)}
        products[issue]={'registry_key':{'member_bioguide_id':'F000477','issue_id':issue},
            'expected_old':{'artifact_id':prior['artifact_id'],'natural_key':prior['presentation_natural_key'],
                'artifact_version':prior['artifact_version'],'content_sha256':prior['content_sha256']},
            'proposed_new':{'natural_key':key,'artifact_version':1,'content_sha256':digest(payload)},
            'payload':payload,'semantic_authority_binding':{'artifact_id':authority['artifact_id'],'subject_sha256':authority['subject_sha256']},
            'additive_graph':{'source_manifest':{'natural_key':key+':source','artifact_version':1,'payload':source,'content_sha256':digest(source)},
                'validation':{'natural_key':key+':validation','artifact_version':1,'payload':validation,'content_sha256':digest(validation)},
                'relationships':[{'relationship_type':role,'ordinal':0,'child_natural_key':key+suffix,
                    'metadata_jsonb':{'activation_bundle_id':key}} for role,suffix in [('has_validation',':validation'),('uses_source_manifest',':source')]]}}
    return {'schema_version':'publication_replacement_preparation_v2r','production_execution_authorized':False,
            'source_commit':BASE,'semantic_authority':authority,'replacements':products,
            'persistence_boundary':'New numeric artifact IDs must be resolved after separately governed immutable persistence; no production-ready authority or preflight is fabricated here.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    text=json.dumps(build(),sort_keys=True,ensure_ascii=False,indent=2)+'\n'
    path=OUT/'approved_semantics_preparation.json'
    if args.check:
        assert path.read_text(encoding='utf-8')==text
    else:
        OUT.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
    print('M15B approved semantics prepared offline: two exact replacement inputs; production execution disabled.')
