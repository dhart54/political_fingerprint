"""Focused source/semantic/held-authority checks for five candidate choices."""
import copy, unittest
from scripts import validate_infrastructure_administrative_information_candidates161 as V
from backend.app.semantic_ir.shared_corpus import (
    SharedCorpusValidationError, digest, validate_shared_issue_mapping,
    validate_member_projection,
)

class HeldAdministrativeInformation161(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=V.inputs()

    def changed_meaning(self,index,old,new):
        data=copy.deepcopy(self.data);action=data['authoring']['actions'][index]
        self.assertIn(old,action['meaning']);action['meaning']=action['meaning'].replace(old,new)
        with self.assertRaisesRegex(ValueError,'meaning/qualification/source scope'):V.validate(data)

    def test_complete_packet_and_native_replay(self):
        self.assertEqual(V.validate()['propositions'],0)
        self.assertEqual(V.validate_manifests(),27)
        self.assertEqual(V.queue_accounting(self.data['preparation_preflight'])['not_prepared'],185)

    def test_bounded_capture_and_complete_operatives(self):
        V.validate_capture();self.assertEqual(len(V.validate_sources(self.data['sources'],self.data['authoring'])),18)

    def test_initial_locators_and_literal_mover_discrepancy(self):
        for index in range(4):
            data=copy.deepcopy(self.data);action=data['authoring']['actions'][index]
            next(c for c in action['claim_source_map'] if c['source_id'].startswith('govinfo:admin161:'))['locator']='Initial passage also contains final question and postponement'
            with self.subTest(index=index),self.assertRaisesRegex(ValueError,'initial locator overstates'):V.validate_sources(data['sources'],data['authoring'])
        data=copy.deepcopy(self.data);action=data['authoring']['actions'][2];action['limitations']=[x for x in action['limitations'] if 'Comer/Boebert' not in x]
        with self.assertRaisesRegex(ValueError,'literal mover discrepancy omitted'):V.validate_sources(data['sources'],data['authoring'])

    def test_disaster_discretion_written_request_and_future_declarations(self):
        for old,new in [('permit the Treasury Secretary','require the Treasury Secretary'),('written request','any request'),('after consultation with FEMA','without consultation with FEMA'),('declarations after enactment','every prior declaration')]:
            with self.subTest(old=old):self.changed_meaning(0,old,new)

    def test_separate_mandatory_extension_terms(self):
        self.changed_meaning(0,'specified mandatory-extension 60-day terms with 120 days','every tax deadline with an automatic120days')

    def test_counsel_delegate_officewide_and_as_if_limits(self):
        for old,new in [('or a delegate','with no delegation'),('any employee of the Office','only local employees of the Office'),('as included in section1102 of the1998','as current unconditional authority under the1998')]:
            with self.subTest(old=old):self.changed_meaning(1,old,new)

    def test_zip_all66_single_unique_postenactment_no_route_inference(self):
        for old,new in [('within270days after enactment','immediately before enactment'),('66 separately enumerated','65 separately enumerated'),('does not itself establish municipal boundaries','also changes municipal boundaries')]:
            with self.subTest(old=old):self.changed_meaning(2,old,new)

    def test_PRA_selected_duties_and_exceptions(self):
        for old,new in [('expressly retaining requirements','expressly removing requirements'),('under the identified subsection','for every SEC collection'),('not incorporate all(c)(2)/(3)','automatically incorporates all(c)(2)/(3)')]:
            with self.subTest(old=old):self.changed_meaning(3,old,new)

    def test_senate_repeal_whole_target_and_conditional_remedy(self):
        for old,new in [('AND the amendments','but not the amendments'),('prevailing-claim greater-of500000dollars-or-actual-damages','automatic500000dollar'),('at most60days','indefinite periods'),('no general elimination of all Senate','general elimination of all Senate'),('prior-law revival','guaranteed prior-law revival')]:
            with self.subTest(old=old):self.changed_meaning(4,old,new)

    def test_canonical_source_change_rejected_even_after_resealing(self):
        data=copy.deepcopy(self.data);source=next(s for s in data['sources']['sources'] if s['source_id']=='govinfo:hr517eh');source['text']+=' invented clause'
        source['governed_bytes_sha256']=digest({k:v for k,v in source.items()if k!='governed_bytes_sha256'})
        with self.assertRaisesRegex(ValueError,'canonical retained source changed'):V.validate_sources(data['sources'],data['authoring'])

    def test_offering_body_change_rejected_even_after_resealing(self):
        data=copy.deepcopy(self.data);source=next(s for s in data['sources']['sources']if s['source_id']=='govinfo:admin161:hr3095-offering');source['text']=source['text'].replace('270 days','27 days')
        source['governed_bytes_sha256']=digest({k:v for k,v in source.items()if k!='governed_bytes_sha256'})
        with self.assertRaisesRegex(ValueError,'offering extraction changed'):V.validate_sources(data['sources'],data['authoring'])

    def test_unresolved_binding_and_false_zero_are_not_silently_applied(self):
        for value in [False,0]:
            data=copy.deepcopy(self.data);pre=data['preparation_preflight'];pre['cases'][0]['record']['exact_action_binding_unresolved']=value
            pre['cases'][0]['record_sha256']=digest(pre['cases'][0]['record']);pre['preflight_sha256']=digest({k:v for k,v in pre.items()if k!='preflight_sha256'})
            with self.assertRaisesRegex(ValueError,'preflight subject/scope drift'):V.validate_preflight(pre)

    def test_decision_cannot_accept_apply_or_omit_cases(self):
        for field in ['accepted','canonical_application','publication','production']:
            data=copy.deepcopy(self.data);bundle=data['decision_bundle'];bundle[field]=True;bundle['bundle_sha256']=digest({k:v for k,v in bundle.items()if k!='bundle_sha256'})
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'held decision bundle'):V.validate(data)

    def test_each_candidate_rejects_accepted_mapping(self):
        core=V.read(V.P/'generated/shared_action_core.json');mapping=V.read(V.P/'generated/shared_issue_mapping.json')
        for aid in V.ACTIONS:
            bad=copy.deepcopy(mapping);row=next(x for x in bad['action_mappings']if x['action_id']==aid);row['eligibility']['decision']='accepted';row['mapping_sha256']=digest({k:v for k,v in row.items()if k!='mapping_sha256'});bad['mapping_sha256']=digest({k:v for k,v in bad.items()if k!='mapping_sha256'})
            with self.subTest(aid=aid),self.assertRaisesRegex(SharedCorpusValidationError,'cannot claim accepted'):validate_shared_issue_mapping(V.ROOT,bad,core)

    def test_both_members_reject_each_stale_core_binding(self):
        core=V.read(V.P/'generated/shared_action_core.json')
        for projection in V.read(V.P/'generated/member_projections.json'):
            for aid in V.ACTIONS:
                bad=copy.deepcopy(projection);next(x for x in bad['actions']if x['action_id']==aid)['action_core_sha256']='0'*64;bad['projection_sha256']=digest({k:v for k,v in bad.items()if k!='projection_sha256'})
                with self.subTest(aid=aid,member=projection['member_id']),self.assertRaisesRegex(SharedCorpusValidationError,'wrong action digest'):validate_member_projection(V.ROOT,bad,core)

if __name__=='__main__':unittest.main()
