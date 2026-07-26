from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.editorial_presentations.compiler import (
    EditorialPresentationError,
    artifact_bytes,
    compile_public_issue_presentation,
)
from app.editorial_presentations.validation import (
    validate_public_issue_presentation,
)
from app.semantic_ir.pipeline import replay_accepted_reference


ROOT = Path(__file__).resolve().parents[2]
DEVELOPMENT = ROOT / "docs/semantic_ir/accepted/development_cases.json"
HELD_OUT = ROOT / "docs/semantic_ir/accepted/held_out_cases.json"
FOUSHEE_FIXTURE = (
    ROOT
    / "docs/editorial/presentations/"
    "f000477_justice_public_safety_119_review_fixture.json"
)


def _cases() -> dict[str, dict]:
    result = {}
    for path in (DEVELOPMENT, HELD_OUT):
        for case in json.loads(path.read_text(encoding="utf-8"))["cases"]:
            result[case["case_id"]] = case
    return result


def _compiled(case_id: str) -> dict:
    return replay_accepted_reference(copy.deepcopy(_cases()[case_id])).compiled_ir


def _approved_controls() -> dict:
    return {
        "semantic": {
            "status": "accepted_semantic_reference",
            "validation_status": "passed",
        },
        "editorial": {"human_approval_status": "human_approved"},
        "benchmark": {"status": "promoted"},
        "production": {"eligible": True},
        "publication": {"active": True},
        "review_receipt": {
            "receipt_id": "test-only-authorized-receipt",
            "status": "approved",
            "approvals": {
                "bounded_issue_conclusion": True,
                "repeated_pattern_statements": True,
                "fentanyl_limitation": True,
                "claim_source_mappings": True,
                "benchmark_promotion": True,
                "production_eligibility": True,
            },
        },
    }


def _input_for(compiled: dict, *, approved: bool = True) -> dict:
    member = compiled["members"][0]
    propositions = {
        item["proposition_id"]: item
        for item in member["proposition_graph"]["propositions"]
    }
    plan = member["composition"]["conclusion_plan"]
    primary = list(plan["primary_proposition_ids"])
    limiting = list(plan["limiting_proposition_ids"])
    repeated_patterns = []
    trajectories = []
    limitations = []
    primary_synthesis = {
        proposition_id
        for proposition_id in primary
        if propositions[proposition_id]["semantic_role"] == "synthesis"
    }
    for proposition_id in [*primary, *limiting]:
        if proposition_id in primary_synthesis:
            continue
        proposition = propositions[proposition_id]
        record = {
            "proposition_id": proposition_id,
            "heading": f"Reviewed {proposition['proposition_type']}",
            "body": f"Reviewed wording for {proposition_id}.",
            "action_ids": list(proposition["evidence_action_ids"]),
        }
        if proposition["proposition_type"] == "repeated_pattern":
            repeated_patterns.append(record)
        elif proposition["semantic_role"] == "behavioral":
            trajectories.append(record)
        else:
            limitations.append(record)
    return {
        "artifact_identity": {
            "artifact_id": "test:artifact:v1",
            "artifact_version": 1,
            "member_id": member["member_id"],
            "issue_id": "JUSTICE_PUBLIC_SAFETY",
            "congress": 119,
            "scope": "119",
            "source_case_id": "test-case",
        },
        "editorial_wording": {
            "status": "test_reviewed",
            "tier_display": {
                "reviewed_conclusion": {
                    "badge": "Reviewed conclusion",
                    "teaser": "Supplied reviewed conclusion wording.",
                },
                "developing_read": {
                    "badge": "Developing read",
                    "teaser": "Supplied developing wording.",
                },
                "non_directional_or_limited_evidence": {
                    "badge": "Limited reviewed evidence",
                    "teaser": "Supplied non-directional wording.",
                },
            },
            "coverage_text": "Supplied reviewed coverage wording.",
            "scope_boundary": "Supplied reviewed scope boundary.",
            "conclusion": (
                {
                    "proposition_ids": primary,
                    "headline": "Supplied reviewed headline.",
                    "body": "Supplied reviewed conclusion.",
                }
                if primary
                else None
            ),
            "repeated_patterns": repeated_patterns,
            "policy_trajectories": trajectories,
            "limitations": limitations,
        },
        "provenance": {
            "semantic_source_case_id": "test-case",
            "focused_validation_case_ids": [],
            "dossier_refs": ["test-dossier"],
            "source_refs": ["test-source"],
            "claim_refs": ["test-claim"],
            "receipt_refs": ["test-receipt"],
        },
        "controls": (
            _approved_controls()
            if approved
            else json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))[
                "controls"
            ]
        ),
    }


