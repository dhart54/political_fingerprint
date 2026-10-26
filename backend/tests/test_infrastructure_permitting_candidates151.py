import copy
import unittest
from unittest.mock import patch

from backend.app.semantic_ir.shared_corpus import (
    digest, sealed_digest, validate_shared_issue_mapping, validate_member_projection,
    candidate_update_impact, SharedCorpusValidationError,
)
from scripts.validate_infrastructure_permitting_candidates151 import (
    ROOT, P, ACTIONS, inputs, read, replay, validate, validate_capture,
    validate_versions, validate_manifest, validate_preservation,
)


class PermittingCandidates151Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data = inputs()

    def changed(self, key):
        data = dict(self.data); data[key] = copy.deepcopy(data[key]); return data

    def test_actual_five_choices_replay_with_no_canonical_application(self):
        result = validate(self.data)
        self.assertEqual((result['cores'],result['official_observations'],result['sources']), (5,10,43))
        self.assertEqual(result['issue_propositions'],0)
        self.assertEqual(result['3898_operative_sections_conformed'],25)
        self.assertIs(result['canonical149_changed'],False)
        self.assertGreaterEqual(validate_preservation(),374)
        self.assertGreaterEqual(validate_manifest(),40)

    def test_member_overlays_reuse_one_shared_whole_choice(self):
        products = self.data['products']; core = products['shared_action_core']
        self.assertEqual([a['package_component_boundary']['boundary_type'] for a in core['actions']],
                         ['whole_measure','exact_amendment','exact_amendment','exact_amendment','whole_measure'])
        by_id = {a['action_id']:a for a in core['actions']}
        for projection in products['member_projections']:
            status = 'Nay' if projection['member_id']=='F000477' else 'Yea'
            for row in projection['actions']:
                self.assertEqual(row['official_status'],status)
                self.assertEqual(row['action_core_sha256'],by_id[row['action_id']]['action_core_sha256'])
        self.assertEqual(digest(replay(self.data['authoring'],self.data['sources'])),digest(products))

    def test_passage_flags_remain_unresolved_and_amendments_resolved(self):
        before = self.data['preflight']['cases']; decisions = self.data['bundle']['cases']
        self.assertEqual([c['existing_binding_unresolved'] for c in before],[True,False,False,False,True])
        self.assertEqual([d['canonical_binding_already_resolved'] for d in decisions],[False,True,True,True,False])
        self.assertTrue(all(d['binding_applied'] is False and d['meaning_accepted'] is False for d in decisions))
        for key,field in [('bundle','accepted'),('bundle','canonical_application'),('bundle','publication'),('bundle','production')]:
            for value in [True,0]:
                data=self.changed(key);data[key][field]=value
                with self.subTest(field=field,value=value),self.assertRaises(ValueError):validate(data)

    def test_whole_4776_cannot_omit_the_deemed_section4(self):
        for sid in ['govinfo:hr4776eh','govinfo:hres953eh']:
            pool={s['source_id']:copy.deepcopy(s) for s in self.data['sources']['sources']}
            source=pool[sid]
            source['text']=source['text'].replace('January 20, 2025','January 20, 2026')
            source['governed_bytes_sha256']=sealed_digest(source,'governed_bytes_sha256')
            with self.subTest(source=sid),self.assertRaises(ValueError):validate_versions(pool,self.data['conformance'])

    def test_3898_reconstruction_rejects_wrong_outcome_target_or_year(self):
        original={s['source_id']:s for s in self.data['sources']['sources']}
        for kind in ['outcome','cropland','material_clause']:
            pool=copy.deepcopy(original)
            if kind=='outcome':
                pool['govinfo:permitting151:3898-PERMIT-article']['text']=pool['govinfo:permitting151:3898-PERMIT-article']['text'].replace('The amendment was agreed to.','The amendment was rejected.',1)
            elif kind=='cropland':
                pool['govinfo:hr3898eh']['text']=pool['govinfo:hr3898eh']['text'].replace('preceding ten years','preceding five years')
            else:
                pool['govinfo:hr3898eh']['text']=pool['govinfo:hr3898eh']['text'].replace('each member of the organization','any member of the organization')
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate_versions(pool,self.data['conformance'])

    def test_old_voice_ayes_cannot_replace_recorded_amendment_rejections(self):
        for roll in [352,353,354]:
            d=self.changed('sources');source=next(s for s in d['sources']['sources'] if s['source_id']==f'clerk:119:1:{roll}')
            source['metadata']['vote-result']='Agreed to'
            source['governed_bytes_sha256']=sealed_digest(source,'governed_bytes_sha256')
            with self.subTest(roll=roll),self.assertRaises(ValueError):validate(d)

    def test_resealed_original_or_new_sources_and_preimages_fail(self):
        for sid in ['govinfo:hr4776rh','govinfo:33usc1341-2024-water-boundary','govinfo:permitting151:33usc1361-2024']:
            d=self.changed('sources');source=next(s for s in d['sources']['sources'] if s['source_id']==sid)
            source['text']+=' invented legal effect';source['governed_bytes_sha256']=sealed_digest(source,'governed_bytes_sha256')
            with self.subTest(source=sid),self.assertRaises(ValueError):validate(d)
        d=self.changed('preflight');d['preflight']['cases'][0]['existing_binding_unresolved']=False
        d['preflight']['preflight_sha256']=sealed_digest(d['preflight'],'preflight_sha256')
        with self.assertRaises(ValueError):validate(d)

    def test_caps_and_closed_routes_cannot_be_resealed_or_reopened(self):
        for kind in ['duplicate','cap_float','accept_rejected','metadata_range']:
            c=copy.deepcopy(self.data['capture'])
            if kind=='duplicate':c['captures'].append(copy.deepcopy(c['captures'][0]))
            elif kind=='cap_float':c['prospective_limits']['locators']=15.0
            elif kind=='accept_rejected':c['captures'][3]['identity_accepted']=True
            else:c['captures'][11]['requested_url']+='?range=next'
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate_capture(c)

    def test_actual_retained_byte_drift_fails_without_evidence_mutation(self):
        target=(ROOT/self.data['capture']['captures'][0]['raw_path']).resolve();original=type(target).read_bytes
        def changed(path):return original(path)+(b'drift' if path.resolve()==target else b'')
        with patch('pathlib.Path.read_bytes',changed),self.assertRaises(ValueError):validate_capture(self.data['capture'])

    def test_controlled_unused_raw_addition_cannot_create_meaning(self):
        capture=copy.deepcopy(self.data['sources']);s={'source_id':'synthetic:unused-raw151','text':'Controlled unused observation; not evidence.'}
        s['governed_bytes_sha256']=sealed_digest(s,'governed_bytes_sha256');capture['sources'].append(s)
        self.assertEqual(digest(replay(self.data['authoring'],capture)),digest(self.data['products']))

    def test_shared_correction_rejects_both_stale_member_projections(self):
        p=self.data['products'];before=p['shared_action_core'];after=copy.deepcopy(before)
        action=after['actions'][0];action['candidate_shared_limitations'].append('CONTROLLED shared correction; no authority.')
        action['action_core_sha256']=sealed_digest(action,'action_core_sha256');after['corpus_sha256']=digest(after['actions'])
        self.assertTrue(candidate_update_impact(before,after,p['member_projections'],p['compiled_ir']))
        for member in p['member_projections']:
            with self.subTest(member=member['member_id']),self.assertRaises(SharedCorpusValidationError):validate_member_projection(ROOT,member,after)

    def test_held_mapping_guard_and_product_replay_fail_closed(self):
        mapping=copy.deepcopy(self.data['products']['shared_issue_mapping']);row=mapping['action_mappings'][0]
        row['eligibility']['decision']='accepted';row['mapping_sha256']=sealed_digest(row,'mapping_sha256');mapping['mapping_sha256']=sealed_digest(mapping,'mapping_sha256')
        with self.assertRaises(SharedCorpusValidationError):validate_shared_issue_mapping(ROOT,mapping,self.data['products']['shared_action_core'])
        for kind in ['hold','member','graph']:
            d=self.changed('authoring' if kind=='hold' else 'products')
            if kind=='hold':d['authoring']['blocked_episode_ids'].pop()
            elif kind=='member':d['products']['member_projections'][0]['actions'][0]['official_status']='Yea'
            else:d['products']['compiled_ir']['members'][0]['proposition_graph']['propositions'].append({'invented':True})
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate(d)


if __name__ == '__main__': unittest.main()
