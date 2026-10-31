import copy
import unittest

from backend.app.semantic_ir.shared_corpus import (
    digest,sealed_digest,validate_member_projection,validate_shared_issue_mapping,
    SharedCorpusValidationError,
)
from scripts.validate_infrastructure_foreign_disclosure_finance_candidates160 import (
    ROOT,P,inputs,replay,validate,validate_units,validate_captures,validate_preserved_parent_refs,
    validate_manifest,validate_preservation,RAW_LABELS,STATUSES,NEW_SOURCE,
)


class ForeignDisclosureFinance160Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=inputs()

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

    def test_three_rejected_children_two_whole_bills_and_three_held_episodes(self):
        result=validate(self.data)
        self.assertEqual(tuple(result[k] for k in ['cores','official_observations','held_episodes','propositions','sources']),(5,10,3,0,13))
        self.assertIs(result['canonical_changes'],False);self.assertEqual(validate_preservation(),715)
        self.assertGreaterEqual(validate_manifest(),18)
        for i,row in enumerate(self.data['products']['shared_action_core']['actions']):
            self.assertEqual(row['package_component_boundary']['boundary_type'],'exact_amendment' if 1<=i<=3 else 'whole_measure')
            self.assertIs(row['package_component_boundary']['parent_package_meaning_projected'],False)

    def test_tax_qualification_wage_conjunction_duration_reciprocity_and_agreement_clocks(self):
        self.operators(0,['TWO TITLES','QUALIFIED','NON-US-CITIZENS','OR regular international ship/aircraft crew',
            'BOTH payment by/on behalf','MORE THAN12MONTHS','MORE THAN30DAYS','TREASURY RECIPROCITY DETERMINATION',
            'AFTER that determination','PRE-NEGOTIATION','BEFORE entering','AFTER entering',
            'approval legislation AND implementing legislation','CODE-CONTROL'])

    def test_self_threshold_aggregation_old_definition_and_database_limits(self):
        self.operators(1,['RCP119-1PAGE2LINE5','ONE DOLLAR OR MORE',
            'ALONE OR AGGREGATED WITH THE SAME FOREIGN SOURCE WITHIN THE CALENDAR YEAR',
            'indeterminate-value alternative','NOT AUTOMATICALLY INCORPORATED',
            'does NOT CREATE A SEARCHABLE DATABASE','Recorded92–321REJECTION'])

    def test_country_alternatives_allegations_and_warrants_do_not_become_guilt(self):
        self.operators(2,['ALTERNATIVE COUNTRY CRITERIA','RCP119-1PAGE57LINE18','ALLEGED',
            'OUTSTANDING ICCARREST WARRANTS','NOT A GUILT DETERMINATION','rather than requiring both','Recorded3–410REJECTION'])

    def test_investment_actor_conduct_conjunctions_and_scope_do_not_collapse(self):
        self.operators(3,['117C(h)(1)(A)INVESTMENT OF CONCERN','NOT A WHOLESALE','SECRETARY OF STATE DETERMINATION',
            'CONSISTENTLY, KNOWINGLY, AND DIRECTLY',
            'state violence AND repression, war AND occupation, OR severe violations of international law AND human rights',
            'ALONE DOES NOT REPLACE THE DETERMINATION AND CONDUCT PREDICATES',
            'Recorded4–404REJECTION','aggregate Present is not either observed member'])

    def test_burma_voice_vote_recipients_disbursements_commitments_and_exception(self):
        self.operators(4,['DIRECT THE USIBRDEXECUTIVE DIRECTOR TO USE USVOICE AND VOTE',
            'BOTH DISBURSEMENTS AND NEW FINANCING COMMITMENTS TO THE GOVERNMENT OF BURMA',
            'UNLESS TREASURY DETERMINES CONTINUATION IS NOT IN THE NATIONAL INTEREST',
            'neither unilateral UScontrol','legislative attribution'])

    def test_own_failed_children_cannot_use_another_component_or_passed_parent(self):
        a=copy.deepcopy(self.data['authoring']);a['actions'][1]['claim_source_map'][0]['passage']=a['actions'][2]['claim_source_map'][0]['passage']
        with self.assertRaises(ValueError):self.units(authoring=a)
        pool={x['source_id']:copy.deepcopy(x) for x in self.data['sources']['sources']}
        sid='immigration:hr1048-package-recorded175';pool[sid]['text']=pool[sid]['text'].replace('rejected','agreed to')
        with self.assertRaises(ValueError):self.units(pool=pool)
        a=copy.deepcopy(self.data['authoring']);a['actions'][2]['stage']='final_passage'
        with self.assertRaises(ValueError):self.units(authoring=a)

    def test_source_predicates_keep_actor_and_allegation_attribution(self):
        sid='immigration:hr1048-package-initial175'
        for old,new in [('alleged violation','proven violation'),('Secretary of State','any person'),('consistently, knowingly','occasionally, unknowingly')]:
            pool={x['source_id']:copy.deepcopy(x) for x in self.data['sources']['sources']};self.assertIn(old,pool[sid]['text']);pool[sid]['text']=pool[sid]['text'].replace(old,new)
            with self.subTest(predicate=old),self.assertRaises(ValueError):self.units(pool=pool)

    def test_raw_labels_not_voting_and_chamber_present_remain_separate(self):
        pool={x['source_id']:x for x in self.data['sources']['sources']};a=self.data['authoring']
        for member,labels in RAW_LABELS.items():
            self.assertEqual([pool['clerk:'+x['action_id'].split(':',1)[1]]['member_records'][member]['official_label'] for x in a['actions']],labels)
        for member in self.data['products']['member_projections']:
            self.assertEqual([x['official_status'] for x in member['actions']],STATUSES[member['member_id']])
        for member in self.data['products']['compiled_ir']['members']:
            cov=member['coverage'];expected=(5,0) if member['member_id']=='F000477' else (4,1)
            self.assertEqual((cov['directional_yes_no_positions'],cov['not_voting_actions']),expected)
            self.assertEqual((cov['resolved_eligible_actions'],cov['missing_evidence_actions'],cov['present_actions']),(5,0,0))
        for label in ['Nay','Present']:
            pool={x['source_id']:copy.deepcopy(x) for x in self.data['sources']['sources']};pool['clerk:119:1:307']['member_records']['M001184']['official_label']=label
            with self.subTest(label=label),self.assertRaises(ValueError):self.units(pool=pool)

    def test_old_baseline_does_not_replace_the_proposed_target(self):
        pool={x['source_id']:copy.deepcopy(x) for x in self.data['sources']['sources']};pool['house-rules:rcp119-1']['text']=pool['house-rules:rcp119-1']['text'].replace('$50,000','$250,000')
        with self.assertRaises(ValueError):self.units(pool=pool)
        pool={x['source_id']:copy.deepcopy(x) for x in self.data['sources']['sources']};pool[NEW_SOURCE]['text']=pool[NEW_SOURCE]['text'].replace('$250,000','$1')
        with self.assertRaises(ValueError):self.units(pool=pool)

    def test_capture_envelope_extent_and_authority_drift_are_rejected(self):
        for kind in ['redirect','budget','range','authority']:
            capture=copy.deepcopy(self.data['capture']);bindings=copy.deepcopy(self.data['bindings']);sources=copy.deepcopy(self.data['sources'])
            if kind=='redirect':capture['attempts'][0]['final_url']='https://example.org/other'
            elif kind=='budget':capture['limits']['response_bytes']*=2
            elif kind=='range':bindings['sources'][0]['governed_end']+=1
            else:
                source=next(x for x in sources['sources'] if x['source_id']==NEW_SOURCE);source['source_type']='official_rule_text';source['governed_bytes_sha256']=sealed_digest(source,'governed_bytes_sha256')
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate_captures(capture,bindings,sources)

    def test_existing_other_and_parent_meanings_are_preserved_without_reauthoring(self):
        self.assertEqual(validate_preserved_parent_refs(self.data['preflight']),3)
        pre=copy.deepcopy(self.data['preflight']);pre['existing_parent_or_other_core_refs_to_preserve'][0]['meaning_ref']='invented-parent'
        with self.assertRaises(ValueError):validate_preserved_parent_refs(pre)
        self.assertTrue({'house:119:1:79','house:119:1:83'}.isdisjoint(x['action_id'] for x in self.data['authoring']['actions']))

    def test_claims_and_resealed_retained_sources_cannot_acquire_unsupported_meaning(self):
        for field in ['source_id','passage']:
            a=copy.deepcopy(self.data['authoring']);a['actions'][0]['claim_source_map'][0][field]='unsupported scope or source'
            with self.subTest(field=field),self.assertRaises((ValueError,KeyError)):self.units(authoring=a)
        data=self.changed('sources');source=next(x for x in data['sources']['sources'] if x['source_id']=='govinfo:hr4423eh');source['text']=source['text'].replace('unless','even if');source['governed_bytes_sha256']=sealed_digest(source,'governed_bytes_sha256')
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
        products=self.data['products'];after=copy.deepcopy(products['shared_action_core']);row=after['actions'][0];row['candidate_shared_limitations'].append('CONTROLLED source qualification, no acceptance.');row['action_core_sha256']=sealed_digest(row,'action_core_sha256');after['corpus_sha256']=digest(after['actions'])
        for member in products['member_projections']:
            with self.subTest(member=member['member_id']),self.assertRaises(SharedCorpusValidationError):validate_member_projection(ROOT,member,after)

    def test_unused_source_changes_no_product_and_authored_meaning_is_member_neutral(self):
        sources=copy.deepcopy(self.data['sources']);extra={'source_id':'synthetic:unused160','text':'Controlled unused source, not evidence.'};extra['governed_bytes_sha256']=digest(extra);sources['sources'].append(extra);self.assertEqual(digest(replay(self.data['authoring'],sources)),digest(self.data['products']))
        a=self.data['authoring'];text=str({k:a[k] for k in ['boundary','blocked_reason']})
        for row in a['actions']:text+=str({k:row[k] for k in ['meaning','compact_description','limitations','choice_meanings']})
        self.assertTrue('Foushee' not in text and 'Massie' not in text)

    def test_hold_proposition_observation_and_prior_identity_drift_fail_closed(self):
        for kind in ['hold','graph','member','prior']:
            key='authoring' if kind=='hold' else 'preflight' if kind=='prior' else 'products';data=self.changed(key)
            if kind=='hold':data[key]['blocked_episode_ids'].clear()
            elif kind=='graph':data[key]['compiled_ir']['members'][0]['proposition_graph']['propositions'].append({'invented':True})
            elif kind=='member':data[key]['member_projections'][1]['actions'][-1]['official_status']='Nay'
            else:data[key]['prior_prepared_identities'][0]=data['authoring']['actions'][0]['action_id']
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate(data)
