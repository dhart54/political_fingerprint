"""Focused regression and preservation checks for the research-only diagnostic."""
import copy
from collections import Counter
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('currency44_diagnostic', HERE / 'diagnose_currency.py')
d = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d)


class CurrencyDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages, cls.locators, _ = d.load_source('.')
        cls.rows = d.split_rows(cls.pages, cls.locators)
        cls.reviews = json.loads((HERE / 'reviewed_rows.json').read_text(encoding='utf8'))['rows']

    def test_reproduces_nine_rejections_and_fifteen_partial_matches(self):
        report = d.make_report(self.rows, [])
        self.assertEqual((report['legacy_missing_amounts'], report['legacy_partial_amounts']), (9, 15))
        self.assertEqual(len(report['unresolved_target_rows']), 24)
        for row in report['target_rows']:
            with self.subTest(row=row['row_id']):
                self.assertIsNone(row['separate_visual_transcription'])
                self.assertEqual(row['status'], 'requires_visual_review')

    def test_does_not_accept_suffix_of_split_or_attached_run(self):
        cases = [('1 5,000,000', 15000000), ('2,000 ,000', 2000000), ('82 0,000', 820000)]
        for literal, provisional in cases:
            with self.subTest(literal=literal):
                spans = d.numeric_spans('Project ' + literal + ' Senator S')
                self.assertEqual(len(spans), 1)
                self.assertEqual(spans[0]['literal'], literal)
                self.assertEqual(spans[0]['provisional_value'], provisional)
        attached = d.numeric_spans('Project USD2 50,000 Senator S')
        self.assertEqual(attached[0]['literal'], '2 50,000')
        self.assertIsNone(attached[0]['provisional_value'])

    def test_numeric_name_punctuation_is_not_an_amount(self):
        spans = d.numeric_spans('AS220, RI, District 1, ME, Future 5, CT, for equipment 1,120,000 Reed S')
        self.assertEqual([x['literal'] for x in spans], ['1,120,000'])

    def test_ambiguous_adjacent_values_and_bad_grouping_stay_unresolved(self):
        for text in ['Project 1,000,000 2,000,000 Senator S', 'Project 100,,000 Senator S']:
            with self.subTest(text=text):
                self.assertIsNone(d.numeric_spans(text)[0]['provisional_value'])

    def test_same_989_rows_and_seven_account_boundaries(self):
        self.assertEqual(len(self.rows), 989)
        self.assertEqual(len({r['row_id'] for r in self.rows}), 989)
        self.assertEqual(dict(Counter(r['branch'] for r in self.rows)),
                         dict(P1=108, P2=386, P3=79, P4=63, P5=36, P6=156, P7=161))
        upstream = json.loads(d.git_blob('.', d.SOURCE_REF, d.ROOT + 'batch4/diagnostic_extraction_limits.json'))
        report = d.make_report(self.rows, [])
        for group in upstream['account_diagnostics']:
            self.assertEqual(report['legacy_account_sums'][group['branch']], group['diagnostic_total'])

    def test_all_target_bindings_and_separate_visual_readings(self):
        report = d.make_report(self.rows, self.reviews)
        self.assertEqual(len(report['target_rows']), 24)
        self.assertFalse(report['unresolved_target_rows'])
        self.assertFalse(report['all_rows_visually_certified'])
        self.assertEqual(sum(r['status'] == 'target_field_visually_checked' for r in report['target_rows']), 24)

    def test_missing_review_is_reported_without_forced_balance(self):
        full = d.make_report(self.rows, self.reviews)
        missing = self.reviews[0]
        partial = d.make_report(self.rows, self.reviews[1:])
        self.assertEqual(partial['unresolved_target_rows'], [missing['row_id']])
        self.assertEqual(full['revised_partial_or_complete_sums'][missing['branch']] -
                         partial['revised_partial_or_complete_sums'][missing['branch']],
                         missing['visual_amount_dollars'])

    def test_changed_visual_amount_is_retained_as_disagreement(self):
        reviews = copy.deepcopy(self.reviews)
        reviews[0]['visual_amount_dollars'] += 1
        report = d.make_report(self.rows, reviews)
        row = next(r for r in report['target_rows'] if r['row_id'] == reviews[0]['row_id'])
        self.assertEqual(row['status'], 'visual_text_disagreement_unresolved')
        self.assertEqual(row['separate_visual_transcription']['visual_amount_dollars'], 250001)
        self.assertIn(row['row_id'], report['unresolved_target_rows'])

    def test_page_offset_account_and_literal_binding_mutations_fail(self):
        for field, value in [('pdf_page', 999), ('printed_page', 'H999'), ('row_on_page', 999),
                             ('start', -1), ('end', 1), ('branch', 'P7'),
                             ('literal', 'changed literal'), ('literal_utf8_sha256', '0' * 64)]:
            with self.subTest(field=field):
                reviews = copy.deepcopy(self.reviews)
                reviews[0][field] = value
                with self.assertRaises(ValueError):
                    d.make_report(self.rows, reviews)

    def test_wrong_column_and_missing_view_identity_fail(self):
        for field, value in [('column_index', 5), ('column_label', 'Senate'), ('image_sha256', '')]:
            with self.subTest(field=field):
                reviews = copy.deepcopy(self.reviews)
                reviews[0][field] = value
                with self.assertRaises(ValueError):
                    d.make_report(self.rows, reviews)

    def test_duplicate_and_unknown_review_fail(self):
        with self.assertRaises(ValueError):
            d.make_report(self.rows, self.reviews + [self.reviews[0]])
        unknown = copy.deepcopy(self.reviews[0]); unknown['row_id'] = 'unknown'
        with self.assertRaises(ValueError):
            d.make_report(self.rows, [unknown])

    def test_image_mutation_and_restricted_view_route_fail(self):
        review = copy.deepcopy(self.reviews[0])
        with patch.object(d, 'git_blob', return_value=b'changed image'):
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                d.verify_review_views('.', 'index', [review])
        review['image_path'] = d.ROOT + 'batch2/source_parents.zip'
        with self.assertRaisesRegex(ValueError, 'outside permitted'):
            d.verify_review_views('.', 'index', [review])

    def test_tampered_page_unknown_prefix_and_duplicate_page_fail(self):
        pages = copy.deepcopy(self.pages)
        target = next(p for p in pages if p['pdf_page'] == 247)
        target['text'] += 'changed'
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            d.split_rows(pages, self.locators)
        pages = copy.deepcopy(self.pages)
        with self.assertRaisesRegex(ValueError, 'Duplicate page'):
            d.split_rows(pages + [pages[0]], self.locators)
        with self.assertRaisesRegex(ValueError, 'account prefix'):
            d.split_rows(self.pages, self.locators[1:])

    def test_delta_arithmetic_independent_of_reference_totals(self):
        report = d.make_report(self.rows, self.reviews)
        by_id = {r['row_id']: r for r in self.rows}
        expected = Counter()
        for r in self.reviews:
            expected[r['branch']] += r['visual_amount_dollars'] - (by_id[r['row_id']]['legacy_value'] or 0)
        self.assertEqual(report['delta_from_separate_visual_transcriptions'], dict(expected))
        for branch, old in report['legacy_account_sums'].items():
            self.assertEqual(report['revised_partial_or_complete_sums'][branch], old + expected[branch])
        self.assertEqual(sum(report['revised_partial_or_complete_sums'].values()), 1386898000)
        self.assertEqual(sum(expected.values()), 32019000)

    def test_inputs_preserved_and_repeated_calls_are_isolated(self):
        before = copy.deepcopy((self.pages, self.locators, self.rows, self.reviews))
        local_rows, local_reviews = copy.deepcopy((self.rows, self.reviews))
        first = d.make_report(local_rows, local_reviews)
        target_id = first['target_rows'][0]['row_id']
        original = next(r for r in self.rows if r['row_id'] == target_id)
        first['target_rows'][0]['numeric_spans'][0]['literal'] = 'caller mutation'
        first['target_rows'][0]['separate_visual_transcription']['visual_amount_dollars'] = 1
        self.assertEqual(next(r for r in local_rows if r['row_id'] == target_id)['numeric_spans'],
                         original['numeric_spans'], 'Returned nested data must not alias the source fixture')
        self.assertEqual(local_reviews, self.reviews)
        first['target_rows'].clear()
        second = d.make_report(local_rows, local_reviews)
        self.assertEqual(len(second['target_rows']), 24)
        self.assertEqual((self.pages, self.locators, self.rows, self.reviews), before)
        self.assertTrue(all(r['literal'] == next(p['text'] for p in self.pages if p['pdf_page'] == r['pdf_page'])
                            [r['start']:r['end']] for r in self.rows))


if __name__ == '__main__':
    unittest.main()
