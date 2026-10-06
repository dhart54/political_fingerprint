"""Bounded GET-only checks of the established public publication contract.

Expectations come from the committed, authorized Green activation after-state,
not from the response under test. This checks serving invariants, not editorial
approval or full API byte equality; presentation prose may be rendered differently.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "docs/editorial/publication_replacements/m15b_green_activation_execution"
AUTHORITY_FILE = "after-justice-direct.json.gz"
MEMBER = "leg_valerie_p_foushee"
OTHER_MEMBER = "leg_thomas_massie"
JUSTICE = "JUSTICE_PUBLIC_SAFETY"
PUBLISHED = {
    "EDUCATION_WORKFORCE", "ENVIRONMENT_ENERGY",
    "NATIONAL_SECURITY_FOREIGN", JUSTICE,
}
ENDPOINTS = {
    "health": "/health",
    "positions": f"/legislators/{MEMBER}/positions?scope=119",
    "evidence": f"/legislators/{MEMBER}/positions/{JUSTICE}/evidence?scope=119",
    "presentations-119": f"/legislators/{MEMBER}/editorial-presentations?scope=119",
    "presentations-all": f"/legislators/{MEMBER}/editorial-presentations?scope=all",
    "presentations-118": f"/legislators/{MEMBER}/editorial-presentations?scope=118",
    "other-member": f"/legislators/{OTHER_MEMBER}/editorial-presentations?scope=119",
}


class SmokeFailure(ValueError):
    """A transport or serving-contract failure; never a semantic success."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def load_authority() -> dict:
    data = (AUTHORITY / AUTHORITY_FILE).read_bytes()
    manifest = json.loads((AUTHORITY / "file_manifest.json").read_text(encoding="utf-8"))
    require(hashlib.sha256(data).hexdigest() == manifest[AUTHORITY_FILE],
            "Committed activation evidence digest differs")
    return json.loads(gzip.decompress(data))


def reference(authority: dict, member: str, scope: str, route: str) -> dict:
    entry = authority[f"{member}:{scope}:{route}"]
    require(entry["status"] == 200, "Authority response is not successful")
    return entry["body"]


def index(rows: object, key: str, label: str) -> dict:
    require(isinstance(rows, list) and bool(rows), f"{label} is empty or not a list")
    result = {}
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get(key), str),
                f"{label} has an invalid {key}")
        require(row[key] not in result, f"{label} has duplicate {key}: {row[key]}")
        result[row[key]] = row
    return result


def finding_binding(item: dict) -> dict:
    keys = ("wording_item_id", "proposition_id", "semantic_role", "direction",
            "action_ids", "episode_ids", "public_supporting_action_ids",
            "public_supporting_episode_ids", "semantic_source_ids",
            "semantic_lineage_action_ids", "semantic_lineage_episode_ids",
            "semantic_lineage_directions", "show_direction", "surface")
    return {key: item[key] for key in keys if key in item}


def stable_findings(row: dict, field: str) -> list:
    """Bind findings to their established identities/actions, independently of copy."""
    items = row[field]
    require(isinstance(items, list), f"{field} is not a list")
    require(all(isinstance(item, dict) for item in items), f"{field} contains non-object findings")
    return [finding_binding(item) for item in items]


def check_health(payload: dict, expected_commit: str | None) -> str:
    commit = payload.get("commit_sha")
    require(payload.get("status") == "ok" and isinstance(commit, str)
            and re.fullmatch(r"[0-9a-f]{40}", commit) is not None,
            "Health is not ok with an identified deployed commit")
    require(expected_commit is None or commit == expected_commit,
            f"Deployment differs: expected {expected_commit}, got {commit}")
    return commit


