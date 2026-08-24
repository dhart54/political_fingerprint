from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from jsonschema import Draft7Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    SourceReadinessError,
    canonical_file_sha256,
    load_json,
    validate_artifact,
)
from scripts.validate_m12b_environment_energy_source_readiness import (  # noqa: E402
    validate_repository as validate_m12b,
)
from scripts.validate_m13a_universe_authority import (  # noqa: E402
    validate_repository as validate_m13a,
)


BASE = "3aa546346aaf612ba24ee77765ca6b791f8490fe"
ARTIFACT_PATH = ROOT / (
    "docs/editorial/full_record_reviews/source_readiness/"
    "f000477_education_workforce_119_interpretation_source_readiness_v1.json"
)
SCHEMA_PATH = ROOT / (
    "docs/methodology/full_record_interpretation_source_readiness_v1.schema.json"
)
AUTHORITY_PATH = ROOT / (
    "docs/editorial/full_record_reviews/"
    "f000477_education_workforce_119_full_issue_universe_authority_receipt_v1.json"
)
M13A_ROOT = ROOT / "docs/editorial/cross_issue_full_record_expansion_m13a_v1"
PROPOSAL_PATH = M13A_ROOT / "selected_domain_universe_proposal.json"
SELECTION_PATH = M13A_ROOT / "domain_selection.json"
INVENTORY_PATH = M13A_ROOT / "source_inventory.json"
CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"
EXPECTED = {
    "authority_sha256": "491b6de2314788f1566f8366f95a66b2375ec6d1271790a18387ba33cad70ea3",
    "action_set_sha256": "83b7b129eaa32d114c72782c70cb06dac55f7cd01c8681c8dc2ae2dca986cf5b",
    "universe_subject_sha256": "edc381362beb1e5700748ffe75fc12c31ae14f090887940197a50bf416aaac6d",
    "selection_sha256": "e877adf1cd5a1bff08c08ecb4ee1ee6acc1bbdff6d93899171e13480f6473f5a",
    "source_inventory_sha256": "66070d29ebe29e6ef3c17dc67c888b522d7043b36e5fd694d0093b4ce5be6fe7",
    "artifact_sha256": "70157fa2f9d55683837d5a7e3ff92249cbf74d89def7a759e5eef4459474b198",
    "subject_sha256": "7f526f1ce37d9f2ec1acd5e092d04e091b8ad5340c56aff57d478f69e45533c7",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceReadinessError(message)


def source_by_class(record: dict[str, Any], content_class: str) -> dict[str, Any]:
    matches = [
        source
        for source in record["sources"]
        if source["content_class"] == content_class
    ]
    require(len(matches) == 1, f"{record['action_id']} lacks one {content_class}")
    return matches[0]


def raw_text(source: dict[str, Any]) -> str:
    path = ROOT / source["raw_provenance"]["governed_local_path"]
    return path.read_text(encoding="utf-8").casefold()


def validate_repository() -> dict[str, Any]:
    m13a = validate_m13a()
    m12b = validate_m12b()
    artifact = load_json(ARTIFACT_PATH)
    authority = load_json(AUTHORITY_PATH)
    proposal = load_json(PROPOSAL_PATH)
    selection = load_json(SELECTION_PATH)
    inventory = load_json(INVENTORY_PATH)
    current = load_json(CURRENT_STATE_PATH)
    schema = load_json(SCHEMA_PATH)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(artifact),
        key=lambda error: list(error.absolute_path),
    )
    require(not errors, f"M13B schema failed: {errors[0].message if errors else ''}")

    subject = artifact["subject"]
    approved = authority["approval_binding"]["approved_action_ids"]
    require(
        canonical_file_sha256(AUTHORITY_PATH)
        == artifact["input_bindings"]["authority_receipt"]["sha256"]
        == EXPECTED["authority_sha256"],
        "M13A authority binding differs",
    )
    require(
        subject["action_ids"] == approved
        and len(approved) == 17
        and len(set(approved)) == 17
        and set(approved) == set(proposal["proposed_action_ids"]),
        "17-action authority equality differs",
    )
    require(
        subject["action_set_sha256"]
        == authority["action_set_sha256"]
        == m13a["accepted_action_set_sha256"]
        == EXPECTED["action_set_sha256"],
        "accepted action-set digest differs",
    )
    require(
        subject["universe_subject_sha256"]
        == authority["universe_subject_sha256"]
        == EXPECTED["universe_subject_sha256"],
        "universe-subject digest differs",
    )
    require(
        selection["selection_sha256"]
        == artifact["input_bindings"]["selection"]["sha256"]
        == EXPECTED["selection_sha256"],
        "selection digest differs",
    )
    require(
        inventory["inventory_sha256"]
        == artifact["input_bindings"]["source_inventory"]["inventory_sha256"]
        == EXPECTED["source_inventory_sha256"],
        "M13A source-inventory digest differs",
    )
    require(
        canonical_file_sha256(ARTIFACT_PATH) == EXPECTED["artifact_sha256"]
        and artifact["source_readiness_subject_sha256"] == EXPECTED["subject_sha256"],
        "M13B candidate identity differs",
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
        "readiness aggregate differs",
    )
    records = subject["action_readiness"]
    by_id = {record["action_id"]: record for record in records}
    require(
        [record["action_id"] for record in records] == approved,
        "readiness record order or membership differs",
    )
    sources = [source for record in records for source in record["sources"]]
    paths = [source["raw_provenance"]["governed_local_path"] for source in sources]
    require(len(sources) == len(set(paths)) == 51, "official source count differs")
    for record in records:
        roles = record["source_roles"]
        require(
            roles["member_action_evidence"]
            and roles["exact_action_identity_and_stage_evidence"]
            and roles["operative_content_interpretation_input"],
            f"role coverage differs: {record['action_id']}",
        )

    amendment = by_id["house:119:1:79"]
    amendment_source = source_by_class(amendment, "exact_amendment_purpose")
    purpose = amendment_source["neutral_projection"]["official_purpose"].casefold()
    require(
        amendment["exact_action_identity"] == "119:hamdt:12"
        and amendment["source_roles"]["operative_content_interpretation_input"]
        == ["congress-amendment:119:hamdt:12"]
        and all(
            term in purpose for term in ("section 117", "foreign gift", "sanctions")
        )
        and "parent H.R. 1048 evidence alone is insufficient"
        in amendment["material_limitations"][0],
        "roll 79 exact amendment proof differs",
    )

    hr1642 = by_id["house:119:1:146"]
    hr1642_text = raw_text(source_by_class(hr1642, "operative_measure_text"))
    proposal_rows = {
        row["action_id"]: row for row in proposal["candidate_dispositions"]
    }
    require(
        proposal_rows["house:119:1:146"]["official_policy_area"] == "Commerce"
        and all(
            term in hr1642_text
            for term in (
                "small business act",
                "career and technical education",
                "hiring graduates",
                "career opportunities",
            )
        )
        and "exclusively or primarily education policy"
        in hr1642["material_limitations"][0],
        "H.R. 1642 cross-domain proof differs",
    )

    s356 = by_id["house:119:1:315"]
    s356_text = raw_text(source_by_class(s356, "stage_compatible_senate_origin_text"))
    s356_summary = source_by_class(s356, "supplemental_program_context")
    summary_text = s356_summary["neutral_projection"]["official_description"].casefold()
    require(
        proposal_rows["house:119:1:315"]["official_policy_area"]
        == "Public Lands and Natural Resources"
        and all(
            term in s356_text
            for term in ("secure rural schools", "federal land", "county payment")
        )
        and all(
            term in summary_text
            for term in ("federal land", "schools", "roads", "municipal services")
        )
        and s356["source_roles"]["material_limitation_context_evidence"]
        == [s356_summary["source_id"]]
        and "general education-funding position" in s356["material_limitations"][0],
        "S. 356 mixed-boundary proof differs",
    )

    not_voting = by_id["house:119:1:312"]
    require(
        not_voting["official_member_action"] == "not_voting"
        and not_voting["readiness_state"] == "ready_for_action_interpretation"
        and not_voting["readiness_criteria"]["member_action_exact"]
        and "non-directional" in not_voting["material_limitations"][0]
        and "cannot infer support or opposition"
        in not_voting["material_limitations"][0],
        "roll 312 non-directional readiness boundary differs",
    )
    hr2262 = by_id["house:119:2:19"]
    require(
        source_by_class(hr2262, "operative_floor_text")["source_type"]
        == "congressional_record",
        "H.R. 2262 exact floor-text fallback differs",
    )

    state = current["active_source_readiness_milestone"]
    identity = state["interpretation_source_readiness_identity"]
    require(
        state["milestone"] == "m13b_education_workforce_source_readiness_v1"
        and state["post_m13a_merge_base"] == BASE
        and state["milestone_state"] == "complete_pending_independent_review"
        and state["official_role_bound_source_count"] == 51
        and identity
        == {
            "id": artifact["artifact_id"],
            "sha256": EXPECTED["artifact_sha256"],
            "source_readiness_subject_sha256": EXPECTED["subject_sha256"],
            "ready_count": 17,
            "blocked_count": 0,
            "authorizing": False,
        }
        and all(value is False for value in state["downstream_authorizations"].values())
        and not state["publication_changes"]
        and not state["production_writes"],
        "current-state M13B boundary differs",
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
    require(review_diff.returncode == 0, "protected review diff inspection failed")
    allowed_prefixes = (
        "docs/editorial/full_record_reviews/source_readiness/"
        "f000477_education_workforce_119_interpretation_source_readiness_v1",
        "docs/editorial/full_record_reviews/source_readiness/evidence/"
        "f000477_education_119_v1/",
    )
    require(
        all(
            path.startswith(allowed_prefixes)
            for path in review_diff.stdout.splitlines()
        ),
        "accepted Justice, National Security, or Environment artifact changed",
    )
    require(
        m12b["total_action_count"] == 63
        and m12b["ready_count"] == 63
        and m12b["blocked_count"] == 0,
        "M12B legacy source-readiness regression",
    )
    return {
        "status": "pass",
        "artifact_id": artifact["artifact_id"],
        "artifact_sha256": EXPECTED["artifact_sha256"],
        "source_readiness_subject_sha256": EXPECTED["subject_sha256"],
        "total_action_count": 17,
        "ready_count": 17,
        "blocked_count": 0,
        "official_role_bound_source_count": 51,
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
