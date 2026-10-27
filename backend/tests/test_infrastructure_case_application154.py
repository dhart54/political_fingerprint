"""Authority, preservation and replay tests for the bounded eight-action application."""
import copy
import unittest
from pathlib import Path

from backend.app.semantic_ir.shared_corpus import digest
from scripts import apply_infrastructure_case_decisions154 as A
from scripts.validate_infrastructure_case_application154 import validate


class ApprovedApplication154Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[2]
        cls.d = A.load_inputs(cls.root)
        cls.m = A.read(cls.root / A.BASE / 'membership_review.json')
        cls.u = A.read(cls.root / A.BASE / 'universe_proposal.json')
        cls.sources = A.read(cls.root / A.BASE / 'sources.json')
        cls.after_m = A.read(cls.root / A.OUT / 'membership_review.json')
        cls.after_u = A.read(cls.root / A.OUT / 'universe_proposal.json')

    def apply(self, m=None, u=None, sources=None, d=None):
        return A.apply_exact_decisions(self.m if m is None else m, self.u if u is None else u,
            self.sources if sources is None else sources, self.d if d is None else d)

    def test_actual_successor_and_native_universe_contract(self):
        result = validate(self.root)
        self.assertEqual((result['eligibility_decisions'], result['resolved_bindings']), (3, 5))
        self.assertEqual(result['other_records_unchanged'], 668)

    def test_fresh_then_idempotent_and_inputs_immutable(self):
        before = digest([self.m, self.u, self.sources, self.d])
        m, u, first = self.apply()
        m2, u2, second = self.apply(m, u)
        self.assertTrue(first['changed'])
        self.assertFalse(second['changed'])
        self.assertEqual(digest([m, u]), digest([m2, u2]))
        self.assertEqual(before, digest([self.m, self.u, self.sources, self.d]))

    def test_three_eligibility_decisions_do_not_admit_meanings(self):
        rows = {r['action_id']: r for r in self.after_m['records']}
        self.assertEqual(rows['house:119:2:49']['disposition'], 'exact_action_ineligible')
        self.assertTrue(rows['house:119:2:49']['exact_action_binding_unresolved'])
        self.assertEqual(rows['house:119:1:231']['disposition'], 'exact_action_ineligible')
        self.assertEqual(rows['house:119:1:125']['disposition'], 'pending_interpretation')
        self.assertEqual(self.u['interpretation_action_ids'], self.after_u['interpretation_action_ids'])

    def test_only_five_bindings_change_and_eligibility_stays_pending(self):
        old = {r['action_id']: r for r in self.m['records']}
        new = {r['action_id']: r for r in self.after_m['records']}
        changed = {aid for aid in old if old[aid]['exact_action_binding_unresolved'] != new[aid]['exact_action_binding_unresolved']}
        self.assertEqual(changed, set(A.BINDINGS))
        self.assertTrue(all(new[aid]['disposition'] == 'pending_interpretation' for aid in A.BINDINGS))

    def test_partial_application_and_wrong_preimage_rejected(self):
        with self.assertRaises(ValueError):
            self.apply(self.after_m, self.u)
        m = copy.deepcopy(self.m)
        m['records'][0]['rationale'] += ' unrelated drift'
        with self.assertRaises(ValueError):
            self.apply(m)

    def test_source_pool_and_typed_boolean_drift_rejected(self):
        s = copy.deepcopy(self.sources)
        s['sources'][0]['raw_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            self.apply(sources=s)
        m = copy.deepcopy(self.after_m)
        m['authoritative_for_new_editorial_work'] = 0
        with self.assertRaises(ValueError):
            self.apply(m, self.after_u)

    def test_approval_cohort_meaning_and_binding_target_mutations_rejected(self):
        mutations = [
            lambda d: d['eligibility_decisions'].update({'house:119:1:19': 'include'}),
            lambda d: d['binding_decisions'].update({'house:119:2:49': 'govinfo:hr980eh'}),
            lambda d: d.update(authored_meaning_acceptance_authorized=True),
            lambda d: d['binding_decisions'].update({'house:119:1:330': 'govinfo:hr3898rh'}),
            lambda d: d['subjects']['house:119:1:125'].update(authored_meaning_accepted=True),
            lambda d: d['binding_evidence']['house:119:1:356'].update(approved_chain='Import rejected amendments1/5/6'),
            lambda d: d['binding_evidence']['house:119:1:19']['selected_immutable_units'].pop(),
            lambda d: d['binding_evidence']['house:119:2:97']['retained_source_identities'][0].update(raw_sha256='0' * 64),
        ]
        for mutation in mutations:
            d = copy.deepcopy(self.d)
            mutation(d)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.apply(d=d)

    def test_no_write_replay_preserves_actual_output_mtimes_and_bytes(self):
        paths = [self.root / A.OUT / p for p in self.d['snapshot_files']]
        paths += [self.root / A.PACKET / 'application_receipt.json']
        before = {str(p): (p.stat().st_mtime_ns, p.stat().st_size) for p in paths}
        self.assertFalse(A.materialize(self.root, check=True)['changed'])
        after = {str(p): (p.stat().st_mtime_ns, p.stat().st_size) for p in paths}
        self.assertEqual(before, after)

    def test_settled_acceptance_old70_and_historical_falseflags_preserved(self):
        for suffix in self.d['snapshot_files']:
            if suffix not in ['membership_review.json', 'universe_proposal.json']:
                self.assertEqual(A.normalized_bytes(self.root / A.BASE / suffix),
                                 A.normalized_bytes(self.root / A.OUT / suffix))
        self.assertEqual(len(self.after_u['interpretation_action_ids']), 77)


if __name__ == '__main__':
    unittest.main()
