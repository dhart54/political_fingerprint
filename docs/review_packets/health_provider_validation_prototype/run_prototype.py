"""Serial frozen-input measurements and explicitly labelled proof-boundary tests.

No canonical candidate artifact or proof is written. Six disposable JSON outputs
under the diagnostic directory establish actual serialization-byte equivalence.
The normalized test mode changes only the
in-memory expected adapter binding of the exact historical Immigration proof.
It does not make that historical proof valid for the changed adapter.
"""
import argparse
from contextlib import nullcontext
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
from unittest.mock import patch

FROZEN = 'eb9d70ab3ca28ea3ee11eae572d2f2befd6f4aea'
SCRIPT = 'scripts/prepare_immigration_shared_candidate.py'
PROOF = 'docs/editorial/shared_candidates/house_119_immigration_20260916/generated/reproducibility_proof.json'
TESTS = ['backend/tests/test_shared_domain_candidate.py', 'backend/tests/test_shared_legislative_corpus.py',
         'backend/tests/test_shared_candidate_research.py', 'backend/tests/test_immigration_shared_candidate.py']


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True, encoding='utf-8').strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code_binding(root, name):
    """Distinguish tested worktree bytes from Git's newline-filtered blob."""
    raw = (root / name).read_bytes()
    blob = subprocess.check_output(['git', '-C', str(root), 'show', 'HEAD:' + name])
    committed = git(root, 'rev-parse', 'HEAD:' + name)
    filtered = git(root, 'hash-object', '--path=' + name, str(root / name))
    if committed != filtered:
        raise AssertionError('validation requires committed source: ' + name)
    return dict(worktree_raw_sha256=hashlib.sha256(raw).hexdigest(),
                git_blob_sha256=hashlib.sha256(blob).hexdigest(), git_blob_object_id=committed,
                worktree_filtered_object_id=filtered, crlf_count=raw.count(b'\r\n'),
                lone_lf_count=raw.count(b'\n') - raw.count(b'\r\n'))


