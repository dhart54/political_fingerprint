"""Independently verify M4B episode implementation against governed inputs."""

from __future__ import annotations

from collections import Counter
import copy
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from backend.app.etl.universe_authority import (  # noqa: E402
    content_digest_matches,
    file_digest_matches,
)

from build_policy_episode_decision_implementation_v1 import (  # noqa: E402
    ACCEPTANCE_CONTENT_SHA256,
    ACCEPTANCE_FILE_SHA256,
    ACCEPTANCE_ID,
    ACCEPTANCE_OUTPUT,
    ACCEPTANCE_SOURCE,
    CANDIDATE_PATH,
    IMPLEMENTATION_ID,
    JSON_NAMES,
    M3BB_PATH,
    M4A_CALIBRATION_PATH,
    M4A_RISK_PATH,
    OUTPUT_ROOT,
    ROOT,
    SCHEMA_ROOT,
    build,
    digest,
    load,
    preflight,
)


class EpisodeImplementationValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EpisodeImplementationValidationError(message)


def verify_seal(value: dict[str, Any], label: str) -> None:
    subject = {
        key: child for key, child in value.items() if key != "content_subject_sha256"
    }
    require(
        value.get("content_subject_sha256") == digest(subject),
        f"{label}: content-subject SHA-256 differs",
    )


def expected_record_fields(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "internal_neutral_label": candidate["internal_neutral_label"],
        "neutral_policy_question": candidate["neutral_policy_question"],
        "issue_id": candidate["issue_id"],
        "congress": candidate["congress"],
        "chamber": candidate["chamber"],
        "primary_action_ids": candidate["primary_action_ids"],
        "chronological_action_sequence": candidate["chronological_action_sequence"],
        "action_roles": [
            {"action_id": row["action_id"], "action_role": row["action_role"]}
            for row in candidate["chronological_action_sequence"]
        ],
        "exact_action_interpretation_references": candidate[
            "source_and_interpretation_references"
        ],
        "relationship_rationale": candidate["relationship_rationale"],
        "material_policy_continuity": candidate["material_policy_continuity"],
        "material_policy_differences": candidate["material_policy_differences"],
        "implemented_episode_scope": candidate["candidate_episode_scope"],
        "implemented_episode_level_behavior": candidate[
            "candidate_episode_level_behavior"
        ],
        "behavior_derivation": candidate["behavior_derivation"],
        "confidence": candidate["confidence"],
        "limitations": candidate["limitations"],
        "competing_plausible_episode_groupings": candidate[
            "competing_plausible_episode_groupings"
        ],
        "unresolved_editorial_questions": candidate["unresolved_editorial_questions"],
    }


