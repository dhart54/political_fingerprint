"""Current record, immutable reviewed meaning, and explicit availability boundaries."""

import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import positions, precomputed
from app.api.editorial_presentations import M11M_CANDIDATE_PATH, M12M_CANDIDATE_PATH, M13M_CANDIDATE_PATH
from app.editorial_presentations.education_workforce_m14g_integration_candidate import merge_m14g_preview_evidence
from app.editorial_presentations.integration_candidate import governed_position_summary
from app.editorial_presentations.reviewed_record import (
    GovernedReceiptProjectionError, REVIEWED, UNREVIEWED, overlay_reviewed_actions, union_database_actions,
)
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
M14 = ROOT / "docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1/site_integration_candidate.json"
DOMAIN = "EDUCATION_WORKFORCE"
MEMBER = "leg_valerie_p_foushee"
DOMAINS = ["JUSTICE_PUBLIC_SAFETY", "NATIONAL_SECURITY_FOREIGN", "ENVIRONMENT_ENERGY", DOMAIN]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def raw(row):
    chamber, congress, session, roll = row["canonical_action_id"].split(":")
    return precomputed._serialize_evidence_row({
        "roll_call_id": f"db-{row['canonical_action_id']}", "chamber": chamber,
        "congress": int(congress), "session": int(session), "rollcall_number": int(roll),
        "vote_date": row.get("vote_date", "2026-07-01"), "position": row["position"],
        "issue_domain": row.get("issue_domain", DOMAIN), "question": "Official raw question",
        "description": "Official raw description", "classification_reason": "eligible",
        "context_version": "test", "final_result": "passed",
    })


def extra(domain=DOMAIN, congress=119):
    return raw({"canonical_action_id": f"house:{congress}:2:9999", "position": "nay", "issue_domain": domain})


def test_m14_eighteenth_action_does_not_expand_or_change_review():
    candidate = load(M14)
    original = copy.deepcopy(candidate)
    reviewed = candidate["subject"]["receipt_projections"]
    rows = [raw(row) for row in reviewed]
    base = {"domain": DOMAIN, "evidence": rows}
    before = merge_m14g_preview_evidence(base, candidate, domain=DOMAIN, scope="119")
    after = merge_m14g_preview_evidence({**base, "evidence": rows + [extra()]}, candidate, domain=DOMAIN, scope="119")
    assert len(after["evidence"]) == 18
    assert after["evidence"][:17] == before["evidence"]
    for source, row in zip(reviewed, after["evidence"]):
        assert row["governed_receipt_projection"] == source["governed_receipt_projection"]
        assert row["interpretation_review_state"] == REVIEWED
        assert row["roll_call_id"].startswith("db-")
        assert row["vote_context"]["final_result"] == "passed"
    new = after["evidence"][-1]
    assert new["interpretation_review_state"] == UNREVIEWED
    assert not new.get("governed_receipt_projection")
    assert after["review_accounting"] == {"available_action_count": 18, "reviewed_action_count": 17, "not_yet_reviewed_action_count": 1}
    assert candidate == original
    presentation = candidate["subject"]["presentation"]
    assert len(presentation["repeated_patterns"]) == 2
    assert len(presentation["notable_choices"]) == 1
    assert len(presentation["evidence_metadata"]["display_action_ids"]) == 6
    assert len(presentation["reviewed_action_ids"]) == 17
    assert len({row["governed_receipt_projection"]["episode_id"] for row in reviewed}) == 16
    assert merge_m14g_preview_evidence(base, candidate, domain=DOMAIN, scope="119") == before


