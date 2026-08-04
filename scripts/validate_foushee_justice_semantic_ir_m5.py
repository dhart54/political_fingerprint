"""Independent deterministic validation for the detached M5 artifacts."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.compiler import (  # noqa: E402
    SemanticCompilerInputError,
    compile_semantic_ir,
)
from backend.app.semantic_ir.pipeline import run_editorial_pipeline  # noqa: E402
from backend.app.semantic_ir.validation import validate_compiled_ir  # noqa: E402
from scripts.build_foushee_justice_semantic_ir_m5 import (  # noqa: E402
    OUTPUT_ROOT,
    build,
    digest,
    file_digest,
    load,
)


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def validate() -> dict[str, object]:
    expected = build(True)
    input_artifact = load(OUTPUT_ROOT / "frozen_final_compiler_input.json")
    graph = load(OUTPUT_ROOT / "frozen_final_compiled_semantic_ir.json")
    implementation = load(OUTPUT_ROOT / "provisional_implementation_bundle.json")
    verification = load(OUTPUT_ROOT / "independent_implementation_verification.json")
    compiler_input = input_artifact["compiler_input"]
    compiled = compile_semantic_ir(copy.deepcopy(compiler_input))
    require(
        compiled == graph["compiled_ir"],
        "compiled graph does not follow from frozen input",
    )
    require(
        run_editorial_pipeline(copy.deepcopy(compiler_input)).compiled_ir == compiled,
        "pipeline output differs",
    )
    validate_compiled_ir(compiled)
    member = compiled["members"][0]
    propositions = member["proposition_graph"]["propositions"]
    behavioral = [p for p in propositions if p["semantic_role"] == "behavioral"]
    accounting = graph["full_universe_action_accounting"]
    require(
        len(accounting) == 37 and len({r["action_id"] for r in accounting}) == 37,
        "action accounting differs",
    )
    for blocked in ("house:119:2:155", "house:119:2:278"):
        require(
            not any(blocked in p["evidence_action_ids"] for p in propositions),
            f"{blocked} entered a proposition",
        )
    roll128 = [p for p in behavioral if "house:119:1:128" in p["evidence_action_ids"]]
    require(
        len(roll128) == 1
        and roll128[0]["mechanism_or_trait_refs"] == ["concealed_carry_resolved_scope"],
        "roll 128 scope differs",
    )
    require(
        graph["render_plan"]
        == {"example_prose": None, "analytical_additions_allowed": False},
        "render plan differs",
    )
    require(
        implementation["accepted_semantic_reference"] is False
        and implementation["canonical"] is False
        and implementation["public"] is False
        and implementation["persisted"] is False
        and implementation["published"] is False,
        "candidate isolation differs",
    )
    require(
        verification["status"] == "pass" and all(verification["checks"].values()),
        "independent verification differs",
    )
    # Invariance and input-only rejection.
    changed = copy.deepcopy(compiler_input)
    changed["members"][0]["member_id"] = "TEST"
    require(
        compile_semantic_ir(changed)["members"][0]["proposition_graph"]
        == member["proposition_graph"],
        "member invariance differs",
    )
    changed = copy.deepcopy(compiler_input)
    changed["members"][0]["party"] = "R"
    require(
        compile_semantic_ir(changed)["members"][0]["proposition_graph"]
        == member["proposition_graph"],
        "party invariance differs",
    )
    changed = copy.deepcopy(compiler_input)
    changed["shared_semantics"]["actions"].reverse()
    changed["members"][0]["actions"].reverse()
    require(
        compile_semantic_ir(changed)["members"][0]["proposition_graph"]
        == member["proposition_graph"],
        "action-order invariance differs",
    )
    changed = copy.deepcopy(compiler_input)
    for action in changed["shared_semantics"]["actions"]:
        action["eligibility"]["exact_action_basis"] = "TITLE MUTATION"
    require(
        compile_semantic_ir(changed)["members"][0]["proposition_graph"]
        == member["proposition_graph"],
        "title invariance differs",
    )
    changed = copy.deepcopy(compiler_input)
    changed["coverage"] = {}
    try:
        compile_semantic_ir(changed)
    except SemanticCompilerInputError:
        pass
    else:
        raise ValueError("expected-output field was accepted")
    parity = load(OUTPUT_ROOT / "parity_manifest.json")
    for entry in parity["entries"]:
        path = OUTPUT_ROOT / entry["path"]
        require(
            file_digest(path) == entry["final_file_sha256"],
            f"stale parity digest: {entry['path']}",
        )
        if entry["content_subject_sha256"]:
            value = load(path)
            subject = {k: v for k, v in value.items() if k != "content_subject_sha256"}
            require(
                digest(subject) == entry["content_subject_sha256"],
                f"stale content digest: {entry['path']}",
            )
    dossier = (OUTPUT_ROOT / "review_dossier.md").read_text(encoding="utf-8")
    require(
        str(graph["action_accounting_counts"]["included_in_behavioral_proposition"])
        in dossier
        and "Roll 155" in dossier
        and "Roll 278" in dossier,
        "JSON-Markdown parity differs",
    )
    changed_paths = {
        p.as_posix() for p in ROOT.glob("docs/semantic_ir/accepted/**/*") if p.is_file()
    }
    require(
        not any("semantic_ir_implementations" in p for p in changed_paths),
        "candidate leaked into accepted corpus",
    )
    return {
        "status": "pass",
        "family_count": expected["families"],
        "trait_count": expected["traits"],
        "relationship_count": expected["relationships"],
        "behavioral_propositions": expected["behavioral"],
        "behavioral_directions": expected["behavioral_directions"],
        "synthesis_propositions": expected["synthesis"],
        "coverage": expected["coverage"],
        "action_accounting": expected["accounting"],
        "risk_count": expected["risk_count"],
        "calibration_count": expected["calibration_count"],
        "independent_verification": expected["verification"],
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
