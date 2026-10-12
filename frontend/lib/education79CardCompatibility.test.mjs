import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import test from 'node:test';
import {contentHash, FINDING_FIELDS, findingIdentity, projectRecordCard, recordCardUrl, resolveCardFinding} from './recordCard.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const candidate = JSON.parse(fs.readFileSync(path.join(root, 'frontend/lib/recordCardContent.json'), 'utf8'));
const historical = JSON.parse(fs.readFileSync(path.join(root, 'docs/review_packets/record_at_a_glance_v1/candidate.json'), 'utf8'));
const before = JSON.parse(gunzipSync(fs.readFileSync(path.join(root, historical.source_snapshot))));
const after = JSON.parse(gunzipSync(fs.readFileSync(path.join(root, 'docs/review_packets/education79_locator_v1/prepared/expected-public-after.json.gz'))));
const hashes = {
  '119': {old: '605b5f87771c63fdcdf76512072f21b19d5540cae54785a473c2bd3f86018826', locator: 'aaeeb85d5dc44c54ff988fc7ef458081a568858f4ee7601ee6adceaea7646e15'},
  all: {old: 'f5177c9cbd08aa073d705855a6fb74895a6429a5cc3528d852ab4d0d96398539', locator: 'ff7ce88bb3bb40545abe849850b27562cf0e2d5ff902b71b0eb3663cf426d9b0'},
};
const education = payload => payload.presentations.find(p => p.issue_id === 'EDUCATION_WORKFORCE');
const source = manifest => manifest.sources.find(s => s.issue_id === 'EDUCATION_WORKFORCE');
const selected = candidate.entries.find(e => e.issue_id === 'EDUCATION_WORKFORCE');
const finding = payload => education(payload)[selected.field].find(f => findingIdentity(f) === selected.finding_id);
const omitted = payload => FINDING_FIELDS.flatMap(field => education(payload)[field] || []).find(f => !candidate.entries.some(e => e.issue_id === 'EDUCATION_WORKFORCE' && e.finding_id === findingIdentity(f)));
const args = (payload, scope, manifest = candidate) => ({candidate: manifest, payload, scope, legislatorId: candidate.legislator_id, memberBioguideId: candidate.member_bioguide_id});
const semanticEntries = model => model.entries.map(({sourcePresentationHash, ...entry}) => entry);

