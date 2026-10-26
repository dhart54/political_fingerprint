"""Batch6 exact-source, nondirectional, protected-boundary and replay checks."""
from __future__ import annotations
import argparse
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
from scripts.validate_infrastructure_candidate_batch4 import versions as older_versions
from scripts.validate_infrastructure_candidate_batch5 import validate_taxonomy
DATA=ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch6_20260916'
PRIOR=ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch5_20260916'
NEW={f'house:119:2:{n}' for n in [181,234,235,238]};CONTROLS={f'house:119:2:{n}' for n in [194,195]}


def versions(sources):
    rows=[]
    for bill,pages in [(3106,[12,13]),(8897,[13,14])]:
        sid=f'record:2026-07-13-hr{bill}-infra6';s=sources[sid];extracts={p['pdf_page']:p['text'] for p in s['page_extracts']};floor=' '.join('\n'.join(extracts[p].splitlines()[1:]).split('VerDate')[0] for p in pages);start=floor.index('Be it enacted',floor.index(f'H.R. {bill}'));floor=floor[start:floor.index('The SPEAKER pro tempore.',start)]
        eh=sources[f'govinfo:hr{bill}eh'];t=eh['text'];body=t[t.index('Be it enacted'):t.index('Passed the')];norm=lambda t:re.sub('[^a-z0-9]','',t.lower());require(eh['text_version']=='EH' and norm(floor)==norm(body),f'floor body differs: HR{bill}')
        rows.append(dict(bill=bill,text_source_id=eh['source_id'],floor_source_id=sid,pdf_pages=pages,matched=True,normalized_body_sha256=digest(norm(body)),comparison='Complete operative bodies under lowercase ASCII-alphanumeric formatting comparison; explicit header/footer removal, original punctuation retained, no legal-equivalence certification.'))
    require(sources['clerk:119:2:235']['metadata']['vote-question']=='On Motion to Suspend the Rules and Pass, as Amended','8897exact amended question differs')
    return rows


