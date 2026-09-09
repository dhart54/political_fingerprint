"""Canonical read-only orchestration for all newly commissioned editorial work."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from ..editorial_presentations.compiler import (
    compile_public_issue_presentation,
)
from ..editorial_presentations.validation import (
    validate_public_issue_presentation,
)
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
    public_presentation_artifact: dict[str, Any] | None
    public_presentation_validation: dict[str, int] | None
    persistence_proposal: dict[str, Any] | None


def run_editorial_pipeline(
    compiler_input: dict[str, Any],
    *,
    prepare_persistence_proposal: bool = False,
    public_presentation_authoring: dict[str, Any] | None = None,
    trusted_action_source_contract: dict[str, Any] | None = None,
    trusted_trajectory_comparisons: dict[str, Any] | None = None,
) -> EditorialPipelineResult:
    return _run_editorial_pipeline(compiler_input,
        prepare_persistence_proposal=prepare_persistence_proposal,
        public_presentation_authoring=public_presentation_authoring,
        trusted_action_source_contract=trusted_action_source_contract,
        trusted_trajectory_comparisons=trusted_trajectory_comparisons)


def _run_editorial_pipeline(compiler_input, *, prepare_persistence_proposal=False,
        public_presentation_authoring=None, trusted_action_source_contract=None,
        trusted_trajectory_comparisons=None, historical_reference=False):
    """Compile input exactly once, validate it, then adapt compiled meaning."""

    input_snapshot = copy.deepcopy(compiler_input)
    compiled = compile_semantic_ir(input_snapshot)
    validation = validate_compiled_ir(compiled)
    if not historical_reference:
        from .trajectory_comparability import validate_comparison, TrajectoryComparabilityError
        from .compiler import SemanticCompilerInputError
        for member in compiled['members']:
            for proposition in member['proposition_graph']['propositions']:
                if proposition['proposition_type'] != 'trajectory':
                    continue
                evidence = (trusted_trajectory_comparisons or {}).get(proposition['proposition_id'])
                if not evidence or evidence.get('compiler_input_sha256') != semantic_digest(input_snapshot):
                    raise SemanticCompilerInputError('new trajectory requires separately trusted substantive comparison evidence')
                candidate = evidence['candidate']
                if (candidate['evidence_action_ids'] != proposition['evidence_action_ids']
                        or candidate['direction'] != proposition['direction']):
                    raise SemanticCompilerInputError('comparison differs from compiled member observations')
                try:
                    validate_comparison(candidate, {e['episode_id']:e for e in evidence['episodes']},
                                        evidence['comparisons'])
                except TrajectoryComparabilityError as exc:
                    raise SemanticCompilerInputError(str(exc)) from exc
    digest_before_adapters = semantic_digest(compiled)
    review = build_review_payload(compiled)
    presentation = build_presentation_payload(compiled)
    if (
        public_presentation_authoring is not None
        and trusted_action_source_contract is None
    ):
        raise ValueError(
            "public presentation authoring requires a separately trusted "
            "action/source contract"
        )
    public_presentation = (
        compile_public_issue_presentation(
            compiled,
            public_presentation_authoring,
            trusted_action_source_contract=trusted_action_source_contract,
        )
        if public_presentation_authoring is not None
        else None
    )
    public_presentation_validation = (
        validate_public_issue_presentation(public_presentation)
        if public_presentation is not None
        else None
    )
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
        public_presentation_artifact=public_presentation,
        public_presentation_validation=public_presentation_validation,
        persistence_proposal=persistence,
    )


def replay_accepted_reference(
    accepted_case: dict[str, Any],
    *,
    prepare_persistence_proposal: bool = False,
    public_presentation_authoring: dict[str, Any] | None = None,
    trusted_action_source_contract: dict[str, Any] | None = None,
) -> EditorialPipelineResult:
    """Deliberately replay an accepted fixture through the same public path."""

    # This is an integrity lookup, not compiler inference from reference outputs.
    # Exact frozen references cannot become a route for new candidate authoring.
    import json
    from pathlib import Path
    from .compiler import SemanticCompilerInputError
    root = Path(__file__).resolve().parents[3] / 'docs/semantic_ir/accepted'
    matched = False
    for name, expected in (
        ('development_cases.json', 'e6f2ba9a90fd06b7a80257a39b5807ed5d819c549561eaf0f52e65ed743a9627'),
        ('held_out_cases.json', '23172278dd2b537151ec4795bfc3d199d208d79f41e3166c6c84d1df480da1f5'),
    ):
        corpus = json.loads((root/name).read_text(encoding='utf-8'))
        if semantic_digest(corpus) != expected:
            raise SemanticCompilerInputError('historical reference corpus differs')
        matched = matched or any(semantic_digest(c) == semantic_digest(accepted_case) for c in corpus['cases'])
    if not matched:
        raise SemanticCompilerInputError('historical replay requires an exact frozen accepted reference')

    return _run_editorial_pipeline(
        project_compiler_input(accepted_case),
        prepare_persistence_proposal=prepare_persistence_proposal,
        public_presentation_authoring=public_presentation_authoring,
        trusted_action_source_contract=trusted_action_source_contract,
        historical_reference=True,
    )
