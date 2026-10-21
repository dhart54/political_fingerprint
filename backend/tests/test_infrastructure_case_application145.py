import copy,unittest
from backend.app.semantic_ir.shared_corpus import digest,sealed_digest
from scripts.apply_infrastructure_case_decisions145 import apply_exact_decisions,SUBJECTS
from scripts.validate_infrastructure_case_application145 import A,P,read,inputs,validate

class ExactCaseApplication145Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m,cls.u,cls.c,cls.p,cls.a,cls.b=inputs();cls.am=read(A/'membership_review.json');cls.au=read(A/'universe_proposal.json')
    def apply(self,m=None,u=None,c=None,p=None,a=None,b=None):
        return apply_exact_decisions(self.m if m is None else m,self.u if u is None else u,self.c if c is None else c,self.p if p is None else p,self.a if a is None else a,self.b if b is None else b)
    def test_actual_application_preserves_all_semantic_and_member_outputs(self):
        r=validate();self.assertEqual((r['other_records_unchanged'],r['sources_unchanged'],r['authored_meanings_unchanged']),(671,1621,70));self.assertTrue(r['compiled_graph_unchanged']);self.assertTrue(r['member_projections_unchanged'])
    def test_pure_idempotent_application_keeps_positive_eligibility_uninterpreted(self):
        old=digest([self.m,self.u]);m,u,e=self.apply();self.assertEqual((m,u),(self.am,self.au));self.assertTrue(e['changed']);self.assertEqual(old,digest([self.m,self.u]));m2,u2,e2=self.apply(m=m,u=u);self.assertFalse(e2['changed']);self.assertEqual((m2,u2),(m,u));self.assertIsNot(m2,m)
        for aid in ['house:119:1:10','house:119:1:13']:
            self.assertEqual(next(r for r in m['records'] if r['action_id']==aid)['disposition'],'pending_interpretation');self.assertEqual(self.p[aid]['approved_eligibility'],'eligible');self.assertIs(self.p[aid]['authored_meaning_accepted'],False)
    def test_approval_cannot_expand_to_meaning_143_or_unrelated_cases(self):
        for edit in ['meaning','143','cohort','transcript']:
            bad=copy.deepcopy(self.a)
            if edit=='meaning':bad['scope']['authored_meaning_acceptance']=True
            elif edit=='143':bad['scope']['batch143_approval']=True
            elif edit=='cohort':bad['scope']['case_actions'].append('house:119:1:109')
            else:bad['approval_transcript']+=' inferred approval'
            with self.subTest(edit=edit),self.assertRaisesRegex(ValueError,'approval'):self.apply(a=bad)
    def test_post_application_authority_drift_is_rejected_even_when_resealed(self):
        for key,value in [('publication_authorized',True),('full_record_claim',True),('approval_receipt',{'fake':True}),('synthesis_eligible',True),('production_writes',True)]:
            bad=copy.deepcopy(self.au);bad[key]=value;bad['proposal_sha256']=sealed_digest(bad,'proposal_sha256')
            with self.subTest(key=key),self.assertRaises(ValueError):self.apply(m=self.am,u=bad)
        bad=copy.deepcopy(self.am);bad['authoritative_for_new_editorial_work']=0;bad['review_sha256']=sealed_digest(bad,'review_sha256')
        with self.assertRaisesRegex(ValueError,'authority'):self.apply(m=bad,u=self.au)
    def test_post_application_derived_and_unrelated_row_drift_cannot_noop(self):
        for edit in ['counts','groups','readiness','unresolved','unrelated']:
            bad=copy.deepcopy(self.au)
            if edit=='counts':bad['accounting']['counts']['pending_interpretation']+=1
            elif edit=='groups':bad['accounting']['action_ids_by_disposition']['pending_interpretation'].pop()
            elif edit=='readiness':bad['accounting']['official_source_readiness']['pending_package_version_bindings']+=1
            elif edit=='unresolved':bad['unresolved_action_ids'].pop()
            else:bad['candidate_dispositions'][0]['rationale']+=' unauthorized drift'
            bad['proposal_sha256']=sealed_digest(bad,'proposal_sha256')
            with self.subTest(edit=edit),self.assertRaises(ValueError):self.apply(m=self.am,u=bad)
    def test_preimage_drift_and_partial_application_require_reconciliation(self):
        for edit in ['case','unrelated','partial']:
            bad=copy.deepcopy(self.m)
            if edit=='case':next(r for r in bad['records'] if r['action_id']=='house:119:1:88')['rationale']+=' drift'
            elif edit=='unrelated':bad['records'][0]['rationale']+=' drift'
            else:bad['records'][8]=copy.deepcopy(self.am['records'][8])
            bad['review_sha256']=sealed_digest(bad,'review_sha256')
            with self.subTest(edit=edit),self.assertRaises(ValueError):self.apply(m=bad)
    def test_literal_binding_proposals_and_reviewed_bundle_cannot_drift(self):
        for edit in ['binding','meaning','rationale']:
            bad=copy.deepcopy(self.p)
            if edit=='binding':bad['house:119:1:88']['external_binding_evidence'][0]['selected_text']='Different floor action'
            elif edit=='meaning':bad['house:119:1:10']['authored_meaning_accepted']=True
            else:bad['house:119:1:49']['proposed_record']['rationale']='Blanket disaster exclusion'
            with self.subTest(edit=edit),self.assertRaises(ValueError):self.apply(p=bad)
        bad=copy.deepcopy(self.b);bad['cases'][4]['candidate_action_core_sha256']='0'*64;bad['bundle_sha256']=sealed_digest(bad,'bundle_sha256')
        with self.assertRaisesRegex(ValueError,'bundle drift'):self.apply(b=bad)
    def test_registered_source_and_official_member_drift_are_rejected(self):
        for edit in ['unrelated_source','member_status']:
            bad=copy.deepcopy(self.c)
            if edit=='unrelated_source':next(s for s in bad['sources'] if s.get('text'))['text']+=' source drift'
            else:next(s for s in bad['sources'] if s['source_id']=='clerk:119:1:13')['member_records']['M001184']['official_label']='Yea'
            with self.subTest(edit=edit),self.assertRaisesRegex(ValueError,'sources'):self.apply(c=bad)

if __name__=='__main__':unittest.main()
