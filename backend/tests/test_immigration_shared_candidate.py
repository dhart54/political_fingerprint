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

    def test_housing226_status_scope_follows_named_programmes_not_all_housing(self):
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        statute = sources['govinfo:42usc1436a-operative2024-housing226']['text']
        self.assertIn('United States Housing Act of 1937', statute)
        self.assertIn('1474, 1490a(a)(2)(A)', statute)
        self.assertIn('subtitle A of title III', statute)
        self.assertNotIn('subtitle A of title II of', statute)
        records = {r['action_id']: r for r in self.values[3]['records']}
        for aid in ['house:119:2:57', 'house:119:2:176']:
            text = records[aid]['rationale']
            self.assertIn('HOME TitleII', text)
            self.assertIn('not an individual', text)
            core = next(c for c in self.products[0]['actions'] if c['action_id'] == aid)
            sid = 'govinfo:42usc1436a-operative2024-housing226'
            self.assertIn(sid, {s['source_id'] for s in core['operative_meaning_source_identities']})
            self.assertTrue(any(c['source_id'] == sid and c['passage'] == statute for c in core['claim_source_map']))

    def test_may226_escrow_admission_and_rent_exception_remain_separate(self):
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        body = sources['govinfo:hres1299eh-full-housing']['text']
        self.assertIn('may not escrow any amounts for any covered family whose adjusted income exceeds 80 percent', body)
        self.assertIn('unless the eligible entity has established an alternative rent structure', body)
        text = next(r['rationale'] for r in self.values[3]['records'] if r['action_id'] == 'house:119:2:176')
        def check(candidate):
            for phrase in ['bars ESCROWING AMOUNTS', 'not an invented blanket definition of family admission eligibility',
                           'Secretary MAY establish', 'UNLESS an approved alternative rent structure',
                           'TENyearprogramme termination', 'ceasing narrowly defined cash-welfare assistance AND']:
                self.assertIn(phrase, candidate)
        check(text)
        for phrase in ['bars ESCROWING AMOUNTS', 'UNLESS an approved alternative rent structure', 'Secretary MAY establish']:
            with self.subTest(predicate=phrase), self.assertRaises(AssertionError):
                check(text.replace(phrase, 'universal admission rule'))
        massie = next(m for m in self.products[2] if m['member_id'] == 'M001184')
        row = next(a for a in massie['actions'] if a['action_id'] == 'house:119:2:176')
        self.assertEqual(row['official_status'], 'Not Voting')
        self.assertEqual(row['exact_choice_effect'], 'resolved_non_directional')

    def test_coastguard226_literal_anchor_and_vessel_crew_scope_survive(self):
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        primary = sources['govinfo:hr4275eh']['text']
        code = sources['govinfo:46usc7304-operative2024-cg226']['text']
        self.assertIn('a citizen of the United States', code)
        self.assertIn('not more than 50 percent of the unlicensed seamen', primary)
        self.assertIn('ending on December 31, 2065', primary)
        core = next(c for c in self.products[0]['actions'] if c['action_id'] == 'house:119:1:218')
        def check(candidate):
            text = candidate['candidate_exact_action_meaning']
            for phrase in ['plural citizens', 'singular citizen', 'not first creation',
                           'not a first-ever citizen-only rule', 'ONLY to the defined large-passenger-vessel',
                           'throughDecember31,2065', 'EXISTING≤36month', 'not every LPR']:
                self.assertIn(phrase, text)
        check(core)
        for phrase in ['singular citizen', 'ONLY to the defined large-passenger-vessel', 'EXISTING≤36month']:
            bad = copy.deepcopy(core)
            bad['candidate_exact_action_meaning'] = bad['candidate_exact_action_meaning'].replace(phrase, 'all vessel crews')
            bad['action_core_sha256'] = sealed_digest(bad, 'action_core_sha256')
            with self.subTest(predicate=phrase), self.assertRaises(AssertionError):
                check(bad)

    def test_housing226_required_source_hold_never_becomes_completion(self):
        rows = {r['action_id']: r for r in self.values[2]['candidate_dispositions']}
        reviewed = {r['action_id'] for r in self.values[3]['records']}
        authored = {a['action_id'] for a in self.values[0]['actions']}
        june = rows['house:119:2:224']
        self.assertEqual(june['disposition'], 'source_unresolved')
        self.assertTrue(june['review_progress']['required_evidence_unavailable'])
        self.assertFalse(june['review_progress']['substantive_review_performed'])
        self.assertNotIn(june['action_id'], reviewed | authored)
        receipt = json.loads((DATA / 'housing_coastguard_screening_checkpoint226.json').read_text())
        self.assertEqual(receipt['receipt_sha256'], sealed_digest(receipt, 'receipt_sha256'))
        self.assertEqual(receipt['replacement_actions'], [])
        self.assertNotIn(june['action_id'], receipt['completed_candidate_action_ids'])
        self.assertEqual(receipt['blocked_action_ids'], ['house:119:2:228'])
        self.assertNotIn('house:119:2:228', reviewed | authored)
        self.assertIsNone(receipt['benchmark']['comparable_five_completion_average'])

    def test_spending224_qualification_conserves_shared_health_truth(self):
        old = json.loads((DATA.parent / 'house_119_health_20260916/generated/shared_action_core.json').read_text())
        originals = {c['action_id']: c for c in old['actions']}
        cores = {c['action_id']: c for c in self.products[0]['actions']}
        actions = {a['action_id']: a for a in self.values[0]['actions']}
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        witnesses = {
            'house:119:1:182': ['govinfo:EO12989-consolidated2024-224', 'govinfo:48cfr221802-policy2024-224', 'govinfo:48cfr221803-prescription2024-224', 'govinfo:48cfr5222254-verification2024-224'],
            'house:119:2:175': ['govinfo:EO12989-consolidated2024-224', 'govinfo:48cfr221803-prescription2024-224'],
            'house:119:1:212': ['govinfo:eo14167-asissued2025-224', 'govinfo:5usc5332-GS2024-224', 'govinfo:eo12333-qualified-part2-defs2024-224'],
            'house:119:2:205': ['govinfo:8usc1183a-2024-sponsor-affidavit', 'govinfo:pl119-21-farm-nutrition-current-law']}
        for aid, ids in witnesses.items():
            with self.subTest(action=aid):
                before, after, action = originals[aid], cores[aid], actions[aid]
                self.assertEqual(before['exact_action_identity'], after['exact_action_identity'])
                self.assertEqual(before['action_meaning_ref'], after['action_meaning_ref'])
                self.assertTrue(after['candidate_exact_action_meaning'].startswith(before['candidate_exact_action_meaning']))
                self.assertTrue(all(w in after['governed_source_identities'] for w in before['governed_source_identities']))
                self.assertTrue(set(before['candidate_shared_limitations']) <= set(after['candidate_shared_limitations']))
                self.assertEqual(action['candidate_core_qualification']['action_core_sha256'], before['action_core_sha256'])
                self.assertEqual(action['shared_core_reuse']['artifact_id'], 'shared-action-core:house:119:v20')
                self.assertEqual(after['meaning_contract_version'], 'source_qualified_candidate_augmentation_v1')
                self.assertEqual(after['action_core_sha256'], sealed_digest(after, 'action_core_sha256'))
                self.assertEqual(after['legislative_stage'], 'final_passage')
                self.assertEqual(after['package_component_boundary']['boundary_type'], 'whole_measure')
                self.assertFalse(re.search(r'Foushee|Massie|F000477|M001184', after['candidate_exact_action_meaning']))
                for sid in ids:
                    self.assertIn(sid, {w['source_id'] for w in after['governed_source_identities']})
                    self.assertTrue(any(c['source_id'] == sid and c['passage'] == sources[sid]['text'] for c in after['claim_source_map']))

    def _assert_spending224_material_predicates(self, records):
        required = {
            'house:119:1:182': ['Act-funded ANY SERVICES', 'BOTH unlawfully present', 'AND not eligible for healthcare', 'this Act,not all federal funds', 'asofJune24,2009'],
            'house:119:2:175': ['does NOT contain', 'FY2026H.R.3944section259', 'COLLECTING AND USING', 'asofJune24,2009'],
            'house:119:1:212': ['HIGHER of', 'whole section does not apply', 'employees inTurkey', '180days after enactment', "President's not-necessary/appropriate determination AND", "Secretary's report within30days", 'on-or-afterJune24,2009'],
            'house:119:2:205': ['funds under THAT HEADING', 'or create a new affidavit requirement for everySNAPrecipient', 'US-residence requirement AND', 'lawfulCOFA-resident alternatives', '45day nonresponse', '10year window', 'not silently treated as unchanged consolidated law']}
        for aid, fragments in required.items():
            for fragment in fragments:
                self.assertIn(fragment, records[aid]['rationale'])
        for aid in ['house:119:1:182', 'house:119:2:175']:
            for fragment in ['exceeding$150,000', 'less-than120day', 'COTS', 'nondelegable contracting-head waivers', 'assigned-worker-only', 'HSPD12 exemptions', 'exceed$3,500', 'interim excusal', 'not automatic guilt', 'permanent residence OR authorization']:
                self.assertIn(fragment, records[aid]['rationale'])

    def test_spending224_rejects_lost_scope_and_conjunctive_predicates(self):
        records = {r['action_id']: r for r in self.values[3]['records']}
        self._assert_spending224_material_predicates(records)
        for aid, before, after in [
            ('house:119:1:182', 'AND not eligible for healthcare', 'OR not eligible for healthcare'),
            ('house:119:2:175', 'does NOT contain', 'contains'),
            ('house:119:2:175', 'nondelegable contracting-head waivers', 'universal verification'),
            ('house:119:1:212', 'HIGHER of', 'LOWER of'),
            ('house:119:1:212', "Secretary's report within30days", 'automatic reassignment'),
            ('house:119:2:205', 'funds under THAT HEADING', 'all appropriated funds'),
            ('house:119:2:205', 'US-residence requirement AND', 'US-residence requirement OR')]:
            with self.subTest(action=aid, lost=before):
                wrong = copy.deepcopy(records)
                wrong[aid]['rationale'] = wrong[aid]['rationale'].replace(before, after)
                with self.assertRaises(AssertionError):
                    self._assert_spending224_material_predicates(wrong)

    def test_spending224_budget_noncounting_and_reconciled207_has_no_credit(self):
        rows = {r['action_id']: r for r in self.values[2]['candidate_dispositions']}
        records = {r['action_id']: r for r in self.values[3]['records']}
        self.assertEqual(records['house:119:2:143']['disposition'], 'procedural_context')
        self.assertTrue(records['house:119:2:143']['substantive_review_performed'])
        self.assertNotIn('house:119:2:143', {a['action_id'] for a in self.values[0]['actions']})
        self.assertIn('not a$70billion immigration appropriation', records['house:119:2:143']['rationale'])
        self.assertEqual(rows['house:119:2:207']['disposition'], 'source_unresolved')
        self.assertNotIn('house:119:2:207', records)
        self.assertTrue(rows['house:119:2:207']['review_progress']['source_application_relationship_unresolved'])
        receipt = json.loads((DATA / 'ordinary_spending_screening_checkpoint224.json').read_text())
        self.assertEqual(receipt['receipt_sha256'], sealed_digest(receipt, 'receipt_sha256'))
        self.assertEqual(len(receipt['completed_action_ids']), 5)
        self.assertEqual(receipt['counts_after']['pending'], 38)
        self.assertTrue(receipt['independent224_source_domain_review_pending'])

    def _assert_section412_printed_linkage225(self, text):
        for fragment in ['Section412(a)', 'Department of Defense IN THIS ACT',
                         'Subsection(b) expressly excepts', 'THIS SUBSECTION',
                         '(a)does not expressly refer to(c)', 'asofJune24,2009',
                         'do not definitively limit(a)to(c)']:
            self.assertIn(fragment, text)
        self.assertNotIn('Section412 separately restricts Act/otherwise-available', text)

    def test_section412_distinct_subsections_and_funding_scope_survive_resealed_prose(self):
        records = {r['action_id']: r for r in self.values[3]['records']}
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        for aid, sid in [('house:119:1:182', 'govinfo:hr3944eh'), ('house:119:2:175', 'govinfo:hr8469eh')]:
            source = sources[sid]['text'];lo = source.index('Sec. 412.');body = source[lo:source.index('Sec. 413.', lo)]
            self.assertIn('to the Department of Defense in this Act', body)
            self.assertIn('prohibition in subsection (a)', body)
            self.assertIn('An individual described in this subsection', body)
            self.assertNotIn('individual described in subsection (c)', body)
            self._assert_section412_printed_linkage225(records[aid]['rationale'])
            for old, wrong in [('Department of Defense IN THIS ACT', 'all available Department of Defense funds'),
                               ('THIS SUBSECTION', 'THIS SECTION'),
                               ('(a)does not expressly refer to(c)', '(a)is limited to(c)')]:
                with self.subTest(action=aid, dropped=old), self.assertRaises(AssertionError):
                    self._assert_section412_printed_linkage225(records[aid]['rationale'].replace(old, wrong))

    def _assert_8132_incorporated_sources225(self, core):
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        ids = ['govinfo:pl114-92-transfer-1034-225', 'govinfo:pl115-232-transfer-1035-225']
        for sid in ids:
            self.assertIn(sid, {w['source_id'] for w in core['operative_meaning_source_identities']})
            self.assertTrue(any(c['source_id'] == sid and c['passage'] == sources[sid]['text']
                                for c in core['claim_source_map']))
        for fragment in ['BOTH PL11492section1034 AND PL115232section1035',
                         'lawful UScourt/competent-tribunal-order exception', 'at least30days',
                         'asofOCTOBER1,2009', 'December31,2016', 'December31,2019',
                         'no silent date extension,revived country ban']:
            self.assertIn(fragment, core['candidate_exact_action_meaning'])

    def test_8132_requires_both_exact_incorporated_bodies_and_retains_dates_exceptions(self):
        core = next(c for c in self.products[0]['actions'] if c['action_id'] == 'house:119:1:212')
        self._assert_8132_incorporated_sources225(core)
        for sid in ['govinfo:pl114-92-transfer-1034-225', 'govinfo:pl115-232-transfer-1035-225']:
            bad = copy.deepcopy(core)
            bad['operative_meaning_source_identities'] = [w for w in bad['operative_meaning_source_identities'] if w['source_id'] != sid]
            bad['claim_source_map'] = [c for c in bad['claim_source_map'] if c['source_id'] != sid]
            bad['action_core_sha256'] = sealed_digest(bad, 'action_core_sha256')
            with self.subTest(missing=sid), self.assertRaises(AssertionError):
                self._assert_8132_incorporated_sources225(bad)
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        self.assertIn('not later than 30 days before', sources['govinfo:pl114-92-transfer-1034-225']['text'])
        self.assertIn('Except as provided in paragraph (2)', sources['govinfo:pl114-92-transfer-1034-225']['text'])
        self.assertIn('ending on December 31, 2019', sources['govinfo:pl115-232-transfer-1035-225']['text'])
        receipt = json.loads((DATA / 'review_corrections_checkpoint225.json').read_text())
        self.assertEqual(receipt['receipt_sha256'], sealed_digest(receipt, 'receipt_sha256'))
        self.assertTrue(receipt['previous224premature212completion_explicitly_superseded'])
        self.assertTrue(receipt['no_new_ordinary_completion'])

    def test_sponsor_benefit_coverage_is_distinct_from_reimbursement_action_window(self):
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        source = sources['govinfo:8usc1183a-2024-sponsor-affidavit']['text']
        self.assertIn('enforceable with respect to benefits provided', source)
        self.assertIn('10 years after the date on which the sponsored alien last received', source)
        text = next(r['rationale'] for r in self.values[3]['records'] if r['action_id'] == 'house:119:2:205')
        def assert_coverage(candidate):
            for phrase in ['benefits PROVIDED BEFORE', 'qualified(a)(3)forty-quarter termination date',
                           'accrued reimbursement claims are extinguished at naturalization',
                           'separate10year window measured from the last covered means-tested benefit,not from naturalization']:
                self.assertIn(phrase, candidate)
            self.assertIn('do not turn this benefit-coverage boundary into a conclusion', candidate)
            self.assertNotIn('Enforceability ends at naturalization', candidate)
        assert_coverage(text)
        wrong = text.replace('do not turn this benefit-coverage boundary into a conclusion',
                             'this benefit-coverage boundary establishes')
        with self.assertRaises(AssertionError):
            assert_coverage(wrong)
        wrong = text.replace('last covered means-tested benefit,not from naturalization', 'naturalization')
        with self.assertRaises(AssertionError):
            assert_coverage(wrong)

    def _assert_wilson252_source_scope(self, core):
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        memo = 'whitehouse:NSPM4-border-military20250411-223'
        self.assertIn(memo, {s['source_id'] for s in core['operative_meaning_source_identities']})
        self.assertTrue(any(c['source_id'] == memo and c['passage'] == sources[memo]['text']
                            for c in core['claim_source_map']))
        for text in ['50 U.S.C. 797', '18 U.S.C. 1382', 'excluding Federal Indian Reservations',
                     'in accordance with applicable law', 'availability of appropriations']:
            self.assertIn(text, sources[memo]['text'])
        self.assertEqual(core['legislative_stage'], 'amendment')
        self.assertEqual(core['package_component_boundary']['boundary_type'], 'exact_amendment')
        self.assertEqual(core['exact_question'], 'On Agreeing to the Amendment')
        for text in ['six months to two years', 'prohibited by law or lawful regulation',
                     'Secretary-designated', "Existing(a)'s willful misdemeanor",
                     'qualifying nonborder military property', 'not proof of final enactment']:
            self.assertIn(text, core['candidate_exact_action_meaning'])
        self.assertEqual([s['source_id'] for s in core['action_outcome_source_identities']],
                         ['clerk:119:1:252'])
        self.assertFalse(any(s['source_id'].startswith('immigration:wilson252-initial') or
                             s['source_id'].startswith('immigration:wilson252-resumed')
                             for s in core['operative_meaning_source_identities']))

    def test_wilson252_binds_the_exact_changed_authorities_and_preserves_conditions(self):
        core = next(c for c in self.products[0]['actions'] if c['action_id'] == 'house:119:1:252')
        self._assert_wilson252_source_scope(core)
        for member in self.products[2]:
            row = next(a for a in member['actions'] if a['action_id'] == core['action_id'])
            self.assertEqual(row['official_status'], {'F000477': 'Nay', 'M001184': 'Yea'}[member['member_id']])
            source = next(s for s in self.values[1]['sources'] if s['source_id'] == 'clerk:119:1:252')
            self.assertEqual(source['member_records'][member['member_id']]['official_label'],
                             {'F000477': 'No', 'M001184': 'Aye'}[member['member_id']])
            self.assertEqual(row['action_core_sha256'], core['action_core_sha256'])
        for defect in ['unbound memorandum', 'omitted claim', 'whole-passage stage', 'dropped lawful predicate']:
            bad = copy.deepcopy(core)
            if defect == 'unbound memorandum':
                bad['operative_meaning_source_identities'] = [w for w in bad['operative_meaning_source_identities']
                    if w['source_id'] != 'whitehouse:NSPM4-border-military20250411-223']
            elif defect == 'omitted claim':
                bad['claim_source_map'] = [c for c in bad['claim_source_map']
                    if c['source_id'] != 'whitehouse:NSPM4-border-military20250411-223']
            elif defect == 'whole-passage stage':
                bad['legislative_stage'] = 'final_passage'
            else:
                bad['candidate_exact_action_meaning'] = bad['candidate_exact_action_meaning'].replace(
                    'prohibited by law or lawful regulation', 'for any purpose')
            with self.subTest(defect=defect), self.assertRaises(AssertionError):
                self._assert_wilson252_source_scope(bad)

    def test_wilson252_two_day_sequence_and_four_open_cases_are_preserved(self):
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        initial = sources['immigration:wilson252-initial-question223']['text']
        self.assertLess(initial.index('question was taken'), initial.index('ayes'))
        self.assertLess(initial.index('ayes'), initial.index('I demand a recorded vote'))
        self.assertLess(initial.index('I demand a recorded vote'), initial.index('will be postponed'))
        self.assertNotIn('recorded vote was ordered', initial)
        resumed = sources['immigration:wilson252-resumed-recorded223']['text']
        self.assertIn('A recorded vote was ordered', resumed)
        self.assertIn('[Roll No. 252]', resumed)
        report = sources['govinfo:hrpt119-255-amend11']['text']
        offered = sources['immigration:wilson252-offered-body223']['text']
        normalize = lambda t: re.sub(r'[^a-z0-9]', '', re.sub(r'SEC\.\s*17\s*(?:_+|l+)',
            'SEC.17PLACEHOLDER', t).casefold())
        self.assertEqual(normalize(report[report.index('At the end of'):]), normalize(offered))
        receipt = json.loads((DATA / 'security_status_source_preparation_checkpoint223.json').read_text())
        self.assertEqual(receipt['receipt_sha256'], sealed_digest(receipt, 'receipt_sha256'))
        self.assertEqual(receipt['completed_action_ids'], ['house:119:1:252'])
        records = {r['action_id']: r for r in self.values[3]['records']}
        rows = {r['action_id']: r for r in self.values[2]['candidate_dispositions']}
        for item in receipt['remaining_selected_actions']:
            self.assertEqual(item['completion_credit'], 0)
            self.assertNotIn(item['action_id'], records)
            self.assertEqual(rows[item['action_id']]['disposition'], 'source_unresolved')

    def test_modern_candidate_qualification_preserves_Health_core_and_whole_CCDF_boundaries(self):
        from pathlib import Path
        original = json.loads((DATA.parent / 'house_119_health_20260916/generated/shared_action_core.json').read_text(encoding='utf-8'))
        old = next(a for a in original['actions'] if a['action_id'] == 'house:119:2:198')
        current = next(a for a in self.products[0]['actions'] if a['action_id'] == old['action_id'])
        self.assertEqual(old['action_core_sha256'], 'ee36a3279d5424a837efe5251202b1e5c050cc2963e0b6e45ce93155103b8702')
        self.assertEqual(current['action_meaning_ref'], old['action_meaning_ref'])
        self.assertEqual(current['exact_action_identity'], old['exact_action_identity'])
        self.assertTrue(current['candidate_exact_action_meaning'].startswith(old['candidate_exact_action_meaning']))
        self.assertTrue(set(old['candidate_shared_limitations']) <= set(current['candidate_shared_limitations']))
        for text in ['description of existing eligibility-documentation and verification procedures',
                     'not substantive benefit-eligibility clearance', 'does not formally revise',
                     'No new citizenship criterion', 'not a separate verification component stance']:
            self.assertIn(text, current['candidate_exact_action_meaning'])
        self.assertEqual(current['semantic_ir_source_ids'], [s['source_id'] for s in current['governed_source_identities']])
        self.assertEqual(current['package_component_boundary']['boundary_type'], 'whole_measure')
        expected = {'F000477': 'Nay', 'M001184': 'Yea'}
        for member in self.products[2]:
            row = next(a for a in member['actions'] if a['action_id'] == old['action_id'])
            self.assertEqual(row['official_status'], expected[member['member_id']])
            self.assertEqual(row['action_core_sha256'], current['action_core_sha256'])
            self.assertEqual(row['member_action_source_identities'], current['action_outcome_source_identities'])

    def _assert_CCDF_retained_source_to_claim_boundaries(self, core, authoring):
        sources = {r['source_id']: r for r in self.values[1]['sources']}
        required = ['govinfo:45cfr98-20-2025-187', 'govinfo:45cfr98-68-2025-187',
                    'ecfr:45cfr98-20-version-history187', 'ecfr:45cfr98-68-version-history187']
        from scripts.prepare_shared_domain_candidate import identity
        for sid in required:
            self.assertIn(identity(sources[sid]), core['operative_meaning_source_identities'])
            self.assertIn(sid, core['semantic_ir_source_ids'])
            self.assertTrue(any(c['source_id'] == sid and c['passage'] == sources[sid]['text']
                                for c in core['claim_source_map']))
        for text in ["only the child's citizenship and immigration status is relevant",
                     "may not condition the child's eligibility for services under 98.50",
                     "parent's citizenship or immigration status or provision of any information",
                     '98.68 already requires analogous Plan descriptions',
                     'not errors or improper payments because of family-circumstance changes',
                     'amounts owed to providers under payment agreements',
                     'annual edition is dated October 1, 2025',
                     'Requested June 3, 2026 XML snapshots returned HTTP 406']:
            self.assertIn(text, core['candidate_exact_action_meaning'])
            self.assertIn(text, authoring['source_render_constraints'][0]['detail'])

    def test_CCDF_current_candidate_retains_complete_regulatory_source_claim_and_typed_bounds(self):
        action = next(r for r in self.values[0]['actions'] if r['action_id'] == 'house:119:2:198')
        core = next(r for r in self.products[0]['actions'] if r['action_id'] == action['action_id'])
        self._assert_CCDF_retained_source_to_claim_boundaries(core, action)
        constraints = self.products[3]['shared_semantics']['source_render_constraints']
        self.assertIn(action['source_render_constraints'][0], constraints)
        self.assertEqual(len(core['governed_source_identities']), 21)

    def test_CCDF_source_to_claim_regression_detects_historical209_and_each_missing_boundary(self):
        from pathlib import Path
        old = json.loads((DATA.parent / 'house_119_ccdf_qualification_checkpoint209/shared_action_core_proposal.json').read_text(encoding='utf-8'))['actions'][0]
        action = next(r for r in self.values[0]['actions'] if r['action_id'] == old['action_id'])
        with self.assertRaises(AssertionError):
            self._assert_CCDF_retained_source_to_claim_boundaries(old, action)
        current = next(r for r in self.products[0]['actions'] if r['action_id'] == old['action_id'])
        for case in ['full section', 'history', 'claim map', 'parent information', 'existing plan', 'typed constraint']:
            with self.subTest(case=case):
                core, row = copy.deepcopy(current), copy.deepcopy(action)
                if case == 'full section':
                    core['operative_meaning_source_identities'] = [r for r in core['operative_meaning_source_identities'] if r['source_id'] != 'govinfo:45cfr98-20-2025-187']
                elif case == 'history':
                    core['semantic_ir_source_ids'].remove('ecfr:45cfr98-68-version-history187')
                elif case == 'claim map':
                    core['claim_source_map'] = [r for r in core['claim_source_map'] if r['source_id'] != 'govinfo:45cfr98-68-2025-187']
                elif case == 'parent information':
                    core['candidate_exact_action_meaning'] = core['candidate_exact_action_meaning'].replace('or provision of any information about that status', '')
                elif case == 'existing plan':
                    core['candidate_exact_action_meaning'] = core['candidate_exact_action_meaning'].replace('98.68 already requires analogous Plan descriptions', 'new unspecified descriptions')
                else:
                    row['source_render_constraints'][0]['detail'] = 'No universal parent check.'
                with self.assertRaises(AssertionError):
                    self._assert_CCDF_retained_source_to_claim_boundaries(core, row)

    def test_modern_candidate_qualification_rejects_missing_stale_or_changed_original_bindings(self):
        for case in ['missing', 'wrong seal', 'wrong artifact', 'wrong primary', 'original limit removed']:
            with self.subTest(case=case):
                authoring = copy.deepcopy(self.values[0])
                row = next(r for r in authoring['actions'] if r['action_id'] == 'house:119:2:198')
                if case == 'missing':
                    row.pop('candidate_core_qualification')
                elif case == 'wrong seal':
                    row['candidate_core_qualification']['action_core_sha256'] = '0' * 64
                elif case == 'wrong artifact':
                    row['candidate_core_qualification']['artifact_id'] = 'shared-action-core:house:119:v1'
                elif case == 'wrong primary':
                    row['source_id'] = 'govinfo:hr5334eh'
                else:
                    row['limitations'].pop(0)
                with self.assertRaises(ValueError):
                    prepare(authoring, self.values[1], ['F000477', 'M001184'])

    def test_modern_candidate_qualification_rejects_fully_resealed_wrapper_and_basis_drift(self):
        from pathlib import Path
        from unittest.mock import patch
        original_read = Path.read_text
        binding = next(r for r in self.values[0]['actions'] if r['action_id'] == 'house:119:2:198')['shared_core_reuse']
        path = Path(binding['artifact_ref']).resolve()
        for case in ['component', 'compiler sources', 'original prefix', 'meaning reference', 'question']:
            with self.subTest(case=case):
                provider = json.loads(original_read(path, encoding='utf-8'))
                current = provider['actions'][0]
                authoring = copy.deepcopy(self.values[0])
                row = next(r for r in authoring['actions'] if r['action_id'] == current['action_id'])
                if case == 'component':
                    current['package_component_boundary']['boundary_type'] = 'exact_amendment'
                elif case == 'compiler sources':
                    current['semantic_ir_source_ids'] = ['clerk:119:2:198']
                elif case == 'original prefix':
                    current['candidate_exact_action_meaning'] = current['candidate_exact_action_meaning'].replace('covered child-care block-grant withholding authority mandatory', 'all benefits automatically inaccessible', 1)
                    current['mechanism'] = current['candidate_exact_action_meaning']
                    row['meaning'] = current['candidate_exact_action_meaning']
                elif case == 'meaning reference':
                    current['action_meaning_ref'] = 'unreviewed:replacement:house:119:2:198:v9'
                    row['shared_core_reuse']['action_meaning_ref'] = current['action_meaning_ref']
                else:
                    current['exact_question'] = 'On Passage of the verification clause only'
                current['action_core_sha256'] = sealed_digest(current, 'action_core_sha256')
                provider['corpus_sha256'] = digest(provider['actions'])
                row['shared_core_reuse']['action_core_sha256'] = current['action_core_sha256']
                def read_provider(target, *args, **kwargs):
                    return json.dumps(provider) if target.resolve() == path else original_read(target, *args, **kwargs)
                with patch.object(Path, 'read_text', new=read_provider):
                    with self.assertRaises(ValueError):
                        prepare(authoring, self.values[1], ['F000477', 'M001184'])

    def test_legacy_ES_candidate_preserves_frozen_ambiguity_and_binds_separate_current_sources(self):
        from pathlib import Path
        original = json.loads((DATA.parents[1] / 'shared_corpora/house_119_v2/shared_action_core.json').read_text(encoding='utf-8'))
        old = next(a for a in original['actions'] if a['action_id'] == 'house:119:2:155')
        current = next(a for a in self.products[0]['actions'] if a['action_id'] == old['action_id'])
        row = next(r for r in self.values[0]['actions'] if r['action_id'] == old['action_id'])
        conflict = row['legacy_core_qualification']['preserved_metadata_conflict']
        self.assertEqual(old['action_core_sha256'], '980d0ab08ded521f6976b4109e35f041a41943080920e0a2b668d3b682eaa3a0')
        self.assertEqual(current['action_meaning_ref'], old['action_meaning_ref'])
        self.assertEqual(current['exact_action_identity'], '119:s:4465')
        self.assertTrue(current['candidate_exact_action_meaning'].startswith(old['accepted_exact_action_meaning']))
        self.assertIn('kept ambiguous', current['candidate_exact_action_meaning'])
        self.assertTrue(conflict['original_title'].startswith('110 S4465 ES:'))
        self.assertIn(conflict['qualification'], current['candidate_exact_action_meaning'])
        self.assertIn(conflict['qualification'], current['candidate_shared_limitations'])
        self.assertEqual(current['chamber_outcome'], 'Passed')
        self.assertEqual(current['enactment_status'], 'not_inferred_from_house_outcome')
        self.assertNotIn('govinfo:pl11987-qualified182', current['semantic_ir_source_ids'])
        self.assertEqual(current['semantic_ir_source_ids'], [s['source_id'] for s in current['governed_source_identities']])
        self.assertEqual([s['source_id'] for s in current['action_outcome_source_identities']],
                         ['clerk:119:2:155', 'immigration:roll155-recorded182'])
        for member in self.products[2]:
            projection = next(a for a in member['actions'] if a['action_id'] == old['action_id'])
            self.assertEqual(projection['official_status'], 'Nay')
            self.assertEqual(projection['action_core_sha256'], current['action_core_sha256'])
            self.assertEqual(projection['member_action_source_identities'], current['action_outcome_source_identities'])

    def test_legacy_ES_candidate_rejects_missing_conflict_or_separate_source_bindings(self):
        for case in ['missing conflict', 'wrong title', 'wrong qualification', 'missing offered', 'missing recorded']:
            with self.subTest(case=case):
                authoring = copy.deepcopy(self.values[0])
                row = next(r for r in authoring['actions'] if r['action_id'] == 'house:119:2:155')
                binding = row['legacy_core_qualification']
                if case == 'missing conflict':
                    binding.pop('preserved_metadata_conflict')
                elif case == 'wrong title':
                    binding['preserved_metadata_conflict']['original_title'] = '119 S4465 ES: repaired title'
                elif case == 'wrong qualification':
                    binding['preserved_metadata_conflict']['qualification'] = 'Old ambiguity resolved automatically.'
                elif case == 'missing offered':
                    row['additional_source_ids'].remove('immigration:roll155-operative182')
                else:
                    row['additional_action_outcome_source_ids'] = []
                with self.assertRaises(ValueError):
                    prepare(authoring, self.values[1], ['F000477', 'M001184'])

    def test_legacy_ES_candidate_rejects_fully_resealed_qualification_and_wrapper_drift(self):
        from pathlib import Path
        from unittest.mock import patch
        original_read = Path.read_text
        path = (DATA.parent / 'house_119_legacy_es_fisa_qualification_checkpoint208/shared_action_core_proposal.json').resolve()
        for case in ['accepted prefix', 'historical qualification', 'component', 'compiler sources', 'question', 'version']:
            with self.subTest(case=case):
                provider = json.loads(original_read(path, encoding='utf-8'))
                current = provider['actions'][0]
                authoring = copy.deepcopy(self.values[0])
                row = next(r for r in authoring['actions'] if r['action_id'] == current['action_id'])
                if case == 'accepted prefix':
                    current['candidate_exact_action_meaning'] = current['candidate_exact_action_meaning'].replace('The action is kept ambiguous', 'The action is automatically cleared', 1)
                    current['mechanism'] = current['candidate_exact_action_meaning']
                    row['meaning'] = current['candidate_exact_action_meaning']
                elif case == 'historical qualification':
                    qualification = row['legacy_core_qualification']['preserved_metadata_conflict']['qualification']
                    current['candidate_exact_action_meaning'] = current['candidate_exact_action_meaning'].replace(qualification, '')
                    current['candidate_shared_limitations'].remove(qualification)
                    current['mechanism'] = current['candidate_exact_action_meaning']
                    row['meaning'] = current['candidate_exact_action_meaning']
                    row['limitations'] = current['candidate_shared_limitations']
                elif case == 'component':
                    current['package_component_boundary']['boundary_type'] = 'exact_amendment'
                elif case == 'compiler sources':
                    current['semantic_ir_source_ids'] = ['clerk:119:2:155']
                elif case == 'question':
                    current['exact_question'] = 'On Motion to Suspend the Rules and Pass paragraph (1) only'
                else:
                    for field in ['governed_source_identities', 'operative_meaning_source_identities']:
                        next(s for s in current[field] if s['source_id'] == row['source_id'])['text_version'] = 'EH'
                    current['governed_source_identity_sha256'] = digest(current['governed_source_identities'])
                current['action_core_sha256'] = sealed_digest(current, 'action_core_sha256')
                provider['corpus_sha256'] = digest(provider['actions'])
                row['shared_core_reuse']['action_core_sha256'] = current['action_core_sha256']
                def read_provider(target, *args, **kwargs):
                    return json.dumps(provider) if target.resolve() == path else original_read(target, *args, **kwargs)
                with patch.object(Path, 'read_text', new=read_provider):
                    with self.assertRaises(ValueError):
                        prepare(authoring, self.values[1], ['F000477', 'M001184'])

    def test_qualified_wrappers_reject_resealed_component_and_compiler_source_changes(self):
        from pathlib import Path
        from unittest.mock import patch
        original_read = Path.read_text
        for aid, provider_folder in [('house:119:2:221', 'house_119_legacy_fisa_qualification_checkpoint206'),
                                     ('house:119:2:142', 'house_119_source_review_checkpoint204')]:
            path = (DATA.parent / provider_folder / 'shared_action_core_proposal.json').resolve()
            cases = ['wrong component', 'Clerk-only sources', 'missing own Record sources', 'reordered sources']
            if aid.endswith(':142'):
                cases.append('wrong meaning contract')
            for case in cases:
                with self.subTest(action=aid, case=case):
                    provider = json.loads(original_read(path, encoding='utf-8'))
                    current = provider['actions'][0]
                    authoring = copy.deepcopy(self.values[0])
                    row = next(r for r in authoring['actions'] if r['action_id'] == aid)
                    if case == 'wrong component':
                        current['package_component_boundary']['boundary_type'] = 'exact_amendment'
                        rejected_field = 'package_component_boundary'
                    elif case == 'Clerk-only sources':
                        current['semantic_ir_source_ids'] = ['clerk:' + aid.removeprefix('house:')]
                        rejected_field = 'semantic_ir_source_ids'
                    elif case == 'missing own Record sources':
                        current['semantic_ir_source_ids'] = (
                            [sid for sid in current['semantic_ir_source_ids']
                             if sid not in row['additional_action_outcome_source_ids']]
                            if aid.endswith(':221') else current['semantic_ir_source_ids'][1:])
                        rejected_field = 'semantic_ir_source_ids'
                    elif case == 'wrong meaning contract':
                        current['meaning_contract_version'] = 'source_review184_unbound_contract_v99'
                        rejected_field = 'meaning_contract_version'
                    else:
                        current['semantic_ir_source_ids'].reverse()
                        rejected_field = 'semantic_ir_source_ids'
                    current['action_core_sha256'] = sealed_digest(current, 'action_core_sha256')
                    provider['corpus_sha256'] = digest(provider['actions'])
                    row['shared_core_reuse']['action_core_sha256'] = current['action_core_sha256']
                    def read_provider(target, *args, **kwargs):
                        return json.dumps(provider) if target.resolve() == path else original_read(target, *args, **kwargs)
                    with patch.object(Path, 'read_text', new=read_provider):
                        with self.assertRaisesRegex(ValueError, 'complete exact Clerk-bound wrapper: ' + rejected_field):
                            prepare(authoring, self.values[1], ['F000477', 'M001184'])

    def test_qualified_wrappers_retain_all_bound_own_Record_compiler_sources(self):
        for aid, expected_boundary in [('house:119:2:221', 'whole_measure'),
                                       ('house:119:2:142', 'whole_FISA_substitute_before_separate_rule8_engrossment_addition')]:
            with self.subTest(action=aid):
                row = next(r for r in self.values[0]['actions'] if r['action_id'] == aid)
                current = next(a for a in self.products[0]['actions'] if a['action_id'] == aid)
                outcome_ids = ['clerk:' + aid.removeprefix('house:'), *row['additional_action_outcome_source_ids']]
                operative_ids = [row['source_id'], *row['additional_source_ids']]
                expected = [*outcome_ids, *operative_ids] if aid.endswith(':221') else operative_ids
                self.assertEqual(current['semantic_ir_source_ids'], expected)
                self.assertEqual([s['source_id'] for s in current['governed_source_identities']],
                                 [*outcome_ids, *operative_ids])
                self.assertEqual(current['package_component_boundary']['boundary_type'], expected_boundary)
                compiler_action = next(a for a in self.products[3]['shared_semantics']['actions']
                                       if a['action_id'] == aid)
                self.assertEqual(compiler_action['source_ids'], expected)
                for member in self.products[2]:
                    projection = next(a for a in member['actions'] if a['action_id'] == aid)
                    self.assertEqual(projection['action_core_sha256'], current['action_core_sha256'])
                    self.assertEqual(projection['member_action_source_identities'], current['action_outcome_source_identities'])

    def test_source_review_preserved_wrapper_binding_rejects_missing_stale_or_self_reference(self):
        for case in ['missing', 'wrong seal', 'wrong artifact', 'self reference']:
            with self.subTest(case=case):
                authoring = copy.deepcopy(self.values[0])
                row = next(r for r in authoring['actions'] if r['action_id'] == 'house:119:2:142')
                if case == 'missing':
                    row.pop('source_review_wrapper_binding')
                elif case == 'wrong seal':
                    row['source_review_wrapper_binding']['action_core_sha256'] = '0' * 64
                elif case == 'wrong artifact':
                    row['source_review_wrapper_binding']['artifact_id'] = 'shared-action-core:house:119:v1'
                else:
                    row['source_review_wrapper_binding'] = {k: row['shared_core_reuse'][k]
                                                           for k in ['artifact_ref', 'artifact_id', 'action_core_sha256']}
                with self.assertRaisesRegex(ValueError, 'typed.wrapper|typed-wrapper'):
                    prepare(authoring, self.values[1], ['F000477', 'M001184'])

    def test_legacy_fisa_qualification_preserves_identity_and_shares_one_current_core(self):
        original = json.loads((DATA.parents[1] / 'shared_corpora/house_119_v2/shared_action_core.json').read_text(encoding='utf-8'))
        old = next(a for a in original['actions'] if a['action_id'] == 'house:119:2:221')
        current = next(a for a in self.products[0]['actions'] if a['action_id'] == old['action_id'])
        self.assertEqual(old['action_core_sha256'], 'a751b1593c5dbbeca206cf27f4c1fba8918829bb219adf97e3a059bc6aa74a42')
        self.assertEqual(current['action_meaning_ref'], old['action_meaning_ref'])
        self.assertEqual(current['exact_action_identity'], old['exact_action_identity'])
        self.assertTrue(current['candidate_exact_action_meaning'].startswith(old['accepted_exact_action_meaning']))
        self.assertTrue(set(old['accepted_shared_limitations']) <= set(current['candidate_shared_limitations']))
        self.assertNotEqual(current['action_core_sha256'], old['action_core_sha256'])
        self.assertNotEqual(current['governed_source_identity_sha256'], old['governed_source_identity_sha256'])
        self.assertEqual(current['exact_question'], 'On Motion to Suspend the Rules and Pass')
        self.assertEqual(current['chamber_outcome'], 'Failed')
        self.assertEqual(current['legislative_stage'], 'suspension_and_passage')
        for member in self.products[2]:
            row = next(r for r in member['actions'] if r['action_id'] == old['action_id'])
            self.assertEqual(row['official_status'], 'Nay')
            self.assertEqual(row['action_core_sha256'], current['action_core_sha256'])
            self.assertEqual(row['member_action_source_identities'], current['action_outcome_source_identities'])
            self.assertEqual(len(row['member_action_source_identities']), 3)
        self.assertFalse(self.products[0]['authoritative_for_new_editorial_work'])

    def test_legacy_fisa_qualification_rejects_changed_original_and_role_bindings(self):
        for case in ['old seal', 'old artifact', 'missing frozen source', 'wrong raw XML',
                     'missing own outcome', 'wrong stage']:
            with self.subTest(case=case):
                authoring = copy.deepcopy(self.values[0])
                row = next(r for r in authoring['actions'] if r['action_id'] == 'house:119:2:221')
                binding = row['legacy_core_qualification']
                if case == 'old seal':
                    binding['action_core_sha256'] = '0' * 64
                elif case == 'old artifact':
                    binding['artifact_id'] = 'shared-action-core:house:119:v1'
                elif case == 'missing frozen source':
                    binding['source_bindings'].pop()
                elif case == 'wrong raw XML':
                    binding['source_bindings'][1]['raw_ref'] = binding['source_bindings'][0]['raw_ref']
                elif case == 'missing own outcome':
                    row['additional_action_outcome_source_ids'] = []
                else:
                    row['stage'] = 'final_passage'
                with self.assertRaises(ValueError):
                    prepare(authoring, self.values[1], ['F000477', 'M001184'])

    def test_legacy_fisa_qualification_rejects_resealed_question_version_and_basis_changes(self):
        from pathlib import Path
        from unittest.mock import patch
        original_read = Path.read_text
        path = (DATA.parent / 'house_119_legacy_fisa_qualification_checkpoint206/shared_action_core_proposal.json').resolve()
        for case in ['wrong bill question', 'component question', 'source version', 'accepted prefix']:
            with self.subTest(case=case):
                provider = json.loads(original_read(path, encoding='utf-8'))
                current = provider['actions'][0]
                authoring = copy.deepcopy(self.values[0])
                row = next(r for r in authoring['actions'] if r['action_id'] == current['action_id'])
                if case == 'wrong bill question':
                    current['exact_question'] = 'On Motion to Suspend the Rules and Pass H.R.4465'
                elif case == 'component question':
                    current['exact_question'] = 'On Motion to Suspend the Rules and Pass only paragraph (1) of H.R.9238'
                elif case == 'source version':
                    for field in ['governed_source_identities', 'operative_meaning_source_identities']:
                        next(s for s in current[field] if s['source_id'] == row['source_id'])['text_version'] = 'unreviewed EH version'
                    current['governed_source_identity_sha256'] = digest(current['governed_source_identities'])
                else:
                    current['candidate_exact_action_meaning'] = current['candidate_exact_action_meaning'].replace('July 2, 2026', 'July 3, 2026', 1)
                    current['mechanism'] = current['candidate_exact_action_meaning']
                    row['meaning'] = current['candidate_exact_action_meaning']
                current['action_core_sha256'] = sealed_digest(current, 'action_core_sha256')
                provider['corpus_sha256'] = digest(provider['actions'])
                row['shared_core_reuse']['action_core_sha256'] = current['action_core_sha256']
                def read_provider(target, *args, **kwargs):
                    return json.dumps(provider) if target.resolve() == path else original_read(target, *args, **kwargs)
                with patch.object(Path, 'read_text', new=read_provider):
                    with self.assertRaises(ValueError):
                        prepare(authoring, self.values[1], ['F000477', 'M001184'])

    def test_legacy_fisa_qualification_rejects_resealed_capture_operator_and_total_drift(self):
        from pathlib import Path
        from unittest.mock import patch
        from scripts.prepare_shared_domain_candidate import identity
        original_read = Path.read_text
        path = (DATA.parent / 'house_119_legacy_fisa_qualification_checkpoint206/shared_action_core_proposal.json').resolve()
        for case in ['repeal operator', 'party total']:
            with self.subTest(case=case):
                provider = json.loads(original_read(path, encoding='utf-8'))
                current = provider['actions'][0]
                authoring = copy.deepcopy(self.values[0])
                row = next(r for r in authoring['actions'] if r['action_id'] == current['action_id'])
                capture = copy.deepcopy(self.values[1])
                sid = row['source_id'] if case == 'repeal operator' else 'clerk:119:2:221'
                source = next(s for s in capture['sources'] if s['source_id'] == sid)
                if case == 'repeal operator':
                    source['text'] = source['text'].replace('July 2, 2026', 'August 2, 2026')
                    for claim in current['claim_source_map']:
                        if claim['source_id'] == sid:
                            claim['passage'] = source['text']
                    row['claim_source_map'] = copy.deepcopy(current['claim_source_map'])
                else:
                    source['party_totals'][0]['yea-total'] = '191'
                source['governed_bytes_sha256'] = digest({k: v for k, v in source.items() if k != 'governed_bytes_sha256'})
                for field in ['governed_source_identities', 'operative_meaning_source_identities', 'action_outcome_source_identities']:
                    current[field] = [identity(source) if s['source_id'] == sid else s for s in current[field]]
                current['governed_source_identity_sha256'] = digest(current['governed_source_identities'])
                current['action_core_sha256'] = sealed_digest(current, 'action_core_sha256')
                provider['corpus_sha256'] = digest(provider['actions'])
                row['shared_core_reuse']['action_core_sha256'] = current['action_core_sha256']
                def read_provider(target, *args, **kwargs):
                    return json.dumps(provider) if target.resolve() == path else original_read(target, *args, **kwargs)
                with patch.object(Path, 'read_text', new=read_provider):
                    with self.assertRaisesRegex(ValueError, 'literal repeal operator|party totals differ'):
                        prepare(authoring, capture, ['F000477', 'M001184'])

    def test_legacy_fisa_qualified_choice_retains_vetting_and_failed_whole_motion_limits(self):
        from scripts.validate_source_sequence import require_source_sequence
        row = next(r for r in self.values[0]['actions'] if r['action_id'] == 'house:119:2:221')
        for text in ['procedures enable vetting all non-US persons',
                     'not a mandate to conduct every individual query',
                     'Non-US-person is not equivalent to unauthorized immigrant',
                     'ninety-day transition is tied to 2008 enactment',
                     'failed House choice establishes no enactment']:
            self.assertIn(text, row['meaning'])
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        require_source_sequence(sources['immigration:roll221-initial182']['text'],
                                ['question is on the motion', 'The question was taken',
                                 'two-thirds being in the affirmative', 'demand the yeas and nays',
                                 'The yeas and nays were ordered', 'will be postponed'])
        require_source_sequence(sources['immigration:roll221-recorded182']['text'],
                                ['unfinished business', 'question is on the motion',
                                 'vote was taken by electronic device',
                                 'yeas 198, nays 218, not voting 15', 'motion was rejected'])

    def test_source_review_question_rejects_coherently_resealed_wrong_whole_choice(self):
        from pathlib import Path
        from unittest.mock import patch
        original_read = Path.read_text
        path = (DATA.parent / 'house_119_source_review_checkpoint204/shared_action_core_proposal.json').resolve()
        for question in [
                'On passage of H.R.4465 as amended by the substitute adopted under H.Res.1224 section7.',
                'On passage of the amendment to S.1318 only.',
                'On passage of S.1318 as amended by the substitute adopted under H.Res.1224 section8.']:
            with self.subTest(question=question):
                provider = json.loads(original_read(path, encoding='utf-8'))
                core = provider['actions'][0]
                core['exact_question'] = question
                core['action_core_sha256'] = sealed_digest(core, 'action_core_sha256')
                provider['corpus_sha256'] = digest(provider['actions'])
                authoring = copy.deepcopy(self.values[0])
                row = next(r for r in authoring['actions'] if r['action_id'] == core['action_id'])
                row['shared_core_reuse']['action_core_sha256'] = core['action_core_sha256']
                def read_provider(target, *args, **kwargs):
                    return json.dumps(provider) if target.resolve() == path else original_read(target, *args, **kwargs)
                with patch.object(Path, 'read_text', new=read_provider):
                    with self.assertRaisesRegex(ValueError, 'exact-action wrapper'):
                        prepare(authoring, self.values[1], ['F000477', 'M001184'])

    def test_source_review_question_binds_rule_section_and_normalizes_labels(self):
        from pathlib import Path
        from unittest.mock import patch
        original_read = Path.read_text
        path = (DATA.parent / 'house_119_source_review_checkpoint204/shared_action_core_proposal.json').resolve()
        provider = json.loads(original_read(path, encoding='utf-8'))
        core = provider['actions'][0]
        core['exact_question'] = '  ON PASSAGE OF S. 1318 as amended by the substitute adopted under H. Res. 1224 section 7.  '
        core['action_core_sha256'] = sealed_digest(core, 'action_core_sha256')
        provider['corpus_sha256'] = digest(provider['actions'])
        authoring = copy.deepcopy(self.values[0])
        row = next(r for r in authoring['actions'] if r['action_id'] == core['action_id'])
        row['shared_core_reuse']['action_core_sha256'] = core['action_core_sha256']
        def read_provider(target, *args, **kwargs):
            return json.dumps(provider) if target.resolve() == path else original_read(target, *args, **kwargs)
        with patch.object(Path, 'read_text', new=read_provider):
            result = prepare(authoring, self.values[1], ['F000477', 'M001184'])
        self.assertEqual(next(r for r in result[0]['actions'] if r['action_id'] == core['action_id']), core)
        for section in [8, 6]:
            authoring = copy.deepcopy(self.values[0])
            row = next(r for r in authoring['actions'] if r['action_id'] == core['action_id'])
            row['source_review_question_binding']['section'] = section
            with self.assertRaises(ValueError):
                prepare(authoring, self.values[1], ['F000477', 'M001184'])

    def test_source_review_reuse_preserves_one_qualified_fisa_identity_and_outcome_set(self):
        aid = 'house:119:2:142'
        original = json.loads((DATA.parent / 'house_119_source_review_checkpoint182/shared_action_core_proposal.json').read_text(encoding='utf-8'))['actions'][0]
        current = json.loads((DATA.parent / 'house_119_source_review_checkpoint204/shared_action_core_proposal.json').read_text(encoding='utf-8'))['actions'][0]
        actual = next(a for a in self.products[0]['actions'] if a['action_id'] == aid)
        self.assertEqual(actual, current)
        self.assertEqual(current['action_meaning_ref'], original['action_meaning_ref'])
        self.assertEqual(current['exact_action_identity'], original['exact_action_identity'])
        self.assertEqual(current['governed_source_identity_sha256'], original['governed_source_identity_sha256'])
        self.assertNotEqual(current['action_core_sha256'], original['action_core_sha256'])
        self.assertEqual(original['action_core_sha256'], '6a8446c7a300280620c971039b7234c073185a2be8f61eff858fdb722276342a')
        for member in self.products[2]:
            row = next(r for r in member['actions'] if r['action_id'] == aid)
            self.assertEqual(row['official_status'], 'Nay')
            self.assertEqual(row['action_core_sha256'], current['action_core_sha256'])
            self.assertEqual(row['member_action_source_identities'], current['action_outcome_source_identities'])
            self.assertEqual([s['source_id'] for s in row['member_action_source_identities']],
                             ['clerk:119:2:142', 'immigration:roll142-recorded181'])
        mapping = next(r for r in self.products[1]['action_mappings'] if r['action_id'] == aid)
        self.assertEqual(mapping['eligibility']['decision'], 'proposed')
        self.assertFalse(self.products[0]['authoritative_for_new_editorial_work'])

    def test_source_review_reuse_rejects_stale_or_changed_candidate_input(self):
        aid = 'house:119:2:142'
        for label in ['stale seal', 'missing outcome', 'wrong outcome role', 'changed meaning', 'wrong stage']:
            with self.subTest(case=label):
                a = copy.deepcopy(self.values[0])
                row = next(r for r in a['actions'] if r['action_id'] == aid)
                if label == 'stale seal':
                    row['shared_core_reuse']['action_core_sha256'] = '0' * 64
                elif label == 'missing outcome':
                    row['additional_action_outcome_source_ids'] = []
                elif label == 'wrong outcome role':
                    row['additional_action_outcome_source_ids'] = [row['source_id']]
                elif label == 'changed meaning':
                    row['meaning'] += ' Every traveler must be queried.'
                else:
                    row['stage'] = 'suspension_and_passage'
                with self.assertRaises(ValueError):
                    prepare(a, self.values[1], ['F000477', 'M001184'])

    def test_source_review_reuse_rejects_resealed_authority_source_and_question_changes(self):
        from pathlib import Path
        from unittest.mock import patch
        aid = 'house:119:2:142'
        original_read = Path.read_text
        path = (DATA.parent / 'house_119_source_review_checkpoint204/shared_action_core_proposal.json').resolve()
        for label in ['authority', 'source version', 'measure', 'question']:
            with self.subTest(case=label):
                provider = json.loads(original_read(path, encoding='utf-8'))
                current = provider['actions'][0]
                a = copy.deepcopy(self.values[0])
                row = next(r for r in a['actions'] if r['action_id'] == aid)
                if label == 'authority':
                    provider['authoritative_for_new_editorial_work'] = True
                elif label == 'source version':
                    for field in ['governed_source_identities', 'operative_meaning_source_identities']:
                        next(s for s in current[field] if s['source_id'] == row['source_id'])['text_version'] = 'unreviewed substitute version'
                    current['governed_source_identity_sha256'] = digest(current['governed_source_identities'])
                elif label == 'measure':
                    current['exact_action_identity'] = '119:s:4465'
                else:
                    current['exact_question'] = 'On Agreeing to the Amendment'
                current['action_core_sha256'] = sealed_digest(current, 'action_core_sha256')
                provider['corpus_sha256'] = digest(provider['actions'])
                row['shared_core_reuse']['action_core_sha256'] = current['action_core_sha256']
                def read_provider(target, *args, **kwargs):
                    return json.dumps(provider) if target.resolve() == path else original_read(target, *args, **kwargs)
                with patch.object(Path, 'read_text', new=read_provider):
                    with self.assertRaises(ValueError):
                        prepare(a, self.values[1], ['F000477', 'M001184'])

    def test_fisa142_penalty_and_vetting_predicates_cannot_borrow_other_branches(self):
        aid = 'house:119:2:142'
        text = next(a['candidate_exact_action_meaning'] for a in self.products[0]['actions'] if a['action_id'] == aid)
        def check_penalty(candidate):
            branch = candidate[candidate.index('Section3 adds two distinct offenses:'):candidate.index('The qualified TitleVII repeal-date extension')]
            for phrase in ['FBI employee or officer AND knowingly and willfully',
                           'relating to US-person queries', 'proposed709(a)(3) separately',
                           'knowingly and willfully falsifying or materially misrepresenting',
                           'not more than five years, or both', 'eight-year maximum remain separate',
                           'was a United States officer or employee at the time']:
                self.assertIn(phrase, branch)
        check_penalty(text)
        for fragment in ['FBI employee or officer AND ', 'knowingly and willfully violating',
                         'or materially misrepresenting', 'eight-year maximum remain separate',
                         'was a United States officer or employee at the time']:
            with self.subTest(removed=fragment):
                self.assertIn(fragment, text)
                with self.assertRaises(AssertionError):
                    check_penalty(text.replace(fragment, '', 1))
        for phrase in ['procedures enable vetting all non-US persons',
                       'terms that do not qualify as US-person query terms',
                       'not a mandate to conduct every individual query',
                       'alien lawfully admitted for permanent residence',
                       'Non-US-person is not equivalent to unauthorized immigrant',
                       'possible abuses of civil liberties and privacy exist',
                       'at most two staff on their behalf', 'April30,2029']:
            self.assertIn(phrase, text)
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        self.assertIn('shall ensure that the procedures enable the vetting of all',
                      sources['govinfo:pl11849-section24-182']['text'])
        self.assertIn('only if the person conducting the United States person query has a reasonable belief',
                      sources['govinfo:50usc1881a-target-query181']['text'])

    def test_fulbright_amendment_deletes_minimum_without_cutting_exchange_total(self):
        aid = 'house:119:2:241'
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        operative = sources['congressional-record:pending241-operative168']['text']
        self.assertIn('strike', operative)
        self.assertIn('not less than $287,800,000', operative)
        account = sources['state:rh-exchange169']['text']
        # Apply only the printed deletion, allowing the PDF's line numbering.
        import re
        match = re.search(r', of which not less than\s+24\s+\$287,800,000 shall be for the Fulbright Program', account)
        self.assertIsNotNone(match)
        changed = account[:match.start()] + account[match.end():]
        self.assertIn('$647,000,000', changed)
        self.assertNotIn('$287,800,000', changed)
        for phrase in ['until expended', '30 days', 'eligibility criteria', 'regular notification procedures']:
            self.assertIn(phrase, changed)
        clerk = sources['clerk:119:2:241']
        self.assertEqual(clerk['metadata']['amendment-author'], 'Boebert of Colorado Part A Amendment No. 1')
        self.assertEqual(clerk['metadata']['vote-result'], 'Failed')
        self.assertEqual(clerk['member_records']['F000477']['official_label'], 'No')
        self.assertEqual(clerk['member_records']['M001184']['official_label'], 'Aye')
        self.assertNotIn(aid, [a['action_id'] for a in self.products[0]['actions']])
        record = next(r for r in self.values[3]['records'] if r['action_id'] == aid)
        self.assertEqual(record['disposition'], 'exact_action_ineligible')
        self.assertEqual(record['review_state'], 'candidate_pending_external_semantic_review')

    def test_fulbright_board_and_currency_exchange_routes_remain_distinct(self):
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        board = sources['govinfo:22usc2456-operative2024-176']['text']
        board_selection = board[board.index('(1) For the purpose'):board.index('(2) In the selection')]
        self.assertIn('section 2452(a)(1)', board_selection)
        self.assertIn('section 2452(b)(4) and (6)', board_selection)
        self.assertNotIn('2452(b)(10)', board_selection)
        activities = sources['govinfo:22usc2452-exchange-operative169']['text']
        education = activities[activities.index('(1) educational exchanges'):activities.index('(2) cultural exchanges')]
        for phrase in ['American citizens and nationals', 'citizens and nationals of foreign countries', 'visits and interchanges']:
            self.assertIn(phrase, education)
        administration = sources['govinfo:22usc2454-operative2024-176']['text']
        grants = administration[administration.index('(e) Grants;'):administration.index('(f) Repealed.')]
        currency = administration[administration.index('(g) Currency exchange'):]
        self.assertIn('tuition', grants)
        self.assertIn('travel expenses', grants)
        self.assertNotIn('will not apply for an immigrant visa', grants)
        self.assertIn('only if he gives satisfactory assurances', currency)
        self.assertIn('will not apply for an immigrant visa or for permanent residence', currency)
        self.assertIn('under section 2452(b)(10)', currency)

    def test_hr5214_document_offense_chain_reuses_the_whole_shared_choice(self):
        health = DATA.parent / 'house_119_health_20260916'
        provider = json.loads((health / 'generated/shared_action_core.json').read_text(encoding='utf-8'))
        aid = 'house:119:1:298'
        shared = next(a for a in provider['actions'] if a['action_id'] == aid)
        reused = next(a for a in self.products[0]['actions'] if a['action_id'] == aid)
        self.assertEqual(shared, reused)
        text = reused['candidate_exact_action_meaning']
        for phrase in ['23-1331(3)(I)', 'knowingly to destroy, conceal, remove, confiscate, or possess',
                       'actual or purported', 'passport or other immigration document',
                       'prevent or restrict, or attempt to prevent or restrict', 'without lawful authority',
                       'in order to maintain', 'five years', 'later 22-3571.01 fine reference',
                       'do not create a new document offense', 'immigration-status detention or removal']:
            self.assertIn(phrase, text)
        source = next(s['text'] for s in self.values[1]['sources']
                      if s['source_id'] == 'dc-council:law18-239-original180')
        document = source[source.index('Sec. 105.'):source.index('Sec. 106.')]
        self.assertIn('including a passport or other immigration document', document)
        self.assertIn('without lawful authority', document)
        self.assertIn('in order to maintain the labor or services', document)
        self.assertIn(document, [c['passage'] for c in shared['claim_source_map']])
        for domain in [self.products[2], json.loads((health / 'generated/member_projections.json').read_text(encoding='utf-8'))]:
            for member in domain:
                row = next(a for a in member['actions'] if a['action_id'] == aid)
                self.assertEqual(row['action_core_sha256'], shared['action_core_sha256'])
                self.assertEqual(row['official_status'], 'Nay' if member['member_id'] == 'F000477' else 'Yea')
        mirror = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
        self.assertIn(mirror['source_render_constraints'][0], self.products[1]['source_render_constraints'])
        self.assertEqual(mirror['source_render_constraints'][0]['semantic_effect'], 'bounds_cross_domain_attribution')

    def test_hr5107_emergency_aid_preserves_observer_actor_trigger_and_immediacy(self):
        aid = 'house:119:1:299'
        health = DATA.parent / 'house_119_health_20260916'
        canonical = next(a for a in json.loads((health / 'authoring.json').read_text(encoding='utf-8'))['actions']
                         if a['action_id'] == aid)
        source = next(s['text'] for s in self.values[1]['sources'] if s['source_id'] == 'dc-council:law24-345')
        trigger = source[4155:4610]
        self.assertIn("observes another law enforcement officer's use of a prohibited technique", trigger)
        self.assertIn('to fail to immediately', trigger)
        def assert_trigger(text):
            self.assertIn('when a law enforcement officer observes another law enforcement officer use a prohibited technique', text)
            self.assertIn('immediately render or cause to be rendered first aid or request emergency medical services', text)
            self.assertIn('for the person on whom the technique was used', text)
            self.assertNotIn('after excessive force', text)
        mirror = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
        shared = next(a for a in self.products[0]['actions'] if a['action_id'] == aid)
        for text in [canonical['meaning'], mirror['meaning'], shared['candidate_exact_action_meaning']]:
            assert_trigger(text)
        for old, new in [('observes another law enforcement officer', 'uses force'),
                         ('prohibited technique', 'excessive force'),
                         ('immediately render', 'render')]:
            with self.subTest(omission=old), self.assertRaises(AssertionError):
                assert_trigger(canonical['meaning'].replace(old, new))
        receipt = json.loads((DATA / 'hr5107_emergency_aid_trigger_correction_checkpoint202.json').read_text(encoding='utf-8'))
        self.assertEqual(receipt['receipt_sha256'], sealed_digest(receipt, 'receipt_sha256'))
        self.assertEqual(receipt['literal_passage'], trigger)
        self.assertIn('after excessive force', receipt['before_canonical_input']['meaning'])
        self.assertEqual(receipt['corrected_canonical_input'], canonical)
        self.assertEqual(receipt['corrected_Immigration_mirror'], mirror)
        self.assertEqual(receipt['corrected_core_sha256'], shared['action_core_sha256'])

    def test_hr5107_immigration_reuses_one_corrected_cross_domain_core(self):
        from scripts.prepare_shared_domain_candidate import prepare as prepare_shared
        health = DATA.parent / 'house_119_health_20260916'
        ha = json.loads((health / 'authoring.json').read_text(encoding='utf-8'))
        hc = json.loads((health / 'sources.json').read_text(encoding='utf-8'))
        hp = prepare_shared(ha, hc, ['F000477', 'M001184'])
        aid = 'house:119:1:299'
        shared = next(a for a in hp[0]['actions'] if a['action_id'] == aid)
        reused = next(a for a in self.products[0]['actions'] if a['action_id'] == aid)
        self.assertEqual(shared, reused)
        source_input = next(a for a in ha['actions'] if a['action_id'] == aid)
        mirror = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
        self.assertEqual(source_input, {k: v for k, v in mirror.items() if k not in ['source_render_constraints', 'shared_core_reuse']})
        self.assertNotIn(chr(92), mirror['shared_core_reuse']['artifact_ref'])
        self.assertIn('at the time of application', shared['candidate_exact_action_meaning'])
        self.assertIn('SubtitleG is outside', shared['candidate_exact_action_meaning'])
        for domain in [hp[2], self.products[2]]:
            for member in domain:
                observed = next(a for a in member['actions'] if a['action_id'] == aid)
                self.assertEqual(observed['action_core_sha256'], shared['action_core_sha256'])
                self.assertEqual(observed['official_status'], 'Nay' if member['member_id'] == 'F000477' else 'Yea')
        boundary = mirror['source_render_constraints'][0]
        self.assertEqual(boundary['action_ids'], [aid])
        self.assertEqual(boundary['semantic_effect'], 'bounds_cross_domain_attribution')
        self.assertIn(boundary, self.products[1]['source_render_constraints'])
        health_rows = json.loads((health / 'universe_proposal.json').read_text(encoding='utf-8'))['candidate_dispositions']
        self.assertEqual(next(r for r in health_rows if r['action_id'] == aid)['disposition'], 'interpreted_substantive_directional')
        for kind in ['stale', 'divergent', 'outside']:
            altered = copy.deepcopy(self.values[0])
            action = next(a for a in altered['actions'] if a['action_id'] == aid)
            if kind == 'stale':
                action['shared_core_reuse']['action_core_sha256'] = '0' * 64
                message = 'stale shared-core reuse reference'
            elif kind == 'divergent':
                action['meaning'] += ' A contradictory independently authored interpretation.'
                message = 'input or governed sources differ from canonical core'
            else:
                action['shared_core_reuse']['artifact_ref'] = '../../outside/shared_action_core.json'
                message = 'repository candidate corpus'
            with self.subTest(rejected=kind), self.assertRaisesRegex(ValueError, message):
                prepare(altered, self.values[1], ['F000477', 'M001184'])
        self.assertFalse(readable_candidates(self.values[0], self.products[0], self.products[2], self.products[-1])['production_eligible'])

    def test_hr7008_investment_exclusions_preserve_fund_conjunct_and_any_member_scope(self):
        aid = 'house:119:2:280'
        fund = ('widely held AND (publicly traded OR widely diversified) AND '
                'neither control nor ability to control underlying financial interests')
        trustee = ('AND a trustee who is not the spouse, child, parent or sibling '
                   'of a Member of Congress')
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        self.assertEqual(sources['govinfo:5usc13104f8-fund198']['text'][121:148],
                         'widely held investment fund')
        self.assertIn('sibling of a Member of Congress', sources['govinfo:hr7008eh']['text'][2424:2509])
        core, _, projections, inputs, result = self.products
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == aid)
        shared = next(a for a in core['actions'] if a['action_id'] == aid)
        receipt = json.loads((DATA / 'hr7008_investment_exclusion_precision_correction_checkpoint200.json').read_text(encoding='utf-8'))
        self.assertEqual(receipt['receipt_sha256'], sealed_digest(receipt, 'receipt_sha256'))
        self.assertEqual(receipt['new_action_input'], action)
        self.assertEqual(receipt['new_shared_core_sha256'], shared['action_core_sha256'])
        def meaning_texts(value):
            if isinstance(value, str):
                if 'The historical13104(f)(8) comparator retains' in value:
                    yield value
            elif isinstance(value, dict):
                for item in value.values():
                    yield from meaning_texts(item)
            elif isinstance(value, list):
                for item in value:
                    yield from meaning_texts(item)
        readable = readable_candidates(self.values[0], core, projections, result)
        for name, value in [('authoring', action), ('shared_core', shared),
                            ('compiler_input', inputs), ('readable', readable),
                            ('current_receipt', receipt['new_action_input'])]:
            texts = list(meaning_texts(value))
            self.assertTrue(texts, name)
            for text in texts:
                with self.subTest(product=name):
                    self.assertIn(fund, text)
                    self.assertIn(trustee, text)
                    self.assertNotIn("trustee who is not the Member's", text)
        for member in readable['members']:
            finding = next(f for f in member['findings'] if aid in f['action_ids'])
            text = json.dumps(finding)
            self.assertIn(fund, text)
            self.assertIn(trustee, text)
            observed = next(o for o in finding['action_observations'] if o['action_id'] == aid)
            self.assertEqual(observed['direction'], 'opposition' if member['member_id'] == 'F000477' else 'support')
        self.assertFalse(readable['production_eligible'])

    def test_state_passage_pending_package_keeps_engrossed_division_and_prior_hold(self):
        receipt = json.loads((DATA / 'state_passage_source_boundaries_checkpoint177.json').read_text(encoding='utf-8'))
        self.assertEqual(receipt['receipt_sha256'], sealed_digest(receipt, 'receipt_sha256'))
        case = receipt['still_pending_candidate_cases'][0]
        self.assertEqual(case['action_id'], 'house:119:2:247')
        self.assertFalse(case['completed_screening'])
        self.assertFalse(case['exact_chain_completed'])
        row = next(x for x in self.values[2]['candidate_dispositions'] if x['action_id'] == case['action_id'])
        self.assertEqual(row['disposition'], 'source_unresolved')
        later = json.loads((DATA / 'state_passage_qualified_research_checkpoint178.json').read_text(encoding='utf-8'))
        self.assertEqual(case['current_pending_row_sha256'], digest(later['prior_pending_row']))
        self.assertNotIn(case['action_id'], {x['action_id'] for x in self.values[0]['actions']})
        self.assertEqual(receipt['existing_shared_core_reference']['action_core_sha256'],
                         '42dc696c8101a52b0f95bd74c8aab08ae71fa4b5ff8de532c4056e4522b429d1')
        sources = {x['source_id']: x for x in self.values[1]['sources']}
        full = sources['govinfo:hr8595eh']['text']
        body = sources['state:divisionB-save177']
        interval = body['source_text_extents'][0]
        self.assertEqual(body['text'], full[interval['start']:interval['end']])
        self.assertIn('investigation to determine whether to initiate removal proceedings', body['text'])
        self.assertIn('Duty of Secretary of Homeland Security To Notify Election Officials of Naturalization', body['text'])
        self.assertIn('Exception for Absent Uniformed Services Voters', body['text'])
        for claim in case['claim_source_map']:
            self.assertIn(claim['passage'], sources[claim['source_id']]['text'])
        self.assertFalse(receipt['actual_source_reading']['complete_read'])
        self.assertEqual(receipt['actual_source_reading']['unread_intervals'], [{'start': 108000, 'end': 301371}])
        self.assertFalse(receipt['editorially_accepted'])
        self.assertFalse(receipt['publication_authorized'])

    def test_state_operator_conflict_preserves_pending_and_historical_reading(self):
        receipt = json.loads((DATA / 'state_passage_qualified_research_checkpoint178.json').read_text(encoding='utf-8'))
        self.assertEqual(receipt['receipt_sha256'], sealed_digest(receipt, 'receipt_sha256'))
        row = next(x for x in self.values[2]['candidate_dispositions'] if x['action_id'] == 'house:119:2:247')
        self.assertEqual(row['disposition'], 'source_unresolved')
        self.assertEqual(receipt['current_pending_row_sha256'], digest(row))
        self.assertTrue(row['review_progress']['authoritative_source_conflict'])
        self.assertFalse(receipt['completed_screening'])
        self.assertTrue(receipt['whole_EH_reading']['complete_read'])
        self.assertEqual(receipt['whole_EH_reading']['unread_intervals'], [])
        old = json.loads((DATA / 'state_passage_source_boundaries_checkpoint177.json').read_text(encoding='utf-8'))
        self.assertEqual(receipt['historical177_receipt_sha256'], old['receipt_sha256'])
        self.assertFalse(old['actual_source_reading']['complete_read'])
        self.assertEqual(old['actual_source_reading']['unread_intervals'], [{'start': 108000, 'end': 301371}])
        self.assertEqual({x['conflict_id'] for x in receipt['blocking_source_conflicts']},
                         {'state-enbloc-A7-178', 'state-enbloc-A17-178'})
        sources = {x['source_id']: x for x in self.values[1]['sources']}
        floor = sources['state:floor-enbloc-page45-178']['text']
        for number in (7, 17):
            start = floor.index(f'AMENDMENT NO. {number} OFFERED')
            end = floor.index('AMENDMENT NO.', start + 20)
            self.assertNotIn('increased by', floor[start:end])
        for conflict in receipt['blocking_source_conflicts']:
            self.assertTrue(conflict['rendered_Record_verified'])
            self.assertTrue(conflict['no_precedence_rule_applied'])
        for item in receipt['candidate_research_observations'] + receipt['blocking_source_conflicts']:
            for claim in item['claim_source_map']:
                self.assertIn(claim['passage'], sources[claim['source_id']]['text'])
        self.assertEqual(receipt['existing_shared_core_reference']['action_core_sha256'],
                         '42dc696c8101a52b0f95bd74c8aab08ae71fa4b5ff8de532c4056e4522b429d1')
        self.assertNotIn('house:119:2:247', {x['action_id'] for x in self.values[0]['actions']})
        self.assertFalse(receipt['editorially_accepted'])
        self.assertFalse(receipt['publication_authorized'])

    def test_jordan_constraint_survives_mapping_compiler_and_presentation(self):
        core, mapping, projections, inputs, result = self.products
        action = next(a for a in self.values[0]['actions'] if a['action_id'] == 'house:119:2:244')
        expected = action['source_render_constraints']
        self.assertEqual(len(expected), 1)
        boundary = expected[0]
        self.assertEqual(boundary['action_ids'], ['house:119:2:244'])
        self.assertEqual(boundary['semantic_effect'], 'bounds_cross_domain_attribution')
        self.assertIn('United States Emergency Refugee and Migration Assistance Fund (ERMA)', boundary['detail'])
        self.assertIn('22 USC2601(f)', boundary['detail'])
        self.assertIn('Reserve application', boundary['detail'])
        self.assertIn('does not establish separate component positions', boundary['detail'])
        for rows in [mapping['source_render_constraints'],
                     inputs['shared_semantics']['source_render_constraints'],
                     result.compiled_ir['source_render_constraints'],
                     result.review_payload['source_render_constraints'],
                     result.presentation_payload['source_render_constraints']]:
            self.assertEqual([r for r in rows if r['constraint_id'] == boundary['constraint_id']], expected)
        from backend.app.editorial_presentations.compiler import source_constraint_boundaries
        target = source_constraint_boundaries(expected)[0]
        self.assertEqual(target['presentation_target'], 'source_note')
        self.assertEqual(target['action_ids'], ['house:119:2:244'])
        self.assertIsNone(result.public_presentation_artifact)
        self.assertIsNone(result.persistence_proposal)

    def test_jordan_constraint_preserves_every_meaning_choice_and_behavior(self):
        baseline = copy.deepcopy(self.values[0])
        action = next(a for a in baseline['actions'] if a['action_id'] == 'house:119:2:244')
        action.pop('source_render_constraints')
        before = prepare(baseline, self.values[1], ['F000477', 'M001184'])
        self.assertEqual(before[0], self.products[0])
        self.assertEqual(before[2], self.products[2])
        self.assertEqual(before[-1].compiled_ir['members'], self.products[-1].compiled_ir['members'])
        self.assertEqual(before[-1].compiled_ir['source_render_constraints'],
                         [r for r in self.products[-1].compiled_ir['source_render_constraints']
                          if r['constraint_id'] != 'source:house119-session2-roll244-immigration-attribution'])
        self.assertNotEqual(before[1]['mapping_sha256'], self.products[1]['mapping_sha256'])

    def test_jordan_constraint_rejects_scope_leak_and_invalid_effect(self):
        from backend.app.semantic_ir.compiler import SemanticCompilerInputError
        for scope in [['house:119:2:243'], [], ['house:119:2:244', 'house:119:2:243']]:
            authoring = copy.deepcopy(self.values[0])
            action = next(a for a in authoring['actions'] if a['action_id'] == 'house:119:2:244')
            action['source_render_constraints'][0]['action_ids'] = scope
            with self.subTest(scope=scope), self.assertRaisesRegex(ValueError, 'own exact action'):
                prepare(authoring, self.values[1], ['F000477', 'M001184'])
        authoring = copy.deepcopy(self.values[0])
        action = next(a for a in authoring['actions'] if a['action_id'] == 'house:119:2:244')
        action['source_render_constraints'][0]['semantic_effect'] = 'unrecognized_effect'
        with self.assertRaisesRegex(SemanticCompilerInputError, 'invalid semantic effect'):
            prepare(authoring, self.values[1], ['F000477', 'M001184'])

    def test_jordan_behavior_depends_on_typed_effect_not_constraint_prose(self):
        inputs = copy.deepcopy(self.products[3])
        boundary = next(r for r in inputs['shared_semantics']['source_render_constraints']
                        if r['constraint_id'] == 'source:house119-session2-roll244-immigration-attribution')
        boundary['semantic_effect'] = 'blocks_behavioral_propositions'
        blocked = run_editorial_pipeline(inputs).compiled_ir
        for before, after in zip(self.products[-1].compiled_ir['members'], blocked['members']):
            kept = [p for p in before['proposition_graph']['propositions']
                    if 'house:119:2:244' not in p['evidence_action_ids']]
            self.assertEqual(after['proposition_graph']['propositions'], kept)
            self.assertTrue(any('house:119:2:244' in p['evidence_action_ids']
                                for p in before['proposition_graph']['propositions']))
            self.assertTrue(any(row['action_id'] == 'house:119:2:244'
                                and row['reason_code'] == 'source_constraint_blocks_behavioral_proposition'
                                for row in after['action_accounting']['non_proposition_reasons']))

    def test_scott_episode_hold_blocks_only_its_behavior_and_survives_delivery(self):
        aids = ['house:119:1:79', 'house:119:1:83']
        result = self.products[-1]
        for rows in [self.products[1]['source_render_constraints'],
                     self.products[3]['shared_semantics']['source_render_constraints'],
                     result.compiled_ir['source_render_constraints'],
                     result.review_payload['source_render_constraints'],
                     result.presentation_payload['source_render_constraints']]:
            hold = next(r for r in rows if r['constraint_id'] == 'candidate-episode-hold')
            self.assertEqual(hold['action_ids'], aids)
            self.assertEqual(hold['semantic_effect'], 'blocks_behavioral_propositions')
        inputs = copy.deepcopy(self.products[3])
        inputs['shared_semantics']['source_render_constraints'] = [
            r for r in inputs['shared_semantics']['source_render_constraints']
            if r['constraint_id'] != 'candidate-episode-hold']
        released = run_editorial_pipeline(inputs).compiled_ir
        for held, unheld in zip(result.compiled_ir['members'], released['members']):
            for aid in aids:
                self.assertFalse(any(aid in p['evidence_action_ids']
                                     for p in held['proposition_graph']['propositions']))
                self.assertTrue(any(r['action_id'] == aid
                                    and r['reason_code'] == 'source_constraint_blocks_behavioral_proposition'
                                    for r in held['action_accounting']['non_proposition_reasons']))
                self.assertTrue(any(aid in p['evidence_action_ids']
                                    for p in unheld['proposition_graph']['propositions']))
            self.assertEqual([p for p in unheld['proposition_graph']['propositions']
                              if not set(aids).intersection(p['evidence_action_ids'])],
                             held['proposition_graph']['propositions'])
        self.assertIsNone(result.public_presentation_artifact)
        self.assertIsNone(result.persistence_proposal)

    def test_scott_candidate_preserves_replaced_baseline_and_pending_passage_history(self):
        receipt = json.loads((DATA / 'translator_qualification_candidate173.json').read_text(encoding='utf-8'))
        self.assertEqual(receipt['receipt_sha256'], sealed_digest(receipt, 'receipt_sha256'))
        self.assertEqual(receipt['baseline']['complete_pages_read'], list(range(1, 61)))
        actions = {a['action_id']: a for a in self.values[0]['actions']}
        candidate = actions['house:119:1:79']
        self.assertEqual(receipt['candidate_action_sha256'], digest(candidate))
        claims = {c['source_id']: c['passage'] for c in candidate['claim_source_map']}
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        sid = receipt['baseline']['source_id']
        self.assertEqual(claims[sid], sources[sid]['text'])
        self.assertEqual(receipt['baseline']['text_sha256'], digest(claims[sid]))
        self.assertIn('all seven foreign-source limbs', candidate['meaning'].lower())
        self.assertIn('trust territory or protectorate', candidate['meaning'])
        self.assertIn('English translation', candidate['meaning'])
        prior = claims[receipt['baseline']['prior_modification_source_id']]
        self.assertEqual(prior.count('The amendment was agreed to.'), 2)
        package = json.loads((DATA / 'passage_package_candidate175.json').read_text(encoding='utf-8'))
        self.assertEqual(package['receipt_sha256'], sealed_digest(package, 'receipt_sha256'))
        pending = package['prior83_pending_row']
        self.assertEqual(pending['disposition'], 'source_unresolved')
        self.assertFalse(pending['review_progress']['substantive_review_performed'])
        current = next(r for r in self.values[2]['candidate_dispositions']
                       if r['action_id'] == pending['action_id'])
        self.assertEqual(current['disposition'], 'interpreted_substantive_directional')
        self.assertEqual(receipt['prior83_membership_review_record']['disposition'], 'exact_action_ineligible')
        self.assertEqual(receipt['restored83_row_sha256'], digest(pending))
        passage = actions[pending['action_id']]
        precision = json.loads((DATA / 'state_source_boundaries_checkpoint176.json').read_text(encoding='utf-8'))['prose_precision_correction']
        self.assertEqual(package['candidate_action_sha256'], precision['prior_authoring_action_sha256'])
        self.assertEqual(precision['prior_authoring_action_sha256'], digest(precision['prior_authoring_action']))
        self.assertEqual(precision['corrected_authoring_action_sha256'], digest(passage))
        self.assertEqual(passage['meaning'], precision['prior_authoring_action']['meaning'].replace(
            precision['before_phrase'], precision['after_phrase']))
        self.assertIn('investigation of possible violations', passage['meaning'])
        self.assertIn('noncompliance triggers the Secretary', passage['meaning'])
        self.assertIn('noncompliance requires a civil action', passage['meaning'])
        literal = precision['literal_source_extent']
        self.assertEqual(literal['passage'], sources[precision['source_id']]['text'][literal['start']:literal['end']])
        boundary = passage['source_render_constraints'][0]
        self.assertEqual(boundary['action_ids'], [passage['action_id']])
        self.assertEqual(boundary['semantic_effect'], 'bounds_cross_domain_attribution')
        self.assertIn('all foreign-source/agency limbs', boundary['detail'])
        self.assertEqual(package['held_authored_action_ids'], ['house:119:1:79', 'house:119:1:83'])
        self.assertIn('by a person that is not--', receipt['passage_material_excerpt']['passage'])

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

    def _assert_precise_Dakota_section(self, row, parent, number):
        title = {'607': 'SEC. 607. MUNICIPAL, RURAL, AND INDUSTRIAL WATER SERVICE.',
                 '610': 'SEC. 610. AUTHORIZATION OF APPROPRIATIONS.'}[number]
        self.assertTrue(row['text'].startswith(title), 'Same section number is not the same Act clause')
        self.assertNotIn('Assets for Independence Act', row['text'])
        self.assertEqual(row['governed_parent_source_identity']['source_id'], parent['source_id'])
        extent, = row['source_text_extents']
        self.assertEqual(extent['total'], len(parent['text']))
        self.assertEqual(row['text'], parent['text'][extent['start']:extent['end']])
        self.assertEqual(row['raw_sha256'], parent['raw_sha256'])
        if number == '607':
            for text in ['State of North Dakota', 'Indian Municipal Rural and Industrial Water Supply',
                         'Fort Berthold', 'Standing Rock', 'Turtle Mountain', 'Fort Totten']:
                self.assertIn(text, row['text'])
        else:
            for text in ['Statewide', 'Indian municipal, rural, and industrial', 'Indexing']:
                self.assertIn(text, row['text'])

    def test_Dakota_provenance_repair_binds_own_Act_sections_and_preserves_history(self):
        bank = {r['source_id']: r for r in self.values[1]['sources']}
        parent = bank['govinfo:pl106-554-dakota-water610']
        self.assertIn('Assets for Independence Act', bank['govinfo:pl106-554-dakota-water607']['text'])
        for number in ['607', '610']:
            sid = f'govinfo:pl106554-dakota-sec{number}-precise218'
            self._assert_precise_Dakota_section(bank[sid], parent, number)
            for aid in ['house:119:2:6', 'house:119:2:7']:
                core = next(r for r in self.products[0]['actions'] if r['action_id'] == aid)
                self.assertIn(sid, core['semantic_ir_source_ids'])
                self.assertTrue(any(r['source_id'] == sid and r['passage'] == bank[sid]['text']
                                    for r in core['claim_source_map']))
                self.assertIn('Assets for Independence Act', core['candidate_exact_action_meaning'])
                original = next(r for r in core['claim_source_map']
                                if r['source_id'] == 'govinfo:pl106-554-dakota-water607')
                self.assertIn('not positive Dakota support', original['locator'])
                broad = next(r for r in core['claim_source_map']
                             if r['source_id'] == parent['source_id'])
                self.assertEqual(broad['passage'], parent['text'][609877:628179])
                self.assertNotIn('Assets for Independence Act', broad['passage'])

    def test_Dakota_regression_rejects_both_historical_same_number_false_matches(self):
        bank = {r['source_id']: r for r in self.values[1]['sources']}
        parent = bank['govinfo:pl106-554-dakota-water610']
        for number in ['607', '610']:
            with self.subTest(section=number):
                row = copy.deepcopy(bank[f'govinfo:pl106554-dakota-sec{number}-precise218'])
                row['text'] = (bank['govinfo:pl106-554-dakota-water607']['text'] if number == '607'
                               else parent['text'][:len(row['text'])])
                row['governed_bytes_sha256'] = sealed_digest(row, 'governed_bytes_sha256')
                with self.assertRaises(AssertionError):
                    self._assert_precise_Dakota_section(row, parent, number)


    def _assert_HR5371_review221_precision(self, core):
        text = core['candidate_exact_action_meaning']
        for term in ['rejected motion to recommit and the separately supplied H.R.5450',
                     'Sections212and213restrict use of ICE Operations and Support funds',
                     'two most recent overall evaluations received by the contracted facility',
                     '1110emergency/disaster designation provisions',
                     '1113spending/expenditure/operating-plan requirements',
                     '1114monthly obligation reports', '1708FEMAtransfer',
                     '1808HistoricPreservationFund availability solely to liquidate valid fiscal2018-2019obligations throughfiscal2026']:
            self.assertIn(term, text)
        self.assertNotIn('two consecutive overall', text)
        bank = {row['source_id']: row for row in self.values[1]['sources']}
        for sid, start, end in [
                ('govinfo:pl118-47-complete-dhs-division-c', 30259, 30733),
                ('govinfo:pl118-47-complete-dhs-division-c', 30733, 31340),
                ('govinfo:pl119-4', 13185, 14270),
                ('govinfo:pl119-4', 15256, 18260),
                ('govinfo:pl119-4', 18260, 18854),
                ('govinfo:pl119-4', 65144, 66144)]:
            self.assertTrue(any(row['source_id'] == sid and
                                row['passage'] == bank[sid]['text'][start:end]
                                for row in core['claim_source_map']))

    def test_HR5371_review221_precise_actor_time_and_excluded_authorities(self):
        core = next(row for row in self.products[0]['actions']
                    if row['action_id'] == 'house:119:1:281')
        self._assert_HR5371_review221_precision(core)

    def test_HR5371_review221_detects_the_actual_historical_P3_errors(self):
        old = json.loads((DATA.parent / 'house_119_continuing_funding_qualification_checkpoint220' /
                          'shared_action_core_proposal.json').read_text(encoding='utf-8'))['actions'][0]
        with self.assertRaises(AssertionError):
            self._assert_HR5371_review221_precision(old)
        current = next(row for row in self.products[0]['actions']
                       if row['action_id'] == 'house:119:1:281')
        for correct, incorrect in [
                ('rejected motion to recommit and the separately supplied H.R.5450', 'rejected H.R.5450'),
                ('ICE Operations and Support funds', 'all DHS funds'),
                ('two most recent overall evaluations received by the contracted facility', 'any historical consecutive pair'),
                ('1110emergency/disaster designation provisions', '1110spending provisions'),
                ('1808HistoricPreservationFund availability solely to liquidate valid fiscal2018-2019obligations throughfiscal2026', '1808transfers')]:
            with self.subTest(boundary=correct):
                core = copy.deepcopy(current)
                core['candidate_exact_action_meaning'] = core['candidate_exact_action_meaning'].replace(correct, incorrect)
                with self.assertRaises(AssertionError):
                    self._assert_HR5371_review221_precision(core)

    def test_DC_credit_routes_preserve_shared_whole_choice_and_personal_status_limits(self):
        old = json.loads((DATA.parent / 'house_119_health_20260916/generated/shared_action_core.json').read_text(encoding='utf-8'))
        previous = next(row for row in old['actions'] if row['action_id'] == 'house:119:2:56')
        core = next(row for row in self.products[0]['actions'] if row['action_id'] == previous['action_id'])
        self.assertEqual(core['exact_action_identity'], previous['exact_action_identity'])
        self.assertEqual(core['action_meaning_ref'], previous['action_meaning_ref'])
        self.assertTrue(core['candidate_exact_action_meaning'].startswith(previous['candidate_exact_action_meaning']))
        for witness in previous['governed_source_identities']:
            self.assertIn(witness, core['governed_source_identities'])
        text = core['candidate_exact_action_meaning']
        self.assertIn('47-1806.04(f)(1)(D)', text)
        self.assertNotIn('47-1806.04(f-1)(1)(D)', text)
        for term in ['same amounts and extent', 'taxresidency', 'An ITIN is not proof of immigration status',
                     'not separately vote on noncitizens', 'separate untargeted emergency26-214law']:
            self.assertIn(term, text)
        bank = {row['source_id']: row for row in self.values[1]['sources']}
        s = bank['dc-council:47-1806.04-permanent-care-earned']['text']
        self.assertTrue(any(row['source_id'] == 'dc-council:47-1806.04-permanent-care-earned'
                            and 'not a citizen or resident alien' in row['passage']
                            and 'individual taxpayer identification number' in row['passage']
                            and row['passage'] in s for row in core['claim_source_map']))
        for member in self.products[2]:
            row = next(row for row in member['actions'] if row['action_id'] == core['action_id'])
            self.assertEqual(row['action_core_sha256'], core['action_core_sha256'])
            self.assertEqual(row['official_status'], 'Nay' if member['member_id'] == 'F000477' else 'Yea')

    def test_programme_screenings_are_noncounting_without_erasing_retained_status_predicates(self):
        reviews = {row['action_id']: row for row in self.values[3]['records']}
        core_ids = {row['action_id'] for row in self.products[0]['actions']}
        for roll, required in [(55, 'govinfo:30usc24-proof221'),
                               (191, 'govinfo:8usc1612-2024-complete')]:
            aid = f'house:119:2:{roll}'
            with self.subTest(action=aid):
                row = reviews[aid]
                self.assertEqual(row['disposition'], 'exact_action_ineligible')
                self.assertTrue(row['substantive_review_performed'])
                self.assertFalse(row['required_evidence_unavailable'])
                self.assertIn(required, {s['source_id'] for s in row['sources']})
                self.assertNotIn(aid, core_ids)
        self.assertIn('resolved nondirectional', reviews['house:119:2:191']['rationale'])


    def test_unresolved_imported_status_relationships_withdraw_completion_credit(self):
        from pathlib import Path
        universe = self.values[2]
        reviews = {row['action_id']: row for row in self.values[3]['records']}
        bank = {row['source_id']: row for row in self.values[1]['sources']}
        receipt = json.loads((DATA / 'programme_status_screening_checkpoint221.json').read_text(encoding='utf-8'))
        original = json.loads((DATA / 'programme_status_original_completion_checkpoint221_preserved222.json').read_text(encoding='utf-8'))
        for roll, witness in [(89, 'govinfo:13cfr121702-2025-ownership221'),
                              (193, 'govinfo:50cfr18-3-2025-native221')]:
            aid = f'house:119:2:{roll}'
            with self.subTest(action=aid):
                row = next(row for row in universe['candidate_dispositions'] if row['action_id'] == aid)
                self.assertEqual(row['disposition'], 'source_unresolved')
                self.assertFalse(row['review_progress']['substantive_review_performed'])
                self.assertTrue(row['review_progress']['source_application_relationship_unresolved'])
                self.assertFalse(row['review_progress']['required_evidence_unavailable'])
                self.assertIn(witness, {source['source_id'] for source in row['sources']})
                self.assertNotIn(aid, reviews)
                self.assertNotIn(aid, receipt['completed_action_ids'])
                self.assertNotIn(aid, receipt['completed_researched_holds'])
                self.assertIn(aid, original['completed_action_ids'])
                self.assertIn(aid, universe['unresolved_action_ids'])
        self.assertIn('PhaseII', next(row['reason'] for row in universe['candidate_dispositions']
                                     if row['action_id'] == 'house:119:2:89'))
        self.assertIn('citizenship', next(row['reason'] for row in universe['candidate_dispositions']
                                         if row['action_id'] == 'house:119:2:193'))
        self.assertIn('on or afterSeptember11,2001', reviews['house:119:2:191']['rationale'])
        self.assertEqual(bank['govinfo:hr6047eh']['text'][6230:6404],
                         reviews['house:119:2:191']['claim_source_map'][-1]['passage'])

    def _assert_HR5371_whole_qualified_core(self, core):
        self.assertEqual(core['legislative_stage'], 'final_passage')
        self.assertEqual(core['action_date'], '2025-09-19')
        self.assertEqual(core['exact_question'], 'On Passage')
        operative = {w['source_id'] for w in core['operative_meaning_source_identities']}
        self.assertTrue({'govinfo:hr5371eh', 'govinfo:pl119-4',
                         'govinfo:pl118-47-complete-dhs-division-c',
                         'govinfo:pl11842-compact-headstart-formula220',
                         'govinfo:pl11743-divisionB1701-research219',
                         'govinfo:pl117328-wildfire-pay440-220'} <= operative)
        self.assertNotIn('govinfo:hr5371eas', operative)
        own = 'immigration:hr5371-roll281-whole-choice220'
        self.assertIn(own, {w['source_id'] for w in core['action_outcome_source_identities']})
        self.assertNotIn(own, operative)
        bank = {r['source_id']: r for r in self.values[1]['sources']}
        self.assertIn('yeas 217, nays 212, not voting 3', bank[own]['text'])
        self.assertIn('level II of the Executive Schedule',
                      bank['govinfo:pl11743-divisionB1701-research219']['text'])
        self.assertIn('if a base grant has been established through appropriations',
                      bank['govinfo:pl11842-compact-headstart-formula220']['text'])
        meaning = core['candidate_exact_action_meaning']
        for boundary in ['operating-rate/account baselines', 'two jurisdictional grant baselines',
                         'not a general30-dayextension', 'authorization endingOctober1,2030',
                         'reporting endingJanuary31,2031']:
            self.assertIn(boundary, meaning)

    def test_HR5371_whole_choice_binds_exact_stage_and_material_source_chain(self):
        core = next(c for c in self.products[0]['actions'] if c['action_id'] == 'house:119:1:281')
        self._assert_HR5371_whole_qualified_core(core)

    def test_HR5371_inherited_Health_core_alone_cannot_pass_Immigration_qualification(self):
        old = json.loads((DATA.parent / 'house_119_health_20260916' / 'generated' /
                          'shared_action_core.json').read_text(encoding='utf-8'))
        core = next(c for c in old['actions'] if c['action_id'] == 'house:119:1:281')
        with self.assertRaises(AssertionError):
            self._assert_HR5371_whole_qualified_core(core)

    def _assert_HR4553_section108_direct_rule(self, core):
        meaning = core['candidate_exact_action_meaning']
        for text in ['Secretary of the Army', 'As of enactment and each fiscal year thereafter',
                     'not to promulgate or enforce a regulation', '36CFR327.0as in effect at enactment',
                     'not otherwise prohibited by law',
                     'AND possession complies with the law of the State']:
            self.assertIn(text, meaning)
        self.assertNotIn('firearm funding/enforcement restriction', meaning)
        bank = {r['source_id']: r for r in self.values[1]['sources']}
        actual = bank['govinfo:hr4553eh']['text'][17189:17836]
        self.assertTrue(any(r['source_id'] == 'govinfo:hr4553eh' and r['passage'] == actual
                            for r in core['claim_source_map']))

    def test_HR4553_section108_keeps_direct_actor_continuing_scope_and_both_conditions(self):
        core = next(r for r in self.products[0]['actions'] if r['action_id'] == 'house:119:1:239')
        self._assert_HR4553_section108_direct_rule(core)

    def test_HR4553_section108_regression_detects_historical_funding_label(self):
        old = json.loads((DATA.parent / 'house_119_energy_qualification_checkpoint218' /
                          'shared_action_core_proposal.json').read_text(encoding='utf-8'))
        core = next(r for r in old['actions'] if r['action_id'] == 'house:119:1:239')
        with self.assertRaises(AssertionError):
            self._assert_HR4553_section108_direct_rule(core)

    def test_funding_shared_prose_excludes_joined_member_name_tokens(self):
        for aid in ['house:119:1:239', 'house:119:2:6', 'house:119:2:7']:
            action = next(r for r in self.values[0]['actions'] if r['action_id'] == aid)
            prose = json.dumps([action[key] for key in ['short_description', 'compact_description',
                'meaning', 'limitations', 'choice_meanings']])
            self.assertIsNone(re.search(r'Foushee|Massie|F000477|M001184', prose))

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

    def _assert_checkpoint140_precision(self, records, sources):
        command = sources['govinfo:hres888ih']['text'][4765:4919]
        self.assertIn('directs the Committee on Ethics to conduct a full investigation', command)
        discipline = records['house:119:1:297']['rationale']
        self.assertIn('direct the Committee on Ethics to conduct a full investigation', discipline)
        self.assertIn('NOT agreed to', discipline)

        framework = sources['govinfo:50usc1544-2024-operative']['text']
        self.assertIn('after a report is submitted or is required to be submitted', framework)
        self.assertIn('extended for not more than an additional thirty days', framework)
        self.assertIn('Notwithstanding subsection (b), at any time', framework)
        military = records['house:119:1:346']['rationale']
        for fragment in ["section 1544(b)'s report-triggered termination",
                         'exceptions and qualified extension',
                         "section 1544(c)'s separate concurrent-resolution removal mechanism",
                         'notwithstanding subsection (b) under its stated conditions',
                         'constitutional enforceability is not resolved']:
            self.assertIn(fragment, military)
        self.assertNotIn('report-conditioned termination/removal framework', military)

    def test_noncounting_precision_keeps_directive_and_independent_war_powers_branches(self):
        records = {r['action_id']: r for r in self.values[3]['records']}
        sources = {s['source_id']: s for s in self.values[1]['sources']}
        self._assert_checkpoint140_precision(records, sources)
        mutations = [
            ('house:119:1:297',
             'direct the Committee on Ethics to conduct a full investigation',
             'request an Ethics investigation'),
            ('house:119:1:346',
             "section 1544(c)'s separate concurrent-resolution removal mechanism",
             'report-conditioned termination/removal framework'),
            ('house:119:1:346',
             'notwithstanding subsection (b) under its stated conditions',
             'under subsection (b)')]
        for aid, before, after in mutations:
            with self.subTest(action=aid, omitted=before):
                wrong = copy.deepcopy(records)
                self.assertIn(before, wrong[aid]['rationale'])
                wrong[aid]['rationale'] = wrong[aid]['rationale'].replace(before, after, 1)
                with self.assertRaises(AssertionError):
                    self._assert_checkpoint140_precision(wrong, sources)

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
