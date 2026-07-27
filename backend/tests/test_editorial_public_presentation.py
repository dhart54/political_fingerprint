from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from app.editorial_presentations.compiler import (
    EditorialPresentationError,
    approval_subject_for_artifact,
    artifact_bytes,
    artifact_digest,
    build_approval_subject,
    compile_public_issue_presentation as _compile_public_issue_presentation,
    detached_receipt_matches,
    limitations_digest,
    validate_trusted_action_source_contract,
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
FOUSHEE_RECEIPT_TEMPLATE = (
    ROOT
    / "docs/editorial/presentations/"
    "f000477_justice_public_safety_119_approval_receipt_template.json"
)
FOUSHEE_APPROVAL_RECEIPT = (
    ROOT
    / "docs/editorial/presentations/"
    "f000477_justice_public_safety_119_approval_receipt.json"
)
FOUSHEE_ACTION_SOURCE_CONTRACT = (
    ROOT
    / "docs/editorial/action_source_contracts/"
    "foushee_justice_public_safety_119_v1.json"
)


def _trusted_contract(compiled: dict, authoring: dict) -> dict:
    if authoring["provenance"]["semantic_source_case_id"] == (
        "semir-dev-05-justice-mechanism-divide"
    ):
        return json.loads(
            FOUSHEE_ACTION_SOURCE_CONTRACT.read_text(encoding="utf-8")
        )
    member = compiled["members"][0]
    proposition_ids = {
        *member["composition"]["conclusion_plan"]["primary_proposition_ids"],
        *member["composition"]["conclusion_plan"]["limiting_proposition_ids"],
    }
    actions = sorted({
        action_id
        for proposition in member["proposition_graph"]["propositions"]
        if proposition["proposition_id"] in proposition_ids
        for action_id in proposition["evidence_action_ids"]
    })
    return {
        "schema_version": "editorial_action_source_contract_v1",
        "contract_id": "synthetic_test_action_source_contract_v1",
        "source_manifest": {"path": "synthetic", "sha256": "0" * 64},
        "claim_source_map": {"path": "synthetic", "sha256": "1" * 64},
        "source_authorities": {
            "test-vote-source": "house_clerk_roll_call",
            "test-meaning-source": "official_measure_text",
        },
        "actions": {
            action_id: {
                "vote_source_refs": ["test-vote-source"],
                "action_meaning_source_refs": ["test-meaning-source"],
                "required_action_meaning_source_types": [
                    "official_measure_text"
                ],
            }
            for action_id in actions
        },
    }


def compile_public_issue_presentation(
    compiled: dict,
    authoring: dict,
) -> dict:
    return _compile_public_issue_presentation(
        compiled,
        authoring,
        trusted_action_source_contract=_trusted_contract(compiled, authoring),
    )


def _approval_subject(compiled: dict, authoring: dict) -> dict:
    return build_approval_subject(
        compiled,
        authoring,
        trusted_action_source_contract=_trusted_contract(compiled, authoring),
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
        "benchmark": {"status": "gold_benchmark"},
        "production": {"eligible": True},
        "publication": {"active": True},
        "approval_mode": "detached_receipt_required",
    }


def _approved_receipt(artifact: dict) -> dict:
    subject = approval_subject_for_artifact(artifact)
    return {
        "schema_version": "editorial_public_issue_approval_receipt_v1",
        "receipt_id": "approval-receipt:test-authorized-001",
        "status": "approved",
        "binding": subject,
        "approved_statement_ids": subject["statement_ids"],
        "approved_mapping_ids": subject["mapping_ids"],
        "reviewer": {
            "reviewer_id": "reviewer:test-editorial-001",
            "authority": "editorial_publication_review_authority_v1",
        },
        "decision_timestamp": "2026-07-26T20:00:00Z",
        "limitations_acknowledged": [
            {
                **item,
                "acknowledged": True,
            }
            for item in artifact["provenance"]["review_limitations"]
        ],
        "limitations_sha256": subject["limitations_sha256"],
        "decisions": {
            "editorial_wording": "approved",
            "gold_benchmark_promotion": "approved",
            "production_eligibility": "approved",
        },
        "publication_activation": {
            "active": False,
            "decision_scope": "out_of_scope",
        },
    }


def _mapped_text(
    *,
    text: str,
    mapping_id: str,
    presentation_target: str,
    action_ids: list[str],
    episode_ids: list[str],
    proposition_ids: list[str] | None = None,
    boundary_ids: list[str] | None = None,
) -> dict:
    return {
        "statement_id": mapping_id.replace("mapping:", "statement:", 1),
        "text": text,
        "mapping": {
            "mapping_id": mapping_id,
            "proposition_ids": proposition_ids or [],
            "boundary_ids": boundary_ids or [],
            "presentation_target": presentation_target,
            "action_ids": list(action_ids),
            "episode_ids": list(episode_ids),
            "source_refs": ["test-vote-source", "test-meaning-source"],
            "receipt_refs": ["test-receipt"],
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
    planned = [propositions[item] for item in [*primary, *limiting]]
    all_actions = sorted(
        {
            action_id
            for proposition in planned
            for action_id in proposition["evidence_action_ids"]
        }
    )
    all_episodes = sorted(
        {
            episode_id
            for proposition in planned
            for episode_id in proposition["evidence_episode_ids"]
        }
    )
    repeated_patterns: list[dict] = []
    trajectories: list[dict] = []
    limitations: list[dict] = []
    conclusion_only = [
        proposition_id
        for proposition_id in primary
        if propositions[proposition_id]["presentation_target"] == "conclusion_only"
    ]
    for proposition_id in [*primary, *limiting]:
        proposition = propositions[proposition_id]
        target = proposition["presentation_target"]
        if target == "conclusion_only":
            continue
        if target not in {
            "repeated_patterns",
            "policy_trajectories",
            "meaningful_limitations",
        }:
            continue
        record = {
            "proposition_id": proposition_id,
            "heading": _mapped_text(
                text=f"Reviewed {proposition['proposition_type']}",
                mapping_id=f"mapping:{proposition_id}:heading",
                presentation_target=target,
                action_ids=proposition["evidence_action_ids"],
                episode_ids=proposition["evidence_episode_ids"],
                proposition_ids=[proposition_id],
            ),
            "body": _mapped_text(
                text=f"Reviewed wording for {proposition_id}.",
                mapping_id=f"mapping:{proposition_id}:body",
                presentation_target=target,
                action_ids=proposition["evidence_action_ids"],
                episode_ids=proposition["evidence_episode_ids"],
                proposition_ids=[proposition_id],
            ),
        }
        if target == "repeated_patterns":
            repeated_patterns.append(record)
        elif target == "policy_trajectories":
            trajectories.append(record)
        else:
            limitations.append(record)
    boundary_suffix = (
        f"{member['member_id']}:justice_public_safety:119".lower()
    )
    teaser_proposition_id = (
        conclusion_only[0]
        if conclusion_only
        else (primary[0] if primary else None)
    )
    teaser_proposition = (
        propositions[teaser_proposition_id] if teaser_proposition_id else None
    )
    teaser_target = (
        teaser_proposition["presentation_target"]
        if teaser_proposition
        else "coverage_note"
    )
    teaser_actions = (
        teaser_proposition["evidence_action_ids"] if teaser_proposition else all_actions
    )
    teaser_episodes = (
        teaser_proposition["evidence_episode_ids"]
        if teaser_proposition
        else all_episodes
    )
    authoring = {
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
                    "teaser": _mapped_text(
                        text="Supplied reviewed conclusion wording.",
                        mapping_id="mapping:tier:reviewed",
                        presentation_target=teaser_target,
                        action_ids=teaser_actions,
                        episode_ids=teaser_episodes,
                        proposition_ids=(
                            [teaser_proposition_id]
                            if teaser_proposition_id
                            else None
                        ),
                        boundary_ids=(
                            None
                            if teaser_proposition_id
                            else [f"boundary:coverage:{boundary_suffix}"]
                        ),
                    ),
                },
                "developing_read": {
                    "badge": "Developing read",
                    "teaser": _mapped_text(
                        text="Supplied developing wording.",
                        mapping_id="mapping:tier:developing",
                        presentation_target=teaser_target,
                        action_ids=teaser_actions,
                        episode_ids=teaser_episodes,
                        proposition_ids=(
                            [teaser_proposition_id]
                            if teaser_proposition_id
                            else None
                        ),
                        boundary_ids=(
                            None
                            if teaser_proposition_id
                            else [f"boundary:coverage:{boundary_suffix}"]
                        ),
                    ),
                },
                "non_directional_or_limited_evidence": {
                    "badge": "Limited reviewed evidence",
                    "teaser": _mapped_text(
                        text="Supplied non-directional wording.",
                        mapping_id="mapping:tier:limited",
                        presentation_target=teaser_target,
                        action_ids=teaser_actions,
                        episode_ids=teaser_episodes,
                        proposition_ids=(
                            [teaser_proposition_id]
                            if teaser_proposition_id
                            else None
                        ),
                        boundary_ids=(
                            None
                            if teaser_proposition_id
                            else [f"boundary:coverage:{boundary_suffix}"]
                        ),
                    ),
                },
            },
            "coverage_text": _mapped_text(
                text="Supplied reviewed coverage wording.",
                mapping_id="mapping:coverage",
                presentation_target="coverage_note",
                action_ids=all_actions,
                episode_ids=all_episodes,
                boundary_ids=[f"boundary:coverage:{boundary_suffix}"],
            ),
            "scope_boundary": _mapped_text(
                text="Supplied reviewed scope boundary.",
                mapping_id="mapping:scope",
                presentation_target="scope_note",
                action_ids=all_actions,
                episode_ids=all_episodes,
                boundary_ids=[f"boundary:scope:{boundary_suffix}"],
            ),
            "conclusion": (
                {
                    "headline": _mapped_text(
                        text="Supplied reviewed headline.",
                        mapping_id="mapping:conclusion:headline",
                        presentation_target="conclusion_only",
                        action_ids=sorted(
                            {
                                action_id
                                for item in conclusion_only
                                for action_id in propositions[item][
                                    "evidence_action_ids"
                                ]
                            }
                        ),
                        episode_ids=sorted(
                            {
                                episode_id
                                for item in conclusion_only
                                for episode_id in propositions[item][
                                    "evidence_episode_ids"
                                ]
                            }
                        ),
                        proposition_ids=conclusion_only,
                    ),
                    "body": _mapped_text(
                        text="Supplied reviewed conclusion.",
                        mapping_id="mapping:conclusion:body",
                        presentation_target="conclusion_only",
                        action_ids=sorted(
                            {
                                action_id
                                for item in conclusion_only
                                for action_id in propositions[item][
                                    "evidence_action_ids"
                                ]
                            }
                        ),
                        episode_ids=sorted(
                            {
                                episode_id
                                for item in conclusion_only
                                for episode_id in propositions[item][
                                    "evidence_episode_ids"
                                ]
                            }
                        ),
                        proposition_ids=conclusion_only,
                    ),
                }
                if conclusion_only
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
            "source_refs": ["test-vote-source", "test-meaning-source"],
            "claim_refs": ["test-claim"],
            "receipt_refs": ["test-receipt"],
            "review_limitations": [
                {
                    "limitation_id": "synthetic-bounded-sample",
                    "text": "Synthetic test evidence remains bounded.",
                }
            ],
        },
        "controls": {},
    }
    if approved:
        authoring["controls"] = _approved_controls()
    else:
        authoring["controls"] = json.loads(
            FOUSHEE_FIXTURE.read_text(encoding="utf-8")
        )["controls"]
    return authoring


def test_accepted_justice_mechanism_divide_presentation() -> None:
    case = copy.deepcopy(_cases()["semir-dev-05-justice-mechanism-divide"])
    compiled = replay_accepted_reference(case).compiled_ir
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    authoring["controls"] = _approved_controls()
    pipeline_result = replay_accepted_reference(
        case,
        public_presentation_authoring=authoring,
        trusted_action_source_contract=_trusted_contract(compiled, authoring),
    )
    artifact = pipeline_result.public_presentation_artifact
    assert pipeline_result.compiled_ir == compiled
    assert pipeline_result.public_presentation_validation == {
        "proposition_count": 4,
        "action_count": 7,
        "episode_count": 5,
    }
    assert artifact["controls"]["derived_semantic_tier"] == "reviewed_conclusion"
    assert artifact["frontend_display"]["tier"] == "receipts_only"
    assert len(artifact["editorial_wording"]["repeated_patterns"]) == 2
    assert artifact["editorial_wording"]["policy_trajectories"][0][
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
    assert artifact["frontend_display"]["tier"] == "receipts_only"
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


def test_not_voting_fixture_derives_non_directional_tier() -> None:
    compiled = _compiled("semir-dev-09-not-voting-heavy-record")
    artifact = compile_public_issue_presentation(compiled, _input_for(compiled))
    assert artifact["controls"]["derived_semantic_tier"] == (
        "non_directional_or_limited_evidence"
    )
    assert artifact["frontend_display"]["tier"] == "receipts_only"
    assert artifact["frontend_display"]["conclusion"] is None
    assert artifact["frontend_display"]["repeated_patterns"] == []


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


def test_approved_inactive_real_fixture_remains_receipts_only() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    artifact = compile_public_issue_presentation(compiled, authoring)
    assert artifact["controls"]["derived_semantic_tier"] == "reviewed_conclusion"
    assert artifact["controls"]["editorial"] == {
        "human_approval_status": "human_approved"
    }
    assert artifact["controls"]["benchmark"] == {"status": "gold_benchmark"}
    assert artifact["controls"]["production"] == {"eligible": True}
    assert artifact["controls"]["publication"] == {"active": False}
    assert artifact["controls"]["publication_gates_passed"] is False
    assert artifact["frontend_display"]["tier"] == "receipts_only"


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
    authoring["editorial_wording"]["policy_trajectories"][0]["body"]["mapping"][
        "action_ids"
    ][0] = "parent-measure:hr27"
    with pytest.raises(EditorialPresentationError, match="exactly match"):
        compile_public_issue_presentation(compiled, authoring)


def test_unmapped_limitation_is_rejected() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = _input_for(compiled)
    authoring["editorial_wording"]["limitations"].append(
        {
            "heading": "Unmapped limitation",
            "body": "This analytical sentence has no semantic mapping.",
        }
    )
    with pytest.raises(EditorialPresentationError, match="explicit mapping"):
        compile_public_issue_presentation(compiled, authoring)


def test_proposition_cannot_be_mapped_to_the_wrong_section() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = _input_for(compiled)
    trajectory = authoring["editorial_wording"]["policy_trajectories"][0]
    trajectory["body"]["mapping"]["presentation_target"] = "repeated_patterns"
    with pytest.raises(EditorialPresentationError, match="wrong presentation"):
        compile_public_issue_presentation(compiled, authoring)


def test_impossible_promoted_benchmark_value_is_rejected() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = _input_for(compiled)
    authoring["controls"]["benchmark"]["status"] = "promoted"
    artifact = compile_public_issue_presentation(compiled, authoring)
    with pytest.raises(EditorialPresentationError, match="benchmark status"):
        validate_public_issue_presentation(artifact)


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


def _all_mapped_text(wording: dict) -> list[dict]:
    records: list[dict] = []

    def collect(value: object) -> None:
        if isinstance(value, dict):
            if {"statement_id", "text", "mapping"} <= set(value):
                records.append(value)
            for nested in value.values():
                collect(nested)
        elif isinstance(value, list):
            for nested in value:
                collect(nested)

    collect(wording)
    return records


def test_real_candidate_emits_all_six_reviewed_replacements() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    artifact = compile_public_issue_presentation(compiled, authoring)
    wording = artifact["editorial_wording"]
    expected = {
        "The reviewed 119th-Congress sample shows support for reporting and for evidence, research, or implementation conditions in two independent episodes, alongside opposition to three specific proposals concerning retired-service firearm access, broader D.C. police pursuit authority, or repeal of most reviewed D.C. policing restrictions.",
        "In this reviewed 119th-Congress sample, Foushee supported reporting and evidence, research, or implementation conditions in two independent episodes, while opposing three specific proposals concerning retired-service firearm access, broader D.C. police pursuit authority, and repeal of most reviewed D.C. policing restrictions.",
        "Certification, fentanyl research provisions, and officer-safety reporting",
        "Retired-service firearm access, D.C. pursuit authority, and policing-rule rollbacks",
        "Across independent episodes, Foushee opposed creating a reviewed federal program for eligible current and retired officers to buy qualifying retired agency firearms, broader D.C. police pursuit authority, and repeal of most reviewed D.C. policing restrictions.",
        "Within one fentanyl legislative episode, Foushee supported a certification amendment, opposed the earlier House bill, and supported a later related framework that permanently scheduled fentanyl-related substances and included research provisions. These related stages count as one episode for breadth and do not establish a change in position, motive, or philosophy.",
    }
    actual = {item["text"] for item in _all_mapped_text(wording)}
    assert expected <= actual
    joined = " ".join(actual).lower()
    assert "police tools" not in joined
    assert "expansion of a law-enforcement firearm purchase program" not in joined


def test_pending_receipt_template_binds_exact_candidate_and_cannot_authorize() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    artifact = compile_public_issue_presentation(compiled, authoring)
    receipt = json.loads(
        FOUSHEE_RECEIPT_TEMPLATE.read_text(encoding="utf-8")
    )
    assert receipt["binding"] == approval_subject_for_artifact(artifact)
    assert receipt["status"] == "human_approval_pending"
    assert receipt["approved_statement_ids"] == []
    assert receipt["approved_mapping_ids"] == []
    assert detached_receipt_matches(
        receipt,
        expected_subject=approval_subject_for_artifact(artifact),
    ) is False


def test_human_approval_receipt_matches_but_inactive_candidate_stays_private() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    artifact = compile_public_issue_presentation(compiled, authoring)
    receipt = json.loads(
        FOUSHEE_APPROVAL_RECEIPT.read_text(encoding="utf-8")
    )
    controls = artifact["controls"]
    assert controls["editorial"]["human_approval_status"] == "human_approved"
    assert controls["benchmark"]["status"] == "gold_benchmark"
    assert controls["production"]["eligible"] is True
    assert controls["publication"]["active"] is False
    assert controls["effective_public_tier"] == "receipts_only"
    assert detached_receipt_matches(
        receipt,
        expected_subject=approval_subject_for_artifact(artifact),
    )


def test_every_real_mapping_has_vote_and_action_meaning_sources() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    artifact = compile_public_issue_presentation(compiled, authoring)
    requirements = _trusted_contract(compiled, authoring)["actions"]
    for record in _all_mapped_text(artifact["editorial_wording"]):
        mapping_sources = set(record["mapping"]["source_refs"])
        for action_id in record["mapping"]["action_ids"]:
            requirement = requirements[action_id]
            assert set(requirement["vote_source_refs"]) <= mapping_sources
            assert set(
                requirement["action_meaning_source_refs"]
            ) <= mapping_sources


def test_missing_action_meaning_provenance_fails_validation() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    teaser_sources = authoring["editorial_wording"]["tier_display"][
        "reviewed_conclusion"
    ]["teaser"]["mapping"]["source_refs"]
    teaser_sources.remove("congress_hr2255_text")
    with pytest.raises(
        EditorialPresentationError,
        match="direct vote or action-meaning provenance",
    ):
        compile_public_issue_presentation(compiled, authoring)


def test_wording_mapping_and_controls_have_expected_digest_boundaries() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    baseline = _approval_subject(compiled, authoring)

    changed_wording = copy.deepcopy(authoring)
    changed_wording["editorial_wording"]["conclusion"]["body"]["text"] += " "
    wording_subject = _approval_subject(compiled, changed_wording)
    assert wording_subject["reviewed_wording_sha256"] != baseline[
        "reviewed_wording_sha256"
    ]
    assert wording_subject["approval_subject_sha256"] != baseline[
        "approval_subject_sha256"
    ]

    changed_mapping = copy.deepcopy(authoring)
    changed_mapping["editorial_wording"]["policy_trajectories"][0][
        "body"
    ]["mapping"]["source_refs"].reverse()
    mapping_subject = _approval_subject(compiled, changed_mapping)
    assert mapping_subject["mapping_set_sha256"] != baseline[
        "mapping_set_sha256"
    ]
    assert mapping_subject["approval_subject_sha256"] != baseline[
        "approval_subject_sha256"
    ]

    changed_controls = copy.deepcopy(authoring)
    changed_controls["controls"]["publication"]["active"] = True
    changed_controls["controls"]["production"]["eligible"] = True
    assert _approval_subject(compiled, changed_controls) == baseline


def test_detached_receipt_has_no_digest_cycle() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    authoring["controls"] = _approved_controls()
    artifact = compile_public_issue_presentation(compiled, authoring)
    subject_before = approval_subject_for_artifact(artifact)
    digest_before = artifact_digest(artifact)
    receipt = _approved_receipt(artifact)
    assert detached_receipt_matches(
        receipt,
        expected_subject=subject_before,
    )
    assert approval_subject_for_artifact(artifact) == subject_before
    assert artifact_digest(artifact) == digest_before


def test_trusted_action_source_contract_matches_governed_evidence() -> None:
    contract = json.loads(
        FOUSHEE_ACTION_SOURCE_CONTRACT.read_text(encoding="utf-8")
    )
    first_digest = validate_trusted_action_source_contract(contract)
    assert first_digest == validate_trusted_action_source_contract(
        json.loads(json.dumps(contract, sort_keys=True))
    )
    for key in ("source_manifest", "claim_source_map"):
        reference = contract[key]
        content = (ROOT / reference["path"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == reference["sha256"]
    manifest = json.loads(
        (ROOT / contract["source_manifest"]["path"]).read_text(encoding="utf-8")
    )
    source_types = {
        item["source_id"]: item["source_type"]
        for item in manifest["sources"]
    }
    claim_map = json.loads(
        (ROOT / contract["claim_source_map"]["path"]).read_text(encoding="utf-8")
    )
    claims = {item["roll"]: set(item["source_ids"]) for item in claim_map["claims"]}
    for action_id, requirement in contract["actions"].items():
        roll = int(action_id.rsplit(":", 1)[1])
        required_sources = {
            *requirement["vote_source_refs"],
            *requirement["action_meaning_source_refs"],
        }
        assert required_sources <= claims[roll]
        assert {
            source_types[source]
            for source in requirement["action_meaning_source_refs"]
        } >= set(requirement["required_action_meaning_source_types"])


def test_independent_contract_rejects_consistent_hr27_for_hr2255_attack() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    authoring["provenance"]["source_refs"].remove("congress_hr2255_text")
    for record in _all_mapped_text(authoring["editorial_wording"]):
        sources = record["mapping"]["source_refs"]
        if "congress_hr2255_text" in sources:
            sources.remove("congress_hr2255_text")
            if "congress_hr27" not in sources:
                sources.append("congress_hr27")
    with pytest.raises(
        EditorialPresentationError,
        match=(
            "direct vote or action-meaning provenance|"
            "not authorized for its exact actions"
        ),
    ):
        compile_public_issue_presentation(compiled, authoring)


@pytest.mark.parametrize(
    "replacement",
    ["congress_hamdt5", "clerk_roll_130", "unknown_official_source"],
)
def test_exact_action_contract_rejects_wrong_vote_only_or_unknown_source(
    replacement: str,
) -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    for record in _all_mapped_text(authoring["editorial_wording"]):
        if "congress_hr2255_text" in record["mapping"]["source_refs"]:
            record["mapping"]["source_refs"].remove("congress_hr2255_text")
            if replacement not in record["mapping"]["source_refs"]:
                record["mapping"]["source_refs"].append(replacement)
    if replacement == "unknown_official_source":
        authoring["provenance"]["source_refs"].append(replacement)
    with pytest.raises(
        EditorialPresentationError,
        match=(
            "direct vote or action-meaning provenance|"
            "not authorized for its exact actions"
        ),
    ):
        compile_public_issue_presentation(compiled, authoring)


def test_authoring_cannot_redefine_trusted_action_sources() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    authoring["provenance"]["action_source_requirements"] = {}
    with pytest.raises(
        EditorialPresentationError,
        match="exactly the permitted fields",
    ):
        compile_public_issue_presentation(compiled, authoring)


@pytest.mark.parametrize(
    "field",
    ["review_receipt", "approval_receipt", "reviewer_decisions", "extra"],
)
def test_provenance_is_closed_against_receipt_aliases_and_unknown_fields(
    field: str,
) -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    artifact = compile_public_issue_presentation(compiled, authoring)
    artifact["provenance"][field] = {"status": "approved"}
    with pytest.raises(
        EditorialPresentationError,
        match="exactly the permitted",
    ):
        validate_public_issue_presentation(artifact)


def test_required_provenance_and_detached_receipt_boundaries_fail_closed() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    artifact = compile_public_issue_presentation(compiled, authoring)
    receipt = _approved_receipt(artifact)
    assert b"approval-receipt:" not in artifact_bytes(artifact)
    changed = copy.deepcopy(artifact)
    changed["provenance"]["receipt_refs"][0] += ".changed"
    assert approval_subject_for_artifact(changed)["approval_subject_sha256"] != (
        receipt["binding"]["approval_subject_sha256"]
    )
    assert not detached_receipt_matches(
        receipt,
        expected_subject=approval_subject_for_artifact(changed),
    )
    del changed["provenance"]["semantic_source_case_id"]
    with pytest.raises(EditorialPresentationError):
        validate_public_issue_presentation(changed)


def test_receipt_requires_exact_canonical_limitations_and_durable_identity() -> None:
    compiled = _compiled("semir-dev-05-justice-mechanism-divide")
    authoring = json.loads(FOUSHEE_FIXTURE.read_text(encoding="utf-8"))
    artifact = compile_public_issue_presentation(compiled, authoring)
    subject = approval_subject_for_artifact(artifact)
    receipt = _approved_receipt(artifact)
    assert len(receipt["limitations_acknowledged"]) == 7
    assert detached_receipt_matches(receipt, expected_subject=subject)
    reordered = copy.deepcopy(receipt)
    reordered["limitations_acknowledged"].reverse()
    assert detached_receipt_matches(reordered, expected_subject=subject)
    for mutate in (
        lambda item: item.__setitem__("receipt_id", "not_supplied"),
        lambda item: item["limitations_acknowledged"].pop(),
        lambda item: item["limitations_acknowledged"].append({
            "limitation_id": "extra",
            "text": "Extra limitation.",
            "acknowledged": True,
        }),
        lambda item: item["limitations_acknowledged"][0].__setitem__(
            "text", "Changed text."
        ),
        lambda item: item["reviewer"].__setitem__("reviewer_id", "placeholder"),
        lambda item: item["reviewer"].__setitem__("authority", "unknown"),
        lambda item: item.__setitem__("decision_timestamp", "not-a-time"),
    ):
        candidate = copy.deepcopy(receipt)
        mutate(candidate)
        assert not detached_receipt_matches(candidate, expected_subject=subject)
    missing_timestamp = copy.deepcopy(receipt)
    del missing_timestamp["decision_timestamp"]
    assert not detached_receipt_matches(
        missing_timestamp,
        expected_subject=subject,
    )
    assert limitations_digest(
        list(reversed(artifact["provenance"]["review_limitations"]))
    ) == subject["limitations_sha256"]
