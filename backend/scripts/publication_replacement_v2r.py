"""Thin operator for one already-persisted V2R replacement; never grants authority."""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.editorial_presentations.publication_replacement_store_v2r import capture_preflight, replace_publication
from scripts.editorial_artifact_store import _connect
from scripts.foushee_education_workforce_m14h_replacement import target_identity


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['preflight', 'apply', 'rollback'])
    parser.add_argument('--database-url-env', required=True)
    parser.add_argument('--target', required=True, choices=['production', 'disposable'])
    parser.add_argument('--write-set', type=Path, required=True)
    parser.add_argument('--authority', type=Path)
    parser.add_argument('--runtime-evidence', type=Path)
    parser.add_argument('--production-preflight', type=Path)
    parser.add_argument('--report-path', type=Path, required=True)
    parser.add_argument('--confirm-production-replacement', action='store_true')
    parser.add_argument('--confirm-production-rollback', action='store_true')
    args = parser.parse_args(argv)
    if args.target == 'production':
        if args.operation == 'apply' and not args.confirm_production_replacement:
            parser.error('explicit production replacement confirmation required')
        if args.operation == 'rollback' and not args.confirm_production_rollback:
            parser.error('explicit production rollback confirmation required')
    if args.operation != 'preflight' and args.authority is None:
        parser.error('apply/rollback require the exact separately reviewed authority')
    if args.operation == 'apply' and (args.runtime_evidence is None or args.production_preflight is None):
        parser.error('apply requires fresh runtime and read-only preflight evidence')

    def load(path):
        return json.loads(path.read_text(encoding='utf-8')) if path else None

    database_url = os.environ[args.database_url_env]
    identity = target_identity(database_url, args.target)
    write_set = load(args.write_set)
    with _connect(database_url, autocommit=False) as conn:
        if args.operation == 'preflight':
            conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            result = capture_preflight(conn, write_set, production_target_identity_sha256=identity)
        else:
            result = replace_publication(conn, write_set, load(args.authority),
                runtime_evidence=load(args.runtime_evidence), production_preflight=load(args.production_preflight),
                production_target_identity_sha256=identity, rollback=args.operation == 'rollback')
    args.report_path.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n', encoding='utf-8')
    print(result.get('status', 'READ_ONLY_PREFLIGHT_CAPTURED'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
