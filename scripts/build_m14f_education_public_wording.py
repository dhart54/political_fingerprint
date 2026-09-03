"""Build/check exact detached M14F Education wording and prominence candidates."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.accepted_findings_public_wording import (  # noqa: E402
    DENIED, PublicWordingSourceBinding, compile_public_wording, limitations, require,
    validate_public_wording,
)
from backend.app.semantic_ir.shared_corpus import digest  # noqa: E402

BASE = "ad469a0f76fb43c16204ec23d68cca73a0cc70c8"
M14D = "docs/editorial/analytical_candidates/f000477_education_workforce_m14d_v1"
M14E = "docs/editorial/synthesis_candidates/f000477_education_workforce_m14e_v1"
OUT = "docs/editorial/public_wording_candidates/f000477_education_workforce_m14f_v1"
BINDING = PublicWordingSourceBinding(
    findings_path=f"{M14D}/accepted_behavioral_findings.json",
    findings_document_sha256="94cf74ee03af627183ef01c6a2838fff76f6f8d17a15eb13d08c66249a98a441",
    behavioral_authority_path=f"{M14D}/human_behavioral_candidate_authority.json",
    behavioral_authority_document_sha256="dfc225a0bdf9cec24ce651acf644fd334a49ff357775937bc9cf4e96b14055c3",
    synthesis_path=f"{M14E}/accepted_internal_synthesis.json",
    synthesis_document_sha256="cfaabfff7b036476592102863c2a018c336e27dded9786db9dd334c7fd5ab753",
    synthesis_authority_path=f"{M14E}/human_synthesis_authority.json",
    synthesis_authority_document_sha256="4be77fa02bc3a3f7e306a40c8d513ca7e172151067814feaa8919847f5afa89a",
)
FUNDING = "m14d:covered_china_linked_funding_exclusions"
BARGAINING = "m14d:continuity_of_collective_bargaining"
HR1048 = "m14d:hr1048_substitute_and_package"
SYNTHESIS = "m14e:education_foreign_influence_mechanism_contrast"
OVERVIEW = "m14f:issue_overview:education_workforce"
FUNDING_ITEM = "m14f:pattern:china_linked_education_funding"
BARGAINING_ITEM = "m14f:pattern:collective_bargaining_continuity"
HR1048_ITEM = "m14f:notable:hr1048_substitute_final"
MAIN_TAKEAWAY = "On foreign influence in education, Foushee opposed two bills that would cut off specified federal funding to schools or colleges over certain China-linked ties or Chinese-government-backed support. She also supported an H.R. 1048 substitute requiring detailed foreign-gift and contract reporting, public disclosure, and penalties for some violations. She later opposed the broader final H.R. 1048 package, so that vote does not show which part of the final bill she rejected."
PROMINENCE_NOTE = "This synthesis is proposed as the Main Takeaway because it is the only accepted cross-finding relationship in the reviewed Education & Workforce record. Human review must still decide whether a three-episode foreign-influence synthesis is representative and useful enough to headline the broader issue page."
COMPRESSED_SCOPE = "The primary sentence uses concrete institutions, mechanisms, and bounded actions; the narrower source detail remains available in the finding and its receipts."
COMPRESSED_PROCEDURE = "Implementation-level procedural detail is not necessary to preserve this public meaning; the wording retains the governing mechanism and does not claim enactment."
COMPRESSED_NO_INFERENCE = "The primary sentence stays within the named reviewed actions and makes no motive, ideological, universal-regime, or broader policy-preference inference."
COMPRESSED_NON_DIRECTIONAL = "The wording names only the accepted directional evidence; H.R.1005 remains separately accounted as Not Voting and supplies no finding evidence."
ALLOWED_PATHS = {
    "backend/app/semantic_ir/accepted_findings_public_wording.py",
    "backend/tests/test_accepted_findings_public_wording.py",
    "scripts/build_m14f_education_public_wording.py",
    "docs/plans/m14f_education_public_wording_review.md",
    ".github/workflows/backend-tests.yml",
    f"{OUT}/public_wording_candidate_package.json", f"{OUT}/review_package.json",
}


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def treatment_rows(source_id: str, source: dict, source_kind: str,
                   states: list[tuple[str, str | None]]) -> list[dict]:
    source_limits = limitations(source_id, source, source_kind)
    require(len(source_limits) == len(states), "authored treatment count differs from accepted limitations")
    return [{"limitation_id": row["limitation_id"], "treatment": state, "reason": reason}
            for row, (state, reason) in zip(source_limits, states, strict=True)]


def definitions(findings: dict, accepted_synthesis: dict) -> list[dict]:
    records = {r["proposition_id"]: r for r in findings["subject"]["accepted_proposition_records"]}
    synthesis = accepted_synthesis["subject"]["accepted_synthesis_records"][0]
    retained = ("retained_public_copy", None)
    return [
        {"wording_item_id": OVERVIEW, "surface": "issue_overview", "public_title": "Education & Workforce",
         "evidence_count_label": "2 linked findings · 4 House votes", "direction_display": None,
         "primary_sentence": MAIN_TAKEAWAY, "semantic_source_id": SYNTHESIS,
         "limitation_treatments": treatment_rows(SYNTHESIS, synthesis, "accepted_internal_synthesis", [
             ("compressed_or_omitted", COMPRESSED_SCOPE), ("compressed_or_omitted", COMPRESSED_PROCEDURE),
             ("compressed_or_omitted", COMPRESSED_NON_DIRECTIONAL), ("compressed_or_omitted", COMPRESSED_PROCEDURE),
             retained, ("compressed_or_omitted", COMPRESSED_PROCEDURE),
             ("compressed_or_omitted", COMPRESSED_NO_INFERENCE)])},
        {"wording_item_id": FUNDING_ITEM, "surface": "repeated_pattern",
         "public_title": "Opposed two China-linked education funding restrictions",
         "evidence_count_label": "2 bills · 2 House votes", "direction_display": None,
         "primary_sentence": "Foushee opposed H.R. 881, which would generally make colleges with specified ties to named China-linked programs or entities ineligible for Department of Homeland Security funding, and H.R. 1069, which would generally withhold covered federal education funds from K–12 schools with specified Chinese-government-backed partnerships or resources. Both bills included waiver routes, but they covered different sectors, funding streams, and conditions.",
         "semantic_source_id": FUNDING,
         "limitation_treatments": treatment_rows(FUNDING, records[FUNDING], "behavioral", [
             retained, retained, ("compressed_or_omitted", COMPRESSED_NON_DIRECTIONAL)])},
        {"wording_item_id": BARGAINING_ITEM, "surface": "repeated_pattern",
         "public_title": "Supported keeping collective bargaining in force",
         "evidence_count_label": "2 bills · 2 House votes", "direction_display": None,
         "primary_sentence": "Foushee supported H.R. 2550, which would restore bargaining coverage and preserve existing union agreements for specified federal workers affected by an executive order. She also supported H.R. 5408, which would require continued bargaining and unchanged employment terms while newly represented workers pursued a first contract, with mediation and binding arbitration if talks remained unresolved.",
         "semantic_source_id": BARGAINING,
         "limitation_treatments": treatment_rows(BARGAINING, records[BARGAINING], "behavioral", [
             retained, retained, retained, ("compressed_or_omitted", COMPRESSED_NO_INFERENCE)])},
        {"wording_item_id": HR1048_ITEM, "surface": "notable_choice",
         "public_title": "Supported a reporting substitute, opposed the final H.R. 1048 package",
         "evidence_count_label": "1 legislative episode · 2 House votes",
         "direction_display": {"label": "Mixed", "symbol": "±"},
         "primary_sentence": "Foushee supported a substitute that would set foreign-gift and contract reporting thresholds for colleges, make reports publicly searchable, allow some equivalent reporting and specified exclusions, and impose fines or compliance plans for some violations. She then opposed the broader final H.R. 1048 package, which also included contract restrictions and other reporting and enforcement provisions. The final vote does not identify which part she opposed.",
         "semantic_source_id": HR1048,
         "limitation_treatments": treatment_rows(HR1048, records[HR1048], "behavioral", [
             ("compressed_or_omitted", COMPRESSED_PROCEDURE), retained,
             ("compressed_or_omitted", COMPRESSED_PROCEDURE),
             ("compressed_or_omitted", COMPRESSED_NO_INFERENCE)])},
    ]


def prominence_review() -> dict:
    return {
        "semantic_validity": "accepted_internal_synthesis_not_reopened",
        "decision_state": "pending_independent_human_product_review",
        "proposed_prominence_note": PROMINENCE_NOTE,
        "main_takeaway_alternative": "omit_main_takeaway_and_retain_all_three_findings",
        "option_a_main_takeaway": [
            "The synthesis adds a mechanism contrast beyond either source finding alone: opposition to two specified funding-eligibility restrictions alongside support for one detailed reporting/compliance substitute, bounded by the later whole-package Nay.",
            "It may merit prominence because it is the only human-accepted cross-finding relationship in the reviewed Education & Workforce record.",
            "Three episodes and four actions may be too narrow to headline a record containing sixteen episodes and seventeen actions.",
            "The explicit opening scope, On foreign influence in education, limits the claim to this policy slice rather than presenting it as the issue record's dominant behavior.",
        ],
        "option_b_no_main_takeaway": [
            "All three behavioral findings remain independently understandable, so the evidence layer loses no accepted semantic information.",
            "The page becomes less interpretively ambitious but avoids overweighting a three-episode foreign-influence slice of the broader record.",
        ],
    }


def build_outputs() -> dict[str, bytes]:
    findings = load(BINDING.findings_path)
    behavioral_authority = load(BINDING.behavioral_authority_path)
    accepted_synthesis = load(BINDING.synthesis_path)
    synthesis_authority = load(BINDING.synthesis_authority_path)
    args = (findings, behavioral_authority, accepted_synthesis, synthesis_authority, BINDING)
    authored = definitions(findings, accepted_synthesis)
    prominence = prominence_review()
    package = compile_public_wording(*args, authored, prominence)
    validate_public_wording(package, *args, authored, prominence)
    zero = compile_public_wording(*args, authored[1:], prominence)
    items = package["subject"]["wording_items"]
    treatments = [t for item in items for t in item["limitation_treatments"]]
    review = {
        "schema_version": "m14f_public_wording_review_package_v1", "baseline_main_sha": BASE,
        "artifact_role": "detached_non_authorizing_public_wording_and_prominence_review",
        "accepted": False, "authorizing": False, "public": False, "production_selectable": False,
        "candidate_package": {"path": f"{OUT}/public_wording_candidate_package.json",
                              "package_sha256": package["package_sha256"]},
        "wording_items": deepcopy(items),
        "wording_item_digests": {i["wording_item_id"]: i["wording_item_sha256"] for i in items},
        "semantic_source_accounting": {
            "behavioral": deepcopy(package["subject"]["behavioral_finding_accounting"]),
            "synthesis": deepcopy(package["subject"]["synthesis_accounting"])},
        "lineage_counts": {"behavioral_findings": 3, "behavioral_episodes": 5, "behavioral_actions": 6,
                           "overview_source_findings": 2, "overview_episodes": 3, "overview_actions": 4,
                           "full_issue_episodes": 16, "full_issue_actions": 17},
        "limitation_treatment_counts": dict(sorted(Counter(t["treatment"] for t in treatments).items())),
        "prominence_review": deepcopy(prominence),
        "zero_main_takeaway_variant": {"valid": True, "wording_item_ids": [i["wording_item_id"] for i in zero["subject"]["wording_items"]],
                                       "package_sha256": zero["package_sha256"],
                                       "synthesis_disposition": zero["subject"]["synthesis_accounting"]["disposition"]},
        "non_directional_exclusion": deepcopy(package["subject"]["excluded_non_directional_receipts"]),
        "review_questions": [
            "Is the proposed overview useful and representative enough to headline a sixteen-episode issue record?",
            "Would omitting Main Takeaway better avoid overweighting the three-episode foreign-influence slice?",
            "Does each sentence remain clear, concrete, and within its accepted semantic source?",
            "Are all compressed limitations justified without losing a material boundary?",
        ],
        "downstream_authorizations": DENIED.copy(),
    }
    return {f"{OUT}/public_wording_candidate_package.json": json_bytes(package),
            f"{OUT}/review_package.json": json_bytes(
                review | {"review_package_sha256": digest(review)})}


def validate_scope() -> None:
    changed = set(subprocess.check_output(["git", "diff", "--name-only", BASE], cwd=ROOT, text=True).splitlines())
    changed.update(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines())
    require(changed <= ALLOWED_PATHS, f"M14F scope violation: {sorted(changed - ALLOWED_PATHS)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-scope", action="store_true")
    args = parser.parse_args()
    if args.check_scope:
        validate_scope()
    outputs = build_outputs()
    for name, content in outputs.items():
        path = ROOT / name
        if args.check:
            require(path.exists() and path.read_bytes().replace(b"\r\n", b"\n") == content,
                    f"M14F artifact differs: {name}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists() or path.read_bytes().replace(b"\r\n", b"\n") != content:
                path.write_bytes(content)
    package = json.loads(outputs[f"{OUT}/public_wording_candidate_package.json"])
    review = json.loads(outputs[f"{OUT}/review_package.json"])
    print(json.dumps({"wording_items": len(package["subject"]["wording_items"]),
                      "item_digests": review["wording_item_digests"],
                      "limitation_treatments": review["limitation_treatment_counts"],
                      "accepted_public_wording": 0, "accepted_prominence": 0}, indent=2))


if __name__ == "__main__":
    main()
