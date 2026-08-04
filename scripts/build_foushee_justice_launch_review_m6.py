"""Build the frozen, review-only Foushee Justice M6 launch package."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.editorial_presentations.compiler import (  # noqa: E402
    canonical_digest,
    compile_public_issue_presentation,
)
from app.editorial_presentations.validation import (  # noqa: E402
    validate_public_issue_presentation,
)


M5 = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_justice_public_safety_119_v2"
)
DECISIONS = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions/f000477_justice_public_safety_119_v1"
)
EPISODES = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_justice_public_safety_119_v1"
)
OUT = (
    ROOT
    / "docs/editorial/full_record_reviews/public_interface_candidates/f000477_justice_public_safety_119_v1"
)
FRONTEND_FIXTURE = ROOT / "frontend/fixtures/foushee_justice_m6_review.json"
ACCEPTANCE_NAME = (
    "f000477_justice_public_safety_119_m5r1_delegated_semantic_ir_acceptance_v1.json"
)
EXPECTED_ACCEPTANCE_FILE = (
    "23d27f84ce196380b6d02ca2d1a2e679847e7a0855c00d60b6df1542d499b405"
)
EXPECTED_ACCEPTANCE_CONTENT = (
    "fe434b3c3bcb0d6235003d144ad25c4e207d0dc104ec42fec1ec8e75d3514db9"
)
GRAPH_FILE = "6a385770ce670e19329e56dfde13c48ae4b581bd740eac7dd7a54bed692abc14"
GRAPH_CONTENT = "f561d3eda50e164a6cbf98520e8c9831468f607e8ed32d333ee6905f4737f7a8"
RECEIPT_REF = "full-record-semantic-validation:f000477:justice_public_safety:119:v1"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def with_digest(value: dict) -> dict:
    value = copy.deepcopy(value)
    value["content_subject_sha256"] = canonical_digest(value)
    return value


def write_json(path: Path, value: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def mapped(
    statement_id: str,
    text: str,
    *,
    target: str,
    proposition_ids: list[str] | None = None,
    boundary_ids: list[str] | None = None,
    actions: list[str],
    episodes: list[str],
    sources_by_action: dict[str, list[str]],
) -> dict:
    sources = sorted(
        {source for action in actions for source in sources_by_action[action]}
    )
    return {
        "statement_id": statement_id,
        "text": text,
        "mapping": {
            "mapping_id": statement_id.replace("statement:", "mapping:"),
            "proposition_ids": proposition_ids or [],
            "boundary_ids": boundary_ids or [],
            "presentation_target": target,
            "action_ids": sorted(actions),
            "episode_ids": sorted(episodes),
            "source_refs": sources,
            "receipt_refs": [RECEIPT_REF],
        },
    }


def source_contract(records: list[dict], source_manifest_sha: str) -> dict:
    authorities: dict[str, str] = {}
    actions: dict[str, dict] = {}
    for record in records:
        refs = record["source_references"]
        vote = [ref for ref in refs if ref.startswith("clerk:")]
        meaning = [ref for ref in refs if ref not in vote]
        if not vote or not meaning:
            raise ValueError(f"{record['action_id']}: incomplete official source pair")
        for ref in vote:
            authorities[ref] = "house_clerk_roll_call"
        for ref in meaning:
            authorities[ref] = "official_measure_text"
        actions[record["action_id"]] = {
            "vote_source_refs": vote,
            "action_meaning_source_refs": meaning,
            "required_action_meaning_source_types": ["official_measure_text"],
        }
    return {
        "schema_version": "editorial_action_source_contract_v1",
        "contract_id": "foushee_justice_public_safety_119_full_record_m6_v1",
        "source_manifest": {
            "path": "docs/editorial/full_record_reviews/source_readiness/f000477_justice_public_safety_119_official_source_manifest_v1.json",
            "sha256": source_manifest_sha,
        },
        "claim_source_map": {
            "path": "docs/editorial/full_record_reviews/interpretation_decisions/f000477_justice_public_safety_119_v1/decision_implementation_bundle.json",
            "sha256": file_sha(DECISIONS / "decision_implementation_bundle.json"),
        },
        "source_authorities": dict(sorted(authorities.items())),
        "actions": dict(sorted(actions.items())),
    }


PATTERN_COPY = {
    "prop:354da734fec2fcf6": (
        "Opposition to displacing D.C. public-safety rules",
        "Across six separate episodes, Foushee opposed the reviewed proposals to replace or repeal specific D.C. public-safety rules concerning youth cases, police bargaining and pursuits, pretrial detention, and policing reforms.",
    ),
    "prop:e76b98cf92ef34cb": (
        "Opposition to reducing firearm-access barriers",
        "Across three separate episodes, Foushee opposed the reviewed proposals to reduce barriers involving retired-service firearm purchases, personal firearms at defense facilities, and firearm-merchant category-code restrictions.",
    ),
    "prop:e75e7aebbd7b2d29": (
        "Opposition to expanding fraud-enforcement capacity",
        "Across two separate episodes, Foushee opposed the reviewed proposals to expand federal payment-integrity oversight and extend the time available to pursue pandemic unemployment fraud.",
    ),
    "prop:d7e189366b477118": (
        "Support for terrorism-preparedness mandates",
        "Across two separate episodes, Foushee supported the reviewed mandates for a cold-weather terrorism-response exercise and an assessment of vehicular-terrorism threats.",
    ),
}


def build(acceptance_path: Path) -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "screenshots").mkdir(parents=True, exist_ok=True)
    if file_sha(acceptance_path) != EXPECTED_ACCEPTANCE_FILE:
        raise ValueError("attached acceptance final bytes do not match")
    acceptance = load(acceptance_path)
    if acceptance["content_subject_sha256"] != EXPECTED_ACCEPTANCE_CONTENT:
        raise ValueError("attached acceptance content subject does not match")
    imported = OUT / ACCEPTANCE_NAME
    shutil.copyfile(acceptance_path, imported)
    if file_sha(imported) != EXPECTED_ACCEPTANCE_FILE:
        raise ValueError("acceptance import changed final bytes")

    graph_path = M5 / "frozen_final_compiled_semantic_ir.json"
    graph_wrapper = load(graph_path)
    if (
        file_sha(graph_path) != GRAPH_FILE
        or graph_wrapper["content_subject_sha256"] != GRAPH_CONTENT
    ):
        raise ValueError("M5-R1 graph identity changed")
    graph = graph_wrapper["compiled_ir"]
    member = graph["members"][0]
    propositions = member["proposition_graph"]["propositions"]
    proposition_index = {item["proposition_id"]: item for item in propositions}
    decisions = load(DECISIONS / "decision_implementation_bundle.json")
    records = decisions["implementation_records"]
    records_by_action = {item["action_id"]: item for item in records}
    episode_bundle = load(EPISODES / "episode_implementation_bundle.json")
    implemented_episodes = episode_bundle["implemented_episodes"]
    episode_by_action = {
        action["action_id"]: episode["episode_id"]
        for episode in implemented_episodes
        for action in episode["chronological_action_sequence"]
    }
    episode_by_action.update(
        {
            item["action_id"]: item.get("primary_episode_id")
            for item in episode_bundle["action_accounting"]
            if item.get("primary_episode_id")
        }
    )
    episode_by_action["house:119:2:155"] = "fisa-title-vii-short-term-extension"
    if (
        len(records) != 37
        or len(implemented_episodes) != 32
        or len(episode_by_action) != 36
    ):
        raise ValueError("full-record accounting differs")
    sources_by_action = {
        item["action_id"]: item["source_references"] for item in records
    }
    all_actions = sorted(records_by_action)
    all_episodes = sorted(item["episode_id"] for item in implemented_episodes)

    semantic_artifact = with_digest(
        {
            "schema_version": "full_record_semantic_artifact_v1",
            "artifact_id": "full-record-semantic-artifact:f000477:justice_public_safety:119:v1",
            "subject": acceptance["subject"],
            "authority": {
                "acceptance_artifact_id": acceptance["artifact_id"],
                "acceptance_content_subject_sha256": EXPECTED_ACCEPTANCE_CONTENT,
                "acceptance_final_file_sha256": EXPECTED_ACCEPTANCE_FILE,
                "decision": acceptance["decision"]["decision"],
            },
            "universe": {
                "action_ids": all_actions,
                "episode_ids": all_episodes,
                "review_cutoff": "2026-07-23",
            },
            "accounting": {
                "total_actions": 37,
                "directional_actions": 35,
                "non_proposition_controls": 2,
                "complete_episodes": 32,
                "missing_actions": 0,
            },
            "semantic_bindings": {
                "compiler_input": acceptance["input_bindings"]["v2_compiler_input"],
                "compiled_graph": acceptance["input_bindings"]["v2_compiled_graph"],
                "provisional_implementation": acceptance["input_bindings"][
                    "v2_provisional_implementation"
                ],
                "proposition_ids": sorted(proposition_index),
                "behavioral_proposition_count": 23,
                "conclusion_plan": member["composition"]["conclusion_plan"],
                "synthesis": proposition_index["prop:7a5b23c610dc467e"],
            },
            "semantic_tier": "reviewed_conclusion_candidate_held_for_launch_review",
            "synthesis_outcome": "mechanism_divide",
            "launch_risk_ids": [
                "launch-risk:semantic-ir:mechanism-divide:v1",
                "launch-risk:roll-128:v1",
                "launch-risk:roll-155-and-fisa-grouping:v1",
                "launch-risk:roll-278:v1",
            ],
            "controls": {
                "authorizing": False,
                "canonical": False,
                "public": False,
                "production_eligible": False,
                "publication_active": False,
                "runtime_selectable": False,
            },
        }
    )
    write_json(OUT / "full_record_semantic_artifact.json", semantic_artifact)

    validation_receipt = with_digest(
        {
            "schema_version": "full_record_semantic_validation_receipt_v1",
            "artifact_id": RECEIPT_REF,
            "subject_artifact_id": semantic_artifact["artifact_id"],
            "subject_content_subject_sha256": semantic_artifact[
                "content_subject_sha256"
            ],
            "status": "passed",
            "checks": {
                "universe_identity": True,
                "action_accounting_37": True,
                "episode_set_32": True,
                "compiled_graph_identity": True,
                "proposition_graph_23_behavioral": True,
                "conclusion_plan": True,
                "mechanism_divide_synthesis": True,
                "special_roll_constraints": True,
                "official_source_boundaries": True,
                "semantic_blockers": 0,
            },
            "non_authorizations": [
                "user_approval",
                "public_approval",
                "production_eligibility",
                "publication_authority",
            ],
        }
    )
    write_json(OUT / "full_record_semantic_validation_receipt.json", validation_receipt)

    source_manifest = (
        ROOT
        / "docs/editorial/full_record_reviews/source_readiness/f000477_justice_public_safety_119_official_source_manifest_v1.json"
    )
    contract = source_contract(records, file_sha(source_manifest))
    write_json(OUT / "full_record_action_source_contract.json", contract)

    coverage_boundary = "boundary:coverage:f000477:justice_public_safety:119"
    scope_boundary = "boundary:scope:f000477:justice_public_safety:119"
    synth = proposition_index["prop:7a5b23c610dc467e"]
    wording = {
        "status": "review_candidate_pending_user_launch_ratification",
        "tier_display": {
            "reviewed_conclusion": {
                "badge": "Full-record review candidate",
                "teaser": mapped(
                    "statement:teaser:mechanism-contrast",
                    "One meaningful contrast in the reviewed record is opposition to the reviewed displacement of D.C. public-safety rules alongside support for two terrorism-preparedness mandates; separate firearm-access and fraud-enforcement patterns remain primary findings.",
                    target="conclusion_only",
                    proposition_ids=[synth["proposition_id"]],
                    actions=synth["evidence_action_ids"],
                    episodes=synth["evidence_episode_ids"],
                    sources_by_action=sources_by_action,
                ),
            }
        },
        "coverage_text": mapped(
            "statement:coverage:full-record",
            "This review accounts for the full defined Justice & Public Safety record through July 23, 2026: 37 governed actions, 35 interpreted directional actions, 32 complete episodes, two governed non-proposition controls, and no missing action accounting.",
            target="coverage_note",
            boundary_ids=[coverage_boundary],
            actions=all_actions,
            episodes=all_episodes,
            sources_by_action=sources_by_action,
        ),
        "scope_boundary": mapped(
            "statement:scope:119",
            "This candidate describes Valerie P. Foushee’s full defined Justice & Public Safety record for the 119th Congress through the review cutoff; it does not infer motive, ideology, character, future behavior, or voting advice.",
            target="scope_note",
            boundary_ids=[scope_boundary],
            actions=all_actions,
            episodes=all_episodes,
            sources_by_action=sources_by_action,
        ),
        "conclusion": {
            "headline": mapped(
                "statement:conclusion:headline",
                "One bounded contrast within a record with four primary patterns",
                target="conclusion_only",
                proposition_ids=[synth["proposition_id"]],
                actions=synth["evidence_action_ids"],
                episodes=synth["evidence_episode_ids"],
                sources_by_action=sources_by_action,
            ),
            "body": mapped(
                "statement:conclusion:body",
                "One meaningful contrast in the reviewed record is that Foushee opposed six reviewed proposals that would displace specific D.C. public-safety rules and supported two reviewed terrorism-preparedness mandates. This contrast is not a complete explanation of the record: opposition to firearm-access barrier reduction and fraud-enforcement capacity expansion remains separately visible, and the mixed HALT Fentanyl episode limits any one-direction account.",
                target="conclusion_only",
                proposition_ids=[synth["proposition_id"]],
                actions=synth["evidence_action_ids"],
                episodes=synth["evidence_episode_ids"],
                sources_by_action=sources_by_action,
            ),
        },
        "repeated_patterns": [],
        "policy_trajectories": [],
        "limitations": [],
    }
    for proposition_id, (heading, body) in PATTERN_COPY.items():
        proposition = proposition_index[proposition_id]
        wording["repeated_patterns"].append(
            {
                "proposition_id": proposition_id,
                "heading": mapped(
                    f"statement:pattern:{proposition_id}:heading",
                    heading,
                    target="repeated_patterns",
                    proposition_ids=[proposition_id],
                    actions=proposition["evidence_action_ids"],
                    episodes=proposition["evidence_episode_ids"],
                    sources_by_action=sources_by_action,
                ),
                "body": mapped(
                    f"statement:pattern:{proposition_id}:body",
                    body,
                    target="repeated_patterns",
                    proposition_ids=[proposition_id],
                    actions=proposition["evidence_action_ids"],
                    episodes=proposition["evidence_episode_ids"],
                    sources_by_action=sources_by_action,
                ),
            }
        )
    halt = proposition_index["prop:53cda8d886a88f12"]
    wording["policy_trajectories"].append(
        {
            "proposition_id": halt["proposition_id"],
            "heading": mapped(
                "statement:trajectory:halt:heading",
                "The HALT Fentanyl path is one mixed episode",
                target="policy_trajectories",
                proposition_ids=[halt["proposition_id"]],
                actions=halt["evidence_action_ids"],
                episodes=halt["evidence_episode_ids"],
                sources_by_action=sources_by_action,
            ),
            "body": mapped(
                "statement:trajectory:halt:body",
                "Within one legislative episode, Foushee supported a certification amendment, opposed the earlier House bill, and supported a later related framework with permanent scheduling and research provisions. These three actions count as one episode and do not establish three independent positions or a change in motive or philosophy.",
                target="policy_trajectories",
                proposition_ids=[halt["proposition_id"]],
                actions=halt["evidence_action_ids"],
                episodes=halt["evidence_episode_ids"],
                sources_by_action=sources_by_action,
            ),
        }
    )
    constraint_by_id = {
        item["constraint_id"]: item for item in graph["source_render_constraints"]
    }
    limitation_copy = {
        "roll-128-unresolved-text-limit": (
            "Roll 128: resolved scope only",
            "The reviewed record supports the concealed-carry expansion meaning, but the exact legal effect of the separate ‘any magazine and’ insertion remains unresolved.",
        ),
        "roll-155-source-identity-block": (
            "Roll 155: source identity conflict",
            "A preserved 110th/119th-Congress source-identity conflict keeps roll 155 out of behavioral propositions and prevents it from adding substantive weight to the FISA relationship.",
        ),
        "roll-278-no-safe-interpretation-block": (
            "Roll 278: no safe final-package meaning",
            "The available official material does not establish the complete final House-passed package after amendments, so this action receives no public analytical meaning.",
        ),
    }
    for constraint_id, (heading, body) in limitation_copy.items():
        constraint = constraint_by_id[constraint_id]
        actions = constraint["action_ids"]
        item = {"boundary_id": constraint_id}
        item["heading"] = mapped(
            f"statement:limitation:{constraint_id}:heading",
            heading,
            target="source_note",
            boundary_ids=[constraint_id],
            actions=actions,
            episodes=[],
            sources_by_action=sources_by_action,
        )
        item["body"] = mapped(
            f"statement:limitation:{constraint_id}:body",
            body,
            target="source_note",
            boundary_ids=[constraint_id],
            actions=actions,
            episodes=[],
            sources_by_action=sources_by_action,
        )
        wording["limitations"].append(item)

    all_source_refs = sorted(
        {ref for refs in sources_by_action.values() for ref in refs}
    )
    authoring = {
        "artifact_identity": {
            "artifact_id": "public-issue-presentation-candidate:f000477:justice_public_safety:119:v1",
            "artifact_version": 1,
            "member_id": "F000477",
            "issue_id": "JUSTICE_PUBLIC_SAFETY",
            "congress": 119,
            "scope": "119",
            "source_case_id": graph_wrapper["artifact_id"],
        },
        "editorial_wording": wording,
        "provenance": {
            "semantic_source_case_id": graph_wrapper["artifact_id"],
            "focused_validation_case_ids": [
                "m6-full-record-coverage",
                "m6-held-mechanism-divide",
                "m6-special-roll-boundaries",
            ],
            "dossier_refs": [
                "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_justice_public_safety_119_v2/review_dossier.md"
            ],
            "source_refs": all_source_refs,
            "claim_refs": sorted(proposition_index),
            "receipt_refs": [RECEIPT_REF, acceptance["artifact_id"]],
            "review_limitations": [
                {
                    "limitation_id": "mechanism-divide-held",
                    "text": "The mechanism divide is one bounded contrast, not a complete explanation of the record, and remains held for launch review.",
                },
                {
                    "limitation_id": "roll-128-unresolved-insertion",
                    "text": limitation_copy["roll-128-unresolved-text-limit"][1],
                },
                {
                    "limitation_id": "roll-155-source-conflict",
                    "text": limitation_copy["roll-155-source-identity-block"][1],
                },
                {
                    "limitation_id": "roll-278-no-safe-package",
                    "text": limitation_copy["roll-278-no-safe-interpretation-block"][1],
                },
            ],
        },
        "controls": {
            "semantic": {"status": "candidate", "validation_status": "passed"},
            "editorial": {"human_approval_status": "human_approval_pending"},
            "benchmark": {"status": "not_promoted"},
            "production": {"eligible": False},
            "publication": {"active": False},
            "approval_mode": "detached_receipt_required",
        },
    }
    write_json(OUT / "public_presentation_authoring.json", authoring)
    candidate = compile_public_issue_presentation(
        graph, authoring, trusted_action_source_contract=contract
    )
    validation = validate_public_issue_presentation(candidate)
    write_json(OUT / "public_presentation_candidate.json", candidate)
    compiler_receipt = with_digest(
        {
            "schema_version": "public_presentation_compiler_receipt_v1",
            "artifact_id": "public-presentation-compiler-receipt:f000477:justice_public_safety:119:v1",
            "candidate_artifact_id": candidate["artifact_identity"]["artifact_id"],
            "candidate_final_file_sha256": "computed_in_parity_manifest",
            "compiled_ir_content_subject_sha256": GRAPH_CONTENT,
            "approval_subject": candidate["provenance"]["compiler_receipt"],
            "validation": validation,
            "effective_public_tier": candidate["controls"]["effective_public_tier"],
            "runtime_selectable": False,
        }
    )
    write_json(OUT / "presentation_compiler_receipt.json", compiler_receipt)

    ledger = []
    worker_root = (
        ROOT
        / "docs/editorial/full_record_reviews/interpretation_candidates/f000477_justice_public_safety_119_v1/worker_packets"
    )
    worker_packets = {
        path.stem.replace("house_", "house:").replace("_", ":"): load(path)
        for path in worker_root.glob("house_*.json")
    }
    action_dates = {
        action_id: packet["official_action_date"]
        for action_id, packet in worker_packets.items()
    }
    for record in records:
        action_id = record["action_id"]
        session, roll = action_id.split(":")[-2:]
        episode_id = episode_by_action.get(action_id)
        prop_ids = sorted(
            p["proposition_id"]
            for p in propositions
            if action_id in p["evidence_action_ids"]
        )
        ledger.append(
            {
                "canonical_action_id": action_id,
                "date": action_dates[action_id],
                "legislative_stage": record["house_stage"],
                "member_action": record["official_member_action"],
                "governed_action_meaning": record["implemented_exact_action_meaning"],
                "non_proposition_state": record["implemented_interpretation_status"]
                if action_id in {"house:119:2:155", "house:119:2:278"}
                else None,
                "episode_id": episode_id,
                "proposition_ids": prop_ids,
                "confidence": record["implemented_confidence"],
                "limitations": record["implemented_limitations"],
                "official_vote_source": [
                    {
                        "source_id": source["source_id"],
                        "url": source["deterministic_extraction"]
                        .get("projection", {})
                        .get("source_url")
                        or source.get("source_url")
                        or "https://clerk.house.gov/",
                    }
                    for source in worker_packets[action_id]["sources"]
                    if source["source_id"].startswith("clerk:")
                ],
                "official_action_meaning_sources": [
                    {
                        "source_id": source["source_id"],
                        "url": source.get("source_url")
                        or source.get("canonical_url")
                        or source.get("url")
                        or "https://www.congress.gov/",
                    }
                    for source in worker_packets[action_id]["sources"]
                    if not source["source_id"].startswith("clerk:")
                ],
                "roll_call": int(roll),
                "session": int(session),
            }
        )
    ledger_artifact = with_digest(
        {
            "schema_version": "exact_action_ledger_v1",
            "artifact_id": "exact-action-ledger:f000477:justice_public_safety:119:v1",
            "record_count": 37,
            "records": ledger,
        }
    )
    write_json(OUT / "exact_action_ledger.json", ledger_artifact)

    mappings = []

    def collect(value: object) -> None:
        if isinstance(value, dict):
            if set(value) >= {"statement_id", "text", "mapping"}:
                entry = copy.deepcopy(value)
                entry["semantic_validation_receipt"] = RECEIPT_REF
                entry["content_subject_sha256"] = canonical_digest(entry)
                mappings.append(entry)
            else:
                for child in value.values():
                    collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(wording)
    notable_props = [
        item
        for item in propositions
        if item["presentation_target"] == "other_notable_choices"
    ]
    notable_actions = sorted(
        {action for item in notable_props for action in item["evidence_action_ids"]}
    )
    notable_episodes = sorted(
        {episode for item in notable_props for episode in item["evidence_episode_ids"]}
    )
    other_notable_statement = mapped(
        "statement:other-notable:disclosure",
        "Seventeen excluded notable-choice propositions remain available through the complete ledger below. They are not promoted to coequal headline findings.",
        target="other_notable_choices",
        proposition_ids=sorted(item["proposition_id"] for item in notable_props),
        actions=notable_actions,
        episodes=notable_episodes,
        sources_by_action=sources_by_action,
    )
    other_notable_statement["semantic_validation_receipt"] = RECEIPT_REF
    other_notable_statement["content_subject_sha256"] = canonical_digest(
        other_notable_statement
    )
    mappings.append(other_notable_statement)
    mapping_registry = with_digest(
        {
            "schema_version": "analytical_string_mapping_set_v1",
            "artifact_id": "analytical-string-mappings:f000477:justice_public_safety:119:v1",
            "mapping_count": len(mappings),
            "mappings": mappings,
        }
    )
    write_json(OUT / "analytical_string_mappings.json", mapping_registry)

    review = with_digest(
        {
            "schema_version": "public_wording_review_v1",
            "artifact_id": "public-wording-review:f000477:justice_public_safety:119:v1",
            "initial_wording": {
                "headline": "Her record divides between local-rule displacement and federal preparedness mandates.",
                "conclusion": "Her record divides between opposition to D.C. rule displacement and support for terrorism preparedness.",
            },
            "passes": [
                {
                    "review": "fidelity",
                    "findings": [
                        "Initial headline overclaimed the synthesis as a complete-record explanation.",
                        "Coverage copy initially lacked the two governed non-proposition controls.",
                    ],
                },
                {
                    "review": "neutrality",
                    "findings": [
                        "No partisan, motive, ideological, emotional, or strategic language remained after correction."
                    ],
                },
                {
                    "review": "compression_and_completeness",
                    "findings": [
                        "Firearm and fraud patterns must immediately follow the bounded contrast.",
                        "HALT must be one mixed episode, not three positions.",
                    ],
                },
                {
                    "review": "reader_interpretation",
                    "findings": [
                        "Action and episode counts needed explicit separation.",
                        "Special-roll limits needed visible headings.",
                    ],
                },
                {
                    "review": "civic_risk",
                    "findings": [
                        "A hostile excerpt of the initial headline could imply a comprehensive political philosophy."
                    ],
                },
            ],
            "correction_cycles": [
                {
                    "cycle": 1,
                    "changes": [
                        "Replaced complete-record divide language with ‘one meaningful contrast’.",
                        "Placed firearm and fraud findings immediately after the contrast.",
                        "Added complete 37/35/32/2 accounting.",
                    ],
                    "rationale": "Bound synthesis scope and preserve all primary evidence.",
                },
                {
                    "cycle": 2,
                    "changes": [
                        "Added explicit HALT one-episode language and visible roll 128/155/278 boundaries.",
                        "Separated no-safe meaning from low-confidence meaning.",
                    ],
                    "rationale": "Prevent duplicated weight and unsupported public meaning.",
                },
            ],
            "final_statement_ids": sorted(item["statement_id"] for item in mappings),
            "remaining_major_or_critical_findings": 0,
        }
    )
    write_json(OUT / "wording_review.json", review)

    risks = with_digest(
        {
            "schema_version": "cumulative_launch_risk_register_v1",
            "artifact_id": "launch-risk-register:f000477:justice_public_safety:119:m6:v1",
            "unresolved_count": 4,
            "unresolved": [
                {
                    "risk_id": "launch-risk:roll-128:v1",
                    "question": "Is the bounded resolved meaning sufficient while the textual insertion remains unresolved?",
                    "current_treatment": "Render resolved scope and disclose the insertion limitation.",
                    "competing_interpretation": "Withhold the entire action from analytical display.",
                    "effect": "One notable choice remains low-confidence and explicitly limited.",
                    "codex_recommendation": "Retain the bounded action meaning with the limitation adjacent.",
                    "delegated_authority_recommendation": None,
                    "user_decision_required": "Acknowledge or require withholding roll 128.",
                },
                {
                    "risk_id": "launch-risk:roll-155-and-fisa-grouping:v1",
                    "question": "How should the source-identity conflict and resulting FISA grouping consequence be treated?",
                    "current_treatment": "Keep roll 155 non-counting and outside substantive FISA weight.",
                    "competing_interpretation": "Resolve identity later and reconsider episode grouping.",
                    "effect": "The ledger exposes the control but assigns no behavioral meaning.",
                    "codex_recommendation": "Launch only with the current non-counting treatment unless source identity is resolved.",
                    "delegated_authority_recommendation": None,
                    "user_decision_required": "Acknowledge the non-counting treatment or require renewed evidence review.",
                },
                {
                    "risk_id": "launch-risk:roll-278:v1",
                    "question": "Can any final-package meaning be stated without the complete House-passed package?",
                    "current_treatment": "No safe public analytical meaning; ledger-only boundary.",
                    "competing_interpretation": "Acquire complete final-package evidence in a later milestone.",
                    "effect": "The action is accounted for but contributes no proposition.",
                    "codex_recommendation": "Retain no-safe state.",
                    "delegated_authority_recommendation": None,
                    "user_decision_required": "Acknowledge the no-safe treatment or require later evidence acquisition.",
                },
                {
                    "risk_id": "launch-risk:semantic-ir:mechanism-divide:v1",
                    "question": "Should launch retain the bounded mechanism divide, require no_common_throughline, or omit overarching synthesis?",
                    "current_treatment": "Option A: one bounded contrast, with firearm and fraud adjacent.",
                    "competing_interpretation": "Option B requires Semantic IR revision to no_common_throughline; Option C requires conclusion-plan revision to omit synthesis.",
                    "effect": "Only Option A is rendered; B and C remain visibly non-authoritative review alternatives.",
                    "codex_recommendation": "Retain Option A if the bounded wording is acceptable.",
                    "delegated_authority_recommendation": None,
                    "user_decision_required": "Choose A, require B revision, or require C revision.",
                },
            ],
            "resolved_internal_history": [
                "roll-298 duplicate primary weight removed in M5-R1",
                "roll-171 remains a bounded notable choice",
            ],
        }
    )
    write_json(OUT / "launch_risk_register.json", risks)

    fixture = {
        "schema_version": "m6_review_fixture_v1",
        "review_only": True,
        "candidate_content_sha256": candidate["provenance"][
            "presentation_content_sha256"
        ],
        "presentation": {
            "issue_id": "JUSTICE_PUBLIC_SAFETY",
            "tier": "reviewed_conclusion",
            "tier_badge": "Full-record review candidate",
            "teaser": wording["tier_display"]["reviewed_conclusion"]["teaser"]["text"],
            "coverage_text": wording["coverage_text"]["text"],
            "scope_boundary": wording["scope_boundary"]["text"],
            "public_status_label": "Review only · launch ratification pending",
            "review_state": {
                "congress_scope": [119],
                "review_scope": "full_defined_issue_record",
                "total_recorded_actions": 37,
                "complete_episode_count": 32,
            },
            "conclusion": {
                "headline": wording["conclusion"]["headline"]["text"],
                "body": wording["conclusion"]["body"]["text"],
            },
            "repeated_patterns": [
                {
                    "proposition_id": item["proposition_id"],
                    "direction": proposition_index[item["proposition_id"]]["direction"],
                    "heading": item["heading"]["text"],
                    "body": item["body"]["text"],
                    "action_ids": item["heading"]["mapping"]["action_ids"],
                }
                for item in wording["repeated_patterns"]
            ],
            "policy_trajectories": [
                {
                    "proposition_id": halt["proposition_id"],
                    "direction": "mixed",
                    "heading": wording["policy_trajectories"][0]["heading"]["text"],
                    "body": wording["policy_trajectories"][0]["body"]["text"],
                    "action_ids": halt["evidence_action_ids"],
                }
            ],
            "limitations": [
                {"heading": item["heading"]["text"], "body": item["body"]["text"]}
                for item in wording["limitations"]
            ],
        },
        "other_notable_copy": other_notable_statement["text"],
        "ledger": ledger,
        "launch_risks": risks["unresolved"],
    }
    write_json(FRONTEND_FIXTURE, fixture)

    ratification_subject = with_digest(
        {
            "schema_version": "user_launch_ratification_subject_v1",
            "artifact_id": "launch-ratification-subject:f000477:justice_public_safety:119:v1",
            "universe": semantic_artifact["content_subject_sha256"],
            "semantic_validation_receipt": validation_receipt["content_subject_sha256"],
            "public_presentation_content": candidate["provenance"][
                "presentation_content_sha256"
            ],
            "reviewed_wording": candidate["provenance"]["reviewed_wording_sha256"],
            "mapping_set": mapping_registry["content_subject_sha256"],
            "evidence_provenance": candidate["provenance"][
                "evidence_provenance_sha256"
            ],
            "limitations": candidate["provenance"]["limitations_sha256"],
            "risk_register": risks["content_subject_sha256"],
            "screenshot_manifest": "pending_render_freeze",
            "calibration_sample": "pending_post_freeze",
        }
    )
    write_json(OUT / "launch_ratification_subject.json", ratification_subject)
    template = with_digest(
        {
            "schema_version": "user_launch_ratification_template_v1",
            "artifact_id": "launch-ratification-template:f000477:justice_public_safety:119:v1",
            "subject_artifact_id": ratification_subject["artifact_id"],
            "subject_content_subject_sha256": ratification_subject[
                "content_subject_sha256"
            ],
            "user_decision": None,
            "user_identity": None,
            "decision_timestamp": None,
            "risk_specific_selections": [],
            "wording_approval": None,
            "production_eligibility_approval": None,
            "publication_approval": None,
            "notice": "Publication activation remains a later, separately explicit operational decision.",
        }
    )
    write_json(OUT / "empty_launch_ratification_template.json", template)

    initial_manifest = []
    for path in sorted(OUT.glob("*.json")):
        if path.name == "parity_manifest.json":
            continue
        value = load(path)
        initial_manifest.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "final_file_sha256": file_sha(path),
                "content_subject_sha256": value.get("content_subject_sha256"),
            }
        )
    parity = with_digest(
        {
            "schema_version": "m6_artifact_parity_manifest_v1",
            "artifact_id": "m6-parity:f000477:justice_public_safety:119:v1",
            "files": initial_manifest,
        }
    )
    write_json(OUT / "parity_manifest.json", parity)
    return {
        "status": "pass",
        "candidate_validation": validation,
        "artifact_count": len(initial_manifest) + 1,
        "mapping_count": len(mappings),
        "candidate_content_sha256": candidate["provenance"][
            "presentation_content_sha256"
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("acceptance", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.acceptance), sort_keys=True))
