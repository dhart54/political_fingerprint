"""Exact nonpolicy discovery screening without converting presence/named ballots."""
from __future__ import annotations
import argparse,json,os,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.app.semantic_ir.shared_corpus import digest
from scripts.prepare_shared_domain_candidate import prepare,readable_candidates,reproducibility_proof,review_text,validate_universe_proposal
from scripts.validate_infrastructure_candidate_seed import assert_neutral,read,require
DATA=ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch7_20260916';PRIOR=ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch6_20260916'
IDS=['house:119:1:1','house:119:1:2','house:119:1:138','house:119:1:169','house:119:1:178','house:119:2:1','house:119:2:106']


def validate(author,capture,universe,membership,*,check_files=True):
    validate_universe_proposal(universe,author,capture,membership);old={n:read(PRIOR/f'{n}.json') for n in ['authoring','sources','universe_proposal','membership_review']};require(author['actions']==old['authoring']['actions'],'screening changed authored meanings or corrections');ss={s['source_id']:s for s in capture['sources']};require(len(ss)==len(capture['sources']),'duplicate source identity')
    for s in old['sources']['sources']:require(ss[s['source_id']]==s,'prior source changed')
    rows={r['action_id']:r for r in universe['candidate_dispositions']};prev={r['action_id']:r for r in old['universe_proposal']['candidate_dispositions']};fields=['action_id','session','roll','date','measure','question','member_action'];require(len(rows)==676 and [[r[k] for k in fields] for r in universe['candidate_dispositions']]==[[r[k] for k in fields] for r in old['universe_proposal']['candidate_dispositions']],'676identity or raw observation changed')
    for aid,row in rows.items():
        if aid not in IDS:require(row==prev[aid],'prior/unexamined boundary changed')
    require(dict(Counter(r['disposition'] for r in rows.values()))==dict(interpreted_substantive_directional=22,interpreted_substantive_non_directional=1,procedural_context=17,exact_action_ineligible=1,source_unresolved=633,pending_interpretation=2),'conservation differs')
    acc=universe['accounting'];require(acc['action_ids_by_disposition']=={k:[r['action_id'] for r in universe['candidate_dispositions'] if r['disposition']==k] for k in acc['counts']},'identity buckets differ');require(all(acc[k]==v for k,v in dict(total_candidate_actions=676,substantive_eligible_actions=23,directional_substantive_actions=22,non_directional_substantive_actions=1,procedural_context_actions=17,exact_action_ineligible_actions=1,unresolved_boundary_cases=635,independent_episode_count=23,multi_action_episode_count=0).items()),'aggregate accounting differs')
    require(all(not universe[k] for k in ['full_record_claim','synthesis_eligible','full_issue_universe_closed','publication_authorized','publication_changes','production_writes','episode_acceptance_authorized','synthesis_authorized']) and universe['approval_receipt'] is None,'reserved authority changed')
    records={r['action_id']:r for r in membership['records']};require(set(records)=={r['action_id'] for r in old['membership_review']['records']}|set(IDS),'screening set differs')
    for r in old['membership_review']['records']:require(records[r['action_id']]==r,'prior membership changed')
    audit=read(DATA/'nonpolicy_observation_audit.json');require([r['action_id'] for r in audit['records']]==IDS,'audit identity set differs')
    for row in audit['records']:
        aid=row['action_id'];source=ss['clerk:119:'+':'.join(aid.split(':')[2:])];meta=source['metadata'];quorum=aid in ['house:119:1:1','house:119:2:1'];speaker=aid=='house:119:1:2';expected='exact_action_ineligible' if speaker else 'procedural_context';question='Election of the Speaker' if speaker else 'Call by States' if aid=='house:119:1:1' else 'Call of the House' if quorum else 'On Motion to Adjourn'
        require(meta['vote-question']==question and rows[aid]['question']==question and row['exact_question']==question,'exact question differs');require(rows[aid]['disposition']==expected and row['disposition']==expected and rows[aid]['episode_candidate_id'] is None and not row['interpretation_or_projection_authored'],'nonpolicy choice became policy interpretation');require(row['vote_type']==meta['vote-type'] and row['reported_chamber_outcome']==meta['vote-result'],'audit outcome differs')
        for obs in row['observations']:
            label=source['member_records'][obs['member_id']]['official_label'];require(obs['official_label']==label and not obs['counting_infrastructure_position'],'raw official observation audit differs')
            if quorum:require(label=='Present' and obs['observation_kind']=='recorded_presence','quorum Present was directionalized')
            elif speaker:require(label==('Jeffries' if obs['member_id']=='F000477' else 'Emmer') and obs['observation_kind']=='named_candidate_choice','named Speaker ballot was directionalized')
    assert_neutral(author['actions']);assert_neutral(membership['records'])
    core,mapping,projections,inputs,result=prepare(author,capture,['F000477','M001184']);readable=readable_candidates(author,core,projections,result);proof=reproducibility_proof(author,capture,['F000477','M001184']);require(result.compiled_ir==read(PRIOR/'generated/compiled_ir.json'),'nonpolicy screening changed behavioral IR')
    for member in readable['members']:require(len(member['findings'])==(22 if member['member_id']=='F000477' else 19),'new nonpolicy finding emitted')
    for member in result.compiled_ir['members']:require(member['coverage']['not_voting_actions']==(1 if member['member_id']=='F000477' else 4),'prior Not Voting changed')
    require(read(DATA/'hr2189_taxonomy_recommendation.json')==read(PRIOR/'hr2189_taxonomy_recommendation.json'),'unaccepted taxonomy proposal changed')
    products=dict(shared_action_core=core,shared_issue_mapping=mapping,member_projections=projections,compiler_input=inputs,compiled_ir=result.compiled_ir,readable_candidates=readable,reproducibility_proof=proof)
    if check_files:
        for name,value in products.items():require((DATA/'generated'/f'{name}.json').read_bytes()==(json.dumps(value,ensure_ascii=False,indent=2)+'\n').replace('\n',os.linesep).encode(),f'generated replay differs: {name}')
        packet=(ROOT/'docs/review_packets/infrastructure_candidate_batch7.md').read_text(encoding='utf-8');region=packet.split('<!-- GENERATED CANDIDATE START -->\n',1)[1].split('<!-- GENERATED CANDIDATE END -->',1)[0];require(region==review_text(author,core,projections,result,capture),'readable packet replay differs')
        for r in read(DATA/'source_reuse_receipt.json')['reused_sources']:require(r['source_object_sha256']==digest(ss[r['source_id']]),'reused Clerk object differs')
    return dict(identity_count=676,new_screenings=7,new_meanings=0,combined_meanings=23,procedural_controls=17,exact_action_exclusions=1,ordinary_pending_screenings=631,source_count=len(ss),source_acquisitions=0,compiled_ir_unchanged=True,core_sha256=core['corpus_sha256'],compiled_sha256=digest(result.compiled_ir),raw_present_and_named_ballots_preserved=True,five_authored_not_voting_preserved=True,prior_boundaries_corrections_unchanged=True,byte_identical_generated_replay=check_files,independent_review='pending',full_issue_universe_closed=False,publication_authorized=False,production_writes=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',type=Path);args=p.parse_args();r=validate(*[read(DATA/f'{n}.json') for n in ['authoring','sources','universe_proposal','membership_review']])
    if args.receipt:args.receipt.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r))
if __name__=='__main__':main()
