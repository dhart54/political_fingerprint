"""Static preservation and negative-dependency checks for the hard cutover."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "docs/editorial/editorial_hard_cutover_v1_receipt.json"


class EditorialHardCutoverIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

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


if __name__ == "__main__":
    unittest.main()
