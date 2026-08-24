from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_action_interpretation import (  # noqa: E402
    ActionInterpretationError,
    validate_candidate_artifact,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
    load_json,
    sha256_json,
)
from backend.scripts.build_m13c_education_workforce_action_interpretation import (  # noqa: E402
    ARTIFACT_PATH,
    DECISION_PATH,
    DOSSIER_PATH,
    PARITY_PATH,
    POST_M13B_V2_MAIN,
    READINESS_PATH,
    SCHEMA_PATH,
    DECISION_SCHEMA_PATH,
    PARITY_SCHEMA_PATH,
    build_outputs,
)
from scripts.validate_m12c_environment_energy_action_interpretation import (  # noqa: E402
    validate_repository as validate_m12c,
)
from scripts.validate_m13a_universe_authority import (  # noqa: E402
    validate_repository as validate_m13a,
)
from scripts.validate_m13b_education_workforce_source_readiness_v2 import (  # noqa: E402
    validate_repository as validate_m13b_v2,
)


CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"
EXPECTED_ARTIFACT_SHA256 = (
    "9a1030518fb922ee4bc2317e0fa5b1dd491b6c9d6a3212d5e488b7c7dd7e5d55"
)
EXPECTED_SUBJECT_SHA256 = (
    "a2dd7b4fa8ba8de9178ecb307a41977e83af2a42d1a364784f598adc2c7dec97"
)
EXPECTED_DECISION_SHA256 = (
    "3144785d663390c9993139e2679bbb5c2f35f9d64c82fb04b5ea629b04ef3543"
)
EXPECTED_DOSSIER_SHA256 = (
    "3669e76d4c94136b1227ff1f99daef8836464db270ad27994c327bb93852dff6"
)
EXPECTED_PARITY_SUBJECT_SHA256 = (
    "b9d82d2f80a7f979096b9e002da36cc486692aba09a03e48c44f2d724d846d04"
)
ROLL19_SOURCE_ID = "congressional-record:2026-01-13:house-section:H663-H719:hr2262"
ROLL19_SOURCE_SHA256 = (
    "d0dc2a327330c1e0137f8a593d82e107a75222ddebc8a9bfcbb5a62532afa80b"
)
OLD_ROLL19_SOURCE_SHA256 = (
    "a5c9f2fc9c16096d99f4939f691b8a509c9bdc62e58204eb853178f612161409"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ActionInterpretationError(message)


def validate_schema(value: dict[str, Any], path: Path, *, label: str) -> None:
    schema = load_json(path)
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda item: list(item.absolute_path),
    )
    require(not errors, f"{label} schema validation failed")


def contains_all(value: str, fragments: tuple[str, ...]) -> bool:
    normalized = value.casefold()
    return all(fragment.casefold() in normalized for fragment in fragments)


