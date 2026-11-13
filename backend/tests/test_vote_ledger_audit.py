from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError
from xml.etree import ElementTree as ET

import pytest

from app.etl.vote_ledger_audit import (
    Scope, fetch_missing_sources, load_database_snapshot, load_sources, main, reconcile,
)


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
HOUSE = Scope("house", 119, 1, 1, 1)
SENATE = replace(HOUSE, chamber="senate")


def snapshot(scope=HOUSE, votes=None, rolls=None):
    return {"scope": asdict(scope), "captured_at": "2026-11-11T00:00:00+00:00",
            "rolls": [list(scope.key(1))] if rolls is None else rolls,
            "votes": [{"roll_key": list(scope.key(1)), "bioguide_id": member, "position": position}
                      for member, position in (votes or {}).items()]}


def house_sources(scope=HOUSE):
    return load_sources(FIXTURES / "house_clerk_sample", scope)


def report(scope=HOUSE, votes=None, rolls=None):
    return reconcile(scope, house_sources(scope), snapshot(scope, votes, rolls))


def write_house(tmp_path, edit=None):
    root = ET.parse(FIXTURES / "house_clerk_sample" / "roll001.xml").getroot()
    if edit:
        edit(root)
    ET.ElementTree(root).write(tmp_path / "roll001.xml")
    return load_sources(tmp_path, HOUSE)


def test_existing_roll_does_not_hide_missing_member_pairs():
    result = report(votes={"M000001": "yea"})
    assert result["status"] == "differences"
    assert result["summary"]["partial_rolls"] == 1
    assert result["summary"]["missing_rolls"] == 0
    assert result["summary"]["missing_pairs_on_existing_rolls"] == 2
    assert result["rolls"][0]["missing_pairs"] == {"P000012": "yea", "T000007": "nay"}


def test_missing_roll_is_distinct_from_partial_roll():
    result = report(rolls=[])
    assert result["summary"]["missing_rolls"] == 1
    assert result["summary"]["missing_pairs"] == 3
    assert result["summary"]["partial_rolls"] == 0


def test_empty_existing_roll_and_position_conflicts_and_ledger_only_pairs():
    assert report()["summary"]["partial_rolls"] == 1
    result = report(votes={"M000001": "nay", "P000012": "yea", "T000007": "nay", "A000001": "present"})
    assert result["summary"]["missing_pairs"] == 0
    assert result["summary"]["matched_pairs"] == 2
    assert result["rolls"][0]["position_conflicts"] == [
        {"bioguide_id": "M000001", "source_position": "yea", "ledger_position": "nay"}]
    assert result["rolls"][0]["ledger_only_pairs"] == {"A000001": "present"}


def test_exact_match_is_deterministic_and_compact():
    result = report(votes={"M000001": "yea", "P000012": "yea", "T000007": "nay"})
    assert result["status"] == "match"
    assert result["summary"]["matched_pairs"] == 3
    assert result == report(votes={"T000007": "nay", "P000012": "yea", "M000001": "yea"})
    assert "votes" not in result["rolls"][0]["source"]


@pytest.mark.parametrize("field,value", [("chamber", "senate"), ("congress", 118), ("session", 2)])
def test_identity_never_collides_across_chamber_congress_or_session(field, value):
    scope = replace(HOUSE, **{field: value})
    result = reconcile(scope, house_sources(scope), snapshot(scope))
    assert result["status"] == "incomplete"
    assert result["summary"]["missing_pairs"] == 0
    with pytest.raises(ValueError, match="exact requested scope"):
        reconcile(scope, house_sources(scope), snapshot())


def test_missing_xml_is_not_missing_ledger_and_never_uses_sample_fallback(tmp_path):
    result = reconcile(HOUSE, load_sources(tmp_path, HOUSE), snapshot(votes={"M000001": "yea"}))
    assert result["status"] == "incomplete"
    assert result["summary"]["missing_rolls"] == 0
    assert result["summary"]["unverified_ledger_pairs"] == 1
    assert result["uncompared_rolls"][0]["ledger_pair_count"] == 1


@pytest.mark.parametrize("contents", ["<broken", "<html>Access denied</html>", "<rollcall-vote/>"])
def test_malformed_or_empty_sources_fail_closed(tmp_path, contents):
    (tmp_path / "roll001.xml").write_text(contents)
    result = reconcile(HOUSE, load_sources(tmp_path, HOUSE), snapshot())
    assert result["status"] == "incomplete"
    assert result["summary"]["comparable_source_pairs"] == 0


