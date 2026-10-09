import unittest
from scripts.validate_source_sequence import require_source_sequence, require_exact_bill_operative

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
