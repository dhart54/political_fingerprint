"""Record/check the user-supplied PR180 wording and prominence decisions."""
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

from scripts import build_m14f_education_public_wording as m  # noqa: E402

REVIEWED = "f8997db8f0a5612795d22b0747d7f63721f901cd"
CANDIDATE_PATH = f"{m.OUT}/public_wording_candidate_package.json"
REVIEW_PATH = f"{m.OUT}/review_package.json"
AUTHORITY_PATH = f"{m.OUT}/human_public_wording_prominence_authority.json"
ACCEPTED_PATH = f"{m.OUT}/accepted_public_copy.json"
CANDIDATE_DOCUMENT_SHA = "f2e503b22435f90299ffcf5d0f082804fee81caaf0428a48a5306f2725b74de7"
CANDIDATE_PACKAGE_SHA = "235359361aced51a43cdd956dbaccaf8aab9ac4e1f2d07e028b331e906b483f1"
REVIEW_DOCUMENT_SHA = "f6950acbab9b08f93f88ec2510c6046de02579585c374ff8d02e967502b15432"
REVIEW_PACKAGE_SHA = "18fce10d408208e851ce5b94cd0ad49c2855bc1f7f09370a719d4e4b2f1c7865"
ITEM_SHAS = {
    m.OVERVIEW: "57c3ac7a93b136e6057ffee961f6e3a0611d004b5e2fd7a0aeaa6a53002aeae1",
    m.FUNDING_ITEM: "45500355c675fc5330b61988fe2a5f24c3967cf7aaaff846464561198fd26120",
    m.BARGAINING_ITEM: "eaec4f73c5bf2103f98ad8710a1330a98c239c163d3bc9f80ef1cfeb52a200cf",
    m.HR1048_ITEM: "87caf258fdae8fadc4420402094f0ff763aee85acb2249296dc0a23d8865dc73",
}
UPSTREAM_SUBJECTS = {
    "m14d_accepted_findings_subject_sha256": "795027fdcf49a4956b99804be9d44ec7bd233877e4bc76caa4121f7b61df169d",
    "m14d_human_authority_subject_sha256": "456d9f6f9577e8604480cdb40a08cb1f92e443ab3e02ff33cb2ecd193ca16638",
    "m14e_accepted_synthesis_subject_sha256": "efbd6105b9320cc8f16e203f16f2da37cd1f6acaf6eb6e7cd153f0c860d2a1ef",
    "m14e_human_synthesis_authority_subject_sha256": "a7e9e599100d4128b2a4414bd21a415d1663eb79d81d92397ddf056795668c82",
}
BOUNDARY = "The synthesis establishes only an observed mechanism contrast within the reviewed actions. It does not establish a durable or general preference for disclosure over enforcement, general opposition to funding restrictions, a general position on China or foreign-influence regulation, opposition to any particular component of final H.R.1048, or motive/ideology."
DOWNSTREAM_DENIED = {key: False for key in (
    "frontend_changes", "site_integration", "publication", "production_persistence",
    "database_writes", "production_writes", "deployment", "merge",
)}
CLOSURE_PATHS = {
    "scripts/build_m14f_public_wording_acceptance.py",
    "scripts/build_m14f_education_public_wording.py",
    "backend/tests/test_accepted_findings_public_wording.py",
    ".github/workflows/backend-tests.yml",
    "docs/plans/m14f_education_public_wording_review.md",
    AUTHORITY_PATH, ACCEPTED_PATH,
}


def load_reviewed_artifacts() -> tuple[dict, dict]:
    generated = m.build_outputs()
    for path in (CANDIDATE_PATH, REVIEW_PATH):
        raw = (ROOT / path).read_bytes()
        reviewed = subprocess.check_output(["git", "show", f"{REVIEWED}:{path}"], cwd=ROOT)
        m.require(raw == reviewed, f"{path} differs byte-for-byte from exact reviewed head")
        m.require(raw == generated[path], f"{path} differs from exact current-path generation")
    candidate, review = (json.loads((ROOT / path).read_text(encoding="utf-8"))
                         for path in (CANDIDATE_PATH, REVIEW_PATH))
    m.require(m.digest(candidate) == CANDIDATE_DOCUMENT_SHA
              and candidate["package_sha256"] == CANDIDATE_PACKAGE_SHA,
              "reviewed candidate package pin differs")
    m.require(m.digest(review) == REVIEW_DOCUMENT_SHA
              and review["review_package_sha256"] == REVIEW_PACKAGE_SHA,
              "review package pin differs")
    items = candidate["subject"]["wording_items"]
    m.require(len(items) == 4 and {item["wording_item_id"]: item["wording_item_sha256"]
                                  for item in items} == ITEM_SHAS,
              "exact four reviewed wording records differ")
    m.require(review["wording_items"] == items and review["wording_item_digests"] == ITEM_SHAS,
              "candidate and review wording records differ")
    actual_upstream_subjects = {
        "m14d_accepted_findings_subject_sha256":
            m.load(m.BINDING.findings_path)["findings_subject_sha256"],
        "m14d_human_authority_subject_sha256":
            m.load(m.BINDING.behavioral_authority_path)["authority_subject_sha256"],
        "m14e_accepted_synthesis_subject_sha256":
            m.load(m.BINDING.synthesis_path)["accepted_internal_synthesis_subject_sha256"],
        "m14e_human_synthesis_authority_subject_sha256":
            m.load(m.BINDING.synthesis_authority_path)["authority_subject_sha256"],
    }
    m.require(actual_upstream_subjects == UPSTREAM_SUBJECTS,
              "accepted M14D/M14E subject binding differs")
    return candidate, review


