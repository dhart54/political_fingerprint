import copy
import unittest
from unittest.mock import patch

from backend.app.semantic_ir.shared_corpus import (
    digest, sealed_digest, validate_member_projection, validate_shared_issue_mapping,
    candidate_update_impact, SharedCorpusValidationError,
)
from scripts.validate_infrastructure_water_resource_candidates152 import (
    ROOT, P, inputs, replay, read, validate, validate_manifest, validate_preservation,
    validate_capture, validate_versions, validate_qualifications, compare_operative,
)


class WaterResourceCandidates152Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data=inputs()

    def changed(self,key):
        d=dict(self.data);d[key]=copy.deepcopy(d[key]);return d

    def test_actual_five_whole_choices_replay_held_and_preserve_canonical_state(self):
        r=validate(self.data)
        self.assertEqual((r['cores'],r['official_observations'],r['sources'],r['whole_motion_conformances']),(5,10,23,3))
        self.assertEqual(r['issue_propositions'],0)
        self.assertIs(r['canonical149_changed'],False)
        self.assertGreaterEqual(validate_preservation(),426)
        self.assertGreaterEqual(validate_manifest(),30)

    def test_two_members_reference_one_shared_whole_choice_per_roll(self):
        p=self.data['products'];core=p['shared_action_core'];by={a['action_id']:a for a in core['actions']}
        self.assertTrue(all(a['package_component_boundary']['boundary_type']=='whole_measure' for a in core['actions']))
        for member in p['member_projections']:
            self.assertEqual([x['official_status'] for x in member['actions']],['Yea']*5 if member['member_id']=='F000477' else ['Yea','Nay','Nay','Nay','Nay'])
            for x in member['actions']:self.assertEqual(x['action_core_sha256'],by[x['action_id']]['action_core_sha256'])
        self.assertEqual(digest(replay(self.data['authoring'],self.data['sources'])),digest(p))

    def test_qualified_whole_meanings_reject_lost_operators_and_conditions(self):
        mutations={187:('maximum extent practicable','without qualification'),776:('does not appropriate','appropriates'),2215:('three years after funds are made available','three years after enactment'),1917:('may purchase','must purchase'),6422:('only for assistance to nonfederal','for all assistance')}
        for bill,(old,new) in mutations.items():
            a=copy.deepcopy(self.data['authoring']);row=next(x for x in a['actions'] if x['bill_number']==bill)
            for field in ['meaning','compact_description']:row[field]=row[field].replace(old,new)
            with self.subTest(bill=bill),self.assertRaises(ValueError):validate_qualifications(a)

    def test_complete_body_comparison_rejects_substantive_glyph_changes(self):
        pool={x['source_id']:x for x in self.data['sources']['sources']}
        for c in self.data['conformance']['cases']:
            eh=pool[f"govinfo:hr{c['bill']}eh"]['text'];eh=eh[eh.index('Be it enacted'):eh.index('Passed the House')]
            full=(ROOT/c['full_extraction_path']).read_text(encoding='utf-8');start,end=c['operative_body'];body=full[start:end]
            compare_operative(eh,body)
            for kind,altered in [('truncated',body[:-50]),('negation',body+' not'),('number',body.replace('2025','2024',1))]:
                if altered==body:continue
                with self.subTest(bill=c['bill'],kind=kind),self.assertRaises(ValueError):compare_operative(eh,altered)

    def test_reviewed_scope_fiscal_funds_and_alternative_conditions_remain_precise(self):
        changes=[(187,'separately defines Federal waterways as waters managed by one or more of the relevant Secretaries','defines waterways as waters managed by the five agencies'),
                 (6422,'FY2027 NEP funds','all funds for implementation in FY2027'),
                 (6422,'OR to any nonfederal entity for projects conducted with','AND only for projects conducted with')]
        for bill,old,new in changes:
            a=copy.deepcopy(self.data['authoring']);row=next(x for x in a['actions'] if x['bill_number']==bill)
            for field in ['meaning','compact_description']:row[field]=row[field].replace(old,new)
            with self.subTest(bill=bill,clause=old),self.assertRaises(ValueError):validate_qualifications(a)

    def test_resealed_floor_or_outcome_substitution_cannot_pass(self):
        original={x['source_id']:x for x in self.data['sources']['sources']}
        for bill in [187,1917,6422]:
            for kind in ['body','outcome']:
                pool=copy.deepcopy(original);sid=f'govinfo:hr{bill}eh' if kind=='body' else f'govinfo:water152:hr{bill}-own-floor'
                pool[sid]['text']=pool[sid]['text'].replace('shall','may',1) if kind=='body' else pool[sid]['text'].replace('was passed','was rejected')
                pool[sid]['governed_bytes_sha256']=sealed_digest(pool[sid],'governed_bytes_sha256')
                with self.subTest(bill=bill,kind=kind),self.assertRaises(ValueError):validate_versions(pool,self.data['conformance'])

    def test_binding_flags_and_exact_case_decisions_do_not_gain_authority(self):
        self.assertEqual([x['existing_binding_unresolved'] for x in self.data['preflight']['cases']],[True,False,False,True,True])
        self.assertEqual([x['recommendation'] for x in self.data['bundle']['cases']],['propose_include_exact_case','propose_exclude_exact_case','route_exact_case_eligibility_review','propose_include_exact_case','propose_include_exact_case'])
        for field in ['accepted','canonical_application','publication','production']:
            for value in [True,0]:
                d=self.changed('bundle');d['bundle'][field]=value;d['bundle']['bundle_sha256']=sealed_digest(d['bundle'],'bundle_sha256')
                with self.subTest(field=field,value=value),self.assertRaises(ValueError):validate(d)
        d=self.changed('preflight');d['preflight']['cases'][0]['existing_binding_unresolved']=False;d['preflight']['preflight_sha256']=sealed_digest(d['preflight'],'preflight_sha256')
        with self.assertRaises(ValueError):validate(d)

    def test_capture_caps_retries_and_identity_cannot_be_resealed(self):
        for kind in ['duplicate','float_cap','redirect','acceptance']:
            c=copy.deepcopy(self.data['capture'])
            if kind=='duplicate':c['captures'].append(copy.deepcopy(c['captures'][0]))
            elif kind=='float_cap':c['prospective_limits']['locators']=15.0
            elif kind=='redirect':c['captures'][0]['redirects'].append({'to':'https://example.invalid'})
            else:c['canonical_registration']=True
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate_capture(c)

    def test_retained_raw_byte_drift_fails_without_mutating_archive(self):
        target=(ROOT/self.data['capture']['captures'][0]['raw_path']).resolve();original=type(target).read_bytes
        def changed(path):return original(path)+(b'drift' if path.resolve()==target else b'')
        with patch('pathlib.Path.read_bytes',changed),self.assertRaises(ValueError):validate_capture(self.data['capture'])

    def test_original_baseline_and_claim_drift_fail_closed(self):
        for sid in ['govinfo:hr187eh','govinfo:33usc1346-2024-operative','govinfo:water152:33usc1330-2024']:
            d=self.changed('sources');s=next(x for x in d['sources']['sources'] if x['source_id']==sid);s['text']+=' invented legal effect';s['governed_bytes_sha256']=sealed_digest(s,'governed_bytes_sha256')
            with self.subTest(source=sid),self.assertRaises(ValueError):validate(d)
        d=self.changed('authoring');d['authoring']['actions'][0]['claim_source_map'][0]['passage']='unobserved invented passage'
        with self.assertRaises(ValueError):replay(d['authoring'],d['sources'])

    def test_unused_raw_observation_cannot_change_any_product(self):
        s=copy.deepcopy(self.data['sources']);x={'source_id':'synthetic:unused152','text':'Controlled unused observation, not evidence.'};x['governed_bytes_sha256']=sealed_digest(x,'governed_bytes_sha256');s['sources'].append(x)
        self.assertEqual(digest(replay(self.data['authoring'],s)),digest(self.data['products']))

    def test_shared_correction_invalidates_both_stale_member_overlays(self):
        p=self.data['products'];before=p['shared_action_core'];after=copy.deepcopy(before);a=after['actions'][0]
        a['candidate_shared_limitations'].append('CONTROLLED shared correction, no authority.');a['action_core_sha256']=sealed_digest(a,'action_core_sha256');after['corpus_sha256']=digest(after['actions'])
        self.assertTrue(candidate_update_impact(before,after,p['member_projections'],p['compiled_ir']))
        for member in p['member_projections']:
            with self.subTest(member=member['member_id']),self.assertRaises(SharedCorpusValidationError):validate_member_projection(ROOT,member,after)

    def test_proposed_mapping_holds_and_zero_propositions_cannot_be_bypassed(self):
        p=self.data['products'];m=copy.deepcopy(p['shared_issue_mapping']);row=m['action_mappings'][0];row['eligibility']['decision']='accepted';row['mapping_sha256']=sealed_digest(row,'mapping_sha256');m['mapping_sha256']=sealed_digest(m,'mapping_sha256')
        with self.assertRaises(SharedCorpusValidationError):validate_shared_issue_mapping(ROOT,m,p['shared_action_core'])
        for kind in ['hold','member','graph']:
            d=self.changed('authoring' if kind=='hold' else 'products')
            if kind=='hold':d['authoring']['blocked_episode_ids'].pop()
            elif kind=='member':d['products']['member_projections'][1]['actions'][0]['official_status']='Nay'
            else:d['products']['compiled_ir']['members'][0]['proposition_graph']['propositions'].append({'invented':True})
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate(d)


if __name__ == '__main__':unittest.main()