def check_presentations(payload: dict, expected: dict) -> dict:
    for key in ("schema_version", "legislator_id", "member_bioguide_id", "scope"):
        require(payload.get(key) == expected[key], f"Editorial identity differs: {key}")
    actual = index(payload.get("presentations"), "issue_id", "Presentations")
    wanted = index(expected["presentations"], "issue_id", "Authority presentations")
    require(actual.keys() == wanted.keys(), "Editorial issue coverage differs")
    for issue_id, row in actual.items():
        ref = wanted[issue_id]
        require(row.get("tier") == ref["tier"], f"{issue_id}: publication tier differs")
        if ref["tier"] == "receipts_only":
            require(row == ref, f"{issue_id}: receipts-only isolation differs")
            continue
        for key in ("requested_scope", "reviewed_scope", "provenance"):
            require(row.get(key) == ref[key], f"{issue_id}: {key} differs")
        if ref["conclusion"] is not None:
            require(isinstance(row.get("conclusion"), dict)
                    and bool(row["conclusion"].get("headline"))
                    and bool(row["conclusion"].get("body")), f"{issue_id}: empty conclusion")
        else:
            require(row.get("conclusion") is None and isinstance(row.get("overview"), dict)
                    and bool(row["overview"].get("primary_sentence"))
                    and finding_binding(row["overview"]) == finding_binding(ref["overview"]),
                    f"{issue_id}: overview/conclusion boundary differs")
        require(bool(row.get("coverage_text")) and bool(row.get("teaser")),
                f"{issue_id}: missing coverage or teaser")
        boundary = row.get("scope_boundary")
        require(isinstance(boundary, str) and re.search(r"119th[- ]Congress", boundary) is not None,
                f"{issue_id}: missing reviewed scope boundary")
        if payload["scope"] == "all":
            require(boundary.endswith(ref["scope_boundary"].rsplit(". ", 1)[-1]),
                    f"{issue_id}: scope=all boundary omitted")
        for field in ("repeated_patterns", "policy_trajectories", "syntheses", "notable_choices"):
            if field not in ref:
                continue
            require(stable_findings(row, field) == stable_findings(ref, field),
                    f"{issue_id}: {field} coverage differs")
            for item, ref_item in zip(row[field], ref[field]):
                for key in ("body", "heading", "title", "primary_sentence"):
                    if ref_item.get(key):
                        require(isinstance(item.get(key), str) and bool(item[key].strip()),
                                f"{issue_id}: {field} has empty {key}")
        require(bool(row["repeated_patterns"]), f"{issue_id}: findings are empty")
    return actual


RECEIPT_BINDINGS = (
    "canonical_action_id", "member_id", "issue_id", "member_action",
    "congress_scope", "review_scope", "published_artifact_identity",
    "action_meaning_id", "action_interpretation_id", "action_interpretation_sha256",
    "interpretation_status", "interpretation_disposition", "vote_sources",
)


def check_justice(row: dict, expected: dict, evidence: dict) -> None:
    for field in ("evidence_metadata", "review_state", "reviewed_action_ids", "noncounting_controls"):
        require(row.get(field) == expected[field], f"Justice {field} accounting differs")
    receipts = index(row.get("exact_action_receipts"), "canonical_action_id", "Justice receipts")
    wanted = index(expected["exact_action_receipts"], "canonical_action_id", "Authority receipts")
    require(receipts.keys() == wanted.keys(), "Justice exact receipt coverage differs")
    rows = index(evidence.get("evidence"), "canonical_action_id", "Justice vote evidence")
    for action_id, receipt in receipts.items():
        for field in RECEIPT_BINDINGS:
            require(receipt.get(field) == wanted[action_id][field],
                    f"Justice {action_id}: receipt {field} differs")
        require(bool(receipt.get("exact_action_meaning"))
                and bool(receipt.get("action_meaning_sources")),
                f"Justice {action_id}: meaning or sources missing")
        vote = rows.get(action_id)
        require(vote is not None, f"Justice {action_id}: supporting vote missing")
        chamber, congress, session, roll = action_id.split(":")
        require((vote.get("chamber"), vote.get("congress"), vote.get("session"),
                 vote.get("rollcall_number")) == (chamber, int(congress), int(session), int(roll)),
                f"Justice {action_id}: vote identity differs")
        require(vote.get("position") == receipt["member_action"].lower(),
                f"Justice {action_id}: recorded vote differs")
        source = vote.get("source_url")
        require(isinstance(source, str) and urlsplit(source).scheme == "https"
                and urlsplit(source).hostname == "clerk.house.gov"
                and source in {s["url"] for s in receipt["vote_sources"]},
                f"Justice {action_id}: official vote source differs")
        require(isinstance(vote.get("interpretation_status"), str),
                f"Justice {action_id}: interpretation status missing")


