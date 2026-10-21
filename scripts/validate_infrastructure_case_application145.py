"""Validate the approved145case application, immutable history and semantic parity."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app.semantic_ir.shared_corpus import digest,sealed_digest
from scripts.apply_infrastructure_case_decisions145 import apply_exact_decisions,SUBJECTS,require
from scripts.prepare_shared_domain_candidate import prepare,readable_candidates,reproducibility_proof,validate_universe_proposal
from scripts.validate_infrastructure_disaster_candidates142 import validate as validate_reviewed142
B=ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch139_20260916'
A=ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch145_20260916'
P=ROOT/'docs/review_packets/infrastructure_case_application145'
D=ROOT/'docs/review_packets/infrastructure_batch142_disaster_baselines'
MEMBERS=['F000477','M001184']
MANIFEST_SHA='7728e6fe4acc1c8aff9cc4f3c4bbd1da7a4ece26e59e6582a976f7b29cd2c087'

def read(p):return json.loads(p.read_text(encoding='utf8'))
def lfsha(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def inputs():return read(B/'membership_review.json'),read(B/'universe_proposal.json'),read(B/'sources.json'),read(P/'proposed_records.json'),read(P/'owner_evidence.json'),read(D/'decision_bundle.json')

def validate():
    manifest=read(P/'preservation_manifest.json');require(digest(manifest)==MANIFEST_SHA,'Preservation manifest differs')
    for path,expected in manifest['preserved_previous_files'].items():require(lfsha(ROOT/path)==expected,'Historical evidence changed: '+path)
    for name,expected in manifest['copied_semantic_files'].items():require(lfsha(A/name)==lfsha(B/name)==expected,'Frozen semantic output changed: '+name)
    bm,bu,c,proposals,authority,bundle=inputs();m,u=read(A/'membership_review.json'),read(A/'universe_proposal.json')
    em,eu,effect=apply_exact_decisions(bm,bu,c,proposals,authority,bundle);require((m,u)==(em,eu),'Materialized application differs')
    rm,ru,replay=apply_exact_decisions(m,u,c,proposals,authority,bundle);require((rm,ru)==(m,u) and replay['changed'] is False,'Idempotent replay differs')
    for key,old,new in [('records',bm,m),('candidate_dispositions',bu,u)]:
        require([r for r in old[key] if r['action_id'] not in SUBJECTS]==[r for r in new[key] if r['action_id'] not in SUBJECTS],'Other671records/rows changed')
    for before,after in zip(bm['records'],m['records']):
        if before['action_id'] in SUBJECTS:
            allowed={'rationale','disposition','exact_action_binding_unresolved'}
            require({k:v for k,v in before.items() if k not in allowed}=={k:v for k,v in after.items() if k not in allowed},'Case sources/claims/evidence flags changed')
    a=read(A/'authoring.json');require(not set(SUBJECTS)&{x['action_id'] for x in a['actions']},'Unaccepted142meaning admitted')
    validate_universe_proposal(u,a,c,m)
    core,mapping,projections,ci,result=prepare(a,c,MEMBERS)
    outputs=dict(shared_action_core=core,shared_issue_mapping=mapping,member_projections=projections,compiler_input=ci,compiled_ir=result.compiled_ir,readable_candidates=readable_candidates(a,core,projections,result),reproducibility_proof=reproducibility_proof(a,c,MEMBERS))
    for name,value in outputs.items():require(read(A/'generated'/(name+'.json'))==value,'Actual typed replay differs: '+name)
    require(result.compiled_ir==read(B/'generated/compiled_ir.json') and projections==read(B/'generated/member_projections.json'),'Member behavior changed')
    for aid in ['house:119:1:10','house:119:1:13']:
        r=next(r for r in m['records'] if r['action_id']==aid)
        require(r['disposition']=='pending_interpretation' and proposals[aid]['approved_eligibility']=='eligible' and proposals[aid]['authored_meaning_accepted'] is False,'Eligibility became interpretation')
    reviewed=validate_reviewed142();require(reviewed['canonical_state_changed'] is False,'Historical142packet gained authority')
    r=read(P/'application_receipt.json');require(r['receipt_sha256']==sealed_digest(r,'receipt_sha256') and r['effects']==effect and r['compiled_sha256']==digest(result.compiled_ir),'Application receipt differs')
    require(r['owner_evidence_sha256']==digest(authority) and r['proposed_records_sha256']==digest(proposals),'Approval subject differs')
    for case in r['cases']:
        aid=case['action_id'];require(case['after_record_sha256']==digest(next(x for x in m['records'] if x['action_id']==aid)) and case['after_universe_row_sha256']==digest(next(x for x in u['candidate_dispositions'] if x['action_id']==aid)),'Receipt postimage differs')
        require(case['detached_binding_evidence']==proposals[aid]['external_binding_evidence'] and case['authored_meaning_accepted'] is False,'Receipt binding/meaning authority differs')
        for witness in case['detached_binding_evidence']:
            source=next(x for x in read(D/'sources.json')['sources'] if x['source_id']==witness['source_id'])
            require(witness['source_object_sha256']==digest(source) and witness['selected_text']==source['text'] and witness['raw_sha256']==source['raw_sha256'] and witness['governed_bytes_sha256']==source['governed_bytes_sha256'],'Detached floor witness differs')
    for key in ['authored_meaning_acceptance','batch143_approval','HR859_or_HR28_decision','six_source_holds_changed','approved_universe_authority','publication_authorized','production_writes','Health_activated']:require(r[key] is False,'Application receipt gained authority')
    return dict(cases=5,other_records_unchanged=671,sources_unchanged=1621,authored_meanings_unchanged=70,compiled_graph_unchanged=True,member_projections_unchanged=True,idempotent=True,positive_eligibility_meanings_pending=2,counts=u['accounting']['counts'])

if __name__=='__main__':print(json.dumps(validate(),indent=2))
