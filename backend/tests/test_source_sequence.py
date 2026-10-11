import unittest
from scripts.validate_source_sequence import require_source_sequence, require_exact_bill_operative, require_same_action_passage_stages

class SourceSequenceTests(unittest.TestCase):
    def test_source_order_with_printed_line_wraps(self):
        text = 'The question is on the amendment. The noes ap-\npeared to have it. I demand a recorded vote. A recorded vote was ordered. [Roll No. 174]'
        positions = require_source_sequence(text, ['The question is', 'noes appeared', 'I demand', 'vote was ordered', '[Roll No. 174]'])
        self.assertEqual(positions, sorted(positions))

    def test_numeric_duration_hyphen_preserved(self):
        require_source_sequence('this 15-\nminute vote', ['15-minute vote'])

    def test_reversed_voice_and_question_rejected(self):
        with self.assertRaises(ValueError):
            require_source_sequence('The question is on the amendment. The noes appeared to have it.', ['noes appeared', 'The question is'])

    def test_absent_postponement_rejected(self):
        with self.assertRaises(ValueError):
            require_source_sequence('The ayes appeared to have it. The yeas and nays were ordered. [Roll No. 29]', ['ayes appeared', 'were postponed', '[Roll No. 29]'])

    def test_normalized_empty_anchor_rejected(self):
        for blank in [' ', '\t\n', '\u00a0']:
            for anchors in [[blank], ['question', blank]]:
                with self.subTest(anchors=anchors), self.assertRaisesRegex(ValueError, 'nonempty explicit source anchors required'):
                    require_source_sequence('question then vote', anchors)

    def test_offered_identity_accepts_printed_spacing(self):
        self.assertEqual(require_exact_bill_operative('The text of the bill, as amended, is as follows: H. R. 1329 Be it enacted by the Senate and House of Rep-\nresentatives', 'H.R. 1329'), 'H.R.1329')

    def test_adjacent_bill_rejected_despite_reference_to_expected_bill(self):
        with self.assertRaisesRegex(ValueError, 'identity differs'):
            require_exact_bill_operative('Earlier debate mentioned H.R. 1329. The text of the bill, as amended, is as follows: H.R. 6047 Be it enacted by the Senate', 'H.R.1329')

    def test_multiple_offered_bodies_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            require_exact_bill_operative('The text of the bill is as follows: S. 1318 Be it enacted by the Senate. The text of the bill is as follows: H.R. 7567 Be it enacted by the Senate.', 'S.1318')

    def test_debate_and_title_alone_cannot_bind_operative(self):
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            require_exact_bill_operative('The Clerk read the title of the bill. The CHAIR. Debate on H.R. 7567.', 'S.1318')

    def test_unparseable_expected_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, 'explicit'):
            require_exact_bill_operative('The text of the bill is as follows: S. 1318 Be it enacted by', '1318')

    def test_checkpoint181_wrong_action_witnesses_rejected(self):
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        sources = json.loads((root / 'docs/editorial/shared_candidates/house_119_immigration_20260916/sources.json').read_text(encoding='utf-8-sig'))
        by_id = {source['source_id']: source for source in sources['sources']}
        for roll, bill in [(142, 'S.1318'), (188, 'H.R.1329'), (198, 'H.R.7726')]:
            with self.subTest(roll=roll), self.assertRaises(ValueError):
                require_exact_bill_operative(by_id[f'immigration:roll{roll}-operative181']['text'], bill)

    def test_fisa_candidate_retains_conditional_waiver_and_approval_exception(self):
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        receipt = json.loads((root / 'docs/editorial/shared_candidates/house_119_immigration_20260916/fisa_precision_correction_checkpoint184.json').read_text())
        core = json.loads((root / receipt['active_candidate_core_path']).read_text())
        mapping = json.loads((root / receipt['active_candidate_issue_mapping_path']).read_text())
        finding = next(action for action in receipt['qualified_held_findings'] if action['action_id'] == 'house:119:2:142')
        qualification = next(action for action in mapping['action_mappings'] if action['action_id'] == 'house:119:2:142')['structural_metadata']['candidate_exact_qualification']
        for meaning in [core['actions'][0]['candidate_exact_action_meaning'], finding['candidate_observation'], qualification]:
            require_source_sequence(meaning, ['The monthly submission clause (D)(iv) is within the expanded FISC waiver range'] + receipt['source_qualification_anchors'])

    def test_isolated_monthly_submission_waiver_linkage_deletion_rejected(self):
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        receipt = json.loads((root / 'docs/editorial/shared_candidates/house_119_immigration_20260916/fisa_precision_correction_checkpoint184.json').read_text())
        core = json.loads((root / receipt['active_candidate_core_path']).read_text())
        mapping = json.loads((root / receipt['active_candidate_issue_mapping_path']).read_text())
        finding = next(action for action in receipt['qualified_held_findings'] if action['action_id'] == 'house:119:2:142')
        qualification = next(action for action in mapping['action_mappings'] if action['action_id'] == 'house:119:2:142')['structural_metadata']['candidate_exact_qualification']
        linkage = 'The monthly submission clause (D)(iv) is within the expanded FISC waiver range'
        for meaning in [core['actions'][0]['candidate_exact_action_meaning'], finding['candidate_observation'], qualification]:
            with self.subTest(meaning=meaning):
                start = meaning.index(linkage)
                end = meaning.index(' The FISC waiver applies only', start)
                mutated = meaning[:start] + meaning[end:]
                # Finding/exception anchors survive this isolated deletion;
                # they cannot verify the missing monthly-submission linkage.
                require_source_sequence(mutated, receipt['source_qualification_anchors'])
                with self.assertRaises(ValueError):
                    require_source_sequence(mutated, [linkage] + receipt['source_qualification_anchors'])

    def test_prior_fisa_candidate_without_material_waiver_rejected(self):
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        prior = json.loads((root / 'docs/editorial/shared_candidates/house_119_source_review_checkpoint184_history/prior_shared_action_core_proposal182.json').read_text())
        with self.assertRaises(ValueError):
            require_source_sequence(prior['actions'][0]['candidate_exact_action_meaning'], ['FISC waiver applies only', 'finding', 'similar compliance outcomes'])

    def test_generic_waiver_or_unconditional_prior_approval_rejected(self):
        anchors = ['FISC waiver applies only', 'finding', 'measures reasonably expected to result in similar compliance outcomes', 'without prior approval', 'reasonable belief', 'mitigating or eliminating a threat to life or serious bodily harm']
        incomplete = [
            'The FISC may waive submissions at its discretion; attorney approval always required.',
            'FISC waiver applies only upon a finding of measures reasonably expected to result in similar compliance outcomes; attorney approval always required.',
        ]
        for meaning in incomplete:
            with self.subTest(meaning=meaning), self.assertRaises(ValueError):
                require_source_sequence(meaning, anchors)

    def test_definitions_import_bridge_bound_to_all_held_fisa_actions(self):
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        receipt = json.loads((root / 'docs/editorial/shared_candidates/house_119_immigration_20260916/fisa_precision_correction_checkpoint184.json').read_text())
        required = 'govinfo:50usc1881-services181'
        for action in receipt['qualified_held_findings']:
            with self.subTest(action=action['action_id']):
                self.assertIn(required, action['source_ids'])
                self.assertIn(required, {claim['source_id'] for claim in action['claim_source_map']})
        core = json.loads((root / receipt['active_candidate_core_path']).read_text())['actions'][0]
        self.assertIn(required, {source['source_id'] for source in core['operative_meaning_source_identities']})
        self.assertIn(required, core['semantic_ir_source_ids'])
        mapping = json.loads((root / receipt['active_candidate_issue_mapping_path']).read_text())
        for action in mapping['action_mappings']:
            with self.subTest(mapping=action['action_id']):
                self.assertIn(required, action['structural_metadata']['source_ids'])

    def test_roll200_wrong_initial_stage_rejected_with_other_stages_unchanged(self):
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        catalog = json.loads((root / 'docs/editorial/shared_candidates/house_119_immigration_20260916/sources.json').read_text(encoding='utf-8-sig'))
        by_id = {source['source_id']: source for source in catalog['sources']}
        declaration = by_id['immigration:roll200-identity191']
        correct = by_id['immigration:roll200-initial-corrected193']
        following = by_id['immigration:roll200-next-action-boundary193']
        result = by_id['immigration:roll200-recorded191']
        wrong = by_id['immigration:roll200-initial191']
        self.assertEqual(require_same_action_passage_stages(
            declaration, correct, following, result, 'S.1582', 200), 'S.1582')
        # Both real witnesses pass the earlier ordering-only check. Only the
        # initial source is substituted; S.1582 declaration/result stay exact.
        for source in (correct, wrong):
            require_source_sequence(source['text'], ['question is on', 'ayes appeared',
                'demand the yeas and nays', 'yeas and nays were ordered',
                'proceedings on this question will be postponed'])
        with self.assertRaisesRegex(ValueError, 'outside the declared action boundary'):
            require_same_action_passage_stages(
                declaration, wrong, following, result, 'S.1582', 200)

    def test_roll200_active_question_locator_matches_corrected_literal_source(self):
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        directory = root / 'docs/editorial/shared_candidates/house_119_immigration_20260916'
        load = lambda name: json.loads((directory / name).read_text(encoding='utf-8-sig'))
        receipt = load('financial_package_source_qualification_checkpoint191.json')
        correction = load('roll200_stage_identity_correction_checkpoint193.json')
        catalog = load('sources.json')
        source = next(item for item in catalog['sources']
                      if item['source_id'] == correction['active_corrected_source_id'])
        question = source['source_text_extents'][0]['start'] + source['text'].index('question is on')
        self.assertEqual(correction['question_start'], question)
        self.assertEqual(receipt['read_progress']['own_initial_passage_sequence_positions']['roll200'], question)
        # A locally valid question in the historical witness belongs to another
        # action and must not supply this action's active locator.
        historical = next(item for item in catalog['sources']
                          if item['source_id'] == correction['historical_wrong_source_id'])
        historical_question = historical['source_text_extents'][0]['start'] + historical['text'].index('question is on')
        self.assertNotEqual(historical_question, question)
