"""Canonical read-only orchestration for all newly commissioned editorial work."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from .adapters import (
    build_persistence_proposal,
    build_presentation_payload,
    build_review_payload,
    semantic_digest,
)
from .compiler import compile_semantic_ir, project_compiler_input
from .validation import validate_compiled_ir


@dataclass(frozen=True)
class EditorialPipelineResult:
    """Products of one compiler invocation and meaning-preserving adaptation."""

    compiled_ir: dict[str, Any]
    validation: dict[str, int]
    review_payload: dict[str, Any]
    presentation_payload: dict[str, Any]
    persistence_proposal: dict[str, Any] | None


def run_editorial_pipeline(
    compiler_input: dict[str, Any],
    *,
    prepare_persistence_proposal: bool = False,
) -> EditorialPipelineResult:
    """Compile input exactly once, validate it, then adapt compiled meaning."""

    input_snapshot = copy.deepcopy(compiler_input)
    compiled = compile_semantic_ir(input_snapshot)
    validation = validate_compiled_ir(compiled)
    digest_before_adapters = semantic_digest(compiled)
    review = build_review_payload(compiled)
    presentation = build_presentation_payload(compiled)
    persistence = (
        build_persistence_proposal(compiled)
        if prepare_persistence_proposal
        else None
    )
    if semantic_digest(compiled) != digest_before_adapters:
        raise RuntimeError("a downstream adapter mutated compiled Semantic IR")
    return EditorialPipelineResult(
        compiled_ir=compiled,
        validation=validation,
        review_payload=review,
        presentation_payload=presentation,
        persistence_proposal=persistence,
    )


def replay_accepted_reference(
    accepted_case: dict[str, Any],
    *,
    prepare_persistence_proposal: bool = False,
) -> EditorialPipelineResult:
    """Deliberately replay an accepted fixture through the same public path."""

    return run_editorial_pipeline(
        project_compiler_input(accepted_case),
        prepare_persistence_proposal=prepare_persistence_proposal,
    )
