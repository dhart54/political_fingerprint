"""Offline tests for the diagnostic pilot inventory; no API or database calls."""
import copy
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts import audit_pilot_slice as audit


class PilotSliceInventoryTests(unittest.TestCase):
    def setUp(self):
        self.scope = "119"
        self.data = {"/health": {"status": "ok", "commit_sha": "a" * 40}}
        for member in audit.MEMBERS:
            prefix = f"/legislators/{member}"
            self.data[prefix + "/profile"] = {"id": member, "name_display": member}
            self.data[prefix + "/contact"] = {"legislator_id": member, "contact_status": "not_loaded"}
            self.data[prefix + "/positions?scope=119"] = {
                "legislator_id": member, "scope": "119",
                "positions": [{"domain": d, "total_votes": 0} for d in audit.DOMAINS]}
            self.data[prefix + "/editorial-presentations?scope=119"] = {
                "legislator_id": member, "scope": "119",
                "presentations": [{"issue_id": d, "tier": "receipts_only", "reviewed_scope": None} for d in audit.DOMAINS]}
            for domain in audit.DOMAINS:
                self.data[prefix + f"/positions/{domain}/evidence?scope=119"] = {
                    "legislator_id": member, "scope": "119", "domain": domain, "evidence": []}
        self.evidence_path = f"/legislators/{audit.MEMBERS[0]}/positions/{audit.DOMAINS[0]}/evidence?scope=119"
        self.editorial_path = f"/legislators/{audit.MEMBERS[0]}/editorial-presentations?scope=119"

    def collect(self, fetch=None):
        return audit.collect("https://example.test", "119", fetch=fetch or (lambda base, path, timeout: copy.deepcopy(self.data[path])))

    def test_valid_empty_is_observed_not_user_ready(self):
        result = self.collect()
        self.assertEqual(result["status"], "observed")
        self.assertEqual(len(result["requests"]), 26)
        self.assertEqual(result["members"][0]["issues"][0]["receipt_rows"], 0)
        self.assertIsNone(result["members"][1]["issues"][0]["reviewed_scope"])
        self.assertNotIn("ready", result)
        self.assertTrue(all("body" not in request for request in result["requests"].values()))
        self.assertTrue(all(len(request["canonical_json_sha256"]) == 64 for request in result["requests"].values()))

    def test_failure_is_unknown_not_zero(self):
        def fetch(base, path, timeout):
            if path == self.evidence_path:
                raise audit.SmokeFailure("HTTP 503")
            return self.data[path]
        result = self.collect(fetch)
        self.assertEqual(result["status"], "incomplete")
        self.assertIsNone(result["members"][0]["issues"][0]["receipt_rows"])
        self.assertIn("HTTP 503", json.dumps(result["members"][0]["errors"]))

    def test_wrong_identity_scope_domain_and_shape_are_rejected(self):
        original = self.data[self.evidence_path]
        for key, value in (("legislator_id", "wrong"), ("scope", "118"), ("domain", "wrong"), ("evidence", {})):
            with self.subTest(key=key):
                self.data[self.evidence_path] = {**original, key: value}
                result = self.collect()
                self.assertEqual(result["status"], "incomplete")
                self.assertIsNone(result["members"][0]["issues"][0]["receipt_rows"])
        self.data[self.evidence_path] = original

    def test_missing_domain_and_duplicate_domain_are_rejected(self):
        original = self.data[self.editorial_path]["presentations"]
        for values in (original[:-1], original + [original[0]]):
            self.data[self.editorial_path]["presentations"] = values
            self.assertEqual(self.collect()["status"], "incomplete")

    def test_public_finding_requires_exact_receipt_without_inference(self):
        row = self.data[self.editorial_path]["presentations"][0]
        row.update(tier="reviewed_conclusion", reviewed_scope="119",
                   repeated_patterns=[{"action_ids": ["house:119:1:10"]}])
        result = self.collect()
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["members"][0]["issues"][0]["missing_linked_receipts"], ["house:119:1:10"])
        self.data[self.evidence_path]["evidence"] = [{"canonical_action_id": "house:119:1:10", "position": "not_voting"}]
        result = self.collect()
        self.assertEqual(result["status"], "observed")
        self.assertEqual(result["members"][0]["issues"][0]["positions_seen"], ["not_voting"])
        self.assertNotIn("support", json.dumps(result["members"][0]["issues"][0]))

    def test_semantic_lineage_is_not_treated_as_a_public_receipt_link(self):
        row = self.data[self.editorial_path]["presentations"][0]
        row["syntheses"] = [{"semantic_lineage_action_ids": ["private"], "action_ids": [], "public_supporting_action_ids": []}]
        self.assertEqual(self.collect()["members"][0]["issues"][0]["linked_finding_actions"], 0)

    def test_public_support_metadata_cannot_hide_rendered_action_links(self):
        row = self.data[self.editorial_path]["presentations"][0]
        row["syntheses"] = [{"action_ids": ["house:119:1:10"], "public_supporting_action_ids": []}]
        result = self.collect()
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["members"][0]["issues"][0]["missing_linked_receipts"], ["house:119:1:10"])

    def test_overview_missing_present_and_malformed_receipt_links(self):
        row = self.data[self.editorial_path]["presentations"][0]
        row["overview"] = {"action_ids": ["house:119:1:10"]}
        result = self.collect()
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["members"][0]["issues"][0]["linked_finding_actions"], 1)
        self.data[self.evidence_path]["evidence"] = [{"canonical_action_id": "house:119:1:10"}]
        self.assertEqual(self.collect()["status"], "observed")
        for overview in ([], {"action_ids": "house:119:1:10"}, {"public_supporting_action_ids": {}}):
            with self.subTest(overview=overview):
                row["overview"] = overview
                self.assertEqual(self.collect()["status"], "incomplete")

    def test_count_mismatch_and_duplicate_ids_are_diagnostics_not_reinterpretation(self):
        self.data[self.evidence_path]["evidence"] = [{"canonical_action_id": "house:119:1:1"}] * 2
        row = self.collect()["members"][0]["issues"][0]
        self.assertFalse(row["receipt_count_matches_positions"])
        self.assertEqual(row["duplicate_canonical_ids"], ["house:119:1:1"])
        self.assertEqual(row["receipts_without_source_url"], 2)

    def test_deployment_change_or_missing_health_is_not_complete(self):
        count = 0
        def fetch(base, path, timeout):
            nonlocal count
            if path == "/health":
                count += 1
                return {"status": "ok", "commit_sha": ("a" if count == 1 else "b") * 40}
            return self.data[path]
        result = self.collect(fetch)
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("Deployment changed", result["errors"][0])
        self.data["/health"] = {"status": "ok"}
        self.assertEqual(self.collect()["status"], "incomplete")

    def test_invalid_count_and_unknown_tier_are_not_observed(self):
        path = f"/legislators/{audit.MEMBERS[0]}/positions?scope=119"
        self.data[path]["positions"][0]["total_votes"] = True
        self.data[self.editorial_path]["presentations"][0]["tier"] = "approved_by_ai"
        self.assertEqual(self.collect()["status"], "incomplete")

    def test_nonobject_payload_is_reported(self):
        self.data[self.evidence_path] = []
        self.assertEqual(self.collect()["status"], "incomplete")

    def test_preserves_existing_output_before_network(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            output.write_text("keep me", encoding="utf-8")
            with patch.object(audit, "collect") as collect, self.assertRaises(SystemExit):
                audit.main(["--output", str(output)])
            collect.assert_not_called()
            self.assertEqual(output.read_text(), "keep me")

    def test_rejects_unsafe_url_and_invalid_timeout_before_network(self):
        for args in (("--api-base-url", "https://user:password@example.test"), ("--timeout", "nan")):
            with patch.object(audit, "collect") as collect, self.assertRaises(SystemExit):
                audit.main(["--output", "unused.json", *args])
            collect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