def test_accepted_justice_mechanism_divide_presentation() -> None:
    case = copy.deepcopy(_cases()["semir-dev-05-justice-mechanism-divide"])
    compiled = replay_accepted_reference(case).compiled_ir
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    authoring["controls"] = _approved_controls()
    pipeline_result = replay_accepted_reference(
        case,
        public_presentation_authoring=authoring,
    )
    artifact = pipeline_result.public_presentation_artifact
    assert pipeline_result.compiled_ir == compiled
    assert pipeline_result.public_presentation_validation == {
        "proposition_count": 4,
        "action_count": 7,
        "episode_count": 5,
    }
    assert artifact["frontend_display"]["tier"] == "reviewed_conclusion"
    assert len(artifact["frontend_display"]["repeated_patterns"]) == 2
    assert artifact["frontend_display"]["policy_trajectories"][0][
        "proposition_id"
    ] == "prop:bc08a2271517ebb7"
    assert validate_public_issue_presentation(artifact) == {
        "proposition_count": 4,
        "action_count": 7,
        "episode_count": 5,
    }


def test_developing_trajectory_fixture_uses_compiled_plan_not_counts() -> None:
    compiled = _compiled("semir-dev-04-justice-mixed-fentanyl-trajectory")
    artifact = compile_public_issue_presentation(compiled, _input_for(compiled))
    assert artifact["frontend_display"]["tier"] == "developing_read"
    assert artifact["controls"]["derived_semantic_tier"] == "developing_read"


@pytest.mark.parametrize(
    "case_id",
    [
        "semir-dev-09-not-voting-heavy-record",
        "semir-dev-10-present-known-coverage",
    ],
)
def test_not_voting_and_present_remain_non_directional(case_id: str) -> None:
    compiled = _compiled(case_id)
    artifact = compile_public_issue_presentation(compiled, _input_for(compiled))
    coverage = artifact["evidence_metadata"]["coverage"]
    assert coverage["not_voting_actions"] or coverage["present_actions"]
    assert all(
        item["direction"] not in {"support", "opposition"}
        for item in artifact["compiled_semantic_meaning"]["propositions"]
        if not item["evidence_action_ids"]
    )


@pytest.mark.parametrize(
    "case_id",
    [
        "semir-held-01-partial-service-missing-evidence",
        "semir-held-02-source-conflict-unsupported",
    ],
)
def test_missing_unresolved_and_conflicting_evidence_fail_to_receipts_only(
    case_id: str,
) -> None:
    compiled = _compiled(case_id)
    artifact = compile_public_issue_presentation(compiled, _input_for(compiled))
    assert artifact["frontend_display"]["tier"] == "receipts_only"
    assert artifact["frontend_display"]["conclusion"] is None


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("editorial", "human_approval_status"), "human_approval_pending"),
        (("production", "eligible"), False),
        (("publication", "active"), False),
    ],
)
def test_each_publication_gate_fails_closed(
    path: tuple[str, str],
    value: object,
) -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = _input_for(compiled)
    authoring["controls"][path[0]][path[1]] = value
    artifact = compile_public_issue_presentation(compiled, authoring)
    assert artifact["frontend_display"]["tier"] == "receipts_only"
    assert artifact["frontend_display"]["repeated_patterns"] == []


def test_pending_real_fixture_is_unpublished_and_preserves_candidate_wording() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    artifact = compile_public_issue_presentation(compiled, authoring)
    assert artifact["controls"]["derived_semantic_tier"] == "reviewed_conclusion"
    assert artifact["controls"]["publication_gates_passed"] is False
    assert artifact["frontend_display"]["tier"] == "receipts_only"
    assert artifact["editorial_wording"]["status"] == (
        "candidate_human_approval_pending"
    )


def test_scope_mismatch_is_rejected() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    artifact = compile_public_issue_presentation(compiled, _input_for(compiled))
    artifact["artifact_identity"]["congress"] = 118
    artifact["artifact_identity"]["scope"] = "118"
    with pytest.raises(EditorialPresentationError, match="119th Congress"):
        validate_public_issue_presentation(artifact)


def test_exact_action_mapping_cannot_be_replaced_by_parent_measure() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = _input_for(compiled)
    authoring["editorial_wording"]["policy_trajectories"][0]["action_ids"][0] = (
        "parent-measure:hr27"
    )
    with pytest.raises(EditorialPresentationError, match="exactly match"):
        compile_public_issue_presentation(compiled, authoring)


def test_amendment_final_passage_and_contradictory_evidence_are_retained() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    artifact = compile_public_issue_presentation(compiled, _input_for(compiled))
    trajectory = next(
        item
        for item in artifact["compiled_semantic_meaning"]["propositions"]
        if item["proposition_type"] == "trajectory"
    )
    assert trajectory["direction"] == "mixed"
    assert set(trajectory["evidence_action_ids"]) == {
        "house:119:1:32",
        "house:119:1:33",
        "house:119:1:166",
    }


def test_artifact_bytes_are_deterministic() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    first = compile_public_issue_presentation(compiled, authoring)
    second = compile_public_issue_presentation(
        copy.deepcopy(compiled),
        copy.deepcopy(authoring),
    )
    assert artifact_bytes(first) == artifact_bytes(second)


def test_action_ids_resolve_to_foushee_source_receipts() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    artifact = compile_public_issue_presentation(compiled, authoring)
    source_refs = set(artifact["provenance"]["source_refs"])
    for action_id in artifact["evidence_metadata"]["action_ids"]:
        roll = int(action_id.rsplit(":", 1)[1])
        assert f"clerk_roll_{roll:03d}" in source_refs
