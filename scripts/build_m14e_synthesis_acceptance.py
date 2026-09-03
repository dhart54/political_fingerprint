"""Record/check the single user-supplied PR179 accept-as-written decision."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_m14e_education_synthesis as m  # noqa: E402

REVIEWED = "0fe441871909b425248ec2e7e9100236bd9b62b2"
CANDIDATE_SHA = "e1f897237de6934c96f034205b4e2fdf6b73afafbe6081507c5d3861180bdc4d"
PACKAGE_PATH = f"{m.OUT}/synthesis_candidate_package.json"
PACKAGE_DOCUMENT_SHA = "7b7a88021cdb285f93785c8ae3305334bda320337c9ca9083a7c099f7565e2d0"
AUTHORITY_PATH = f"{m.OUT}/human_synthesis_authority.json"
ACCEPTED_PATH = f"{m.OUT}/accepted_internal_synthesis.json"
DENIED = m.DENIED | {"production_writes": False}
BOUNDARY = "The accepted synthesis establishes only an observed mechanism contrast within the reviewed actions. It does not establish a durable or general preference for disclosure over enforcement, general opposition to funding restrictions, a general position on China or foreign-influence regulation, opposition to any particular component of final H.R.1048, or motive/ideology."
CLOSURE_PATHS = {
    "scripts/build_m14e_synthesis_acceptance.py", "scripts/build_m14e_education_synthesis.py",
    "backend/tests/test_accepted_findings_synthesis.py", ".github/workflows/backend-tests.yml",
    "docs/plans/m14e_education_synthesis_review.md", AUTHORITY_PATH, ACCEPTED_PATH,
}


def load_reviewed_package() -> dict:
    # Check the existing generation path without rewriting either reviewed file.
    for name, content in m.build_outputs().items():
        m.require((ROOT / name).read_bytes().replace(b"\r\n", b"\n") == content,
                  f"reviewed M14E output changed: {name}")
    raw = (ROOT / PACKAGE_PATH).read_bytes().replace(b"\r\n", b"\n")
    reviewed = subprocess.check_output(["git", "show", f"{REVIEWED}:{PACKAGE_PATH}"], cwd=ROOT)
    m.require(raw == reviewed, "candidate package differs from exact reviewed head")
    package = json.loads(raw)
    m.require(m.digest(package) == PACKAGE_DOCUMENT_SHA, "reviewed package pin differs")
    return package


def expected_authority(package: dict) -> dict:
    m.require(m.digest(package) == PACKAGE_DOCUMENT_SHA, "reviewed package pin differs")
    subject = package["subject"]
    candidates = subject["synthesis_candidates"]
    m.require(len(candidates) == 1, "exactly one reviewed synthesis required")
    candidate = candidates[0]
    m.require(candidate["proposition_id"] == m.CANDIDATE and candidate["candidate_sha256"] == CANDIDATE_SHA
              and m.digest({k: v for k, v in candidate.items() if k != "candidate_sha256"}) == CANDIDATE_SHA,
              "accepted candidate identity differs")
    accepted = {
        "pr_number": 179, "baseline_main_sha": m.BASE, "reviewed_candidate_head": REVIEWED,
        "candidate_id": m.CANDIDATE, "candidate_sha256": CANDIDATE_SHA,
        "reviewed_package": {"path": PACKAGE_PATH, "document_sha256": m.digest(package),
                             "package_sha256": package["package_sha256"],
                             "file_lf_sha256": hashlib.sha256(m.json_bytes(package)).hexdigest()},
        "m14d_accepted_source_binding": deepcopy(subject["accepted_source_binding"]),
        "source_finding_accounting": deepcopy(subject["source_finding_accounting"]),
        "source_finding_record_digests": [
            {"source_finding_id": r["source_finding_id"], "accepted_record_sha256": r["accepted_record_sha256"],
             "disposition": r["disposition"], "material_limiter": r["material_limiter"]}
            for r in subject["source_finding_accounting"]],
        "inherited_ledger": {"source_package_path": PACKAGE_PATH,
                             "field": "subject.inherited_episode_disposition_ledger",
                             "sha256": m.digest(subject["inherited_episode_disposition_ledger"]),
                             "episodes": 16, "actions": 17},
        "decision": "accept_as_written", "decision_source": "user_supplied_M14E_human_product_review_PR179",
        "authority_effect": "canonical_internal_synthesis_only", "substantive_boundary": BOUNDARY,
        "downstream_authorizations": DENIED.copy(),
    }
    return {"schema_version": "m14e_human_synthesis_authority_v1",
            "artifact_id": "human-synthesis-authority:f000477:education_workforce:m14e:v1",
            "artifact_role": "immutable_user_supplied_human_synthesis_decision", "immutable": True,
            "subject": accepted, "authority_subject_sha256": m.digest(accepted)}


def accepted_artifact(package: dict, authority: dict) -> dict:
    m.require(authority == expected_authority(package), "immutable M14E synthesis authority differs")
    subject = package["subject"]
    candidate = subject["synthesis_candidates"][0]
    records = {r["proposition_id"]: r for r in subject["accepted_source_findings"]}
    standalone = next(r for r in subject["source_finding_accounting"] if r["source_finding_id"] == m.BARGAINING)
    accepted = {
        "human_synthesis_authority": {"path": AUTHORITY_PATH, "artifact_id": authority["artifact_id"],
                                      "authority_subject_sha256": authority["authority_subject_sha256"]},
        "reviewed_package": deepcopy(authority["subject"]["reviewed_package"]),
        "accepted_synthesis_count": 1, "accepted_synthesis_records": [deepcopy(candidate)],
        "candidate_sha256": CANDIDATE_SHA,
        "accepted_input_findings": [deepcopy(records[pid]) for pid in candidate["source_finding_ids"]],
        "intentionally_standalone_finding": {"finding": deepcopy(records[m.BARGAINING]), "accounting": deepcopy(standalone)},
        "source_finding_accounting": deepcopy(subject["source_finding_accounting"]),
        "source_lineage": deepcopy(candidate["source_lineage"]), "evidence_counts": deepcopy(candidate["evidence_counts"]),
        "inherited_episode_disposition_ledger": deepcopy(subject["inherited_episode_disposition_ledger"]),
        "inherited_material_limitations": deepcopy(candidate["inherited_material_limitations"]),
        "competing_interpretation": candidate["competing_interpretation"],
        "prohibited_inferences": deepcopy(candidate["prohibited_inferences"]),
        "hr1048_final_passage_limitation": records[m.HR1048]["material_limitations"][1],
        "authority_effect": "canonical_internal_synthesis_only", "substantive_boundary": BOUNDARY,
        "candidate_provenance_note": "The exact reviewed candidate record retains its non-authorizing pre-acceptance flags. Only this artifact and its bound user-supplied human synthesis authority confer canonical internal acceptance; no downstream authority is conferred.",
        "downstream_authorizations": DENIED.copy(),
    }
    return {"schema_version": "m14e_accepted_internal_synthesis_v1",
            "artifact_id": "accepted-internal-synthesis:f000477:education_workforce:m14e:v1",
            "artifact_role": "human_accepted_canonical_internal_synthesis",
            "accepted": True, "canonical_internal_synthesis": True, "public": False, "production_selectable": False,
            "subject": accepted, "accepted_internal_synthesis_subject_sha256": m.digest(accepted)}


def validate_artifacts(package: dict, authority: dict, accepted: dict) -> None:
    m.require(accepted == accepted_artifact(package, authority), "accepted internal synthesis differs from exact authority")


def record_authority(package: dict) -> None:
    """Materialize only this supplied decision, once; never overwrite authority."""
    authority = expected_authority(package)
    with (ROOT / AUTHORITY_PATH).open("xb") as stream:
        stream.write(m.json_bytes(authority))


def build_outputs(*, record_human_decision: bool = False) -> dict[str, bytes]:
    package = load_reviewed_package()
    if record_human_decision:
        record_authority(package)
    authority = m.load(AUTHORITY_PATH)
    accepted = accepted_artifact(package, authority)
    validate_artifacts(package, authority, accepted)
    return {AUTHORITY_PATH: m.json_bytes(authority), ACCEPTED_PATH: m.json_bytes(accepted)}


def validate_scope() -> None:
    changed = set(subprocess.check_output(["git", "diff", "--name-only", REVIEWED], cwd=ROOT, text=True).splitlines())
    changed.update(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines())
    m.require(changed <= CLOSURE_PATHS, f"M14E acceptance scope violation: {sorted(changed - CLOSURE_PATHS)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-scope", action="store_true")
    parser.add_argument("--record-human-decision", action="store_true", help="write the exact supplied PR179 decision once; refuses overwrite")
    args = parser.parse_args()
    m.require(not (args.check and args.record_human_decision), "check mode cannot record authority")
    if args.check_scope:
        validate_scope()
    outputs = build_outputs(record_human_decision=args.record_human_decision)
    for name, content in outputs.items():
        path = ROOT / name
        if args.check or name == AUTHORITY_PATH:
            m.require(path.exists() and path.read_bytes().replace(b"\r\n", b"\n") == content, f"M14E acceptance artifact differs: {name}")
        elif not path.exists() or path.read_bytes().replace(b"\r\n", b"\n") != content:
            path.write_bytes(content)
    authority, accepted = (json.loads(outputs[p]) for p in (AUTHORITY_PATH, ACCEPTED_PATH))
    print(json.dumps({"accepted_synthesis_count": 1, "candidate_sha256": CANDIDATE_SHA,
                      "authority_subject_sha256": authority["authority_subject_sha256"],
                      "accepted_internal_synthesis_subject_sha256": accepted["accepted_internal_synthesis_subject_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
