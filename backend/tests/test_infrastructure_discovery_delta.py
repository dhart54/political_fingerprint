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
    def test_conduit_cost_hardship_and_construction_entity_qualifications(self):
        from scripts.validate_infrastructure_discovery_delta import validate_conduit_repayment_boundaries
        action=next(a for a in read(folder(65)/'authoring.json')['actions'] if a['action_id']=='house:119:2:9');s={s['source_id']:s for s in read(folder(65)/'sources.json')['sources']}
        for old,new,error in [('35 percent of the full conduit cost, not a new 35 percent charge on the remaining balance','35 percent of remaining debt only','conduit total-cost obligation became balance charge or forgiveness'),('favorable balance-repayment terms require a demonstration of financial hardship determined by the Secretary','favorable terms are automatic for every contract','conduit hardship/maximum/simple-interest qualifications lost'),('Any entity other than the Secretary is not narrowed here to State/local or non-Federal entities','Only State/local or non-Federal construction money qualifies','conduit construction funding narrowed to non-Federal entities')]:
            with self.subTest(boundary=error):
                bad=copy.deepcopy(action);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,error):validate_conduit_repayment_boundaries(bad,s['govinfo:hr131enr'],s['govinfo:pl111-11-arkansas9115'],s['clerk:119:2:9'])
    def test_conduit_failed_override_does_not_enact_enrolled_bill(self):
        from scripts.validate_infrastructure_discovery_delta import validate_conduit_repayment_boundaries
        action=copy.deepcopy(next(a for a in read(folder(65)/'authoring.json')['actions'] if a['action_id']=='house:119:2:9'));s={s['source_id']:s for s in read(folder(65)/'sources.json')['sources']};action['meaning']=action['meaning'].replace('House veto-override attempt failed and did not itself enact the bill','House veto-override attempt passed and enacted the bill')
        with self.assertRaisesRegex(ValueError,'conduit failed override became ordinary passage or enactment'):validate_conduit_repayment_boundaries(action,s['govinfo:hr131enr'],s['govinfo:pl111-11-arkansas9115'],s['clerk:119:2:9'])
    def test_housing_energy_advice_does_not_force_hud_or_remove_its_standards(self):
        from scripts.validate_infrastructure_discovery_delta import validate_housing_energy_role_boundaries
        action=next(a for a in read(folder(66)/'authoring.json')['actions'] if a['action_id']=='house:119:2:12');s={s['source_id']:s for s in read(folder(66)/'sources.json')['sources']}
        for old,new in [('does not require HUD to adopt every DOE recommendation','requires HUD to adopt every DOE recommendation automatically'),('does not repeal HUD’s separate section 5403(g) energy-standard duty','repeals every HUD energy and safety standard')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'housing advice became compulsory HUD adoption or abolished independent standards'):validate_housing_energy_role_boundaries(bad,s['govinfo:hr5184eh'],s['olrc:42usc17071-2024-operative'],s['govinfo:42usc5403g-2024-operative'],s['doe:manufactured-housing2022-operative'],s['doe:manufactured-housing2025-compliance'])
    def test_housing_contingent_dates_and_single_multi_section_tiers_remain(self):
        from scripts.validate_infrastructure_discovery_delta import validate_housing_energy_role_boundaries
        action=next(a for a in read(folder(66)/'authoring.json')['actions'] if a['action_id']=='house:119:2:12');s={s['source_id']:s for s in read(folder(66)/'sources.json')['sources']}
        for old,new,error in [('60-day and 180-day clocks after publication of final enforcement procedures','a fixed current May 31, 2023 deadline','housing original deadline replaced later contingent compliance clocks'),('Tier 1 single-section homes and Tier 2 multi-section homes','Tier 1 homes below a retail-price cutoff and Tier 2 higher-priced homes','housing rule tiers became an invented price cutoff'),('relative to the standard as proposed to be revised','relative to every existing standard before revision','housing performance comparator changed from proposed revision to existing standard')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,error):validate_housing_energy_role_boundaries(bad,s['govinfo:hr5184eh'],s['olrc:42usc17071-2024-operative'],s['govinfo:42usc5403g-2024-operative'],s['doe:manufactured-housing2022-operative'],s['doe:manufactured-housing2025-compliance'])
    def test_small_business_ai_assistance_is_not_compelled_adoption_or_optional_list(self):
        from scripts.validate_infrastructure_discovery_delta import validate_small_business_ai_boundaries
        action=next(a for a in read(folder(70)/'authoring.json')['actions'] if a['action_id']=='house:119:2:33');s={s['source_id']:s for s in read(folder(70)/'sources.json')['sources']}
        for old,new in [('Outreach is required only to the extent practical','Outreach is unconditionally required'),('mandatory assistance subjects and qualified outreach','optional assistance and mandatory outreach'),('not a vote requiring small businesses to buy or use an AI product','requires every business to buy an AI product')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'small-business AI assistance became optional or compelled adoption'):validate_small_business_ai_boundaries(bad,s['govinfo:hr5764eh'],s['govinfo:15usc648-2024-sbdc-services'],s['govinfo:15usc9401-2024-ai-definition'],s['clerk:119:2:33'])
    def test_small_business_ai_preserves_existing_funding_services_and_definition(self):
        from scripts.validate_infrastructure_discovery_delta import validate_small_business_ai_boundaries
        action=next(a for a in read(folder(70)/'authoring.json')['actions'] if a['action_id']=='house:119:2:33');s={s['source_id']:s for s in read(folder(70)/'sources.json')['sources']}
        for old,new in [('neither creates a new appropriation nor cancels all existing SBDC funding','cancels all existing SBDC funding'),('not the first authorization for every technology or cybersecurity service','creates the first technology service authority'),('not confined here to generative chatbots','confined to generative chatbots')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'small-business AI lost existing services funding or broad definition'):validate_small_business_ai_boundaries(bad,s['govinfo:hr5764eh'],s['govinfo:15usc648-2024-sbdc-services'],s['govinfo:15usc9401-2024-ai-definition'],s['clerk:119:2:33'])
    def test_vehicle_standard_funding_is_not_repeal_or_all_government(self):
        from scripts.validate_infrastructure_discovery_delta import validate_vehicle_standard_funding_boundaries
        action=next(a for a in read(folder(72)/'authoring.json')['actions'] if a['action_id']=='house:119:2:43');s={s['source_id']:s for s in read(folder(72)/'sources.json')['sources']}
        bad=copy.deepcopy(action);bad['meaning']=bad['meaning'].replace('restriction on the funds made available by DivisionD, not a permanent repeal of section24220 or a restriction on every federal account','permanent repeal of section24220 and a restriction on every federal account')
        with self.assertRaisesRegex(ValueError,'vehicle funding rider became permanent repeal or all-government restriction'):validate_vehicle_standard_funding_boundaries(bad,s['immigration:session2-roll43-initial174'],s['govinfo:49usc30111-24220-complete174'],s['govinfo:hr7148ih-reference-scope'],s['clerk:119:2:43'])
    def test_vehicle_standard_alternatives_compliance_and_failed_outcome(self):
        from scripts.validate_infrastructure_discovery_delta import validate_vehicle_standard_funding_boundaries
        action=next(a for a in read(folder(72)/'authoring.json')['actions'] if a['action_id']=='house:119:2:43');s={s['source_id']:s for s in read(folder(72)/'sources.json')['sources']}
        for old,new,error in [('does not require both detection paths in every system','requires both detection paths in every system','vehicle technology alternatives became mandatory combined design'),('Manufacturer compliance is two to three years after rule issuance','Manufacturer compliance is immediate for every existing vehicle','vehicle funding candidate lost conditional compliance or current-rule limits'),('recorded amendment was rejected164–268with4NotVoting','recorded amendment passed and was adopted','vehicle funding failed amendment became adopted or accepted')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,error):validate_vehicle_standard_funding_boundaries(bad,s['immigration:session2-roll43-initial174'],s['govinfo:49usc30111-24220-complete174'],s['govinfo:hr7148ih-reference-scope'],s['clerk:119:2:43'])
    def test_critical_energy_resource_definition_and_existing_office_scope(self):
        from scripts.validate_infrastructure_discovery_delta import validate_critical_energy_resource_boundaries
        action=next(a for a in read(folder(75)/'authoring.json')['actions'] if a['action_id']=='house:119:2:64');s={s['source_id']:s for s in read(folder(75)/'sources.json')['sources']}
        for old,new in [('requires BOTH essentiality to the US energy sector/energy systems AND a supply chain vulnerable to disruption','requires either energy essentiality OR a vulnerable supply chain'),('adds functions to existing Assistant Secretaries, not a new office','creates a new critical-minerals office')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'critical-energy-resource definition became fixed list or new office'):validate_critical_energy_resource_boundaries(bad,s['govinfo:hr3617eh'],s['govinfo:42usc7112-operative149'],s['govinfo:42usc7133-operative149'])
    def test_critical_energy_resource_duties_and_report_are_distinct(self):
        from scripts.validate_infrastructure_discovery_delta import validate_critical_energy_resource_boundaries
        action=next(a for a in read(folder(75)/'authoring.json')['actions'] if a['action_id']=='house:119:2:64');s={s['source_id']:s for s in read(folder(75)/'sources.json')['sources']}
        for old,new in [('operative duties, not only an optional study','only an optional study'),('not an annual reporting requirement or a universal two-year completion deadline','an annual report and universal two-year completion deadline'),('subjects for assessment, not findings by this candidate','proved findings of foreign misconduct')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'critical-energy-resource duties/report/assessment or candidate limits lost'):validate_critical_energy_resource_boundaries(bad,s['govinfo:hr3617eh'],s['govinfo:42usc7112-operative149'],s['govinfo:42usc7133-operative149'])
    def test_cable_sanctuary_exemption_requires_effective_authorization(self):
        from scripts.validate_infrastructure_discovery_delta import validate_cable_sanctuary_boundaries
        action=next(a for a in read(folder(83)/'authoring.json')['actions'] if a['action_id']=='house:119:2:67');s={s['source_id']:s for s in read(folder(83)/'sources.json')['sources']};bad=copy.deepcopy(action);bad['meaning']=bad['meaning'].replace('IF a Federal OR State agency has issued a license, lease or permit that is in effect authorizing those activities','whether or not another agency has authorized the activities')
        with self.assertRaisesRegex(ValueError,'cable sanctuary exemption lost effective matching authorization'):validate_cable_sanctuary_boundaries(bad,s['govinfo:hr261eh'],s['govinfo:16usc1441-permit-terms'],s['govinfo:16usc1434-cooperation'])
    def test_cable_general_permit_scope_and_surviving_cooperation(self):
        from scripts.validate_infrastructure_discovery_delta import validate_cable_sanctuary_boundaries
        action=next(a for a in read(folder(83)/'authoring.json')['actions'] if a['action_id']=='house:119:2:67');s={s['source_id']:s for s in read(folder(83)/'sources.json')['sources']}
        for old,new,error in [('deletions apply to special-use permits generally, not only cable permits','deletions apply only to cable permits','cable sanctuary general term deletion or surviving protections lost'),('insurance/equivalent-bond and hold-harmless term is redesignated, not deleted','insurance and hold-harmless protections are deleted','cable sanctuary general term deletion or surviving protections lost'),('expressly preserves interagency cooperation under304(d)','abolishes all interagency cooperation','cable sanctuary cooperation became abolished or automatic approval')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,error):validate_cable_sanctuary_boundaries(bad,s['govinfo:hr261eh'],s['govinfo:16usc1441-permit-terms'],s['govinfo:16usc1434-cooperation'])
    def test_roll43_part_a_binding_is_required_without_semantic_change(self):
        from scripts.validate_infrastructure_discovery_delta import validate_roll43_part_a_binding
        p=folder(77);action=next(a for a in read(p/'authoring.json')['actions'] if a['action_id']=='house:119:2:43');record=next(r for r in read(p/'membership_review.json')['records'] if r['action_id']=='house:119:2:43');row=next(r for r in read(p/'universe_proposal.json')['candidate_dispositions'] if r['action_id']=='house:119:2:43');s={x['source_id']:x for x in read(p/'sources.json')['sources']};receipt=read(p/'roll43_partA_version_binding_receipt.json');recommendation=read(p/'vehicle_standard_funding_taxonomy_recommendation.json')
        bad=copy.deepcopy(action);bad['claim_source_map']=[x for x in bad['claim_source_map'] if x['source_id']!='govinfo:hrpt119-462-operative-amendments']
        with self.assertRaisesRegex(ValueError,'roll43 PartA claim binding missing'):validate_roll43_part_a_binding(bad,record,row,s,receipt,recommendation)
        bad=copy.deepcopy(action);bad['meaning']+=' This restricts every federal account.'
        with self.assertRaisesRegex(ValueError,'roll43 provenance repair changed meaning or other action fields'):validate_roll43_part_a_binding(bad,record,row,s,receipt,recommendation)
    def test_roll29_three_conditions_are_not_three_arrangements(self):
        from scripts.validate_infrastructure_discovery_delta import validate_roll29_conditions_wording
        p=folder(80);record=copy.deepcopy(next(r for r in read(p/'membership_review.json')['records'] if r['action_id']=='house:119:2:29'));row=next(r for r in read(p/'universe_proposal.json')['candidate_dispositions'] if r['action_id']=='house:119:2:29');receipt=read(p/'roll29_conditions_wording_correction_receipt.json');source=next(s for s in read(p/'sources.json')['sources'] if s['source_id']==receipt['source_id']);record['rationale']=record['rationale'].replace('investment arrangements satisfying all three specified conditions','exactly three investment arrangements')
        with self.assertRaisesRegex(ValueError,'roll29 conjunctive conditions became exactly three arrangements'):validate_roll29_conditions_wording(record,row,source,receipt)
    def test_blue_catfish_purchase_roles_and_transport_cap_remain(self):
        from scripts.validate_infrastructure_discovery_delta import validate_blue_catfish_program_boundaries
        p=folder(83);action=next(a for a in read(p/'authoring.json')['actions'] if a['action_id']=='house:119:2:88');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('pet-food, animal-feed or aquaculture-feed manufacturers/processors, not human-food recipients or every research partner','human-food recipients and all research partners'),('may use no more than15percent for transport','may use unlimited funds for transport')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'blue-catfish purchasing roles price or transport limits lost'):validate_blue_catfish_program_boundaries(bad,s['govinfo:hr4294eh'],s['govinfo:15usc1511d-2024-marine'])
    def test_blue_catfish_later_fiscal_year_start_and_uncertainty_remain(self):
        from scripts.validate_infrastructure_discovery_delta import validate_blue_catfish_program_boundaries
        p=folder(83);action=next(a for a in read(p/'authoring.json')['actions'] if a['action_id']=='house:119:2:88');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new,error in [('fiscal year AFTER the LATER fiscal year of the first public abundance estimate and the required guidance','date of enactment alone','blue-catfish conditional timing or seek-MOU became automatic'),('Seeking the memorandum is not a guarantee of agreement','The memorandum is automatically guaranteed','blue-catfish conditional timing or seek-MOU became automatic'),('requested assessments are not proved causal effects','requested assessments are proved causal benefits','blue-catfish report scientific uncertainty or candidate scope lost')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,error):validate_blue_catfish_program_boundaries(bad,s['govinfo:hr4294eh'],s['govinfo:15usc1511d-2024-marine'])
    def test_cable_agency_scope_has_no_other_agency_identity_condition(self):
        from scripts.validate_infrastructure_discovery_delta import validate_source_literal_scope_corrections
        p=folder(83);a={x['action_id']:x for x in read(p/'authoring.json')['actions']};m={x['action_id']:x for x in read(p/'membership_review.json')['records']};u={x['action_id']:x for x in read(p/'universe_proposal.json')['candidate_dispositions']};s={x['source_id']:x for x in read(p/'sources.json')['sources']};r=read(p/'source_literal_scope_corrections_83_receipt.json');recs={x['recommendation']:read(p/(x['recommendation']+'.json')) for x in r['corrections']};a['house:119:2:67']['meaning']=a['house:119:2:67']['meaning'].replace('IF a Federal OR State agency','IF another Federal OR State agency')
        with self.assertRaisesRegex(ValueError,'cable agency category acquired unsupported other-agency identity predicate'):validate_source_literal_scope_corrections(a,m,u,s,r,recs)
    def test_catfish_research_institution_examples_are_nonexclusive(self):
        from scripts.validate_infrastructure_discovery_delta import validate_source_literal_scope_corrections
        p=folder(83);a={x['action_id']:x for x in read(p/'authoring.json')['actions']};m={x['action_id']:x for x in read(p/'membership_review.json')['records']};u={x['action_id']:x for x in read(p/'universe_proposal.json')['candidate_dispositions']};s={x['source_id']:x for x in read(p/'sources.json')['sources']};r=read(p/'source_literal_scope_corrections_83_receipt.json');recs={x['recommendation']:read(p/(x['recommendation']+'.json')) for x in r['corrections']};a['house:119:2:88']['meaning']=a['house:119:2:88']['meaning'].replace('research institutions, including those with the specified expertise','the specified expert research institutions')
        with self.assertRaisesRegex(ValueError,'catfish research-institution examples became exclusive expert-only eligibility'):validate_source_literal_scope_corrections(a,m,u,s,r,recs)
    def test_conservation_advance_payment_cost_denominators_and_forest_ceiling(self):
        from scripts.validate_infrastructure_discovery_delta import validate_emergency_conservation_advances
        p=folder(83);action=next(a for a in read(p/'authoring.json')['actions'] if a['action_id']=='house:119:2:109');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('ECP replacement/rehabilitation advances are up to75percentofpayment; ECP repair advances are up to50percentofpayment','ECP advances are75or50percentoftotalprojectcost'),('overall forest assistance ceiling remains75percentoftotalcost','forest assistance addsanother75percentontopofexistinglimit')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'conservation advance denominators or retained ceiling changed'):validate_emergency_conservation_advances(bad,s['govinfo:hr1011eh'],s['govinfo:16usc2201-operative162'],s['govinfo:16usc2206-operative162'])
    def test_conservation_wildfire_spread_and_return_clocks_remain_distinct(self):
        from scripts.validate_infrastructure_discovery_delta import validate_emergency_conservation_advances
        p=folder(83);action=next(a for a in read(p/'authoring.json')['actions'] if a['action_id']=='house:119:2:109');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('new unnatural-ignition inclusion retains the natural-cause spread condition','allgovernmentignitionsqualifyautomatically'),('existing ECP60dayunspent-funds deadline after receipt remains','ECP180dayruleappliestoalladvances')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'conservation wildfire spread or distinct return predicates lost'):validate_emergency_conservation_advances(bad,s['govinfo:hr1011eh'],s['govinfo:16usc2201-operative162'],s['govinfo:16usc2206-operative162'])
    def test_epa_review_preserves_legislation_publication_and_exact_categories(self):
        from scripts.validate_infrastructure_discovery_delta import validate_epa_review_channel_boundaries
        p=folder(85);action=next(a for a in read(p/'authoring.json')['actions'] if a['action_id']=='house:119:2:118');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('It retains mandatory section309review/written comment for proposed Federal-department/agency legislation','It abolishes every EPAreview'),("retains publication of that comment at review's conclusion",'makes all comments private'),('removes the construction/NEPA-linked-action and proposed-regulation categories from this section309duty','removes only the construction category')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);self.assertIn(old,bad['meaning']);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'EPA review deletion lost exact categories or retained legislation/publication'):validate_epa_review_channel_boundaries(bad,s['govinfo:hr6398eh'],s['govinfo:42usc7609-2024-policy-review'],s['govinfo:42usc4332-2024-operative'])
    def test_epa_referral_condition_and_separate_nepa_duties_remain(self):
        from scripts.validate_infrastructure_discovery_delta import validate_epa_review_channel_boundaries
        p=folder(85);action=next(a for a in read(p/'authoring.json')['actions'] if a['action_id']=='house:119:2:118');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('IF the Administrator determines it unsatisfactory','whether or not EPAfinds it unsatisfactory'),('H.R.6398does not amend that separate NEPA4332text','H.R.6398repeals the separateNEPAtext')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);self.assertIn(old,bad['meaning']);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'EPA review conditional referral separate NEPA or candidate boundary lost'):validate_epa_review_channel_boundaries(bad,s['govinfo:hr6398eh'],s['govinfo:42usc7609-2024-policy-review'],s['govinfo:42usc4332-2024-operative'])
    def test_air_monitoring_retains_eligibility_health_and_public_data(self):
        from scripts.validate_infrastructure_discovery_delta import validate_air_monitoring_boundaries
        p=folder(87);action=next(a for a in read(p/'authoring.json')['actions']if a['action_id']=='house:119:2:136');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('the event still must affect air quality, be not reasonably controllable or preventable, and receive the specified Administrator determination','every deliberate fire qualifies automatically'),('Retained principles still prioritize public health','Public health principles are deleted'),('Exclusion from those regulatory uses does not delete the monitoring record or abolish public access','All excluded monitoring data must be erased')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);self.assertIn(old,bad['meaning']);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'air monitoring retained eligibility public health or data duties lost'):validate_air_monitoring_boundaries(bad,s['govinfo:hr6387eh'],s['govinfo:42usc7619-2024-exceptional-events'])
    def test_air_monitoring_regional_alternatives_and_distinct_clocks(self):
        from scripts.validate_infrastructure_discovery_delta import validate_air_monitoring_boundaries
        p=folder(87);action=next(a for a in read(p/'authoring.json')['actions']if a['action_id']=='house:119:2:136');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('OR the Administrator determines such a multistate event occurred','AND the Administrator determines such a multistate event occurred'),('due1yearafterpublicationoftheproposal','due1yearafterenactment'),('due12monthsafterenactment and must then be updated monthly','due18monthsafterenactment and updated yearly')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);self.assertIn(old,bad['meaning']);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'air monitoring regional alternatives clocks or source limits lost'):validate_air_monitoring_boundaries(bad,s['govinfo:hr6387eh'],s['govinfo:42usc7619-2024-exceptional-events'])
    def test_air_monitoring_foushee_not_voting_is_nondirectional(self):
        from scripts.validate_infrastructure_discovery_delta import validate_air_monitoring_nondirectional,validate_air_monitoring_membership_neutrality
        p=folder(87);r=read(p/'generated/readable_candidates.json');c=read(p/'generated/compiled_ir.json');bad=copy.deepcopy(r);next(m for m in bad['members']if m['member_id']=='F000477')['findings'].append(dict(action_ids=['house:119:2:136']))
        with self.assertRaisesRegex(ValueError,'air monitoring Foushee Not Voting became directional or omitted'):validate_air_monitoring_nondirectional(bad,c)
        bad=copy.deepcopy(c);next(m for m in bad['members']if m['member_id']=='F000477')['coverage']['not_voting_actions']=1
        with self.assertRaisesRegex(ValueError,'air monitoring Foushee Not Voting became directional or omitted'):validate_air_monitoring_nondirectional(r,bad)
        record=next(x for x in read(p/'membership_review.json')['records']if x['action_id']=='house:119:2:136');record['rationale']+=' FousheeNotVoting remains nondirectional.'
        with self.assertRaisesRegex(ValueError,'air monitoring shared membership rationale became member-specific'):validate_air_monitoring_membership_neutrality(record)
    def test_military_construction_shift_preserves_math_and_account_lifetimes(self):
        from scripts.validate_infrastructure_discovery_delta import validate_military_construction_shift_boundaries
        p=folder(91);action=next(a for a in read(p/'authoring.json')['actions']if a['action_id']=='house:119:2:174');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('Defense-WideMilitaryConstructionfrom$3,757,301,000to$4,239,133,000','Defense-WideMilitaryConstructionfrom$3,757,301,000to$4,757,301,000'),('available untilSeptember30,2031','available forever')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);self.assertIn(old,bad['meaning']);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'construction shift amount math or distinct account life lost'):validate_military_construction_shift_boundaries(bad,s['congressional-record:8469-amend50-roll174-choice160'],s['house-bill:8469rh-Defensewide-NATO-complete160'],s['govinfo:10usc2806-operative160'])
    def test_military_construction_shift_cannot_be_enacted_or_all_nato_cut(self):
        from scripts.validate_infrastructure_discovery_delta import validate_military_construction_shift_boundaries
        p=folder(91);action=next(a for a in read(p/'authoring.json')['actions']if a['action_id']=='house:119:2:174');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('amendment was rejected80–333with22NotVoting','amendment was adopted and enacted'),('does not repeal2806or end allNATOfunding','repeals2806and ends allNATOfunding'),('Neither fixed amount is automatically raised','Both fixed amounts are automatically raised')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);self.assertIn(old,bad['meaning']);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'construction shift failed outcome fixed conditions or limited NATO scope lost'):validate_military_construction_shift_boundaries(bad,s['congressional-record:8469-amend50-roll174-choice160'],s['house-bill:8469rh-Defensewide-NATO-complete160'],s['govinfo:10usc2806-operative160'])
    def test_battlefield_authorization_deletion_does_not_remove_share_caps(self):
        from scripts.validate_infrastructure_discovery_delta import validate_battlefield_program_boundaries
        p=folder(93);action=next(a for a in read(p/'authoring.json')['actions']if a['action_id']=='house:119:2:192');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('deletes(d), the separate$1millionauthorization, not(c), the50percentFederal-sharecap','deletes all50percentsharecaps'),('one shared$2millionannualauthorization for BOTH308104','separate$2millionannualauthorization EACH for308104')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);self.assertIn(old,bad['meaning']);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'battlefield operative subsection share or joint-pool amount changed'):validate_battlefield_program_boundaries(bad,s['govinfo:hr7618eh'],s['govinfo:54usc3081-2024-operative134'])
    def test_battlefield_study_clocks_and_existing_site_eligibility_remain(self):
        from scripts.validate_infrastructure_discovery_delta import validate_battlefield_program_boundaries
        p=folder(93);action=next(a for a in read(p/'authoring.json')['actions']if a['action_id']=='house:119:2:192');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('within2yearsafterfundsareavailable','within2yearsafterenactment'),('certify WHETHER it meets','mustpositivelycertifyitmeets'),('does not by itself make every studied site eligible for every grant','automatically makes every studied site eligible for all grants')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);self.assertIn(old,bad['meaning']);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'battlefield conditional study clocks or remaining eligibility lost'):validate_battlefield_program_boundaries(bad,s['govinfo:hr7618eh'],s['govinfo:54usc3081-2024-operative134'])
    def test_northwest_straits_base_membership_and_nonvoting_liaison(self):
        from scripts.validate_infrastructure_discovery_delta import validate_northwest_straits_boundaries
        p=folder(93);action=next(a for a in read(p/'authoring.json')['actions']if a['action_id']=='house:119:2:196');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('14base, not a permanent maximum','exactly14forever'),('does not create a fifteenth ordinary voting seat','creates a fifteenth ordinary voting seat'),('twoInteriorappointments','oneInteriorappointment')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);self.assertIn(old,bad['meaning']);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'Northwest Straits membership or liaison boundary lost'):validate_northwest_straits_boundaries(bad,s['govinfo:hr2860eh'],s['govinfo:pl105384-titleIV-original162'],s['nwstraits:1998-report-reprint-edition168'],s['nwstraits:1998-report-reprint-membership-complete169'])
    def test_northwest_straits_advisory_funding_and_old_report_limits(self):
        from scripts.validate_infrastructure_discovery_delta import validate_northwest_straits_boundaries
        p=folder(93);action=next(a for a in read(p/'authoring.json')['actions']if a['action_id']=='house:119:2:196');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('no authority to issue regulations or implement Federal law or regulation','authority to issue allFederalregulations'),('No new fixed appropriation or guaranteed recipient payment','New fixed appropriation and guaranteed payments'),('authority to carry out the title7yearsafterenactment','authority to carry out the title7yearsafterHousepassage')]:
            with self.subTest(boundary=old):
                bad=copy.deepcopy(action);self.assertIn(old,bad['meaning']);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'Northwest Straits regulatory funding sunset or baseline limit lost'):validate_northwest_straits_boundaries(bad,s['govinfo:hr2860eh'],s['govinfo:pl105384-titleIV-original162'],s['nwstraits:1998-report-reprint-edition168'],s['nwstraits:1998-report-reprint-membership-complete169'])
    def test_s629_cost_base_and_return_clock_cannot_inherit_hr1011(self):
        from scripts.validate_infrastructure_discovery_delta import validate_conservation_s629_boundaries
        p=folder(96);a=next(x for x in read(p/'authoring.json')['actions']if x['action_id']=='house:119:2:223');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('receiving75percent of replacement COST or50percent of repair/restoration COST','receiving at most75percent or50percent of payment'),('from60days to180days after receipt','retains60days after receipt')]:
            bad=copy.deepcopy(a);bad['meaning']=bad['meaning'].replace(old,new)
            with self.assertRaisesRegex(ValueError,'S629 cost base percentage or return predicate lost'):validate_conservation_s629_boundaries(bad,s['govinfo:s629es'],s['govinfo:16usc2201-operative162'],s['govinfo:16usc2206-operative162'])
    def test_s629_federal_fire_category_and_total_forest_cap_remain_distinct(self):
        from scripts.validate_infrastructure_discovery_delta import validate_conservation_s629_boundaries
        p=folder(96);a=next(x for x in read(p/'authoring.json')['actions']if x['action_id']=='house:119:2:223');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('not imposed on the separate Federal-caused item','also imposed on all Federal-caused fires'),('retained75percent total-cost assistance cap','removed total-cost assistance cap')]:
            bad=copy.deepcopy(a);bad['meaning']=bad['meaning'].replace(old,new)
            with self.assertRaisesRegex(ValueError,'S629 distinct wildfire category eligibility or forest cap lost'):validate_conservation_s629_boundaries(bad,s['govinfo:s629es'],s['govinfo:16usc2201-operative162'],s['govinfo:16usc2206-operative162'])
    def test_software_loan_discretion_and_all_construction_limits_survive(self):
        from scripts.validate_infrastructure_discovery_delta import validate_software_loan_boundaries
        p=folder(96);a=next(x for x in read(p/'authoring.json')['actions']if x['action_id']=='house:119:2:226');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('Administration MAY provide loans','Administration MUST approve all loans'),('does NOT authorize research-and-development use','authorizes research-and-development use'),('does NOT imply that pre-enactment7(a) loans for these purposes were impermissible','establishes all prior loans were impermissible'),('does NOT limit the definition of working capital','limits working capital to software')]:
            bad=copy.deepcopy(a);bad['meaning']=bad['meaning'].replace(old,new)
            with self.assertRaisesRegex(ValueError,'software loan discretion or construction limit lost'):validate_software_loan_boundaries(bad,s['govinfo:hr915eh'],s['govinfo:15usc636-2024-7a-authority'])
    def test_software_loan_does_not_import_disaster_or_complete_eligibility(self):
        from scripts.validate_infrastructure_discovery_delta import validate_software_loan_boundaries
        p=folder(96);a=next(x for x in read(p/'authoring.json')['actions']if x['action_id']=='house:119:2:226');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('does not establish the remainder of7(a)','certifies all current7(a)eligibility'),('disaster-loan unit is not the operative7(a) baseline','disaster damage is mandatory for these7(a)loans')]:
            bad=copy.deepcopy(a);bad['meaning']=bad['meaning'].replace(old,new)
            with self.assertRaisesRegex(ValueError,'software loan remaining baseline or outcome boundary lost'):validate_software_loan_boundaries(bad,s['govinfo:hr915eh'],s['govinfo:15usc636-2024-7a-authority'])
    def test_exceptional_events_qualification_preserves_original_source_and_actual_extent(self):
        from scripts.validate_infrastructure_discovery_delta import validate_historical86_90_disclosures
        p=folder(96);a={x['action_id']:x for x in read(p/'authoring.json')['actions']};m={x['action_id']:x for x in read(p/'membership_review.json')['records']};u={x['action_id']:x for x in read(p/'universe_proposal.json')['candidate_dispositions']};s={x['source_id']:x for x in read(p/'sources.json')['sources']};r=read(p/'historical86_90_disclosure_corrections_receipt.json')
        bad=copy.deepcopy(a);next(c for c in bad['house:119:2:136']['claim_source_map']if c['source_id']=='govinfo:42usc7619-2024-exceptional-events')['locator']='Captured(a)andKarinote'
        with self.assertRaisesRegex(ValueError,'exceptional-events correction exceeded source locator'):validate_historical86_90_disclosures(bad,m,u,s,r)
        bad=copy.deepcopy(s);bad['govinfo:42usc7619-2024-exceptional-events']['text_version']='Rewritten historical label'
        with self.assertRaisesRegex(ValueError,'disclosure correction changed historical source object'):validate_historical86_90_disclosures(a,m,u,bad,r)
    def test_whistleblower_report_cadence_cannot_return_without_baseline(self):
        from scripts.validate_infrastructure_discovery_delta import validate_historical86_90_disclosures
        p=folder(96);a={x['action_id']:x for x in read(p/'authoring.json')['actions']};m={x['action_id']:x for x in read(p/'membership_review.json')['records']};u={x['action_id']:x for x in read(p/'universe_proposal.json')['candidate_dispositions']};s={x['source_id']:x for x in read(p/'sources.json')['sources']};r=read(p/'historical86_90_disclosure_corrections_receipt.json');m['house:119:2:138']['rationale']=m['house:119:2:138']['rationale'].replace('existing whistleblower report','annual report')
        with self.assertRaisesRegex(ValueError,'bounded disclosure correction or dependent binding differs'):validate_historical86_90_disclosures(a,m,u,s,r)
    def test_voice_pilot_is_optional_with_conditional_punitive_privacy_elements(self):
        from scripts.validate_infrastructure_discovery_delta import validate_voice_pilot_deletion_boundaries
        p=folder(99);a=next(x for x in read(p/'authoring.json')['actions']if x['action_id']=='house:119:2:258');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('permit, rather than require','require'),('punitive or other appropriate actions','nonpunitive use only'),('one year AFTER ESTABLISHMENT','one year AFTER ENACTMENT'),('three years AFTER ESTABLISHMENT','three years AFTER ENACTMENT')]:
            bad=copy.deepcopy(a);bad['meaning']=bad['meaning'].replace(old,new)
            with self.assertRaisesRegex(ValueError,'voice pilot optional conditional elements or clocks lost'):validate_voice_pilot_deletion_boundaries(bad,s['rules:rcp119-33-ndaa-struck-sections'],s['clerk:119:2:258'])
    def test_voice_pilot_deletion_cannot_end_all_testing_or_prove_accuracy(self):
        from scripts.validate_infrastructure_discovery_delta import validate_voice_pilot_deletion_boundaries
        p=folder(99);a=next(x for x in read(p/'authoring.json')['actions']if x['action_id']=='house:119:2:258');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('not all Department of Defense drug testing','all Department of Defense drug testing'),('not evidence that the technology detects drug use accurately','proof of accurate drug detection')]:
            bad=copy.deepcopy(a);bad['meaning']=bad['meaning'].replace(old,new)
            with self.assertRaisesRegex(ValueError,'voice pilot deletion scope accuracy or enacted outcome changed'):validate_voice_pilot_deletion_boundaries(bad,s['rules:rcp119-33-ndaa-struck-sections'],s['clerk:119:2:258'])
    def test_refining_study_has_two_enactment_clocks_and_national_scope(self):
        from scripts.validate_infrastructure_discovery_delta import validate_refining_study_boundaries
        p=folder(99);a=next(x for x in read(p/'authoring.json')['actions']if x['action_id']=='house:119:2:261');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('120days AFTER ENACTMENT','120daysafter study completion'),('Scope is NATIONAL, with California as a required case study','Scope is California only')]:
            bad=copy.deepcopy(a);bad['meaning']=bad['meaning'].replace(old,new)
            with self.assertRaisesRegex(ValueError,'refining study clocks national scope or minimum mechanisms lost'):validate_refining_study_boundaries(bad,s['congressional-record:2026-07-21-ndaa-remaining-offerings'],s['clerk:119:2:261'])
    def test_failed_refining_study_cannot_exercise_preemption_or_find_state_harm(self):
        from scripts.validate_infrastructure_discovery_delta import validate_refining_study_boundaries
        p=folder(99);a=next(x for x in read(p/'authoring.json')['actions']if x['action_id']=='house:119:2:261');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('does not itself preempt or repeal a State law','immediately preempts all State laws'),('subjects for study, not established conclusions','established findings of State-caused harm')]:
            bad=copy.deepcopy(a);bad['meaning']=bad['meaning'].replace(old,new)
            with self.assertRaisesRegex(ValueError,'refining study became actual preemption or factual finding'):validate_refining_study_boundaries(bad,s['congressional-record:2026-07-21-ndaa-remaining-offerings'],s['clerk:119:2:261'])
    def test_investor_clearance_pilot_keeps_discretion_need_to_know_and_security_alternative(self):
        from scripts.validate_infrastructure_discovery_delta import validate_investor_clearance_pilot_boundaries
        p=folder(101);a=next(x for x in read(p/'authoring.json')['actions']if x['action_id']=='house:119:2:274');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('participation approval and investor sponsorship are discretionary','approval is guaranteed'),('LAWFUL NEED-TO-KNOW','unrestricted classified access'),('FACILITY CLEARANCE OR Secretary-approved ALTERNATIVE SECURITY ARRANGEMENT','facility clearance AND an additional arrangement')]:
            bad=copy.deepcopy(a);bad['meaning']=bad['meaning'].replace(old,new)
            with self.assertRaisesRegex(ValueError,'investor pilot mandatory/discretionary security alternatives or eligibility lost'):validate_investor_clearance_pilot_boundaries(bad,s['congressional-record:2026-07-22-ndaa-remaining-offerings'],s['clerk:119:2:274'])
    def test_failed_investor_pilot_does_not_prefer_awards_or_prove_eligible_profit(self):
        from scripts.validate_infrastructure_discovery_delta import validate_investor_clearance_pilot_boundaries
        p=folder(101);a=next(x for x in read(p/'authoring.json')['actions']if x['action_id']=='house:119:2:274');s={x['source_id']:x for x in read(p/'sources.json')['sources']}
        for old,new in [('NO PREFERENCE in Federal contracts','automatic preference in Federal contracts'),('may not be used for personal financial gain, securities trading, market manipulation','may be used for unrestricted personal profits'),('five years AFTER ENACTMENT unless reauthorized','permanent program with no sunset'),('Rejection did not add','Passage enacted')]:
            bad=copy.deepcopy(a);bad['meaning']=bad['meaning'].replace(old,new)
            with self.assertRaisesRegex(ValueError,'investor pilot gain award clocks baseline or failed outcome boundary lost'):validate_investor_clearance_pilot_boundaries(bad,s['congressional-record:2026-07-22-ndaa-remaining-offerings'],s['clerk:119:2:274'])
    def test_roll241_report_extent_correction_preserves_source_and_pending_state(self):
        from scripts.validate_infrastructure_discovery_delta import validate_roll241_report_extent_disclosure
        p=folder(103);r=read(p/'roll241_report_extent_disclosure_correction_receipt.json');m=next(x for x in read(p/'membership_review.json')['records']if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions']if x['action_id']==r['action_id']);s=next(x for x in read(p/'sources.json')['sources']if x['source_id']==r['source_id']);validate_roll241_report_extent_disclosure(m,u,s,r)
        bad=copy.deepcopy(m);bad['rationale']+=r['removed_sentence']
        with self.assertRaisesRegex(ValueError,'roll241 correction exceeded rationale and locator'):validate_roll241_report_extent_disclosure(bad,u,s,r)
        bad=copy.deepcopy(m);next(c for c in bad['claim_source_map']if c['source_id']==s['source_id'])['locator']='Only old stale label'
        with self.assertRaisesRegex(ValueError,'roll241 correction exceeded rationale and locator'):validate_roll241_report_extent_disclosure(bad,u,s,r)
        bad=copy.deepcopy(s);bad['text_version']='Silently rewritten historical label'
        with self.assertRaisesRegex(ValueError,'roll241 retained source object or canonical digest changed'):validate_roll241_report_extent_disclosure(m,u,bad,r)
        bad=copy.deepcopy(u);bad['disposition']='exact_action_ineligible'
        with self.assertRaisesRegex(ValueError,'roll241 universe binding or pending disposition changed'):validate_roll241_report_extent_disclosure(m,bad,s,r)
    def test_hr804_partial_baseline_cannot_supply_rural_definition_or_promote_pending(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr804_partial_baseline_link
        p=folder(104);r=read(p/'hr804_partial_baseline_link_receipt.json');m=next(x for x in read(p/'membership_review.json')['records']if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions']if x['action_id']==r['action_id']);s=next(x for x in read(p/'sources.json')['sources']if x['source_id']==r['source_id']);validate_hr804_partial_baseline_link(m,u,s,r)
        bad=copy.deepcopy(m);bad['rationale']=bad['rationale'].replace('ONLY paragraphs(1)and(2), not all7(b) or its rural paragraph16','the entire7(b), including its rural definition')
        with self.assertRaisesRegex(ValueError,'804partial baseline scope or program-specific qualifications lost'):validate_hr804_partial_baseline_link(bad,u,s,r)
        bad=copy.deepcopy(m);bad['claim_source_map'][-1]['locator']='Full7(b)and rural eligibility certified'
        with self.assertRaisesRegex(ValueError,'804partial baseline became whole program or rural proof'):validate_hr804_partial_baseline_link(bad,u,s,r)
        bad=copy.deepcopy(u);bad['disposition']='interpreted_substantive_directional'
        with self.assertRaisesRegex(ValueError,'804remaining baseline or taxonomy gap was promoted'):validate_hr804_partial_baseline_link(m,bad,s,r)
        bad=copy.deepcopy(r);bad['agricultural_rural_proxy_used']=True
        with self.assertRaisesRegex(ValueError,'804baseline receipt or proxy boundary differs'):validate_hr804_partial_baseline_link(m,u,s,bad)
    def test_investor_first_report_is_due_within_one_year_and_annually_thereafter(self):
        from scripts.validate_infrastructure_discovery_delta import validate_investor_report_deadline_precision
        p=folder(105);r=read(p/'investor_report_deadline_precision_receipt.json');a=next(x for x in read(p/'authoring.json')['actions']if x['action_id']==r['action_id']);m=next(x for x in read(p/'membership_review.json')['records']if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions']if x['action_id']==r['action_id']);s=next(x for x in read(p/'sources.json')['sources']if x['source_id']==r['source_id']);rec=read(p/'investor_clearance_pilot_taxonomy_recommendation.json');validate_investor_report_deadline_precision(a,m,u,s,rec,r)
        for field,old,new in [('compact_description','The first report is due within one year after enactment, with annual reports thereafter;','Reports begin one year after enactment;'),('compact_description',', with annual reports thereafter;',';'),('meaning','would be due WITHIN one year AFTER ENACTMENT and annually thereafter','would be due one year AFTER ENACTMENT and annually thereafter'),('meaning','and annually thereafter','with no annual recurrence')]:
            with self.subTest(field=field,change=new):
                bad=copy.deepcopy(a);self.assertIn(old,bad[field]);bad[field]=bad[field].replace(old,new)
                with self.assertRaisesRegex(ValueError,'investor initial report became fixed start or lost annual recurrence'):validate_investor_report_deadline_precision(bad,m,u,s,rec,r)
    def test_hr1326_partial_arpae_context_cannot_complete_other_programs_or_promote(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hr1326_partial_baseline_link
        p=folder(106);r=read(p/'hr1326_partial_baseline_link_receipt.json');m=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s=next(x for x in read(p/'sources.json')['sources'] if x['source_id']==r['source_id']);validate_hr1326_partial_baseline_link(m,u,s,r)
        bad=copy.deepcopy(m);bad['rationale']=bad['rationale'].replace('qualified by to the maximum extent practicable','unconditional')
        with self.assertRaisesRegex(ValueError,'1326partial program scope or qualifications lost'):validate_hr1326_partial_baseline_link(bad,u,s,r)
        bad=copy.deepcopy(m);bad['claim_source_map'][-1]['locator']='All baseline/current-law requirements resolved'
        with self.assertRaisesRegex(ValueError,'1326partial baseline became whole or current-law proof'):validate_hr1326_partial_baseline_link(bad,u,s,r)
        bad=copy.deepcopy(u);bad['disposition']='interpreted_substantive_directional'
        with self.assertRaisesRegex(ValueError,'1326remaining baseline gap was promoted'):validate_hr1326_partial_baseline_link(m,bad,s,r)
        bad=copy.deepcopy(s);bad['text']+=' Unretained later law.'
        with self.assertRaisesRegex(ValueError,'1326retained baseline object changed'):validate_hr1326_partial_baseline_link(m,u,bad,r)

    def test_shared_consumer_definition_cannot_drop_exclusions_or_complete_pending_bills(self):
        from scripts.validate_infrastructure_discovery_delta import validate_consumer_definition_dependency
        p=folder(107);r=read(p/'consumer_definition_dependency_receipt.json');records={x['action_id']:x for x in read(p/'membership_review.json')['records']};rows={x['action_id']:x for x in read(p/'universe_proposal.json')['candidate_dispositions']};s=next(x for x in read(p/'sources.json')['sources'] if x['source_id']==r['source_id'])
        for case in r['cases']:
            aid=case['action_id'];m=records[aid];u=rows[aid]
            with self.subTest(action=aid):
                validate_consumer_definition_dependency(m,u,s,r)
                bad=copy.deepcopy(m);bad['claim_source_map'][-2]['passage']=bad['claim_source_map'][-2]['passage'].replace('(I) food.','(I) all food is included.')
                with self.assertRaisesRegex(ValueError,'consumer baseline claim lost exact scope or exclusions'):validate_consumer_definition_dependency(bad,u,s,r)
                bad=copy.deepcopy(m);bad['claim_source_map'][-2]['locator']='All technical and current-law baselines complete'
                with self.assertRaisesRegex(ValueError,'consumer baseline claim lost exact scope or exclusions'):validate_consumer_definition_dependency(bad,u,s,r)
                bad=copy.deepcopy(u);bad['disposition']='interpreted_substantive_directional'
                with self.assertRaisesRegex(ValueError,'consumer definition dependency promoted pending case'):validate_consumer_definition_dependency(m,bad,s,r)
        bad=copy.deepcopy(r);bad['source_acquisitions']=1
        with self.assertRaisesRegex(ValueError,'consumer definition receipt boundary differs'):validate_consumer_definition_dependency(m,u,s,bad)

    def regional_commission_cases(self):
        p=folder(108);actions={x['action_id']:x for x in read(p/'authoring.json')['actions']};sources={x['source_id']:x for x in read(p/'sources.json')['sources']};recommendations=read(p/'regional_commission_appropriation_taxonomy_recommendations.json')['cases']
        return [(actions[r['action_id']],sources,r) for r in recommendations]

    def test_regional_commission_candidates_keep_exact_pairs_rejection_and_whole_scope(self):
        from scripts.validate_infrastructure_discovery_delta import validate_regional_commission_amendment
        for a,s,r in self.regional_commission_cases():
            with self.subTest(action=a['action_id']):validate_regional_commission_amendment(a,s,r)

    def test_regional_commission_residuals_cannot_be_zeroed_or_given_to_a_new_program(self):
        from scripts.validate_infrastructure_discovery_delta import validate_regional_commission_amendment
        for a,s,r in self.regional_commission_cases():
            with self.subTest(action=a['action_id']):
                bad=copy.deepcopy(a);bad['meaning']=bad['meaning'].replace('leaving$2,000,000','leaving$0').replace('leaving$250,000','leaving$0')
                with self.assertRaisesRegex(ValueError,'regional commission paired accounting or residual amount differs'):validate_regional_commission_amendment(bad,s,r)

    def test_regional_commission_grant_share_admin_and_matching_limits_are_not_universal(self):
        from scripts.validate_infrastructure_discovery_delta import validate_regional_commission_amendment
        a,s,r=self.regional_commission_cases()[0]
        for old,new in [('At least40percent of GRANT AMOUNTS','At least40percent of the entire appropriation'),('exception when less than10million','no exception'),('NorthernBorder-specific COVID cost-share waiver is not transferred','NorthernBorder waiver applies to every Commission'),('3or more counties OR more than one State AND','3or more counties OR more than one State OR')]:
            with self.subTest(change=new):
                bad=copy.deepcopy(a);self.assertIn(old,bad['meaning']);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'regional commission whole program or funding qualifications lost'):validate_regional_commission_amendment(bad,s,r)

    def test_regional_commission_geography_choice_and_review_boundary_remain_scoped(self):
        from scripts.validate_infrastructure_discovery_delta import validate_regional_commission_amendment
        a,s,r=self.regional_commission_cases()[2];bad=copy.deepcopy(a);bad['meaning']=bad['meaning'].replace('not every county in those eight States','every county in those eight States')
        with self.assertRaisesRegex(ValueError,'regional commission geography or external-definition limit lost'):validate_regional_commission_amendment(bad,s,r)
        bad=copy.deepcopy(a);bad['choice_meanings']['Nay']='supported every Commission program'
        with self.assertRaisesRegex(ValueError,'regional commission choice became component or parent stance'):validate_regional_commission_amendment(bad,s,r)
        bad=copy.deepcopy(r);bad['accepted_membership']=True
        with self.assertRaisesRegex(ValueError,'regional commission independent-review boundary differs'):validate_regional_commission_amendment(a,s,bad)

    def drbc_funding_case(self):
        p=folder(109);a=next(x for x in read(p/'authoring.json')['actions'] if x['action_id']=='house:119:1:228');m=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']=='house:119:1:227');u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']=='house:119:1:227');s={x['source_id']:x for x in read(p/'sources.json')['sources']};r=read(p/'drbc_funding_restriction_taxonomy_recommendation.json');return a,m,u,s,r

    def test_drbc_funding_candidate_uses_verified_retained_operative_pages(self):
        from scripts.validate_infrastructure_discovery_delta import validate_drbc_funding_restriction
        validate_drbc_funding_restriction(*self.drbc_funding_case())

    def test_drbc_funding_cannot_become_all_money_rule_repeal_or_revived_membership(self):
        from scripts.validate_infrastructure_discovery_delta import validate_drbc_funding_restriction
        a,m,u,s,r=self.drbc_funding_case()
        for old,new in [('this Act’s funds, rather than every source of money','all funding from all governments'),('does not itself cancel those other funding authorities','cancels all other funding authorities'),('They are not revived','They are revived')]:
            with self.subTest(change=new):
                bad=copy.deepcopy(a);self.assertIn(old,bad['meaning']);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'DRBC funding scope, financing or historical qualifications lost'):validate_drbc_funding_restriction(bad,m,u,s,r)

    def test_drbc_cannot_invent_retained_text_or_expand_published_rule_asterisks(self):
        from scripts.validate_infrastructure_discovery_delta import validate_drbc_funding_restriction
        a,m,u,s,r=self.drbc_funding_case();bad=copy.deepcopy(s);bad['drbc:compact-operative-retained-109']['text']+=' Invented later law.'
        with self.assertRaisesRegex(ValueError,'DRBC governed operative witness not exact retained extent'):validate_drbc_funding_restriction(a,m,u,bad,r)
        bad=copy.deepcopy(m);bad['rationale']=bad['rationale'].replace('Published asterisks omit unchanged401text','All asterisks expanded into complete regulations')
        with self.assertRaisesRegex(ValueError,'DRBC published rule expanded asterisks or promoted pending case'):validate_drbc_funding_restriction(a,bad,u,s,r)
        bad=copy.deepcopy(u);bad['disposition']='interpreted_substantive_directional'
        with self.assertRaisesRegex(ValueError,'DRBC published rule expanded asterisks or promoted pending case'):validate_drbc_funding_restriction(a,m,bad,s,r)

    def test_roll241_parent_relay_correction_is_required_without_rewriting_history(self):
        from unittest.mock import patch
        from scripts import validate_infrastructure_discovery_delta as validator
        p=folder(109);original=read(p/'roll241_report_extent_disclosure_correction_receipt.json');source=next(x for x in read(p/'sources.json')['sources'] if x['source_id']=='state:roll241-report169');path=validator.ROOT/'docs/review_packets/infrastructure_roll241_relay_attribution_clarification_20261019.json';clarification=read(path)
        validator.validate_roll241_relay_attribution_clarification(clarification,original,source)
        bad=copy.deepcopy(clarification);bad['corrected_attribution']='The independent reviewer introduced the malformed duplicate.'
        with self.assertRaisesRegex(ValueError,'roll241 correcting addendum misattributes the parent relay'):validator.validate_roll241_relay_attribution_clarification(bad,original,source)
        bad=copy.deepcopy(clarification);bad['original_attribution_preimage']['resolution']='Old receipt silently replaced'
        with self.assertRaisesRegex(ValueError,'roll241 attribution original receipt or preimage changed'):validator.validate_roll241_relay_attribution_clarification(bad,original,source)
        bad=copy.deepcopy(clarification);bad['verified_canonical_digest']='0'*64
        with self.assertRaisesRegex(ValueError,'roll241 attribution canonical retained source digest differs'):validator.validate_roll241_relay_attribution_clarification(bad,original,source)
        bad=copy.deepcopy(clarification);bad['meaning_or_disposition_changed']=True
        with self.assertRaisesRegex(ValueError,'roll241 attribution correction became acceptance or semantic change'):validator.validate_roll241_relay_attribution_clarification(bad,original,source)
        original_read=validator.read
        def missing_addendum(candidate):
            if candidate==path:raise FileNotFoundError('required correcting addendum missing')
            return original_read(candidate)
        with patch.object(validator,'read',side_effect=missing_addendum):
            with self.assertRaisesRegex(FileNotFoundError,'required correcting addendum missing'):validator.validate(109,check_files=False)

    def test_title17_dated_program_context_cannot_revive_superseded_law_or_promote_funding_case(self):
        from scripts.validate_infrastructure_discovery_delta import validate_title17_dated_baseline_link
        p=folder(110);r=read(p/'title17_dated_baseline_link_receipt.json');m=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s={x['source_id']:x for x in read(p/'sources.json')['sources']};validate_title17_dated_baseline_link(m,u,s,r)
        for old,new in [('16517text is HISTORICAL relative','16517text is current regardless of'),('additional1billion throughSeptember30,2028with NOT MORE THAN3percent','no other administrative funding'),('four-billion commitment figure is NOT certified as the current aggregate limit','four-billion is the current aggregate limit'),('not loan principal','loan principal')]:
            with self.subTest(change=new):
                bad=copy.deepcopy(m);self.assertIn(old,bad['rationale']);bad['rationale']=bad['rationale'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'Title17 source age, funding or remaining-gap qualifications lost'):validate_title17_dated_baseline_link(bad,u,s,r)
        bad=copy.deepcopy(m);bad['claim_source_map'][-1]['locator']='Current complete law, all funding effects resolved'
        with self.assertRaisesRegex(ValueError,'Title17 baseline claim lost dated exact scope'):validate_title17_dated_baseline_link(bad,u,s,r)
        bad=copy.deepcopy(u);bad['disposition']='interpreted_substantive_directional'
        with self.assertRaisesRegex(ValueError,'Title17 unresolved fee/currentlaw case was promoted'):validate_title17_dated_baseline_link(m,bad,s,r)

    def post_act_case(self):
        p=folder(111);a=next(x for x in read(p/'authoring.json')['actions'] if x['action_id']=='house:119:1:241');s={x['source_id']:x for x in read(p/'sources.json')['sources']};r=read(p/'post_act_taxonomy_recommendation.json');v=read(p/'post_act_retained_baseline_version_receipt.json')['exact_version_binding'];return a,s,r,v

    def test_post_act_candidate_keeps_complete_same_day_amended_House_version(self):
        from scripts.validate_infrastructure_discovery_delta import validate_post_act_boundaries
        a,s,r,v=self.post_act_case();validate_post_act_boundaries(a,s,r,v);bad=copy.deepcopy(s);bad['govinfo:hr3425eh']['text']=bad['govinfo:hr3425eh']['text'].replace('September 8, 2025','September 9, 2025')
        with self.assertRaisesRegex(ValueError,'POSTAct exact amended House version/date binding differs'):validate_post_act_boundaries(a,bad,r,v)

    def test_post_act_cannot_force_replacement_or_collapse_distinct_report_clocks(self):
        from scripts.validate_infrastructure_discovery_delta import validate_post_act_boundaries
        a,s,r,v=self.post_act_case()
        bad=copy.deepcopy(a);bad['compact_description']=bad['compact_description'].replace('choice between replacement and corrective actions','replacement-or-repair determination')
        with self.assertRaisesRegex(ValueError,'POSTAct compact lost nontechnical corrective-action alternative'):validate_post_act_boundaries(bad,s,r,v)
        for old,new in [('report is due UPON COMPLETION','report is due at exactly one year'),('annually thereafter FOR THREE YEARS','annually thereafter forever'),('OR to implement technical, operational or administrative corrective actions','AND install a private replacement'),('does not mandate replacement rather than repair','mandates replacement rather than repair')]:
            with self.subTest(change=new):
                bad=copy.deepcopy(a);self.assertIn(old,bad['meaning']);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'POSTAct timing, alternative, scope or historical qualifications lost'):validate_post_act_boundaries(bad,s,r,v)

    def test_post_act_cannot_convert_contractors_or_revive_historic_police_authority(self):
        from scripts.validate_infrastructure_discovery_delta import validate_post_act_boundaries
        a,s,r,v=self.post_act_case()
        for old,new in [('does not designate DHS contractor employees','designates DHS contractor employees'),('HISTORICAL, not revived operative authority','current revived operative authority'),('not a command that every Facility Security Committee accept every recommendation','a command that every Facility Security Committee accept every recommendation')]:
            with self.subTest(change=new):
                bad=copy.deepcopy(a);bad['meaning']=bad['meaning'].replace(old,new)
                with self.assertRaisesRegex(ValueError,'POSTAct timing, alternative, scope or historical qualifications lost'):validate_post_act_boundaries(bad,s,r,v)

    def test_retained_attestation_proposals_cannot_clear_gates_or_claim_body_reading(self):
        from scripts.validate_infrastructure_discovery_delta import validate_retained_attestation_proposals
        p=folder(112);r=read(p/'retained_eh_attestation_proposals_receipt.json');m={x['action_id']:x for x in read(p/'membership_review.json')['records']};u={x['action_id']:x for x in read(p/'universe_proposal.json')['candidate_dispositions']};s={x['source_id']:x for x in read(p/'sources.json')['sources']};validate_retained_attestation_proposals(m,u,s,r);self.assertTrue(validate(112)['generated_replay']);aid=r['cases'][0]['action_id']
        bad=copy.deepcopy(m);bad[aid]['exact_action_binding_unresolved']=False
        with self.assertRaisesRegex(ValueError,'attestation metadata proposal cleared an unresolved or semantic gate'):validate_retained_attestation_proposals(bad,u,s,r)
        bad=copy.deepcopy(r);bad['cases'][0]['complete_body_reread']=True
        with self.assertRaisesRegex(ValueError,'attestation metadata proposal cleared an unresolved or semantic gate'):validate_retained_attestation_proposals(m,u,s,bad)
        bad=copy.deepcopy(r);bad['cases'][0]['attestation']='Passed the House of Representatives January 22, 2025.'
        with self.assertRaisesRegex(ValueError,'attestation proposal quote or bounded body extent differs'):validate_retained_attestation_proposals(m,u,s,bad)
        bad=copy.deepcopy(s);bad[r['cases'][0]['clerk_source_id']]['metadata']['vote-result']='Failed'
        with self.assertRaisesRegex(ValueError,'attestation proposal Clerk question/result/date mismatch'):validate_retained_attestation_proposals(m,u,bad,r)
        bad=copy.deepcopy(m);bad[aid]['rationale']='All remaining substantive source and membership gaps resolved.'
        with self.assertRaisesRegex(ValueError,'attestation proposal changed prior evidence, flags or material limits'):validate_retained_attestation_proposals(bad,u,s,r)
        bad=copy.deepcopy(m);bad['house:119:1:108']['claim_source_map'][1]['passage']='Old consumer definition silently removed'
        with self.assertRaisesRegex(ValueError,'attestation proposal changed prior evidence, flags or material limits'):validate_retained_attestation_proposals(bad,u,s,r)

    def test_hea117_old_definitions_cannot_become_proposed_or_clear_pending_actions(self):
        from scripts.validate_infrastructure_discovery_delta import validate_hea117_definition_context
        p=folder(113);r=read(p/'hea117_dated_definition_context_receipt.json');m={x['action_id']:x for x in read(p/'membership_review.json')['records']};u={x['action_id']:x for x in read(p/'universe_proposal.json')['candidate_dispositions']};s=next(x for x in read(p/'sources.json')['sources'] if x['source_id']==r['source_id']);validate_hea117_definition_context(m,u,s,r);self.assertTrue(validate(113)['generated_replay'])
        bad=copy.deepcopy(r);bad['proposed_definitions_inherited']=True
        with self.assertRaisesRegex(ValueError,'old context became proposed definitions'):validate_hea117_definition_context(m,u,s,bad)
        bad=copy.deepcopy(s);bad['text']=bad['text'].replace('any single campus','any educational organization')
        with self.assertRaisesRegex(ValueError,'dated definition source differs'):validate_hea117_definition_context(m,u,bad,r)
        for aid in ['house:119:1:79','house:119:1:80','house:119:1:81','house:119:1:82','house:119:1:83']:
            bad=copy.deepcopy(m);bad[aid]['claim_source_map']=bad[aid]['claim_source_map'][1:]
            with self.assertRaisesRegex(ValueError,'changed prior action evidence flags or pending state'):validate_hea117_definition_context(bad,u,s,r)
        bad=copy.deepcopy(m);bad['house:119:1:83']['exact_action_binding_unresolved']=False
        with self.assertRaisesRegex(ValueError,'changed prior action evidence flags or pending state'):validate_hea117_definition_context(bad,u,s,r)

    def test_title17_fee_collection_includes_financial_close_date_only(self):
        from scripts.validate_infrastructure_discovery_delta import validate_title17_same_day_fee_precision
        p=folder(113);r=read(p/'title17_same_day_fee_precision_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s=next(x for x in read(p/'sources.json')['sources'] if x['source_id']==r['source_id']);validate_title17_same_day_fee_precision(a,u,s,r)
        for bad_text in ['fee collection after financial close','fee collection before financial close','fee collection on or after financial close with all fee-offset interactions resolved']:
            bad=copy.deepcopy(a);bad['rationale']=bad['rationale'].replace('fee collection on or after financial close',bad_text)
            with self.assertRaisesRegex(ValueError,'excluded same-day collection or exceeded exact phrase'):validate_title17_same_day_fee_precision(bad,u,s,r)
        bad=copy.deepcopy(r);bad['fee_offset_interaction_resolved']=True
        with self.assertRaisesRegex(ValueError,'same-day boundary or unresolved limits differ'):validate_title17_same_day_fee_precision(a,u,s,bad)

    def test_title17_export_lengths_match_published_lf_bytes_without_other_changes(self):
        from scripts import validate_infrastructure_discovery_delta as validator
        p=validator.ROOT/'docs/review_packets/infrastructure_batch110_title17_original_objects/manifest.json';m=read(p);r=read(folder(113)/'title17_export_length_correction_receipt.json');objects={x['export_path']:(validator.ROOT/x['export_path']).read_bytes().replace(b'\r\n',b'\n') for x in m['objects']};validator.validate_title17_export_lengths(m,objects,r)
        for i in range(7):
            bad=copy.deepcopy(m);bad['objects'][i]['export_bytes']+=9
            with self.assertRaisesRegex(ValueError,'exported byte length or preserved hash differs'):validator.validate_title17_export_lengths(bad,objects,r)
        bad=copy.deepcopy(m);bad['objects'][0]['origin_git_blob']='0'*40
        with self.assertRaisesRegex(ValueError,'exceeded seven length fields'):validator.validate_title17_export_lengths(bad,objects,r)
        bad=copy.deepcopy(objects);path=m['objects'][0]['export_path'];bad[path]+=b' '
        with self.assertRaisesRegex(ValueError,'exported byte length or preserved hash differs'):validator.validate_title17_export_lengths(m,bad,r)

    def test_land_baselines_cannot_certify_maps_revive_terms_or_clear_membership(self):
        from scripts.validate_infrastructure_discovery_delta import validate_land_governance_baselines
        p=folder(114);r=read(p/'land_governance_dated_baseline_receipt.json');m={x['action_id']:x for x in read(p/'membership_review.json')['records']};u={x['action_id']:x for x in read(p/'universe_proposal.json')['candidate_dispositions']};s={x['source_id']:x for x in read(p/'sources.json')['sources']};validate_land_governance_baselines(m,u,s,r);self.assertTrue(validate(114)['generated_replay'])
        bad=copy.deepcopy(r);bad['cases'][0]['actual_map_or_instrument_reviewed']=True
        with self.assertRaisesRegex(ValueError,'became map/current-law/membership clearance'):validate_land_governance_baselines(m,u,s,bad)
        bad=copy.deepcopy(r);bad['cases'][1]['domain_membership_accepted']=True
        with self.assertRaisesRegex(ValueError,'became map/current-law/membership clearance'):validate_land_governance_baselines(m,u,s,bad)
        bad=copy.deepcopy(s);bad['govinfo:40usc8902-services181']['text']=bad['govinfo:40usc8902-services181']['text'].replace('June 24, 2003','May 1, 1986')
        with self.assertRaisesRegex(ValueError,'retained unit or source changed'):validate_land_governance_baselines(m,u,bad,r)
        bad=copy.deepcopy(m);bad['house:119:1:28']['rationale']=bad['house:119:1:28']['rationale'].replace('historical ten-year','renewed ten-year')
        with self.assertRaisesRegex(ValueError,'changed earlier evidence flags or exact-action limits'):validate_land_governance_baselines(bad,u,s,r)
        bad=copy.deepcopy(m);bad['house:119:1:28']['rationale']=bad['house:119:1:28']['rationale'].replace('administration, which remains','administration, which always transfers')
        with self.assertRaisesRegex(ValueError,'changed earlier evidence flags or exact-action limits'):validate_land_governance_baselines(bad,u,s,r)
        bad=copy.deepcopy(m);bad['house:119:1:18']['claim_source_map']=bad['house:119:1:18']['claim_source_map'][1:]
        with self.assertRaisesRegex(ValueError,'changed earlier evidence flags or exact-action limits'):validate_land_governance_baselines(bad,u,s,r)
        bad=copy.deepcopy(r);bad['cases'][1]['appended_claims'][1]['passage']='All easements extinguished.'
        with self.assertRaisesRegex(ValueError,'omitted operative or historical context'):validate_land_governance_baselines(m,u,s,bad)

    def test_nepa_framework_preserves_conditional_review_and_pending_proposal_limits(self):
        from scripts.validate_infrastructure_discovery_delta import validate_nepa_review_framework
        p=folder(115);r=read(p/'nepa_dated_review_framework_receipt.json');m={x['action_id']:x for x in read(p/'membership_review.json')['records']};u={x['action_id']:x for x in read(p/'universe_proposal.json')['candidate_dispositions']};s={x['source_id']:x for x in read(p/'sources.json')['sources']};validate_nepa_review_framework(m,u,s,r);self.assertTrue(validate(115)['generated_replay'])
        for field in ['whole_proposal_effects_resolved','whole_parent_body_reread','current_law_certified','rejected_changes_imported']:
            bad=copy.deepcopy(r);bad['cases'][3][field]=True
            with self.assertRaisesRegex(ValueError,'became whole-effect parent/current-law or rejection clearance'):validate_nepa_review_framework(m,u,s,bad)
        aid='house:119:1:354'
        for old,new in [('SOONER OF','LATER OF'),('NOT EXCEEDING90days UNLESS longer','automatic project approval after90days'),('after5years only after reevaluating','after5years without reevaluating'),('exception for substantial new circumstances or information about the significance of adverse effects bearing on the analysis','unconditional five-year reliance'),('UNLESS essential','under no circumstances'),('independent agency evaluation/responsibility','automatic acceptance of sponsor findings')]:
            bad=copy.deepcopy(m);bad[aid]['rationale']=bad[aid]['rationale'].replace(old,new)
            with self.assertRaisesRegex(ValueError,'changed prior evidence flags or conditional review boundaries'):validate_nepa_review_framework(bad,u,s,r)
        bad=copy.deepcopy(m);bad['house:119:1:356']['exact_action_binding_unresolved']=False
        with self.assertRaisesRegex(ValueError,'changed prior evidence flags or conditional review boundaries'):validate_nepa_review_framework(bad,u,s,r)
        bad=copy.deepcopy(s);bad['govinfo:42usc4336c-2024-operative']['text']=bad['govinfo:42usc4336c-2024-operative']['text'].replace('consult with','do not consult with')
        with self.assertRaisesRegex(ValueError,'source or dated extent changed'):validate_nepa_review_framework(m,u,bad,r)
        bad=copy.deepcopy(m);bad[aid]['claim_source_map']=bad[aid]['claim_source_map'][1:]
        with self.assertRaisesRegex(ValueError,'changed prior evidence flags or conditional review boundaries'):validate_nepa_review_framework(bad,u,s,r)

    def test_complete_4776_retained_body_cannot_clear_versions_or_repair_printed_questions(self):
        from scripts.validate_infrastructure_discovery_delta import validate_4776_complete_retained_body
        p=folder(116);r=read(p/'hr4776_complete_retained_body_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s=next(x for x in read(p/'sources.json')['sources'] if x['source_id']==r['source_id']);validate_4776_complete_retained_body(a,u,s,r);self.assertTrue(validate(116)['generated_replay'])
        for field in ['exact_floor_version_gate_cleared','printed_references_resolved','current_law_certified','new_shared_meaning_authored','rejected_amendments_imported']:
            bad=copy.deepcopy(r);bad[field]=True
            with self.assertRaisesRegex(ValueError,'cleared floor/reference/current-law/meaning gates'):validate_4776_complete_retained_body(a,u,s,bad)
        bad=copy.deepcopy(a);bad['claim_source_map'][-1]['passage']=s['text'][:3000]
        with self.assertRaisesRegex(ValueError,'changed earlier evidence flags or complete read extent'):validate_4776_complete_retained_body(bad,u,s,r)
        bad=copy.deepcopy(a);bad['exact_action_binding_unresolved']=False
        with self.assertRaisesRegex(ValueError,'cleared floor/reference/current-law/meaning gates'):validate_4776_complete_retained_body(bad,u,s,r)
        bad=copy.deepcopy(r);bad['topics'][4]['start']+=1
        with self.assertRaisesRegex(ValueError,'section coverage is incomplete'):validate_4776_complete_retained_body(a,u,s,bad)
        bad=copy.deepcopy(r);bad['printed_reference_witnesses'][1]['quote']=bad['printed_reference_witnesses'][1]['quote'].replace('107(g)(3)','107(g)(6)')
        with self.assertRaisesRegex(ValueError,'references or supplemental deadline were silently repaired'):validate_4776_complete_retained_body(a,u,s,bad)
        for old,new in [('OTHER OUTSTANDING AUTHORIZATIONS','all permits completed'),('NOT silently rendered as a new150days-after clock','automatically a new150days-after clock'),('BOTH exceptions','no exceptions')]:
            bad=copy.deepcopy(a);bad['rationale']=bad['rationale'].replace(old,new)
            with self.assertRaisesRegex(ValueError,'changed earlier evidence flags or complete read extent'):validate_4776_complete_retained_body(bad,u,s,r)
        bad=copy.deepcopy(a);bad['claim_source_map']=bad['claim_source_map'][1:]
        with self.assertRaisesRegex(ValueError,'changed earlier evidence flags or complete read extent'):validate_4776_complete_retained_body(bad,u,s,r)

    def test_senate_data_dated_context_cannot_imply_notice_revival_payment_or_claim_effects(self):
        from scripts.validate_infrastructure_discovery_delta import validate_senate_data_dated_context
        p=folder(117);r=read(p/'senate_data_dated_program_context_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s=next(x for x in read(p/'sources.json')['sources'] if x['source_id']==r['source_id']);validate_senate_data_dated_context(a,u,s,r);self.assertTrue(validate(117)['generated_replay'])
        for field in ['immediate_pre213_version_certified','repeal_effects_resolved','prior_law_revived','accrued_claims_cancelled','automatic_payment_inferred','current_law_certified']:
            bad=copy.deepcopy(r);bad[field]=True
            with self.assertRaisesRegex(ValueError,'became revival/payment/current-law clearance'):validate_senate_data_dated_context(a,u,s,bad)
        for old,new in [('permission to notify, NOT an affirmative notice mandate','mandatory notice in every case'),('quash OR modify','quash in every case'),('intended-recipient use qualification','unrestricted privileges for every person')]:
            bad=copy.deepcopy(a);bad['rationale']=bad['rationale'].replace(old,new)
            with self.assertRaisesRegex(ValueError,'changed earlier evidence flags or dated claim'):validate_senate_data_dated_context(bad,u,s,r)
        bad=copy.deepcopy(s);bad['text']=bad['text'].replace('shall not be barred','must always notify')
        with self.assertRaisesRegex(ValueError,'dated program source differs'):validate_senate_data_dated_context(a,u,bad,r)
        bad=copy.deepcopy(a);bad['claim_source_map']=bad['claim_source_map'][1:]
        with self.assertRaisesRegex(ValueError,'changed earlier evidence flags or dated claim'):validate_senate_data_dated_context(bad,u,s,r)

    def test_wildlife_context_cannot_mix_share_bases_repair_references_or_clear_membership(self):
        from scripts.validate_infrastructure_discovery_delta import validate_wildlife_dated_program_context
        p=folder(118);r=read(p/'wildlife_dated_program_context_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s={x['source_id']:x for x in read(p/'sources.json')['sources']};validate_wildlife_dated_program_context(a,u,s,r);self.assertTrue(validate(118)['generated_replay'])
        for field in ['printed_program_reference_repaired','all_projects_infrastructure','federal_shares_changed','current_law_certified','membership_accepted']:
            bad=copy.deepcopy(r);bad[field]=True
            with self.assertRaisesRegex(ValueError,'cleared program/reference/share/membership gates'):validate_wildlife_dated_program_context(a,u,s,bad)
        for old,new in [('MAY be supervised','must be supervised'),('EXCLUDING LAW ENFORCEMENT','including all law enforcement'),('up-to90percent','guaranteed100percent'),('no silent repair to669c(e)','all references automatically corrected')]:
            bad=copy.deepcopy(a);bad['rationale']=bad['rationale'].replace(old,new)
            with self.assertRaisesRegex(ValueError,'changed earlier evidence flags or complete claims'):validate_wildlife_dated_program_context(bad,u,s,r)
        bad=copy.deepcopy(a);bad['claim_source_map']=bad['claim_source_map'][1:]
        with self.assertRaisesRegex(ValueError,'changed earlier evidence flags or complete claims'):validate_wildlife_dated_program_context(bad,u,s,r)

    def test_4776_challenge_precision_only_limits_establishment_and_preserves_preimage(self):
        from scripts.validate_infrastructure_discovery_delta import validate_4776_establishment_challenge_precision
        p=folder(118);r=read(p/'hr4776_establishment_challenge_precision_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s=next(x for x in read(p/'sources.json')['sources'] if x['source_id']==r['source_id']);validate_4776_establishment_challenge_precision(a,u,s,r)
        for text in ['no-categorical-exclusion-challenge conditions','no-application-specific-challenges condition','all application challenges necessarily survive']:
            bad=copy.deepcopy(a);bad['rationale']=bad['rationale'].replace(r['rationale_replacement'][1],text)
            with self.assertRaisesRegex(ValueError,'exceeded exact phrase or retained broad shorthand'):validate_4776_establishment_challenge_precision(bad,u,s,r)
        bad=copy.deepcopy(r);bad['application_specific_challenge_outcomes_decided']=True
        with self.assertRaisesRegex(ValueError,'decided application challenges or exceeded scope'):validate_4776_establishment_challenge_precision(a,u,s,bad)
        bad=copy.deepcopy(r);bad['source_quote']='challenge any categorical exclusion application'
        with self.assertRaisesRegex(ValueError,'source quote differs'):validate_4776_establishment_challenge_precision(a,u,s,bad)
        bad=copy.deepcopy(a);bad['claim_source_map']=bad['claim_source_map'][1:]
        with self.assertRaisesRegex(ValueError,'exceeded exact phrase or retained broad shorthand'):validate_4776_establishment_challenge_precision(bad,u,s,r)

    def test_nepa_judicial_context_cannot_replace_child_or_certify_full_reported_form(self):
        from scripts.validate_infrastructure_discovery_delta import validate_nepa_judicial_dependency_context
        p=folder(119);r=read(p/'nepa_judicial_dependency_context_receipt.json');m={x['action_id']:x for x in read(p/'membership_review.json')['records']};u={x['action_id']:x for x in read(p/'universe_proposal.json')['candidate_dispositions']};s={x['source_id']:x for x in read(p/'sources.json')['sources']};validate_nepa_judicial_dependency_context(m,u,s,r);self.assertTrue(validate(119)['generated_replay'])
        for field in ['whole_RH_body_read','child_antecedent_resolved','whole_version_equivalence_certified','claim_remedy_outcomes_decided','current_law_certified','membership_accepted']:
            bad=copy.deepcopy(r);bad['cases'][0][field]=True
            with self.assertRaisesRegex(ValueError,'cleared child/version/standing/outcome gates'):validate_nepa_judicial_dependency_context(m,u,s,bad)
        bad=copy.deepcopy(r);bad['cases'][0]['appended_claims'][0]['passage']=s['govinfo:hr4776rh']['text']
        with self.assertRaisesRegex(ValueError,'became whole RH or truncated operative context'):validate_nepa_judicial_dependency_context(m,u,s,bad)
        bad=copy.deepcopy(r);bad['cases'][1]['source_ids'].insert(0,'govinfo:hr4776rh')
        with self.assertRaisesRegex(ValueError,'transferred reported form to parent'):validate_nepa_judicial_dependency_context(m,u,s,bad)
        bad=copy.deepcopy(m);bad['house:119:1:352']['claim_source_map']=bad['house:119:1:352']['claim_source_map'][1:]
        with self.assertRaisesRegex(ValueError,'changed earlier evidence flags or comparative limits'):validate_nepa_judicial_dependency_context(bad,u,s,r)
        bad=copy.deepcopy(m);bad['house:119:1:356']['rationale']=bad['house:119:1:356']['rationale'].replace('not the entire six-ground list','the entire six-ground list repealed')
        with self.assertRaisesRegex(ValueError,'changed earlier evidence flags or comparative limits'):validate_nepa_judicial_dependency_context(bad,u,s,r)

    def test_urban_definition_keeps_population_alternatives_and_boundary_exception_scoped(self):
        from scripts.validate_infrastructure_discovery_delta import validate_urban_definition_context
        p=folder(120);r=read(p/'urban_dated_definition_context_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s=next(x for x in read(p/'sources.json')['sources'] if x['source_id']==r['source_id']);validate_urban_definition_context(a,u,s,r);self.assertTrue(validate(120)['generated_replay'])
        for field in ['full_101_reviewed','current_Census_geography_certified','EDGE_thresholds_resolved','actual_recipient_eligibility_decided','current_law_certified','membership_accepted']:
            bad=copy.deepcopy(r);bad[field]=True
            with self.assertRaisesRegex(ValueError,'cleared full-law/geography/EDGE/recipient/membership gates'):validate_urban_definition_context(a,u,s,bad)
        bad=copy.deepcopy(s);bad['text']=bad['text'].replace('5,000','50,000')
        with self.assertRaisesRegex(ValueError,'dated definition source differs'):validate_urban_definition_context(a,u,bad,r)
        for old,new in [('5,000cutoff is not universal','5,000cutoff applies to every State portion'),('50,000people AND Census designation','population alone is sufficient'),('NOT a population waiver','a waiver of population limits'),('NOT imported into paragraph36','also automatically imported into paragraph36')]:
            bad=copy.deepcopy(a);bad['rationale']=bad['rationale'].replace(old,new)
            with self.assertRaisesRegex(ValueError,'dropped remaining named program gaps'):validate_urban_definition_context(bad,u,s,r)
        bad=copy.deepcopy(r);bad['previous_gap_phrase_replacement'][1]='All remaining program and EDGEgaps resolved.'
        with self.assertRaisesRegex(ValueError,'dropped remaining named program gaps'):validate_urban_definition_context(a,u,s,bad)
        bad=copy.deepcopy(a);bad['claim_source_map']=bad['claim_source_map'][1:]
        with self.assertRaisesRegex(ValueError,'changed prior evidence flags or bounded claim'):validate_urban_definition_context(bad,u,s,r)

    def test_1048_complete_body_preserves_thresholds_privacy_waiver_court_and_timing_limits(self):
        from scripts.validate_infrastructure_discovery_delta import validate_1048_complete_retained_body
        p=folder(121);r=read(p/'hr1048_complete_retained_body_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s={x['source_id']:x for x in read(p/'sources.json')['sources']};validate_1048_complete_retained_body(a,u,s,r);self.assertTrue(validate(121)['generated_replay'])
        for field in ['whole_floor_version_equivalence_certified','external_definitions_resolved','printed_reference_formula_conformance_resolved','current_law_certified','new_meaning_authored','membership_accepted','rejected_children_imported']:
            bad=copy.deepcopy(r);bad[field]=True
            with self.assertRaisesRegex(ValueError,'cleared floor/external/current-law/meaning gates'):validate_1048_complete_retained_body(a,u,s,bad)
        bad=copy.deepcopy(r);bad['topics'].pop(4)
        with self.assertRaisesRegex(ValueError,'omitted a body section'):validate_1048_complete_retained_body(a,u,s,bad)
        bad=copy.deepcopy(a);bad['claim_source_map'][0]['passage']=bad['claim_source_map'][0]['passage'][:3000]
        with self.assertRaisesRegex(ValueError,'changed source/claim passages/evidence flags'):validate_1048_complete_retained_body(bad,u,s,r)
        bad=copy.deepcopy(r);bad['reference_and_formula_witnesses'][1]['quote']='1286(c)(9)(A)'
        with self.assertRaisesRegex(ValueError,'silently repaired'):validate_1048_complete_retained_body(a,u,s,bad)
        for old,new in [('50,000dollars or more','every gift'),('natural-person name/address protections','all identities public'),('UNREDACTED interagency','only redacted interagency'),('60dayPRE-CONTRACT-or-RENEWAL','60days after waiver request'),('SOONER of one-year-after-enactment or contract end','one year after issuance'),('ANY of the previousfivecalendar years OR titleVIfunding','all faculty everywhere'),('NONPUBLIC AND','public OR'),('REPORTING, not a standalone command to DIVEST','mandatory divestment'),('court-COMPELLED compliance before','alleged errors alone before'),('not automatic fines','automatic fines'),('AND the specified waiver-ineligibility','OR three alleged reporting errors'),('THREE YEARS OF STUDY INITIATION','three years after enactment')]:
            bad=copy.deepcopy(r);bad['new_rationale']=bad['new_rationale'].replace(old,new);aa=copy.deepcopy(a);aa['rationale']=bad['new_rationale'];uu=copy.deepcopy(u);uu.update(reason=aa['rationale'],rationale=aa['rationale']);uu['review_progress']['shared_review_record_sha256']=digest(aa)
            with self.assertRaisesRegex(ValueError,'boundary lost'):validate_1048_complete_retained_body(aa,uu,s,bad)
        bad=copy.deepcopy(r);bad['historical_baseline_paragraph']='Old definitions now govern proposed117A-D.'
        with self.assertRaisesRegex(ValueError,'old-definition baseline history'):validate_1048_complete_retained_body(a,u,s,bad)

    def test_hr33_full_source_preserves_tax_crew_project_and_agreement_conditions(self):
        from scripts.validate_infrastructure_discovery_delta import validate_33_complete_retained_body
        p=folder(122);r=read(p/'hr33_complete_retained_body_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s=next(x for x in read(p/'sources.json')['sources'] if x['source_id']==r['source_id']);validate_33_complete_retained_body(a,u,s,r);self.assertTrue(validate(122)['generated_replay'])
        for field in ['external_tax_baselines_resolved','model_convention_reviewed','actual_reciprocity_or_agreement_certified','current_law_certified','new_meaning_authored','membership_accepted']:
            bad=copy.deepcopy(r);bad[field]=True
            with self.assertRaisesRegex(ValueError,'cleared external-tax/current-law/actual-agreement/meaning gates'):validate_33_complete_retained_body(a,u,s,bad)
        bad=copy.deepcopy(r);bad['topics'].pop(10)
        with self.assertRaisesRegex(ValueError,'coverage omitted'):validate_33_complete_retained_body(a,u,s,bad)
        for old,new in [('ownership/12-month conditions and RIC/REIT limits','every dividend qualifies'),('non-US resident OR a regular ship/aircraft crew member','non-US resident AND any transport worker'),('BOTH its non-US-person-employer','only its employer'),('30,000-dollar gross-receipts ceiling','unlimited receipts'),('MORE THAN 12 months','12 months or less'),('MORE THAN 30 days','any interruption'),('RECIPROCITY DETERMINATION','automatic relief on passage'),('60 days BEFORE entering','60 days after entering'),('270 days AFTER entering','270 days after enactment'),('approval AND implementing legislation','signature alone'),("does not erase Title I's proposed Code amendments",'this bill never amends the Code')]:
            bad=copy.deepcopy(r);bad['new_rationale']=bad['new_rationale'].replace(old,new);aa=copy.deepcopy(a);aa['rationale']=bad['new_rationale'];uu=copy.deepcopy(u);uu.update(reason=aa['rationale'],rationale=aa['rationale']);uu['review_progress']['shared_review_record_sha256']=digest(aa)
            with self.assertRaisesRegex(ValueError,'boundary lost'):validate_33_complete_retained_body(aa,uu,s,bad)
        bad=copy.deepcopy(a);bad['exact_action_binding_unresolved']=True
        with self.assertRaisesRegex(ValueError,'changed source/claim passage/evidence flags'):validate_33_complete_retained_body(bad,u,s,r)
        bad=copy.deepcopy(a);bad['claim_source_map'][0]['passage']=s['text'][3000:6000]
        with self.assertRaisesRegex(ValueError,'changed source/claim passage/evidence flags'):validate_33_complete_retained_body(bad,u,s,r)

    def test_hr1048_asset_exclusion_requires_direct_exempt_purpose_use(self):
        from scripts.validate_infrastructure_discovery_delta import validate_1048_direct_use_precision
        p=folder(122);r=read(p/'hr1048_direct_use_asset_precision_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s=next(x for x in read(p/'sources.json')['sources'] if x['source_id']==r['source_id']);validate_1048_direct_use_precision(a,u,s,r)
        bad=copy.deepcopy(a);bad['rationale']=bad['rationale'].replace('those used directly in carrying out', 'those used in carrying out')
        with self.assertRaisesRegex(ValueError,'direct-use qualifier lost'):validate_1048_direct_use_precision(bad,u,s,r)
        bad=copy.deepcopy(r);bad['rationale_replacement'][1]=bad['rationale_replacement'][1].replace('directly ','')
        with self.assertRaisesRegex(ValueError,'direct-use precision changed exclusion'):validate_1048_direct_use_precision(a,u,s,bad)
        for field in ['IRC4968_application_decided','membership_accepted','current_law_certified']:
            bad=copy.deepcopy(r);bad[field]=True
            with self.assertRaisesRegex(ValueError,'cleared coverage/current-law/membership gates'):validate_1048_direct_use_precision(a,u,s,bad)
        bad=copy.deepcopy(r);bad['source_passage']=bad['source_passage'].replace('directly ','')
        with self.assertRaisesRegex(ValueError,'lost exact source witness'):validate_1048_direct_use_precision(a,u,s,bad)

    def test_hr275_named_definitions_exclude_nationals_and_do_not_infer_risk_or_procurement_rules(self):
        from scripts.validate_infrastructure_discovery_delta import validate_275_named_definition_context
        p=folder(123);r=read(p/'hr275_dated_named_definitions_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s={x['source_id']:x for x in read(p/'sources.json')['sources']};validate_275_named_definition_context(a,u,s,r);self.assertTrue(validate(123)['generated_replay'])
        for field in ['complete_1101_or_4872_reviewed','procurement_rules_imported','covered_nationality_is_risk_finding','actual_person_or_encounter_certified','current_law_certified','whole_version_binding_cleared','membership_accepted']:
            bad=copy.deepcopy(r);bad[field]=True
            with self.assertRaisesRegex(ValueError,'cleared law/procurement/risk/person/version/membership gates'):validate_275_named_definition_context(a,u,s,bad)
        for old,new in [('NEITHER a United States citizen NOR a United States national','every noncitizen including USnationals'),('Russian Federation','a fifth unnamed nation'),('not surrounding defense-procurement restrictions','all defense-procurement restrictions'),('NOT an individual risk finding','an automatic individual risk finding'),('travel-pattern analysis of POTENTIAL risk','nationality alone as actual wrongdoing')]:
            bad=copy.deepcopy(r);bad['new_rationale']=bad['new_rationale'].replace(old,new);aa=copy.deepcopy(a);aa['rationale']=bad['new_rationale'];uu=copy.deepcopy(u);uu.update(reason=aa['rationale'],rationale=aa['rationale']);uu['review_progress']['shared_review_record_sha256']=digest(aa)
            with self.assertRaisesRegex(ValueError,'potential-risk boundary lost'):validate_275_named_definition_context(aa,uu,s,bad)
        bad=copy.deepcopy(a);bad['claim_source_map']=bad['claim_source_map'][1:]
        with self.assertRaisesRegex(ValueError,'changed prior claims/evidence flags'):validate_275_named_definition_context(bad,u,s,r)
        bad=copy.deepcopy(r);bad['appended_claims'][0]['passage']='A person who is not a citizen.'
        with self.assertRaisesRegex(ValueError,'exceeded named dated scope'):validate_275_named_definition_context(a,u,s,bad)

    def test_hr4922_record_context_keeps_private_files_purpose_clocks_and_printed_reference_distinct(self):
        from scripts.validate_infrastructure_discovery_delta import validate_4922_record_access_context
        p=folder(124);r=read(p/'hr4922_dated_record_access_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s={x['source_id']:x for x in read(p/'sources.json')['sources']};validate_4922_record_access_context(a,u,s,r);self.assertTrue(validate(124)['generated_replay'])
        for field in ['complete_title16_reviewed','all_privacy_interactions_resolved','raw_files_public_release_authorized','actual_record_or_person_classified','printed_reference_repaired','current_law_certified','new_meaning_authored','membership_accepted']:
            bad=copy.deepcopy(r);bad[field]=True
            with self.assertRaisesRegex(ValueError,'cleared full-law/privacy/public-files/person/reference/current-law/meaning gates'):validate_4922_record_access_context(a,u,s,bad)
        for old,new in [('Case records EXCLUDE social records','All records are the same class'),('press provision is DISCRETIONARY','all press access is mandatory'),('LIMITED to photos, description, addresses and contact information','unlimited access to all health files'),('Mayor MAY','Mayor SHALL'),('within ONE HOUR','within one month'),('ONLY specified INFORMATION, NOT the records/files','all raw records and files'),('EVERY SIX MONTHS','every month already'),('FOR THE WEBSITE PURPOSE','for any public purpose'),('exactly(b)/(b)/(a)','all sections without limitation'),('NO JUVENILE PERSONALLY IDENTIFIABLE INFORMATION','juvenile names and addresses allowed'),('prints16-2341although the inserted section is16-2340a','automatically conformed to16-2340a')]:
            bad=copy.deepcopy(r);bad['new_rationale']=bad['new_rationale'].replace(old,new);aa=copy.deepcopy(a);aa['rationale']=bad['new_rationale'];uu=copy.deepcopy(u);uu.update(reason=aa['rationale'],rationale=aa['rationale']);uu['review_progress']['shared_review_record_sha256']=digest(aa)
            with self.assertRaisesRegex(ValueError,'reference boundary lost'):validate_4922_record_access_context(aa,uu,s,bad)
        bad=copy.deepcopy(a);bad['claim_source_map']=bad['claim_source_map'][1:]
        with self.assertRaisesRegex(ValueError,'changed prior source claims/evidence flags'):validate_4922_record_access_context(bad,u,s,r)
        bad=copy.deepcopy(r);bad['appended_claims'][1]['passage']=bad['appended_claims'][1]['passage'][:3000]
        with self.assertRaisesRegex(ValueError,'exceeded operative section scope'):validate_4922_record_access_context(a,u,s,bad)

    def test_hr4922_definitions_keep_offense_lists_allegation_child_exceptions_and_age_at_act_distinct(self):
        from scripts.validate_infrastructure_discovery_delta import validate_4922_definition_context
        p=folder(125);r=read(p/'hr4922_dated_definition_jurisdiction_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s={x['source_id']:x for x in read(p/'sources.json')['sources']};validate_4922_definition_context(a,u,s,r);self.assertTrue(validate(125)['generated_replay'])
        for field in ['later_November_unit_substituted','allegation_is_conviction','child_equals_website_juvenile','statistical_population_resolved','all_privacy_interactions_resolved','actual_record_or_person_classified','printed_reference_repaired','current_law_certified','new_meaning_authored','membership_accepted']:
            bad=copy.deepcopy(r);bad[field]=True
            with self.assertRaisesRegex(ValueError,'cleared later-version/guilt/population/privacy/current-law/meaning gates'):validate_4922_definition_context(a,u,s,bad)
        for old,new in [('ACT OF CONGRESS','any law anywhere'),('EXCLUDES the specified military tribunals','includes all military tribunals'),('MISDEMEANOR','felony-only'),('ATTEMPT, SOLICITATION OR CONSPIRACY','completed offenses only'),('DANGEROUS CRIME is not synonymous','DANGEROUS CRIME is interchangeable'),('ALLEGED to be delinquent, NEGLECTED, or IN NEED OF SUPERVISION','convicted of a crime'),('UNDER18 WITH specified16-or-older exclusions','all persons under18'),('UNDER21 extension for specified earlier-age acts','all persons under21'),('TIME THE PERSON COMMITTED A CRIME','time of conviction'),('not replaced by16-2301child','replaced by every FamilyCourt child')]:
            bad=copy.deepcopy(r);bad['new_rationale']=bad['new_rationale'].replace(old,new);aa=copy.deepcopy(a);aa['rationale']=bad['new_rationale'];uu=copy.deepcopy(u);uu.update(reason=aa['rationale'],rationale=aa['rationale']);uu['review_progress']['shared_review_record_sha256']=digest(aa)
            with self.assertRaisesRegex(ValueError,'population boundary lost'):validate_4922_definition_context(aa,uu,s,bad)
        bad=copy.deepcopy(s);bad['dc-council:code-23-1331-20250916']['text_version']='Later November operative version'
        with self.assertRaisesRegex(ValueError,'not exact pre-vote unit'):validate_4922_definition_context(a,u,bad,r)
        bad=copy.deepcopy(r);bad['existing_age_basis_witness']['quote']='at conviction'
        with self.assertRaisesRegex(ValueError,'age-at-act source witness differs'):validate_4922_definition_context(a,u,s,bad)
        bad=copy.deepcopy(a);bad['claim_source_map']=bad['claim_source_map'][1:]
        with self.assertRaisesRegex(ValueError,'changed prior claims/evidence flags'):validate_4922_definition_context(bad,u,s,r)

    def test_hr3638_definitions_keep_alternative_material_entity_utility_and_ERO_scopes_distinct(self):
        from scripts.validate_infrastructure_discovery_delta import validate_3638_definition_context
        p=folder(126);r=read(p/'hr3638_dated_named_definitions_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s={x['source_id']:x for x in read(p/'sources.json')['sources']};validate_3638_definition_context(a,u,s,r);self.assertTrue(validate(126)['generated_replay'])
        for field in ['whole_Acts_reviewed','printed_reference_corrected','reference_equivalence_certified','current_designation_lists_reviewed','actual_entity_or_person_classified','covered_country_list_imported','reliability_limits_narrow_whole_bill','current_law_certified','whole_version_binding_cleared','new_meaning_authored','membership_accepted']:
            bad=copy.deepcopy(r);bad[field]=True
            with self.assertRaisesRegex(ValueError,'cleared Acts/reference/classification/list/whole-bill/current-law/meaning gates'):validate_3638_definition_context(a,u,s,bad)
        for old,new in [('BOTH high supply-chain disruption risk AND an essential function','either risk or function'),('Secretary of the INTERIOR','Secretary of ENERGY alone'),('OR a critical mineral','AND a critical mineral'),('not silently applied to every item in the other critical-material route','automatically applied to every material'),('conviction clause is not allegation ALONE','allegation alone is sufficient'),('no rewrite to4872or import','automatic4872country-list substitution'),('person OR Federal/Stateagency that SELLS electric energy','only investor-owned producers'),('Commission-CERTIFIED under(c)','any self-described reliability group'),('SUBJECT TO COMMISSION REVIEW','free of Commission review'),('does NOT exclude the bill','automatically excludes the bill'),('that STANDARD definition','the whole bill prohibition'),('printed42US824o(a)reference remains UNCORRECTED','printed citation automatically repaired')]:
            bad=copy.deepcopy(r);bad['new_rationale']=bad['new_rationale'].replace(old,new);aa=copy.deepcopy(a);aa['rationale']=bad['new_rationale'];uu=copy.deepcopy(u);uu.update(reason=aa['rationale'],rationale=aa['rationale']);uu['review_progress']['shared_review_record_sha256']=digest(aa)
            with self.assertRaisesRegex(ValueError,'scope boundary lost'):validate_3638_definition_context(aa,uu,s,bad)
        bad=copy.deepcopy(r);bad['printed_bill_reference_witness']['quote']=bad['printed_bill_reference_witness']['quote'].replace('42 U.S.C.','16 U.S.C.')
        with self.assertRaisesRegex(ValueError,'Code-title reference witness changed'):validate_3638_definition_context(a,u,s,bad)
        bad=copy.deepcopy(a);bad['claim_source_map']=bad['claim_source_map'][1:]
        with self.assertRaisesRegex(ValueError,'changed prior source claims/evidence flags'):validate_3638_definition_context(bad,u,s,r)

    def test_partA7_full_own_body_keeps_condemnation_license_safety_and_State_scopes_qualified(self):
        from scripts.validate_infrastructure_discovery_delta import validate_partA7_complete_own_body
        p=folder(127);r=read(p/'partA7_complete_retained_own_body_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s=next(x for x in read(p/'sources.json')['sources'] if x['source_id']==r['source_id']);validate_partA7_complete_own_body(a,u,s,r);self.assertTrue(validate(127)['generated_replay'])
        for field in ['whole_record_source_read','adjacent_PartA6_or_A8_imported','referenced_laws_fully_reviewed','actual_military_need_certified','actual_title_or_compensation_decided','license_issued_or_operation_certified','State_or_Federal_permits_globally_cleared','Clerk_agreement_implies_enactment','current_law_certified','whole_version_binding_cleared','new_meaning_authored','membership_accepted']:
            bad=copy.deepcopy(r);bad[field]=True
            with self.assertRaisesRegex(ValueError,'cleared adjacent/law/actual-rights/enactment/version/meaning gates'):validate_partA7_complete_own_body(a,u,s,bad)
        for old,new in [('Condemnation MAY','Condemnation must'),('SEVEN DAYS AFTER commencement','seven days before enactment'),('BOTH filing a declaration of taking AND depositing estimated just compensation','House agreement alone'),('IF THE PARTIES ELECT','unilaterally by the operator'),('ALTERNATIVE exceptions','cumulative prerequisites'),('IMMINENT HAZARD','any alleged violation'),('REASONABLE PERIOD','no cure opportunity'),('FOR THAT TRANSFER PARAGRAPH','for all safety laws'),('HALT OR SUBSTANTIALLY DELAY','any State or local requirement'),('BROADER CALIFORNIA','only the narrow continuity test'),('UNITED STATES IS NOT A PARTY','any proceeding including Federal courts'),('Reimbursement MAY','Reimbursement SHALL')]:
            bad=copy.deepcopy(r);bad['new_rationale']=bad['new_rationale'].replace(old,new);aa=copy.deepcopy(a);aa['rationale']=bad['new_rationale'];uu=copy.deepcopy(u);uu.update(reason=aa['rationale'],rationale=aa['rationale']);uu['review_progress']['shared_review_record_sha256']=digest(aa)
            with self.assertRaisesRegex(ValueError,'actual-outcome boundary lost'):validate_partA7_complete_own_body(aa,uu,s,bad)
        bad=copy.deepcopy(r);bad['appended_full_claim']['passage']=s['text']
        with self.assertRaisesRegex(ValueError,'not exact own unit'):validate_partA7_complete_own_body(a,u,s,bad)
        bad=copy.deepcopy(a);bad['claim_source_map'][0]['passage']='changed earlier bookend'
        with self.assertRaisesRegex(ValueError,'changed source references/passages/evidence flags'):validate_partA7_complete_own_body(bad,u,s,r)
        bad=copy.deepcopy(r);bad['topics'].pop(6)
        with self.assertRaisesRegex(ValueError,'omitted an operative section'):validate_partA7_complete_own_body(a,u,s,bad)

    def test_partA6_full_own_body_preserves_certification_review_clocks_literal_discretion_and_savings(self):
        from scripts.validate_infrastructure_discovery_delta import validate_partA6_complete_own_body
        p=folder(128);r=read(p/'partA6_complete_retained_own_body_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s=next(x for x in read(p/'sources.json')['sources'] if x['source_id']==r['source_id']);validate_partA6_complete_own_body(a,u,s,r);self.assertTrue(validate(128)['generated_replay'])
        for field in ['whole_record_source_read','adjacent_PartA7_or_A8_imported','referenced_laws_fully_reviewed','actual_military_need_certified','actual_certification_or_court_outcome_decided','permit_or_Tribal_rights_globally_cleared','conclusive_evidence_and_review_interactions_resolved','termination_clocks_reconciled','lacks_discretion_rewritten','Clerk_failure_implies_enactment','current_law_certified','whole_version_binding_cleared','new_meaning_authored','membership_accepted']:
            bad=copy.deepcopy(r);bad[field]=True
            with self.assertRaisesRegex(ValueError,'cleared adjacent/law/certification/judicial/rights/interaction/version/meaning gates'):validate_partA6_complete_own_body(a,u,s,bad)
        for old,new in [('DISCRETIONARY MAY','automatic approval'),('REBUTTABLE','irrebuttable'),('60dayclock AFTER SUBMISSION OF TERMINATION MATERIALS','60days after effective termination'),('GRANT OR DENIAL within15days of a COMPLETE request','automatic grant within15days of any request'),('ENDEAVOR','mandatory result'),('ALL THREE clear-and-convincing elements','any one ordinary-evidence element'),('REMOVABLE','automatically removed'),('UPON REMOVAL','upon certification'),('60days after service of the first relevant pleading','90days after any pleading'),('90dayAFTER-ENACTMENT window','60days after certification'),('SUBSTANTIALLY PREVAILS','merely files suit'),('LACKS DISCRETION TO WAIVE OR DECLINE','HAS discretion to waive or decline'),('more stringent than OR additional to a Federally COMPELLED requirement','every State permit condition'),('EXPRESS(l)(8)(A)(ii)(III)EXCEPTION','no exception at all'),('NONCERTIFIED infrastructure','every energy facility'),('NO FEDERAL PROPERTY INTEREST','Federal easement acquired'),('AGintervention MAY','AGintervention must')]:
            bad=copy.deepcopy(r);bad['new_rationale']=bad['new_rationale'].replace(old,new);aa=copy.deepcopy(a);aa['rationale']=bad['new_rationale'];uu=copy.deepcopy(u);uu.update(reason=aa['rationale'],rationale=aa['rationale']);uu['review_progress']['shared_review_record_sha256']=digest(aa)
            with self.assertRaisesRegex(ValueError,'State-floor/savings boundary lost'):validate_partA6_complete_own_body(aa,uu,s,bad)
        bad=copy.deepcopy(r);bad['appended_full_claim']['passage']=s['text'][26180:39188]
        with self.assertRaisesRegex(ValueError,'not exact own unit'):validate_partA6_complete_own_body(a,u,s,bad)
        bad=copy.deepcopy(a);bad['claim_source_map'][1]['passage']='altered old bookend'
        with self.assertRaisesRegex(ValueError,'changed source references/passages/evidence flags'):validate_partA6_complete_own_body(bad,u,s,r)
        bad=copy.deepcopy(r);bad['topics'].pop(12)
        with self.assertRaisesRegex(ValueError,'omitted an operative section'):validate_partA6_complete_own_body(a,u,s,bad)

    def test_partA7_precision_requires_California_payee_and_separate_preemption_verbs(self):
        from scripts.validate_infrastructure_discovery_delta import validate_partA7_compensation_preemption_precision
        p=folder(128);r=read(p/'partA7_compensation_preemption_precision_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s=next(x for x in read(p/'sources.json')['sources'] if x['source_id']==r['source_id']);validate_partA7_compensation_preemption_precision(a,u,s,r)
        bad=copy.deepcopy(a);bad['rationale']=bad['rationale'].replace('Compensation payable to California or its agencies','All compensation including private parties')
        with self.assertRaisesRegex(ValueError,'omitted California/agencies or broadened operator verbs'):validate_partA7_compensation_preemption_precision(bad,u,s,r)
        bad=copy.deepcopy(a);bad['rationale']=bad['rationale'].replace('OR whose PURPOSE OR EFFECT is PREVENTING operator use','OR whose PURPOSE OR EFFECT is PREVENTING, CONDITIONING OR DELAYING operator use')
        with self.assertRaisesRegex(ValueError,'omitted California/agencies or broadened operator verbs'):validate_partA7_compensation_preemption_precision(bad,u,s,r)
        for i in [0,1]:
            bad=copy.deepcopy(r);bad['rationale_replacements'][i]['new']=bad['rationale_replacements'][i]['old']
            with self.assertRaisesRegex(ValueError,'lost California-payee/separate-verb scope'):validate_partA7_compensation_preemption_precision(a,u,s,bad)
        for field in ['private_compensation_scope_adjudicated','actual_preemption_outcome_decided','current_law_certified','membership_accepted']:
            bad=copy.deepcopy(r);bad[field]=True
            with self.assertRaisesRegex(ValueError,'adjudicated outcomes'):validate_partA7_compensation_preemption_precision(a,u,s,bad)
        bad=copy.deepcopy(r);bad['source_witnesses'][0]['source_start']=30664
        with self.assertRaisesRegex(ValueError,'source witnesses differ'):validate_partA7_compensation_preemption_precision(a,u,s,bad)

    def test_hr4371_full_EH_keeps_age_sponsor_disclosure_and_conditional_implementation_scopes(self):
        from scripts.validate_infrastructure_discovery_delta import validate_4371_complete_retained_body
        p=folder(129);r=read(p/'hr4371_complete_retained_body_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);s=next(x for x in read(p/'sources.json')['sources'] if x['source_id']==r['source_id'])
        validate_4371_complete_retained_body(a,u,s,r);self.assertTrue(validate(129)['generated_replay'])
        for field in ['referenced_laws_fully_reviewed','committee_floor_version_binding_cleared','current_law_certified','actual_child_or_sponsor_risk_determined','information_disclosure_is_public_posting','APA_or_PRA_unconditionally_waived','House_passage_implies_enactment','new_meaning_authored','membership_accepted']:
            bad=copy.deepcopy(r);bad[field]=True
            with self.assertRaisesRegex(ValueError,'cleared law/version/individual-risk/publication/implementation/meaning gates'):validate_4371_complete_retained_body(a,u,s,bad)
        for old,new in [('BY REASON OF IMMIGRATION STATUS','for any reason'),('ARRESTED, CHARGED AND CONVICTED','convicted'),('children12OR OLDER','children of all ages'),('FLIGHT RISK OR DANGER','flight risk AND danger'),('IF ORDERED REMOVED','regardless of removal order'),('FOR CONDUCT IN CONNECTION WITH GANG AFFILIATION OR ACTIVITY','for any conduct'),('NEITHER A US CITIZEN NOR A LAWFUL PERMANENT RESIDENT','not a US citizen'),('OR A HOUSEHOLD RESIDENT','only the sponsor'),('MORE THAN ONE YEAR','at least one year'),('HHS SHALL PROVIDE DHS','HHS shall publicly post'),('EACH ADULT HOUSEHOLD RESIDENT','only the sponsor'),('SSN OR ITIN','SSN only'),('AT A MINIMUM','optional'),('public-records background check AND fingerprint-based national criminal-history check','public-records OR fingerprint checks'),('IF THEY DETERMINE compliance WOULD IMPEDE IMMEDIATE IMPLEMENTATION','unconditionally'),('AND ALL RELEASE REDETERMINATIONS','new determinations only'),('printed section642(g)(2)','corrected section462(g)(2)')]:
            bad=copy.deepcopy(r);bad['new_rationale']=bad['new_rationale'].replace(old,new);aa=copy.deepcopy(a);aa['rationale']=bad['new_rationale'];uu=copy.deepcopy(u);uu.update(reason=aa['rationale'],rationale=aa['rationale']);uu['review_progress']['shared_review_record_sha256']=digest(aa)
            with self.assertRaisesRegex(ValueError,'conditional-implementation/applicability boundary lost'):validate_4371_complete_retained_body(aa,uu,s,bad)
        bad=copy.deepcopy(r);bad['appended_full_claim']['passage']=s['text'][:3200]+s['text'][-900:]
        with self.assertRaisesRegex(ValueError,'not exact complete EH'):validate_4371_complete_retained_body(a,u,s,bad)
        bad=copy.deepcopy(a);bad['claim_source_map'][0]['passage']='altered earlier passage'
        with self.assertRaisesRegex(ValueError,'changed source references/passages/evidence flags'):validate_4371_complete_retained_body(bad,u,s,r)
        bad=copy.deepcopy(r);bad['topics'].pop(5)
        with self.assertRaisesRegex(ValueError,'omitted an operative section'):validate_4371_complete_retained_body(a,u,s,bad)
        bad=copy.deepcopy(u);bad['exact_action_source_binding']['complete']=True
        with self.assertRaisesRegex(ValueError,'changed unresolved version or universe gates'):validate_4371_complete_retained_body(a,bad,s,r)

    def test_hr4371_dated_placement_context_keeps_old_rules_selected_scope_and_opposite_dataflows(self):
        from scripts.validate_infrastructure_discovery_delta import validate_4371_placement_context
        p=folder(130);r=read(p/'hr4371_dated_placement_context_receipt.json');a=next(x for x in read(p/'membership_review.json')['records'] if x['action_id']==r['action_id']);u=next(x for x in read(p/'universe_proposal.json')['candidate_dispositions'] if x['action_id']==r['action_id']);ss={x['source_id']:x for x in read(p/'sources.json')['sources']}
        validate_4371_placement_context(a,u,ss,r);self.assertTrue(validate(130)['generated_replay'])
        for field in ['whole_1232_read','all_editorial_notes_reviewed','current_law_certified','committee_floor_version_binding_cleared','all_review_or_alternatives_abolished','old_bond_or_642_reference_repaired','actual_child_or_sponsor_risk_determined','new_software_or_construction_mandated','membership_accepted','new_meaning_authored']:
            bad=copy.deepcopy(r);bad[field]=True
            with self.assertRaisesRegex(ValueError,'cleared selected-unit/law/reference/outcome/technology/meaning gates'):validate_4371_placement_context(a,u,ss,bad)
        for old,new in [('ONLY(c)(1)–(6)(F)','whole1232'),('EXISTING CONTEXT','new bill mandate'),('ALREADY PROHIBITS OWN-RECOGNIZANCE RELEASE','first introduced the prohibition'),('ALL THREE branches','any one branch'),('AVAILABLE TO PROVIDE CARE AND PHYSICAL CUSTODY','physically present anywhere'),('REPLACES ALL OF(c)(2)','replaces only the first sentence'),('does not establish that ALL REVIEW OR ALL ALTERNATIVES UNDER OTHER LAW DISAPPEAR','all review and alternatives disappear'),('does not mandate a home study for every child','mandates a home study for every child'),('DHS TO PROVIDE HHS','HHS TO PROVIDE DHS'),('WITHIN TWO WEEKS AFTER HHS REQUEST','before placement'),('HHS TO PROVIDE DHS sponsor/adult-household information BEFORE PLACEMENT','DHS TO PROVIDE HHS before placement'),('do not transfer the two-weekclock to(D)','apply the two-weekclock to(D)'),('AT LEAST25percent OF FEDERAL FUNDS','25percent of the entire budget')]:
            bad=copy.deepcopy(r);bad['new_rationale']=bad['new_rationale'].replace(old,new);aa=copy.deepcopy(a);aa['rationale']=bad['new_rationale'];uu=copy.deepcopy(u);uu.update(reason=aa['rationale'],rationale=aa['rationale']);uu['review_progress']['shared_review_record_sha256']=digest(aa)
            with self.assertRaisesRegex(ValueError,'retained-safeguard boundary lost'):validate_4371_placement_context(aa,uu,ss,bad)
        bad=copy.deepcopy(r);bad['source_contexts'][1]['appended_claim']['locator']='Entire1232andcurrentlaw'
        with self.assertRaisesRegex(ValueError,'claim broadened source scope'):validate_4371_placement_context(a,u,ss,bad)
        bad=copy.deepcopy(a);bad['claim_source_map'][2]['passage']='altered complete EH'
        with self.assertRaisesRegex(ValueError,'changed existing EH/source/flags/meaning state'):validate_4371_placement_context(bad,u,ss,r)
        bad=copy.deepcopy(u);bad['exact_action_source_binding']['complete']=True
        with self.assertRaisesRegex(ValueError,'cleared version or changed universe gates'):validate_4371_placement_context(a,bad,ss,r)

if __name__=='__main__':unittest.main()
