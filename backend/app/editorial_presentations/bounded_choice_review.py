"""Closed S.2393 bounded-choice review, without inherited full-record authority.

Semantic objects are frozen inputs. A detached receipt accepts their exact
bounded presentation/rendering subject; it never grants publication or writes.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import struct
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from .compiler import canonical_digest
from . import bounded_choice_authority as owner_authority
from ..semantic_ir.validation import validate_compiled_ir
from ..etl.full_record_source_readiness import _filesystem_path

ROOT = Path(__file__).resolve().parents[3]
BASE = "c52d121b64d814de3cf684980368bced40e5b4ea"
PACKAGE = "docs/editorial/review_packages/health_s2393_one_action_v1/"
ACTION = "house:119:2:180"
EPISODE = "episode:s2393:119"
ISSUE = "HEALTH_SOCIAL"
MEMBERS = {
    "F000477": ("Valerie Foushee", "leg_valerie_p_foushee", "Yea"),
    "M001184": ("Thomas Massie", "leg_thomas_massie", "Not Voting"),
}
PACKET_SHA = "3b6b60a88bb7ca9ef42abe4fb80714910d490ea9dac4eb8b79a6cfc547960347"
FOUNDATION = {
    "claim_source_map.json": "06842839c6e2d30f98fe54b3715dec076d29f2229e3daf585448fef655b68a18",
    "compiled_ir.json": "29be897f6a2d48754f2ac5ec5966474cad88ba0bed9df36cb654af2fa9b4ace6",
    "compiler_input.json": "9028cec5e68c768a3a1492cafd60d4f567b69ecca21c02b9afed83883b7a23b7",
    "governed_sources.json": "7fa4ca255dd204670279e20ca2bcd69c1523d4787a28e0f15cb7991e22f0bc9a",
    "member_projections.json": "91ec2c9ae85acb4f3414c5443ec2ab69fa072bf99161f5c5da651e7897787fea",
    "membership_evidence.json": "cf9b26e72cfb61551dd29f4e02128d93816fb90313e7f93ba614287218669009",
    "presentation_inputs.json": "8ab6421bebb608284d95f7186a7294c687f7015db12915a214a15c81dc63f2ce",
    "presentation_payload.json": "a45e00939f5b31c11e15f0cfb49f731125ce1ffcb5f746522ccd6ad26a8636f3",
    "provenance.json": "bcbbfc8d5bbfd5b575b2d2988c93fd391e6e10bd4f385f4006ce949e09f7ae31",
    "review_source_contract.json": "ae39cd1129f3dfcb51de9f60ae32866d684255384c74f6bbcca8bc5488bca975",
    "shared_action_core.json": "202d6b30429e4b30b577d14beee9318045514ba2426f0870c621f4a4e923324f",
    "shared_issue_mapping.json": "13d974f4c290977f0c16b77d19bbf025f7d59a9010c08949307dde4130dcaa03",
}
RAW_ROOT = "docs/editorial/full_record_reviews/source_readiness/evidence/f000477_national_security_foreign_119_v1/"
RAW = {
    "04f063befa42e8b335fc14539b218401408cfb806c3e734438a67d944db10689_BILLS-119s2393es.xml": "congress-text:119:s:2393:es",
    "d52d940529fbb4eab886c5c32ad6e712097829f93c886d5adb8cd171541c5e52_roll119_2_180.xml": "clerk:house:119:2:180",
    "a143f675f626923c67e3b3b50b242be832f4daab6389caed725b3f70ccef7bc0_119_s_2393_actions.json": "congress-actions:house:119:2:180",
}
NO_OPERATIONAL_AUTHORITY = {
    "publication": False,
    "production_eligibility": False,
    "database_writes": False,
    "deployment": False,
}
RENDER_FILES = (
    "frontend/components/BoundedChoiceReview.js",
    "frontend/components/ReviewedAnalysisSection.js",
    "frontend/app/review/health-choice/page.js",
    "frontend/app/globals.css",
    "frontend/app/layout.js",
    "frontend/package-lock.json",
    "frontend/next.config.mjs",
    "frontend/components/IssueDetail.js",
    "frontend/lib/selectedIssueExperience.mjs",
    "frontend/lib/editorialPresentation.mjs",
    "frontend/lib/boundedChoicePresentation.mjs",
    "frontend/lib/frontendPassA.mjs",
    "frontend/lib/recordCard.mjs",
    "frontend/components/IssueOverviewGrid.js",
    "frontend/components/RepresentativeExperience.js",
    "backend/app/editorial_presentations/bounded_choice_authority.py",
    "backend/app/editorial_presentations/bounded_choice_pair.py",
    "backend/app/editorial_presentations/bounded_choice_sources.py",
    "backend/app/editorial_presentations/bounded_choice_review.py",
    "backend/app/editorial_presentations/bounded_choice_publication.py",
    "backend/app/editorial_presentations/selector.py",
    "backend/app/editorial_presentations/compiler.py",
    "backend/app/editorial_presentations/publication_activation_governance_v2.py",
    "backend/app/editorial_artifacts/repository.py",
    "backend/app/api/editorial_presentations.py",
    "backend/app/semantic_ir/validation.py",
    "scripts/validate_full_record_issue_interpretation.py",
    "docs/methodology/full_record_issue_interpretation_v1.schema.json",
    "backend/migrations/0016_editorial_artifact_persistence.sql",
    "backend/migrations/staged/20261019231216_bounded_health_choice_publication.sql",
)


class BoundedChoiceReviewError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BoundedChoiceReviewError(message)


def seal(value: dict, field: str) -> dict:
    result = copy.deepcopy(value)
    result.pop(field, None)
    result[field] = canonical_digest(result)
    return result


def check_seal(value: dict, field: str) -> None:
    require(isinstance(value, dict), "bounded object is required")
    require(
        value.get(field)
        == canonical_digest({k: v for k, v in value.items() if k != field}),
        field + " differs",
    )


def load_foundation(root: Path = ROOT) -> dict[str, Any]:
    result = {
        name: json.loads((root / PACKAGE / name).read_text(encoding="utf-8"))
        for name in FOUNDATION
    }
    validate_foundation(result)
    require(
        hashlib.sha256((root / PACKAGE / "DECISION-PACKET.md").read_bytes()).hexdigest()
        == PACKET_SHA,
        "original packet bytes differ",
    )
    return result


def validate_foundation(foundation: dict) -> None:
    require(set(foundation) == set(FOUNDATION), "bounded foundation file set differs")
    for name, expected in FOUNDATION.items():
        require(
            canonical_digest(foundation[name]) == expected,
            "frozen bounded input differs: " + name,
        )
    validate_compiled_ir(foundation["compiled_ir.json"])
    replay_foundation(foundation)


def replay_foundation(foundation: dict) -> None:
    from ..semantic_ir.shared_corpus import adapt_to_semantic_ir_input
    from ..semantic_ir.pipeline import run_editorial_pipeline

    compiler_input = adapt_to_semantic_ir_input(
        ROOT,
        foundation["shared_action_core.json"],
        foundation["shared_issue_mapping.json"],
        foundation["member_projections.json"],
    )
    require(
        canonical_digest(compiler_input)
        == canonical_digest(foundation["compiler_input.json"]),
        "compiler input replay differs",
    )
    result = run_editorial_pipeline(compiler_input)
    require(
        canonical_digest(result.compiled_ir)
        == canonical_digest(foundation["compiled_ir.json"]),
        "compiled IR replay differs",
    )
    require(
        canonical_digest(result.presentation_payload)
        == canonical_digest(foundation["presentation_payload.json"]),
        "presentation replay differs",
    )


def source_evidence(root: Path = ROOT) -> list[dict]:
    evidence = []
    raw_sources = {}
    for name, source_id in RAW.items():
        path = RAW_ROOT + name
        raw = _filesystem_path(root / path).read_bytes()
        raw_sources[source_id] = raw
        require(
            hashlib.sha256(raw).hexdigest() == name[:64],
            "retained raw evidence differs: " + source_id,
        )
        evidence.append(
            {
                "source_id": source_id,
                "path": path,
                "raw_sha256": name[:64],
                "origin_commit": BASE,
                "role": "additional_preparation_evidence_no_inherited_acceptance",
            }
        )
    from .bounded_choice_sources import reconcile_sources

    governed = json.loads(
        (root / PACKAGE / "governed_sources.json").read_text(encoding="utf-8")
    )
    reconcile_sources(raw_sources, governed)
    return evidence


def member_part(foundation: dict, name: str, member_id: str) -> dict:
    require(member_id in MEMBERS, "bounded member is not permitted")
    matches = [
        row for row in foundation[name]["members"] if row["member_id"] == member_id
    ]
    require(len(matches) == 1, "bounded member identity differs")
    return copy.deepcopy(matches[0])


def build_accounting_review(foundation: dict, member_id: str) -> dict:
    """Construct a candidate manifest for the EXISTING validate_review boundary."""
    validate_foundation(foundation)
    require(member_id in MEMBERS, "bounded member is not permitted")
    status = MEMBERS[member_id][2]
    meaning = foundation["shared_action_core.json"]["actions"][0]
    interpretation = {
        "interpretation_id": f"bounded-choice-interpretation:{member_id.lower()}:s2393:v1",
        "action_meaning_id": meaning["action_meaning_ref"],
        "exact_action_meaning": meaning["candidate_exact_action_meaning"],
        "member_action": status,
        "evidence_status": "official_record_resolved",
        "service_status": "in_service",
        "vote_source_refs": ["clerk:119:2:180"],
        "action_meaning_source_refs": ["govinfo:s2393es"],
        "episode_id": EPISODE,
        "review_state": "candidate",
        "interpretation_receipt_refs": [
            "docs/review_packets/health_one_action_owner_decision_receipt_draft.md"
        ],
    }
    interpretation = seal(interpretation, "interpretation_sha256")
    axes = {
        "semantic_tier": "receipts_only",
        "review_scope": "bounded_partial_record",
        "review_completion_state": "in_progress",
        "public_claim_class": "vote_record_only",
    }
    review = {
        "schema_version": "full_record_issue_interpretation_v1",
        "review_id": f"full-review:{member_id.lower()}:health-s2393:bounded:119:v1",
        "subject": {"member_id": member_id, "issue_id": ISSUE, "congress_scope": [119]},
        "axes": axes,
        "issue_universe": {
            "snapshot_id": f"issue-universe:{member_id.lower()}:health-s2393:119:v1",
            "snapshot_sha256": "",
            "definition": "Exactly one previously selected House choice on S.2393; a bounded partial Health sample, not the complete issue record.",
            "as_of_date": "2026-05-20",
            "action_ids": [ACTION],
            "source_refs": [PACKAGE + "shared_issue_mapping.json"],
        },
        "action_accounting": [
            {
                "action_id": ACTION,
                "action_date": "2026-05-20",
                "disposition": "interpreted_substantive_directional"
                if status == "Yea"
                else "interpreted_substantive_non_directional",
                "review_friendliness": {
                    "substantive_candidate": True,
                    "stable_canonical_action_identity": True,
                    "service_status": "in_service",
                    "member_action": status,
                    "exact_action_issue_eligibility": "eligible",
                    "action_meaning_evidence": "sufficient",
                    "vote_provenance": "authoritative",
                    "action_meaning_provenance": "authoritative",
                    "source_conflict_state": "none",
                    "is_review_friendly": True,
                },
                "episode_id": EPISODE,
                "episode_membership_state": "established",
                "episode_membership_reason": None,
                "interpretation": interpretation,
            }
        ],
        "episodes": [
            {
                "episode_id": EPISODE,
                "action_ids": [ACTION],
                "chronological_action_ids": [ACTION],
                "latest_action_date": "2026-05-20",
                "policy_question": meaning["candidate_exact_action_meaning"],
                "action_interpretation_refs": [
                    {
                        "action_id": ACTION,
                        "interpretation_id": interpretation["interpretation_id"],
                        "interpretation_sha256": interpretation[
                            "interpretation_sha256"
                        ],
                    }
                ],
                "member_record": [{"action_id": ACTION, "member_action": status}],
                "outcome": "directional_support"
                if status == "Yea"
                else "non_directional",
                "contrary_or_limiting_evidence": [],
                "source_completeness": "complete",
                "source_refs": ["clerk:119:2:180", "govinfo:s2393es"],
                "completion_state": "complete",
                "unresolved_action_ids": [],
            }
        ],
        "synthesis": {
            "outcome": "not_yet_determined",
            "full_record_action_accounting": "not_passed",
            "all_interpreted_episode_outcomes_supplied": True,
            "contradictory_and_mixed_evidence_retained": True,
            "source_boundaries": "resolved",
            "semantic_validation": "passed",
            "human_editorial_review": "not_started",
            "human_approval_receipt_refs": [],
            "full_issue_synthesis_eligible": False,
            "eligibility_blockers": sorted(
                [
                    "review_scope_not_full_defined_issue_record",
                    "review_completion_not_complete",
                    "action_accounting_incomplete",
                    "human_editorial_review_not_approved",
                ]
            ),
        },
        "benchmark": {
            "benchmark_sample_available": False,
            "role": "no_benchmark",
            "benchmark_refs": [],
            "confers_full_record_scope": False,
            "confers_full_record_completion": False,
        },
        "historical_publication": {
            "state": "none",
            "artifact_id": None,
            "effective_semantic_tier": None,
            "publication_receipt_refs": [],
            "historical_truth_note": "This candidate changes no existing publication.",
            "mutated_by_this_record": False,
        },
        "frontend_state": {
            **{
                k: axes[k]
                for k in (
                    "review_scope",
                    "review_completion_state",
                    "public_claim_class",
                )
            },
            "total_recorded_actions": 1,
            "review_friendly_actions": 1,
            "interpreted_actions": 1,
            "unresolved_actions": 0,
            "procedural_context_actions": 0,
            "present_actions": 0,
            "not_voting_actions": int(status == "Not Voting"),
            "complete_episode_count": 1,
            "partial_episode_count": 0,
            "full_issue_synthesis_eligible": False,
            "benchmark_sample_available": False,
            "conclusion_teaser": None,
            "available_labels": ["Vote receipts available"],
        },
        "external_authority": {
            key: None
            for key in (
                "universe_manifest",
                "universe_authority_receipt",
                "semantic_artifact",
                "semantic_validation_receipt",
                "human_approval_receipt",
            )
        },
        "provenance": {
            "contract_path": "docs/methodology/full_record_issue_interpretation_v1.md",
            "schema_path": "docs/methodology/full_record_issue_interpretation_v1.schema.json",
            "created_from_repository_commit": BASE,
            "source_refs": [
                PACKAGE + "governed_sources.json",
                PACKAGE + "membership_evidence.json",
            ],
            "protected_files": [
                {"path": PACKAGE + "DECISION-PACKET.md", "sha256": PACKET_SHA}
            ],
        },
    }
    review["issue_universe"]["snapshot_sha256"] = canonical_digest(
        {
            "action_ids": [ACTION],
            "congress_scope": [119],
            "issue_id": ISSUE,
            "member_id": member_id,
            "review_scope": "bounded_partial_record",
        }
    )
    return review


def build_semantic_subject(foundation: dict, member_id: str) -> dict:
    validate_foundation(foundation)
    return seal(
        {
            "schema_version": "bounded_choice_semantic_subject_v1",
            "artifact_id": f"bounded-choice:{member_id.lower()}:health:s2393:119:v1",
            "member_id": member_id,
            "issue_id": ISSUE,
            "congress": 119,
            "review_scope": "bounded_partial_record",
            "action_ids": [ACTION],
            "episode_ids": [EPISODE],
            "foundation_sha256": FOUNDATION,
            "original_packet_sha256": PACKET_SHA,
            "original_zip_verified": False,
            "member_ir": member_part(foundation, "compiled_ir.json", member_id),
            "presentation_inputs": member_part(
                foundation, "presentation_inputs.json", member_id
            ),
            "accounting_review": build_accounting_review(foundation, member_id),
            "normalized_source_sha256": FOUNDATION["governed_sources.json"],
            "additional_raw_evidence": [
                {
                    "source_id": source_id,
                    "path": RAW_ROOT + name,
                    "raw_sha256": name[:64],
                    "origin_commit": BASE,
                    "role": "additional_preparation_evidence_no_inherited_acceptance",
                }
                for name, source_id in RAW.items()
            ],
            "authorizing": False,
        },
        "semantic_subject_sha256",
    )


@lru_cache(maxsize=1)
def _accounting_validator():
    # Render starts in backend/, where an unrelated scripts namespace can mask
    # the repository script. Load the established validator at its fixed path;
    # do not duplicate its contract or depend on the caller's Python search path.
    spec = importlib.util.spec_from_file_location(
        "_bounded_choice_accounting_validator",
        ROOT / "scripts/validate_full_record_issue_interpretation.py",
    )
    require(
        spec is not None and spec.loader is not None,
        "accounting validator is unavailable",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_review


def validate_semantic_subject(subject: dict, foundation: dict | None = None) -> None:
    require(isinstance(subject, dict), "bounded semantic subject must be an object")
    check_seal(subject, "semantic_subject_sha256")
    _accounting_validator()(subject["accounting_review"], authority_root=ROOT)
    foundation = load_foundation() if foundation is None else foundation
    require(
        canonical_digest(subject)
        == canonical_digest(
            build_semantic_subject(foundation, subject.get("member_id"))
        ),
        "bounded semantic subject differs from exact frozen evidence",
    )


def build_presentation(subject: dict, foundation: dict | None = None) -> dict:
    validate_semantic_subject(subject, foundation)
    inputs = subject["presentation_inputs"]
    status = MEMBERS[subject["member_id"]][2]
    return seal(
        {
            "schema_version": "bounded_choice_presentation_v1",
            "presentation_branch": "bounded_choice_review",
            "artifact_id": subject["artifact_id"] + ":presentation",
            "member_id": subject["member_id"],
            "issue_id": ISSUE,
            "congress": 119,
            "review_scope": "bounded_partial_record",
            "semantic_subject_sha256": subject["semantic_subject_sha256"],
            "display_role": "supporting_notable_choice"
            if status == "Yea"
            else "non_directional_accounting",
            "official_member_action": status,
            "records": inputs["records"],
            "boundaries": inputs["boundaries"],
            "proposition_ids": [
                p["proposition_id"]
                for p in subject["member_ir"]["proposition_graph"]["propositions"]
            ],
            "action_ids": [ACTION],
            "episode_ids": [EPISODE],
            "sources": [
                {
                    "source_id": s["source_id"],
                    "url": s["url"],
                    "governed_bytes_sha256": s["governed_bytes_sha256"],
                }
                for s in (foundation or load_foundation())["governed_sources.json"][
                    "sources"
                ]
            ],
            "receipt": {
                "action_id": ACTION,
                "bill": "S.2393",
                "date": "2026-05-20",
                "question": "On Motion to Suspend the Rules and Pass",
                "chamber": "House",
                "roll_number": 180,
            },
            "authorizing": False,
            "publication_basis": "bounded_choice_review",
        },
        "presentation_subject_sha256",
    )


def validate_presentation(
    presentation: dict, subject: dict, foundation: dict | None = None
) -> None:
    check_seal(presentation, "presentation_subject_sha256")
    require(
        canonical_digest(presentation)
        == canonical_digest(build_presentation(subject, foundation)),
        "bounded presentation differs from exact mapped wording",
    )


def pending_receipt(
    subject: dict,
    presentation: dict,
    rendering_subject_sha256: str | None,
    pair_subject_sha256: str,
) -> dict:
    return seal(
        {
            "schema_version": "bounded_choice_acceptance_receipt_v1",
            "artifact_id": subject["artifact_id"] + ":acceptance",
            "member_id": subject["member_id"],
            "issue_id": ISSUE,
            "review_scope": "bounded_partial_record",
            "semantic_subject_sha256": subject["semantic_subject_sha256"],
            "presentation_subject_sha256": presentation["presentation_subject_sha256"],
            "rendering_subject_sha256": rendering_subject_sha256,
            "pair_subject_sha256": pair_subject_sha256,
            "decision": None,
            "reviewer": None,
            "reviewer_authority": None,
            "decided_at_utc": None,
            "authority_evidence": None,
            "authorizations": NO_OPERATIONAL_AUTHORITY,
        },
        "receipt_subject_sha256",
    )


def rendering_manifest(root: Path = ROOT) -> dict:
    return {
        path: hashlib.sha256(
            (root / path).read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        for path in RENDER_FILES
    }


def validate_rendering(
    rendering: dict, presentation: dict, *, root: Path = ROOT, verify_files: bool = True
) -> None:
    require(isinstance(rendering, dict), "bounded rendering must be an object")
    require(
        set(rendering)
        == {
            "schema_version",
            "member_id",
            "presentation_subject_sha256",
            "runtime_manifest",
            "captures",
            "rendering_subject_sha256",
        },
        "bounded rendering fields differ",
    )
    check_seal(rendering, "rendering_subject_sha256")
    require(
        rendering["schema_version"] == "bounded_choice_rendering_subject_v1"
        and rendering["member_id"] == presentation["member_id"]
        and rendering["presentation_subject_sha256"]
        == presentation["presentation_subject_sha256"],
        "bounded rendering identity differs",
    )
    require(
        rendering["runtime_manifest"] == rendering_manifest(root),
        "bounded rendering runtime is stale",
    )
    captures = rendering["captures"]
    require(
        isinstance(captures, list)
        and len(captures) == 2
        and all(isinstance(c, dict) for c in captures)
        and {c.get("viewport") for c in captures} == {"desktop", "mobile"},
        "both rendered viewports are required",
    )
    for capture in captures:
        require(
            set(capture)
            == {
                "viewport",
                "width",
                "height",
                "path",
                "sha256",
                "visible_text_sha256",
                "presentation_subject_sha256",
                "page_errors",
                "requested_scope",
                "representative_path",
            },
            "bounded capture fields differ",
        )
        require(
            capture["presentation_subject_sha256"]
            == presentation["presentation_subject_sha256"]
            and capture["page_errors"] == [],
            "bounded capture identity or browser errors differ",
        )
        require(
            type(capture["width"]) is int
            and type(capture["height"]) is int
            and capture["requested_scope"]
            == ("119" if capture["viewport"] == "desktop" else "all")
            and capture["representative_path"]
            == f"/?representative={MEMBERS[presentation['member_id']][1]}&issue=HEALTH_SOCIAL&scope={capture['requested_scope']}"
            and (capture["width"], capture["height"])
            == ((1280, 900) if capture["viewport"] == "desktop" else (390, 844)),
            "bounded viewport differs",
        )
        require(
            bool(re.fullmatch(r"[0-9a-f]{64}", capture["sha256"]))
            and bool(re.fullmatch(r"[0-9a-f]{64}", capture["visible_text_sha256"])),
            "bounded capture digest differs",
        )
        expected_path = f"docs/editorial/review_packages/health_bounded_choice_v1/previews/{presentation['member_id'].lower()}-{capture['viewport']}.png"
        require(capture["path"] == expected_path, "bounded capture path differs")
        if verify_files:
            raw = (root / expected_path).read_bytes()
            require(
                hashlib.sha256(raw).hexdigest() == capture["sha256"]
                and raw[:8] == b"\x89PNG\r\n\x1a\n"
                and len(raw) >= 24,
                "bounded capture bytes differ",
            )
            width, height = struct.unpack(">II", raw[16:24])
            require(
                width == capture["width"] and height >= capture["height"],
                "bounded capture dimensions differ",
            )


def validate_receipt(
    receipt: dict,
    *,
    subject: dict,
    presentation: dict,
    rendering: dict,
    require_accepted: bool = True,
    allow_test_authority: bool = False,
) -> None:
    validate_semantic_subject(subject)
    validate_presentation(presentation, subject)
    validate_rendering(rendering, presentation)
    from .bounded_choice_pair import validate_pair_subject

    pair = validate_pair_subject()
    require(
        pair["members"][subject["member_id"]]["rendering_subject_sha256"]
        == rendering["rendering_subject_sha256"],
        "member rendering differs from shared pair",
    )
    check_seal(receipt, "receipt_subject_sha256")
    expected = pending_receipt(
        subject,
        presentation,
        rendering["rendering_subject_sha256"],
        pair["pair_subject_sha256"],
    )
    decisions = {
        "decision",
        "reviewer",
        "reviewer_authority",
        "decided_at_utc",
        "receipt_subject_sha256",
        "authority_evidence",
    }
    require(
        set(receipt) == set(expected)
        and canonical_digest({k: receipt[k] for k in set(expected) - decisions})
        == canonical_digest({k: expected[k] for k in set(expected) - decisions}),
        "bounded receipt identity, scope, source or subject binding differs",
    )
    if receipt["decision"] is None:
        require(
            all(receipt[k] is None for k in decisions - {"receipt_subject_sha256"}),
            "pending bounded receipt contains an owner decision",
        )
        require(not require_accepted, "bounded owner acceptance is pending")
        return
    require(
        receipt["decision"] == "accept_exact_bounded_choice_and_rendering"
        and isinstance(receipt["reviewer"], str)
        and bool(receipt["reviewer"].strip())
        and receipt["reviewer_authority"] == "bounded_choice_review_authority_v1",
        "bounded owner decision is not accepted authority",
    )
    require(
        isinstance(receipt["decided_at_utc"], str),
        "bounded owner decision timestamp is missing",
    )
    try:
        decided = datetime.fromisoformat(
            receipt["decided_at_utc"].replace("Z", "+00:00")
        )
    except ValueError as error:
        raise BoundedChoiceReviewError(
            "bounded owner decision timestamp is invalid"
        ) from error
    require(
        decided.tzinfo is not None
        and decided.utcoffset().total_seconds() == 0
        and decided <= datetime.now(timezone.utc),
        "bounded owner decision timestamp is invalid",
    )
    if (
        allow_test_authority
        and receipt["authority_evidence"] == owner_authority.TEST_EVIDENCE
    ):
        return
    owner_authority.require_trusted_decision(receipt)
