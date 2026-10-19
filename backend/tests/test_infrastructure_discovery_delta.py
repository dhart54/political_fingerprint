import copy,unittest
from unittest.mock import patch
import scripts.validate_infrastructure_discovery_delta as delta
from backend.app.semantic_ir.shared_corpus import digest,sealed_digest
from scripts.validate_infrastructure_discovery_delta import CASES,folder,read,validate
class InfrastructureDiscoveryDeltaTests(unittest.TestCase):
    def test_each_complete_increment(self):
        for n in CASES:
            with self.subTest(batch=n):self.assertTrue(validate(n)['generated_replay'])
    def test_prior_hold_cannot_be_closed_by_new_screening(self):
        v=[read(folder(8)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];r=next(r for r in v[2]['candidate_dispositions'] if r['action_id']=='house:119:1:111');r['disposition']='exact_action_ineligible';v[2]['universe_subject_sha256']=digest(dict(subject=v[2]['subject'],cutoff=v[2]['cutoff'],candidate_records=v[2]['candidate_dispositions']));v[2]['proposal_sha256']=sealed_digest(v[2],'proposal_sha256')
        with self.assertRaises(ValueError):validate(8,v,check_files=False)
    def test_incorporated_recommendations_cannot_drop_last_five(self):
        v=[read(folder(8)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];s=next(s for s in v[1]['sources'] if s['source_id']=='doj-oig:23-034-recommendations-infra8');s['text']=s['text'].split('5.')[0];s['governed_bytes_sha256']=sealed_digest(s,'governed_bytes_sha256')
        with self.assertRaises(ValueError):validate(8,v,check_files=False)
    def test_shared_authoring_cannot_name_projected_member(self):
        v=[read(folder(8)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];v[0]['actions'][-1]['meaning']+=' Massie supported this.'
        with self.assertRaisesRegex(ValueError,'member/party contamination'):validate(8,v,check_files=False)
    def test_universe_authority_stays_reserved(self):
        v=[read(folder(8)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];v[2]['publication_authorized']=True;v[2]['proposal_sha256']=sealed_digest(v[2],'proposal_sha256')
        with self.assertRaises(ValueError):validate(8,v,check_files=False)
    def test_authorization_extension_cannot_become_appropriation(self):
        v=[read(folder(10)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];a=next(a for a in v[0]['actions'] if a['action_id']=='house:119:2:304');a['meaning']=a['meaning'].replace('It does not itself make an appropriation.','It appropriates the funds.')
        with self.assertRaisesRegex(ValueError,'authorization/appropriation boundary differs'):validate(10,v,check_files=False)
    def test_consideration_cannot_become_universal_adoption(self):
        v=[read(folder(11)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];a=next(a for a in v[0]['actions'] if a['action_id']=='house:119:2:312');a['meaning']=a['meaning'].replace('permits implementation OR DECLINING implementation','requires implementation everywhere')
        with self.assertRaisesRegex(ValueError,'PURPAconsideration became universal adoption'):validate(11,v,check_files=False)
    def validate_corrected_fixture(self,values):
        original=delta.read;receipt=copy.deepcopy(original(folder(12)/'candidate_correction_receipt.json'))
        for a in values[0]['actions']:
            if a['action_id'] in receipt['corrected_action_sha256']:receipt['corrected_action_sha256'][a['action_id']]=digest(a)
        def reading(path):return receipt if path.name=='candidate_correction_receipt.json' else original(path)
        with patch.object(delta,'read',side_effect=reading):return validate(12,values,check_files=False)
    def test_whale_report_recipient_cannot_return_to_committees(self):
        v=[read(folder(12)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];a=next(a for a in v[0]['actions'] if a['action_id']=='house:119:2:291');a['meaning']=a['meaning'].replace('submit an annual report to Congress','report annually to the named committees')
        with self.assertRaisesRegex(ValueError,'9436recipient/PBR operator correction lost'):self.validate_corrected_fixture(v)
    def test_pbr_expectation_cannot_become_attainment_target(self):
        v=[read(folder(12)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];a=next(a for a in v[0]['actions'] if a['action_id']=='house:119:2:291');a['meaning']=a['meaning'].replace('measures expected to not exceed Potential Biological Removal','plans to attain potential biological removal')
        with self.assertRaisesRegex(ValueError,'9436recipient/PBR operator correction lost'):self.validate_corrected_fixture(v)
    def test_context_witness_cannot_be_swapped_between_choices(self):
        v=[read(folder(12)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];a=next(a for a in v[0]['actions'] if a['action_id']=='house:119:2:294');a['additional_source_ids'][-2]='clerk:119:2:290'
        with self.assertRaises(ValueError):validate(12,v,check_files=False)
    def test_frontier_cannot_relabel_examined_delta_unscreened(self):
        original=delta.read;resume=copy.deepcopy(original(folder(12)/'resume_receipt.json'));resume['next_research_frontier']['scope']='All38deltaidentities remain unscreened.'
        def reading(path):return resume if path==folder(12)/'resume_receipt.json' else original(path)
        with patch.object(delta,'read',side_effect=reading):
            with self.assertRaisesRegex(ValueError,'stale frontier or review-head attribution'):validate(12,check_files=False)
    def test_private_land_work_cannot_lose_owner_consent(self):
        v=[read(folder(14)/f'{k}.json') for k in ['authoring','sources','universe_proposal','membership_review']];a=next(a for a in v[0]['actions'] if a['action_id']=='house:119:1:24');a['meaning']=a['meaning'].replace("with private landowners' consent for the private-land work",'with unconditional private-land access')
        with self.assertRaisesRegex(ValueError,'375consent/continuation/funding boundary differs'):validate(14,v,check_files=False)
    def test_tva_baseline_cannot_drop_power_station_costs(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr144_boundary
        c,u,m=[copy.deepcopy(read(folder(15)/f'{k}.json')) for k in ['sources','universe_proposal','membership_review']];receipt=copy.deepcopy(read(folder(15)/'hr144_baseline_boundary_review.json'));s=next(s for s in c['sources'] if s['source_id']=='govinfo:16usc831h-a-and-reporting-note-2024-infra15');receipt['complete_baseline_subsection']=receipt['complete_baseline_subsection'].replace('cost of power at each power station','corporate administration');s['text']=receipt['complete_baseline_subsection']+'\n\n'+receipt['termination_note'];s['governed_bytes_sha256']=sealed_digest(s,'governed_bytes_sha256')
        with self.assertRaisesRegex(ValueError,'material TVA financial/power-station reporting span lost'):validate_hr144_boundary(c,u,m,receipt)
    def test_tva_exclusion_cannot_return_without_boundary_resolution(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr144_boundary
        c,u,m=[copy.deepcopy(read(folder(15)/f'{k}.json')) for k in ['sources','universe_proposal','membership_review']];receipt=read(folder(15)/'hr144_baseline_boundary_review.json')
        for records in [u['candidate_dispositions'],m['records']]:next(r for r in records if r['action_id']=='house:119:1:14')['disposition']='exact_action_ineligible'
        with self.assertRaisesRegex(ValueError,'TVA operator-reporting boundary must remain pending'):validate_hr144_boundary(c,u,m,receipt)
    def test_doe_sba_permissions_cannot_become_compulsory(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr788_boundaries
        action=copy.deepcopy(next(a for a in read(folder(16)/'authoring.json')['actions'] if a['action_id']=='house:119:1:48'));action['meaning']=action['meaning'].replace('may use reimbursable agreements','must use reimbursable agreements')
        with self.assertRaisesRegex(ValueError,'788duties/permissions/qualification/report clock differ'):validate_hr788_boundaries(action)
    def test_doe_sba_authorization_limit_cannot_become_funding(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr788_boundaries
        action=copy.deepcopy(next(a for a in read(folder(16)/'authoring.json')['actions'] if a['action_id']=='house:119:1:48'));action['meaning']=action['meaning'].replace('Section3 authorizes no additional amounts to be appropriated','Section3 appropriates new program funding')
        with self.assertRaisesRegex(ValueError,'788no-additional-authorization boundary differs'):validate_hr788_boundaries(action)
    def test_mail_reporting_cannot_lose_serious_injury_accommodation(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr758_boundaries
        action=copy.deepcopy(next(a for a in read(folder(17)/'authoring.json')['actions'] if a['action_id']=='house:119:1:55'));action['meaning']=action['meaning'].replace('must provide alternative-deadline procedures','may decline any alternative deadline')
        with self.assertRaisesRegex(ValueError,'758report trigger/injury accommodation differs'):validate_hr758_boundaries(action)
    def test_mail_internal_database_cannot_become_public_identifying_data(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr758_boundaries
        action=copy.deepcopy(next(a for a in read(folder(17)/'authoring.json')['actions'] if a['action_id']=='house:119:1:55'));action['meaning']=action['meaning'].replace('does not personally identify any employee, contractor or other individual','identifies individual employees and contractors')
        with self.assertRaisesRegex(ValueError,'758internal/public privacy or discretionary penalty boundary differs'):validate_hr758_boundaries(action)
    def test_border_team_permission_cannot_become_creation_mandate(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr993_boundaries
        action=copy.deepcopy(next(a for a in read(folder(18)/'authoring.json')['actions'] if a['action_id']=='house:119:1:65'));action['meaning']=action['meaning'].replace('does not require creation of a team','requires creation of a team')
        with self.assertRaisesRegex(ValueError,'993team permission/conditional duty/technology example scope differs'):validate_hr993_boundaries(action)
    def test_border_technology_review_cannot_drop_negative_consequences(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr993_boundaries
        action=copy.deepcopy(next(a for a in read(folder(18)/'authoring.json')['actions'] if a['action_id']=='house:119:1:65'));action['meaning']=action['meaning'].replace('including NEGATIVE consequences','limited to successful outcomes')
        with self.assertRaisesRegex(ValueError,'993negative consequences/privacy/report clocks differ'):validate_hr993_boundaries(action)
    def test_cost_share_report_cannot_lose_public_quarterly_requirement(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr359_boundaries
        action=copy.deepcopy(next(a for a in read(folder(20)/'authoring.json')['actions'] if a['action_id']=='house:119:1:72'));baseline=next(s for s in read(folder(20)/'sources.json')['sources'] if s['source_id']=='govinfo:42usc16352-2024-infra20');action['meaning']=action['meaning'].replace('MAKE IT PUBLICLY AVAILABLE','send it privately to one committee')
        with self.assertRaisesRegex(ValueError,'359public/quarterly/deadline/recipient boundary differs'):validate_hr359_boundaries(action,baseline)
    def test_cost_share_baseline_cannot_make_temporary_exemption_permanent(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr359_boundaries
        action=next(a for a in read(folder(20)/'authoring.json')['actions'] if a['action_id']=='house:119:1:72');baseline=copy.deepcopy(next(s for s in read(folder(20)/'sources.json')['sources'] if s['source_id']=='govinfo:42usc16352-2024-infra20'));baseline['text']=baseline['text'].replace('2-year period beginning on August 9, 2022','permanent period');baseline['governed_bytes_sha256']=sealed_digest(baseline,'governed_bytes_sha256')
        with self.assertRaisesRegex(ValueError,'359material baseline defaults/exclusions/dated exemption lost'):validate_hr359_boundaries(action,baseline)
    def test_quad_negotiations_cannot_guarantee_international_group(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr1263_boundaries
        action=copy.deepcopy(next(a for a in read(folder(24)/'authoring.json')['actions'] if a['action_id']=='house:119:1:132'));action['meaning']=action['meaning'].replace('ONLY IF the governments enter that written agreement','even without an agreement')
        with self.assertRaisesRegex(ValueError,'1263negotiation/conditional group/financing/ethics boundary differs'):validate_hr1263_boundaries(action)
    def test_quad_not_voting_cannot_become_opposition(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr1263_nondirectional
        readable=copy.deepcopy(read(folder(24)/'generated/readable_candidates.json'));member=next(m for m in readable['members'] if m['member_id']=='M001184');member['findings'].append(dict(action_ids=['house:119:1:132'],compact='Massie opposed the Quad bill'))
        with self.assertRaisesRegex(ValueError,'1263Not Voting became directional finding'):validate_hr1263_nondirectional(readable)
    def test_allocation_deletion_cannot_become_overall_account_cut(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr4016_amend114_boundaries
        action=copy.deepcopy(next(a for a in read(folder(36)/'authoring.json')['actions'] if a['action_id']=='house:119:1:207'));target=next(s for s in read(folder(36)/'sources.json')['sources'] if s['source_id']=='govinfo:hr4016rh-section8067-complete171');action['meaning']=action['meaning'].replace('does not establish a $500 million reduction in the overall account totals','cuts $500 million from the overall account totals');action['compact_description']=action['compact_description'].replace('does not establish a cut to overall account totals','cuts overall account totals')
        with self.assertRaisesRegex(ValueError,'8067allocation directive became overall-account cut'):validate_hr4016_amend114_boundaries(action,target)
    def test_allocation_deletion_cannot_drop_respective_agreement_conditions(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr4016_amend114_boundaries
        action=copy.deepcopy(next(a for a in read(folder(36)/'authoring.json')['actions'] if a['action_id']=='house:119:1:207'));target=next(s for s in read(folder(36)/'sources.json')['sources'] if s['source_id']=='govinfo:hr4016rh-section8067-complete171');action['meaning']=action['meaning'].replace("their respective U.S.-Israeli co-production agreements and each nation's laws, regulations and procedures",'no conditions')
        with self.assertRaisesRegex(ValueError,'8067respective agreement/law conditions lost'):validate_hr4016_amend114_boundaries(action,target)
    def test_atvm_administration_does_not_become_loan_principal(self):
        from scripts.validate_infrastructure_discovery_delta import validate_atvm_administration_boundaries
        action=copy.deepcopy(next(a for a in read(folder(38)/'authoring.json')['actions'] if a['action_id']=='house:119:1:230'));target=next(s for s in read(folder(38)/'sources.json')['sources'] if s['source_id']=='govinfo:hr4553-rh-amend26-account-SRA146');action['meaning']=action['meaning'].replace('$13 million is administrative funding, not loan principal or credit subsidy','$13 million is loan principal')
        with self.assertRaisesRegex(ValueError,'ATVM administrative reduction became loan-principal cut'):validate_atvm_administration_boundaries(action,target)
    def test_atvm_administration_does_not_repeal_program(self):
        from scripts.validate_infrastructure_discovery_delta import validate_atvm_administration_boundaries
        action=copy.deepcopy(next(a for a in read(folder(38)/'authoring.json')['actions'] if a['action_id']=='house:119:1:230'));target=next(s for s in read(folder(38)/'sources.json')['sources'] if s['source_id']=='govinfo:hr4553-rh-amend26-account-SRA146');action['compact_description']=action['compact_description'].replace('would not repeal the loan program or cancel existing loans','would repeal the loan program and cancel existing loans')
        with self.assertRaisesRegex(ValueError,'ATVM administrative reduction became program repeal'):validate_atvm_administration_boundaries(action,target)
    def test_northern_border_administrative_override_is_retained(self):
        from scripts.validate_infrastructure_discovery_delta import validate_northern_border_appropriation_boundaries
        action=copy.deepcopy(next(a for a in read(folder(39)/'authoring.json')['actions'] if a['action_id']=='house:119:1:232'));target=next(s for s in read(folder(39)/'sources.json')['sources'] if s['source_id']=='govinfo:hr4553-rh-amend28-account-SRA148');action['meaning']=action['meaning'].replace('administrative expenses notwithstanding section 15751(b) remains unchanged','administrative expenses only within the ordinary cap')
        with self.assertRaisesRegex(ValueError,'Northern Border administrative exception lost'):validate_northern_border_appropriation_boundaries(action,target)
    def test_northern_border_grant_share_is_not_whole_account_share(self):
        from scripts.validate_infrastructure_discovery_delta import validate_northern_border_appropriation_boundaries
        action=copy.deepcopy(next(a for a in read(folder(39)/'authoring.json')['actions'] if a['action_id']=='house:119:1:232'));target=next(s for s in read(folder(39)/'sources.json')['sources'] if s['source_id']=='govinfo:hr4553-rh-amend28-account-SRA148');action['meaning']=action['meaning'].replace('not 40 percent of this entire appropriation','40 percent of this entire appropriation')
        with self.assertRaisesRegex(ValueError,'Northern Border grant share became account/project allocation'):validate_northern_border_appropriation_boundaries(action,target)
    def test_retained_numeric_conflict_cannot_be_cleared(self):
        from scripts.validate_infrastructure_discovery_delta import validate_retained_numeric_conflict
        record=copy.deepcopy(next(r for r in read(folder(40)/'membership_review.json')['records'] if r['action_id']=='house:119:1:237'));sources={s['source_id']:s for s in read(folder(40)/'sources.json')['sources']};receipt=read(folder(40)/'retained_numeric_conflict_receipt.json');record['authoritative_source_conflict']=False
        with self.assertRaisesRegex(ValueError,'retained237numeric conflict cleared or recast'):validate_retained_numeric_conflict(record,sources,receipt)
    def test_vehicle_repeal_keeps_2035_multitechnology_scope(self):
        from scripts.validate_infrastructure_discovery_delta import validate_vehicle_repeal_boundaries
        action=copy.deepcopy(next(a for a in read(folder(42)/'authoring.json')['actions'] if a['action_id']=='house:119:1:251'));target=next(s for s in read(folder(42)/'sources.json')['sources'] if s['source_id']=='govinfo:10usc2922g-2024-operative');action['meaning']=action['meaning'].replace('not an immediate electric-only requirement for all military vehicles','an immediate electric-only requirement for all military vehicles')
        with self.assertRaisesRegex(ValueError,'vehicle repeal lost time/technology/waiver qualifications'):validate_vehicle_repeal_boundaries(action,target)
    def test_vehicle_preference_repeal_does_not_become_ev_ban(self):
        from scripts.validate_infrastructure_discovery_delta import validate_vehicle_repeal_boundaries
        action=copy.deepcopy(next(a for a in read(folder(42)/'authoring.json')['actions'] if a['action_id']=='house:119:1:251'));target=next(s for s in read(folder(42)/'sources.json')['sources'] if s['source_id']=='govinfo:10usc2922g-2024-operative');action['meaning']=action['meaning'].replace('does not create a new ban on electric or hybrid procurement','creates a new ban on electric or hybrid procurement')
        with self.assertRaisesRegex(ValueError,'vehicle preference repeal became EV procurement ban'):validate_vehicle_repeal_boundaries(action,target)
    def test_current_mechanism_summary_includes_authored_amendments(self):
        from scripts.validate_infrastructure_discovery_delta import validate_mechanism_summary
        accounting=copy.deepcopy(read(folder(42)/'universe_proposal.json')['accounting']);core=read(folder(42)/'generated/shared_action_core.json');accounting['mechanism_types']=['final_passage','suspension_and_passage']
        with self.assertRaisesRegex(ValueError,'accounting mechanism summary omits or invents'):validate_mechanism_summary(accounting,core)
    def test_cell_cultured_authorized_funding_is_not_only_appropriations(self):
        from scripts.validate_infrastructure_discovery_delta import validate_cell_cultured_funding_boundaries
        action=copy.deepcopy(next(a for a in read(folder(43)/'authoring.json')['actions'] if a['action_id']=='house:119:1:254'));report=next(s for s in read(folder(43)/'sources.json')['sources'] if s['source_id']=='house-rules:119255-partA-amend20-operative157');action['meaning']=action['meaning'].replace('The first funding description is Act-authorized funds, not merely funds appropriated by this Act','The first funding description covers only actual appropriations made by this Act')
        with self.assertRaisesRegex(ValueError,'cell-cultured authorization funding collapsed'):validate_cell_cultured_funding_boundaries(action,report)
    def test_cell_cultured_choice_keeps_procurement_and_promotion(self):
        from scripts.validate_infrastructure_discovery_delta import validate_cell_cultured_funding_boundaries
        action=copy.deepcopy(next(a for a in read(folder(43)/'authoring.json')['actions'] if a['action_id']=='house:119:1:254'));report=next(s for s in read(folder(43)/'sources.json')['sources'] if s['source_id']=='house-rules:119255-partA-amend20-operative157');action['meaning']=action['meaning'].replace('research, development, procurement and promotion','research only')
        with self.assertRaisesRegex(ValueError,'cell-cultured whole activity scope reduced'):validate_cell_cultured_funding_boundaries(action,report)
    def test_north_dakota_exceptions_cannot_expand_to_drinking_water(self):
        from scripts.validate_infrastructure_discovery_delta import validate_north_dakota_exception_scope
        record=copy.deepcopy(next(r for r in read(folder(43)/'membership_review.json')['records'] if r['action_id']=='house:119:1:226'));source=next(s for s in read(folder(43)/'sources.json')['sources'] if s['source_id']=='blm:north-dakota-2025-reviewed-decision')
        validate_north_dakota_exception_scope(record,source)
        record['rationale']=record['rationale'].replace('The stated drainage/new-data exceptions apply only to low-development-potential leasing; they are not stated exceptions to the drinking-water source-protection closure','low-potential/drinking-water leasing restrictions have stated drainage/new-data exceptions')
        with self.assertRaisesRegex(ValueError,'North Dakota exceptions improperly cover drinking-water closure'):validate_north_dakota_exception_scope(record,source)
    def test_refinery_directive_deadline_is_not_completion_deadline(self):
        from scripts.validate_infrastructure_discovery_delta import validate_refinery_report_boundaries
        action=copy.deepcopy(next(a for a in read(folder(52)/'authoring.json')['actions'] if a['action_id']=='house:119:1:303'));sources={s['source_id']:s for s in read(folder(52)/'sources.json')['sources']};action['meaning']=action['meaning'].replace('The 90-day deadline is for the Secretary to direct the Council, not an express 90-day deadline for completing the report','The report must be completed within 90 days')
        with self.assertRaisesRegex(ValueError,'refinery direction deadline became report completion deadline'):validate_refinery_report_boundaries(action,sources['govinfo:hr3109eh'],sources['clerk:119:1:303'],read(folder(52)/'generated/compiled_ir.json'),read(folder(52)/'generated/readable_candidates.json'))
    def test_refinery_not_voting_cannot_become_directional_finding(self):
        from scripts.validate_infrastructure_discovery_delta import validate_refinery_report_boundaries
        action=next(a for a in read(folder(52)/'authoring.json')['actions'] if a['action_id']=='house:119:1:303');sources={s['source_id']:s for s in read(folder(52)/'sources.json')['sources']};readable=copy.deepcopy(read(folder(52)/'generated/readable_candidates.json'));member=next(m for m in readable['members'] if m['member_id']=='M001184');member['findings'][0]['action_ids'].append('house:119:1:303')
        with self.assertRaisesRegex(ValueError,'refinery Not Voting became directional finding'):validate_refinery_report_boundaries(action,sources['govinfo:hr3109eh'],sources['clerk:119:1:303'],read(folder(52)/'generated/compiled_ir.json'),readable)
    def test_state_generation_consideration_is_not_compulsory_implementation(self):
        from scripts.validate_infrastructure_discovery_delta import validate_state_generation_boundaries
        action=copy.deepcopy(next(a for a in read(folder(56)/'authoring.json')['actions'] if a['action_id']=='house:119:1:323'));sources={s['source_id']:s for s in read(folder(56)/'sources.json')['sources']};action['meaning']=action['meaning'].replace('it requires consideration and a determination, not automatic adoption or implementation of the standard','it requires every utility to implement the standard automatically')
        with self.assertRaisesRegex(ValueError,'State consideration became compulsory implementation'):validate_state_generation_boundaries(action,sources['govinfo:hr3628eh'],sources['govinfo:16usc-2621abc-2024-195'])
    def test_state_generation_fuel_supply_keeps_contractual_alternative(self):
        from scripts.validate_infrastructure_discovery_delta import validate_state_generation_boundaries
        action=copy.deepcopy(next(a for a in read(folder(56)/'authoring.json')['actions'] if a['action_id']=='house:119:1:323'));sources={s['source_id']:s for s in read(folder(56)/'sources.json')['sources']};action['meaning']=action['meaning'].replace('on-site fuel or an on-site continuously available energy source, or contractual fuel-supply obligations','only fuel stored on site')
        with self.assertRaisesRegex(ValueError,'State generation contractual alternative or on-site scope lost'):validate_state_generation_boundaries(action,sources['govinfo:hr3628eh'],sources['govinfo:16usc-2621abc-2024-195'])
    def test_pipeline_deadline_does_not_grant_automatic_approval(self):
        from scripts.validate_infrastructure_discovery_delta import validate_pipeline_review_boundaries
        action=copy.deepcopy(next(a for a in read(folder(58)/'authoring.json')['actions'] if a['action_id']=='house:119:1:334'));sources={s['source_id']:s for s in read(folder(58)/'sources.json')['sources']}
        action['meaning']=action['meaning'].replace('This is not automatic approval or a 90-day clock from application','Applications receive automatic approval 90 days after application')
        with self.assertRaisesRegex(ValueError,'pipeline deadline became automatic approval'):validate_pipeline_review_boundaries(action,sources['govinfo:hr3668eh'],sources['govinfo:33usc1341-2024-water-boundary'])
    def test_pipeline_proposed_state_conditions_are_not_binding(self):
        from scripts.validate_infrastructure_discovery_delta import validate_pipeline_review_boundaries
        action=copy.deepcopy(next(a for a in read(folder(58)/'authoring.json')['actions'] if a['action_id']=='house:119:1:334'));sources={s['source_id']:s for s in read(folder(58)/'sources.json')['sources']}
        action['meaning']=action['meaning'].replace('FERC may include a proposed condition only if it finds the condition necessary for that compliance; proposed conditions are not automatically binding','All proposed State conditions are automatically binding and State certification remains mandatory')
        with self.assertRaisesRegex(ValueError,'pipeline certification displacement or FERC discretion lost'):validate_pipeline_review_boundaries(action,sources['govinfo:hr3668eh'],sources['govinfo:33usc1341-2024-water-boundary'])
    def test_power_retirement_environmental_shield_is_compliance_linked(self):
        from scripts.validate_infrastructure_discovery_delta import validate_power_retirement_boundaries
        action=copy.deepcopy(next(a for a in read(folder(60)/'authoring.json')['actions'] if a['action_id']=='house:119:1:342'));sources={s['source_id']:s for s in read(folder(60)/'sources.json')['sources']}
        action['meaning']=action['meaning'].replace('only acts or omissions necessary to comply with an order issued or extended under this subsection, including acts or omissions taken to voluntarily comply','every voluntary plant operation regardless of any compliance link')
        with self.assertRaisesRegex(ValueError,'power environmental shield became unconditional immunity'):validate_power_retirement_boundaries(action,sources['govinfo:hr3632eh'],sources['govinfo:16usc824f-2024-operative'],sources['govinfo:16usc824o-2024-definitions'])
    def test_power_retirement_notice_is_not_a_universal_ban(self):
        from scripts.validate_infrastructure_discovery_delta import validate_power_retirement_boundaries
        action=copy.deepcopy(next(a for a in read(folder(60)/'authoring.json')['actions'] if a['action_id']=='house:119:1:342'));sources={s['source_id']:s for s in read(folder(60)/'sources.json')['sources']}
        action['meaning']=action['meaning'].replace('notice duty is not an automatic five-year retirement ban or a requirement to obtain a retirement permit','bill automatically bans every plant retirement for five years')
        with self.assertRaisesRegex(ValueError,'power retirement notice became universal ban or lost unit/exception scope'):validate_power_retirement_boundaries(action,sources['govinfo:hr3632eh'],sources['govinfo:16usc824f-2024-operative'],sources['govinfo:16usc824o-2024-definitions'])
    def test_reliability_gate_requires_finding_beyond_agency_response(self):
        from scripts.validate_infrastructure_discovery_delta import validate_reliability_gate_boundaries
        action=copy.deepcopy(next(a for a in read(folder(61)/'authoring.json')['actions'] if a['action_id']=='house:119:1:347'));sources={s['source_id']:s for s in read(folder(61)/'sources.json')['sources']}
        action['meaning']=action['meaning'].replace('AND FERC finds the action will not likely have a significant negative impact','with no separate FERC finding required')
        with self.assertRaisesRegex(ValueError,'reliability finalization lost independent FERC gate'):validate_reliability_gate_boundaries(action,sources['govinfo:hr3616eh'],sources['govinfo:16usc824o-2024-operative'],sources['govinfo:16usc824o-2024-definitions'])
    def test_reliability_advance_submission_is_not_automatic_clearance(self):
        from scripts.validate_infrastructure_discovery_delta import validate_reliability_gate_boundaries
        action=copy.deepcopy(next(a for a in read(folder(61)/'authoring.json')['actions'] if a['action_id']=='house:119:1:347'));sources={s['source_id']:s for s in read(folder(61)/'sources.json')['sources']}
        action['meaning']=action['meaning'].replace('The90dayfallback governs advance agency submission, not a deadline for FERC to decide or automatic clearance after90days','FERC must decide within90days or the action is automatically cleared')
        with self.assertRaisesRegex(ValueError,'reliability advance submission became automatic clearance'):validate_reliability_gate_boundaries(action,sources['govinfo:hr3616eh'],sources['govinfo:16usc824o-2024-operative'],sources['govinfo:16usc824o-2024-definitions'])
    def test_active_failed_adoption_and_ssa_provenance_disclosures_fail_closed(self):
        from scripts.validate_infrastructure_discovery_delta import validate_active_disclosure_corrections
        m=read(folder(62)/'membership_review.json');u=read(folder(62)/'universe_proposal.json');s=read(folder(62)/'sources.json');receipt=read(folder(62)/'active_disclosure_corrections_20261019.json')
        validate_active_disclosure_corrections(m,u,s,receipt)
        bad=copy.deepcopy(m);next(r for r in bad['records'] if r['action_id']=='house:119:1:293')['rationale']=next(r for r in bad['records'] if r['action_id']=='house:119:1:293')['rationale'].replace('roll 297, which failed','roll 297, which passed')
        with self.assertRaisesRegex(ValueError,'roll293 later adoption disclosure omits failed result'):validate_active_disclosure_corrections(bad,u,s,receipt)
        bad=copy.deepcopy(m);next(c for c in next(r for r in bad['records'] if r['action_id']=='house:119:1:306')['claim_source_map'] if c['source_id']=='govinfo:42usc405c2Bi-2024-ssn-issuance')['locator']='Captured I/III commentary applies to this bill'
        with self.assertRaisesRegex(ValueError,'SSA captured I/III commentary lacks active IV/V qualification'):validate_active_disclosure_corrections(bad,u,s,receipt)
if __name__=='__main__':unittest.main()
