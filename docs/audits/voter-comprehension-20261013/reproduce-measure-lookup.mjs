// Offline diagnosis of the unmodified captured public response. No network or writes.
// --regression asserts the desired lookup behavior and intentionally fails at d81eec08.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { gunzipSync } from 'node:zlib';
import { createHash } from 'node:crypto';
import { filterLoadedReceipts, normalizeLocalRecordQuery } from '../../../frontend/lib/localRecordFilter.mjs';
import { getActionPresentation } from '../../../frontend/lib/selectedIssueExperience.mjs';

const directory = new URL('./', import.meta.url);
const manifest = JSON.parse(fs.readFileSync(new URL('manifest.json', directory)));
for (const entry of manifest.records) {
  const bytes = fs.readFileSync(new URL(entry.path, directory));
  const expanded = entry.path.endsWith('.gz') ? gunzipSync(bytes) : bytes;
  const decoded = entry.sha256Mode === 'lf-normalized'
    ? Buffer.from(expanded.toString('utf8').replace(/\r\n/g, '\n')) : expanded;
  assert.equal(createHash('sha256').update(decoded).digest('hex'), entry.decodedSha256, entry.path);
  assert.equal(decoded.length, entry.decodedBytes, entry.path);
}
function readCaptured(name) {
  const decoded = gunzipSync(fs.readFileSync(new URL(name, directory)));
  const entry = manifest.records.find(record => record.path === name);
  assert.equal(createHash('sha256').update(decoded).digest('hex'), entry.decodedSha256);
  return decoded.toString('utf8');
}
const response = JSON.parse(readCaptured('live-evidence.json.gz'));
const officialXml = readCaptured('roll282.xml.gz');
const targetId = 'house:119:2:282';
const target = response.evidence.find(row => row.canonical_action_id === targetId);
assert.equal(response.legislator_id, 'leg_valerie_p_foushee');
assert.equal(response.domain, 'NATIONAL_SECURITY_FOREIGN');
assert.equal(String(response.scope), '119');
assert.equal(response.evidence.length, 93);
assert.ok(target);
assert.equal(target.source_url, manifest.officialVoteUrl);
assert.equal(target.congress, 119);
assert.equal(target.session, 2);
assert.equal(target.rollcall_number, 282);
assert.equal(target.position, 'yea');
assert.match(officialXml, /<congress>119<\/congress>/);
assert.match(officialXml, /<session>2nd<\/session>/);
assert.match(officialXml, /<rollcall-num>282<\/rollcall-num>/);
assert.match(officialXml, /<legis-num>H CON RES 89<\/legis-num>/);
assert.match(officialXml, /<legislator name-id="F000477"[^>]*>Foushee<\/legislator>\s*<vote>Yea<\/vote>/);

const identityFields = ['source_bill_id', 'bill_id', 'bill_ref', 'bill_identifier', 'roll_call_bill_id', 'roll_call_bill_ref', 'bill_congress', 'bill_type', 'bill_number', 'parent_bill_type', 'parent_bill_number', 'parent_bill_display'];
const suppliedIdentity = [target, target.raw_evidence, target.vote_context, target.governed_receipt_projection]
  .filter(Boolean).flatMap(object => identityFields.filter(field => object[field] != null && String(object[field]).trim()));
assert.deepEqual(suppliedIdentity, []);
for (const query of ['H.Con.Res. 89', 'hconres89', 'h con res 89']) {
  assert.equal(normalizeLocalRecordQuery(query), 'hconres 89');
  // Existing normalization succeeds when the identifier is actually printed.
  const printed = { ...target, bill_title: 'H.Con.Res. 89' };
  assert.deepEqual(filterLoadedReceipts([printed], query), [printed]);
}
const ids = query => filterLoadedReceipts(response.evidence, query).map(row => row.canonical_action_id);
const diagnosis = {
  codeBase: manifest.codeBase, evidenceUrl: manifest.evidenceUrl,
  officialVoteUrl: manifest.officialVoteUrl,
  loadedCount: response.evidence.length, targetId,
  targetIdentityFields: suppliedIdentity,
  printedMatcherInputs: getActionPresentation(target),
  chamberRollInput: `${target.chamber} Roll ${target.rollcall_number}`,
  normalizedMeasureQuery: normalizeLocalRecordQuery('H.Con.Res. 89'),
  measureMatches: ids('H.Con.Res. 89'), rollMatches: ids('roll 282'),
  conclusion: 'Structured measure identity is absent from the loaded response; normalization works. No frontend ID is inferred from prose or URLs.',
};
console.log(JSON.stringify(diagnosis, null, 2));
assert.ok(diagnosis.rollMatches.includes(targetId));
assert.ok(!diagnosis.measureMatches.includes(targetId));
if (process.argv.includes('--regression')) {
  assert.ok(diagnosis.measureMatches.includes(targetId), 'Desired regression: H.Con.Res. 89 must find the already loaded house:119:2:282 receipt');
}