def test_exact_identity_missing_identity_and_duplicate_conflicts():
    accepted = load(M14)["subject"]["receipt_projections"][:1]
    row = raw(accepted[0])
    unknown = copy.deepcopy(row)
    unknown.pop("canonical_action_id")
    unknown.pop("session")
    result = overlay_reviewed_actions({"evidence": [row, unknown, extra()]}, accepted, domain=DOMAIN)
    assert len(result["evidence"]) == 3
    assert [item["interpretation_review_state"] for item in result["evidence"]] == [REVIEWED, UNREVIEWED, UNREVIEWED]
    assert not result["evidence"][1].get("governed_receipt_projection")
    for duplicate in (row, {**row, "position": "yea"}):
        with pytest.raises(GovernedReceiptProjectionError, match="repeated"):
            overlay_reviewed_actions({"evidence": [row, duplicate]}, accepted, domain=DOMAIN)
        with pytest.raises(GovernedReceiptProjectionError, match="repeated"):
            union_database_actions([], [row, duplicate])
    with pytest.raises(GovernedReceiptProjectionError, match="repeated"):
        overlay_reviewed_actions({"evidence": [row]}, accepted * 2, domain=DOMAIN)
    with pytest.raises(GovernedReceiptProjectionError, match="conflicting"):
        union_database_actions([row], [{**row, "position": "present"}])
    assert union_database_actions([row], [row]) == [row]


@pytest.mark.parametrize("path", [M11M_CANDIDATE_PATH, M12M_CANDIDATE_PATH, M13M_CANDIDATE_PATH, M14])
def test_all_site_generations_overlay_instead_of_replacing(path):
    candidate = load(path)
    subject = candidate["subject"]
    reviewed = subject.get("receipt_projections") or subject["preview_data"]["evidence_119"]
    domain = subject["issue_id"]
    rows = [raw(row) for row in reviewed] + [extra(domain)]
    result = positions._merge_site_integration_evidence({"domain": domain, "evidence": rows}, candidate, domain=domain, scope="119")
    assert len(result["evidence"]) == len(reviewed) + 1
    assert result["review_accounting"]["reviewed_action_count"] == len(reviewed)
    assert result["evidence"][-1]["interpretation_review_state"] == UNREVIEWED


@pytest.mark.parametrize("scope", ["118", "119", "all"])
def test_discovery_and_detail_share_database_universe_for_every_active_domain(monkeypatch, scope):
    candidates = {load(path)["subject"]["issue_id"]: load(path) for path in (M11M_CANDIDATE_PATH, M12M_CANDIDATE_PATH, M14)}
    # Exercise Justice's publication-governed receipt path as well as site generations.
    from backend.tests.test_governed_receipt_projection import _presentation, _raw_row
    justice = _presentation()
    reviewed = {domain: candidate["subject"].get("receipt_projections") or candidate["subject"]["preview_data"]["evidence_119"] for domain, candidate in candidates.items()}
    reviewed["JUSTICE_PUBLIC_SAFETY"] = [{**_raw_row(receipt), "canonical_action_id": receipt["canonical_action_id"], "issue_domain": "JUSTICE_PUBLIC_SAFETY"} for receipt in justice["exact_action_receipts"]]
    database = {domain: [raw(row) for row in reviewed[domain]] for domain in DOMAINS}
    monkeypatch.setattr(positions, "get_legislator_profile", lambda **kw: {"bioguide_id": "F000477"})
    monkeypatch.setattr(positions, "_load_publication_rows", lambda: [])
    monkeypatch.setattr(positions, "_active_site_integration_publication", lambda **kw: candidates.get(kw["issue_id"]))
    monkeypatch.setattr(positions, "select_public_presentations", lambda *a, **kw: {"presentations": [justice]})
    monkeypatch.setattr(positions, "get_governed_position_evidence_rows", lambda **kw: copy.deepcopy(next(rows for rows in database.values() if {row["canonical_action_id"] for row in rows} == set(kw["canonical_action_ids"]))))
    monkeypatch.setattr(positions, "get_position_response", lambda **kw: {"positions": [{"domain": domain, "total_votes": 999} for domain in DOMAINS]})

    def evidence(**kw):
        domain = kw["domain"]
        # Includes overlap plus one reviewed action absent from the classified selection.
        rows = database[domain][1:] + [extra(domain), extra(domain, 118)]
        return {"domain": domain, "evidence": copy.deepcopy([row for row in rows if scope == "all" or row["congress"] == int(scope)])}

    monkeypatch.setattr(positions, "get_position_evidence_response", evidence)
    client = TestClient(app)
    discovery = client.get(f"/legislators/{MEMBER}/positions", params={"scope": scope})
    assert discovery.status_code == 200, discovery.text
    for summary in discovery.json()["positions"]:
        detail = client.get(f"/legislators/{MEMBER}/positions/{summary['domain']}/evidence", params={"scope": scope})
        assert detail.status_code == 200, detail.text
        rows = detail.json()["evidence"]
        assert summary["total_votes"] == summary["available_action_count"] == len(rows)
        assert summary["reviewed_action_count"] <= len(rows)
        if scope == "118":
            assert len(rows) == 1 and rows[0]["congress"] == 118
            assert not rows[0].get("governed_receipt_projection")
        else:
            assert summary["reviewed_action_count"] == len(reviewed[summary["domain"]])
            assert len(rows) == len(reviewed[summary["domain"]]) + (2 if scope == "all" else 1)
            assert summary["not_yet_reviewed_action_count"] == (2 if scope == "all" else 1)