def validate_semantic_boundaries(
    artifact: dict[str, Any], readiness: dict[str, Any]
) -> None:
    candidates = artifact["subject"]["candidates"]
    candidate_by_id = {item["action_id"]: item for item in candidates}
    evidence_by_action = {
        item["action_id"]: item for item in artifact["subject"]["evidence_maps"]
    }
    roll79 = candidate_by_id["house:119:1:79"]
    require(
        roll79["exact_action_identity"] == "119:hamdt:12"
        and "h.r. 1048" not in roll79["proposed_exact_action_meaning"].casefold()
        and contains_all(
            roll79["proposed_exact_action_meaning"],
            ("section 117", "foreign gift", "sanctions", "negotiated rulemaking"),
        ),
        "roll 79 inherited whole-bill meaning",
    )
    roll312 = candidate_by_id["house:119:1:312"]
    require(
        roll312["official_member_action"] == "not_voting"
        and roll312["proposed_member_position_effect"] == "non_directional_not_voting",
        "roll 312 gained directionality",
    )
    roll146 = candidate_by_id["house:119:1:146"]
    require(
        contains_all(
            roll146["proposed_exact_action_meaning"],
            ("small business act", "hiring", "students and graduates"),
        )
        and not any(
            phrase in roll146["proposed_exact_action_meaning"].casefold()
            for phrase in (
                "general support for education",
                "supports career and technical education generally",
                "supports workforce spending",
                "supports small-business policy",
            )
        ),
        "roll 146 became a generic issue position",
    )
    roll315 = candidate_by_id["house:119:1:315"]
    require(
        contains_all(
            roll315["proposed_exact_action_meaning"],
            ("secure rural schools", "federal land", "payments"),
        )
        and not any(
            phrase in roll315["proposed_exact_action_meaning"].casefold()
            for phrase in (
                "general support for education funding",
                "general support for public lands",
                "supports forestry",
                "supports county aid",
                "supports municipal spending",
            )
        ),
        "roll 315 became a generic issue position",
    )
    roll19 = candidate_by_id["house:119:2:19"]
    roll19_evidence = evidence_by_action["house:119:2:19"]
    require(
        ROLL19_SOURCE_ID in roll19["source_references"]
        and roll19["claim_components"][0]["source_id"] == ROLL19_SOURCE_ID
        and OLD_ROLL19_SOURCE_SHA256 not in json.dumps(roll19_evidence, sort_keys=True)
        and not any(
            "congress-text:119:hr:2262" in item for item in roll19["source_references"]
        )
        and contains_all(
            roll19["proposed_exact_action_meaning"],
            (
                "modified committee substitute",
                "outside regular working hours",
                "participation is voluntary",
                "no work is performed",
                "bona fide apprenticeship",
                "on or after enactment",
            ),
        ),
        "roll 19 used defective, earlier-version, or incomplete meaning evidence",
    )
    advocacy_fragments = (
        "hardworking americans",
        "commonsense legislation",
        "so-called flexibility",
        "cut workers' wages",
        "empower the american worker",
        "vote for",
        "vote against",
    )
    require(
        all(
            not any(
                fragment in candidate["proposed_exact_action_meaning"].casefold()
                for fragment in advocacy_fragments
            )
            for candidate in candidates
        ),
        "source-native advocacy leaked into neutral meaning",
    )
    readiness_by_id = {
        item["action_id"]: item for item in readiness["subject"]["action_readiness"]
    }
    require(
        all(
            candidate["claim_components"][0]["source_id"]
            in readiness_by_id[candidate["action_id"]]["source_roles"][
                "operative_content_interpretation_input"
            ]
            for candidate in candidates
        ),
        "meaning exceeded accepted operative source binding",
    )


