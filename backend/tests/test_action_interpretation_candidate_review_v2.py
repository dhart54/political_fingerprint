from __future__ import annotations

from copy import deepcopy
import json

import pytest
from jsonschema import Draft7Validator

from scripts.build_action_interpretation_candidate_review_v2 import (
    BATCH_ID,
    OUTPUT_ROOT,
    SCHEMA_ROOT,
    _sha256,
    build_freeze,
    build_post_freeze,
)
from scripts.validate_action_interpretation_candidate_review_v2 import (
    CandidateReviewV2ValidationError,
    validate,
    validate_parity,
)


def _load(name: str) -> dict[str, object]:
    return json.loads((OUTPUT_ROOT / name).read_text(encoding="utf-8"))


def _reseal(value: dict[str, object]) -> dict[str, object]:
    value = deepcopy(value)
    value.pop("content_subject_sha256", None)
    value["content_subject_sha256"] = _sha256(value)
    return value


def test_v2_bundle_validates_end_to_end() -> None:
    result = validate()
    assert result["status"] == "pass"
    assert result["action_count"] == 37
    assert result["title_only_exception_count"] == 0


def test_v2_freeze_and_post_freeze_are_deterministic() -> None:
    batch = build_freeze(check=True)
    post = build_post_freeze(check=True)
    assert batch["batch_id"] == BATCH_ID
    assert post["parity"]["parity_state"] == "pass"


@pytest.mark.parametrize(
    "artifact_name",
    [
        "benchmark_comparison.json",
        "sample_manifest.json",
        "human_decision_template.json",
    ],
)
def test_parity_rejects_final_artifact_modified_after_dossier(
    artifact_name: str,
) -> None:
    path = OUTPUT_ROOT / artifact_name
    mutated = path.read_bytes() + b" "
    with pytest.raises(
        CandidateReviewV2ValidationError, match="final file SHA-256 mismatch"
    ):
        validate_parity(
            byte_overrides={
                str(
                    path.relative_to(OUTPUT_ROOT.parent.parent.parent.parent.parent)
                ).replace("\\", "/"): mutated
            }
        )


def test_parity_rejects_content_digest_substituted_for_final_file_digest() -> None:
    parity = _load("parity_manifest.json")
    parity["canonical_artifacts"][0]["file_sha256"] = parity["canonical_artifacts"][0][
        "content_subject_sha256"
    ]
    parity = _reseal(parity)
    with pytest.raises(
        CandidateReviewV2ValidationError, match="final file SHA-256 mismatch"
    ):
        validate_parity(parity_override=parity)


def test_parity_rejects_mixed_digest_conventions() -> None:
    parity = _load("parity_manifest.json")
    parity["canonical_artifacts"][0]["artifact_sha256"] = parity["canonical_artifacts"][
        0
    ]["content_subject_sha256"]
    parity = _reseal(parity)
    with pytest.raises(
        CandidateReviewV2ValidationError, match="mixed digest convention"
    ):
        validate_parity(parity_override=parity)


def test_closed_candidate_schema_rejects_unknown_nested_field() -> None:
    batch = _load("candidate_batch.json")
    batch["final_candidates"][0]["material_provisions"][0]["unknown"] = True
    schema = json.loads(
        (SCHEMA_ROOT / "candidate_batch_v2.schema.json").read_text(encoding="utf-8")
    )
    errors = list(Draft7Validator(schema).iter_errors(batch))
    assert errors
    assert any(
        "Additional properties are not allowed" in error.message for error in errors
    )


def test_roll_155_conflict_and_roll_278_no_safe_are_preserved() -> None:
    candidates = {
        row["action_id"]: row
        for row in _load("candidate_batch.json")["final_candidates"]
    }
    roll155 = candidates["house:119:2:155"]
    assert roll155["status"] == "ambiguous"
    assert roll155["source_identity_reconciliation"]["dublin_core_title"].startswith(
        "110 S4465 ES"
    )
    assert roll155["source_identity_reconciliation"]["structured_congress"] == (
        "119th CONGRESS"
    )
    assert roll155["source_identity_reconciliation"]["structured_legis_num"] == (
        "S. 4465"
    )
    roll278 = candidates["house:119:2:278"]
    assert roll278["status"] == "no_safe_candidate"
    assert roll278["proposed_exact_action_meaning"] is None


def test_candidate_bundle_is_non_authorizing_and_unfilled() -> None:
    batch = _load("candidate_batch.json")
    decision = _load("human_decision_template.json")
    assert batch["accepted"] is False
    assert batch["canonical_review_state"] is False
    assert batch["production_selector_eligible"] is False
    assert decision["unfilled"] is True
    assert decision["top_level_decision"] is None
