import copy
import unittest
import os
import subprocess
import sys

from backend.app.semantic_ir.shared_corpus import digest
from scripts.prepare_shared_domain_candidate import prepare
from scripts.validate_infrastructure_land_siting_candidates143 import (
    ROOT, PACKET, MEMBERS, OUTPUTS, read, validate, validate_sources, validate_transport,
    validate_binding_boundaries, validate_member_neutral_authoring,
)


class LandSitingCandidates143Tests(unittest.TestCase):
    def test_sources_and_typed_replay_preserve_held_scope_and_not_voting(self):
        r=validate()
        self.assertEqual((r['actions'],r['cores'],r['official_observations']),(5,5,10))
        self.assertEqual((r['issue_propositions'],r['not_voting_observations']),(0,1))
        self.assertFalse(r['canonical_state_changed'])
        self.assertGreater(validate_transport(),90)

    def test_standalone_validators_do_not_require_pythonpath(self):
        env=dict(os.environ)
        env.pop('PYTHONPATH',None)
        for script in ['validate_infrastructure_disaster_candidates142.py','validate_infrastructure_land_siting_candidates143.py']:
            with self.subTest(script=script):
                run=subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT,env=env,
                                   text=True,encoding='utf8',capture_output=True)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                self.assertIn('"canonical_state_changed": false',run.stdout)

    def test_shared_meaning_cannot_take_the_member_observation_layer(self):
        a=read(PACKET/'authoring.json')
        for field,leak in [('meaning','Massie voted against the museum.'),
                           ('short_description','Foushee supports this.'),
                           ('compact_description','m001184 did not vote.')]:
            bad=copy.deepcopy(a);bad['actions'][3][field]+=' '+leak
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'member-specific'):
                validate_member_neutral_authoring(bad)

    def test_shared_core_is_identical_when_member_order_changes(self):
        a=read(PACKET/'authoring.json');s=read(PACKET/'sources.json')
        core,mapping,_,_,_=prepare(a,s,MEMBERS)
        other_core,other_mapping,projections,_,_=prepare(a,s,list(reversed(MEMBERS)))
        self.assertEqual(digest(core),digest(other_core))
        self.assertEqual(digest(mapping),digest(other_mapping))
        self.assertEqual(projections[0]['member_id'],'M001184')
        self.assertEqual(projections[0]['actions'][3]['exact_choice_effect'],'resolved_non_directional')

    def test_soft404_or_expanded_extents_cannot_become_context(self):
        u=read(PACKET/'source_units.json')
        for change in ['soft404','extent','whole_parent']:
            bad=copy.deepcopy(u)
            if change=='soft404':
                next(x for x in bad['units'] if x['capture_key']=='25usc177_publisherlocated')['capture_key']='25usc177'
            elif change=='extent':
                next(x for x in bad['units'] if 'html_extent' in x)['html_extent']['end']+=1
            else:
                next(x for x in bad['units'] if 'pdf_normalized_page_extents' in x)['whole_parent_document_reviewed']=True
            with self.subTest(change=change),self.assertRaises(ValueError):validate_sources(units=bad)

    def test_prior_amendment_or_neighbor_outcome_cannot_bind_A7(self):
        original=read(PACKET/'sources.json')
        units={u['unit_key']:u['source_id'] for u in read(PACKET/'source_units.json')['units']}
        for change in ['prior_roll','rejected_A6','adjacent_operative']:
            bad=copy.deepcopy(original);pool={x['source_id']:x for x in bad['sources']}
            if change=='prior_roll':pool[units['partA7_resumption_roll260']]['text']=pool[units['partA7_resumption_roll260']]['text'].replace('[Roll No. 260]','[Roll No. 259]')
            elif change=='rejected_A6':pool[units['partA7_roll260_result']]['text']='So the amendment was rejected.'
            else:pool[units['partA7_operative']]['text']+=' AMENDMENT NO. 8'
            with self.subTest(change=change),self.assertRaises(ValueError):validate_binding_boundaries(bad)

    def test_failed_museum_vote_and_literal_III_cannot_be_repaired(self):
        original=read(PACKET/'sources.json');units={u['unit_key']:u['source_id'] for u in read(PACKET/'source_units.json')['units']}
        for key,old,new in [('hr1329_passage_result','was not passed','was passed'),
                            ('hr1329_recommit_rejected','was rejected','was agreed to'),
                            ('partA7_operative','subchapter III','subchapter II')]:
            bad=copy.deepcopy(original);source=next(x for x in bad['sources'] if x['source_id']==units[key]);source['text']=source['text'].replace(old,new)
            with self.subTest(key=key),self.assertRaises(ValueError):validate_binding_boundaries(bad)

    def test_generated_not_voting_hold_and_authority_cannot_drift(self):
        o={k:read(PACKET/'generated'/(k+'.json')) for k in OUTPUTS}
        for change in ['NV','hold','authority']:
            bad=copy.deepcopy(o)
            if change=='NV':bad['member_projections'][1]['actions'][3]['official_status']='Nay'
            elif change=='hold':bad['shared_issue_mapping']['source_render_constraints']=[]
            else:bad['readable_candidates']['production_eligible']=True
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'replay'):validate(outputs=bad)

    def test_review_clearance_cannot_apply_candidates_or_accept_meanings(self):
        b=read(PACKET/'decision_bundle.json')
        for key,value in [('semantic_acceptance',True),('canonical_state_changed',True),('publication_authorized',True),
                          ('batch142_or_HR859_or_HR28_accepted',True),('six_source_holds_changed',0)]:
            bad=copy.deepcopy(b);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate(bundle=bad)


if __name__=='__main__':
    unittest.main()
