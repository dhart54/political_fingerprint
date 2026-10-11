import copy
import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('education_locator',ROOT/'scripts/prepare_education79_locator_release.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)

def inputs():
    catalog=release.load(ROOT/release.CATALOG)
    core=release.load(ROOT/'docs/editorial/shared_corpora/house_119_v2/shared_action_core.json')
    source=next(s for s in catalog['sources'] if s['source_id']==release.SOURCE_ID)
    raw=(ROOT/source['raw_provenance']['governed_local_path']).read_bytes()
    return catalog,core,raw

def test_actual_governed_bytes_are_authenticated():
    catalog,core,raw=inputs()
    assert release.authenticate_source(catalog,core,raw)['source_url']==release.URL
    with pytest.raises(release.LocatorPreparationError,match='actual governed bytes differ'):
        release.authenticate_source(catalog,core,raw+b'changed')

@pytest.mark.parametrize('mutation',['url','hash','duplicate','missing','type'])
def test_catalog_declarations_alone_cannot_authenticate_a_locator(mutation):
    catalog,core,raw=inputs()
    source=next(s for s in catalog['sources'] if s['source_id']==release.SOURCE_ID)
    if mutation=='url':source['source_url']='https://www.govinfo.gov/content/pkg/unreviewed/html/unreviewed.htm'
    if mutation=='hash':source['raw_provenance']['sha256']='0'*64
    if mutation=='type':source['source_type']='congress_gov_bill_text'
    if mutation=='duplicate':catalog['sources'].append(copy.deepcopy(source))
    if mutation=='missing':catalog['sources'].remove(source)
    with pytest.raises(release.LocatorPreparationError):release.authenticate_source(catalog,core,raw)

def test_complete_projection_changes_only_the_same_locator_copies():
    before_files={p:p.read_bytes() for p in [release.PACKET/'baseline/persisted-education.json',ROOT/release.CATALOG,
        ROOT/'docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1/site_integration_candidate.json']}
    output=release.build();proof=output['invariance-proof.json']
    assert len(proof['projection_changes'])==4 and len(proof['receipt_changes'])==2
    assert proof['reviewed_actions']==17 and proof['all_other_fields_equal']
    assert output['persistence-preparation.json']['production_execution_authorized'] is False
    assert all(p.read_bytes()==value for p,value in before_files.items())
    for scope in ['119','all']:
        a=copy.deepcopy(output['candidate-projection.json']['subject']['presentations'][scope])
        receipt=next(r for r in a['exact_action_receipts'] if r['canonical_action_id']==release.ACTION)
        receipt['action_meaning_sources'][0]['url']=release.OLD_URL
        assert a==output['baseline-public-projection.json']['subject']['presentations'][scope]
