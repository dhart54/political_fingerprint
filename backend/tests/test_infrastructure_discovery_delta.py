import copy,unittest
from backend.app.semantic_ir.shared_corpus import digest,sealed_digest
from scripts.validate_infrastructure_discovery_delta import CASES,folder,read,validate
class InfrastructureDiscoveryDeltaTests(unittest.TestCase):
    def test_each_complete_increment(self):
        for n in CASES:
            with self.subTest(batch=n):self.assertTrue(validate(n)['generated_replay'])
    def test_prior_hold_cannot_be_closed_by_new_screening(self):
        v=[read(folder(8)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];r=next(r for r in v[2]['candidate_dispositions'] if r['action_id']=='house:119:1:111');r['disposition']='exact_action_ineligible';v[2]['universe_subject_sha256']=digest(dict(subject=v[2]['subject'],cutoff=v[2]['cutoff'],candidate_records=v[2]['candidate_dispositions']));v[2]['proposal_sha256']=sealed_digest(v[2],'proposal_sha256')
        with self.assertRaises(ValueError):validate(8,v,check_files=False)
    def test_incorporated_recommendations_cannot_drop_last_five(self):
        v=[read(folder(8)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];s=next(s for s in v[1]['sources'] if s['source_id']=='doj-oig:23-034-recommendations-infra8');s['text']=s['text'].split('5.')[0];s['governed_bytes_sha256']=sealed_digest(s,'governed_bytes_sha256')
        with self.assertRaises(ValueError):validate(8,v,check_files=False)
    def test_shared_authoring_cannot_name_projected_member(self):
        v=[read(folder(8)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];v[0]['actions'][-1]['meaning']+=' Massie supported this.'
        with self.assertRaisesRegex(ValueError,'member/party contamination'):validate(8,v,check_files=False)
    def test_universe_authority_stays_reserved(self):
        v=[read(folder(8)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];v[2]['publication_authorized']=True;v[2]['proposal_sha256']=sealed_digest(v[2],'proposal_sha256')
        with self.assertRaises(ValueError):validate(8,v,check_files=False)
if __name__=='__main__':unittest.main()