def test_rolls_without_supported_bills_are_still_audited(tmp_path):
    sources = write_house(tmp_path, lambda root: root.find("vote-metadata").remove(root.find("vote-metadata/legis-num")))
    assert reconcile(HOUSE, sources, snapshot())["summary"]["missing_pairs"] == 3


@pytest.mark.parametrize("raw,expected", [("Aye", "yea"), ("No", "nay"), ("Present", "present"), ("Not Voting", "not_voting")])
def test_recorded_positions_preserve_nondirectional_statuses(tmp_path, raw, expected):
    sources = write_house(tmp_path, lambda root: setattr(root.find("vote-data/recorded-vote/vote"), "text", raw))
    assert sources["rolls"][1]["votes"]["M000001"] == expected


def test_unsupported_positions_are_unresolved_not_coerced(tmp_path):
    sources = write_house(tmp_path, lambda root: setattr(root.find("vote-data/recorded-vote/vote"), "text", "Speaker Candidate"))
    result = reconcile(HOUSE, sources, snapshot(votes={"M000001": "yea"}))
    assert result["status"] == "incomplete"
    assert result["rolls"][0]["source"]["issues"][0]["reason"] == "unsupported_position"
    assert result["rolls"][0]["ledger_only_pairs"] == {}
    assert result["rolls"][0]["unverified_ledger_pairs"] == {"M000001": "yea"}


def test_source_duplicates_are_not_silently_deduplicated(tmp_path):
    def duplicate(root):
        votes = root.find("vote-data")
        votes.append(ET.fromstring(ET.tostring(votes[0])))
    sources = write_house(tmp_path, duplicate)
    result = reconcile(HOUSE, sources, snapshot(votes={"M000001": "yea"}))
    assert result["status"] == "incomplete"
    assert "M000001" not in result["rolls"][0]["missing_pairs"]
    assert result["summary"]["unverified_ledger_pairs"] == 1


def test_senate_mapping_is_explicit_and_missing_lis_never_becomes_bioguide():
    directory = FIXTURES / "senate_xml_sample"
    result = reconcile(SENATE, load_sources(directory, SENATE, directory / "members.xml"), snapshot(SENATE))
    assert result["status"] == "differences"
    assert result["rolls"][0]["missing_pairs"] == {"S000001": "yea", "S000002": "nay"}
    assert result["member_mapping"]["sha256"]
    unresolved = reconcile(SENATE, load_sources(directory, SENATE), snapshot(SENATE, {"S000001": "yea"}))
    assert unresolved["status"] == "incomplete"
    assert unresolved["summary"]["missing_pairs"] == 0
    assert unresolved["summary"]["unverified_ledger_pairs"] == 1


def test_conflicting_senate_member_map_is_rejected(tmp_path):
    path = tmp_path / "members.xml"
    path.write_text('<senators><senator><lis_member_id>S1</lis_member_id><bioguide_id>A000001</bioguide_id></senator>'
                    '<senator><lis_member_id>S1</lis_member_id><bioguide_id>B000001</bioguide_id></senator></senators>')
    with pytest.raises(ValueError, match="conflicting LIS"):
        load_sources(tmp_path, SENATE, path)


def test_manifest_reuses_renamed_sources_with_verified_bytes(tmp_path):
    xml = FIXTURES / "house_clerk_sample" / "roll001.xml"
    path = tmp_path / "sources.json"
    path.write_text(json.dumps({"scope": asdict(HOUSE), "files": [
        {"roll_key": list(HOUSE.key(1)), "file": str(xml), "sha256": hashlib.sha256(xml.read_bytes()).hexdigest()}]}))
    sources = load_sources(None, HOUSE, source_manifest=path)
    result = reconcile(HOUSE, sources, snapshot())
    assert result["status"] == "differences"
    assert result["summary"]["missing_pairs"] == 3
    assert result["source_manifest"]["sha256"]
    data = json.loads(path.read_text())
    data["files"][0]["sha256"] = "0" * 64
    path.write_text(json.dumps(data))
    assert reconcile(HOUSE, load_sources(None, HOUSE, source_manifest=path), snapshot())["status"] == "incomplete"


@pytest.mark.parametrize("fault", ["missing", "duplicate", "wrong_scope", "wrong_roll", "bad_hash"])
def test_manifest_never_silently_fills_or_selects_conflicting_sources(tmp_path, fault):
    xml = FIXTURES / "house_clerk_sample" / "roll001.xml"
    data = {"scope": asdict(HOUSE), "files": [
        {"roll_key": list(HOUSE.key(1)), "file": str(xml), "sha256": hashlib.sha256(xml.read_bytes()).hexdigest()}]}
    if fault == "missing":
        data["files"] = []
    elif fault == "duplicate":
        data["files"].append(data["files"][0])
    elif fault == "wrong_scope":
        data["scope"]["session"] = 2
    elif fault == "wrong_roll":
        data["files"][0]["roll_key"][3] = 2
    else:
        data["files"][0]["sha256"] = "not a hash"
    path = tmp_path / "sources.json"
    path.write_text(json.dumps(data))
    if fault == "missing":
        assert reconcile(HOUSE, load_sources(None, HOUSE, source_manifest=path), snapshot())["status"] == "incomplete"
    else:
        with pytest.raises(ValueError):
            load_sources(None, HOUSE, source_manifest=path)