def validate(responses: dict, authority: dict, expected_commit: str | None = None) -> dict:
    commit = check_health(responses["health"], expected_commit)
    if "health-after" in responses:
        require(check_health(responses["health-after"], expected_commit) == commit,
                "Deployment changed during smoke checks")
    presentations = {}
    for scope in ("119", "all", "118"):
        presentations[scope] = check_presentations(
            responses[f"presentations-{scope}"], reference(authority, MEMBER, scope, "editorial"))
    check_presentations(responses["other-member"], reference(authority, OTHER_MEMBER, "119", "editorial"))
    require({key for key, row in presentations["119"].items()
             if row["tier"] == "reviewed_conclusion"} == PUBLISHED,
            "Expected four established published domains")
    for name in ("positions", "evidence"):
        require(responses[name].get("legislator_id") == MEMBER
                and responses[name].get("scope") == "119", f"{name}: identity/scope differs")
    require(responses["evidence"].get("domain") == JUSTICE, "Evidence domain differs")
    positions = index(responses["positions"].get("positions"), "domain", "Positions")
    require(JUSTICE in positions and type(positions[JUSTICE].get("interpreted_total")) is int
            and positions[JUSTICE]["interpreted_total"] > 0, "Justice interpreted positions are empty")
    justice_ref = next(row for row in reference(authority, MEMBER, "119", "editorial")["presentations"]
                       if row["issue_id"] == JUSTICE)
    for scope in ("119", "all"):
        check_justice(presentations[scope][JUSTICE], justice_ref, responses["evidence"])
    return {"status": "passed", "deployed_commit": commit,
            "published_issues": sorted(PUBLISHED),
            "justice_directional_receipts": len(presentations["119"][JUSTICE]["exact_action_receipts"]),
            "justice_noncounting_controls": len(presentations["119"][JUSTICE]["noncounting_controls"]),
            "cross_scope_and_member_isolation": "passed"}


def get_json(base: str, path: str, timeout: float) -> dict:
    """No retry or fixture fallback: a transient is a reported transport failure."""
    try:
        with urlopen(Request(base.rstrip("/") + path, headers={"Accept": "application/json"},
                             method="GET"), timeout=timeout) as response:
            require(response.status == 200, f"GET {path}: HTTP {response.status}")
            raw = response.read(8 * 1024 * 1024 + 1)
            require(len(raw) <= 8 * 1024 * 1024, f"GET {path}: response exceeds 8 MiB")
            payload = json.loads(raw)
    except HTTPError as exc:
        raise SmokeFailure(f"GET {path}: HTTP {exc.code}; no contract success") from None
    except SmokeFailure:
        raise
    except (URLError, TimeoutError, OSError) as exc:
        raise SmokeFailure(f"GET {path}: transport failure ({type(exc).__name__})") from None
    except (ValueError, UnicodeError):
        raise SmokeFailure(f"GET {path}: invalid JSON response") from None
    require(isinstance(payload, dict), f"GET {path}: JSON object required")
    return payload


def run(base: str, output_dir: Path, expected_commit: str | None = None, timeout: float = 30) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {"status": "failed", "api_base_url": base,
              "captured_at_utc": datetime.now(timezone.utc).isoformat(),
              "authority_file": (AUTHORITY / AUTHORITY_FILE).relative_to(ROOT).as_posix(),
              "checked_endpoints": []}
    try:
        responses = {}
        for name, path in ENDPOINTS.items():
            responses[name] = get_json(base, path, timeout)
            if name == "health":
                report["deployed_commit"] = check_health(responses[name], expected_commit)
            (output_dir / f"{name}.json").write_text(json.dumps(responses[name]), encoding="utf-8")
            report["checked_endpoints"].append(path)
        responses["health-after"] = get_json(base, "/health", timeout)
        (output_dir / "health-after.json").write_text(json.dumps(responses["health-after"]), encoding="utf-8")
        report["checked_endpoints"].append("/health")
        report.update(validate(responses, load_authority(), expected_commit))
    except (SmokeFailure, KeyError, TypeError, ValueError, OSError) as exc:
        report["failure"] = str(exc)
    report["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    (output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base-url", default="https://political-fingerprint.onrender.com")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-commit")
    args = parser.parse_args(argv)
    parsed = urlsplit(args.api_base_url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        parser.error("API base must be an HTTPS URL without credentials, query or fragment")
    if args.expected_commit and re.fullmatch(r"[0-9a-f]{40}", args.expected_commit) is None:
        parser.error("Expected commit must be a full lowercase Git SHA")
    report = run(args.api_base_url, args.output_dir, args.expected_commit)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
