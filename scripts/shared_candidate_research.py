"""Read-only queue and exact-URL governed-source lookup; no editorial decisions."""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import sealed_digest


def research_queue(universe, membership, *, session=None, start_roll=1, limit=20):
    """Include unfinished screening and controls lacking a governed review.

    Preserve inventory order and explicit dependencies. A procedural inventory
    label alone does not establish a completed governed membership review.
    """
    if limit < 1 or start_roll < 1:
        raise ValueError("queue bounds must be positive")
    reviewed = {r["action_id"] for r in membership["records"]}
    result = []
    for row in universe["candidate_dispositions"]:
        if session is not None and row["session"] != session:
            continue
        if row["roll"] < start_roll:
            continue
        if row["disposition"] != "source_unresolved" and row["action_id"] in reviewed:
            continue
        result.append({key: row[key] for key in (
            "action_id", "date", "measure", "question", "disposition", "review_progress"
        )} | {"has_membership_record": row["action_id"] in reviewed})
        if len(result) == limit:
            break
    return result


def governed_sources_at_url(capture, url):
    """Return all exact URL matches, preserving version/excerpt distinctions.

    A match is a reuse lead, not proof that an excerpt supports a new action.
    Changed governed bytes fail closed. No URL normalization or fuzzy matching
    substitutes another edition, version, amendment, or authority.
    """
    matches = []
    seen = set()
    for source in capture["sources"]:
        if source["source_id"] in seen:
            raise ValueError("duplicate source identity")
        seen.add(source["source_id"])
        if source.get("url") != url:
            continue
        if sealed_digest(source, "governed_bytes_sha256") != source["governed_bytes_sha256"]:
            raise ValueError(f"governed source changed: {source['source_id']}")
        matches.append(source)
    return matches


def queue_table(rows):
    """Compact research display; keep the JSON queue available for full receipts."""
    out = io.StringIO(newline="")
    writer = csv.writer(out, delimiter="\t", lineterminator="\n")
    progress = ("substantive_review_performed", "exact_action_binding_unresolved",
                "required_evidence_unavailable", "authoritative_source_conflict")
    fields = ("action_id", "date", "measure", "question", "disposition")
    writer.writerow((*fields, "has_membership_record", *progress))
    for row in rows:
        writer.writerow((*[row[k] for k in fields], row["has_membership_record"],
                         *[row["review_progress"][k] for k in progress]))
    return out.getvalue().rstrip("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    queue = commands.add_parser("queue")
    queue.add_argument("--session", type=int, choices=[1, 2])
    queue.add_argument("--start-roll", type=int, default=1)
    queue.add_argument("--limit", type=int, default=20)
    queue.add_argument("--compact", action="store_true", help="Tab-separated queue; JSON remains the default")
    source = commands.add_parser("source")
    source.add_argument("--url", action="append", required=True)
    source.add_argument("--show-text", action="store_true")
    args = parser.parse_args()
    def read(name):
        return json.loads((args.input / f"{name}.json").read_text(encoding="utf-8"))
    if args.command == "queue":
        result = research_queue(read("universe_proposal"), read("membership_review"),
                                session=args.session, start_roll=args.start_roll, limit=args.limit)
        if args.compact:
            print(queue_table(result))
            return
    else:
        capture = read("sources")
        result = []
        for url in args.url:
            matches = governed_sources_at_url(capture, url)
            result.append({"url": url, "reuse_requires_material_support_review": True,
                           "sources": [s if args.show_text else {
                               k: s[k] for k in ("source_id", "source_type", "text_version",
                                                "raw_sha256", "governed_bytes_sha256")
                           } | {"text_characters": len(s.get("text", ""))} for s in matches]})
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
