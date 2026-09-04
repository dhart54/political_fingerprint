"""Record and verify the user-supplied PR181 M14G site-integration acceptance."""
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

from backend.app.editorial_presentations.compiler import canonical_digest  # noqa: E402

OUT = "docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1"
CANDIDATE_PATH = f"{OUT}/site_integration_candidate.json"
REVIEW_PATH = f"{OUT}/review_package.json"
MANIFEST_PATH = f"{OUT}/screenshot_manifest.json"
AUTHORITY_PATH = f"{OUT}/human_site_integration_authority.json"
ACCEPTED_PATH = f"{OUT}/accepted_site_integration.json"
BASE = "50777a5fd1ce84763e6a294db25578639aa5dce7"
REVIEWED = "cfe9e54fa618d92e82dd0a262359e9fa5631b207"
CAPTURE_HEAD = "b90824b5fd14d719c47545fca650fad2933a1ebb"
CANDIDATE_SUBJECT = "92d491a97ff675d60896d64fe3cb9e5d9e87ffc684f19f151a13f01b99ab05d0"
FILE_DIGESTS = {
    CANDIDATE_PATH: "7022fff0cbd8e54acab095401c2810b93359c3a55d8a5a03eba86e4e6d14d2c6",
    REVIEW_PATH: "35376319e9a556c82a217da7d70b9b128236325f084b1d630aaa1030d07acb4e",
    MANIFEST_PATH: "cd8fdec5048cade1f731d14746c9008e86181f52afbc62acf7530c37ded44208",
}
DOCUMENT_DIGESTS = {
    CANDIDATE_PATH: "76d06a43beb51c164a199c576c3d0aa539b6c05da2f8e4eff8fe54845547e4ec",
    REVIEW_PATH: "531c454efa59482da03cf3a72e0ff6563e0a411708c8d9e3d2118adf537ed85b",
    MANIFEST_PATH: "6324d9ff5afb8454efe27642a76875bb7cb173009990d64e30911b399031c5eb",
}
SCREENSHOTS = {
    f"{OUT}/screenshots/desktop_overview.png": "93e47c314176ee94c54bb90e23121a4c7f0afc57fef8f47fd0011a015dbf6a73",
    f"{OUT}/screenshots/desktop_notable_expanded.png": "099f5ceeac742cabfbcc2ecce1ebe9742c3646a062ac3bfb2bed4d6dd6330fba",
    f"{OUT}/screenshots/desktop_hr5408_receipt.png": "2dc10d3a7edaed6df15e1eabd29bce922df072cf4b29b2b985d9b4851b212c09",
    f"{OUT}/screenshots/mobile_overview.png": "9f3694c956ea4881b54ca27bec7943fdcbc008b8953d5519242077d48b5a73e3",
}
WORDING = {
    "m14f:issue_overview:education_workforce": "57c3ac7a93b136e6057ffee961f6e3a0611d004b5e2fd7a0aeaa6a53002aeae1",
    "m14f:pattern:china_linked_education_funding": "45500355c675fc5330b61988fe2a5f24c3967cf7aaaff846464561198fd26120",
    "m14f:pattern:collective_bargaining_continuity": "eaec4f73c5bf2103f98ad8710a1330a98c239c163d3bc9f80ef1cfeb52a200cf",
    "m14f:notable:hr1048_substitute_final": "87caf258fdae8fadc4420402094f0ff763aee85acb2249296dc0a23d8865dc73",
}
UPSTREAM = {
    "m14f_accepted_public_copy_subject_sha256": "4fed310450608f1465f2617721e7665670d855f70cbcd50471aa46fc7cac0810",
    "m14f_human_authority_subject_sha256": "9b1962e1d33dd144a609cd9cbcb5114f81c51a8ce4195bc24112ba9fb10d0cfb",
    "m14d_accepted_findings_subject_sha256": "795027fdcf49a4956b99804be9d44ec7bd233877e4bc76caa4121f7b61df169d",
    "m14d_human_authority_subject_sha256": "456d9f6f9577e8604480cdb40a08cb1f92e443ab3e02ff33cb2ecd193ca16638",
    "v2_shared_action_core_subject_sha256": "fc7b376cd3e0b485e0ac28c15ba7a5111a1e41c4855a3cbb99354b4ac04d0aa2",
    "v2_member_projection_subject_sha256": "d1ad8f68ca8a419427ce23e6b0c870c02a450de0ae3309df33db691c78e46892",
    "v2_promotion_manifest_subject_sha256": "0ec2ffd7e5ee3f86c7386f61b7af5c0682cdbe66fb5d18283ebbfce6139d2298",
}
DOWNSTREAM = {key: False for key in (
    "publication", "publication_preparation", "publication_eligibility",
    "production_selectable", "production_persistence", "database_writes",
    "production_writes", "public_activation", "deployment", "live_activation", "merge",
)}
BOUNDARY = ("Acceptance is limited to the exact reviewed site-integration presentation. "
            "It does not convert the scoped Main Takeaway into an issue-wide ideological characterization.")
