from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from backend.app.etl.full_record_synthesis_decisions import (
    SynthesisDecisionError,
    digest,
    validate_authority,
    validate_implementation,
)
from backend.scripts.build_m13j_education_workforce_synthesis_acceptance import (
    AUTHORITY_PATH,
    IMPLEMENTATION_PATH,
    M13H_AUTHORITY_PATH,
    M13H_IMPLEMENTATION_PATH,
    PACKAGE_PATH,
    TEMPLATE_PATH,
    build,
)
from scripts.validate_m13j_education_workforce_synthesis_acceptance import validate


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def inputs() -> tuple[dict, dict, dict, dict, dict, dict]:
    return (
        load(PACKAGE_PATH),
        load(TEMPLATE_PATH),
        load(AUTHORITY_PATH),
        load(IMPLEMENTATION_PATH),
        load(M13H_AUTHORITY_PATH),
        load(M13H_IMPLEMENTATION_PATH),
    )


def test_m13j_build_and_independent_validator_pass() -> None:
    assert build(check=True)["canonical_internal_synthesis_count"] == 0
    assert validate()["status"] == "pass"


def test_zero_candidate_authority_requires_package_level_no_safe_decision() -> None:
    package, template, authority, *_ = inputs()
    changed = deepcopy(authority)
    changed["subject"]["authority_decision"]["decision"] = (
        "approved_all_synthesis_candidates_as_written"
    )
    changed["authority_subject_sha256"] = digest(
        {
            key: value
            for key, value in changed.items()
            if key != "authority_subject_sha256"
        }
    )
    with pytest.raises(SynthesisDecisionError, match="lacks accepted"):
        validate_authority(changed, package=package, decision_template=template)


def test_fake_placeholder_synthesis_is_rejected() -> None:
    package, template, authority, *_ = inputs()
    changed = deepcopy(package)
    changed["subject"]["synthesis_candidates"] = [
        {"synthesis_candidate_id": "fake-placeholder"}
    ]
    with pytest.raises(SynthesisDecisionError):
        validate_authority(authority, package=changed, decision_template=template)


def test_standalone_proposition_cannot_enter_relationship() -> None:
    package, template, authority, *_ = inputs()
    changed = deepcopy(package)
    changed["subject"]["complete_proposition_accounting"][0][
        "candidate_relationships"
    ] = [
        {
            "synthesis_candidate_id": "invented",
            "relationship_role": "primary_support",
        }
    ]
    with pytest.raises(SynthesisDecisionError, match="no-safe-synthesis"):
        validate_authority(authority, package=changed, decision_template=template)


def test_raw_evidence_or_implementation_record_cannot_bypass_m13h() -> None:
    package, template, authority, implementation, h_authority, h_implementation = (
        inputs()
    )
    changed = deepcopy(implementation)
    changed["subject"]["implementation_records"] = [
        {
            "synthesis_candidate_id": "raw-episode-placeholder",
            "evidence_episode_ids": ["single-119-hr-1005-1-312"],
        }
    ]
    changed["implementation_subject_sha256"] = digest(
        {
            key: value
            for key, value in changed.items()
            if key != "implementation_subject_sha256"
        }
    )
    with pytest.raises(SynthesisDecisionError, match="candidate set differs"):
        validate_implementation(
            changed,
            authority=authority,
            package=package,
            decision_template=template,
            accepted_behavioral_semantic_ir_authority=h_authority,
            accepted_behavioral_semantic_ir_implementation=h_implementation,
        )
