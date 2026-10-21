import copy
import unittest
from backend.app.semantic_ir.shared_corpus import sealed_digest
from scripts.validate_infrastructure_candidate_batch5 import DATA,read,validate,validate_taxonomy


class InfrastructureBatch5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.values=[read(DATA/f'{n}.json') for n in ['authoring','sources','universe_proposal','membership_review']]

    def test_real_replay_preserves_corrected_actor_and_nondirectional_boundaries(self):
        r=validate(*self.values);self.assertEqual(r['finding_counts'],{'F000477':18,'M001184':16});self.assertEqual(r['not_voting_counts'],{'F000477':1,'M001184':3})

    def test_source_backed_regression_operator_alternatives_are_not_mandatory(self):
        v=copy.deepcopy(self.values);r=read(DATA/'candidate_correction_receipt.json');source=next(s for s in v[1]['sources'] if s['source_id']==r['controlling_source_id'])
        self.assertIn('the Administrator shall establish performance requirements',r['controlling_complete_clause']);self.assertIn(r['controlling_complete_clause'],source['text'])
        a=next(a for a in v[0]['actions'] if a['action_id']=='house:119:2:72');a['meaning']=a['meaning'].replace(r['corrected_s2503_passage'],r['defective_s2503_preimage'])
        with self.assertRaisesRegex(ValueError,'alternative pathway actor'):validate(*v,check_files=False)

    def test_inherited_public_law_label_cannot_be_silently_rewritten(self):
        v=copy.deepcopy(self.values);s=next(s for s in v[1]['sources'] if s['source_id']=='govinfo:pl119-21-firearm-tax-baseline');s['text_version']='Public Law119-21';s['governed_bytes_sha256']=sealed_digest(s,'governed_bytes_sha256')
        with self.assertRaisesRegex(ValueError,'source identity differs|source changed|source identity|source binding'):validate(*v,check_files=False)

    def test_public_law_qualification_cannot_be_dropped_from_active_copies(self):
        v=copy.deepcopy(self.values);next(a for a in v[0]['actions'] if a['action_id']=='house:119:2:70')['limitations'].pop()
        with self.assertRaisesRegex(ValueError,'Public Law label qualification'):validate(*v,check_files=False)

    def test_structural_test_success_cannot_accept_taxonomy(self):
        rec=read(DATA/'hr2189_taxonomy_recommendation.json');rec['structural_tests_are_semantic_approval']=True
        with self.assertRaisesRegex(ValueError,'taxonomy recommendation conferred authority'):validate_taxonomy(rec)

    def test_new_compact_cannot_drop_material_existing_direct911_baseline(self):
        v=copy.deepcopy(self.values);next(a for a in v[0]['actions'] if a['bill_number']==5201)['compact_source_refs'].remove('govinfo:47usc623-2024-multiline911')
        with self.assertRaisesRegex(ValueError,'compact lost material baseline'):validate(*v,check_files=False)

if __name__=='__main__':unittest.main()
