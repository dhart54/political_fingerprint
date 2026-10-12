// Fixture-only proof of historical single-hash clients and the bounded bridge.
// No Git-history dependency: shallow exact-head CI can replay this boundary.
import assert from 'node:assert/strict';
import {contentHash, projectRecordCard, recordCardUrl} from '../frontend/lib/recordCard.mjs';

export async function bindCompleteEducationScopes(candidate, afterByScope) {
  const derived = structuredClone(candidate);
  const source = derived.sources.find(s => s.issue_id === 'EDUCATION_WORKFORCE');
  for (const scope of ['119', 'all']) {
    source.presentation_sha256[scope] = await contentHash(afterByScope[scope].presentations.find(p => p.issue_id === source.issue_id));
  }
  return derived;
}

async function historicalSingleHashClient(args) {
  // Reconstruct only the original complete-presentation hash boundary, over
  // these identity-valid fixtures. Remaining guards still run in the projector.
  for (const source of args.candidate.sources) {
    const p = args.payload.presentations.find(p => p.issue_id === source.issue_id);
    if (!p || await contentHash(p) !== source.presentation_sha256[args.scope]) {
      return {status: 'source_mismatch', entries: []};
    }
  }
  return projectRecordCard(args);
}

export async function proveEducationCardStates({current, derived, before, after, scope}) {
  const args = {legislatorId: 'leg_valerie_p_foushee', memberBioguideId: 'F000477', scope};
  const old = await historicalSingleHashClient({candidate: current, payload: before, ...args});
  const historicalAfter = await historicalSingleHashClient({candidate: current, payload: after, ...args});
  assert.equal(old.status, 'ready'); assert.equal(old.entries.length, 6);
  assert.equal(historicalAfter.status, 'source_mismatch'); assert.equal(historicalAfter.entries.length, 0);
  const bridgeBefore = await projectRecordCard({candidate: current, payload: before, ...args});
  const bridgeAfter = await projectRecordCard({candidate: current, payload: after, ...args});
  const prepared = await projectRecordCard({candidate: derived, payload: after, ...args});
  const derivedRollback = await projectRecordCard({candidate: derived, payload: before, ...args});
  for (const [model, payload] of [[bridgeBefore, before], [bridgeAfter, after], [prepared, after], [derivedRollback, before]]) {
    assert.equal(model.status, 'ready'); assert.equal(model.entries.length, 6);
    assert.deepEqual(model.entries.map(e => e.sourceFinding), old.entries.map(e => e.sourceFinding));
    for (const entry of model.entries) {
      const actual = await contentHash(payload.presentations.find(p => p.issue_id === entry.issue_id));
      assert.equal(entry.sourcePresentationHash, actual);
      const url = new URL(recordCardUrl('/', {legislatorId: args.legislatorId, scope, issue: entry.issue_id, findingId: entry.finding_id, sourceHash: entry.sourcePresentationHash}), 'http://localhost');
      assert.equal(url.searchParams.get('source'), actual);
    }
  }
  const semantic = model => model.entries.map(({sourcePresentationHash, ...entry}) => entry);
  assert.deepEqual(semantic(bridgeBefore), semantic(bridgeAfter));
  assert.deepEqual(derived.entries, current.entries);
  const primary = candidate => candidate.sources.find(s => s.issue_id === 'EDUCATION_WORKFORCE');
  for (const [start, other] of [[current, derived], [derived, current]]) {
    const mixed = structuredClone(start);
    primary(mixed).presentation_sha256.all = primary(other).presentation_sha256.all;
    for (const payload of [before, after]) {
      const rejected = await projectRecordCard({candidate: mixed, payload, ...args});
      assert.equal(rejected.status, 'source_mismatch'); assert.equal(rejected.entries.length, 0);
    }
  }
  const unknown = structuredClone(after);
  unknown.presentations.find(p => p.issue_id === 'EDUCATION_WORKFORCE').provenance.unreviewed_proof_mutation = true;
  for (const candidate of [current, derived]) {
    const rejected = await projectRecordCard({candidate, payload: unknown, ...args});
    assert.equal(rejected.status, 'source_mismatch'); assert.equal(rejected.entries.length, 0);
  }
  return {
    historical_pre_bridge_after: historicalAfter.status,
    bridge_before: bridgeBefore.status, bridge_after: bridgeAfter.status,
    complete_derived_after: prepared.status, complete_derived_registry_rollback: derivedRollback.status,
    entries: prepared.entries.length, actual_current_hash_links_verified: true,
    identical_six_source_findings_verified: true, mixed_families_rejected: true, unknown_projection_rejected: true,
  };
}
