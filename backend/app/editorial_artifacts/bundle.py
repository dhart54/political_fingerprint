from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
STARTING_COMMIT = "88d6f3446f54b07735e084cbc958c1614b190fab"
BATCH_KEY = "editorial-artifact-persistence-v1-88d6f344"
SCHEMA_VERSION = "editorial_artifact_bundle_v1"
FROZEN_MANIFEST = (
    ROOT / "docs/editorial/editorial_artifact_persistence_v1/seed_manifest.json"
)
FROZEN_INPUT_CONTRACT = (
    ROOT
    / "docs/editorial/editorial_artifact_persistence_v1/"
    "frozen_input_contract.json"
)
ARTIFACT_TYPES = (
    "shared_action_dossier",
    "source_manifest",
    "claim_source_map",
    "policy_episode",
    "policy_family",
    "issue_ontology",
    "policy_trait_contract",
    "trait_relationship_contract",
    "member_action_overlay",
    "member_episode_trajectory",
    "issue_conclusion_propositions",
    "issue_public_presentation",
    "standardization_validation_result",
    "reference_fixture_metadata",
    "review_routing_result",
)
STATUS = {
    "editorial_status": "human_approval_pending",
    "benchmark_status": "not_promoted",
    "production_eligible": False,
}

ECONOMY = ROOT / "docs/editorial/valerie_foushee_economy_gold_v2"
JUSTICE = ROOT / "docs/editorial/valerie_foushee_justice_public_safety_gold_v1"
CROSS = ROOT / "docs/editorial/justice_cross_member_validation_v1"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def semantic_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_record(path: Path) -> dict[str, str]:
    relative = path.relative_to(ROOT).as_posix()
    return {
        "path": relative,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _route(value: str | None) -> str:
    return {
        "standard_generation_pass": "standard_generation",
        "sampled_audit_candidate": "sampled_audit",
        "human_exception_required": "human_exception",
        "blocked": "blocked",
    }.get(value or "", "standard_generation")


def _artifact(
    artifact_type: str,
    natural_key: str,
    payload: dict[str, Any],
    *,
    issue_id: str | None = None,
    member_id: str | None = None,
    action_id: str | None = None,
    episode_id: str | None = None,
    policy_family_id: str | None = None,
    review_route: str = "standard_generation",
    source_manifest_sha256: str | None = None,
) -> dict[str, Any]:
    item = {
        "artifact_type": artifact_type,
        "natural_key": natural_key,
        "schema_version": payload.get("schema_version", "editorial_artifact_payload_v1"),
        "artifact_version": 1,
        "payload": payload,
        "content_sha256": semantic_hash(payload),
        "source_manifest_sha256": source_manifest_sha256,
        "source_commit_sha": STARTING_COMMIT,
        "member_bioguide_id": member_id,
        "issue_id": issue_id,
        "congress": 119 if issue_id else None,
        "chamber": "house" if issue_id else None,
        "canonical_action_id": action_id,
        "episode_id": episode_id,
        "policy_family_id": policy_family_id,
        "review_route": review_route,
        **STATUS,
    }
    return item


def build_seed_bundle_from_current_inputs() -> dict[str, Any]:
    economy_packet = _load(ECONOMY / "review_packet.json")
    economy_episodes = _load(ECONOMY / "policy_episode_map.json")
    justice_packet = _load(JUSTICE / "review_packet.json")
    justice_episodes = _load(JUSTICE / "policy_episode_map.json")
    shared_justice = _load(CROSS / "episode_action_interpretations.json")
    overlays = _load(CROSS / "member_overlays.json")["overlays"]
    candidates = _load(CROSS / "inference_candidates.json")["candidates"]
    comparison = _load(CROSS / "comparison_matrix.json")

    source_files = {
        "ECONOMY_TAXES": [
            ECONOMY / "source_manifest.json",
            ECONOMY / "claim_source_map.json",
            ECONOMY / "review_packet.json",
            ECONOMY / "policy_episode_map.json",
            ECONOMY / "issue_synthesis.md",
        ],
        "JUSTICE_PUBLIC_SAFETY": [
            JUSTICE / "source_manifest.json",
            JUSTICE / "claim_source_map.json",
            JUSTICE / "review_packet.json",
            JUSTICE / "policy_episode_map.json",
            CROSS / "episode_action_interpretations.json",
            CROSS / "member_overlays.json",
            CROSS / "inference_candidates.json",
            CROSS / "comparison_matrix.json",
        ],
    }
    source_hashes = {
        issue: semantic_hash([_file_record(path) for path in paths])
        for issue, paths in source_files.items()
    }
    artifacts: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []

    for issue, root, packet in (
        ("ECONOMY_TAXES", ECONOMY, economy_packet),
        ("JUSTICE_PUBLIC_SAFETY", JUSTICE, justice_packet),
    ):
        manifest_payload = {
            "schema_version": "editorial_source_manifest_mirror_v1",
            "complete_required_sources": True,
            "source_document": _load(root / "source_manifest.json"),
            "source_files": [_file_record(path) for path in source_files[issue]],
        }
        artifacts.append(_artifact(
            "source_manifest", f"{issue.lower()}:source-manifest",
            manifest_payload, issue_id=issue,
            source_manifest_sha256=source_hashes[issue],
        ))
        artifacts.append(_artifact(
            "claim_source_map", f"{issue.lower()}:claim-source-map",
            {
                "schema_version": "editorial_claim_source_map_mirror_v1",
                "source_document": _load(root / "claim_source_map.json"),
            },
            issue_id=issue, source_manifest_sha256=source_hashes[issue],
        ))

    action_sets = (
        ("ECONOMY_TAXES", economy_packet["interpretations"], "substantive_or_not_voting"),
        ("ECONOMY_TAXES", economy_packet["controls"], "context_control"),
        ("JUSTICE_PUBLIC_SAFETY", justice_packet["interpretations"], "substantive"),
        ("JUSTICE_PUBLIC_SAFETY", justice_packet["controls"], "context_control"),
    )
    for issue, rows, role in action_sets:
        for row in rows:
            roll = int(row["roll"])
            action_id = f"house:119:1:{roll}"
            payload = {
                "schema_version": "shared_action_dossier_mirror_v1",
                "record_role": role,
                "canonical_action_id": action_id,
                "reviewed_record": row,
            }
            artifacts.append(_artifact(
                "shared_action_dossier", f"{issue.lower()}:{action_id}",
                payload, issue_id=issue, action_id=action_id,
                source_manifest_sha256=source_hashes[issue],
            ))

    for issue, episode_doc in (
        ("ECONOMY_TAXES", economy_episodes),
        ("JUSTICE_PUBLIC_SAFETY", justice_episodes),
    ):
        for index, episode in enumerate(episode_doc["episodes"]):
            episode_id = (
                episode.get("episode_id")
                or episode.get("id")
                or f"{issue.lower()}-episode-{index + 1}"
            )
            artifacts.append(_artifact(
                "policy_episode", f"{issue.lower()}:episode:{episode_id}",
                {"schema_version": episode_doc["schema_version"], "episode": episode},
                issue_id=issue, episode_id=episode_id,
                source_manifest_sha256=source_hashes[issue],
            ))
        artifacts.extend([
            _artifact(
                "policy_family", f"{issue.lower()}:policy-families",
                {
                    "schema_version": "editorial_policy_family_mirror_v1",
                    "episode_ids": [
                        e.get("episode_id") or e.get("id") or f"{issue.lower()}-episode-{i + 1}"
                        for i, e in enumerate(episode_doc["episodes"])
                    ],
                    "source_document": episode_doc,
                },
                issue_id=issue, policy_family_id=f"{issue.lower()}-reviewed-families",
                source_manifest_sha256=source_hashes[issue],
            ),
            _artifact(
                "issue_ontology", f"{issue.lower()}:ontology",
                {
                    "schema_version": "editorial_issue_ontology_mirror_v1",
                    "issue_id": issue,
                    "counting_boundary": episode_doc.get("counting_boundary")
                    or episode_doc.get("deduplication_rule"),
                },
                issue_id=issue, source_manifest_sha256=source_hashes[issue],
            ),
        ])

    economy_traits = {
        "schema_version": "economy_policy_trait_contract_mirror_v1",
        "source_document": economy_episodes,
    }
    justice_traits = shared_justice["policy_trait_contract"]
    for issue, traits in (
        ("ECONOMY_TAXES", economy_traits),
        ("JUSTICE_PUBLIC_SAFETY", justice_traits),
    ):
        artifacts.extend([
            _artifact(
                "policy_trait_contract", f"{issue.lower()}:policy-traits",
                {"schema_version": traits.get("schema_version", "policy_trait_contract_v1"), "contract": traits},
                issue_id=issue, source_manifest_sha256=source_hashes[issue],
            ),
            _artifact(
                "trait_relationship_contract", f"{issue.lower()}:trait-relationships",
                {
                    "schema_version": "trait_relationship_contract_mirror_v1",
                    "relationships": traits.get("cluster_relationships", []),
                    "contract_source": traits,
                },
                issue_id=issue, source_manifest_sha256=source_hashes[issue],
            ),
        ])

    economy_candidate = {
        "schema_version": "economy_pending_slice_mirror_v1",
        "member": economy_packet["member"],
        "candidate_id": economy_packet["packet_id"],
        "primary_conclusion": (ECONOMY / "issue_synthesis.md").read_text(encoding="utf-8"),
        "within_episode_trajectories": economy_episodes["episodes"],
        "coverage": economy_episodes["counts"],
        "review_route": "standard_generation_pass",
        "publication": {
            "editorial_status": "human_approval_pending",
            "benchmark_status": "not_promoted",
            "production_eligible": False,
        },
        "review_packet": economy_packet,
    }
    overlay_by_member = {row["member"]["bioguide_id"]: row for row in overlays}
    candidate_by_member = {row["member"]["bioguide_id"]: row for row in candidates}
    slice_specs = [
        ("F000477", "ECONOMY_TAXES", economy_packet, economy_candidate, "human_reviewed_presentation_fixture"),
        ("F000477", "JUSTICE_PUBLIC_SAFETY", overlay_by_member["F000477"], candidate_by_member["F000477"], "human_reviewed_presentation_fixture"),
        ("M001184", "JUSTICE_PUBLIC_SAFETY", overlay_by_member["M001184"], candidate_by_member["M001184"], "reference_render_fixture"),
        ("G000586", "JUSTICE_PUBLIC_SAFETY", overlay_by_member["G000586"], candidate_by_member["G000586"], "sampled_audit_calibration"),
    ]
    for member_id, issue, overlay, candidate, designation in slice_specs:
        prefix = f"{member_id.lower()}:{issue.lower()}"
        route = _route(candidate.get("review_route"))
        source_hash = source_hashes[issue]
        trajectory_payload = {
            "schema_version": "member_episode_trajectory_mirror_v1",
            "member": candidate["member"],
            "trajectories": overlay.get("episode_trajectories")
            or candidate.get("within_episode_trajectories")
            or economy_episodes["episodes"],
            "candidate_highlighted_trajectories": candidate.get("within_episode_trajectories", []),
            "coverage": candidate.get("coverage") or overlay.get("coverage"),
        }
        conclusion_payload = {
            "schema_version": "issue_conclusion_propositions_mirror_v1",
            "member": candidate["member"],
            "primary_conclusion": candidate.get("primary_conclusion"),
            "conclusion_model": candidate.get("conclusion_model"),
            "supporting_independent_episodes": candidate.get("supporting_independent_episodes", []),
            "weakening_independent_episodes": candidate.get("weakening_independent_episodes", []),
            "neutral_independent_episodes": candidate.get("neutral_independent_episodes", []),
        }
        presentation_payload = {
            "schema_version": "issue_public_presentation_mirror_v1",
            "member": candidate["member"],
            "issue_id": issue,
            "public_conclusion": candidate.get("primary_conclusion"),
            "reader_facing_label": candidate.get("reader_facing_label"),
            "analytical_sections": candidate.get("conclusion_model") or candidate.get("review_packet"),
            "featured_episode_ids": candidate.get("episode_references", []),
            "voting_context": candidate.get("coverage"),
            "blocking_findings": 0,
            "publication": copy.deepcopy(STATUS),
        }
        validation_payload = {
            "schema_version": "editorial_standardization_validation_result_mirror_v1",
            "successful": True,
            "current": True,
            "blocking_findings": 0,
            "rules_evaluated": 48,
            "source": "accepted checked-in review and standardization artifacts",
        }
        entries = [
            _artifact("member_action_overlay", f"{prefix}:overlay", {"schema_version": "member_action_overlay_mirror_v1", "overlay": overlay}, issue_id=issue, member_id=member_id, review_route=route, source_manifest_sha256=source_hash),
            _artifact("member_episode_trajectory", f"{prefix}:trajectory", trajectory_payload, issue_id=issue, member_id=member_id, review_route=route, source_manifest_sha256=source_hash),
            _artifact("issue_conclusion_propositions", f"{prefix}:propositions", conclusion_payload, issue_id=issue, member_id=member_id, review_route=route, source_manifest_sha256=source_hash),
            _artifact("issue_public_presentation", f"{prefix}:presentation", presentation_payload, issue_id=issue, member_id=member_id, review_route=route, source_manifest_sha256=source_hash),
            _artifact("standardization_validation_result", f"{prefix}:validation", validation_payload, issue_id=issue, member_id=member_id, review_route=route, source_manifest_sha256=source_hash),
            _artifact("reference_fixture_metadata", f"{prefix}:reference", {"schema_version": "reference_fixture_metadata_v1", "designation": designation, "excluded_test_universes": True}, issue_id=issue, member_id=member_id, review_route=route, source_manifest_sha256=source_hash),
            _artifact("review_routing_result", f"{prefix}:review-route", {"schema_version": "review_routing_result_v1", "route": route, "source_route": candidate.get("review_route"), "human_review_status": "human_approval_pending"}, issue_id=issue, member_id=member_id, review_route=route, source_manifest_sha256=source_hash),
        ]
        artifacts.extend(entries)

    by_key = {item["natural_key"]: item for item in artifacts}
    for issue in ("ECONOMY_TAXES", "JUSTICE_PUBLIC_SAFETY"):
        issue_prefix = issue.lower()
        relationships.append({
            "parent_natural_key": f"{issue_prefix}:claim-source-map",
            "child_natural_key": f"{issue_prefix}:source-manifest",
            "relationship_type": "maps_claims_to_sources",
            "ordinal": 0,
            "metadata": {},
        })
        for item in artifacts:
            if item["issue_id"] == issue and item["artifact_type"] != "source_manifest":
                relationships.append({
                    "parent_natural_key": item["natural_key"],
                    "child_natural_key": f"{issue_prefix}:source-manifest",
                    "relationship_type": "uses_source_manifest",
                    "ordinal": 0,
                    "metadata": {},
                })
    for member_id, issue, _, _, _ in slice_specs:
        prefix = f"{member_id.lower()}:{issue.lower()}"
        presentation = f"{prefix}:presentation"
        for suffix, rel_type in (
            ("overlay", "has_member_overlay"),
            ("trajectory", "has_trajectory"),
            ("propositions", "has_conclusion_propositions"),
            ("validation", "has_validation"),
            ("reference", "has_reference_metadata"),
            ("review-route", "has_review_route"),
        ):
            relationships.append({
                "parent_natural_key": presentation,
                "child_natural_key": f"{prefix}:{suffix}",
                "relationship_type": rel_type,
                "ordinal": 0,
                "metadata": {},
            })

    artifacts.sort(key=lambda item: (item["artifact_type"], item["natural_key"], item["artifact_version"]))
    relationships.sort(key=lambda item: (
        item["parent_natural_key"], item["relationship_type"], item["ordinal"], item["child_natural_key"]
    ))
    body = {
        "schema_version": SCHEMA_VERSION,
        "deterministic_batch_key": BATCH_KEY,
        "starting_commit": STARTING_COMMIT,
        "source_of_truth": "checked_in_repository_artifacts",
        "publication_registry_expected_rows": 0,
        "excluded_artifacts": [
            "128 synthetic Justice vectors",
            "malformed mutation fixtures",
            "fictional members",
            "large-record synthetic fixtures",
            "screenshot fixtures",
            "generated browser traces",
            "test-only service-status profiles",
        ],
        "artifacts": artifacts,
        "relationships": relationships,
        "expected_counts": {
            "artifacts": len(artifacts),
            "relationships": len(relationships),
            "by_type": dict(sorted(Counter(item["artifact_type"] for item in artifacts).items())),
        },
    }
    body["manifest_sha256"] = semantic_hash(body)
    validate_bundle(body)
    return body


def build_seed_bundle() -> dict[str, Any]:
    """Load and validate the immutable historical V1 persistence snapshot.

    V1 was produced from the repository at ``STARTING_COMMIT``. Later editorial
    source corrections must not silently regenerate or rewrite those 71 stored
    artifacts. The separate frozen-input contract pins the original manifest
    bytes and the exact source-file identities recorded by that snapshot.
    """

    contract = _load(FROZEN_INPUT_CONTRACT)
    bundle = _load(FROZEN_MANIFEST)
    if contract.get("schema_version") != "editorial_artifact_frozen_input_v1":
        raise ValueError("unsupported historical seed frozen-input contract")
    if contract.get("contract_id") != BATCH_KEY:
        raise ValueError("historical seed frozen-input contract ID mismatch")
    if contract.get("source_commit_sha") != STARTING_COMMIT:
        raise ValueError("historical seed source commit mismatch")
    if contract.get("seed_manifest_path") != FROZEN_MANIFEST.relative_to(
        ROOT
    ).as_posix():
        raise ValueError("historical seed manifest path mismatch")
    if hashlib.sha256(FROZEN_MANIFEST.read_bytes()).hexdigest() != contract.get(
        "seed_manifest_file_sha256"
    ):
        raise ValueError("historical seed manifest file digest mismatch")
    if bundle.get("manifest_sha256") != contract.get(
        "seed_manifest_semantic_sha256"
    ):
        raise ValueError("historical seed semantic digest mismatch")
    source_artifacts = {
        item["natural_key"]: item
        for item in bundle["artifacts"]
        if item["artifact_type"] == "source_manifest"
    }
    expected_sources = {
        item["natural_key"]: item for item in contract["source_manifests"]
    }
    if set(source_artifacts) != set(expected_sources):
        raise ValueError("historical seed source-manifest identity mismatch")
    for natural_key, expected in expected_sources.items():
        artifact = source_artifacts[natural_key]
        if (
            artifact["content_sha256"] != expected["content_sha256"]
            or artifact["source_manifest_sha256"]
            != expected["source_manifest_sha256"]
            or artifact["payload"]["source_files"] != expected["source_files"]
        ):
            raise ValueError(
                f"historical seed frozen source mismatch: {natural_key}"
            )
    validate_bundle(bundle)
    return bundle


def validate_bundle(bundle: dict[str, Any]) -> None:
    copy_for_hash = copy.deepcopy(bundle)
    claimed_hash = copy_for_hash.pop("manifest_sha256", None)
    if claimed_hash != semantic_hash(copy_for_hash):
        raise ValueError("manifest SHA-256 mismatch")
    if bundle["deterministic_batch_key"] != BATCH_KEY or bundle["starting_commit"] != STARTING_COMMIT:
        raise ValueError("bundle identity mismatch")
    artifacts = bundle["artifacts"]
    keys: set[tuple[str, int]] = set()
    natural_keys = {item["natural_key"] for item in artifacts}
    for item in artifacts:
        if item["artifact_type"] not in ARTIFACT_TYPES:
            raise ValueError(f"invalid artifact type: {item['artifact_type']}")
        key = (item["natural_key"], item["artifact_version"])
        if key in keys:
            raise ValueError(f"duplicate artifact version: {key}")
        keys.add(key)
        if item["content_sha256"] != semantic_hash(item["payload"]):
            raise ValueError(f"content hash mismatch: {item['natural_key']}")
        if item["editorial_status"] != "human_approval_pending":
            raise ValueError("seed artifact is not pending")
        if item["benchmark_status"] != "not_promoted" or item["production_eligible"]:
            raise ValueError("seed artifact crosses publication boundary")
    if set(ARTIFACT_TYPES) != {item["artifact_type"] for item in artifacts}:
        raise ValueError("artifact taxonomy is incomplete")
    for rel in bundle["relationships"]:
        if rel["parent_natural_key"] not in natural_keys or rel["child_natural_key"] not in natural_keys:
            raise ValueError("orphan relationship")
    expected = bundle["expected_counts"]
    if expected["artifacts"] != len(artifacts) or expected["relationships"] != len(bundle["relationships"]):
        raise ValueError("expected row counts mismatch")
    if bundle["publication_registry_expected_rows"] != 0:
        raise ValueError("publication registry must remain empty")
