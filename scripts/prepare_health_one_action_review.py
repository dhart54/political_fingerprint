"""Build/check the inert S.2393 review package; no public compiler or storage.

Read pinned local Git objects and the exact plaintext packet. All generated
legislative objects remain candidates. Presentation inputs are existing typed
analytical-text fragments, not a public presentation or executable release.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jsonschema import Draft7Validator
from backend.app.semantic_ir.shared_corpus import (
    adapt_to_semantic_ir_input, digest, sealed_digest,
)
from backend.app.semantic_ir.pipeline import run_editorial_pipeline
from backend.app.editorial_presentations.compiler import (
    _validate_analytical_text, validate_trusted_action_source_contract,
)

PIN = "d61146f7cd6055d6ad4b74979bcb575d7b40c97b"
BASE = "ac22199dff31bd2e271d95be82077c8e7de064c4"
OLD = "51211e8ec2fac3152380e705d8c1646b47047dc0"
UPSTREAM = "docs/editorial/shared_candidates/house_119_health_20260916/"
PACKAGE = ROOT / "docs/editorial/review_packages/health_s2393_one_action_v1"
PACKET_SHA = "3b6b60a88bb7ca9ef42abe4fb80714910d490ea9dac4eb8b79a6cfc547960347"
ACTION = "house:119:2:180"
EPISODE = "episode:s2393:119"
CANDIDATE = "candidate_pending_external_semantic_review"
RECEIPT = "docs/review_packets/health_one_action_owner_decision_receipt_draft.md"
SOURCE_IDS = ["clerk:119:2:180", "govinfo:s2393es"]
LABELS = {
    "scope_label": "Scope label", "finding_title": "Finding title",
    "finding": "Foushee finding", "accounting": "Massie receipt/accounting text",
    "qualifications": "Required detail/qualifications",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git_bytes(ref, path):
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT)


def packet_wording(raw):
    require(sha(raw) == PACKET_SHA, "exact packet SHA-256 mismatch; no normalization permitted")
    text = raw.decode("utf-8")
    result = {}
    for key, label in LABELS.items():
        lines = [line for line in text.splitlines() if line.startswith(label + ": ")]
        require(len(lines) == 1, f"packet wording identity missing/ambiguous: {key}")
        value = lines[0][len(label) + 2:]
        require(value.startswith("“") and value.endswith("”"), "packet quotation boundary differs")
        result[key] = value[1:-1]
    return result


def mapped_text(key, text, *, proposition=None, boundary=None):
    require(bool(proposition) != bool(boundary), "one semantic reference is required")
    reference = proposition or boundary
    return {
        "statement_id": "statement:s2393-review:" + key, "text": text,
        "mapping": {
            "mapping_id": "mapping:s2393-review:" + key,
            "proposition_ids": [reference["proposition_id"]] if proposition else [],
            "boundary_ids": [reference["boundary_id"]] if boundary else [],
            "presentation_target": reference["presentation_target"],
            "action_ids": reference.get("evidence_action_ids", reference.get("action_ids", [])),
            "episode_ids": reference.get("evidence_episode_ids", reference.get("episode_ids", [])),
            "source_refs": SOURCE_IDS.copy(), "receipt_refs": [RECEIPT],
        },
    }


def validate_presentation_inputs(inputs, compiled, source_contract, wording):
    """Validate existing fragment types and mappings; never compile public output."""
    require(inputs["review_state"] == compiled["review_state"] == CANDIDATE, "candidate state required")
    require(inputs["review_scope"] == "bounded_partial_record", "bounded scope required")
    validate_trusted_action_source_contract(source_contract)
    schema = json.loads((ROOT / "docs/editorial_public_issue_presentation_v1.schema.json").read_text(encoding="utf-8"))
    validator = Draft7Validator({**schema, "$ref": "#/definitions/analyticalText"})
    members = {m["member_id"]: m for m in compiled["members"]}
    require([m["member_id"] for m in inputs["members"]] == ["F000477", "M001184"], "exact member scope required")
    for member in inputs["members"]:
        mid = member["member_id"]
        expected_scope = {"boundary_id": f"scope:s2393-review:{mid.lower()}", "boundary_type": "reviewed_congress_scope", "presentation_target": "scope_note", "action_ids": [ACTION], "episode_ids": [EPISODE]}
        require(member["boundaries"] == [expected_scope, *members[mid]["composition"]["coverage_boundaries"]], "presentation boundaries differ from exact scope/compiled IR")
        propositions = {p["proposition_id"]: p for p in members[mid]["proposition_graph"]["propositions"]}
        boundaries = {b["boundary_id"]: b for b in member["boundaries"]}
        expected_keys = {"scope_label", "finding_title", "finding", "qualifications"} if mid == "F000477" else {"scope_label", "accounting", "qualifications"}
        require(set(member["records"]) == expected_keys, "unexpected presentation field")
        for key, record in member["records"].items():
            validator.validate(record)
            require(record["text"] == wording[key], "accepted packet wording parity differs: " + key)
            require(record["mapping"]["source_refs"] == SOURCE_IDS, "exact source closure required")
            expected_proposition = mid == "F000477" and key in {"finding_title", "finding"}
            require(bool(record["mapping"]["proposition_ids"]) == expected_proposition, "field semantic role differs")
            if expected_proposition:
                require(len(propositions) == 1, "one exact-choice proposition required")
                reference = next(iter(propositions.values()))
            elif key == "accounting":
                not_voting = [b for b in members[mid]["composition"]["coverage_boundaries"] if b["boundary_type"] == "not_voting"]
                require(len(not_voting) == 1, "one compiled Not Voting boundary required")
                reference = not_voting[0]
            else:
                reference = expected_scope
            expected_mapping = {
                "proposition_ids": [reference["proposition_id"]] if expected_proposition else [],
                "boundary_ids": [] if expected_proposition else [reference["boundary_id"]],
                "presentation_target": reference["presentation_target"],
                "action_ids": reference.get("evidence_action_ids", reference.get("action_ids", [])),
                "episode_ids": reference.get("evidence_episode_ids", reference.get("episode_ids", [])),
            }
            require(all(record["mapping"][field] == value for field, value in expected_mapping.items()), f"field semantic reference differs: {mid}:{key}")
            _validate_analytical_text(
                record, allowed_targets={"other_notable_choices", "scope_note", "coverage_note"},
                propositions=propositions, boundaries=boundaries,
                source_refs=set(SOURCE_IDS), receipt_refs={RECEIPT},
                trusted_action_source_contract=source_contract,
            )
        require(len({r["mapping"]["mapping_id"] for r in member["records"].values()}) == len(expected_keys), "duplicate mapping")


def build_package(packet_raw):
    wording = packet_wording(packet_raw)
    provenance = {}
    cache = {}

    def load(path):
        if path not in cache:
            raw = git_bytes(PIN, UPSTREAM + path)
            blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            expected = subprocess.check_output(["git", "rev-parse", PIN + ":" + UPSTREAM + path], cwd=ROOT).decode().strip()
            require(blob == expected, "Git object identity mismatch")
            # The accepted slice dependencies are unchanged at PR236's merge.
            require(raw == git_bytes(BASE, UPSTREAM + path), "reconciled main dependency drift")
            cache[path] = json.loads(raw)
            provenance[path] = {"commit": PIN, "git_blob": blob, "raw_file_sha256": sha(raw)}
        return copy.deepcopy(cache[path])

    core = load("generated/shared_action_core.json")
    action = next(a for a in core["actions"] if a["action_id"] == ACTION)
    require(action["action_core_sha256"] == "7df0c99b81ac06d558a9a6906202b25993e3f38eb9fe9a9421fd3c827e95e3e5", "accepted action seal differs")
    core["actions"] = [action]
    # Existing issue-neutral numeric revision vocabulary; no identity-schema change.
    core["artifact_id"] = "shared-action-core:house:119:v4"
    core["corpus_sha256"] = digest(core["actions"])
    mapping = load("generated/shared_issue_mapping.json")
    mapping["action_mappings"] = [a for a in mapping["action_mappings"] if a["action_id"] == ACTION]
    mapping["episodes"] = [e for e in mapping["episodes"] if e["episode_id"] == EPISODE]
    require(mapping["episodes"][0]["action_ids"] == [ACTION], "episode not singleton")
    mapping["artifact_id"] = "candidate:HEALTH_SOCIAL:s2393-one-action:119:v1"
    mapping["scope_boundaries"] = [wording["scope_label"]]
    mapping["mapping_sha256"] = sealed_digest(mapping, "mapping_sha256")
    membership = next(r for r in load("membership_review.json")["records"] if r["action_id"] == ACTION)
    require(digest(membership) == "cf9b26e72cfb61551dd29f4e02128d93816fb90313e7f93ba614287218669009", "accepted membership evidence differs")
    projections = load("generated/member_projections.json")
    require([p["member_id"] for p in projections] == ["F000477", "M001184"], "member scope drift")
    for projection in projections:
        projection["actions"] = [a for a in projection["actions"] if a["action_id"] == ACTION]
        projection["artifact_id"] = f"member-action-projection:{projection['member_id'].lower()}:house:119:v4"
        projection["projection_sha256"] = sealed_digest(projection, "projection_sha256")
    capture = load("sources.json")
    sources = [s for s in capture["sources"] if s["source_id"] in SOURCE_IDS]
    require([s["source_id"] for s in sources] == SOURCE_IDS, "source scope drift")
    for source in sources:
        require(sealed_digest(source, "governed_bytes_sha256") == source["governed_bytes_sha256"], "governed source drift")
    for projection, status, effect in zip(projections, ["Yea", "Not Voting"], ["supports_exact_choice", "resolved_non_directional"]):
        row = projection["actions"][0]
        require(sources[0]["member_records"][projection["member_id"]]["official_label"] == row["official_status"] == status, "member observation differs from Clerk")
        require(row["exact_choice_effect"] == effect, "member exact-choice effect differs")
    require(action["claim_source_map"][0]["passage"] == sources[1]["text"], "complete bill passage drift")
    source_capture = {"capture_date": capture["capture_date"], "capture_method": capture["capture_method"], "sources": sources}
    compiler_input = adapt_to_semantic_ir_input(ROOT, core, mapping, projections)
    result = run_editorial_pipeline(compiler_input)
    compiled = result.compiled_ir
    prop = compiled["members"][0]["proposition_graph"]["propositions"]
    require(len(prop) == 1 and prop[0]["evidence_action_ids"] == [ACTION] and prop[0]["direction"] == "support", "Foushee finding drift")
    require(compiled["members"][1]["proposition_graph"]["propositions"] == [], "Massie must have no behavioral proposition")
    source_contract = {
        "schema_version": "editorial_action_source_contract_v1",
        "contract_id": "candidate-review-only:s2393:119:v1",
        "source_manifest": {"path": "governed_sources.json", "sha256": sha(encoded(source_capture))},
        "claim_source_map": {"path": "claim_source_map.json", "sha256": sha(encoded(action["claim_source_map"]))},
        "source_authorities": {s["source_id"]: s["source_type"] for s in sources},
        "actions": {ACTION: {"vote_source_refs": [SOURCE_IDS[0]], "action_meaning_source_refs": [SOURCE_IDS[1]], "required_action_meaning_source_types": ["official_bill_text"]}},
    }
    presentation = {"review_state": CANDIDATE, "review_scope": "bounded_partial_record", "members": []}
    for member in compiled["members"]:
        mid = member["member_id"]
        scope = {"boundary_id": f"scope:s2393-review:{mid.lower()}", "boundary_type": "reviewed_congress_scope", "presentation_target": "scope_note", "action_ids": [ACTION], "episode_ids": [EPISODE]}
        boundaries = [scope, *copy.deepcopy(member["composition"]["coverage_boundaries"])]
        records = {
            "scope_label": mapped_text(mid + ":scope", wording["scope_label"], boundary=scope),
            "qualifications": mapped_text(mid + ":qualifications", wording["qualifications"], boundary=scope),
        }
        if mid == "F000477":
            for key in ["finding_title", "finding"]:
                records[key] = mapped_text(mid + ":" + key, wording[key], proposition=prop[0])
        else:
            records["accounting"] = mapped_text(mid + ":accounting", wording["accounting"], boundary=boundaries[1])
        presentation["members"].append({"member_id": mid, "boundaries": boundaries, "records": records})
    validate_presentation_inputs(presentation, compiled, source_contract, wording)
    outputs = {
        "shared_action_core.json": core, "shared_issue_mapping.json": mapping,
        "member_projections.json": projections, "governed_sources.json": source_capture,
        "claim_source_map.json": action["claim_source_map"], "compiler_input.json": compiler_input,
        "compiled_ir.json": compiled, "presentation_payload.json": result.presentation_payload,
        "presentation_inputs.json": presentation, "review_source_contract.json": source_contract,
        "membership_evidence.json": membership,
    }
    rule_paths = ["scripts/prepare_shared_domain_candidate.py", *[
        f"backend/app/semantic_ir/{name}.py"
        for name in ["shared_corpus", "compiler", "pipeline", "adapters", "validation"]
    ], "docs/semantic_ir/shared_legislative_corpus_v1.schema.json"]
    rule_hashes = {}
    for path in rule_paths:
        frozen_text = git_bytes(BASE, path).decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        current_text = (ROOT / path).read_text(encoding="utf-8")
        require(frozen_text == current_text, "generation rule differs from reconciled base: " + path)
        rule_hashes[path] = digest(current_text)
    outputs["provenance.json"] = {
        "artifact_role": "inert_review_package_provenance_not_storage_contract",
        "review_state": CANDIDATE, "new_artifacts_accepted": False,
        "production_eligible": False, "publication_authorized": False, "persistence_authorized": False,
        "review_scope": "bounded_partial_record", "full_issue_claim": False,
        "action_ids": [ACTION], "episode_ids": [EPISODE], "member_ids": ["F000477", "M001184"],
        "packet_sha256": PACKET_SHA, "packet_route": "supported plaintext handoff; no Library download claimed",
        "original_zip_verified": False, "original_zip_expected_sha256_only": "92e8e77beb8c25758da10bcbe9c744c5ed23079d105abaa1180b75c576f26fce",
        "git_evidence_route": "independent local Git-object extraction, not original archive contents",
        "dependency_commit": PIN, "earlier_comparison_commit": OLD, "reconciled_base": BASE,
        "upstream_files": provenance, "owner_decision_receipt": RECEIPT,
        "generation_rule_canonical_string_sha256": rule_hashes,
        "preparation_tool_canonical_string_sha256": digest(Path(__file__).read_text(encoding="utf-8")),
        "owner_decision_timestamp": "2026-10-19T16:57:50Z",
        "message_reference": "messageSentinel_b43433d9493081918ba2101e97dac6e3",
        "request_reference": "requestSentinel_94f29fc5c1f481919ff69134613a60a5",
        "presentation_admission": "typed mapped review fragments only; candidate public compiler remains blocked",
        "storage_admission": "none; no persistence proposal or importer",
        "derived_file_sha256": {name: sha(encoded(value)) for name, value in outputs.items()},
    }
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare only; never write")
    args = parser.parse_args(argv)
    outputs = build_package((PACKAGE / "DECISION-PACKET.md").read_bytes())
    for name, value in outputs.items():
        path = PACKAGE / name
        if args.check:
            # Text checkout newline differences do not change JSON object identity.
            require(json.loads(path.read_text(encoding="utf-8")) == value, "regeneration differs: " + name)
        else:
            path.write_bytes(encoded(value))
    print(json.dumps({"generated_json_files": len(outputs), "check_only": args.check, "candidate": True, "public_artifact_compiled": False, "database_accessed": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
