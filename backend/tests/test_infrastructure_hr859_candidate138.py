import copy
import unittest

from scripts.validate_infrastructure_hr859_candidate138 import PACKET, OUTPUTS, read, validate, validate_transport


class HR859Candidate138Tests(unittest.TestCase):
    def test_existing_pipeline_replays_one_core_for_both_official_choices(self):
        result = validate()
        self.assertEqual(result['member_statuses'], {'F000477': 'Yea', 'M001184': 'Nay'})
        self.assertEqual(result['candidate_propositions'], 2)
        self.assertFalse(result['governed_inventory_changed'])

    def test_authored_choice_and_source_status_changes_require_a_new_review_subject(self):
        a = read(PACKET / 'authoring.json')
        for edit in ['clock', 'exception', 'choice']:
            bad = copy.deepcopy(a)
            if edit == 'clock':
                bad['actions'][0]['meaning'] += '\nA fixed360-day deadline applies after House passage.'
            elif edit == 'exception':
                bad['actions'][0]['limitations'].pop(1)
            else:
                bad['actions'][0]['choice_meanings']['Nay'] = 'Opposes all technology'
            with self.subTest(edit=edit), self.assertRaisesRegex(ValueError, 'Authored review subject'):
                validate(authoring=bad)
        source = read(PACKET / 'sources.json')
        source['sources'][0]['member_records']['M001184']['official_label'] = 'Yea'
        with self.assertRaisesRegex(ValueError, 'Source review subject'):
            validate(capture=source)

    def test_generated_projection_mapping_and_publication_cannot_drift(self):
        outputs = {k: read(PACKET / 'generated' / (k + '.json')) for k in OUTPUTS}
        for edit in ['projection', 'core_authority', 'mapping', 'public']:
            bad = copy.deepcopy(outputs)
            if edit == 'projection':
                bad['member_projections'][1]['actions'][0]['official_status'] = 'Yea'
            elif edit == 'core_authority':
                bad['shared_action_core']['authoritative_for_new_editorial_work'] = True
            elif edit == 'mapping':
                bad['shared_issue_mapping']['action_mappings'][0]['eligibility']['decision'] = 'eligible'
            else:
                bad['readable_candidates']['production_eligible'] = True
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                validate(outputs=bad)

    def test_candidate_cannot_apply_itself_or_the_separate_approved_work(self):
        p = read(PACKET / 'proposal.json')
        for field in ['governed_inventory_changed', 'registered_source_pool_changed',
                      'prior_sealed_decisions_or_index_changed', 'canonical_admission_authorized',
                      'semantic_acceptance', 'issue_membership_accepted', 'approved_universe_or_full_issue_claim',
                      'publication_authorized', 'production_authorized', 'compatibility_change_performed', 'Health_activated']:
            bad = copy.deepcopy(p)
            bad[field] = True
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'authority'):
                validate(proposal=bad)

    def test_counterargument_and_requested_human_decision_are_bound(self):
        p = read(PACKET / 'proposal.json')
        for field in ['strongest_counterevidence', 'requested_content_bound_human_disposition']:
            bad = copy.deepcopy(p)
            bad[field] = ''
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'human decision'):
                validate(proposal=bad)
        bad = copy.deepcopy(p)
        bad['eligibility_recommendation'] = 'All product information automatically qualifies'
        with self.assertRaisesRegex(ValueError, 'Sealed proposal'):
            validate(proposal=bad)

    def test_manifest_counts_committed_lf_bytes_without_weakening_source_hashes(self):
        self.assertEqual(validate_transport()['files'], 12)
        v = read(PACKET / 'validation_receipt.json')
        for edit in ['count', 'hash', 'units']:
            bad = copy.deepcopy(v)
            if edit == 'count':
                bad['packet_files'][0]['bytes'] += 1
            elif edit == 'hash':
                bad['packet_files'][0]['lf_sha256'] = '0' * 64
            else:
                bad['packet_byte_units'] = 'Windows_worktree_bytes'
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                validate_transport(bad)


if __name__ == '__main__':
    unittest.main()
