"""Focused source/replay/mutation checks; no candidate gate or network."""
import argparse
import json
import re
import unittest
from pathlib import Path
import verify_packet as v
from source_tools import field,replay

parser=argparse.ArgumentParser();parser.add_argument('--ref');args,rest=parser.parse_known_args()
root=Path(__file__).resolve().parent
def load(name):return v.git_blob(args.ref,v.BASE+name)if args.ref else(root/name).read_bytes()
raw=load('govinfo_2024_1812.html');op=field(raw,'statute')
bank=json.loads(v.git_blob(v.SNAPSHOT,v.BANK))['sources'];text=next(x['text']for x in bank if x['source_id']=='govinfo:hr6955eh');a=text.index('SEC. 401.');eh=text[a:text.index('SEC. 402.',a)]


class Packet(unittest.TestCase):
    def changed_loader(self,name,change):
        def changed(path):
            if path==name:
                value=json.loads(load(path));change(value);return json.dumps(value,ensure_ascii=False).encode()
            return load(path)
        return changed

    def test_complete_source_and_replay(self):v.validate(load)
    def test_citizenship_is_carried_text(self):
        r=replay(op,eh);phrase='from among individuals who are citizens of the United States'
        self.assertIn(phrase,r['old_C']);self.assertIn(phrase,r['new_C'])
    def test_state_experience_retained(self):
        r=replay(op,eh);self.assertIn('1 of whom shall have State bank supervisory experience',r['old_C']);self.assertIn('1 of whom shall have State bank supervisory experience',r['new_C'])
    def test_new_experience_strict_threshold_and_separately(self):
        r=replay(op,eh);self.assertIn('and separately 1 of whom',r['new_C']);self.assertIn('having less than $17,000,000,000',r['new_C'])
    def test_rename_all_five_only_operative(self):
        r=replay(op,eh);self.assertEqual(r['rename_count'],5);self.assertNotIn(r['rename_from'],r['after_text']);self.assertEqual(r['after_text'].count(r['rename_to']),5)
    def test_six_year_term_and_two_term_append_distinct(self):
        r=replay(op,eh);self.assertTrue(r['new_c1'].startswith(r['old_c1']));self.assertIn('more than two terms',r['new_c1'])
    def test_total_cap_keeps_notwithstanding(self):self.assertIn('Notwithstanding any other provision of this Act',replay(op,eh)['new_c4'])
    def test_tables_have_positive_controls_and_no_target(self):
        self.assertEqual(len(v.classification_check(load('olrc_119_1_code_order.html'),21,['1','3702'])),21)
        self.assertEqual(len(v.classification_check(load('olrc_119_2_code_order.html'),46,['1811','1820'])),46)
    def test_currentthrough_comes_from_dated_raw_metadata(self):self.assertIn(b'currentthrough:20250106',raw)
    def test_soft404_excluded_despite_http200(self):
        r=next(x for x in json.loads(load('capture_receipts.json'))if '2025'in x['file']);self.assertEqual(r['http_status'],200);self.assertFalse(r['usable']);self.assertIn(b'Page Not Found | GovInfo',load(r['file']))
    def test_repeatability_and_input_isolation(self):
        before=(op,eh);first=replay(op,eh);first['after_text']='mutated';self.assertEqual((op,eh),before);self.assertEqual(replay(op,eh),replay(op,eh));self.assertNotEqual(first,replay(op,eh))
    def test_reject_new_citizenship_claim(self):
        change=lambda x:x['carried_language']['citizenship'].__setitem__('textually_new',True)
        with self.assertRaises(AssertionError):v.validate(self.changed_loader('comparison.json',change))
    def test_reject_tenure_in_political_affiliation_subsection(self):
        change=lambda x:x['tenure_context'].__setitem__('target_subsection','(a)(2)')
        with self.assertRaises(AssertionError):v.validate(self.changed_loader('comparison.json',change))
    def test_reject_inclusive_threshold_operator(self):
        with self.assertRaises(AssertionError):replay(op,eh.replace('having less than $17,000,000,000','having at most $17,000,000,000'))
    def test_reject_soft404_promotion(self):
        def change(x):next(r for r in x if '2025'in r['file']).__setitem__('usable',True)
        with self.assertRaises(AssertionError):v.validate(self.changed_loader('capture_receipts.json',change))
    def test_reject_missing_holdover_in_synthetic_after(self):
        def changed(name):return load(name).replace(b'until a successor has been appointed and qualified',b'')if name=='proposed_after_2024.txt'else load(name)
        with self.assertRaises(AssertionError):v.validate(changed)
    def test_reject_new_1812_table_entry(self):
        original=load('olrc_119_2_code_order.html')
        bad,n=re.subn(rb'</pre>',b'\n12 1812 119-121 9 1069\n</pre>',original,count=1,flags=re.I)
        self.assertEqual(n,1)
        self.assertTrue(bad!=original)
        with self.assertRaises(AssertionError):v.classification_check(bad,47,['1811','1820'])
    def test_reject_wrong_claimed_baseline_currency(self):
        change=lambda x:x.__setitem__('baseline_currentthrough','2026-01-06')
        with self.assertRaises(AssertionError):v.validate(self.changed_loader('currency_boundary.json',change))


if __name__=='__main__':unittest.main(argv=[__file__]+rest,verbosity=2)