SOURCE_ROWS = [
    {"canonical_action_id": "house:119:1:332", "source_id": "govinfo:FR-2025-04-03:2025-05836:EO14251", "source_type": "federal_register_executive_order", "public_label": "Executive order", "url": "https://www.govinfo.gov/content/pkg/FR-2025-04-03/html/2025-05836.htm"},
    {"canonical_action_id": "house:119:2:184", "source_id": "govinfo:FR-2025-01-30:2025-02090:EO14168", "source_type": "federal_register_executive_order", "public_label": "Executive order", "url": "https://www.govinfo.gov/content/pkg/FR-2025-01-30/html/2025-02090.htm"},
    {"canonical_action_id": "house:119:1:79", "source_id": "govinfo:USCODE-2024-title20:sec1094:e2Bii", "source_type": "united_states_code", "public_label": "U.S. Code", "url": "https://www.govinfo.gov/content/pkg/USCODE-2024-title20/html/USCODE-2024-title20-chap28-subchapIV-partG-sec1094.htm"},
]
H5408_PREFIX = "Current wages, hours, and employment terms would have to be maintained"
CLOSURE_PATHS = {".github/workflows/backend-tests.yml", "scripts/validate_m14g_education_workforce_site_integration.py", "scripts/build_m14g_site_integration_acceptance.py", "backend/tests/test_m14g_site_integration_acceptance.py", AUTHORITY_PATH, ACCEPTED_PATH}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def file_digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def receipt(candidate: dict, action_id: str) -> dict:
    return next(row for row in candidate["subject"]["receipt_projections"]
                if row["canonical_action_id"] == action_id)