def frozen_text(root, name):
    return subprocess.check_output(['git', '-C', str(root), 'show', FROZEN + ':' + name]).decode('utf-8').replace('\r\n', '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--variant', choices=['baseline', 'prototype'], required=True)
    parser.add_argument('--mode', choices=['measure', 'suite-raw', 'suite-normalized'], default='measure')
    parser.add_argument('--repeats', type=int, choices=[1, 2, 3], default=2)
    parser.add_argument('--profile', action='store_true')
    parser.add_argument('--include-controls', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve()
    if output.exists() or (output.is_relative_to(root) and not output.is_relative_to(root / '.local')):
        parser.error('choose a fresh diagnostic output outside the checkout or under ignored .local')
    head = git(root, 'rev-parse', 'HEAD')
    if head != args.expected_head or git(root, 'merge-base', head, FROZEN) != FROZEN:
        parser.error('checkout does not match the expected frozen-based head')
    allowed = {SCRIPT, 'backend/tests/test_health_provider_validation_prototype.py',
               'docs/plans/health_provider_validation_prototype.md'}
    changed = git(root, 'diff', '--name-only', FROZEN).splitlines()
    if any(name not in allowed and not name.startswith('docs/review_packets/health_provider_validation_prototype/') for name in changed):
        parser.error('prototype diff exceeds the bounded engineering envelope')
    baseline_script = frozen_text(root, SCRIPT)
    current_script = (root / SCRIPT).read_text(encoding='utf-8')
    if (current_script == baseline_script) != (args.variant == 'baseline'):
        parser.error('variant label does not match observed adapter bytes')
    code_names = [SCRIPT] + (['backend/tests/test_health_provider_validation_prototype.py']
                            if args.include_controls else [])
    code_bindings = {name: code_binding(root, name) for name in code_names}
    driver_root = Path(__file__).resolve().parents[3]
    driver_name = str(Path(__file__).resolve().relative_to(driver_root)).replace('\\', '/')
    driver_binding = code_binding(driver_root, driver_name)
    sys.path.insert(0, str(root))
    os.chdir(root)
    adapter = importlib.import_module('scripts.prepare_immigration_shared_candidate')
    data = root / 'docs/editorial/shared_candidates/house_119_immigration_20260916'
    generated = data / 'generated'
    fixed = [SCRIPT, *TESTS, PROOF, 'docs/review_packets/foushee_immigration_shared_candidate.md', 'scripts/prepare_shared_domain_candidate.py',
             'docs/editorial/shared_candidates/house_119_health_20260916/generated/shared_action_core.json',
             'backend/app/semantic_ir/shared_corpus.py', 'backend/app/semantic_ir/compiler.py',
             'backend/app/semantic_ir/pipeline.py', 'backend/app/semantic_ir/adapters.py',
             'backend/app/semantic_ir/validation.py', 'docs/semantic_ir/shared_legislative_corpus_v1.schema.json']
    fixed.extend(str(path.relative_to(root)).replace('\\', '/') for path in data.glob('*.json'))
    fixed.extend(str(path.relative_to(root)).replace('\\', '/') for path in generated.glob('*.json'))
    hashes = {name: sha(root / name) for name in sorted(set(fixed))}
    old_binding = adapter.digest(baseline_script)
    new_binding = adapter.digest(current_script)
    observed_proof = (root / PROOF).read_text(encoding='utf-8')
    if observed_proof != frozen_text(root, PROOF):
        parser.error('historical proof differs from frozen evidence')
    if json.loads(observed_proof)['rule_files_sha256'][SCRIPT] != old_binding:
        parser.error('historical proof does not bind the frozen adapter')
    receipt = dict(started_at_utc=datetime.now(timezone.utc).isoformat(), head=head, frozen_base=FROZEN,
                   variant=args.variant, mode=args.mode, python=sys.version,
                   processor=platform.processor(), platform=platform.platform(), logical_cpus=os.cpu_count(),
                   jsonschema=importlib.metadata.version('jsonschema'), pytest=importlib.metadata.version('pytest'),
                   adapter_raw_sha256=hashes[SCRIPT], adapter_old_text_binding=old_binding,
                   adapter_current_text_binding=new_binding, historical_proof_valid_for_changed_adapter=False,
                   protected_hashes=hashes, initial_tracked_diff=changed,
                   code_bindings=code_bindings, driver_binding=driver_binding,
                   conditions='One benchmark process; fresh-process first call/warm repeats; OS cache not cleared.')
    if args.mode == 'measure':
        author = json.loads((data / 'authoring.json').read_text(encoding='utf-8'))
        capture = json.loads((data / 'sources.json').read_text(encoding='utf-8'))
        before = [adapter.digest(author), adapter.digest(capture)]
        measurements = []
        expected = None
        def compare(products):
            core, mapping, projections, inputs, result = products
            values = dict(shared_action_core=core, shared_issue_mapping=mapping, member_projections=projections,
                          compiler_input=inputs, compiled_ir=result.compiled_ir,
                          readable_candidates=adapter.readable_candidates(author, core, projections, result))
            serialized = output.parent / (output.stem + '-serialized')
            serialized.mkdir(parents=True, exist_ok=True)
            serialized_digests = {}
            for name, value in values.items():
                if value != json.loads((generated / (name + '.json')).read_text(encoding='utf-8')):
                    raise AssertionError('generated semantic output differs: ' + name)
                adapter.write_json(serialized / (name + '.json'), value)
                serialized_digests[name + '_serialized_bytes'] = sha(serialized / (name + '.json'))
            packet = (root / 'docs/review_packets/foushee_immigration_shared_candidate.md').read_text(encoding='utf-8')
            text = packet.split('<!-- GENERATED CANDIDATE START -->\n', 1)[1].split('<!-- GENERATED CANDIDATE END -->', 1)[0]
            rendered = adapter.review_text(author, core, projections, result, capture)
            receipt['historical_packet_matches_current_renderer'] = rendered == text
            receipt['historical_packet_limit'] = ('Frozen Markdown retains44-input generation; current JSON/renderer has65. '
                                                   'Preserve old bytes and compare baseline/prototype renderer output exactly.')
            if [adapter.digest(author), adapter.digest(capture)] != before:
                raise AssertionError('preparation mutated loaded inputs')
            return {name: adapter.digest(value) for name, value in values.items()} | {
                'rendered_packet_text': adapter.digest(rendered), 'historical_packet_text': adapter.digest(text)} | serialized_digests
        for index in range(args.repeats):
            start, cpu = time.perf_counter(), time.process_time()
            products = adapter.prepare(author, capture, ['F000477', 'M001184'])
            row = dict(condition='fresh_process_first_call' if index == 0 else 'same_process_warm_call',
                       wall_seconds=time.perf_counter() - start, cpu_seconds=time.process_time() - cpu)
            results = compare(products)
            if expected is not None and expected != results:
                raise AssertionError('repeat output digests differ')
            expected = results
            measurements.append(row)
            print(json.dumps(row), flush=True)
        receipt['measurements'], receipt['all_generated_output_digests'] = measurements, expected
        if args.profile:
            profiler = cProfile.Profile()
            start = time.perf_counter()
            products = profiler.runcall(adapter.prepare, author, capture, ['F000477', 'M001184'])
            elapsed = time.perf_counter() - start
            if compare(products) != expected:
                raise AssertionError('profiled output differs')
            stats = pstats.Stats(profiler)
            watched = {'prepare', '_prepare_reused_action', '_prepare_candidate_core_augmentation', 'validate',
                       '_validate_schema', 'validate_shared_action_core', 'validate_sources', '_same_json'}
            rows = [dict(file=file.replace(str(root), '$CHECKOUT'), line=line, function=fn,
                         primitive_calls=primitive, total_calls=total, exclusive_seconds=exclusive,
                         cumulative_seconds=cumulative)
                    for (file, line, fn), (primitive, total, exclusive, cumulative, _) in stats.stats.items() if fn in watched]
            receipt['profile'] = dict(wall_seconds=elapsed, functions=sorted(rows, key=lambda r:r['cumulative_seconds'], reverse=True))
    else:
        import pytest
        original_read = Path.read_text
        adjusted_reads = []
        def expected_proof(path, *positional, **keywords):
            text = original_read(path, *positional, **keywords)
            if path.resolve() == (root / PROOF).resolve():
                if text != observed_proof:
                    raise AssertionError('historical proof read changed during tests')
                old = '"' + SCRIPT + '": "' + old_binding + '"'
                new = '"' + SCRIPT + '": "' + new_binding + '"'
                if text.count(old) != 1:
                    raise AssertionError('expected exactly one historical adapter binding')
                adjusted_reads.append(str(path))
                return text.replace(old, new, 1)
            return text
        context = patch.object(Path, 'read_text', new=expected_proof) if args.mode == 'suite-normalized' else nullcontext()
        modules = TESTS + (['backend/tests/test_health_provider_validation_prototype.py'] if args.include_controls else [])
        with context:
            exit_code = pytest.main(['-q', *modules, '--durations=30', '--basetemp=.local/' + args.mode,
                                    '-o', 'cache_dir=.local/cache-' + args.mode, '--junitxml=' + str(output.with_suffix('.xml'))])
        receipt['exit_code'], receipt['proof_adjusted_reads'] = int(exit_code), adjusted_reads
        receipt['proof_accommodation'] = ('Only the expected adapter hash on the exact proof read; no disk write. '
                                          'This run establishes conditional structural equivalence, not historical proof validity.'
                                          if args.mode == 'suite-normalized' else 'None; historical binding mismatch remains visible.')
    if git(root, 'rev-parse', 'HEAD') != head or any(sha(root / name) != value for name, value in hashes.items()):
        raise AssertionError('adapter, tests, input/rules or historical evidence changed during execution')
    if git(root, 'diff', '--name-only', FROZEN).splitlines() != changed:
        raise AssertionError('tracked diff changed during execution')
    if ({name: code_binding(root, name) for name in code_names} != code_bindings
            or code_binding(driver_root, driver_name) != driver_binding):
        raise AssertionError('tested source or driver bytes changed during execution')
    receipt['protected_bytes_unchanged'] = True
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as file:
        json.dump(receipt, file, indent=2)
        file.write('\n')
    print('Receipt:', output, flush=True)
    if args.mode != 'measure':
        return receipt['exit_code']
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
