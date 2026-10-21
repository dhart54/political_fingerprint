"""Replay five isolated land/siting/easement candidates without admission authority."""
import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pypdf import PdfReader
import io

from backend.app.semantic_ir.shared_corpus import digest, sealed_digest
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates
from scripts.validate_infrastructure_disaster_candidates142 import (
    reconstruct_capture, normalized_pdf, sha, TextParser,
)

PACKET = ROOT/'docs/review_packets/infrastructure_batch143_land_siting_easements'
BASE = ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch139_20260916'
ACTIONS = ['house:119:1:18','house:119:1:22','house:119:1:28','house:119:2:188','house:119:2:260']
MEMBERS = ['F000477','M001184']
OUTPUTS = ['shared_action_core','shared_issue_mapping','member_projections','compiler_input','compiled_ir','readable_candidates']
BUNDLE_SHA = '306217a1abe8ec449a5abacc6abfa1e7ae21ea73e8e102f22810f2bb947a72a3'
MANIFEST_SHA = 'a383154f4b060d7276e2f9fb95e8a735e69479a9dc05f8e05f0473432dde659e'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def require(value,message):
    if not value:
        raise ValueError(message)


def validate_transport():
    receipt=read(PACKET/'packet_manifest.json')
    require(digest(receipt)==MANIFEST_SHA,'Frozen packet manifest differs')
    actual={p.relative_to(PACKET).as_posix() for p in PACKET.rglob('*') if p.is_file() and p.name!='packet_manifest.json'}
    require(actual==set(receipt['files']),'Packet file cohort differs')
    for name,item in receipt['files'].items():
        path=(PACKET/name).resolve()
        require(path.is_relative_to(PACKET.resolve()),'Packet path escaped')
        raw=path.read_bytes().replace(b'\r\n',b'\n')
        require(len(raw)==item['bytes']<195000 and sha(raw)==item['lf_sha256'],'Frozen LF packet bytes differ: '+name)
    for name,expected in receipt['canonical_baseline_files'].items():
        require(sha((BASE/name).read_bytes().replace(b'\r\n',b'\n'))==expected,'Canonical139baseline changed')
    return len(actual)


