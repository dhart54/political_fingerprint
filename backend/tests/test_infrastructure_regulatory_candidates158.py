import copy
import unittest

from backend.app.semantic_ir.shared_corpus import (
    digest, sealed_digest, validate_member_projection, validate_shared_issue_mapping,
    SharedCorpusValidationError,
)
from scripts.validate_infrastructure_regulatory_candidates158 import (
    ROOT, P, inputs, replay, validate, validate_units, validate_captures,
    validate_manifest, validate_preservation,
)


class RegulatoryChoices158Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = inputs()

    def changed(self, key):
        data = dict(self.data)
        data[key] = copy.deepcopy(data[key])
        return data

    def units(self, authoring=None, pool=None, preflight=None):
        return validate_units(authoring or self.data['authoring'],
                              pool or {x['source_id']:x for x in self.data['sources']['sources']},
                              preflight or self.data['preflight'])

    def test_five_exact_passage_choices_replay_in_five_held_episodes(self):
        result = validate(self.data)
        self.assertEqual(tuple(result[k] for k in ['cores','official_observations','held_episodes','propositions','sources']),
                         (5,10,5,0,14))
        self.assertIs(result['canonical_changes'],False)
        self.assertEqual(validate_preservation(),708)
        self.assertGreaterEqual(validate_manifest(),20)
        for row in self.data['products']['shared_action_core']['actions']:
            self.assertEqual(row['package_component_boundary']['boundary_type'],'whole_measure')
            self.assertIs(row['package_component_boundary']['parent_package_meaning_projected'],False)

    def test_nonbinding_sense_and_qualified_presidential_bar_cannot_collapse(self):
        for token in ['NONBINDING','PRESIDENT MAY NOT DECLARE A MORATORIUM',
                      'UNLESS authorized by an Act of Congress','subsection(b)prints no such land limitation']:
            a=copy.deepcopy(self.data['authoring']);a['actions'][0]['meaning']=a['actions'][0]['meaning'].replace(token,'changed')
            with self.subTest(token=token),self.assertRaises(ValueError):self.units(authoring=a)

    def test_methane_reporting_threshold_intensity_exemptions_and_delay_remain_distinct(self):
        for token in ['MORE THAN25000metrictonsCO2e','METHANE INTENSITY THRESHOLDS','36months',
                      'next business day','not unrestricted cross-owner','omitted graphical equations are unintegrated']:
            a=copy.deepcopy(self.data['authoring']);a['actions'][1]['meaning']=a['actions'][1]['meaning'].replace(token,'changed')
            with self.subTest(token=token),self.assertRaises(ValueError):self.units(authoring=a)

    def test_digital_interface_capability_exclusions_and_applicability_are_material(self):
        for token in ['GROSS PROCEEDS','POSITION TO KNOW','actual fee collection is not required',
                      'VALIDATION-ONLY','only for sales using those services','ON OR AFTER JANUARY1,2027','February28,2025']:
            a=copy.deepcopy(self.data['authoring']);a['actions'][2]['compact_description']=a['actions'][2]['compact_description'].replace(token,'changed')
            with self.subTest(token=token),self.assertRaises(ValueError):self.units(authoring=a)

    def test_vehicle_road_area_elevation_clocks_and_discretion_remain_specific(self):
        for token in ['VEHICLE/ROAD/AREA-SPECIFIC','BELOW FOR SEVEN CONSECUTIVE DAYS',
                      'ABOVE FOR SEVEN CONSECUTIVE DAYS','within14days','superintendent discretion',
                      'except LoneRockBeach','seven named unpaved','unchanged starred text']:
            a=copy.deepcopy(self.data['authoring']);a['actions'][3]['meaning']=a['actions'][3]['meaning'].replace(token,'changed')
            with self.subTest(token=token),self.assertRaises(ValueError):self.units(authoring=a)

    def test_species_dps_listing_cannot_become_habitat_designation_or_project_exemption(self):
        for token in ['THAT DPS','ENDANGERED(E)','does NOT ITSELF DESIGNATE CRITICAL HABITAT',
                      'attributed to the agency','written not-likely-adversely-affect concurrence exception',
                      'not a universal project exemption']:
            a=copy.deepcopy(self.data['authoring']);a['actions'][4]['meaning']=a['actions'][4]['meaning'].replace(token,'changed')
            with self.subTest(token=token),self.assertRaises(ValueError):self.units(authoring=a)

    def test_exact_rule_context_and_official_question_cannot_cross_choices(self):
        a=copy.deepcopy(self.data['authoring']);a['actions'][1]['additional_source_ids']=a['actions'][2]['additional_source_ids']
        with self.assertRaises(ValueError):self.units(authoring=a)
        for sid,key,new in [('clerk:119:1:52','vote-question','On Motion to Recommit'),
                            ('clerk:119:1:71','rollcall-num','72')]:
            pool={x['source_id']:copy.deepcopy(x) for x in self.data['sources']['sources']};pool[sid]['metadata'][key]=new
            with self.subTest(key=key),self.assertRaises(ValueError):self.units(pool=pool)

    def test_raw_official_statuses_and_both_projections_are_bound_to_shared_truth(self):
        self.units()
        pool={x['source_id']:copy.deepcopy(x) for x in self.data['sources']['sources']}
        pool['clerk:119:1:35']['member_records']['F000477']['official_label']='Not Voting'
        with self.assertRaises(ValueError):self.units(pool=pool)
        core={x['action_id']:x for x in self.data['products']['shared_action_core']['actions']}
        for member in self.data['products']['member_projections']:
            for row in member['actions']:
                self.assertEqual(row['action_core_sha256'],core[row['action_id']]['action_core_sha256'])

    def test_capture_budget_identity_binding_and_redirect_drift_fail_closed(self):
        for kind in ['redirect','budget','wrong_url','raw_hash','binding']:
            capture=copy.deepcopy(self.data['capture']);bindings=copy.deepcopy(self.data['bindings'])
            if kind=='redirect':capture['limits']['redirects_allowed']=True
            elif kind=='budget':capture['limits']['response_bytes']*=2
            elif kind=='wrong_url':capture['attempts'][0]['final_url']='https://example.org/other'
            elif kind=='raw_hash':capture['attempts'][0]['sha256']='0'*64
            else:bindings['sources'][0]['source_id']=bindings['sources'][1]['source_id']
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                validate_captures(capture,bindings,self.data['sources'])

    def test_claim_cannot_escape_own_source_or_invent_an_omitted_formula(self):
        for field in ['source_id','passage']:
            a=copy.deepcopy(self.data['authoring']);a['actions'][1]['claim_source_map'][1][field]='unsupported formula or source'
            with self.subTest(field=field),self.assertRaises((ValueError,KeyError)):self.units(authoring=a)
        s=copy.deepcopy(self.data['sources']);row=next(x for x in s['sources'] if x['source_id']=='govinfo:regulatory158:2024-26643')
        row['text']=row['text'].replace('[GRAPHIC]','[RECONSTRUCTED FORMULA]');row['governed_bytes_sha256']=sealed_digest(row,'governed_bytes_sha256')
        with self.assertRaises(ValueError):validate_captures(self.data['capture'],self.data['bindings'],s)

    def test_resealed_retained_source_is_not_accepted_as_original(self):
        data=self.changed('sources');source=next(x for x in data['sources']['sources'] if x['source_id']=='govinfo:hr26eh')
        source['text']=source['text'].replace('unless','even if');source['governed_bytes_sha256']=sealed_digest(source,'governed_bytes_sha256')
        with self.assertRaises(ValueError):validate(data)
        with self.assertRaises(ValueError):replay(self.data['authoring'],data['sources'])

    def test_all_authority_flags_remain_literal_false(self):
        for key in ['accepted','canonical_application','publication','production']:
            for value in [True,0]:
                data=self.changed('bundle');data['bundle'][key]=value;data['bundle']['bundle_sha256']=sealed_digest(data['bundle'],'bundle_sha256')
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):validate(data)

    def test_mapping_cannot_accept_case_eligibility(self):
        products=self.data['products'];mapping=copy.deepcopy(products['shared_issue_mapping']);row=mapping['action_mappings'][0]
        row['eligibility']['decision']='accepted';row['mapping_sha256']=sealed_digest(row,'mapping_sha256');mapping['mapping_sha256']=sealed_digest(mapping,'mapping_sha256')
        with self.assertRaises(SharedCorpusValidationError):validate_shared_issue_mapping(ROOT,mapping,products['shared_action_core'])

    def test_shared_correction_rejects_both_stale_member_projections(self):
        products=self.data['products'];after=copy.deepcopy(products['shared_action_core']);row=after['actions'][0]
        row['candidate_shared_limitations'].append('CONTROLLED source qualification; no acceptance.');row['action_core_sha256']=sealed_digest(row,'action_core_sha256');after['corpus_sha256']=digest(after['actions'])
        for member in products['member_projections']:
            with self.subTest(member=member['member_id']),self.assertRaises(SharedCorpusValidationError):validate_member_projection(ROOT,member,after)

    def test_unused_source_changes_no_product_and_authored_meaning_is_member_neutral(self):
        s=copy.deepcopy(self.data['sources']);extra={'source_id':'synthetic:unused158','text':'Controlled unused source; not evidence.'};extra['governed_bytes_sha256']=digest(extra);s['sources'].append(extra)
        self.assertEqual(digest(replay(self.data['authoring'],s)),digest(self.data['products']))
        a=self.data['authoring'];text=str({k:a[k] for k in ['boundary','blocked_reason']})
        for row in a['actions']:text+=str({k:row[k] for k in ['meaning','compact_description','limitations','choice_meanings']})
        self.assertTrue('Foushee' not in text and 'Massie' not in text)

    def test_hold_proposition_observation_and_prior_identity_drift_fail_closed(self):
        for kind in ['hold','graph','member','prior']:
            key='authoring' if kind=='hold' else 'preflight' if kind=='prior' else 'products';data=self.changed(key)
            if kind=='hold':data[key]['blocked_episode_ids'].clear()
            elif kind=='graph':data[key]['compiled_ir']['members'][0]['proposition_graph']['propositions'].append({'invented':True})
            elif kind=='member':data[key]['member_projections'][0]['actions'][0]['official_status']='Yea'
            else:data[key]['prior_prepared_identities'][0]=data['authoring']['actions'][0]['action_id']
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate(data)
