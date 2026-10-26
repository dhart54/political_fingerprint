"""Offline batch3 conservation, exact-source, prior-snapshot and replay checks."""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app.semantic_ir.shared_corpus import digest
from scripts.prepare_shared_domain_candidate import (
    prepare,readable_candidates,reproducibility_proof,review_text,validate_universe_proposal,
)
from scripts.validate_infrastructure_candidate_seed import assert_neutral,official_status,read,require
from scripts.validate_infrastructure_candidate_batch2 import versions as prior_versions

DATA=ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch3_20260916'
PRIOR=ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch2_20260916'
NEW={'house:119:1:277','house:119:1:286','house:119:1:287','house:119:2:13'}
CONTROLS={'house:119:1:343','house:119:1:344'}
PACKAGE='house:119:1:218'
HOLD='house:119:1:111'


def versions(sources):
    rows=[]
    for bill,sid,pages in [
        (1608,'record:2025-11-17-hr1608-infra3',[11,12]),
        (2659,'record:2025-11-17-hr2659-infra3',[12,13,14]),
        (2683,'congressional-record:2026-01-12-suspension2683-6500-6504',[5,6]),
    ]:
        source=sources[sid]
        extracts={p['pdf_page']:p['text'] for p in source['page_extracts']}
        floor=' '.join('\n'.join(extracts[p].splitlines()[1:]).split('VerDate')[0] for p in pages)
        start=floor.index('Be it enacted',floor.index(f'H.R. {bill}'))
        floor=floor[start:floor.index('The SPEAKER pro tempore.',start)]
        text_source=sources[f'govinfo:hr{bill}eh']
        require(text_source['text_version']=='EH','wrong bill version')
        text=text_source['text'];body=text[text.index('Be it enacted'):text.index('Passed the')]
        normalized=lambda value:re.sub('[^a-z0-9]','',value.lower())
        require(normalized(floor)==normalized(body),f'floor body differs: HR{bill}')
        rows.append(dict(bill=bill,source_id=f'govinfo:hr{bill}eh',floor_source_id=sid,
            pdf_pages=pages,normalized_body_sha256=digest(normalized(body)),matched=True))
    return rows


