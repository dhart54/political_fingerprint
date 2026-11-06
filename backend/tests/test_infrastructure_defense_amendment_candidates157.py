import copy
import unittest

from backend.app.semantic_ir.shared_corpus import (
    digest, sealed_digest, validate_member_projection, validate_shared_issue_mapping,
    SharedCorpusValidationError,
)
from scripts.validate_infrastructure_defense_amendment_candidates157 import (
    ROOT, P, inputs, replay, validate, validate_units, validate_extents,
    validate_manifest, validate_preservation,
)


class DefenseAmendments157Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = inputs()

    def changed(self, key):
        data = dict(self.data)
        data[key] = copy.deepcopy(data[key])
        return data

    def test_five_exact_amendments_replay_in_one_bounded_held_episode(self):
        result = validate(self.data)
        self.assertEqual((result['cores'], result['official_observations'], result['held_episodes'],
                          result['propositions'], result['sources']), (5, 10, 1, 0, 19))
        self.assertIs(result['canonical_changes'], False)
        self.assertEqual(validate_preservation(), 708)
        self.assertGreaterEqual(validate_manifest(), 15)
        for action in self.data['products']['shared_action_core']['actions']:
            self.assertEqual(action['package_component_boundary']['boundary_type'], 'exact_amendment')
            self.assertIs(action['package_component_boundary']['parent_package_meaning_projected'], False)

    def test_raw_official_labels_and_normalized_statuses_remain_distinct(self):
        pool = {x['source_id']: x for x in self.data['sources']['sources']}
        for aid in [x['action_id'] for x in self.data['authoring']['actions']]:
            source = pool['clerk:'+aid.split(':', 1)[1]]
            self.assertEqual(source['member_records']['F000477']['official_label'], 'No')
            self.assertEqual(source['member_records']['M001184']['official_label'], 'Aye')
        products = self.data['products']
        cores = {x['action_id']: x for x in products['shared_action_core']['actions']}
        for member in products['member_projections']:
            expected = ['Nay']*5 if member['member_id'] == 'F000477' else ['Yea']*5
            self.assertEqual([x['official_status'] for x in member['actions']], expected)
            for row in member['actions']:
                self.assertEqual(row['action_core_sha256'], cores[row['action_id']]['action_core_sha256'])

    def test_material_operator_definition_and_reference_drift_rejected(self):
        probes = [(0, 'REQUIRED sex/gender question', 'every sex/gender question'),
                  (0, 'not a scientific/clinical certification', 'a scientific/clinical certification'),
                  (1, 'CASE BY CASE', 'universally'),
                  (1, 'EXCEPT for emergency medical personnel', 'including emergency medical personnel'),
                  (2, 'NO study/report deadline printed', 'a90-day study/report deadline'),
                  (3, 'a MAXIMUM', 'a mandatory sentence'),
                  (3, 'WILLFUL misdemeanor', 'general-intent felony'),
                  (4, 'FISCAL2026', 'all fiscal years'),
                  (4, 'not itself appropriate/rescind1billion', 'automatically rescind1billion')]
        for index, old, new in probes:
            data = self.changed('authoring')
            for key in ['meaning', 'compact_description']:
                text = data['authoring']['actions'][index][key]
                self.assertTrue(old in text, 'Missing test fixture operator: '+old)
                data['authoring']['actions'][index][key] = text.replace(old, new)
            with self.subTest(index=index, operator=old), self.assertRaises(ValueError):
                validate(data)

    def test_own_report_number_and_final_recorded_result_are_required(self):
        original = {x['source_id']: x for x in self.data['sources']['sources']}
        sid = 'congressional-record:3838-amend7-roll250-choice158'
        for old, new in [('rejected', 'agreed to'), ('119–255', '119–225'), ('[Roll No. 250]', '[Roll No. 251]')]:
            pool = copy.deepcopy(original)
            self.assertTrue(old in pool[sid]['text'], 'Missing own recorded fixture: '+old)
            pool[sid]['text'] = pool[sid]['text'].replace(old, new)
            with self.subTest(operator=old), self.assertRaises(ValueError):
                validate_units(self.data['authoring'], pool, self.data['preflight'])

    def test_exact_printed_target_cannot_be_replaced_by_parent_table(self):
        pool = {x['source_id']: x for x in self.data['sources']['sources']}
        for operator in ['fiscal year 2026', '$1,000,000,000']:
            altered = copy.deepcopy(pool)
            sid = 'govinfo:rcp119-8-humanitarian-taiwan'
            altered[sid]['text'] = altered[sid]['text'].replace(operator, 'other value')
            with self.subTest(operator=operator), self.assertRaises(ValueError):
                validate_units(self.data['authoring'], altered, self.data['preflight'])

    def test_claim_passages_must_remain_in_their_exact_bound_source(self):
        for field in ['passage', 'source_id']:
            authoring = copy.deepcopy(self.data['authoring'])
            authoring['actions'][0]['claim_source_map'][0][field] = 'unobserved claim or source'
            with self.subTest(field=field), self.assertRaises((ValueError, KeyError)):
                replay(authoring, self.data['sources'])

    def test_resealed_retained_source_is_not_accepted_as_original(self):
        data = self.changed('sources')
        source = next(x for x in data['sources']['sources'] if x['source_id'] == 'govinfo:50usc797-2024')
        source['text'] = source['text'].replace('willfully', 'unknowingly')
        source['governed_bytes_sha256'] = sealed_digest(source, 'governed_bytes_sha256')
        with self.assertRaises(ValueError):
            validate(data)
        with self.assertRaises(ValueError):
            replay(self.data['authoring'], data['sources'])

    def test_retained_source_extents_do_not_acquire_new_evidence_or_authority(self):
        for key, value in [('new_acquisitions', 1), ('new_extractions', 1),
                           ('original_pdfs_or_visual_review', True), ('source_holds_changed', True)]:
            extents = copy.deepcopy(self.data['extents'])
            extents[key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                validate_extents(extents, self.data['sources'])

    def test_all_authority_flags_remain_literal_false(self):
        for key in ['accepted', 'canonical_application', 'publication', 'production']:
            for value in [True, 0]:
                data = self.changed('bundle')
                data['bundle'][key] = value
                data['bundle']['bundle_sha256'] = sealed_digest(data['bundle'], 'bundle_sha256')
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    validate(data)

    def test_mapping_cannot_accept_case_eligibility(self):
        products = self.data['products']
        mapping = copy.deepcopy(products['shared_issue_mapping'])
        row = mapping['action_mappings'][0]
        row['eligibility']['decision'] = 'accepted'
        row['mapping_sha256'] = sealed_digest(row, 'mapping_sha256')
        mapping['mapping_sha256'] = sealed_digest(mapping, 'mapping_sha256')
        with self.assertRaises(SharedCorpusValidationError):
            validate_shared_issue_mapping(ROOT, mapping, products['shared_action_core'])

    def test_shared_correction_rejects_both_stale_member_projections(self):
        products = self.data['products']
        after = copy.deepcopy(products['shared_action_core'])
        row = after['actions'][0]
        row['candidate_shared_limitations'].append('CONTROLLED qualification correction; no authority.')
        row['action_core_sha256'] = sealed_digest(row, 'action_core_sha256')
        after['corpus_sha256'] = digest(after['actions'])
        for member in products['member_projections']:
            with self.subTest(member=member['member_id']), self.assertRaises(SharedCorpusValidationError):
                validate_member_projection(ROOT, member, after)

    def test_unused_raw_ledger_input_changes_no_product(self):
        sources = copy.deepcopy(self.data['sources'])
        extra = {'source_id': 'synthetic:unused157', 'text': 'Controlled unused input, not evidence.'}
        extra['governed_bytes_sha256'] = digest(extra)
        sources['sources'].append(extra)
        self.assertEqual(digest(replay(self.data['authoring'], sources)), digest(self.data['products']))

    def test_member_identity_cannot_enter_authored_shared_meaning(self):
        authoring = self.data['authoring']
        text = str({key: authoring[key] for key in ['boundary', 'blocked_reason']})
        for row in authoring['actions']:
            text += str({key: row[key] for key in ['meaning', 'compact_description', 'limitations', 'choice_meanings']})
        self.assertTrue('Foushee' not in text and 'Massie' not in text)

    def test_hold_graph_observation_and_prior_identity_drift_fail_closed(self):
        for kind in ['hold', 'graph', 'member', 'prior']:
            key = 'authoring' if kind == 'hold' else 'preflight' if kind == 'prior' else 'products'
            data = self.changed(key)
            if kind == 'hold':
                data[key]['blocked_episode_ids'].clear()
            elif kind == 'graph':
                data[key]['compiled_ir']['members'][0]['proposition_graph']['propositions'].append({'invented': True})
            elif kind == 'member':
                data[key]['member_projections'][0]['actions'][0]['official_status'] = 'Yea'
            else:
                data[key]['prior_prepared_identities'][0] = data['authoring']['actions'][0]['action_id']
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                validate(data)


if __name__ == '__main__':
    unittest.main()
