import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { gunzipSync } from "node:zlib";
import { transport } from "../tests/health-choice-routes.mjs";
import { issuePresentationStatus, getEditorialPresentation } from "./editorialPresentation.mjs";
import { buildIssueOverviewRows, isPublicAnalysisAvailable } from "./frontendPassA.mjs";
import { contentHash, projectRecordCard, findingIdentity, suppliedDirection } from "./recordCard.mjs";

for (const scope of ["119", "all"]) test(`existing four-domain record card remains byte-identical after bounded Health in ${scope}`, async () => {
  const candidate=JSON.parse(fs.readFileSync(new URL("../../docs/review_packets/record_at_a_glance_v1/candidate.json",import.meta.url)));
  const snapshots=JSON.parse(gunzipSync(fs.readFileSync(new URL(`../../${candidate.source_snapshot}`,import.meta.url))));
  const before=snapshots[`${candidate.legislator_id}:${scope}:editorial`].body;
  const after=structuredClone(before);
  const health=transport.responses.find((p)=>p.member_bioguide_id==="F000477"&&p.scope===scope).presentations.find((p)=>p.issue_id==="HEALTH_SOCIAL");
  after.presentations=after.presentations.map((p)=>p.issue_id==="HEALTH_SOCIAL"?structuredClone(health):p);
  const args={candidate,legislatorId:candidate.legislator_id,memberBioguideId:candidate.member_bioguide_id,scope};
  const baseline=await projectRecordCard({...args,payload:before});
  assert.equal(baseline.status,"ready"); assert.equal(baseline.entries.length,6);
  assert.deepEqual(await projectRecordCard({...args,payload:after}),baseline);
});

for (const scope of ["119", "all"]) test(`bounded Health preserves existing selected Justice card in ${scope}`, async () => {
  const before=transport.baselines.find((p)=>p.member_bioguide_id==="F000477"&&p.scope===scope);
  const after=transport.responses.find((p)=>p.member_bioguide_id==="F000477"&&p.scope===scope);
  const justice=before.presentations.find((p)=>p.issue_id==="JUSTICE_PUBLIC_SAFETY");
  const field=["repeated_patterns","policy_trajectories","notable_choices","syntheses"].find((f)=>justice[f]?.some((x)=>suppliedDirection(x)));
  const finding=justice[field].find((x)=>suppliedDirection(x));
  const candidate={status:"candidate",legislator_id:before.legislator_id,member_bioguide_id:before.member_bioguide_id,scopes:[scope],
    sources:[{issue_id:justice.issue_id,presentation_sha256:{[scope]:await contentHash(justice)},
      evidence_coverage:{[scope]:{source_field:"scope_boundary",source_text:justice.scope_boundary,source_sha256:await contentHash(justice.scope_boundary)}}}],
    entries:[{issue_id:justice.issue_id,field,finding_id:findingIdentity(finding),finding_sha256:await contentHash(finding),section:suppliedDirection(finding),action_ids:finding.action_ids}]};
  const args={candidate,legislatorId:before.legislator_id,memberBioguideId:before.member_bioguide_id,scope};
  const baseline=await projectRecordCard({...args,payload:before});
  assert.equal(baseline.status,"ready"); assert.equal(baseline.entries.length,1);
  assert.deepEqual(await projectRecordCard({...args,payload:after}),baseline);
});

for (const [i, payload] of transport.responses.entries()) {
  const identity = { legislatorId: payload.legislator_id, memberBioguideId: payload.member_bioguide_id };
  test(`${payload.member_bioguide_id} ${payload.scope}: real API ingestion preserves all eight domains`, () => {
    assert.equal(issuePresentationStatus(payload, identity, payload.scope), "ready");
    const health = getEditorialPresentation(payload, "HEALTH_SOCIAL", identity);
    assert.equal(health.tier, payload.scope === "118" ? "receipts_only" : "bounded_choice_review");
    for (const p of payload.presentations.filter((p) => p.issue_id !== "HEALTH_SOCIAL")) {
      assert.deepEqual(p, transport.baselines[i].presentations.find((b) => b.issue_id === p.issue_id));
      assert.deepEqual(getEditorialPresentation(payload, p.issue_id, identity), p);
    }
    if (payload.scope !== "118") {
      assert.equal(isPublicAnalysisAvailable(health), false);
      const [row] = buildIssueOverviewRows({ rows: [{domain:"HEALTH_SOCIAL"}], presentations: new Map([["HEALTH_SOCIAL",health]]) });
      assert.equal(row.analysisAvailable, false);
      assert.equal(row.boundedChoiceAvailable, payload.member_bioguide_id === "F000477");
      assert.equal(row.boundedAccountingAvailable, payload.member_bioguide_id === "M001184");
    }
    assert.equal(getEditorialPresentation(payload, "HEALTH_SOCIAL", { ...identity, memberBioguideId: "wrong" }), null);
  });
  if (payload.scope === "118") continue;
  for (const mutate of [
    (p) => delete p.requested_scope, (p) => p.requested_scope="118", (p) => p.bounded_choice.member_id="wrong",
    (p) => p.bounded_choice.congress=true, (p) => p.bounded_choice.display_role="primary", (p) => delete p.bounded_choice.records.qualifications,
    (p) => p.bounded_choice.records.scope_label.mapping.action_ids=[], (p) => p.bounded_choice.boundaries=[],
    (p) => p.conclusion={body:"Overall Health"}, (p) => p.review_state.full_issue_synthesis_eligible=true,
  ]) test(`${payload.member_bioguide_id} ${payload.scope}: malformed bounded transport ${mutate}`, () => {
    const copy=structuredClone(payload); mutate(copy.presentations.find((p) => p.issue_id==="HEALTH_SOCIAL"));
    assert.notEqual(issuePresentationStatus(copy, identity, payload.scope), "ready");
    assert.equal(getEditorialPresentation(copy,"HEALTH_SOCIAL",identity),null);
    for (const p of payload.presentations.filter((p) => p.issue_id!=="HEALTH_SOCIAL")) assert.deepEqual(getEditorialPresentation(copy,p.issue_id,identity),p);
  });
}
