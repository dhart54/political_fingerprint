import copy
import json
import re
import unittest

from backend.app.semantic_ir.shared_corpus import digest, sealed_digest
from backend.app.semantic_ir.adapters import build_persistence_proposal
from backend.app.semantic_ir.pipeline import run_editorial_pipeline
from backend.app.editorial_presentations.compiler import compile_public_issue_presentation, EditorialPresentationError
from scripts.prepare_immigration_shared_candidate import prepare, readable_candidates, reproducibility_proof
from scripts.validate_immigration_shared_candidate import DATA, validate


class ImmigrationCandidateIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values = [json.loads((DATA / (name+'.json')).read_text(encoding='utf-8'))
                      for name in ['authoring', 'sources', 'universe_proposal', 'membership_review']]
        cls.products = prepare(cls.values[0], cls.values[1], ['F000477', 'M001184'])

    @staticmethod
    def seal_universe(universe):
        universe['universe_subject_sha256'] = digest(dict(subject=universe['subject'],
            cutoff=universe['cutoff'], candidate_records=universe['candidate_dispositions']))
        universe['proposal_sha256'] = sealed_digest(universe, 'proposal_sha256')

    def test_fixed_inventory_and_every_clerk_observation(self):
        result = validate(*self.values)
        self.assertEqual(result['inventory_count'], 676)

    def test_direct_concurrence_uses_real_question_observations_and_one_episode(self):
        core, mapping, projections, _, result = self.products
        action = next(a for a in core['actions'] if a['action_id'] == 'house:119:1:203')
        self.assertEqual(action['exact_question'], 'On Agreeing to the Resolution')
        self.assertEqual(action['legislative_stage'], 'concurrence')
        episode = next(e for e in mapping['episodes'] if e['episode_id'] == 'episode:hr4:119')
        self.assertEqual(episode['action_ids'], ['house:119:1:168', 'house:119:1:203'])
        readable = readable_candidates(self.values[0], core, projections, result)
        for member, status in [('F000477', 'Nay'), ('M001184', 'Yea')]:
            projection = next(p for p in projections if p['member_id'] == member)
            row = next(a for a in projection['actions'] if a['action_id'] == action['action_id'])
            self.assertEqual(row['official_status'], status)
            self.assertEqual(row['action_core_sha256'], action['action_core_sha256'])
            finding = next(f for m in readable['members'] if m['member_id'] == member
                           for f in m['findings'] if action['action_id'] in f['action_ids'])
            self.assertEqual(finding['action_ids'], episode['action_ids'])

    def test_resealed_consideration_rule_cannot_become_final_concurrence(self):
        author, capture, _, _ = copy.deepcopy(self.values)
        action = next(a for a in author['actions'] if a['action_id'] == 'house:119:1:203')
        source = next(s for s in capture['sources'] if s['source_id'] == action['source_id'])
        old = action['deemed_concurrence']['passage']
        new = 'Resolved, That it shall be in order to consider a motion to concur in the Senate amendment.'
        source['text'] = source['text'].replace(old, new)
        source['governed_bytes_sha256'] = sealed_digest(source, 'governed_bytes_sha256')
        action['deemed_concurrence']['passage'] = new
        for claim in action['claim_source_map']:
            if claim['source_id'] == source['source_id']:
                claim['passage'] = claim['passage'].replace(old, new)
        with self.assertRaisesRegex(ValueError, 'exact governed operative clause'):
            prepare(author, capture, ['F000477', 'M001184'])

    def test_direct_concurrence_requires_the_bound_senate_amendment(self):
        author, capture, _, _ = copy.deepcopy(self.values)
        action = next(a for a in author['actions'] if a['action_id'] == 'house:119:1:203')
        action['additional_source_ids'].remove(action['deemed_concurrence']['senate_amendment_source_id'])
        with self.assertRaisesRegex(ValueError, 'exact Senate amendment'):
            prepare(author, capture, ['F000477', 'M001184'])

    def test_resealed_wrong_direct_concurrence_clerk_question_is_rejected(self):
        author, capture, _, _ = copy.deepcopy(self.values)
        source = next(s for s in capture['sources'] if s['source_id'] == 'clerk:119:1:203')
        source['metadata']['vote-question'] = 'On Ordering the Previous Question'
        source['governed_bytes_sha256'] = sealed_digest(source, 'governed_bytes_sha256')
        with self.assertRaisesRegex(ValueError, 'differs from exact Clerk question'):
            prepare(author, capture, ['F000477', 'M001184'])

    def test_resealed_wrong_amendment_version_or_future_date_is_rejected(self):
        for change in ['version', 'date']:
            with self.subTest(change=change):
                author, capture, _, _ = copy.deepcopy(self.values)
                source = next(s for s in capture['sources'] if s['source_id'] == 'govinfo:hr4eas')
                action = next(a for a in author['actions'] if a['action_id'] == 'house:119:1:203')
                if change == 'version':
                    source['text_version'] = 'EH'
                else:
                    source['text'] = source['text'].replace('July 17 (legislative day, July 16), 2025',
                                                         'July 19 (legislative day, July 18), 2025')
                    for claim in action['claim_source_map']:
                        if claim['source_id'] == source['source_id']:
                            claim['passage'] = source['text']
                source['governed_bytes_sha256'] = sealed_digest(source, 'governed_bytes_sha256')
                with self.assertRaisesRegex(ValueError, 'exact Senate amendment|follows the House choice'):
                    prepare(author, capture, ['F000477', 'M001184'])

    def test_direct_concurrence_cannot_create_a_separate_rule_episode(self):
        author, capture, _, _ = copy.deepcopy(self.values)
        action = next(a for a in author['actions'] if a['action_id'] == 'house:119:1:203')
        action['episode_id'] = 'episode:hres590:119'
        with self.assertRaisesRegex(ValueError, 'underlying bill episode'):
            prepare(author, capture, ['F000477', 'M001184'])

    def test_whole_house_replacement_preserves_actual_rule_choices(self):
        core, mapping, projections, _, result = self.products
        action = next(a for a in core['actions'] if a['action_id'] == 'house:119:2:108')
        self.assertEqual(action['exact_question'], 'On Agreeing to the Resolution')
        self.assertEqual(action['legislative_stage'], 'concurrence')
        self.assertEqual(next(r for r in mapping['action_mappings']
                             if r['action_id'] == action['action_id'])['episode_id'], 'episode:hr7147:119')
        self.assertIn('May22,2026', action['candidate_exact_action_meaning'].replace(' ', ''))
        readable = readable_candidates(self.values[0], core, projections, result)
        for mid, status in [('F000477', 'Nay'), ('M001184', 'Yea')]:
            row = next(a for p in projections if p['member_id'] == mid
                       for a in p['actions'] if a['action_id'] == action['action_id'])
            self.assertEqual(row['official_status'], status)
            self.assertEqual(row['action_core_sha256'], action['action_core_sha256'])
            findings = [f for m in readable['members'] if m['member_id'] == mid
                        for f in m['findings'] if action['action_id'] in f['action_ids']]
            self.assertEqual(len(findings), 1)

    def test_replacement_concurrence_rejects_unbound_or_partial_print_claim(self):
        for defect in ['missing_source', 'missing_reference', 'partial_claim']:
            with self.subTest(defect=defect):
                author, capture, _, _ = copy.deepcopy(self.values)
                action = next(a for a in author['actions'] if a['action_id'] == 'house:119:2:108')
                sid = action['deemed_replacement_concurrence']['replacement_text_source_id']
                if defect == 'missing_source':
                    capture['sources'] = [s for s in capture['sources'] if s['source_id'] != sid]
                elif defect == 'missing_reference':
                    action['additional_source_ids'].remove(sid)
                else:
                    claim = next(c for c in action['claim_source_map'] if c['source_id'] == sid)
                    claim['passage'] = claim['passage'][:400]
                with self.assertRaisesRegex(ValueError, 'whole exact Rules print'):
                    prepare(author, capture, ['F000477', 'M001184'])

    def test_resealed_replacement_print_wrong_bill_number_or_future_date_is_rejected(self):
        for defect in ['wrong_bill', 'wrong_print', 'future_date']:
            with self.subTest(defect=defect):
                author, capture, _, _ = copy.deepcopy(self.values)
                action = next(a for a in author['actions'] if a['action_id'] == 'house:119:2:108')
                sid = action['deemed_replacement_concurrence']['replacement_text_source_id']
                source = next(s for s in capture['sources'] if s['source_id'] == sid)
                old, new = {'wrong_bill': ('H.R. 7147', 'H.R. 7744'),
                            'wrong_print': ('119–21', '119–22'),
                            'future_date': ('March 27, 2026', 'March 28, 2026')}[defect]
                self.assertIn(old, source['text'])
                source['text'] = source['text'].replace(old, new)
                source['governed_bytes_sha256'] = sealed_digest(source, 'governed_bytes_sha256')
                next(c for c in action['claim_source_map'] if c['source_id'] == sid)['passage'] = source['text']
                with self.assertRaisesRegex(ValueError, 'whole exact Rules print|follows the House choice'):
                    prepare(author, capture, ['F000477', 'M001184'])

    def test_resealed_consideration_only_rule_cannot_adopt_replacement(self):
        author, capture, _, _ = copy.deepcopy(self.values)
        action = next(a for a in author['actions'] if a['action_id'] == 'house:119:2:108')
        source = next(s for s in capture['sources'] if s['source_id'] == action['source_id'])
        old = action['deemed_replacement_concurrence']['passage']
        new = 'Resolved, That it shall be in order to consider a motion to concur with the House replacement.'
        source['text'] = source['text'].replace(old, new)
        source['governed_bytes_sha256'] = sealed_digest(source, 'governed_bytes_sha256')
        action['deemed_replacement_concurrence']['passage'] = new
        next(c for c in action['claim_source_map'] if c['source_id'] == source['source_id'])['passage'] = new
        with self.assertRaisesRegex(ValueError, 'exact governed operative clause'):
            prepare(author, capture, ['F000477', 'M001184'])

    def test_replacement_cannot_use_a_rule_episode_or_two_conflicting_witnesses(self):
        for defect in ['rule_episode', 'parallel_witness']:
            with self.subTest(defect=defect):
                author, capture, _, _ = copy.deepcopy(self.values)
                action = next(a for a in author['actions'] if a['action_id'] == 'house:119:2:108')
                if defect == 'rule_episode':
                    action['episode_id'] = 'episode:hres1142:119'
                else:
                    action['deemed_concurrence'] = copy.deepcopy(action['deemed_replacement_concurrence'])
                with self.assertRaisesRegex(ValueError, 'underlying bill episode|invalid whole-replacement'):
                    prepare(author, capture, ['F000477', 'M001184'])

    def test_resealed_changed_exact_question_is_not_trusted(self):
        author, capture, universe, membership = copy.deepcopy(self.values)
        universe['candidate_dispositions'][0]['question'] = 'On Passage'
        self.seal_universe(universe)
        with self.assertRaisesRegex(ValueError, 'exact Clerk action identity differs'):
            validate(author, capture, universe, membership)

    def test_resealed_changed_member_observation_is_not_trusted(self):
        author, capture, universe, membership = copy.deepcopy(self.values)
        universe['candidate_dispositions'][0]['member_action'] = 'Yea'
        self.seal_universe(universe)
        with self.assertRaisesRegex(ValueError, 'Clerk member observation differs'):
            validate(author, capture, universe, membership)

    def test_resealed_cutoff_extension_is_rejected(self):
        author, capture, universe, membership = copy.deepcopy(self.values)
        universe['cutoff']['end_date'] = '2026-10-05'
        self.seal_universe(universe)
        with self.assertRaisesRegex(ValueError, 'fixed September 16 cutoff differs'):
            validate(author, capture, universe, membership)

    def test_duplicate_source_even_if_sealed_is_rejected(self):
        author, capture, universe, membership = copy.deepcopy(self.values)
        capture['sources'].append(copy.deepcopy(capture['sources'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate governed source identity'):
            validate(author, capture, universe, membership)

    def test_resealed_stale_disposition_identity_accounting_is_rejected(self):
        author, capture, universe, membership = copy.deepcopy(self.values)
        key = next(iter(universe['accounting']['action_ids_by_disposition']))
        universe['accounting']['action_ids_by_disposition'][key].pop()
        self.seal_universe(universe)
        with self.assertRaisesRegex(ValueError, 'disposition identity accounting differs'):
            validate(author, capture, universe, membership)

    def test_shared_prose_cannot_contain_observed_member_behavior(self):
        for action in self.values[0]['actions']:
            prose = json.dumps([action[key] for key in ['short_description', 'compact_description',
                'meaning', 'limitations', 'choice_meanings']])
            self.assertIsNone(re.search(r'\b(?:Foushee|Massie|F000477|M001184)\b', prose))

    def test_laken_parallel_bills_preserve_their_distinct_versions_and_episodes(self):
        author = {a['action_id']: a for a in self.values[0]['actions']}
        capture = {s['source_id']: s for s in self.values[1]['sources']}
        house, senate = [author[aid] for aid in ['house:119:1:6', 'house:119:1:23']]
        self.assertNotEqual(house['episode_id'], senate['episode_id'])
        self.assertEqual(capture[house['source_id']]['text_version'], 'EH')
        self.assertEqual(capture[senate['source_id']]['text_version'], 'ES')
        self.assertNotIn('assault of a law enforcement officer offense', capture[house['source_id']]['text'])
        self.assertIn('assault of a law enforcement officer offense', capture[senate['source_id']]['text'])

    def test_missing_material_baseline_cannot_compile(self):
        author, capture, _, _ = copy.deepcopy(self.values)
        sid = 'govinfo:8usc1226-2024-laken-context'
        capture['sources'] = [s for s in capture['sources'] if s['source_id'] != sid]
        with self.assertRaises(KeyError) as caught:
            prepare(author, capture, ['F000477', 'M001184'])
        self.assertEqual(caught.exception.args, (sid,))

    def test_laken_actual_choices_reuse_one_meaning_and_exclude_controls(self):
        core, _, projections, _, result = self.products
        by_action = {a['action_id']: a for a in core['actions']}
        for member in projections:
            actual = {a['action_id']: a for a in member['actions']}
            for aid in ['house:119:1:6', 'house:119:1:23']:
                self.assertEqual(actual[aid]['action_core_sha256'], by_action[aid]['action_core_sha256'])
                self.assertEqual(actual[aid]['official_status'], 'Nay' if member['member_id'] == 'F000477' else 'Yea')
            self.assertFalse({'house:119:1:20', 'house:119:1:21'} & actual.keys())
        readable = readable_candidates(self.values[0], core, projections, result)
        self.assertFalse(readable['production_eligible'])
        for member in readable['members']:
            for finding in member['findings']:
                for observation in finding['action_observations']:
                    if observation['action_id'] in ['house:119:1:6', 'house:119:1:23']:
                        self.assertEqual(observation['direction'], 'opposition' if member['member_id'] == 'F000477' else 'support')

    def test_immigration_candidates_fail_closed_at_all_public_persistence_entrypoints(self):
        inputs, compiled = self.products[3], self.products[-1].compiled_ir
        with self.assertRaisesRegex(ValueError, 'cannot prepare'):
            run_editorial_pipeline(inputs, prepare_persistence_proposal=True)
        with self.assertRaises(ValueError):
            build_persistence_proposal(compiled)
        with self.assertRaises(EditorialPresentationError):
            compile_public_issue_presentation(compiled, {}, trusted_action_source_contract={})

    def test_actual_present_status_keeps_shared_choices_without_a_directional_finding(self):
        core, _, projections, _, result = self.products
        aid = 'house:119:1:7'
        shared = next(a for a in core['actions'] if a['action_id'] == aid)
        self.assertEqual(set(shared['choice_meanings']), {'Yea', 'Nay'})
        member = next(p for p in projections if p['member_id'] == 'M001184')
        observed = next(a for a in member['actions'] if a['action_id'] == aid)
        self.assertEqual(observed['official_status'], 'Present')
        self.assertEqual(observed['action_core_sha256'], shared['action_core_sha256'])
        readable = readable_candidates(self.values[0], core, projections, result)
        massie = next(m for m in readable['members'] if m['member_id'] == 'M001184')
        foushee = next(m for m in readable['members'] if m['member_id'] == 'F000477')
        self.assertTrue(any(aid in f['action_ids'] for f in foushee['findings']))
        self.assertFalse(any(aid in f['action_ids'] for f in massie['findings']))
        self.assertIn({'action_id': aid, 'reason_code': 'non_directional_status',
            'detail': 'The action is explicitly excluded from behavioral evidence.'},
            massie['non_proposition_accounting'])

    def test_all_checked_in_generated_outputs_match_an_independent_replay(self):
        author, capture = self.values[:2]
        core, mapping, projections, inputs, result = self.products
        replay = dict(shared_action_core=core, shared_issue_mapping=mapping,
            member_projections=projections, compiler_input=inputs, compiled_ir=result.compiled_ir,
            readable_candidates=readable_candidates(author, core, projections, result),
            reproducibility_proof=reproducibility_proof(author, capture, ['F000477', 'M001184']))
        for name, value in replay.items():
            with self.subTest(output=name):
                stored = json.loads((DATA / 'generated' / (name+'.json')).read_text(encoding='utf-8'))
                self.assertEqual(stored, value)

    def test_recorded_audit_binds_current_meanings_sources_and_observations(self):
        audit_path = DATA.parents[2] / 'review_packets' / 'immigration_semantic_audit_in_progress.json'
        audit = json.loads(audit_path.read_text(encoding='utf-8'))
        actions = {a['action_id']: a for a in self.values[0]['actions']}
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        reviewed = {r['action_id']: r for r in audit['substantive_actions']}
        self.assertEqual(set(reviewed), set(actions))
        for aid, action in actions.items():
            with self.subTest(action=aid):
                record = reviewed[aid]
                self.assertEqual(record['corrected_authoring_action_sha256'], digest(action))
                clerk = sources['clerk:' + aid.removeprefix('house:')]
                self.assertEqual(record['exact_identity'], clerk['metadata'])
                self.assertEqual(record['recorded_member_observations'], clerk['member_records'])
                evidence = {s['source_id']: s for s in record['primary_evidence']}
                self.assertTrue({action['source_id'], *action['additional_source_ids']} <= evidence.keys())
                for sid, witness in evidence.items():
                    self.assertEqual(witness['governed_bytes_sha256'], sources[sid]['governed_bytes_sha256'])

    def test_noncounting_audit_sample_binds_current_ledger_and_covers_risks(self):
        audit_path = DATA.parents[2] / 'review_packets' / 'immigration_semantic_audit_in_progress.json'
        audit = json.loads(audit_path.read_text(encoding='utf-8'))
        ledger = {r['action_id']: r for r in self.values[3]['records']}
        sample = audit['noncounting_actions']
        for case in sample:
            self.assertEqual(case['corrected_review_record_sha256'], digest(ledger[case['action_id']]))
        self.assertGreaterEqual(sum(c['current_disposition'] == 'exact_action_ineligible' for c in sample), 12)
        self.assertGreaterEqual(sum(c['current_disposition'] == 'procedural_context' for c in sample), 6)
        expressive = {aid for aid, r in ledger.items() if r['disposition'] == 'expressive_nonbinding_context'}
        self.assertTrue(expressive <= {c['action_id'] for c in sample})


if __name__ == '__main__':
    unittest.main()
