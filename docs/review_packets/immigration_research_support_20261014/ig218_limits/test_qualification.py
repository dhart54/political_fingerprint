"""Source qualification only: no legal-application engine or candidate imports."""
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest
from source_tools import field, display, validate_passages

P = Path(__file__).resolve().parent
O = json.loads((P/'operative.json').read_text(encoding='utf8'))
X = json.loads((P/'passages.json').read_text(encoding='utf8'))['passages']
R = json.loads((P/'reused_callers.json').read_text(encoding='utf8'))
C = {r['id']: re.sub(r'\s+', ' ', r['text']) for r in R['sources']}


class Qualification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.streams = {}
        for n in ['code6329b.html', 'code3346.html']:
            raw = (P/n).read_bytes()
            cls.streams[n+':operative'] = field(raw, 'statute')
            cls.streams[n+':all_display'] = display(raw.decode())
        s = display((P/'code3345.html').read_text(encoding='utf8'))
        cls.streams['code3345.html:effective_note'] = s[s.index('Effective Date'):s.index('Executive Documents',s.index('Effective Date'))]
        cls.streams.update({'reused:'+r['id']:r['text'] for r in R['sources']})

    def test_raw_bytes_and_dated_identity(self):
        for r in json.loads((P/'captures.json').read_text()):
            raw = (P/r['file']).read_bytes()
            self.assertEqual(r['http_status'],200)
            self.assertEqual(len(raw),r['raw_bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(),r['raw_sha256'])
            self.assertIn('United States Code, 2024 Edition',display(raw.decode()))

    def test_all_25_literal_bindings(self):
        self.assertEqual(len(X),25)
        validate_passages(X,self.streams)

    def test_complete_operative_fields_not_selected_fragments(self):
        for n,length in [('code6329b.html',14223),('code3346.html',1243)]:
            self.assertEqual(O[n]['operative'],self.streams[n+':operative'])
            self.assertEqual(len(O[n]['operative']),length)
        self.assertTrue(O['code6329b.html']['operative'].endswith('subsection (b) of that section.'))
        self.assertTrue(O['code3346.html']['operative'].endswith('Senate first reconvenes.'))

    def test_four_disjunctive_threat_predicates(self):
        t = next(r['text'] for r in X if r['id']=='6329b_b2_predicates')
        for s in ['may— (i) pose a threat to the employee or others;',
                  '(ii) result in the destruction of evidence relevant to an investigation;',
                  '(iii) result in loss of or damage to Government property; or',
                  '(iv) otherwise jeopardize legitimate Government interests;']:
            self.assertIn(s,t)
        self.assertIn('(B) considered—',t)
        self.assertIn('(C) determined that none of the available options',t)

    def test_ig_exclusion_and_oig_employee_rule_distinct(self):
        s = O['code6329b.html']['operative']
        self.assertIn('(ii) the Inspector General of an agency;',s)
        self.assertIn('(4) Extensions for OIG employees.',s)
        self.assertIn('rather than the Chief Human Capital Officer',s)
        self.assertIn('at the request of the Inspector General',s)

    def test_work_calendar_business_day_units_and_certification(self):
        s = O['code6329b.html']['operative']
        for q in ['not more than 30 work days','may not exceed 90 work days',
                  'not later than 5 business days after granting each further extension',
                  'not more than 30 work days each', '30 calendar days after the completion',
                  'certify to the appropriate agency', 'not less than 70 work days']:
            self.assertIn(q,s)

    def test_6329b_implementation_anchors_not_assumed_regulation_dates(self):
        s = O['code6329b.html']['operative']
        for q in ['270 calendar days after the date of enactment',
                  '270 calendar days after the date on which the Director prescribes regulations',
                  '(i) Relation to Other Laws.', 'Notwithstanding subsection (a) of section 7421']:
            self.assertIn(q,s)
        self.assertIn('approved Dec. 23, 2016',O['code6329b.html']['all_display'])

    def test_3346_sickness_exception_210_and_pending_nomination(self):
        s = O['code3346.html']['operative']
        for q in ['Except in the case of a vacancy caused by sickness',
                  'as described under section 3345', '210 days beginning on the date the vacancy occurs',
                  'or (2) subject to subsection (b)', 'first or second nomination',
                  'from the date of such nomination for the period that the nomination is pending']:
            self.assertIn(q,s)
        self.assertNotIn('180 days',s)

    def test_first_and_second_nomination_branches(self):
        s = next(r['text']for r in X if r['id']=='3346_b')
        for q in ['rejected by the Senate, withdrawn, or returned to the President by the Senate',
                  '210 days after the date of such rejection, withdrawal, or return',
                  'Notwithstanding paragraph (1)', 'until the second nomination is confirmed; or',
                  '210 days after the second nomination is rejected, withdrawn, or returned']:
            self.assertIn(q,s)

    def test_sine_die_rule_limited_to_a_period(self):
        s = next(r['text']for r in X if r['id']=='3346_c')
        self.assertEqual(s,'(c) If a vacancy occurs during an adjournment of the Congress sine die, the 210-day period under subsection (a) shall begin on the date that the Senate first reconvenes.')

    def test_complete_151d_effective_date_exceptions(self):
        s = O['code3345.html']['effective_note']
        for q in ['30 days after the date of enactment', '[Oct. 21, 1998]',
                  'any office that becomes vacant after the effective date',
                  'for any office vacant on the effective date',
                  'as though such office first became vacant on the effective date',
                  'the next nomination of such person after such date shall be considered a first nomination']:
            self.assertIn(q,s)
        self.assertNotIn('Ex. Ord.',s)

    def test_403_threat_callers_and_report_are_not_whole_6329b(self):
        s = C['5202a1']
        self.assertEqual(s.count('any of clauses (i) through (iv) of section 6329b(b)(2)(A)'),2)
        self.assertEqual(s.count('section 6329b(b)(2)(A)'),3)
        for q in ['poses a threat described', 'including the report required under clause (ii)',
                  'not later than 15 days before', 'during the 30-day period preceding']:
            self.assertIn(q,s)

    def test_four_403h_3346_callers_with_other_eligibility_limits(self):
        s = C['5203a']
        self.assertEqual(s.count('time limitations of section 3346'),4)
        for q in ['not less than 90 days', 'not fewer than 90 of the 365 days',
                  'GS-15', 'only 1 Inspector General position', 'section 3345(a)']:
            self.assertIn(q,s)
        self.assertNotIn('210 days',s)

    def test_2022_applicability_separate_from_1998_and_bill(self):
        s = C['5203de']
        self.assertIn('3345 through 3349d',s)
        self.assertIn('other than with respect to section 3345(a)',s)
        self.assertIn('30 days after the date of enactment',s)
        self.assertIn('Existing vacancies',s)

    def test_outer_bill_notwithstanding_endpoint_and_initial_ag_separate(self):
        s = C['bill_outer3c']
        for q in ['(c) Transitional Provision', 'Notwithstanding sections 403 and 3345 through 3349',
                  'section 317(b)(1)', 'until such permanent Inspector General can be appointed',
                  'Prevention','if the position', 'Executive Director']:
            self.assertIn(q,s)
        self.assertNotIn('3349d',s)
        self.assertIn('exempt from an initial determination',C['bill317d1d2'])
        self.assertNotIn('Transitional Provision',C['bill317d1d2'])

    def test_mutation_and_truncation_rejected_without_mutating_inputs(self):
        original = copy.deepcopy(X)
        for source,old,new in [('code3346.html:operative','210 days','180 days'),
                               ('code6329b.html:operative','or others','and others')]:
            streams = dict(self.streams)
            self.assertIn(old,streams[source])
            streams[source] = streams[source].replace(old,new)
            with self.assertRaises(ValueError):validate_passages(X,streams)
        streams = dict(self.streams);streams['code3346.html:operative'] = streams['code3346.html:operative'][:-1]
        with self.assertRaises(ValueError):validate_passages(X,streams)
        self.assertEqual(X,original)
        validate_passages(X,self.streams)


if __name__=='__main__':unittest.main(verbosity=2)