def test_database_serializer_and_query_preserve_domain_and_session(monkeypatch):
    row = extra()
    assert row["issue_domain"] == DOMAIN
    assert row["session"] == 2
    assert governed_position_summary([row], domain=DOMAIN)["total_votes"] == 1
    queries = []
    monkeypatch.setattr(precomputed, "_query_all_dicts", lambda sql, params: queries.append(sql) or [])
    precomputed._get_db_scoped_position_evidence_rows(legislator_db_id=1, domain=DOMAIN, scope="119", classification_version="v1")
    assert "rc.session" in queries[0]


@pytest.mark.parametrize("path", ["positions", f"positions/{DOMAIN}/evidence", "fingerprint", "drift"])
def test_production_database_failure_is_sanitized_503_never_fixture(monkeypatch, path):
    monkeypatch.delenv("ENABLE_FIXTURE_FALLBACK", raising=False)
    monkeypatch.setattr(precomputed, "get_connection", lambda: (_ for _ in ()).throw(RuntimeError("secret database details")))
    for name in ("position_response", "position_evidence_response", "fingerprint_response", "drift_response"):
        monkeypatch.setattr(precomputed, "_get_fallback_" + name, lambda **kw: pytest.fail("production called fixtures"))
    response = TestClient(app).get(f"/legislators/leg_alex_morgan/{path}")
    assert response.status_code == 503
    assert response.json() == {"detail": "Public record data is unavailable right now."}


def test_successful_missing_is_404_and_never_fixture(monkeypatch):
    monkeypatch.delenv("ENABLE_FIXTURE_FALLBACK", raising=False)
    monkeypatch.setattr(precomputed, "_query_all_dicts", lambda *a, **kw: [])
    monkeypatch.setattr(precomputed, "_get_fallback_position_response", lambda **kw: pytest.fail("missing called fixtures"))
    assert TestClient(app).get("/legislators/leg_alex_morgan/positions").status_code == 404


@pytest.mark.parametrize("scope", ["118", "119", "all"])
def test_explicit_demo_is_marked_and_scope_correct(monkeypatch, scope):
    monkeypatch.setenv("ENABLE_FIXTURE_FALLBACK", "1")
    monkeypatch.setattr(precomputed, "get_connection", lambda: (_ for _ in ()).throw(RuntimeError("offline")))
    positions_payload = precomputed.get_position_response(legislator_id="leg_alex_morgan", scope=scope)
    assert positions_payload["data_source"] == "fixtures"
    for summary in positions_payload["positions"]:
        evidence = precomputed.get_position_evidence_response(legislator_id="leg_alex_morgan", domain=summary["domain"], scope=scope)
        assert evidence["data_source"] == "fixtures" and evidence["scope"] == scope
        assert summary["total_votes"] == len(evidence["evidence"])
        assert all(row["congress"] in precomputed.PROFILE_SCOPES[scope]["congresses"] for row in evidence["evidence"])
    fingerprint = precomputed.get_fingerprint_response(legislator_id="leg_alex_morgan", scope=scope)
    assert fingerprint["scope"] == scope and fingerprint["data_source"] == "fixtures"
    assert sum(row["vote_count"] for row in fingerprint["fingerprint"]) == sum(row["total_votes"] for row in positions_payload["positions"])


