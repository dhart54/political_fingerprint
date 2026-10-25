import copy
import unittest

from backend.app.semantic_ir.shared_corpus import digest, sealed_digest
from scripts.prepare_shared_domain_candidate import prepare
from scripts.validate_infrastructure_va_candidates147 import (
    PACKET, CHECKPOINT, MEMBERS, OUTPUTS, read, validate, validate_preservation,
    validate_sources, validate_bundle, validate_member_neutral, validate_successors,
)


class VACandidates147Tests(unittest.TestCase):
    def test_actual_replay_keeps_five_shared_choices_held_and_current_state_unchanged(self):
        result = validate()
        self.assertEqual((result['cores'], result['official_observations'], result['issue_propositions']), (5, 10, 0))
        self.assertEqual((result['not_voting_observations'], result['new_captures']), (1, 0))
        self.assertFalse(result['semantic_acceptance'])
        self.assertGreater(validate_preservation(), 60)

    def test_member_order_cannot_change_shared_meaning_or_mapping(self):
        a = read(PACKET / 'authoring.json'); s = read(CHECKPOINT / 'sources.json')
        normal = prepare(a, s, MEMBERS)
        reversed_members = prepare(a, s, list(reversed(MEMBERS)))
        self.assertEqual(normal[:2], reversed_members[:2])
        self.assertEqual(reversed_members[2][0]['actions'][-1]['exact_choice_effect'], 'resolved_non_directional')
        for shared in normal[0]['actions']:
            for projection in normal[2]:
                row = next(x for x in projection['actions'] if x['action_id'] == shared['action_id'])
                self.assertEqual(shared['action_core_sha256'], row['action_core_sha256'])

    def test_neighbor_roll_or_pension_date_cannot_replace_frozen_source(self):
        original = read(CHECKPOINT / 'sources.json')
        for sid, old, new in [
            ('govinfo:context144:hr1286_resumption_roll133', '[Roll No. 133]', '[Roll No. 132]'),
            ('govinfo:pl119-43-pension-expiry', 'January 31, 2033', 'December 31, 2031'),
            ('govinfo:context144:38usc5100_operative', '(including electronic means)', ''),
        ]:
            bad = copy.deepcopy(original)
            source = next(x for x in bad['sources'] if x['source_id'] == sid)
            self.assertIn(old, source['text']); source['text'] = source['text'].replace(old, new)
            source['governed_bytes_sha256'] = sealed_digest(source, 'governed_bytes_sha256')
            with self.subTest(sid=sid), self.assertRaisesRegex(ValueError, 'source pool'):
                validate_sources(bad)

    def test_wrong_measure_and_wrong_question_cannot_compile_as_same_action(self):
        a = read(PACKET / 'authoring.json'); s = read(CHECKPOINT / 'sources.json')
        for field, value in [('bill_number', 1039), ('stage', 'final_passage')]:
            bad = copy.deepcopy(a); bad['actions'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                prepare(bad, s, MEMBERS)

    def test_claim_cannot_escape_selected_source_into_unread_parent(self):
        a = read(PACKET / 'authoring.json'); s = read(CHECKPOINT / 'sources.json')
        bad = copy.deepcopy(a)
        bad['actions'][0]['claim_source_map'][-1]['passage'] += ' Unsupported neighboring measure result.'
        with self.assertRaisesRegex(ValueError, 'claim passage absent'):
            prepare(bad, s, MEMBERS)

    def test_member_and_taxonomy_decisions_cannot_enter_shared_core(self):
        a = read(PACKET / 'authoring.json')
        for field, leak in [('meaning', 'Massie opposed this.'), ('compact_description', 'F000477 supported it.'),
                            ('limitations', 'This proves Infrastructure membership.')]:
            bad = copy.deepcopy(a)
            if field == 'limitations': bad['actions'][0][field].append(leak)
            else: bad['actions'][0][field] += ' ' + leak
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'member/issue'):
                validate_member_neutral(bad)

    def test_even_resealed_acceptance_or_numeric_false_is_rejected(self):
        a = read(PACKET / 'authoring.json'); b = read(PACKET / 'decision_bundle.json')
        for key, value in [('semantic_acceptance', True), ('publication_authorized', True),
                           ('canonical_state_changed', True), ('six_source_holds_changed', 0)]:
            bad = copy.deepcopy(b); bad[key] = value
            bad['bundle_sha256'] = sealed_digest(bad, 'bundle_sha256')
            with self.subTest(key=key), self.assertRaises(ValueError): validate_bundle(bad, a)

    def test_removing_an_episode_hold_is_not_review_clearance(self):
        a = read(PACKET / 'authoring.json'); b = read(PACKET / 'decision_bundle.json')
        bad = copy.deepcopy(a); bad['blocked_episode_ids'].pop()
        b['authoring_sha256'] = digest(bad); b['bundle_sha256'] = sealed_digest(b, 'bundle_sha256')
        with self.assertRaises(ValueError): validate_bundle(b, bad)

    def test_not_voting_or_generated_publication_cannot_drift(self):
        outputs = {k: read(PACKET / 'generated' / (k + '.json')) for k in OUTPUTS}
        for mutation in ['status', 'authority']:
            bad = copy.deepcopy(outputs)
            if mutation == 'status': bad['member_projections'][1]['actions'][-1]['official_status'] = 'Nay'
            else: bad['readable_candidates']['production_eligible'] = True
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'replay'):
                validate(outputs=bad)

    def test_receipt_commencement_and_negotiation_clocks_cannot_be_silently_rewritten(self):
        a = read(PACKET / 'authoring.json'); b = read(PACKET / 'decision_bundle.json')
        for index, old, new in [
            (0, 'within one year after study completion', 'within one year after enactment'),
            (1, 'within one year after commencement', 'within two years after commencement'),
            (2, 'within 60 days after negotiations begin', 'within 60 days after enactment'),
            (3, 'within two years after commencement', 'within one year after commencement'),
            (4, 'approved OR denied', 'approved'),
        ]:
            bad = copy.deepcopy(a); subject = copy.deepcopy(b)
            self.assertIn(old, bad['actions'][index]['meaning'])
            bad['actions'][index]['meaning'] = bad['actions'][index]['meaning'].replace(old, new)
            subject['authoring_sha256'] = digest(bad)
            subject['bundle_sha256'] = sealed_digest(subject, 'bundle_sha256')
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, 'replay'):
                validate(authoring=bad, bundle=subject)

    def test_successor_comparison_cannot_hide_prior_core_or_dependency(self):
        core = read(PACKET / 'generated/shared_action_core.json')
        projections = read(PACKET / 'generated/member_projections.json')
        compiled = read(PACKET / 'generated/compiled_ir.json')
        proposal = read(PACKET / 'shared_successor_proposals.json')
        for mutation in ['before', 'delta', 'dependency', 'accepted']:
            bad = copy.deepcopy(proposal)
            if mutation == 'before': bad['cases'][0]['before_core_sha256'] = bad['cases'][0]['after_core_sha256']
            elif mutation == 'delta': bad['cases'][0]['changed_fields'].pop('candidate_exact_action_meaning')
            elif mutation == 'dependency': bad['dependency_impact']['affected_projections'] = []
            else: bad['cases'][0]['successor_accepted'] = True
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_successors(core, projections, compiled, bad)


if __name__ == '__main__':
    unittest.main()
