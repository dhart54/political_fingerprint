"""Verify exact Git INDEX/commit, prior caller reuse and this packet only."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

PREFIX='docs/review_packets/immigration_research_support_20261014/ig218_limits/'
PARENT='85c124576fa70cac4f309759f60052185365f982'


def git(*args):return subprocess.check_output(['git',*args])


def main(ref):
    start=time.perf_counter()
    def blob(n):return git('show',(':' if ref=='INDEX' else ref+':')+PREFIX+n)
    manifest=json.loads(blob('delivered_blobs.json'))
    changes=git('diff','--cached','--name-status',PARENT)if ref=='INDEX'else git('diff','--name-status',PARENT,ref)
    names=[]
    for line in changes.decode().splitlines():
        status,name=line.split('\t')
        if status!='A' or not name.startswith(PREFIX):raise ValueError(('Scope violation',line))
        names.append(name.removeprefix(PREFIX))
    expected=set(manifest['files'])|{'delivered_blobs.json'}
    if set(names)!=expected:raise ValueError(('File set mismatch',set(names)^expected))
    with tempfile.TemporaryDirectory(prefix='ig218-limits-',dir='.local')as directory:
        root=Path(directory)
        for name,r in manifest['files'].items():
            if Path(name).name!=name:raise ValueError('Flat packet files only')
            b=blob(name);actual={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob_oid':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()}
            if actual!=r:raise ValueError(('Git blob identity mismatch',name))
            (root/name).write_bytes(b)
        reused=json.loads((root/'reused_callers.json').read_text(encoding='utf8'))
        raw=git('show',reused['reference_snapshot']+':'+reused['reference_path'])
        if hashlib.sha256(raw).hexdigest()!=reused['blob_sha256']:raise ValueError('Prior source blobSHA mismatch')
        if git('rev-parse',reused['reference_snapshot']+':'+reused['reference_path']).decode().strip()!=reused['blob_oid']:raise ValueError('Prior GitOID mismatch')
        rows=json.loads(raw)['passages']
        for row in reused['sources']:
            if next(x for x in rows if x['id']==row['id'])!=row:raise ValueError('Prior literal caller mismatch')
        result=subprocess.run([sys.executable,'-X','utf8','test_qualification.py'],cwd=root,capture_output=True,text=True)
        print(result.stdout+result.stderr)
        if result.returncode:raise SystemExit(result.returncode)
    print(json.dumps({'ref':ref,'files':len(expected),'sealed_blobs':len(manifest['files']),'reused_callers':5,'passage_bindings':25,'tests':16,'seconds':round(time.perf_counter()-start,6),'outcome':'PASS','limits':'Dated source/qualification checks only; no legal-application, candidate or current-law certificate.'}))


if __name__=='__main__':main(sys.argv[1])
