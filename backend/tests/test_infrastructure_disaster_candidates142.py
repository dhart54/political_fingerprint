import copy
import unittest

from scripts.validate_infrastructure_disaster_candidates142 import (
    PACKET, OUTPUTS, read, reconstruct_capture, validate, validate_sources, validate_transport,
)


class DisasterCandidates142Tests(unittest.TestCase):
    def test_original_bytes_and_existing_pipeline_produce_held_five_case_candidates(self):
        r = validate()
        self.assertEqual((r['actions'], r['shared_cores'], r['official_member_observations']), (5, 5, 10))
        self.assertEqual(r['issue_propositions'], 0)
        self.assertFalse(r['canonical_state_changed'])
        self.assertGreater(validate_transport(), 40)

    def test_response_corruption_or_status_cannot_be_relabelled_as_evidence(self):
        c = read(PACKET/'26usc6303_capture.json')
        for key, value in [('raw_response_sha256','0'*64),('http_status',403),('attempt_number',2),
                           ('source_registered',True),('canonical_state_changed',0)]:
            bad=copy.deepcopy(c);bad[key]=value
            with self.subTest(key=key), self.assertRaises(ValueError):
                reconstruct_capture(bad)

    def test_partitioned_response_cannot_escape_packet_or_reorder_parts(self):
        c=read(PACKET/'crec20250331house_capture.json')
        for key,value in [('path','../../outside.json'),('index',1),('sha256','0'*64)]:
            bad=copy.deepcopy(c);bad['raw_response_base64_parts'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                reconstruct_capture(bad)

    def test_selected_extent_cannot_expand_beyond_documentary_reading(self):
        u=read(PACKET/'source_units.json')
        for change in ['extent','whole_document']:
            bad=copy.deepcopy(u)
            if change=='extent':bad['units'][0]['source_extent']['end']+=1
            else:bad['units'][0]['whole_document_reviewed']=True
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_sources(units=bad)

    def test_member_labels_and_retained_source_objects_cannot_be_rewritten(self):
        s=read(PACKET/'sources.json')
        clerk=next(x for x in s['sources'] if x['source_id']=='clerk:119:1:13')
        clerk['member_records']['M001184']['official_label']='Yea'
        with self.assertRaisesRegex(ValueError,'Retained sources'):
            validate_sources(capture=s)

    def test_candidate_cannot_acquire_acceptance_publication_or_general_rule(self):
        b=read(PACKET/'decision_bundle.json')
        for key in ['semantic_acceptance','publication_authorized','production_authorized','canonical_state_changed']:
            bad=copy.deepcopy(b);bad[key]=True
            with self.subTest(key=key),self.assertRaises(ValueError):validate(bundle=bad)
        a=read(PACKET/'authoring.json');a['actions'][0]['meaning']='All studies are categorically ineligible.'
        with self.assertRaises(ValueError):validate(authoring=a)

    def test_compiled_mapping_and_member_projection_cannot_bypass_holds(self):
        o={k:read(PACKET/'generated'/(k+'.json')) for k in OUTPUTS}
        for change in ['hold','eligibility','member','authority']:
            bad=copy.deepcopy(o)
            if change=='hold':bad['shared_issue_mapping']['source_render_constraints']=[]
            elif change=='eligibility':bad['shared_issue_mapping']['action_mappings'][0]['eligibility']['decision']='eligible'
            elif change=='member':bad['member_projections'][1]['actions'][2]['official_status']='Yea'
            else:bad['readable_candidates']['production_eligible']=True
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'replay'):
                validate(outputs=bad)


if __name__ == '__main__':
    unittest.main()