def validate_sources(capture=None,units=None,qa=None):
    s=read(PACKET/'sources.json') if capture is None else capture
    u=read(PACKET/'source_units.json') if units is None else units
    q=read(PACKET/'pdf_pages_review.json') if qa is None else qa
    pool={x['source_id']:x for x in s['sources']}
    old={x['source_id']:x for x in read(BASE/'sources.json')['sources']}
    require(len(pool)==len(s['sources'])==u['source_objects']==52,'Source pool differs')
    retained=[x for x in s['sources'] if x['source_id'] in old]
    require(len(retained)==u['retained_source_objects_used_unchanged']==13
            and all(digest(x)==digest(old[x['source_id']]) for x in retained),'Retained source changed')
    require(all(sealed_digest(x,'governed_bytes_sha256')==x['governed_bytes_sha256'] for x in s['sources']),
            'Governed source seal differs')
    captures={p.name.removesuffix('_capture.json'):read(p) for p in PACKET.glob('*_capture.json')}
    require(len(captures)==u['raw_response_attempts']==18 and sum(c['raw_response_bytes'] for c in captures.values())==u['raw_bytes']==7636900,
            'Raw response accounting differs')
    require(u['successful_document_identities']==17 and u['publisher_soft404_rejected']==1
            and u['canonical_state_changed'] is u['source_registered'] is u['current_law_certified'] is False,
            'Source authority or identity accounting differs')
    require(len(q['pages'])==14 and q['whole_House_parent_PDFs_claimed_read'] is False,'PDF review scope differs')
    texts,pages={},{}
    for key,c in captures.items():
        raw=reconstruct_capture(c,PACKET)
        if key=='25usc177':
            require(c['final_url']=='https://www.govinfo.gov/error','Rejected locator route differs')
        else:
            require(c['requested_url']==c['final_url'],'Source route differs')
        if c.get('format')=='pdf':
            reader=PdfReader(io.BytesIO(raw))
            for page in [p for p in q['pages'] if p['capture_key']==key]:
                text=reader.pages[page['one_based_pdf_page']-1].extract_text() or ''
                require(text==page['raw_page_text'] and sha(text.encode())==page['raw_page_text_sha256']
                        and sha(normalized_pdf(text).encode())==page['normalized_page_text_sha256']
                        and page['visual_read_completed'] is True,'Selected PDF extraction/review differs')
                pages[(key,page['one_based_pdf_page'])]=normalized_pdf(text)
        else:
            parser=TextParser();parser.feed(raw.decode('utf8'));text=' '.join(' '.join(parser.parts).split())
            require(len(text)==c['normalized_text_characters'] and sha(text.encode())==c['normalized_text_sha256'],
                    'Raw HTML reconstruction differs')
            if 'normalized_text' in c:require(text==c['normalized_text'],'Stored normalized text differs')
            texts[key]=text
    rejected=captures['25usc177']
    require(texts['25usc177'].startswith('Page Not Found | GovInfo')
            and rejected['content_validation']=='EDITION_IDENTITY_FAIL; no source meaning accepted'
            and not any(x['capture_key']=='25usc177' for x in u['units']),'Soft404was accepted as evidence')
    require('/chap4-' not in captures['25usc177_publisherlocated']['requested_url']
            and 'title25-chap5-sec177' in captures['25usc177_publisherlocated']['requested_url']
            and '§177. Purchases or grants' in texts['25usc177_publisherlocated'],'Publisher-located177identity differs')
    require(captures['crec20260521house']['raw_response_sha256']==old['congressional-record:2026-05-21-hr1329-exact']['raw_sha256']
            and captures['crec20260721house']['raw_response_sha256']==old['congressional-record:2026-07-21-ndaa-remaining-offerings']['raw_sha256'],
            'Original Record PDF identity differs')
    require(len(u['units'])==39,'Selected context unit inventory differs')
    for unit in u['units']:
        source=pool[unit['source_id']];c=captures[unit['capture_key']]
        require(source['url']==c['requested_url'] and source['raw_sha256']==c['raw_response_sha256']
                and digest(source)==unit['source_object_sha256'],'Selected source identity differs')
        if 'html_extent' in unit:
            e=unit['html_extent'];full=texts[unit['capture_key']]
            require(0<=e['start']<e['end']<=len(full),'Selected HTML extent differs')
            text=full[e['start']:e['end']]
        elif 'pdf_normalized_page_extents' in unit:
            selected=[]
            for e in unit['pdf_normalized_page_extents']:
                page=pages[(unit['capture_key'],e['page'])]
                require(0<=e['start']<e['end']<=len(page),'Selected PDF extent differs')
                selected.append(page[e['start']:e['end']])
            text=unit['page_join_marker'].join(selected)
            require(unit['whole_parent_document_reviewed'] is False,'Selected PDF became whole parent')
        else:
            review=read(PACKET/'reserve_map_review.json')
            require(unit['manual_literal_caption_transcription'] is True and unit['whole_geographic_geometry_validated'] is False
                    and review['visual_identity_reviewed'] is True and review['geographic_boundary_accuracy_certified'] is False,
                    'Map caption acquired geographic authority')
            text='Commemorative Areas\nWashington, DC and Environs\nMap Number 869 / 86501 B\nJune 24, 2003\nReserve\nArea I\nNational Capital Parks Areas\nOther Federal Lands'
        require(text==source['text'] and sha(text.encode())==unit['passage_sha256'],'Selected passage differs')
    return s


