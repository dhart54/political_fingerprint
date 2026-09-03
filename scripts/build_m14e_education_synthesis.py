"""Build/check one detached M14E hypothesis from frozen human-accepted findings."""
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

from backend.app.semantic_ir.accepted_findings_synthesis import (  # noqa: E402
    AcceptedSourceBinding, DENIED, compile_detached_synthesis, require,
    validate_detached_synthesis,
)
from backend.app.semantic_ir.shared_corpus import digest  # noqa: E402

BASE = "79995a5a4d8840e2e3783905327ba02c6d40cffa"
SOURCE = "docs/editorial/analytical_candidates/f000477_education_workforce_m14d_v1"
OUT = "docs/editorial/synthesis_candidates/f000477_education_workforce_m14e_v1"
BINDING = AcceptedSourceBinding(
    findings_path=f"{SOURCE}/accepted_behavioral_findings.json",
    findings_document_sha256="94cf74ee03af627183ef01c6a2838fff76f6f8d17a15eb13d08c66249a98a441",
    authority_path=f"{SOURCE}/human_behavioral_candidate_authority.json",
    authority_document_sha256="dfc225a0bdf9cec24ce651acf644fd334a49ff357775937bc9cf4e96b14055c3",
)
FUNDING = "m14d:covered_china_linked_funding_exclusions"
HR1048 = "m14d:hr1048_substitute_and_package"
BARGAINING = "m14d:continuity_of_collective_bargaining"
CANDIDATE = "m14e:education_foreign_influence_mechanism_contrast"
SUMMARY = "Within the reviewed education foreign-influence record, Foushee opposed two proposals that would make educational institutions ineligible for specified federal funds because of China-linked relationships, while supporting an H.R. 1048 substitute that would impose detailed foreign-gift and contract reporting and compliance rules. Her later opposition to the distinct final H.R. 1048 package does not identify which broader provision she rejected and prevents treating these votes as a general position on foreign-influence regulation."
STANDALONE_REASON = "The accepted collective-bargaining pattern relates continuity of bargaining across two labor systems. It does not compare education funding eligibility with foreign-gift reporting and compliance. Shared education/workforce context supplies no safe mechanism relationship, so both labor episodes remain intentionally standalone."
COMPETING = "These may be bill-specific judgments rather than evidence of a durable regulatory preference beyond the reviewed actions. The measures differ in covered institutions, relationships, funds, waiver routes, and legal tools; the final H.R.1048 package contains several provisions, and its Nay cannot identify which one was rejected."
ALLOWED_PATHS = {
    "backend/app/semantic_ir/accepted_findings_synthesis.py",
    "backend/tests/test_accepted_findings_synthesis.py",
    "scripts/build_m14e_education_synthesis.py",
    "docs/plans/m14e_education_synthesis_review.md",
    ".github/workflows/backend-tests.yml",
    f"{OUT}/synthesis_candidate_package.json", f"{OUT}/review_package.json",
    "scripts/build_m14e_synthesis_acceptance.py",
    f"{OUT}/human_synthesis_authority.json", f"{OUT}/accepted_internal_synthesis.json",
}


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def proposal(findings: dict) -> dict:
    records = {r["proposition_id"]: r for r in findings["subject"]["accepted_proposition_records"]}
    return {
        "proposition_id": CANDIDATE, "proposition_type": "mechanism_divide", "summary": SUMMARY,
        "source_finding_ids": [FUNDING, HR1048], "material_limiter_finding_ids": [HR1048],
        "relationship_evidence": {
            "basis": "contrasting_policy_mechanisms", "claim_scope": "observed_reviewed_actions_only",
            "contrast": "The proposed relationship compares two specified funding-eligibility exclusions with a specific reporting/compliance substitute. It is grounded in the accepted policy mechanisms and contrasting choices, not just their foreign-influence topic. The substitute includes thresholds, enforcement through fines or compliance plans, exclusions, and negotiated rulemaking; it is not enforcement-free. The later Nay on the distinct whole package limits the comparison and cannot identify rejection of any component or establish a durable preference.",
            "mechanisms_by_finding": {
                FUNDING: {"mechanism": "funding_eligibility_restriction", "source_quote": records[FUNDING]["summary"]},
                HR1048: {"mechanism": "reporting_and_compliance", "source_quote": records[HR1048]["episode_semantic_evidence"]["hr-1048-amendment-and-final-passage"]},
            },
        },
        "competing_interpretation": COMPETING,
    }