def test_duplicate_lis_with_different_direct_bioguides_is_not_two_facts(tmp_path):
    root = ET.parse(FIXTURES / "senate_xml_sample" / "vote_001.xml").getroot()
    for index, member in enumerate(root.findall("./members/member")):
        member.find("lis_member_id").text = "S001"
        ET.SubElement(member, "bioguide_id").text = f"A00000{index}"
    ET.ElementTree(root).write(tmp_path / "vote_001.xml")
    sources = load_sources(tmp_path, SENATE)
    result = reconcile(SENATE, sources, snapshot(SENATE, {"A000000": "yea", "A000001": "nay"}))
    assert result["status"] == "incomplete"
    assert result["summary"]["comparable_source_pairs"] == 0
    assert result["summary"]["unverified_ledger_pairs"] == 2


def test_conflicting_house_identity_attributes_are_unresolved(tmp_path):
    sources = write_house(tmp_path, lambda root: root.find("vote-data/recorded-vote/legislator").set("name-id", "A000001"))
    result = reconcile(HOUSE, sources, snapshot(votes={"M000001": "yea"}))
    assert result["status"] == "incomplete"
    assert result["summary"]["comparable_source_pairs"] == 2


@pytest.mark.parametrize("yeas,status", [("2", "differences"), ("3", "incomplete"), ("bad", "incomplete"), ("-1", "incomplete")])
def test_published_tallies_detect_truncated_or_inconsistent_rows(tmp_path, yeas, status):
    def add_totals(root):
        totals = ET.SubElement(ET.SubElement(root.find("vote-metadata"), "vote-totals"), "totals-by-vote")
        for name, value in [("yea", yeas), ("nay", "1"), ("present", "0"), ("not-voting", "0")]:
            ET.SubElement(totals, f"{name}-total").text = value
    sources = write_house(tmp_path, add_totals)
    assert reconcile(HOUSE, sources, snapshot())["status"] == status


@pytest.mark.parametrize("mutation", ["duplicate_pair", "duplicate_roll", "outside_scope", "orphan", "bad_bioguide", "bad_position"])
def test_invalid_ledger_is_rejected(mutation):
    data = snapshot(votes={"M000001": "yea"})
    if mutation == "duplicate_pair":
        data["votes"].append(data["votes"][0])
    elif mutation == "duplicate_roll":
        data["rolls"].append(data["rolls"][0])
    elif mutation == "outside_scope":
        data["rolls"][0][2] = 2
    elif mutation == "orphan":
        data["rolls"] = []
    elif mutation == "bad_bioguide":
        data["votes"][0]["bioguide_id"] = "S419"
    else:
        data["votes"][0]["position"] = "abstain"
    with pytest.raises(ValueError):
        reconcile(HOUSE, house_sources(), data)


class FakeConnection:
    def __init__(self, *, fail=False, readonly="on", isolation="repeatable read"):
        self.queries = []
        self.fail, self.readonly = fail, readonly
        self.isolation = isolation
        self.rolled_back = self.closed = False

    def cursor(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, query, params=None):
        self.queries.append((query, params))
        if self.fail and "FROM roll_calls" in query:
            raise RuntimeError("simulated read failure")

    def fetchone(self):
        return datetime(2026, 11, 11, tzinfo=timezone.utc), self.readonly, self.isolation

    def fetchall(self):
        return [("house", 119, 1, 1, 5, "M000001", "yea"), ("house", 119, 1, 2, None, None, None)]

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_database_reader_is_bounded_readonly_repeatable_and_never_commits():
    connection = FakeConnection()
    scope = replace(HOUSE, last_roll=2)
    data = load_database_snapshot(scope, connect=lambda: connection)
    assert data["rolls"] == [list(scope.key(1)), list(scope.key(2))]
    assert len(data["votes"]) == 1
    assert connection.queries[0][0] == "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
    assert connection.queries[-1][1] == ("house", 119, 1, 1, 2)
    assert connection.rolled_back and connection.closed
    assert not hasattr(connection, "commit")


