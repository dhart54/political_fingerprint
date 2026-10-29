"""Local-only publication/role readiness using intact PostgreSQL guards.

Existing explicitly synthetic authority helpers opt into the guarded test flag.
No authority file, production selector, or production role is changed.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from functools import partial
import json
import os
from pathlib import Path
from threading import Barrier

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
import pytest

from app.api import positions
from app.editorial_artifacts.repository import EditorialArtifactRepository
from app.editorial_presentations.compiler import canonical_digest
from app.editorial_presentations.site_publication import (
    active_site_integration_candidate,
)
from app.editorial_presentations.publication_replacement_runtime_v2r import eligible_site_integration_candidate_v2r as eligible_site_integration_candidate
from backend.tests.positions_disposable_postgres import DisposablePostgres
from backend.tests.test_positions_read_scope_http import DOMAINS, _approved_artifact, _presentation, _row, raw
from backend.tests.test_positions_route_postgres import Trace, request
from backend.tests import test_m11n_national_security_publication_activation as national
from backend.tests import test_m12n_environment_energy_publication_preparation_postgres as environment
from backend.scripts import foushee_environment_energy_publication_preparation as environment_script
from backend.tests import test_m14h_education_publication_replacement as education

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / ".tmp/positions-reuse/publication-readiness-2026-10-29"
TABLES = ("editorial_artifact_batches", "editorial_artifact_versions",
          "editorial_artifact_relationships", "editorial_publication_registry")
pytestmark = pytest.mark.skipif(os.getenv("RUN_POSITIONS_DISPOSABLE") != "1",
                               reason="explicit owned local PostgreSQL opt-in required")


def packages():
    """Return existing contract fixtures; all non-Justice authority is synthetic."""
    nw = national._load(national.WRITE_SET_PATH)
    nr = national._row(nw, activation_authority=national._activation_authority(nw, synthetic=True), allow_test_authority=True)
    ew = environment_script._load(environment_script.WRITE_SET_PATH)
    em = environment_script.publication_metadata_for_activation(
        ew, environment_script._load(environment_script.AUTHORITY_PATH),
        environment._synthetic_activation_authority(ew), allow_test_authority=True)
    ep = next(a for a in ew["artifacts"] if a["natural_key"] == em["presentation_natural_key"])
    er = {**ep, "member_bioguide_id": "F000477", "issue_id": "ENVIRONMENT_ENERGY",
          "payload_jsonb": ep["payload"], "publication_metadata_jsonb": em,
          "publicly_active": True, "deactivated_at": None}
    ww = education._load("publication_replacement_write_set.json")
    wp = next(a for a in ww["subject"]["artifacts"] if a["natural_key"] == education.PRESENTATION_KEY)
    wr = {**wp, "payload_jsonb": wp["payload"],
          "publication_metadata_jsonb": education.publication_metadata_for_activation(ww, education._sealed_authority()),
          "publicly_active": True, "deactivated_at": None}
    result = [(nr, nw["artifacts"]), (er, ew["artifacts"]), (wr, ww["subject"]["artifacts"])]
    for row, artifacts in result:
        assert eligible_site_integration_candidate(row, member_bioguide_id="F000477") is None
        assert eligible_site_integration_candidate(row, member_bioguide_id="F000477", allow_test_authority=True) == row["payload_jsonb"]
        for artifact in artifacts:
            assert canonical_digest(artifact["payload"]) == artifact["content_sha256"]
    jr = _row(_approved_artifact())
    jm = jr["publication_metadata_jsonb"]
    jm.update(presentation_natural_key=jr["natural_key"], presentation_artifact_version=1,
              active_artifact_sha256=jr["content_sha256"], relationship_metadata={"activation_bundle_id": "local-justice"})
    ja = [{"artifact_type": "issue_public_presentation", "natural_key": jr["natural_key"],
           "payload": jr["payload_jsonb"], "schema_version": jr["schema_version"], "content_sha256": jr["content_sha256"]}]
    for kind, prefix, payload in (("standardization_validation_result", "validation", {"successful": True, "current": True, "blocking_findings": 0}),
                                   ("source_manifest", "source_manifest", {"complete_required_sources": True})):
        key = "local-justice-" + prefix
        digest = canonical_digest(payload)
        ja.append(dict(artifact_type=kind, natural_key=key, payload=payload, schema_version="local_test_v1", content_sha256=digest))
        jm.update({prefix + "_natural_key": key, prefix + "_artifact_version": 1, prefix + "_content_sha256": digest})
    return [(jr, ja), *result]


@pytest.fixture(scope="module")
def publication_db():
    server = DisposablePostgres(EVIDENCE)
    observations = []
    try:
        with server:
            with server.connect() as connection:
                connection.autocommit = True
                # Only this owned cluster: roles required by the unchanged migration.
                connection.execute("CREATE ROLE anon NOLOGIN NOBYPASSRLS; CREATE ROLE authenticated NOLOGIN NOBYPASSRLS; CREATE ROLE fixture_rls_probe NOLOGIN NOBYPASSRLS")
                for name in ("0001_initial_schema.sql", "0002_vote_interpretations.sql", "0003_vote_interpretation_details.sql",
                             "0008_vote_contexts.sql", "0009_vote_interpretation_so_what_fields.sql",
                             "0010_senate_amendment_references.sql", "0012_roll_call_session_identity.sql",
                             "0016_editorial_artifact_persistence.sql"):
                    connection.execute((ROOT / "backend/migrations" / name).read_text(encoding="utf-8-sig"))
            fixture = packages()
            seed_publications(server, fixture)
            yield server, fixture, observations
    finally:
        EVIDENCE.mkdir(exist_ok=True, parents=True)
        stopped = not (server.directory / "postmaster.pid").exists()
        (EVIDENCE / "latest-results.json").write_text(json.dumps({"cluster": str(server.directory),
            "server_stopped": stopped, "observations": observations}, indent=2), encoding="utf-8")
        assert stopped


def seed_publications(server, fixture):
    actions = {}
    justice = _presentation()
    member_actions = {r["canonical_action_id"]: r["member_action"].lower().replace(" ", "_") for r in justice["exact_action_receipts"]}
    for action in justice["reviewed_action_ids"]:
        actions[action] = (DOMAINS[0], raw(action, member_actions.get(action, "nay")))
    for row, _ in fixture[1:]:
        subject = row["payload_jsonb"]["subject"]
        reviewed = subject.get("receipt_projections") or subject["preview_data"]["evidence_119"]
        for source in reviewed:
            action = source["canonical_action_id"]
            position = source["position"]
            if action in actions:
                assert actions[action][1]["position"] == position, "fixture member-action conflict"
            else:
                actions[action] = (row["issue_id"], raw(action, position))
    for i, domain in enumerate(DOMAINS):
        for congress, position in ((118, "not_voting"), (119, "present")):
            action = f"house:{congress}:1:{9900 + i}"
            actions[action] = (domain, raw(action, position))
    with server.connect() as connection:
        connection.execute("INSERT INTO legislators (id,bioguide_id,name_display,chamber,state,district,party) VALUES (1,'F000477','Valerie P. Foushee','house','NC','4','D'),(2,'X000001','Fixture Member','house','NC','1','D')")
        for i, (domain, row) in enumerate(actions.values(), 1):
            connection.execute("INSERT INTO roll_calls (id,chamber,congress,session,rollcall_number,vote_date,question,description) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (i,row["chamber"],row["congress"],row["session"],row["rollcall_number"],row["vote_date"],row["question"],row["description"]))
            connection.execute("INSERT INTO votes_cast (roll_call_id,legislator_id,position) VALUES (%s,1,%s)",(i,row["position"]))
            if i != 1:
                connection.execute("INSERT INTO vote_classifications (roll_call_id,is_eligible,eligibility_reason,primary_domain,classification_version) VALUES (%s,true,'local fixture',%s,'v1')",(i,domain))
        connection.execute("INSERT INTO editorial_artifact_batches (batch_id,deterministic_batch_key,source_commit_sha,manifest_sha256,status,artifact_count,relationship_count) VALUES (1,'local-four-domain',%s,%s,'applied',12,8)",("0"*40,"0"*64))
        for index, (row, artifacts) in enumerate(fixture):
            ids = {}
            for offset, artifact in enumerate(artifacts):
                artifact_id = 1000 + index * 10 + offset
                ids[artifact["natural_key"]] = artifact_id
                connection.execute("INSERT INTO editorial_artifact_versions (artifact_id,artifact_type,natural_key,schema_version,artifact_version,payload_jsonb,content_sha256,source_commit_sha,batch_id,member_bioguide_id,issue_id,editorial_status,benchmark_status,production_eligible,review_route) VALUES (%s,%s,%s,%s,1,%s,%s,%s,1,'F000477',%s,'human_approved','gold_benchmark',true,'standard_generation')",
                    (artifact_id,artifact["artifact_type"],artifact["natural_key"],artifact["schema_version"],Jsonb(artifact["payload"]),artifact["content_sha256"],"0"*40,row["issue_id"]))
            metadata = row["publication_metadata_jsonb"]
            parent = ids[row["natural_key"]]
            for relation, key in (("has_validation","validation_natural_key"),("uses_source_manifest","source_manifest_natural_key")):
                connection.execute("INSERT INTO editorial_artifact_relationships VALUES (%s,%s,%s,0,%s)",(parent,ids[metadata[key]],relation,Jsonb(metadata["relationship_metadata"])))
            # The intact trigger verifies these actual inserts, including member/domain.
            connection.execute("INSERT INTO editorial_publication_registry (member_bioguide_id,issue_id,artifact_id,publicly_active,activated_at,publication_metadata_jsonb) VALUES ('F000477',%s,%s,true,now(),%s)",(row["issue_id"],parent,Jsonb(metadata)))
            row["artifact_id"] = parent  # Local database identity only; authority is untouched.


def install(trace, patch, *, allow_synthetic):
    trace.install(patch)
    if allow_synthetic:
        patch.setattr(positions, "active_site_integration_candidate", partial(active_site_integration_candidate, allow_test_authority=True))


@pytest.mark.parametrize("scope", ["118", "119", "all"])
def test_four_domains_real_http_parity(publication_db, monkeypatch, scope):
    server, fixture, records = publication_db
    results = []
    for mode in ("fresh", "held", "release"):
        trace = Trace(server, mode)
        with monkeypatch.context() as patch:
            install(trace, patch, allow_synthetic=True)
            response = request(scope)
        assert response.status_code == 200, response.text
        summary = trace.summary()
        assert summary["peak"] == (2 if mode == "held" else 1)
        records.append({"test":"four_domain_parity","scope":scope,**summary})
        results.append((response,trace.queries))
    for response, queries in results[1:]:
        assert response.content == results[0][0].content
        assert response.headers == results[0][0].headers
        assert queries == results[0][1]
    rows = {r["domain"]:r for r in results[0][0].json()["positions"]}
    for domain in DOMAINS:
        assert rows[domain]["total_votes"] > 0
        assert rows[domain]["reviewed_action_count"] > 0 if scope != "118" else rows[domain]["reviewed_action_count"] == 0
    if scope != "118":
        assert rows["EDUCATION_WORKFORCE"]["reviewed_action_count"] == 17


def test_default_route_rejects_synthetic_activation(publication_db,monkeypatch):
    server,_,records=publication_db
    trace=Trace(server,"release")
    install(trace,monkeypatch,allow_synthetic=False)
    response=request()
    assert response.status_code==200
    rows={r["domain"]:r for r in response.json()["positions"]}
    assert rows[DOMAINS[0]]["reviewed_action_count"]>0
    assert all(rows[d]["reviewed_action_count"]==0 for d in DOMAINS[1:])
    records.append({"test":"default_rejects_synthetic",**trace.summary()})


@pytest.mark.parametrize("domain",DOMAINS)
@pytest.mark.parametrize("field",["active_artifact_sha256","source_manifest_content_sha256","validation_content_sha256"])
def test_sql_digest_mismatch_fails_closed(publication_db,monkeypatch,domain,field):
    server,fixture,records=publication_db
    original=next(row["publication_metadata_jsonb"] for row,_ in fixture if row["issue_id"]==domain)
    bad=deepcopy(original);bad[field]="f"*64
    with server.connect() as connection:
        connection.execute("UPDATE editorial_publication_registry SET publication_metadata_jsonb=%s WHERE issue_id=%s",(Jsonb(bad),domain))
    try:
        with server.connect() as connection:
            assert domain not in {r["issue_id"] for r in EditorialArtifactRepository(connection).publication_selector()}
        trace=Trace(server,"release")
        install(trace,monkeypatch,allow_synthetic=True)
        response=request()
        assert response.status_code==200
        rows={r["domain"]:r for r in response.json()["positions"]}
        assert rows[domain]["reviewed_action_count"]==0
        assert all(rows[d]["reviewed_action_count"]>0 for d in DOMAINS if d!=domain)
        records.append({"test":"sql_digest_rejection","domain":domain,"field":field,**trace.summary()})
    finally:
        with server.connect() as connection:
            connection.execute("UPDATE editorial_publication_registry SET publication_metadata_jsonb=%s WHERE issue_id=%s",(Jsonb(original),domain))


@pytest.mark.parametrize("index",[1,2,3])
@pytest.mark.parametrize("mutation",["member","domain","payload","source_binding","unsealed","deactivated"])
def test_actual_selected_row_bindings_fail_closed(publication_db,index,mutation):
    server,fixture,_=publication_db
    domain=fixture[index][0]["issue_id"]
    with server.connect() as connection:
        row=next(r for r in EditorialArtifactRepository(connection).publication_selector() if r["issue_id"]==domain)
    assert eligible_site_integration_candidate(row,member_bioguide_id="F000477",allow_test_authority=True) is not None
    row=deepcopy(row)
    if mutation=="member":row["member_bioguide_id"]="X000001"
    elif mutation=="domain":row["issue_id"]="HEALTH_SOCIAL"
    elif mutation=="payload":row["payload_jsonb"]["subject"]["member_bioguide_id"]="X000001"
    elif mutation=="deactivated":row["deactivated_at"]="2026-01-01"
    else:
        metadata=row["publication_metadata_jsonb"]
        key="publication_replacement_activation_authority" if index==3 else "publication_activation_authority"
        if mutation=="unsealed":metadata[key]["sealed"]=False
        elif index==3:
            authority=metadata[key]
            authority["subject"]["reviewed_candidate_complete_file_sha256"]="f"*64
            authority["activation_authority_subject_sha256"]=canonical_digest(authority["subject"])
            metadata["activation_authority_subject_sha256"]=authority["activation_authority_subject_sha256"]
        else:
            if index==1:
                metadata["accepted_m11m_file_sha256"]="f"*64
            else:
                # Environment's authoritative source binding is nested in its
                # preparation authority, not a free-standing metadata field.
                preparation=metadata["production_eligibility_publication_authority"]
                preparation["subject"]["accepted_site_integration_binding"]["file_sha256"]="f"*64
                preparation["authority_subject_sha256"]=canonical_digest(preparation["subject"])
                metadata["authority_subject_sha256"]=preparation["authority_subject_sha256"]
    assert eligible_site_integration_candidate(row,member_bioguide_id="F000477",allow_test_authority=True) is None


@pytest.mark.parametrize("role",["anon","authenticated"])
@pytest.mark.parametrize("table",TABLES)
def test_public_roles_have_no_table_access(publication_db,role,table):
    server,_,_=publication_db
    with server.connect() as connection:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            with connection.transaction():
                connection.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                connection.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table)))


@pytest.mark.parametrize("table",TABLES)
def test_rls_denies_nonbypass_role_even_with_select_grant(publication_db,table):
    server,_,_=publication_db
    with server.connect() as connection:
        assert connection.execute("SELECT rolbypassrls OR rolsuper FROM pg_roles WHERE rolname='fixture_rls_probe'").fetchone()==(False,)
        assert connection.execute("SELECT relrowsecurity FROM pg_class WHERE oid=%s::regclass",(table,)).fetchone()==(True,)
        connection.execute(sql.SQL("GRANT SELECT ON {} TO fixture_rls_probe").format(sql.Identifier(table)))
        connection.execute("SET LOCAL ROLE fixture_rls_probe")
        assert connection.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table))).fetchone()==(0,)
        connection.rollback()  # Local probe grant does not persist.


def test_rls_rejects_writes_and_role_elevation(publication_db):
    server,_,_=publication_db
    with server.connect() as connection:
        connection.execute("GRANT INSERT ON editorial_artifact_batches TO fixture_rls_probe")
        with pytest.raises(psycopg.errors.InsufficientPrivilege, match="row-level security"):
            with connection.transaction():
                connection.execute("SET LOCAL ROLE fixture_rls_probe")
                connection.execute("INSERT INTO editorial_artifact_batches (batch_id,deterministic_batch_key,source_commit_sha,manifest_sha256,status,artifact_count,relationship_count) VALUES (99,'forbidden',%s,%s,'pending_review',0,0)",("0"*40,"0"*64))
        connection.rollback()
    # SET SESSION AUTHORIZATION removes superuser session authority for this connection.
    with server.connect() as connection:
        connection.execute("SET SESSION AUTHORIZATION fixture_rls_probe")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            connection.execute("SET ROLE experiment")


@pytest.mark.parametrize("mutation",["member","domain","not_presentation","missing_validation","missing_source","blocking",
                                      "unapproved","not_benchmarked","ineligible","failed_validation","incomplete_source"])
def test_activation_trigger_rejects_invalid_candidate(publication_db,mutation):
    server,fixture,_=publication_db
    row=fixture[0][0]
    with server.connect() as connection:
        # Every mutation is inside a rolled-back savepoint/transaction.
        with pytest.raises(psycopg.errors.RaiseException):
            with connection.transaction():
                if mutation in {"missing_validation","missing_source"}:
                    relation="has_validation" if mutation=="missing_validation" else "uses_source_manifest"
                    connection.execute("DELETE FROM editorial_artifact_relationships WHERE parent_artifact_id=%s AND relationship_type=%s",(row["artifact_id"],relation))
                    connection.execute("UPDATE editorial_publication_registry SET activated_at=activated_at WHERE issue_id=%s",(row["issue_id"],))
                elif mutation in {"unapproved","not_benchmarked","ineligible"}:
                    connection.execute("INSERT INTO editorial_artifact_versions (artifact_id,artifact_type,natural_key,schema_version,artifact_version,payload_jsonb,content_sha256,source_commit_sha,batch_id,member_bioguide_id,issue_id,editorial_status,benchmark_status,production_eligible,review_route) SELECT 2000,artifact_type,'local-ineligible',schema_version,1,payload_jsonb,content_sha256,source_commit_sha,batch_id,member_bioguide_id,issue_id,%s,%s,false,review_route FROM editorial_artifact_versions WHERE artifact_id=%s",
                        ("human_approval_pending" if mutation=="unapproved" else "human_approved","not_promoted" if mutation=="not_benchmarked" else "gold_benchmark",row["artifact_id"]))
                    connection.execute("UPDATE editorial_publication_registry SET artifact_id=2000 WHERE issue_id=%s",(row["issue_id"],))
                elif mutation in {"failed_validation","incomplete_source"}:
                    relation="has_validation" if mutation=="failed_validation" else "uses_source_manifest"
                    payload={"successful":False,"current":True,"blocking_findings":0} if mutation=="failed_validation" else {"complete_required_sources":False}
                    connection.execute("INSERT INTO editorial_artifact_versions (artifact_id,artifact_type,natural_key,schema_version,artifact_version,payload_jsonb,content_sha256,source_commit_sha,batch_id,member_bioguide_id,issue_id,editorial_status,benchmark_status,production_eligible,review_route) SELECT 2001,artifact_type,'local-bad-child',schema_version,1,%s,%s,source_commit_sha,batch_id,member_bioguide_id,issue_id,editorial_status,benchmark_status,production_eligible,review_route FROM editorial_artifact_versions WHERE artifact_id=(SELECT child_artifact_id FROM editorial_artifact_relationships WHERE parent_artifact_id=%s AND relationship_type=%s)",
                        (Jsonb(payload),canonical_digest(payload),row["artifact_id"],relation))
                    connection.execute("UPDATE editorial_artifact_relationships SET child_artifact_id=2001 WHERE parent_artifact_id=%s AND relationship_type=%s",(row["artifact_id"],relation))
                    connection.execute("UPDATE editorial_publication_registry SET activated_at=activated_at WHERE issue_id=%s",(row["issue_id"],))
                elif mutation=="blocking":
                    payload=deepcopy(row["payload_jsonb"]);payload["blocking_findings"]=1
                    connection.execute("INSERT INTO editorial_artifact_versions (artifact_id,artifact_type,natural_key,schema_version,artifact_version,payload_jsonb,content_sha256,source_commit_sha,batch_id,member_bioguide_id,issue_id,editorial_status,benchmark_status,production_eligible,review_route) SELECT 2000,artifact_type,'local-blocking',schema_version,1,%s,%s,source_commit_sha,batch_id,member_bioguide_id,issue_id,editorial_status,benchmark_status,production_eligible,review_route FROM editorial_artifact_versions WHERE artifact_id=%s",(Jsonb(payload),canonical_digest(payload),row["artifact_id"]))
                    connection.execute("INSERT INTO editorial_artifact_relationships SELECT 2000,child_artifact_id,relationship_type,ordinal,metadata_jsonb FROM editorial_artifact_relationships WHERE parent_artifact_id=%s",(row["artifact_id"],))
                    connection.execute("UPDATE editorial_publication_registry SET artifact_id=2000 WHERE issue_id=%s",(row["issue_id"],))
                else:
                    field,value=("member_bioguide_id","X000001") if mutation=="member" else ("issue_id","HEALTH_SOCIAL") if mutation=="domain" else ("artifact_id",row["artifact_id"]+1)
                    connection.execute(sql.SQL("UPDATE editorial_publication_registry SET {}=%s WHERE issue_id=%s").format(sql.Identifier(field)),(value,row["issue_id"]))


@pytest.mark.parametrize("operation",["update","delete","published_delete"])
def test_immutable_artifact_guard(publication_db,operation):
    server,fixture,_=publication_db
    with server.connect() as connection:
        with pytest.raises(psycopg.errors.RaiseException):
            with connection.transaction():
                artifact_id=fixture[0][0]["artifact_id"]
                if operation=="published_delete":connection.execute("SET LOCAL app.editorial_artifact_rollback_batch='local-four-domain'")
                if operation=="update":connection.execute("UPDATE editorial_artifact_versions SET content_sha256=content_sha256 WHERE artifact_id=%s",(artifact_id,))
                else:connection.execute("DELETE FROM editorial_artifact_versions WHERE artifact_id=%s",(artifact_id,))


def test_four_domain_concurrent_route(publication_db,monkeypatch):
    server,_,records=publication_db
    trace=Trace(server,"release",gate=Barrier(2))
    install(trace,monkeypatch,allow_synthetic=True)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures=[executor.submit(request) for _ in range(2)]
        responses=[future.result(timeout=15) for future in futures]
    assert responses[0].status_code==responses[1].status_code==200
    assert responses[0].content==responses[1].content
    summary=trace.summary();assert summary["peak"]==2 and summary["opens"]==6
    records.append({"test":"four_domain_concurrent",**summary})
