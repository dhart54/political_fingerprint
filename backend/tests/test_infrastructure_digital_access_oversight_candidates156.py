import copy
import unittest
from unittest.mock import patch

from backend.app.semantic_ir.shared_corpus import (
    digest, sealed_digest, validate_member_projection,
    validate_shared_issue_mapping, SharedCorpusValidationError,
)
from scripts.validate_infrastructure_digital_access_oversight_candidates156 import (
    ROOT, P, inputs, replay, validate, validate_capture, validate_manifest, validate_preservation,
)


class DigitalAccessOversight156Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = inputs()

    def changed(self, key):
        data = dict(self.data)
        data[key] = copy.deepcopy(data[key])
        return data

    def test_five_exact_choices_conserve_shared_meanings_and_hold_all_episodes(self):
        result = validate(self.data)
        self.assertEqual((result['cores'], result['official_observations'], result['held_episodes'],
                          result['propositions'], result['sources']), (5, 10, 5, 0, 25))
        self.assertIs(result['canonical_changes'], False)
        self.assertGreaterEqual(validate_preservation(), 500)
        self.assertGreaterEqual(validate_manifest(), 15)

    def test_both_members_bind_identical_core_and_exact_official_observations(self):
        products = self.data['products']
        cores = {x['action_id']: x for x in products['shared_action_core']['actions']}
        for member in products['member_projections']:
            expected = ['Yea', 'Yea', 'Yea', 'Not Voting', 'Yea'] if member['member_id'] == 'F000477' else ['Nay', 'Yea', 'Nay', 'Yea', 'Yea']
            self.assertEqual([x['official_status'] for x in member['actions']], expected)
            for action in member['actions']:
                self.assertEqual(action['action_core_sha256'], cores[action['action_id']]['action_core_sha256'])

    def test_semantic_operator_changes_do_not_replay_as_frozen_candidate(self):
        probes = [(0, 'EXCEEDING200', 'at least200'),
                  (0, 'actual OR constructive', 'actual AND constructive'),
                  (1, 'IN ADDITION TO', 'in place of'),
                  (1, 'dollar-value AND loan-number', 'dollar-value OR loan-number'),
                  (2, 'BEFORE, DURING AND AFTER', 'only before'),
                  (3, 'phone number OR', 'phone number AND'),
                  (4, 'would PERMIT', 'would REQUIRE'),
                  (4, 'AFTER THAT USE', 'after enactment')]

        for index, old, new in probes:
            data = self.changed('authoring')
            for key in ['meaning', 'compact_description']:
                self.assertIn(old, data['authoring']['actions'][index][key])
                data['authoring']['actions'][index][key] = data['authoring']['actions'][index][key].replace(old, new)
            with self.subTest(index=index, operator=old), self.assertRaises(ValueError):
                validate(data)

    def test_literal_program_limits_and_source_constraints_cannot_disappear(self):
        probes = [(2, 'redirected and are closed without retries', 'resolved by alternative routes'),
                  (4, 'its contents are unintegrated', 'all contents are integrated'),
                  (4, 'not a blanket condition', 'a universal condition'),
                  (4, 'not adjudicated fraud or proven victim losses', 'proven fraud and victim losses')]
        for index, old, new in probes:
            data = self.changed('authoring')
            action = data['authoring']['actions'][index]
            self.assertIn(old, action['meaning'])
            action['meaning'] = action['meaning'].replace(old, new)
            with self.subTest(index=index), self.assertRaises(ValueError):
                validate(data)

    def test_actual_not_voting_is_non_directional_and_shared_text_is_member_neutral(self):
        products = self.data['products']
        member = copy.deepcopy(products['member_projections'][0])
        row = member['actions'][3]
        self.assertEqual(row['official_status'], 'Not Voting')
        self.assertEqual(row['exact_choice_effect'], 'resolved_non_directional')
        row['exact_choice_effect'] = products['member_projections'][1]['actions'][3]['exact_choice_effect']
        member['projection_sha256'] = sealed_digest(member, 'projection_sha256')
        with self.assertRaises(SharedCorpusValidationError):
            validate_member_projection(ROOT, member, products['shared_action_core'])
        # Literal Record witnesses retain their roll lists. Only authored meaning
        # fields must exclude member identity; do not rewrite governed evidence.
        authoring = self.data['authoring']
        text = str({
            'boundary': authoring['boundary'], 'blocked_reason': authoring['blocked_reason'],
            'actions': [{key: action[key] for key in ['meaning', 'compact_description',
                         'short_description', 'limitations', 'choice_meanings']}
                        for action in authoring['actions']],
        })
        self.assertTrue('Foushee' not in text and 'Massie' not in text,
                        'Authored shared meaning contains member identity')

    def test_complete_2978_floor_comparison_rejects_a_substantive_operator_change(self):
        from scripts.validate_infrastructure_digital_access_oversight_candidates156 import validate_floor
        pool = {x['source_id']: copy.deepcopy(x) for x in self.data['sources']['sources']}
        self.assertEqual(validate_floor(pool, self.data['conformance'])['compared_characters'], 7151)
        source = pool['immigration:roll301-floor-complete195']
        self.assertIn('may assist', source['text'])
        source['text'] = source['text'].replace('may assist', 'shall assist')
        with self.assertRaises(ValueError):
            validate_floor(pool, self.data['conformance'])

    def test_resealed_sources_and_false_canonical_preimages_are_rejected(self):
        for key in ['sources', 'preflight']:
            data = self.changed(key)
            if key == 'sources':
                source = data[key]['sources'][-1]
                source['text'] += ' invented present-law conclusion'
                source['governed_bytes_sha256'] = sealed_digest(source, 'governed_bytes_sha256')
            else:
                data[key]['cases'][0]['record']['exact_action_binding_unresolved'] = True
                data[key]['preflight_sha256'] = sealed_digest(data[key], 'preflight_sha256')
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(data)

    def test_claim_passages_must_exist_in_bound_source(self):
        for key in ['passage', 'source_id']:
            authoring = copy.deepcopy(self.data['authoring'])
            authoring['actions'][0]['claim_source_map'][0][key] = 'not an observed source passage'
            with self.subTest(key=key), self.assertRaises((ValueError, KeyError)):
                replay(authoring, self.data['sources'])

    def test_all_authority_flags_require_literal_false(self):
        for key in ['accepted', 'canonical_application', 'publication', 'production']:
            for value in [True, 0]:
                data = self.changed('bundle')
                data['bundle'][key] = value
                data['bundle']['bundle_sha256'] = sealed_digest(data['bundle'], 'bundle_sha256')
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    validate(data)

    def test_mapping_cannot_accept_eligibility(self):
        products = self.data['products']
        mapping = copy.deepcopy(products['shared_issue_mapping'])
        row = mapping['action_mappings'][0]
        row['eligibility']['decision'] = 'accepted'
        row['mapping_sha256'] = sealed_digest(row, 'mapping_sha256')
        mapping['mapping_sha256'] = sealed_digest(mapping, 'mapping_sha256')
        with self.assertRaises(SharedCorpusValidationError):
            validate_shared_issue_mapping(ROOT, mapping, products['shared_action_core'])

    def test_shared_correction_invalidates_both_stale_member_projections(self):
        products = self.data['products']
        after = copy.deepcopy(products['shared_action_core'])
        action = after['actions'][0]
        action['candidate_shared_limitations'].append('CONTROLLED corrected shared qualification.')
        action['action_core_sha256'] = sealed_digest(action, 'action_core_sha256')
        after['corpus_sha256'] = digest(after['actions'])
        for member in products['member_projections']:
            with self.subTest(member=member['member_id']), self.assertRaises(SharedCorpusValidationError):
                validate_member_projection(ROOT, member, after)

    def test_unused_raw_observation_does_not_change_any_native_product(self):
        sources = copy.deepcopy(self.data['sources'])
        extra = {'source_id': 'synthetic:unused156', 'text': 'Controlled unused observation, not evidence.'}
        extra['governed_bytes_sha256'] = digest(extra)
        sources['sources'].append(extra)
        self.assertEqual(digest(replay(self.data['authoring'], sources)), digest(self.data['products']))

    def test_raw_byte_drift_is_detected_without_modifying_capture(self):
        target = (P / 'captures/15usc45c-2024.html').resolve()
        original = type(target).read_bytes

        def changed(path):
            return original(path) + (b'drift' if path.resolve() == target else b'')

        with patch('pathlib.Path.read_bytes', changed), self.assertRaises(ValueError):
            validate_capture()

    def test_captures_reject_retry_redirect_cap_type_and_source_rebinding(self):
        for kind in ['retry', 'redirect', 'cap', 'rebind']:
            capture = copy.deepcopy(self.data['capture'])
            bindings = copy.deepcopy(self.data['bindings'])
            if kind == 'retry':
                capture['attempts'].append(copy.deepcopy(capture['attempts'][0]))
            elif kind == 'redirect':
                capture['attempts'][0]['final_url'] = 'https://example.invalid/'
            elif kind == 'cap':
                capture['limits']['locators'] = 12.0
            else:
                bindings['sources'][0]['source_id'] = 'govinfo:oversight156:15usc657t-2024'
            with self.subTest(kind=kind), self.assertRaises((ValueError, KeyError)):
                validate_capture(capture, bindings, self.data['sources'])

    def test_episode_hold_member_choice_and_graph_cannot_drift(self):
        for kind in ['hold', 'member', 'graph']:
            data = self.changed('authoring' if kind == 'hold' else 'products')
            if kind == 'hold':
                data['authoring']['blocked_episode_ids'].pop()
            elif kind == 'member':
                data['products']['member_projections'][0]['actions'][0]['official_status'] = 'Nay'
            else:
                data['products']['compiled_ir']['members'][0]['proposition_graph']['propositions'].append({'invented': True})
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                validate(data)


if __name__ == '__main__':
    unittest.main()
