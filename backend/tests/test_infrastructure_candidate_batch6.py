import copy
import unittest
from backend.app.semantic_ir.shared_corpus import sealed_digest
from scripts.validate_infrastructure_candidate_batch6 import DATA,read,validate,versions


class InfrastructureBatch6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.values=[read(DATA/f'{n}.json') for n in ['authoring','sources','universe_proposal','membership_review']]

    def test_replay_keeps_new_massie_not_voting_nondirectional(self):
        r=validate(*self.values);self.assertEqual(r['not_voting_counts'],{'F000477':1,'M001184':4});self.assertEqual(r['finding_counts'],{'F000477':22,'M001184':19})

    def test_new_not_voting_cannot_be_changed_to_opposition(self):
        v=copy.deepcopy(self.values);s=next(s for s in v[1]['sources'] if s['source_id']=='clerk:119:2:181');s['member_records']['M001184']['official_label']='Nay';s['governed_bytes_sha256']=sealed_digest(s,'governed_bytes_sha256')
        # Binding/replay must reject the attempted status change before it can
        # create a directional finding, even if the governed object is resealed.
        with self.assertRaisesRegex(ValueError,'source identity differs|Not Voting changed'):validate(*v,check_files=False)

    def test_floor_cannot_turn_discretionary_pilot_into_mandate(self):
        sources={s['source_id']:copy.deepcopy(s) for s in self.values[1]['sources']};s=sources['record:2026-07-13-hr8897-infra6']
        changed=0
        for page in s['page_extracts']:
            changed+=page['text'].count('may establish');page['text']=page['text'].replace('may establish','shall establish')
        self.assertGreater(changed,0);s['governed_bytes_sha256']=sealed_digest(s,'governed_bytes_sha256')
        with self.assertRaisesRegex(ValueError,'floor body differs'):versions(sources)

    def test_compact_cannot_omit_repealed_full_seasonal_section(self):
        v=copy.deepcopy(self.values);next(a for a in v[0]['actions'] if a['action_id']=='house:119:2:238')['compact_source_refs'].remove('govinfo:15usc260a-2024-operative')
        with self.assertRaisesRegex(ValueError,'compact lost material baseline'):validate(*v,check_files=False)

    def test_prior_faa_actor_correction_cannot_regress_in_next_active_snapshot(self):
        v=copy.deepcopy(self.values);r=read(DATA.parent/'house_119_infrastructure_batch5_20260916/candidate_correction_receipt.json');a=next(a for a in v[0]['actions'] if a['action_id']=='house:119:2:72');a['meaning']=a['meaning'].replace(r['corrected_s2503_passage'],r['defective_s2503_preimage'])
        with self.assertRaisesRegex(ValueError,'prior action or correction changed'):validate(*v,check_files=False)

    def test_prior_source_gap_cannot_be_silently_marked_interpreted(self):
        v=copy.deepcopy(self.values);r=next(r for r in v[2]['candidate_dispositions'] if r['action_id']=='house:119:2:134');r['review_progress']['required_evidence_unavailable']=False
        # A digest-only rewrite cannot replace the old source boundary.
        from backend.app.semantic_ir.shared_corpus import digest
        v[2]['universe_subject_sha256']=digest(dict(subject=v[2]['subject'],cutoff=v[2]['cutoff'],candidate_records=v[2]['candidate_dispositions']));v[2]['proposal_sha256']=sealed_digest(v[2],'proposal_sha256')
        with self.assertRaisesRegex(ValueError,'prior/unexamined boundary changed'):validate(*v,check_files=False)

if __name__=='__main__':unittest.main()
