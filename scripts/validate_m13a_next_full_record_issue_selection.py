from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "docs/editorial/cross_issue_full_record_expansion_m13a_v1"
SCHEMA = ROOT / "docs/methodology/cross_issue_full_record_expansion_v2.schema.json"
SELECTION = ARTIFACT_ROOT / "domain_selection.json"
UNIVERSE = ARTIFACT_ROOT / "selected_domain_universe_proposal.json"
SOURCES = ARTIFACT_ROOT / "source_inventory.json"
INVENTORY = ARTIFACT_ROOT / "complete_official_action_inventory.json"
CURRENT_STATE = ROOT / "docs/editorial/current_state_index.json"
BASE = "1edb335a787040a7cfab39e36b9260234a74d683"
ACTIVE = {
    "JUSTICE_PUBLIC_SAFETY",
    "NATIONAL_SECURITY_FOREIGN",
    "ENVIRONMENT_ENERGY",
}
REMAINING = {
    "ECONOMY_TAXES",
    "EDUCATION_WORKFORCE",
    "HEALTH_SOCIAL",
    "IMMIGRATION_BORDER",
    "INFRASTRUCTURE_TECH_TRANSPORT",
}
EXPECTED = {
    "ECONOMY_TAXES": (152, 44, 2, 55, 2, 43, 6),
    "EDUCATION_WORKFORCE": (50, 16, 1, 26, 0, 7, 0),
    "HEALTH_SOCIAL": (25, 10, 0, 12, 1, 2, 0),
    "IMMIGRATION_BORDER": (32, 14, 0, 15, 1, 2, 0),
    "INFRASTRUCTURE_TECH_TRANSPORT": (38, 23, 1, 11, 0, 3, 0),
}
PROTECTED_PATHS = (
    "docs/editorial/cross_issue_full_record_expansion_v1",
    "docs/editorial/cross_issue_full_record_expansion_m12a_v1",
)
ALLOWED_FULL_RECORD_REVIEW_CHANGE = (
    "docs/editorial/full_record_reviews/"
    "f000477_education_workforce_119_full_issue_universe_authority_receipt_v1.json"
)
ALLOWED_EDUCATION_WORKFORCE_PREFIXES = (
    "docs/editorial/full_record_reviews/source_readiness/"
    "f000477_education_workforce_119_",
    "docs/editorial/full_record_reviews/source_readiness/evidence/"
    "f000477_education_119_v1/",
    "docs/editorial/full_record_reviews/source_readiness/evidence/"
    "f000477_education_119_v2/",
    "docs/editorial/full_record_reviews/source_readiness/corrections/"
    "f000477_education_workforce_119_",
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
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    schema = load(SCHEMA)
    selection = load(SELECTION)
    universe = load(UNIVERSE)
    sources = load(SOURCES)
    inventory = load(INVENTORY)
    current_state = load(CURRENT_STATE)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for path, payload in (
        (SELECTION, selection),
        (UNIVERSE, universe),
        (SOURCES, sources),
    ):
        errors = sorted(
            validator.iter_errors(payload), key=lambda error: list(error.path)
        )
        require(not errors, f"{path.name}: {errors[0].message if errors else ''}")

    require(selection["starting_commit"] == BASE, "starting commit differs")
    require(
        set(selection["excluded_domains"]) == ACTIVE, "active-domain exclusion differs"
    )
    by_domain = {row["domain_id"]: row for row in selection["candidate_domains"]}
    require(set(by_domain) == REMAINING, "remaining-domain set differs")
    require(
        selection["selected_domain"] == "EDUCATION_WORKFORCE", "selected domain differs"
    )
    require(
        selection["eligible_domains_ranked"]
        == [
            "EDUCATION_WORKFORCE",
            "INFRASTRUCTURE_TECH_TRANSPORT",
            "IMMIGRATION_BORDER",
            "HEALTH_SOCIAL",
        ],
        "readiness rank differs",
    )
    for domain_id, expected in EXPECTED.items():
        row = by_domain[domain_id]
        actual = (
            row["total_candidate_actions"],
            row["directional_substantive_actions"],
            row["non_directional_substantive_actions"],
            row["procedural_context_actions"],
            row["expressive_nonbinding_actions"],
            row["exact_action_ineligible_actions"],
            row["unresolved_boundary_cases"],
        )
        require(actual == expected, f"accounting differs for {domain_id}: {actual}")
        require(
            sum(len(ids) for ids in row["action_ids_by_disposition"].values())
            == row["total_candidate_actions"],
            f"disposition accounting gap for {domain_id}",
        )
        require(
            row["full_issue_universe_closed"]
            == (row["unresolved_boundary_cases"] == 0),
            f"closed-universe state differs for {domain_id}",
        )
    require(
        by_domain["ECONOMY_TAXES"]["generic_manageability_gate_passed"],
        "Economy fresh manageability gate did not pass",
    )
    require(
        not by_domain["ECONOMY_TAXES"]["selection_ready"],
        "Economy boundary hold missing",
    )

    rows = inventory["actions"]
    require(
        len(rows) == inventory["complete_official_action_count"] == 638,
        "inventory count differs",
    )
    action_ids = [row["action_id"] for row in rows]
    require(len(action_ids) == len(set(action_ids)), "duplicate official action")
    require(action_ids[-1] == "house:119:2:283", "official cutoff action differs")
    require(inventory["cutoff"]["end_date"] == "2026-07-23", "cutoff date differs")
    require(
        digest(action_ids) == inventory["complete_official_action_id_set_sha256"],
        "action-ID digest differs",
    )
    require(
        digest(rows) == inventory["complete_official_action_inventory_sha256"],
        "full inventory digest differs",
    )
    for payload in (selection, universe, sources):
        require(
            payload["complete_official_action_set_sha256"]
            == inventory["complete_official_action_id_set_sha256"],
            "cross-artifact action-ID digest differs",
        )
        require(
            payload["complete_official_action_inventory_sha256"]
            == inventory["complete_official_action_inventory_sha256"],
            "cross-artifact inventory digest differs",
        )

    proposed = universe["proposed_action_ids"]
    dispositions = universe["candidate_dispositions"]
    require(len(dispositions) == 50, "selected candidate set differs")
    require(len(proposed) == 17, "proposed universe count differs")
    require(
        not universe["unresolved_action_ids"],
        "selected universe has unresolved actions",
    )
    require(universe["full_issue_universe_closed"], "selected universe is not closed")
    counts = Counter(row["disposition"] for row in dispositions)
    require(counts["proposed_in_scope_substantive"] == 16, "directional count differs")
    require(
        counts["proposed_in_scope_non_directional"] == 1,
        "non-directional count differs",
    )
    require(counts["procedural_context"] == 26, "procedural count differs")
    require(counts["exact_action_ineligible"] == 7, "ineligible count differs")
    require(
        all(
            row["exact_action_source_binding"] is not None
            for row in dispositions
            if row["disposition"].startswith("proposed_in_scope_")
        ),
        "proposed action lacks exact official source binding",
    )
    require(
        not universe["action_interpretation_started"], "action interpretation started"
    )
    require(not universe["semantic_ir_started"], "Semantic IR started")
    require(not universe["production_writes"], "production write recorded")
    require(
        all(
            value is False for value in selection["downstream_authorizations"].values()
        ),
        "downstream authorization leaked",
    )

    acquisition = sources["fresh_boundary_source_acquisition"]
    require(len(acquisition["summary_sources"]) == 62, "summary source count differs")
    require(
        len(acquisition["amendment_index_sources"]) == 11,
        "amendment source count differs",
    )
    require(
        not acquisition["production_or_database_access"],
        "source acquisition used production",
    )
    require(
        sources["complete_official_action_count"] == 638,
        "source inventory count differs",
    )
    require(
        digest(
            {key: value for key, value in sources.items() if key != "inventory_sha256"}
        )
        == sources["inventory_sha256"],
        "source inventory digest differs",
    )

    milestone = current_state["active_universe_selection_milestone"]
    require(
        current_state["current_project_state"]["active_full_record_publications"]
        == [
            "JUSTICE_PUBLIC_SAFETY",
            "NATIONAL_SECURITY_FOREIGN",
            "ENVIRONMENT_ENERGY",
        ],
        "active-publication baseline differs",
    )
    require(
        current_state["current_project_state"]["active_publication_count"] == 3,
        "active-publication count differs",
    )
    require(
        milestone["selected_domain"] == selection["selected_domain"],
        "state selection differs",
    )
    require(
        milestone["proposed_action_count"] == len(proposed),
        "state proposal count differs",
    )
    require(
        milestone["unresolved_boundary_count"] == 0, "state unresolved count differs"
    )
    require(
        milestone["selection_sha256"] == selection["selection_sha256"],
        "state selection digest differs",
    )
    require(
        milestone["proposal_sha256"] == universe["proposal_sha256"],
        "state proposal digest differs",
    )
    require(
        milestone["source_inventory_sha256"] == sources["inventory_sha256"],
        "state source-inventory digest differs",
    )
    require(
        milestone["complete_official_action_inventory_sha256"]
        == inventory["complete_official_action_inventory_sha256"],
        "state official-inventory digest differs",
    )
    require(
        all(
            value is False for value in milestone["downstream_authorizations"].values()
        ),
        "current state authorizes downstream work",
    )

    result = subprocess.run(
        ["git", "diff", "--quiet", BASE, "--", *PROTECTED_PATHS],
        cwd=ROOT,
        check=False,
    )
    require(
        result.returncode == 0, "accepted active-domain artifact regression detected"
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
    require(review_diff.returncode == 0, "full-record review diff inspection failed")
    require(
        all(
            path == ALLOWED_FULL_RECORD_REVIEW_CHANGE
            or path.startswith(ALLOWED_EDUCATION_WORKFORCE_PREFIXES)
            for path in review_diff.stdout.splitlines()
        ),
        "accepted full-record review artifact regression detected",
    )
    print(
        json.dumps(
            {
                "status": "pass",
                "selected_domain": selection["selected_domain"],
                "official_action_count": len(rows),
                "proposed_action_count": len(proposed),
                "selected_unresolved_count": 0,
                "protected_active_domain_regressions": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
