"""Focused source/operator regressions; no candidate gate or network."""
import argparse
import json
import re
import unittest
from pathlib import Path
import verify_packet as v
from source_tools import pre,normalize,section,replay

parser=argparse.ArgumentParser();parser.add_argument('--ref');args,rest=parser.parse_known_args();root=Path(__file__).resolve().parent
def load(name):return v.git_blob(args.ref,v.BASE+name)if args.ref else(root/name).read_bytes()
law=pre(load('pl119101.html'));a,b,body=section(law,908,909);baseline=normalize(body)
bank=json.loads(v.git_blob(v.SNAPSHOT,v.BANK))['sources'];by={x['source_id']:x for x in bank};text=by['govinfo:hr6955eh']['text'];a=text.index('SEC. 101.');eh=text[a:text.index('SEC. 102.',a)]


class Packet(unittest.TestCase):
    def altered_ledger(self,change):
        def altered(name):
            if name=='ledger.json':
                value=json.loads(load(name));change(value);return json.dumps(value,ensure_ascii=False).encode()
            return load(name)
        return altered
    def test_all_source_bindings_and_operations(self):v.validate(load)
    def test_actual_section_not_105_overcapture(self):
        self.assertEqual(len(body),6535);self.assertTrue(normalize(body).startswith('SEC. 908.'));self.assertNotIn('SEC. 105.',body)
    def test_NOTE_match_cannot_cross_closed_annotation(self):
        fake='SEC. <<NOTE: a.>> 105. Other. SEC. <<NOTE: b.>> 908. Body. SEC. 909. Next.'
        a,b,t=section(fake,908,909);self.assertEqual(normalize(t),'SEC. 908. Body.')
    def test_hyphen_word_join_preserves_paragraph_separator(self):
        self.assertEqual(normalize('90-\n day period.--\n (1) test'),'90-day period.-- (1) test')
    def test_law_before_stage_without_president_signature(self):
        x=json.loads(load('ledger.json'))['source_identity'];self.assertEqual(x['enactment_date'],'2026-07-11');self.assertEqual(x['House_stage_date'],'2026-07-21');self.assertIn('without President signature',x['enactment_mode'])
    def test_baseline_clocks_both_preserved(self):
        x=json.loads(load('ledger.json'))['clock_and_branch_inventory'];self.assertEqual(x['baseline_b2'],'180-day');self.assertEqual(x['baseline_b3'],'90-day')
    def test_b2_only_clock_becomes_90(self):
        r=replay(baseline,eh);self.assertIn('180-day',r['before_b2']);self.assertIn('90-day',r['after_b2']);self.assertNotIn('180-day',r['after_b2'])
    def test_b3_90_reference_unchanged(self):
        r=replay(baseline,eh);s=baseline[baseline.index('(3) Result of failure to act.'):baseline.index('(c) Pilot Program Study.')];self.assertIn('90-day',s);self.assertIn(s,r['after'])
    def test_decision_notice_and_denial_conditions(self):
        b2=replay(baseline,eh)['after_b2']
        for phrase in ['approve, conditionally approve, or deny','notify the applicant','if the agency denies','reason for such denial','suggest changes']:self.assertIn(phrase,b2)
    def test_two_institution_insurance_date_periods_retained(self):
        r=replay(baseline,eh);self.assertIn('may issue rules that provide for a 2-year phase-in period',r['after']);self.assertIn('During the 2-year period beginning on the date on which a qualifying community bank became an insured',r['after'])
    def test_joint_discretion_and2031window(self):
        p=replay(baseline,eh)['inserted_c2'];self.assertIn('may, jointly, determine',p);self.assertIn('Not earlier than January 1, 2031, and not later than June 30, 2031',p)
    def test_default_permanence_and_grandfather_reporting(self):
        p=replay(baseline,eh)['inserted_c2']
        for phrase in ['Unless the Federal banking agencies make the determination','shall be permanent','If the Federal banking agencies make the determination','before the date of such determination','make such report available to the public','the reasons for such determination']:self.assertIn(phrase,p)
    def test_report_redesignation_does_not_reset_deadline(self):
        r=replay(baseline,eh);self.assertTrue(r['after_report'].startswith('(3) Report'));self.assertIn('Not later than December 31, 2031',r['after_report']);self.assertEqual(r['before_report'][3:],r['after_report'][3:])
    def test_separate_de_novo_report_anchor_retained(self):
        r=replay(baseline,eh);old=baseline[baseline.index('(d) Study on De Novo'):baseline.index('(e) Definitions.')];self.assertIn(old,r['after']);self.assertIn('1-year period beginning on the date of enactment of this Act',old)
    def test_date_and_strict_assets_predicates(self):
        r=replay(baseline,eh);self.assertIn('between January 1, 2026, and December 31, 2028',baseline);self.assertNotIn(r['before_dates'],r['after']);self.assertIn('on or after January 1, 2026',r['after']);self.assertIn('less than $10,000,000,000',r['after']);self.assertIn('all of its subsidiaries and affiliates',r['after'])
    def test_comparator_stays_separate180_90(self):
        c=json.loads(load('ledger.json'))['EAS2_comparator'];self.assertIn('180-day',c['b2']);self.assertIn('90-day',c['b3']);self.assertFalse(c['whole_text_equivalence_claim'])
    def test_repeatability_and_isolation(self):
        first=replay(baseline,eh);first['after']='changed';self.assertNotEqual(first,replay(baseline,eh));self.assertEqual(replay(baseline,eh),replay(baseline,eh))
    def test_reject_comparator_claimed_as_enacted_base(self):
        with self.assertRaises(AssertionError):v.validate(self.altered_ledger(lambda x:x.__setitem__('base_source_kind','EAS2_proposal')))
    def test_reject_signed_law_claim(self):
        with self.assertRaises(AssertionError):v.validate(self.altered_ledger(lambda x:x['source_identity'].__setitem__('enactment_mode','signed by President')))
    def test_reject_wrong_stage_date(self):
        with self.assertRaises(AssertionError):v.validate(self.altered_ledger(lambda x:x['source_identity'].__setitem__('House_stage_date','2026-07-01')))
    def test_reject_other_section_delay_import(self):
        with self.assertRaises(AssertionError):v.validate(self.altered_ledger(lambda x:x['temporal_boundary'].__setitem__('section1001_specific_delay_applied_to908',True)))
    def test_reject_silent_baseline_clock_repair(self):
        with self.assertRaises(AssertionError):v.validate(self.altered_ledger(lambda x:x['clock_and_branch_inventory'].__setitem__('baseline_b3','180-day')))
    def test_reject_missing_public_report_in_after(self):
        def changed(name):return load(name).replace(b'make such report available to the public',b'keep such report private')if name=='proposed_after_101.txt'else load(name)
        with self.assertRaises(AssertionError):v.validate(changed)
    def test_reject_reapplying_to_already_amended_text(self):
        with self.assertRaises(AssertionError):replay(replay(baseline,eh)['after'],eh)


if __name__=='__main__':unittest.main(argv=[__file__]+rest,verbosity=2)