def validate_artifacts(
    values: dict[str, dict[str, Any]],
    *,
    acceptance_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    acceptance = acceptance_override or load(ACCEPTANCE_SOURCE)
    candidates = load(CANDIDATE_PATH)
    action_implementation = load(M3BB_PATH)
    prior_risk = load(M4A_RISK_PATH)
    prior_calibration = load(M4A_CALIBRATION_PATH)
    bundle = values["episode_implementation_bundle.json"]
    risk = values["launch_review_risk_register.json"]
    calibration = values["episode_calibration_population.json"]
    report = values["implementation_parity_report.json"]
    decision_template = values["delegated_authority_decision_template.json"]

    verify_seal(acceptance, "delegated M4A acceptance")
    require(
        acceptance["artifact_id"] == ACCEPTANCE_ID
        and acceptance["content_subject_sha256"] == ACCEPTANCE_CONTENT_SHA256,
        "delegated M4A acceptance identity differs",
    )
    acceptance_decision = acceptance["decision"]
    require(
        acceptance_decision["decision"]
        == "delegated_authority_accepts_episode_candidates"
        and acceptance_decision["not_user_signature"] is True
        and acceptance_decision["reviewer_identity"]
        == "chatgpt:political_fingerprint_authority_thread"
        and acceptance_decision["reviewer_authority"]
        == "delegated_product_methodology_editorial_authority_v1",
        "delegated decision or reviewer boundary differs",
    )
    delegated_by_id = {
        row["episode_id"]: row for row in acceptance_decision["episode_decisions"]
    }
    require(
        len(delegated_by_id) == 32
        and all(
            row["decision"] == "delegated_authority_accepts_episode_candidate"
            for row in delegated_by_id.values()
        ),
        "recommendation or revision substituted for delegated acceptance",
    )

    verify_seal(bundle, "episode implementation bundle")
    require(
        bundle["artifact_id"] == IMPLEMENTATION_ID
        and bundle["episode_count"] == 32
        and bundle["single_action_episode_count"] == 30
        and bundle["multi_action_episode_count"] == 2,
        "implementation identity or 32/30/2 accounting differs",
    )
    candidate_by_id = {row["episode_id"]: row for row in candidates["episodes"]}
    implemented_by_id = {
        row["episode_id"]: row for row in bundle["implemented_episodes"]
    }
    require(
        len(candidate_by_id) == len(implemented_by_id) == 32
        and set(candidate_by_id) == set(implemented_by_id) == set(delegated_by_id),
        "missing, extra, or changed episode ID",
    )
    action_impl_by_id = {
        row["action_id"]: row for row in action_implementation["implementation_records"]
    }
    primary_membership: dict[str, str] = {}
    for episode_id, candidate in candidate_by_id.items():
        verify_seal(candidate, f"candidate {episode_id}")
        implemented = implemented_by_id[episode_id]
        verify_seal(implemented, f"implemented episode {episode_id}")
        require(
            delegated_by_id[episode_id]["episode_content_subject_sha256"]
            == candidate["content_subject_sha256"]
            == implemented["candidate_episode_content_subject_sha256"],
            f"{episode_id}: candidate or delegated digest differs",
        )
        require(
            implemented["delegated_acceptance_artifact_id"] == ACCEPTANCE_ID
            and implemented["delegated_acceptance_content_subject_sha256"]
            == ACCEPTANCE_CONTENT_SHA256
            and implemented["delegated_acceptance_decision"]
            == "delegated_authority_accepts_episode_candidate",
            f"{episode_id}: delegated acceptance binding differs",
        )
        expected = expected_record_fields(candidate)
        for key, expected_value in expected.items():
            require(
                implemented[key] == expected_value,
                f"{episode_id}: unauthorized episode revision in {key}",
            )
        require(
            implemented["record_id"]
            == f"policy-episode-decision-implementation:{episode_id}:v1"
            and implemented["implementation_state"]
            == "implemented_delegated_episode_candidate",
            f"{episode_id}: implementation state differs",
        )
        require(
            implemented["candidate_episode_delegated_accepted"] is True
            and implemented["implementation_accepted"] is False
            and implemented["canonical"] is False
            and implemented["public"] is False
            and implemented["published"] is False
            and implemented["persisted"] is False
            and implemented["authorizing"] is False,
            f"{episode_id}: implementation authority boundary differs",
        )
        for action in implemented["chronological_action_sequence"]:
            action_id = action["action_id"]
            require(
                action_id not in primary_membership,
                f"{action_id}: duplicate primary episode membership",
            )
            primary_membership[action_id] = episode_id
            source = action_impl_by_id[action_id]
            require(
                action["implementation_record_content_subject_sha256"]
                == source["content_subject_sha256"]
                and action["implemented_exact_action_meaning"]
                == source["implemented_exact_action_meaning"]
                and action["implemented_exact_choice_position_effect"]
                == source["implemented_exact_choice_position_effect"]
                and action["official_member_action"]
                == source["official_member_action"],
                f"{action_id}: action interpretation meaning differs",
            )

    accounting = bundle["action_accounting"]
    accounting_by_id = {row["action_id"]: row for row in accounting}
    candidate_accounting_by_id = {
        row["action_id"]: row for row in candidates["action_accounting"]
    }
    require(
        len(accounting) == len(accounting_by_id) == 37
        and set(accounting_by_id) == set(candidate_accounting_by_id),
        "37-action accounting differs",
    )
    for action_id, source in candidate_accounting_by_id.items():
        row = accounting_by_id[action_id]
        verify_seal(row, f"accounting {action_id}")
        require(
            row["candidate_accounting_content_subject_sha256"]
            == source["content_subject_sha256"]
            and row["primary_accounting_state"] == source["primary_accounting_state"]
            and row["primary_episode_id"] == source["primary_episode_id"]
            and row["related_episode_ids"] == source["related_candidate_episode_ids"]
            and row["action_interpretation_record_content_subject_sha256"]
            == action_impl_by_id[action_id]["content_subject_sha256"],
            f"{action_id}: action accounting drift",
        )
        episode_id = row["primary_episode_id"]
        if row["primary_accounting_state"] == "assigned_primary_episode":
            episode = implemented_by_id[episode_id]
            require(
                primary_membership.get(action_id) == episode_id
                and row["implemented_episode_record_id"] == episode["record_id"]
                and row["implemented_episode_content_subject_sha256"]
                == episode["content_subject_sha256"]
                and row["counts_toward_episode_behavior"] is True,
                f"{action_id}: primary implementation binding differs",
            )
        else:
            require(
                action_id not in primary_membership
                and episode_id is None
                and row["implemented_episode_record_id"] is None
                and row["implemented_episode_content_subject_sha256"] is None
                and row["counts_toward_episode_behavior"] is False,
                f"{action_id}: non-counting state contributes to an episode",
            )
    counts = dict(
        sorted(Counter(row["primary_accounting_state"] for row in accounting).items())
    )
    require(
        counts
        == {
            "assigned_primary_episode": 35,
            "retained_ambiguous_episode_assignment": 1,
            "unassigned_no_safe_interpretation": 1,
        }
        and bundle["action_accounting_counts"] == counts,
        "35/1/1 action accounting differs",
    )

    require(
        implemented_by_id["laken-riley-detention-enforcement"]["primary_action_ids"]
        == ["house:119:1:6", "house:119:1:23"]
        and implemented_by_id["laken-riley-detention-enforcement"]["confidence"]
        == "medium"
        and implemented_by_id["laken-riley-detention-enforcement"][
            "implemented_episode_level_behavior"
        ]
        == "opposes_episode_direction",
        "Laken Riley versions were split or changed",
    )
    require(
        implemented_by_id["halt-fentanyl-legislative-path"]["primary_action_ids"]
        == ["house:119:1:32", "house:119:1:33", "house:119:1:166"]
        and [
            row["action_role"]
            for row in implemented_by_id["halt-fentanyl-legislative-path"][
                "chronological_action_sequence"
            ]
        ]
        == ["amendment", "initial_passage", "later_version"]
        and implemented_by_id["halt-fentanyl-legislative-path"][
            "implemented_episode_level_behavior"
        ]
        == "mixed_actions",
        "HALT Fentanyl path was split, flattened, or changed",
    )
    require(
        implemented_by_id["dc-youth-offender-sentencing"]["primary_action_ids"]
        == ["house:119:1:270"]
        and implemented_by_id["dc-juvenile-court-transfer-age"]["primary_action_ids"]
        == ["house:119:1:271"],
        "D.C. juvenile actions were recombined",
    )
    roll_155 = accounting_by_id["house:119:2:155"]
    require(
        roll_155["primary_accounting_state"] == "retained_ambiguous_episode_assignment"
        and roll_155["related_episode_ids"] == ["fisa-title-vii-short-term-extension"]
        and implemented_by_id["fisa-title-vii-short-term-extension"][
            "primary_action_ids"
        ]
        == ["house:119:2:221"]
        and not roll_155["counts_toward_episode_behavior"],
        "roll 155 was assigned, counted, or normalized",
    )
    roll_278 = accounting_by_id["house:119:2:278"]
    require(
        roll_278["primary_accounting_state"] == "unassigned_no_safe_interpretation"
        and roll_278["primary_episode_id"] is None
        and not roll_278["counts_toward_episode_behavior"],
        "roll 278 was assigned or interpreted",
    )

    verify_seal(risk, "M4B launch-risk successor")
    require(
        risk["entry_count"] == len(risk["entries"]) == 8
        and risk["carried_entry_count"] == 8
        and risk["updated_entry_count"] == 1
        and risk["entries"][:7] == prior_risk["entries"][:7],
        "launch-risk continuity differs",
    )
    source_fisa_risk = copy.deepcopy(prior_risk["entries"][-1])
    successor_fisa_risk = copy.deepcopy(risk["entries"][-1])
    verify_seal(successor_fisa_risk, "FISA grouping risk successor")
    source_fisa_risk.pop("content_subject_sha256")
    successor_fisa_risk.pop("content_subject_sha256")
    source_history = source_fisa_risk.pop("resolution_history")
    successor_history = successor_fisa_risk.pop("resolution_history")
    source_fisa_risk.pop("delegated_authority_disposition")
    disposition = successor_fisa_risk.pop("delegated_authority_disposition")
    require(
        successor_fisa_risk == source_fisa_risk
        and successor_history[:-1] == source_history
        and successor_history[-1]
        == {
            "stage": "M4B",
            "authority": "delegated_product_methodology_editorial_authority_v1",
            "disposition": "roll_155_outside_primary_membership_with_non_counting_roll_221_relationship_retained_ambiguous",
            "acceptance_content_subject_sha256": ACCEPTANCE_CONTENT_SHA256,
        }
        and disposition == "delegated_authority_accepts_retained_ambiguous_assignment"
        and risk["entries"][-1]["current_status"] == "retained_ambiguous",
        "FISA grouping risk was removed, resolved, or changed beyond authority",
    )
    accepted_risk_statuses = {
        row["risk_id"]: row["status"] for row in acceptance["carried_risk_dispositions"]
    }
    successor_risk_statuses = {
        row["risk_id"]: row["current_status"] for row in risk["entries"]
    }
    require(
        all(
            successor_risk_statuses.get(risk_id) == status
            for risk_id, status in accepted_risk_statuses.items()
        ),
        "accepted carried-risk disposition missing",
    )

    verify_seal(calibration, "M4B calibration successor")
    prior_calibration_by_id = {
        row["episode_id"]: row for row in prior_calibration["eligible_items"]
    }
    calibration_by_id = {
        row["episode_id"]: row for row in calibration["eligible_items"]
    }
    require(
        calibration["eligible_count"] == len(calibration_by_id) == 30
        and set(calibration_by_id) == set(prior_calibration_by_id)
        and calibration["sample_selected"] is False
        and calibration["selected_sample"] == [],
        "calibration population or deferred sample state differs",
    )
    for episode_id, prior in prior_calibration_by_id.items():
        item = calibration_by_id[episode_id]
        verify_seal(item, f"calibration {episode_id}")
        expected = {
            key: value
            for key, value in prior.items()
            if key not in {"content_subject_sha256", "episode_content_subject_sha256"}
        }
        actual = {
            key: value
            for key, value in item.items()
            if key
            not in {
                "content_subject_sha256",
                "candidate_episode_content_subject_sha256",
                "implemented_episode_record_id",
                "implemented_episode_content_subject_sha256",
            }
        }
        episode = implemented_by_id[episode_id]
        require(
            actual == expected
            and item["candidate_episode_content_subject_sha256"]
            == prior["episode_content_subject_sha256"]
            and item["implemented_episode_record_id"] == episode["record_id"]
            and item["implemented_episode_content_subject_sha256"]
            == episode["content_subject_sha256"],
            f"{episode_id}: calibration implementation binding differs",
        )
    require(
        not (
            {
                "law-enforcement-concealed-carry-expansion",
                "fisa-title-vii-short-term-extension",
            }
            & set(calibration_by_id)
        ),
        "held ambiguity entered calibration population",
    )

    verify_seal(report, "implementation parity report")
    parity_by_id = {row["episode_id"]: row for row in report["episode_parity"]}
    require(
        report["episode_count"] == len(parity_by_id) == 32
        and set(parity_by_id) == set(candidate_by_id)
        and report["parity_state"] == "pass"
        and report["reviewer_identity"]
        == "chatgpt:political_fingerprint_authority_thread"
        and report["not_user_signature"] is True,
        "implementation parity report differs",
    )
    for episode_id, row in parity_by_id.items():
        require(
            row["candidate_content_subject_sha256"]
            == candidate_by_id[episode_id]["content_subject_sha256"]
            and row["implementation_content_subject_sha256"]
            == implemented_by_id[episode_id]["content_subject_sha256"]
            and all(
                row[key]
                for key in (
                    "policy_question_match",
                    "membership_match",
                    "chronology_match",
                    "action_roles_match",
                    "scope_match",
                    "behavior_and_derivation_match",
                    "confidence_match",
                    "limitations_and_ambiguity_match",
                )
            ),
            f"{episode_id}: asserted parity report differs",
        )

    verify_seal(decision_template, "delegated decision template")
    require(
        decision_template["decision_state"]
        == "awaiting_delegated_implementation_acceptance"
        and decision_template["selected_batch_decision"] is None
        and decision_template["reviewer_identity"] is None
        and decision_template["not_user_signature"] is None
        and all(
            row["selected_decision"] is None and row["rationale"] is None
            for row in decision_template["episode_decisions"]
        ),
        "empty delegated implementation decision template was filled",
    )
    require(
        decision_template["allowed_batch_decisions"]
        == [
            "delegated_authority_accepts_episode_implementation",
            "bounded_episode_implementation_correction_required",
            "delegated_authority_rejects_episode_implementation",
        ],
        "delegated implementation decision choices differ",
    )

    for value in values.values():
        verify_seal(value, value["artifact_id"])
        require(
            value.get("accepted") is False
            and value.get("canonical") is False
            and value.get("public") is False
            and value.get("authorizing") is False,
            f"{value['artifact_id']}: canonical/public/authorizing state asserted",
        )
    corpus = json.dumps(
        values, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    require(
        'accepted_semantic_reference":true' not in corpus
        and 'canonical":true' not in corpus
        and 'public":true' not in corpus
        and 'published":true' not in corpus
        and 'persisted":true' not in corpus
        and "user_approved" not in corpus,
        "forbidden authority state asserted",
    )
    require(
        bundle["accepted_semantic_reference"] is False
        and bundle["semantic_ir_exists"] is False
        and bundle["synthesis_eligible"] is False,
        "Semantic IR or synthesis authority asserted",
    )
    return {
        "episode_count": 32,
        "single_action_episode_count": 30,
        "multi_action_episode_count": 2,
        "action_accounting": counts,
        "risk_count": 8,
        "calibration_eligible_count": 30,
    }


def validate_final_byte_parity(
    *,
    byte_overrides: dict[str, bytes] | None = None,
    markdown_override: str | None = None,
) -> None:
    overrides = byte_overrides or {}
    parity = load(OUTPUT_ROOT / "parity_manifest.json")
    verify_seal(parity, "M4B final-byte parity manifest")
    require(
        parity["generated_last"]
        and parity["parity_state"] == "pass"
        and parity["referenced_file_count"] == len(parity["referenced_artifacts"]),
        "final-byte parity state differs",
    )
    for item in parity["referenced_artifacts"]:
        raw = overrides.get(item["path"], (ROOT / item["path"]).read_bytes())
        require(
            content_digest_matches(
                raw,
                item["final_file_sha256"],
                suffix=Path(item["path"]).suffix,
            ),
            f"{item['path']}: stale final-file SHA-256",
        )
        if "content_subject_sha256" in item:
            require(
                json.loads(raw)["content_subject_sha256"]
                == item["content_subject_sha256"],
                f"{item['path']}: stale content-subject SHA-256",
            )
    bundle = load(OUTPUT_ROOT / "episode_implementation_bundle.json")
    risk = load(OUTPUT_ROOT / "launch_review_risk_register.json")
    calibration = load(OUTPUT_ROOT / "episode_calibration_population.json")
    markdown = (
        markdown_override
        if markdown_override is not None
        else (OUTPUT_ROOT / "implementation_dossier.md").read_text(encoding="utf-8")
    )
    for row in bundle["implemented_episodes"]:
        require(
            row["episode_id"] in markdown
            and row["neutral_policy_question"] in markdown
            and row["candidate_episode_content_subject_sha256"] in markdown
            and row["content_subject_sha256"] in markdown,
            f"{row['episode_id']}: JSON/Markdown episode parity differs",
        )
    for row in bundle["action_accounting"]:
        require(
            row["action_id"] in markdown
            and row["primary_accounting_state"] in markdown
            and row["content_subject_sha256"] in markdown,
            f"{row['action_id']}: JSON/Markdown accounting parity differs",
        )
    require(
        str(risk["entry_count"]) in markdown
        and str(calibration["eligible_count"]) in markdown
        and ACCEPTANCE_CONTENT_SHA256 in markdown
        and "delegated_authority_accepts_episode_implementation" in markdown,
        "JSON/Markdown authority, risk, calibration, or decision parity differs",
    )


def validate() -> dict[str, Any]:
    preflight()
    require(
        ACCEPTANCE_OUTPUT.read_bytes() == ACCEPTANCE_SOURCE.read_bytes()
        and file_digest_matches(ACCEPTANCE_OUTPUT, ACCEPTANCE_FILE_SHA256),
        "imported delegated acceptance final bytes differ",
    )
    schema_inputs = {
        "delegated_episode_candidate_acceptance.json": load(ACCEPTANCE_OUTPUT),
        **{name: load(OUTPUT_ROOT / name) for name in JSON_NAMES},
        "parity_manifest.json": load(OUTPUT_ROOT / "parity_manifest.json"),
    }
    for name, value in schema_inputs.items():
        schema = load(SCHEMA_ROOT / name.replace(".json", "_v1.schema.json"))
        Draft7Validator.check_schema(schema)
        errors = list(Draft7Validator(schema).iter_errors(value))
        require(
            not errors,
            f"{name}: schema failure: {errors[0].message if errors else ''}",
        )
    values = {name: load(OUTPUT_ROOT / name) for name in JSON_NAMES}
    result = validate_artifacts(values)
    validate_final_byte_parity()
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
        "episode implementation entered runtime/public selectors",
    )
    canonical_state = (
        ROOT
        / "docs/editorial/full_record_reviews/f000477_justice_public_safety_119_review_state_v1.json"
    )
    require(
        IMPLEMENTATION_ID.encode() not in canonical_state.read_bytes(),
        "canonical review state changed",
    )
    return {
        "status": "pass",
        "bundle_id": IMPLEMENTATION_ID,
        "bundle_content_subject_sha256": values["episode_implementation_bundle.json"][
            "content_subject_sha256"
        ],
        **result,
        "parity_state": "pass",
    }


def main() -> int:
    print(json.dumps(validate(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