def validate(author,capture,universe,membership,*,check_files=True):
    validate_universe_proposal(universe,author,capture,membership)
    old_author=read(PRIOR/'authoring.json');old_capture=read(PRIOR/'sources.json')
    old_universe=read(PRIOR/'universe_proposal.json');old_membership=read(PRIOR/'membership_review.json')
    by={a['action_id']:a for a in author['actions']}
    require(set(by)=={a['action_id'] for a in old_author['actions']}|NEW,'interpretation set differs')
    for old in old_author['actions']:
        current=copy.deepcopy(by[old['action_id']])
        if old['action_id']=='house:119:1:136':
            require(len(current['limitations'])==len(old['limitations'])+1,'wrapper discrepancy qualification absent')
            qualification=current['limitations'].pop()
            require(all(t in qualification for t in ['EH wrapper','May19,2025','May20','Clerk','does not reconcile','controls the action date']),
                    'wrapper discrepancy qualification absent')
        require(current==old,'prior action changed beyond disclosed qualification')
    sources={s['source_id']:s for s in capture['sources']}
    require(len(sources)==len(capture['sources']),'duplicate source identity')
    for source in old_capture['sources']:
        require(sources[source['source_id']]==source,'retained prior source changed')
    for source in sources.values():
        require('unblock.federalregister.gov' not in source['url'] and
                'Federal Register :: Request Access' not in source.get('text','') and
                'Page Not Found' not in source.get('text',''),'denied/error response promoted')
    ids=['action_id','session','roll','date','measure','question','member_action']
    rows={r['action_id']:r for r in universe['candidate_dispositions']}
    require(len(rows)==676 and [[r[k] for k in ids] for r in universe['candidate_dispositions']]==
            [[r[k] for k in ids] for r in old_universe['candidate_dispositions']],'676 discovery identities changed')
    require(dict(Counter(r['disposition'] for r in rows.values()))=={
        'interpreted_substantive_directional':12,'interpreted_substantive_non_directional':1,
        'procedural_context':4,'source_unresolved':658,'pending_interpretation':1},'conservation differs')
    require(universe['accounting']['action_ids_by_disposition']=={
        k:[r['action_id'] for r in universe['candidate_dispositions'] if r['disposition']==k]
        for k in universe['accounting']['counts']},'disposition identity buckets differ')
    accounting=universe['accounting']
    require(all(accounting[k]==v for k,v in dict(total_candidate_actions=676,substantive_eligible_actions=13,
        directional_substantive_actions=12,non_directional_substantive_actions=1,procedural_context_actions=4,
        unresolved_boundary_cases=659,independent_episode_count=13,multi_action_episode_count=0).items()) and
        accounting['official_source_readiness']['ready_substantive_actions']==13 and
        accounting['official_source_readiness']['substantive_actions']==13 and
        accounting['mechanism_types']==['final_passage','suspension_and_passage'],
        'aggregate accounting or readiness differs')
    pending=[r for r in rows.values() if r['unresolved_reason']=='pending_research']
    require(len(pending)==657 and all(not r['review_progress']['substantive_review_performed'] and
        not r['review_progress']['required_evidence_unavailable'] and r['episode_candidate_id'] is None
        for r in pending),'ordinary pending misrepresented')
    require(rows[HOLD]==next(r for r in old_universe['candidate_dispositions'] if r['action_id']==HOLD),
            'protected source hold changed')
    p=rows[PACKAGE]
    require(p['disposition']=='pending_interpretation' and p['review_progress']['substantive_review_performed'] and
            not p['review_progress']['required_evidence_unavailable'] and
            p['review_progress']['exact_action_binding_unresolved'] and not p['exact_action_source_binding']['complete'] and
            p['episode_candidate_id'] is None and PACKAGE not in by,'unfinished package misrepresented')
    require(all(rows[aid]['disposition']=='procedural_context' and aid not in by and
                rows[aid]['episode_candidate_id'] is None for aid in CONTROLS),'procedure became counting')
    require(all(not universe[k] for k in ['full_record_claim','synthesis_eligible','full_issue_universe_closed',
        'publication_authorized','publication_changes','production_writes','episode_acceptance_authorized',
        'synthesis_authorized']) and universe['approval_receipt'] is None,'reserved authority changed')
    records={r['action_id']:r for r in membership['records']}
    require(set(records)=={r['action_id'] for r in old_membership['records']}|NEW|CONTROLS|{PACKAGE},'screening set differs')
    for record in old_membership['records']:
        require(records[record['action_id']]==record,'prior membership changed')
    for aid,rec in records.items():
        row=rows[aid];clerk=sources[f"clerk:119:{row['session']}:{row['roll']}"]
        require(clerk['metadata']['vote-question']==row['question'],'exact question differs')
        status=official_status(clerk['member_records']['F000477']['official_label'])
        # The fixed inventory contains both canonical and original official labels.
        require(official_status(row['member_action'].replace('_',' ').title())==status,
                'official universe observation differs')
        if aid in by:
            expected='interpreted_substantive_non_directional' if status in ['Present','Not Voting'] else 'interpreted_substantive_directional'
            require(row['disposition']==expected,'nondirectional disposition contradicts official status')
    assert_neutral(author['actions']);assert_neutral(membership['records'])
    for action in author['actions']:
        prose=' '.join([action['meaning'],action['compact_description'],*action['limitations']])
        require(re.search(r'\b(?:Health|Infrastructure|Immigration|Education)\s+(?:membership|inclusion|eligibility)\b',prose,re.I) is None,
                'issue-specific membership in shared core')
    for bill,required in [(3062,'govinfo:16usc824a-2024-operative'),(2659,'govinfo:5usc1008-2024-operative'),
                          (2683,'olrc:50usc4801-2024-operative'),(2683,'olrc:50usc4819-2024-operative')]:
        require(required in next(a for a in author['actions'] if a['bill_number']==bill)['compact_source_refs'],
                'compact lost material baseline provenance')
    version_checks=versions(sources);prior_versions(sources)
    require('Passed the House of Representatives September 18, 2025.' in sources['govinfo:hr3062eh']['text'] and
        sources['clerk:119:1:277']['metadata']['action-date']=='18-Sep-2025','HR3062 passage version differs')
    core,mapping,projections,inputs,result=prepare(author,capture,['F000477','M001184'])
    readable=readable_candidates(author,core,projections,result)
    proof=reproducibility_proof(author,capture,['F000477','M001184'])
    cores={a['action_id']:a for a in core['actions']}
    for member in readable['members']:
        expected=12 if member['member_id']=='F000477' else 10
        require(len(member['findings'])==expected,'finding count includes noncounting action')
        for finding in member['findings']:
            for observation in finding['action_observations']:
                shared=cores[observation['action_id']]
                require(observation['status'] in ['Yea','Nay'] and
                        observation['detail'][1]==shared['candidate_exact_action_meaning'] and
                        observation['qualifications']==shared['candidate_shared_limitations'],
                        'generated shared copy changed or nondirectional finding produced')
    for member in result.compiled_ir['members']:
        expected_nv=1 if member['member_id']=='F000477' else 3
        require(member['coverage']['not_voting_actions']==expected_nv and
                member['coverage']['directional_yes_no_positions']==13-expected_nv,'Not Voting became directional')
    products=dict(shared_action_core=core,shared_issue_mapping=mapping,member_projections=projections,
        compiler_input=inputs,compiled_ir=result.compiled_ir,readable_candidates=readable,reproducibility_proof=proof)
    if check_files:
        for name,value in products.items():
            expected=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').replace('\n',os.linesep).encode()
            require((DATA/'generated'/f'{name}.json').read_bytes()==expected,f'generated replay differs: {name}')
        packet=(ROOT/'docs/review_packets/infrastructure_candidate_batch3.md').read_text(encoding='utf-8')
        region=packet.split('<!-- GENERATED CANDIDATE START -->\n',1)[1].split('<!-- GENERATED CANDIDATE END -->',1)[0]
        require(region==review_text(author,core,projections,result,capture),'readable packet replay differs')
        receipt=read(DATA/'source_reuse_and_version_receipt.json')
        for row in receipt['reused_sources']:
            require(row['source_object_sha256']==digest(sources[row['source_id']]),'source reuse receipt differs')
        for row,recorded in zip(version_checks,receipt['floor_version_checks'],strict=True):
            require(all(recorded[k]==v for k,v in row.items()),'version receipt differs')
    return dict(identity_count=676,new_screenings=7,new_meanings=4,combined_meanings=13,
        procedural_controls=4,ordinary_pending_screenings=657,ordinary_pending_interpretation_ids=[PACKAGE],
        protected_examined_hold_ids=[HOLD],source_count=len(sources),member_observations=26,
        finding_counts={m['member_id']:len(m['findings']) for m in readable['members']},
        not_voting_counts={m['member_id']:m['coverage']['not_voting_actions'] for m in result.compiled_ir['members']},
        floor_version_checks=version_checks,core_sha256=core['corpus_sha256'],compiled_sha256=digest(result.compiled_ir),
        prior_actions_unchanged_except_disclosed_hr1223_qualification=True,prior_source_objects_unchanged=True,
        member_neutral_prose=True,byte_identical_generated_replay=check_files,independent_batch_semantic_review='pending',
        full_issue_universe_closed=False,publication_authorized=False,production_writes=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--receipt',type=Path);args=parser.parse_args()
    result=validate(*[read(DATA/f'{n}.json') for n in ['authoring','sources','universe_proposal','membership_review']])
    if args.receipt:args.receipt.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':main()