def validate_repository() -> dict[str, Any]:
    m13a = validate_m13a()
    m13b = validate_m13b_v2()
    m12c = validate_m12c()
    readiness = load_json(READINESS_PATH)
    artifact = load_json(ARTIFACT_PATH)
    validate_schema(artifact, SCHEMA_PATH, label="M13C candidate")
    validate_candidate_artifact(
        artifact, readiness_artifact=readiness, repository_root=ROOT
    )
    subject = artifact["subject"]
    candidates = subject["candidates"]
    candidate_by_id = {item["action_id"]: item for item in candidates}
    evidence_by_action = {item["action_id"]: item for item in subject["evidence_maps"]}
    aggregate = subject["aggregate"]
    validate_semantic_boundaries(artifact, readiness)

    require(
        artifact["artifact_id"]
        == "action-interpretation-candidates:f000477:education_workforce:119:v1"
        and canonical_file_sha256(ARTIFACT_PATH) == EXPECTED_ARTIFACT_SHA256
        and artifact["interpretation_subject_sha256"] == EXPECTED_SUBJECT_SHA256,
        "M13C candidate identity mismatch",
    )
    require(
        subject["post_source_readiness_merge_base"] == POST_M13B_V2_MAIN,
        "post-M13B-v2 main mismatch",
    )
    require(
        subject["action_ids"] == readiness["subject"]["action_ids"]
        and len(subject["action_ids"]) == len(candidates) == 17
        and not subject["blocked_action_ids"],
        "17/17 candidate accounting mismatch",
    )
    require(
        aggregate
        == {
            "approved_universe_count": 17,
            "interpretation_eligible_count": 17,
            "candidate_count": 17,
            "source_blocked_count": 0,
            "evidence_source_binding_count": 51,
            "unique_evidence_source_count": 51,
            "candidate_status_counts": {
                "proposed": 4,
                "proposed_with_material_limitation": 13,
            },
            "coverage_assessment_counts": {
                "bounded_official_purpose_summary": 15,
                "package_level_bounded_summary": 2,
            },
            "member_action_counts": {"nay": 10, "not_voting": 1, "yea": 6},
            "position_effect_counts": {
                "non_directional_not_voting": 1,
                "opposes_exact_choice": 10,
                "supports_exact_choice": 6,
            },
        },
        "M13C aggregate mismatch",
    )

    roll79 = candidate_by_id["house:119:1:79"]
    require(
        roll79["exact_action_identity"] == "119:hamdt:12"
        and roll79["official_member_action"] == "yea"
        and roll79["proposed_member_position_effect"] == "supports_exact_choice"
        and contains_all(
            roll79["proposed_exact_action_meaning"],
            (
                "section 117",
                "foreign gift and contract reporting",
                "research security compliance requirements",
                "sanctions for noncompliance",
                "negotiated rulemaking",
                "stakeholder feedback",
            ),
        )
        and "h.r. 1048" not in roll79["proposed_exact_action_meaning"].casefold()
        and all("hr:1048" not in item for item in roll79["source_references"]),
        "roll 79 exact-amendment boundary differs",
    )

    roll146 = candidate_by_id["house:119:1:146"]
    require(
        contains_all(
            roll146["proposed_exact_action_meaning"],
            (
                "small business act",
                "small business development centers",
                "women's business centers",
                "hiring",
                "students and graduates",
                "career opportunities",
            ),
        )
        and contains_all(
            " ".join(roll146["limitations"]),
            ("commerce", "does not establish general support", "workforce spending"),
        ),
        "roll 146 bounded Small Business Act treatment differs",
    )

    roll315 = candidate_by_id["house:119:1:315"]
    roll315_evidence = evidence_by_action["house:119:1:315"]
    roll315_bindings = {
        item["source_id"]: item for item in roll315_evidence["source_bindings"]
    }
    require(
        contains_all(
            roll315["proposed_exact_action_meaning"],
            (
                "secure rural schools",
                "states and counties",
                "federal land",
                "payments",
                "special-project",
                "resource-advisory-committee",
            ),
        )
        and contains_all(
            " ".join(roll315["limitations"]),
            (
                "public lands and natural resources",
                "schools",
                "roads",
                "other municipal services",
                "does not replace the operative s. 356 text",
            ),
        )
        and roll315_bindings["congress-summary:119:s:356:public-law-v49"]["roles"]
        == ["material_limitation_context_evidence"]
        and roll315["claim_components"][0]["source_id"] == "congress-text:119:s:356:es",
        "roll 315 operative/supplemental evidence boundary differs",
    )

    roll312 = candidate_by_id["house:119:1:312"]
    require(
        roll312["official_member_action"] == "not_voting"
        and roll312["proposed_member_position_effect"] == "non_directional_not_voting",
        "roll 312 gained directionality",
    )

    roll19 = candidate_by_id["house:119:2:19"]
    roll19_evidence = evidence_by_action["house:119:2:19"]
    roll19_sources = {
        item["source_id"]: item for item in roll19_evidence["source_bindings"]
    }
    require(
        ROLL19_SOURCE_ID in roll19_sources
        and roll19_sources[ROLL19_SOURCE_ID]["raw_provenance"]["sha256"]
        == ROLL19_SOURCE_SHA256
        and OLD_ROLL19_SOURCE_SHA256 not in json.dumps(roll19_evidence, sort_keys=True)
        and not any(
            "congress-text:119:hr:2262" in item for item in roll19["source_references"]
        )
        and roll19["official_title_or_purpose"]["locator"]
        == "operative-floor-text-pages"
        and roll19["claim_components"][0]["source_id"] == ROLL19_SOURCE_ID
        and contains_all(
            roll19["proposed_exact_action_meaning"],
            (
                "modified committee substitute",
                "house resolution 988",
                "outside regular working hours",
                "participation is voluntary",
                "adverse action",
                "no work is performed",
                "bona fide apprenticeship",
                "on or after enactment",
            ),
        ),
        "corrected roll 19 exact floor-text treatment differs",
    )

    advocacy_fragments = (
        "hardworking americans",
        "commonsense legislation",
        "so-called flexibility",
        "cut workers' wages",
        "empower the american worker",
        "vote for",
        "vote against",
    )
    require(
        all(
            not any(
                fragment in candidate["proposed_exact_action_meaning"].casefold()
                for fragment in advocacy_fragments
            )
            for candidate in candidates
        ),
        "source-native advocacy leaked into neutral meaning",
    )
    require(
        all(
            candidate["claim_components"][0]["source_id"]
            in readiness_record["source_roles"][
                "operative_content_interpretation_input"
            ]
            for candidate, readiness_record in (
                (
                    candidate,
                    next(
                        item
                        for item in readiness["subject"]["action_readiness"]
                        if item["action_id"] == candidate["action_id"]
                    ),
                )
                for candidate in candidates
            )
        ),
        "meaning exceeded accepted operative source binding",
    )

    decision = load_json(DECISION_PATH)
    parity = load_json(PARITY_PATH)
    validate_schema(decision, DECISION_SCHEMA_PATH, label="M13C decision template")
    validate_schema(parity, PARITY_SCHEMA_PATH, label="M13C parity manifest")
    require(
        canonical_file_sha256(DECISION_PATH) == EXPECTED_DECISION_SHA256
        and canonical_file_sha256(DOSSIER_PATH) == EXPECTED_DOSSIER_SHA256
        and parity["parity_subject_sha256"] == EXPECTED_PARITY_SUBJECT_SHA256
        and all(
            row["decision"] is None
            and row["reviewer_id"] is None
            and row["reviewer_authority"] is None
            and row["rationale"] is None
            and row["decision_timestamp"] is None
            for row in decision["subject"]["decisions"]
        ),
        "M13C review surfaces or empty decisions differ",
    )
    for item in parity["subject"]["files"]:
        require(
            canonical_file_sha256(ROOT / item["path"]) == item["sha256"],
            f"M13C parity file digest mismatch: {item['path']}",
        )
    require(
        sha256_json(parity["subject"]) == parity["parity_subject_sha256"],
        "M13C parity subject digest mismatch",
    )
    for path, content in build_outputs().items():
        require(
            path.is_file() and path.read_bytes().replace(b"\r\n", b"\n") == content,
            f"M13C deterministic regeneration mismatch: {path.relative_to(ROOT)}",
        )

    current = load_json(CURRENT_STATE_PATH)
    source_state = current["active_source_readiness_milestone"]
    candidate_state = current["active_m13c_action_interpretation_milestone"]
    require(
        source_state["accepted_pr"] == 164
        and source_state["accepted_head"] == "885b625333413b5e880808fda41937e9ff22abca"
        and source_state["post_merge_main"] == POST_M13B_V2_MAIN
        and source_state["m13c_stop_resolution"]
        == "resolved_by_accepted_m13b_v2_complete_roll19_source",
        "accepted M13B v2 checkpoint differs",
    )
    require(
        candidate_state["milestone"]
        == "m13c_education_workforce_action_interpretation_v1"
        and candidate_state["post_m13b_v2_main"] == POST_M13B_V2_MAIN
        and candidate_state["candidate_count"] == 17
        and candidate_state["non_directional_action_ids"] == ["house:119:1:312"]
        and candidate_state["candidate_identity"]["sha256"] == EXPECTED_ARTIFACT_SHA256
        and candidate_state["candidate_identity"]["interpretation_subject_sha256"]
        == EXPECTED_SUBJECT_SHA256
        and all(
            value is False
            for value in candidate_state["downstream_authorizations"].values()
        ),
        "M13C current-state boundary differs",
    )
    require(
        all(value is False for value in subject["downstream_authorizations"].values())
        and all(
            value is False
            for value in decision["subject"]["downstream_authorizations"].values()
        ),
        "M13C downstream authority became true",
    )
    require(
        m13a["accepted_action_count"] == 17
        and m13a["accepted_action_set_sha256"]
        == "83b7b129eaa32d114c72782c70cb06dac55f7cd01c8681c8dc2ae2dca986cf5b"
        and m13b["artifact_sha256"]
        == "36cff9b3b5f3a7ad21579373c4437aad5c9c18aaf8d2f0874721695685899aa0"
        and m13b["ready_count"] == 17
        and m13b["blocked_count"] == 0
        and m12c["artifact_sha256"]
        == "84713da4156f8a3f0347384225905351017bf21615ebcdca76e147aa2294b242",
        "upstream or accepted cross-domain compatibility changed",
    )

    return {
        "status": "pass",
        "artifact_id": artifact["artifact_id"],
        "artifact_sha256": canonical_file_sha256(ARTIFACT_PATH),
        "interpretation_subject_sha256": artifact["interpretation_subject_sha256"],
        "candidate_count": len(candidates),
        "blocked_count": 0,
        "directional_count": 16,
        "non_directional_count": 1,
        "evidence_source_binding_count": aggregate["evidence_source_binding_count"],
        "roll19_source_sha256": ROLL19_SOURCE_SHA256,
        "aggregate": aggregate,
    }


def main() -> int:
    try:
        print(json.dumps(validate_repository(), sort_keys=True))
    except (ActionInterpretationError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
