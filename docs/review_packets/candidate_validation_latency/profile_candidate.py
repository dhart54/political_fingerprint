"""Read-only, exact-checkout candidate profiling; run one process at a time.

Example (from the feature worktree):
  python docs/review_packets/candidate_validation_latency/profile_candidate.py \
    --root ../cvb --expected-head eb9d70ab3ca28ea3ee11eae572d2f2befd6f4aea \
    --domain immigration --repeats 2 --profile --output .local/immigration.json

Cold means fresh Python process, not cleared OS disk cache. No validation
outcomes are cached or checks patched. Outputs include machine-specific paths.
"""
from __future__ import annotations

import argparse
import cProfile
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import pstats
import subprocess
import sys
import time


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def referenced_artifacts(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == 'artifact_ref' and isinstance(nested, str):
                yield nested
            else:
                yield from referenced_artifacts(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from referenced_artifacts(nested)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--domain', choices=['health', 'immigration'], required=True)
    parser.add_argument('--repeats', type=int, choices=range(1, 4), default=2)
    parser.add_argument('--profile', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    started_at = datetime.now(timezone.utc).isoformat()
    root = args.root.resolve()
    output = args.output.resolve()
    if output.is_relative_to(root) and not output.is_relative_to(root / '.local'):
        parser.error('diagnostic output must be outside benchmark checkout or under its ignored .local directory')
    if output.exists():
        parser.error('measurement output already exists; choose a new path to preserve evidence')
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if head != args.expected_head:
        parser.error(f'exact-head mismatch: expected {args.expected_head}, found {head}')
    tracked = subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain', '--untracked-files=no'], text=True)
    if tracked:
        parser.error('benchmark requires an unchanged tracked checkout')
    sys.path.insert(0, str(root))
    module_name = ('scripts.prepare_immigration_shared_candidate' if args.domain == 'immigration'
                   else 'scripts.prepare_shared_domain_candidate')
    started = time.perf_counter()
    adapter = importlib.import_module(module_name)
    import_seconds = time.perf_counter() - started
    data = root / f'docs/editorial/shared_candidates/house_119_{args.domain}_20260916'
    started = time.perf_counter()
    authoring = json.loads((data / 'authoring.json').read_text(encoding='utf-8'))
    capture = json.loads((data / 'sources.json').read_text(encoding='utf-8'))
    load_seconds = time.perf_counter() - started
    rule_names = [
        'scripts/prepare_shared_domain_candidate.py', 'backend/app/semantic_ir/shared_corpus.py',
        'backend/app/semantic_ir/compiler.py', 'backend/app/semantic_ir/pipeline.py',
        'backend/app/semantic_ir/adapters.py', 'backend/app/semantic_ir/validation.py',
        'docs/semantic_ir/shared_legislative_corpus_v1.schema.json',
    ]
    if args.domain == 'immigration':
        rule_names.append('scripts/prepare_immigration_shared_candidate.py')
    providers = sorted(set(referenced_artifacts(authoring)))
    paths = [data / 'authoring.json', data / 'sources.json',
             *(root / name for name in rule_names + providers)]
    if any(not path.resolve().is_relative_to(root) for path in paths):
        parser.error('referenced input escapes benchmark checkout')
    initial_hashes = {path.relative_to(root).as_posix(): sha256(path) for path in paths}
    loaded_inputs = [adapter.digest(authoring), adapter.digest(capture)]
    members = ['F000477', 'M001184']
    measurements = []
    expected = None
    for index in range(args.repeats):
        started = time.perf_counter()
        cpu = time.process_time()
        products = adapter.prepare(authoring, capture, members)
        measurement = {
            'condition': 'fresh_process_first_call' if index == 0 else 'same_process_warm_call',
            'wall_seconds': time.perf_counter() - started,
            'cpu_seconds': time.process_time() - cpu,
        }
        # Timing excludes equivalence bookkeeping. Every actual prepare executes.
        observed = [adapter.digest(value) for value in products[:4]]
        observed.append(adapter.digest(products[-1].compiled_ir))
        if expected is not None and observed != expected:
            raise AssertionError('repeat products differ')
        if [adapter.digest(authoring), adapter.digest(capture)] != loaded_inputs:
            raise AssertionError('prepare mutated loaded inputs')
        expected = observed
        measurement['product_digests'] = observed
        measurements.append(measurement)
        print(json.dumps(measurement), flush=True)
    profile_rows = []
    if args.profile:
        profiler = cProfile.Profile()
        cpu = time.process_time()
        started = time.perf_counter()
        products = profiler.runcall(adapter.prepare, authoring, capture, members)
        profile_wall = time.perf_counter() - started
        profile_cpu = time.process_time() - cpu
        observed = [adapter.digest(value) for value in products[:4]]
        observed.append(adapter.digest(products[-1].compiled_ir))
        if observed != expected:
            raise AssertionError('profile products differ')
        if [adapter.digest(authoring), adapter.digest(capture)] != loaded_inputs:
            raise AssertionError('profiled prepare mutated loaded inputs')
        stats = pstats.Stats(profiler)
        for (filename, line, function), (primitive, total, exclusive, cumulative, _) in stats.stats.items():
            profile_rows.append({'file': filename, 'line': line, 'function': function,
                                 'primitive_calls': primitive, 'total_calls': total,
                                 'exclusive_seconds': exclusive, 'cumulative_seconds': cumulative})
        profile_rows.sort(key=lambda row: row['cumulative_seconds'], reverse=True)
        profile = {'wall_seconds': profile_wall, 'cpu_seconds': profile_cpu,
                   'total_calls': stats.total_calls, 'functions': profile_rows}
    else:
        profile = None
    final_head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    final_tracked = subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain', '--untracked-files=no'], text=True)
    if final_head != head or final_tracked or any(sha256(root / name) != value for name, value in initial_hashes.items()):
        raise AssertionError('checkout, rules or input bytes changed during benchmark')
    report = {
        'started_at_utc': started_at,
        'head': head, 'root': str(root), 'domain': args.domain,
        'python': sys.version, 'platform': platform.platform(), 'processor': platform.processor(),
        'logical_cpus': os.cpu_count(), 'jsonschema': importlib.metadata.version('jsonschema'),
        'pytest': importlib.metadata.version('pytest'),
        'condition_limits': 'Fresh process / warm call; OS file cache not cleared; single benchmark process.',
        'input_files': {name: {'sha256': sha256(data / name), 'bytes': (data / name).stat().st_size}
                        for name in ['authoring.json', 'sources.json']},
        'rule_files': {name: sha256(root / name) for name in rule_names},
        'provider_files': {name: initial_hashes[name] for name in providers},
        'input_and_rule_bytes_unchanged': True,
        'loaded_inputs_unchanged': True,
        'authored_actions': len(authoring['actions']), 'captured_sources': len(capture['sources']),
        'import_seconds': import_seconds, 'input_load_seconds': load_seconds,
        'measurements': measurements, 'profile': profile,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as report_file:
        report_file.write(json.dumps(report, indent=2) + '\n')
    print(f'Wrote {args.output}', flush=True)


if __name__ == '__main__':
    main()
