"""Freeze, validate, and render M14B Action Interpretability V1 candidates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.action_interpretability import (  # noqa: E402
    digest,
    file_sha256,
    load_json,
    qualify_candidate,
    validate_candidate_set,
)


OUTPUT_ROOT = ROOT / "docs/editorial/interpretability_candidates/house_119_v1/education_workforce_v1"
CANDIDATE_PATH = OUTPUT_ROOT / "action_interpretability_candidates.json"
REVIEW_PATH = OUTPUT_ROOT / "human_review_packet.md"
MANIFEST_PATH = OUTPUT_ROOT / "build_manifest.json"
READINESS_PATH = ROOT / "docs/editorial/full_record_reviews/source_readiness/f000477_education_workforce_119_interpretation_source_readiness_v2.json"
LEGACY_PATH = ROOT / "docs/editorial/full_record_reviews/interpretation_decisions/f000477_education_workforce_119_v1/decision_implementation_bundle.json"
CORE_PATH = ROOT / "docs/editorial/shared_corpora/house_119_v1/shared_action_core.json"
STARTING_MAIN = "9b56358184e828e641ce2538cc9ed8788972b566"
PROTECTED = [
    ("docs/editorial/full_record_reviews/interpretation_decisions/f000477_education_workforce_119_v1/decision_implementation_bundle.json", "074a3bd396a55f6c31b2f7acfacb63455e4b56e1cb2da522b7fa53c62523d656"),
    ("docs/editorial/full_record_reviews/interpretation_decisions/f000477_justice_public_safety_119_v1/decision_implementation_bundle.json", "a1cafe5718772521542f98b797d6e95280ae3092a0e0cdfa355c0e17f3fe5d39"),
    ("docs/editorial/full_record_reviews/interpretation_decisions/f000477_national_security_foreign_119_v1/decision_implementation_bundle.json", "402928780286f98fec90242132a829058f57517328c532e60371afab3c2173ff"),
    ("docs/editorial/full_record_reviews/interpretation_decisions/f000477_environment_energy_119_v1/decision_implementation_bundle.json", "8cd447d71e606064c04caec0f34901e3b3bce2fb515e4dba4718806a06fff507"),
    ("docs/editorial/shared_corpora/house_119_v1/shared_action_core.json", "331194e87a86764ac8282d67dc13e93df412cb57516bd1d256a9630fab4be0ab"),
]


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def normalized_sha256_bytes(value: bytes) -> str:
    import hashlib

    return hashlib.sha256(value.replace(b"\r\n", b"\n")).hexdigest()


def freeze_candidates() -> dict[str, Any]:
    from scripts.m14b_action_interpretability_candidate_data import CANDIDATE_DRAFTS

    readiness_artifact = load_json(READINESS_PATH)
    legacy_artifact = load_json(LEGACY_PATH)
    core_artifact = load_json(CORE_PATH)
    readiness_by_id = {row["action_id"]: row for row in readiness_artifact["subject"]["action_readiness"]}
    legacy_by_id = {row["action_id"]: row for row in legacy_artifact["subject"]["implementation_records"]}
    core_by_id = {row["action_id"]: row for row in core_artifact["actions"]}
    candidates: list[dict[str, Any]] = []
    for action_id in sorted(CANDIDATE_DRAFTS):
        draft = CANDIDATE_DRAFTS[action_id]
        readiness = readiness_by_id[action_id]
        source_id = str(draft["source_id"])
        locator = str(draft["locator"])
        claims = {
            "policy_choice": draft["policy_choice"],
            "mechanism": draft["mechanism"],
            "affected_entities": "; ".join(draft["affected_entities"]),
            "direct_effect": draft["direct_effect"],
            "plain_language_meaning": draft["plain_language_meaning"],
        }
        mappings = [
            {
                "mapping_id": f"claim-map:{action_id}:m14b:{field}",
                "field": field,
                "claim": claim,
                "source_id": source_id,
                "locator": locator,
            }
            for field, claim in claims.items()
        ]
        mappings.extend(
            {
                "mapping_id": f"claim-map:{action_id}:m14b:limitation:{index}",
                "field": "limitations",
                "claim": limitation,
                "source_id": source_id,
                "locator": locator,
            }
            for index, limitation in enumerate(draft["limitations"], 1)
        )
        core = core_by_id.get(action_id)
        candidate = {
            "candidate_id": f"action-interpretability-candidate:{action_id}:m14b:v1",
            "action_id": action_id,
            "exact_action_identity": readiness["exact_action_identity"],
            "legislative_stage": readiness["house_action_stage"],
            "action_date": readiness["official_action_date"],
            "governed_source_packet_sha256": readiness["source_packet_sha256"],
            "governed_sources": [
                {
                    "source_id": source["source_id"],
                    "source_type": source["source_type"],
                    "content_class": source["content_class"],
                    "raw_sha256": source["raw_provenance"]["sha256"],
                    "neutral_projection_sha256": source["neutral_projection_sha256"],
                }
                for source in readiness["sources"]
            ],
            "shared_action_core_reference": None if core is None else {
                "action_core_sha256": core["action_core_sha256"],
                "governed_source_identity_sha256": core["governed_source_identity_sha256"],
            },
            "current_accepted_legacy_meaning": legacy_by_id[action_id]["accepted_exact_action_meaning"],
            "policy_choice": draft["policy_choice"],
            "mechanism": {"type": draft["mechanism_type"], "description": draft["mechanism"]},
            "affected_entities": draft["affected_entities"],
            "direct_effect": draft["direct_effect"],
            "plain_language_meaning": draft["plain_language_meaning"],
            "limitations": draft["limitations"],
            "downstream_effects": [],
            "claim_source_mappings": mappings,
            "exact_action_boundary": {
                "boundary_type": draft["boundary_type"],
                "proposal_effect": draft["direct_effect"],
                "house_action_outcome": draft["house_action_outcome"],
                "enactment_status": "not_inferred_from_house_action",
                "parent_package_meaning_projected": False,
                "ungoverned_component_projection": False,
            },
            "candidate_state": draft["candidate_state"],
            "legacy_interpretability_assessment": draft["legacy_assessment"],
            "qualification": {},
            "authorizing": False,
            "accepted": False,
            "public": False,
            "production_selectable": False,
        }
        candidate["qualification"] = qualify_candidate(candidate, readiness)
        candidates.append(candidate)
    artifact = {
        "schema_version": "action_interpretability_candidate_set_v1",
        "artifact_id": "action-interpretability-candidates:house:119:education_workforce:m14b:v1",
        "authority_state": "detached_non_authorizing_candidate",
        "authorizing": False,
        "accepted": False,
        "public": False,
        "production_selectable": False,
        "historical_artifacts_rewritten": False,
        "input_bindings": {
            "starting_main": STARTING_MAIN,
            "source_readiness": {
                "path": READINESS_PATH.relative_to(ROOT).as_posix(),
                "sha256": file_sha256(READINESS_PATH),
                "artifact_id": readiness_artifact["artifact_id"],
                "subject_sha256": readiness_artifact["source_readiness_subject_sha256"],
            },
            "legacy_decision_implementation": {
                "path": LEGACY_PATH.relative_to(ROOT).as_posix(),
                "sha256": file_sha256(LEGACY_PATH),
                "artifact_id": legacy_artifact["artifact_id"],
                "subject_sha256": legacy_artifact["implementation_subject_sha256"],
            },
        },
        "protected_historical_artifacts": [
            {"path": path, "sha256": sha256} for path, sha256 in PROTECTED
        ],
        "candidates": candidates,
    }
    validate_candidate_set(ROOT, artifact)
    return artifact


def render_review_packet(artifact: dict[str, Any], result: dict[str, Any]) -> bytes:
    lines = [
        "# M14B Education & Workforce Action Interpretability Review Packet",
        "",
        "Status: detached, source-mapped candidates for independent semantic/product review. Nothing here accepts, promotes, publishes, or persists a meaning.",
        "",
        f"- Starting main: `{artifact['input_bindings']['starting_main']}`",
        f"- Candidate-set digest: `{result['candidate_set_digest']}`",
        f"- Candidate states: `{json.dumps(result['candidate_state_counts'], sort_keys=True)}`",
        f"- Legacy assessments: `{json.dumps(result['legacy_assessment_counts'], sort_keys=True)}`",
        "- Shared Action Core exact-identity matches: 1 (`house:119:1:68`); the remaining 16 retain governed legacy lineage and are not promoted.",
        "",
        "## Independent review questions",
        "",
        "For each action: Can the policy change be explained from the candidate alone? Does it state an actual mechanism? Would it work identically for any representative? Is every substantive claim grounded? Is caveat-heavy wording hiding an important action? Should the action be held for better evidence?",
        "",
    ]
    for candidate in artifact["candidates"]:
        boundary = candidate["exact_action_boundary"]
        lines.extend([
            f"## {candidate['action_id']} — `{candidate['exact_action_identity']}`",
            "",
            f"1. **Exact action and stage:** `{candidate['legislative_stage']}` on `{candidate['action_date']}`; proposal effect is separate from `{boundary['house_action_outcome']}` and enactment is `{boundary['enactment_status']}`.",
            f"2. **Current accepted meaning:** {candidate['current_accepted_legacy_meaning']}",
            f"3. **Proposed policy_choice:** {candidate['policy_choice']}",
            f"4. **Proposed mechanism:** `{candidate['mechanism']['type']}` — {candidate['mechanism']['description']}",
            f"5. **Proposed affected_entities:** {', '.join(candidate['affected_entities'])}",
            f"6. **Proposed direct_effect:** {candidate['direct_effect']}",
            f"7. **Proposed plain_language_meaning:** {candidate['plain_language_meaning']}",
            f"8. **Limitations / omitted downstream claims:** {' '.join(candidate['limitations']) or 'No material limitation recorded.'} Downstream predictions: omitted.",
            "9. **Source receipts / locators:**",
            "",
        ])
        for source in candidate["governed_sources"]:
            lines.append(
                f"   - governed `{source['source_id']}` (`{source['source_type']}`, `{source['content_class']}`); "
                f"raw `{source['raw_sha256']}`; projection `{source['neutral_projection_sha256']}`"
            )
        for mapping in candidate["claim_source_mappings"]:
            lines.append(f"   - `{mapping['field']}` → `{mapping['source_id']}` at `{mapping['locator']}`")
        checks = candidate["qualification"]["checks"]
        lines.extend([
            "",
            f"10. **Mechanical qualification:** `{candidate['qualification']['result']}`; " + ", ".join(f"{name}={'pass' if checks[name] else 'fail'}" for name in sorted(checks)) + ".",
            f"- **Candidate state:** `{candidate['candidate_state']}`",
            f"- **Legacy comparison:** `{candidate['legacy_interpretability_assessment']}`",
            "",
        ])
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def build_outputs() -> tuple[dict[str, Any], dict[Path, bytes]]:
    artifact = load_json(CANDIDATE_PATH)
    if artifact["input_bindings"]["starting_main"] != STARTING_MAIN:
        raise ValueError("M14B starting-main binding differs")
    if artifact["protected_historical_artifacts"] != [
        {"path": path, "sha256": sha256} for path, sha256 in PROTECTED
    ]:
        raise ValueError("M14B protected historical bindings differ")
    result = validate_candidate_set(ROOT, artifact)
    if result["candidate_count"] != 17:
        raise ValueError("M14B requires exactly 17 governed Education actions")
    review_bytes = render_review_packet(artifact, result)
    manifest_subject = {
        "candidate_artifact_id": artifact["artifact_id"],
        "candidate_file_sha256": file_sha256(CANDIDATE_PATH),
        "candidate_set_digest": result["candidate_set_digest"],
        "candidate_record_digests": [
            {"action_id": item["action_id"], "sha256": digest(item)}
            for item in artifact["candidates"]
        ],
        "review_packet_sha256": normalized_sha256_bytes(review_bytes),
        "candidate_state_counts": result["candidate_state_counts"],
        "legacy_assessment_counts": result["legacy_assessment_counts"],
        "protected_historical_artifact_parity": True,
        "accepted_or_promoted": False,
        "public_or_production_change": False,
    }
    manifest = {
        "schema_version": "action_interpretability_build_manifest_v1",
        "manifest_id": "action-interpretability-build:house:119:education_workforce:m14b:v1",
        "subject": manifest_subject,
        "manifest_subject_sha256": digest(manifest_subject),
    }
    return result, {REVIEW_PATH: review_bytes, MANIFEST_PATH: json_bytes(manifest)}


def write_outputs(outputs: dict[Path, bytes]) -> None:
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def check_outputs(outputs: dict[Path, bytes]) -> None:
    mismatches = [path.relative_to(ROOT).as_posix() for path, content in outputs.items() if not path.exists() or path.read_bytes().replace(b"\r\n", b"\n") != content.replace(b"\r\n", b"\n")]
    if mismatches:
        raise SystemExit("M14B generated output differs: " + ", ".join(mismatches))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate frozen candidates and compare deterministic outputs")
    parser.add_argument("--freeze-candidates", action="store_true", help="explicitly materialize the reviewed draft data once; never used by --check")
    args = parser.parse_args()
    if args.check and args.freeze_candidates:
        raise SystemExit("--check and --freeze-candidates are mutually exclusive")
    if args.freeze_candidates:
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        CANDIDATE_PATH.write_bytes(json_bytes(freeze_candidates()))
    result, outputs = build_outputs()
    if args.check:
        check_outputs(outputs)
    else:
        write_outputs(outputs)
    print(json.dumps({key: value for key, value in result.items() if key != "qualification_by_action"}, sort_keys=True))


if __name__ == "__main__":
    main()
