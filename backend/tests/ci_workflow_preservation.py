"""Preserve historical CI blocks with one exact approved path-filter extension."""
import hashlib
import re

APPROVED_MAIN = 'c52d121b64d814de3cf684980368bced40e5b4ea'
APPROVED_WORKFLOW_BLOB = '2cac1cb6178adf88fd412e63ad6fb48566e721fc'


def assert_prior_ci_preserved(before, after, *, accepted_baseline=None):
    before = before.replace('\r\n', '\n')
    after = after.replace('\r\n', '\n')
    old_header, old_jobs = before.split('\njobs:\n', 1)
    new_header, new_jobs = after.split('\njobs:\n', 1)
    allowed_headers = {old_header}
    anchor = '      - ".github/workflows/backend-tests.yml"'
    extension = '      - ".gitattributes"'
    # This exception admits only the reviewed addition in BOTH existing event
    # filters. It cannot hide another path, branch, event or header change.
    if old_header.count(anchor) == 2 and extension not in old_header:
        allowed_headers.add(old_header.replace(anchor, anchor + '\n' + extension))
    if new_header not in allowed_headers:
        raise AssertionError('CI event/header changed outside exact approved attribute-path extension')

    def blocks(text):
        if re.search(r'(?m)^ {0,1}[^ \n#]', text):
            raise AssertionError('Unexpected top-level CI section after jobs')
        starts = list(re.finditer(r'(?m)^  ([a-zA-Z0-9_-]+):\n', text))
        if len({match.group(1) for match in starts}) != len(starts):
            raise AssertionError('Duplicate CI job identifier')
        return {match.group(1): text[match.start():end].rstrip()
                for match, end in zip(starts, [*[m.start() for m in starts[1:]], len(text)], strict=True)}

    accepted_jobs = {}
    if accepted_baseline is not None:
        raw = accepted_baseline.replace('\r\n', '\n').encode('utf8')
        identity = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        if identity != APPROVED_WORKFLOW_BLOB:
            raise AssertionError('Accepted CI baseline identity differs')
        accepted_jobs = blocks(raw.decode('utf8').split('\njobs:\n', 1)[1])
    existing, current = blocks(old_jobs), blocks(new_jobs)
    for name, original in existing.items():
        if name in current and original == current[name]:
            continue
        # Later accepted main extended the receipt job. Preserve that exact
        # pinned evolution, including every original byte; permit no new change.
        accepted = accepted_jobs.get(name)
        if accepted is None or original not in accepted or current.get(name) != accepted:
            raise AssertionError('Prior CI job changed: ' + name)
