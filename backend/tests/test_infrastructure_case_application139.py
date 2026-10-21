import copy
import unittest

from backend.app.semantic_ir.shared_corpus import sealed_digest
from scripts.apply_infrastructure_case_decisions139 import apply_exact_decisions, SUBJECTS
from scripts.validate_infrastructure_case_application139 import APPLIED, inputs, read, validate


class ExactCaseApplication139Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m, cls.u, cls.capture, cls.proposals, cls.authority = inputs()
        cls.after_m = read(APPLIED / 'membership_review.json')
        cls.after_u = read(APPLIED / 'universe_proposal.json')

    def apply(self, m=None, u=None, proposals=None, authority=None):
        return apply_exact_decisions(self.m if m is None else m, self.u if u is None else u,
                                     self.capture, self.proposals if proposals is None else proposals,
                                     self.authority if authority is None else authority)

    def test_actual_application_replays_preserving_sources_meanings_and_member_behavior(self):
        self.assertTrue(validate()['compiled_graph_unchanged'])

    def test_application_is_pure_and_idempotent(self):
        before_m, before_u = copy.deepcopy(self.m), copy.deepcopy(self.u)
        m, u, effect = self.apply()
        self.assertTrue(effect['changed'])
        self.assertEqual((m, u), (self.after_m, self.after_u))
        self.assertEqual((self.m, self.u), (before_m, before_u))
        m2, u2, replay = self.apply(m, u)
        self.assertFalse(replay['changed'])
        self.assertEqual((m2, u2), (m, u))
        self.assertIsNot(m2, m)
        self.assertIsNot(u2, u)

    def test_already_applied_authority_drift_is_rejected_even_when_resealed(self):
        for field, value in [('publication_authorized', True), ('full_record_claim', True), ('approval_receipt', {'fake': True})]:
            bad = copy.deepcopy(self.after_u)
            bad[field] = value
            bad['proposal_sha256'] = sealed_digest(bad, 'proposal_sha256')
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'authority'):
                self.apply(self.after_m, bad)
        bad = copy.deepcopy(self.after_m)
        bad['authoritative_for_new_editorial_work'] = True
        bad['review_sha256'] = sealed_digest(bad, 'review_sha256')
        with self.assertRaisesRegex(ValueError, 'authority'):
            self.apply(bad, self.after_u)

    def test_already_applied_accounting_and_derived_row_drift_are_rejected(self):
        for edit in ['count', 'group', 'readiness', 'unresolved', 'rationale', 'source', 'progress', 'unrelated']:
            bad = copy.deepcopy(self.after_u)
            row = next(r for r in bad['candidate_dispositions'] if r['action_id'] == 'house:119:1:340')
            if edit == 'count':
                bad['accounting']['counts']['pending_interpretation'] += 1
            elif edit == 'group':
                bad['accounting']['action_ids_by_disposition']['pending_interpretation'].pop()
            elif edit == 'readiness':
                bad['accounting']['official_source_readiness']['pending_package_version_bindings'] += 1
            elif edit == 'unresolved':
                bad['unresolved_action_ids'].pop()
            elif edit == 'rationale':
                row['rationale'] = 'A different unapproved reason'
            elif edit == 'source':
                row['exact_action_source_binding']['source_ids'].pop()
            elif edit == 'progress':
                row['review_progress']['substantive_review_performed'] = False
            else:
                bad['candidate_dispositions'][0]['reason'] = 'Unrelated change'
            bad['proposal_sha256'] = sealed_digest(bad, 'proposal_sha256')
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                self.apply(self.after_m, bad)

    def test_preimage_proposal_and_partial_application_drift_are_rejected(self):
        bad = copy.deepcopy(self.m)
        bad['records'][339]['rationale'] += ' drift'
        with self.assertRaisesRegex(ValueError, 'subject drift'):
            self.apply(m=bad)
        bad = copy.deepcopy(self.proposals)
        bad[next(iter(SUBJECTS))]['proposed_record']['rationale'] += ' drift'
        with self.assertRaisesRegex(ValueError, 'proposed subject'):
            self.apply(proposals=bad)
        bad = copy.deepcopy(self.m)
        bad['records'][339] = copy.deepcopy(self.after_m['records'][339])
        with self.assertRaises(ValueError):
            self.apply(m=bad)

    def test_approval_scope_and_unchanged_preimage_authority_are_enforced(self):
        bad = copy.deepcopy(self.authority)
        bad['scope']['case_actions'].append('house:119:1:109')
        with self.assertRaisesRegex(ValueError, 'approval scope'):
            self.apply(authority=bad)
        bad = copy.deepcopy(self.u)
        bad['publication_authorized'] = True
        with self.assertRaisesRegex(ValueError, 'authority'):
            self.apply(u=bad)


if __name__ == '__main__':
    unittest.main()
