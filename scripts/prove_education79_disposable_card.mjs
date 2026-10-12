// Resolve the inert manifest from actual fixture IDs and runtime responses.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {bindCompleteEducationScopes, proveEducationCardStates} from './education79_card_proof.mjs';

const output = path.resolve(process.argv[2]);
const report = JSON.parse(fs.readFileSync(path.join(output, 'disposable-proof.json'), 'utf8'));
assert.equal(report.disposable_only, true);
assert.equal(report.production_execution_authorized, false);
assert.equal(report.activation_authority.test_only_synthetic, true);
const root = path.resolve(import.meta.dirname, '..');
const current = JSON.parse(fs.readFileSync(path.join(root, 'frontend/lib/recordCardContent.json'), 'utf8'));
const afterByScope = Object.fromEntries(['119', 'all'].map(scope => [scope, report.after[`leg_valerie_p_foushee:${scope}:editorial`]]));
const derived = await bindCompleteEducationScopes(current, afterByScope);
const source = derived.sources.find(s => s.issue_id === 'EDUCATION_WORKFORCE');
const identity = report.write_set.subject.proposed_new;
source.published_artifact_id = identity.artifact_id;
source.published_natural_key = identity.natural_key;
source.artifact_version = identity.artifact_version;
source.content_sha256 = identity.content_sha256;
derived.release_preparation_only = true;
derived.production_execution_authorized = false;
const proof = {disposable_only: true, production_execution_authorized: false,
  resolved_fixture_artifact_id: identity.artifact_id, complete_six_findings_unchanged: true, scopes: {}};
for (const scope of ['119', 'all']) {
  const key = `leg_valerie_p_foushee:${scope}:editorial`;
  const before = report.before[key], after = report.after[key];
  const states = await proveEducationCardStates({current, derived, before, after, scope});
  proof.scopes[scope] = {...states, new_presentation_sha256: source.presentation_sha256[scope]};
}
fs.writeFileSync(path.join(output, 'record-card-content.disposable.json'), JSON.stringify(derived, null, 2) + '\n');
fs.writeFileSync(path.join(output, 'card-runtime-proof.json'), JSON.stringify(proof, null, 2) + '\n');
console.log('PASS actual fixture: historical clients reject new source; bridge and complete derived bindings retain six findings through activation/rollback; mixed and unknown states reject.');
