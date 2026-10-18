import copy,unittest
from unittest.mock import patch
import scripts.validate_infrastructure_discovery_delta as delta
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
    def test_authorization_extension_cannot_become_appropriation(self):
        v=[read(folder(10)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];a=next(a for a in v[0]['actions'] if a['action_id']=='house:119:2:304');a['meaning']=a['meaning'].replace('It does not itself make an appropriation.','It appropriates the funds.')
        with self.assertRaisesRegex(ValueError,'authorization/appropriation boundary differs'):validate(10,v,check_files=False)
    def test_consideration_cannot_become_universal_adoption(self):
        v=[read(folder(11)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];a=next(a for a in v[0]['actions'] if a['action_id']=='house:119:2:312');a['meaning']=a['meaning'].replace('permits implementation OR DECLINING implementation','requires implementation everywhere')
        with self.assertRaisesRegex(ValueError,'PURPAconsideration became universal adoption'):validate(11,v,check_files=False)
    def validate_corrected_fixture(self,values):
        original=delta.read;receipt=copy.deepcopy(original(folder(12)/'candidate_correction_receipt.json'))
        for a in values[0]['actions']:
            if a['action_id'] in receipt['corrected_action_sha256']:receipt['corrected_action_sha256'][a['action_id']]=digest(a)
        def reading(path):return receipt if path.name=='candidate_correction_receipt.json' else original(path)
        with patch.object(delta,'read',side_effect=reading):return validate(12,values,check_files=False)
    def test_whale_report_recipient_cannot_return_to_committees(self):
        v=[read(folder(12)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];a=next(a for a in v[0]['actions'] if a['action_id']=='house:119:2:291');a['meaning']=a['meaning'].replace('submit an annual report to Congress','report annually to the named committees')
        with self.assertRaisesRegex(ValueError,'9436recipient/PBR operator correction lost'):self.validate_corrected_fixture(v)
    def test_pbr_expectation_cannot_become_attainment_target(self):
        v=[read(folder(12)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];a=next(a for a in v[0]['actions'] if a['action_id']=='house:119:2:291');a['meaning']=a['meaning'].replace('measures expected to not exceed Potential Biological Removal','plans to attain potential biological removal')
        with self.assertRaisesRegex(ValueError,'9436recipient/PBR operator correction lost'):self.validate_corrected_fixture(v)
    def test_context_witness_cannot_be_swapped_between_choices(self):
        v=[read(folder(12)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];a=next(a for a in v[0]['actions'] if a['action_id']=='house:119:2:294');a['additional_source_ids'][-2]='clerk:119:2:290'
        with self.assertRaises(ValueError):validate(12,v,check_files=False)
    def test_frontier_cannot_relabel_examined_delta_unscreened(self):
        original=delta.read;resume=copy.deepcopy(original(folder(12)/'resume_receipt.json'));resume['next_research_frontier']['scope']='All38deltaidentities remain unscreened.'
        def reading(path):return resume if path==folder(12)/'resume_receipt.json' else original(path)
        with patch.object(delta,'read',side_effect=reading):
            with self.assertRaisesRegex(ValueError,'stale frontier or review-head attribution'):validate(12,check_files=False)
    def test_private_land_work_cannot_lose_owner_consent(self):
        v=[read(folder(14)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];a=next(a for a in v[0]['actions'] if a['action_id']=='house:119:1:24');a['meaning']=a['meaning'].replace("with private landowners' consent for the private-land work",'with unconditional private-land access')
        with self.assertRaisesRegex(ValueError,'375consent/continuation/funding boundary differs'):validate(14,v,check_files=False)
    def test_tva_baseline_cannot_drop_power_station_costs(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr144_boundary
        c,u,m=[copy.deepcopy(read(folder(15)/f'{k}.json')) for k in ['sources','universe_proposal','membership_review']];receipt=copy.deepcopy(read(folder(15)/'hr144_baseline_boundary_review.json'));s=next(s for s in c['sources'] if s['source_id']=='govinfo:16usc831h-a-and-reporting-note-2024-infra15');receipt['complete_baseline_subsection']=receipt['complete_baseline_subsection'].replace('cost of power at each power station','corporate administration');s['text']=receipt['complete_baseline_subsection']+'\n\n'+receipt['termination_note'];s['governed_bytes_sha256']=sealed_digest(s,'governed_bytes_sha256')
        with self.assertRaisesRegex(ValueError,'material TVA financial/power-station reporting span lost'):validate_hr144_boundary(c,u,m,receipt)
    def test_tva_exclusion_cannot_return_without_boundary_resolution(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr144_boundary
        c,u,m=[copy.deepcopy(read(folder(15)/f'{k}.json')) for k in ['sources','universe_proposal','membership_review']];receipt=read(folder(15)/'hr144_baseline_boundary_review.json')
        for records in [u['candidate_dispositions'],m['records']]:next(r for r in records if r['action_id']=='house:119:1:14')['disposition']='exact_action_ineligible'
        with self.assertRaisesRegex(ValueError,'TVA operator-reporting boundary must remain pending'):validate_hr144_boundary(c,u,m,receipt)
if __name__=='__main__':unittest.main()