for (const scope of ['119', 'all']) {
  const key = `${candidate.legislator_id}:${scope}:editorial`;
  const oldPayload = before[key].body, newPayload = after[key].body;
  test(`${scope}: exact old/new states and registry rollback preserve the same six entries`, async () => {
    assert.equal(await contentHash(education(oldPayload)), hashes[scope].old);
    assert.equal(await contentHash(education(newPayload)), hashes[scope].locator);
    const oldModel = await projectRecordCard(args(oldPayload, scope));
    const newModel = await projectRecordCard(args(newPayload, scope));
    const restored = await projectRecordCard(args(oldPayload, scope));
    for (const model of [oldModel, newModel, restored]) {
      assert.equal(model.status, 'ready'); assert.equal(model.entries.length, 6);
      assert.deepEqual(model.evidenceCoverage, oldModel.evidenceCoverage);
    }
    assert.deepEqual(semanticEntries(newModel), semanticEntries(oldModel));
    assert.deepEqual(restored, oldModel);
    for (const model of [oldModel, newModel]) for (const entry of model.entries) {
      assert.equal(entry.sourcePresentationHash, await contentHash((model === oldModel ? oldPayload : newPayload).presentations.find(p => p.issue_id === entry.issue_id)));
      const url = new URL(recordCardUrl('/', {legislatorId: candidate.legislator_id, scope, issue: entry.issue_id, findingId: entry.finding_id, sourceHash: entry.sourcePresentationHash}), 'http://localhost');
      assert.equal(url.searchParams.get('source'), entry.sourcePresentationHash);
    }
  });
  test(`${scope}: new content uses its actual hash; old deep link remains an honest fallback`, async () => {
    const model = await projectRecordCard(args(newPayload, scope));
    assert.equal(resolveCardFinding(model, selected.issue_id, selected.finding_id, hashes[scope].old), null);
    assert.deepEqual(resolveCardFinding(model, selected.issue_id, selected.finding_id, hashes[scope].locator).action_ids, selected.action_ids);
    const rolledBack = await projectRecordCard(args(oldPayload, scope));
    assert.equal(resolveCardFinding(rolledBack, selected.issue_id, selected.finding_id, hashes[scope].locator), null);
    assert.ok(resolveCardFinding(rolledBack, selected.issue_id, selected.finding_id, hashes[scope].old));
  });
  test(`${scope}: a complete locator-primary manifest also retains exactly the two approved states`, async () => {
    const locatorManifest = structuredClone(candidate);
    source(locatorManifest).presentation_sha256 = {119: hashes['119'].locator, all: hashes.all.locator};
    for (const payload of [oldPayload, newPayload]) {
      const model = await projectRecordCard(args(payload, scope, locatorManifest));
      assert.equal(model.status, 'ready'); assert.equal(model.entries.length, 6);
      assert.equal(model.entries.find(e => e.issue_id === selected.issue_id).sourcePresentationHash, await contentHash(education(payload)));
    }
  });
  for (const [state, pristine] of [['old', oldPayload], ['locator', newPayload]]) {
    const mutations = {
      omitted_finding: p => { omitted(p).public_title += ' altered'; },
      provenance: p => { education(p).provenance.compatibility_test = 'altered'; },
      coverage_boundary: p => { education(p).scope_boundary += ' altered'; },
      selected_direction: p => { finding(p).direction = 'support'; },
      selected_actions: p => { finding(p).action_ids = finding(p).action_ids.slice(0, 1); },
      selected_finding_text: p => { finding(p).public_title += ' altered'; },
      unrelated_domain: p => { p.presentations.find(p => p.issue_id === 'NATIONAL_SECURITY_FOREIGN').teaser += ' altered'; },
      candidate_preview: p => { education(p).review_state.candidate_preview = true; },
      congress_scope: p => { education(p).review_state.congress_scope = [118]; },
    };
    for (const [label, mutate] of Object.entries(mutations)) test(`${scope}/${state}: ${label} fails closed`, async () => {
      const payload = structuredClone(pristine); mutate(payload);
      const model = await projectRecordCard(args(payload, scope));
      assert.equal(model.status, 'source_mismatch'); assert.equal(model.entries.length, 0);
    });
    for (const [label, mutate] of Object.entries({
      coverage: m => { source(m).evidence_coverage[scope].source_text += ' altered'; },
      finding_hash: m => { m.entries.find(e => e.issue_id === selected.issue_id).finding_sha256 = '0'.repeat(64); },
      direction: m => { m.entries.find(e => e.issue_id === selected.issue_id).section = 'opposition'; },
      action_list: m => { m.entries.find(e => e.issue_id === selected.issue_id).action_ids = []; },
    })) test(`${scope}/${state}: reviewed selection ${label} check remains enforced`, async () => {
      const manifest = structuredClone(candidate); mutate(manifest);
      assert.equal((await projectRecordCard(args(pristine, scope, manifest))).status, 'source_mismatch');
    });
  }
  test(`${scope}: unknown presentation cannot self-authorize through candidate hashes or injected alternates`, async () => {
    const payload = structuredClone(newPayload); education(payload).provenance.compatibility_test = 'unknown';
    const manifest = structuredClone(candidate);
    const unknown = await contentHash(education(payload));
    source(manifest).presentation_sha256[scope] = unknown;
    assert.equal((await projectRecordCard(args(payload, scope, manifest))).status, 'source_mismatch');
    source(manifest).presentation_sha256 = structuredClone(source(candidate).presentation_sha256);
    source(manifest).presentation_sha256_alternates = {[scope]: [unknown]};
    assert.equal((await projectRecordCard(args(payload, scope, manifest))).status, 'source_mismatch');
  });
  test(`${scope}: partial or cross-scope source-manifest combinations are not approved families`, async () => {
    const mixed = structuredClone(candidate); source(mixed).presentation_sha256.all = hashes.all.locator;
    assert.equal((await projectRecordCard(args(newPayload, scope, mixed))).status, 'source_mismatch');
    const extra = structuredClone(candidate); source(extra).presentation_sha256['118'] = hashes[scope].locator;
    assert.equal((await projectRecordCard(args(newPayload, scope, extra))).status, 'source_mismatch');
    const swapped = structuredClone(candidate); source(swapped).presentation_sha256 = {119: hashes.all.locator, all: hashes['119'].locator};
    assert.equal((await projectRecordCard(args(newPayload, scope, swapped))).status, 'source_mismatch');
  });
  test(`${scope}: member, legislator and scope guards remain enforced`, async () => {
    for (const field of ['member_bioguide_id', 'legislator_id', 'scope']) {
      const payload = structuredClone(newPayload); payload[field] = 'WRONG';
      assert.equal((await projectRecordCard(args(payload, scope))).status, 'identity_mismatch');
    }
    const payload = structuredClone(newPayload);
    const manifest = structuredClone(candidate);
    payload.legislator_id = manifest.legislator_id = 'leg_thomas_massie';
    payload.member_bioguide_id = manifest.member_bioguide_id = 'M001184';
    assert.equal((await projectRecordCard({...args(payload, scope, manifest), legislatorId: manifest.legislator_id, memberBioguideId: manifest.member_bioguide_id})).status, 'source_mismatch');
    const wrongScope = structuredClone(newPayload); education(wrongScope).requested_scope = scope === '119' ? 'all' : '119';
    assert.equal((await projectRecordCard(args(wrongScope, scope))).status, 'source_mismatch');
  });
  test(`${scope}: only the exact complete locator value matches; partial URI mutations reject`, async () => {
    const deltas = [];
    function walk(a, b, keys = []) {
      if (a === b) return;
      if (a && b && typeof a === 'object' && typeof b === 'object') {
        assert.deepEqual(Object.keys(a), Object.keys(b));
        for (const key of Object.keys(a)) walk(a[key], b[key], [...keys, key]);
      } else deltas.push({keys, value: b});
    }
    walk(education(oldPayload), education(newPayload));
    assert.equal(deltas.length, 1);
    for (const delta of deltas) {
      assert.equal(delta.keys.at(-1), 'url');
      const partial = structuredClone(oldPayload);
      let cursor = education(partial);
      for (const key of delta.keys.slice(0, -1)) cursor = cursor[key];
      cursor[delta.keys.at(-1)] = delta.value;
      assert.equal((await projectRecordCard(args(partial, scope))).status, 'ready', 'The one exact URI leaf produces the complete reviewed new projection');
      cursor[delta.keys.at(-1)] = delta.value + '?unreviewed=1';
      const model = await projectRecordCard(args(partial, scope));
      assert.equal(model.status, 'source_mismatch'); assert.equal(model.entries.length, 0);
    }
  });
}