@pytest.mark.parametrize("kwargs", [{"fail": True}, {"readonly": "off"}, {"isolation": "read committed"}])
def test_database_failure_rolls_back_and_closes(kwargs):
    connection = FakeConnection(**kwargs)
    with pytest.raises((ValueError, RuntimeError)):
        load_database_snapshot(HOUSE, connect=lambda: connection)
    assert connection.rolled_back and connection.closed


@pytest.mark.parametrize("kwargs", [{"first_roll": 0}, {"last_roll": 2001}, {"session": 3}, {"congress": 0}, {"chamber": "joint"}])
def test_scope_rejects_unbounded_or_invalid_queries(kwargs):
    with pytest.raises(ValueError):
        replace(HOUSE, **kwargs)


def test_cli_replay_exits_nonzero_on_difference_and_never_overwrites(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps(snapshot(votes={"M000001": "yea"})))
    output = tmp_path / "audit.json"
    args = ["--chamber", "house", "--congress", "119", "--session", "1", "--first-roll", "1", "--last-roll", "1",
            "--source-dir", str(FIXTURES / "house_clerk_sample"), "--ledger-json", str(ledger), "--output", str(output)]
    assert main(args) == 1
    saved = json.loads(output.read_text())
    assert saved["ledger_input"]["sha256"]
    assert saved["read_only"]
    assert json.loads(capsys.readouterr().out)["summary"]["missing_pairs"] == 2
    before = output.read_bytes()
    with pytest.raises(FileExistsError):
        main(args)
    assert output.read_bytes() == before


@pytest.mark.parametrize("scope,fetch_name,filename", [
    (replace(HOUSE, session=2), "fetch_house_clerk_roll_calls", "roll001.xml"),
    (SENATE, "fetch_senate_vote_files", "vote_001.xml"),
])
def test_opt_in_collection_reuses_existing_downloader_and_never_overwrites(tmp_path, monkeypatch, scope, fetch_name, filename):
    from app.etl import fetch_sources
    calls = []
    def fetch(**kwargs):
        calls.append(kwargs)
        return [fetch_sources.DownloadResult("https://official.example/vote.xml", tmp_path / filename, 123, True)]
    monkeypatch.setattr(fetch_sources, fetch_name, fetch)
    result = fetch_missing_sources(tmp_path, scope)
    assert calls[0]["roll_numbers"] == [1]
    assert calls[0]["output_dir"] == tmp_path
    assert calls[0]["overwrite"] is False
    if scope.chamber == "house":
        assert calls[0]["year"] == 2026
    else:
        assert (calls[0]["congress"], calls[0]["session"]) == (119, 1)
    assert result[0]["status"] == "reused_cache"


def test_collection_stops_on_access_failure_without_retry(tmp_path, monkeypatch):
    from app.etl import fetch_sources
    calls = []
    def denied(**kwargs):
        calls.append(kwargs)
        raise HTTPError("https://official.example/roll001.xml", 403, "Forbidden", {}, None)
    monkeypatch.setattr(fetch_sources, "fetch_house_clerk_roll_calls", denied)
    result = fetch_missing_sources(tmp_path, replace(HOUSE, last_roll=3))
    assert len(calls) == len(result) == 1
    assert result[0]["status"] == "failed"
    assert result[0]["remaining_downloads_stopped"]


def test_fetch_and_audit_cli_uses_downloaded_bytes_and_retains_partial_roll_detection(tmp_path, monkeypatch):
    from app.etl import fetch_sources
    source_dir = tmp_path / "cache"
    def fetch(**kwargs):
        source_dir.mkdir()
        destination = source_dir / "roll001.xml"
        destination.write_bytes((FIXTURES / "house_clerk_sample" / "roll001.xml").read_bytes())
        return [fetch_sources.DownloadResult("https://official.example/roll001.xml", destination, destination.stat().st_size, False)]
    monkeypatch.setattr(fetch_sources, "fetch_house_clerk_roll_calls", fetch)
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps(snapshot(votes={"M000001": "yea"})))
    output = tmp_path / "audit.json"
    args = ["--chamber", "house", "--congress", "119", "--session", "1", "--first-roll", "1", "--last-roll", "1",
            "--source-dir", str(source_dir), "--fetch-missing", "--ledger-json", str(ledger), "--output", str(output)]
    assert main(args) == 1
    saved = json.loads(output.read_text())
    assert saved["source_collection"][0]["status"] == "downloaded"
    assert saved["summary"]["missing_pairs_on_existing_rolls"] == 2
    assert saved["read_only"]
    with pytest.raises(FileExistsError):
        main(args)  # Fails before a second fetch could create the directory again.
