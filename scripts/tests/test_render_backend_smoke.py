"""Offline regression/mutation tests using authorized activation responses."""

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from scripts import render_backend_smoke as smoke


class SmokeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.authority = smoke.load_authority()

    def setUp(self):
        self.responses = {
            "health": {"status": "ok", "commit_sha": "a" * 40},
            "positions": copy.deepcopy(smoke.reference(self.authority, smoke.MEMBER, "119", "positions")),
            "evidence": copy.deepcopy(smoke.reference(self.authority, smoke.MEMBER, "119", smoke.JUSTICE)),
            "other-member": copy.deepcopy(smoke.reference(self.authority, smoke.OTHER_MEMBER, "119", "editorial")),
        }
        for scope in ("118", "119", "all"):
            self.responses[f"presentations-{scope}"] = copy.deepcopy(
                smoke.reference(self.authority, smoke.MEMBER, scope, "editorial"))

    def issue(self, issue=smoke.JUSTICE, name="presentations-119"):
        return next(row for row in self.responses[name]["presentations"] if row["issue_id"] == issue)

    def validate(self):
        return smoke.validate(self.responses, self.authority)

    def rejects(self, phrase):
        with self.assertRaisesRegex(smoke.SmokeFailure, phrase):
            self.validate()

    def test_authorized_after_state_passes(self):
        report = self.validate()
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["justice_directional_receipts"], 35)
        self.assertEqual(report["justice_noncounting_controls"], 2)
        self.assertEqual(report["published_issues"], sorted(smoke.PUBLISHED))

    def test_no_obsolete_fixture_member(self):
        self.assertEqual(self.responses["other-member"]["member_bioguide_id"], "M001184")
        self.assertTrue(all("leg_alex_morgan" not in path for path in smoke.ENDPOINTS.values()))

    def test_all_receipts_only_is_not_success(self):
        for row in self.responses["presentations-119"]["presentations"]:
            row["tier"] = "receipts_only"
        self.rejects("publication tier")

    def test_empty_missing_and_duplicate_issue_coverage_fail(self):
        original = copy.deepcopy(self.responses["presentations-119"]["presentations"])
        for rows in ([], original[:-1], original + [original[0]]):
            with self.subTest(length=len(rows)):
                self.responses["presentations-119"]["presentations"] = rows
                self.rejects("empty|coverage|duplicate")

    def test_identity_and_scope_drift_fail(self):
        for key in ("schema_version", "legislator_id", "member_bioguide_id", "scope"):
            with self.subTest(key=key):
                original = self.responses["presentations-119"][key]
                self.responses["presentations-119"][key] = "wrong"
                self.rejects("identity")
                self.responses["presentations-119"][key] = original

    def test_every_published_domain_requires_exact_provenance_and_findings(self):
        for issue in smoke.PUBLISHED:
            for field in ("provenance", "repeated_patterns", "conclusion", "coverage_text"):
                with self.subTest(issue=issue, field=field):
                    row = self.issue(issue)
                    original = row[field]
                    row[field] = {} if field in ("provenance", "conclusion") else []
                    self.rejects("differs|empty|missing")
                    row[field] = original

    def test_wrapper_identity_cannot_replace_embedded_provenance(self):
        self.issue()["provenance"]["artifact_id"] = "public-issue-presentation:f000477:justice_public_safety:m15b:v1"
        self.rejects("provenance")

    def test_empty_finding_copy_or_changed_action_binding_fails(self):
        for issue in smoke.PUBLISHED:
            row = self.issue(issue)
            finding = row["repeated_patterns"][0]
            key = "body" if issue == smoke.JUSTICE else "primary_sentence"
            for field, value in ((key, ""), ("action_ids", [])):
                with self.subTest(issue=issue, field=field):
                    original = finding[field]
                    finding[field] = value
                    self.rejects("empty|coverage")
                    finding[field] = original

    def test_overview_and_additional_findings_cannot_disappear(self):
        for issue in smoke.PUBLISHED - {smoke.JUSTICE}:
            row = self.issue(issue)
            for field in ("overview", "syntheses", "notable_choices"):
                if not row.get(field):
                    continue
                with self.subTest(issue=issue, field=field):
                    original = row[field]
                    row[field] = {} if field == "overview" else []
                    self.rejects("boundary|coverage")
                    row[field] = original

    def test_receipts_only_isolation_in_all_dimensions(self):
        for name, issue in (("presentations-119", "IMMIGRATION_BORDER"),
                            ("presentations-119", "HEALTH_SOCIAL"),
                            ("presentations-119", "ECONOMY_TAXES"),
                            ("presentations-119", "INFRASTRUCTURE_TECH_TRANSPORT"),
                            ("presentations-118", smoke.JUSTICE),
                            ("other-member", smoke.JUSTICE)):
            for field, value in (("conclusion", {"headline": "leaked"}),
                                 ("repeated_patterns", [{"body": "leaked"}]),
                                 ("exact_action_receipts", [{"canonical_action_id": "leaked"}]),
                                 ("provenance", {"artifact_id": "leaked"})):
                with self.subTest(name=name, issue=issue, field=field):
                    row = self.issue(issue, name)
                    old = row.get(field)
                    present = field in row
                    row[field] = value
                    self.rejects("isolation")
                    if present:
                        row[field] = old
                    else:
                        row.pop(field)

    def test_all_scope_boundary_required_for_every_published_domain(self):
        for issue in smoke.PUBLISHED:
            with self.subTest(issue=issue):
                row = self.issue(issue, "presentations-all")
                original = row["scope_boundary"]
                row["scope_boundary"] = "119th-Congress"
                self.rejects("scope=all boundary")
                row["scope_boundary"] = original

    def test_exact_receipts_and_noncounting_accounting_cannot_shrink(self):
        for field in ("exact_action_receipts", "reviewed_action_ids", "noncounting_controls"):
            with self.subTest(field=field):
                row = self.issue()
                old = row[field]
                row[field] = old[:-1]
                self.rejects("coverage|accounting")
                row[field] = old

    def test_empty_positions_and_evidence_fail(self):
        for response, key in (("positions", "positions"), ("evidence", "evidence")):
            with self.subTest(response=response):
                original = self.responses[response][key]
                self.responses[response][key] = []
                self.rejects("empty")
                self.responses[response][key] = original

    def test_same_roll_in_other_session_does_not_satisfy_receipt(self):
        action = self.issue()["exact_action_receipts"][0]["canonical_action_id"]
        vote = next(row for row in self.responses["evidence"]["evidence"] if row["canonical_action_id"] == action)
        vote["session"] = 2
        self.rejects("vote identity")

    def test_missing_vote_wrong_position_or_unofficial_source_fail(self):
        action = self.issue()["exact_action_receipts"][0]["canonical_action_id"]
        vote = next(row for row in self.responses["evidence"]["evidence"] if row["canonical_action_id"] == action)
        for field, value in (("position", "present"), ("position", "not_voting"),
                             ("source_url", "https://clerk.house.gov.evil.test/roll.xml"),
                             ("canonical_action_id", "house:119:2:128")):
            with self.subTest(field=field, value=value):
                original = vote[field]
                vote[field] = value
                self.rejects("recorded vote|official vote source|supporting vote missing")
                vote[field] = original

    def test_receipt_member_action_and_interpretation_binding_fail(self):
        receipt = self.issue()["exact_action_receipts"][0]
        for field in ("member_id", "member_action", "action_interpretation_sha256", "published_artifact_identity"):
            with self.subTest(field=field):
                original = receipt[field]
                receipt[field] = "wrong"
                self.rejects("receipt .* differs")
                receipt[field] = original

    def test_health_unhealthy_unknown_mismatched_or_changing_commit_fails(self):
        for health in ({"status": "error", "commit_sha": "a" * 40},
                       {"status": "ok", "commit_sha": "unknown"}):
            with self.subTest(health=health):
                self.responses["health"] = health
                self.rejects("Health")
        self.responses["health"] = {"status": "ok", "commit_sha": "a" * 40}
        with self.assertRaisesRegex(smoke.SmokeFailure, "Deployment differs"):
            smoke.validate(self.responses, self.authority, "b" * 40)
        self.responses["health-after"] = {"status": "ok", "commit_sha": "b" * 40}
        self.rejects("changed during")

    def test_http_errors_and_transients_never_use_fallback_or_retry(self):
        for error in (HTTPError("https://example.test", 404, "missing", {}, None),
                      HTTPError("https://example.test", 503, "unavailable", {}, None),
                      URLError("unavailable"), TimeoutError()):
            with self.subTest(error=type(error).__name__):
                with patch.object(smoke, "urlopen", side_effect=error) as get:
                    with self.assertRaisesRegex(smoke.SmokeFailure, "HTTP|transport"):
                        smoke.get_json("https://example.test", "/health", 1)
                self.assertEqual(get.call_count, 1)
                self.assertEqual(get.call_args.args[0].get_method(), "GET")

    def test_invalid_json_and_non_object_fail(self):
        for data in (b"not JSON", b"[]"):
            response = unittest.mock.MagicMock()
            response.__enter__.return_value = response
            response.status = 200
            response.read.return_value = data
            with self.subTest(data=data), patch.object(smoke, "urlopen", return_value=response):
                with self.assertRaises(smoke.SmokeFailure):
                    smoke.get_json("https://example.test", "/health", 1)

    def test_cli_records_failure_and_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as directory:
            error = HTTPError("https://example.test/health", 503, "unavailable", {}, None)
            with patch.object(smoke, "urlopen", side_effect=error) as get, patch("sys.stdout", io.StringIO()):
                code = smoke.main(["--api-base-url", "https://example.test", "--output-dir", directory])
            report = json.loads((Path(directory) / "report.json").read_text())
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "failed")
        self.assertIn("503", report["failure"])
        self.assertEqual(report["checked_endpoints"], [])
        self.assertEqual(get.call_count, 1)

    def test_runner_records_bounded_get_success_with_both_health_observations(self):
        values = [self.responses[name] for name in smoke.ENDPOINTS] + [self.responses["health"]]
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(smoke, "get_json", side_effect=values) as get:
                report = smoke.run("https://example.test", Path(directory), "a" * 40)
            self.assertEqual(report["status"], "passed")
            self.assertEqual(len(report["checked_endpoints"]), 8)
            self.assertEqual(get.call_count, 8)
            self.assertEqual(json.loads((Path(directory) / "health-after.json").read_text()), self.responses["health"])


if __name__ == "__main__":
    unittest.main()
