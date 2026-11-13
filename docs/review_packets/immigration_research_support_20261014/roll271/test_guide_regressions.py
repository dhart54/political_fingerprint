"""Focused research-guide/source regressions; no candidate tests or writes.

python -X utf8 path/to/roll271/test_guide_regressions.py --ref HEAD
Each of nine reviewed distinctions has a source-backed positive check and
negative probes changing each duplicate guide field independently. Tests use
fresh deep copies for every target.
"""
import argparse
import copy
import json
import unittest
from pathlib import Path

import verify_packet as verifier

PARSER = argparse.ArgumentParser()
PARSER.add_argument('--ref')
ARGS, REST = PARSER.parse_known_args()
NAMES = ['source_identities.json','section_ledger.json','imports.json',
         'read_receipt.json','guide_review.json']
ROOT = Path(__file__).resolve().parent
PRIOR = 'c3c108a05f1132a38172c33b2e8463c4a3c663d2'


def packet_bytes(name):
    return (verifier.git_blob(ARGS.ref,verifier.BASE+name) if ARGS.ref
            else (ROOT/name).read_bytes())


DOCUMENTS = {name:json.loads(packet_bytes(name)) for name in NAMES}
RAW_BANK = verifier.git_blob(verifier.SNAPSHOT,verifier.BANK)


def replace_target(documents, rule, index=0):
    target = rule['targets'][index]
    container = documents[target['file']]
    for component in target['path'][:-1]:
        container = container[component]
    key = target['path'][-1]
    old,new = rule['bad_replacement']
    assert old in container[key]
    container[key] = container[key].replace(old,new)


class GuideRegressions(unittest.TestCase):
    def test_duplicate_notes_remain_consistent(self):
        notes = DOCUMENTS['read_receipt.json']['section_notes']
        for row in DOCUMENTS['section_ledger.json']['sections']:
            self.assertEqual(row['operator_conditions_exceptions_dates'],notes[row['section']])

    def test_literal_evidence_and_historical_attribution_unchanged(self):
        def passages(value):
            result = []
            if isinstance(value,dict):
                if {'source_id','start','end','text','passage_utf8_sha256'} <= value.keys():
                    result.append({k:value[k] for k in ['source_id','start','end','text','passage_utf8_sha256']})
                for child in value.values():
                    result.extend(passages(child))
            elif isinstance(value,list):
                for child in value:
                    result.extend(passages(child))
            return result
        for name in ['section_ledger.json','imports.json']:
            original = json.loads(verifier.git_blob(PRIOR,verifier.BASE+name))
            self.assertEqual(passages(original),passages(DOCUMENTS[name]))
        for name in ['source_identities.json','timing_and_scope.json']:
            self.assertEqual(verifier.git_blob(PRIOR,verifier.BASE+name),packet_bytes(name))
        original = json.loads(verifier.git_blob(PRIOR,verifier.BASE+'read_receipt.json'))
        current = copy.deepcopy(DOCUMENTS['read_receipt.json'])
        current.pop('guide_notes_revision')
        current.pop('section_notes')
        original.pop('section_notes')
        self.assertEqual(original,current)

    def test_nested_mutation_does_not_leak_into_shared_inputs(self):
        original = copy.deepcopy(DOCUMENTS)
        rule = DOCUMENTS['guide_review.json']['rules'][0]
        altered = copy.deepcopy(DOCUMENTS)
        replace_target(altered,rule)
        with self.assertRaises(AssertionError):
            verifier.validate_guide_rule(altered,RAW_BANK,rule)
        self.assertEqual(DOCUMENTS,original)
        verifier.validate_guide_rule(DOCUMENTS,RAW_BANK,rule)


def positive(rule):
    def test(self):
        verifier.validate_guide_rule(copy.deepcopy(DOCUMENTS),RAW_BANK,rule)
    return test


def negative(rule):
    def test(self):
        for index,target in enumerate(rule['targets']):
            with self.subTest(target=target):
                altered = copy.deepcopy(DOCUMENTS)
                replace_target(altered,rule,index)
                with self.assertRaises(AssertionError):
                    verifier.validate_guide_rule(altered,RAW_BANK,rule)
    return test


for RULE in DOCUMENTS['guide_review.json']['rules']:
    setattr(GuideRegressions,'test_source_backed_'+RULE['id'],positive(RULE))
    setattr(GuideRegressions,'test_reject_wrong_guide_'+RULE['id'],negative(RULE))


if __name__ == '__main__':
    unittest.main(argv=[__file__]+REST,verbosity=2)
