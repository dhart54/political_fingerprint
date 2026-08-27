"""Mechanical boundaries only; semantic completeness remains independent review."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

from backend.app.semantic_ir.action_interpretability import (
    canonical_bytes, digest, load_json, qualify_candidate,
)
from backend.app.semantic_ir.m14c_source_hold_closure import (
    ACCEPTED_IDS, AM, BASE, BASE_DIGEST, EO51, EO68, HOLD_IDS, OUTPUT,
    ClosureError, baseline, expected_authority, source_catalog,
    validate_closure, validate_scope,
    ENRICHED_AUTHORITY_FILE, ORIGINAL_AUTHORITY_SHA256, REVIEWED_RECORD_DIGESTS,
    REVIEWED_SET_DIGEST, expected_enriched_authority, validate_human_acceptance,
)

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / OUTPUT
BUILDER = ROOT / "scripts/build_m14c_source_hold_closure.py"


class M14CSourceHoldClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = load_json(DEST / "action_interpretability_candidates.json")
        cls.authority = load_json(DEST / "human_acceptance_authority.json")
        cls.catalog = load_json(DEST / "source_catalog.json")
        cls.overlay = load_json(DEST / "source_overlay.json")
        cls.base = baseline(ROOT)

    def validate(self, artifact=None, authority=None, catalog=None, overlay=None):
        return validate_closure(
            ROOT, artifact if artifact is not None else self.artifact,
            authority if authority is not None else self.authority,
            catalog if catalog is not None else self.catalog,
            overlay if overlay is not None else self.overlay,
        )

    def invalid_candidate(self, artifact) -> None:
        # Negative cases must not rely on stale cached qualification.
        readiness = {r["action_id"]: r for r in self.overlay["subject"]["action_readiness"]}
        for candidate in artifact["candidates"]:
            candidate["qualification"] = qualify_candidate(candidate, readiness[candidate["action_id"]])
        with self.assertRaises(ValueError):
            self.validate(artifact=artifact)

    def changed_candidate(self, action_id=HOLD_IDS[0]):
        artifact = copy.deepcopy(self.artifact)
        return artifact, next(r for r in artifact["candidates"] if r["action_id"] == action_id)

    def test_real_v1_closure_has_seventeen_human_approved_without_promotion(self):
        result = self.validate()
        self.assertEqual(result["candidate_state_counts"], {"candidate_complete_for_semantic_review": 17})
        self.assertEqual(result["human_accepted_unchanged_count"], 14)
        self.assertEqual(result["newly_accepted_count"], 3)
        self.assertEqual(result["human_approved_count"], 17)
        self.assertEqual(result["unaccepted_count"], 0)
        self.assertEqual(result["automatic_acceptance_count"], 0)
        self.assertFalse(result["canonical_promotion"])
        self.assertEqual(result["remaining_source_hold_ids"], [])

    def test_only_three_candidate_records_change(self):
        before = {r["action_id"]: canonical_bytes(r) for r in self.base["candidates"]}
        changed = {r["action_id"] for r in self.artifact["candidates"] if canonical_bytes(r) != before[r["action_id"]]}
        self.assertEqual(changed, set(HOLD_IDS))

    def test_authority_binds_exact_baseline_manifest_records_and_scope(self):
        self.assertEqual(self.authority, expected_authority(ROOT))
        subject = self.authority["subject"]
        self.assertEqual(subject["baseline_commit"], BASE)
        self.assertEqual(subject["m14b_candidate_set_sha256"], BASE_DIGEST)
        self.assertEqual([r["action_id"] for r in subject["accepted_records"]], list(ACCEPTED_IDS))
        self.assertEqual(subject["explicitly_unaccepted_source_hold_ids"], list(HOLD_IDS))
        self.assertEqual([k for k, v in subject["authorizations"].items() if v],
                         ["later_canonical_semantic_promotion_of_exact_accepted_records"])

    def test_authority_rehash_does_not_permit_record_or_scope_changes(self):
        for mutation in ("record", "membership", "promotion", "historical"):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(self.authority)
                subject = changed["subject"]
                if mutation == "record":
                    subject["accepted_records"][0]["candidate_record_sha256"] = "0" * 64
                elif mutation == "membership":
                    subject["accepted_records"][0]["action_id"] = HOLD_IDS[0]
                elif mutation == "promotion":
                    subject["authorizations"]["promotion_during_m14c"] = True
                else:
                    subject["historical_m13_authority_replaced"] = True
                changed["authority_subject_sha256"] = digest(subject)
                with self.assertRaisesRegex(ClosureError, "immutable human authority"):
                    self.validate(authority=changed)

    def test_all_accepted_records_reject_semantic_and_metadata_edits(self):
        for action_id in ACCEPTED_IDS:
            for field in ("policy_choice", "candidate_id"):
                with self.subTest(action_id=action_id, field=field):
                    changed, candidate = self.changed_candidate(action_id)
                    candidate[field] += " changed"
                    self.invalid_candidate(changed)

    def test_holds_cannot_be_automatically_accepted_or_published(self):
        for action_id in HOLD_IDS:
            for flag in ("accepted", "authorizing", "public", "production_selectable"):
                with self.subTest(action_id=action_id, flag=flag):
                    changed, candidate = self.changed_candidate(action_id)
                    candidate[flag] = True
                    self.invalid_candidate(changed)

    def test_exact_action_identity_and_legacy_meaning_are_frozen(self):
        for field in ("legislative_stage", "current_accepted_legacy_meaning"):
            changed, candidate = self.changed_candidate()
            candidate[field] = "changed"
            self.invalid_candidate(changed)

    def test_catalog_rejects_source_identity_role_excerpt_or_digest_changes(self):
        for field in ("source_id", "action_id", "source_type", "relation_role", "source_url"):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.catalog)
                changed["sources"][0][field] += " changed"
                with self.assertRaisesRegex(ClosureError, "source identity"):
                    self.validate(catalog=changed)
        changed = copy.deepcopy(self.catalog)
        source = changed["sources"][0]
        excerpt = source["neutral_projection"]["excerpts"][0]
        excerpt["text"] += " changed"
        excerpt["text_sha256"] = hashlib.sha256(excerpt["text"].encode()).hexdigest()
        source["neutral_projection_sha256"] = digest(source["neutral_projection"])
        with self.assertRaisesRegex(ClosureError, "source identity"):
            self.validate(catalog=changed)

    def test_official_raw_byte_corruption_fails_for_every_source(self):
        original = Path.read_bytes
        for source in self.catalog["sources"]:
            target = ROOT / source["raw_provenance"]["governed_local_path"]
            def read(path):
                raw = original(path)
                return raw + b"corruption" if path == target else raw
            with self.subTest(source=source["source_id"]), mock.patch.object(Path, "read_bytes", read):
                with self.assertRaisesRegex(ClosureError, "official source bytes differ"):
                    source_catalog(ROOT)

    def test_source_scopes_separate_amendment_text_and_incorporated_definition(self):
        sources = {s["source_id"]: s for s in self.catalog["sources"]}
        amendment = " ".join(e["text"] for e in sources[AM]["neutral_projection"]["excerpts"])
        definition = sources[EO68]["neutral_projection"]["excerpts"][0]["text"]
        self.assertNotIn("The Acting CHAIR", amendment)
        self.assertTrue(definition.startswith("Sec. 2. Policy and Definitions."))
        self.assertNotIn("Sec. 3. Recognizing", definition)

    def test_source_overlay_changes_only_three_packets(self):
        old = load_json(ROOT / self.base["input_bindings"]["source_readiness"]["path"])
        before = {r["action_id"]: r for r in old["subject"]["action_readiness"]}
        changed = set()
        for row in self.overlay["subject"]["action_readiness"]:
            if row != before[row["action_id"]]:
                changed.add(row["action_id"])
                self.assertEqual(row["baseline_source_packet_sha256"], before[row["action_id"]]["source_packet_sha256"])
        self.assertEqual(changed, set(HOLD_IDS))

    def test_overlay_cannot_reclassify_legacy_purpose_as_operative_amendment(self):
        changed = copy.deepcopy(self.overlay)
        row = next(r for r in changed["subject"]["action_readiness"] if r["action_id"] == HOLD_IDS[0])
        row["source_roles"]["operative_content_interpretation_input"] = ["congress-text:119:hr:1048:eh"]
        changed["source_readiness_subject_sha256"] = digest(changed["subject"])
        with self.assertRaisesRegex(ClosureError, "source overlay differs"):
            self.validate(overlay=changed)

    def test_amendment_cannot_map_claims_to_parent_bill(self):
        changed, candidate = self.changed_candidate()
        candidate["claim_source_mappings"][0]["source_id"] = "congress-text:119:hr:1048:eh"
        self.invalid_candidate(changed)

    def test_cross_action_source_and_ungoverned_locator_fail(self):
        for source_id, locator in ((EO51, "other action"), (AM, "invented locator")):
            changed, candidate = self.changed_candidate()
            candidate["claim_source_mappings"][0].update(source_id=source_id, locator=locator)
            self.invalid_candidate(changed)

    def test_new_official_source_must_be_claim_bound(self):
        changed, candidate = self.changed_candidate(HOLD_IDS[2])
        candidate["claim_source_mappings"] = [m for m in candidate["claim_source_mappings"] if m["source_id"] != EO68]
        self.invalid_candidate(changed)

    def test_wrong_packet_binding_fails(self):
        changed, candidate = self.changed_candidate()
        candidate["governed_source_packet_sha256"] = "0" * 64
        self.invalid_candidate(changed)

    def test_protected_historical_bindings_cannot_be_removed(self):
        changed = copy.deepcopy(self.artifact)
        changed["protected_historical_artifacts"] = []
        self.invalid_candidate(changed)

    def test_milestone_scope_guard_rejects_other_domains_core_and_public_paths(self):
        for path in ("docs/editorial/full_record_reviews/education.json",
                     "docs/editorial/full_record_reviews/justice.json",
                     "docs/editorial/full_record_reviews/national_security.json",
                     "docs/editorial/full_record_reviews/environment.json",
                     "docs/shared_legislative_corpus/core.json",
                     "frontend/app/page.tsx", "backend/app/api/positions.py"):
            with self.subTest(path=path), mock.patch("subprocess.check_output", return_value=path + "\n"):
                with self.assertRaisesRegex(ClosureError, "protected baseline artifact changed"):
                    validate_scope(ROOT)

    def test_offline_check_reproduces_without_rewriting_any_artifact(self):
        paths = list(DEST.glob("*.json"))
        before = {p: p.read_bytes() for p in paths}
        run = subprocess.run([sys.executable, str(BUILDER), "--check"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(before, {p: p.read_bytes() for p in paths})

    def test_initialize_cannot_overwrite_authority_or_candidates(self):
        paths = [DEST / "human_acceptance_authority.json", DEST / "action_interpretability_candidates.json"]
        before = {p: p.read_bytes() for p in paths}
        run = subprocess.run([sys.executable, str(BUILDER), "--initialize"], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("refusing to overwrite immutable authority", run.stderr)
        self.assertEqual(before, {p: p.read_bytes() for p in paths})

    def test_all_seventeen_record_digests_match_the_human_reviewed_inputs(self):
        expected = {r["action_id"]: digest(r) for r in self.base["candidates"] if r["action_id"] in ACCEPTED_IDS}
        expected.update(REVIEWED_RECORD_DIGESTS)
        self.assertEqual({r["action_id"]: digest(r) for r in self.artifact["candidates"]}, expected)
        self.assertEqual(digest(self.artifact["candidates"]), REVIEWED_SET_DIGEST)
        self.assertEqual(hashlib.sha256((DEST / "human_acceptance_authority.json").read_bytes()).hexdigest(),
                         ORIGINAL_AUTHORITY_SHA256)

    def test_enriched_authority_is_exact_additive_and_promotion_bounded(self):
        authority = load_json(DEST / ENRICHED_AUTHORITY_FILE)
        self.assertEqual(authority, expected_enriched_authority())
        self.assertTrue(authority["immutable"])
        self.assertTrue(authority["subject"]["additive"])
        self.assertFalse(authority["subject"]["replaces_existing_authority"])
        self.assertEqual({r["action_id"] for r in authority["subject"]["accepted_records"]}, set(HOLD_IDS))
        self.assertEqual([k for k, v in authority["subject"]["authorizations"].items() if v],
                         ["later_canonical_semantic_promotion_of_exact_accepted_records"])

    def test_enriched_authority_rejects_rehashed_identity_record_and_permission_changes(self):
        authority = expected_enriched_authority()
        mutations = ["baseline_commit", "reviewed_m14c_head", "candidate_set_sha256", "accepted_records"]
        mutations.extend(authority["subject"]["authorizations"])
        for field in mutations:
            with self.subTest(field=field):
                changed = copy.deepcopy(authority)
                if field in changed["subject"]["authorizations"]:
                    changed["subject"]["authorizations"][field] = not changed["subject"]["authorizations"][field]
                elif field == "accepted_records":
                    changed["subject"][field][0]["candidate_record_sha256"] = "0" * 64
                else:
                    changed["subject"][field] = "0" * 64
                changed["authority_subject_sha256"] = digest(changed["subject"])
                with self.assertRaisesRegex(ClosureError, "immutable enriched3"):
                    validate_human_acceptance(ROOT, self.artifact, changed)

    def test_newly_human_accepted_records_also_reject_semantic_or_metadata_edits(self):
        for action_id in HOLD_IDS:
            for field in ("policy_choice", "candidate_id"):
                changed, candidate = self.changed_candidate(action_id)
                candidate[field] += " changed"
                with self.subTest(action_id=action_id, field=field):
                    with self.assertRaisesRegex(ClosureError, "reviewed17 candidate records changed"):
                        validate_human_acceptance(ROOT, changed, expected_enriched_authority())

    def test_acceptance_cannot_be_rewritten_or_accepted_candidates_refrozen(self):
        paths = list(DEST.glob("*.json"))
        before = {p: p.read_bytes() for p in paths}
        for option, error in (("--record-human-acceptance", "refusing to overwrite immutable enriched3"),
                              ("--freeze-candidates", "human-accepted candidate records cannot be regenerated")):
            run = subprocess.run([sys.executable, str(BUILDER), option], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn(error, run.stderr)
            self.assertEqual(before, {p: p.read_bytes() for p in paths})

    def test_original_authority_byte_change_fails_even_if_json_meaning_is_unchanged(self):
        original = Path.read_bytes
        target = DEST / "human_acceptance_authority.json"
        def read(path):
            raw = original(path)
            return raw + b"\n" if path == target else raw
        with mock.patch.object(Path, "read_bytes", read):
            with self.assertRaisesRegex(ClosureError, "original14 authority bytes changed"):
                validate_human_acceptance(ROOT, self.artifact, expected_enriched_authority())

    def test_acceptance_scope_rejects_reviewed_candidate_or_authority_file_changes(self):
        for name in ("action_interpretability_candidates.json", "human_acceptance_authority.json", "source_overlay.json"):
            with mock.patch("subprocess.check_output", return_value=f"{OUTPUT}/{name}\n"):
                with self.assertRaisesRegex(ClosureError, "acceptance closure changed protected reviewed files"):
                    validate_scope(ROOT)


if __name__ == "__main__":
    unittest.main()