def validate_binding_boundaries(sources):
    pool={s['source_id']:s for s in sources['sources']}
    units={u['unit_key']:pool[u['source_id']]['text'] for u in read(PACKET/'source_units.json')['units']}
    require('AMENDMENT NO. 7 OFFERED BY MR . HUNT' in units['partA7_operative']
            and 'AMENDMENT NO. 6' not in units['partA7_operative'] and 'AMENDMENT NO. 8' not in units['partA7_operative'],
            'Adjacent amendment entered own operative source')
    require('further proceedings' in units['partA7_question_postponement']
            and 'from Texas' in units['partA7_question_postponement']
            and 'amendment No. 7' in units['partA7_resumption_roll260']
            and '[Roll No. 260]' in units['partA7_resumption_roll260']
            and 'ayes 215, noes 214, not voting 8' in units['partA7_resumption_roll260']
            and 'So the amendment was agreed to.' in units['partA7_roll260_result']
            and 'was rejected' not in units['partA7_roll260_result'],'Own A7motion/roll/result chain differs')
    require('So the motion to recommit was rejected.' in units['hr1329_recommit_rejected']
            and '[Roll No. 188]' in units['hr1329_passage_question']
            and 'yeas 204, nays 216, not voting 10' in units['hr1329_passage_question']
            and 'So the bill was not passed.' in units['hr1329_passage_result'],
            'Exact1329question/recommittal/failure chain differs')
    anomaly=read(PACKET/'reference_anomalies.json')
    require(anomaly['resolved_intended_citation'] is anomaly['canonical_state_changed'] is anomaly['semantic_acceptance'] is False
            and anomaly['offering_passage'] in {x['source_id']:x for x in read(BASE/'sources.json')['sources']}['congressional-record:2026-07-21-ndaa-remaining-offerings']['text']
            and 'SUBCHAPTER III—BONDS' in units['40usc31_structure']
            and 'subchapter III' in units['partA7_operative']
            and anomaly['original_PDF_visual_confirmation']['literal_III_confirmed'] is True,
            'Literal IIIreference was repaired or lost')


    museum=read(PACKET/'hr1329_literal_qualifications.json')
    source=pool[museum['source_id']];extent=museum['report_self_reference']['source_extent']
    require(museum['source_object_sha256']==digest(source)
            and source['text'][extent['start']:extent['end']]==museum['report_self_reference']['raw_passage']
            and 'amendments made by subsection (f)' in normalized_pdf(source['text'])
            and museum['report_self_reference']['literal_f_confirmed'] is True
            and museum['report_self_reference']['intended_target_chosen'] is False
            and museum['site_description']['geographic_correction_chosen'] is False
            and museum['site_description']['actual_parcel_determined'] is False
            and museum['reimbursement_period']['unstated_period_trigger_invented'] is False
            and museum['semantic_acceptance'] is museum['canonical_state_changed'] is False,
            'Museum literal qualification became an intended correction')


def validate_member_neutral_authoring(authoring):
    for action in authoring['actions']:
        require(not any(name.casefold() in action[field].casefold()
                        for name in ['Foushee','Massie','F000477','M001184']
                        for field in ['meaning','short_description','compact_description']),
                'Shared meaning contains member-specific observation')


