"""Pure bounded application of the five eligibility/binding decisions approved21:17UTC."""
import copy
import hashlib
from collections import Counter
from backend.app.semantic_ir.shared_corpus import digest,sealed_digest

BUNDLE_SHA='5ae115e381d009896db611688182d6c273bbcf293b05dbf1765bde8487ad6003'
TRANSCRIPT_SHA='2e6c9a82de5b6aa4c168c5e861723732e2eb1b7f6172527c58b121803ecd0e2a'
AUTHORITY_SHA='b1c8f9f65803e58e449a4dd6a0e62327f968db031eb51cba609f94336a7f4948'
CAPTURE_SHA='e4ef4934ca795fab9e04ed0a91dd33e4fd1ef2a5b77792435a3802bbd0e65032'
PROPOSALS_SHA='f559ca456dd99ba8ef204405c8527867d5733f08c57ffa6f5554ee816dc43568'
SUBJECTS={'house:119:1:9': ('2639745f7f9e758153ebe4876459c4df8b54e04b41b170fe0626e4a9798f3c20', '8535f5e51c2ac7e3903be992be8d3ad13a0dc4959abe8b0979d6ee9765dc60ad', 'b2ab9bdc81d9906936c90e86832cc9a25ac54b383ae8f4df4d2178e8a21f8bc9', 'pending_interpretation'), 'house:119:1:10': ('16f44bc28fe31a7829e78090c6254cd90c641304b72f8135762ba1db5ce4de6b', 'd01d5b314be63120bbed30213655309490b52e72987f75a1de58fdcc60d40d52', '99cf717f8d1aac858e704fc96c086240e8a327dffaf31da10dd1264ed2dd2498', 'pending_interpretation'), 'house:119:1:13': ('20434d69e61edac2472408ca880d0e39e89900bdcf0e3df76f9673d6e01d6d52', '40376fe6d25c5baf405ebbcedc0e117939d018452d3693c81bbf84037ac02d20', '81a588a9a102b621626e97ad7589f65c8673ae55ebbd19c07349d4d8f4931f42', 'pending_interpretation'), 'house:119:1:49': ('7fd151cb8bf17ddcbf1eac84ed47cad037ed29fc9a263d647203a3aea1da1bda', '784ee6dbf3b7c144deccb8102dc6369a6646789d5b913ba3a174ec5faa90ea49', 'd6f39f2d0f6df1fd61fa95b9d0225a0a09db55959148a1617afb156da1381a99', 'exact_action_ineligible'), 'house:119:1:88': ('192ea228cc811c7976ed60e55ec1069b04e074c7ce69f33e900e09eaa84cdf10', 'bcb95e070b1bb0e8eb3fea3d3496262cc1bb6de160cdde9d1d4e6a1df930759d', '14b1941854a520f849b5a78b1b55de56c2d8572a36dc8f0bf8ca497d1035e9b6', 'exact_action_ineligible')}
STATE_SEALS={False:('d149216e429afa0d988bd9f4aa29573997814b9ea578f652715f5a4116e8754b','4c15b2dd9624ba0aca3710bfcb78612be6120b22612167f45b51c03756d017fa'),True:('25d5609f2107fa1042646e1cd7b8063bc93cf2481bd586cd8fbb02e270db9419','fc4e7aa610d0c826eb5c778cd76b439e0578f6535067e42a188814b8362187e3')}
BOUNDARY=('Owner-approved exact batch142 case application only: H.R.153/H.R.164 eligibility approved but meanings remain unaccepted and pending interpretation; H.R.804/H.R.1491 excluded; H.R.1491 reviewed amended-action binding resolved; H.R.152 retained pending its exact scope judgment. All other records, sources, meanings, holds and semantic outputs preserved. No general rule, universe, editorial, publication or production authority.')

def require(value,message):
    if not value:raise ValueError(message)


def validate_state(m,u,applied):
    require(m['authoritative_for_new_editorial_work'] is False and u['approval_receipt'] is None
            and all(u[k] is False for k in ['full_record_claim','synthesis_eligible','publication_authorized','episode_acceptance_authorized','synthesis_authorized','publication_changes','production_writes','full_issue_universe_closed']), 'Application escalated authority')
    counts=dict(Counter(r['disposition'] for r in u['candidate_dispositions']))
    require(u['accounting']['counts']==counts and u['accounting']['action_ids_by_disposition']=={k:[r['action_id'] for r in u['candidate_dispositions'] if r['disposition']==k] for k in counts},'Derived accounting differs')
    require(u['unresolved_action_ids']==[r['action_id'] for r in u['candidate_dispositions'] if r['disposition'] in ['source_unresolved','pending_interpretation']], 'Unresolved accounting differs')
    ms,us=STATE_SEALS[applied]
    require(m['review_sha256']==sealed_digest(m,'review_sha256')==ms,'Bounded membership state differs')
    require(u['proposal_sha256']==sealed_digest(u,'proposal_sha256')==us and u['membership_review_sha256']==ms
            and u['universe_subject_sha256']==digest(dict(subject=u['subject'],cutoff=u['cutoff'],candidate_records=u['candidate_dispositions'])),'Bounded universe state differs')


