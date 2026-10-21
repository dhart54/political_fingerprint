"""Batch5 source/actor correction, candidate boundaries, conservation and replay."""
from __future__ import annotations
import argparse
import copy
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.app.semantic_ir.shared_corpus import digest
from scripts.prepare_shared_domain_candidate import prepare,readable_candidates,reproducibility_proof,review_text,validate_universe_proposal
from scripts.validate_infrastructure_candidate_seed import assert_neutral,official_status,read,require
from scripts.validate_infrastructure_candidate_batch4 import versions as prior_versions
DATA=ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch5_20260916'
PRIOR=ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch4_20260916'
NEW={f'house:119:2:{n}' for n in [105,125,126,127]}
SCREENED=NEW|{f'house:119:2:{n}' for n in [110,133,134]}


def validate_taxonomy(rec):
    require(rec['state']=='recommendation_pending_independent_boundary_review' and rec['existing_proposal_unaccepted'] and
        not rec['structural_tests_are_semantic_approval'] and not rec['proposal_or_authority_changed'] and
        not rec['publication_authorized'],'taxonomy recommendation conferred authority')


def validate(author,capture,universe,membership,*,check_files=True):
    validate_universe_proposal(universe,author,capture,membership)
    old={n:read(PRIOR/f'{n}.json') for n in ['authoring','sources','universe_proposal','membership_review']}
    correction=read(DATA/'candidate_correction_receipt.json');by={a['action_id']:a for a in author['actions']};sources={s['source_id']:s for s in capture['sources']}
    require(set(by)=={a['action_id'] for a in old['authoring']['actions']}|NEW,'interpretation set differs')
    clause_source=sources['govinfo:s2503es'];t=clause_source['text'];lo=t.index('(B) Alternative equipment or technology.--');hi=t.index('(C) Required briefing.--',lo)
    require(correction['controlling_complete_clause']==t[lo:hi] and correction['clause_governed_source_sha256']==clause_source['governed_bytes_sha256'],'correcting source clause differs')
    for prior in old['authoring']['actions']:
        current=copy.deepcopy(by[prior['action_id']]);expected=copy.deepcopy(prior)
        if prior['action_id']=='house:119:2:72':
            require(correction['corrected_s2503_passage'] in current['meaning'] and correction['defective_s2503_preimage'] not in current['meaning'],
                    'alternative pathway actor or operator choice misrepresented')
            expected['meaning']=prior['meaning'].replace(correction['defective_s2503_preimage'],correction['corrected_s2503_passage'])
            require(len(current['limitations'])==len(prior['limitations'])+1 and
                'duty on FAA' in current['limitations'][-1] and 'not an operator duty' in current['limitations'][-1],
                'alternative pathway qualification absent');current['limitations'].pop()
        elif prior['action_id']=='house:119:2:70':
            require(len(current['limitations'])==len(prior['limitations'])+1 and current['limitations'].pop()==correction['source_label_qualification'],
                    'inherited Public Law label qualification absent')
        require(current==expected,'prior action changed beyond disclosed corrections')
    for source in old['sources']['sources']:require(sources[source['source_id']]==source,'retained prior source changed')
    require(len(sources)==len(capture['sources']),'duplicate source identity')
    require(all('unblock.federalregister.gov' not in s['url'] and 'Federal Register :: Request Access' not in s.get('text','') and 'Page Not Found' not in s.get('text','') for s in sources.values()),'rejected response promoted to evidence')
    rows={r['action_id']:r for r in universe['candidate_dispositions']};priorrows={r['action_id']:r for r in old['universe_proposal']['candidate_dispositions']};fields=['action_id','session','roll','date','measure','question','member_action']
    require(len(rows)==676 and [[r[k] for k in fields] for r in universe['candidate_dispositions']]==[[r[k] for k in fields] for r in old['universe_proposal']['candidate_dispositions']],'676 discovery identities changed')
    for aid,row in rows.items():
        if aid not in SCREENED:require(row==priorrows[aid],'prior/unexamined boundary changed')
    require(dict(Counter(r['disposition'] for r in rows.values()))==dict(interpreted_substantive_directional=18,interpreted_substantive_non_directional=1,procedural_context=9,source_unresolved=646,pending_interpretation=2),'conservation differs')
    acc=universe['accounting'];require(acc['action_ids_by_disposition']=={k:[r['action_id'] for r in universe['candidate_dispositions'] if r['disposition']==k] for k in acc['counts']},'identity buckets differ')
    require(all(acc[k]==v for k,v in dict(total_candidate_actions=676,substantive_eligible_actions=19,directional_substantive_actions=18,non_directional_substantive_actions=1,procedural_context_actions=9,unresolved_boundary_cases=648,independent_episode_count=19,multi_action_episode_count=0).items()) and acc['official_source_readiness']['ready_substantive_actions']==19 and acc['official_source_readiness']['substantive_actions']==19,'aggregate accounting or readiness differs')
    require(sum(r['unresolved_reason']=='pending_research' for r in rows.values())==644,'ordinary pending count differs')
    package=rows['house:119:2:110'];require(package['disposition']=='pending_interpretation' and package['review_progress']['exact_action_binding_unresolved'] and not package['review_progress']['required_evidence_unavailable'] and package['episode_candidate_id'] is None and package['action_id'] not in by,'unfinished package misrepresented')
    held=rows['house:119:2:134'];require(held['disposition']=='source_unresolved' and held['review_progress']['required_evidence_unavailable'] and held['unresolved_reason']=='unclassified_rejected_CFR_response_no_retry' and held['episode_candidate_id'] is None and held['action_id'] not in by,'unclassified source hold misrepresented')
    proc=rows['house:119:2:133'];require(proc['disposition']=='procedural_context' and proc['episode_candidate_id'] is None and proc['action_id'] not in by,'procedure became counting')
    for aid in ['house:119:2:133','house:119:2:134']:require(official_status(sources['clerk:119:2:'+aid.split(':')[-1]]['member_records']['F000477']['official_label'])=='Not Voting','noncounting Not Voting status changed')
    require(all(not universe[k] for k in ['full_record_claim','synthesis_eligible','full_issue_universe_closed','publication_authorized','publication_changes','production_writes','episode_acceptance_authorized','synthesis_authorized']) and universe['approval_receipt'] is None,'reserved authority changed')
    records={r['action_id']:r for r in membership['records']};require(set(records)=={r['action_id'] for r in old['membership_review']['records']}|SCREENED,'screening set differs')
    for rec in old['membership_review']['records']:require(records[rec['action_id']]==rec,'prior membership changed')
    for aid,rec in records.items():
        row=rows[aid];clerk=sources[f"clerk:119:{row['session']}:{row['roll']}"];require(clerk['metadata']['vote-question']==row['question'],'exact question differs');status=official_status(clerk['member_records']['F000477']['official_label']);require(official_status(row['member_action'].replace('_',' ').title())==status,'official universe observation differs')
        if aid in by:require(row['disposition']==('interpreted_substantive_non_directional' if status in ['Present','Not Voting'] else 'interpreted_substantive_directional'),'nondirectional disposition contradicts official status')
    assert_neutral(author['actions']);assert_neutral(membership['records'])
    for action in author['actions']:
        prose=' '.join([action['meaning'],action['compact_description'],*action['limitations']]);require(re.search(r'\b(?:Health|Infrastructure|Immigration|Education)\s+(?:membership|inclusion|eligibility)\b',prose,re.I) is None,'issue-specific membership in shared core')
    for bill,sid in [(7084,'govinfo:46usc70022-2024-operative'),(1681,'govinfo:47usc1455d-infra5'),(5201,'govinfo:47usc623-2024-multiline911')]:require(sid in next(a for a in author['actions'] if a['bill_number']==bill)['compact_source_refs'],'compact lost material baseline provenance')
    for aid in NEW:
        clerk=sources['clerk:119:2:'+aid.split(':')[-1]];action=by[aid];require(clerk['metadata']['vote-question'] in ['On Passage','On Motion to Suspend the Rules and Pass'] and sources[action['source_id']]['text_version']=='EH','new exact question/version differs')
        require(rows[aid]['date']=={'105':'2026-03-27','125':'2026-04-20','126':'2026-04-20','127':'2026-04-21'}[aid.split(':')[-1]],'new action date differs')
    prior_versions(sources);validate_taxonomy(read(DATA/'hr2189_taxonomy_recommendation.json'))
    core,mapping,projections,inputs,result=prepare(author,capture,['F000477','M001184']);readable=readable_candidates(author,core,projections,result);proof=reproducibility_proof(author,capture,['F000477','M001184']);cores={a['action_id']:a for a in core['actions']}
    for member in readable['members']:
        require(len(member['findings'])==(18 if member['member_id']=='F000477' else 16),'finding count includes noncounting action')
        for finding in member['findings']:
            for obs in finding['action_observations']:
                shared=cores[obs['action_id']];require(obs['status'] in ['Yea','Nay'] and obs['detail'][1]==shared['candidate_exact_action_meaning'] and obs['qualifications']==shared['candidate_shared_limitations'],'generated shared copy changed or nondirectional finding produced')
    for member in result.compiled_ir['members']:
        nv=1 if member['member_id']=='F000477' else 3;require(member['coverage']['not_voting_actions']==nv and member['coverage']['directional_yes_no_positions']==19-nv,'Not Voting became directional')
    products=dict(shared_action_core=core,shared_issue_mapping=mapping,member_projections=projections,compiler_input=inputs,compiled_ir=result.compiled_ir,readable_candidates=readable,reproducibility_proof=proof)
    if check_files:
        for name,value in products.items():require((DATA/'generated'/f'{name}.json').read_bytes()==(json.dumps(value,ensure_ascii=False,indent=2)+'\n').replace('\n',os.linesep).encode(),f'generated replay differs: {name}')
        packet=(ROOT/'docs/review_packets/infrastructure_candidate_batch5.md').read_text(encoding='utf-8');region=packet.split('<!-- GENERATED CANDIDATE START -->\n',1)[1].split('<!-- GENERATED CANDIDATE END -->',1)[0];require(region==review_text(author,core,projections,result,capture),'readable packet replay differs')
        receipt=read(DATA/'source_reuse_and_version_receipt.json');require(not receipt['known_denied_chains_retried'] and not receipt['rejected_responses_are_evidence'] and len(receipt['unclassified_rejected_responses'])==2,'source restriction declaration differs')
        for row in receipt['reused_sources']:require(row['source_object_sha256']==digest(sources[row['source_id']]),'source reuse receipt differs')
    return dict(identity_count=676,new_screenings=7,new_meanings=4,combined_meanings=19,procedural_controls=9,ordinary_pending_screenings=644,ordinary_pending_interpretation_ids=['house:119:1:218','house:119:2:110'],examined_source_hold_ids=['house:119:1:111','house:119:2:134'],source_count=len(sources),new_successful_captures=3,unclassified_rejected_responses=2,member_observations=38,finding_counts={m['member_id']:len(m['findings']) for m in readable['members']},not_voting_counts={m['member_id']:m['coverage']['not_voting_actions'] for m in result.compiled_ir['members']},additional_procedural_and_held_not_voting_ids=['house:119:2:133','house:119:2:134'],core_sha256=core['corpus_sha256'],compiled_sha256=digest(result.compiled_ir),s2503_source_backed_actor_correction=True,public_law_label_error_disclosed_source_unchanged=True,hr2189_membership_unaccepted=True,member_neutral_prose=True,byte_identical_generated_replay=check_files,independent_batch_semantic_review='pending',full_issue_universe_closed=False,publication_authorized=False,production_writes=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',type=Path);args=p.parse_args();r=validate(*[read(DATA/f'{n}.json') for n in ['authoring','sources','universe_proposal','membership_review']])
    if args.receipt:args.receipt.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r))
if __name__=='__main__':main()
