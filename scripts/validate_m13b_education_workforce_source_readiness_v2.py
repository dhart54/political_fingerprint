from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from jsonschema import Draft7Validator, FormatChecker
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    SourceReadinessError,
    _normalized_pdf_text,
    canonical_file_sha256,
    derive_readiness,
    load_json,
    sha256_file,
    sha256_json,
    validate_artifact,
    verify_operative_floor_text_pdf,
)
from backend.scripts.build_m13b_education_workforce_source_readiness_v2 import (  # noqa: E402
    ACTION_ID,
    CONTENT_VERIFICATION,
    M13A_ACTION_SET_SHA256,
    M13A_UNIVERSE_SUBJECT_SHA256,
    NEW_SOURCE_ID,
    NEW_SOURCE_PATH,
    NEW_SOURCE_SHA256,
    NEW_SOURCE_URL,
    OLD_SOURCE_ID,
    OLD_SOURCE_SHA256,
    RECEIPT_PATH,
    V1_FILE_SHA256,
    V1_ID,
    V1_PATH,
    V1_SUBJECT_SHA256,
    V2_ID,
    V2_PATH,
)
from scripts.validate_m12b_environment_energy_source_readiness import (  # noqa: E402
    validate_repository as validate_m12b,
)
from scripts.validate_m13a_universe_authority import (  # noqa: E402
    validate_repository as validate_m13a,
)


