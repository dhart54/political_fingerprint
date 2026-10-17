"""Batch3 source/version, copy-boundary and noncounting regressions."""
import copy
import re
import unittest
from backend.app.semantic_ir.shared_corpus import digest,sealed_digest
from scripts.validate_infrastructure_candidate_batch3 import DATA,PACKAGE,read,validate,versions


class InfrastructureBatch3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values=[read(DATA/f'{n}.json') for n in ['authoring','sources','universe_proposal','membership_review']]

    def test_replay_conserves_real_choices_and_four_not_voting_observations(self):
        result=validate(*self.values)
        self.assertEqual(result['not_voting_counts'],{'F000477':1,'M001184':3})
        self.assertEqual(result['finding_counts'],{'F000477':12,'M001184':10})

    def test_matching_resealed_package_flags_cannot_fabricate_unavailable_evidence(self):
        values=copy.deepcopy(self.values);u,m=values[2:]
        row=next(r for r in u['candidate_dispositions'] if r['action_id']==PACKAGE)
        record=next(r for r in m['records'] if r['action_id']==PACKAGE)
        row['review_progress']['required_evidence_unavailable']=record['required_evidence_unavailable']=True
        m['review_sha256']=sealed_digest(m,'review_sha256');u['membership_review_sha256']=m['review_sha256']
        row['review_progress']['shared_review_record_sha256']=digest(record)
        u['universe_subject_sha256']=digest(dict(subject=u['subject'],cutoff=u['cutoff'],candidate_records=u['candidate_dispositions']))
        u['proposal_sha256']=sealed_digest(u,'proposal_sha256')
        with self.assertRaisesRegex(ValueError,'unfinished package misrepresented'):
            validate(*values,check_files=False)

    def test_coherently_resealed_floor_substantive_change_is_rejected(self):
        sources={s['source_id']:copy.deepcopy(s) for s in self.values[1]['sources']}
        s=sources['record:2025-11-17-hr2659-infra3']
        for page in s['page_extracts']:page['text']=re.sub(r'540\s+days','180 days',page['text'])
        self.assertTrue(any('180 days' in page['text'] for page in s['page_extracts']))
        s['governed_bytes_sha256']=sealed_digest(s,'governed_bytes_sha256')
        with self.assertRaisesRegex(ValueError,'floor body differs'):
            versions(sources)

    def test_wrapper_discrepancy_cannot_be_dropped_from_all_copies_by_replay(self):
        values=copy.deepcopy(self.values)
        next(a for a in values[0]['actions'] if a['bill_number']==1223)['limitations'].pop()
        with self.assertRaisesRegex(ValueError,'wrapper discrepancy qualification absent'):
            validate(*values,check_files=False)

    def test_remote_access_compact_requires_status_and_mens_rea_baselines(self):
        values=copy.deepcopy(self.values)
        next(a for a in values[0]['actions'] if a['bill_number']==2683)['compact_source_refs'].remove('olrc:50usc4819-2024-operative')
        with self.assertRaisesRegex(ValueError,'compact lost material baseline'):
            validate(*values,check_files=False)

    def test_fixed_inventory_original_official_no_label_is_not_rewritten(self):
        values=copy.deepcopy(self.values)
        next(r for r in values[2]['candidate_dispositions'] if r['action_id']=='house:119:1:344')['member_action']='nay'
        values[2]['universe_subject_sha256']=digest(dict(subject=values[2]['subject'],cutoff=values[2]['cutoff'],candidate_records=values[2]['candidate_dispositions']))
        values[2]['proposal_sha256']=sealed_digest(values[2],'proposal_sha256')
        with self.assertRaisesRegex(ValueError,'676 discovery identities changed'):
            validate(*values,check_files=False)

    def test_aggregate_readiness_cannot_lag_identity_buckets(self):
        values=copy.deepcopy(self.values)
        values[2]['accounting']['official_source_readiness']['ready_substantive_actions']=9
        values[2]['proposal_sha256']=sealed_digest(values[2],'proposal_sha256')
        with self.assertRaisesRegex(ValueError,'aggregate accounting or readiness differs'):
            validate(*values,check_files=False)


if __name__=='__main__':unittest.main()