def validate(author,capture,universe,membership,*,check_files=True):
    validate_universe_proposal(universe,author,capture,membership)
    old={n:read(PRIOR/f'{n}.json') for n in ['authoring','sources','universe_proposal','membership_review']};by={a['action_id']:a for a in author['actions']};sources={s['source_id']:s for s in capture['sources']}
    require(set(by)=={a['action_id'] for a in old['authoring']['actions']}|NEW,'interpretation set differs')
    for a in old['authoring']['actions']:require(by[a['action_id']]==a,'prior action or correction changed')
    for s in old['sources']['sources']:require(sources[s['source_id']]==s,'retained prior source changed')
    require(len(sources)==len(capture['sources']),'duplicate source identity')
    require(all('unblock.federalregister.gov' not in s['url'] and 'Federal Register :: Request Access' not in s.get('text','') and 'Page Not Found' not in s.get('text','') for s in sources.values()),'rejected response promoted to evidence')
    rows={r['action_id']:r for r in universe['candidate_dispositions']};priorrows={r['action_id']:r for r in old['universe_proposal']['candidate_dispositions']};fields=['action_id','session','roll','date','measure','question','member_action'];require(len(rows)==676 and [[r[k] for k in fields] for r in universe['candidate_dispositions']]==[[r[k] for k in fields] for r in old['universe_proposal']['candidate_dispositions']],'676 discovery identities changed')
    for aid,row in rows.items():
        if aid not in NEW|CONTROLS:require(row==priorrows[aid],'prior/unexamined boundary changed')
    require(dict(Counter(r['disposition'] for r in rows.values()))==dict(interpreted_substantive_directional=22,interpreted_substantive_non_directional=1,procedural_context=11,source_unresolved=640,pending_interpretation=2),'conservation differs')
    acc=universe['accounting'];require(acc['action_ids_by_disposition']=={k:[r['action_id'] for r in universe['candidate_dispositions'] if r['disposition']==k] for k in acc['counts']},'identity buckets differ')
    require(all(acc[k]==v for k,v in dict(total_candidate_actions=676,substantive_eligible_actions=23,directional_substantive_actions=22,non_directional_substantive_actions=1,procedural_context_actions=11,unresolved_boundary_cases=642,independent_episode_count=23,multi_action_episode_count=0).items()) and acc['official_source_readiness']['ready_substantive_actions']==23 and acc['official_source_readiness']['substantive_actions']==23,'aggregate accounting or readiness differs')
    require(sum(r['unresolved_reason']=='pending_research' for r in rows.values())==638,'ordinary pending count differs')
    require(all(rows[aid]['disposition']=='procedural_context' and rows[aid]['episode_candidate_id'] is None and aid not in by for aid in CONTROLS),'procedure became counting')
    require(all(not universe[k] for k in ['full_record_claim','synthesis_eligible','full_issue_universe_closed','publication_authorized','publication_changes','production_writes','episode_acceptance_authorized','synthesis_authorized']) and universe['approval_receipt'] is None,'reserved authority changed')
    records={r['action_id']:r for r in membership['records']};require(set(records)=={r['action_id'] for r in old['membership_review']['records']}|NEW|CONTROLS,'screening set differs')
    for rec in old['membership_review']['records']:require(records[rec['action_id']]==rec,'prior membership changed')
    for aid,rec in records.items():
        row=rows[aid];clerk=sources[f"clerk:119:{row['session']}:{row['roll']}"];require(clerk['metadata']['vote-question']==row['question'],'exact question differs');status=official_status(clerk['member_records']['F000477']['official_label']);require(official_status(row['member_action'].replace('_',' ').title())==status,'official universe observation differs')
        if aid in by:require(row['disposition']==('interpreted_substantive_non_directional' if status in ['Present','Not Voting'] else 'interpreted_substantive_directional'),'nondirectional disposition contradicts official status')
    assert_neutral(author['actions']);assert_neutral(membership['records'])
    for a in author['actions']:
        prose=' '.join([a['meaning'],a['compact_description'],*a['limitations']]);require(re.search(r'\b(?:Health|Infrastructure|Immigration|Education)\s+(?:membership|inclusion|eligibility)\b',prose,re.I) is None,'issue-specific membership in shared core')
    for bill,sid in [(1003,'govinfo:47cfr10-10a-2025-infra6'),(8897,'govinfo:49usc44903-j2-secure-flight'),(139,'govinfo:15usc260a-2024-operative'),(139,'govinfo:15usc261-2024-operative'),(139,'govinfo:15usc262-2024-infra6'),(139,'govinfo:15usc267-2024-infra6')]:require(sid in next(a for a in author['actions'] if a['bill_number']==bill and a['action_id'] in NEW)['compact_source_refs'],'compact lost material baseline provenance')
    version_checks=versions(sources);older_versions(sources)
    require(sources['clerk:119:2:181']['member_records']['M001184']['official_label']=='Not Voting','S1003 Not Voting changed')
    require(all(sources[f'clerk:119:2:{n}']['metadata']['vote-result']=='Passed' for n in [194,195]),'1333actual rule outcome differs')
    validate_taxonomy(read(DATA/'hr2189_taxonomy_recommendation.json'));require(read(DATA/'hr2189_taxonomy_recommendation.json')==read(PRIOR/'hr2189_taxonomy_recommendation.json'),'taxonomy recommendation or authority changed')
    core,mapping,projections,inputs,result=prepare(author,capture,['F000477','M001184']);readable=readable_candidates(author,core,projections,result);proof=reproducibility_proof(author,capture,['F000477','M001184']);cores={a['action_id']:a for a in core['actions']}
    for member in readable['members']:
        require(len(member['findings'])==(22 if member['member_id']=='F000477' else 19),'finding count includes noncounting action')
        for finding in member['findings']:
            for obs in finding['action_observations']:
                s=cores[obs['action_id']];require(obs['status'] in ['Yea','Nay'] and obs['detail'][1]==s['candidate_exact_action_meaning'] and obs['qualifications']==s['candidate_shared_limitations'],'generated shared copy changed or nondirectional finding produced')
    for member in result.compiled_ir['members']:
        nv=1 if member['member_id']=='F000477' else 4;require(member['coverage']['not_voting_actions']==nv and member['coverage']['directional_yes_no_positions']==23-nv,'Not Voting became directional')
    products=dict(shared_action_core=core,shared_issue_mapping=mapping,member_projections=projections,compiler_input=inputs,compiled_ir=result.compiled_ir,readable_candidates=readable_candidates(author,core,projections,result),reproducibility_proof=proof)
    if check_files:
        for name,value in products.items():require((DATA/'generated'/f'{name}.json').read_bytes()==(json.dumps(value,ensure_ascii=False,indent=2)+'\n').replace('\n',os.linesep).encode(),f'generated replay differs: {name}')
        packet=(ROOT/'docs/review_packets/infrastructure_candidate_batch6.md').read_text(encoding='utf-8');region=packet.split('<!-- GENERATED CANDIDATE START -->\n',1)[1].split('<!-- GENERATED CANDIDATE END -->',1)[0];require(region==review_text(author,core,projections,result,capture),'readable packet replay differs')
        receipt=read(DATA/'source_reuse_and_version_receipt.json');require(not receipt['protected_targets_retried'] and not receipt['rejected_prior_responses_reclassified'] and len(receipt['new_successful_raw_captures'])==4 and all(r['status']=='captured' for r in receipt['new_successful_raw_captures']),'source restriction/capture declaration differs')
        for row in receipt['reused_sources']:require(row['source_object_sha256']==digest(sources[row['source_id']]),'source reuse receipt differs')
    return dict(identity_count=676,new_screenings=6,new_meanings=4,combined_meanings=23,procedural_controls=11,ordinary_pending_screenings=638,ordinary_pending_interpretation_ids=['house:119:1:218','house:119:2:110'],examined_source_hold_ids=['house:119:1:111','house:119:2:134'],source_count=len(sources),new_successful_raw_captures=4,new_governed_sources=5,member_observations=46,finding_counts={m['member_id']:len(m['findings']) for m in readable['members']},not_voting_counts={m['member_id']:m['coverage']['not_voting_actions'] for m in result.compiled_ir['members']},version_checks=version_checks,core_sha256=core['corpus_sha256'],compiled_sha256=digest(result.compiled_ir),prior_actions_sources_memberships_corrections_unchanged=True,hr2189_membership_unaccepted=True,member_neutral_prose=True,byte_identical_generated_replay=check_files,independent_batch_semantic_review='pending',full_issue_universe_closed=False,publication_authorized=False,production_writes=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',type=Path);args=p.parse_args();r=validate(*[read(DATA/f'{n}.json') for n in ['authoring','sources','universe_proposal','membership_review']])
    if args.receipt:args.receipt.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r))
if __name__=='__main__':main()