def limitation_rows(candidate: dict) -> list[dict]:
    return [{"wording_item_id": item["wording_item_id"],
             "limitation_treatments": deepcopy(item["limitation_treatments"])}
            for item in candidate["subject"]["wording_items"]]


def expected_authority(candidate: dict, review: dict) -> dict:
    m.require(m.digest(candidate) == CANDIDATE_DOCUMENT_SHA, "reviewed candidate package pin differs")
    m.require(m.digest(review) == REVIEW_DOCUMENT_SHA, "review package pin differs")
    items = candidate["subject"]["wording_items"]
    treatments = [row for item in items for row in item["limitation_treatments"]]
    counts = Counter(row["treatment"] for row in treatments)
    m.require(len(treatments) == 18 and counts == {
        "retained_public_copy": 7, "compressed_or_omitted": 11},
        "limitation accounting differs")
    m.require(all(row["public_copy"] and row["reason"] is None for row in treatments
                  if row["treatment"] == "retained_public_copy"),
              "retained public copy differs")
    m.require(all(row["public_copy"] is None and row["reason"] for row in treatments
                  if row["treatment"] == "compressed_or_omitted"),
              "compressed limitation differs")
    context = candidate["subject"]["prominence_review"]["record_context"]
    m.require(context == m.prominence_review()["record_context"], "prominence lineage differs")
    subject = {
        "pr_number": 180,
        "baseline_main_sha": m.BASE,
        "reviewed_candidate_head": REVIEWED,
        "reviewed_candidate_package": {
            "path": CANDIDATE_PATH, "document_sha256": CANDIDATE_DOCUMENT_SHA,
            "package_sha256": CANDIDATE_PACKAGE_SHA,
        },
        "reviewed_review_package": {
            "path": REVIEW_PATH, "document_sha256": REVIEW_DOCUMENT_SHA,
            "review_package_sha256": REVIEW_PACKAGE_SHA,
        },
        "wording_decisions": [
            {"wording_item_id": item["wording_item_id"],
             "reviewed_wording_item_sha256": item["wording_item_sha256"],
             "decision": "accept_wording_as_written"}
            for item in items
        ],
        "decision_accounting": {
            "accept_wording_as_written": 4, "revised": 0, "rejected": 0},
        "upstream_accepted_subjects": UPSTREAM_SUBJECTS.copy(),
        "accepted_semantic_source_binding": deepcopy(
            candidate["subject"]["accepted_source_binding"]),
        "limitation_treatments_by_wording_item": limitation_rows(candidate),
        "limitation_treatment_accounting": {
            "total": 18, "retained_public_copy": 7, "compressed_or_omitted": 11},
        "lineage_accounting": deepcopy(review["lineage_counts"]),
        "prominence_decision": {
            "option": "A", "decision": "accept_main_takeaway",
            "wording_item_id": m.OVERVIEW,
            "record_context": deepcopy(context),
            "standalone_finding_preserved": m.BARGAINING,
            "scope": "On foreign influence in education",
        },
        "decision_source": "user_supplied_M14F_human_product_review_PR180",
        "authority_effect": "canonical_internal_public_copy_and_main_takeaway_selection_only",
        "substantive_boundary": BOUNDARY,
        "downstream_operational_authorizations": DOWNSTREAM_DENIED.copy(),
    }
    return {
        "schema_version": "m14f_human_public_wording_prominence_authority_v1",
        "artifact_id": "human-public-wording-prominence-authority:f000477:education_workforce:m14f:v1",
        "artifact_role": "immutable_user_supplied_public_wording_and_prominence_decision",
        "immutable": True,
        "subject": subject,
        "authority_subject_sha256": m.digest(subject),
    }


