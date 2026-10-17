"""Offline batch4 exact-version, conservation, portability and replay gates."""
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
from scripts.validate_infrastructure_candidate_batch3 import versions as prior_versions
DATA=ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch4_20260916'
PRIOR=ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch3_20260916'
NEW={'house:119:2:70','house:119:2:72'}
CONTROLS={f'house:119:2:{n}' for n in [59,60,61,62]}


def versions(sources):
    record=sources['congressional-record:2026-02-23-6329-rotor']['text']
    parts=re.split(r'PDF PAGE (\d+)\s*\n',record)
    floor=' '.join('\n'.join(parts[n+1].splitlines()[1:]).split('VerDate')[0] for n in range(1,len(parts),2))
    start=floor.index('Be it enacted',floor.index('S. 2503'))
    floor=floor[start:floor.index('The SPEAKER pro tempore.',start)]
    senate=sources['govinfo:s2503es'];text=senate['text'];body=text[text.index('Be it enacted'):text.index('Passed the')]
    normalize=lambda t:re.sub('[^a-z0-9]','',t.lower())
    require(senate['text_version']=='ES' and normalize(floor)==normalize(body),'S2503 full floor body differs')
    clerk=sources['clerk:119:2:72']['metadata']
    require(clerk['vote-result']=='Failed' and clerk['vote-type']=='2/3 YEA-AND-NAY' and
            clerk['action-date']=='24-Feb-2026','failed suspension outcome or resumed date differs')
    rcp=sources['house:rcp119-18-complete'];pieces=[]
    require([p['pdf_page'] for p in rcp['page_extracts']]==list(range(1,8)),'complete adopted print missing pages')
    for page in rcp['page_extracts']:
        pieces.append(re.sub(r'(?m)\d+\s*$','',page['text'].split('VerDate')[0]))
    printed=' '.join(pieces);printed=printed[printed.index('TITLE I'):]
    eh=sources['govinfo:hr2189eh'];text=eh['text'];body2189=text[text.index('TITLE I'):text.index('Passed the')]
    normprint=lambda t:normalize(re.sub(r'\bSEC\.','SECTION',t))
    require(eh['text_version']=='EH' and normprint(printed)==normprint(body2189),'HR2189 full adopted print body differs')
    require('Rules Committee Print 119-18 shall be considered as adopted' in sources['govinfo:hres1057eh']['text'],
            'HR2189 adopted-print authority absent')
    require(sources['clerk:119:2:60']['metadata']['vote-result']=='Failed','failed1042rule outcome differs')
    require(sources['clerk:119:2:62']['metadata']['vote-question']=='On Agreeing to the Resolution, as Amended' and
            sources['clerk:119:2:62']['metadata']['vote-result']=='Passed','1057amended agreement identity differs')
    return [dict(bill='S2503',matched=True,normalized_body_sha256=digest(normalize(body)),
        comparison='Complete operative floor/ES bodies; remove explicit PDF page labels, first header line and VerDate footer; lowercase ASCII-alphanumeric comparison.'),
        dict(bill='HR2189',matched=True,normalized_body_sha256=digest(normprint(body2189)),
        comparison='Complete adopted seven-page RCP119-18/EH bodies from TitleI; remove printed line/page numbers and VerDate footers, map SEC. abbreviation to SECTION, lowercase ASCII-alphanumeric comparison. Original punctuation retained; legal equivalence not certified.')]


