// Offline consequence/rebinding proof. Never imports the prepared data into the app.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {gunzipSync} from 'node:zlib';
import {contentHash,projectRecordCard,canonicalJson} from '../frontend/lib/recordCard.mjs';
const root=path.resolve(import.meta.dirname,'..');
const packet=path.join(root,'docs/review_packets/education79_locator_v1');
const load=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const current=load('frontend/lib/recordCardContent.json');
const review=load('docs/review_packets/record_at_a_glance_v1/candidate.json');
const oldSnapshot=JSON.parse(gunzipSync(fs.readFileSync(path.join(root,review.source_snapshot))));
const newSnapshot=JSON.parse(gunzipSync(fs.readFileSync(path.join(packet,'prepared/expected-public-after.json.gz'))));
const proposal=load('docs/review_packets/education79_locator_v1/prepared/persistence-preparation.json');
const sourceProof=load('docs/review_packets/education79_locator_v1/prepared/live-and-source-proof.json');
const derived=structuredClone(current);
const source=derived.sources.find(s=>s.issue_id==='EDUCATION_WORKFORCE');
source.published_artifact_id=null; // Resolve only after separately authorized immutable persistence.
source.published_natural_key=proposal.candidate.natural_key;
source.artifact_version=proposal.candidate.artifact_version;
source.content_sha256=proposal.candidate.content_sha256;
derived.source_snapshot='docs/review_packets/education79_locator_v1/prepared/expected-public-after.json.gz';
derived.source_snapshot_sha256=sourceProof.expected_snapshot_sha256;
derived.release_preparation_only=true;
derived.production_execution_authorized=false;
derived.source_snapshot_kind='offline_predicted_after_state';
const proof={production_execution_authorized:false,findings_text_direction_order_actions_unchanged:true,
 unresolved_binding:'published_artifact_id is null pending separately authorized persistence',scopes:{}};
for(const scope of ['119','all']){
 const key=`leg_valerie_p_foushee:${scope}:editorial`;
 const before=oldSnapshot[key].body,after=newSnapshot[key].body;
 const args={legislatorId:'leg_valerie_p_foushee',memberBioguideId:'F000477',scope};
 const old=await projectRecordCard({candidate:current,payload:before,...args});assert.equal(old.status,'ready');
 const mismatched=await projectRecordCard({candidate:current,payload:after,...args});assert.equal(mismatched.status,'source_mismatch');
 const p=after.presentations.find(p=>p.issue_id==='EDUCATION_WORKFORCE');source.presentation_sha256[scope]=await contentHash(p);
 const prepared=await projectRecordCard({candidate:derived,payload:after,...args});assert.equal(prepared.status,'ready');
 assert.equal(prepared.entries.length,6);
 assert.equal(canonicalJson(derived.entries),canonicalJson(current.entries));
 assert.equal(canonicalJson(prepared.entries.map(e=>e.sourceFinding)),canonicalJson(old.entries.map(e=>e.sourceFinding)));
 proof.scopes[scope]={old_manifest_after_locator:mismatched.status,derived_manifest_after_locator:prepared.status,entries:prepared.entries.length,
   prior_presentation_sha256:current.sources.find(s=>s.issue_id==='EDUCATION_WORKFORCE').presentation_sha256[scope],new_presentation_sha256:source.presentation_sha256[scope]};
}
for(const [name,value] of [['record-card-content.candidate.json',derived],['record-card-rebinding-proof.json',proof]]){
 const file=path.join(packet,'prepared',name);const text=JSON.stringify(value,null,2)+'\n';
 if(process.argv.includes('--check'))assert.equal(fs.readFileSync(file,'utf8'),text);else fs.writeFileSync(file,text);
}
console.log('PASS both scopes: existing manifest would withhold entire card; derived candidate restores identical six findings. No active frontend data changed.');