def validate_reviewed(candidate: dict, review: dict, manifest: dict) -> None:
    require(canonical_digest(candidate) == DOCUMENT_DIGESTS[CANDIDATE_PATH], "candidate document differs")
    require(canonical_digest(review) == DOCUMENT_DIGESTS[REVIEW_PATH], "review package document differs")
    require(canonical_digest(manifest) == DOCUMENT_DIGESTS[MANIFEST_PATH], "screenshot manifest document differs")
    require(candidate["candidate_subject_sha256"] == CANDIDATE_SUBJECT, "candidate subject differs")
    require(canonical_digest(candidate["subject"]) == CANDIDATE_SUBJECT, "candidate subject seal differs")
    require(candidate["subject"]["accepted_wording_item_sha256s"] == WORDING, "wording identities differ")
    bindings = candidate["subject"]["input_bindings"]
    actual_upstream = {
        "m14f_accepted_public_copy_subject_sha256": bindings["m14f_accepted_public_copy"]["subject_sha256"],
        "m14f_human_authority_subject_sha256": bindings["m14f_human_authority"]["subject_sha256"],
        "m14d_accepted_findings_subject_sha256": bindings["m14d_accepted_ledger"]["subject_sha256"],
        "m14d_human_authority_subject_sha256": bindings["m14d_human_authority"]["subject_sha256"],
        "v2_shared_action_core_subject_sha256": bindings["v2_shared_action_core"]["subject_sha256"],
        "v2_member_projection_subject_sha256": bindings["v2_member_projection"]["subject_sha256"],
        "v2_promotion_manifest_subject_sha256": bindings["v2_promotion_manifest"]["subject_sha256"],
    }
    require(actual_upstream == UPSTREAM, "upstream accepted subject bindings differ")
    p = candidate["subject"]["presentation"]
    require((len(p["repeated_patterns"]), len(p["notable_choices"]), len(p["syntheses"]), len(p["policy_trajectories"])) == (2, 1, 0, 0), "presentation hierarchy differs")
    require(all(row["direction"] is None and not row["show_direction"] for row in p["repeated_patterns"]), "pattern direction display differs")
    require(p["notable_choices"][0]["direction_label"] == "Mixed" and len(p["notable_choices"][0]["action_ids"]) == 2 and len(p["notable_choices"][0]["episode_ids"]) == 1, "H.R.1048 presentation differs")
    receipt_rows = candidate["subject"]["receipt_projections"]
    require(len(receipt_rows) == 17 and len({row["governed_receipt_projection"]["episode_id"] for row in receipt_rows}) == 16, "receipt accounting differs")
    require(len(p["evidence_metadata"]["display_action_ids"]) == 6, "finding-supporting action count differs")
    require(len(p["overview"]["action_ids"]) == 4 and len(p["overview"]["episode_ids"]) == 3 and len(p["overview"]["semantic_source_ids"]) == 1, "Main Takeaway lineage differs")
    require(review["rendered_hierarchy"]["counts"]["findings"] == 3, "finding count differs")
    require(review["rendered_limitations_by_surface"]["treatment_instance_count"] == 7, "rendered limitation count differs")
    require(review["hr1005_non_directional_proof"] == {"canonical_action_id": "house:119:1:312", "exact_choice_effect": "resolved_non_directional", "official_status": "Not Voting", "supports_finding": False}, "H.R.1005 state differs")
    require(receipt(candidate, "house:119:2:216")["governed_receipt_projection"]["exact_action_meaning"].startswith(H5408_PREFIX), "H.R.5408 meaning differs")
    require(manifest["source_head_at_capture"] == CAPTURE_HEAD, "capture head differs")
    require({row["repo_path"]: row["file_sha256"] for row in manifest["captures"]} == SCREENSHOTS, "screenshot bindings differ")
    for expected in SOURCE_ROWS:
        row = receipt(candidate, expected["canonical_action_id"])
        require(any(source["source_id"] == expected["source_id"] and source["source_type"] == expected["source_type"] for source in row["source_identity_bindings"]["governed_action_meaning"]), "source identity differs")
        require(any(source["url"] == expected["url"] and source["public_label"] == expected["public_label"] for source in row["governed_receipt_projection"]["action_meaning_sources"]), "source URL or public label differs")
    for key in ("accepted", "authorizing", "public", "production_selectable", "publication_eligible", "publication_active", "database_writes", "production_writes", "deployment"):
        require(candidate[key] is False, f"reviewed candidate control changed: {key}")


def load_reviewed_artifacts() -> tuple[dict, dict, dict]:
    for path, expected in {**FILE_DIGESTS, **SCREENSHOTS}.items():
        raw = (ROOT / path).read_bytes()
        reviewed = subprocess.check_output(["git", "show", f"{REVIEWED}:{path}"], cwd=ROOT)
        require(raw == reviewed, f"{path} differs byte-for-byte from reviewed head")
        require(file_digest(raw) == expected, f"{path} complete file digest differs")
    artifacts = tuple(load(path) for path in (CANDIDATE_PATH, REVIEW_PATH, MANIFEST_PATH))
    validate_reviewed(*artifacts)
    return artifacts


