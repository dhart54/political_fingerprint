"""Bounded replay compatibility; confer no acceptance or publication authority.

Health slices pinned outputs rather than executing the shared preparation helper.
Its original provenance remains historical evidence. A separate sidecar records
the actual tools used to verify that those frozen products still replay exactly.
"""
import hashlib
import json
from pathlib import Path

from backend.app.semantic_ir.shared_corpus import digest

PACKAGE_PIN = 'a0605e4e3e3a81751bf273155f1cf5e0cfa4d21a'
RULE_BASE = 'ac22199dff31bd2e271d95be82077c8e7de064c4'
PACKAGE_PATH = 'docs/editorial/review_packages/health_s2393_one_action_v1/'
SIDECAR = 'docs/review_packets/health_infrastructure_compatibility140.json'
HELPER = 'scripts/prepare_shared_domain_candidate.py'
PREPARER = 'scripts/prepare_health_one_action_review.py'
HISTORICAL_HELPER = '8eb95a54bb95b17009023e851cfdeb26cb9a4573'
SUCCESSOR_HELPER = '674ec45d22e8f890d654b499e438d4356e0b2227'
HISTORICAL_PREPARER = 'df2ca221f8ca3676130a582d1b53efd8d33382f4'
RULES = [HELPER, *[f'backend/app/semantic_ir/{n}.py' for n in
         ['shared_corpus', 'compiler', 'pipeline', 'adapters', 'validation']],
         'docs/semantic_ir/shared_legislative_corpus_v1.schema.json']
PRODUCTS = ['shared_action_core.json', 'shared_issue_mapping.json', 'member_projections.json',
            'governed_sources.json', 'claim_source_map.json', 'compiler_input.json', 'compiled_ir.json',
            'presentation_payload.json', 'presentation_inputs.json', 'review_source_contract.json',
            'membership_evidence.json', 'provenance.json']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def normalized(raw):
    return raw.decode('utf8').replace('\r\n', '\n').replace('\r', '\n')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def expected_evidence(root, git_bytes, *, current_texts=None):
    """Validate exact allowed code identities, then describe actual replay tools."""
    current = {p: (root / p).read_text(encoding='utf8') for p in RULES} if current_texts is None else current_texts
    require(set(current) == set(RULES), 'Compatibility rule cohort differs')
    old_helper = git_bytes(RULE_BASE, HELPER)
    require(blob(old_helper) == HISTORICAL_HELPER, 'Historical helper identity differs')
    helper_blob = blob(current[HELPER].encode('utf8'))
    require(helper_blob in {HISTORICAL_HELPER, SUCCESSOR_HELPER}, 'Unreviewed shared helper drift')
    frozen_rules = {}
    for path in RULES:
        historical = normalized(git_bytes(RULE_BASE, path))
        if path != HELPER:
            require(current[path] == historical, 'Frozen generation rule differs: ' + path)
        frozen_rules[path] = digest(historical)
    historical_tool = git_bytes(PACKAGE_PIN, PREPARER)
    require(blob(historical_tool) == HISTORICAL_PREPARER, 'Historical Health preparer identity differs')
    frozen = {name: json.loads(git_bytes(PACKAGE_PIN, PACKAGE_PATH + name)) for name in PRODUCTS}
    historical_proof = frozen['provenance.json']
    require(historical_proof['generation_rule_canonical_string_sha256'] == frozen_rules
            and historical_proof['preparation_tool_canonical_string_sha256'] == digest(normalized(historical_tool)),
            'Historical provenance does not authenticate historical tools')
    evidence = {
        'role': 'bounded_replay_compatibility_not_acceptance',
        'historical_package_commit': PACKAGE_PIN, 'historical_rule_base': RULE_BASE,
        'historical_preparer': {'path': PREPARER, 'git_blob': HISTORICAL_PREPARER,
                               'canonical_text_sha256': sha(normalized(historical_tool).encode())},
        'actual_replay_tools': {path: sha((root / path).read_text(encoding='utf8').encode()) for path in
                                [PREPARER, 'scripts/health_infrastructure_compatibility.py']},
        'shared_helper': {'path': HELPER, 'historical_git_blob': HISTORICAL_HELPER,
                          'reviewed_successor_git_blob': SUCCESSOR_HELPER, 'actual_git_blob': helper_blob,
                          'executed_by_Health_preparer': False,
                          'reviewed_change': 'Include substantive non-directional actions in exact authored/interpreted/proposed set equality'},
        'other_six_rule_canonical_string_sha256': {p: frozen_rules[p] for p in RULES if p != HELPER},
        'frozen_package_file_sha256': {name: sha(git_bytes(PACKAGE_PIN, PACKAGE_PATH + name)) for name in PRODUCTS},
        'historical_provenance_policy': 'Retained byte-for-byte as historical evidence; actual replay identities are recorded only in this sidecar',
        'new_editorial_acceptance': False, 'publication_authorized': False,
        'persistence_authorized': False, 'production_writes': False,
    }
    return evidence, frozen


def validate_compatibility(root, git_bytes, *, sidecar=None, current_texts=None):
    expected, frozen = expected_evidence(root, git_bytes, current_texts=current_texts)
    actual = json.loads((root / SIDECAR).read_text(encoding='utf8')) if sidecar is None else sidecar
    require(digest(actual) == digest(expected), 'Compatibility sidecar differs from actual tools or frozen subjects')
    return frozen


def validate_products(outputs, frozen):
    require(set(outputs) == set(PRODUCTS) - {'provenance.json'}, 'Health replay product cohort differs')
    for name, value in outputs.items():
        require(digest(value) == digest(frozen[name]), 'Health replay differs from frozen product: ' + name)
