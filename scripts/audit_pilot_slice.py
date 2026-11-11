"""GET-only coverage inventory for the bounded Foushee/Massie public pilot.

This is an observation, not editorial approval or a user-readiness verdict. It
retains response digests and small counts, not duplicate source/response blobs.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.render_backend_smoke import SmokeFailure, check_health, get_json, require

MEMBERS = ("leg_valerie_p_foushee", "leg_thomas_massie")
DOMAINS = (
    "ECONOMY_TAXES", "EDUCATION_WORKFORCE", "ENVIRONMENT_ENERGY", "HEALTH_SOCIAL",
    "IMMIGRATION_BORDER", "INFRASTRUCTURE_TECH_TRANSPORT", "JUSTICE_PUBLIC_SAFETY",
    "NATIONAL_SECURITY_FOREIGN",
)
LIMITS = (
    "Counts describe API responses, not completed editorial review or record completeness.",
    "No editorial approval, publication, persistence, or production mutation is performed.",
    "HTTP/schema/linkage checks do not establish rendering, human comprehension, or source truth.",
    "Per-issue counts overlap; do not sum them into a member-wide unique-vote total.",
)


def endpoints(scope: str) -> dict[str, str]:
    result = {}
    for member in MEMBERS:
        prefix = f"/legislators/{member}"
        result[f"{member}:profile"] = prefix + "/profile"
        result[f"{member}:contact"] = prefix + "/contact"
        result[f"{member}:positions"] = prefix + f"/positions?scope={scope}"
        result[f"{member}:editorial"] = prefix + f"/editorial-presentations?scope={scope}"
        for domain in DOMAINS:
            result[f"{member}:{domain}"] = prefix + f"/positions/{domain}/evidence?scope={scope}"
    return result


def index(rows: object, field: str) -> dict:
    require(isinstance(rows, list), f"{field} rows must be a list")
    result = {}
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get(field), str), f"Invalid {field} row")
        require(row[field] not in result, f"Duplicate {field}: {row[field]}")
        result[row[field]] = row
    return result


def identity(payload: dict, member: str, scope: str | None = None) -> None:
    require(payload.get("legislator_id") == member, "Response member differs")
    if scope is not None:
        require(payload.get("scope") == scope, "Response scope differs")


def findings(presentation: dict) -> set[str]:
    result = set()
    for field in ("repeated_patterns", "policy_trajectories", "syntheses", "notable_choices"):
        rows = presentation.get(field, [])
        require(isinstance(rows, list), f"Invalid {field}")
        for row in rows:
            require(isinstance(row, dict), f"Invalid {field} item")
            # Public supporting IDs are the selector's explicit public boundary.
            values = row.get("public_supporting_action_ids", row.get("action_ids", []))
            require(isinstance(values, list) and all(isinstance(v, str) for v in values),
                    f"Invalid {field} action IDs")
            result.update(values)
    return result


def inspect_member(member: str, scope: str, captures: dict) -> dict:
    errors = []

    def read(resource, check):
        captured = captures[f"{member}:{resource}"]
        if captured["status"] != "observed":
            errors.append({"resource": resource, "error": captured["error"]})
            return None
        try:
            return check(captured["body"])
        except (SmokeFailure, KeyError, TypeError, ValueError) as exc:
            errors.append({"resource": resource, "error": str(exc)})
            return None

    def profile(payload):
        require(payload.get("id") == member, "Profile member differs")
        require(bool(payload.get("name_display")), "Profile name missing")
        return {key: payload.get(key) for key in ("id", "name_display", "bioguide_id", "chamber", "state", "district", "party")}

    def contact(payload):
        identity(payload, member)
        require(payload.get("contact_status") in ("loaded", "not_loaded"), "Unknown contact status")
        return {"status": payload["contact_status"],
                "has_phone": bool(payload.get("phone")),
                "has_official_website": bool(payload.get("official_website_url")),
                "has_contact_form": bool(payload.get("contact_form_url")),
                "source_retrieved_at": payload.get("source_retrieved_at")}

    def rows(payload, key, field):
        identity(payload, member, scope)
        result = index(payload.get(key), field)
        require(set(result) == set(DOMAINS), f"{key} must cover the eight established issue domains")
        return result

    result = {"member_id": member, "profile": read("profile", profile),
              "contact": read("contact", contact), "issues": [], "errors": errors}
    positions = read("positions", lambda p: rows(p, "positions", "domain"))
    editorial = read("editorial", lambda p: rows(p, "presentations", "issue_id"))
    for domain in DOMAINS:
        def evidence(payload):
            identity(payload, member, scope)
            require(payload.get("domain") == domain, "Evidence issue differs")
            value = payload.get("evidence")
            require(isinstance(value, list) and all(isinstance(row, dict) for row in value), "Evidence must be a list of objects")
            return value
        receipts = read(domain, evidence)
        row = {"domain": domain, "recorded_actions": None, "receipt_rows": None,
               "publication_tier": None, "reviewed_scope": None,
               "linked_finding_actions": None, "missing_linked_receipts": None}
        if positions is not None:
            total = positions[domain].get("total_votes")
            if type(total) is int and total >= 0:
                row["recorded_actions"] = total
            else:
                errors.append({"resource": domain, "error": "Invalid recorded-action count"})
        if editorial is not None:
            presentation = editorial[domain]
            row["publication_tier"] = presentation.get("tier")
            row["reviewed_scope"] = presentation.get("reviewed_scope")
            if row["publication_tier"] not in ("receipts_only", "reviewed_conclusion"):
                errors.append({"resource": domain, "error": "Unknown publication tier"})
            try:
                linked = findings(presentation)
                row["linked_finding_actions"] = len(linked)
                if receipts is not None:
                    supplied = {r.get("canonical_action_id") for r in receipts}
                    row["missing_linked_receipts"] = sorted(linked - supplied)
                    if row["missing_linked_receipts"]:
                        errors.append({"resource": domain, "error": "Published finding actions lack exact canonical receipts"})
            except (SmokeFailure, KeyError, TypeError, ValueError) as exc:
                errors.append({"resource": domain, "error": str(exc)})
        if receipts is not None:
            row["receipt_rows"] = len(receipts)
            row["receipt_count_matches_positions"] = (None if row["recorded_actions"] is None else len(receipts) == row["recorded_actions"])
            # Diagnostics only. Do not rewrite eligibility, direction, or readiness.
            row["positions_seen"] = sorted({str(r.get("position")) for r in receipts})
            row["receipts_without_source_url"] = sum(not r.get("source_url") for r in receipts)
            row["receipts_without_canonical_id"] = sum(not r.get("canonical_action_id") for r in receipts)
            ids = [r["canonical_action_id"] for r in receipts if isinstance(r.get("canonical_action_id"), str)]
            row["duplicate_canonical_ids"] = sorted({value for value in ids if ids.count(value) > 1})
        result["issues"].append(row)
    return result


def collect(base: str, scope: str, timeout: float = 30, fetch=get_json) -> dict:
    report = {"schema_version": "pilot_slice_inventory_v1", "status": "incomplete",
              "api_base_url": base, "scope": scope,
              "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "limits": list(LIMITS), "requests": {}, "errors": [], "members": []}

    def capture(item):
        name, path = item
        metadata = {"path": path, "status": "failed"}
        try:
            payload = fetch(base, path, timeout)
            require(isinstance(payload, dict), "Response must be an object")
            raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
            metadata.update(status="observed", canonical_json_sha256=hashlib.sha256(raw).hexdigest(), canonical_json_bytes=len(raw))
            return name, {**metadata, "body": payload}
        except (SmokeFailure, ValueError, TypeError, OSError) as exc:
            return name, {**metadata, "error": str(exc)}

    _, before = capture(("health-before", "/health"))
    try:
        require(before["status"] == "observed", before.get("error", "Health unavailable"))
        report["deployed_commit"] = check_health(before["body"], None)
    except SmokeFailure as exc:
        report["errors"].append(str(exc))
    # Four concurrent GETs at most; no retries, credentials, or fixture fallback.
    with ThreadPoolExecutor(max_workers=4) as pool:
        captures = dict(pool.map(capture, endpoints(scope).items()))
    _, after = capture(("health-after", "/health"))
    try:
        require(after["status"] == "observed", after.get("error", "Health unavailable"))
        commit = check_health(after["body"], None)
        require(commit == report.get("deployed_commit"), "Deployment changed or could not be bound across the capture")
    except SmokeFailure as exc:
        report["errors"].append(str(exc))
    report["members"] = [inspect_member(member, scope, captures) for member in MEMBERS]
    for name, value in {"health-before": before, **captures, "health-after": after}.items():
        report["requests"][name] = {key: val for key, val in value.items() if key != "body"}
    if not report["errors"] and not any(member["errors"] for member in report["members"]):
        report["status"] = "observed"
    report["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base-url", default="https://political-fingerprint.onrender.com")
    parser.add_argument("--scope", choices=("119", "118", "all"), default="119")
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    url = urlsplit(args.api_base_url)
    if url.scheme != "https" or not url.hostname or url.username or url.password or url.query or url.fragment:
        parser.error("API base must use HTTPS without credentials, query, or fragment")
    if not math.isfinite(args.timeout) or not 0 < args.timeout <= 120:
        parser.error("Timeout must be positive and at most 120 seconds")
    if args.output.exists():
        parser.error("Output already exists; choose a new capture path to preserve receipts")
    report = collect(args.api_base_url, args.scope, args.timeout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "output": str(args.output), "errors": report["errors"]}))
    return 0 if report["status"] == "observed" else 1


if __name__ == "__main__":
    sys.exit(main())