@pytest.mark.parametrize("stage", ["execute", "fetchall", "close"])
def test_query_and_cleanup_failures_are_unavailable_not_missing(monkeypatch, stage):
    class Connection:
        description = [("id",)]
        def cursor(self):
            return self
        def execute(self, *args):
            if stage == "execute":
                raise RuntimeError("private execution error")
        def fetchall(self):
            if stage == "fetchall":
                raise RuntimeError("private fetch error")
            return []
        def close(self):
            if stage == "close":
                raise RuntimeError("private close error")
    monkeypatch.delenv("ENABLE_FIXTURE_FALLBACK", raising=False)
    monkeypatch.setattr(precomputed, "get_connection", Connection)
    from app.api.public_data import PublicDataUnavailable
    with pytest.raises(PublicDataUnavailable) as exc:
        precomputed._query_all_dicts("SELECT id FROM legislators")
    assert exc.value.status_code == 503
    assert "private" not in exc.value.detail


def test_demo_summary_is_marked_and_cannot_be_persisted(monkeypatch):
    from app.summaries import cache
    monkeypatch.setenv("ENABLE_FIXTURE_FALLBACK", "1")
    monkeypatch.setattr(precomputed, "get_connection", lambda: (_ for _ in ()).throw(RuntimeError("offline")))
    monkeypatch.setattr(cache, "persist_summary_record", lambda **kw: pytest.fail("demo summary persisted"))
    response = TestClient(app).get("/legislators/leg_alex_morgan/summary")
    assert response.status_code == 200
    assert response.json()["data_source"] == "fixtures"


@pytest.mark.parametrize("read", [
    lambda: precomputed.search_legislators(),
    lambda: precomputed.get_coverage_metadata(),
    lambda: precomputed.get_zip_lookup_response(zip_code="27701"),
    lambda: precomputed.get_zip_race_response(zip_code="27701"),
    lambda: precomputed.get_supported_zip_responses(),
    lambda: precomputed.get_alignment_response(legislator_id="leg_alex_morgan", preferences={DOMAIN: "support"}),
    lambda: precomputed.get_legislator_contact_response(legislator_id="leg_valerie_p_foushee"),
])
def test_other_public_reads_fail_closed_without_positive_opt_in(monkeypatch, read):
    from app.api.public_data import PublicDataUnavailable
    monkeypatch.setenv("ENABLE_FIXTURE_FALLBACK", "0")
    monkeypatch.setattr(precomputed, "get_connection", lambda: (_ for _ in ()).throw(RuntimeError("offline")))
    with pytest.raises(PublicDataUnavailable):
        read()


@pytest.mark.parametrize("status", [200, 404, 503])
def test_real_http_smoke_distinguishes_absent_demo_from_unavailable(monkeypatch, status):
    from urllib.error import HTTPError
    from scripts import foushee_justice_publication_activation as activation
    from scripts.editorial_artifact_store import StoreSafetyError

    def response(*args):
        if status != 200:
            raise HTTPError("http://disposable", status, "test", {}, None)
        return {"presentations": []}

    monkeypatch.setattr(activation, "_get_public_presentations", response)
    if status == 404:
        activation._assert_demo_member_absent("http://disposable")
    else:
        with pytest.raises(StoreSafetyError):
            activation._assert_demo_member_absent("http://disposable")
