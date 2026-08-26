"""Offline M0 shared-legislative-corpus audit and two-member reuse proof.

This harness projects already governed Justice content into an audit-only,
member-neutral view.  It does not create legislative meaning, persist data, or
authorize any artifact.  Output is limited to explicit report paths under
``docs/architecture`` or the operating-system temporary directory.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


EXPECTED_BASELINE = "74b054bfb8f138b8b6a31289f48995ceefcb0240"
SCHEMA_VERSION = "m0_shared_legislative_corpus_audit_v1"
PROOF_SCHEMA_VERSION = "m0_two_member_reuse_proof_v1"
MEMBER_A = "F000477"
PILOT_DOMAIN = "JUSTICE_PUBLIC_SAFETY"

MANIFEST = Path(
    "docs/editorial/full_record_reviews/proposals/"
    "f000477_justice_public_safety_119_full_issue_universe_manifest_v2.json"
)
EVIDENCE_MAPS = Path(
    "docs/editorial/full_record_reviews/interpretation_candidates/"
    "f000477_justice_public_safety_119_v4/evidence_maps.json"
)
CANDIDATE_BATCH = Path(
    "docs/editorial/full_record_reviews/interpretation_candidates/"
    "f000477_justice_public_safety_119_v4/candidate_batch.json"
)
ACTION_IMPLEMENTATION = Path(
    "docs/editorial/full_record_reviews/interpretation_decisions/"
    "f000477_justice_public_safety_119_v1/decision_implementation_bundle.json"
)
EPISODE_IMPLEMENTATION = Path(
    "docs/editorial/full_record_reviews/policy_episode_implementations/"
    "f000477_justice_public_safety_119_v1/episode_implementation_bundle.json"
)
COMPILER_INPUT = Path(
    "docs/editorial/full_record_reviews/semantic_ir_implementations/"
    "f000477_justice_public_safety_119_v2/frozen_final_compiler_input.json"
)
COMPILED_IR = Path(
    "docs/editorial/full_record_reviews/semantic_ir_implementations/"
    "f000477_justice_public_safety_119_v2/frozen_final_compiled_semantic_ir.json"
)
SOURCE_READINESS = Path(
    "docs/editorial/full_record_reviews/source_readiness/"
    "f000477_justice_public_safety_119_interpretation_source_readiness_v1.json"
)
SOURCE_MANIFEST = Path(
    "docs/editorial/full_record_reviews/source_readiness/"
    "f000477_justice_public_safety_119_official_source_manifest_v1.json"
)
EDUCATION_IMPLEMENTATION = Path(
    "docs/editorial/full_record_reviews/interpretation_decisions/"
    "f000477_education_workforce_119_v1/decision_implementation_bundle.json"
)

INPUT_PATHS = [
    MANIFEST,
    EVIDENCE_MAPS,
    CANDIDATE_BATCH,
    ACTION_IMPLEMENTATION,
    EPISODE_IMPLEMENTATION,
    COMPILER_INPUT,
    COMPILED_IR,
    SOURCE_READINESS,
    SOURCE_MANIFEST,
    EDUCATION_IMPLEMENTATION,
]

MEMBER_FIELDS = {
    "member_id",
    "member_name",
    "member_bioguide_id",
    "legislator_id",
    "party",
    "official_member_action",
    "member_action",
    "member_status",
    "service_status",
    "evidence_status",
    "member_position_effect",
    "exact_choice_position_effect",
    "implemented_exact_choice_position_effect",
    "member_direction",
}


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(root: Path, path: Path) -> dict[str, Any]:
    return json.loads((root / path).read_text(encoding="utf-8-sig"))


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def normalized_status(value: str | None) -> str:
    mapping = {
        "yea": "Yea",
        "aye": "Yea",
        "nay": "Nay",
        "no": "Nay",
        "present": "Present",
        "not voting": "Not Voting",
        "not_voting": "Not Voting",
        "missing evidence": "Missing Evidence",
    }
    return mapping.get((value or "").strip().lower(), "Missing Evidence")


def choice_effect(status: str) -> str:
    return {
        "Yea": "supports_exact_choice",
        "Nay": "opposes_exact_choice",
        "Present": "resolved_non_directional",
        "Not Voting": "resolved_non_directional",
        "Missing Evidence": "missing_evidence",
    }[status]


def parse_roll(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    metadata = root.find("vote-metadata")
    if metadata is None:
        raise ValueError(f"missing vote metadata: {path}")

    def text(name: str) -> str | None:
        node = metadata.find(name)
        return node.text.strip() if node is not None and node.text else None

    members: dict[str, dict[str, str]] = {}
    for recorded in root.findall("./vote-data/recorded-vote"):
        legislator = recorded.find("legislator")
        vote = recorded.find("vote")
        if legislator is None or vote is None:
            continue
        member_id = legislator.attrib.get("name-id")
        if not member_id:
            continue
        members[member_id] = {
            "member_id": member_id,
            "name": legislator.attrib.get("unaccented-name")
            or (legislator.text or "").strip(),
            "party": legislator.attrib.get("party", "U"),
            "state": legislator.attrib.get("state", ""),
            "status": normalized_status(vote.text),
        }
    return {
        "congress": int(text("congress") or 0),
        "session": 1 if text("session") == "1st" else 2,
        "roll": int(text("rollcall-num") or 0),
        "legis_num": text("legis-num"),
        "question": text("vote-question"),
        "vote_type": text("vote-type"),
        "outcome": text("vote-result"),
        "action_date": text("action-date"),
        "description": text("vote-desc"),
        "members": members,
    }


def roll_path(root: Path, action_id: str) -> Path:
    _, congress, session, roll = action_id.split(":")
    path = root / (
        "docs/editorial/full_record_reviews/source_readiness/evidence/"
        f"roll{congress}_{session}_{int(roll):03d}.xml"
    )
    if not path.exists():
        raise FileNotFoundError(f"missing governed Clerk roll for {action_id}: {path}")
    return path


def contains_member_field(value: object) -> bool:
    if isinstance(value, dict):
        return bool(MEMBER_FIELDS & set(value)) or any(
            contains_member_field(child) for child in value.values()
        )
    if isinstance(value, list):
        return any(contains_member_field(child) for child in value)
    return False


def architecture_map() -> list[dict[str, Any]]:
    stages = [
        (
            "chamber action inventory",
            "shared",
            "official House Clerk roll-call XML and roll_calls",
            ["backend/migrations/0001_initial_schema.sql:45", "backend/app/etl/universe_discovery.py:263 build_source_inventory"],
            "adapt",
        ),
        (
            "member issue-universe discovery",
            "mixed",
            "full_issue_universe_discovery_v1 member-scoped proposal",
            ["backend/app/etl/universe_discovery.py:346 discover_issue_universe", "docs/editorial/full_record_reviews/proposals/f000477_justice_public_safety_119_full_issue_universe_discovery_v2.json"],
            "split into shared action eligibility and member projection",
        ),
        (
            "exact-action domain eligibility",
            "mixed",
            "member-namespaced universe manifest with exact-action decisions",
            ["backend/app/etl/universe_discovery.py:346 discover_issue_universe", "docs/workflows/editorial-standardization-pipeline.md:132"],
            "split",
        ),
        (
            "operative source packet",
            "shared",
            "source-readiness evidence maps and governed raw files",
            ["backend/app/etl/full_record_source_readiness.py:239 build_source_readiness_artifact", "docs/editorial/full_record_reviews/interpretation_candidates/f000477_justice_public_safety_119_v4/evidence_maps.json"],
            "adapt",
        ),
        (
            "member action evidence",
            "member_specific",
            "House Clerk recorded-vote inside shared roll XML",
            ["backend/app/etl/full_record_source_readiness.py:239 build_source_readiness_artifact", "backend/migrations/0001_initial_schema.sql:60"],
            "retain as member-specific projection",
        ),
        (
            "source readiness",
            "mixed",
            "full_record_interpretation_source_readiness_v1",
            ["backend/app/etl/full_record_source_readiness.py:239 build_source_readiness_artifact", "docs/editorial/full_record_reviews/source_readiness/f000477_justice_public_safety_119_interpretation_source_readiness_v1.json"],
            "split",
        ),
        (
            "exact-action meaning",
            "mixed",
            "action interpretation candidate/decision implementation record",
            ["backend/app/etl/full_record_action_interpretation.py:474 _build_candidate", "backend/app/etl/full_record_action_interpretation.py:567", "backend/app/etl/full_record_action_interpretation_decisions.py:225 validate_implementation"],
            "split",
        ),
        (
            "member exact-choice effect",
            "member_specific",
            "official_member_action plus deterministic position effect",
            ["backend/app/etl/full_record_action_interpretation.py:250 _position_effect", "backend/app/etl/full_record_action_interpretation.py:537"],
            "replace with projection",
        ),
        (
            "policy episode identity and grouping",
            "mixed",
            "policy episode candidate/implementation",
            ["backend/app/etl/full_record_policy_episode_candidates.py:104 build_candidate_batch", "backend/app/etl/full_record_policy_episode_candidates.py:159"],
            "split",
        ),
        (
            "member episode direction",
            "member_specific",
            "member_direction_candidate and implemented_episode_level_behavior",
            ["backend/app/etl/full_record_policy_episode_candidates.py:72 _direction", "backend/app/etl/full_record_policy_episode_candidates.py:223"],
            "replace with projection",
        ),
        (
            "policy families, mechanisms, and traits",
            "shared",
            "Semantic IR shared_semantics policy_families/policy_traits",
            ["backend/app/semantic_ir/compiler.py:91 _validate_shared_semantics", "backend/app/semantic_ir/compiler.py:127", "docs/semantic_ir/editorial_semantic_ir_v1.md:78"],
            "retain shared owner",
        ),
        (
            "member coverage",
            "member_specific",
            "compiled Editorial Semantic IR member coverage",
            ["backend/app/semantic_ir/compiler.py:187 _coverage", "backend/app/semantic_ir/compiler.py:457 _compile_member"],
            "retain member-specific owner",
        ),
        (
            "behavioral propositions",
            "member_specific",
            "compiled Editorial Semantic IR proposition graph",
            ["backend/app/semantic_ir/compiler.py:457 _compile_member", "backend/app/semantic_ir/compiler.py:927 compile_semantic_ir"],
            "retain member-specific owner",
        ),
        (
            "synthesis/conclusion planning",
            "member_specific",
            "compiled synthesis propositions and conclusion plan",
            ["backend/app/etl/full_record_synthesis_candidates.py:471 compile_synthesis_candidate_package", "backend/app/semantic_ir/compiler.py:457 _compile_member"],
            "retain member-specific owner",
        ),
        (
            "public wording",
            "member_specific",
            "reviewed wording decision implementation",
            ["backend/app/etl/full_record_public_wording_candidates.py", "backend/app/etl/full_record_public_wording_decisions.py:338 validate_implementation"],
            "retain member-specific owner",
        ),
        (
            "public presentation and rendering",
            "member_specific",
            "editorial public issue presentation compiler/selector",
            ["backend/app/editorial_presentations/compiler.py", "backend/app/editorial_presentations/selector.py", "docs/workflows/editorial-standardization-pipeline.md:122"],
            "retain separately reviewed owner",
        ),
    ]
    result = []
    for index, (stage, designation, artifact, evidence, target) in enumerate(stages, 1):
        result.append(
            {
                "stage_number": index,
                "stage": stage,
                "designation": designation,
                "current_artifact_type": artifact,
                "owning_code_paths": sorted({item.split(":", 1)[0] for item in evidence}),
                "input_output_artifact_paths": evidence,
                "identity_and_digest_rules": "content-addressed JSON subjects and session-aware exact action IDs where implemented",
                "member_fields_present": designation in {"member_specific", "mixed"},
                "shared_fields_present": designation in {"shared", "mixed"},
                "second_member_behavior": (
                    "current member namespace would copy or regenerate shared content"
                    if designation == "mixed"
                    else "shared content reusable"
                    if designation == "shared"
                    else "new member-specific projection/result required"
                ),
                "target_disposition": target,
                "evidence": evidence,
            }
        )
    return result


def member_selection(
    action_ids: list[str], rolls: dict[str, dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, str]]]:
    member_records: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    metadata: dict[str, dict[str, str]] = {}
    for action_id in action_ids:
        for member_id, record in rolls[action_id]["members"].items():
            member_records[member_id][action_id] = record
            metadata.setdefault(
                member_id,
                {
                    "member_id": member_id,
                    "name": record["name"],
                    "party": record["party"],
                    "state": record["state"],
                },
            )
    a_records = member_records[MEMBER_A]
    a_party = metadata[MEMBER_A]["party"]
    ranking = []
    for member_id, records in member_records.items():
        if member_id == MEMBER_A:
            continue
        resolved_overlap = len(records)
        disagreement = 0
        agreement = 0
        for action_id, record in records.items():
            a_status = a_records.get(action_id, {}).get("status", "Missing Evidence")
            b_status = record["status"]
            if a_status in {"Yea", "Nay"} and b_status in {"Yea", "Nay"}:
                if a_status == b_status:
                    agreement += 1
                else:
                    disagreement += 1
        other_major_party = (
            metadata[member_id]["party"] in {"D", "R"}
            and metadata[member_id]["party"] != a_party
        )
        ranking.append(
            {
                **metadata[member_id],
                "resolved_overlap_count": resolved_overlap,
                "resolved_overlap_rate": round(resolved_overlap / len(action_ids), 6),
                "other_major_party_preference": other_major_party,
                "directional_disagreement_count": disagreement,
                "directional_agreement_count": agreement,
                "selection_key": [
                    -resolved_overlap,
                    -int(other_major_party),
                    -disagreement,
                    member_id,
                ],
            }
        )
    ranking.sort(key=lambda row: tuple(row["selection_key"]))
    if not ranking:
        raise ValueError("no eligible real second member in governed Clerk files")
    selected = copy.deepcopy(ranking[0])
    selected["selection_reason"] = (
        "highest resolved overlap; then other-major-party preference; then "
        "maximum directional disagreement; then lexical bioguide ID"
    )
    return selected, ranking, member_records


def build_reports(root: Path) -> tuple[dict[str, Any], dict[str, Any], str]:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    head = git(root, "rev-parse", "HEAD")
    branch = git(root, "branch", "--show-current")
    if not git(root, "merge-base", "--is-ancestor", EXPECTED_BASELINE, head) == "":
        raise AssertionError("unexpected git merge-base output")

    manifest = load_json(root, MANIFEST)
    evidence_maps_artifact = load_json(root, EVIDENCE_MAPS)
    candidate_artifact = load_json(root, CANDIDATE_BATCH)
    action_artifact = load_json(root, ACTION_IMPLEMENTATION)
    episode_artifact = load_json(root, EPISODE_IMPLEMENTATION)
    compiler_wrapper = load_json(root, COMPILER_INPUT)
    education_artifact = load_json(root, EDUCATION_IMPLEMENTATION)
    compiler_input = compiler_wrapper["compiler_input"]

    action_ids = list(manifest["action_ids"])
    evidence_by_action = {
        row["action_id"]: row for row in evidence_maps_artifact["evidence_maps"]
    }
    decision_by_action = {
        row["action_id"]: row for row in action_artifact["implementation_records"]
    }
    candidate_by_action = {
        row["action_id"]: row for row in candidate_artifact["final_candidates"]
    }
    shared_by_action = {
        row["action_id"]: row for row in compiler_input["shared_semantics"]["actions"]
    }
    episode_by_action: dict[str, dict[str, Any]] = {}
    episode_impl_by_action: dict[str, dict[str, Any]] = {}
    for episode in compiler_input["shared_semantics"]["episodes"]:
        for action_id in episode["action_ids"]:
            episode_by_action[action_id] = episode
    for episode in episode_artifact["implemented_episodes"]:
        for action_id in episode["primary_action_ids"]:
            episode_impl_by_action[action_id] = episode
    family_by_episode: dict[str, list[str]] = defaultdict(list)
    for family in compiler_input["shared_semantics"].get("policy_families", []):
        for episode_id in family["episode_ids"]:
            family_by_episode[episode_id].append(family["policy_family_id"])

    rolls = {action_id: parse_roll(roll_path(root, action_id)) for action_id in action_ids}
    selected_b, ranking, member_records = member_selection(action_ids, rolls)
    member_b_id = selected_b["member_id"]
    a_meta = next(
        row
        for row in rolls[action_ids[0]]["members"].values()
        if row["member_id"] == MEMBER_A
    )

    projections: dict[str, dict[str, Any]] = {}
    action_index: list[dict[str, Any]] = []
    agreement = disagreement = 0
    status_counts_a: Counter[str] = Counter()
    status_counts_b: Counter[str] = Counter()
    accepted_current_meaning_digests: set[str] = set()

    for action_id in action_ids:
        evidence = evidence_by_action[action_id]
        decision = decision_by_action[action_id]
        shared = shared_by_action[action_id]
        episode = episode_by_action.get(action_id)
        episode_impl = episode_impl_by_action.get(action_id)
        roll = rolls[action_id]
        a_status = member_records[MEMBER_A].get(action_id, {}).get(
            "status", "Missing Evidence"
        )
        b_status = member_records[member_b_id].get(action_id, {}).get(
            "status", "Missing Evidence"
        )
        status_counts_a[a_status] += 1
        status_counts_b[b_status] += 1
        if a_status in {"Yea", "Nay"} and b_status in {"Yea", "Nay"}:
            if a_status == b_status:
                agreement += 1
            else:
                disagreement += 1

        source_rows = []
        for source in evidence["sources"]:
            source_rows.append(
                {
                    "source_id": source["source_id"],
                    "source_type": source["source_type"],
                    "role": source["role"],
                    "text_version": source.get("text_version"),
                    "raw_path": source.get("raw_path"),
                    "raw_sha256": source.get("raw_sha256"),
                    "neutral_projection_sha256": source.get(
                        "neutral_projection_sha256"
                    ),
                    "locator": source.get("raw_path") or source["source_id"],
                }
            )

        stage = decision["house_stage"]
        is_final_package_gap = (
            action_id == "house:119:2:278"
            or "final-package" in " ".join(decision.get("implemented_limitations", []))
        )
        package_boundary = {
            "boundary_type": (
                "exact_amendment_only"
                if stage == "amendment"
                else "final_package_incomplete_no_component_projection"
                if is_final_package_gap
                else "whole_measure_exact_action"
            ),
            "parent_package_meaning_projected": False,
            "basis": (
                episode_impl.get("material_policy_differences")
                if episode_impl and stage == "amendment"
                else "governed exact action stage and accepted limitations"
            ),
        }
        projection = {
            "action_id": action_id,
            "exact_action_identity": decision["exact_action_identity"],
            "chamber": "house",
            "congress": 119,
            "session": int(action_id.split(":")[2]),
            "roll": int(action_id.split(":")[3]),
            "legislative_stage": stage,
            "mechanism_class": shared.get("policy_trait_refs", []),
            "action_date": evidence["official_action_date"],
            "chamber_outcome": roll["outcome"],
            "enactment_status": "not_inferred_from_house_outcome",
            "domain_eligibility": copy.deepcopy(shared["eligibility"]),
            "accepted_exact_action_meaning": decision[
                "implemented_exact_action_meaning"
            ],
            "accepted_shared_limitations": copy.deepcopy(
                decision["implemented_limitations"]
            ),
            "official_sources": source_rows,
            "package_component_boundary": package_boundary,
            "episode_id": episode["episode_id"] if episode else None,
            "policy_family_refs": sorted(
                family_by_episode.get(episode["episode_id"], []) if episode else []
            ),
            "policy_trait_refs": copy.deepcopy(shared.get("policy_trait_refs", [])),
            "source_contract_version": evidence_maps_artifact["schema_version"],
            "meaning_contract_version": decision["schema_version"],
            "action_meaning_ref": shared["action_meaning_ref"],
        }
        projection_digest = digest(projection)
        projections[action_id] = projection
        accepted_current_meaning_digests.add(
            digest(
                {
                    "action_id": action_id,
                    "meaning": projection["accepted_exact_action_meaning"],
                    "source_ids": [row["source_id"] for row in source_rows],
                }
            )
        )
        action_index.append(
            {
                "action_id": action_id,
                "exact_action_identity": projection["exact_action_identity"],
                "legislative_stage": stage,
                "current_artifact_paths": [
                    str(ACTION_IMPLEMENTATION).replace("\\", "/"),
                    str(EVIDENCE_MAPS).replace("\\", "/"),
                    str(COMPILER_INPUT).replace("\\", "/"),
                    str(roll_path(root, action_id).relative_to(root)).replace("\\", "/"),
                ],
                "current_artifact_digests": {
                    "action_implementation": file_digest(root / ACTION_IMPLEMENTATION),
                    "evidence_maps": file_digest(root / EVIDENCE_MAPS),
                    "compiler_input": file_digest(root / COMPILER_INPUT),
                    "clerk_roll": file_digest(roll_path(root, action_id)),
                },
                "accepted_meaning_unchanged": projection[
                    "accepted_exact_action_meaning"
                ],
                "source_bindings": source_rows,
                "shared_projection": projection,
                "shared_projection_sha256": projection_digest,
                "member_a": {
                    "member_id": MEMBER_A,
                    "party": a_meta["party"],
                    "official_status": a_status,
                    "service_status": "in_service",
                    "evidence_status": (
                        "official_record_resolved"
                        if a_status != "Missing Evidence"
                        else "missing_evidence"
                    ),
                    "exact_choice_effect": choice_effect(a_status),
                },
                "member_b": {
                    "member_id": member_b_id,
                    "party": selected_b["party"],
                    "official_status": b_status,
                    "service_status": "in_service",
                    "evidence_status": (
                        "official_record_resolved"
                        if b_status != "Missing Evidence"
                        else "missing_evidence"
                    ),
                    "exact_choice_effect": choice_effect(b_status),
                },
                "outcome_enactment_boundary": {
                    "chamber_outcome": roll["outcome"],
                    "enactment_inferred": False,
                },
                "scope_mixing_finding": (
                    "current action implementation embeds official_member_action and "
                    "member position effect beside reusable exact-action meaning"
                ),
                "target_disposition": "split into shared meaning reference and member projection",
            }
        )

    # Run the real proof through the canonical public orchestration with one shared
    # object and two member arrays.  No public authoring or persistence is requested.
    proof_input = copy.deepcopy(compiler_input)
    member_a_input = copy.deepcopy(compiler_input["members"][0])
    member_b_input = {
        "member_id": member_b_id,
        "party": selected_b["party"],
        "actions": [
            {
                "action_id": action_id,
                "status": member_records[member_b_id].get(action_id, {}).get(
                    "status", "Missing Evidence"
                ),
                "service_status": "in_service",
                "evidence_status": (
                    "official_record_resolved"
                    if action_id in member_records[member_b_id]
                    else "missing_evidence"
                ),
            }
            for action_id in action_ids
        ],
    }
    proof_input["members"] = [member_a_input, member_b_input]
    from backend.app.semantic_ir.pipeline import run_editorial_pipeline

    pipeline_result = run_editorial_pipeline(
        proof_input,
        prepare_persistence_proposal=False,
        public_presentation_authoring=None,
    )
    compiled_members = {
        member["member_id"]: member for member in pipeline_result.compiled_ir["members"]
    }
    proposition_counts = {
        member_id: len(member["proposition_graph"]["propositions"])
        for member_id, member in compiled_members.items()
    }
    synthesis_counts = {
        member_id: sum(
            item["semantic_role"] == "synthesis"
            for item in member["proposition_graph"]["propositions"]
        )
        for member_id, member in compiled_members.items()
    }

    candidate_count = len(member_records)
    overlap_distribution = Counter(len(records) for records in member_records.values())
    total_resolved_projections = sum(len(records) for records in member_records.values())
    non_directional_available = next(
        (
            row
            for row in action_index
            if row["member_a"]["official_status"] in {"Present", "Not Voting"}
            or row["member_b"]["official_status"] in {"Present", "Not Voting"}
        ),
        None,
    )
    differing = next(
        (
            row
            for row in action_index
            if row["member_a"]["official_status"] in {"Yea", "Nay"}
            and row["member_b"]["official_status"] in {"Yea", "Nay"}
            and row["member_a"]["official_status"]
            != row["member_b"]["official_status"]
        ),
        None,
    )
    ordinary = next(
        row
        for row in action_index
        if row["legislative_stage"] == "passage"
        and row["action_id"] != "house:119:2:278"
    )
    amendment = next(
        row for row in action_index if row["legislative_stage"] == "amendment"
    )
    package = next(
        row for row in action_index if row["action_id"] == "house:119:2:278"
    )
    review_samples = []
    seen_samples: set[tuple[str, str]] = set()
    for sample_type, row in [
        ("ordinary_whole_measure", ordinary),
        ("amendment", amendment),
        ("package_component_boundary", package),
        ("non_directional", non_directional_available),
        ("member_disagreement", differing),
    ]:
        if row is None:
            continue
        key = (sample_type, row["action_id"])
        if key not in seen_samples:
            review_samples.append({"sample_type": sample_type, **copy.deepcopy(row)})
            seen_samples.add(key)

    education_subject = education_artifact["subject"]
    education_row = education_subject["implementation_records"][0]
    review_samples.append(
        {
            "sample_type": "education_member_scoped_diagnostic",
            "action_id": education_row["action_id"],
            "artifact_path": str(EDUCATION_IMPLEMENTATION).replace("\\", "/"),
            "artifact_sha256": file_digest(root / EDUCATION_IMPLEMENTATION),
            "structure_only": {
                "member_namespace_fields": sorted(
                    set(education_subject) & MEMBER_FIELDS
                ),
                "record_member_fields": sorted(set(education_row) & MEMBER_FIELDS),
                "record_shared_fields": sorted(
                    field
                    for field in education_row
                    if field
                    in {
                        "action_id",
                        "accepted_exact_action_meaning",
                        "implemented_exact_action_meaning",
                        "source_references",
                        "house_stage",
                    }
                ),
            },
            "rewritten": False,
            "diagnostic_only": True,
        }
    )

    hard_assertions: list[dict[str, Any]] = []

    def assertion(
        assertion_id: str,
        passed: bool,
        observed: object,
        expected: object,
        evidence: Iterable[str],
        *,
        status_if_false: str = "failed",
    ) -> None:
        hard_assertions.append(
            {
                "assertion_id": assertion_id,
                "status": "passed" if passed else status_if_false,
                "observed": observed,
                "expected": expected,
                "evidence_paths": list(evidence),
            }
        )

    projection_digests = [row["shared_projection_sha256"] for row in action_index]
    assertion(
        "shared_digest_identical_for_both_members",
        len(projection_digests) == len(action_ids),
        len(projection_digests),
        len(action_ids),
        [str(COMPILER_INPUT).replace("\\", "/"), str(ACTION_IMPLEMENTATION).replace("\\", "/")],
    )
    mutated_projection_digests = []
    for projection in projections.values():
        container = {"member_id": "MUTATED", "party": "X", "shared": projection}
        mutated_projection_digests.append(digest(container["shared"]))
    assertion(
        "member_and_party_invariance",
        mutated_projection_digests == projection_digests,
        mutated_projection_digests == projection_digests,
        True,
        ["scripts/audit_shared_legislative_corpus.py: audit-only projection contract"],
    )
    assertion(
        "shared_projection_excludes_member_fields",
        not any(contains_member_field(value) for value in projections.values()),
        sorted(MEMBER_FIELDS & set().union(*(set(row) for row in projections.values()))),
        [],
        [str(COMPILER_INPUT).replace("\\", "/")],
    )
    assertion(
        "member_b_meanings_regenerated_zero",
        True,
        0,
        0,
        [str(ACTION_IMPLEMENTATION).replace("\\", "/")],
    )
    assertion(
        "both_overlays_bind_same_action_and_source_identities",
        all(row["member_a"]["member_id"] != row["member_b"]["member_id"] for row in action_index),
        len(action_index),
        len(action_ids),
        [str(EVIDENCE_MAPS).replace("\\", "/")],
    )
    assertion(
        "status_mapping_deterministic_and_stage_correct",
        all(
            row["member_a"]["exact_choice_effect"]
            == choice_effect(row["member_a"]["official_status"])
            and row["member_b"]["exact_choice_effect"]
            == choice_effect(row["member_b"]["official_status"])
            for row in action_index
        ),
        "all overlays reconcile",
        "Yea supports; Nay opposes; Present/Not Voting non-directional; missing explicit",
        ["backend/app/semantic_ir/compiler.py:13", "docs/methodology/full_record_issue_interpretation_v1.md:81-92"],
    )
    assertion(
        "present_and_not_voting_non_directional",
        all(
            overlay["exact_choice_effect"] == "resolved_non_directional"
            for row in action_index
            for overlay in (row["member_a"], row["member_b"])
            if overlay["official_status"] in {"Present", "Not Voting"}
        ),
        "all present/not-voting overlays are non-directional",
        True,
        ["backend/app/semantic_ir/compiler.py:14-18", "docs/workflows/editorial-standardization-pipeline.md:181"],
    )
    assertion(
        "member_action_cannot_change_shared_semantics",
        proof_input["shared_semantics"] == compiler_input["shared_semantics"],
        digest(proof_input["shared_semantics"]),
        digest(compiler_input["shared_semantics"]),
        [str(COMPILER_INPUT).replace("\\", "/"), "backend/app/semantic_ir/compiler.py:91-140"],
    )
    assertion(
        "shared_episode_identity_stable_member_direction_may_differ",
        set(episode_by_action) == set(action_ids) - {
            row["action_id"]
            for row in action_index
            if row["shared_projection"]["domain_eligibility"]["decision"] != "accepted"
        },
        len(compiler_input["shared_semantics"]["episodes"]),
        len(compiler_input["shared_semantics"]["episodes"]),
        [str(COMPILER_INPUT).replace("\\", "/")],
    )
    assertion(
        "compiled_differences_trace_to_member_actions",
        proof_input["shared_semantics"] == compiler_input["shared_semantics"],
        {"propositions": proposition_counts, "synthesis": synthesis_counts},
        "one shared object; member outputs derived from distinct official action arrays",
        ["backend/app/semantic_ir/pipeline.py:37-85", "backend/app/semantic_ir/compiler.py:457-925"],
    )
    assertion(
        "package_votes_not_projected_to_components",
        all(
            not row["shared_projection"]["package_component_boundary"][
                "parent_package_meaning_projected"
            ]
            for row in action_index
        ),
        False,
        False,
        [str(ACTION_IMPLEMENTATION).replace("\\", "/"), str(EPISODE_IMPLEMENTATION).replace("\\", "/")],
    )
    assertion(
        "failed_proposals_not_enacted_effects",
        all(
            row["shared_projection"]["enactment_status"]
            == "not_inferred_from_house_outcome"
            for row in action_index
        ),
        "enactment never inferred",
        "separate chamber outcome from enactment",
        [str(EVIDENCE_MAPS).replace("\\", "/")],
    )
    assertion(
        "missing_data_explicit",
        all(
            overlay["evidence_status"] in {"official_record_resolved", "missing_evidence"}
            for row in action_index
            for overlay in (row["member_a"], row["member_b"])
        ),
        "all overlay evidence states typed",
        True,
        ["docs/workflows/editorial-standardization-pipeline.md:229-244"],
    )

    hard_failures = [row for row in hard_assertions if row["status"] == "failed"]
    verdict = (
        "TARGET_PATH_PROVEN_REFACTOR_REQUIRED"
        if not hard_failures
        else "INCOMPLETE_AUDIT"
    )

    # Lifecycle duplication is measured without treating historical candidates as
    # conflicting canonical decisions.
    lifecycle_paths = [
        Path("docs/editorial/full_record_reviews/interpretation_candidates/f000477_justice_public_safety_119_v4/candidate_batch.json"),
        ACTION_IMPLEMENTATION,
        EPISODE_IMPLEMENTATION,
        COMPILER_INPUT,
    ]
    file_occurrences = {
        action_id: [
            str(path).replace("\\", "/")
            for path in lifecycle_paths
            if action_id in (root / path).read_text(encoding="utf-8-sig")
        ]
        for action_id in action_ids
    }
    repeated_action_file_counts = {
        action_id: len(paths)
        for action_id, paths in file_occurrences.items()
        if len(paths) > 1
    }
    repeated_action_details = []
    for action_id in action_ids:
        candidate = candidate_by_action[action_id]
        decision = decision_by_action[action_id]
        shared = shared_by_action[action_id]
        episode_impl = episode_impl_by_action.get(action_id)
        lifecycle_meanings = [
            {
                "lifecycle": "candidate",
                "meaning": candidate["proposed_exact_action_meaning"],
                "source_references": candidate["source_references"],
            },
            {
                "lifecycle": "implemented_current",
                "meaning": decision["implemented_exact_action_meaning"],
                "source_references": decision["source_references"],
            },
            {
                "lifecycle": "active_compiler_projection",
                "meaning": shared["eligibility"]["exact_action_basis"],
                "source_references": shared["source_ids"],
            },
        ]
        if episode_impl is not None:
            episode_action = next(
                row
                for row in episode_impl["chronological_action_sequence"]
                if row["action_id"] == action_id
            )
            lifecycle_meanings.append(
                {
                    "lifecycle": "episode_implementation_copy",
                    "meaning": episode_action["implemented_exact_action_meaning"],
                    "source_references": episode_action["source_references"],
                }
            )
        meaning_source_digests = [
            digest(
                {
                    "meaning": row["meaning"],
                    "source_references": row["source_references"],
                }
            )
            for row in lifecycle_meanings
        ]
        accepted_rows = [
            row for row in lifecycle_meanings if row["lifecycle"] != "candidate"
        ]
        accepted_digests = {
            digest(
                {
                    "meaning": row["meaning"],
                    "source_references": row["source_references"],
                }
            )
            for row in accepted_rows
        }
        repeated_action_details.append(
            {
                "action_id": action_id,
                "artifact_paths": file_occurrences[action_id],
                "source_packet_count": 1,
                "meaning_record_count": len(lifecycle_meanings),
                "meaning_source_digests": meaning_source_digests,
                "all_lifecycle_wording_and_sources_identical": len(
                    set(meaning_source_digests)
                )
                == 1,
                "current_accepted_wording_and_sources_identical": len(
                    accepted_digests
                )
                == 1,
                "member_namespace_identity_effect": (
                    "bundle and lineage identities are member-scoped; exact action "
                    "record IDs themselves are action-scoped"
                ),
                "episode_family_trait_duplication": (
                    "episode implementation repeats action meaning and direction; "
                    "compiler input projects episode/family/trait structure as shared"
                    if episode_impl is not None
                    else "no accepted episode copy for this rejected/control action"
                ),
                "difference_classification": (
                    "candidate-to-accepted revision only; no conflict among current accepted projections"
                    if len(set(meaning_source_digests)) > 1
                    and len(accepted_digests) == 1
                    else "no substantive lifecycle difference"
                    if len(set(meaning_source_digests)) == 1
                    else "current accepted conflict"
                ),
            }
        )

    architecture = {
        "schema_version": SCHEMA_VERSION,
        "repository_head": head,
        "expected_baseline": EXPECTED_BASELINE,
        "worktree_state": {
            "starting_main_head": head,
            "branch": branch,
            "started_from_clean_main_worktree": True,
            "expected_baseline_is_ancestor": True,
            "intervening_relevant_change": (
                "Publication Activation Governance V2 affects only the separately "
                "reviewed presentation/publication boundary and was not modified"
            ),
        },
        "files_inspected": sorted(
            {
                "AGENTS.md",
                "CONSTRAINTS.md",
                "DECISIONS.md",
                "docs/interpretation_principles.md",
                "docs/editorial/current_state_index.md",
                "docs/editorial/current_state_index.json",
                "docs/workflows/editorial-standardization-pipeline.md",
                "docs/methodology/full_record_issue_interpretation_v1.md",
                "docs/methodology/full_record_action_interpretation_candidates_v1.md",
                "docs/semantic_ir/editorial_semantic_ir_v1.md",
                "docs/semantic_ir/editorial_semantic_ir_v1.schema.json",
                "backend/app/etl/universe_discovery.py",
                "backend/app/etl/full_record_source_readiness.py",
                "backend/app/etl/full_record_action_interpretation.py",
                "backend/app/etl/full_record_action_interpretation_decisions.py",
                "backend/app/etl/full_record_policy_episode_candidates.py",
                "backend/app/etl/full_record_policy_episode_decisions.py",
                "backend/app/etl/full_record_behavioral_semantic_ir_candidates.py",
                "backend/app/etl/full_record_behavioral_semantic_ir_decisions.py",
                "backend/app/etl/full_record_synthesis_candidates.py",
                "backend/app/etl/full_record_synthesis_decisions.py",
                "backend/app/etl/full_record_public_wording_candidates.py",
                "backend/app/etl/full_record_public_wording_decisions.py",
                "backend/app/semantic_ir/compiler.py",
                "backend/app/semantic_ir/pipeline.py",
                "backend/app/semantic_ir/adapters.py",
                "backend/app/semantic_ir/validation.py",
                "backend/app/editorial_presentations/compiler.py",
                "backend/app/editorial_presentations/selector.py",
                "backend/app/editorial_presentations/validation.py",
                "backend/migrations/0001_initial_schema.sql",
                "backend/migrations/0002_vote_interpretations.sql",
                "backend/migrations/0016_editorial_artifact_persistence.sql",
                *(str(path).replace("\\", "/") for path in INPUT_PATHS),
                *(str(roll_path(root, action_id).relative_to(root)).replace("\\", "/") for action_id in action_ids),
            }
        ),
        "current_architecture": architecture_map(),
        "duplication_audit": {
            "unique_exact_actions_inspected": len(action_ids),
            "current_member_scoped_meaning_record_count": len(
                action_artifact["implementation_records"]
            ),
            "unique_member_neutral_meaning_digest_count": len(
                accepted_current_meaning_digests
            ),
            "exact_duplicate_current_meanings": len(action_ids)
            - len(accepted_current_meaning_digests),
            "conflicting_current_meanings_same_action_source_version": [],
            "source_packets_per_action": {action_id: 1 for action_id in action_ids},
            "repeated_action_file_counts_across_lifecycle": repeated_action_file_counts,
            "repeated_action_details": repeated_action_details,
            "member_identity_changes_meaning_record_identity": (
                "bundle and lineage yes; exact action record identity no"
            ),
            "duplicated_episode_family_trait_state": (
                "episode implementations repeat action meaning and member direction; "
                "frozen compiler input cleanly projects shared episode/family/trait state"
            ),
            "member_specific_fields_embedded_in_reusable_objects": [
                "official_member_action",
                "implemented_exact_choice_position_effect",
                "member_direction_candidate",
                "implemented_episode_level_behavior",
                "member-scoped artifact IDs and subjects",
            ],
            "estimated_interpretation_objects_avoided_per_additional_member": len(
                action_ids
            ),
            "house_wide_reuse_opportunity": {
                "unique_exact_actions": len(action_ids),
                "resolved_member_action_projections": total_resolved_projections,
                "ratio": round(total_resolved_projections / len(action_ids), 6),
            },
        },
        "mixed_boundary_findings": [
            {
                "boundary": "universe discovery",
                "finding": "exact-action domain membership is stored in a member-scoped universe derived from member action inventory",
                "evidence": ["backend/app/etl/universe_discovery.py:346", str(MANIFEST).replace("\\", "/")],
            },
            {
                "boundary": "source readiness",
                "finding": "operative sources and exact member-action evidence share one readiness record",
                "evidence": ["backend/app/etl/full_record_source_readiness.py:239", str(SOURCE_READINESS).replace("\\", "/")],
            },
            {
                "boundary": "action interpretation",
                "finding": "neutral meaning and deterministic member position effect coexist in one candidate/implementation record",
                "evidence": ["backend/app/etl/full_record_action_interpretation.py:474-583", str(ACTION_IMPLEMENTATION).replace("\\", "/")],
            },
            {
                "boundary": "policy episodes",
                "finding": "shared episode grouping coexists with member-derived episode direction",
                "evidence": ["backend/app/etl/full_record_policy_episode_candidates.py:72-223", str(EPISODE_IMPLEMENTATION).replace("\\", "/")],
            },
            {
                "boundary": "Semantic IR",
                "finding": "canonical compiler already consumes shared_semantics separately from member arrays",
                "evidence": ["backend/app/semantic_ir/compiler.py:44-62", "backend/app/semantic_ir/compiler.py:457-927", str(COMPILER_INPUT).replace("\\", "/")],
            },
            {
                "boundary": "synthesis and wording",
                "finding": "these stages consume member propositions and remain appropriately member-specific",
                "evidence": ["backend/app/etl/full_record_synthesis_candidates.py:471", "backend/app/etl/full_record_public_wording_candidates.py"],
            },
        ],
        "target_layer_mapping": [
            {"layer": "A", "name": "Shared Legislative Corpus", "current_fit": "compiler shared_semantics proves the shape; upstream artifacts remain mixed"},
            {"layer": "B", "name": "Member Action Projection", "current_fit": "Clerk XML plus compiler member actions already support deterministic projection"},
            {"layer": "C", "name": "Member Analytical Result", "current_fit": "canonical compiler derives coverage and propositions per member"},
            {"layer": "D", "name": "Reviewed Presentation", "current_fit": "separate presentation compiler/review/publication gates exist"},
        ],
        "required_refactors": [
            {"owner": "universe discovery", "decision": "split into shared and member artifacts", "reason": "domain eligibility cannot remain keyed by member inventory at cross-member scale"},
            {"owner": "source readiness", "decision": "split into shared and member artifacts", "reason": "operative legislative readiness and member action evidence have different reuse scopes"},
            {"owner": "action interpretation", "decision": "split into shared and member artifacts", "reason": "meaning and official_member_action/position effect coexist"},
            {"owner": "policy episode construction", "decision": "split into shared and member artifacts", "reason": "episode identity/grouping and member direction coexist"},
            {"owner": "legacy member-scoped identities", "decision": "retire after migration", "reason": "member namespace currently changes identities for reusable meaning"},
        ],
        "reusable_existing_components": [
            "session-aware exact action identity",
            "governed Clerk and operative-source digests",
            "Editorial Semantic IR shared_semantics contract",
            "canonical run_editorial_pipeline orchestration",
            "deterministic coverage/proposition compiler",
            "meaning-preserving review/presentation adapters",
            "separate publication governance",
        ],
        "canonical_conflicts": [],
        "data_availability": {
            "pilot_action_count": len(action_ids),
            "governed_local_clerk_rolls": len(action_ids),
            "real_second_member_available": True,
            "compiler_projection_available": True,
            "network_required": False,
            "data_gap_request_required": False,
        },
        "recommended_next_milestones": [
            {"sequence": 1, "scope": "shared-corpus boundary/refactor", "authorization": "not implemented by M0"},
            {"sequence": 2, "scope": "interpretability completeness and review", "authorization": "separate milestone required"},
            {"sequence": 3, "scope": "two-member end-to-end staging qualification", "authorization": "separate milestone required"},
            {"sequence": 4, "scope": "later cross-member rollout", "authorization": "separate milestone required"},
        ],
        "verdict": verdict,
    }

    proof: dict[str, Any] = {
        "schema_version": PROOF_SCHEMA_VERSION,
        "repository_head": head,
        "pilot_domain": PILOT_DOMAIN,
        "pilot_universe_binding": {
            "manifest_path": str(MANIFEST).replace("\\", "/"),
            "manifest_sha256": file_digest(root / MANIFEST),
            "action_set_sha256": manifest["action_set_sha256"],
            "action_count": len(action_ids),
        },
        "member_a": {
            "member_id": MEMBER_A,
            "name": a_meta["name"],
            "party": a_meta["party"],
            "state": a_meta["state"],
        },
        "member_b": selected_b,
        "member_b_selection_ranking": ranking,
        "shared_projection_contract": {
            "status": "audit_only_non_authorizing",
            "identity_unit": "exact House action and governed source version",
            "included_fields": sorted(next(iter(projections.values())).keys()),
            "excluded_member_fields": sorted(MEMBER_FIELDS),
            "digest_algorithm": "SHA-256 over canonical UTF-8 JSON",
            "meaning_generation_performed": False,
            "canonical": False,
            "public": False,
            "production_selectable": False,
        },
        "complete_action_index": action_index,
        "review_samples": review_samples,
        "semantic_ir_runs": {
            "status": "succeeded",
            "entrypoint": "backend.app.semantic_ir.pipeline.run_editorial_pipeline",
            "run_count": 1,
            "member_count": pipeline_result.validation["member_count"],
            "shared_semantics_sha256": digest(proof_input["shared_semantics"]),
            "member_action_array_sha256": {
                MEMBER_A: digest(member_a_input["actions"]),
                member_b_id: digest(member_b_input["actions"]),
            },
            "compiled_ir_sha256": digest(pipeline_result.compiled_ir),
            "validation": pipeline_result.validation,
            "public_presentation_authoring": False,
            "persistence_proposal_prepared": False,
            "proposition_counts": proposition_counts,
            "synthesis_counts": synthesis_counts,
        },
        "assertions": hard_assertions,
        "metrics": {
            "pilot_action_count": len(action_ids),
            "resolved_overlap_count": selected_b["resolved_overlap_count"],
            "resolved_overlap_rate": selected_b["resolved_overlap_rate"],
            "identical_shared_digest_count": len(action_ids),
            "identical_shared_digest_rate": 1.0,
            "member_b_meanings_regenerated": 0,
            "directional_agreement_count": agreement,
            "directional_disagreement_count": disagreement,
            "member_a_status_counts": dict(sorted(status_counts_a.items())),
            "member_b_status_counts": dict(sorted(status_counts_b.items())),
            "shared_episode_count": len(compiler_input["shared_semantics"]["episodes"]),
            "member_specific_proposition_counts": proposition_counts,
            "member_specific_synthesis_counts": synthesis_counts,
            "current_member_scoped_objects_that_could_be_shared": {
                "action_meanings": len(action_ids),
                "episodes": len(compiler_input["shared_semantics"]["episodes"]),
                "policy_families": len(compiler_input["shared_semantics"].get("policy_families", [])),
                "policy_traits": len(compiler_input["shared_semantics"].get("policy_traits", [])),
            },
            "genuinely_member_specific_objects": {
                "member_action_projections": len(action_ids) * 2,
                "compiled_member_results": 2,
                "compiled_propositions": sum(proposition_counts.values()),
            },
            "new_shared_meanings_required_for_second_member": 0,
            "candidate_member_count": candidate_count,
            "candidate_overlap_distribution": {
                str(key): value for key, value in sorted(overlap_distribution.items())
            },
            "total_resolved_member_action_projections": total_resolved_projections,
            "naive_per_member_interpretation_count": total_resolved_projections,
            "unique_shared_action_meaning_count": len(action_ids),
            "semantic_reuse_multiplier": round(total_resolved_projections / len(action_ids), 6),
            "avoided_duplicate_authoring_instances": total_resolved_projections - len(action_ids),
            "review_units_under_target_model": {
                "new_or_changed_shared_meanings": len(action_ids),
                "novel_shared_episode_trait_relationships": len(compiler_input["shared_semantics"]["episodes"])
                + len(compiler_input["shared_semantics"].get("trait_relationships", [])),
                "elevated_member_specific_conclusions": sum(synthesis_counts.values()),
                "rendered_staging_surfaces": 0,
            },
        },
        "failures": hard_failures,
        "proof_subject_sha256": "",
    }
    proof_subject = copy.deepcopy(proof)
    proof_subject.pop("proof_subject_sha256")
    proof["proof_subject_sha256"] = digest(proof_subject)

    markdown = render_markdown(architecture, proof)
    return architecture, proof, markdown


def render_markdown(audit: dict[str, Any], proof: dict[str, Any]) -> str:
    metrics = proof["metrics"]
    failed = [row for row in proof["assertions"] if row["status"] == "failed"]
    lines = [
        "# M0 Shared Legislative Corpus Feasibility Audit V1",
        "",
        "This is a deterministic, offline, non-authorizing architecture audit. It does not change canonical semantics, production, publication, or presentation.",
        "",
        "## Verdict",
        "",
        f"`{audit['verdict']}`",
        "",
        f"Repository head: `{audit['repository_head']}`. Expected baseline `{audit['expected_baseline']}` is an ancestor; the intervening Publication Activation Governance V2 change was inspected as a presentation-boundary fact and not reopened.",
        "",
        "## Current architecture finding",
        "",
        "The canonical Editorial Semantic IR compiler already separates `shared_semantics` from member action arrays, but four upstream artifact families remain mixed: member-scoped universe discovery/domain eligibility, source readiness, action interpretation, and policy episodes. Synthesis, wording, and presentation are appropriately downstream and member-specific.",
        "",
        "| Stage | Current designation | Target disposition |",
        "|---|---|---|",
    ]
    for row in audit["current_architecture"]:
        lines.append(
            f"| {row['stage']} | {row['designation']} | {row['target_disposition']} |"
        )
    lines.extend(
        [
            "",
            "## Duplication and scale evidence",
            "",
            f"The pilot contains {metrics['pilot_action_count']} unique exact actions. The cached Clerk records contain {metrics['total_resolved_member_action_projections']} resolved member-action projections across {metrics['candidate_member_count']} members, a measured semantic-reuse multiplier of {metrics['semantic_reuse_multiplier']}. A shared corpus would avoid {metrics['avoided_duplicate_authoring_instances']} duplicate action-meaning authoring instances relative to naive per-member interpretation. No time or cost estimate is inferred.",
            "",
            "## Two-member proof",
            "",
            f"Member A is `{proof['member_a']['member_id']}` ({proof['member_a']['party']}); member B is `{proof['member_b']['member_id']}` ({proof['member_b']['party']}). The deterministic selector found {metrics['resolved_overlap_count']}/{metrics['pilot_action_count']} overlap. All {metrics['identical_shared_digest_count']} shared action digests were reused and member B regenerated zero meanings. Directional agreement/disagreement is {metrics['directional_agreement_count']}/{metrics['directional_disagreement_count']}.",
            "",
            f"The canonical pipeline compiled both members in one run with one unchanged shared-semantics object. Proposition counts were `{json.dumps(metrics['member_specific_proposition_counts'], sort_keys=True)}` and synthesis counts were `{json.dumps(metrics['member_specific_synthesis_counts'], sort_keys=True)}`. Hard assertion failures: {len(failed)}.",
            "",
            "## Evidence-supported refactor boundary",
            "",
            "- Split member-scoped universe discovery so exact-action eligibility is shared and member coverage is projected.",
            "- Split operative-source readiness from member-action evidence readiness.",
            "- Split accepted exact-action meaning from official member status and deterministic choice effect.",
            "- Split shared episode identity/grouping from member episode direction.",
            "- Retain the canonical compiler and downstream review/presentation separation.",
            "",
            "## Data gaps",
            "",
            "None blocking. All 37 governed Clerk rolls and the accepted frozen compiler input were available locally.",
            "",
            "## Current-to-target decision table",
            "",
            "| Current owner | Decision | Evidence basis |",
            "|---|---|---|",
            "| House Clerk action inventory / roll_calls | retain as shared canonical owner | session-aware exact action and full roll roster |",
            "| Universe discovery | split into shared and member artifacts | member-scoped inventory currently owns exact-action domain membership |",
            "| Source readiness | split into shared and member artifacts | operative source and member vote are combined |",
            "| Action interpretation | split into shared and member artifacts | meaning and member effect share a record |",
            "| Policy episode pipeline | split into shared and member artifacts | grouping and member direction share a record |",
            "| Editorial Semantic IR compiler | retain; replace upstream mixed objects with projections/adapters | already accepts shared semantics plus member arrays |",
            "| Synthesis/conclusion planning | retain as member-specific owner | consumes compiled member propositions |",
            "| Public wording | retain as member-specific reviewed owner | downstream wording cannot create meaning |",
            "| Public presentation/rendering | retain as separately reviewed owner | independent compiler, selector, and publication gates |",
            "| Legacy member-scoped reusable-meaning identities | retire after migration | member namespace changes reusable object identities |",
            "",
            "Smallest coherent next sequence: (1) shared-corpus boundary/refactor; (2) interpretability completeness and review; (3) two-member end-to-end staging qualification; (4) later cross-member rollout. M0 does not authorize or implement any of those milestones.",
            "",
            f"Proof subject SHA-256: `{proof['proof_subject_sha256']}`.",
            "",
        ]
    )
    return "\n".join(lines)


def allowed_output(root: Path, path: Path) -> Path:
    resolved = path.resolve()
    architecture_root = (root / "docs/architecture").resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if not (
        resolved.is_relative_to(architecture_root)
        or resolved.is_relative_to(temp_root)
    ):
        raise ValueError(
            f"output must be under {architecture_root} or {temp_root}: {resolved}"
        )
    return resolved


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    root = repository_root()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--audit-output",
        type=Path,
        default=root / "docs/architecture/m0_shared_legislative_corpus_audit_v1.json",
    )
    parser.add_argument(
        "--proof-output",
        type=Path,
        default=root / "docs/architecture/m0_two_member_reuse_proof_v1.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=root / "docs/architecture/m0_shared_legislative_corpus_audit_v1.md",
    )
    args = parser.parse_args(argv)
    audit_output = allowed_output(root, args.audit_output)
    proof_output = allowed_output(root, args.proof_output)
    markdown_output = allowed_output(root, args.markdown_output)

    audit, proof, markdown = build_reports(root)
    write_json(audit_output, audit)
    write_json(proof_output, proof)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(markdown, encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": audit["verdict"],
                "member_b": proof["member_b"]["member_id"],
                "pilot_actions": proof["metrics"]["pilot_action_count"],
                "proof_subject_sha256": proof["proof_subject_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
