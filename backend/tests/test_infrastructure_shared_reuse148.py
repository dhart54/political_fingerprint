import copy
import unittest

from backend.app.semantic_ir.shared_corpus import digest, sealed_digest
from scripts.prepare_shared_domain_candidate import prepare
from scripts.validate_infrastructure_shared_reuse148 import (
    PACKET, INDEX, MEMBERS, OUTPUTS, read, validate, validate_sources, validate_reuse,
    validate_index, validate_preservation,
)


class SharedReuse148Tests(unittest.TestCase):
    def test_held_replay_preserves_three_whole_choices_and_all_predecessors(self):
        r = validate()
        self.assertEqual((r['shared_cores'], r['member_observations'], r['not_voting'], r['propositions']), (3, 6, 1, 0))
        self.assertFalse(r['new_acquisition'])
        self.assertGreater(validate_preservation(), 240)
        self.assertEqual(validate_index(), 17)

    def test_source_qualified_meaning_is_shared_when_member_order_changes(self):
        a = read(PACKET / 'authoring.json'); s = read(PACKET / 'sources.json')
        normal = prepare(a, s, MEMBERS); reversed_members = prepare(a, s, list(reversed(MEMBERS)))
        self.assertEqual(normal[:2], reversed_members[:2])
        self.assertEqual(reversed_members[2][0]['actions'][0]['official_status'], 'Not Voting')
        for core in normal[0]['actions']:
            for projection in normal[2]:
                row = next(x for x in projection['actions'] if x['action_id'] == core['action_id'])
                self.assertEqual(row['action_core_sha256'], core['action_core_sha256'])

    def test_whole_existing_meaning_cannot_be_narrowed_or_turn_authority_into_spending(self):
        a = read(PACKET / 'authoring.json')
        for index, old, new in [
            (0, 'Neither clause is an actual appropriation', 'Both clauses are an actual appropriation'),
            (1, 'only the unobligated balances under sections 50122 and 50131', 'all original appropriations under all three repealed sections'),
            (1, "Section 50121's distinct HOMES rebate program is not repealed.", 'The HOMES rebate program is repealed.'),
            (2, 'TO THE EXTENT PERMITTED BY LAW', 'without legal limitation'),
        ]:
            bad = copy.deepcopy(a); self.assertIn(old, bad['actions'][index]['meaning'])
            bad['actions'][index]['meaning'] = bad['actions'][index]['meaning'].replace(old, new)
            with self.subTest(index=index, old=old), self.assertRaisesRegex(ValueError, 'reuse'):
                validate_reuse(bad)

    def test_member_observation_or_issue_membership_cannot_enter_shared_meaning(self):
        a = read(PACKET / 'authoring.json')
        for leak in ['Massie voted for this.', 'This proves Health membership.']:
            bad = copy.deepcopy(a); bad['actions'][1]['meaning'] += ' ' + leak
            with self.subTest(leak=leak), self.assertRaises(ValueError): validate_reuse(bad)

    def test_source_resealing_cannot_change_the_original_qualifications(self):
        s = read(PACKET / 'sources.json')
        for sid in ['govinfo:s2393es', 'govinfo:pl119-21-50402-energy-rescissions', 'govinfo:eo14252-dc-safe-beautiful']:
            bad = copy.deepcopy(s); source = next(x for x in bad['sources'] if x['source_id'] == sid)
            source['text'] += ' Invented present outcome.'; source['governed_bytes_sha256'] = sealed_digest(source, 'governed_bytes_sha256')
            with self.subTest(sid=sid), self.assertRaisesRegex(ValueError, 'retained source'): validate_sources(bad)

    def test_unread_passage_or_wrong_action_stage_cannot_compile(self):
        a = read(PACKET / 'authoring.json'); s = read(PACKET / 'sources.json')
        for mutation in ['passage', 'stage']:
            bad = copy.deepcopy(a)
            if mutation == 'passage': bad['actions'][1]['claim_source_map'][0]['passage'] += ' Unread text.'
            else: bad['actions'][1]['stage'] = 'amendment'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): prepare(bad, s, MEMBERS)

    def test_hold_not_voting_and_publication_cannot_drift_in_outputs(self):
        o = {k: read(PACKET / 'generated' / (k + '.json')) for k in OUTPUTS}
        for mutation in ['hold', 'NV', 'publication']:
            bad = copy.deepcopy(o)
            if mutation == 'hold': bad['shared_issue_mapping']['source_render_constraints'] = []
            elif mutation == 'NV': bad['member_projections'][1]['actions'][0]['official_status'] = 'Nay'
            else: bad['readable_candidates']['production_eligible'] = True
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'replay'): validate(outputs=bad)

    def test_candidate_review_cannot_apply_or_accept_even_when_resealed(self):
        b = read(PACKET / 'decision_bundle.json')
        for key, value in [('canonical_state_changed', True), ('semantic_acceptance', True), ('six_source_holds_changed', 0)]:
            bad = copy.deepcopy(b); bad[key] = value; bad['bundle_sha256'] = sealed_digest(bad, 'bundle_sha256')
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'authority'): validate(bundle=bad)

    def test_original_twelve_inventory_subjects_cannot_change(self):
        i = read(INDEX)
        for mutation in ['remove', 'approved']:
            bad = copy.deepcopy(i)
            if mutation == 'remove': bad['cases'].pop(0)
            else: bad['cases'][0]['accepted_by_this_index'] = True
            bad['index_sha256'] = sealed_digest(bad, 'index_sha256')
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'Original twelve'): validate_index(bad)

    def test_inventory_cannot_accept_content_or_change_147_facts(self):
        i = read(INDEX)
        for mutation in ['authority', 'NV', 'preimage', 'counter']:
            bad = copy.deepcopy(i)
            if mutation == 'authority': bad['canonical_application_authorized'] = True
            elif mutation == 'NV': bad['cases'][-1]['member_observations']['M001184'] = 'Nay'
            elif mutation == 'preimage': bad['cases'][-1]['current_record_sha256'] = '0' * 64
            else: bad['cases'][12]['material_counterevidence'] = ''
            bad['index_sha256'] = sealed_digest(bad, 'index_sha256')
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): validate_index(bad)

    def test_immutable_147_pointer_and_review_attribution_cannot_drift(self):
        i = read(INDEX)
        for mutation in ['link', 'review']:
            bad = copy.deepcopy(i)
            if mutation == 'link': bad['cases'][12]['sealed_meaning_link'] = bad['cases'][12]['sealed_meaning_link'].replace('323343335855b0b3729bb02111637e735a777eda', 'main')
            else: bad['existing_independent_review_attribution'][-1]['hosted_runs'][0]['result'] = 'pending'
            bad['index_sha256'] = sealed_digest(bad, 'index_sha256')
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): validate_index(bad)

    def test_resealed_147_links_and_pointers_must_bind_the_same_exact_action(self):
        i = read(INDEX)
        for mutation in ['other_action_line', 'other_packet', 'pointer', 'bundle', 'core', 'successor']:
            bad = copy.deepcopy(i); c = bad['cases'][12]
            if mutation == 'other_action_line': c['sealed_meaning_link'] = bad['cases'][13]['sealed_meaning_link']
            elif mutation == 'pointer': c['meaning_pointer'] = '/actions/1'
            else:
                field = {'other_packet': 'sealed_meaning_link', 'bundle': 'sealed_bundle_link',
                         'core': 'sealed_core_link', 'successor': 'shared_successor_proposal_link'}[mutation]
                c[field] = c[field].replace('infrastructure_batch147_va_candidates', 'infrastructure_batch143_land_siting_easements')
            bad['index_sha256'] = sealed_digest(bad, 'index_sha256')
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'exact action/pointer'):
                validate_index(bad)


if __name__ == '__main__':
    unittest.main()
