"""Bounded offline source/mapping checks; no candidate imports or writes."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from pypdf import PdfReader
from source_tools import Text, pre, normalize, plain, between, replay

P = Path(__file__).resolve().parent
X = json.loads((P/'passages.json').read_text(encoding='utf8'))['passages']
T = {r['id']: r['text'] for r in X}
C = json.loads((P/'comparison.json').read_text(encoding='utf8'))
E = json.loads((P/'existing_sources.json').read_text(encoding='utf8'))


class Qualification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.streams = {n: pre((P/n).read_bytes()) for n in ['pl117263.html', 'pl117286.html']}
        p = Text(); p.feed((P/'code401.html').read_text(encoding='utf8'))
        cls.streams['code401.html:display'] = normalize(''.join(p.parts))
        cls.streams.update({r['source_id']: r['text'] for r in E['sources']})
        cls.pdf = PdfReader(P/'pl117286.pdf')
        for i in [166, 167, 168]:
            cls.streams['pl117286.pdf:page'+str(i)] = cls.pdf.pages[i-1].extract_text()

    def test_all_literal_passage_bindings(self):
        for r in X:
            with self.subTest(id=r['id']):
                s = self.streams[r['source']]
                self.assertEqual(len(s), r['total'])
                self.assertEqual(s[r['start']:r['end']], r['text'])
                self.assertEqual(hashlib.sha256(r['text'].encode()).hexdigest(), r['text_sha256'])

    def test_raw_identity_receipts(self):
        for r in json.loads((P/'capture_receipts.json').read_text()):
            b = (P/r['file']).read_bytes()
            self.assertEqual(r['http_status'], 200)
            self.assertEqual(len(b), r['raw_bytes'])
            self.assertEqual(hashlib.sha256(b).hexdigest(), r['raw_sha256'])

    def test_complete_pdf_required_for_savings(self):
        self.assertEqual(len(self.pdf.pages), 168)
        self.assertNotIn('SEC. 5. TRANSITIONAL AND SAVINGS', self.streams['pl117286.html'])
        self.assertIn('SEC. 5. TRANSITIONAL AND SAVINGS', T['pdf166'])
        self.assertIn('Approved December 27, 2022', T['pdf168'])

    def test_cutoff_and_correspondence_not_repeal_erasure(self):
        s = normalize(T['pdf166'])
        for phrase in ['October 19, 2021', 'enacted after that date', 'is deemed to amend or repeal',
                       'to the extent of the inconsistency', 'continues in effect']:
            self.assertIn(phrase, s)
        self.assertIn('rights and duties', normalize(T['pdf167']))

    def test_2022_identity_dates(self):
        self.assertIn('Public Law 117-263', self.streams['pl117263.html'])
        self.assertIn('Approved December 23, 2022.', self.streams['pl117263.html'])
        self.assertIn('Public Law 117-286', self.streams['pl117286.html'])
        self.assertIn('DEC. 27, 2022', T['pdf166'])

    def test_definition_mapping_and_operand_discrepancy(self):
        self.assertIn('paragraph (4) of this section', T['code401_note'])
        self.assertIn('paragraphs (1) to (5)', T['code401_note'])
        self.assertIn('began with "The term"', T['code401_note'])
        self.assertIn('except as otherwise expressly provided', C['401_ig_qualifier_payload'])
        self.assertNotIn('401_ig_correspondence_display', C)

    def test_replay_determinism_and_input_isolation(self):
        saved = copy.deepcopy(X)
        self.assertEqual(replay(X), C)
        self.assertEqual(X, saved)
        self.assertEqual(replay(copy.deepcopy(X)), C)

    def test_403_untouched_parts_survive(self):
        before = C['403_before']; after = C['403_after_selected_2022']
        for first,last in [('(a) In General.--','(b) Removal'), ('(c) Not Employee','(d) Assistant'),
                           ('(e) Rate of Pay.--','(f) Prohibition'), ('(f) Prohibition','(g) Legal Advice.--')]:
            self.assertEqual(between(before,first,last), between(after,first,last))
        self.assertEqual(before.split('(g) Legal Advice.--',1)[1].strip(),
                         after.split('(g) Legal Advice.--',1)[1].split('(h)(1)',1)[0].strip())

    def test_removal_nonduty_distinct_clocks_and_savings(self):
        s = C['403_after_selected_2022']
        for v in ['not later than 30 days before the removal or transfer',
                  'Nothing in this subsection shall prohibit a personnel action',
                  'not later than 15 days before the date',
                  'during the 30-day period preceding', 'including the report required under clause (ii)',
                  'without regard to whether the Senate provided advice and consent']:
            self.assertIn(v, s)

    def test_acting_qualifications_and_exceptions_retained(self):
        s = C['403_after_selected_2022']
        for v in ['365-day period', 'not less than 90 days', 'shall not apply if the officer is an Inspector General',
                  'does not qualify as service', 'GS-15', 'with respect to only 1 Inspector General position',
                  'subject to the time limitations of section 3346', 'not fewer than 90 of the 365 days']:
            self.assertIn(v, s)

    def test_acting_applicability_not_every_vacancy_immediate(self):
        s = plain(T['5203de'])
        for v in ['other than with respect to section 3345(a)', 'Existing vacancies',
                  'this section, and the amendments made by this section', '30 days after the date of enactment']:
            self.assertIn(v, s)

    def test_whistleblower_insertions_bounded(self):
        s = C['403_after_selected_2022']
        self.assertIn('educate agency employees, including employees of that Office of Inspector General--', s)
        self.assertIn('and Efficiency (including the Integrity Committee of that Council), the establishment', s)
        self.assertIn('shall not act as a legal representative, agent, or advocate', s)

    def test_information_notice_clock_starts_from_report(self):
        s = C['406_after_selected_2022']
        self.assertIn('by the date that is 30 days after the report is made', s)
        self.assertIn('insofar as is practicable and not in contravention', s)
        self.assertIn('in the judgment of an Inspector General', s)

    def test_zero_government_match_not_fabricated(self):
        self.assertEqual(C['406_h4B_Government']['matches'], 0)
        self.assertNotIn('Government', C['406_h4B_Government']['text'])
        self.assertIn('(C) Any other relevant congressional committee or subcommittee of jurisdiction.', C['406_after_selected_2022'])

    def test_406f_authority_and_constraints_unchanged(self):
        self.assertEqual(C['unchanged_406f'], between(C['406_after_selected_2022'], '(f) Additional Authority.--', '(g) Budgets.--'))
        for v in ['Guidelines.--', 'rescinded or suspended', 'is no longer satisfied', 'shall not be reviewable',
                  '180 days after November 25, 2002', 'reviewed periodically', 'other statutory authority',
                  'appointed under section 403', 'appointed under section 415']:
            self.assertIn(v, C['unchanged_406f'])

    def test_bill_initial_only_and_outer_transition_separate(self):
        s = T['bill317d1d2']; t = T['bill_outer3c']
        self.assertIn('shall be considered to be an office described in section 406(f)(3)', s)
        self.assertIn('exempt from an initial determination', s)
        self.assertIn('references to the establishment', s)
        self.assertTrue(t.startswith('(c) Transitional Provision.--'))
        for v in ['Notwithstanding sections 403 and 3345 through 3349', 'if the position',
                  'Executive Director', 'Prevention']:
            self.assertIn(v,t)
        self.assertNotIn('Transitional Provision', s)

    def test_committee_definition_complete(self):
        s = C['401_new_definition_payload']
        for v in ['Homeland Security and Governmental Affairs', 'Oversight and Reform',
                  'any other relevant congressional committee or subcommittee of jurisdiction']:
            self.assertIn(v,s)

    def test_mutated_operator_rejected(self):
        for old,new in [('by striking ``reasons', 'by striking ``purposes'),
                        ('after ``Houses of Congress', 'after ``Senate')]:
            bad = copy.deepcopy(X)
            r = next(r for r in bad if r['id']=='5202a1')
            original = normalize(r['text'])
            self.assertIn(old, original)
            r['text'] = original.replace(old,new)
            with self.assertRaises(ValueError):replay(bad)

    def test_mutated_baseline_rejected(self):
        bad = copy.deepcopy(X); r = next(r for r in bad if r['id']=='recod403')
        r['text'] = r['text'].replace('the reasons', 'the purposes')
        with self.assertRaises(ValueError):replay(bad)

    def test_mutated_notice_output_detected(self):
        bad = copy.deepcopy(X); r = next(r for r in bad if r['id']=='5261')
        r['text'] = r['text'].replace('30 days','60 days')
        self.assertNotEqual(replay(bad), C)


if __name__ == '__main__':
    unittest.main(verbosity=2)