BASE = "e49d416b3549d87763e375079f742f7013c1c988"
EXPECTED_ARTIFACT_SHA256 = (
    "36cff9b3b5f3a7ad21579373c4437aad5c9c18aaf8d2f0874721695685899aa0"
)
EXPECTED_SUBJECT_SHA256 = (
    "aeecda1d7e883a6c03ac43c85e355812dffed1e74751e2bf1e4f8a0afb325ab0"
)
EXPECTED_CORRECTION_SUBJECT_SHA256 = (
    "d9a896caba1b62d9fed3d4beb44fb850e43f9f0886145a264c4ba3f55756c6d3"
)
SCHEMA_PATH = ROOT / (
    "docs/methodology/full_record_interpretation_source_readiness_v1.schema.json"
)
CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"
OLD_SOURCE_PATH = ROOT / (
    "docs/editorial/full_record_reviews/source_readiness/evidence/"
    f"f000477_education_119_v1/{OLD_SOURCE_SHA256}.pdf"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceReadinessError(message)


def roll19_record(artifact: dict[str, Any]) -> dict[str, Any]:
    matches = [
        row
        for row in artifact["subject"]["action_readiness"]
        if row["action_id"] == ACTION_ID
    ]
    require(len(matches) == 1, "roll 19 readiness record is not unique")
    return matches[0]


def operative_source(record: dict[str, Any]) -> dict[str, Any]:
    ids = record["source_roles"]["operative_content_interpretation_input"]
    require(ids == [NEW_SOURCE_ID], "roll 19 operative role is not corrected source")
    matches = [source for source in record["sources"] if source["source_id"] in ids]
    require(len(matches) == 1, "roll 19 corrected operative source is not unique")
    return matches[0]


def validate_roll19_content_contract(record: dict[str, Any]) -> None:
    source = operative_source(record)
    require(
        source.get("content_verification") == CONTENT_VERIFICATION,
        "roll 19 page/content verification metadata differs",
    )
    require(
        verify_operative_floor_text_pdf(source, repository_root=ROOT),
        "roll 19 governed raw PDF does not satisfy declared anchors",
    )
    roles = {
        item["evidence_role"] for item in source["content_verification"]["page_checks"]
    }
    require(
        {
            "exact_stage_adoption_and_operative_text_start",
            "operative_text_completion",
            "final_passage_resumption",
            "roll19_final_passage_disposition",
        }
        <= roles,
        "roll 19 required page roles are incomplete",
    )


def old_source_rejection_state(record: dict[str, Any]) -> str:
    mutated = deepcopy(record)
    source = operative_source(mutated)
    source["raw_provenance"] = {
        "governed_local_path": OLD_SOURCE_PATH.relative_to(ROOT).as_posix(),
        "sha256": OLD_SOURCE_SHA256,
    }
    source["neutral_projection"]["raw_provenance_sha256"] = OLD_SOURCE_SHA256
    source["neutral_projection_sha256"] = sha256_json(source["neutral_projection"])
    for key in (
        "readiness_criteria",
        "blocker_codes",
        "readiness_state",
        "source_packet_sha256",
    ):
        mutated.pop(key, None)
    return derive_readiness(mutated, repository_root=ROOT)[2]


def validate_repository() -> dict[str, Any]:
    m13a = validate_m13a()
    m12b = validate_m12b()
    artifact = load_json(V2_PATH)
    v1 = load_json(V1_PATH)
    receipt = load_json(RECEIPT_PATH)
    schema = load_json(SCHEMA_PATH)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(artifact),
        key=lambda error: list(error.absolute_path),
    )
    require(not errors, f"M13B v2 schema failed: {errors[0].message if errors else ''}")
    require(
        v1["artifact_id"] == V1_ID
        and canonical_file_sha256(V1_PATH) == V1_FILE_SHA256
        and v1["source_readiness_subject_sha256"] == V1_SUBJECT_SHA256,
        "historical M13B v1 identity changed",
    )
    require(
        artifact["artifact_id"] == V2_ID
        and canonical_file_sha256(V2_PATH) == EXPECTED_ARTIFACT_SHA256
        and artifact["source_readiness_subject_sha256"] == EXPECTED_SUBJECT_SHA256,
        "M13B v2 identity differs",
    )
    aggregate = validate_artifact(artifact, repository_root=ROOT)
    require(
        aggregate
        == {
            "total_action_count": 17,
            "ready_count": 17,
            "blocked_count": 0,
            "counts_by_readiness_state": {"ready_for_action_interpretation": 17},
        },
        "M13B v2 readiness aggregate differs",
    )
    subject = artifact["subject"]
    require(
        subject["action_set_sha256"]
        == m13a["accepted_action_set_sha256"]
        == M13A_ACTION_SET_SHA256
        and subject["universe_subject_sha256"] == M13A_UNIVERSE_SUBJECT_SHA256
        and len(subject["action_ids"]) == len(set(subject["action_ids"])) == 17,
        "M13A authority or membership changed",
    )
    record = roll19_record(artifact)
    require(
        record["house_action_stage"] == "final_passage_or_suspension_passage"
        and record["official_member_action"] == "nay"
        and record["readiness_state"] == "ready_for_action_interpretation",
        "roll 19 stage, member action, or readiness differs",
    )
    source = operative_source(record)
    require(
        source["source_url"] == NEW_SOURCE_URL
        and source["raw_provenance"]["sha256"] == NEW_SOURCE_SHA256
        and sha256_file(NEW_SOURCE_PATH) == NEW_SOURCE_SHA256
        and source["content_class"] == "operative_floor_text"
        and source["source_type"] == "congressional_record"
        and not any(
            item["content_class"]
            in {"operative_measure_text", "operative_resolution_text"}
            for item in record["sources"]
        ),
        "roll 19 source identity or no-substitution boundary differs",
    )
    validate_roll19_content_contract(record)
    old_reader = PdfReader(OLD_SOURCE_PATH)
    require(
        len(old_reader.pages) == 2
        and "h676" in _normalized_pdf_text(old_reader.pages[0].extract_text() or "")
        and "h677" in _normalized_pdf_text(old_reader.pages[1].extract_text() or "")
        and old_source_rejection_state(record) != "ready_for_action_interpretation",
        "defective old PDF was not rejected",
    )

    v1_by_id = {
        row["action_id"]: row
        for row in v1["subject"]["action_readiness"]
        if row["action_id"] != ACTION_ID
    }
    v2_by_id = {
        row["action_id"]: row
        for row in subject["action_readiness"]
        if row["action_id"] != ACTION_ID
    }
    require(
        len(v1_by_id) == len(v2_by_id) == 16
        and all(v1_by_id[action_id] == v2_by_id[action_id] for action_id in v1_by_id),
        "one or more non-roll-19 source packets changed",
    )
    require(
        receipt["correction_subject_sha256"]
        == sha256_json(receipt["subject"])
        == EXPECTED_CORRECTION_SUBJECT_SHA256
        and receipt["subject"]["historical_m13b_v1"][
            "m13b_v1_current_interpretation_readiness"
        ]
        == "superseded_due_to_incomplete_roll19_operational_source"
        and receipt["subject"]["defect"]["defective_source_id"] == OLD_SOURCE_ID
        and receipt["subject"]["defect"]["actual_coverage"] == "H676-H677"
        and receipt["subject"]["unchanged_source_packet_parity"][
            "unchanged_action_count"
        ]
        == 16,
        "correction/supersession receipt differs",
    )
    current = load_json(CURRENT_STATE_PATH)["active_source_readiness_milestone"]
    require(
        current["milestone"]
        == "m13b_education_workforce_source_readiness_v2_correction"
        and current["post_m13b_v1_merge_base"] == BASE
        and current["interpretation_source_readiness_identity"]["id"] == V2_ID
        and current["historical_m13b_v1"]["id"] == V1_ID
        and current["historical_m13b_v1"]["status"]
        == "superseded_due_to_incomplete_roll19_operational_source"
        and current["milestone_state"] == "completed_independent_review_accepted_merged"
        and current["accepted_pr"] == 164
        and current["accepted_head"] == "885b625333413b5e880808fda41937e9ff22abca"
        and current["post_merge_main"] == "9c675413b2b238bbc61d9daa1245636f6f5b161f"
        and current["historical_m13c_stop_reason"]
        == "house:119:2:19_operational_congressional_record_source_incomplete"
        and current["m13c_stop_resolution"]
        == "resolved_by_accepted_m13b_v2_complete_roll19_source"
        and all(
            value is False for value in current["downstream_authorizations"].values()
        ),
        "current-state correction boundary differs",
    )
    review_diff = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            BASE,
            "--",
            "docs/editorial/full_record_reviews",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    require(review_diff.returncode == 0, "protected historical diff inspection failed")
    allowed = (
        "docs/editorial/full_record_reviews/source_readiness/"
        "f000477_education_workforce_119_interpretation_source_readiness_v2",
        "docs/editorial/full_record_reviews/source_readiness/corrections/"
        "f000477_education_workforce_119_m13b_v1_supersession_v2.json",
        "docs/editorial/full_record_reviews/source_readiness/evidence/"
        "f000477_education_119_v2/",
        "docs/editorial/full_record_reviews/interpretation_candidates/"
        "f000477_education_workforce_119_v1/",
        "docs/editorial/full_record_reviews/interpretation_decisions/"
        "f000477_education_workforce_119_v1/",
        "docs/editorial/full_record_reviews/policy_episode_candidates/"
        "f000477_education_workforce_119_v1/",
        "docs/editorial/full_record_reviews/policy_episode_implementations/"
        "f000477_education_workforce_119_v1/",
        "docs/editorial/full_record_reviews/semantic_ir_candidates/"
        "f000477_education_workforce_119_v1/",
        "docs/editorial/full_record_reviews/semantic_ir_implementations/"
        "f000477_education_workforce_119_v1/",
        "docs/editorial/full_record_reviews/synthesis_candidates/"
        "f000477_education_workforce_119_v1/",
        "docs/editorial/full_record_reviews/synthesis_implementations/"
        "f000477_education_workforce_119_v1/",
        "docs/editorial/full_record_reviews/public_wording_candidates/"
        "f000477_education_workforce_119_v1/",
        "docs/editorial/full_record_reviews/public_wording_implementations/"
        "f000477_education_workforce_119_v1/",
        "docs/editorial/full_record_reviews/site_integration_candidates/"
        "f000477_education_workforce_119_v1/",
        "docs/editorial/full_record_reviews/publication_activation_candidates/"
        "f000477_education_workforce_119_v1/",
    )
    require(
        all(path.startswith(allowed) for path in review_diff.stdout.splitlines()),
        "protected Justice, National Security, Environment, or M13B v1 artifact changed",
    )
    require(
        m12b["total_action_count"] == 63
        and m12b["ready_count"] == 63
        and m12b["blocked_count"] == 0,
        "M12B Environment compatibility changed",
    )
    return {
        "status": "pass",
        "artifact_id": V2_ID,
        "artifact_sha256": EXPECTED_ARTIFACT_SHA256,
        "source_readiness_subject_sha256": EXPECTED_SUBJECT_SHA256,
        "ready_count": 17,
        "blocked_count": 0,
        "corrected_source_id": NEW_SOURCE_ID,
        "corrected_source_sha256": NEW_SOURCE_SHA256,
        "old_pdf_actual_page_count": 2,
        "old_source_rejected": True,
        "unchanged_source_packet_count": 16,
        "correction_receipt_id": receipt["receipt_id"],
        "correction_subject_sha256": EXPECTED_CORRECTION_SUBJECT_SHA256,
        "m12b_backward_compatibility": "63_actions_63_ready_0_blocked_passed",
    }


def main() -> int:
    try:
        print(json.dumps(validate_repository(), sort_keys=True))
    except (SourceReadinessError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
