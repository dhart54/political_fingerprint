"""Static preservation and negative-dependency checks for the hard cutover."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "docs/editorial/editorial_hard_cutover_v1_receipt.json"
FROZEN_MANIFEST = (
    ROOT / "docs/editorial/frozen_historical_evidence_manifest_v1.json"
)


class EditorialHardCutoverIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
        cls.frozen_manifest = json.loads(
            FROZEN_MANIFEST.read_text(encoding="utf-8")
        )

    def test_deleted_executable_and_test_paths_are_absent(self) -> None:
        deleted = (
            self.receipt["deleted_executable_paths"]
            + self.receipt["deleted_test_paths"]
        )
        self.assertGreater(len(deleted), 0)
        for relative in deleted:
            with self.subTest(path=relative):
                self.assertFalse((ROOT / relative).exists())

    def test_surviving_runtime_cannot_import_legacy_paths(self) -> None:
        forbidden = tuple(self.receipt["deleted_import_tokens"])
        runtime_roots = (
            ROOT / "backend/app",
            ROOT / "backend/scripts",
            ROOT / "frontend/app",
            ROOT / "frontend/components",
            ROOT / "frontend/lib",
            ROOT / "scripts",
        )
        executable_suffixes = {".py", ".js", ".mjs"}
        violations: list[str] = []
        for runtime_root in runtime_roots:
            for path in runtime_root.rglob("*"):
                if not path.is_file() or path.suffix not in executable_suffixes:
                    continue
                if path.name.endswith((".test.js", ".test.mjs")):
                    continue
                source = path.read_text(encoding="utf-8")
                matches = [token for token in forbidden if token in source]
                if matches:
                    violations.append(
                        f"{path.relative_to(ROOT).as_posix()}: {matches}"
                    )
        self.assertEqual(violations, [])

    def test_preserved_files_match_base_hashes(self) -> None:
        for record in self.receipt["preserved_file_hashes"]:
            path = ROOT / record["path"]
            with self.subTest(path=record["path"]):
                self.assertTrue(path.is_file())
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(digest, record["sha256"])

    def test_frozen_historical_json_is_parseable(self) -> None:
        parsed = 0
        for relative in self.receipt["preserved_historical_evidence_roots"]:
            root = ROOT / relative
            self.assertTrue(root.exists(), relative)
            for path in root.rglob("*.json"):
                with self.subTest(path=path.relative_to(ROOT).as_posix()):
                    json.loads(path.read_text(encoding="utf-8"))
                    parsed += 1
        self.assertGreater(parsed, 0)

    def test_frozen_historical_tree_matches_base_manifest(self) -> None:
        manifest = self.frozen_manifest
        self.assertEqual(
            manifest["base_commit"],
            self.receipt["base_commit"],
        )
        self.assertEqual(
            manifest["roots"],
            self.receipt["preserved_historical_evidence_roots"],
        )
        expected = {record["path"]: record for record in manifest["files"]}
        self.assertEqual(len(expected), len(manifest["files"]))

        actual: set[str] = set()
        for relative_root in manifest["roots"]:
            root = ROOT / relative_root
            actual.update(
                path.relative_to(ROOT).as_posix()
                for path in root.rglob("*")
                if path.is_file()
            )
        self.assertEqual(actual, set(expected))

        for relative, record in expected.items():
            path = ROOT / relative
            with self.subTest(path=relative):
                content = path.read_bytes()
                if path.suffix in {".json", ".md"}:
                    content = content.replace(b"\r\n", b"\n")
                self.assertEqual(len(content), record["size_bytes"])
                self.assertEqual(
                    hashlib.sha256(content).hexdigest(),
                    record["sha256"],
                )
                self.assertRegex(record["git_blob_sha1"], r"^[0-9a-f]{40}$")

    def test_economy_provenance_graph_resolves(self) -> None:
        root = ROOT / "docs/editorial/valerie_foushee_economy_gold_v2"
        sources = _load(root / "source_manifest.json")["sources"]
        claims = _load(root / "claim_source_map.json")["claims"]
        source_ids = _assert_sources(self, sources)
        claim_ids = _assert_claims(
            self,
            claims,
            source_ids,
            allowed_states={
                "supported",
                "supported_as_attributed_argument",
                "supported_as_editorial_safety_conclusion",
                "supported_context_only",
            },
        )

        context_only = {
            source["source_id"]
            for source in sources
            if source["claim_support_status"] == "context_only"
        }
        referenced = {
            source_id for claim in claims for source_id in claim["source_ids"]
        }
        self.assertTrue(context_only)
        self.assertTrue(context_only.isdisjoint(referenced))

        references: set[str] = set()
        for path in [root / "review_packet.json", *root.glob("measures/*.json")]:
            references.update(_collect_id_references(_load(path), "claim"))
        self.assertTrue(references)
        self.assertTrue(references.issubset(claim_ids))

    def test_justice_provenance_and_review_sources_resolve(self) -> None:
        root = (
            ROOT
            / "docs/editorial/valerie_foushee_justice_public_safety_gold_v1"
        )
        claims = _load(root / "claim_source_map.json")["claims"]
        claim_ids = [claim["claim_id"] for claim in claims]
        self.assertEqual(len(claim_ids), len(set(claim_ids)))
        for claim in claims:
            self.assertTrue(claim["source_ids"])
            self.assertEqual(
                claim["human_approval_status"],
                "human_approval_pending",
            )

        packet = _load(root / "review_packet.json")
        sources = [
            source
            for interpretation in packet["interpretations"]
            for source in interpretation["two_minute"]["sources"]
        ]
        self.assertTrue(sources)
        for source in sources:
            self.assertTrue(source["url"].startswith("https://"))
            self.assertTrue(source["locator"].strip())

    def test_environment_provenance_and_preservation_receipts_resolve(self) -> None:
        root = ROOT / "docs/editorial/commissioning_domain_v1"
        for variant in (root, root / "corrected"):
            with self.subTest(variant=variant.relative_to(ROOT).as_posix()):
                source_manifest = _load(variant / "source_manifest.json")
                self.assertEqual(
                    source_manifest["source_states"],
                    [
                        "source_attached",
                        "claim_mapped",
                        "claim_supported",
                        "human_verified",
                    ],
                )
                source_ids = _assert_sources(self, source_manifest["sources"])
                claims = _load(variant / "claim_source_map.json")["claims"]
                _assert_claims(
                    self,
                    claims,
                    source_ids,
                    allowed_states={"claim_supported", "supported_absence"},
                )
                for dossier_path in variant.glob("dossiers/*.json"):
                    dossier = _load(dossier_path)["dossier"]
                    self.assertTrue(set(dossier["source_ids"]).issubset(source_ids))
                    self.assertFalse(
                        _load(dossier_path)["publication"]["production_eligible"]
                    )

        preservation = _load(
            root / "corrected/original_preservation_receipt.json"
        )
        self.assertEqual(
            preservation["status"],
            "preserved_unchanged_historical_evidence",
        )
        for relative, record in preservation["artifacts"].items():
            with self.subTest(artifact=relative):
                payload = _load(root / relative)
                if relative == "persistence_batch_manifest.json":
                    self.assertEqual(
                        payload["manifest_sha256"],
                        preservation["original_manifest_sha256"],
                    )
                    self.assertEqual(
                        len(payload["artifacts"]),
                        payload["expected_counts"]["artifacts"],
                    )
                    self.assertEqual(
                        len(payload["relationships"]),
                        payload["expected_counts"]["relationships"],
                    )
                    continue
                semantic = json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
                self.assertEqual(
                    hashlib.sha256(semantic).hexdigest(),
                    record["semantic_sha256"],
                )

        final_receipt = _load(root / "corrected/final_composition_receipt.json")
        self.assertFalse(
            final_receipt["production_state"]["final_proposal_applied"]
        )
        self.assertEqual(
            final_receipt["production_state"]["publication_registry_count"],
            0,
        )
        self.assertGreater(
            final_receipt["final_persistence_proposal"]["relationship_count"],
            0,
        )

    def test_acquisition_and_persistence_safety_boundaries_exist(self) -> None:
        for key in (
            "preserved_acquisition_paths",
            "preserved_persistence_and_recovery_paths",
        ):
            for relative in self.receipt[key]:
                with self.subTest(boundary=key, path=relative):
                    self.assertTrue((ROOT / relative).exists())

    def test_frontend_route_outcomes_are_deliberate(self) -> None:
        self.assertFalse(
            (ROOT / "frontend/app/golden-render-fixture/page.js").exists()
        )
        self.assertTrue((ROOT / "frontend/app/page.js").is_file())
        self.assertTrue(
            (ROOT / "frontend/lib/basicEvidencePresentation.mjs").is_file()
        )


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_sources(
    test_case: unittest.TestCase,
    sources: list[dict],
) -> set[str]:
    source_ids = [source["source_id"] for source in sources]
    test_case.assertEqual(len(source_ids), len(set(source_ids)))
    for source in sources:
        test_case.assertTrue(source["url"].startswith("https://"))
        test_case.assertTrue(source["locator"].strip())
    return set(source_ids)


def _assert_claims(
    test_case: unittest.TestCase,
    claims: list[dict],
    source_ids: set[str],
    *,
    allowed_states: set[str],
) -> set[str]:
    claim_ids = [claim["claim_id"] for claim in claims]
    test_case.assertEqual(len(claim_ids), len(set(claim_ids)))
    for claim in claims:
        test_case.assertTrue(set(claim["source_ids"]).issubset(source_ids))
        state = claim.get("claim_support_status", claim.get("state"))
        test_case.assertIn(state, allowed_states)
    return set(claim_ids)


def _collect_id_references(value: object, prefix: str) -> set[str]:
    references: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == f"{prefix}_id" and isinstance(nested, str):
                references.add(nested)
            elif key == f"{prefix}_ids" and isinstance(nested, list):
                references.update(
                    item for item in nested if isinstance(item, str)
                )
            else:
                references.update(_collect_id_references(nested, prefix))
    elif isinstance(value, list):
        for nested in value:
            references.update(_collect_id_references(nested, prefix))
    return references


if __name__ == "__main__":
    unittest.main()
