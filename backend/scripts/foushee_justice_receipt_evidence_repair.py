"""Exact fact-only repair operator for eight missing Foushee governed receipts.

Preparation and preflight are read-only. Production write modes require a
content-bound bundle digest and an explicit production confirmation flag.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.editorial_artifacts.bundle import semantic_hash  # noqa: E402
from app.etl.house_clerk_adapter import load_house_clerk_bundle  # noqa: E402
from app.etl.vote_context import build_vote_contexts  # noqa: E402
from psycopg.types.json import Jsonb  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from scripts.editorial_artifact_store import (  # noqa: E402
    StoreSafetyError,
    _connect,
    target_info,
)


MEMBER_BIOGUIDE_ID = "F000477"
ISSUE_ID = "JUSTICE_PUBLIC_SAFETY"
LOCK_KEY = "foushee_justice_receipt_evidence_repair_v1"
EXPECTED_ACTIONS = {
    "house:119:2:227": "yea",
    "house:119:2:234": "yea",
    "house:119:2:240": "nay",
    "house:119:2:259": "nay",
    "house:119:2:265": "nay",
    "house:119:2:273": "nay",
    "house:119:2:275": "nay",
    "house:119:2:278": "nay",
}
EXPECTED_SOURCE_SHA256 = {
    "roll227.xml": "ca3748fac2dafceecb690e61ca4d09345872ac26296ffb214438e012c127669b",
    "roll234.xml": "31be3c2f95e9869c95230e3d51c54c4477fb28cc0e86409442a3485f901d287e",
    "roll240.xml": "0947b0014b41aa36e21bea99d91deeca220b7349e5ba7f3381e4098d7bb1ced9",
    "roll259.xml": "ab51ade3ec96483c519c9640e5c936cbf292dd5e1d4235f80419a7604f3e89e2",
    "roll265.xml": "baceb48520bd60338c3163fefa738baa5d0749da25c20375e1a1048a07dd02e9",
    "roll273.xml": "6549ec1f36b0897cafdb4e67e6d860403f1d2f1514816654e9a31dd1d59eda21",
    "roll275.xml": "ad07cb974f5d2b14f3ccb22866392107a27d8a84eaafd4b3bbc65092674c5968",
    "roll278.xml": "dad4d3b2a853d794e8d760a02c5cc04b8d5e6b19db019ed2cc12cb3a797d175a",
}
WRITE_CAPS = {
    "bills": 4,
    "roll_calls": 8,
    "votes_cast": 8,
    "vote_contexts": 8,
    "vote_classifications": 0,
    "vote_interpretations": 0,
    "editorial_artifacts": 0,
    "publication_registry": 0,
    "updates": 0,
    "deletes": 0,
}
CONTEXT_FIELDS = (
    "chamber_session",
    "vote_type",
    "member_position",
    "final_result",
    "vote_margin",
    "winning_position",
    "party_vote_totals",
    "member_party",
    "member_party_majority_position",
    "member_voted_with_party_majority",
    "member_voted_with_winning_side",
    "bipartisan_majority",
    "sponsor_party",
    "context_source_list",
    "context_version",
)

load_dotenv(BACKEND / ".env")


def _jsonable(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _digest(body: dict[str, Any]) -> str:
    return semantic_hash({key: value for key, value in body.items() if key != "bundle_sha256"})


def _action_id(row: dict[str, Any]) -> str:
    return (
        f"{str(row['chamber']).lower()}:{int(row['congress'])}:"
        f"{int(row['session'])}:{int(row['rollcall_number'])}"
    )


def _bill_key_from_ref(value: str) -> tuple[int, str, int]:
    _, congress, bill_type, bill_number = value.split("_")
    return int(congress), bill_type, int(bill_number)


def _bill_identity(congress: Any, bill_type: Any, bill_number: Any) -> str:
    return f"{int(congress)}:{str(bill_type)}:{int(bill_number)}"


def _semantic_vote_date(value: Any) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc).isoformat()
    parsed = datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _source_facts(source_dir: Path) -> dict[str, Any]:
    source_records = []
    for filename, expected_digest in EXPECTED_SOURCE_SHA256.items():
        path = source_dir / filename
        if not path.is_file():
            raise StoreSafetyError(f"missing exact official source: {filename}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected_digest:
            raise StoreSafetyError(f"official source digest mismatch: {filename}")
        source_records.append({"filename": filename, "sha256": digest})
    if not (source_dir / "members.xml").is_file():
        raise StoreSafetyError("official House member roster is missing")

    parsed = load_house_clerk_bundle(source_dir=source_dir)
    roll_calls = sorted(parsed.roll_calls, key=lambda row: int(row["rollcall_number"]))
    if {_action_id(row) for row in roll_calls} != set(EXPECTED_ACTIONS):
        raise StoreSafetyError("source roll-call universe differs from the exact repair set")
    member = next(
        (row for row in parsed.legislators if row["bioguide_id"] == MEMBER_BIOGUIDE_ID),
        None,
    )
    if member is None:
        raise StoreSafetyError("official roster lacks Valerie Foushee")
    member_votes = {
        str(row["roll_call_id"]): row
        for row in parsed.votes_cast
        if row["legislator_id"] == member["id"]
    }
    contexts = {
        str(row["roll_call_id"]): row
        for row in build_vote_contexts(
            legislators=parsed.legislators,
            roll_calls=parsed.roll_calls,
            votes_cast=parsed.votes_cast,
        )
        if row["legislator_id"] == member["id"]
    }
    votes = []
    selected_contexts = []
    for roll_call in roll_calls:
        action_id = _action_id(roll_call)
        vote = member_votes.get(str(roll_call["id"]))
        context = contexts.get(str(roll_call["id"]))
        if vote is None or context is None:
            raise StoreSafetyError(f"{action_id}: official Foushee vote/context is missing")
        if vote["position"] != EXPECTED_ACTIONS[action_id]:
            raise StoreSafetyError(f"{action_id}: official member action differs from approved receipt")
        votes.append({"action_id": action_id, "position": vote["position"]})
        selected_contexts.append({"action_id": action_id, **_jsonable(context)})

    bills_by_key = {
        _bill_key_from_ref(str(row["id"])): _jsonable(row) for row in parsed.bills
    }
    referenced_keys = {_bill_key_from_ref(str(row["bill_ref"])) for row in roll_calls}
    if set(bills_by_key) != referenced_keys or len(bills_by_key) != WRITE_CAPS["bills"]:
        raise StoreSafetyError("exact repair does not resolve to four closed bill facts")
    return {
        "official_sources": source_records,
        "member_roster_sha256": hashlib.sha256((source_dir / "members.xml").read_bytes()).hexdigest(),
        "bills": [bills_by_key[key] for key in sorted(bills_by_key)],
        "roll_calls": [_jsonable(row) for row in roll_calls],
        "votes_cast": votes,
        "vote_contexts": selected_contexts,
    }


def _publication_guard(conn: Any) -> dict[str, Any]:
    artifact = conn.execute(
        """SELECT artifact_id,natural_key,artifact_version,content_sha256
             FROM editorial_artifact_versions WHERE artifact_id=221"""
    ).fetchone()
    registry = conn.execute(
        """SELECT member_bioguide_id,issue_id,artifact_id,publicly_active,
                  publication_metadata_jsonb
             FROM editorial_publication_registry
            WHERE member_bioguide_id=%s AND issue_id=%s""",
        (MEMBER_BIOGUIDE_ID, ISSUE_ID),
    ).fetchone()
    if artifact is None or registry is None or int(registry["artifact_id"]) != 221:
        raise StoreSafetyError("artifact 221 or its active publication registry binding differs")
    payload = {"artifact": _jsonable(dict(artifact)), "registry": _jsonable(dict(registry))}
    return {"rows": payload, "sha256": semantic_hash(payload)}


def _target_state(conn: Any) -> dict[str, Any]:
    identities = [tuple(action.split(":")) for action in sorted(EXPECTED_ACTIONS)]
    roll_numbers = [int(identity[3]) for identity in identities]
    legislator = conn.execute(
        "SELECT id FROM legislators WHERE bioguide_id=%s", (MEMBER_BIOGUIDE_ID,)
    ).fetchone()
    if legislator is None:
        raise StoreSafetyError("production lacks the exact Foushee legislator identity")
    legislator_id = int(legislator["id"])
    bills = [
        _jsonable(dict(row))
        for row in conn.execute(
            """SELECT congress,bill_type,bill_number,title,summary,committee,subjects
                 FROM bills
                WHERE congress=119 AND bill_type='hr'
                  AND bill_number=ANY(%s)
                ORDER BY bill_number""",
            ([1181, 2478, 3106, 8800],),
        ).fetchall()
    ]
    rolls = [
        _jsonable(dict(row))
        for row in conn.execute(
            """SELECT r.id,r.chamber,r.congress,r.session,r.rollcall_number,r.vote_date,
                      r.question,r.description,r.bill_id,r.source_url,
                      b.congress AS bill_congress,b.bill_type AS bill_type,
                      b.bill_number AS bill_number
                 FROM roll_calls r
                 LEFT JOIN bills b ON b.id=r.bill_id
                WHERE r.chamber='house' AND r.congress=119 AND r.session=2
                  AND r.rollcall_number=ANY(%s)
                ORDER BY r.rollcall_number""",
            (roll_numbers,),
        ).fetchall()
    ]
    roll_ids = [int(row["id"]) for row in rolls]
    def rows(query: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        return [_jsonable(dict(row)) for row in conn.execute(query, params).fetchall()]
    votes = rows(
        """SELECT roll_call_id,legislator_id,position FROM votes_cast
             WHERE legislator_id=%s AND roll_call_id=ANY(%s) ORDER BY roll_call_id""",
        (legislator_id, roll_ids),
    ) if roll_ids else []
    contexts = rows(
        """SELECT roll_call_id,legislator_id,chamber_session,vote_type,member_position,
                  final_result,vote_margin,winning_position,party_vote_totals,member_party,
                  member_party_majority_position,member_voted_with_party_majority,
                  member_voted_with_winning_side,bipartisan_majority,sponsor_party,
                  context_source_list,context_version
             FROM vote_contexts WHERE legislator_id=%s AND roll_call_id=ANY(%s)
             ORDER BY roll_call_id""",
        (legislator_id, roll_ids),
    ) if roll_ids else []
    classifications = rows(
        "SELECT roll_call_id FROM vote_classifications WHERE roll_call_id=ANY(%s)",
        (roll_ids,),
    ) if roll_ids else []
    interpretations = rows(
        "SELECT roll_call_id FROM vote_interpretations WHERE roll_call_id=ANY(%s)",
        (roll_ids,),
    ) if roll_ids else []
    state = {
        "legislator_id": legislator_id,
        "bills": bills,
        "roll_calls": rolls,
        "votes_cast": votes,
        "vote_contexts": contexts,
        "vote_classifications": classifications,
        "vote_interpretations": interpretations,
    }
    return {"rows": state, "sha256": semantic_hash(state)}


def prepare(conn: Any, source_dir: Path) -> dict[str, Any]:
    facts = _source_facts(source_dir)
    baseline = _target_state(conn)
    if any(baseline["rows"][key] for key in (
        "bills", "roll_calls", "votes_cast", "vote_contexts",
        "vote_classifications", "vote_interpretations",
    )):
        raise StoreSafetyError("exact production repair baseline is no longer empty")
    bundle = {
        "schema_version": "foushee_justice_receipt_evidence_repair_bundle_v1",
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "member_bioguide_id": MEMBER_BIOGUIDE_ID,
        "issue_id": ISSUE_ID,
        "canonical_action_ids": sorted(EXPECTED_ACTIONS),
        "facts": facts,
        "expected_baseline": baseline,
        "publication_guard": _publication_guard(conn),
        "write_caps": WRITE_CAPS,
    }
    bundle["bundle_sha256"] = _digest(bundle)
    return bundle


def validate_bundle(bundle: dict[str, Any]) -> None:
    if bundle.get("schema_version") != "foushee_justice_receipt_evidence_repair_bundle_v1":
        raise StoreSafetyError("repair bundle schema is not exact")
    if bundle.get("bundle_sha256") != _digest(bundle):
        raise StoreSafetyError("repair bundle digest mismatch")
    if bundle.get("canonical_action_ids") != sorted(EXPECTED_ACTIONS):
        raise StoreSafetyError("repair bundle action universe differs")
    if bundle.get("write_caps") != WRITE_CAPS:
        raise StoreSafetyError("repair bundle write caps differ")
    facts = bundle.get("facts") or {}
    if [row["filename"] for row in facts.get("official_sources", [])] != list(EXPECTED_SOURCE_SHA256):
        raise StoreSafetyError("repair bundle official source set differs")
    if any(EXPECTED_SOURCE_SHA256[row["filename"]] != row["sha256"] for row in facts["official_sources"]):
        raise StoreSafetyError("repair bundle official source digest differs")
    if not (
        len(facts.get("bills", [])) == 4
        and len(facts.get("roll_calls", [])) == 8
        and len(facts.get("votes_cast", [])) == 8
        and len(facts.get("vote_contexts", [])) == 8
    ):
        raise StoreSafetyError("repair bundle fact counts differ")


def preflight(conn: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    validate_bundle(bundle)
    publication = _publication_guard(conn)
    if publication["sha256"] != bundle["publication_guard"]["sha256"]:
        raise StoreSafetyError("artifact 221 or publication registry drifted")
    state = _target_state(conn)
    already_applied = _matches_post_state(state, bundle)
    if not already_applied and state["sha256"] != bundle["expected_baseline"]["sha256"]:
        raise StoreSafetyError("exact fact-table baseline fingerprint drifted")
    return {
        "read_only": True,
        "already_applied": already_applied,
        "target_state_sha256": state["sha256"],
        "publication_guard_sha256": publication["sha256"],
        "write_caps": bundle["write_caps"],
    }


def _matches_post_state(state: dict[str, Any], bundle: dict[str, Any]) -> bool:
    return _actual_semantic_post_state(state) == _expected_semantic_post_state(bundle)


def _expected_semantic_post_state(bundle: dict[str, Any]) -> dict[str, Any]:
    facts = bundle["facts"]
    bills = [
        {
            "bill_identity": _bill_identity(
                bill["congress"], bill["bill_type"], bill["bill_number"]
            ),
            "congress": int(bill["congress"]),
            "bill_type": str(bill["bill_type"]),
            "bill_number": int(bill["bill_number"]),
            "title": bill["title"],
            "summary": bill.get("summary") or "",
            "committee": bill.get("committee"),
            "subjects": _jsonable(bill.get("subjects") or []),
        }
        for bill in facts["bills"]
    ]
    rolls = [
        {
            "action_id": _action_id(roll),
            "chamber": str(roll["chamber"]),
            "congress": int(roll["congress"]),
            "session": int(roll["session"]),
            "rollcall_number": int(roll["rollcall_number"]),
            "vote_date": _semantic_vote_date(roll["vote_date"]),
            "question": roll["question"],
            "description": roll["description"],
            "bill_identity": _bill_identity(*_bill_key_from_ref(roll["bill_ref"])),
            "source_url": roll["source_url"],
        }
        for roll in facts["roll_calls"]
    ]
    votes = [
        {
            "action_id": vote["action_id"],
            "member_bioguide_id": MEMBER_BIOGUIDE_ID,
            "position": vote["position"],
        }
        for vote in facts["votes_cast"]
    ]
    contexts = [
        {
            "action_id": context["action_id"],
            "member_bioguide_id": MEMBER_BIOGUIDE_ID,
            **{field: _jsonable(context[field]) for field in CONTEXT_FIELDS},
        }
        for context in facts["vote_contexts"]
    ]
    return {
        "bills": sorted(bills, key=lambda row: row["bill_identity"]),
        "roll_calls": sorted(rolls, key=lambda row: row["action_id"]),
        "votes_cast": sorted(votes, key=lambda row: row["action_id"]),
        "vote_contexts": sorted(contexts, key=lambda row: row["action_id"]),
        "vote_classifications": [],
        "vote_interpretations": [],
    }


def _actual_semantic_post_state(state: dict[str, Any]) -> dict[str, Any]:
    rows = state["rows"]
    roll_actions = {
        int(roll["id"]): _action_id(roll) for roll in rows["roll_calls"]
    }
    bills = [
        {
            "bill_identity": _bill_identity(
                bill["congress"], bill["bill_type"], bill["bill_number"]
            ),
            "congress": int(bill["congress"]),
            "bill_type": str(bill["bill_type"]),
            "bill_number": int(bill["bill_number"]),
            "title": bill["title"],
            "summary": bill["summary"],
            "committee": bill["committee"],
            "subjects": _jsonable(bill["subjects"]),
        }
        for bill in rows["bills"]
    ]
    rolls = [
        {
            "action_id": _action_id(roll),
            "chamber": str(roll["chamber"]),
            "congress": int(roll["congress"]),
            "session": int(roll["session"]),
            "rollcall_number": int(roll["rollcall_number"]),
            "vote_date": _semantic_vote_date(roll["vote_date"]),
            "question": roll["question"],
            "description": roll["description"],
            "bill_identity": (
                _bill_identity(
                    roll["bill_congress"], roll["bill_type"], roll["bill_number"]
                )
                if roll["bill_id"] is not None
                and roll["bill_congress"] is not None
                and roll["bill_type"] is not None
                and roll["bill_number"] is not None
                else None
            ),
            "source_url": roll["source_url"],
        }
        for roll in rows["roll_calls"]
    ]
    votes = [
        {
            "action_id": roll_actions.get(int(vote["roll_call_id"])),
            "member_bioguide_id": MEMBER_BIOGUIDE_ID,
            "position": vote["position"],
        }
        for vote in rows["votes_cast"]
    ]
    contexts = [
        {
            "action_id": roll_actions.get(int(context["roll_call_id"])),
            "member_bioguide_id": MEMBER_BIOGUIDE_ID,
            **{field: _jsonable(context[field]) for field in CONTEXT_FIELDS},
        }
        for context in rows["vote_contexts"]
    ]
    return {
        "bills": sorted(bills, key=lambda row: row["bill_identity"]),
        "roll_calls": sorted(rolls, key=lambda row: row["action_id"]),
        "votes_cast": sorted(votes, key=lambda row: str(row["action_id"])),
        "vote_contexts": sorted(contexts, key=lambda row: str(row["action_id"])),
        "vote_classifications": _jsonable(rows["vote_classifications"]),
        "vote_interpretations": _jsonable(rows["vote_interpretations"]),
    }


def apply(conn: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    check = preflight(conn, bundle)
    if check["already_applied"]:
        return {**check, "writes": {key: 0 for key in WRITE_CAPS}, "already_applied": True}
    facts = bundle["facts"]
    inserted = {key: 0 for key in WRITE_CAPS}
    bill_ids: dict[tuple[int, str, int], int] = {}
    for bill in facts["bills"]:
        row = conn.execute(
            """INSERT INTO bills
                   (congress,bill_type,bill_number,title,summary,committee,subjects)
                 VALUES (%s,%s,%s,%s,%s,%s,%s)
                 RETURNING id""",
            (
                bill["congress"], bill["bill_type"], bill["bill_number"], bill["title"],
                bill.get("summary") or "", bill.get("committee"), Jsonb(bill.get("subjects") or []),
            ),
        ).fetchone()
        bill_ids[(int(bill["congress"]), str(bill["bill_type"]), int(bill["bill_number"]))] = int(row["id"])
        inserted["bills"] += 1
    roll_ids: dict[str, int] = {}
    for roll in facts["roll_calls"]:
        row = conn.execute(
            """INSERT INTO roll_calls
                   (chamber,congress,session,rollcall_number,vote_date,question,
                    description,bill_id,source_url)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (
                roll["chamber"], roll["congress"], roll["session"], roll["rollcall_number"],
                roll["vote_date"], roll["question"], roll["description"],
                bill_ids[_bill_key_from_ref(roll["bill_ref"])], roll["source_url"],
            ),
        ).fetchone()
        roll_ids[_action_id(roll)] = int(row["id"])
        inserted["roll_calls"] += 1
    legislator_id = int(bundle["expected_baseline"]["rows"]["legislator_id"])
    for vote in facts["votes_cast"]:
        conn.execute(
            "INSERT INTO votes_cast (roll_call_id,legislator_id,position) VALUES (%s,%s,%s)",
            (roll_ids[vote["action_id"]], legislator_id, vote["position"]),
        )
        inserted["votes_cast"] += 1
    for context in facts["vote_contexts"]:
        conn.execute(
            """INSERT INTO vote_contexts
                   (roll_call_id,legislator_id,chamber_session,vote_type,member_position,
                    final_result,vote_margin,winning_position,party_vote_totals,member_party,
                    member_party_majority_position,member_voted_with_party_majority,
                    member_voted_with_winning_side,bipartisan_majority,sponsor_party,
                    context_source_list,context_version)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                roll_ids[context["action_id"]], legislator_id, context["chamber_session"],
                context["vote_type"], context["member_position"], context["final_result"],
                context["vote_margin"], context["winning_position"], Jsonb(context["party_vote_totals"]),
                context["member_party"], context["member_party_majority_position"],
                context["member_voted_with_party_majority"], context["member_voted_with_winning_side"],
                context["bipartisan_majority"], context["sponsor_party"],
                Jsonb(context["context_source_list"]), context["context_version"],
            ),
        )
        inserted["vote_contexts"] += 1
    if inserted != WRITE_CAPS:
        raise StoreSafetyError(f"actual writes differ from exact caps: {inserted}")
    post = _target_state(conn)
    if not _matches_post_state(post, bundle):
        raise StoreSafetyError("post-write fact state does not match the exact repair")
    if _publication_guard(conn)["sha256"] != bundle["publication_guard"]["sha256"]:
        raise StoreSafetyError("editorial publication state changed during fact repair")
    return {"already_applied": False, "writes": inserted, "post_state_sha256": post["sha256"]}


def rollback(conn: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    validate_bundle(bundle)
    if _publication_guard(conn)["sha256"] != bundle["publication_guard"]["sha256"]:
        raise StoreSafetyError("artifact 221 or publication registry drifted before rollback")
    state = _target_state(conn)
    if not _matches_post_state(state, bundle):
        raise StoreSafetyError("rollback target does not exactly match the proven repair")
    roll_ids = [int(row["id"]) for row in state["rows"]["roll_calls"]]
    legislator_id = int(state["rows"]["legislator_id"])
    deleted = {}
    deleted["vote_contexts"] = conn.execute(
        "DELETE FROM vote_contexts WHERE legislator_id=%s AND roll_call_id=ANY(%s)",
        (legislator_id, roll_ids),
    ).rowcount
    deleted["votes_cast"] = conn.execute(
        "DELETE FROM votes_cast WHERE legislator_id=%s AND roll_call_id=ANY(%s)",
        (legislator_id, roll_ids),
    ).rowcount
    deleted["roll_calls"] = conn.execute(
        "DELETE FROM roll_calls WHERE id=ANY(%s)", (roll_ids,)
    ).rowcount
    deleted["bills"] = conn.execute(
        "DELETE FROM bills WHERE congress=119 AND bill_type='hr' AND bill_number=ANY(%s)",
        ([1181, 2478, 3106, 8800],),
    ).rowcount
    if deleted != {"bills": 4, "roll_calls": 8, "votes_cast": 8, "vote_contexts": 8}:
        raise StoreSafetyError(f"rollback deletes differ from exact repair: {deleted}")
    if _target_state(conn)["sha256"] != bundle["expected_baseline"]["sha256"]:
        raise StoreSafetyError("rollback did not restore exact fact baseline")
    if _publication_guard(conn)["sha256"] != bundle["publication_guard"]["sha256"]:
        raise StoreSafetyError("editorial publication state changed during rollback")
    return {"deleted": deleted, "restored_baseline": True}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, body: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "preflight", "dry-run", "apply", "postcheck", "rollback"))
    parser.add_argument("--target", choices=("disposable", "production"), default="disposable")
    parser.add_argument("--database-url")
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--bundle-path", type=Path, required=True)
    parser.add_argument("--confirm-bundle-digest")
    parser.add_argument("--confirm-production-repair", action="store_true")
    parser.add_argument("--confirm-production-rollback", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    db_url = args.database_url or (
        os.getenv("DATABASE_URL") if args.target == "production"
        else os.getenv("EDITORIAL_DISPOSABLE_DATABASE_URL")
    )
    if not db_url:
        raise StoreSafetyError("an explicit database URL is required")
    target_info(db_url, args.target, None)
    if args.mode == "prepare":
        if args.source_dir is None:
            raise StoreSafetyError("prepare requires --source-dir")
        with _connect(db_url, autocommit=True) as conn:
            conn.execute("SET default_transaction_read_only=on")
            with conn.transaction():
                conn.execute("SET TRANSACTION READ ONLY")
                result = prepare(conn, args.source_dir)
        _write(args.bundle_path, result)
        print(json.dumps({"bundle_sha256": result["bundle_sha256"], "path": str(args.bundle_path.resolve())}, indent=2))
        return 0
    bundle = _load(args.bundle_path)
    validate_bundle(bundle)
    if args.mode in {"dry-run", "apply", "rollback"} and args.confirm_bundle_digest != bundle["bundle_sha256"]:
        raise StoreSafetyError("write mode requires exact bundle digest confirmation")
    if args.target == "production" and args.mode in {"dry-run", "apply"} and not args.confirm_production_repair:
        raise StoreSafetyError("production fact repair lacks explicit authorization flag")
    if args.target == "production" and args.mode == "rollback" and not args.confirm_production_rollback:
        raise StoreSafetyError("production repair rollback lacks explicit authorization flag")
    read_only = args.mode in {"preflight", "postcheck"}
    with _connect(db_url, autocommit=read_only) as conn:
        if read_only:
            conn.execute("SET default_transaction_read_only=on")
        with conn.transaction(force_rollback=args.mode == "dry-run"):
            conn.execute("SET LOCAL lock_timeout='10000ms'")
            conn.execute("SET LOCAL statement_timeout='120000ms'")
            if read_only:
                conn.execute("SET TRANSACTION READ ONLY")
            else:
                conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (LOCK_KEY,))
            if args.mode in {"preflight", "postcheck"}:
                result = preflight(conn, bundle)
            elif args.mode in {"dry-run", "apply"}:
                result = apply(conn, bundle)
            else:
                result = rollback(conn, bundle)
    print(json.dumps(_jsonable(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
