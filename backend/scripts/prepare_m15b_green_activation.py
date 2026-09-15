"""Prepare technical activation evidence read-only; never creates human authority."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.editorial_presentations.publication_replacement_store_v2r import prepare_write_set, capture_preflight
from scripts import m15b_persistence_preparation as persistence
from scripts.green_production_target import target_identity
from scripts.green_vote_storage import connect_readonly
from scripts.foushee_education_workforce_m14h_replacement import (
    _git_submanifest, capture_runtime, BACKEND_RUNTIME_PATHS, FRONTEND_RUNTIME_PATHS,
)

OUT = BACKEND.parent/'docs/editorial/publication_replacements/m15b_green_activation'


def load(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'))


def build_write_sets(runtime, owned):
    package = persistence.load(persistence.OUT/'persistence_package.json')
    persistence.validate_package(package)
    return {issue: prepare_write_set(
        registry_key=b['registry_key'], prior_row=b['prior_registry_row'],
        expected_old=b['expected_old'],
        proposed_new={**b['proposed_new'], 'artifact_id': owned[issue]['artifact_ids'][b['proposed_new']['natural_key']]},
        semantic_authority_binding=b['semantic_authority_binding'],
        publication_metadata=b['publication_metadata'],
        production_target_identity_sha256=b['production_target_identity_sha256'],
        public_runtime_manifest_binding={side+'_submanifest_sha256': runtime[side+'_deployment']['submanifest_sha256']
                                         for side in ('backend', 'frontend')},
    ) for issue, b in package['replacements'].items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-path', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise SystemExit('Preserve existing execution evidence; use a new output directory')
    from dotenv import dotenv_values
    environment = dotenv_values(args.env_path)
    assert environment['NORMALIZED_VOTE_STORAGE'] == '1'
    url = environment['DATABASE_URL']; identity = target_identity(url, 'production')
    package = persistence.load(persistence.OUT/'persistence_package.json')
    receipts = load('persistence_receipts.json')
    assert receipts['production_package_sha256'] == package['package_sha256']
    # Trusted deployment record, not a guessed frontend source SHA.
    deployment = json.loads(subprocess.check_output(['gh', 'api',
        'repos/dhart54/political_fingerprint/deployments?environment=Production&per_page=1'], text=True))[0]
    assert deployment['sha'] == persistence.MERGED
    status = json.loads(subprocess.check_output(['gh', 'api',
        f"repos/dhart54/political_fingerprint/deployments/{deployment['id']}/statuses"], text=True))[0]
    assert status['state'] == 'success'
    source = {key: deployment[key] for key in ('id', 'sha', 'environment', 'created_at')}
    source['status'] = {key: status[key] for key in ('state', 'environment_url', 'target_url', 'created_at')}
    manifest = {'subject': {'backend': _git_submanifest(persistence.MERGED, BACKEND_RUNTIME_PATHS),
                            'frontend': _git_submanifest(deployment['sha'], FRONTEND_RUNTIME_PATHS)}}
    runtime = capture_runtime('https://political-fingerprint.onrender.com', manifest,
        frontend_deployed_commit=deployment['sha'],
        frontend_deployment_source_identity=f"github:dhart54/political_fingerprint:deployment:{deployment['id']}:{status['environment_url']}")
    assert runtime['backend_deployment']['deployed_commit_sha'] == persistence.MERGED
    with connect_readonly(url) as conn:
        conn.execute("SET LOCAL timezone='UTC'")
        owned = {i: persistence.preflight(conn, b) for i, b in package['replacements'].items()}
        assert all(owned.values())
        assert all(owned[i] == {k: receipts['receipts'][i][k] for k in ('artifact_ids', 'batch_id')} for i in owned)
        write_sets = build_write_sets(runtime, owned)
        preflights = {i: capture_preflight(conn, ws, production_target_identity_sha256=identity)
                      for i, ws in write_sets.items()}
        conn.rollback()
    args.output_dir.mkdir(parents=True)
    for name, value in [('runtime_evidence.json', runtime), ('runtime_manifest.json', manifest),
                        ('frontend_deployment_source.json', source), ('write_sets.json', write_sets),
                        ('activation_preflights.json', preflights)]:
        (args.output_dir/name).write_text(json.dumps(value, sort_keys=True, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'runtime_sha256': runtime['runtime_health_proof_subject_sha256'],
                      'write_sets': {i: ws['write_set_subject_sha256'] for i, ws in write_sets.items()},
                      'preflights': {i: p['preflight_subject_sha256'] for i, p in preflights.items()},
                      'production_writes': 0, 'activation_authorized': False}))


if __name__ == '__main__':
    main()
