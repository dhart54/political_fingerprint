from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.etl.interpretation_source_readiness import (  # noqa: E402
    SourceReadinessError,
    build_readiness_artifact,
    canonical_file_sha256,
    load_json,
    sha256_json,
)
from scripts.validate_full_issue_interpretation_source_readiness import (  # noqa: E402
    ARTIFACT_PATH,
    AUTHORITY_PATH,
    CURRENT_STATE_PATH,
    DISCOVERY_PATH,
    MANIFEST_PATH,
    SCHEMA_PATH,
    SOURCE_MANIFEST_PATH,
    validate_values,
)


class FullIssueInterpretationSourceReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = load_json(ROOT / ARTIFACT_PATH)
        cls.source_manifest = load_json(ROOT / SOURCE_MANIFEST_PATH)
        cls.manifest = load_json(ROOT / MANIFEST_PATH)
        cls.authority = load_json(ROOT / AUTHORITY_PATH)
        cls.discovery = load_json(ROOT / DISCOVERY_PATH)
        cls.schema = load_json(ROOT / SCHEMA_PATH)
        cls.current_state = load_json(ROOT / CURRENT_STATE_PATH)

    def _validate(
        self,
        *,
        artifact=None,
        source_manifest=None,
        current_state=None,
    ):
        return validate_values(
            artifact=artifact or copy.deepcopy(self.artifact),
            source_manifest=source_manifest or copy.deepcopy(self.source_manifest),
            approved_manifest=copy.deepcopy(self.manifest),
            authority=copy.deepcopy(self.authority),
            discovery=copy.deepcopy(self.discovery),
            schema=copy.deepcopy(self.schema),
            current_state=current_state or copy.deepcopy(self.current_state),
            repository_root=ROOT,
        )

    def _reject_artifact(self, mutator) -> None:
        artifact = copy.deepcopy(self.artifact)
        mutator(artifact)
        with self.assertRaises(SourceReadinessError):
            self._validate(artifact=artifact)

    def test_repository_artifact_passes_with_37_ready_actions(self) -> None:
        result = self._validate()
        self.assertEqual(result["total_action_count"], 37)
        self.assertEqual(result["ready_count"], 37)
        self.assertEqual(result["blocked_count"], 0)

    def test_missing_duplicate_and_outside_actions_are_rejected(self) -> None:
        mutations = [
            lambda value: value["subject"]["action_readiness"].pop(),
            lambda value: value["subject"]["action_readiness"].append(
                copy.deepcopy(value["subject"]["action_readiness"][0])
            ),
            lambda value: value["subject"]["action_readiness"][0].__setitem__(
                "action_id", "house:119:2:999"
            ),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self._reject_artifact(mutation)

    def test_authority_and_action_set_tampering_is_rejected(self) -> None:
        mutations = [
            lambda value: value["subject"].__setitem__(
                "approved_manifest_sha256", "0" * 64
            ),
            lambda value: value["subject"].__setitem__(
                "authority_receipt_sha256", "0" * 64
            ),
            lambda value: value["subject"].__setitem__("action_set_sha256", "0" * 64),
            lambda value: value["subject"].__setitem__(
                "universe_subject_sha256", "0" * 64
            ),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self._reject_artifact(mutation)

    def test_missing_or_changed_vote_source_is_rejected(self) -> None:
        self._reject_artifact(
            lambda value: value["subject"]["action_readiness"][0][
                "vote_source_bindings"
            ].clear()
        )
        self._reject_artifact(
            lambda value: value["subject"]["action_readiness"][0][
                "vote_source_bindings"
            ][0].__setitem__("source_content_sha256", "0" * 64)
        )

    def test_missing_changed_or_wrong_action_exact_source_is_rejected(self) -> None:
        self._reject_artifact(
            lambda value: value["subject"]["action_readiness"][0][
                "exact_action_source_bindings"
            ].clear()
        )
        self._reject_artifact(
            lambda value: value["subject"]["action_readiness"][0][
                "exact_action_source_bindings"
            ][0].__setitem__("source_content_sha256", "0" * 64)
        )
        self._reject_artifact(
            lambda value: value["subject"]["action_readiness"][0][
                "exact_action_source_bindings"
            ][0].__setitem__("source_id", "source-for-another-action")
        )

    def test_parent_only_amendment_source_and_wrong_text_version_are_rejected(
        self,
    ) -> None:
        def parent_only(value):
            record = next(
                row
                for row in value["subject"]["action_readiness"]
                if row["action_id"] == "house:119:1:32"
            )
            record["exact_action_source_bindings"][0]["source_subject"] = "119:hr:27"

        self._reject_artifact(parent_only)
        self._reject_artifact(
            lambda value: value["subject"]["action_readiness"][0][
                "exact_action_source_bindings"
            ][0].__setitem__("text_version", "")
        )

    def test_unapproved_source_type_and_escaping_path_are_rejected(self) -> None:
        self._reject_artifact(
            lambda value: value["subject"]["action_readiness"][0][
                "exact_action_source_bindings"
            ][0].__setitem__("source_type", "news_article")
        )
        source_manifest = copy.deepcopy(self.source_manifest)
        raw = next(
            source
            for row in source_manifest["subject"]["action_sources"]
            for source in row["exact_action_sources"]
            if "governed_local_path" in source
        )
        raw["governed_local_path"] = "../outside.xml"
        source_manifest["source_manifest_subject_sha256"] = sha256_json(
            source_manifest["subject"]
        )
        with self.assertRaises(SourceReadinessError):
            self._validate(source_manifest=source_manifest)

    def test_conflict_constraint_and_blocked_as_ready_are_rejected(self) -> None:
        self._reject_artifact(
            lambda value: value["subject"]["action_readiness"][0].__setitem__(
                "source_conflict_state", "unresolved"
            )
        )
        self._reject_artifact(
            lambda value: value["subject"]["action_readiness"][0].__setitem__(
                "source_constraint_state", "blocked"
            )
        )
        self._reject_artifact(
            lambda value: value["subject"]["action_readiness"][0][
                "readiness_criteria"
            ].__setitem__("all_source_digests_valid", False)
        )

    def test_fisa_memberships_and_every_limitation_are_required(self) -> None:
        for action_id in ("house:119:2:155", "house:119:2:221"):

            def missing_membership(value, action_id=action_id):
                row = next(
                    item
                    for item in value["subject"]["action_readiness"]
                    if item["action_id"] == action_id
                )
                row["cross_domain_memberships"].remove("NATIONAL_SECURITY")

            def missing_limitation(value, action_id=action_id):
                row = next(
                    item
                    for item in value["subject"]["action_readiness"]
                    if item["action_id"] == action_id
                )
                row["cross_domain_scope_limitations"].pop()

            with self.subTest(action_id=action_id, case="membership"):
                self._reject_artifact(missing_membership)
            with self.subTest(action_id=action_id, case="limitation"):
                self._reject_artifact(missing_limitation)

    def test_semantic_and_presentation_fields_are_rejected(self) -> None:
        forbidden = [
            "party",
            "accepted_interpretation",
            "benchmark_conclusion",
            "episode_id",
            "proposition_ids",
            "synthesis",
            "public_wording",
        ]
        for field in forbidden:
            with self.subTest(field=field):
                self._reject_artifact(
                    lambda value, field=field: value["subject"]["action_readiness"][
                        0
                    ].__setitem__(field, "forbidden")
                )

    def test_current_state_cannot_claim_interpretation_started(self) -> None:
        state = copy.deepcopy(self.current_state)
        state["full_record_issue_interpretation"][
            "f000477_justice_119_action_interpretation_state"
        ] = "in_progress"
        with self.assertRaises(SourceReadinessError):
            self._validate(current_state=state)

    def test_source_manifest_has_no_test_only_or_secondary_evidence(self) -> None:
        serialized = json.dumps(self.source_manifest, sort_keys=True).lower()
        self.assertNotIn("fixture", serialized)
        self.assertNotIn("pytest", serialized)
        self.assertNotIn("news_article", serialized)
        self.assertNotIn("advocacy", serialized)

    def test_build_is_deterministic(self) -> None:
        kwargs = {
            "approved_manifest": self.manifest,
            "authority_receipt": self.authority,
            "authority_receipt_sha256": canonical_file_sha256(ROOT / AUTHORITY_PATH),
            "manifest_sha256": canonical_file_sha256(ROOT / MANIFEST_PATH),
            "source_manifest": self.source_manifest,
            "source_manifest_sha256": canonical_file_sha256(
                ROOT / SOURCE_MANIFEST_PATH
            ),
            "discovery": self.discovery,
        }
        first = build_readiness_artifact(**kwargs)
        second = build_readiness_artifact(**kwargs)
        self.assertEqual(first, second)
        self.assertEqual(first, self.artifact)


if __name__ == "__main__":
    unittest.main()