def presentation_accounting(candidate: dict, review: dict) -> dict:
    p = candidate["subject"]["presentation"]
    return {"overviews": 1, "repeated_patterns": 2, "directionless_repeated_patterns": 2,
            "notable_choices": 1, "hr1048_direction_label": "Mixed", "syntheses": 0,
            "trajectories": 0, "findings": 3, "main_takeaway_linked_findings": 2,
            "main_takeaway_actions": len(p["overview"]["action_ids"]),
            "main_takeaway_episodes": len(p["overview"]["episode_ids"]),
            "rendered_retained_limitation_instances": review["rendered_limitations_by_surface"]["treatment_instance_count"]}


def receipt_accounting(candidate: dict) -> dict:
    p = candidate["subject"]["presentation"]
    return {"reviewed_actions": 17, "reviewed_episodes": 16,
            "finding_supporting_actions": 6,
            "finding_supporting_action_ids": deepcopy(p["evidence_metadata"]["display_action_ids"]),
            "main_takeaway_action_ids": deepcopy(p["overview"]["action_ids"])}


def source_contract() -> dict:
    return {"allowed_action_source_labels": ["Bill or amendment text", "Congressional Record", "Executive order", "U.S. Code", "Official cost estimate", "Official report", "Official law text"],
            "arbitrary_public_label_behavior": "reject_by_ignoring_and_use_url_derived_label",
            "absent_public_label_behavior": "use_prior_url_derived_label",
            "accepted_sources": deepcopy(SOURCE_ROWS)}


def expected_authority(candidate: dict, review: dict, manifest: dict) -> dict:
    validate_reviewed(candidate, review, manifest)
    subject = {
        "pr_number": 181, "baseline_main_sha": BASE, "reviewed_candidate_head": REVIEWED,
        "decision": "accept_as_rendered", "decision_source": "user_supplied_M14G_human_product_review_PR181",
        "authority_effect": "canonical_internal_site_integration_candidate_only",
        "reviewed_candidate": {"path": CANDIDATE_PATH, "artifact_id": candidate["artifact_id"], "candidate_subject_sha256": CANDIDATE_SUBJECT, "complete_file_sha256": FILE_DIGESTS[CANDIDATE_PATH]},
        "reviewed_review_package": {"path": REVIEW_PATH, "artifact_id": review["artifact_id"], "complete_file_sha256": FILE_DIGESTS[REVIEW_PATH]},
        "reviewed_screenshot_manifest": {"path": MANIFEST_PATH, "artifact_id": manifest["artifact_id"], "complete_file_sha256": FILE_DIGESTS[MANIFEST_PATH], "capture_head": CAPTURE_HEAD},
        "screenshot_bindings": [{"path": path, "file_sha256": sha} for path, sha in SCREENSHOTS.items()],
        "wording_item_sha256s": WORDING.copy(), "upstream_accepted_subjects": UPSTREAM.copy(),
        "preview_token": "m14g-education-workforce",
        "presentation_accounting": presentation_accounting(candidate, review),
        "receipt_accounting": receipt_accounting(candidate),
        "receipt_state_bindings": {"hr1005": deepcopy(review["hr1005_non_directional_proof"]), "hr1048": deepcopy(review["hr1048_one_episode_proof"]), "hr5408_exact_action_meaning": deepcopy(review["hr5408_governed_receipt"]["exact_action_meaning"])},
        "source_label_contract": source_contract(), "substantive_boundary": BOUNDARY,
        "downstream_authorizations": DOWNSTREAM.copy(),
    }
    return {"schema_version": "m14g_human_site_integration_authority_v1", "artifact_id": "human-site-integration-authority:f000477:education_workforce:m14g:v1", "artifact_role": "immutable_user_supplied_site_integration_decision", "immutable": True, "public": False, **DOWNSTREAM, "subject": subject, "authority_subject_sha256": canonical_digest(subject)}


