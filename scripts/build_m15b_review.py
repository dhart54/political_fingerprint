"""Deterministic, non-authorizing review of two trajectory items and hidden caveats."""
import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.trajectory_comparability import digest
from backend.app.editorial_presentations.site_publication import select_site_integration_public

BASE = '5a1593d67d5ccb952acf7234cebffa5a7d1d53fc'
OUT = ROOT / 'docs/reviews/m15b_interpretive_trust'
REVIEWS = ROOT / 'docs/editorial/full_record_reviews'
NS = 'NATIONAL_SECURITY_FOREIGN'
TARGET = 'trajectory-milcon-va-appropriations-direction-change'
PUBLIC_COPY = 'This action alone does not establish motive, ideology, or a broader position on this issue.'
LIMIT = 'This candidate does not establish motive, ideology, a broad issue position, or a synthesis conclusion.'


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def inputs():
    paths = {d:REVIEWS/f'site_integration_candidates/f000477_{d.lower()}_119_v1/site_integration_candidate.json'
             for d in (NS,'ENVIRONMENT_ENERGY')}
    paths['EDUCATION_WORKFORCE'] = ROOT/'docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1/site_integration_candidate.json'
    paths['JUSTICE_PUBLIC_SAFETY'] = REVIEWS/'publication_preparations/f000477_justice_public_safety_119_v1/public_review_state_projection.json'
    rows = {}
    for domain,path in paths.items():
        value=load(path)
        if domain=='JUSTICE_PUBLIC_SAFETY':
            rows[domain]=[{'canonical_action_id':r['canonical_action_id'],'governed_receipt_projection':r} for r in value['exact_action_receipts']]
        else:
            subject=value['subject']
            rows[domain]=subject.get('receipt_projections') or subject['preview_data']['evidence_119']
    return paths,rows


def rendered_limitations(rows):
    old_source=subprocess.check_output(['git','show',f'{BASE}:frontend/lib/publicReceipt.mjs'],cwd=ROOT).decode()
    script="""import fs from 'node:fs';
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const old=await import('data:text/javascript;base64,'+Buffer.from(input.old).toString('base64'));
const current=await import(input.current);
const result=[];
for(const [domain,rows] of Object.entries(input.rows)) for(const row of rows) {
 const receipt=row.governed_receipt_projection;
 const caveats=receipt ? receipt.caveats||[] : [row.uncertainty_note].filter(Boolean);
 result.push({domain,canonical_action_id:row.canonical_action_id,source_caveats:caveats,
   old_public:old.buildPublicReceipt(row).limitations,new_public:current.buildPublicReceipt(row).limitations,
   old_suppressed:caveats.filter(x=>old.publicLimitations([x]).length===0)});
}
console.log(JSON.stringify(result));"""
    return json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT,
        input=json.dumps({'old':old_source,'current':(ROOT/'frontend/lib/publicReceipt.mjs').as_uri(),'rows':rows}).encode()))


def ns_removal_candidate(before):
    after = copy.deepcopy(before)
    after['policy_trajectories'] = [f for f in after['policy_trajectories'] if TARGET not in f['semantic_source_ids']]
    ordinary = [f for key in ('repeated_patterns', 'notable_choices', 'policy_trajectories') for f in after[key]]
    surviving = ordinary + after['syntheses']
    actions = sorted({a for f in ordinary for a in f['action_ids']})
    episodes = sorted({e for f in ordinary for e in f['episode_ids']})
    overview = after['overview']
    overview['semantic_source_ids'] = sorted({s for f in surviving for s in f['semantic_source_ids']})
    overview['mapping']['semantic_binding_count'] = len(overview['semantic_source_ids'])
    for key in ('action_ids', 'semantic_lineage_action_ids', 'public_supporting_action_ids'):
        overview[key] = actions.copy()
    for key in ('episode_ids', 'semantic_lineage_episode_ids', 'public_supporting_episode_ids'):
        overview[key] = episodes.copy()
    label = f"{len(ordinary)} findings · {len(actions)} votes"
    overview['evidence_count_label'] = label
    after['coverage_text'] = label
    after['evidence_metadata']['display_action_ids'] = actions.copy()
    overview['secondary_clarification'] = overview['secondary_clarification'].replace(', annual appropriations', '')
    return after


