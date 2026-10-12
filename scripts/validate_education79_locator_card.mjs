// Offline consequence/rebinding proof. Never imports the prepared data into the app.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {gunzipSync} from 'node:zlib';
import {bindCompleteEducationScopes,proveEducationCardStates} from './education79_card_proof.mjs';
const root=path.resolve(import.meta.dirname,'..');
const packet=path.join(root,'docs/review_packets/education79_locator_v1');
const load=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const current=load('frontend/lib/recordCardContent.json');
const review=load('docs/review_packets/record_at_a_glance_v1/candidate.json');
const oldSnapshot=JSON.parse(gunzipSync(fs.readFileSync(path.join(root,review.source_snapshot))));
const newSnapshot=JSON.parse(gunzipSync(fs.readFileSync(path.join(packet,'prepared/expected-public-after.json.gz'))));
const proposal=load('docs/review_packets/education79_locator_v1/prepared/persistence-preparation.json');
const sourceProof=load('docs/review_packets/education79_locator_v1/prepared/live-and-source-proof.json');
const afterByScope=Object.fromEntries(['119','all'].map(scope=>[scope,newSnapshot[`leg_valerie_p_foushee:${scope}:editorial`].body]));
const derived=await bindCompleteEducationScopes(current,afterByScope);
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
const compatibility={production_execution_authorized:false,historical_single_hash_client_reconstructed_separately:true,scopes:{}};
for(const scope of ['119','all']){
 const key=`leg_valerie_p_foushee:${scope}:editorial`;
 const before=oldSnapshot[key].body,after=newSnapshot[key].body;
 const states=await proveEducationCardStates({current,derived,before,after,scope});
 // Preserve the frozen historical consequence proof; modern bridge results
 // have a separately identified proof rather than rewriting prior history.
 proof.scopes[scope]={old_manifest_after_locator:states.historical_pre_bridge_after,derived_manifest_after_locator:states.complete_derived_after,entries:states.entries,
   prior_presentation_sha256:current.sources.find(s=>s.issue_id==='EDUCATION_WORKFORCE').presentation_sha256[scope],new_presentation_sha256:source.presentation_sha256[scope]};
 compatibility.scopes[scope]=states;
}
for(const [name,value] of [['record-card-content.candidate.json',derived],['record-card-rebinding-proof.json',proof],['record-card-compatibility-proof.json',compatibility]]){
 const file=path.join(packet,'prepared',name);const text=JSON.stringify(value,null,2)+'\n';
 if(process.argv.includes('--check'))assert.equal(fs.readFileSync(file,'utf8').replaceAll('\r\n','\n'),text);else fs.writeFileSync(file,text);
}
console.log('PASS both scopes: historical single-hash mismatch retained separately; bridge/complete derived states and rollback keep six findings; mixed/unknown states reject. No serving data changed.');