def accepted_artifact(candidate: dict, review: dict, manifest: dict, authority: dict) -> dict:
    require(authority == expected_authority(candidate, review, manifest), "immutable M14G site-integration authority differs")
    a = authority["subject"]
    subject = {
        "human_site_integration_authority": {"path": AUTHORITY_PATH, "artifact_id": authority["artifact_id"], "authority_subject_sha256": authority["authority_subject_sha256"]},
        "reviewed_candidate": deepcopy(a["reviewed_candidate"]),
        "reviewed_review_package": deepcopy(a["reviewed_review_package"]),
        "reviewed_screenshot_manifest": deepcopy(a["reviewed_screenshot_manifest"]),
        "screenshot_bindings": deepcopy(a["screenshot_bindings"]),
        "presentation_accounting": deepcopy(a["presentation_accounting"]),
        "receipt_accounting": deepcopy(a["receipt_accounting"]),
        "wording_item_sha256s": deepcopy(a["wording_item_sha256s"]),
        "upstream_accepted_subjects": deepcopy(a["upstream_accepted_subjects"]),
        "receipt_state_bindings": deepcopy(a["receipt_state_bindings"]),
        "source_label_contract": deepcopy(a["source_label_contract"]),
        "authority_effect": a["authority_effect"], "substantive_boundary": BOUNDARY,
        "downstream_authorizations": DOWNSTREAM.copy(),
    }
    return {"schema_version": "m14g_accepted_site_integration_v1", "artifact_id": "accepted-site-integration:f000477:education_workforce:m14g:v1", "artifact_role": "human_accepted_canonical_internal_site_integration", "accepted": True, "canonical_internal_site_integration": True, "public": False, **DOWNSTREAM, "subject": subject, "accepted_site_integration_subject_sha256": canonical_digest(subject)}


def validate_scope() -> None:
    changed = set(subprocess.check_output(["git", "diff", "--name-only", REVIEWED], cwd=ROOT, text=True).splitlines())
    changed.update(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines())
    require(changed <= CLOSURE_PATHS, f"M14G acceptance scope violation: {sorted(changed - CLOSURE_PATHS)}")


def build_outputs(*, record_human_decision: bool = False) -> dict[str, bytes]:
    candidate, review, manifest = load_reviewed_artifacts()
    expected = expected_authority(candidate, review, manifest)
    if record_human_decision:
        with (ROOT / AUTHORITY_PATH).open("xb") as stream:
            stream.write(json_bytes(expected))
    authority = load(AUTHORITY_PATH)
    accepted = accepted_artifact(candidate, review, manifest, authority)
    return {AUTHORITY_PATH: json_bytes(authority), ACCEPTED_PATH: json_bytes(accepted)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-scope", action="store_true")
    parser.add_argument("--record-human-decision", action="store_true")
    args = parser.parse_args()
    require(not (args.check and args.record_human_decision), "check mode cannot record authority")
    if args.check_scope:
        validate_scope()
    outputs = build_outputs(record_human_decision=args.record_human_decision)
    for name, content in outputs.items():
        path = ROOT / name
        if args.check or name == AUTHORITY_PATH:
            require(path.exists() and path.read_bytes() == content, f"M14G acceptance artifact differs: {name}")
        elif not path.exists() or path.read_bytes() != content:
            path.write_bytes(content)
    authority = json.loads(outputs[AUTHORITY_PATH])
    accepted = json.loads(outputs[ACCEPTED_PATH])
    print(json.dumps({"candidate_subject_sha256": CANDIDATE_SUBJECT, "authority_subject_sha256": authority["authority_subject_sha256"], "accepted_site_integration_subject_sha256": accepted["accepted_site_integration_subject_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
