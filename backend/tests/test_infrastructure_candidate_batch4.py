import copy
import unittest
from backend.app.semantic_ir.shared_corpus import sealed_digest
from scripts.validate_infrastructure_candidate_batch4 import DATA,read,validate,versions


class InfrastructureBatch4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.values=[read(DATA/f'{n}.json') for n in ['authoring','sources','universe_proposal','membership_review']]

    def test_real_replay_conserves_four_not_voting_observations(self):
        r=validate(*self.values);self.assertEqual(r['not_voting_counts'],{'F000477':1,'M001184':3});self.assertEqual(r['finding_counts'],{'F000477':14,'M001184':12})

    def test_failed_majority_suspension_cannot_be_called_passage(self):
        ss={s['source_id']:copy.deepcopy(s) for s in self.values[1]['sources']};s=ss['clerk:119:2:72'];s['metadata']['vote-result']='Passed';s['governed_bytes_sha256']=sealed_digest(s,'governed_bytes_sha256')
        with self.assertRaisesRegex(ValueError,'failed suspension outcome'):versions(ss)

    def test_complete_adopted_print_cannot_omit_tax_title(self):
        ss={s['source_id']:copy.deepcopy(s) for s in self.values[1]['sources']};s=ss['house:rcp119-18-complete'];s['page_extracts']=s['page_extracts'][:3];s['governed_bytes_sha256']=sealed_digest(s,'governed_bytes_sha256')
        with self.assertRaisesRegex(ValueError,'complete adopted print missing pages'):versions(ss)

    def test_floor_package_cannot_silently_change_repeal_scope(self):
        ss={s['source_id']:copy.deepcopy(s) for s in self.values[1]['sources']};s=ss['congressional-record:2026-02-23-6329-rotor'];s['text']=s['text'].replace('Section 373(a)','Section 373(b)');self.assertNotEqual(s['text'],next(x for x in self.values[1]['sources'] if x['source_id']==s['source_id'])['text']);s['governed_bytes_sha256']=sealed_digest(s,'governed_bytes_sha256')
        with self.assertRaisesRegex(ValueError,'S2503 full floor body differs'):versions(ss)

    def test_compact_cannot_drop_material_already_enacted_tax_context(self):
        v=copy.deepcopy(self.values);next(a for a in v[0]['actions'] if a['bill_number']==2189)['compact_source_refs'].remove('govinfo:pl119-21-firearm-tax-baseline')
        with self.assertRaisesRegex(ValueError,'compact lost material baseline'):validate(*v,check_files=False)

    def test_shared_core_cannot_carry_domain_membership_conclusion(self):
        v=copy.deepcopy(self.values);next(a for a in v[0]['actions'] if a['bill_number']==2189)['meaning']+=' Infrastructure membership is settled.'
        with self.assertRaisesRegex(ValueError,'issue-specific membership'):validate(*v,check_files=False)

if __name__=='__main__':unittest.main()