def accepted_artifact(candidate: dict, review: dict, authority: dict) -> dict:
    m.require(authority == expected_authority(candidate, review),
              "immutable M14F wording authority differs")
    source = candidate["subject"]
    items = source["wording_items"]
    subject = {
        "human_public_wording_prominence_authority": {
            "path": AUTHORITY_PATH, "artifact_id": authority["artifact_id"],
            "authority_subject_sha256": authority["authority_subject_sha256"],
        },
        "reviewed_candidate_package": deepcopy(authority["subject"]["reviewed_candidate_package"]),
        "reviewed_review_package": deepcopy(authority["subject"]["reviewed_review_package"]),
        "accepted_wording_count": 4,
        "accepted_wording_records": deepcopy(items),
        "wording_item_digests": ITEM_SHAS.copy(),
        "semantic_sources_by_wording_item": [
            {"wording_item_id": item["wording_item_id"],
             "semantic_source_id": item["semantic_source_id"],
             "semantic_source": deepcopy(item["semantic_source"])} for item in items],
        "source_lineage_by_wording_item": [
            {"wording_item_id": item["wording_item_id"],
             "derived_lineage": deepcopy(item["derived_lineage"])} for item in items],
        "limitation_treatments_by_wording_item": limitation_rows(candidate),
        "limitation_treatment_accounting": deepcopy(
            authority["subject"]["limitation_treatment_accounting"]),
        "selected_main_takeaway_count": 1,
        "selected_main_takeaway_wording_item_id": m.OVERVIEW,
        "prominence_decision": deepcopy(authority["subject"]["prominence_decision"]),
        "standalone_behavioral_finding": {
            "source_finding_id": m.BARGAINING,
            "wording_item_id": m.BARGAINING_ITEM,
            "disposition": "independent_behavioral_finding_outside_main_takeaway",
        },
        "excluded_non_directional_receipts": deepcopy(source["excluded_non_directional_receipts"]),
        "behavioral_finding_accounting": deepcopy(source["behavioral_finding_accounting"]),
        "lineage_accounting": deepcopy(review["lineage_counts"]),
        "hr1048_mixed_episode": {
            "wording_item_id": m.HR1048_ITEM, "episodes": 1, "actions": 2,
            "direction_display": {"label": "Mixed", "symbol": "±"}},
        "authority_effect": "canonical_internal_public_copy_and_main_takeaway_selection_only",
        "substantive_boundary": BOUNDARY,
        "copied_candidate_downstream_flag_interpretation": "Any acceptance-named false flags inside the copied reviewed wording records describe downstream delegation from those pre-acceptance candidate records. They do not negate the explicit human wording and prominence decisions recorded by the bound authority and this accepted artifact.",
        "candidate_provenance_note": "The exact reviewed wording records retain their non-authorizing pre-acceptance flags. Only this artifact and its bound user-supplied human authority confer canonical internal public-copy and Main Takeaway acceptance; no downstream operational authority is conferred.",
        "downstream_operational_authorizations": DOWNSTREAM_DENIED.copy(),
    }
    return {
        "schema_version": "m14f_accepted_public_copy_v1",
        "artifact_id": "accepted-public-copy:f000477:education_workforce:m14f:v1",
        "artifact_role": "human_accepted_canonical_internal_public_copy",
        "accepted": True, "canonical_public_copy": True,
        "public": False, "production_selectable": False,
        "subject": subject,
        "accepted_public_copy_subject_sha256": m.digest(subject),
    }


def validate_artifacts(candidate: dict, review: dict, authority: dict, accepted: dict) -> None:
    m.require(accepted == accepted_artifact(candidate, review, authority),
              "accepted M14F public copy differs from exact authority")


def record_authority(candidate: dict, review: dict) -> None:
    """Materialize only this supplied decision, once; never overwrite it."""
    authority = expected_authority(candidate, review)
    with (ROOT / AUTHORITY_PATH).open("xb") as stream:
        stream.write(m.json_bytes(authority))


def build_outputs(*, record_human_decision: bool = False) -> dict[str, bytes]:
    candidate, review = load_reviewed_artifacts()
    if record_human_decision:
        record_authority(candidate, review)
    authority = m.load(AUTHORITY_PATH)
    accepted = accepted_artifact(candidate, review, authority)
    validate_artifacts(candidate, review, authority, accepted)
    return {AUTHORITY_PATH: m.json_bytes(authority), ACCEPTED_PATH: m.json_bytes(accepted)}


def validate_scope() -> None:
    changed = set(subprocess.check_output(
        ["git", "diff", "--name-only", REVIEWED], cwd=ROOT, text=True).splitlines())
    changed.update(subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines())
    m.require(changed <= CLOSURE_PATHS,
              f"M14F acceptance scope violation: {sorted(changed - CLOSURE_PATHS)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-scope", action="store_true")
    parser.add_argument("--record-human-decision", action="store_true",
                        help="write the exact supplied PR180 decision once; refuses overwrite")
    args = parser.parse_args()
    m.require(not (args.check and args.record_human_decision),
              "check mode cannot record authority")
    if args.check_scope:
        validate_scope()
    outputs = build_outputs(record_human_decision=args.record_human_decision)
    for name, content in outputs.items():
        path = ROOT / name
        if args.check or name == AUTHORITY_PATH:
            m.require(path.exists() and path.read_bytes() == content,
                      f"M14F acceptance artifact differs: {name}")
        elif not path.exists() or path.read_bytes() != content:
            path.write_bytes(content)
    authority, accepted = (json.loads(outputs[path])
                           for path in (AUTHORITY_PATH, ACCEPTED_PATH))
    print(json.dumps({
        "accepted_wording_count": 4,
        "selected_main_takeaway_wording_item_id": m.OVERVIEW,
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "accepted_public_copy_subject_sha256":
            accepted["accepted_public_copy_subject_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
