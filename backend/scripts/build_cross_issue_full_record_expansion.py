from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
STARTING_COMMIT = "f16bc73fb4e60d34fe75b17e58cb4f224e5b7fcd"
MILESTONE = "m11a_cross_issue_full_record_expansion_v1"
EXCLUDED_DOMAINS = {"JUSTICE_PUBLIC_SAFETY", "ECONOMY_TAXES"}
DOMAIN_IDS = (
    "EDUCATION_WORKFORCE",
    "ENVIRONMENT_ENERGY",
    "HEALTH_SOCIAL",
    "IMMIGRATION_BORDER",
    "INFRASTRUCTURE_TECH_TRANSPORT",
    "NATIONAL_SECURITY_FOREIGN",
)
DISPLAY_NAMES = {
    "EDUCATION_WORKFORCE": "Education & Workforce",
    "ENVIRONMENT_ENERGY": "Environment & Energy",
    "HEALTH_SOCIAL": "Health & Social Policy",
    "IMMIGRATION_BORDER": "Immigration & Border",
    "INFRASTRUCTURE_TECH_TRANSPORT": "Infrastructure, Technology & Transportation",
    "NATIONAL_SECURITY_FOREIGN": "National Security & Foreign Policy",
}

# These are the current classifier's shared, member-neutral signals. Selection
# uses any hit for high recall; hits never establish membership by themselves.
DOMAIN_SIGNALS = {
    "EDUCATION_WORKFORCE": (
        "education",
        "school",
        "student",
        "teacher",
        "college",
        "workforce",
        "apprenticeship",
        "labor",
    ),
    "ENVIRONMENT_ENERGY": (
        "energy",
        "environment",
        "climate",
        "emission",
        "pipeline",
        "drilling",
        "wildfire",
        "public lands",
        "natural resources",
        "conservation",
    ),
    "HEALTH_SOCIAL": (
        "health",
        "medicaid",
        "medicare",
        "hospital",
        "prescription",
        "social welfare",
        "social services",
        "child care",
        "families",
    ),
    "IMMIGRATION_BORDER": (
        "immigration",
        "border",
        "asylum",
        "visa",
        "migrant",
        "deportation",
        "customs",
    ),
    "INFRASTRUCTURE_TECH_TRANSPORT": (
        "transportation",
        "infrastructure",
        "technology",
        "broadband",
        "cyber",
        "bridge",
        "rail",
        "airport",
        "highway",
        "transit",
    ),
    "NATIONAL_SECURITY_FOREIGN": (
        "armed forces",
        "national security",
        "international affairs",
        "defense",
        "military",
        "missile",
        "alliance",
        "ukraine",
        "foreign aid",
        "navy",
        "terrorism",
        "war powers",
        "hostilities",
    ),
}

PROCEDURAL_QUESTIONS = re.compile(
    r"(?i)\b(ordering the previous question|motion to recommit|motion to commit|"
    r"motion to table|motion to refer|motion to discharge|motion to reconsider|"
    r"motion to instruct conferees)\b"
)
EXPRESSIVE_PREFIX = re.compile(
    r"(?i)^(expressing|reaffirming|recognizing|supporting|condemning|denouncing|"
    r"honoring|commemorating|celebrating)\b"
)
RULE_PREFIX = re.compile(r"(?i)^providing for (consideration|disposition)\b")
AMENDMENT_ROLL = re.compile(r"(?i)\broll no\.\s*(\d+)\b")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def action_sort_key(action_id: str) -> tuple[int, int]:
    _, _, session, roll = action_id.split(":")
    return int(session), int(roll)


def sorted_action_ids(values: Iterable[str]) -> list[str]:
    return sorted(set(values), key=action_sort_key)


def _text(value: Any) -> str:
    return str(value or "").strip()


def domain_hits(*values: Any) -> list[str]:
    haystack = " ".join(_text(value) for value in values).lower()
    return [
        domain_id
        for domain_id in DOMAIN_IDS
        if any(signal in haystack for signal in DOMAIN_SIGNALS[domain_id])
    ]