def validate(author,capture,universe,membership,*,check_files=True):
    validate_universe_proposal(universe,author,capture,membership)
    old={n:read(PRIOR/f'{n}.json') for n in ['authoring','sources','universe_proposal','membership_review']}
    by={a['action_id']:a for a in author['actions']};sources={s['source_id']:s for s in capture['sources']}
    require(set(by)=={a['action_id'] for a in old['authoring']['actions']}|NEW,'interpretation set differs')
    for action in old['authoring']['actions']:require(by[action['action_id']]==action,'prior action changed')
    for source in old['sources']['sources']:require(sources[source['source_id']]==source,'retained prior source changed')
    require(len(sources)==len(capture['sources']),'duplicate source identity')
    require(all('unblock.federalregister.gov' not in s['url'] and 'Federal Register :: Request Access' not in s.get('text','') and 'Page Not Found' not in s.get('text','') for s in sources.values()),'denied/error response promoted')
    rows={r['action_id']:r for r in universe['candidate_dispositions']};priorrows={r['action_id']:r for r in old['universe_proposal']['candidate_dispositions']}
    fields=['action_id','session','roll','date','measure','question','member_action']
    require(len(rows)==676 and [[r[k] for k in fields] for r in universe['candidate_dispositions']]==[[r[k] for k in fields] for r in old['universe_proposal']['candidate_dispositions']],'676 discovery identities changed')
    for aid,row in rows.items():
        if aid not in NEW|CONTROLS:require(row==priorrows[aid],'unexamined/prior boundary changed')
    require(dict(Counter(r['disposition'] for r in rows.values()))==dict(interpreted_substantive_directional=14,interpreted_substantive_non_directional=1,procedural_context=8,source_unresolved=652,pending_interpretation=1),'conservation differs')
    acc=universe['accounting'];require(acc['action_ids_by_disposition']=={k:[r['action_id'] for r in universe['candidate_dispositions'] if r['disposition']==k] for k in acc['counts']},'disposition identity buckets differ')
    require(all(acc[k]==v for k,v in dict(total_candidate_actions=676,substantive_eligible_actions=15,directional_substantive_actions=14,non_directional_substantive_actions=1,procedural_context_actions=8,unresolved_boundary_cases=653,independent_episode_count=15,multi_action_episode_count=0).items()) and acc['official_source_readiness']['ready_substantive_actions']==15 and acc['official_source_readiness']['substantive_actions']==15,'aggregate accounting or readiness differs')
    require(sum(r['unresolved_reason']=='pending_research' for r in rows.values())==651,'ordinary pending count differs')
    require(all(rows[aid]['disposition']=='procedural_context' and rows[aid]['episode_candidate_id'] is None and aid not in by for aid in CONTROLS),'procedure became counting')
    require(all(not universe[k] for k in ['full_record_claim','synthesis_eligible','full_issue_universe_closed','publication_authorized','publication_changes','production_writes','episode_acceptance_authorized','synthesis_authorized']) and universe['approval_receipt'] is None,'reserved authority changed')
    records={r['action_id']:r for r in membership['records']};require(set(records)=={r['action_id'] for r in old['membership_review']['records']}|NEW|CONTROLS,'screening set differs')
    for rec in old['membership_review']['records']:require(records[rec['action_id']]==rec,'prior membership changed')
    for aid,record in records.items():
        row=rows[aid];clerk=sources[f"clerk:119:{row['session']}:{row['roll']}"];require(clerk['metadata']['vote-question']==row['question'],'exact question differs')
        status=official_status(clerk['member_records']['F000477']['official_label']);require(official_status(row['member_action'].replace('_',' ').title())==status,'official universe observation differs')
        if aid in by:require(row['disposition']==('interpreted_substantive_non_directional' if status in ['Present','Not Voting'] else 'interpreted_substantive_directional'),'nondirectional disposition contradicts official status')
    assert_neutral(author['actions']);assert_neutral(membership['records'])
    for a in author['actions']:
        prose=' '.join([a['meaning'],a['compact_description'],*a['limitations']]);require(re.search(r'\b(?:Health|Infrastructure|Immigration|Education)\s+(?:membership|inclusion|eligibility)\b',prose,re.I) is None,'issue-specific membership in shared core')
    for bill,sid in [(2189,'govinfo:pl119-21-firearm-tax-baseline'),(2189,'govinfo:26usc5845-firearm'),(2503,'govinfo:pl119-60-rotor-373'),(2503,'govinfo:14cfr91-225-2025-sol-slice')]:require(sid in next(a for a in author['actions'] if a['bill_number']==bill)['compact_source_refs'],'compact lost material baseline provenance')
    version_checks=versions(sources);prior_versions(sources)
    core,mapping,projections,inputs,result=prepare(author,capture,['F000477','M001184']);readable=readable_candidates(author,core,projections,result);proof=reproducibility_proof(author,capture,['F000477','M001184']);cores={a['action_id']:a for a in core['actions']}
    for member in readable['members']:
        require(len(member['findings'])==(14 if member['member_id']=='F000477' else 12),'finding count includes noncounting action')
        for finding in member['findings']:
            for obs in finding['action_observations']:
                shared=cores[obs['action_id']];require(obs['status'] in ['Yea','Nay'] and obs['detail'][1]==shared['candidate_exact_action_meaning'] and obs['qualifications']==shared['candidate_shared_limitations'],'generated shared copy changed or nondirectional finding produced')
    for member in result.compiled_ir['members']:
        nv=1 if member['member_id']=='F000477' else 3;require(member['coverage']['not_voting_actions']==nv and member['coverage']['directional_yes_no_positions']==15-nv,'Not Voting became directional')
    products=dict(shared_action_core=core,shared_issue_mapping=mapping,member_projections=projections,compiler_input=inputs,compiled_ir=result.compiled_ir,readable_candidates=readable,reproducibility_proof=proof)
    if check_files:
        for name,value in products.items():require((DATA/'generated'/f'{name}.json').read_bytes()==(json.dumps(value,ensure_ascii=False,indent=2)+'\n').replace('\n',os.linesep).encode(),f'generated replay differs: {name}')
        packet=(ROOT/'docs/review_packets/infrastructure_candidate_batch4.md').read_text(encoding='utf-8');region=packet.split('<!-- GENERATED CANDIDATE START -->\n',1)[1].split('<!-- GENERATED CANDIDATE END -->',1)[0];require(region==review_text(author,core,projections,result,capture),'readable packet replay differs')
        receipt=read(DATA/'source_reuse_and_version_receipt.json');require(receipt['source_acquisitions']==0 and not receipt['protected_denials_retried'],'source restriction declaration differs')
        for row in receipt['reused_sources']:require(row['source_object_sha256']==digest(sources[row['source_id']]),'source reuse receipt differs')
    return dict(identity_count=676,new_screenings=6,new_meanings=2,combined_meanings=15,procedural_controls=8,ordinary_pending_screenings=651,ordinary_pending_interpretation_ids=['house:119:1:218'],protected_examined_hold_ids=['house:119:1:111'],source_count=len(sources),source_acquisitions=0,member_observations=30,finding_counts={m['member_id']:len(m['findings']) for m in readable['members']},not_voting_counts={m['member_id']:m['coverage']['not_voting_actions'] for m in result.compiled_ir['members']},version_checks=version_checks,core_sha256=core['corpus_sha256'],compiled_sha256=digest(result.compiled_ir),prior_actions_sources_and_membership_unchanged=True,member_neutral_prose=True,byte_identical_generated_replay=check_files,independent_batch_semantic_review='pending',full_issue_universe_closed=False,publication_authorized=False,production_writes=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--receipt',type=Path);args=parser.parse_args();r=validate(*[read(DATA/f'{n}.json') for n in ['authoring','sources','universe_proposal','membership_review']])
    if args.receipt:args.receipt.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r))
if __name__=='__main__':main()
