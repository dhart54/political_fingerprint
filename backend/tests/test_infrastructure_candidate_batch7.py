import copy,unittest
from backend.app.semantic_ir.shared_corpus import sealed_digest,digest
from scripts.validate_infrastructure_candidate_batch7 import DATA,read,validate


class InfrastructureBatch7Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.values=[read(DATA/f'{n}.json') for n in ['authoring','sources','universe_proposal','membership_review']]

    def test_exact_screening_preserves_policy_ir(self):
        r=validate(*self.values);self.assertTrue(r['compiled_ir_unchanged']);self.assertEqual(r['new_meanings'],0)

    def test_named_speaker_ballot_cannot_be_normalized_to_nay(self):
        v=copy.deepcopy(self.values);s=next(s for s in v[1]['sources'] if s['source_id']=='clerk:119:1:2');s['member_records']['M001184']['official_label']='Nay';s['governed_bytes_sha256']=sealed_digest(s,'governed_bytes_sha256')
        with self.assertRaisesRegex(ValueError,'source identity differs|named Speaker ballot|raw official'):validate(*v,check_files=False)

    def test_quorum_present_cannot_be_normalized_to_support(self):
        v=copy.deepcopy(self.values);s=next(s for s in v[1]['sources'] if s['source_id']=='clerk:119:1:1');s['member_records']['F000477']['official_label']='Yea';s['governed_bytes_sha256']=sealed_digest(s,'governed_bytes_sha256')
        with self.assertRaisesRegex(ValueError,'source identity differs|quorum Present|raw official'):validate(*v,check_files=False)

    def test_raw_inventory_aye_label_is_preserved(self):
        v=copy.deepcopy(self.values);r=next(r for r in v[2]['candidate_dispositions'] if r['action_id']=='house:119:1:169');r['member_action']='Yea';v[2]['universe_subject_sha256']=digest(dict(subject=v[2]['subject'],cutoff=v[2]['cutoff'],candidate_records=v[2]['candidate_dispositions']));v[2]['proposal_sha256']=sealed_digest(v[2],'proposal_sha256')
        with self.assertRaisesRegex(ValueError,'676identity or raw observation'):validate(*v,check_files=False)

if __name__=='__main__':unittest.main()
