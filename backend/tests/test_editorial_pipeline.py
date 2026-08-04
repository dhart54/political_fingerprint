"""Canonical-path and adapter-isolation tests for Editorial Pipeline V1."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import run_editorial_pipeline as pipeline_command

from backend.app.semantic_ir.adapters import (
    build_persistence_proposal,
    build_presentation_payload,
    semantic_digest,
)
from backend.app.semantic_ir.compiler import (
    SemanticCompilerInputError,
    compile_semantic_ir,
    project_compiler_input,
)
from backend.app.semantic_ir.pipeline import (
    replay_accepted_reference,
    run_editorial_pipeline,
)

ROOT = Path(__file__).resolve().parents[2]
DEVELOPMENT = ROOT / "docs/semantic_ir/accepted/development_cases.json"
HELD_OUT = ROOT / "docs/semantic_ir/accepted/held_out_cases.json"


def _cases() -> dict[str, dict]:
    result = {}
    for path in (DEVELOPMENT, HELD_OUT):
        for case in json.loads(path.read_text(encoding="utf-8"))["cases"]:
            result[case["case_id"]] = case
    return result


class EditorialPipelineV1Tests(unittest.TestCase):
    def test_pipeline_invokes_pure_compiler_exactly_once(self) -> None:
        payload = project_compiler_input(
            _cases()["semir-dev-01-economy-funding-stages"]
        )
        with patch(
            "backend.app.semantic_ir.pipeline.compile_semantic_ir",
            wraps=compile_semantic_ir,
        ) as compiler:
            result = run_editorial_pipeline(payload)
        self.assertEqual(compiler.call_count, 1)
        self.assertEqual(result.validation["member_count"], 1)

    def test_new_work_rejects_expected_semantic_outputs(self) -> None:
        payload = project_compiler_input(
            _cases()["semir-dev-04-justice-mixed-fentanyl-trajectory"]
        )
        payload["composition"] = {"conclusion_plan": {}}
        with self.assertRaises(SemanticCompilerInputError):
            run_editorial_pipeline(payload)

    def test_adapters_preserve_compiled_meaning_and_do_not_mutate(self) -> None:
        result = replay_accepted_reference(
            _cases()["semir-dev-08-environment-separate-family-episodes"]
        )
        compiled = result.compiled_ir
        before = semantic_digest(compiled)
        presentation = build_presentation_payload(compiled)
        proposal = build_persistence_proposal(compiled)
        self.assertEqual(semantic_digest(compiled), before)
        self.assertEqual(proposal["compiled_ir"], compiled)
        self.assertFalse(proposal["persistence_authorized"])
        self.assertFalse(proposal["publication_authorized"])
        for source, adapted in zip(compiled["members"], presentation["members"]):
            self.assertEqual(source["proposition_graph"], adapted["proposition_graph"])
            self.assertEqual(source["composition"], adapted["composition"])

    def test_optional_persistence_stage_is_inert_and_explicit(self) -> None:
        case = _cases()["semir-held-01-partial-service-missing-evidence"]
        default = replay_accepted_reference(case)
        requested = replay_accepted_reference(case, prepare_persistence_proposal=True)
        self.assertIsNone(default.persistence_proposal)
        self.assertIsNotNone(requested.persistence_proposal)
        self.assertFalse(requested.persistence_proposal["production_write_performed"])
        self.assertEqual(
            default.compiled_ir,
            requested.persistence_proposal["compiled_ir"],
        )

    def test_default_command_has_no_legacy_or_publication_imports(self) -> None:
        source = (ROOT / "scripts/run_editorial_pipeline.py").read_text(
            encoding="utf-8"
        )
        forbidden = (
            "editorial_candidate_evaluation",
            "editorial_candidate_selection",
            "editorial_conclusion_synthesis",
            "editorial_domain_eligibility",
            "editorial_inference",
            "editorial_member_overlay",
            "editorial_proposition_ownership",
            "editorial_review_routing",
            "build_blind_editorial_pipeline_validation",
            "build_commissioning_domain_v1",
            "build_justice_cross_member_validation",
            "build_valerie_foushee",
            "editorial_artifact_store",
        )
        for name in forbidden:
            self.assertNotIn(name, source)

    def test_frontend_release_resolves_platform_npm_executable(self) -> None:
        with (
            patch.object(
                pipeline_command,
                "_semantic_loop",
                return_value={"tier": "semantic", "commands": []},
            ),
            patch.object(
                pipeline_command.shutil,
                "which",
                return_value=r"C:\tools\npm.cmd",
            ),
            patch.object(
                pipeline_command,
                "_run",
                return_value={"command": "npm build", "status": "pass"},
            ) as run,
        ):
            result = pipeline_command._release_loop(
                include_frontend=True,
                include_persistence=False,
            )
        run.assert_called_once_with(
            [r"C:\tools\npm.cmd", "run", "build", "--prefix", "frontend"]
        )
        self.assertTrue(result["frontend_included"])

    def test_persistence_release_uses_pytest_collection(self) -> None:
        with (
            patch.object(
                pipeline_command,
                "_semantic_loop",
                return_value={"tier": "semantic", "commands": []},
            ),
            patch.object(
                pipeline_command,
                "_run",
                return_value={"command": "pytest persistence", "status": "pass"},
            ) as run,
        ):
            result = pipeline_command._release_loop(
                include_frontend=False,
                include_persistence=True,
            )
        run.assert_called_once_with(
            [
                pipeline_command.sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "backend/tests/test_editorial_artifact_persistence.py",
            ]
        )
        self.assertTrue(result["persistence_included"])

    def test_representative_boundary_routes_are_preserved(self) -> None:
        cases = _cases()
        expected = {
            "semir-dev-01-economy-funding-stages": "human_exception_required",
            "semir-dev-04-justice-mixed-fentanyl-trajectory": (
                "human_exception_required"
            ),
            "semir-dev-08-environment-separate-family-episodes": (
                "standard_generation_pass"
            ),
            "semir-held-02-source-conflict-unsupported": "blocked",
            "semir-held-01-partial-service-missing-evidence": "blocked",
        }
        for case_id, route in expected.items():
            with self.subTest(case_id=case_id):
                result = replay_accepted_reference(copy.deepcopy(cases[case_id]))
                self.assertEqual(
                    result.compiled_ir["members"][0]["review_route"], route
                )


if __name__ == "__main__":
    unittest.main()
