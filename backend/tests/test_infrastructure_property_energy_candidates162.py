"""Whole-choice source-version, qualification and held-authority regressions."""
import copy,unittest
from scripts import validate_infrastructure_property_energy_candidates162 as V
from backend.app.semantic_ir.shared_corpus import SharedCorpusValidationError,digest,validate_shared_issue_mapping,validate_member_projection

class HeldPropertyEnergy162(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=V.inputs()

    def changed(self,index,old,new):
        data=copy.deepcopy(self.data);action=data['authoring']['actions'][index];self.assertIn(old,action['meaning']);action['meaning']=action['meaning'].replace(old,new)
        with self.assertRaisesRegex(ValueError,'meaning/qualification/source scope'):V.validate(data)

    def test_complete_packet_and_native_replay(self):
        result=V.validate();self.assertEqual(result['propositions'],0);self.assertEqual(V.validate_manifests(),16);self.assertEqual(result['operational_queue_after_preparation']['not_prepared'],180)

    def test_zero_acquisition_retained_source_scope(self):
        V.validate_source_extent();self.assertEqual(len(V.validate_sources(self.data['sources'],self.data['authoring'])),17)

    def test_Wabeno_conditional_clocks_rights_and_whole_review(self):
        for old,new in [('within180days beginning on Federal appraisal approval','within180days after enactment'),('within180days AFTERreceiving that offer','within300days after appraisal'),('due300days AFTERenactment','due180days after an offer'),('ANDall conveyance costs','without any conveyance costs'),('mineral rights','excluding mineral rights')]:
            with self.subTest(old=old):self.changed(0,old,new)
        self.changed(0,'Separately, Interior must consult','Separately, Agriculture alone may ignore')
        self.changed(0,'MINORmaperrors','all parcel boundaries')
        self.changed(0,'for public inspection','only for private inspection')
        self.changed(0,'BOTHthe Uniform Appraisal Standards for Federal Land Acquisitions ANDthe Uniform Standards of Professional Appraisal Practice','either one of the two appraisal standards')

    def test_GSA_leased_tenant_consultation_sixmonth_and_baseline(self):
        for old,new in [('FEDERALLY LEASEDspace','all privately owned space'),('INCONSULTATIONWITHthose tenants','without consulting tenants'),('within6months AFTERenactment','within12months before enactment'),('baseline, broader property authority','baseline is fully integrated, broader property authority')]:
            with self.subTest(old=old):self.changed(1,old,new)

    def test_coal_charter_whole1013_and_qualified552b(self):
        for old,new in [('November19,2021','November19,2025'),('ALL5U.S.C.1013shallnotapply','only the two-year termination rule shallnotapply'),('does not establish a wholesale FACA exemption','establishes a wholesale FACA exemption'),('not a guarantee that every meeting is entirely open or secret','guarantees that every meeting is secret')]:
            with self.subTest(old=old):self.changed(2,old,new)

    def test_electric_assessment_frequency_and_no_nationality_finding(self):
        for old,new in [('PERIODICALLYthereafter','ANNUALLYthereafter'),('topics to assess, not established nationality-based threats','established nationality-based threats'),('recommend ways to address','mandate construction to address'),('generation/storage/transmission/distribution','generation/transmission only')]:
            with self.subTest(old=old):self.changed(3,old,new)

    def test_critical_material_FEC_alternatives_and_actors(self):
        for old,new in [('BOTH high disruption risk ANDessential','EITHER high disruption risk ORessential'),('ORan Interior-designated critical mineral','ANDan Energy-designated critical mineral'),('WITHconviction-for-underlying-activities','without conviction-for-underlying-activities'),('not silently transferred to every material route','automatically transferred to every material route'),('a person ORFederal/Stateagency SELLINGelectricity','only a private corporation generating electricity')]:
            with self.subTest(old=old):self.changed(3,old,new)
        self.changed(3,'without borrowing the Interior actor','by automatically borrowing the Interior actor')

    def test_ERO_printed_citation_and_definition_scope(self):
        for old,new in [('"42 U.S.C. 824o(a)"','"16 U.S.C. 824o(a)"'),('establishing ANDenforcing','establishing ORenforcing'),('SUBJECTTOCommissionreview','without Commissionreview'),('do NOToverride the bill','override the bill')]:
            with self.subTest(old=old):self.changed(3,old,new)

    def test_Perry_request_costs_public_use_discretion(self):
        for old,new in [('request deadline, not a180day conveyance-completion guarantee','180day conveyance-completion guarantee'),('no consideration ANDCounty-paid','no consideration ANDno County-paid'),('ONLYfor public purposes','for unrestricted private purposes'),('Secretary\'s DISCRETION, not automatic','Secretary\'s automatic duty'),('education/youth development are examples','education/youth development are exclusive requirements')]:
            with self.subTest(old=old):self.changed(4,old,new)

    def test_CERCLA_selected_unit_not_blanket_waiver(self):
        self.changed(4,'SELECTED9620(h)(1)–(3)unit','complete9620unit')
        self.changed(4,'not allCERCLAor proof that every notice, cleanup, access or responsibility disappears','a blanket waiver of all cleanup, notice and access duties')

    def test_resealed_canonical_source_cannot_drift(self):
        data=copy.deepcopy(self.data);source=next(s for s in data['sources']['sources']if s['source_id']=='govinfo:hr3937eh');source['text']=source['text'].replace('300 days','30 days');source['governed_bytes_sha256']=digest({k:v for k,v in source.items()if k!='governed_bytes_sha256'})
        with self.assertRaisesRegex(ValueError,'canonical retained source changed'):V.validate_sources(data['sources'],data['authoring'])

    def test_all_unresolved_flags_and_false_zero_stay_exact(self):
        for index in range(5):
            for value in [False,0]:
                data=copy.deepcopy(self.data);pre=data['preparation_preflight'];pre['cases'][index]['record']['exact_action_binding_unresolved']=value;pre['cases'][index]['record_sha256']=digest(pre['cases'][index]['record']);pre['preflight_sha256']=digest({k:v for k,v in pre.items()if k!='preflight_sha256'})
                with self.subTest(index=index,value=value),self.assertRaisesRegex(ValueError,'preflight subject/scope drift'):V.validate_preflight(pre)

    def test_no_acceptance_application_publication(self):
        for field in ['accepted','canonical_application','publication','production']:
            data=copy.deepcopy(self.data);bundle=data['decision_bundle'];bundle[field]=True;bundle['bundle_sha256']=digest({k:v for k,v in bundle.items()if k!='bundle_sha256'})
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'held decision bundle'):V.validate(data)

    def test_pending_binding_evidence_cannot_request_approval(self):
        original=V.read(V.P/'proposed_bindings.json')
        V.validate_binding_readiness(self.data['decision_bundle'],original)
        for target in ['bundle','evidence']:
            for index in range(5):
                for field,value in [('binding_approval_requested',True),('binding_review_ready',True),('binding_evidence_state','ready_for_approval'),('binding_approval_requested',0)]:
                    bundle=copy.deepcopy(self.data['decision_bundle']);evidence=copy.deepcopy(original);artifact=bundle if target=='bundle'else evidence;artifact['cases'][index][field]=value
                    with self.subTest(target=target,index=index,field=field),self.assertRaisesRegex(ValueError,'binding approval prematurely requested'):V.validate_binding_readiness(bundle,evidence)

    def test_all_candidate_accepted_mappings_reject(self):
        core=V.read(V.P/'generated/shared_action_core.json');mapping=V.read(V.P/'generated/shared_issue_mapping.json')
        for aid in V.ACTIONS:
            bad=copy.deepcopy(mapping);row=next(x for x in bad['action_mappings']if x['action_id']==aid);row['eligibility']['decision']='accepted';row['mapping_sha256']=digest({k:v for k,v in row.items()if k!='mapping_sha256'});bad['mapping_sha256']=digest({k:v for k,v in bad.items()if k!='mapping_sha256'})
            with self.subTest(aid=aid),self.assertRaisesRegex(SharedCorpusValidationError,'cannot claim accepted'):validate_shared_issue_mapping(V.ROOT,bad,core)

    def test_each_member_rejects_each_stale_binding(self):
        core=V.read(V.P/'generated/shared_action_core.json')
        for projection in V.read(V.P/'generated/member_projections.json'):
            for aid in V.ACTIONS:
                bad=copy.deepcopy(projection);next(x for x in bad['actions']if x['action_id']==aid)['action_core_sha256']='0'*64;bad['projection_sha256']=digest({k:v for k,v in bad.items()if k!='projection_sha256'})
                with self.subTest(aid=aid,member=projection['member_id']),self.assertRaisesRegex(SharedCorpusValidationError,'wrong action digest'):validate_member_projection(V.ROOT,bad,core)

if __name__=='__main__':unittest.main()
