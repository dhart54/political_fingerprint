import copy
import unittest
from unittest.mock import patch

from backend.app.semantic_ir.shared_corpus import (
    digest, sealed_digest, validate_member_projection, validate_shared_issue_mapping,
    candidate_update_impact, SharedCorpusValidationError,
)
from scripts.prepare_shared_domain_candidate import prepare
from scripts.validate_infrastructure_equipment_candidates150 import (
    ROOT, P, ACTIONS, MEMBERS, DOCS, inputs, read, replay, validate,
    validate_capture, validate_manifest, validate_preservation,
)


class EquipmentRuleCandidates150Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = inputs()

    def changed(self, key):
        data = dict(self.data); data[key] = copy.deepcopy(data[key]); return data

    def test_actual_held_outputs_and_predecessor_preservation(self):
        result = validate(self.data)
        self.assertEqual((result['cores'], result['official_observations'], result['sources']), (5, 10, 15))
        self.assertEqual(result['issue_propositions'], 0)
        self.assertIs(result['canonical149_changed'], False)
        self.assertGreaterEqual(validate_preservation(), 321)
        self.assertGreaterEqual(validate_manifest(), 30)

    def test_deterministic_replay_keeps_shared_meaning_and_member_sources(self):
        before = digest([self.data['authoring'], self.data['sources']])
        one = replay(self.data['authoring'], self.data['sources'])
        two = replay(self.data['authoring'], self.data['sources'])
        self.assertEqual(digest(one), digest(two))
        self.assertEqual(digest(one), digest(self.data['products']))
        self.assertEqual(before, digest([self.data['authoring'], self.data['sources']]))
        for row in one['shared_action_core']['actions']:
            self.assertEqual(row['legislative_stage'], 'final_passage')
            self.assertEqual(row['package_component_boundary']['boundary_type'], 'whole_measure')

    def test_member_choices_concern_disapproval_and_not_support_for_the_rule(self):
        products = self.data['products']; core = products['shared_action_core']
        for action in core['actions']:
            self.assertIn('supported passing', action['choice_meanings']['Yea'])
            self.assertIn('to disapprove its whole identified', action['choice_meanings']['Yea'])
            self.assertIn('opposed passing', action['choice_meanings']['Nay'])
        by_id = {c['action_id']: c for c in core['actions']}
        for p in products['member_projections']:
            status = 'Nay' if p['member_id'] == 'F000477' else 'Yea'
            self.assertTrue(all(r['official_status'] == status for r in p['actions']))
            self.assertTrue(all(r['action_core_sha256'] == by_id[r['action_id']]['action_core_sha256'] for r in p['actions']))
        self.assertTrue(all(not m['proposition_graph']['propositions'] for m in products['compiled_ir']['members']))

    def test_every_named_rule_binding_and_bounded_reading_scope_is_explicit(self):
        for action, doc, coverage in zip(self.data['authoring']['actions'], DOCS, self.data['questions']['coverage']):
            self.assertEqual(action['additional_source_ids'], ['govinfo:rule150:'+doc])
            self.assertTrue(coverage['complete_EH_read'])
            self.assertIs(coverage['full_rule_preamble_read'], False)
            self.assertIs(coverage['exhaustive_current_law_review'], False)
            self.assertEqual(coverage['action_id'], action['action_id'])
            self.assertTrue(action['claim_source_map'])

    def test_material_rule_qualifications_are_present_without_blanket_claims(self):
        meanings = {a['action_id']: a['meaning'] for a in self.data['authoring']['actions']}
        water = meanings[ACTIONS[0]]
        self.assertIn('below 2 gallons', water)
        self.assertIn('rather than an across-the-board increase', water)
        self.assertIn('severability', water)
        certification = meanings[ACTIONS[1]]
        self.assertIn('does not itself impose one new efficiency threshold', certification)
        self.assertIn('foam-insulated non-display doors', certification)
        self.assertIn('may not exceed 20 hours', certification)
        walk = meanings[ACTIONS[2]]
        self.assertIn('Display-door and panel standards are expressly not amended', walk)
        self.assertIn('medical, scientific or research', walk)
        self.assertIn('not interchangeable', walk)
        commercial = meanings[ACTIONS[3]]
        self.assertIn('large-capacity', commercial)
        self.assertIn('hybrid/refrigerator-freezer compartment', commercial)
        self.assertIn('Office of the Office', commercial)
        rubber = meanings[ACTIONS[4]]
        self.assertIn('rather than the proposal', rubber)
        self.assertIn('facility-wide averaging', rubber)
        self.assertIn('fPM 3.0 grams/Mg OR metal-HAP 0.051 grams/Mg', rubber)
        self.assertIn('November 16, 2023', rubber)

    def test_unused_raw_addition_does_not_change_interpreted_products(self):
        capture = copy.deepcopy(self.data['sources'])
        source = {'source_id': 'synthetic:uninterpreted-raw150', 'text': 'Controlled unused raw observation; not historical evidence.'}
        source['governed_bytes_sha256'] = sealed_digest(source, 'governed_bytes_sha256')
        capture['sources'].append(source)
        result = replay(self.data['authoring'], capture)
        self.assertEqual(digest(result), digest(self.data['products']))

    def test_shared_correction_rejects_both_stale_member_projections_without_findings(self):
        products = self.data['products']; before = products['shared_action_core']; after = copy.deepcopy(before)
        target = after['actions'][0]
        target['candidate_shared_limitations'].append('CONTROLLED TEST: source-qualified shared correction; no acceptance.')
        target['action_core_sha256'] = sealed_digest(target, 'action_core_sha256')
        after['corpus_sha256'] = digest(after['actions'])
        impact = candidate_update_impact(before, after, products['member_projections'], products['compiled_ir'])
        self.assertTrue(impact)
        for p in products['member_projections']:
            with self.subTest(member=p['member_id']), self.assertRaises(SharedCorpusValidationError):
                validate_member_projection(ROOT, p, after)
        self.assertEqual(len(before['actions']), 5)

    def test_existing_candidate_guard_rejects_accepted_eligibility(self):
        products = self.data['products']; mapping = copy.deepcopy(products['shared_issue_mapping'])
        mapping['action_mappings'][0]['eligibility']['decision'] = 'accepted'
        mapping['action_mappings'][0]['mapping_sha256'] = sealed_digest(mapping['action_mappings'][0], 'mapping_sha256')
        mapping['mapping_sha256'] = sealed_digest(mapping, 'mapping_sha256')
        with self.assertRaises(SharedCorpusValidationError):
            validate_shared_issue_mapping(ROOT, mapping, products['shared_action_core'])

    def test_source_and_whole_meaning_drift_cannot_be_self_resealed(self):
        for kind in ['rule_text', 'raw_sha', 'member', 'source_swap']:
            d = self.changed('sources'); source = next(s for s in d['sources']['sources'] if s['source_id'] == 'govinfo:rule150:2024-30369')
            if kind == 'rule_text': source['text'] += ' invented scope'
            elif kind == 'raw_sha': source['raw_sha256'] = '0'*64
            elif kind == 'member':
                source = next(s for s in d['sources']['sources'] if s['source_id'] == 'clerk:119:1:53')
                source['member_records']['F000477']['official_label'] = 'Yea'
            else: source['url'] = next(s['url'] for s in d['sources']['sources'] if s['source_id'] == 'govinfo:rule150:2024-28474')
            source['governed_bytes_sha256'] = sealed_digest(source, 'governed_bytes_sha256')
            with self.subTest(kind=kind), self.assertRaises(ValueError): validate(d)
        for kind in ['meaning', 'stage', 'rule', 'hold']:
            d = self.changed('authoring')
            if kind == 'meaning': d['authoring']['actions'][0]['meaning'] = 'Bans every gas appliance.'
            elif kind == 'stage': d['authoring']['actions'][0]['stage'] = 'amendment'
            elif kind == 'rule': d['authoring']['actions'][0]['additional_source_ids'] = ['govinfo:rule150:2024-28474']
            else: d['authoring']['blocked_episode_ids'].pop()
            with self.subTest(kind=kind), self.assertRaises(ValueError): validate(d)

    def test_preflight_and_decision_scope_cannot_acquire_authority(self):
        for key, field, value in [('bundle','accepted',True), ('bundle','accepted',0), ('bundle','canonical_application',True),
                                  ('bundle','publication',True), ('bundle','production',True),
                                  ('questions','current_law_integration_complete',True), ('questions','later_rule_delays_or_withdrawals_adopted',True)]:
            d = self.changed(key); d[key][field] = value
            with self.subTest(key=key, field=field), self.assertRaises(ValueError): validate(d)
        d = self.changed('preflight'); d['preflight']['cases'][0]['record']['rationale'] += ' changed'
        d['preflight']['preflight_sha256'] = sealed_digest(d['preflight'], 'preflight_sha256')
        with self.assertRaises(ValueError): validate(d)

    def test_overcap_routes_stay_closed_and_capture_caps_are_type_strict(self):
        for kind in ['duplicate', 'alternate', 'closed_accept', 'new_cap', 'float_cap']:
            c = copy.deepcopy(self.data['capture'])
            if kind == 'duplicate': c['captures'].append(copy.deepcopy(c['captures'][0]))
            elif kind == 'alternate': c['captures'][6]['requested_url'] = 'https://example.com/alternative.pdf'
            elif kind == 'closed_accept': c['captures'][6]['identity_accepted'] = True
            elif kind == 'new_cap': c['prospective_limits']['bytes_per_response'] = 8000000
            else: c['prospective_limits']['locators'] = 15.0
            with self.subTest(kind=kind), self.assertRaises(ValueError): validate_capture(c)

    def test_actual_capture_byte_drift_fails_without_mutating_evidence(self):
        target = (ROOT/self.data['capture']['captures'][0]['raw_path']).resolve()
        original_read = type(target).read_bytes
        def changed_bytes(path):
            raw = original_read(path)
            return raw + b'drift' if path.resolve() == target else raw
        with patch('pathlib.Path.read_bytes', changed_bytes), self.assertRaises(ValueError):
            validate_capture(self.data['capture'])
        self.assertEqual(len(target.read_bytes()), self.data['capture']['captures'][0]['retained_bytes'])

    def test_resealed_core_and_compiled_output_drift_fail_replay(self):
        for kind in ['core', 'mapping', 'member', 'graph', 'proof']:
            d = self.changed('proof' if kind == 'proof' else 'products')
            if kind == 'core':
                core = d['products']['shared_action_core']; core['authoritative_for_new_editorial_work'] = True
            elif kind == 'mapping':
                d['products']['shared_issue_mapping']['action_mappings'][0]['eligibility']['parent_context_used'] = True
            elif kind == 'member':
                d['products']['member_projections'][0]['actions'][0]['official_status'] = 'Yea'
            elif kind == 'graph':
                d['products']['compiled_ir']['members'][0]['proposition_graph']['propositions'].append({'invented': True})
            else: d['proof']['behavioral_update_proof_exercised'] = True
            with self.subTest(kind=kind), self.assertRaises(ValueError): validate(d)


if __name__ == '__main__': unittest.main()
