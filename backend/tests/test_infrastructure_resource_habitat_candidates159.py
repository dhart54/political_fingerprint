import copy
import unittest

from backend.app.semantic_ir.shared_corpus import (
    digest, sealed_digest, validate_member_projection, validate_shared_issue_mapping,
    SharedCorpusValidationError,
)
from scripts.validate_infrastructure_resource_habitat_candidates159 import (
    ROOT, P, inputs, replay, validate, validate_units, validate_captures,
    validate_manifest, validate_preservation, RAW_LABELS, STATUSES,
)


class ResourceHabitat159Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=inputs()

    def changed(self,key):
        data=dict(self.data);data[key]=copy.deepcopy(data[key]);return data

    def units(self,authoring=None,pool=None):
        return validate_units(authoring or self.data['authoring'],
            pool or {x['source_id']:x for x in self.data['sources']['sources']},self.data['preflight'])

    def operators(self,index,tokens):
        for token in tokens:
            a=copy.deepcopy(self.data['authoring']);self.assertIn(token,a['actions'][index]['meaning'])
            a['actions'][index]['meaning']=a['actions'][index]['meaning'].replace(token,'changed operator')
            with self.subTest(token=token),self.assertRaises(ValueError):self.units(authoring=a)

    def test_two_exact_amendments_three_whole_choices_and_five_held_episodes(self):
        result=validate(self.data)
        self.assertEqual(tuple(result[k] for k in ['cores','official_observations','held_episodes','propositions','sources']),(5,10,5,0,26))
        self.assertIs(result['canonical_changes'],False);self.assertEqual(validate_preservation(),708)
        self.assertGreaterEqual(validate_manifest(),20)
        for i,row in enumerate(self.data['products']['shared_action_core']['actions']):
            self.assertEqual(row['package_component_boundary']['boundary_type'],'exact_amendment' if i<2 else 'whole_measure')
            self.assertIs(row['package_component_boundary']['parent_package_meaning_projected'],False)

    def test_perry_whole_rule_funds_threshold_withdrawal_and_final_result_are_material(self):
        self.operators(0,['ONLY FUNDS MADE AVAILABLE BY THIS ACT','WHOLE named DRBC',
            'COMBINED TOTAL OF300000OR MORE GALLONS','WITHDRAWN','Recorded195–235REJECTION','asterisks omitting unchanged'])

    def test_biggs_whole_operation_personnel_plan_and_report_limits_are_material(self):
        self.operators(1,['OTHER qualifying','REGARDLESS OF AN INTEGRATED NATURAL RESOURCES PLAN',
            'BUT NOT THE PURPOSE OF','ANY TIER','overseas Defense support',
            'Initial floor119–225, resumed119–255','Recorded200–228REJECTION','not a technology-only'])

    def test_wildlife_review_conditional_reservation_share_and_recreation_caps_are_distinct(self):
        self.operators(2,['180-DAY','CONDITIONALLY AUTHORIZE','SET ASIDE','JUNE1OF THE IMMEDIATELY FOLLOWING YEAR',
            'NOT FINAL APPROVAL OR IMMEDIATE PAYMENT','NOT EXCEEDING75PERCENT OF ESTIMATED PROGRAM COST',
            'SEPARATE10PERCENT','EXCLUDING LAW ENFORCEMENT','not a new100percent share'])

    def test_mill_site_approval_single_site_patent_scope_and_available_funds_are_material(self):
        self.operators(3,['REASONABLY NECESSARY','USE/OCCUPY LAND UNDER AN APPROVED PLAN','SINGLE SITE',
            'NO MINERAL RIGHTS','UNDER THIS SECTION','MAY expend AVAILABLE FUND AMOUNTS WITHOUT FURTHER APPROPRIATIONS ONLY',
            'not new guaranteed revenue','Clerical28fchanges'])

    def test_urban_grants_optional_administration_entities_geography_and_authorization_are_distinct(self):
        self.operators(4,['VOLUNTARY','COMPETITIVE GRANT PROGRAM','COVERED entities','ELIGIBLE GRANT entities',
            'MAY agree','SHALL NOT APPLY','TO THE EXTENT PRACTICABLE','ALTERNATIVE urban-area branches',
            '50000PLUS CENSUS DESIGNATION','AUTHORIZES200000DOLLARS FOR EACH FY2027–2033'])

    def test_known_report_discrepancy_final_rejection_and_printed_baseline_are_not_repaired(self):
        for sid,old,new in [('congressional-record:3838-amend29-roll259-choice158','119–225','119–255'),
                           ('congressional-record:4553-amend23-roll227-choice150','rejected','agreed to'),
                           ('govinfo:resource159:30usc1245','shall be for available','shall be available')]:
            pool={x['source_id']:copy.deepcopy(x) for x in self.data['sources']['sources']};self.assertIn(old,pool[sid]['text']);pool[sid]['text']=pool[sid]['text'].replace(old,new)
            with self.subTest(source=sid),self.assertRaises(ValueError):self.units(pool=pool)

    def test_exact_stage_question_and_source_cannot_cross_between_choices(self):
        a=copy.deepcopy(self.data['authoring']);a['actions'][0]['stage']='final_passage'
        with self.assertRaises(ValueError):self.units(authoring=a)
        a=copy.deepcopy(self.data['authoring']);a['actions'][2]['source_id']=a['actions'][4]['source_id']
        with self.assertRaises(ValueError):self.units(authoring=a)
        pool={x['source_id']:copy.deepcopy(x) for x in self.data['sources']['sources']};pool['clerk:119:2:297']['metadata']['vote-question']='On Passage'
        with self.assertRaises(ValueError):self.units(pool=pool)

    def test_raw_official_labels_and_different_member_directions_bind_to_shared_truth(self):
        pool={x['source_id']:x for x in self.data['sources']['sources']};a=self.data['authoring']
        for member,expected in RAW_LABELS.items():
            self.assertEqual([pool['clerk:'+x['action_id'].split(':',1)[1]]['member_records'][member]['official_label'] for x in a['actions']],expected)
        core={x['action_id']:x for x in self.data['products']['shared_action_core']['actions']}
        for member in self.data['products']['member_projections']:
            self.assertEqual([x['official_status'] for x in member['actions']],STATUSES[member['member_id']])
            for row in member['actions']:self.assertEqual(row['action_core_sha256'],core[row['action_id']]['action_core_sha256'])

    def test_capture_budget_redirect_and_closed_locator_cannot_be_reclassified(self):
        for kind in ['redirect','budget','closed','raw_hash']:
            capture=copy.deepcopy(self.data['capture'])
            if kind=='redirect':capture['limits']['redirects_allowed']=True
            elif kind=='budget':capture['limits']['response_bytes']*=2
            elif kind=='closed':capture['attempts'][3]['result']='captured'
            else:capture['attempts'][0]['sha256']='0'*64
            with self.subTest(kind=kind),self.assertRaises((ValueError,KeyError)):
                validate_captures(capture,self.data['bindings'],self.data['sources'])

    def test_new_operative_extent_cannot_include_unrelated_notes_or_silent_source_repairs(self):
        for kind in ['range','notes','type']:
            bindings=copy.deepcopy(self.data['bindings']);sources=copy.deepcopy(self.data['sources'])
            if kind=='range':bindings['sources'][0]['governed_end']+=1
            else:
                source=next(x for x in sources['sources'] if x['source_id']=='govinfo:resource159:30usc1245')
                if kind=='notes':source['text']+=' Good Samaritan statutory note substituted.'
                else:source['source_type']='official_rule_text'
                source['governed_bytes_sha256']=sealed_digest(source,'governed_bytes_sha256')
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate_captures(self.data['capture'],bindings,sources)

    def test_claims_must_remain_in_their_own_declared_sources(self):
        for field in ['source_id','passage']:
            a=copy.deepcopy(self.data['authoring']);a['actions'][0]['claim_source_map'][0][field]='unsupported scope or source'
            with self.subTest(field=field),self.assertRaises((ValueError,KeyError)):self.units(authoring=a)

    def test_resealed_retained_source_is_not_accepted_as_original(self):
        data=self.changed('sources');source=next(x for x in data['sources']['sources'] if x['source_id']=='govinfo:hr1676eh');source['text']=source['text'].replace('shall','may');source['governed_bytes_sha256']=sealed_digest(source,'governed_bytes_sha256')
        with self.assertRaises(ValueError):validate(data)
        with self.assertRaises(ValueError):replay(self.data['authoring'],data['sources'])

    def test_all_authority_flags_remain_literal_false(self):
        for key in ['accepted','canonical_application','publication','production']:
            for value in [True,0]:
                data=self.changed('bundle');data['bundle'][key]=value;data['bundle']['bundle_sha256']=sealed_digest(data['bundle'],'bundle_sha256')
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):validate(data)

    def test_mapping_cannot_accept_case_eligibility(self):
        products=self.data['products'];mapping=copy.deepcopy(products['shared_issue_mapping']);row=mapping['action_mappings'][0];row['eligibility']['decision']='accepted';row['mapping_sha256']=sealed_digest(row,'mapping_sha256');mapping['mapping_sha256']=sealed_digest(mapping,'mapping_sha256')
        with self.assertRaises(SharedCorpusValidationError):validate_shared_issue_mapping(ROOT,mapping,products['shared_action_core'])

    def test_shared_correction_rejects_both_stale_member_projections(self):
        products=self.data['products'];after=copy.deepcopy(products['shared_action_core']);row=after['actions'][0];row['candidate_shared_limitations'].append('CONTROLLED source qualification; no acceptance.');row['action_core_sha256']=sealed_digest(row,'action_core_sha256');after['corpus_sha256']=digest(after['actions'])
        for member in products['member_projections']:
            with self.subTest(member=member['member_id']),self.assertRaises(SharedCorpusValidationError):validate_member_projection(ROOT,member,after)

    def test_unused_source_changes_no_product_and_authored_meaning_is_member_neutral(self):
        sources=copy.deepcopy(self.data['sources']);extra={'source_id':'synthetic:unused159','text':'Controlled unused source, not evidence.'};extra['governed_bytes_sha256']=digest(extra);sources['sources'].append(extra);self.assertEqual(digest(replay(self.data['authoring'],sources)),digest(self.data['products']))
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
