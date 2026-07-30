from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree


PROCEDURAL_QUESTIONS = re.compile(
    r"(?i)\b("
    r"ordering the previous question|motion to recommit|motion to commit|"
    r"motion to table|motion to refer|motion to discharge|"
    r"motion to reconsider"
    r")\b"
)
RULE_TITLES = re.compile(
    r"(?i)^(providing for (consideration|disposition)|waiving a requirement)"
)
UNRESOLVED_DISPOSITIONS = {
    "source_missing",
    "source_unresolved",
    "source_conflicting",
    "boundary_review_required",
}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def action_sort_key(action_id: str) -> tuple[str, int, int, int]:
    chamber, congress, session, roll = action_id.split(":")
    return chamber, int(congress), int(session), int(roll)


def sorted_action_ids(values: Iterable[str]) -> list[str]:
    return sorted(set(values), key=action_sort_key)


def action_set(value: Iterable[str]) -> dict[str, Any]:
    action_ids = sorted_action_ids(value)
    return {
        "action_ids": action_ids,
        "action_count": len(action_ids),
        "action_set_sha256": sha256_json(sorted(action_ids)),
    }


def load_house_clerk_member_actions(
    source_dirs: Iterable[Path],
    *,
    bioguide_id: str,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for source_dir in source_dirs:
        for path in sorted(source_dir.glob("roll*.xml")):
            root = ElementTree.parse(path).getroot()
            metadata = root.find("vote-metadata")
            if metadata is None:
                raise ValueError(f"missing vote metadata: {path}")
            member_vote = None
            for recorded_vote in root.findall("./vote-data/recorded-vote"):
                legislator = recorded_vote.find("legislator")
                if legislator is None:
                    continue
                identity = (
                    legislator.attrib.get("bioguide-id")
                    or legislator.attrib.get("name-id")
                )
                if identity == bioguide_id:
                    member_vote = _required_text(recorded_vote.find("vote"))
                    break
            if member_vote is None:
                raise ValueError(
                    f"{bioguide_id} missing from official roll call {path.name}"
                )
            congress = int(_required_text(metadata.find("congress")))
            session = _session_number(_required_text(metadata.find("session")))
            roll = int(_required_text(metadata.find("rollcall-num")))
            description = (
                _optional_text(metadata.find("vote-desc"))
                or _optional_text(metadata.find("amendment-author"))
                or _required_text(metadata.find("vote-question"))
            )
            bill_text = _optional_text(metadata.find("legis-num"))
            if bill_text is None:
                continue
            try:
                bill_ref = _bill_ref(congress, bill_text)
            except ValueError:
                # Match the repository House adapter: organizational votes
                # such as QUORUM lack a supported legislative measure identity
                # and are not member legislative actions in this inventory.
                continue
            actions.append(
                {
                    "canonical_action_id": (
                        f"house:{congress}:{session}:{roll}"
                    ),
                    "chamber": "house",
                    "congress": congress,
                    "session": session,
                    "rollcall_number": roll,
                    "vote_date": _house_date(
                        _required_text(metadata.find("action-date"))
                    ),
                    "bill_ref": bill_ref,
                    "question": _required_text(metadata.find("vote-question")),
                    "description": description,
                    "member_action": _member_action(member_vote),
                    "source_url": (
                        f"https://clerk.house.gov/evs/"
                        f"{_house_year(congress, session)}/roll{roll:03d}.xml"
                    ),
                }
            )
    by_id: dict[str, dict[str, Any]] = {}
    for action in actions:
        action_id = action["canonical_action_id"]
        if action_id in by_id:
            raise ValueError(f"duplicate official action: {action_id}")
        by_id[action_id] = action
    return sorted(by_id.values(), key=lambda row: action_sort_key(row["canonical_action_id"]))


def load_congress_metadata(
    metadata_dirs: Iterable[Path],
) -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    for source_dir in metadata_dirs:
        if not source_dir.exists():
            continue
        for path in sorted(source_dir.glob("119_*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            bill = payload.get("bill", payload)
            congress = int(bill["congress"])
            bill_type = str(bill.get("type") or bill.get("billType")).lower()
            bill_number = int(bill.get("number") or bill.get("billNumber"))
            identity = f"bill_{congress}_{bill_type}_{bill_number}"
            policy = bill.get("policyArea") or {}
            metadata[identity] = {
                "bill_ref": identity,
                "title": str(bill.get("title") or ""),
                "policy_area": (
                    str(policy.get("name")) if policy.get("name") else None
                ),
                "legislation_url": bill.get("legislationUrl"),
                "source_file_sha256": sha256_file(path),
            }
    return metadata


def build_candidate_recall(
    production_rows: list[dict[str, Any]],
    official_rows: list[dict[str, Any]],
    congress_metadata: dict[str, dict[str, Any]],
    config: dict[str, Any],
) -> tuple[list[str], dict[str, list[str]]]:
    recall_pattern = re.compile(config["candidate_recall_regex"], re.IGNORECASE)
    reasons: dict[str, set[str]] = {}

    def include(action_id: str, reason: str) -> None:
        reasons.setdefault(action_id, set()).add(reason)

    for row in production_rows:
        action_id = str(row["canonical_action_id"])
        primary = row.get("primary_domain")
        breakdown = row.get("score_breakdown") or {}
        if primary == config["subject"]["issue_id"]:
            include(action_id, "production_primary_classification")
        if config["subject"]["issue_id"] in breakdown:
            include(action_id, "production_secondary_or_provisional_signal")
        text = " ".join(
            str(row.get(key) or "")
            for key in ("bill_title", "bill_summary", "question", "description")
        )
        if recall_pattern.search(text):
            include(action_id, "broad_text_recall")

    for row in official_rows:
        action_id = str(row["canonical_action_id"])
        metadata = congress_metadata.get(str(row["bill_ref"]))
        if metadata and metadata.get("policy_area") in set(
            config["official_in_scope_policy_areas"]
        ):
            include(action_id, "official_policy_area")

    for action_id in config["benchmark_action_ids"]:
        include(action_id, "governed_benchmark")
    for action_id in config["explicit_recall_action_ids"]:
        include(action_id, "structured_cross_domain_recall")
    for action_id in config.get("refresh_review_action_ids", []):
        include(action_id, "newly_observed_full_boundary_review")

    return (
        sorted_action_ids(reasons),
        {
            action_id: sorted(values)
            for action_id, values in sorted(
                reasons.items(), key=lambda item: action_sort_key(item[0])
            )
        },
    )


def is_procedural_context(action: dict[str, Any]) -> bool:
    question = str(action.get("question") or "")
    description = str(action.get("description") or "")
    bill_ref = str(action.get("bill_ref") or "")
    if PROCEDURAL_QUESTIONS.search(question):
        return True
    return (
        bill_ref.startswith("bill_119_hres_")
        and RULE_TITLES.search(description) is not None
    )


def discovery_disposition(
    action: dict[str, Any],
    *,
    production_row: dict[str, Any] | None,
    metadata: dict[str, Any] | None,
    config: dict[str, Any],
) -> tuple[str, str, str]:
    action_id = str(action["canonical_action_id"])
    reviewed = config.get("reviewed_dispositions", {}).get(action_id)
    if reviewed:
        return (
            str(reviewed["disposition"]),
            str(reviewed.get("confidence", "high")),
            str(reviewed["rationale"]),
        )
    if is_procedural_context(action):
        return (
            "procedural_context",
            "high",
            "The exact action is a procedural control and remains non-counting context.",
        )
    if action_id in set(config["boundary_review_action_ids"]):
        return (
            "boundary_review_required",
            "low",
            "The exact action has a plausible Justice relationship but crosses an official policy-area or omnibus boundary that requires human review.",
        )
    if metadata is None:
        return (
            "source_missing",
            "low",
            "The Clerk vote is resolved, but official measure metadata needed for the issue-boundary decision is absent.",
        )
    in_scope_policy = metadata.get("policy_area") in set(
        config["official_in_scope_policy_areas"]
    )
    if in_scope_policy or action_id in set(config["benchmark_action_ids"]):
        if str(action["member_action"]) in {"present", "not_voting"}:
            return (
                "proposed_in_scope_non_directional",
                "high",
                "Official exact-action evidence supports proposed Justice membership, while the member action is non-directional.",
            )
        return (
            "proposed_in_scope_substantive",
            "high",
            "Official exact-action metadata supports proposed Justice membership; no support/opposition meaning is assigned here.",
        )
    if (
        production_row
        and production_row.get("primary_domain") == config["subject"]["issue_id"]
    ):
        return (
            "boundary_review_required",
            "low",
            "Production assigns Justice as primary, but official exact-action metadata does not independently resolve the Justice boundary.",
        )
    return (
        "proposed_exact_action_ineligible",
        "medium",
        "The recall signal is not supported as Justice membership by the official exact-action policy area.",
    )


def directory_manifest(
    roots: Iterable[tuple[str, Path]],
    *,
    patterns: tuple[str, ...],
) -> dict[str, Any]:
    records: list[dict[str, str]] = []
    for logical_root, root in roots:
        for pattern in patterns:
            for path in sorted(root.glob(pattern)):
                records.append(
                    {
                        "path": f"{logical_root}/{path.name}",
                        "sha256": sha256_file(path),
                    }
                )
    records.sort(key=lambda row: row["path"])
    return {
        "artifact_count": len(records),
        "artifact_set_sha256": sha256_json(records),
    }


def _required_text(element: ElementTree.Element | None) -> str:
    if element is None or element.text is None or not element.text.strip():
        raise ValueError("expected House Clerk XML text")
    return element.text.strip()


def _optional_text(element: ElementTree.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    return element.text.strip() or None


def _session_number(value: str) -> int:
    digits = "".join(character for character in value if character.isdigit())
    if not digits:
        raise ValueError(f"unsupported House session: {value}")
    return int(digits)


def _house_year(congress: int, session: int) -> int:
    return 1789 + ((congress - 1) * 2) + (session - 1)


def _house_date(value: str) -> str:
    from datetime import datetime

    for format_string in ("%Y-%m-%d", "%d-%b-%Y"):
        try:
            return datetime.strptime(value, format_string).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"unsupported House date: {value}")


def _member_action(value: str) -> str:
    mapping = {
        "yea": "yea",
        "aye": "yea",
        "nay": "nay",
        "no": "nay",
        "present": "present",
        "not voting": "not_voting",
    }
    normalized = value.strip().lower()
    if normalized not in mapping:
        raise ValueError(f"unsupported House member action: {value}")
    return mapping[normalized]


def _bill_ref(congress: int, value: str) -> str:
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
    raise ValueError(f"unsupported House bill reference: {value}")
