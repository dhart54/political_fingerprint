import copy
import unittest

from backend.app.semantic_ir.shared_corpus import digest
from scripts.validate_infrastructure_hr4371_decision import PACKET, read, validate


class HR4371DecisionTests(unittest.TestCase):
    def test_stage_sources_and_unchanged_governed_preimage(self):
        self.assertFalse(validate()['governed_inventory_changed'])
        v = read(PACKET / 'recommendation.json')
        for edit in ['source', 'clerk', 'extent', 'preimage', 'omitted_rule']:
            bad = copy.deepcopy(v)
            if edit == 'source':
                bad['evidence'][1]['source_object_sha256'] = '0' * 64
            elif edit == 'clerk':
                bad['evidence'][0]['metadata']['vote-question'] = 'On Motion to Recommit'
            elif edit == 'extent':
                bad['evidence'][1]['end'] = 10929
            elif edit == 'preimage':
                bad['before_record_sha256'] = '0' * 64
            else:
                bad['evidence'].pop(3)
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                validate(bad)

    def test_proposal_cannot_clear_current_state_or_gain_authority(self):
        v = read(PACKET / 'recommendation.json')
        for field in ['applied_to_governed_inventory', 'semantic_acceptance',
                      'membership_accepted', 'publication_authorized',
                      'production_authorized', 'compatibility_implementation_authorized']:
            bad = copy.deepcopy(v)
            bad[field] = True
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'authority'):
                validate(bad)
        bad = copy.deepcopy(v)
        bad['current_governed_binding_unresolved'] = False
        with self.assertRaisesRegex(ValueError, 'Governed pending'):
            validate(bad)
        bad = copy.deepcopy(v)
        bad['proposed_record']['claim_source_map'][2]['passage'] = 'Changed EH'
        bad['proposed_record_sha256'] = digest(bad['proposed_record'])
        with self.assertRaisesRegex(ValueError, 'Prior claims'):
            validate(bad)

    def test_case_boundary_and_whole_choice_remain_review_subjects(self):
        v = read(PACKET / 'recommendation.json')
        bad = copy.deepcopy(v)
        bad['eligibility_analysis']['inclusion_rule'] = 'All information handling is technology'
        with self.assertRaisesRegex(ValueError, 'Existing rule'):
            validate(bad)
        bad = copy.deepcopy(v)
        bad['whole_choice_candidate'].pop(3)
        with self.assertRaisesRegex(ValueError, 'Whole-choice'):
            validate(bad)
        bad = copy.deepcopy(v)
        bad['whole_choice_candidate'][3]['meaning'] = 'All privacy law is waived'
        with self.assertRaisesRegex(ValueError, 'Whole-choice meaning'):
            validate(bad)
        bad = copy.deepcopy(v)
        bad['proposed_record']['rationale'] = 'All PRA references are Infrastructure'
        bad['proposed_record_sha256'] = digest(bad['proposed_record'])
        with self.assertRaisesRegex(ValueError, 'Candidate meaning changed'):
            validate(bad)


if __name__ == '__main__':
    unittest.main()