def load_production_snapshot(
    path: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["results"]["complete_member_actions"]
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        action_id = str(row["canonical_action_id"])
        if action_id in by_id:
            raise ValueError(f"duplicate production action: {action_id}")
        by_id[action_id] = row
    proof = payload["read_only_session_proof"]
    if proof.get("transaction_read_only") != "on":
        raise ValueError("production snapshot is not proven read-only")
    return by_id, payload


def _bill_ref(congress: int, value: str) -> str | None:
    normalized = re.sub(r"[^A-Z0-9]+", " ", value.upper()).strip()
    prefixes = (
        ("H CON RES ", "hconres"),
        ("H J RES ", "hjres"),
        ("H RES ", "hres"),
        ("H R ", "hr"),
        ("S CON RES ", "sconres"),
        ("S J RES ", "sjres"),
        ("S RES ", "sres"),
        ("S ", "s"),
    )
    for prefix, bill_type in prefixes:
        if normalized.startswith(prefix):
            return f"bill_{congress}_{bill_type}_{int(normalized.split()[-1])}"
    return None


def load_clerk_actions(
    source_dirs: list[Path], bioguide_id: str
) -> list[dict[str, Any]]:
    from xml.etree import ElementTree

    actions: list[dict[str, Any]] = []
    for source_dir in source_dirs:
        for path in sorted(source_dir.glob("roll*.xml")):
            root = ElementTree.parse(path).getroot()
            metadata = root.find("vote-metadata")
            if metadata is None:
                raise ValueError(f"missing vote metadata: {path}")
            vote = None
            for recorded_vote in root.findall("./vote-data/recorded-vote"):
                legislator = recorded_vote.find("legislator")
                identity = (
                    None
                    if legislator is None
                    else (
                        legislator.attrib.get("bioguide-id")
                        or legislator.attrib.get("name-id")
                    )
                )
                if identity == bioguide_id:
                    vote = _text(recorded_vote.findtext("vote"))
                    break
            if not vote:
                raise ValueError(f"{bioguide_id} missing from {path.name}")
            congress = int(_text(metadata.findtext("congress")))
            session = int(re.sub(r"\D", "", _text(metadata.findtext("session"))))
            roll = int(_text(metadata.findtext("rollcall-num")))
            bill_ref = _bill_ref(congress, _text(metadata.findtext("legis-num")))
            if not bill_ref:
                continue
            member_action = {
                "yea": "yea",
                "aye": "yea",
                "nay": "nay",
                "no": "nay",
                "present": "present",
                "not voting": "not_voting",
            }[vote.lower()]
            action_id = f"house:{congress}:{session}:{roll}"
            actions.append(
                {
                    "action_id": action_id,
                    "session": session,
                    "roll": roll,
                    "date": _text(metadata.findtext("action-date")),
                    "bill_ref": bill_ref,
                    "question": _text(metadata.findtext("vote-question")),
                    "description": _text(
                        metadata.findtext("vote-desc")
                        or metadata.findtext("amendment-author")
                    ),
                    "member_action": member_action,
                    "vote_source": {
                        "source_id": f"clerk:{congress}:{session}:{roll}",
                        "source_type": "house_clerk_roll_call_xml",
                        "url": f"https://clerk.house.gov/evs/{2024 + session}/roll{roll:03d}.xml",
                        "sha256": sha256_file(path),
                    },
                }
            )
    by_id = {row["action_id"]: row for row in actions}
    if len(by_id) != len(actions):
        raise ValueError("duplicate official Clerk action identity")
    return sorted(actions, key=lambda row: action_sort_key(row["action_id"]))


def load_congress_metadata(source_dir: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(source_dir.glob("119_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        bill = payload.get("bill", payload)
        bill_type = _text(bill.get("type") or bill.get("billType")).lower()
        bill_number = int(bill.get("number") or bill.get("billNumber"))
        bill_ref = f"bill_{int(bill['congress'])}_{bill_type}_{bill_number}"
        records[bill_ref] = {
            "bill_ref": bill_ref,
            "title": _text(bill.get("title")),
            "policy_area": _text((bill.get("policyArea") or {}).get("name")),
            "url": _text(bill.get("legislationUrl"))
            or (
                f"https://www.congress.gov/bill/119th-congress/{bill_type}/{bill_number}"
            ),
            "sha256": sha256_file(path),
            "text_version_count": int(
                (bill.get("textVersions") or {}).get("count") or 0
            ),
            "amendment_count": int((bill.get("amendments") or {}).get("count") or 0),
        }
    return records


def load_amendment_indexes(source_dir: Path) -> dict[tuple[str, int], dict[str, Any]]:
    by_roll: dict[tuple[str, int], dict[str, Any]] = {}
    for path in sorted(source_dir.glob("119_*.json")):
        stem = path.stem.split("_")
        if len(stem) != 3:
            continue
        bill_ref = f"bill_{stem[0]}_{stem[1]}_{stem[2]}"
        payload = json.loads(path.read_text(encoding="utf-8"))
        file_sha = sha256_file(path)
        for amendment in payload.get("amendments", []):
            latest_text = _text((amendment.get("latestAction") or {}).get("text"))
            match = AMENDMENT_ROLL.search(latest_text)
            if not match:
                continue
            roll = int(match.group(1))
            key = (bill_ref, roll)
            if key in by_roll:
                raise ValueError(f"duplicate amendment roll binding: {key}")
            by_roll[key] = {
                "identity": f"119:{_text(amendment.get('type')).lower()}:{amendment['number']}",
                "description": _text(amendment.get("description")),
                "purpose": _text(amendment.get("purpose")),
                "latest_action": latest_text,
                "url": _text(amendment.get("url")),
                "sha256": file_sha,
                "source_id": f"congress-amendment-index:{bill_ref}",
            }
    return by_roll


def is_procedural(action: dict[str, Any]) -> bool:
    question = action["question"]
    if PROCEDURAL_QUESTIONS.search(question):
        return True
    return action["bill_ref"].startswith("bill_119_hres_") and bool(
        RULE_PREFIX.search(action["description"])
    )


def is_expressive(action: dict[str, Any], title: str) -> bool:
    measure_type = action["bill_ref"].split("_")[2]
    return measure_type in {"hres", "hconres", "sres", "sconres"} and bool(
        EXPRESSIVE_PREFIX.search(title or action["description"])
    )


def action_stage(question: str) -> str:
    lowered = question.lower()
    if "amendment" in lowered:
        return "amendment"
    if "pass" in lowered:
        return "final_passage_or_suspension_passage"
    if "resolution" in lowered:
        return "resolution_adoption"
    if "retaining division" in lowered:
        return "division_retention"
    return "other_exact_house_action"


def episode_candidate(domain_id: str, action: dict[str, Any], title: str) -> str:
    text = f"{title} {action['description']}".lower()
    if domain_id == "NATIONAL_SECURITY_FOREIGN" and (
        "war powers" in text or ("armed forces" in text and "hostilities" in text)
    ):
        if "iran" in text:
            return "episode-candidate:war-powers:iran"
        if "lebanon" in text:
            return "episode-candidate:war-powers:lebanon"
        if "venezuela" in text:
            return "episode-candidate:war-powers:venezuela"
    return f"episode-candidate:{action['bill_ref'].removeprefix('bill_119_').replace('_', ':')}"


def build_candidate_record(
    domain_id: str,
    action: dict[str, Any],
    metadata: dict[str, Any] | None,
    production: dict[str, Any] | None,
    amendment: dict[str, Any] | None,
) -> dict[str, Any] | None:
    title = "" if metadata is None else metadata["title"]
    policy_area = "" if metadata is None else metadata["policy_area"]
    parent_hits = set(domain_hits(title, policy_area, action["description"]))
    production_breakdown = (
        {} if production is None else (production.get("score_breakdown") or {})
    )
    recall_reasons: list[str] = []
    if production and production.get("primary_domain") == domain_id:
        recall_reasons.append("production_primary_domain")
    if domain_id in production_breakdown:
        recall_reasons.append("production_secondary_or_provisional_signal")
    if domain_id in parent_hits:
        recall_reasons.append("official_measure_signal")
    if not recall_reasons:
        return None

    exact_text = ""
    exact_hits: set[str] = set()
    exact_source: dict[str, Any] | None = None
    question_lower = action["question"].lower()
    child_action_requires_binding = (
        "amendment" in question_lower
        or "retaining division" in question_lower
        or "concur in the senate amendment" in question_lower
    )
    if "amendment" in question_lower and "senate amendment" not in question_lower:
        if amendment:
            exact_text = f"{amendment['description']} {amendment['purpose']}"
            exact_hits = set(domain_hits(exact_text))
            exact_source = {
                "source_id": amendment["source_id"],
                "source_type": "congress_gov_bill_amendment_index",
                "url": amendment["url"],
                "sha256": amendment["sha256"],
                "exact_identity": amendment["identity"],
                "evidence_role": "exact_amendment_identity_purpose_and_recorded_roll_binding",
                "house_action_stage": action_stage(action["question"]),
                "canonical_action_id": action["action_id"],
            }
    elif child_action_requires_binding:
        # A parent measure title or policy area cannot establish what a retained
        # division or Senate amendment itself contained.
        exact_text = ""
        exact_hits = set()
    else:
        exact_text = f"{title} {policy_area} {action['description']}"
        exact_hits = set(domain_hits(exact_text))
        if metadata:
            exact_source = {
                "source_id": f"congress-metadata:{action['bill_ref']}",
                "source_type": "congress_gov_measure_metadata",
                "url": metadata["url"],
                "sha256": metadata["sha256"],
                "exact_identity": action["bill_ref"]
                .removeprefix("bill_")
                .replace("_", ":"),
                "evidence_role": "exact_measure_identity_and_issue_boundary",
                "house_action_stage": action_stage(action["question"]),
                "canonical_action_id": action["action_id"],
            }

    unresolved_reason = None
    if is_procedural(action):
        disposition = "procedural_context"
        rationale = (
            "The exact House action is a procedural control and remains non-counting."
        )
    elif is_expressive(action, title):
        disposition = "expressive_nonbinding_context"
        rationale = "The exact resolution expresses a House view without creating operative policy."
    elif metadata is None:
        disposition = "source_missing"
        rationale = (
            "The Clerk action is resolved but official measure metadata is absent."
        )
        unresolved_reason = "missing_official_measure_metadata"
    elif child_action_requires_binding and exact_source is None:
        disposition = "boundary_review_required"
        rationale = "Parent-measure context cannot establish the narrower child action's domain membership."
        unresolved_reason = "missing_exact_child_action_binding"
    elif domain_id in exact_hits:
        disposition = (
            "proposed_in_scope_non_directional"
            if action["member_action"] in {"present", "not_voting"}
            else "proposed_in_scope_substantive"
        )
        rationale = "Official exact-action evidence independently supports proposed domain membership."
    elif production and production.get("primary_domain") == domain_id:
        disposition = "boundary_review_required"
        rationale = "Production supplies a domain signal, but the exact official action does not independently resolve membership."
        unresolved_reason = "production_official_boundary_mismatch"
    else:
        disposition = "exact_action_ineligible"
        rationale = "The recall signal is not supported as domain membership by the exact official action."

    sources = [action["vote_source"]]
    if metadata:
        sources.append(
            {
                "source_id": f"congress-metadata:{action['bill_ref']}",
                "source_type": "congress_gov_measure_metadata",
                "url": metadata["url"],
                "sha256": metadata["sha256"],
            }
        )
    if exact_source and exact_source["source_id"] != sources[-1]["source_id"]:
        sources.append(
            {
                key: exact_source[key]
                for key in ("source_id", "source_type", "url", "sha256")
            }
        )

    episode_id = None
    if disposition.startswith("proposed_in_scope_"):
        episode_id = episode_candidate(domain_id, action, title)
    return {
        "action_id": action["action_id"],
        "date": action["date"],
        "bill_ref": action["bill_ref"],
        "question": action["question"],
        "description": action["description"],
        "member_action": action["member_action"],
        "house_action_stage": action_stage(action["question"]),
        "official_title": title,
        "official_policy_area": policy_area or None,
        "recall_reasons": sorted(recall_reasons),
        "exact_action_domain_signals": sorted(exact_hits),
        "disposition": disposition,
        "rationale": rationale,
        "unresolved_reason": unresolved_reason,
        "episode_candidate_id": episode_id,
        "sources": sources,
        "exact_action_source_binding": exact_source,
        "public_action_sha256": sha256_json(
            {
                "action_id": action["action_id"],
                "date": action["date"],
                "bill_ref": action["bill_ref"],
                "question": action["question"],
                "description": action["description"],
                "member_action": action["member_action"],
            }
        ),
    }


def domain_accounting(domain_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(record["disposition"] for record in records)
    substantive = [
        record
        for record in records
        if record["disposition"].startswith("proposed_in_scope_")
    ]
    episode_actions: dict[str, list[str]] = defaultdict(list)
    for record in substantive:
        episode_actions[record["episode_candidate_id"]].append(record["action_id"])
    episodes = [
        {"episode_candidate_id": key, "action_ids": sorted_action_ids(values)}
        for key, values in sorted(episode_actions.items())
    ]
    multi = [episode for episode in episodes if len(episode["action_ids"]) > 1]
    unresolved = [
        record
        for record in records
        if record["disposition"]
        in {
            "boundary_review_required",
            "source_missing",
            "source_unresolved",
            "source_conflicting",
        }
    ]
    procedural_count = counts["procedural_context"]
    expressive_count = counts["expressive_nonbinding_context"]
    ineligible_count = counts["exact_action_ineligible"]
    substantive_count = len(substantive)
    exclusion_reasons: list[str] = []
    if substantive_count < 5:
        exclusion_reasons.append("fewer_than_five_substantive_actions")
    if len(episodes) < 3:
        exclusion_reasons.append("fewer_than_three_independent_episode_candidates")
    if not multi:
        exclusion_reasons.append("no_legitimate_multi_action_episode")
    source_ready = sum(
        bool(record["exact_action_source_binding"]) for record in substantive
    )
    mechanisms = sorted(
        {
            "amendment"
            if "amendment" in record["question"].lower()
            else "passage"
            if "pass" in record["question"].lower()
            else "resolution"
            if "resolution" in record["question"].lower()
            else "other_exact_action"
            for record in substantive
        }
    )
    return {
        "domain_id": domain_id,
        "display_name": DISPLAY_NAMES[domain_id],
        "eligible": not exclusion_reasons,
        "exclusion_reasons": exclusion_reasons,
        "total_candidate_actions": len(records),
        "substantive_eligible_actions": substantive_count,
        "procedural_context_actions": procedural_count,
        "expressive_nonbinding_actions": expressive_count,
        "exact_action_ineligible_actions": ineligible_count,
        "unresolved_boundary_cases": len(unresolved),
        "independent_episode_count": len(episodes),
        "multi_action_episode_count": len(multi),
        "mechanism_types": mechanisms,
        "official_source_readiness": {
            "state": "complete_for_proposed_membership"
            if source_ready == substantive_count
            else "partial",
            "ready_substantive_actions": source_ready,
            "substantive_actions": substantive_count,
        },
        "material_source_gaps": sorted(
            {
                record["unresolved_reason"]
                for record in unresolved
                if record["unresolved_reason"]
            }
        ),
        "episodes": episodes,
        "multi_action_episodes": multi,
        "action_ids_by_disposition": {
            disposition: sorted_action_ids(
                record["action_id"]
                for record in records
                if record["disposition"] == disposition
            )
            for disposition in sorted(counts)
        },
    }


def selection_rank(accounting: dict[str, Any]) -> tuple[Any, ...]:
    readiness = accounting["official_source_readiness"]
    complete = readiness["state"] == "complete_for_proposed_membership"
    return (
        0 if complete else 1,
        -accounting["independent_episode_count"],
        -len(accounting["mechanism_types"]),
        -accounting["multi_action_episode_count"],
        accounting["unresolved_boundary_cases"],
        accounting["domain_id"],
    )


def build(
    *,
    production_snapshot: Path,
    clerk_dirs: list[Path],
    congress_metadata_dir: Path,
    amendment_index_dir: Path,
    cutoff: str,
) -> dict[str, Any]:
    production, production_payload = load_production_snapshot(production_snapshot)
    official_actions = load_clerk_actions(clerk_dirs, "F000477")
    metadata = load_congress_metadata(congress_metadata_dir)
    amendments = load_amendment_indexes(amendment_index_dir)
    if len(official_actions) != 638:
        raise ValueError(
            f"expected governed 638-action cutoff, found {len(official_actions)}"
        )

    records_by_domain: dict[str, list[dict[str, Any]]] = {}
    accounting: list[dict[str, Any]] = []
    for domain_id in DOMAIN_IDS:
        records = []
        for action in official_actions:
            record = build_candidate_record(
                domain_id,
                action,
                metadata.get(action["bill_ref"]),
                production.get(action["action_id"]),
                amendments.get((action["bill_ref"], action["roll"])),
            )
            if record:
                records.append(record)
        records_by_domain[domain_id] = records
        accounting.append(domain_accounting(domain_id, records))

    eligible = sorted(
        (item for item in accounting if item["eligible"]), key=selection_rank
    )
    selected_domain = eligible[0]["domain_id"] if eligible else None
    selection_material = {
        "starting_commit": STARTING_COMMIT,
        "cutoff": cutoff,
        "complete_official_action_set_sha256": sha256_json(
            [row["action_id"] for row in official_actions]
        ),
        "domain_accounting": accounting,
        "selected_domain": selected_domain,
        "selection_order": [item["domain_id"] for item in eligible],
    }
    selection = {
        "schema_version": "cross_issue_domain_selection_v2",
        "milestone": MILESTONE,
        "starting_commit": STARTING_COMMIT,
        "subject": {
            "member_id": "F000477",
            "legislator_id": "leg_valerie_p_foushee",
            "congress": 119,
            "chamber": "house",
        },
        "cutoff": cutoff,
        "excluded_domains": sorted(EXCLUDED_DOMAINS),
        "complete_official_action_count": len(official_actions),
        "complete_official_action_set_sha256": selection_material[
            "complete_official_action_set_sha256"
        ],
        "production_snapshot": {
            "snapshot_id": production_payload["snapshot_id"],
            "sha256": sha256_file(production_snapshot),
            "read_only": True,
            "transaction_rolled_back": True,
            "production_action_count": len(production),
        },
        "candidate_domains": accounting,
        "eligible_domains_ranked": [item["domain_id"] for item in eligible],
        "selected_domain": selected_domain,
        "selection_state": "selected"
        if selected_domain
        else "blocked_no_eligible_domain",
        "selection_basis": [
            "complete_official_source_evidence",
            "independent_policy_episode_count",
            "policy_mechanism_variation",
            "legitimate_multi_action_episode",
            "smallest_unresolved_boundary_set",
            "canonical_domain_id_tie_breaker",
        ],
        "selection_sha256": sha256_json(selection_material),
        "next_stage_authorized": selected_domain is not None,
    }
    selected_records = (
        [] if selected_domain is None else records_by_domain[selected_domain]
    )
    selected_accounting = (
        None
        if selected_domain is None
        else next(item for item in accounting if item["domain_id"] == selected_domain)
    )
    universe_material = {
        "subject": {
            "member_id": "F000477",
            "issue_id": selected_domain,
            "congress": 119,
        },
        "cutoff": cutoff,
        "candidate_records": selected_records,
    }
    universe = {
        "schema_version": "cross_issue_universe_proposal_v1",
        "milestone": MILESTONE,
        "subject": universe_material["subject"],
        "authority_status": "pending_human_universe_boundary_review",
        "full_record_claim": False,
        "synthesis_eligible": False,
        "cutoff": {
            "start_date": "2025-01-03",
            "end_date": cutoff,
            "latest_roll": "house:119:2:283",
        },
        "complete_member_action_count": len(official_actions),
        "selection_sha256": selection["selection_sha256"],
        "universe_subject_sha256": sha256_json(universe_material),
        "accounting": selected_accounting,
        "candidate_dispositions": selected_records,
        "proposed_action_ids": sorted_action_ids(
            record["action_id"]
            for record in selected_records
            if record["disposition"].startswith("proposed_in_scope_")
        ),
        "unresolved_action_ids": sorted_action_ids(
            record["action_id"]
            for record in selected_records
            if record["disposition"] in {"boundary_review_required", "source_missing"}
        ),
        "episode_candidates_are_non_authorizing": True,
        "action_interpretation_started": False,
        "semantic_ir_started": False,
        "publication_changes": False,
        "production_writes": False,
    }
    source_inventory = {
        "schema_version": "cross_issue_source_inventory_v1",
        "subject": universe_material["subject"],
        "cutoff": cutoff,
        "source_acquired_at": production_payload["query_audit"][0][
            "snapshot_started_at"
        ],
        "complete_official_action_count": len(official_actions),
        "source_roots": [
            {
                "source_type": "house_clerk_roll_call_xml",
                "file_count": sum(
                    len(list(path.glob("roll*.xml"))) for path in clerk_dirs
                ),
            },
            {
                "source_type": "congress_gov_measure_metadata",
                "file_count": len(metadata),
            },
            {
                "source_type": "congress_gov_bill_amendment_index",
                "file_count": len(list(amendment_index_dir.glob("119_*.json"))),
            },
        ],
        "selected_candidate_source_bindings": [
            {
                "action_id": record["action_id"],
                "member_action": record["member_action"],
                "house_action_stage": record["house_action_stage"],
                "disposition": record["disposition"],
                "sources": record["sources"],
                "exact_action_source_binding": record["exact_action_source_binding"],
            }
            for record in selected_records
        ],
    }
    source_inventory["inventory_sha256"] = sha256_json(
        {
            key: value
            for key, value in source_inventory.items()
            if key != "inventory_sha256"
        }
    )
    return {
        "selection": selection,
        "universe": universe,
        "source_inventory": source_inventory,
    }


def render_review_packet(payloads: dict[str, Any]) -> str:
    selection = payloads["selection"]
    universe = payloads["universe"]
    accounting = universe["accounting"]
    records = universe["candidate_dispositions"]
    proposed = [
        record
        for record in records
        if record["disposition"].startswith("proposed_in_scope_")
    ]
    unresolved = [record for record in records if record["unresolved_reason"]]
    lines = [
        "# M11A Cross-Issue Full-Record Expansion Review Packet",
        "",
        "## Decision boundary",
        "",
        "- Subject: Valerie Foushee (`F000477`; `leg_valerie_p_foushee`), House, 119th Congress.",
        f"- Official cutoff: `{universe['cutoff']['end_date']}` through `{universe['cutoff']['latest_roll']}`.",
        f"- Selected domain: **{accounting['display_name']}** (`{selection['selected_domain']}`).",
        f"- Selection digest: `{selection['selection_sha256']}`.",
        f"- Universe-subject digest: `{universe['universe_subject_sha256']}`.",
        "- Authority: pending human universe-boundary review. This packet does not authorize action interpretation, episode acceptance, synthesis, Semantic IR conclusions, publication, or production writes.",
        "",
        "## Why this domain was selected",
        "",
        "The deterministic selector excludes Justice & Public Safety and Economy & Taxes, applies the same eligibility gates to every remaining canonical domain, then ranks eligible domains by official-source completeness, episode count, mechanism variation, legitimate multi-action episodes, smallest unresolved boundary, and canonical ID as the final tie-breaker. No party, vote direction, ideology, or political-interest signal participates.",
        "",
        "| Domain | Candidates | Proposed substantive | Procedural/context | Expressive | Exact-action ineligible | Unresolved | Episode candidates | Multi-action | Eligible |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in selection["candidate_domains"]:
        lines.append(
            f"| {item['display_name']} | {item['total_candidate_actions']} | {item['substantive_eligible_actions']} | "
            f"{item['procedural_context_actions']} | {item['expressive_nonbinding_actions']} | "
            f"{item['exact_action_ineligible_actions']} | {item['unresolved_boundary_cases']} | "
            f"{item['independent_episode_count']} | {item['multi_action_episode_count']} | "
            f"{'yes' if item['eligible'] else 'no: ' + ', '.join(item['exclusion_reasons'])} |"
        )
    lines.extend(
        [
            "",
            "## Selected-universe accounting",
            "",
            f"The high-recall candidate set contains **{accounting['total_candidate_actions']}** actions. It proposes **{accounting['substantive_eligible_actions']}** exact-action-supported substantive actions across **{accounting['independent_episode_count']}** non-authorizing episode candidates, including **{accounting['multi_action_episode_count']}** multi-action candidates. It preserves **{accounting['procedural_context_actions']}** procedural/context actions, **{accounting['expressive_nonbinding_actions']}** expressive nonbinding actions, **{accounting['exact_action_ineligible_actions']}** exact-action-ineligible actions, and **{accounting['unresolved_boundary_cases']}** unresolved boundaries.",
            "",
            "## Proposed included actions",
            "",
            "Each row is an inclusion proposal based only on exact official action evidence. Episode IDs are review conveniences, not accepted semantic episodes.",
            "",
            "| Action | Date | Stage | Member action | Measure | Exact official source | Episode candidate |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for record in proposed:
        binding = record["exact_action_source_binding"]
        lines.append(
            f"| `{record['action_id']}` | {record['date']} | {record['house_action_stage']} | "
            f"{record['member_action']} | {record['bill_ref']} | [{binding['exact_identity']}]({binding['url']}) | "
            f"`{record['episode_candidate_id']}` |"
        )
    lines.extend(
        [
            "",
            "## Exclusion and unresolved categories",
            "",
        ]
    )
    for disposition, action_ids in accounting["action_ids_by_disposition"].items():
        if disposition.startswith("proposed_in_scope_"):
            continue
        lines.extend(
            [
                f"### `{disposition}` ({len(action_ids)})",
                "",
                ", ".join(f"`{action_id}`" for action_id in action_ids) or "None.",
                "",
            ]
        )
    lines.extend(
        [
            "## Material source gaps and boundary cases",
            "",
            "Unresolved rows are excluded from the proposed substantive universe. In particular, parent-measure evidence is not used to establish a narrower amendment, retained division, or Senate-amendment action.",
            "",
            "| Action | Question | Reason |",
            "|---|---|---|",
        ]
    )
    for record in unresolved:
        lines.append(
            f"| `{record['action_id']}` | {record['question']} | `{record['unresolved_reason']}` |"
        )
    lines.extend(
        [
            "",
            "## Human review requested",
            "",
            "Review the selected-domain decision, every proposed inclusion, the preserved exclusion categories, the six unresolved child-action boundaries, the non-authorizing episode candidates, and the genericity audit. Acceptance would authorize only a later, separate action-interpretation milestone; it would not approve any interpretation, synthesis, public wording, publication, or production operation.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production-snapshot", required=True, type=Path)
    parser.add_argument("--clerk-dir", required=True, action="append", type=Path)
    parser.add_argument("--congress-metadata-dir", required=True, type=Path)
    parser.add_argument("--amendment-index-dir", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--cutoff", default="2026-07-23")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payloads = build(
        production_snapshot=args.production_snapshot,
        clerk_dirs=args.clerk_dir,
        congress_metadata_dir=args.congress_metadata_dir,
        amendment_index_dir=args.amendment_index_dir,
        cutoff=args.cutoff,
    )
    outputs = {
        args.output_root / "domain_selection.json": payloads["selection"],
        args.output_root / "selected_domain_universe_proposal.json": payloads[
            "universe"
        ],
        args.output_root / "source_inventory.json": payloads["source_inventory"],
    }
    review_packet_path = (
        args.output_root.parents[1]
        / "review_packets"
        / "m11a_cross_issue_full_record_expansion_v1.md"
    )
    review_packet = render_review_packet(payloads)
    if args.check:
        drift = [
            str(path)
            for path, payload in outputs.items()
            if not path.exists()
            or json.loads(path.read_text(encoding="utf-8")) != payload
        ]
        if (
            not review_packet_path.exists()
            or review_packet_path.read_text(encoding="utf-8") != review_packet
        ):
            drift.append(str(review_packet_path))
        if drift:
            raise SystemExit("generated M11A artifacts differ: " + ", ".join(drift))
    else:
        args.output_root.mkdir(parents=True, exist_ok=True)
        for path, payload in outputs.items():
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        review_packet_path.parent.mkdir(parents=True, exist_ok=True)
        review_packet_path.write_text(review_packet, encoding="utf-8")
    print(
        json.dumps(
            {
                "selected_domain": payloads["selection"]["selected_domain"],
                "eligible_domains": payloads["selection"]["eligible_domains_ranked"],
                "selected_accounting": payloads["universe"]["accounting"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
