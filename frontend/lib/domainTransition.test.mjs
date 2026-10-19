import assert from "node:assert/strict";
import test from "node:test";
import { contentHash, projectRecordCard, reviewedPresentations } from "./recordCard.mjs";
import { issuePresentationStatus } from "./editorialPresentation.mjs";
import {
  makeDomainTransitionFixture, SYNTHETIC_DOMAIN, SYNTHETIC_ROOT,
  TRANSITION_SCOPES, transitionIdentity,
} from "../tests/fixtures/domain-transition.mjs";

const args = (fixture, scope, manifest = "four", payload = "four") => ({
  ...transitionIdentity, scope,
  candidate: fixture.manifests[manifest], payload: fixture.payloads[payload][scope],
});
const fifth = (payload) => payload.presentations.find((p) => p.issue_id === SYNTHETIC_DOMAIN);
const fifthSource = (candidate) => candidate.sources.find((s) => s.issue_id === SYNTHETIC_DOMAIN);

for (const scope of TRANSITION_SCOPES) {
  test(`${scope}: staged synthetic artifacts leave the exact four-domain serving pair unchanged`, async () => {
    const fixture = await makeDomainTransitionFixture();
    const before = await contentHash({ candidate: fixture.manifests.four, payload: fixture.payloads.four[scope] });
    assert.equal(fixture.synthetic_test_only, true);
    assert.deepEqual(fixture.staged, { root: SYNTHETIC_ROOT, activated: false, publication_eligible: false });
    const current = await projectRecordCard(args(fixture, scope));
    assert.equal(current.status, "ready");
    assert.equal(current.entries.length, 6);
    assert.deepEqual(current.reviewedDomains, ["EDUCATION_WORKFORCE", "ENVIRONMENT_ENERGY", "JUSTICE_PUBLIC_SAFETY", "NATIONAL_SECURITY_FOREIGN"]);
    assert.equal(reviewedPresentations(fixture.payloads.five[scope]).length, 5);
    assert.equal(await contentHash({ candidate: fixture.manifests.four, payload: fixture.payloads.four[scope] }), before);
    assert.ok(!JSON.stringify(fixture.manifests.four).includes(SYNTHETIC_ROOT));
  });

  test(`${scope}: exact pairing matrix withholds both mismatches without invalidating issue payloads`, async () => {
    const fixture = await makeDomainTransitionFixture();
    const current = await projectRecordCard(args(fixture, scope));
    for (const [manifest, payload, status] of [
      ["four", "four", "ready"], ["four", "five", "source_mismatch"],
      ["five", "four", "incomplete"], ["five", "five", "ready"],
    ]) {
      const input = args(fixture, scope, manifest, payload);
      assert.equal(issuePresentationStatus(input.payload, transitionIdentity, scope), "ready");
      const model = await projectRecordCard(input);
      assert.equal(model.status, status, `${manifest}/${payload}`);
      assert.equal(model.entries.length, status === "ready" ? 6 : 0);
      if (status === "ready") assert.deepEqual(model.entries, current.entries);
      if (manifest === "five" && payload === "five") {
        assert.equal(model.reviewedDomains.length, 5);
        assert.ok(model.reviewedDomains.includes(SYNTHETIC_DOMAIN));
        assert.equal(model.evidenceCoverage.length, 5);
      }
    }
  });

  test(`${scope}: both activation and rollback orders preserve mismatch guards and exact restoration`, async () => {
    const fixture = await makeDomainTransitionFixture();
    const untouched = await contentHash(fixture);
    const original = await projectRecordCard(args(fixture, scope));
    const paths = {
      manifest_first_activation: [["four", "four", "ready"], ["five", "four", "incomplete"], ["five", "five", "ready"]],
      serving_first_activation: [["four", "four", "ready"], ["four", "five", "source_mismatch"], ["five", "five", "ready"]],
      manifest_first_rollback: [["five", "five", "ready"], ["four", "five", "source_mismatch"], ["four", "four", "ready"]],
      serving_first_rollback: [["five", "five", "ready"], ["five", "four", "incomplete"], ["four", "four", "ready"]],
    };
    for (const [name, steps] of Object.entries(paths)) {
      for (const [manifest, payload, status] of steps) {
        const model = await projectRecordCard(args(fixture, scope, manifest, payload));
        assert.equal(model.status, status, name);
        assert.equal(model.entries.length, status === "ready" ? 6 : 0);
      }
    }
    assert.deepEqual(await projectRecordCard(args(fixture, scope)), original);
    assert.deepEqual(await projectRecordCard(args(fixture, scope)), original, "restored reads are idempotent");
    assert.equal(await contentHash(fixture), untouched, "projection/rollback rehearsal must not mutate either pair or staged data");
  });

  test(`${scope}: a stale opposite-scope response cannot satisfy the requested pair`, async () => {
    const fixture = await makeDomainTransitionFixture();
    const other = scope === "119" ? "all" : "119";
    const input = { ...args(fixture, scope, "five", "five"), payload: fixture.payloads.five[other] };
    assert.equal(issuePresentationStatus(input.payload, transitionIdentity, scope), "identity_mismatch");
    const model = await projectRecordCard(input);
    assert.equal(model.status, "identity_mismatch");
    assert.deepEqual(model.entries, []);
  });

  const faults = {
    wrong_fifth_root: { mutate: (input) => { fifth(input.payload).provenance.artifact_id = "test-only:wrong-root"; } },
    wrong_existing_root: { mutate: (input) => { input.payload.presentations.find((p) => p.issue_id === "JUSTICE_PUBLIC_SAFETY").provenance.artifact_id = "test-only:wrong-existing-root"; } },
    wrong_presentation_hash: { mutate: (input) => { fifthSource(input.candidate).presentation_sha256[scope] = "0".repeat(64); } },
    wrong_coverage_hash: { mutate: (input) => { fifthSource(input.candidate).evidence_coverage[scope].source_sha256 = "0".repeat(64); } },
    wrong_member: { status: "identity_mismatch", mutate: (input) => { input.payload.member_bioguide_id = "TEST_WRONG"; } },
    wrong_legislator: { status: "identity_mismatch", mutate: (input) => { input.payload.legislator_id = "test_only_wrong_member"; } },
    wrong_scope: { status: "identity_mismatch", mutate: (input) => { input.payload.scope = "118"; } },
    wrong_manifest_member: { status: "not_selected", mutate: (input) => { input.candidate.member_bioguide_id = "TEST_WRONG"; } },
    wrong_manifest_scope: { status: "not_selected", mutate: (input) => { input.candidate.scopes = ["118"]; } },
    wrong_requested_scope_even_if_rehashed: { mutate: async (input) => {
      fifth(input.payload).requested_scope = "118";
      fifthSource(input.candidate).presentation_sha256[scope] = await contentHash(fifth(input.payload));
    } },
    wrong_reviewed_scope_even_if_rehashed: { mutate: async (input) => {
      fifth(input.payload).reviewed_scope = "118";
      fifthSource(input.candidate).presentation_sha256[scope] = await contentHash(fifth(input.payload));
    } },
    wrong_congress_even_if_rehashed: { mutate: async (input) => {
      fifth(input.payload).review_state.congress_scope = [118];
      fifthSource(input.candidate).presentation_sha256[scope] = await contentHash(fifth(input.payload));
    } },
    missing_domain: { status: "incomplete", mutate: (input) => { input.payload.presentations.pop(); } },
    duplicate_domain: { status: "incomplete", mutate: (input) => { input.payload.presentations[1] = structuredClone(fifth(input.payload)); } },
  };
  for (const [name, { mutate, status = "source_mismatch" }] of Object.entries(faults)) {
    test(`${scope}: synthetic target rejects ${name}`, async () => {
      const fixture = await makeDomainTransitionFixture();
      const input = args(fixture, scope, "five", "five");
      await mutate(input);
      const model = await projectRecordCard(input);
      assert.equal(model.status, status);
      assert.deepEqual(model.entries, []);
    });
  }
}
