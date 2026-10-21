import copy
import unittest

from scripts.validate_infrastructure_hr859_scope137 import PACKET, SOURCES, read, validate, validate_transport


class HR859Scope137Tests(unittest.TestCase):
    def test_packet_transport_measures_the_committed_lf_bytes_it_hashes(self):
        self.assertEqual(validate_transport()['files'], 10)
        receipt = read(PACKET / 'validation_receipt.json')
        for edit in ['count', 'hash', 'units']:
            bad = copy.deepcopy(receipt)
            if edit == 'count':
                bad['packet_files'][0]['bytes'] += 1
            elif edit == 'hash':
                bad['packet_files'][0]['lf_sha256'] = '0' * 64
            else:
                bad['packet_byte_units'] = 'unspecified_worktree_bytes'
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                validate_transport(bad)

    def test_raw_captures_reconstruct_exact_selected_scopes(self):
        self.assertEqual(validate()['selected_sources'], 5)
        packet = read(PACKET / 'source_questions.json')
        for edit in ['extent', 'passage', 'whole_source', 'annotation']:
            bad = copy.deepcopy(packet)
            if edit == 'extent':
                bad['source_units'][2]['source_extent']['start'] = 0
            elif edit == 'passage':
                bad['source_units'][0]['passage'] = 'Only photographs qualify'
            elif edit == 'whole_source':
                bad['source_units'][2]['whole_source_reviewed'] = True
            else:
                bad['source_units'][4]['annotation'] = 'Silently repaired reference'
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                validate(bad)

    def test_response_bytes_cannot_be_replaced_by_an_error_or_modified_projection(self):
        captures = {k: read(PACKET / (k + '_capture.json')) for k in SOURCES}
        for edit in ['body', 'hash', 'text', 'status', 'registration']:
            bad = copy.deepcopy(captures)
            c = bad['47usc619']
            if edit == 'body':
                c['raw_response_base64'] = 'Tm90IGEgQ29kZSBwYWdl'
            elif edit == 'hash':
                c['raw_response_sha256'] = '0' * 64
            elif edit == 'text':
                c['normalized_text'] = 'All Internet services are excluded'
            elif edit == 'status':
                c['http_status'] = 403
            else:
                c['source_registered'] = True
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                validate(captures=bad)

    def test_missing_body_and_locator_provenance_are_not_reconstructed(self):
        diagnosis = read(PACKET / 'access_diagnosis_and_followup.json')
        for edit in ['missing_body', 'href', 'locator', 'ordering', 'helper']:
            bad = copy.deepcopy(diagnosis)
            if edit == 'missing_body':
                next(f for f in bad['followups'] if f['source_key'] == '47usc255')['raw_response_sha256'] = '0' * 64
            elif edit == 'href':
                bad['retained617_href_inspection']['hrefs_containing255'] = ['invented255link']
            elif edit == 'locator':
                bad['publisher_locator_followup']['original_failure_body_reconstructed'] = True
            elif edit == 'ordering':
                bad['publisher_locator_followup']['response_retained_before_validation'] = False
            else:
                bad['executed_locator_capture_helper']['LF_sha256'] = '0' * 64
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                validate(diagnosis=bad)

    def test_research_cannot_clear_case_coverage_or_pending_approval(self):
        packet = read(PACKET / 'source_questions.json')
        for field in ['canonical_state_changed', 'whole_action_meaning_completed',
                      'device_exception_scope_cleared', 'actual_device_classified',
                      'current_law_certified', 'all_incorporated_regulations_reviewed',
                      'semantic_acceptance', 'publication_authorized',
                      'production_authorized', 'compatibility_authorized', 'Health_activated']:
            bad = copy.deepcopy(packet)
            bad[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate(bad)
        bad = copy.deepcopy(packet)
        bad['successful_original_raw_captures'] = 6
        with self.assertRaisesRegex(ValueError, 'accounting'):
            validate(bad)


if __name__ == '__main__':
    unittest.main()
