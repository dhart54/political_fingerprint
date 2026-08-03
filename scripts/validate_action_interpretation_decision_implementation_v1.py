"""Independently verify the detached M3B-B decision implementation."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from backend.app.etl.universe_authority import content_digest_matches  # noqa: E402

from build_action_interpretation_decision_implementation_v1 import (  # noqa: E402
    AUTHORITY_CONTENT_SHA256,
    AUTHORITY_FILE_SHA256,
    AUTHORITY_ID,
    AUTHORITY_MARKDOWN_FILE_SHA256,
    AUTHORITY_MARKDOWN_PATH,
    AUTHORITY_PATH,
    DECISION_ROOT,
    IMPLEMENTATION_ID,
    MAPPING_ID,
    OUTPUT_NAMES,
    PREPARATION_PATH,
    REVIEWER_AUTHORITY,
    REVIEWER_IDENTITY,
    SCHEMA_ROOT,
    STATE_BY_DECISION,
    V4_ROOT,
    build,
    digest,
    load,
    preflight,
)


class ImplementationValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ImplementationValidationError(message)


def verify_seal(value: dict[str, Any], label: str) -> None:
    subject = {
        key: child for key, child in value.items() if key != "content_subject_sha256"
    }
    require(
        value.get("content_subject_sha256") == digest(subject),
        f"{label}: content-subject digest mismatch",
    )


def _expected_record(
    decision: dict[str, Any], unit: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    selected = decision["selected_decision"]
    return {
        "action_id": decision["action_id"],
        "candidate_id": candidate["candidate_id"],
        "candidate_content_subject_sha256": candidate[
            "candidate_content_subject_sha256"
        ],
        "candidate_exact_action_meaning": candidate["proposed_exact_action_meaning"],
        "candidate_exact_choice_position_effect": candidate[
            "proposed_member_position_effect"
        ],
        "decision_unit_id": unit["decision_unit_id"],
        "decision_unit_content_subject_sha256": unit["content_subject_sha256"],
        "authority_artifact_id": AUTHORITY_ID,
        "authority_artifact_content_subject_sha256": AUTHORITY_CONTENT_SHA256,
        "authority_decision_content_subject_sha256": decision["content_subject_sha256"],
        "selected_decision": selected,
        "implementation_state": STATE_BY_DECISION[selected],
        "implemented_interpretation_status": "ambiguous"
        if selected == "preserve_ambiguous"
        else "no_safe_candidate"
        if selected == "preserve_no_safe_candidate"
        else "internally_implemented",
        "implemented_exact_action_meaning": decision["accepted_exact_action_meaning"],
        "implemented_exact_choice_position_effect": decision[
            "accepted_exact_choice_position_effect"
        ],
        "implemented_confidence": decision["confidence_decision"],
        "implemented_limitations": decision["accepted_limitations"],
        "implemented_competing_interpretation": decision[
            "accepted_competing_interpretation"
        ],
        "unresolved_question": decision["unresolved_question"],
        "required_wording_or_field_revisions": decision[
            "required_wording_or_field_revisions"
        ],
        "secondary_detail_decisions": decision["secondary_detail_decisions"],
        "source_references": unit["source_references"],
        "evidence_map_id": unit["evidence_map_id"],
        "evidence_map_content_subject_sha256": unit[
            "evidence_map_content_subject_sha256"
        ],
        "related_action_contrast_groups": unit["sample_memberships"]["contrast_groups"],
        "cross_domain_limitations": candidate["cross_domain_limitations"],
    }


def validate_values(values: dict[str, dict[str, Any]]) -> dict[str, Any]:
    authority = load(AUTHORITY_PATH)
    preparation = load(PREPARATION_PATH)
    v4 = load(V4_ROOT / "candidate_batch.json")
    decisions = {row["action_id"]: row for row in authority["decisions"]}
    units = {row["action_id"]: row for row in preparation["decision_units"]}
    candidates = {row["action_id"]: row for row in v4["final_candidates"]}
    bundle = values["decision_implementation_bundle.json"]
    mapping = values["delegated_authority_mapping.json"]
    risk = values["launch_review_risk_register.json"]
    calibration = values["launch_calibration_population.json"]

    require(
        bundle["artifact_id"] == IMPLEMENTATION_ID,
        "implementation bundle identity differs",
    )
    records = bundle["implementation_records"]
    ids = [row["action_id"] for row in records]
    require(
        len(records) == 37 and bundle["implementation_record_count"] == 37,
        "implementation completeness differs",
    )
    require(len(set(ids)) == 37, "implementation action duplicated")
    require(
        set(ids) == set(decisions) == set(units) == set(candidates),
        "approved-universe membership differs",
    )
    require(ids == sorted(ids), "implementation action ordering differs")
    for row in records:
        action_id = row["action_id"]
        expected = _expected_record(
            decisions[action_id], units[action_id], candidates[action_id]
        )
        for key, wanted in expected.items():
            require(
                row.get(key) == wanted,
                f"{action_id}: independently recomputed {key} differs",
            )
        require(
            row["canonical"] is False
            and row["public"] is False
            and row["publication_authorized"] is False,
            f"{action_id}: canonical/public status asserted",
        )
        require(
            row["delegated_editorial_acceptance_state"]
            == "delegated_editorial_acceptance_pending"
            and row["launch_ratification_state"] == "launch_ratification_pending",
            f"{action_id}: acceptance boundary differs",
        )
    counts = dict(
        sorted(Counter(row["implementation_state"] for row in records).items())
    )
    require(
        counts
        == {
            "implemented_accepted_candidate": 32,
            "implemented_accepted_with_revision": 2,
            "implemented_preserved_ambiguous": 2,
            "implemented_preserved_no_safe_candidate": 1,
        },
        "implementation accounting is not 32/2/2/1",
    )
    require(
        bundle["implementation_accounting"] == counts,
        "asserted implementation accounting differs",
    )
    unchanged = [
        row for row in records if row["selected_decision"] == "accept_candidate"
    ]
    for row in unchanged:
        candidate = candidates[row["action_id"]]
        require(
            row["implemented_exact_action_meaning"]
            == candidate["proposed_exact_action_meaning"]
            and row["implemented_exact_choice_position_effect"]
            == candidate["proposed_member_position_effect"]
            and row["implemented_confidence"] == candidate["confidence"],
            f"{row['action_id']}: unchanged acceptance differs from V4",
        )
        added_limit_count = sum(
            detail["decision"] == "include_as_accepted_limitation"
            for detail in row["secondary_detail_decisions"]
        )
        require(
            row["implemented_limitations"][: len(candidate["limitations"])]
            == candidate["limitations"]
            and len(row["implemented_limitations"])
            == len(candidate["limitations"]) + added_limit_count,
            f"{row['action_id']}: limitations differ beyond delegated secondary-detail additions",
        )
    by_id = {row["action_id"]: row for row in records}
    require(
        "five years" in by_id["house:119:1:27"]["implemented_exact_action_meaning"],
        "roll 27 five-year maximum omitted",
    )
    require(
        "seven years" in by_id["house:119:2:157"]["implemented_exact_action_meaning"],
        "roll 157 seven-year sunset omitted",
    )
    require(
        by_id["house:119:1:128"]["implemented_interpretation_status"] == "ambiguous"
        and "any magazine and" in by_id["house:119:1:128"]["unresolved_question"],
        "roll 128 uncertainty removed",
    )
    require(
        by_id["house:119:2:155"]["implemented_interpretation_status"] == "ambiguous"
        and "110th/119th" in by_id["house:119:2:155"]["unresolved_question"],
        "roll 155 metadata conflict removed",
    )
    require(
        by_id["house:119:2:278"]["implemented_exact_action_meaning"] is None
        and by_id["house:119:2:278"]["implemented_interpretation_status"]
        == "no_safe_candidate",
        "roll 278 received unsupported prose",
    )
    for action_id, marker in (
        ("house:119:2:218", "$10,000,000"),
        ("house:119:2:240", "90 days"),
    ):
        require(
            marker in " ".join(by_id[action_id]["implemented_limitations"]),
            f"{action_id}: accepted limitations removed",
        )
    details = [
        detail for row in records for detail in row["secondary_detail_decisions"]
    ]
    detail_counts = dict(
        sorted(Counter(detail["decision"] for detail in details).items())
    )
    require(
        bundle["secondary_detail_decision_count"] == len(details) == 30,
        "secondary-detail count differs",
    )
    require(
        detail_counts
        == {
            "include_as_accepted_limitation": 6,
            "include_in_revised_meaning": 2,
            "safely_compressed": 22,
        },
        "secondary-detail accounting differs",
    )
    require(
        bundle["secondary_detail_decision_accounting"] == detail_counts,
        "asserted secondary-detail accounting differs",
    )
    require(
        bundle["accepted_limitation_count"]
        == sum(len(row["implemented_limitations"]) for row in records),
        "accepted-limitation accounting differs",
    )
    require(
        mapping["artifact_id"] == MAPPING_ID and mapping["not_user_signature"] is True,
        "successor authority mapping differs",
    )
    require(
        mapping["delegated_decision_maker"]
        == {
            "reviewer_identity": REVIEWER_IDENTITY,
            "reviewer_authority": REVIEWER_AUTHORITY,
        },
        "reviewer identity changed",
    )
    require(
        mapping["authority_record"]["content_subject_sha256"]
        == AUTHORITY_CONTENT_SHA256
        and mapping["authority_record"]["final_file_sha256"] == AUTHORITY_FILE_SHA256,
        "authority-record digest changed",
    )
    require(
        mapping["launch_ratification_state"] == "launch_ratification_pending"
        and mapping["publication_authorized"] is False,
        "mapping grants launch/publication authority",
    )
    risk_ids = [row["risk_id"] for row in risk["entries"]]
    require(
        risk["entry_count"] == len(risk_ids) == len(set(risk_ids)),
        "risk-register accounting differs",
    )
    require(
        {row["subject"]["action_id"] for row in risk["entries"]}
        >= {"house:119:1:128", "house:119:2:155", "house:119:2:278"},
        "unresolved launch risk omitted",
    )
    require(
        calibration["sample_selected"] is False
        and calibration["selected_sample"] == [],
        "calibration sample selected prematurely",
    )
    require(
        calibration["eligible_count"] == len(calibration["eligible_items"]) == 34,
        "calibration eligibility population differs",
    )
    require(
        all(
            row["action_id"]
            not in {"house:119:1:128", "house:119:2:155", "house:119:2:278"}
            for row in calibration["eligible_items"]
        ),
        "held risk entered calibration population",
    )
    for value in values.values():
        verify_seal(value, value.get("artifact_id", "artifact"))
    forbidden = (
        "accepted_semantic_reference",
        "human_reviewed",
        '"canonical":true',
        '"public":true',
        '"publication_authorized":true',
    )
    corpus = json.dumps(
        values, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    require(
        not any(marker in corpus for marker in forbidden),
        "canonical/public or forbidden acceptance status asserted",
    )
    return {
        "action_count": 37,
        "accounting": counts,
        "risk_count": risk["entry_count"],
        "calibration_eligible_count": calibration["eligible_count"],
    }


def validate_parity(
    *,
    byte_overrides: dict[str, bytes] | None = None,
    markdown_override: str | None = None,
) -> None:
    overrides = byte_overrides or {}
    parity = load(DECISION_ROOT / "implementation_parity_manifest.json")
    verify_seal(parity, "implementation parity manifest")
    require(
        parity["parity_state"] == "pass" and parity["generated_last"] is True,
        "parity state differs",
    )
    require(
        parity["imported_authority"]["content_subject_sha256"]
        == AUTHORITY_CONTENT_SHA256,
        "parity authority content digest differs",
    )
    require(
        parity["imported_authority"]["final_file_sha256"] == AUTHORITY_FILE_SHA256,
        "parity authority final-byte digest differs",
    )
    require(
        content_digest_matches(
            AUTHORITY_MARKDOWN_PATH.read_bytes(),
            AUTHORITY_MARKDOWN_FILE_SHA256,
            suffix=AUTHORITY_MARKDOWN_PATH.suffix,
        ),
        "authority companion Markdown final bytes differ",
    )
    for item in parity["referenced_artifacts"]:
        path = ROOT / item["path"]
        raw = overrides.get(item["path"], path.read_bytes())
        require(
            content_digest_matches(
                raw,
                item["final_file_sha256"],
                suffix=Path(item["path"]).suffix,
            ),
            f"{item['path']}: stale final-file hash",
        )
        if "content_subject_sha256" in item:
            value = json.loads(raw.decode("utf-8"))
            require(
                value["content_subject_sha256"] == item["content_subject_sha256"],
                f"{item['path']}: stale content-subject hash",
            )
    markdown = (
        markdown_override
        if markdown_override is not None
        else (DECISION_ROOT / "decision_implementation_dossier.md").read_text(
            encoding="utf-8"
        )
    )
    bundle = load(DECISION_ROOT / "decision_implementation_bundle.json")
    for row in bundle["implementation_records"]:
        require(
            row["action_id"] in markdown
            and str(row["implemented_exact_action_meaning"]) in markdown,
            f"{row['action_id']}: Markdown differs from JSON",
        )
    require(
        "delegated_authority_accepts_implementation" in markdown,
        "Markdown final decision request differs",
    )


def validate() -> dict[str, Any]:
    preflight()
    values = {name: load(DECISION_ROOT / name) for name in OUTPUT_NAMES}
    authority_schema = load(SCHEMA_ROOT / "authority_decisions_v1.schema.json")
    authority_errors = list(
        Draft7Validator(authority_schema).iter_errors(load(AUTHORITY_PATH))
    )
    require(
        not authority_errors,
        f"authority schema failure: {authority_errors[0].message if authority_errors else ''}",
    )
    for name, value in values.items():
        schema = load(SCHEMA_ROOT / name.replace(".json", "_v1.schema.json"))
        Draft7Validator.check_schema(schema)
        errors = list(Draft7Validator(schema).iter_errors(value))
        require(
            not errors, f"{name}: schema failure: {errors[0].message if errors else ''}"
        )
    parity = load(DECISION_ROOT / "implementation_parity_manifest.json")
    parity_schema = load(SCHEMA_ROOT / "implementation_parity_manifest_v1.schema.json")
    errors = list(Draft7Validator(parity_schema).iter_errors(parity))
    require(not errors, f"parity schema failure: {errors[0].message if errors else ''}")
    result = validate_values(values)
    validate_parity()
    build(check=True)
    tracked_runtime = subprocess.check_output(
        ["git", "ls-files", "backend/app", "frontend"], cwd=ROOT, text=True
    ).splitlines()
    require(
        not any(
            IMPLEMENTATION_ID.encode() in (ROOT / path).read_bytes()
            for path in tracked_runtime
            if Path(path).suffix in {".py", ".ts", ".tsx", ".js", ".json"}
        ),
        "implementation entered runtime/public selectors",
    )
    review_state = (
        ROOT
        / "docs/editorial/full_record_reviews/f000477_justice_public_safety_119_review_state_v1.json"
    )
    require(
        IMPLEMENTATION_ID.encode() not in review_state.read_bytes(),
        "canonical review state changed",
    )
    return {
        "status": "pass",
        "bundle_id": IMPLEMENTATION_ID,
        **result,
        "parity_state": "pass",
    }


def main() -> int:
    print(json.dumps(validate(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
