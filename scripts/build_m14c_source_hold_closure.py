"""Freeze detached M14C candidates once; reproduce all checks offline thereafter."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.action_interpretability import digest, file_sha256, load_json, qualify_candidate
from backend.app.semantic_ir.m14c_source_hold_closure import (
    BASE, OUTPUT, HOLD_IDS, ACCEPTED_IDS, baseline, expected_authority,
    require, source_catalog, source_overlay, validate_closure, validate_scope,
    ENRICHED_AUTHORITY_FILE, expected_enriched_authority, validate_human_acceptance,
)

DEST = ROOT / OUTPUT
AUTHORITY = DEST / "human_acceptance_authority.json"
ENRICHED_AUTHORITY = DEST / ENRICHED_AUTHORITY_FILE
CANDIDATES = DEST / "action_interpretability_candidates.json"


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def freeze_candidates(catalog: dict, overlay: dict) -> dict:
    from scripts.m14c_candidate_drafts import DRAFTS

    require(set(DRAFTS) == set(HOLD_IDS), "only the three source holds may be drafted")
    artifact = copy.deepcopy(baseline(ROOT))
    artifact["artifact_id"] = "action-interpretability-candidates:house:119:education_workforce:m14c:v1"
    artifact["input_bindings"]["starting_main"] = BASE
    artifact["input_bindings"]["source_readiness"] = {
        "path": f"{OUTPUT}/source_overlay.json",
        "sha256": file_sha256(DEST / "source_overlay.json"),
        "artifact_id": overlay["artifact_id"], "subject_sha256": overlay["source_readiness_subject_sha256"],
    }
    sources = {s["source_id"]: s for s in catalog["sources"]}
    readiness = {r["action_id"]: r for r in overlay["subject"]["action_readiness"]}
    for candidate in artifact["candidates"]:
        action_id = candidate["action_id"]
        if action_id not in DRAFTS:
            continue  # Never rewrite the accepted14, including their metadata.
        draft = DRAFTS[action_id]
        legacy_locator = candidate["claim_source_mappings"][0]["locator"]
        candidate["candidate_id"] = f"action-interpretability-candidate:{action_id}:m14c:v1"
        for key in ("policy_choice", "mechanism", "affected_entities", "direct_effect", "plain_language_meaning"):
            candidate[key] = copy.deepcopy(draft[key])
        candidate["limitations"] = [text for text, _ in draft["limitations"]]
        candidate["exact_action_boundary"]["proposal_effect"] = candidate["direct_effect"]
        candidate["candidate_state"] = "candidate_complete_for_semantic_review"
        candidate["legacy_interpretability_assessment"] = "revision_would_be_required"
        candidate["governed_source_packet_sha256"] = readiness[action_id]["source_packet_sha256"]
        candidate["governed_sources"] = [
            {"source_id": s["source_id"], "source_type": s["source_type"], "content_class": s["content_class"],
             "raw_sha256": s["raw_provenance"]["sha256"], "neutral_projection_sha256": s["neutral_projection_sha256"]}
            for s in readiness[action_id]["sources"]
        ]
        mappings = []

        def add(field: str, claim: str, refs: list) -> None:
            for source_id, index in refs:
                if source_id == "bill":
                    source_id = {"house:119:1:332": "congress-text:119:hr:2550:eh", "house:119:2:184": "congress-text:119:hr:2616:eh"}[action_id]
                    locator = legacy_locator
                else:
                    locator = sources[source_id]["neutral_projection"]["excerpts"][index]["locator"]
                mappings.append({"mapping_id": f"claim-map:{action_id}:m14c:{len(mappings) + 1}",
                                 "field": field, "claim": claim, "source_id": source_id, "locator": locator})

        for field, refs in draft["field_refs"].items():
            claim = candidate[field]
            if field == "mechanism":
                claim = claim["description"]
            elif field == "affected_entities":
                claim = "; ".join(claim)
            add(field, claim, refs)
        for text, refs in draft["limitations"]:
            add("limitations", text, refs)
        candidate["claim_source_mappings"] = mappings
        candidate["qualification"] = qualify_candidate(candidate, readiness[action_id])
    return artifact


def build_outputs() -> tuple[dict, dict[Path, bytes]]:
    artifact = load_json(CANDIDATES)
    authority = load_json(AUTHORITY)
    catalog = load_json(DEST / "source_catalog.json")
    overlay = load_json(DEST / "source_overlay.json")
    result = validate_closure(ROOT, artifact, authority, catalog, overlay)
    summary = {k: v for k, v in result.items() if k != "qualification_by_action"}
    review = {
        "schema_version": "m14c_source_hold_review_packet_v1",
        "status": "independent_semantic_product_review_complete_17_human_approved",
        "baseline_commit": BASE,
        "human_acceptance_authority_sha256": file_sha256(AUTHORITY),
        "previously_accepted_unchanged_ids": list(ACCEPTED_IDS),
        "new_candidate_acceptance": True,
        "enriched3_human_acceptance_authority": {"path": f"{OUTPUT}/{ENRICHED_AUTHORITY_FILE}",
                                                 "sha256": file_sha256(ENRICHED_AUTHORITY)},
        "acceptance_storage": "additive_authorities_only_candidate_records_unchanged",
        "review_questions": [
            "Does every material first-order provision and exception appear or have an explicit ancillary boundary?",
            "Does each claim follow from its exact operative or incorporated source, without importing parent meaning or source rhetoric?",
            "Are amendment adoption, House outcome, enactment, and actual implementation kept distinct?",
            "Is the explanation concrete, neutral, and useful without forecasting behavior?",
        ],
        "summary": summary,
        "new_candidates": [row for row in artifact["candidates"] if row["action_id"] in HOLD_IDS],
        "governed_sources": catalog["sources"],
    }
    outputs = {DEST / "source_catalog.json": json_bytes(source_catalog(ROOT)),
               DEST / "source_overlay.json": json_bytes(source_overlay(ROOT, source_catalog(ROOT))),
               DEST / "review_packet.json": json_bytes(review)}
    subject = summary | {
        "baseline_commit": BASE,
        "authority_file_sha256": file_sha256(AUTHORITY),
        "enriched3_authority_file_sha256": file_sha256(ENRICHED_AUTHORITY),
        "existing14_authority_preserved": True, "enriched3_authority_additive": True,
        "candidate_file_sha256": file_sha256(CANDIDATES),
        "candidate_record_digests": [{"action_id": r["action_id"], "sha256": digest(r)} for r in artifact["candidates"]],
        "generated_file_sha256": {p.name: hashlib.sha256(data).hexdigest() for p, data in outputs.items()},
        "sources": [{"source_id": s["source_id"], "raw_sha256": s["raw_provenance"]["sha256"],
                     "projection_sha256": s["neutral_projection_sha256"]} for s in catalog["sources"]],
        "accepted14_unchanged": True, "shared_core_promotion": False,
        "public_or_production_authority": False,
    }
    outputs[DEST / "build_manifest.json"] = json_bytes({"schema_version": "m14c_source_hold_build_manifest_v1", "subject": subject, "manifest_subject_sha256": digest(subject)})
    return summary, outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--initialize", action="store_true", help="one-time creation of authority and frozen detached candidates")
    mode.add_argument("--freeze-candidates", action="store_true", help="explicit proposal revision; never rewrites authority")
    mode.add_argument("--check", action="store_true", help="offline, no-write reproduction from frozen candidates")
    mode.add_argument("--record-human-acceptance", action="store_true", help="one-time materialization of the supplied exact3 human decision")
    parser.add_argument("--check-scope", action="store_true", help="milestone-only diff guard against the exact baseline")
    args = parser.parse_args()
    if args.record_human_acceptance:
        require(not ENRICHED_AUTHORITY.exists(), "refusing to overwrite immutable enriched3 authority")
        accepted = expected_enriched_authority()
        validate_human_acceptance(ROOT, load_json(CANDIDATES), accepted)
        ENRICHED_AUTHORITY.write_bytes(json_bytes(accepted))
    if args.initialize:
        require(not AUTHORITY.exists() and not CANDIDATES.exists(), "refusing to overwrite immutable authority or existing frozen candidates")
        AUTHORITY.write_bytes(json_bytes(expected_authority(ROOT)))
    if args.initialize or args.freeze_candidates:
        require(not ENRICHED_AUTHORITY.exists(), "human-accepted candidate records cannot be regenerated")
        require(load_json(AUTHORITY) == expected_authority(ROOT), "immutable authority must remain unchanged")
        catalog = source_catalog(ROOT)
        overlay = source_overlay(ROOT, catalog)
        (DEST / "source_catalog.json").write_bytes(json_bytes(catalog))
        (DEST / "source_overlay.json").write_bytes(json_bytes(overlay))
        CANDIDATES.write_bytes(json_bytes(freeze_candidates(catalog, overlay)))
    summary, outputs = build_outputs()
    for path, content in outputs.items():
        if args.check:
            require(path.exists() and path.read_bytes().replace(b"\r\n", b"\n") == content, f"generated artifact differs: {path.name}")
        elif not path.exists() or path.read_bytes().replace(b"\r\n", b"\n") != content:
            path.write_bytes(content)
    if args.check_scope:
        validate_scope(ROOT)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
