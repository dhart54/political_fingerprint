import copy
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

import pytest

from scripts import foushee_m15a2_core_repair as repair
from scripts.editorial_artifact_store import StoreSafetyError


def test_exact_source_universe_and_member_votes():
    manifest=repair.load(repair.DIRECTORY/'source_manifest.json')
    facts=repair.source_facts(manifest,repair.DIRECTORY/'official_sources.zip')
    assert len(repair.IDS)==31
    assert sum(d==repair.NS for d in repair.ACTION_DOMAINS.values())==16
    assert sum(d==repair.ENV for d in repair.ACTION_DOMAINS.values())==15
    assert {repair._action_id(r) for r in facts['roll_calls']}==set(repair.IDS)
    assert len(facts['votes_cast'])==len(facts['vote_contexts'])==31
    expected={r['canonical_action_id']:r['publication_expected_vote'] for r in manifest['sources']}
    assert {v['action_id']:v['position'] for v in facts['votes_cast']}==expected
    assert {r['session'] for r in facts['roll_calls']}=={1,2}
    assert manifest['member_identity']['bioguide_id']=='F000477'
    assert manifest['production_database_write'] is False


def test_context_party_totals_match_each_official_roll_not_current_roster():
    manifest=repair.load(repair.DIRECTORY/'source_manifest.json')
    facts=repair.source_facts(manifest,repair.DIRECTORY/'official_sources.zip')
    contexts={c['action_id']:c for c in facts['vote_contexts']}
    positions={'Yea':'yea','Aye':'yea','Nay':'nay','No':'nay','Present':'present','Not Voting':'not_voting'}
    with zipfile.ZipFile(repair.DIRECTORY/'official_sources.zip') as archive:
        for source in manifest['sources']:
            totals=defaultdict(Counter)
            for recorded in ET.fromstring(archive.read(source['source_filename'])).findall('.//recorded-vote'):
                totals[recorded.find('legislator').get('party')][positions[recorded.findtext('vote')]]+=1
            expected={party:{p:counts[p] for p in ('yea','nay','present','not_voting')} for party,counts in totals.items()}
            assert contexts[source['canonical_action_id']]['party_vote_totals']==expected
    # A historical roll predates a roster party change: all 217 Yea votes were R.
    assert contexts['house:119:1:110']['party_vote_totals']['R']['yea']==217
    assert 'I' not in contexts['house:119:1:110']['party_vote_totals']


@pytest.mark.parametrize('mutation',['digest','universe','vote','roster'])
def test_manifest_or_source_discrepancy_fails_closed(mutation):
    manifest=repair.load(repair.DIRECTORY/'source_manifest.json')
    if mutation=='digest':manifest['sources'][0]['sha256']='0'*64
    if mutation=='universe':manifest['sources'][0]['canonical_action_id']='house:118:1:110'
    if mutation=='vote':manifest['sources'][0]['F000477_vote']='yea'
    if mutation=='roster':manifest['member_identity']['bioguide_id']='F999999'
    # Even internally resealed candidates must reproduce actual pinned XML facts.
    repair.seal(manifest,'manifest_sha256')
    with pytest.raises(StoreSafetyError):
        repair.source_facts(manifest,repair.DIRECTORY/'official_sources.zip')


def test_archive_byte_change_fails_closed(tmp_path):
    path=tmp_path/'changed.zip';path.write_bytes((repair.DIRECTORY/'official_sources.zip').read_bytes()+b'changed')
    with pytest.raises(StoreSafetyError,match='archive digest'):
        repair.source_facts(repair.load(repair.DIRECTORY/'source_manifest.json'),path)


def test_wrong_session_cannot_replace_exact_action(tmp_path):
    manifest=repair.load(repair.DIRECTORY/'source_manifest.json')
    path=tmp_path/'wrong-session.zip';changed=manifest['sources'][0]
    with zipfile.ZipFile(repair.DIRECTORY/'official_sources.zip') as source,zipfile.ZipFile(path,'w') as dest:
        for name in source.namelist():
            data=source.read(name)
            if name==changed['source_filename']:
                data=data.replace(b'<session>1st</session>',b'<session>2nd</session>')
                changed['sha256']=hashlib.sha256(data).hexdigest()
            dest.writestr(name,data)
    manifest['archive_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();repair.seal(manifest,'manifest_sha256')
    with pytest.raises(StoreSafetyError,match='identities differ'):
        repair.source_facts(manifest,path)


def test_exact_caps_exclude_interpretation_and_updates():
    assert repair.CAPS=={'bills':6,'roll_calls':31,'votes_cast':31,'vote_contexts':31,
        'vote_classifications':0,'vote_interpretations':0,'editorial_artifacts':0,
        'publication_registry':0,'updates':0,'deletes':0}


def test_public_reads_restore_connections_after_failure():
    from app.main import app
    from app.api import precomputed,editorial_presentations
    original=(precomputed.get_connection,editorial_presentations.get_connection)
    with pytest.raises(RuntimeError):
        with repair.public_reads_in_transaction(object()):raise RuntimeError('injected')
    assert (precomputed.get_connection,editorial_presentations.get_connection)==original


@pytest.mark.parametrize('field',['accepted','sealed','production_database_write'])
def test_preparation_cannot_grant_authority(field):
    bundle=repair.load(repair.DIRECTORY/'repair_bundle.json');bundle[field]=True
    repair.seal(bundle,'bundle_sha256')
    with pytest.raises(StoreSafetyError):repair.validate_bundle(bundle)


def test_modified_write_graph_cannot_be_resealed_as_source_facts():
    bundle=repair.load(repair.DIRECTORY/'repair_bundle.json')
    bundle['facts']['votes_cast'][0]['position']='yea'
    repair.seal(bundle,'bundle_sha256')
    with pytest.raises(StoreSafetyError,match='does not reproduce'):repair.validate_bundle(bundle)


@pytest.mark.parametrize('mode',['apply','rollback'])
def test_production_mode_requires_explicit_authorization_before_connect(mode,monkeypatch,tmp_path):
    bundle=repair.load(repair.DIRECTORY/'repair_bundle.json')
    monkeypatch.setenv('DATABASE_URL','unused-test-value')
    monkeypatch.setattr(repair,'target_info',lambda *a:bundle['production_target'])
    def connect(*a,**k):pytest.fail('must reject before connecting')
    monkeypatch.setattr(repair,'_connect',connect)
    with pytest.raises(StoreSafetyError,match='production authorization'):
        repair.main([mode,'--target','production','--confirm-bundle-digest',bundle['bundle_sha256'],'--receipt',str(tmp_path/'receipt.json')])
