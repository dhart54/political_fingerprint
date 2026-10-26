import copy
import unittest
from unittest.mock import patch

from backend.app.semantic_ir.shared_corpus import (
    digest,sealed_digest,candidate_update_impact,validate_member_projection,
    validate_shared_issue_mapping,SharedCorpusValidationError,
)
from scripts.validate_infrastructure_energy_governance_candidates153 import (
    ROOT,P,HEALTH,inputs,read,replay,validate,validate_manifest,validate_preservation,
    validate_inventory,validate_capture,validate_versions,validate_qualifications,
)


class EnergyGovernanceCandidates153Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=inputs()

    def changed(self,k):
        d=dict(self.data);d[k]=copy.deepcopy(d[k]);return d

    def test_actual_five_exact_choices_replay_held_with_conservation(self):
        r=validate(self.data);self.assertEqual((r['cores'],r['official_observations'],r['sources'],r['held_episodes'],r['issue_propositions']),(5,10,32,3,0));self.assertIs(r['canonical149_changed'],False);self.assertGreaterEqual(validate_preservation(),474);self.assertGreaterEqual(validate_manifest(),20)

    def test_member_overlays_reference_identical_shared_whole_choices(self):
        p=self.data['products'];by={a['action_id']:a for a in p['shared_action_core']['actions']}
        self.assertEqual([a['package_component_boundary']['boundary_type'] for a in by.values()],['whole_measure','exact_amendment','exact_amendment','exact_amendment','whole_measure'])
        for member in p['member_projections']:
            expected=['Yea','Nay','Nay','Nay','Nay'] if member['member_id']=='F000477' else ['Nay','Yea','Yea','Yea','Yea'];self.assertEqual([r['official_status'] for r in member['actions']],expected)
            for row in member['actions']:self.assertEqual(row['action_core_sha256'],by[row['action_id']]['action_core_sha256'])
        self.assertEqual(digest(replay(self.data['authoring'],self.data['sources'])),digest(p))

    def test_optional_research_nested_amounts_fees_and_queue_conditions_preserved(self):
        changes=[(73,'enumerated coordination activities are optional','enumerated coordination activities are mandatory'),(229,'$40million OF THAT AMOUNT','independent $40million'),(231,'already estimated at zero','estimated at $35million'),(236,'not a $2.053billion','a $2.053billion'),(279,'reliability OR grid resilience','reliability AND grid resilience')]
        for roll,old,new in changes:
            a=copy.deepcopy(self.data['authoring']);row=next(r for r in a['actions'] if r['action_id'].endswith(':'+str(roll)))
            for k in ['meaning','compact_description']:row[k]=row[k].replace(old,new)
            with self.subTest(roll=roll),self.assertRaises(ValueError):validate_qualifications(a)

    def test_RCP_floor_and_deemed_rule_reject_substantive_changes(self):
        original={s['source_id']:s for s in self.data['sources']['sources']}
        for sid,old,new in [('govinfo:hr1047eh','90 days','91 days'),('house-rules:energy153:RCP119-9','180 days','181 days'),('govinfo:energy153:1047-own-floor','So the bill was passed.','So the bill was rejected.'),('govinfo:hres707eh','119-9 shall be considered as adopted','119-8 shall be considered as adopted')]:
            pool=copy.deepcopy(original);self.assertIn(old,pool[sid]['text']);pool[sid]['text']=pool[sid]['text'].replace(old,new,1);pool[sid]['governed_bytes_sha256']=sealed_digest(pool[sid],'governed_bytes_sha256')
            with self.subTest(source=sid),self.assertRaises(ValueError):validate_versions(pool,self.data['conformance'])

    def test_resealed_original_baseline_and_exact_preimage_drift_fail(self):
        for sid in ['govinfo:hr1326eh','govinfo:42usc16512-2024','govinfo:hrpt119-213-eere']:
            d=self.changed('sources');s=next(s for s in d['sources']['sources'] if s['source_id']==sid);s['text']+=' invented effect';s['governed_bytes_sha256']=sealed_digest(s,'governed_bytes_sha256')
            with self.subTest(source=sid),self.assertRaises(ValueError):validate(d)
        d=self.changed('preflight');d['preflight']['cases'][0]['existing_binding_unresolved']=True;d['preflight']['preflight_sha256']=sealed_digest(d['preflight'],'preflight_sha256')
        with self.assertRaises(ValueError):validate(d)

    def test_archived_raw_byte_drift_is_detected_without_file_mutation(self):
        target=(ROOT/self.data['capture']['captures'][0]['raw_path']).resolve();original=type(target).read_bytes
        def changed(path):return original(path)+(b'drift' if path.resolve()==target else b'')
        with patch('pathlib.Path.read_bytes',changed),self.assertRaises(ValueError):validate_capture(self.data['capture'])

    def test_capture_caps_identity_redirects_and_retries_are_fixed(self):
        for kind in ['duplicate','float_cap','redirect','acceptance']:
            c=copy.deepcopy(self.data['capture'])
            if kind=='duplicate':c['captures'].append(copy.deepcopy(c['captures'][0]))
            elif kind=='float_cap':c['prospective_limits']['locators']=15.0
            elif kind=='redirect':c['captures'][0]['redirects'].append({'to':'https://example.invalid'})
            else:c['editorial_acceptance']=True
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate_capture(c)

    def test_candidate_mapping_cannot_accept_eligibility_or_binding_authority(self):
        p=self.data['products'];m=copy.deepcopy(p['shared_issue_mapping']);x=m['action_mappings'][0];x['eligibility']['decision']='accepted';x['mapping_sha256']=sealed_digest(x,'mapping_sha256');m['mapping_sha256']=sealed_digest(m,'mapping_sha256')
        with self.assertRaises(SharedCorpusValidationError):validate_shared_issue_mapping(ROOT,m,p['shared_action_core'])
        for k in ['accepted','canonical_application','publication','production']:
            for v in [True,0]:
                d=self.changed('bundle');d['bundle'][k]=v;d['bundle']['bundle_sha256']=sealed_digest(d['bundle'],'bundle_sha256')
                with self.subTest(field=k,value=v),self.assertRaises(ValueError):validate(d)

    def test_unused_raw_observation_changes_no_product(self):
        s=copy.deepcopy(self.data['sources']);x={'source_id':'synthetic:unused153','text':'Controlled unused observation, not evidence.'};x['governed_bytes_sha256']=sealed_digest(x,'governed_bytes_sha256');s['sources'].append(x);self.assertEqual(digest(replay(self.data['authoring'],s)),digest(self.data['products']))

    def test_shared_correction_rejects_both_stale_new_member_projections(self):
        p=self.data['products'];before=p['shared_action_core'];after=copy.deepcopy(before);x=after['actions'][0];x['candidate_shared_limitations'].append('CONTROLLED shared correction; no authority.');x['action_core_sha256']=sealed_digest(x,'action_core_sha256');after['corpus_sha256']=digest(after['actions']);self.assertTrue(candidate_update_impact(before,after,p['member_projections'],p['compiled_ir']))
        for member in p['member_projections']:
            with self.subTest(member=member['member_id']),self.assertRaises(SharedCorpusValidationError):validate_member_projection(ROOT,member,after)

    def test_actual_prior_Health236_core_invalidates_its_stale_member_rows(self):
        before=read(HEALTH/'generated/shared_action_core.json');after=copy.deepcopy(before);new=next(x for x in self.data['products']['shared_action_core']['actions'] if x['action_id']=='house:119:1:236');at=next(i for i,x in enumerate(after['actions']) if x['action_id']==new['action_id']);after['actions'][at]=copy.deepcopy(new);after['corpus_sha256']=digest(after['actions']);members=read(HEALTH/'generated/member_projections.json');compiled=read(HEALTH/'generated/compiled_ir.json');self.assertTrue(candidate_update_impact(before,after,members,compiled))
        for member in members:
            with self.subTest(member=member['member_id']),self.assertRaises(SharedCorpusValidationError):validate_member_projection(ROOT,member,after)

    def test_prior23_decisions_do_not_apply_or_invent_binding_requests(self):
        self.assertEqual(validate_inventory(self.data['inventory']),23)
        for kind in ['apply','request','resolved','proposal_count']:
            inv=copy.deepcopy(self.data['inventory'])
            if kind=='apply':inv['decisions_applied']=True
            elif kind=='request':next(c for c in inv['cases'] if c['batch']==152 and c['binding']['canonical_unresolved'])['binding']['original_binding_approval_requested']=True
            elif kind=='resolved':next(c for c in inv['cases'] if c['batch']==151 and c['binding']['canonical_unresolved'])['binding']['canonical_unresolved']=False
            else:inv['eligibility_proposal_counts']['proposed_inclusion']=19
            inv['inventory_sha256']=sealed_digest(inv,'inventory_sha256')
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate_inventory(inv)

    def test_claim_passages_must_exist_in_the_bound_operative_source(self):
        for field in ['passage','source_id']:
            a=copy.deepcopy(self.data['authoring']);a['actions'][0]['claim_source_map'][0][field]='unobserved invented claim'
            with self.subTest(field=field),self.assertRaises((ValueError,KeyError)):replay(a,self.data['sources'])

    def test_episode_holds_member_identity_and_zero_graph_fail_closed(self):
        for kind in ['hold','member','graph']:
            d=self.changed('authoring' if kind=='hold' else 'products')
            if kind=='hold':d['authoring']['blocked_episode_ids'].pop()
            elif kind=='member':d['products']['member_projections'][0]['actions'][0]['official_status']='Nay'
            else:d['products']['compiled_ir']['members'][0]['proposition_graph']['propositions'].append({'invented':True})
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate(d)


if __name__=='__main__':unittest.main()
