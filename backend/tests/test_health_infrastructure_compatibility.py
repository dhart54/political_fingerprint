"""Preserve both bounded contracts without rewriting historical provenance."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import health_infrastructure_compatibility as compatibility
from scripts import prepare_health_one_action_review as review
from scripts.validate_infrastructure_case_application139 import APPLIED, read
from scripts.prepare_shared_domain_candidate import validate_universe_proposal


class HealthInfrastructureCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence, cls.frozen = compatibility.expected_evidence(review.ROOT, review.git_bytes)
        cls.current = {p: (review.ROOT / p).read_text(encoding='utf8') for p in compatibility.RULES}

    def test_exact_reviewed_successor_with_historical_payload_and_provenance_parity(self):
        self.assertEqual(self.evidence['shared_helper']['actual_git_blob'], compatibility.SUCCESSOR_HELPER)
        frozen = compatibility.validate_compatibility(review.ROOT, review.git_bytes)
        before = {name: (review.PACKAGE / name).read_bytes() for name in compatibility.PRODUCTS}
        products = review.build_package((review.PACKAGE / 'DECISION-PACKET.md').read_bytes())
        self.assertEqual(products, frozen)
        self.assertEqual({name: (review.PACKAGE / name).read_bytes() for name in before}, before)
        self.assertFalse(self.evidence['shared_helper']['executed_by_Health_preparer'])
        self.assertNotEqual(self.evidence['historical_preparer']['canonical_text_sha256'],
                            self.evidence['actual_replay_tools'][compatibility.PREPARER])

    def test_legacy_helper_remains_supported_without_generalizing_successor_permission(self):
        texts = dict(self.current)
        texts[compatibility.HELPER] = compatibility.normalized(review.git_bytes(compatibility.RULE_BASE, compatibility.HELPER))
        evidence, _ = compatibility.expected_evidence(review.ROOT, review.git_bytes, current_texts=texts)
        self.assertEqual(evidence['shared_helper']['actual_git_blob'], compatibility.HISTORICAL_HELPER)
        compatibility.validate_compatibility(review.ROOT, review.git_bytes, current_texts=texts, sidecar=evidence)
        texts[compatibility.HELPER] += '\n# Unreviewed successor\n'
        with self.assertRaisesRegex(ValueError, 'Unreviewed shared helper drift'):
            compatibility.validate_compatibility(review.ROOT, review.git_bytes, current_texts=texts, sidecar=evidence)

    def test_each_other_frozen_rule_still_rejects_drift(self):
        for path in compatibility.RULES[1:]:
            texts = dict(self.current)
            texts[path] += '\n# Unreviewed rule change\n'
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'Frozen generation rule differs'):
                compatibility.validate_compatibility(review.ROOT, review.git_bytes, current_texts=texts, sidecar=self.evidence)

    def test_sidecar_cannot_falsify_actual_tools_historical_subject_or_authority(self):
        for change in ['tool', 'helper', 'historical', 'payload', 'publication', 'persistence', 'extra']:
            sidecar = copy.deepcopy(self.evidence)
            if change == 'tool':
                sidecar['actual_replay_tools'][compatibility.PREPARER] = sidecar['historical_preparer']['canonical_text_sha256']
            elif change == 'helper':
                sidecar['shared_helper']['executed_by_Health_preparer'] = True
            elif change == 'historical':
                sidecar['historical_package_commit'] = '0' * 40
            elif change == 'payload':
                sidecar['frozen_package_file_sha256']['compiled_ir.json'] = '0' * 64
            elif change == 'extra':
                sidecar['exception_for_any_future_helper'] = True
            else:
                sidecar[change + '_authorized'] = True
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'sidecar differs'):
                compatibility.validate_compatibility(review.ROOT, review.git_bytes, sidecar=sidecar)

    def test_replayed_products_cannot_change_meaning_wording_or_member_behavior(self):
        for name in compatibility.PRODUCTS:
            if name == 'provenance.json':
                continue
            products = {n: copy.deepcopy(v) for n, v in self.frozen.items() if n != 'provenance.json'}
            products[name] = {'unreviewed': True}
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'frozen product'):
                compatibility.validate_products(products, self.frozen)

    def test_infrastructure_nondirectional_authoring_and_exact_set_equality_are_preserved(self):
        a, u, c, m = [read(APPLIED / (n + '.json')) for n in ['authoring', 'universe_proposal', 'sources', 'membership_review']]
        validate_universe_proposal(u, a, c, m)
        non_directional = {r['action_id'] for r in u['candidate_dispositions']
                           if r['disposition'] == 'interpreted_substantive_non_directional'}
        self.assertEqual(len(non_directional), 1)
        bad = copy.deepcopy(a)
        bad['actions'] = [r for r in bad['actions'] if r['action_id'] not in non_directional]
        with self.assertRaisesRegex(ValueError, 'interpretation set differs'):
            validate_universe_proposal(u, bad, c, m)

    def test_original_packet_bytes_and_checkout_policy_are_exact(self):
        packet = review.PACKAGE / 'DECISION-PACKET.md'
        self.assertEqual(packet.read_bytes(), review.git_bytes(compatibility.PACKAGE_PIN,
                                                              compatibility.PACKAGE_PATH + packet.name))
        self.assertIn(compatibility.PACKAGE_PATH + packet.name + ' -text',
                      (review.ROOT / '.gitattributes').read_text(encoding='utf8'))

    def test_boolean_authority_cannot_be_replaced_with_equal_numeric_values(self):
        for field in ['new_editorial_acceptance', 'publication_authorized', 'persistence_authorized', 'production_writes']:
            sidecar = copy.deepcopy(self.evidence)
            sidecar[field] = 0
            with self.subTest(gate='sidecar', field=field), self.assertRaisesRegex(ValueError, 'sidecar differs'):
                compatibility.validate_compatibility(review.ROOT, review.git_bytes, sidecar=sidecar)
        sidecar = copy.deepcopy(self.evidence)
        sidecar['shared_helper']['executed_by_Health_preparer'] = 0
        with self.assertRaisesRegex(ValueError, 'sidecar differs'):
            compatibility.validate_compatibility(review.ROOT, review.git_bytes, sidecar=sidecar)
        products = {n: copy.deepcopy(v) for n, v in self.frozen.items() if n != 'provenance.json'}
        products['shared_action_core.json']['authoritative_for_new_editorial_work'] = 0
        with self.assertRaisesRegex(ValueError, 'frozen product'):
            compatibility.validate_products(products, self.frozen)

    def test_check_only_cli_rejects_numeric_substitutions_in_frozen_provenance(self):
        with tempfile.TemporaryDirectory(prefix='health-compatibility-') as directory:
            package = Path(directory)
            (package / 'DECISION-PACKET.md').write_bytes((review.PACKAGE / 'DECISION-PACKET.md').read_bytes())
            for name, value in self.frozen.items():
                (package / name).write_bytes(review.encoded(value))
            for field in ['new_artifacts_accepted', 'production_eligible', 'publication_authorized',
                          'persistence_authorized', 'full_issue_claim', 'original_zip_verified']:
                bad = copy.deepcopy(self.frozen['provenance.json'])
                bad[field] = 0
                (package / 'provenance.json').write_bytes(review.encoded(bad))
                with self.subTest(field=field), patch.object(review, 'PACKAGE', package), \
                        self.assertRaisesRegex(ValueError, 'regeneration differs: provenance.json'):
                    review.main(['--check'])


if __name__ == '__main__':
    unittest.main()
