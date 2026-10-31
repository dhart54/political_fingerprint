"""Whole-choice evidence chains, member neutrality and held authority for163."""
import copy,unittest
from scripts import validate_infrastructure_energy_regulation_candidates163 as V
from backend.app.semantic_ir.shared_corpus import SharedCorpusValidationError,digest,validate_shared_issue_mapping,validate_member_projection

class HeldEnergyRegulation163(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=V.inputs();cls.procedural=V.read(V.P/'procedural_witnesses.json');cls.evidence=V.read(V.P/'proposed_bindings.json')

    def changed(self,index,old,new):
        data=copy.deepcopy(self.data);a=data['authoring']['actions'][index];self.assertIn(old,a['meaning']);a['meaning']=a['meaning'].replace(old,new)
        with self.assertRaisesRegex(ValueError,'meaning/qualification/source scope'):V.validate(data)

    def test_packet_native_replay_and_actual_queue(self):
        r=V.validate();self.assertEqual(V.validate_manifests(),21);self.assertEqual(r['propositions'],0);self.assertEqual(r['prepared_binding_proposals'],2);self.assertEqual(r['operational_queue_after_preparation']['not_prepared'],175)

    def test_capture_and_procedural_source_bounds(self):
        V.validate_source_extent();self.assertEqual(len(V.validate_sources(self.data['sources'],self.data['authoring'])),18)
        V.validate_binding_readiness(self.data['decision_bundle'],self.evidence,self.data['sources'],self.procedural)

    def test_shared_meaning_cannot_contain_member_status(self):
        for name in ['Massie','Foushee','M001184','F000477']:
            a=copy.deepcopy(self.data['authoring']);a['actions'][0]['meaning']+=' '+name+' voted against the bill.'
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'member-specific'):V.validate_member_neutral(a)

    def test_LNG_trade_deeming_is_not_facility_approval(self):
        for old,new in [('APPROVE ORDENY','automatically APPROVE'),('EXPORTATION/IMPORTATIONconsistent','every facility automatically consistent'),('Other-agency applicable-law responsibilities remain','Other-agency responsibilities disappear'),('preserves the printed Constitution','removes the printed Constitution')]:
            with self.subTest(old=old):self.changed(0,old,new)

    def test_LNG_literal_citation_anomaly_stays_unrepaired(self):
        self.changed(0,'50U.S.C.4318(c)(1)(A)','50U.S.C.4813(c)(1)(A)')
        self.changed(0,'unrelated naturalized-citizen expatriation claims','the operative terrorism-designation criteria')

    def test_shower_unretained_standard_safety_and_conforming_clock(self):
        for old,new in [('EXCEPTsafetyshower showerheads','INCLUDINGsafetyshower showerheads'),('within180days AFTERenactment','within90days BEFOREenactment'),('not retained or inspected','fully retained and inspected'),('no single-versus-multiple-nozzle/head/device counting','a definitive multiple-nozzle counting rule')]:
            with self.subTest(old=old):self.changed(1,old,new)

    def test_mining_whole_package_clocks_and_eligibility(self):
        for old,new in [('within10days AFTERthat list','within10days BEFOREenactment'),('CANIMMEDIATELYapprove','must automatically approve'),('BOTHquick permitting/operation ANDgreatest','EITHERquick permitting/operation ORgreatest'),('not repeal of those State/local laws','repeal of those State/local laws'),('coal/oil/oilshale/gas/sodium/potassium/sulfur/MaterialsActmaterials are excluded','coal/oil/oilshale/gas/sodium/potassium/sulfur/MaterialsActmaterials are all included'),('not independent realized outcomes','independently established realized outcomes')]:
            with self.subTest(old=old):self.changed(2,old,new)

    def test_air_distinct_geography_causes_mobile_and_renewal(self):
        for old,new in [('OUTSIDETHE NONATTAINMENTAREA','only OUTSIDETHE UNITEDSTATES'),('ONEORMOREof','ALLTHREEof'),('BOTHbeyond-State-control-to-reduce/eliminate ANDfull','EITHERbeyond-State-control-to-reduce/eliminate ORfull'),('Underlying duties to establish/implement attainment measures remain','Underlying attainment duties disappear'),('ATLEASTONCEEVERY5YEARS','only once five years after enactment'),('PM10heading/carbon-monoxide-body','PM10heading/PM10body')]:
            with self.subTest(old=old):self.changed(3,old,new)

    def test_geothermal_predicates_royalties_tribal_and_historic_scope(self):
        for old,new in [('LESSTHAN50PERCENT','50PERCENTORLESS'),('SUBMITSANACTUALSTATEPERMIT','merely applies for a State permit'),('MAYCOMMENCE30days AFTERsubmission','must receive Federal approval within30days'),('ONLYIFthe State has NOLAW','whenever the State has an inadequate law'),('does not establish allroyalties waived','waives all royalties'),('DOESNOTAPPLYto actions on Indianlands ORresources','APPLIESto actions on Indianlands ANDresources')]:
            with self.subTest(old=old):self.changed(4,old,new)

    def test_NotVoting_is_resolved_non_directional_and_source_bound(self):
        projections=V.read(V.P/'generated/member_projections.json');p=next(x for x in projections if x['member_id']=='M001184');self.assertEqual(p['actions'][0]['official_status'],'Not Voting')
        ir=V.read(V.P/'generated/compiled_ir.json');m=next(x for x in ir['members']if x['member_id']=='M001184');self.assertEqual(m['coverage']['directional_yes_no_positions'],4);self.assertEqual(m['coverage']['not_voting_actions'],1);self.assertEqual(m['coverage']['missing_evidence_actions'],0);self.assertEqual(m['coverage']['resolved_eligible_actions'],5)
        for status in ['Yea','Nay','Missing Evidence']:
            data=copy.deepcopy(self.data);s=next(x for x in data['sources']['sources']if x['source_id']=='clerk:119:1:304');s['member_records']['M001184']['official_label']=status;s['governed_bytes_sha256']=digest({k:v for k,v in s.items()if k!='governed_bytes_sha256'})
            with self.subTest(status=status),self.assertRaisesRegex(ValueError,'canonical retained source changed'):V.validate_sources(data['sources'],data['authoring'])

    def test_reported_body_cannot_drift_after_resealing(self):
        data=copy.deepcopy(self.data);s=next(x for x in data['sources']['sources']if x['source_id']=='govinfo:energy163:hr4090rh-substitute');self.assertIn('10 days',s['text']);s['text']=s['text'].replace('10 days','11 days');s['governed_bytes_sha256']=digest({k:v for k,v in s.items()if k!='governed_bytes_sha256'})
        with self.assertRaisesRegex(ValueError,'reported substitute extent changed'):V.validate_sources(data['sources'],data['authoring'])

    def test_unrelated_adjacent_or_previous_question_role_is_rejected(self):
        chain=copy.deepcopy(self.evidence['prepared_chains'][1]);extra=copy.deepcopy(chain['procedural_witnesses'][0]);extra['role']='motion_to_recommit';extra['source_id']='clerk:119:2:136';chain['procedural_witnesses'].append(extra)
        with self.assertRaisesRegex(ValueError,'procedural role'):V.validate_prepared_chain(chain,self.data['sources'],self.procedural)
        chain=copy.deepcopy(self.evidence['prepared_chains'][0]);chain['procedural_witnesses'][0]['source_id']='clerk:119:2:51'
        with self.assertRaisesRegex(ValueError,'procedural source identity'):V.validate_prepared_chain(chain,self.data['sources'],self.procedural)

    def test_each_procedural_measure_question_date_and_outcome_is_bound(self):
        for original in self.evidence['prepared_chains']:
            for field,value in [('legis-num','H R 6387'),('vote-question','On Passage'),('vote-result','Failed'),('action-date','1-Jan-2020')]:
                chain=copy.deepcopy(original);chain['procedural_witnesses'][0]['metadata'][field]=value
                with self.subTest(bill=chain['bill'],field=field),self.assertRaisesRegex(ValueError,'procedural source identity'):V.validate_prepared_chain(chain,self.data['sources'],self.procedural)

    def test_readiness_requires_the_supported_chain_and_pending_stays_deferred(self):
        for target in ['bundle','evidence']:
            for index in range(5):
                bundle=copy.deepcopy(self.data['decision_bundle']);evidence=copy.deepcopy(self.evidence);obj=bundle if target=='bundle'else evidence;obj['cases'][index]['binding_approval_requested']=not V.READY[index]
                with self.subTest(target=target,index=index),self.assertRaisesRegex(ValueError,'binding readiness does not match'):V.validate_binding_readiness(bundle,evidence,self.data['sources'],self.procedural)
        evidence=copy.deepcopy(self.evidence);evidence['prepared_chains'][0]['complete_operative_match_after_whitespace_only']=False
        with self.assertRaisesRegex(ValueError,'operative tokens differ'):V.validate_binding_readiness(self.data['decision_bundle'],evidence,self.data['sources'],self.procedural)

    def test_unresolved_flags_and_false_zero_are_not_applied(self):
        for value in [False,0]:
            data=copy.deepcopy(self.data);pre=data['preparation_preflight'];pre['cases'][2]['record']['exact_action_binding_unresolved']=value;pre['cases'][2]['record_sha256']=digest(pre['cases'][2]['record']);pre['preflight_sha256']=digest({k:v for k,v in pre.items()if k!='preflight_sha256'})
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'preflight subject/scope drift'):V.validate_preflight(pre)

    def test_candidate_mapping_cannot_accept_each_action(self):
        c=V.read(V.P/'generated/shared_action_core.json');m=V.read(V.P/'generated/shared_issue_mapping.json')
        for aid in V.ACTIONS:
            bad=copy.deepcopy(m);row=next(x for x in bad['action_mappings']if x['action_id']==aid);row['eligibility']['decision']='accepted';row['mapping_sha256']=digest({k:v for k,v in row.items()if k!='mapping_sha256'});bad['mapping_sha256']=digest({k:v for k,v in bad.items()if k!='mapping_sha256'})
            with self.subTest(aid=aid),self.assertRaisesRegex(SharedCorpusValidationError,'cannot claim accepted'):validate_shared_issue_mapping(V.ROOT,bad,c)

    def test_both_member_projections_reject_every_stale_core(self):
        c=V.read(V.P/'generated/shared_action_core.json')
        for projection in V.read(V.P/'generated/member_projections.json'):
            for aid in V.ACTIONS:
                bad=copy.deepcopy(projection);next(x for x in bad['actions']if x['action_id']==aid)['action_core_sha256']='0'*64;bad['projection_sha256']=digest({k:v for k,v in bad.items()if k!='projection_sha256'})
                with self.subTest(aid=aid,member=projection['member_id']),self.assertRaisesRegex(SharedCorpusValidationError,'wrong action digest'):validate_member_projection(V.ROOT,bad,c)

if __name__=='__main__':unittest.main()