def _materialize(membership,universe,proposals):
    m,u=copy.deepcopy(membership),copy.deepcopy(universe)
    changed={aid:copy.deepcopy(p['proposed_record']) for aid,p in proposals.items()}
    m['records']=[changed.get(r['action_id'],r) for r in m['records']]
    m['review_sha256']=sealed_digest(m,'review_sha256')
    for row in u['candidate_dispositions']:
        if row['action_id'] not in changed:continue
        r=changed[row['action_id']]
        row.update(disposition=r['disposition'],reason=r['rationale'],rationale=r['rationale'],issue_boundary_status=r['disposition'])
        row['unresolved_reason']=None if r['disposition']=='exact_action_ineligible' else ('Authored meaning acceptance remains pending after case-specific eligibility approval.' if row['action_id'] in ['house:119:1:10','house:119:1:13'] else 'Exact-case eligibility scope judgment and authored meaning acceptance remain pending.')
        row['exact_action_source_binding']['complete']=not r['exact_action_binding_unresolved']
        row['review_progress'].update({k:r[k] for k in ['substantive_review_performed','exact_action_binding_unresolved','required_evidence_unavailable','authoritative_source_conflict']})
        row['review_progress']['shared_review_record_sha256']=digest(r)
    counts=dict(Counter(r['disposition'] for r in u['candidate_dispositions']))
    u.update(proposal_id='full-universe-proposal:f000477:infrastructure:119:20260916:candidate-batch145',membership_review_sha256=m['review_sha256'],unresolved_action_ids=[r['action_id'] for r in u['candidate_dispositions'] if r['disposition'] in ['source_unresolved','pending_interpretation']])
    u['accounting'].update(counts=counts,action_ids_by_disposition={k:[r['action_id'] for r in u['candidate_dispositions'] if r['disposition']==k] for k in counts},exact_action_ineligible_actions=counts['exact_action_ineligible'],unresolved_boundary_cases=len(u['unresolved_action_ids']),accounting_scope=BOUNDARY)
    u['accounting']['official_source_readiness']['pending_package_version_bindings']=counts['pending_interpretation']
    u['universe_subject_sha256']=digest(dict(subject=u['subject'],cutoff=u['cutoff'],candidate_records=u['candidate_dispositions']))
    u['proposal_sha256']=sealed_digest(u,'proposal_sha256')
    return m,u


def apply_exact_decisions(membership,universe,capture,proposals,authority,bundle):
    """Validate exact approval, case and whole-state seals before every write/no-write path."""
    require(digest(authority)==AUTHORITY_SHA and hashlib.sha256(authority['approval_transcript'].encode()).hexdigest()==TRANSCRIPT_SHA,'Owner evidence or bounded approval scope differs')
    require(digest(bundle)==BUNDLE_SHA and bundle['bundle_sha256']==sealed_digest(bundle,'bundle_sha256'),'Reviewed decision bundle drift')
    require(digest(capture)==CAPTURE_SHA and digest(proposals)==PROPOSALS_SHA,'Frozen sources or bounded proposals differ')
    require(set(proposals)==set(SUBJECTS)==set(c['action_id'] for c in bundle['cases']),'Approved action cohort differs')
    records={r['action_id']:r for r in membership['records']};rows={r['action_id']:r for r in universe['candidate_dispositions']};sources={s['source_id']:s for s in capture['sources']}
    require(len(records)==len(rows)==676 and len(sources)==1621,'Universe/source population differs')
    already=[]
    for aid,(before,row_before,after,decision) in SUBJECTS.items():
        p=proposals[aid];r=p['proposed_record'];case=next(c for c in bundle['cases'] if c['action_id']==aid)
        require(case['candidate_sha256']==sealed_digest(case,'candidate_sha256') and case['governed_before_record_sha256']==before and case['governed_before_row_sha256']==row_before,'Reviewed case preimage drift')
        require(digest(r)==p['proposed_record_sha256']==after and r['action_id']==aid and r['disposition']==decision
                and p['approved_candidate_sha256']==case['candidate_sha256'] and p['authored_meaning_accepted'] is False,'Approved proposed subject drift')
        current=digest(records[aid]);require(current in {before,after},'Current subject drift: '+aid);is_after=current==after;already.append(is_after)
        if not is_after:require(digest(rows[aid])==row_before,'Current universe row drift: '+aid)
        require(r['exact_action_binding_unresolved'] is False and r['required_evidence_unavailable'] is r['authoritative_source_conflict'] is False,'Unexpected binding/evidence change')
        for ref in r['sources']:
            require(ref['source_id'] in sources and all(sources[ref['source_id']][k]==v for k,v in ref.items()),'Approved source binding drift: '+aid)
        for claim in r['claim_source_map']:
            require(claim['source_id'] in {x['source_id'] for x in r['sources']} and claim['passage'] in sources[claim['source_id']]['text'],'Approved claim drift: '+aid)
    require(all(already) or not any(already),'Partial application requires explicit reconciliation')
    validate_state(membership,universe,all(already))
    if all(already):return copy.deepcopy(membership),copy.deepcopy(universe),dict(changed=False,action_ids=list(SUBJECTS))
    m,u=_materialize(membership,universe,proposals);validate_state(m,u,True)
    counts=u['accounting']['counts'];require(counts['pending_interpretation']==258 and counts['exact_action_ineligible']==124 and counts['source_unresolved']==6,'Expected bounded effects differ')
    return m,u,dict(changed=True,action_ids=list(SUBJECTS),before_counts=universe['accounting']['counts'],after_counts=counts,other_records_unchanged=671,registered_sources_unchanged=1621,eligibility_approved_but_meaning_pending=['house:119:1:10','house:119:1:13'])