def build_outputs() -> dict[str, bytes]:
    findings, authority = load(BINDING.findings_path), load(BINDING.authority_path)
    proposals, standalone = [proposal(findings)], {BARGAINING: STANDALONE_REASON}
    package = compile_detached_synthesis(findings, authority, BINDING, proposals, standalone)
    validate_detached_synthesis(package, findings, authority, BINDING, proposals, standalone)
    subject = package["subject"]
    records = {r["proposition_id"]: r for r in subject["accepted_source_findings"]}
    require(set(records) == {FUNDING, HR1048, BARGAINING}, "M14E must account for exactly three accepted findings")
    candidate = subject["synthesis_candidates"][0]
    ledger = subject["inherited_episode_disposition_ledger"]
    review = {
        "schema_version": "m14e_synthesis_review_package_v1", "baseline_main_sha": BASE,
        "artifact_role": "detached_non_authorizing_independent_review",
        "accepted": False, "authorizing": False, "public": False, "production_selectable": False,
        "decision_requested": "Independent ChatGPT/product review: retain, revise, or omit this single hypothesis. No acceptance is recorded here.",
        "candidate_package": {"path": f"{OUT}/synthesis_candidate_package.json", "package_sha256": package["package_sha256"]},
        "source_bindings": subject["accepted_source_binding"],
        "exact_candidate": deepcopy(candidate),
        "two_accepted_input_findings": [deepcopy(records[pid]) for pid in candidate["source_finding_ids"]],
        "standalone_finding": {"finding": deepcopy(records[BARGAINING]), "reason": STANDALONE_REASON},
        "source_finding_accounting": subject["source_finding_accounting"],
        "accounting_counts": {
            "accepted_source_findings": len(records), "primary_synthesis_findings": 2,
            "standalone_findings": 1, "candidate_episodes": candidate["evidence_counts"]["episodes"],
            "candidate_actions": candidate["evidence_counts"]["actions"],
            "all_source_finding_episodes": len({e for r in records.values() for e in r["evidence_episode_ids"]}),
            "all_source_finding_actions": len({a for r in records.values() for a in r["evidence_action_ids"]}),
            "inherited_ledger_episodes": len(ledger), "inherited_ledger_actions": len({a for r in ledger for a in r["action_ids"]}),
        },
        "inherited_ledger_sha256": digest(ledger),
        "inherited_episode_dispositions": dict(sorted(Counter(r["disposition"] for r in ledger).items())),
        "hr1048_final_passage_boundary": records[HR1048]["material_limitations"],
        "review_questions": [
            "Does this specific mechanism contrast add explanatory value beyond the two accepted findings?",
            "Is the substitute's enforcement/compliance substance preserved rather than portrayed as merely softer disclosure?",
            "Does the whole-package Nay remain a material limiter without assigning opposition to any component?",
            "Are bill-specific judgments a sufficient competing interpretation to revise or omit this hypothesis?",
            "Are the seven input limitations intact, with bargaining intentionally standalone and no inflated finding count?",
        ],
        "zero_candidate_outcome": "Mechanically valid: omit the candidate and account for all three accepted findings as intentionally standalone; no forced synthesis.",
        "accepted_synthesis_count": 0, "downstream_authorizations": DENIED.copy(),
    }
    return {f"{OUT}/synthesis_candidate_package.json": json_bytes(package),
            f"{OUT}/review_package.json": json_bytes(review | {"review_package_sha256": digest(review)})}


def validate_scope() -> None:
    changed = set(subprocess.check_output(["git", "diff", "--name-only", BASE], cwd=ROOT, text=True).splitlines())
    changed.update(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines())
    require(changed <= ALLOWED_PATHS, f"M14E scope violation: {sorted(changed - ALLOWED_PATHS)}")


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
            require(path.exists() and path.read_bytes().replace(b"\r\n", b"\n") == content, f"M14E artifact differs: {name}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists() or path.read_bytes().replace(b"\r\n", b"\n") != content:
                path.write_bytes(content)
    package = json.loads(outputs[f"{OUT}/synthesis_candidate_package.json"])
    candidate = package["subject"]["synthesis_candidates"][0]
    print(json.dumps({"mode": "check" if args.check else "build", "candidate_sha256": candidate["candidate_sha256"],
                      "evidence_counts": candidate["evidence_counts"], "accepted_synthesis_count": 0}, indent=2))


if __name__ == "__main__":
    main()
