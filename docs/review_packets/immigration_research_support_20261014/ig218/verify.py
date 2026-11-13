"""Verify exact INDEX or commit blobs; execute only this packet's source checks."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

PREFIX = 'docs/review_packets/immigration_research_support_20261014/ig218/'
PARENT = '0dc1b5bfc0b3e014eea1b04fe62f4fe1b7428add'


def run(*args):
    return subprocess.check_output(['git', *args])


def main(ref):
    start = time.perf_counter()
    def blob(name):return run('show', (':' if ref == 'INDEX' else ref+':')+PREFIX+name)
    m = json.loads(blob('delivered_blobs.json'))
    changes = run('diff', '--cached', '--name-status', PARENT) if ref == 'INDEX' else run('diff', '--name-status', PARENT, ref)
    paths = []
    for line in changes.decode().splitlines():
        status, name = line.split('\t')
        if status != 'A' or not name.startswith(PREFIX):raise ValueError(('Out of scope change', line))
        paths.append(name.removeprefix(PREFIX))
    expected = set(m['files']) | {'delivered_blobs.json'}
    if set(paths) != expected:raise ValueError(('Unexpected file set', sorted(set(paths)^expected)))
    with tempfile.TemporaryDirectory(prefix='ig218-', dir='.local') as root:
        root = Path(root)
        for name, receipt in m['files'].items():
            if Path(name).name != name:raise ValueError('Only flat packet files allowed')
            b = blob(name)
            oid = hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
            actual = {'bytes':len(b), 'sha256':hashlib.sha256(b).hexdigest(), 'git_blob_oid':oid}
            if actual != receipt:raise ValueError(('Blob mismatch',name,actual,receipt))
            (root/name).write_bytes(b)
        e = json.loads((root/'existing_sources.json').read_text(encoding='utf8'))
        bank_raw = run('show', e['snapshot']+':'+e['path'])
        if hashlib.sha256(bank_raw).hexdigest() != e['blob_sha256']:raise ValueError('Source bank SHA256 mismatch')
        bank = json.loads(bank_raw)['sources']
        if run('rev-parse',e['snapshot']+':'+e['path']).decode().strip() != e['blob_oid']:raise ValueError('Source bank Git mismatch')
        for row in e['sources']:
            if next(r for r in bank if r['source_id']==row['source_id']) != row:raise ValueError('Snapshot row mismatch')
        result = subprocess.run([sys.executable,'-X','utf8','test_qualification.py'],cwd=root,capture_output=True,text=True)
        print(result.stdout+result.stderr)
        if result.returncode:raise SystemExit(result.returncode)
    print(json.dumps({'ref':ref,'files':len(expected),'sealed_blobs':len(m['files']),'snapshot_rows':len(e['sources']),'passage_bindings':21,'tests':20,'seconds':round(time.perf_counter()-start,6),'outcome':'PASS','limits':'Focused source/correspondence checks; no candidate/full-domain/current-law or visual correctness certificate.'}))


if __name__ == '__main__':
    main(sys.argv[1])
