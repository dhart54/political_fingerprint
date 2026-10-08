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

    def test_taiwan_dual_resident_routes_keep_citizenship_and_tax_only_limits(self):
        action = getattr(self, 'taiwan_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:15')
        source = next(s['text'] for s in self.values[1]['sources'] if s['source_id'] == 'govinfo:hr33eh')
        start = source.index('``(3) Dual residents.')
        end = source.index('``(4) Rules of special application.', start)
        witness = source[start:end]
        for phrase in ['is not a United States citizen',
                       'described in subparagraph (B), (C), or (D)',
                       'would be a qualified resident of Taiwan but for paragraph (1)(B)',
                       'does not have a permanent home available to such individual in the United States',
                       'center of vital interests under subparagraph (C)(ii) cannot be determined',
                       'has a habitual abode in Taiwan and not the United States',
                       "for purposes of computing such individual's United States income tax liability"]:
            self.assertIn(phrase, witness)
        for phrase in ['NOT A USCITIZEN', 'ONE of three routes',
                       'The three routes are alternatives, not three cumulative requirements',
                       'AND habitual abode in Taiwan AND NOT the US',
                       'ONLY FOR COMPUTING', 'US INCOME-TAX LIABILITY',
                       'does not itself revoke or confer LPR status']:
            self.assertIn(phrase, action['meaning'])
        self.assertIn('noncitizen dual residents', action['compact_description'])
        self.assertIn('separate home, vital-interests or abode tests', action['compact_description'])
        self.assertIn('would not change immigration status', action['compact_description'])

    def test_taiwan_wage_relief_does_not_follow_automatically_from_dual_tax_residence(self):
        action = getattr(self, 'taiwan_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:15')
        source = next(s['text'] for s in self.values[1]['sources'] if s['source_id'] == 'govinfo:hr33eh')
        start = source.index('``(2) Qualified wages.')
        end = source.index('``(b) Income Connected', start)
        witness = source[start:end]
        for phrase in ['determined without regard to subsection (c)(3)(E)',
                       'regular component of a ship or aircraft operated in international traffic',
                       'any employer other than a United States person',
                       'not borne by a United States permanent establishment',
                       'income derived as a student or trainee',
                       'aggregate amount of gross receipts', 'do not exceed $30,000']:
            self.assertIn(phrase, witness)
        for phrase in ['ADDITIONAL recipient test',
                       'Therefore(c)(3)(E)\'s income-tax nonresidence does not by itself satisfy the first wage route',
                       'AND not be borne', 'student/trainee income',
                       'annual aggregate gross receipts NOT EXCEEDING $30,000',
                       'not a deduction or exclusion of the first $30,000 from unlimited receipts']:
            self.assertIn(phrase, action['meaning'])

    def test_taiwan_reciprocity_and_agreement_preserve_separate_conditions(self):
        action = getattr(self, 'taiwan_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:15')
        source = next(s['text'] for s in self.values[1]['sources'] if s['source_id'] == 'govinfo:hr33eh')
        for phrase in ['shall not apply to any period unless the Secretary has determined',
                       'that are reciprocal to the benefits',
                       'which may be separate dates for taxes withheld at the source and other taxes',
                       'at least 15 calendar days before commencing such negotiations',
                       'at least 60 days before the day on which the President enters into the Agreement',
                       'Not later than 270 days after the President enters into the Agreement',
                       'approval legislation and implementing legislation pursuant to section 207']:
            self.assertIn(phrase, source)
        for phrase in ['NONE of new894A applies for a period unless Treasury determines',
                       'dates MAY differ for source withholding and other taxes',
                       'at least15calendar days BEFORE negotiations',
                       'at least60days BEFORE entering the agreement',
                       'separate270-day AFTER-entry triggers',
                       'congressional approval/implementing legislation plus Taiwan approval/implementation confirmation',
                       'distinct14percent qualified scholarship/fellowship baseline']:
            self.assertIn(phrase, action['meaning'])
        self.assertIn('reciprocal, qualified Taiwan tax relief', action['compact_description'])
        claims = {c['source_id']: c['passage'] for c in action['claim_source_map']}
        self.assertEqual(claims['govinfo:hr33eh'], source)
        bank = {s['source_id']: s for s in self.values[1]['sources']}
        self.assertIn('a citizen or resident of the United States', claims['govinfo:26usc7701a30-2024-taiwan-us-person122'])
        self.assertEqual(claims['govinfo:26usc1441-2024-taiwan-withholding122'], bank['govinfo:26usc1441-2024-taiwan-withholding122']['text'])

    def test_research_security_witness_has_operating_body_not_table_of_contents(self):
        source = getattr(self, 'research_subtitle_source', None)
        if source is None:
            source = next(s for s in self.values[1]['sources']
                          if s['source_id'] == 'govinfo:pl117-167-subtitleD-research-security121')
        text = source['text']
        for section in range(10631, 10639):
            self.assertEqual(text.count('SEC. ' + str(section) + '.'), 1)
        self.assertIn('prohibit participation in any foreign talent recruitment program', text)
        self.assertIn('shall not apply retroactively', text)
        self.assertIn('preponderance of evidence', text)
        self.assertIn('the 5-year period ending on the date of the enactment of this Act', text)
        self.assertIn('does not target, stigmatize, or discriminate', text)
        self.assertIn('(ix) having a conflict of interest or conflict of commitment', text)
        self.assertIn('and (B) a program that is sponsored by', text)

    def test_hr1968_medical_transfer_keeps_chc_money_distinct_from_assessment_matching(self):
        action = getattr(self, 'hr1968_source_precision_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        bank = {s['source_id']: s for s in self.values[1]['sources']}
        source = bank['govinfo:18usc3014h1-h4-2024-health-financing-conditions']['text']
        for qualification in [
            'From amounts appropriated under section 10503(b)(1)',
            'equal to the amount transferred under subsection (d)',
            'not be less than $5,000,000 or more than $30,000,000',
            'shall remain available until expended',
        ]:
            self.assertIn(qualification, source)
        self.assertNotIn("assessment-funded medical transfer's", action['meaning'])
        self.assertNotIn("assessment-funded Domestic Trafficking Victims' Fund health-transfer source", action['meaning'])
        self.assertIn("medical transfer from CHC appropriations under PPACA 10503(b)(1) into the Domestic Trafficking Victims' Fund", action['meaning'])
        self.assertIn('health-transfer source in CHC appropriations under PPACA 10503(b)(1)', action['meaning'])
        self.assertIn("sized by matching the assessment transfer subject to the medical transfer's own annual $5 million-$30 million bounds", action['meaning'])
        self.assertTrue({'govinfo:18usc3014h1-h4-2024-health-financing-conditions',
                         'govinfo:42usc254b2b1-2024-chc-transfer-source',
                         'govinfo:hr1968eh-sec2101a-d-e-health-financing'} <= {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_transfer_reprogramming_keeps_authority_money_and_source_years(self):
        action = getattr(self, 'hr1968_transfer_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The materially referenced transfer and reprogramming controls', 1)[1]
        for qualification in [
            'a transfer made by, or transfer authority provided in, that Act or any other appropriation Act',
            'Both an enacted transfer and provided transfer authority remain within the exception',
            'corresponding-account/original-purpose/original-period constraints',
            'three covered-funding branches',
            'previous-appropriations funds for agencies funded by that Act',
            'Treasury-account funds derived from fee collections available to those agencies',
            'original printed fiscal years are 2015, 2017, 2020 and 2023 respectively, in both subsections',
            'does not erase those years, declare that every earlier period is now 2025',
            'All 70 separate application questions',
        ]:
            self.assertIn(qualification, text)
        self.assertTrue({'govinfo:pl113-235-divisionG-sec512-514-transfer-reprogramming',
                         'govinfo:pl115-31-divisionH-sec512-514-transfer-reprogramming',
                         'govinfo:pl116-94-divisionA-sec512-514-transfer-reprogramming',
                         'govinfo:pl117-328-divisionH-sec512-514-transfer-reprogramming'} <= {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_reprogramming_keeps_independent_triggers_thresholds_and_deadlines(self):
        action = getattr(self, 'hr1968_transfer_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The materially referenced transfer and reprogramming controls', 1)[1]
        for qualification in [
            'creates new programs',
            'eliminates a program, project or activity',
            'increases funds or personnel by any means for a project or activity whose funds have been denied or restricted',
            'relocates offices or employees',
            'reorganizes or renames offices',
            'reorganizes programs or activities',
            'contracts out or privatizes functions or activities presently performed by Federal employees',
            'All seven triggers remain',
            'separate subsection (b) monetary/percentage threshold is not imported into (a)',
            'in excess of $500,000 or 10 percent, whichever is less',
            'including construction projects',
            'augments existing programs/projects',
            'reduces by 10 percent funding for an existing program/project/activity or numbers of personnel by 10 percent',
            'arises from general personnel-reduction savings that would change existing programs/activities/projects as approved by Congress',
            'All three branches and the distinct personnel and funding reductions remain',
            'In excess of is not changed to at least',
            '15 days in advance of the reprogramming or an announcement of intent relating to it, whichever occurs earlier',
            'written notification to those Committees 10 days in advance of the reprogramming',
            'no new requirement to obtain committee approval is invented',
            'No actual consultation, announcement, notification, compliance or violation is inferred',
            'without a separate transfer/reprogramming policy stance or four additional legislative actions',
        ]:
            self.assertIn(qualification, text)

    def test_hr1968_publicity_keeps_two_money_branches_and_presentation_exceptions(self):
        action = getattr(self, 'hr1968_lobby_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The materially referenced publicity/lobbying funding conditions', 1)[1]
        for qualification in [
            'complete section 503(a)-(c)',
            'an appropriation contained in its Act/division or funds transferred pursuant to PPACA section 4002',
            'Both covered-money branches remain explicit',
            'normal and recognized executive-legislative relationships qualification',
            'except in presentation to Congress or the State/local legislature itself',
            'except in presentation to that executive branch itself',
            'Legislative-body and State/local-executive presentation exceptions remain separate',
            'not expanded here into every Federal regulatory communication or a universal ban on ordinary information',
        ]:
            self.assertIn(qualification, text)
        self.assertTrue({'govinfo:pl113-235-divisionG-sec503-publicity-lobbying',
                         'govinfo:pl115-31-divisionH-sec503-publicity-lobbying',
                         'govinfo:pl116-94-divisionA-sec503-publicity-lobbying',
                         'govinfo:pl117-328-divisionH-sec503-publicity-lobbying',
                         'govinfo:pl111-148-sec4002-10401b-pphf-transfer',
                         'govinfo:42usc300u11-2024-pphf-transfer-identity'} <= {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_lobbying_keeps_recipient_process_and_consumer_product_scope(self):
        action = getattr(self, 'hr1968_lobby_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The materially referenced publicity/lobbying funding conditions', 1)[1]
        for qualification in [
            'salary or expenses of a grant or contract recipient, or an agent acting for that recipient',
            'Both the recipient/agent and salary/expenses nexus remain',
            'an agency or officer of a State, local or tribal government',
            'policymaking and administrative processes within that government\'s executive branch',
            'tribal-government process qualification is not dropped',
            'proposed, pending or future Federal/State/local tax increases',
            'requirements or restrictions on legal consumer products, including sale or marketing',
            'including but not limited to advocacy or promotion of gun control',
            'inclusion within the qualified covered-funding prohibitions',
            'not only a gun-related clause, a ban on every person\'s policy discussion',
            'No actual communication, salary charge, recipient conduct or violation is found',
        ]:
            self.assertIn(qualification, text)

    def test_hr1968_named_lobbying_fund_keeps_original_amendment_and_current_identity_distinct(self):
        action = getattr(self, 'hr1968_lobby_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The materially referenced publicity/lobbying funding conditions', 1)[1]
        for qualification in [
            'Prevention and Public Health Fund',
            'HHS\'s Office of the Secretary',
            'increase funding over the fiscal year 2008 level',
            'programs authorized by the Public Health Service Act',
            'House and Senate Appropriations Committees',
            'subject to subsection (c)',
            'original same-Act 10401(b) substitutions',
            'distinct 2024 Code identity at 42 USC 300u-11',
            'not declared identical or applied to every earlier period/current grant',
            'not silently substituted for the separate health-transfer source in CHC appropriations under PPACA 10503(b)(1), whose transfer into the Domestic Trafficking Victims\' Fund is sized by matching the assessment transfer subject to the medical transfer\'s own annual $5 million-$30 million bounds, or for every PHS program',
            'All 70 separate application questions',
        ]:
            self.assertIn(qualification, text)

    def test_hr1968_health_availability_keeps_transfer_purpose_time_and_express_exception(self):
        action = getattr(self, 'hr1968_availability_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The materially referenced health-funding availability and disclosure conditions', 1)[1]
        for qualification in [
            'complete sections 501, 502 and 505 in each original requirements Act',
            'within its own division unless expressly provided otherwise',
            'transfer unexpended balances of prior appropriations to accounts corresponding to current appropriations',
            'not a new appropriation, a mandatory transfer or permission to move every balance to any account',
            'same purpose and the same periods of time for which they were originally appropriated',
            'does not reset the funds\' life',
            'available for obligation beyond the current fiscal year unless expressly so provided therein',
            'express-exception predicate remains part of the condition',
            'until-expended language and other express source availability provisions are retained',
            'not converted here into a categorical current-grant expiry or a blanket override',
        ]:
            self.assertIn(qualification, text)
        self.assertTrue({'govinfo:pl113-235-divisionG-sec501-502-505-availability-disclosure',
                         'govinfo:pl115-31-divisionH-sec501-502-505-availability-disclosure',
                         'govinfo:pl116-94-divisionA-sec501-502-505-availability-disclosure',
                         'govinfo:pl117-328-divisionH-sec501-502-505-availability-disclosure'} <= {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_health_disclosure_keeps_grantee_document_trigger_and_nongovernmental_measures(self):
        action = getattr(self, 'hr1968_availability_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The materially referenced health-funding availability and disclosure conditions', 1)[1]
        for qualification in [
            'all grantees receiving Federal funds included in the Act/division',
            'funded in whole or in part with Federal money',
            'statements, press releases, requests for proposals, bid solicitations and other such documents',
            'the percentage of total project/program costs financed with Federal money',
            'the dollar amount of Federal funds for the project/program',
            'both the percentage and dollar amount of total costs financed by non-governmental sources',
            'not silently changed to all non-Federal sources, every State/local contribution or an invented matching-fund requirement',
            'No actual allocation, recipient compliance, undisclosed financing, misuse or motive is inferred',
            'without assigning a separate balance-transfer/disclosure stance or four additional actions',
            'All 70 separate application questions',
        ]:
            self.assertIn(qualification, text)

    def test_hr1968_needle_conditions_keep_original_section_and_version_difference(self):
        action = getattr(self, 'hr1968_needle_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The materially referenced needle-program conditions', 1)[1]
        for qualification in [
            'PL113-235 division G section 521 (2015)',
            'PL115-31 division H section 520 (2017)',
            'PL116-94 division A section 527 (2020)',
            'PL117-328 division H section 526 (2023)',
            'funds appropriated in its own Act/division',
            'each complete needle-program clause is selected in its own operative Title V',
            'bars use of covered appropriated division funds to carry out any program of distributing',
            'sterile needles or syringes for hypodermic injection of any illegal drug',
            'does not print the later purchase-only wording or the later qualified other-program-elements proviso',
            'not retroactively inserted into this source object',
            '2015 rule is materially different and is recorded separately',
        ]:
            self.assertIn(qualification, text)
        self.assertTrue({'govinfo:pl113-235-divisionG-sec521-needle-program-conditions',
                         'govinfo:pl115-31-divisionH-sec520-needle-program-conditions',
                         'govinfo:pl116-94-divisionA-sec527-needle-program-conditions',
                         'govinfo:pl117-328-divisionH-sec526-needle-program-conditions'} <= {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_needle_conditions_keep_later_other_elements_proviso_complete(self):
        action = getattr(self, 'hr1968_needle_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The materially referenced needle-program conditions', 1)[1]
        for qualification in [
            'bar use of their covered appropriated division funds to purchase',
            'program elements other than making those purchases',
            'relevant State or local health department',
            'in consultation with the Centers for Disease Control and Prevention',
            'experiencing, or is at risk for, a significant increase in hepatitis infections or an HIV outbreak due to injection drug use',
            'operates in accordance with State and local law',
            'does not authorize the prohibited purchases',
            'one version repeals or overrides another incorporated reference',
            'full dated carry-forward application remains unfinished research',
            'without assigning a separate needle-policy stance, motive or four additional legislative actions',
            'All 70 separate application questions',
        ]:
            self.assertIn(qualification, text)

    def test_hr1968_healthcare_limits_keep_covered_funds_definition_and_complete_exceptions(self):
        action = getattr(self, 'hr1968_healthcare_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The materially referenced health-care funding conditions', 1)[1]
        for qualification in [
            "referring only to that division's provisions, except as expressly provided otherwise",
            'bars expenditure of both funds appropriated',
            'both funds appropriated in the relevant Act/division and funds in any trust fund to which funds are appropriated',
            "managed-care provider or organization's package of services under a contract or other arrangement",
            'both exceptions',
            'pregnancy resulting from rape or incest',
            'physical disorder, injury or illness',
            'a physician certifies would place the woman in danger of death unless an abortion is performed',
            'Neither exception is dropped, expanded to every health concern, limited to only one offense or presumed satisfied by an individual trafficking-victim label',
            'No actual expenditure, provider contract, individual service, coverage determination or violation is found',
        ]:
            self.assertIn(qualification, text)
        self.assertTrue({'govinfo:pl113-235-divisionG-sec3-506-507-healthcare-conditions',
                         'govinfo:pl115-31-divisionH-sec3-506-507-healthcare-conditions',
                         'govinfo:pl116-94-divisionA-sec3-506-507-healthcare-conditions',
                         'govinfo:pl117-328-divisionH-sec3-506-507-healthcare-conditions'} <= {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_healthcare_limits_keep_nonfederal_reservations_conditional_entity_and_version_bounds(self):
        action = getattr(self, 'hr1968_healthcare_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The materially referenced health-care funding conditions', 1)[1]
        for qualification in [
            "express exception for a State's or locality's Medicaid matching contribution",
            "managed-care providers' ability to offer abortion coverage",
            'State/local ability to contract separately with a provider',
            'conditions availability of funds',
            'to a Federal agency/program or State/local government',
            'subjects an institutional or individual health-care entity to discrimination',
            'does not provide, pay for, cover or refer for abortions',
            'All four listed refusal grounds remain',
            'physicians and other health professionals, hospitals, provider-sponsored organizations, HMOs, health-insurance plans',
            'other health-care facilities/organizations/plans',
            'does not merge the Acts into one unqualified version, create four independent member actions or decide all dated carry-forward applications',
            'without attributing a separate abortion position or intent from this package vote',
            'All 70 separate application questions',
        ]:
            self.assertIn(qualification, text)

    def test_hr1968_health_reference_chain_keeps_four_requirements_acts_and_dated_scopes(self):
        action = getattr(self, 'hr1968_health_chain_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The complete eleven-reference health-conditions chain', 1)[1]
        for qualification in [
            "continuing direction remains alongside each source's printed fiscal-year, period or amendment-appropriation scope",
            'FY2016 and FY2017 subject to PL113-235 requirements',
            'FY2018 or FY2019 amounts and PL115-31 requirements',
            'four subsequent selected application clauses name PL116-94 requirements',
            'FY2020 and October 1-November 30, 2020',
            'October 1 through December 11, 2020',
            'December 11-18, 2020',
            'division BB 301(d) retains FY2021-2023',
            'five later original application clauses point to PL117-328 requirements',
            'no additional fiscal-year restriction is inserted into these (d) clauses',
        ]:
            self.assertIn(qualification, text)
        self.assertTrue({'govinfo:pl114-10-sec221-health-conditions-reference',
                         'govinfo:pl115-123-sec50901-health-conditions-reference',
                         'govinfo:pl116-260-divisionBB-sec301-health-conditions-reference',
                         'govinfo:pl118-42-divisionG-sec101-health-conditions-reference'} <= {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_health_reference_chain_keeps_baseline_eh_and_unfinished_requirements(self):
        action = getattr(self, 'hr1968_health_chain_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The complete eleven-reference health-conditions chain', 1)[1]
        for qualification in [
            'historical replacement directive is not an additional current h4 authority',
            'printed touching/overlapping December 11 boundaries',
            'whole-section versus subsection reference forms are preserved',
            "earlier unqualified 'Consolidated Appropriations Act, 2024' name",
            'division-G clarification',
            'EH addition is distinct from the eleven-authority current-2024 baseline list',
            'four actual underlying requirements Acts, PL113-235, PL115-31, PL116-94 and PL117-328',
            'remain executable research',
            "without expanding that old governed source's extent",
            'all 70 application questions remain unchanged',
        ]:
            self.assertIn(qualification, text)

    def test_hr1968_medical_grants_keep_source_purpose_and_complete_authorities(self):
        action = getattr(self, 'hr1968_medical_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The medical-grant and child-service objects are separately bound', 1)[1]
        for qualification in [
            'amounts transferred to the Fund under paragraph (1)',
            'must use',
            'award grants that may be used for health care or medical items or services',
            'mandatory grant-award direction and permissive medical purpose',
            'medical-spending bar except as provided in (h)(2)',
            'sections 202, 203 and 204',
            '2000 section 107(b)(2) and (f)',
            'current 34 USC 20702/20703/20705',
            'current 34 USC 20304(b)',
            'not replaced with a universal common cohort or a new medical eligibility finding',
        ]:
            self.assertIn(qualification, text)
        self.assertIn('govinfo:18usc3014h2-h3-2024-medical-grants-child-minimum', {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_child_minimum_keeps_availability_literal_paragraph_and_cohort_boundaries(self):
        action = getattr(self, 'hr1968_medical_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The medical-grant and child-service objects are separately bound', 1)[1]
        for qualification in [
            'literally addresses amounts in the Fund used under paragraph (1)',
            'not less than $2 million',
            'if such amounts are available in the Fund during the relevant fiscal year',
            'under 214(b)',
            'not silently changed to paragraph (2)',
            "complete severe definition's sex and labor branches",
            'under-18-at-the-time-of-offense condition',
            'additional human-trafficking/child-pornography wording',
            'this increment does not resolve every interaction into one universal victim cohort',
            'automatically import the 20702 18-20 continuation cohort',
            'new separately scoped application question 70 about the medical branch',
            'Prior Q68 remains specifically the fund (e)(1)(B) programming reference and is unchanged',
        ]:
            self.assertIn(qualification, text)

    def test_hr1968_medical_duplicate_reference_question_keeps_four_witnesses_and_separate_scope(self):
        questions = getattr(self, 'medical_duplicate_questions', None)
        if questions is None:
            audit = json.loads((DATA.parents[2] / 'review_packets' / 'immigration_semantic_audit_in_progress.json').read_text(encoding='utf-8'))
            questions = [q for q in audit['open_legal_interactions'] if q['scope'].startswith('Question 70:')]
        self.assertEqual(1, len(questions))
        question = questions[0]
        self.assertIn('3014(h)(2)(B)', question['scope'])
        self.assertIn('distinct from frozen Q68 fund (e)(1)(B) scope', question['scope'])
        self.assertIn('before choosing a categorical medical-allocation target', question['recommendation'])
        expected = {'govinfo:18usc3014h2-h3-2024-medical-grants-child-minimum',
                    'govinfo:22usc7105f-2024-citizen-lpr-program-duplicate-notes',
                    'govinfo:pl106-386-sec107f-historical-adjustment-directive',
                    'govinfo:pl110-457-sec213a1-assistance-program-insertion'}
        self.assertEqual(expected, set(question['source_ids']))
        witnesses = question['primary_witnesses']
        self.assertEqual(4, len(witnesses))
        self.assertEqual(expected, {w['source_id'] for w in witnesses})
        bank = {s['source_id']: s for s in self.values[1]['sources']}
        for witness in witnesses:
            self.assertEqual(0, witness['start'])
            self.assertEqual(len(bank[witness['source_id']]['text']), witness['total'])
            self.assertEqual(witness['total'], witness['end'])
            self.assertEqual(bank[witness['source_id']]['text'], witness['passage'])
            self.assertEqual(digest(witness['passage']), witness['passage_sha256'])

    def test_hr1968_health_transfer_keeps_annual_bounds_and_separate_source(self):
        action = getattr(self, 'hr1968_health_financing_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The health-transfer financing context is separately bound', 1)[1]
        for qualification in [
            'annual amount equals the amount transferred under assessment subsection (d)',
            '$5 million annual floor and $30 million annual ceiling',
            'remains available until expended',
            'not a new floor or ceiling for every partial-year health extension',
            'authorized-and-appropriated Treasury funding introduction',
            'distinct from the separately printed National Health Service Corps (b)(2) and construction funding',
            'not silently repaired or summed into a new amount',
            '$1,050,410,959 for January 1-March 31, 2025',
            'whole 10503(b)(1) source for FY2015 and each subsequent fiscal year or period thereof',
        ]:
            self.assertIn(qualification, text)
        self.assertTrue({'govinfo:18usc3014h1-h4-2024-health-financing-conditions',
                         'govinfo:42usc254b2b1-2024-chc-transfer-source',
                         'govinfo:pl118-158-sec3101a-d-e-health-source-amendments'} <= {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_health_amendments_keep_exact_dates_and_condition_research_boundary(self):
        action = getattr(self, 'hr1968_health_financing_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The health-transfer financing context is separately bound', 1)[1]
        for qualification in [
            '$2,135,835,616 for April 1-September 30, 2025',
            "literal duplicate 'inserting and inserting' and trailing '; and'",
            'not the assessment charged to each offender and not an observed transfer, award or service',
            'eleven printed continuing-conditions authorities',
            'PL117-328 requirements for funds for programs under PHSA sections 330-340',
            'exact division B 2101(d) identity',
            'Code references-in-text note describes the 3101(d) authority as section 101(d)',
            'Both the editorial mismatch and actual operative witnesses are preserved',
            'not full fund-health review',
            'Q68 remains specifically about fund (e)',
            'All 69 prior application questions remain unchanged',
        ]:
            self.assertIn(qualification, text)
        self.assertIn('govinfo:hr1968eh-sec2101a-d-e-health-financing', {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_regional_centers_keep_prior_attributes_proposal_and_selection(self):
        action = getattr(self, 'hr1968_regional_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The separately incorporated regional-center consultation and evaluation context', 1)[1]
        for qualification in [
            'printed in-region and 20304-recipient qualification',
            'one year after November 4, 1992',
            'conditions the Administrator may require: one or more of five existing attributes',
            'literal proven-record reference to kinds of activities described in subsection (c)',
            'demonstrate ability to operate a center or provide training so others can do so',
            'Selection is competitive',
            'to the greatest extent possible and subject to available appropriations',
            'amounts made available in separate appropriation Acts',
        ]:
            self.assertIn(qualification, text)
        self.assertIn('govinfo:34usc20303-2024-complete-regional-center-context', {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_regional_centers_keep_reporting_shared_authorization_and_repeal(self):
        action = getattr(self, 'hr1968_regional_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The separately incorporated regional-center consultation and evaluation context', 1)[1]
        for qualification in [
            'compliance with the original proposal and modifications',
            'report annually on progress and needed/ongoing changes',
            'Upon funding discontinuation the Administrator must solicit new proposals under (c)',
            '2019 deletion of the former regional discontinuation-notice/reconsideration clause',
            'authorizes $40 million for each fiscal year 2022-2028',
            'shared authorization context for all three named authorities',
            'not $40 million newly appropriated by H.R. 1968',
            'not imported as the current amount or automatic program expiration',
            'All prior 69 application questions',
        ]:
            self.assertIn(qualification, text)
        self.assertIn('govinfo:34usc20306-2024-shared-center-authorization', {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_centers_keep_program_criteria_and_privacy_qualifications(self):
        action = getattr(self, 'hr1968_center_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split("The separately referenced local children's advocacy-center authority", 1)[1]
        for qualification in [
            'General center grants under (a) are mandatory authority duties; specialized direct-service grants under (b) are discretionary',
            'current 7102(11)(A), the sex-trafficking branch, with under-18-at-the-time-of-offense qualification',
            'No Senate-confirmation requirement',
            'reasonable notice and an opportunity for hearing',
            'law-authorized disclosure, service-recipient/representative consent or necessary-administration qualifications',
            'may under no circumstances contain actual names of individual service recipients',
            'permissive criteria the Administrator may require',
            'cases meeting designated referral criteria',
            '24 hours to the greatest extent practicable, but in no case later than 72 hours',
            'all eligible States',
            'an unspecified portion for State chapters',
        ]:
            self.assertIn(qualification, text)
        self.assertTrue({'govinfo:34usc20304-2024-complete-local-center-program',
                         'govinfo:34usc11183-2024-center-criteria-consistency',
                         'govinfo:34usc11186-2024-center-confidentiality-consistency'} <= {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_centers_keep_audit_periods_and_literal_reference_reservation(self):
        action = getattr(self, 'hr1968_center_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split("The separately referenced local children's advocacy-center authority", 1)[1]
        for qualification in [
            'within twelve months from the date when the final audit report is issued and any appeal has been completed',
            'ineligible during the following two fiscal years',
            'in the prior three fiscal years',
            'literally cites paragraph (2)',
            'audit exclusion is in paragraph (1)(C)',
            'same reference',
            'reserved separately as question 69',
            'no additional two-year nonprofit bar is invented',
        ]:
            self.assertIn(qualification, text)
        questions = getattr(self, 'center_reimbursement_questions', None)
        if questions is None:
            audit = json.loads((DATA.parents[2] / 'review_packets' / 'immigration_semantic_audit_in_progress.json').read_text(encoding='utf-8'))
            questions = [q for q in audit['open_legal_interactions'] if q['scope'].startswith('Question 69:')]
        self.assertEqual(1, len(questions))
        receipt = json.loads((DATA / 'hr1968_local_center_accountability_review.json').read_text(encoding='utf-8'))
        self.assertEqual(receipt['new_application_question'], questions[0])
        self.assertTrue({'govinfo:34usc20307-2024-center-accountability',
                         'govinfo:pl113-163-sec2b-original-center-accountability'} <= {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_centers_keep_nonprofit_purpose_disclosure_and_conference_scope(self):
        action = getattr(self, 'hr1968_center_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split("The separately referenced local children's advocacy-center authority", 1)[1]
        for qualification in [
            'requires both description under 501(c)(3) and exemption under 501(a)',
            'for the purpose of avoiding the tax described in complete 511(a)',
            'applies only to grantees using the prescribed rebuttable-presumption procedures',
            'public inspection of that disclosed information is upon request',
            'amounts authorized to be appropriated to DOJ under this center subchapter',
            'more than $20,000 in Department funds',
            'discretionary funds through a cooperative agreement under the printed Act',
            'prior written authorization',
            'with an all-cost estimate',
            'due by March 1 each year',
            'no actual submission is claimed',
        ]:
            self.assertIn(qualification, text)
        self.assertTrue({'govinfo:26usc501a-c3-2024-center-nonprofit-definition',
                         'govinfo:26usc511a-2024-center-offshore-tax-reference'} <= {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_icac_keeps_formula_need_pools_and_qualified_match(self):
        action = getattr(self, 'hr1968_icac_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split("The fund's separately named ICAC grant authority", 1)[1]
        self.assertIn('At least 75 percent of the total funds appropriated to carry out 21116', text)
        self.assertIn('minimum 0.5 percent is measured against funds available for formula grants', text)
        self.assertIn('at least 25 percent is measured against funds received under the remaining need-based branch only', text)
        self.assertIn('not total project costs, every formula grant or the whole appropriation', text)
        self.assertIn('disqualifies the task force from that need-based branch', text)
        self.assertIn('may waive all or part for good cause or financial hardship', text)
        self.assertIn('No combined net award is calculated', text)
        self.assertIn('govinfo:34usc21116-2024-icac-grants', {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_icac_keeps_duties_privacy_and_dated_authorities(self):
        action = getattr(self, 'hr1968_icac_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split("The fund's separately named ICAC grant authority", 1)[1]
        for qualification in [
            'award ceiling applies to any one entity other than a law-enforcement agency',
            'as permitted by available task-force resources',
            "qualified by consistency with the task force's State law",
            'existing Federal privacy laws',
            'prohibits using the system to search for or obtain information that does not involve Internet-facilitated child exploitation',
            'foreign or international agency support requires Attorney General approval',
            'separate Attorney General report to Congress is due within one year after October 13, 2008',
            'appropriated funds remaining available until expended',
            'distinct from an actual appropriation',
            'All prior 68 application questions',
        ]:
            self.assertIn(qualification, text)
        self.assertTrue({'govinfo:34usc21112-21115-2024-icac-program-context',
                         'govinfo:34usc21117-2024-icac-dated-authorization'} <= {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_citizen_program_keeps_status_victim_and_existing_eligibility(self):
        action = getattr(self, 'hr1968_citizen_program_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The separately printed citizen/permanent-resident trafficking-assistance program', 1)[1]
        self.assertIn('United States citizens or aliens lawfully admitted for permanent residence who are victims of severe trafficking', text)
        self.assertIn('such status not having changed', text)
        self.assertIn('referrals to programs for which victims are already eligible', text)
        self.assertIn('not a new entitlement or blanket eligibility for every Federal benefit', text)
        self.assertIn('Mandatory program/coordination duties remain distinct from discretionary grant awards', text)
        self.assertIn('Federal grant share cannot exceed 75 percent of the total costs of projects described in the grantee\'s application', text)
        self.assertIn('govinfo:8usc1101a20-2024-electricity-status',
                      {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_citizen_program_keeps_fund_boundary_and_duplicate_reference_reservation(self):
        action = getattr(self, 'hr1968_citizen_program_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The separately printed citizen/permanent-resident trafficking-assistance program', 1)[1]
        self.assertIn('without further appropriation', text)
        self.assertIn('in addition to other available amounts', text)
        self.assertIn('to award grants or enhance victims\' programming', text)
        self.assertIn('each fiscal year 2016-2027', text)
        self.assertIn('medical-items/services bar retains the express (h)(2) exception', text)
        self.assertIn('Code prints two enacted subsections (f)', text)
        self.assertIn('Omitted Code text is not automatically repealed law', text)
        self.assertIn('historical adjustment predicates are not imported as current rules', text)
        self.assertIn('Neither label is silently renumbered', text)
        self.assertIn('reserved separately as question 68', text)
        refs = {b['source_id'] for b in action['claim_source_map']}
        self.assertTrue({'govinfo:22usc7105f-2024-citizen-lpr-program-duplicate-notes',
                         'govinfo:18usc3014e-2024-programming-medical-boundary',
                         'govinfo:pl106-386-sec107f-historical-adjustment-directive',
                         'govinfo:pl110-457-sec213a1-assistance-program-insertion'} <= refs)
        questions = getattr(self, 'citizen_f_reference_questions', None)
        if questions is None:
            audit = json.loads((DATA.parents[2] / 'review_packets' / 'immigration_semantic_audit_in_progress.json').read_text(encoding='utf-8'))
            questions = [q for q in audit['open_legal_interactions'] if q['scope'].startswith('Question 68:')]
        self.assertEqual(1, len(questions))
        receipt = json.loads((DATA / 'hr1968_citizen_lpr_trafficking_program_review.json').read_text(encoding='utf-8'))
        self.assertEqual(receipt['new_application_question'], questions[0])

    def test_hr1968_state_grants_keep_current_jurisdiction_purposes_and_partners(self):
        action = getattr(self, 'hr1968_state_grant_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The current State/local trafficking law-enforcement grant program', 1)[1]
        self.assertIn('old condition is not a current recipient or offense limitation', text)
        self.assertIn('occur wholly or partly within the United States', text)
        self.assertIn('committed in connection with sex trafficking or a severe form of trafficking', text)
        self.assertIn('purchaser investigations/prosecutions prioritizing minor-victim cases', text)
        self.assertIn('as appropriate designation of at least one severe-trafficking prosecutor', text)
        self.assertIn('collaborates with social-service providers and relevant nongovernmental organizations', text)
        self.assertIn('does not itself require every victim to collaborate with police', text)
        refs = {b['source_id'] for b in action['claim_source_map']}
        self.assertTrue({'govinfo:34usc20705-2024-state-local-law-enforcement-grants',
                         'govinfo:pl109-164-sec204-historical-state-local-grants',
                         'govinfo:pl113-4-sec1242-state-local-grant-amendments'} <= refs)

    def test_hr1968_state_grants_keep_project_ceiling_savings_and_dated_objects(self):
        action = getattr(self, 'hr1968_state_grant_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The current State/local trafficking law-enforcement grant program', 1)[1]
        self.assertIn('Federal share cannot exceed 75 percent of the total costs of projects described in the application', text)
        self.assertIn('not a minimum, a percent of the entire $88 million', text)
        self.assertIn('Concurrent applications do not guarantee eligibility, awards, double funding', text)
        self.assertIn('$10 million for each fiscal year 2014-2021', text)
        self.assertIn('thirty months after March 7, 2013', text)
        self.assertIn('not new H.R. 1968 appropriations, observed grants or automatic termination', text)
        self.assertIn('explicit original note tracing redesignation to current 7102(11)', text)
        self.assertIn('fund-use/medical-transfer conditions and exact 2101(d)-(e)', text)
        self.assertIn('govinfo:22usc7102-2024-blue-campaign-definitions',
                      {b['source_id'] for b in action['claim_source_map']})

    def test_hr1968_child_grants_keep_current_cohort_access_and_expertise(self):
        action = getattr(self, 'hr1968_child_grant_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The distinct current child-trafficking deterrence block-grant program', 1)[1]
        self.assertIn('current child definition is under 18', text)
        self.assertIn('including sex-trafficking and forced-labor branches', text)
        self.assertIn('not only sex trafficking, every child, a citizenship/LPR condition', text)
        self.assertIn('access to funded shelter or services must not require law-enforcement collaboration', text)
        self.assertIn('substantial relevant service experience or specialized staff', text)
        self.assertIn('alternatives, not two cumulative qualifications', text)
        refs = {b['source_id'] for b in action['claim_source_map']}
        self.assertTrue({'govinfo:34usc20703-2024-child-deterrence-block-grants',
                         'govinfo:pl109-164-sec203-historical-juvenile-pilot',
                         'govinfo:22usc7102-2024-blue-campaign-definitions'} <= refs)

    def test_hr1968_child_grants_keep_salary_court_and_preference_conditions(self):
        action = getattr(self, 'hr1968_child_grant_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The distinct current child-trafficking deterrence block-grant program', 1)[1]
        self.assertIn('percentage of on-duty time devoted to child-trafficking cases', text)
        self.assertIn('percentage of total worked hours devoted to those cases', text)
        self.assertIn('regular mandatory victim appearances', text)
        self.assertIn('relevant nonviolent charges following successful compliance', text)
        self.assertIn('whether charged or not', text)
        self.assertIn('alternative routes to preference, not both required', text)
        self.assertIn('expires three years after award and may renew no more than twice', text)
        self.assertIn('each renewal lasting no more than two years', text)

    def test_hr1968_child_grants_keep_expended_cap_share_and_reference_boundaries(self):
        action = getattr(self, 'hr1968_child_grant_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The distinct current child-trafficking deterrence block-grant program', 1)[1]
        self.assertIn('five percent of total amount expended', text)
        self.assertIn('program-cost share is 70/60/50 percent', text)
        self.assertIn('each fiscal year 2016-2020', text)
        self.assertIn('not a new H.R. 1968 $7 million appropriation', text)
        self.assertIn('explicit original note tracing reclassification to 34 USC 20301 et seq.', text)
        self.assertIn('grant criteria may require listed elements', text)
        self.assertIn('excluding a member convicted or accused of child abuse', text)
        center_limits = [q for q in action['limitations']
                         if q.startswith('Printed child-advocacy reference and explicit reclassification note')]
        self.assertEqual(1, len(center_limits))
        self.assertIn('Further center/fund-use/medical-transfer authorities remain ordinary research', center_limits[0])
        refs = {b['source_id'] for b in action['claim_source_map']}
        self.assertIn('govinfo:34usc20302-20304-material-center-context', refs)

    def test_hr1968_special_assessment_keeps_exact_date_amount_and_conviction_cohort(self):
        action = getattr(self, 'hr1968_assessment_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The selected additional-special-assessment amendment', 1)[1]
        self.assertIn('division C section 3103', text)
        self.assertIn('replace March 14, 2025 with September 30, 2025', text)
        self.assertIn('retain the May 29, 2015 starting reference', text)
        self.assertIn('not the $5,000 amount, the separate section 3013 assessment', text)
        self.assertIn('non-indigent person or entity convicted under one of five named branches', text)
        self.assertIn('not every person with an immigration violation', text)
        self.assertIn('spouse/parent/son/daughter relationship at the time of action and no other individual', text)
        self.assertIn('printed referent is not silently reassigned', text)

    def test_hr1968_special_assessment_keeps_payment_priority_and_fine_restitution_duration(self):
        action = getattr(self, 'hr1968_assessment_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The selected additional-special-assessment amendment', 1)[1]
        self.assertIn('not payable until all outstanding court-ordered fines, restitution and other victim-compensation obligations', text)
        self.assertIn('civil remedies authorized by section 3613 where appropriate', text)
        self.assertIn('pay-until-full language remains subject to complete 3613(b)', text)
        self.assertIn('Fine liability terminates at the later of twenty years from entry of judgment or twenty years after release from imprisonment', text)
        self.assertIn('it also terminates upon the individual\'s death', text)
        self.assertIn('Restitution liability terminates at the later of twenty years from entry of judgment or twenty years after release from imprisonment', text)
        self.assertIn('the individual\'s estate is responsible for any unpaid restitution balance', text)
        self.assertIn('the subsection (c) lien continues until the estate receives written release of that liability', text)
        self.assertIn('No universal perpetual assessment, September-30 discharge', text)
        self.assertIn('qualified religious-denomination/nonprofit volunteer-minister exception', text)

    def test_hr1968_special_assessment_keeps_collected_amount_and_explicit_fee_reference_mapping(self):
        action = getattr(self, 'hr1968_assessment_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The selected additional-special-assessment amendment', 1)[1]
        self.assertIn('amount equal to assessments collected, available until expended', text)
        self.assertIn('not every nominal charge as an observed receipt or a new fixed appropriation', text)
        self.assertIn('explicit original reference note identifies the redesignation to current 3718(d)', text)
        self.assertIn('qualifying contract under (a) or (b) may pay a recovery fee from recovered amounts', text)
        self.assertIn('appropriation-effectiveness limit has its express fee-contract exception', text)
        self.assertIn('excludes Internal Revenue Code debts', text)
        self.assertIn('No actual contract/fee or unconditional zero-fee/no-exception net-deposit calculation', text)
        self.assertIn('other use/health-transfer clauses and their material authorities', text)

    def test_hr1968_minor_grants_keep_current_recipient_and_block_grant_qualifications(self):
        action = getattr(self, 'hr1968_minor_grant_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The current domestic minor-victim block-grant program', 1)[1]
        self.assertIn('person ages 18-20 who met the under-18 definition before turning 18 and was receiving shelter or services as a minor victim', text)
        self.assertIn('not every 18-20-year-old', text)
        self.assertIn('four eligible State/local entities in different United States regions', text)
        self.assertIn('at least one in a State population below five million', text)
        self.assertIn('At least 67 percent of each block grant', text)
        self.assertIn('four care-use clauses', text)
        self.assertIn('each victim must receive all four services', text)
        self.assertIn('preceding-year recipients eligible for renewal receive mandatory priority', text)
        self.assertIn('experience or specialized staff, together with a sustainability plan', text)
        self.assertIn('excludes a person charged with purchasing sex with a minor', text)

    def test_hr1968_minor_grants_keep_restoration_pilot_and_matching_distinctions(self):
        action = getattr(self, 'hr1968_minor_grant_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The current domestic minor-victim block-grant program', 1)[1]
        self.assertIn('original 2005 section 202 HHS program', text)
        self.assertIn('historical, not imported as current recipient or matching rules', text)
        self.assertIn('2018 restoration of the March 6, 2017 text', text)
        self.assertIn('repeal of the sunset provision', text)
        self.assertIn('not silently redirected to (i)', text)
        self.assertIn('Subsection (g) contains matching requirements while subsection (i) contains authorization of appropriations', text)
        self.assertIn('pilot is not confined to the block grant\'s defined minor sex-trafficking-victim cohort', text)
        self.assertIn('three-percent administration cap on the total amount appropriated', text)
        self.assertIn('15/25/40/50 percent of the grant', text)
        self.assertIn('not the historical 75-percent Federal project-cost ceiling', text)
        self.assertIn('dated provisions, not new current appropriations', text)
        self.assertIn('other current 2005/2013 trafficking programs', text.lower())

    def test_hr1968_minor_recipient_predicate_keeps_advertising_and_age_proof_boundaries(self):
        action = getattr(self, 'hr1968_minor_grant_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The current domestic minor-victim block-grant program', 1)[1]
        self.assertIn('reckless-disregard route excludes a paragraph (1) advertising violation', text)
        self.assertIn('under-18 commercial-sex branch are alternatives', text)
        self.assertIn('person will be caused to engage in a commercial sex act', text)
        self.assertIn('limited to the stated (a)(1) prosecution and listed acts', text)
        self.assertIn('removes proof of under-age knowledge/recklessness, not every offense element', text)
        self.assertIn('No actual offense, State-law equivalence, conviction, sentence', text)
        refs = {b['source_id'] for b in action['claim_source_map']}
        self.assertIn('govinfo:18usc1591-2024-grant-recipient-predicate', refs)
        self.assertIn('govinfo:34usc20702-2024-minor-victim-block-grants', refs)

    def test_hr1968_trafficking_grants_keep_alternative_authorities_and_scoped_percentages(self):
        action = getattr(self, 'hr1968_trafficking_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The selected trafficking victim-services funding', 1)[1]
        self.assertIn('three alternative named authorities', text)
        self.assertIn("not paragraph (3)'s $88 million", text)
        self.assertIn('not automatically to the entire $88 million line covering alternative authorities', text)
        self.assertIn('three percent for research/evaluation/statistics', text)
        self.assertIn('five percent for training/technical assistance', text)
        self.assertIn('one percent for management/administration', text)
        self.assertIn('remain separate from CJS section 212', text)
        self.assertIn('75 percent of total project cost', text)
        self.assertIn('consistent with grant requirements and approved project scope', text)
        self.assertIn('other two named authorities still require current program mapping', text)

    def test_hr1968_trafficking_priority_keeps_nonexclusive_examples_and_narrow_attestations(self):
        action = getattr(self, 'hr1968_trafficking_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The selected trafficking victim-services funding', 1)[1]
        self.assertIn('examples are nonexclusive', text)
        self.assertIn('age and circumstance requirements are joined within the first example', text)
        self.assertIn('three examples are alternatives', text)
        self.assertIn('priority applies only when selecting grants available solely for law-enforcement operations or task forces', text)
        self.assertIn('Attorney General may prioritize', text)
        self.assertIn('offenses directly resulting from victimization', text)
        self.assertIn('not condition access to shelter or restorative services on collaboration with law enforcement', text)
        self.assertIn("resources extending beyond the grant's duration", text)
        self.assertIn('combined attestation conditions for that discretionary priority', text)
        self.assertIn('not silently narrowed by importing separate individual-assistance/certification provisions', text)

    def test_hr1968_marshals_budget_keeps_override_caps_and_two_designations(self):
        action = getattr(self, 'hr1968_transport_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The selected Marshals mechanism', 1)[1]
        self.assertIn('replaces the account level with $2,236,000,000 rather than adding', text)
        self.assertIn('total is not a separately allocated Immigration or JPATS transportation budget', text)
        self.assertIn('$250 million emergency designation is within its printed total', text)
        self.assertIn('both a congressional account-specific emergency designation and a subsequent presidential designation', text)
        self.assertIn('not more than $20 million within its funds', text)
        self.assertIn('a cap, not a minimum, an additional appropriation', text)
        self.assertIn('allowable costs or other conditions specified in the contract for per-diem rates', text)
        self.assertIn('not a universal actual-cost-only rule', text)

    def test_hr1968_transport_keeps_current_fund_lease_and_conviction_security_predicates(self):
        action = getattr(self, 'hr1968_transport_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The selected Marshals mechanism', 1)[1]
        self.assertIn('printed illegal/criminal-alien categories in Marshals custody', text)
        self.assertIn('reimbursement or advance-credit rates recovering operating expense including leave and depreciation', text)
        self.assertIn('credit of aircraft-disposal proceeds', text)
        self.assertIn('operating-equipment leases not exceeding ten years', text)
        self.assertIn('older five-year predecessor is not substituted', text)
        self.assertIn('not a universal duration limit for the separate reasonable-duration detention-contract authority', text)
        self.assertIn('prisoner pursuant to a State/Federal conviction and classified maximum or high security', text)
        self.assertIn('appropriately secure BOP-certified prison or other facility', text)
        self.assertIn('not every civil immigration detainee, all DHS transport', text)

    def test_hr1968_scaap_keeps_separate_amount_cost_cap_and_conviction_plus_status(self):
        action = getattr(self, 'hr1968_scaap_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The selected State Criminal Alien Assistance Program funding', 1)[1]
        self.assertIn('does not replace SCAAP paragraph (2)\'s $234 million', text)
        self.assertIn('no jurisdiction request compensation above its actual cost', text)
        self.assertIn('chief executive\'s written request', text)
        self.assertIn('contractual compensation arrangement or Federal custody/incarceration alternative', text)
        self.assertIn('a felony conviction or two or more misdemeanor convictions, together with one of the three stated status routes', text)
        self.assertIn('when taken into that custody', text)
        self.assertIn('average State incarceration-cost basis as determined by the Attorney General', text)
        self.assertIn('fiscal-year 2006-2011 authorization amounts', text)
        self.assertIn('correctional-purpose-only use', text)

    def test_hr1968_scaap_keeps_distinct_two_percent_mechanisms_and_no_guaranteed_award(self):
        action = getattr(self, 'hr1968_scaap_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The selected State Criminal Alien Assistance Program funding', 1)[1]
        self.assertIn('two distinct up-to-two-percent mechanisms at the Attorney General\'s discretion', text)
        self.assertIn('training/technical assistance may use up to two percent', text)
        self.assertIn('transferred and merged into NIJ/BJS research, evaluation or statistics', text)
        self.assertIn('except funds specifically appropriated for those NIJ/BJS purposes', text)
        self.assertIn('shall-transfer direction remains subject to the stated discretion and up-to cap', text)
        self.assertIn('exclusion does not become an exclusion for SCAAP paragraph (2)', text)
        self.assertIn('not an automatic four-percent deduction or a computed guaranteed net SCAAP award', text)
        self.assertIn('no unlimited transfer or every-expenditure notice claim', text)

    def test_hr1968_eoir_funding_keeps_included_fees_minimum_and_comparable_availability(self):
        action = getattr(self, 'hr1968_eoir_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The selected DOJ court-funding mechanism', 1)[1]
        self.assertIn('$4 million is included in, not added to, the $844 million', text)
        self.assertIn('Not less than $28 million', text)
        self.assertIn('not a ceiling or an individual right to a lawyer', text)
        self.assertIn('not more than $50 million of the total', text)
        self.assertIn('printed availability through September 30, 2028', text)
        self.assertIn('section 1103 carries comparable multi-year/no-year availability', text)
        self.assertIn('no silently invented new fixed courtroom endpoint', text)
        self.assertIn('No actual fee collection, transfer, reprogramming', text)

    def test_hr1968_eoir_transfer_and_reprogramming_keep_caps_lower_threshold_and_advance_notice(self):
        action = getattr(self, 'hr1968_eoir_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The selected DOJ court-funding mechanism', 1)[1]
        self.assertIn('not more than five percent', text)
        self.assertIn('increased by more than ten percent by such transfers except as otherwise specifically provided', text)
        self.assertIn('exclusions do not become an EOIR exemption', text)
        self.assertIn('all eight listed kinds of change', text)
        self.assertIn('more than $500,000 or ten percent, whichever is less', text)
        self.assertIn('separate funding/personnel reduction trigger is ten percent', text)
        self.assertIn('Both Appropriations Committees must be notified fifteen days in advance', text)
        self.assertIn('use of previous-year deobligated balances', text)
        self.assertIn('Unreviewed explanatory-statement allocations are not imported', text)

    def test_hr1968_blue_campaign_keeps_minimum_before_obligation_and_reserved_fiscal_year(self):
        action = getattr(self, 'hr1968_blue_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The retained Blue Campaign provision', 1)[1]
        self.assertIn('not less than $5 million', text)
        self.assertIn('amount is a minimum, not a $5 million ceiling or an observed transfer/spend', text)
        self.assertIn('both House and Senate Appropriations Committees before obligation', text)
        self.assertIn('printed fiscal year 2024', text)
        self.assertIn('combined fiscal-year application is reserved', text)
        self.assertIn('rather than replacing every 2024 reference with 2025', text)
        audit = json.loads((DATA.parents[2] / 'review_packets/immigration_semantic_audit_in_progress.json').read_text(encoding='utf-8'))
        frozen = json.loads((DATA / 'hr1968_blue_campaign_scope_review.json').read_text(encoding='utf-8'))['new_application_question']
        questions = [q for q in audit['open_legal_interactions']
                     if 'separate from frozen incorporated-program question63' in q['scope']]
        self.assertEqual(questions, [frozen])

    def test_hr1968_blue_campaign_keeps_broader_program_and_distinct_trafficking_definitions(self):
        action = getattr(self, 'hr1968_blue_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The retained Blue Campaign provision', 1)[1]
        self.assertIn('broader scope than Immigration alone', text)
        self.assertIn('no border crossing, foreign citizenship, lack of lawful status or immigration benefit is required', text)
        self.assertIn('redesignation to (11) and (12)', text)
        self.assertIn('Complete severe-trafficking and sex-trafficking definitions remain distinct', text)
        self.assertIn('commercial sex act induced by force, fraud or coercion, or a person induced to perform it under eighteen', text)
        self.assertIn('labor/services route requires the stated force/fraud/coercion', text)
        self.assertIn('without importing every severe-form qualifier into it', text)
        self.assertIn('no individual conduct, criminal liability or victim classification is adjudicated', text)
        self.assertIn('do not establish new H.R. 1968 transfer events', text)

    def test_hr1968_uscis_vehicle_permission_keeps_replacement_area_and_discretion(self):
        action = getattr(self, 'hr1968_operational_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The retained USCIS operational provisions', 1)[1]
        self.assertIn('up to five vehicles, for replacement only', text)
        self.assertIn('areas where the General Services Administration does not provide vehicles for lease', text)
        self.assertIn('permits the USCIS Director to authorize employees assigned to those areas', text)
        self.assertIn('does not mandate commuting use', text)
        self.assertIn('No purchase, disposal, commuting authorization or actual travel is inferred', text)

    def test_hr1968_uscis_competition_and_report_qualification_do_not_become_universal_bans(self):
        action = getattr(self, 'hr1968_operational_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The retained USCIS operational provisions', 1)[1]
        self.assertIn('funds appropriated by this Act to process or approve a competition under OMB Circular A-76', text)
        self.assertIn('including temporary or term employees', text)
        for name in ['Immigration Information Officers', 'Immigration Service Analysts', 'Contact Representatives', 'Investigative Assistants', 'Immigration Services Officers']:
            self.assertIn(name, text)
        self.assertIn('does not become a ban on all contracting, all outsourcing', text)
        self.assertIn('not the superseded 1999 circular', text)
        self.assertIn('Unreviewed attachments, costing algorithms, referenced-memorandum applications', text)
        self.assertIn('may not delegate authority to perform that act unless specifically authorized in the Act', text)
        self.assertIn('separately bound ICE Director and CFO report actors remain distinct', text)

    def test_hr1968_sponsor_protection_keeps_funding_information_and_distinct_exceptions(self):
        action = getattr(self, 'hr1968_sponsor_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The retained sponsor-information protection', 1)[1]
        self.assertIn('funds provided by this Act or any other Act', text)
        self.assertIn('specified Treasury fee accounts', text)
        self.assertIn('sponsor, potential sponsor or household member of either', text)
        self.assertIn('based on information shared by the Secretary of Health and Human Services', text)
        self.assertIn('not limited to one ICE annual account', text)
        self.assertIn('felony conviction or pending felony charge', text)
        self.assertIn('pending charge is not recast as a conviction', text)
        self.assertIn('minor unrelated to the sponsor/potential sponsor/household member', text)
        self.assertIn('minor is not paid a legal wage or cannot attend school due to the employment', text)
        self.assertIn('second and third routes do not gain an invented felony-conviction prerequisite', text)
        self.assertIn('does not order detention', text)

    def test_hr1968_sponsor_child_and_criminal_definitions_do_not_become_universal_categories(self):
        action = getattr(self, 'hr1968_sponsor_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        text = action['meaning'].split('The retained sponsor-information protection', 1)[1]
        self.assertIn('requires no lawful immigration status in the United States and age under eighteen', text)
        self.assertIn('either no parent/legal guardian in the United States or no parent/legal guardian there available to provide care and physical custody', text)
        self.assertIn('not a definition of every foreign minor, every separated child or only orphans', text)
        self.assertIn('do not convert every felony into an aggravated felony', text)
        self.assertIn('16(b) residual clause in the INA aggravated-felony context', text)
        self.assertIn('printed residual clause is not treated as an automatically valid classification rule', text)
        self.assertIn('does not invalidate the entire aggravated-felony list', text)
        self.assertIn('No particular pending charge, conviction, background-check association or sponsor/child category is classified', text)

    def test_house_foreign_tax_applicable_date_starts_on_first_day_with_three_latest_triggers(self):
        action = getattr(self, 'foreign_tax_date_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:145')
        self.assertIn('The applicable date is the first day of the first calendar year beginning on or after the latest of the printed enactment-related 90-day, foreign-tax-enactment-related 180-day and foreign-tax-first-application events;', action['meaning'])
        receipt = json.loads((DATA / 'hr1_foreign_tax_date_precision_correction.json').read_text(encoding='utf-8'))
        source = receipt['operative_witness']['passage']
        self.assertIn('first day of the first calendar year beginning on or after the latest of', source)
        self.assertIn('90 days after the date of enactment of this section', source)
        self.assertIn('180 days after the date of enactment of the unfair foreign tax', source)
        self.assertIn('the first date that an unfair foreign tax of such country begins to apply', source)

    def test_electricity_personal_status_candidates_keep_exact_version_predicates(self):
        actions = getattr(self, 'electricity_candidate_actions', None)
        if actions is None:
            actions = {a['action_id']: a for a in self.values[0]['actions']}
        house = actions['house:119:1:145']['meaning'].split('Selected exact House 112008 clean-electricity', 1)[1]
        senate = actions['house:119:1:190']['meaning'].split('Selected exact Senate 70512 clean-electricity', 1)[1]
        self.assertIn('citizen, national or resident of a covered nation', house)
        self.assertIn('except an individual who is a United States citizen or lawful permanent resident', house)
        self.assertIn('House branch does not separately print a United States national exception', house)
        self.assertIn('citizen or national of a covered nation', senate)
        self.assertIn('except an individual who is a United States citizen, national or lawful permanent resident', senate)
        self.assertIn("does not add the House's covered-country residence-only route", senate)
        self.assertIn('national and citizen are not collapsed', senate)
        for text in [house, senate]:
            self.assertIn('defined person can feed the specified-foreign-entity', text)
            self.assertIn('subject to', text)

    def test_electricity_candidates_keep_branch_exclusions_and_own_credit_periods(self):
        actions = getattr(self, 'electricity_candidate_actions', None)
        if actions is None:
            actions = {a['action_id']: a for a in self.values[0]['actions']}
        house = actions['house:119:1:145']['meaning'].split('Selected exact House 112008 clean-electricity', 1)[1]
        senate = actions['house:119:1:190']['meaning'].split('Selected exact Senate 70512 clean-electricity', 1)[1]
        for text in [house, senate]:
            self.assertIn('4651(8)(A), (B), (D) and (E), not (C)', text)
            self.assertIn('not the product list (iii)', text)
            self.assertIn('not a blanket protected-person exemption', text)
            self.assertIn('company definition excludes natural persons', text)
        self.assertIn('that delay is not applied to the direct specified-foreign-entity route', house)
        self.assertIn("not the House's separate two-year foreign-influence delay", senate)
        self.assertIn('first-year first-day exception applies to specified-foreign-entity clauses (i)-(iv)', senate)
        self.assertIn('not the direct foreign-controlled clause (v)', senate)
        self.assertIn('ratio is not the prohibited-foreign-entity share', senate)
        self.assertIn('knowing/reason-to-know certification limits', senate)

    def test_house_foreign_tax_candidate_keeps_conjunctive_personal_coverage(self):
        action = getattr(self, 'foreign_tax_candidate_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:145')
        text = action['meaning'].split('Selected exact House section 112028 adds', 1)[1]
        self.assertIn('other than a citizen or resident of the United States who is also tax resident of a discriminatory foreign country', text)
        self.assertIn('subject to Secretary exceptions', text)
        self.assertIn('cease to be applicable for less than one year', text)
        self.assertIn('not a tax increase on every immigrant, noncitizen or foreign national', text)
        self.assertIn('permanent-residence, substantial-presence and first-year-election routes', text)
        self.assertIn('tax residence does not establish citizenship, lawful presence or immigration permission', text)
        self.assertIn('House mechanism is not copied into the Senate concurrence', text)

    def test_house_foreign_tax_candidate_keeps_qualified_fiscal_effect_and_unrepaired_reference(self):
        action = getattr(self, 'foreign_tax_candidate_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:145')
        text = action['meaning'].split('Selected exact House section 112028 adds', 1)[1]
        self.assertIn('non-FIRPTA reduction, not below zero', text)
        self.assertIn('statutory rate plus twenty percentage points', text)
        self.assertIn('not a twenty-percent total tax rate', text)
        self.assertIn('fourteen-percent rate specified in 1441(a) is expressly excluded', text)
        self.assertIn('listed-country withholding safe harbors', text)
        self.assertIn('conditional best-efforts withholding-agent protection before January 1, 2027', text)
        self.assertIn('No present country listing, current effective date, actual compliance or tax owed is inferred', text)
        self.assertIn('printed (c)(2) has no such subparagraph', text)
        self.assertIn('separately reserved without source repair', text)
        self.assertIn('Yea or Nay does not establish a separate component preference', text)

    def test_hr1968_dhs_account_amounts_do_not_become_unqualified_enforcement_totals(self):
        action = getattr(self, 'hr1968_dhs_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        claims = '\n'.join(c['passage'] for c in action['claim_source_map'])
        self.assertIn('$9,986,542,000', claims)
        self.assertIn('not less than $5,082,218,000', claims)
        self.assertIn('$650,000,000 shall be transferred', claims)
        self.assertIn('not to exceed $9,100,000', claims)
        self.assertIn('mixed-use account', action['meaning'])
        self.assertIn('include DHS funding and retained safeguards', action['meaning'])
        self.assertIn('within that amount', action['meaning'])
        self.assertIn('not a repeal of all current USCIS funding or fee revenue', action['meaning'])
        self.assertIn('except sections 543 through 546', claims)
        self.assertIn('their old rescissions are not repeated', action['meaning'])

    def test_hr1968_dhs_custody_controls_keep_different_triggers_and_exceptions(self):
        action = getattr(self, 'hr1968_dhs_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        claims = '\n'.join(c['passage'] for c in action['claim_source_map'])
        self.assertIn('two most recent overall performance evaluations', claims)
        self.assertIn('Office of Professional Responsibility', claims)
        self.assertIn('both of the two most recent', action['meaning'])
        self.assertIn('not the Inspector General', action['meaning'])
        self.assertIn('Active labor or delivery is an absolute restraint bar', action['meaning'])
        self.assertIn("requires that person's request", action['meaning'])
        self.assertIn('24 hours ahead', action['meaning'])
        self.assertIn('towing-vessel inspection-fee funding restriction', action['meaning'])
        self.assertIn('not an immigration detention safeguard', action['meaning'])
        partial = next(r for r in self.values[2]['accounting']['partial_component_reviews']
                       if r['action_id'] == action['action_id'])
        self.assertFalse(partial['complete_immigration_component_review'])
        self.assertTrue(partial['remaining_executable_component_work'])

    def test_hr1968_incorporated_programs_preserve_limits_and_reserved_timing(self):
        action = getattr(self, 'hr1968_g_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        claims = {c['source_id']: c['passage'] for c in action['claim_source_map']}
        incorporated = claims['govinfo:pl118-47-g102-105-hr1968']
        self.assertIn('September 30, 2024', incorporated)
        self.assertIn('during fiscal year 2024', incorporated)
        self.assertIn('may increase', incorporated)
        self.assertIn('highest number of H-2B nonimmigrants', incorporated)
        self.assertIn('separately reserved for source-grounded review', action['meaning'])
        self.assertIn('not a universal deadline for every physician-waiver application', action['meaning'])
        self.assertIn('generally voluntary participation with specific', action['meaning'])
        self.assertIn('tentative nonconfirmation may be contested', action['meaning'])
        self.assertIn('both non-minister paths', action['meaning'])
        self.assertIn('permits, rather than mandates', action['meaning'])
        self.assertIn('not an unlimited allotment', action['meaning'])
        self.assertIn('reserved timing questions', action['compact_description'])
        audit = json.loads((DATA.parents[2] / 'review_packets' /
                            'immigration_semantic_audit_in_progress.json').read_text(encoding='utf-8'))
        questions = [q for q in audit['open_legal_interactions']
                     if q['action_id'] == action['action_id'] and
                     'G102-105' in q['scope']]
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['state'], 'preserved_for_independent_candidate_review')

    def test_hr1968_refugee_allocation_distinguishes_parent_pool_and_religious_recipients(self):
        action = getattr(self, 'hr1968_allocation_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        claim = next(c['passage'] for c in action['claim_source_map']
                     if c['source_id'] == 'govinfo:8usc1157-2024-hr1968-refugee-rules')
        self.assertIn('Within the number of admissions of refugees allocated', claim)
        self.assertIn('shall allocate one thousand of such admissions', claim)
        self.assertIn('current members of, and demonstrate public, active, and continuous participation (or attempted participation)', claim)
        self.assertIn('larger nationality-based admissions allocation and this narrower religious recipient category are distinct', action['meaning'])
        self.assertIn('are current members of the Ukrainian Catholic Church or Ukrainian Orthodox Church', action['meaning'])
        self.assertIn('demonstrate public, active and continuous participation (or attempted participation)', action['meaning'])
        self.assertIn('does not increase the general refugee admission ceiling', action['meaning'])
        limitation = next(l for l in action['limitations'] if l.startswith('The 599D(b)(3)'))
        self.assertIn('larger former-Soviet/Baltic-national refugee admissions allocation', limitation)
        self.assertIn('narrower 599D(b)(2)(B) recipient category', limitation)
        self.assertIn('public, active and continuous participation (or attempted participation)', limitation)

    def test_hr1968_oath_funding_bar_preserves_existing_qualified_accommodations(self):
        action = getattr(self, 'hr1968_restrictions_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        claims = '\n'.join(c['passage'] for c in action['claim_source_map'])
        self.assertIn('may be used to amend the oath of allegiance', claims)
        self.assertIn('physical or developmental disability or mental impairment', claims)
        self.assertIn('existing oath\'s accommodations', action['meaning'])
        self.assertIn('Their stated showings and official determinations remain', action['meaning'])
        self.assertIn('does not grant a waiver to any person', action['meaning'])

    def test_hr1968_id_and_employment_funding_bars_do_not_become_universal_status_rules(self):
        action = getattr(self, 'hr1968_restrictions_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        claims = '\n'.join(c['passage'] for c in action['claim_source_map'])
        self.assertIn('with respect to the employment of an alien at a particular time', claims)
        self.assertIn('lawfully admitted for permanent residence', claims)
        self.assertIn('authorized to be so employed', claims)
        self.assertIn('does not abolish all existing identification documents', action['meaning'])
        self.assertIn('employment-specific at the particular time', action['meaning'])
        self.assertIn('not a bar on employing every noncitizen', action['meaning'])

    def test_hr1968_transfer_exceptions_do_not_erase_other_conditions_or_create_payments(self):
        action = getattr(self, 'hr1968_controls_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        claims = '\n'.join(c['passage'] for c in action['claim_source_map'])
        self.assertIn('limitation as to time and condition of section 503(d)', claims)
        self.assertIn('at least 5 days in advance', claims)
        self.assertIn('requirement of paragraph (1) that an immigration emergency be determined shall not apply', claims)
        self.assertIn('specific subsection exception, not removal of all transfer caps', action['meaning'])
        self.assertIn('paragraph expressly does not require the paragraph (1)', action['meaning'])
        self.assertIn('not combined into an automatic $40,000,000 allotment', action['meaning'])
        self.assertIn('does not establish that balance or actual transfers', action['meaning'])

    def test_hr1968_fence_fee_and_biometric_scopes_remain_qualified(self):
        action = getattr(self, 'hr1968_controls_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        claims = '\n'.join(c['passage'] for c in action['claim_source_map'])
        self.assertIn('within or east of the Vista del Mar', claims)
        self.assertIn('remain available until expended', claims)
        self.assertIn('Application Support Center that is overseen virtually', claims)
        self.assertIn('not a prohibition on every border project or every other funding stream', action['meaning'])
        self.assertIn('not an all-wall-construction amount', action['meaning'])
        self.assertIn('Virgin Islands and Guam payment provisions', action['meaning'])
        self.assertIn('neither that saving nor this baseline fixes a new applicant fee', action['meaning'])
        self.assertIn('not permission for unrestricted home collection', action['meaning'])

    def test_hr1968_reporting_keeps_actors_cadence_and_literal_duration_boundaries(self):
        action = getattr(self, 'hr1968_reporting_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        claims = '\n'.join(c['passage'] for c in action['claim_source_map'])
        self.assertIn('Chief Financial Officer', claims)
        self.assertIn('previous twelve months of semimonthly data', claims)
        self.assertIn('for less than 6 months', claims)
        self.assertIn('submitted by the ICE Director, not the Inspector General', action['meaning'])
        self.assertIn('submitted by the ICE Chief Financial Officer', action['meaning'])
        self.assertIn('There is no enumerated training-report requirement', action['meaning'])
        self.assertIn('Semimonthly is retained; no biweekly schedule', action['meaning'])
        self.assertIn('preserves those exact endpoints rather than filling unstated boundary cases', action['meaning'])
        self.assertIn('not observed counts', action['meaning'])

    def test_hr1968_reporting_cohort_is_reserved_with_complete_historical_definitions(self):
        action = getattr(self, 'hr1968_reporting_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        claims = {c['source_id']: c['passage'] for c in action['claim_source_map']}
        source = next(s for s in self.values[1]['sources']
                      if s['source_id'] == 'ecfr:28cfr1155-2024-04-01-complete')
        self.assertEqual(claims[source['source_id']], source['text'])
        for definition in ['Detainee means', 'Employee means', 'Intersex means',
                           'Transgender means', 'Youthful detainee means']:
            self.assertIn(definition, source['text'])
        self.assertIn('selects neither only transgender/intersex people nor every person', action['meaning'])
        self.assertIn('does not extend all of part 115', action['meaning'])
        audit = json.loads((DATA.parents[2] / 'review_packets' /
                            'immigration_semantic_audit_in_progress.json').read_text(encoding='utf-8'))
        questions = [q for q in audit['open_legal_interactions']
                     if q['action_id'] == action['action_id'] and '115.5 reporting-cohort' in q['scope']]
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['state'], 'preserved_for_independent_candidate_review')
        self.assertIn(source['source_id'], questions[0]['source_ids'])
        self.assertTrue(questions[0]['recommendation'])
        self.assertTrue(questions[0]['alternatives'])
        self.assertTrue(questions[0]['safe_parallel_work'])

    def test_retained_287g_reporter_and_fields_are_separate_from_ig_and_budget_roles(self):
        actions = getattr(self, 'retained_report_actions', None)
        if actions is None:
            actions = [a for a in self.values[0]['actions']
                       if a['action_id'] in {'house:119:2:42', 'house:119:2:87', 'house:119:2:104'}]
        self.assertEqual(len(actions), 3)
        source = next(s for s in self.values[1]['sources']
                      if s['source_id'] == 'govinfo:pl116-93-dhs216-217')['text']
        retained = source[source.index('Sec. 217.'):source.index('Sec. 218.')]
        self.assertIn('Director of U.S. Immigration and Customs Enforcement', retained)
        self.assertNotIn('training', retained.lower())
        for action in actions:
            with self.subTest(action=action['action_id']):
                self.assertIn('submitted by the ICE Director, not the Inspector General', action['meaning'])
                self.assertIn('enumerated fields do not include training', action['meaning'])
                self.assertIn("distinct from the current Act's section 217 budget plan", action['meaning'])
                self.assertNotIn('The accompanying IG 287(g) report', action['meaning'])

    def test_package_documentary_index_preserves_occurrences_and_tail_boundaries(self):
        receipt = getattr(self, 'package_coverage_receipt', None)
        if receipt is None:
            receipt = json.loads((DATA / 'hr1_full_package_coverage_reconciliation.json').read_text(encoding='utf-8'))
        versions = receipt['version_ledgers']
        self.assertEqual([len(v['rows']) for v in versions], [335, 332, 309])
        self.assertEqual(sum(len(v['rows']) for v in versions), 976)
        for version in versions:
            self.assertEqual(len({r['interval_id'] for r in version['rows']}), len(version['rows']))
            self.assertEqual(version['rows'][-1]['source_text_extent']['end'], version['indexed_body_extent']['end'])
            self.assertNotIn('The SPEAKER pro tempore', version['final_section_passage'])
            self.assertNotIn('Passed the House of Representatives', version['final_section_passage'])
            self.assertNotIn('Attest:', version['final_section_passage'])
        duplicates = [r for r in versions[0]['rows'] if r['outer_section'] == 60004]
        self.assertEqual(len(duplicates), 2)
        self.assertNotEqual(duplicates[0]['source_text_extent']['start'], duplicates[1]['source_text_extent']['start'])
        self.assertIn('STATE BORDER SECURITY REIMBURSEMENT', duplicates[0]['title_excerpt'])
        self.assertIn('PRESIDENTIAL RESIDENCE PROTECTION', duplicates[1]['title_excerpt'])

    def test_package_index_does_not_promote_overlap_or_numbers_to_semantic_closure(self):
        receipt = getattr(self, 'package_coverage_receipt', None)
        if receipt is None:
            receipt = json.loads((DATA / 'hr1_full_package_coverage_reconciliation.json').read_text(encoding='utf-8'))
        self.assertFalse(receipt['full_section_semantic_screening_complete'])
        self.assertFalse(receipt['all_absent_counterparts_verified'])
        self.assertTrue(receipt['ordinary_screenings_can_continue'])
        self.assertTrue(receipt['available_operative_evidence_not_reclassified_unavailable'])
        self.assertTrue(receipt['number_identity_limitations']['numeric_pairing_not_safe_for_semantic_counterparts'])
        self.assertEqual(len(receipt['remaining_domain_fits']), 3)
        self.assertEqual(receipt['accounting']['application_questions'], 62)
        for row in receipt['house_eh_documentary_comparison_index']:
            self.assertFalse(row['meaning_transferred'])
            self.assertFalse(row['full_semantic_comparison_complete'])
        for version in receipt['version_ledgers']:
            for row in version['rows']:
                self.assertFalse(row['full_section_semantic_review_complete'])
                for overlap in row['exact_primary_canonical_binding_overlaps']:
                    self.assertTrue(overlap['not_full_section_semantic_coverage'])

    def test_electricity_person_predicates_keep_exact_version_exceptions(self):
        receipt = getattr(self, 'electricity_scope_receipt', None)
        if receipt is None:
            receipt = json.loads((DATA / 'hr1_foreign_entity_electricity_scope_review.json').read_text(encoding='utf-8'))
        bodies = {w['source_id']: w['passage'] for w in receipt['operative_witnesses']}
        house = bodies['congressional-record:2025-05-21-hr1-as-amended']
        senate = bodies['govinfo:hr1eas']
        self.assertIn('a person who is a citizen, national, or resident of a covered nation', house)
        self.assertIn('not an individual who is a citizen or lawful permanent resident of the United States', house)
        self.assertIn('a person who is a citizen or national of a covered nation', senate)
        self.assertIn('not an individual who is a citizen, national, or lawful permanent resident of the United States', senate)
        self.assertNotIn('citizen, national, or resident of a covered nation', senate)
        originals = receipt['original_context_witnesses']
        protected = next(w['passage'] for w in originals if '1324b' in w['source_id'])
        self.assertIn('fails to apply for naturalization within six months', protected)
        self.assertIn('actively pursuing naturalization', protected)
        company = next(w['passage'] for w in originals if '10usc113' in w['source_id'])
        self.assertIn('does not include natural persons', company)
        self.assertEqual(receipt['scope_assessment']['domain_application_boundary']['state'], 'reserved_bounded_domain_fit')
        self.assertFalse(receipt['scope_assessment']['canonical_meanings_changed'])

    def test_electricity_ownership_and_influence_rules_are_version_specific(self):
        receipt = getattr(self, 'electricity_scope_receipt', None)
        if receipt is None:
            receipt = json.loads((DATA / 'hr1_foreign_entity_electricity_scope_review.json').read_text(encoding='utf-8'))
        bodies = {w['source_id']: w['passage'] for w in receipt['operative_witnesses']}
        house = bodies['congressional-record:2025-05-21-hr1-as-amended']
        senate = bodies['govinfo:hr1eas']
        self.assertIn('section 318 (other than subsection (a)(3) thereof)', house)
        self.assertIn('section 318(a)(2) shall apply', senate)
        self.assertIn('direct or indirect authority to appoint a covered officer', house)
        self.assertIn('direct authority to appoint a covered officer', senate)
        self.assertIn('owns at least 10 percent', house)
        self.assertIn('owns at least 25 percent', senate)
        self.assertIn('shall not apply unless such entity makes such payments knowingly (or has reason to know)', house)
        self.assertIn('any purchase or sale of intellectual property where the agreement provides that ownership of the intellectual property reverts', senate)
        self.assertIn('not be considered a bona-fide purchase or sale', senate)
        self.assertIn('not less than 80 percent of the equity securities', senate)

    def test_electricity_material_ratio_and_house_formal_labels_are_preserved(self):
        receipt = getattr(self, 'electricity_scope_receipt', None)
        if receipt is None:
            receipt = json.loads((DATA / 'hr1_foreign_entity_electricity_scope_review.json').read_text(encoding='utf-8'))
        bodies = {w['source_id']: w['passage'] for w in receipt['operative_witnesses']}
        senate = bodies['govinfo:hr1eas']
        self.assertIn('a material assistance cost ratio which is less than the threshold percentage', senate)
        self.assertIn('the total direct costs to the taxpayer attributable to all manufactured products', senate)
        self.assertIn('the cost to the taxpayer with respect to such product, component, element, material, or subcomponent shall not be included', senate)
        self.assertIn('pursuant to a binding written contract which was entered into prior to June 16, 2025', senate)
        self.assertIn('the taxpayer may not rely on such certification', senate)
        self.assertIn('due to a reasonable cause and not willful neglect', senate)
        self.assertIn('(d) Definitions Relating to Prohibited Foreign Entities', bodies['congressional-record:2025-05-21-hr1-as-amended'])
        self.assertIn('(c) Definitions Relating to Prohibited Foreign Entities', bodies['govinfo:hr1eh'])
        self.assertFalse(receipt['house_eh_comparison']['exact_bytes_equal'])
        self.assertFalse(receipt['scope_assessment']['full_package_review_complete'])

    def test_foreign_tax_applicability_is_not_nationality_or_immigration_entry(self):
        receipt = getattr(self, 'foreign_tax_scope_receipt', None)
        if receipt is None:
            receipt = json.loads((DATA / 'hr1_foreign_tax_remedy_scope_review.json').read_text(encoding='utf-8'))
        for witness in receipt['operative_witnesses']:
            with self.subTest(source=witness['source_id']):
                self.assertIn('any individual (other than a citizen or resident of the United States) who is tax resident of a discriminatory foreign country', witness['passage'])
                self.assertIn('if a person would cease to be an applicable person for a period of less than one year', witness['passage'])
        original = {w['source_id']: w['passage'] for w in receipt['original_context_witnesses']}
        self.assertIn('temporarily present in the United States as a nonimmigrant', original['govinfo:26usc871-2024-complete'])
        self.assertIn('under section 871(b)(1)', original['govinfo:26usc897-2024-complete'])
        definition = original['govinfo:26usc7701-2024-complete']
        self.assertIn('Such individual meets the substantial presence test', definition)
        self.assertIn('is neither a citizen of the United States nor a resident of the United States', definition)
        self.assertFalse(receipt['scope_assessment']['canonical_meanings_changed'])
        self.assertEqual(receipt['scope_assessment']['domain_application_boundary']['state'], 'reserved_bounded_domain_fit')
        self.assertFalse(receipt['senate_counterpart_search']['complete_counterpart_absence_verified'])

    def test_foreign_tax_cap_exceptions_and_printed_reference_remain_bounded(self):
        receipt = getattr(self, 'foreign_tax_scope_receipt', None)
        if receipt is None:
            receipt = json.loads((DATA / 'hr1_foreign_tax_remedy_scope_review.json').read_text(encoding='utf-8'))
        for witness in receipt['operative_witnesses']:
            with self.subTest(source=witness['source_id']):
                body = witness['passage']
                self.assertIn('statutory rate) increased by 20 percentage points', body)
                self.assertIn('shall not apply to the 14 percent rate', body)
                self.assertIn('first day of the first calendar year beginning on or after the latest of', body)
                self.assertIn('90 days after the date of enactment of this section', body)
                self.assertIn('180 days after the date of enactment of the unfair foreign tax', body)
                self.assertIn('before January 1, 2027', body)
                self.assertIn('made best efforts to comply', body)
                self.assertIn('(c)(2)(A)(ii)', body)
                self.assertIn('Such term does not include any possession of the United States', body)
        self.assertFalse(receipt['house_eh_comparison']['exact_bytes_equal'])
        self.assertEqual(len(receipt['house_eh_comparison']['enumerated_typographic_differences']), 3)
        self.assertEqual(receipt['scope_assessment']['candidate_scope_disposition'], 'proposed_context_only_pending_bounded_domain_review')

    def test_customs_scope_keeps_article_object_and_maximum_penalty(self):
        receipt = getattr(self, 'customs_scope_receipt', None)
        if receipt is None:
            receipt = json.loads((DATA / 'hr1_customs_shipment_scope_review.json').read_text(encoding='utf-8'))
        for witness in receipt['operative_witnesses']:
            with self.subTest(source=witness['source_id']):
                body = witness['passage']
                self.assertIn('attempts to introduce an article into the United States using the privilege', body)
                self.assertIn('the importation of which violates any other provision of United States customs law', body)
                self.assertIn('up to $5,000 for the first violation and up to $10,000 for each subsequent violation', body)
                self.assertIn('in addition to any other penalty permitted by law', body)
                self.assertIn('30 days after the date of the enactment of this Act', body)
                self.assertIn('Subsection (c) of such section 321, as added by subsection (a) of this section, is repealed', body)
                self.assertIn('shall take effect on July 1, 2027', body)
                self.assertNotIn('CHAPTER 6--', body)
        scope = receipt['scope_assessment']
        self.assertEqual(scope['candidate_scope_disposition'], 'context_only_no_new_immigration_meaning')
        self.assertFalse(scope['canonical_meanings_changed'])
        self.assertFalse(scope['eligibility_or_counting_changed'])

    def test_customs_version_targets_and_original_goods_privileges_are_distinct(self):
        receipt = getattr(self, 'customs_scope_receipt', None)
        if receipt is None:
            receipt = json.loads((DATA / 'hr1_customs_shipment_scope_review.json').read_text(encoding='utf-8'))
        bodies = {w['source_id']: w['passage'] for w in receipt['operative_witnesses']}
        self.assertIn('Section 321(a)(2)(B) of such Act (19 U.S.C. 1321(a)(2)(B))', bodies['congressional-record:2025-05-21-hr1-as-amended'])
        self.assertIn('Section 321(a)(2) of such Act (19 U.S.C. 1321(a)(2))', bodies['govinfo:hr1eas'])
        self.assertNotIn('1321(a)(2)(B)', bodies['govinfo:hr1eas'])
        original = receipt['original_context_witnesses'][0]['passage']
        self.assertIn('articles imported by one person on one day', original)
        self.assertIn('$100 in the case of articles sent as bona fide gifts', original)
        self.assertIn('$200 in the case of articles accompanying, and for the personal or household use', original)
        self.assertIn('$800 in any other case', original)
        self.assertIn('a single order or contract is forwarded in separate lots', original)
        self.assertIn('The Secretary of the Treasury is authorized by regulations to prescribe exceptions', original)
        self.assertEqual(receipt['scope_assessment']['amendment_application_boundary']['state'],
                         'literal_instruction_preserved_no_codification_adjudication')

    def test_hra_employee_class_permission_keeps_joint_tax_predicate(self):
        receipt = getattr(self, 'hra_scope_receipt', None)
        if receipt is None:
            receipt = json.loads((DATA / 'hr1_hra_employee_class_scope_review.json').read_text(encoding='utf-8'))
        house = receipt['operative_witnesses'][0]['passage']
        self.assertIn('any of the following may be designated as a specified class of employee', house)
        self.assertIn('who are nonresident aliens and who receive no earned income', house)
        self.assertIn('(within the meaning of section 911(d)(2)) from the employer', house)
        self.assertIn('income from sources within the United States (within the meaning of section 861(a)(3))', house)
        self.assertIn('offers such arrangement to all employees within such specified class on the same terms', house)
        self.assertIn('To the extent not inconsistent with the amendments made by this section', house)
        self.assertIn('plan years beginning after December 31, 2025', house)
        self.assertFalse(receipt['scope_assessment']['canonical_meanings_changed'])
        self.assertFalse(receipt['scope_assessment']['eligibility_or_counting_changed'])
        self.assertTrue(receipt['scope_assessment']['independent_domain_review_pending'])

    def test_hra_original_tax_exceptions_and_cfr_reference_remain_distinct(self):
        receipt = getattr(self, 'hra_scope_receipt', None)
        if receipt is None:
            receipt = json.loads((DATA / 'hr1_hra_employee_class_scope_review.json').read_text(encoding='utf-8'))
        witnesses = receipt['original_context_witnesses']
        income = next(w['passage'] for w in witnesses if w['source_id'] == 'govinfo:26usc861-2024-complete')
        self.assertIn('not exceeding a total of 90 days', income)
        self.assertIn('does not exceed $3,000 in the aggregate', income)
        self.assertIn('regular member of the crew of a foreign vessel', income)
        earned = next(w['passage'] for w in witnesses if w['source_id'] == 'govinfo:26usc911-2024-complete'
                      and w['passage'].startswith('(2) Earned income'))
        self.assertIn('not in excess of 30 percent', earned)
        self.assertIn('distribution of earnings or profits rather than a reasonable allowance', earned)
        definition = next(w['passage'] for w in witnesses if w['source_id'] == 'govinfo:26usc7701-2024-complete')
        self.assertIn('Substantial presence test', definition)
        self.assertIn('First year election', definition)
        self.assertIn('neither a citizen of the United States nor a resident of the United States', definition)
        old_class = next(w['passage'] for w in witnesses if w['source_id'] == 'govinfo:cfr2024-26-1.105-11-page407')
        self.assertIn('911(b)', old_class)
        self.assertNotIn('911(d)(2)', old_class)

    def test_duplicate_enrollment_number_condition_is_not_a_new_status_gate(self):
        receipt = getattr(self, 'duplicate_enrollment_receipt', None)
        if receipt is None:
            receipt = json.loads((DATA / 'hr1_duplicate_enrollment_scope_review.json').read_text(encoding='utf-8'))
        scope = receipt['scope_assessment']
        self.assertEqual(scope['candidate_scope_disposition'], 'context_only_no_new_immigration_meaning')
        self.assertFalse(scope['whole_action_disposition_changed'])
        self.assertFalse(scope['eligibility_or_counting_changed'])
        for witness in receipt['operative_witnesses']:
            with self.subTest(source=witness['source_id']):
                body = witness['passage']
                self.assertIn('if such individual has a social security number and is required to provide such number', body)
                self.assertIn('if such individual does not reside in such State', body)
                self.assertIn('unless such individual meets such an exception as the Secretary may specify', body)
                self.assertIn('not less frequently than once each month and during each determination or redetermination', body)
                self.assertIn('consistent with subsection (a)(7)', body)
                self.assertIn('directly from, or verified by such entity or plan directly with, such individual', body)

    def test_duplicate_enrollment_versions_preserve_funding_actor_and_paris_scope(self):
        receipt = getattr(self, 'duplicate_enrollment_receipt', None)
        if receipt is None:
            receipt = json.loads((DATA / 'hr1_duplicate_enrollment_scope_review.json').read_text(encoding='utf-8'))
        bodies = {w['source_id']: w['passage'] for w in receipt['operative_witnesses']}
        house = bodies['congressional-record:2025-05-21-hr1-as-amended']
        senate = bodies['govinfo:hr1eas']
        self.assertIn('appropriated to the Secretary', house)
        self.assertIn('notify or transmit information to a State', house)
        self.assertIn('appropriated to the Administrator of the Centers for Medicare & Medicaid Services', senate)
        self.assertNotIn('notify or transmit information to a State', senate)
        self.assertIn('(for purposes of address verification under section 1902(vv))', senate)
        self.assertNotIn('(for purposes of address verification under section 1902(vv))', house)
        self.assertIn('(or wavier of such plan)', house)
        for body in [house, senate]:
            self.assertIn('for fiscal year 2026, $10,000,000', body)
            self.assertIn('for fiscal year 2029, $20,000,000', body)
            self.assertIn('beginning not later than January 1, 2027', body)
            self.assertIn('beginning not later than October 1, 2029', body)

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

    def test_scholarship_citizen_resident_condition_stays_with_senate_donor(self):
        for aid, label in [('house:119:1:145', 'House'), ('house:119:1:190', 'Senate')]:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
            qualification = next(q for q in action['limitations']
                                 if q.startswith('Selected exact ' + label + ' scholarship contributing-taxpayer'))
            for text in [action['meaning'], qualification]:
                own = text[text.index('Selected exact ' + label + ' scholarship contributing-taxpayer'):]
                with self.subTest(action=aid, surface='meaning' if text == action['meaning'] else 'qualification'):
                    if label == 'House':
                        allowance = own[own.index('House new 25F allowance:'):own.index('House own contributing-taxpayer credit limits:')]
                        student = own[own.index('House own eligible-student definition:'):own.index('House own complete calendar volume-cap mechanism:')]
                        self.assertNotIn('citizen or resident', allowance)
                    else:
                        allowance = own[own.index('Senate own new 25F clause a:'):own.index('Senate own new 25F clause b:')]
                        self.assertIn('individual who is a citizen or resident of the United States', allowance)
                        self.assertIn('section 7701(a)(9)', allowance)
                        self.assertNotIn('7701(b)', allowance)
                        definitions = own[own.index('Senate own new 25F clause c:'):own.index('Senate own new 25F clause d:')]
                        student = definitions[definitions.index('(2) Eligible student.--'):definitions.index('(3) Qualified contribution.--')]
                        self.assertIn('calendar year prior to the date of the application', student)
                    self.assertIn('300 percent of the area median gross income', student)
                    self.assertIn('eligible to enroll in a public elementary or secondary school', student)
                    self.assertNotIn('citizen or resident', student)

    def test_scholarship_versions_keep_income_recipient_and_calendar_boundaries(self):
        for aid, label, year in [('house:119:1:145', 'House', '2025'), ('house:119:1:190', 'Senate', '2026')]:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
            qualification = next(q for q in action['limitations']
                                 if q.startswith('Selected exact ' + label + ' scholarship contributing-taxpayer'))
            for text in [action['meaning'], qualification]:
                own = text[text.index('Selected exact ' + label + ' scholarship contributing-taxpayer'):]
                with self.subTest(action=aid, surface='meaning' if text == action['meaning'] else 'qualification'):
                    income = own[own.index(label + ' separate scholarship income '):own.index(label + ' own applicability dates:')]
                    dates = own[own.index(label + ' own applicability dates:'):]
                    self.assertIn('taxable years ending after December 31, ' + year, dates)
                    if label == 'House':
                        self.assertIn('provided to any dependent of such individual', income)
                        self.assertIn('shall not apply to amounts received after December 31, 2029', income)
                        cap = own[own.index('House own complete calendar volume-cap mechanism:'):own.index('House separate scholarship income exemption:')]
                        self.assertIn('calendar years 2026 through 2029, and zero for calendar years thereafter', cap)
                        self.assertIn('105 percent', cap)
                        self.assertIn('shall not be less than the volume cap', cap)
                        self.assertIn('separately reserved as question 62', own)
                    else:
                        self.assertIn('provided to such individual or any dependent of such individual', income)
                        self.assertNotIn('2029', income)
                        limit = own[own.index('Senate own new 25F clause b:'):own.index('Senate own new 25F clause c:')]
                        self.assertIn('shall not exceed $1,700', limit)

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

    def test_ordinary_screening_capture_is_present_in_durable_manifest(self):
        receipt = json.loads((DATA / 'ordinary_screening_checkpoint80.json').read_text(encoding='utf-8'))
        manifest = getattr(self, 'screening_capture_manifest', None)
        if manifest is None:
            manifest = json.loads((DATA / 'research_capture_manifest.json').read_text(encoding='utf-8'))
        rows = [r for r in manifest['sources'] if r['source_id'] == receipt['acquisition_source_id']]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['raw_sha256'], receipt['acquisition']['raw_sha256'])
        self.assertEqual(rows[0]['text_length'], receipt['acquisition']['full_text_length'])
        source = next(s for s in self.values[1]['sources']
                      if s['source_id'] == 'govinfo:43usc1613-2024-land-conveyance-c-g')
        self.assertEqual(source['captured_full_text_sha256'], rows[0]['text_sha256'])
        self.assertEqual(source['raw_sha256'], rows[0]['raw_sha256'])

    def test_zero_ordinary_screenings_does_not_close_partial_package_review(self):
        reviews = self.values[2]['accounting']['partial_component_reviews']
        incomplete = sum(r.get('complete_immigration_component_review') is not True
                         or bool(r.get('remaining_executable_component_work')) for r in reviews)
        self.assertGreaterEqual(incomplete, 2)
        self.assertTrue({'house:119:1:145', 'house:119:1:190'} <= {r['action_id'] for r in reviews})
        with self.assertRaisesRegex(ValueError, f'package component review remains incomplete: {incomplete}'):
            require_complete_research([], reviews)
        self.assertEqual(validate(*self.values)['unfinished_component_reviews'], incomplete)

    def test_hr1968_refugee_adjustment_and_heading_keep_distinct_limits(self):
        action = getattr(self, 'hr1968_action', None)
        if action is None:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:1:70')
        claims = {c['source_id']: c['passage'] for c in action['claim_source_map']}
        refugee = claims['govinfo:8usc1157-2024-hr1968-refugee-rules']
        adjustment = claims['govinfo:8usc1255-2024-hr1968-adjustment-rules']
        self.assertIn('within the number of such admissions allocated', refugee)
        self.assertIn('before October 1, 2024', refugee)
        self.assertNotIn('Iran', adjustment)
        self.assertIn('beginning on August 15, 1988', adjustment)
        self.assertIn('after being denied refugee status', adjustment)
        self.assertIn('at least 1 year', adjustment)
        self.assertIn('physically present in the United States on the date', adjustment)
        self.assertIn('pays a fee', adjustment)
        self.assertIn('Within refugee admissions already allocated under section 207(a)(3)', action['meaning'])
        self.assertIn('three section 599D(e) branches', action['meaning'])
        self.assertIn('changes only the terminal year in the heading', action['meaning'])
        self.assertIn('not a new universal parole power', action['meaning'])
        self.assertIn('no separate position', action['choice_meanings']['Nay'])
        partial = next(r for r in self.values[2]['accounting']['partial_component_reviews']
                       if r['action_id'] == action['action_id'])
        self.assertFalse(partial['complete_immigration_component_review'])
        self.assertTrue(partial['remaining_executable_component_work'])

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

    def _assert_relative_trafficking_common_chapeau(self, action, source):
        branch = source[source.index('(C) Controlled substance traffickers'):
                        source.index('(D) Prostitution')]
        chapeau = branch[:branch.index('(i)')]
        self.assertIn('the consular officer or the Attorney General knows or has reason to believe', chapeau)
        self.assertIn('(ii) is the spouse, son, or daughter', branch)
        relative = re.search(r'Clause \(C\)\(ii\).*?(?=\nUnder |$)',
                             action['meaning'], re.S)
        self.assertIsNotNone(relative, 'The relative-benefit branch needs a self-contained explanation')
        for role in ['consular officer', 'Attorney General']:
            self.assertIn(role, relative.group())
        self.assertRegex(relative.group(), r'know(?:s)? or ha(?:ve|s) reason to believe')
        qualification = next(q for q in action['limitations'] if '(C)(ii)' in q)
        for role in ['consular officer', 'Attorney General']:
            self.assertIn(role, qualification)
        self.assertRegex(qualification, r'know(?:s)? or ha(?:ve|s) reason to believe')
        self.assertIn("recipient's own knowledge", qualification)

    def test_relative_trafficking_branch_cannot_drop_the_common_official_threshold(self):
        source = next(s['text'] for s in self.values[1]['sources']
                      if s['source_id'] == 'govinfo:8usc1182a-2024-current-student-aid-reference')
        for aid in ['house:119:1:32', 'house:119:1:33', 'house:119:1:166']:
            action = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
            with self.subTest(action=aid, surface='meaning and both-level qualification'):
                self._assert_relative_trafficking_common_chapeau(action, source)
            with self.subTest(action=aid, omission='relative-branch official threshold'):
                bad = copy.deepcopy(action)
                fragment = 'the consular officer or Attorney General must know or have reason to believe that '
                self.assertEqual(bad['meaning'].count(fragment), 1)
                bad['meaning'] = bad['meaning'].replace(fragment, '', 1)
                # The earlier (i) threshold remains; it cannot repair the omission in (ii).
                with self.assertRaises(AssertionError):
                    self._assert_relative_trafficking_common_chapeau(bad, source)
            with self.subTest(action=aid, omission='both-level qualification threshold'):
                bad = copy.deepcopy(action)
                index = next(i for i, q in enumerate(bad['limitations']) if '(C)(ii)' in q)
                fragment = 'the consular officer or Attorney General to know or have reason to believe their conditions'
                self.assertIn(fragment, bad['limitations'][index])
                bad['limitations'][index] = bad['limitations'][index].replace(fragment, 'the listed conditions', 1)
                with self.assertRaises(AssertionError):
                    self._assert_relative_trafficking_common_chapeau(bad, source)

    def test_s331_uses_its_june_extension_without_consuming_an_ordinary_item(self):
        aid = 'house:119:1:166'
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        law = sources['govinfo:pl119-4']['text']
        start = law.index('SEC. 3105.')
        extension = law[start:law.index('SEC. 3106.', start)]
        self.assertIn('striking ``March 31, 2025', extension)
        self.assertIn('inserting ``September 30, 2025', extension)
        self.assertIn('Mar. 15, 2025', law[:450])
        self.assertEqual(action['source_id'], 'govinfo:s331es')
        self.assertEqual(sources[action['source_id']]['text_version'], 'ES')
        self.assertEqual(action['stage'], 'final_passage')
        self.assertIn(extension, [c['passage'] for c in action['claim_source_map']])
        self.assertNotIn('govinfo:hr27eh', action['additional_source_ids'])
        self.assertNotIn('govinfo:hres93eh', action['additional_source_ids'])

        def assert_june_baseline(candidate):
            for surface in [candidate['compact_description'], candidate['meaning'],
                            candidate['limitations'][1]]:
                self.assertIn('september30,2025', re.sub(r'\s+', '', surface).lower())
            self.assertFalse(any('Current166exclusion' in q for q in candidate['limitations']))

        assert_june_baseline(action)
        wrong = copy.deepcopy(action)
        for key in ['compact_description', 'meaning']:
            wrong[key] = re.sub(r'September\s*30,\s*2025', 'March 31, 2025', wrong[key])
        wrong['limitations'][1] = re.sub(r'September\s*30,\s*2025', 'March 31, 2025',
                                         wrong['limitations'][1])
        with self.assertRaises(AssertionError):
            assert_june_baseline(wrong)

        receipt = json.loads((DATA / 's331_candidate_reclassification_checkpoint137.json')
                             .read_text(encoding='utf-8'))
        self.assertEqual(receipt['receipt_sha256'], sealed_digest(receipt, 'receipt_sha256'))
        before = receipt['before_review_record']
        after = receipt['corrected_review_record']
        self.assertEqual(before['action_id'], after['action_id'])
        self.assertEqual(before['disposition'], 'exact_action_ineligible')
        self.assertEqual(after['disposition'], 'interpreted_substantive_directional')
        self.assertEqual(receipt['before_review_record_sha256'], digest(before))
        self.assertEqual(receipt['corrected_review_record_sha256'], digest(after))
        self.assertEqual(receipt['accounting_deltas']['governed_reviews'], 0)
        self.assertEqual(receipt['accounting_deltas']['ordinary_pending'], 0)
        self.assertEqual(receipt['accounting_deltas']['interpreted_actions'], 1)
        self.assertEqual(receipt['accounting_deltas']['excluded_actions'], -1)

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
