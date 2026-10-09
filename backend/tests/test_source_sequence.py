import unittest
from scripts.validate_source_sequence import require_source_sequence

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
