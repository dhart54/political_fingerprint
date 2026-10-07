import copy
import json
import re
import unittest

from backend.app.semantic_ir.shared_corpus import digest, sealed_digest
from backend.app.semantic_ir.adapters import build_persistence_proposal
from backend.app.semantic_ir.pipeline import run_editorial_pipeline
from backend.app.editorial_presentations.compiler import compile_public_issue_presentation, EditorialPresentationError
from scripts.prepare_immigration_shared_candidate import prepare, readable_candidates, reproducibility_proof
from scripts.validate_immigration_shared_candidate import DATA, validate, require_complete_research


class ImmigrationCandidateIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values = [json.loads((DATA / (name+'.json')).read_text(encoding='utf-8'))
                      for name in ['authoring', 'sources', 'universe_proposal', 'membership_review']]
        cls.products = prepare(cls.values[0], cls.values[1], ['F000477', 'M001184'])

    def test_state_border_fund_keeps_separate_detection_and_relocation_categories(self):
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:190')
        passage = next(c['passage'] for c in action['claim_source_map']
                       if c['passage'].startswith('(b) State Border Security Reinforcement Fund.'))
        detection = passage[passage.index('(C) Detection'):passage.index('(D) Relocation')]
        relocation = passage[passage.index('(D) Relocation'):passage.index('(3) Appropriation')]
        self.assertIn('unlawfully entered the United States and have committed a crime', detection)
        self.assertIn('from small population centers to other domestic locations', relocation)
        self.assertNotIn('committed a crime', relocation)
        qualification = next(q for q in action['limitations']
                             if q.startswith('The Senate 90005(b) State Border Security Reinforcement Fund'))
        for text in [action['meaning'], qualification]:
            own_detection = text[text.index('Senate 90005(b) purpose C:'):text.index('Senate 90005(b) purpose D:')]
            own_relocation = text[text.index('Senate 90005(b) purpose D:'):text.index('Senate 90005(b) paragraph 3:')]
            self.assertIn('unlawfully entered the United States and have committed a crime', own_detection)
            self.assertIn('transfer or referral of such aliens to the Department of Homeland Security as provided by law', own_detection)
            self.assertIn('unlawfully present in the United States from small population centers to other domestic locations', own_relocation)
            self.assertNotIn('committed a crime', own_relocation)

    def test_stonegarden_context_does_not_confer_additional_authority(self):
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:190')
        notice = next(s['text'] for s in self.values[1]['sources']
                      if s['source_id'] == 'hawaii:fema-fy2024-hsgp-nofo-program-eligibility')
        self.assertIn('do not receive any additional authority by participating in OPSG',
                      ' '.join(notice.split()))
        qualification = next(q for q in action['limitations']
                             if q.startswith('Selected Senate 90005(a) funding'))
        for text in [action['meaning'], qualification]:
            self.assertIn('use their inherent law enforcement authorities and receive no additional authority', text)
            self.assertIn('only FIFA paragraph (1)(B) and Olympics paragraph (1)(C)', text)
            self.assertIn('no exemption for Stonegarden paragraph (1)(D) or drone paragraph (1)(A)', text)

    def test_house_stonegarden_context_keeps_own_event_wording(self):
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:145')
        passage = next(c['passage'] for c in action['claim_source_map']
                       if c['passage'].startswith('SEC. 60005. STATE HOMELAND SECURITY GRANT PROGRAM.'))
        event = passage[passage.index('(3) $1,000,000,000'):passage.index('(4) $450,000,000')]
        literal_events = '2028 Olympic Games and 2028 Paralympic Games'
        self.assertIn(literal_events, event)
        qualification = next(q for q in action['limitations']
                             if q.startswith('Selected exact House floor State Homeland Security'))
        for text in [action['meaning'], qualification]:
            own = text[text.index('House floor 60005 purpose 3:'):text.index('House floor 60005 purpose 4:')]
            self.assertIn(literal_events, own)
            self.assertIn('until September 30, 2029', own)
            self.assertIn('security, planning, and other costs', own)

    def test_loan_exclusion_keeps_version_specific_spouse_requirements(self):
        for aid, label, section in [('house:119:1:145', 'House', '110019'),
                                    ('house:119:1:190', 'Senate', '70119')]:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
            passage = next(c['passage'] for c in action['claim_source_map']
                           if c['passage'].startswith('SEC. ' + section + '.'))
            own_source = passage[passage.index('``(C) Social security number requirement.'):
                                 passage.index('(b) Omission of Correct Social Security Number')]
            qualification = next(q for q in action['limitations']
                                 if q.startswith('Selected exact ' + label + ' ' + section + ' death/disability'))
            for text in [action['meaning'], qualification]:
                own = text[text.index(label + ' ' + section + ' identification and own marital rules:'):
                           text.index(label + ' ' + section + ' math-error amendment:')]
                with self.subTest(action=aid):
                    if label == 'House':
                        self.assertIn('if the taxpayer is married', own_source)
                        self.assertIn('if the taxpayer is married', own)
                        self.assertIn('social security number of such taxpayers\'s spouse', own)
                        self.assertIn('Rules similar to the rules of section 32(d)', own)
                    else:
                        self.assertNotIn('spouse', own_source)
                        self.assertNotIn('spouse', own)
                        self.assertNotIn('32(d)', own)
                        self.assertIn("taxpayer's social security number on the return", own)

    def test_account_and_pilot_keep_distinct_citizenship_and_identification_rules(self):
        for aid, label, account_section, pilot_section in [
                ('house:119:1:145', 'House', '110115', '110116'),
                ('house:119:1:190', 'Senate', '70204', '70204')]:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
            qualification = next(q for q in action['limitations']
                                 if q.startswith('Selected exact ' + label + ' account and separate pilot'))
            source = next(c['passage'] for c in action['claim_source_map']
                          if c['passage'].startswith('SEC. ' + pilot_section + '.'))
            pilot_source = source[source.index('``SEC. 6434.') : source.index('``SEC. 6659.')]
            citizenship = 'who is a United States citizen at birth' if label == 'House' else 'who is a United States citizen'
            self.assertIn(citizenship, pilot_source)
            if label == 'Senate':
                self.assertNotIn('citizen at birth', pilot_source)
                self.assertNotIn('spouse', pilot_source)
                self.assertIn('before the date of the election made under section 6434', pilot_source)
            for text in [action['meaning'], qualification]:
                with self.subTest(action=aid):
                    child_label = 'pilot birth window and citizenship at birth:' if label == 'House' else 'pilot birth window, no prior election and citizenship:'
                    child = text[text.index(label + ' ' + pilot_section + ' ' + child_label):]
                    child = child[:child.index(label + ' ' + pilot_section + ' ', 1)]
                    self.assertIn(citizenship, child)
                    identification_label = 'pilot return identification:' if label == 'House' else 'pilot child identification and election-date definition:'
                    identification = text[text.index(label + ' ' + pilot_section + ' ' + identification_label):]
                    identification = identification[:identification.index(label + ' ' + pilot_section + ' ', 1)]
                    account = text[text.index(label + ' ' + account_section + ' account establishment and instrument:'):]
                    account = account[:account.index(label + ' ' + account_section + ' ', 1)]
                    self.assertNotIn('citizen', account)
                    if label == 'House':
                        self.assertIn('if such individual is married', identification)
                        self.assertIn("social security number of such individual's spouse", identification)
                        self.assertNotIn('24(h)(7)', account)
                        self.assertIn('has not attained age 8 on the date of the establishment', account)
                    else:
                        self.assertNotIn('at birth', child)
                        self.assertNotIn('spouse', identification)
                        self.assertIn('includes with the election', identification)
                        self.assertIn('before the date of the election made under section 6434', identification)

    def test_account_pilot_preserve_own_election_and_applicability_dates(self):
        for aid, label in [('house:119:1:145', 'House'), ('house:119:1:190', 'Senate')]:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
            qualification = next(q for q in action['limitations']
                                 if q.startswith('Selected exact ' + label + ' account and separate pilot'))
            for text in [action['meaning'], qualification]:
                own = text[text.index('Selected exact ' + label + ' account and separate pilot'):]
                with self.subTest(action=aid):
                    if label == 'House':
                        self.assertIn('before January 1, 2026', own)
                        self.assertIn('House 110116 tax-year applicability: The amendments made by this section shall apply to taxable years beginning after December 31, 2024.', own)
                    else:
                        self.assertIn('12 months after the date of the enactment', own)
                        self.assertIn('Senate 70204 tax-year applicability: The amendments made by this section shall apply to taxable years beginning after December 31, 2025.', own)
                        self.assertIn('before the close of the calendar year in which the election', own)
                        self.assertIn('issued before the date on which an election', own)
                        self.assertIn('no prior election has been made under this section by such individual or any other individual', own)
                        self.assertIn('shall not begin before January 1, 2028', own)

    def test_tips_overtime_keep_own_spouse_number_and_married_return_rules(self):
        for aid, label, sections in [('house:119:1:145', 'House', ['110101', '110102']),
                                      ('house:119:1:190', 'Senate', ['70201', '70202'])]:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
            qualification = next(q for q in action['limitations']
                                 if q.startswith('Selected exact ' + label + ' tips and overtime'))
            for section in sections:
                source = next(c['passage'] for c in action['claim_source_map']
                              if c['passage'].startswith('SEC. ' + section + '.'))
                source_numbers = source[source.index('Social Security Number Required.--'):]
                source_numbers = source_numbers[:source_numbers.index('Regulations.--')]
                for text in [action['meaning'], qualification]:
                    with self.subTest(action=aid, section=section):
                        own = text[text.index(label + ' ' + section + ' identification'):]
                        own = own[:own.index(label + ' ' + section + ' ', 1)]
                        if label == 'House':
                            self.assertIn('if the individual is married', source_numbers)
                            self.assertIn('if the individual is married', own)
                            self.assertIn("social security number of such individual's spouse", own)
                            self.assertIn('Rules similar to the rules of section 32(d)', own)
                        else:
                            self.assertNotIn('social security number of such individual\'s spouse', source_numbers)
                            self.assertNotIn('spouse', own)
                            self.assertNotIn('32(d)', own)
                            married = text[text.index(label + ' ' + section + ' own married-individual joint-return rule:'):]
                            married = married[:married.index(label + ' ' + section + ' ', 1)]
                            self.assertIn('within the meaning of section 7703', married)
                            self.assertIn("only if the taxpayer and the taxpayer's spouse file a joint return", married)

    def test_tips_overtime_preserve_qualified_income_and_tax_year_limits(self):
        for aid, label, sections in [('house:119:1:145', 'House', ['110101', '110102']),
                                      ('house:119:1:190', 'Senate', ['70201', '70202'])]:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
            qualification = next(q for q in action['limitations']
                                 if q.startswith('Selected exact ' + label + ' tips and overtime'))
            for section in sections:
                source = next(c['passage'] for c in action['claim_source_map']
                              if c['passage'].startswith('SEC. ' + section + '.'))
                self.assertIn('taxable year beginning after December 31, 2028', source)
                for text in [action['meaning'], qualification]:
                    with self.subTest(action=aid, section=section):
                        own = text[text.index(label + ' ' + section + ' deduction'):]
                        own = own[:own.index(label + ' ' + section + ' tax-year applicability:')]
                        self.assertIn('taxable year beginning after December 31, 2028', own)
                        if section in ['110102', '70202']:
                            self.assertIn('required under section 7 of the Fair Labor Standards Act of 1938', own)
                            self.assertIn('that is in excess of the regular rate', own)
                        elif label == 'House':
                            self.assertIn('paid voluntarily without any consequence in the event of nonpayment', own)
                            self.assertIn('earned income', own)
                        else:
                            self.assertIn('shall not exceed $25,000', own)
                            self.assertIn('paid voluntarily without any consequence in the event of nonpayment', own)
                            self.assertIn('reduced (but not below zero) by $100 for each $1,000', own)

    def test_eitc_definition_keeps_role_scope_and_exact_version_mapping(self):
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:145')
        floor = next(c['passage'] for c in action['claim_source_map']
                     if c['locator'].startswith('Complete governing floor 112206 EITC'))
        engrossed = next(c['passage'] for c in action['claim_source_map']
                         if c['locator'].startswith('Served EH 112205 EITC comparison'))
        self.assertTrue(floor.startswith('SEC. 112206. EARNED INCOME TAX CREDIT REFORMS.'))
        self.assertTrue(engrossed.startswith('SEC. 112205. EARNED INCOME TAX CREDIT REFORMS.'))
        baseline = next(s['text'] for s in self.values[1]['sources']
                        if s['source_id'] == 'govinfo:26usc32-operative-2024-eitc-baseline')
        self.assertIn('Solely for purposes of subsections (c)(1)(E) and (c)(3)(D)', baseline)
        self.assertIn('on or before the due date for filing the return', baseline)
        qualification = next(q for q in action['limitations']
                             if q.startswith('Selected exact House floor 112206 EITC'))
        for text in [action['meaning'], qualification]:
            own = text[text.index('Selected exact House floor 112206 EITC'):]
            with self.subTest(surface='meaning' if text == action['meaning'] else 'qualification'):
                self.assertIn('before the return due date, not the original on-or-before boundary', own)
                self.assertIn('No change is invented for the unchanged solely-for role limitation', own)
                self.assertIn('No Senate EITC amendment', own)
                self.assertIn('the correction strikes that preceding floor section', own)

    def test_eitc_increase_keeps_separate_eligibility_payment_and_date_conditions(self):
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:145')
        qualification = next(q for q in action['limitations']
                             if q.startswith('Selected exact House floor 112206 EITC'))
        for text in [action['meaning'], qualification]:
            own = text[text.index('Selected exact House floor 112206 EITC'):]
            with self.subTest(surface='meaning' if text == action['meaning'] else 'qualification'):
                self.assertIn('whether or not such specified Purple Heart recipient is an eligible individual', own)
                self.assertIn('ceased to be payable by reason of section 223(e)(1)', own)
                self.assertIn('12-month period beginning with the first month', own)
                self.assertIn('shall not include any month if the specified Purple Heart recipient receives any benefit payment', own)
                self.assertIn('shall not apply with respect to the increase under paragraph (1)', own)
                self.assertIn('taxable years ending after the date of the enactment', own)
                self.assertIn('number-amendment taxable-year-beginning applicability: The amendment made by this section shall apply to taxable years beginning after December 31, 2024', own)

    def test_dod_border_funding_preserves_own_account_amount_and_chapter_reference(self):
        for aid, label, amount in [('house:119:1:145', 'House', '$5,000,000,000'),
                                   ('house:119:1:190', 'Senate', '$1,000,000,000')]:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
            source_id = 'congressional-record:2025-05-21-hr1-as-amended' if label == 'House' else 'govinfo:hr1eas'
            passage = next(c['passage'] for c in action['claim_source_map']
                           if c['source_id'] == source_id and c['passage'].startswith('SEC. 20011.'))
            self.assertIn(amount, passage)
            qualification = next(q for q in action['limitations']
                                 if q.startswith('Selected exact ' + label + ' 20011 DOD border-support'))
            for text in [action['meaning'], qualification]:
                own = text[text.index(label + ' 20011 DOD border-support appropriation:'):]
                own = own[:own.index('Senate 20011 incorporated chapter 15 section') if label == 'Senate' else own.index('Both exact provisions')]
                with self.subTest(action=aid):
                    self.assertIn('appropriated to the Secretary of Defense for fiscal year 2025', own)
                    self.assertIn('remain available until September 30, 2029', own)
                    self.assertIn(amount, own)
                    self.assertIn('temporary detention of migrants on Department of Defense installations', own)
                    if label == 'Senate':
                        self.assertIn('in accordance with chapter 15 of title 10', own)
                    else:
                        self.assertNotIn('chapter 15', own)

    def test_dod_chapter_restriction_retains_otherwise_law_and_preparedness_waiver(self):
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:190')
        qualification = next(q for q in action['limitations']
                             if q.startswith('Selected exact Senate 20011 DOD border-support'))
        for text in [action['meaning'], qualification]:
            with self.subTest(surface='meaning' if text == action['meaning'] else 'qualification'):
                restriction = text[text.index('Senate 20011 incorporated chapter 15 section 275:'):text.index('Senate 20011 incorporated chapter 15 section 276:')]
                self.assertIn('Army, Navy, Air Force, or Marine Corps', restriction)
                self.assertIn('search, seizure, arrest, or other similar activity', restriction)
                self.assertIn('unless participation in such activity by such member is otherwise authorized by law', restriction)
                waiver = text[text.index('Senate 20011 chapter 15 counterdrug short-term preparedness waiver:'):text.index('Senate 20011 chapter 15 counterdrug relationship and exceptions:')]
                self.assertIn('adversely affect the military preparedness of the United States in the short term', waiver)
                self.assertIn('importance of providing such support outweighs such short-term adverse effect', waiver)
                relationship = text[text.index('Senate 20011 chapter 15 counterdrug relationship and exceptions:'):text.index('Both exact provisions')]
                self.assertIn('subject to the provisions of section 275', relationship)
                self.assertIn('except as provided in subsection (e), section 276', relationship)

    def test_senate_orr_sponsor_funding_keeps_own_purposes_and_definitions(self):
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:190')
        passage = next(c['passage'] for c in action['claim_source_map']
                       if c['source_id'] == 'govinfo:hr1eas' and c['passage'].startswith('SEC. 87001.'))
        self.assertNotIn('TITLE IX', passage)
        qualification = next(q for q in action['limitations']
                             if q.startswith('Selected exact Senate 87001 ORR sponsor-vetting'))
        for text in [action['meaning'], qualification]:
            own = text[text.index('Selected exact Senate 87001 ORR sponsor-vetting'):]
            with self.subTest(surface='meaning' if text == action['meaning'] else 'qualification'):
                self.assertIn('appropriated to the Office of Refugee Resettlement for fiscal year 2025', own)
                self.assertIn('$300,000,000, to remain available until September 30, 2028', own)
                self.assertIn('may only be used for the Office of Refugee Resettlement', own)
                checks = own[own.index('Senate 87001 background-check purpose and required contents:'):own.index('Senate 87001 home-study purpose:')]
                self.assertIn('social security number or tax payer identification number', checks)
                self.assertIn('in-person or virtual interview with, and suitability study concerning', checks)
                self.assertIn('national criminal history check based on fingerprints', checks)
                self.assertIn('an individual or entity who applies for the custody', own)
                exam = own[own.index('Senate 87001 child examination and covering purpose:'):own.index('Senate 87001 data-system purpose:')]
                self.assertIn('while the child is in the care of the Office of Refugee Resettlement', exam)
                self.assertNotIn('12', exam)
                self.assertNotIn('Customs', exam)

    def test_senate_orr_funding_retains_placement_and_category_protections(self):
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:190')
        qualification = next(q for q in action['limitations']
                             if q.startswith('Selected exact Senate 87001 ORR sponsor-vetting'))
        for text in [action['meaning'], qualification]:
            own = text[text.index('Selected exact Senate 87001 ORR sponsor-vetting'):]
            with self.subTest(surface='meaning' if text == action['meaning'] else 'qualification'):
                self.assertIn('no parent or legal guardian in the United States is available to provide care and physical custody', own)
                self.assertIn('has no lawful immigration status in the United States', own)
                self.assertIn('has not attained 18 years of age', own)
                self.assertIn('least restrictive setting that is in the best interest of the child', own)
                self.assertIn('shall not be placed in a secure facility absent a determination', own)
                self.assertIn('shall be reviewed, at a minimum, on a monthly basis', own)
                self.assertIn('Before placing the child with an individual', own)
                self.assertIn('shall determine whether a home study is first necessary', own)
                self.assertIn('Subject to the requirements of subparagraph (B)', own)

    def test_coast_guard_versions_keep_own_asset_purposes_and_exceptions(self):
        for aid, label in [('house:119:1:145', 'House'), ('house:119:1:190', 'Senate')]:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
            qualification = next(q for q in action['limitations']
                                 if q.startswith('Selected exact ' + label + ' Coast Guard funding'))
            for text in [action['meaning'], qualification]:
                own = text[text.index('Selected exact ' + label + ' Coast Guard funding'):]
                with self.subTest(action=aid, surface='meaning' if text == action['meaning'] else 'qualification'):
                    self.assertIn('September 30, 2029', own)
                    if label == 'House':
                        opening = own[own.index('House 100001 own Commandant appropriation'):own.index('House 100001 asset line 1:')]
                        self.assertIn('appropriated to the Commandant of the Coast Guard', opening)
                        self.assertIn('acquisition, sustainment, improvement, and operation', opening)
                        self.assertIn('heading or agency mission does not establish every asset as Immigration spending', own)
                    else:
                        opening = own[own.index('Senate 40001 own Coast Guard appropriation'):own.index('Senate 40001 asset line 1:')]
                        self.assertIn('appropriated to the Coast Guard', opening)
                        self.assertIn('$24,593,500,000', opening)
                        self.assertIn('paragraphs (1) and (2) of section 1105(a)', opening)
                        self.assertIn('1131, 1132, 1133, and 1156', opening)
                        arctic = own[own.index('Senate 40001 asset line 6:'):own.index('Senate 40001 asset line 8:')]
                        self.assertIn('Arctic and Antarctic regions', arctic)
                        self.assertNotIn('maritime border', arctic)
                        shore = own[own.index('Senate 40001 asset line 10:'):own.index('Senate 40001 asset line 11:')]
                        self.assertIn('not more than $2,729,500,000', shore)
                        self.assertIn('homeporting of the existing polar icebreaker commissioned into service in 2025', shore)

    def test_house_coast_guard_reporting_drydock_and_foreign_yard_gates(self):
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:145')
        qualification = next(q for q in action['limitations']
                             if q.startswith('Selected exact House Coast Guard funding'))
        for text in [action['meaning'], qualification]:
            own = text[text.index('Selected exact House Coast Guard funding'):]
            with self.subTest(surface='meaning' if text == action['meaning'] else 'qualification'):
                gate = own[own.index('House 100001 own condition f:'):own.index('House 100001 own condition g:')]
                self.assertIn('this section may be obligated or expended during any fiscal year', gate)
                self.assertIn('sections 5102 and 5103 (excluding section 5103(e))', gate)
                self.assertIn('paragraphs (1) and (2) of subsection (a)', gate)
                self.assertIn('Public Law 117-263', gate)
                drydock = own[own.index('House 100001 own condition b:'):own.index('House 100001 own condition c:')]
                self.assertIn('Except as provided in paragraph (2)', drydock)
                self.assertIn('may, through September 30, 2030', drydock)
                self.assertIn('documented under chapter 121', drydock)
                self.assertIn('Offshore Patrol Cutter or a National Security Cutter', drydock)
                foreign = own[own.index('House 100001 own condition i:'):own.index('Original statutory context 1151:')]
                self.assertIn('paragraphs (4) through (7)', foreign)
                self.assertIn('no such funds shall be obligated until the President submits', foreign)
                self.assertIn('insufficient qualified United States shipyards', foreign)
                self.assertIn('prior to the issuance of such an exception', foreign)

    @staticmethod
    def seal_universe(universe):
        universe['universe_subject_sha256'] = digest(dict(subject=universe['subject'],
            cutoff=universe['cutoff'], candidate_records=universe['candidate_dispositions']))
        universe['proposal_sha256'] = sealed_digest(universe, 'proposal_sha256')

    def test_house_child_credit_preserves_literal_amount_window(self):
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:145')
        passage = next(c['passage'] for c in action['claim_source_map']
                       if c['passage'].startswith('SEC. 110004.'))
        window = re.search(r"taxable years beginning after (December 31, 2024), and before (December 31, 2028)", passage)
        self.assertIsNotNone(window, 'Exact governing nominal-amount window must remain available')
        for text in [action['meaning'], next(q for q in action['limitations'] if 'Existing 24(h)(4)(C)' in q)]:
            sentence = next(s for s in re.split(r'(?<=[.!?])\s+', text)
                            if '$2,500' in s)
            for bound in window.groups():
                self.assertIn(bound, sentence)
            self.assertNotRegex(sentence, re.compile(r'before\s+(?:2028|2029|January 1, 2029)', re.I))

    def test_house_senior_baseline_keeps_separate_person_age_branches(self):
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:145')
        source = next(s['text'] for s in self.values[1]['sources']
                      if s['source_id'] == 'govinfo:26usc63-operative-2024-senior-income-baseline')
        aged = source[source.index('(1) Additional amounts for the aged'):
                      source.index('(2) Additional amount for blind')]
        self.assertIn('(A) for himself if he has attained age 65 before the close of his taxable year', aged)
        self.assertIn('(B) for the spouse of the taxpayer if the spouse has attained age 65', aged)
        self.assertIn('an additional exemption is allowable to the taxpayer for such spouse under section 151(b)', aged)
        sentences = re.split(r'(?<=[.!?])\s+', action['meaning'])
        own = next((s for s in sentences if 'taxpayer amount' in s), '')
        spouse = next((s for s in sentences if 'spouse amount' in s), '')
        self.assertIn('taxpayer to have attained 65 before the tax year closes', own)
        self.assertIn('spouse to have attained 65 before that close', spouse)
        self.assertIn('exemption for that spouse to be allowable to the taxpayer under section 151(b)', spouse)
        self.assertNotIn('taxpayer to have attained 65', spouse)

    def test_child_credit_due_date_applies_to_both_issuance_categories(self):
        for aid, section in [('house:119:1:145', '110004'), ('house:119:1:190', '70104')]:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
            passage = next(c['passage'] for c in action['claim_source_map']
                           if c['passage'].startswith('SEC. ' + section + '.'))
            definition = passage[passage.index('(B) Social security number.'):
                                 passage.index('before the due date for such return.') + len('before the due date for such return.')]
            self.assertIn('to a citizen of the United States or pursuant to', definition)
            self.assertIn('and ``(ii) before the due date', definition)
            for text in [action['meaning'], next(q for q in action['limitations'] if 'Existing 24(h)(4)(C)' in q)]:
                self.assertRegex(text, r'In either case, (?:the SSN must have been issued|it must have been issued) before the due date for the return')
                self.assertNotIn('BRANCH AND BEFORE RETURN DUE DATE', text)

    def test_senate_ice_bonus_conditions_remain_separate_by_bonus(self):
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:190')
        passage = next(c['passage'] for c in action['claim_source_map']
                       if c['passage'].startswith('SEC. 100052.'))
        performance = passage[passage.index('(B) Performance bonuses.'):
                              passage.index('(C) Retention bonuses.')]
        retention = passage[passage.index('(C) Retention bonuses.'):
                            passage.index('(D) Signing bonuses.')]
        signing = passage[passage.index('(D) Signing bonuses.'):
                          passage.index('(E) Service agreement.')]
        self.assertIn('demonstrates exemplary service', performance)
        self.assertNotIn('date of the enactment', performance)
        self.assertIn('commits to 2 years of additional service', retention)
        self.assertNotIn('5 years', retention)
        self.assertIn('is hired on or after the date of the enactment', signing)
        self.assertIn('commits to 5 years of service', signing)
        self.assertIn('In providing a retention or signing bonus', passage)
        qualification = next(q for q in action['limitations']
                             if q.startswith('Senate 100052 uses one additional'))
        sentences = re.split(r'(?<=[.!?])\s+', qualification)
        performance_copy = next((s for s in sentences if 'performance bonus' in s), '')
        retention_copy = next((s for s in sentences if 'retention bonus' in s), '')
        signing_copy = next((s for s in sentences if 'signing bonus' in s), '')
        self.assertIn('demonstrates exemplary service', performance_copy)
        self.assertIn('commits to two additional years', retention_copy)
        for text in [performance_copy, retention_copy]:
            self.assertNotIn('hired on or after', text)
            self.assertNotIn('five years', text)
        self.assertIn('hired on or after enactment', signing_copy)
        self.assertIn('commits to five years', signing_copy)
        agreement = next((s for s in sentences if 'written service agreement' in s), '')
        self.assertIn('For retention and signing bonuses', agreement)
        self.assertNotIn('performance', agreement)

    def test_fletc_training_preserves_law_enforcement_actor_restrictions(self):
        for aid, section in [('house:119:1:145', '60002'), ('house:119:1:190', '100053')]:
            with self.subTest(action_id=aid):
                action = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
                passage = next(c['passage'] for c in action['claim_source_map']
                               if c['passage'].startswith('SEC. ' + section + '.'))
                self.assertIn('newly hired Federal law enforcement personnel employed by the Department of Homeland Security', passage)
                qualification = next(q for q in action['limitations'] if 'FLETC' in q)
                for text in [action['meaning'], qualification]:
                    training = next((s for s in re.split(r'(?<=[.!?])\s+', text)
                                     if 'newly hired' in s and ('FLETC' in s or 'training' in s.lower())), '')
                    self.assertRegex(training, r'newly hired (?:Federal law enforcement personnel employed by DHS|DHS federal[ -]law[ -]enforcement (?:personnel|training))')
                    if section == '100053':
                        self.assertIn('State and local law enforcement agencies operating in support of DHS', training)
                        self.assertIn('State and local law enforcement agencies operating in support of the Department of Homeland Security', passage)

    def test_senate_removal_funding_keeps_own_dhs_account(self):
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:190')
        source = next(s['text'] for s in self.values[1]['sources'] if s['source_id'] == 'govinfo:hr1eas')
        start = source.index('SEC. 100051.')
        passage = source[start:source.index('SEC. 100052.', start)]
        self.assertIn('appropriated to the Secretary of Homeland Security', passage)
        self.assertIn('$2,055,000,000', passage)
        for purpose in ['(9) Expedited removal of criminal aliens.', '(10) Removal of certain criminal aliens without further hearings.']:
            self.assertIn(purpose, passage)
        self.assertTrue(any(c['passage'] == passage for c in action['claim_source_map']))
        qualification = next(q for q in action['limitations'] if q.startswith('Senate 100051(9)/(10)'))
        for text in [action['meaning'], qualification]:
            sentence = next((s for s in re.split(r'(?<=[.!?])\s+', text)
                             if 'removal purposes remain' in s or s.startswith('Senate 100051(9)/(10)')), '')
            self.assertIn('100051', sentence)
            self.assertIn('$2,055,000,000', sentence)
            self.assertIn('DHS envelope', sentence)
            self.assertNotIn('ICE envelope', sentence)

    def test_reimbursement_transport_keeps_domestic_limit_and_person_category(self):
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:190')
        passage = next(c['passage'] for c in action['claim_source_map']
                       if c['passage'].startswith('SEC. 100055.'))
        transport = passage[passage.index('(6) Transporting'):passage.index('(7) Vehicle')]
        for phrase in ['aliens described in paragraph (1)', 'within the United States',
                       'apprehension, detention, and prosecution']:
            self.assertIn(phrase, transport)
        qualification = next(q for q in action['limitations'] if q.startswith('Senate 100054(2)/(3)'))
        for text in [action['meaning'], qualification]:
            sentence = next((s for s in re.split(r'(?<=[.!?])\s+', text)
                             if ('(6)' in s or 'paragraph 6' in s) and 'transport' in s.lower()), '')
            self.assertIn('within the United States', sentence)
            self.assertIn('aliens described in paragraph (1)', sentence)
            for purpose in ['apprehension', 'detention', 'prosecution']:
                self.assertIn(purpose, sentence)

    def test_dhs_assignment_and_return_keep_own_authority_predicates(self):
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:190')
        assignment = next(c['passage'] for c in action['claim_source_map']
                          if c['source_id'] == 'govinfo:8usc1103-2024-s2-enforcement')
        assignment = assignment[assignment.index('(10) In the event'):assignment.index('(11) The Attorney')]
        return_source = next(c['passage'] for c in action['claim_source_map']
                             if c['source_id'] == 'govinfo:8usc1225-2024-laken-context')
        return_source = return_source[return_source.index('(2) Inspection of other aliens'):]
        offshore = 'aliens arriving off the coast of the United States, or near a land border'
        entitlement = 'not clearly and beyond a doubt entitled to be admitted'
        self.assertIn(offshore, assignment)
        self.assertIn('conferred or imposed by this chapter or regulations issued thereunder', assignment)
        self.assertIn(entitlement, return_source)
        qualification = next(q for q in action['limitations'] if q.startswith('Remaining Senate 100051 purposes'))
        for surface, text in [('meaning', action['meaning']), ('qualification', qualification)]:
            sentences = re.split(r'(?<=[.!?])\s+', text)
            with self.subTest(surface=surface, authority='103(a)(10)'):
                own = next((s for s in sentences if s.startswith('Its (10) State/local')
                            or s.startswith('In captured 103(a)(10)')), '')
                for predicate in [offshore, 'Attorney General', 'urgent circumstances requiring an immediate Federal response',
                                  'conferred or imposed by this chapter or regulations issued thereunder',
                                  'with the consent of the head of the department, agency, or establishment']:
                    self.assertIn(predicate, own)
            with self.subTest(surface=surface, authority='235(b)(2)(C)'):
                own = next((s for s in sentences if s.startswith('The captured authority concerns an alien described in (A)')
                            or s.startswith('The captured 235(b)(2)(C) return authority')), '')
                for predicate in [entitlement, 'applicant for admission', 'examining immigration officer',
                                  'arriving on land', 'from a foreign territory contiguous to the United States']:
                    self.assertIn(predicate, own)

    def test_senate_child_ssn_is_required_in_both_claimant_alternatives(self):
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:190')
        passage = next(c['passage'] for c in action['claim_source_map']
                       if c['passage'].startswith('SEC. 70104.'))
        requirement = passage[passage.index('(A) In general.--No credit'):
                              passage.index('(B) Social security number.')]
        self.assertIn('at least 1 spouse), and', requirement)
        self.assertIn('``(ii) the social security number of such qualifying child', requirement)
        for text in [action['meaning'], next(q for q in action['limitations'] if 'Existing 24(h)(4)(C)' in q)]:
            self.assertRegex(text, r"qualifying child's defined SSN (?:in either case|is required in either case)")
            self.assertIn('on a joint return', text)
            self.assertIn('defined SSN of at least one spouse', text)

    def test_fixed_inventory_and_every_clerk_observation(self):
        result = validate(*self.values)
        self.assertEqual(result['inventory_count'], 676)

    def test_zero_ordinary_screenings_does_not_close_partial_package_review(self):
        reviews = self.values[2]['accounting']['partial_component_reviews']
        with self.assertRaisesRegex(ValueError, 'package component review remains incomplete: 2'):
            require_complete_research([], reviews)
        self.assertEqual(validate(*self.values)['unfinished_component_reviews'], 2)

    def test_component_completion_flag_does_not_erase_remaining_work(self):
        reviews = copy.deepcopy(self.values[2]['accounting']['partial_component_reviews'])
        for review in reviews:
            review['complete_immigration_component_review'] = True
        with self.assertRaisesRegex(ValueError, 'package component review remains incomplete'):
            require_complete_research([], reviews)

    def test_parole_funeral_exception_does_not_inherit_relative_location(self):
        for aid, section in [('house:119:1:145', '70004'), ('house:119:1:190', '100004')]:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
            passage = next(c['passage'] for c in action['claim_source_map']
                           if c['passage'].startswith('SEC. ' + section + '.'))
            dying = passage[passage.index('(4)'):passage.index('(5)')]
            funeral = passage[passage.index('(5)'):passage.index('(6)')]
            self.assertIn('close family member in the United States', dying)
            self.assertNotIn('close family member in the United States', funeral)
            self.assertIn('funeral', action['meaning'])
            self.assertNotRegex(action['meaning'], re.compile(
                r'funeral of a close family member\s+(?:in the US|in the United States)', re.I))

    def test_visa_refund_qualification_preserves_common_compliance_predicate(self):
        senate = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:190')
        passage = next(c['passage'] for c in senate['claim_source_map']
                       if c['passage'].startswith('SEC. 100007.'))
        refund = passage[passage.index('(b) Fee Reimbursement'):passage.index('SEC. 100008.')]
        self.assertIn('; and (2)(A)', refund)
        self.assertIn('; or (B)', refund)
        for aid in ['house:119:1:145', 'house:119:1:190']:
            with self.subTest(action_id=aid):
                action = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
                qualification = next(q for q in action['limitations']
                                     if q.startswith('Visa-integrity reimbursement'))
                self.assertNotRegex(qualification, re.compile(
                    r'Senate compliance\s+AND\s+no-extension-request.*\sOR\s+granted', re.I))
                self.assertIn('Senate requires post-admission compliance with all visa conditions in BOTH alternatives', qualification)
                self.assertIn('during the visa validity period', qualification)
                self.assertIn('"such period"', qualification)

    def test_hr1_distinct_versions_project_once_per_underlying_episode(self):
        core, mapping, projections, _, result = self.products
        ids = ['house:119:1:145', 'house:119:1:190']
        actions = {a['action_id']: a for a in core['actions']}
        self.assertEqual(actions[ids[0]]['legislative_stage'], 'final_passage')
        self.assertEqual(actions[ids[1]]['legislative_stage'], 'concurrence')
        self.assertNotEqual(actions[ids[0]]['action_core_sha256'], actions[ids[1]]['action_core_sha256'])
        episode = next(e for e in mapping['episodes'] if e['episode_id'] == 'episode:hr1:119')
        self.assertEqual(episode['action_ids'], ids)
        readable = readable_candidates(self.values[0], core, projections, result)
        for projection, member in zip(projections, readable['members']):
            rows = {a['action_id']: a for a in projection['actions']}
            for aid in ids:
                self.assertEqual(rows[aid]['official_status'], 'Nay')
                self.assertEqual(rows[aid]['action_core_sha256'], actions[aid]['action_core_sha256'])
            findings = [f for f in member['findings'] if set(ids).intersection(f['action_ids'])]
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]['action_ids'], ids)

    def test_hr1_senate_text_cannot_replace_house_passage_witness(self):
        author, capture, _, _ = copy.deepcopy(self.values)
        action = next(a for a in author['actions'] if a['action_id'] == 'house:119:1:145')
        action['source_id'] = 'govinfo:hr1eas'
        with self.assertRaisesRegex(ValueError, 'primary bill version differs'):
            prepare(author, capture, ['F000477', 'M001184'])

    def test_hr1_house_text_cannot_replace_senate_concurrence_witness(self):
        author, capture, _, _ = copy.deepcopy(self.values)
        action = next(a for a in author['actions'] if a['action_id'] == 'house:119:1:190')
        action['source_id'] = 'govinfo:hr1eh'
        with self.assertRaisesRegex(ValueError, 'primary bill version differs'):
            prepare(author, capture, ['F000477', 'M001184'])

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
        for defect in ['wrong_bill', 'wrong_print', 'future_date', 'later_same_day']:
            with self.subTest(defect=defect):
                author, capture, _, _ = copy.deepcopy(self.values)
                action = next(a for a in author['actions'] if a['action_id'] == 'house:119:2:108')
                sid = action['deemed_replacement_concurrence']['replacement_text_source_id']
                source = next(s for s in capture['sources'] if s['source_id'] == sid)
                old, new = {'wrong_bill': ('H.R. 7147', 'H.R. 7744'),
                            'wrong_print': ('119–21', '119–22'),
                            'future_date': ('March 27, 2026', 'March 28, 2026'),
                            'later_same_day': ('12:42 p.m.', '11:30 p.m.')}[defect]
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

    def test_missing_clerk_time_cannot_establish_same_day_replacement(self):
        author, capture, _, _ = copy.deepcopy(self.values)
        source = next(s for s in capture['sources'] if s['source_id'] == 'clerk:119:2:108')
        del source['metadata']['action-time']
        source['governed_bytes_sha256'] = sealed_digest(source, 'governed_bytes_sha256')
        with self.assertRaisesRegex(ValueError, 'exact dated Clerk time'):
            prepare(author, capture, ['F000477', 'M001184'])

    def test_annual_and_replacement_choices_share_one_episode_preserving_mixed_direction(self):
        core, mapping, projections, _, result = self.products
        episode = next(e for e in mapping['episodes'] if e['episode_id'] == 'episode:hr7147:119')
        self.assertEqual(episode['action_ids'], ['house:119:2:42', 'house:119:2:108'])
        readable = readable_candidates(self.values[0], core, projections, result)
        for mid, expected in [('F000477', ['Nay', 'Nay']), ('M001184', ['Nay', 'Yea'])]:
            member = next(m for m in readable['members'] if m['member_id'] == mid)
            findings = [f for f in member['findings'] if set(episode['action_ids']) & set(f['action_ids'])]
            self.assertEqual(len(findings), 1)
            self.assertEqual(set(findings[0]['action_ids']), set(episode['action_ids']))
            self.assertEqual([r['status'] for r in findings[0]['action_observations']], expected)
            self.assertIn('annual DHS', findings[0]['compact'])
            self.assertIn('continuing-resolution replacement', findings[0]['compact'])
        member = next(m for m in result.compiled_ir['members'] if m['member_id'] == 'M001184')
        nodes = [p for p in member['proposition_graph']['propositions']
                 if p['evidence_episode_ids'] == ['episode:hr7147:119']]
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]['direction'], 'mixed')

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
