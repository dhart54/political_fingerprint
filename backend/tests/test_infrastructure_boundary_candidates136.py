import copy
import unittest

from backend.app.semantic_ir.shared_corpus import digest
from scripts.validate_infrastructure_boundary_candidates136 import PACKET, SUBJECTS, read, validate


class BoundaryCandidates136Tests(unittest.TestCase):
    def test_exact_sources_stages_and_retained_governed_states(self):
        for bill in SUBJECTS:
            v = read(PACKET / f'hr{bill}_recommendation.json')
            with self.subTest(bill=bill):
                self.assertFalse(validate(bill)['governed_inventory_changed'])
            for edit in ['omission', 'metadata', 'text', 'preimage', 'current_flag']:
                bad = copy.deepcopy(v)
                if edit == 'omission':
                    bad['evidence'].pop()
                elif edit == 'metadata':
                    bad['evidence'][0]['source']['metadata']['vote-question'] = 'On Recommittal'
                elif edit == 'text':
                    bad['evidence'][1]['source']['text'] = 'Only a bill title'
                elif edit == 'preimage':
                    bad['before_record_sha256'] = '0' * 64
                else:
                    bad['current_governed_binding_unresolved'] = not bad['current_governed_binding_unresolved']
                with self.subTest(bill=bill, edit=edit), self.assertRaises(ValueError):
                    validate(bill, bad)

    def test_unaccepted_proposals_cannot_acquire_authority_or_change_old_claims(self):
        for bill in SUBJECTS:
            v = read(PACKET / f'hr{bill}_recommendation.json')
            for field in ['applied_to_governed_inventory', 'semantic_acceptance',
                          'membership_accepted', 'publication_authorized',
                          'production_authorized', 'compatibility_implementation_authorized']:
                bad = copy.deepcopy(v)
                bad[field] = True
                with self.subTest(bill=bill, field=field), self.assertRaisesRegex(ValueError, 'authority'):
                    validate(bill, bad)
            bad = copy.deepcopy(v)
            bad['proposed_record']['claim_source_map'][0]['passage'] = 'Altered evidence'
            bad['proposed_record_sha256'] = digest(bad['proposed_record'])
            with self.subTest(bill=bill), self.assertRaisesRegex(ValueError, 'Prior claims'):
                validate(bill, bad)

    def test_boundary_meaning_and_exact_qualifications_require_explicit_review(self):
        for bill in SUBJECTS:
            v = read(PACKET / f'hr{bill}_recommendation.json')
            bad = copy.deepcopy(v)
            bad['eligibility_analysis']['inclusion_rule'] = 'All studies and manufactured products qualify'
            with self.subTest(bill=bill), self.assertRaisesRegex(ValueError, 'Existing rule'):
                validate(bill, bad)
            bad = copy.deepcopy(v)
            bad['whole_choice_candidate']['meaning'] = (
                'The GAO study proves adverse effects' if bill == 28 else
                'All sodium nitrate products were banned90days after House passage')
            with self.subTest(bill=bill), self.assertRaisesRegex(ValueError, 'Whole-choice'):
                validate(bill, bad)
            bad = copy.deepcopy(v)
            bad['proposed_record']['rationale'] = 'Exclude all social research and all chemical technology'
            bad['proposed_record_sha256'] = digest(bad['proposed_record'])
            with self.subTest(bill=bill), self.assertRaisesRegex(ValueError, 'Candidate meaning'):
                validate(bill, bad)


if __name__ == '__main__':
    unittest.main()
