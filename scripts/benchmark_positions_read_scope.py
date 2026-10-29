"""Local disposable microbenchmark, not a production latency estimate.

Run: python scripts/benchmark_positions_read_scope.py --output <ignored-json>
Uses identical SELECT text/parameters/results and 39 serial precomputed reads
for each mode. Query shape is synthetic, not a full positions API benchmark.
"""
import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'backend')]
# No application .env is needed for this strictly local harness.
import dotenv
dotenv.load_dotenv = lambda *a, **k: False
from app import db
from app.api import precomputed
from backend.tests.positions_disposable_postgres import DisposablePostgres


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    allowed = (ROOT / '.tmp/positions-reuse').resolve()
    if not output.is_relative_to(allowed):
        raise SystemExit('Output must be inside owned .tmp/positions-reuse')
    result = {'kind': 'local synthetic SELECT microbenchmark', 'reads_per_trial': 39, 'pairs': 8, 'warmup_pairs': 1, 'trials': [], 'limitations': 'Loopback PostgreSQL, synthetic same-result queries, no injected latency, no production savings claim.'}
    original = precomputed.get_connection
    try:
        with DisposablePostgres(allowed) as postgres:
            result['cluster'] = str(postgres.directory)
            for pair in range(9):
                for mode in (['baseline', 'candidate'] if pair % 2 == 0 else ['candidate', 'baseline']):
                    connections = []
                    def connect():
                        connection = postgres.connect()
                        connections.append(connection)
                        return connection
                    precomputed.get_connection = connect
                    started = perf_counter()
                    with db.precomputed_read_scope() if mode == 'candidate' else nullcontext():
                        for value in range(39):
                            assert precomputed._query_all_dicts('SELECT %s::integer AS value', (value,)) == [{'value': value}]
                    elapsed = (perf_counter() - started) * 1000
                    assert all(c.closed for c in connections)
                    if pair:
                        result['trials'].append({'pair': pair, 'mode': mode, 'wall_ms': elapsed, 'connections': len(connections)})
            for mode in ['baseline', 'candidate']:
                values = [r['wall_ms'] for r in result['trials'] if r['mode'] == mode]
                result[mode] = {'median_ms': statistics.median(values), 'min_ms': min(values), 'max_ms': max(values)}
        result['server_stopped'] = not postgres.started
    finally:
        precomputed.get_connection = original
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