def validate(authoring=None,bundle=None,outputs=None):
    a=read(PACKET/'authoring.json') if authoring is None else authoring
    b=read(PACKET/'decision_bundle.json') if bundle is None else bundle
    require(digest(b)==BUNDLE_SHA and b['bundle_sha256']==sealed_digest(b,'bundle_sha256'),'Frozen decision bundle differs')
    for key in ['canonical_state_changed','source_registered','semantic_acceptance','publication_authorized','production_authorized',
                'batch142_or_HR859_or_HR28_accepted','six_source_holds_changed','issue_propositions_authorized']:
        require(b[key] is False,'Candidate gained authority')
    require([x['action_id'] for x in a['actions']]==[x['action_id'] for x in b['cases']]==ACTIONS
            and a['blocked_episode_ids']==[x['episode_id'] for x in a['actions']],'Candidate cohort or holds differ')
    require(digest(a)==b['authoring_sha256'],'Authored subject changed')
    s=validate_sources();require(digest(s)==b['source_pool_sha256'],'Source subject changed');validate_binding_boundaries(s)
    records={r['action_id']:r for r in read(BASE/'membership_review.json')['records']}
    rows={r['action_id']:r for r in read(BASE/'universe_proposal.json')['candidate_dispositions']}
    counts=Counter(r['disposition'] for r in records.values())
    expected_accounting=dict(records=676,sources=1621,authored_meanings=70,pending=260,ineligible=122,source_holds=6,ordinary_unscreened=0)
    require(len(records)==676 and len(read(BASE/'sources.json')['sources'])==1621
            and len(read(BASE/'authoring.json')['actions'])==70 and counts['pending_interpretation']==260
            and counts['exact_action_ineligible']==122 and counts['source_unresolved']==6
            and digest(b['baseline_accounting'])==digest(expected_accounting),'Canonical baseline accounting differs')
    for case in b['cases']:
        aid=case['action_id'];require(case['candidate_sha256']==sealed_digest(case,'candidate_sha256')
            and digest(records[aid])==case['governed_before_record_sha256'] and digest(rows[aid])==case['governed_before_row_sha256']
            and records[aid]['disposition']=='pending_interpretation'
            and records[aid]['exact_action_binding_unresolved'] is (aid in ACTIONS[-2:]),'Canonical case preimage differs')
        require(case['eligibility_accepted'] is case['meaning_accepted'] is case['canonical_binding_changed'] is False
                and case['strongest_case_specific_counterevidence'] and case['requested_content_bound_decision'],'Content-bound case gate lost')
    core,mapping,projections,inputs,result=prepare(a,s,MEMBERS)
    expected=dict(shared_action_core=core,shared_issue_mapping=mapping,member_projections=projections,compiler_input=inputs,
                  compiled_ir=result.compiled_ir,readable_candidates=readable_candidates(a,core,projections,result))
    o={k:read(PACKET/'generated'/(k+'.json')) for k in OUTPUTS} if outputs is None else outputs
    require(digest(o)==digest(expected),'Typed candidate replay differs')
    validate_member_neutral_authoring(a)
    for authored,c in zip(a['actions'],core['actions']):
        case=next(x for x in b['cases'] if x['action_id']==c['action_id'])
        require(case['candidate_action_core_sha256']==c['action_core_sha256'],'Case core seal differs')
    require(result.validation['proposition_count']==0 and result.validation['source_render_constraint_count']==1
            and core['authoritative_for_new_editorial_work'] is mapping['authoritative_for_new_editorial_work'] is False
            and expected['readable_candidates']['production_eligible'] is False,'Held candidate gained analytical authority')
    statuses=[['Yea','Yea','Yea','Nay','Nay'],['Yea','Yea','Yea','Not Voting','Nay']]
    for p,expected_statuses in zip(projections,statuses):
        require([x['official_status'] for x in p['actions']]==expected_statuses,'Official member status changed')
    require(projections[1]['actions'][3]['exact_choice_effect']=='resolved_non_directional','NotVoting became support/opposition')
    for member in result.compiled_ir['members']:
        require(member['review_route']=='blocked' and not member['proposition_graph']['propositions'],'Candidate hold lost')
    coverage={m['member_id']:m['coverage'] for m in result.compiled_ir['members']}
    require(coverage['M001184']['not_voting_actions']==1
            and coverage['M001184']['directional_yes_no_positions']==4
            and coverage['F000477']['not_voting_actions']==0
            and coverage['F000477']['directional_yes_no_positions']==5,
            'NotVoting entered directional candidate accounting')
    receipt=read(PACKET/'generated/replay_receipt.json')
    require(receipt['input_sha256']==digest(a) and receipt['capture_sha256']==digest(s)
            and receipt['output_sha256']=={k:digest(v) for k,v in expected.items()}
            and receipt['canonical_mutation'] is receipt['semantic_acceptance'] is receipt['publication_authorized'] is False,
            'Replay receipt differs')
    return dict(actions=5,cores=5,official_observations=10,source_objects=52,raw_responses=18,accepted_document_identities=17,
                issue_propositions=0,not_voting_observations=1,canonical_state_changed=False)


if __name__=='__main__':
    print(json.dumps(dict(packet_files=validate_transport(),candidate=validate()),indent=2))
