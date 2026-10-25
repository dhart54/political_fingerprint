import copy
import unittest

from backend.app.semantic_ir.shared_corpus import digest, sealed_digest
from scripts.apply_infrastructure_case_decisions149 import (
    ACCEPT, ADMIT, EXCLUDE, SCOPE, MEMBERS, load_inputs, build_application,
    materialized_payload, before_payload, apply_to_current, validate_lossless,
    same_json,
)
from scripts.validate_infrastructure_case_application149 import (
    A, P, current_state, validate, validate_state, validate_preservation, validate_output_bytes,
)


class ExactCaseApplication149Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = load_inputs()
        cls.expected = build_application(cls.inputs)
        cls.current = current_state()

    def test_actual_outputs_replay_and_preservation(self):
        result = validate(self.current, self.expected, self.inputs)
        self.assertEqual((result['accepted_meanings'], result['admissions'], result['exclusions']), (9, 7, 3))
        self.assertEqual((result['unchanged_other_records'], result['new_existing_sources']), (666, 41))
        self.assertGreaterEqual(validate_preservation(), 282)
        self.assertEqual(validate_output_bytes(), 21)

    def test_stateful_fresh_then_no_write_is_pure_and_identical(self):
        before = before_payload(self.inputs)
        before_digest = digest(before)
        paths = [p for folder in [A, P] for p in folder.rglob('*') if p.is_file()]
        stamps = {str(p): (p.stat().st_mtime_ns, p.stat().st_size) for p in paths}
        first, change = apply_to_current(before, self.inputs)
        self.assertIs(change['changed'], True)
        self.assertTrue(same_json(first, self.current))
        second, repeat = apply_to_current(first, self.inputs)
        self.assertIs(repeat['changed'], False)
        self.assertTrue(same_json(first, second))
        self.assertIsNot(first, second)
        self.assertEqual(digest(before), before_digest)
        self.assertEqual(stamps, {str(p): (p.stat().st_mtime_ns, p.stat().st_size) for p in paths})

    def test_json_types_are_strict_on_fresh_and_no_write_paths(self):
        for post in [False, True]:
            base = self.current if post else before_payload(self.inputs)
            for component, field, replacement in [
                ('membership', 'authoritative_for_new_editorial_work', 0),
                ('universe', 'publication_authorized', 0),
                ('universe', 'production_writes', 0),
            ]:
                bad = dict(base); bad[component] = dict(base[component]); bad[component][field] = replacement
                with self.subTest(post=post, field=field), self.assertRaises(ValueError):
                    apply_to_current(bad, self.inputs)
            bad = dict(base); bad['research'] = dict(base['research'])
            bad['research']['shared_action_core'] = copy.deepcopy(base['research']['shared_action_core'])
            row = bad['research']['shared_action_core']['actions'][0]
            row['roll'] = float(row['roll'])
            with self.subTest(post=post, field='roll'), self.assertRaises(ValueError):
                apply_to_current(bad, self.inputs)
        self.assertFalse(same_json(False, 0))
        self.assertFalse(same_json(1, 1.0))

    def test_partial_and_resealed_post_state_are_rejected(self):
        partial = dict(before_payload(self.inputs)); partial['membership'] = self.current['membership']
        with self.assertRaises(ValueError): apply_to_current(partial, self.inputs)
        for field, value in [('publication_authorized', True), ('full_record_claim', True), ('production_writes', True)]:
            bad = dict(self.current); bad['universe'] = copy.deepcopy(self.current['universe'])
            bad['universe'][field] = value
            bad['universe']['proposal_sha256'] = sealed_digest(bad['universe'], 'proposal_sha256')
            with self.subTest(field=field), self.assertRaises(ValueError): apply_to_current(bad, self.inputs)

    def test_lifecycle_conversion_is_lossless_for_every_pinned_subject(self):
        original = self.inputs[4]
        for core in self.current['accepted']['shared_action_core']['actions']:
            validate_lossless(original[core['action_id']]['core'], core)
            self.assertEqual(core['accepted_exact_action_meaning'], original[core['action_id']]['core']['candidate_exact_action_meaning'])
            self.assertNotIn('candidate_exact_action_meaning', core)
            self.assertNotIn('candidate_shared_limitations', core)

    def test_resealed_literal_qualification_and_type_drift_fail_lossless_check(self):
        core = self.current['accepted']['shared_action_core']['actions'][0]
        original = self.inputs[4][core['action_id']]['core']
        for field, value in [('accepted_exact_action_meaning', core['accepted_exact_action_meaning'] + ' changed'),
                             ('roll', float(core['roll'])), ('session', True),
                             ('accepted_shared_limitations', []), ('candidate_shared_limitations', [])]:
            bad = copy.deepcopy(core); bad[field] = value
            bad['action_core_sha256'] = sealed_digest(bad, 'action_core_sha256')
            with self.subTest(field=field), self.assertRaises(ValueError): validate_lossless(original, bad)

    def test_accepted_nine_and_admitted_seven_do_not_promote_candidates(self):
        accepted = self.current['accepted']; research = self.current['research']
        self.assertEqual([c['action_id'] for c in accepted['shared_action_core']['actions']], ACCEPT)
        self.assertEqual([r['action_id'] for r in accepted['shared_issue_mapping']['action_mappings']], ADMIT)
        self.assertTrue(set(EXCLUDE).isdisjoint(ADMIT))
        self.assertIs(research['shared_action_core']['authoritative_for_new_editorial_work'], False)
        self.assertIs(research['shared_issue_mapping']['authoritative_for_new_editorial_work'], False)
        self.assertEqual(len(research['shared_action_core']['actions']), 70)
        self.assertIsNone(self.current['universe']['approval_receipt'])

    def test_not_voting_is_resolved_without_directional_evidence(self):
        for projection, member in zip(self.current['accepted']['member_projections'], MEMBERS):
            self.assertEqual(projection['member_id'], member)
            self.assertEqual([r['action_id'] for r in projection['actions']], ADMIT)
        massie = next(p for p in self.current['accepted']['member_projections'] if p['member_id'] == 'M001184')
        row = next(r for r in massie['actions'] if r['action_id'] == 'house:119:2:188')
        self.assertEqual(row['official_status'], 'Not Voting')
        member = next(m for m in self.current['accepted']['compiled_ir']['members'] if m['member_id'] == 'M001184')
        self.assertEqual(member['coverage']['directional_yes_no_positions'], 6)
        self.assertEqual(member['coverage']['not_voting_actions'], 1)
        self.assertTrue(all('house:119:2:188' not in p['evidence_action_ids'] for p in member['proposition_graph']['propositions']))

    def test_scope_rationales_preserve_research_and_disclosure_boundaries(self):
        rows = {r['action_id']: r for r in self.current['membership']['records']}
        self.assertIn('substantive mandatory GAO', rows['house:119:1:12']['rationale'])
        self.assertIn('not an athletics-subject', rows['house:119:1:12']['rationale'])
        self.assertIn('does not deploy', rows['house:119:1:9']['rationale'])
        self.assertIn('pre-purchase disclosure/enforcement', rows['house:119:1:109']['rationale'])
        self.assertNotIn('house:119:1:12', ACCEPT)
        for aid in ['house:119:1:22', 'house:119:1:28']:
            self.assertEqual(rows[aid]['disposition'], 'exact_action_ineligible')

    def test_sources_are_only_the_exact_preserved_admission_closure(self):
        sources = self.current['sources']['sources']; before = self.inputs[0]['sources.json']['sources']
        self.assertTrue(same_json(sources[:1621], before))
        self.assertEqual(len(sources), 1662)
        additions = self.inputs[3]['sources']; witnesses = self.inputs[5]
        self.assertEqual({s['source_id'] for s in sources[1621:]}, {s['source_id'] for s in additions})
        for source in sources[1621:]: self.assertTrue(same_json(source, witnesses[source['source_id']]))

    def test_authority_subject_ledger_and_source_caps_cannot_be_resealed(self):
        for index, field, value in [(1, 'publication_authorized', True), (1, 'HR28_meaning_accepted', True),
                                    (1, 'global_corpus_acceptance', True), (2, 'accepted_meaning_ids', ACCEPT + ['house:119:2:49']),
                                    (3, 'object_count_cap', 42), (3, 'new_acquisition', True)]:
            inputs = list(self.inputs); inputs[index] = copy.deepcopy(inputs[index]); inputs[index][field] = value
            with self.subTest(index=index, field=field), self.assertRaises(ValueError): build_application(inputs)

    def test_prepared_baseline_and_pinned_subjects_are_authenticated(self):
        for name in ['membership_review.json', 'sources.json', 'generated/readable_candidates.json']:
            inputs = list(self.inputs); inputs[0] = dict(inputs[0]); inputs[0][name] = copy.deepcopy(inputs[0][name])
            inputs[0][name]['unexpected'] = 'drift'
            with self.subTest(name=name), self.assertRaises(ValueError): build_application(inputs)
        for part in ['core', 'authoring', 'mapping', 'episode', 'projections']:
            inputs = list(self.inputs); inputs[4] = dict(inputs[4]); aid = ADMIT[0]
            inputs[4][aid] = copy.deepcopy(inputs[4][aid]); inputs[4][aid][part]['unexpected'] = 'drift'
            with self.subTest(part=part), self.assertRaises(ValueError): build_application(inputs)

    def test_governed_source_witness_drift_is_rejected_even_when_resealed(self):
        inputs = list(self.inputs); inputs[5] = dict(inputs[5]); sid = self.inputs[3]['sources'][0]['source_id']
        inputs[5][sid] = copy.deepcopy(inputs[5][sid]); inputs[5][sid]['text'] += ' altered'
        inputs[5][sid]['governed_bytes_sha256'] = sealed_digest(inputs[5][sid], 'governed_bytes_sha256')
        with self.assertRaises(ValueError): build_application(inputs)

    def test_full_validator_rejects_resealed_receipt_authority_and_wrong_cohorts(self):
        for field, value in [('publication_authorized', 0), ('exact_nine_meaning_acceptance', 1),
                             ('HR28_meaning_accepted', True), ('accepted_meaning_ids', ACCEPT + ['house:119:1:12']),
                             ('admitted_action_ids', ADMIT + ['house:119:1:22'])]:
            bad = dict(self.current); bad['receipt'] = copy.deepcopy(self.current['receipt']); bad['receipt'][field] = value
            bad['receipt']['receipt_sha256'] = sealed_digest(bad['receipt'], 'receipt_sha256')
            with self.subTest(field=field), self.assertRaises(ValueError): validate_state(bad, self.inputs)

    def test_semantic_output_drift_cannot_pass_full_replay(self):
        bad = dict(self.current); bad['accepted'] = dict(self.current['accepted'])
        bad['accepted']['presentation_payload'] = copy.deepcopy(bad['accepted']['presentation_payload'])
        bad['accepted']['presentation_payload']['unexpected'] = True
        with self.assertRaises(ValueError): validate(bad, self.expected, self.inputs)


if __name__ == '__main__':
    unittest.main()
