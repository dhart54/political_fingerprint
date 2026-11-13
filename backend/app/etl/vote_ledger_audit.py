"""Read-only raw-source/member-vote reconciliation. Never an import plan."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET


POSITIONS = {"yea": "yea", "aye": "yea", "nay": "nay", "no": "nay",
             "present": "present", "not voting": "not_voting", "not_voting": "not_voting"}
BIOGUIDE = re.compile(r"[A-Z][0-9]{6}")


@dataclass(frozen=True)
class Scope:
    chamber: str
    congress: int
    session: int
    first_roll: int
    last_roll: int

    def __post_init__(self):
        if (self.chamber not in {"house", "senate"} or self.congress < 1
                or self.session not in {1, 2} or not 1 <= self.first_roll <= self.last_roll
                or self.last_roll - self.first_roll >= 2000):
            raise ValueError("Scope requires a chamber, positive Congress, session 1/2 and at most 2000 rolls.")

    def key(self, number):
        return (self.chamber, self.congress, self.session, number)


def _text(node, path):
    return (node.findtext(path) or "").strip()


def _session(value):
    if value in {"1", "1st"}:
        return 1
    if value in {"2", "2nd"}:
        return 2
    raise ValueError("Invalid source session")


def _read_xml(path):
    data = path.read_bytes()
    return ET.fromstring(data), {"file": str(path), "sha256": hashlib.sha256(data).hexdigest()}


def fetch_missing_sources(source_dir, scope):
    """Opt-in official-source collection. Reuse cache; stop at the first failure."""
    from app.etl.fetch_sources import fetch_house_clerk_roll_calls, fetch_senate_vote_files

    receipts = []
    for number in range(scope.first_roll, scope.last_roll + 1):
        try:
            if scope.chamber == "house":
                results = fetch_house_clerk_roll_calls(
                    year=1789 + 2 * (scope.congress - 1) + scope.session - 1,
                    roll_numbers=[number], output_dir=source_dir, overwrite=False)
            else:
                results = fetch_senate_vote_files(
                    congress=scope.congress, session=scope.session,
                    roll_numbers=[number], output_dir=source_dir, overwrite=False)
            result = results[0]
            receipts.append({"roll_key": list(scope.key(number)), "url": result.source_url,
                             "file": str(result.destination), "bytes": result.bytes_written,
                             "status": "reused_cache" if result.skipped else "downloaded",
                             "checked_at": datetime.now(timezone.utc).isoformat()})
        except OSError as exc:
            receipts.append({"roll_key": list(scope.key(number)), "status": "failed",
                             "error": str(exc), "remaining_downloads_stopped": True})
            break
    return receipts


def load_senate_member_map(path):
    """Use explicit LIS/Bioguide identifiers, never names, current seats or guesses."""
    root, provenance = _read_xml(path)
    result = {}
    members = root.findall("./members/member") or root.findall("./senator")
    for member in members:
        lis = _text(member, "lis_member_id") or member.get("lis_member_id", "")
        bioguide = _text(member, "bioguide_id") or _text(member, "bioguideId")
        if not lis or not BIOGUIDE.fullmatch(bioguide):
            raise ValueError("Senate member mapping contains a missing or invalid identifier")
        if lis in result and result[lis] != bioguide:
            raise ValueError("Senate member mapping has conflicting LIS identities")
        result[lis] = bioguide
    if not result:
        raise ValueError("Senate member mapping is empty")
    return result, provenance


def read_source_roll(path, scope, number, senate_members):
    root, provenance = _read_xml(path)
    if scope.chamber == "house":
        if root.tag != "rollcall-vote":
            raise ValueError("Not House roll-call XML")
        metadata = root.find("vote-metadata")
        if metadata is None:
            raise ValueError("Missing vote metadata")
        key = ("house", int(_text(metadata, "congress")), _session(_text(metadata, "session")),
               int(_text(metadata, "rollcall-num")))
        members = root.findall("./vote-data/recorded-vote")
    else:
        if root.tag != "roll_call_vote":
            raise ValueError("Not Senate roll-call XML")
        key = ("senate", int(_text(root, "congress")), _session(_text(root, "session")),
               int(_text(root, "vote_number")))
        members = root.findall("./members/member")
    if key != scope.key(number):
        raise ValueError("Source identity does not match requested chamber/Congress/session/roll")
    if not members:
        raise ValueError("Source has no recorded member votes")
    votes, issues = {}, []
    lis_counts = Counter(_text(member, "lis_member_id") for member in members) if scope.chamber == "senate" else {}
    seen = set()
    recorded_totals = Counter()
    for index, member in enumerate(members, 1):
        if scope.chamber == "house":
            legislator = member.find("legislator")
            bioguide = "" if legislator is None else (legislator.get("bioguide-id") or legislator.get("name-id", ""))
            raw_position = _text(member, "vote")
            source_id = bioguide
            if (legislator is not None and legislator.get("bioguide-id") and legislator.get("name-id")
                    and legislator.get("bioguide-id") != legislator.get("name-id")):
                issues.append({"row": index, "reason": "conflicting_member_identity", "source_id": source_id})
                continue
        else:
            source_id = _text(member, "lis_member_id")
            if source_id and lis_counts[source_id] > 1:
                issues.append({"row": index, "reason": "duplicate_source_identity", "source_id": source_id})
                continue
            direct = _text(member, "bioguide_id")
            mapped = senate_members.get(source_id, "")
            if direct and mapped and direct != mapped:
                issues.append({"row": index, "reason": "conflicting_member_identity", "source_id": source_id})
                continue
            bioguide = direct or mapped
            raw_position = _text(member, "vote_cast")
        if not BIOGUIDE.fullmatch(bioguide):
            issues.append({"row": index, "reason": "unresolved_member_identity", "source_id": source_id})
            continue
        if bioguide in seen:
            issues.append({"row": index, "reason": "duplicate_member", "bioguide_id": bioguide})
            votes.pop(bioguide, None)
            continue
        seen.add(bioguide)
        position = POSITIONS.get(raw_position.lower())
        if position is None:
            issues.append({"row": index, "reason": "unsupported_position", "bioguide_id": bioguide,
                           "source_position": raw_position})
            continue
        votes[bioguide] = position
        recorded_totals[position] += 1
    totals_path = "vote-metadata/vote-totals/totals-by-vote" if scope.chamber == "house" else "count"
    totals = root.find(totals_path)
    published_totals = None
    if totals is not None:
        fields = ({"yea": "yea-total", "nay": "nay-total", "present": "present-total", "not_voting": "not-voting-total"}
                  if scope.chamber == "house" else {"yea": "yeas", "nay": "nays", "present": "present", "not_voting": "absent"})
        try:
            # Official Senate XML commonly emits <present/> (and sometimes
            # <absent/>) rather than a numeric zero. Preserve the unpublished
            # value as null; do not synthesize a tally from member positions.
            published_totals = {position: int(value) if (value := _text(totals, field)) else None
                                for position, field in fields.items()}
            if any(value is not None and value < 0 for value in published_totals.values()):
                raise ValueError("Negative source tally")
        except ValueError:
            issues.append({"reason": "invalid_source_totals"})
        else:
            if any(value is not None and recorded_totals[position] != value
                   for position, value in published_totals.items()):
                issues.append({"reason": "source_totals_mismatch"})
    return {**provenance, "votes": votes, "member_rows": len(members), "published_totals": published_totals,
            "issues": issues}


def _manifest_files(path, scope):
    data = path.read_bytes()
    manifest = json.loads(data)
    if manifest.get("scope") != asdict(scope):
        raise ValueError("Source manifest requires the exact requested scope")
    files = {}
    expected = {scope.key(number) for number in range(scope.first_roll, scope.last_roll + 1)}
    for row in manifest["files"]:
        key = tuple(row["roll_key"])
        digest = row["sha256"]
        if key not in expected or key[3] in files:
            raise ValueError("Duplicate or out-of-scope source manifest roll")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Source manifest requires a lowercase SHA256 for each file")
        files[key[3]] = (path.parent / row["file"], digest)
    return files, {"file": str(path), "sha256": hashlib.sha256(data).hexdigest()}


def load_sources(source_dir, scope, senate_member_file=None, *, source_manifest=None):
    if (source_dir is None) == (source_manifest is None):
        raise ValueError("Specify exactly one source directory or manifest")
    senate_members, mapping_provenance = {}, None
    if senate_member_file is not None:
        senate_members, mapping_provenance = load_senate_member_map(senate_member_file)
    files, manifest_provenance = _manifest_files(source_manifest, scope) if source_manifest else ({}, None)
    rolls, errors = {}, []
    for number in range(scope.first_roll, scope.last_roll + 1):
        if source_manifest:
            if number not in files:
                errors.append({"roll_key": list(scope.key(number)), "reason": "source_not_in_manifest"})
                continue
            path, digest = files[number]
        else:
            filename = f"roll{number:03d}.xml" if scope.chamber == "house" else f"vote_{number:03d}.xml"
            path, digest = source_dir / filename, None
        try:
            source = read_source_roll(path, scope, number, senate_members)
            if digest is not None and source["sha256"] != digest:
                raise ValueError("Source file does not match manifest hash")
            rolls[number] = source
        except (OSError, ET.ParseError, ValueError) as error:
            # Never fall back to samples, another session, or a stale alternate filename.
            errors.append({"roll_key": list(scope.key(number)), "file": str(path),
                           "reason": "source_unavailable_or_invalid", "error_type": type(error).__name__})
    return {"rolls": rolls, "errors": errors, "member_mapping": mapping_provenance,
            "source_manifest": manifest_provenance}


def load_database_snapshot(scope, connect=None):
    """One bounded repeatable-read snapshot; the database enforces read-only."""
    if connect is None:
        from app.db import get_connection
        connect = get_connection
    connection = connect()
    try:
        with connection.cursor() as cursor:
            # psycopg opens a transaction before the first execute. Configure that
            # transaction instead of issuing a nested BEGIN (which can be ignored).
            cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            cursor.execute("SET LOCAL statement_timeout = '30s'")
            cursor.execute("SET LOCAL lock_timeout = '3s'")
            cursor.execute("""SELECT transaction_timestamp(), current_setting('transaction_read_only'),
                              current_setting('transaction_isolation')""")
            captured_at, readonly, isolation = cursor.fetchone()
            if readonly != "on" or isolation != "repeatable read":
                raise ValueError("Read-only repeatable-read transaction was not established")
            cursor.execute("""
                SELECT rc.chamber::text, rc.congress, rc.session, rc.rollcall_number,
                       vc.legislator_id, l.bioguide_id, vc.position::text
                FROM roll_calls rc
                LEFT JOIN votes_cast vc ON vc.roll_call_id = rc.id
                LEFT JOIN legislators l ON l.id = vc.legislator_id
                WHERE rc.chamber::text = %s AND rc.congress = %s AND rc.session = %s
                  AND rc.rollcall_number BETWEEN %s AND %s
                ORDER BY rc.rollcall_number, vc.legislator_id
            """, (scope.chamber, scope.congress, scope.session, scope.first_roll, scope.last_roll))
            rolls, votes = set(), []
            for chamber, congress, session, number, legislator_id, bioguide, position in cursor.fetchall():
                key = [chamber, congress, session, number]
                rolls.add(tuple(key))
                if legislator_id is not None:
                    votes.append({"roll_key": key, "bioguide_id": bioguide, "position": position})
            return {"scope": asdict(scope), "captured_at": captured_at.isoformat(),
                    "rolls": [list(key) for key in sorted(rolls)], "votes": votes}
    finally:
        try:
            connection.rollback()
        finally:
            connection.close()


def _ledger_index(snapshot, scope):
    if snapshot.get("scope") != asdict(scope) or not snapshot.get("captured_at"):
        raise ValueError("Ledger snapshot requires the exact requested scope and capture timestamp")
    expected = {scope.key(number) for number in range(scope.first_roll, scope.last_roll + 1)}
    rolls = [tuple(key) for key in snapshot["rolls"]]
    if len(rolls) != len(set(rolls)) or not set(rolls) <= expected:
        raise ValueError("Duplicate or out-of-scope ledger roll")
    roll_set = set(rolls)
    result = {key[3]: {} for key in rolls}
    for row in snapshot["votes"]:
        key = tuple(row["roll_key"])
        bioguide, position = row["bioguide_id"], row["position"]
        if key not in roll_set:
            raise ValueError("Ledger vote has no in-scope roll")
        if not isinstance(bioguide, str) or not BIOGUIDE.fullmatch(bioguide):
            raise ValueError("Ledger vote has no valid Bioguide identity")
        if position not in {"yea", "nay", "present", "not_voting"}:
            raise ValueError("Ledger vote has unsupported position")
        if bioguide in result[key[3]]:
            raise ValueError("Duplicate ledger member pair")
        result[key[3]][bioguide] = position
    return result


def reconcile(scope, sources, snapshot):
    ledger = _ledger_index(snapshot, scope)
    counts = Counter()
    details = []
    for number, source in sorted(sources["rolls"].items()):
        expected, stored = source["votes"], ledger.get(number, {})
        counts["source_member_rows"] += source["member_rows"]
        counts["comparable_source_pairs"] += len(expected)
        if source["issues"]:
            counts["source_issue_rolls"] += 1
        if number not in ledger:
            counts["missing_rolls"] += 1
        missing = {member: position for member, position in sorted(expected.items()) if member not in stored}
        conflicts = [{"bioguide_id": member, "source_position": position, "ledger_position": stored[member]}
                     for member, position in sorted(expected.items())
                     if member in stored and stored[member] != position]
        # If any source identities/positions are unresolved, stored-only pairs are
        # unverified, not evidence that a member did not participate.
        stored_only = {member: position for member, position in sorted(stored.items()) if member not in expected}
        extra = {} if source["issues"] else stored_only
        unverified = stored_only if source["issues"] else {}
        counts["missing_pairs"] += len(missing)
        counts["missing_pairs_on_existing_rolls"] += len(missing) if number in ledger else 0
        counts["position_conflicts"] += len(conflicts)
        counts["ledger_only_pairs"] += len(extra)
        counts["unverified_ledger_pairs"] += len(unverified)
        counts["matched_pairs"] += sum(stored.get(member) == position for member, position in expected.items())
        if missing and number in ledger:
            counts["partial_rolls"] += 1
        details.append({"roll_key": list(scope.key(number)), "source": {k: v for k, v in source.items() if k != "votes"},
                        "ledger_roll_exists": number in ledger, "ledger_pair_count": len(stored),
                        "missing_pairs": missing, "position_conflicts": conflicts,
                        "ledger_only_pairs": extra, "unverified_ledger_pairs": unverified})
    unavailable = sorted(set(range(scope.first_roll, scope.last_roll + 1)) - set(sources["rolls"]))
    counts["unverified_ledger_pairs"] += sum(len(ledger.get(number, {})) for number in unavailable)
    summary_keys = ("source_member_rows", "comparable_source_pairs", "source_issue_rolls", "missing_rolls",
                    "missing_pairs", "missing_pairs_on_existing_rolls", "partial_rolls", "position_conflicts",
                    "ledger_only_pairs", "unverified_ledger_pairs", "matched_pairs")
    incomplete = bool(sources["errors"] or counts["source_issue_rolls"])
    differences = any(counts[key] for key in ("missing_rolls", "missing_pairs", "position_conflicts", "ledger_only_pairs"))
    return {"schema_version": "vote_ledger_audit_v1", "read_only": True, "scope": asdict(scope),
            "ledger_captured_at": snapshot["captured_at"],
            "status": "incomplete" if incomplete else "differences" if differences else "match",
            "source_coverage_complete": not incomplete,
            "summary": {"requested_rolls": scope.last_roll - scope.first_roll + 1,
                        "parsed_source_rolls": len(sources["rolls"]), "ledger_rolls": len(ledger),
                        **{key: counts[key] for key in summary_keys}},
            "member_mapping": sources["member_mapping"], "source_manifest": sources["source_manifest"],
            "source_errors": sources["errors"],
            "uncompared_rolls": [{"roll_key": list(scope.key(number)), "ledger_roll_exists": number in ledger,
                                  "ledger_pair_count": len(ledger.get(number, {}))} for number in unavailable],
            "rolls": details,
            "limits": ["Compared only supplied source bytes within the explicit roll range; no live-source freshness claim.",
                       "Fact reconciliation only, not eligibility, interpretation, service status, or approval to write.",
                       "Source issues make missing-pair counts partial; no member votes are inferred from rosters."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chamber", choices=("house", "senate"), required=True)
    for field in ("congress", "session", "first-roll", "last-roll"):
        parser.add_argument(f"--{field}", type=int, required=True)
    source_mode = parser.add_mutually_exclusive_group(required=True)
    source_mode.add_argument("--source-dir", type=Path)
    source_mode.add_argument("--source-manifest", type=Path)
    parser.add_argument("--fetch-missing", action="store_true",
                        help="Fetch missing official roll XML into --source-dir before auditing; never overwrite cache.")
    parser.add_argument("--senate-member-file", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--ledger-json", type=Path)
    mode.add_argument("--database", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    scope = Scope(args.chamber, args.congress, args.session, args.first_roll, args.last_roll)
    if args.fetch_missing and args.source_dir is None:
        parser.error("--fetch-missing requires --source-dir, not --source-manifest")
    if args.output.exists():
        raise FileExistsError(args.output)
    if args.ledger_json:
        data = args.ledger_json.read_bytes()
        snapshot = json.loads(data)
        ledger_input = {"file": str(args.ledger_json), "sha256": hashlib.sha256(data).hexdigest()}
    else:
        snapshot = load_database_snapshot(scope)
        ledger_input = {"mode": "database_read_only"}
    _ledger_index(snapshot, scope)  # Reject invalid replay input before making any network requests.
    collection = fetch_missing_sources(args.source_dir, scope) if args.fetch_missing else None
    sources = load_sources(args.source_dir, scope, args.senate_member_file, source_manifest=args.source_manifest)
    if collection and collection[-1]["status"] == "failed":
        sources["errors"].append({"reason": "source_collection_failed", **collection[-1]})
    report = reconcile(scope, sources, snapshot)
    report.update(generated_at=datetime.now(timezone.utc).isoformat(), ledger_input=ledger_input)
    if collection is not None:
        report["source_collection"] = collection
    # Exclusive creation prevents accidental overwrite of source files or prior receipts.
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "summary": report["summary"], "output": str(args.output)}, sort_keys=True))
    return {"match": 0, "differences": 1, "incomplete": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