def build():
    paths,rows=inputs()
    candidate=load(paths[NS])
    before=next(p for p in select_site_integration_public(candidate,legislator_id='leg_valerie_p_foushee',
        member_bioguide_id='F000477',scope='119')['presentations'] if p['issue_id']==NS)
    episodes_path=REVIEWS/'policy_episode_implementations/f000477_national_security_foreign_119_v1/episode_decision_implementation_bundle.json'
    episodes=load(episodes_path)['subject']['implementation_records']
    item=before['policy_trajectories'][0]
    assert item['semantic_source_ids']==[TARGET]
    evidence=[e for e in episodes if e['episode_id'] in item['episode_ids']]
    evidence.sort(key=lambda e:e['actions'][0]['official_action_date'])
    # Inspect accepted semantics, never infer equivalence from annual titles/directions.
    assert len(evidence)==2
    assert all(e['grouping_type']=='single_action' for e in evidence)
    assert all(e['material_policy_differences']=='Any topically related action uses a different measure, mechanism, target, package, or proposition unless separately reviewed.' for e in evidence)
    assert 'The package contents differed between fiscal years.' in item['limitations']
    assert all('comparison_binding' not in e and 'comparison_semantics' not in e for e in evidence)
    justice_path=REVIEWS/'publication_preparations/f000477_justice_public_safety_119_v1/approved_public_presentation_projection.json'
    justice=load(justice_path)
    justice_episode_path=REVIEWS/'policy_episode_implementations/f000477_justice_public_safety_119_v1/episode_implementation_bundle.json'
    justice_episode=next(e for e in load(justice_episode_path)['implemented_episodes'] if e['episode_id']=='halt-fentanyl-legislative-path')
    justice_wording=justice['editorial_wording']['policy_trajectories'][0]
    justice_item={'proposition_id':justice_wording['proposition_id'],
                  'body':justice_wording['body']['text'],
                  'action_ids':justice_wording['body']['mapping']['action_ids']}
    scan=[dict(proposition_id=TARGET,domain=NS,current_public_wording=item['primary_sentence'],
        evidence_episodes=item['episode_ids'],evidence_actions=item['action_ids'],
        proposed_comparability_basis=None,result='FAIL_NEW_COMPARABILITY_CONTRACT',
        reason='Accepted meanings establish distinct whole-package choices. Accepted differences explicitly require separate review; no common operative choice or whole-package equivalence is established.',
        accepted_evidence=[{k:e[k] for k in ('episode_id','record_subject_sha256','policy_proposition','material_policy_differences','material_limitations','actions')} for e in evidence]),
        dict(proposition_id=justice_item['proposition_id'],domain='JUSTICE_PUBLIC_SAFETY',
             current_public_wording=justice_item['body'],evidence_episodes=['halt-fentanyl-legislative-path'],
             evidence_actions=justice_item['action_ids'],proposed_comparability_basis=None,
             accepted_action_meanings=justice_episode['chronological_action_sequence'],
             episode_content_sha256=justice_episode['content_subject_sha256'],
             result='NEEDS_HUMAN_SEMANTIC_REVIEW',
             reason='The accepted object is one mixed legislative episode, with an amendment and two whole frameworks. It explicitly disclaims a change in motive/philosophy. No separately accepted common decision comparison is bound; whether it should retain the trajectory type needs semantic review. No Justice remediation is applied or proposed here.')]
    after=ns_removal_candidate(before)
    overview=after['overview']
    assert before['exact_action_receipts']==after['exact_action_receipts']
    assert before['reviewed_action_ids']==after['reviewed_action_ids']
    for field in ('syntheses','repeated_patterns','notable_choices','limitations','policy_episodes'):
        assert before[field]==after[field]
    rendering=rendered_limitations(rows)
    affected=[]
    for r in rendering:
        for source in r['old_suppressed']:
            assert source==LIMIT, 'New suppressed caveat requires bounded review, not automatic classification'
            affected.append(dict(domain=r['domain'],canonical_action_id=r['canonical_action_id'],
                source_text=source,old_frontend_disposition='SUPPRESSED_BY_GENERIC_RECEIPT_CAVEAT',
                proposed_treatment='MIXED_REQUIRES_PUBLIC_COPY',proposed_mapping_id='justice-limitation-public-copy-v1',
                reason='Substantive inference boundaries are mixed with internal editorial terms candidate and synthesis conclusion. Authored public wording requires explicit acceptance.',
                semantic_public_acceptance='pending',source_projection_sha256=digest(next(row['governed_receipt_projection'] for row in rows[r['domain']] if row['canonical_action_id']==r['canonical_action_id']))))
    assert len(affected)==35
    common=dict(baseline_main_sha=BASE,accepted=False,authorizing=False,production_selectable=False,
                publication_authorized=False,human_semantic_acceptance='pending independent review',
                production_writes_performed=False)
    bindings={str(p.relative_to(ROOT)).replace('\\','/'):digest(load(p)) for p in [*paths.values(),episodes_path,justice_path,justice_episode_path]}
    return {
      'trajectory_review.json':{**common,'source_bindings':bindings,'contract_summary':{
          'rule':'Strict chronology plus independently accepted substantive comparability, exact episode/action evidence, behavioral dimension and comparison limits.',
          'authoring_boundary':'comparison_binding points to separately trusted semantic evidence; author prose, same family, topic, vote direction, or components cannot establish eligibility.',
          'enforcement':['compile_behavioral_candidate_ir','run_editorial_pipeline'],
          'history':'Exact frozen M11G input replay and explicit accepted-reference replay preserve history; neither grants new trajectory eligibility.'},
          'existing_trajectory_scan':scan,'domains_without_trajectories':['ENVIRONMENT_ENERGY','EDUCATION_WORKFORCE'],
          'national_security_remediation_candidate':{'proposition_id':TARGET,'proposed_operation':'remove from policy_trajectories without replacement',
              'preserved_action_ids':item['action_ids'],'preserved_episode_ids':item['episode_ids'],'independent_findings_changed':False,
              'publication_replacement_required_after_acceptance':True}},
      'active_limitation_treatment_review.json':{**common,'affected_occurrences':len(affected),
          'distinct_source_texts':len({r['source_text'] for r in affected}),
          'breakdown':{'PUBLIC':0,'INTERNAL':0,'MIXED':35},'entries':affected,
          'authored_public_copy_changes':[{'mapping_id':'justice-limitation-public-copy-v1',
              'source_text':LIMIT,'proposed_treatment':'MIXED_REQUIRES_PUBLIC_COPY',
              'proposed_public_copy':PUBLIC_COPY,'semantic_public_acceptance':'pending',
              'occurrences':[{'domain':r['domain'],'canonical_action_id':r['canonical_action_id']} for r in affected]}],
          'active_runtime_unchanged':True,
          'note':'Historical source wording is immutable. One additive authored public-copy candidate covers all 35 occurrences and is unaccepted. Exact legacy suppression preserves active behavior pending explicit approval; structured treatment remains authoritative.'},
      'before_after_public_review.json':{**common,'national_security':{'before':before,'after_candidate':after,
          'ledger_preservation':{'unchanged':True,
              'note':'Selected presentation and evidence ledger are separate surfaces. Candidate changes only the presentation; these original governed receipt rows remain in the ledger.',
              'retained_receipts':[copy.deepcopy(r) for r in rows[NS] if r.get('canonical_action_id') in item['action_ids']],
              'retained_episode_ids':[e['episode_id'] for e in evidence],
              'evidence_ledger_sha256':digest(rows[NS])},
          'delta':{'policy_trajectories':[len(p['policy_trajectories']) for p in (before,after)],
              'ordinary_findings':[sum(len(p[k]) for k in ('repeated_patterns','notable_choices','policy_trajectories')) for p in (before,after)],
              'finding_supporting_actions':[len(p['evidence_metadata']['display_action_ids']) for p in (before,after)],
              'coverage_labels_reconciled':after['coverage_text']==overview['evidence_count_label'],
              'receipts_preserved':True,'underlying_action_meanings_preserved':True,'overview_primary_sentence_unchanged':True,
              'overview_secondary_before':before['overview']['secondary_clarification'],
              'overview_secondary_after':overview['secondary_clarification'],
              'removed_trajectory_limitations':item['limitations'],'other_limitations_unchanged':True}},
          'receipt_rendering':rendering}
    }


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--live-snapshot',type=Path)
    args=parser.parse_args();products=build()
    if args.live_snapshot:
        active=load(args.live_snapshot)
        before=products['before_after_public_review.json']['national_security']['before']
        assert before==next(p for p in active['presentations']['presentations'] if p['issue_id']==NS)
        live_trajectories=[(p['issue_id'],t) for p in active['presentations']['presentations'] for t in p.get('policy_trajectories',[])]
        assert len(live_trajectories)==2
        for scan in products['trajectory_review.json']['existing_trajectory_scan']:
            live=next(t for d,t in live_trajectories if d==scan['domain'])
            assert live.get('primary_sentence',live.get('body'))==scan['current_public_wording']
            assert live['action_ids']==scan['evidence_actions']
        _,rows=inputs()
        for d,live_rows in active['details'].items():
            expected={r['canonical_action_id']:r['governed_receipt_projection']['caveats'] for r in rows[d] if r.get('governed_receipt_projection')}
            assert {r['canonical_action_id']:r['governed_receipt_projection']['caveats'] for r in live_rows}==expected
        print('Local accepted caveat sources and selected NS presentation match active public snapshot.')
    OUT.mkdir(parents=True,exist_ok=True)
    for name,body in products.items():
        text=json.dumps(body,ensure_ascii=False,sort_keys=True,indent=2)+'\n';path=OUT/name
        if args.check:
            assert path.read_text(encoding='utf-8')==text, name+' is stale'
        else:
            path.write_text(text,encoding='utf-8')
    print('M15B review package: 2 trajectories; NS removal pending; 0 PUBLIC; 0 INTERNAL; 35 MIXED; one pending public-copy candidate; active output unchanged.')


if __name__=='__main__':main()
