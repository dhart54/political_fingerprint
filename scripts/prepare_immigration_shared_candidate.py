"""Immigration-only candidate source binding over the established Semantic IR V1.

The common adapter and canonical V1 contracts remain unchanged. Historical proof
receipts are preserved. Ordinary shared-core reuse binds a sealed candidate
identity; deemed concurrence admits only explicitly bound unamended or whole
replacement choices. It
invents no House question, member observation, legislative meaning, acceptance
or publication authority.
"""
from __future__ import annotations
import argparse
import copy
import json
import re
import sys
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import prepare_shared_domain_candidate as common
from scripts.prepare_shared_domain_candidate import identity, readable_candidates, review_text, write_json
from backend.app.semantic_ir.shared_corpus import (
    adapt_to_semantic_ir_input, candidate_update_impact, choice_effect, digest,
    sealed_digest, validate_member_projection, validate_shared_action_core, SharedCorpusValidationError,
)
from backend.app.semantic_ir.pipeline import run_editorial_pipeline
from backend.app.semantic_ir import shared_corpus
CANDIDATE = common.CANDIDATE

_HEALTH_PROVIDER = Path("docs/editorial/shared_candidates/house_119_health_20260916/generated/shared_action_core.json")
_SHARED_SCHEMA = "docs/semantic_ir/shared_legislative_corpus_v1.schema.json"
_UNOBSERVED = object()


def _same_json(left, right):
    """Python equality alone conflates JSON booleans and numbers."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_same_json(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(_same_json(a, b) for a, b in zip(left, right))
    if isinstance(left, float):
        return left == right and left.hex() == right.hex()
    return left == right


class _ObservedSchemaPath:
    def __init__(self, path, observation):
        self.path, self.observation = path, observation

    def read_text(self, *args, **kwargs):
        if self.observation.text is _UNOBSERVED:
            text = self.path.read_text(*args, **kwargs)
            self.observation.reads.append(text)
            return text
        return self.observation.text

    def __fspath__(self):
        return str(self.path)

    def __str__(self):
        return str(self.path)

    def __getattr__(self, name):
        return getattr(self.path, name)


class _ObservedSchemaRoot:
    """Give the existing validator its exact fresh read without reading twice."""
    def __init__(self, root, text=_UNOBSERVED):
        self.root, self.text = root, text
        self.reads = []

    def __truediv__(self, name):
        path = self.root / name
        return _ObservedSchemaPath(path, self) if name == _SHARED_SCHEMA else path

    def __fspath__(self):
        return str(self.root)

    def __str__(self):
        return str(self.root)

    def __getattr__(self, name):
        return getattr(self.root, name)


class _HealthProviderValidation:
    """One successful value, private to a single Immigration prepare call."""
    def __init__(self):
        self.observation = None
        self.root = None
        self.dependencies_changed = False

    @staticmethod
    def _dependencies():
        try:
            return (
                validate_shared_action_core, shared_corpus._validate_schema, shared_corpus._walk_keys,
                shared_corpus.sealed_digest, shared_corpus.digest, shared_corpus.canonical_bytes,
                shared_corpus._identity_set, shared_corpus.Draft202012Validator, shared_corpus.FormatChecker,
                frozenset(shared_corpus.MEMBER_FIELDS),
                tuple(shared_corpus.Draft202012Validator.VALIDATORS.items()),
                tuple((name, checker, tuple(raises) if isinstance(raises, (list, tuple)) else raises)
                      for name, (checker, raises) in shared_corpus.FormatChecker.checkers.items()),
            )
        except (AttributeError, TypeError, ValueError, RuntimeError):
            # Unsupported or changing registry configuration takes original dispatch.
            return None

    def validate(self, root, path, provider_text, provider):
        validator = validate_shared_action_core
        dependencies = self._dependencies()
        if (self.dependencies_changed or dependencies is None
                or self.observation is not None and dependencies != self.observation[0][-1]):
            self.dependencies_changed = True
            return validator(root, provider)
        if self.observation is None:
            observed_root = _ObservedSchemaRoot(root)
            validator(observed_root, provider)
            if len(observed_root.reads) == 1 and dependencies == self._dependencies():
                key = (id(root), str(root), path, provider_text, observed_root.reads[0], dependencies)
                self.observation = (key, copy.deepcopy(provider))
                self.root = root
            else:
                self.dependencies_changed = True
            return
        # Only unchanged established dispatch may observe before deciding reuse.
        schema_text = (root / _SHARED_SCHEMA).read_text(encoding="utf-8")
        key = (id(root), str(root), path, provider_text, schema_text, dependencies)
        prior_key, prior_provider = self.observation
        if (dependencies == self._dependencies() and root is self.root
                and key == prior_key and _same_json(provider, prior_provider)):
            return
        validator(_ObservedSchemaRoot(root, schema_text), provider)
        if dependencies == self._dependencies():
            self.observation = (key, copy.deepcopy(provider))
            self.root = root
        else:
            self.dependencies_changed = True

def _extended(action):
    witness = action.get("deemed_concurrence")
    return (isinstance(witness, dict) and "senate_amendment_source_id" in witness
            or "deemed_replacement_concurrence" in action)


def _bind_replacement_concurrence(proposed, sources, congress, clerk):
    witness = proposed.get("deemed_replacement_concurrence")
    if (not isinstance(witness, dict)
            or set(witness) != {"underlying_bill_number", "source_id", "passage",
                                "replacement_text_source_id", "rules_committee_print_number"}
            or "deemed_concurrence" in proposed
            or proposed.get("stage") != "concurrence"
            or proposed.get("bill_type") != "hres"):
        raise ValueError("invalid whole-replacement concurrence binding")
    number = witness["underlying_bill_number"]
    print_number = witness["rules_committee_print_number"]
    if (not isinstance(number, str) or not number.isdigit() or int(number) <= 0
            or not isinstance(print_number, str) or not print_number.isdigit()
            or int(print_number) <= 0
            or proposed["episode_id"] != f"episode:hr{number}:{congress}"
            or witness["source_id"] != proposed["source_id"]):
        raise ValueError("replacement concurrence must bind the underlying bill episode and print")
    source = sources[witness["source_id"]]
    clause = witness["passage"]
    prefix = ("Resolved, That upon adoption of this resolution, the House shall be "
              "considered to have taken from the Speaker's table the bill "
              f"(H.R. {number}) ")
    suffix = (", with the Senate amendment thereto, and to have concurred in the "
              "Senate amendment with an amendment consisting of the text of "
              f"Rules Committee Print {congress}-{print_number}.")
    if (source["source_type"] != "official_bill_text" or source["text_version"] != "EH"
            or f"[H. Res. {proposed['bill_number']} Engrossed in House (EH)]" not in source["text"]
            or not isinstance(clause, str) or not clause.startswith(prefix)
            or not clause.endswith(suffix)
            or not source["text"].endswith(clause + " Attest: Clerk.")
            or source["text"].count("Resolved,") != 1
            or not any(c["source_id"] == source["source_id"] and c["passage"] == clause
                       for c in proposed["claim_source_map"])):
        raise ValueError("replacement concurrence requires the exact governed operative clause")
    replacement_id = witness["replacement_text_source_id"]
    if (replacement_id not in proposed.get("additional_source_ids", [])
            or replacement_id not in sources):
        raise ValueError("replacement concurrence requires the whole exact Rules print")
    replacement = sources[replacement_id]
    normalized = " ".join(replacement["text"].split())
    header = f"RULES COMMITTEE PRINT {congress}–{print_number}"
    try:
        house_choice = datetime.strptime(
            clerk["metadata"]["action-date"] + " " + clerk["metadata"]["action-time"],
            "%d-%b-%Y %I:%M %p",
        )
    except (KeyError, ValueError) as exc:
        raise ValueError("replacement concurrence requires the exact dated Clerk time") from exc
    dates = re.findall(r"([A-Za-z]+) (\d+), (\d{4}) \((\d+):(\d+) ([ap])\.m\.\)", normalized)
    if (replacement["source_type"] != "official_rules_committee_print"
            or header not in normalized
            or f"TEXT OF THE HOUSE AMENDMENT TO THE SENATE AMENDMENT TO H.R. {number}" not in normalized
            or "In lieu of the matter proposed to be inserted by the Senate amendment, insert the following:" not in normalized
            or not dates
            or not any(c["source_id"] == replacement_id and c["passage"] == replacement["text"]
                       for c in proposed["claim_source_map"])):
        raise ValueError("replacement concurrence requires the whole exact Rules print")
    timestamps = [datetime.strptime(
        " ".join(date[:3]) + " " + date[3] + ":" + date[4] + " " + date[5].upper() + "M",
        "%B %d %Y %I:%M %p",
    ) for date in dates]
    if any(stamp > house_choice for stamp in timestamps):
        raise ValueError("replacement concurrence Rules print follows the House choice")
    return True

def _bind_concurrence(proposed, sources, congress, clerk):
    witness = proposed["deemed_concurrence"]
    if proposed.get("stage") != "concurrence":
        raise ValueError("invalid deemed-concurrence candidate binding")
    if (set(witness) != {"underlying_bill_number", "source_id", "passage",
                        "senate_amendment_source_id"}
            or proposed.get("bill_type") != "hres" or clerk is None):
        raise ValueError("invalid deemed-concurrence candidate binding")
    number = witness["underlying_bill_number"]
    if (not isinstance(number, str) or not number.isdigit() or int(number) <= 0
            or proposed["episode_id"] != f"episode:hr{number}:{congress}"
            or witness["source_id"] != proposed["source_id"]):
        raise ValueError("deemed concurrence must bind the underlying bill episode")
    source = sources[witness["source_id"]]
    clause = witness["passage"]
    prefix = (
        "Resolved, That upon adoption of this resolution, the House shall be "
        "considered to have taken from the Speaker's table the bill "
        f"(H.R. {number}) "
    )
    suffix = (", with the Senate amendment thereto, and to have concurred "
              "in the Senate amendment.")
    if (source["source_type"] != "official_bill_text" or source["text_version"] != "EH"
            or f"[H. Res. {proposed['bill_number']} Engrossed in House (EH)]" not in source["text"]
            or not isinstance(clause, str) or not clause.startswith(prefix)
            or not clause.endswith(suffix)
            or not source["text"].endswith(clause + " Attest: Clerk.")
            or source["text"].count("Resolved,") != 1
            or not any(c["source_id"] == source["source_id"] and c["passage"] == clause
                       for c in proposed["claim_source_map"])):
        raise ValueError("deemed concurrence requires the exact governed operative clause")
    amendment_id = witness["senate_amendment_source_id"]
    if amendment_id not in proposed.get("additional_source_ids", []):
        raise ValueError("deemed concurrence requires the exact Senate amendment")
    amendment = sources[amendment_id]
    senate_date = re.search(
        r"In the Senate of the United States, ([A-Za-z]+) (\d+)(?: \([^)]*\))?, (\d{4})\.",
        amendment["text"],
    )
    if (amendment["source_type"] != "official_bill_text" or amendment["text_version"] != "EAS"
            or f"[H.R. {number} Engrossed Amendment Senate (EAS)]" not in amendment["text"]
            or not any(c["source_id"] == amendment_id and c["passage"] == amendment["text"]
                       for c in proposed["claim_source_map"])
            or senate_date is None):
        raise ValueError("deemed concurrence requires the exact Senate amendment")
    dated = datetime.strptime(" ".join(senate_date.groups()), "%B %d %Y").date()
    house_date = datetime.strptime(clerk["metadata"]["action-date"], "%d-%b-%Y").date()
    if dated > house_date:
        raise ValueError("deemed concurrence Senate amendment follows the House choice")
    return True

def _action_source_constraints(authoring):
    """Carry explicitly authored action boundaries without interpreting prose."""
    constraints = []
    ids = {"candidate-episode-hold"}
    for action in authoring["actions"]:
        rows = action.get("source_render_constraints", [])
        if not isinstance(rows, list):
            raise ValueError("action source constraints must be a list")
        for row in rows:
            if (not isinstance(row, dict)
                    or set(row) != {"action_ids", "constraint_id", "detail", "semantic_effect"}
                    or row["action_ids"] != [action["action_id"]]
                    or any(not isinstance(row[k], str) or not row[k].strip()
                           for k in ["constraint_id", "detail", "semantic_effect"])):
                raise ValueError("source constraint must bind its own exact action")
            if row["constraint_id"] in ids:
                raise ValueError("duplicate action source constraint identity")
            ids.add(row["constraint_id"])
            constraints.append(copy.deepcopy(row))
    return constraints


def _source_bound_substitute_question(authoring, proposed, sources):
    """Reconstruct the full whole-passage label from its adopted rule section."""
    binding = proposed.get('source_review_question_binding')
    if (not isinstance(binding, dict)
            or set(binding) != {'source_id', 'section', 'kind'}
            or binding['kind'] != 'adopted_substitute_passage'
            or type(binding['section']) is not int or binding['section'] <= 0
            or proposed['stage'] != 'final_passage'):
        raise ValueError('source-review question requires an exact adopted-substitute binding')
    source = sources.get(binding['source_id'])
    if (source is None or source['source_type'] != 'official_bill_text'
            or source['text_version'] != 'EH'
            or binding['source_id'] not in proposed.get('additional_source_ids', [])):
        raise ValueError('source-review question lacks a governed engrossed rule')
    header = re.search(r'\[H\. Res\. ([1-9][0-9]*) Engrossed in House \(EH\)\]', source['text'])
    section = re.search(r'Sec\. ' + str(binding['section'])
                        + r'\. (.*?)(?=Sec\. [0-9]+\.|$)', source['text'], re.S)
    bill = {'s': 'S.', 'hr': 'H.R.'}.get(proposed.get('bill_type', 'hr'))
    if not header or not section or bill is None:
        raise ValueError('source-review question lacks its exact rule section')
    clause = section[0].rstrip()
    if (f"bill ({bill} {proposed['bill_number']})" not in clause
            or not re.search(r'An amendment in the nature of a substitute consisting of the text of Rules Committee Print '
                             + str(authoring['congress'])
                             + r'-\s*[0-9]+, modified by the amendment printed in part [A-Z] of the report of the Committee on Rules accompanying this resolution, shall be considered as adopted\.', clause)
            or 'on the bill, as amended, and on any further amendment thereto, to final passage' not in clause
            or not any(c['source_id'] == source['source_id'] and clause in c['passage']
                       for c in proposed['claim_source_map'])):
        raise ValueError('source-review question does not bind whole adopted-substitute passage')
    return (f"On passage of {bill}{proposed['bill_number']} as amended by the substitute "
            f"adopted under H.Res.{header[1]} section{binding['section']}.")


def _require_complete_candidate_wrapper(canonical, generated, sources, outcome_ids, identity_overrides,
                                        compiler_source_identities=None):
    """Bind every typed wrapper field, preserving explicitly governed outcomes."""
    expected = copy.deepcopy(generated)
    expected.update(identity_overrides)
    expected['action_outcome_source_identities'] = [identity(sources[sid]) for sid in outcome_ids]
    expected['governed_source_identities'] = [*expected['action_outcome_source_identities'],
                                              *expected['operative_meaning_source_identities']]
    expected['governed_source_identity_sha256'] = digest(expected['governed_source_identities'])
    compiler_sources = (expected['governed_source_identities'] if compiler_source_identities is None
                        else compiler_source_identities)
    expected['semantic_ir_source_ids'] = [s['source_id'] for s in compiler_sources]
    expected['action_core_sha256'] = sealed_digest(expected, 'action_core_sha256')
    if set(canonical) != set(expected):
        raise ValueError('candidate wrapper field set differs from exact generated action')
    for field in sorted(set(expected) - {'action_core_sha256'}):
        if canonical[field] != expected[field]:
            raise ValueError('candidate differs from complete exact Clerk-bound wrapper: ' + field)
    if canonical['action_core_sha256'] != expected['action_core_sha256']:
        raise ValueError('candidate wrapper seal differs from exact generated action')


def _prepare_source_review_reuse(authoring, capture, proposed, canonical, member_ids):
    """Copy a qualified V1 candidate after binding its source-review wrapper."""
    aid = proposed['action_id']
    if (not canonical['meaning_contract_version'].startswith('source_review')
            or not re.fullmatch(re.escape('candidate-exact-action:' + aid)
                                + r':source-review\d+:v\d+', canonical['action_meaning_ref'])
            or canonical['mechanism_availability'] != 'candidate_source_grounded_pending_external_semantic_review'):
        raise ValueError('unsupported source-review candidate identity')
    sources = {s['source_id']: s for s in capture['sources']}
    clerk_id = 'clerk:' + aid.removeprefix('house:')
    outcome_ids = [clerk_id, *proposed.get('additional_action_outcome_source_ids', [])]
    if (len(outcome_ids) != len(set(outcome_ids))
            or [s['source_id'] for s in canonical['action_outcome_source_identities']] != outcome_ids):
        raise ValueError('source-review outcome witness roles differ')
    # Every role, version and seal must bind the supplied capture, including the
    # additional own Record witness that ordinary preparation does not partition.
    for witness in canonical['governed_source_identities']:
        if witness['source_id'] not in sources or identity(sources[witness['source_id']]) != witness:
            raise ValueError('source-review governed witness differs from capture')
    subset = copy.deepcopy(authoring)
    subset['actions'] = [copy.deepcopy(proposed)]
    subset['blocked_episode_ids'] = []
    prepared = common.prepare(subset, capture, member_ids)
    generated = prepared[0]['actions'][0]
    expected_measure = f"{authoring['congress']}:{proposed.get('bill_type', 'hr')}:{proposed['bill_number']}"
    if (canonical['exact_action_identity'] != expected_measure
            or ''.join(canonical['exact_question'].split()).casefold()
            != ''.join(_source_bound_substitute_question(authoring, proposed, sources).split()).casefold()
            or canonical['mechanism'] not in [canonical['candidate_exact_action_meaning'], canonical['candidate_short_description']]):
        raise ValueError('source-review exact-action wrapper differs from Clerk-bound input')
    wrapper_binding = proposed.get('source_review_wrapper_binding')
    if (not isinstance(wrapper_binding, dict)
            or set(wrapper_binding) != {'artifact_ref', 'artifact_id', 'action_core_sha256'}):
        raise ValueError('source-review lacks its preserved typed-wrapper binding')
    wrapper_path = (ROOT / wrapper_binding['artifact_ref']).resolve()
    if (wrapper_path.name != 'shared_action_core_proposal.json'
            or not wrapper_path.is_relative_to((ROOT / 'docs/editorial/shared_candidates').resolve())
            or wrapper_path == (ROOT / proposed['shared_core_reuse']['artifact_ref']).resolve()):
        raise ValueError('source-review typed wrapper must bind a distinct preserved provider')
    wrapper_provider = json.loads(wrapper_path.read_text(encoding='utf-8'))
    validate_shared_action_core(ROOT, wrapper_provider)
    prior = next((a for a in wrapper_provider['actions'] if a['action_id'] == aid), None)
    if (wrapper_provider['artifact_id'] != wrapper_binding['artifact_id'] or prior is None
            or prior['action_core_sha256'] != wrapper_binding['action_core_sha256']
            or prior['action_meaning_ref'] != canonical['action_meaning_ref']
            or prior['exact_action_identity'] != expected_measure):
        raise ValueError('source-review preserved typed-wrapper identity or seal differs')
    _require_complete_candidate_wrapper(canonical, generated, sources, outcome_ids, dict(
        exact_action_identity=expected_measure,
        exact_question=canonical['exact_question'],
        action_meaning_ref=canonical['action_meaning_ref'],
        meaning_contract_version=prior['meaning_contract_version'],
        package_component_boundary=copy.deepcopy(prior['package_component_boundary']),
        source_contract_version=prior['source_contract_version'],
        mechanism_availability='candidate_source_grounded_pending_external_semantic_review',
        mechanism=canonical['mechanism'],
    ), compiler_source_identities=generated['operative_meaning_source_identities'])
    return copy.deepcopy(canonical), prepared[1]['action_mappings'][0], prepared[1]['episodes'][0]


def _prepare_legacy_fisa_reuse(authoring, capture, proposed, canonical, member_ids):
    """Qualify a frozen FISA extension without rewriting its accepted core."""
    import hashlib
    import xml.etree.ElementTree as ET
    witness = proposed.get('legacy_core_qualification')
    if (not isinstance(witness, dict)
            or set(witness) not in ({'artifact_ref', 'artifact_id', 'action_core_sha256', 'source_bindings'},
                                   {'artifact_ref', 'artifact_id', 'action_core_sha256', 'source_bindings', 'preserved_metadata_conflict'})
            or canonical['meaning_contract_version'] != 'source_qualified_legacy_fisa_extension_v1'
            or canonical['mechanism_availability'] != 'candidate_source_grounded_pending_external_semantic_review'):
        raise ValueError('invalid legacy FISA qualification contract')
    target = (ROOT / witness['artifact_ref']).resolve()
    if (target.name != 'shared_action_core.json'
            or not target.is_relative_to((ROOT / 'docs/editorial/shared_corpora').resolve())):
        raise ValueError('legacy qualification must reference a frozen shared corpus')
    provider = json.loads(target.read_text(encoding='utf-8'))
    validate_shared_action_core(ROOT, provider)
    original = next((a for a in provider['actions'] if a['action_id'] == proposed['action_id']), None)
    if (provider['authoritative_for_new_editorial_work'] is not True
            or provider['artifact_id'] != witness['artifact_id'] or original is None
            or original['action_core_sha256'] != witness['action_core_sha256']
            or canonical['action_meaning_ref'] != original['action_meaning_ref']
            or canonical['exact_action_identity'] != original['exact_action_identity']
            or not canonical['candidate_exact_action_meaning'].startswith(original['accepted_exact_action_meaning'])
            or not set(original['accepted_shared_limitations']) <= set(canonical['candidate_shared_limitations'])
            or original['legislative_stage'] != 'suspension_passage'
            or proposed['stage'] != 'suspension_and_passage' or proposed.get('bill_type') not in {'hr', 's'}):
        raise ValueError('legacy qualification changes the frozen identity or accepted basis')
    sources = {s['source_id']: s for s in capture['sources']}
    clerk_id = 'clerk:' + proposed['action_id'].removeprefix('house:')
    bindings = witness['source_bindings']
    if (not isinstance(bindings, list) or len(bindings) != 2
            or any(not isinstance(b, dict) or set(b) != {'source_id', 'raw_ref'} for b in bindings)
            or {b['source_id'] for b in bindings} != {s['source_id'] for s in original['governed_source_identities']}):
        raise ValueError('legacy qualification lacks the complete frozen source set')
    primary = sources[proposed['source_id']]
    for binding in bindings:
        old_source = next(s for s in original['governed_source_identities'] if s['source_id'] == binding['source_id'])
        path = (ROOT / binding['raw_ref']).resolve()
        if (path.suffix != '.xml'
                or not path.is_relative_to((ROOT / 'docs/editorial/full_record_reviews/source_readiness/evidence').resolve())):
            raise ValueError('legacy witness must reference frozen evidence XML')
        raw = path.read_bytes()
        if (hashlib.sha256(raw).hexdigest() != old_source['raw_sha256']
                or old_source['governed_bytes_sha256'] != old_source['raw_sha256']):
            raise ValueError('legacy frozen witness bytes differ')
        root = ET.fromstring(raw)
        if old_source['source_id'] == clerk_id:
            meta = root.find('vote-metadata')
            if (root.tag != 'rollcall-vote' or meta is None
                    or {e.tag: e.text for e in meta if e.tag != 'vote-totals'} != sources[clerk_id]['metadata']):
                raise ValueError('legacy Clerk source version changes exact action metadata')
            totals = [{e.tag: e.text for e in p} for p in meta.findall('vote-totals/totals-by-party')]
            if totals != sources[clerk_id]['party_totals']:
                raise ValueError('legacy Clerk party totals differ from capture')
            observed = {v.find('legislator').attrib['name-id']: v.findtext('vote')
                        for v in root.findall('vote-data/recorded-vote')}
            for mid in member_ids:
                if observed.get(mid) != sources[clerk_id]['member_records'][mid]['official_label']:
                    raise ValueError('legacy Clerk member observation differs')
        else:
            title = root.findtext('metadata/dublinCore/{http://purl.org/dc/elements/1.1/}title', '')
            is_es = proposed['bill_type'] == 's'
            conflict = witness.get('preserved_metadata_conflict')
            if is_es:
                qualification = ('The frozen 110/119 title ambiguity remains in the historical accepted record; '
                                 'this unapproved candidate binds separately governed 119th-Congress ES and own '
                                 'House Record without repairing or reclassifying that XML.')
                independent_ids = ['govinfo:s4465es', 'immigration:roll155-operative182',
                                   'immigration:roll155-recorded182']
                if (proposed['action_id'] != 'house:119:2:155'
                        or original['action_core_sha256'] != '980d0ab08ded521f6976b4109e35f041a41943080920e0a2b668d3b682eaa3a0'
                        or not title.startswith('110 S4465 ES:')
                        or not isinstance(conflict, dict)
                        or set(conflict) != {'original_title', 'separate_binding_source_ids', 'qualification'}
                        or conflict['original_title'] != title
                        or conflict['separate_binding_source_ids'] != independent_ids
                        or conflict['qualification'] != qualification
                        or qualification not in canonical['candidate_exact_action_meaning']
                        or qualification not in canonical['candidate_shared_limitations']
                        or proposed['source_id'] != independent_ids[0]
                        or independent_ids[1] not in proposed.get('additional_source_ids', [])
                        or proposed.get('additional_action_outcome_source_ids') != independent_ids[2:]):
                    raise ValueError('legacy ES title conflict lacks its preserved separate-source qualification')
                from scripts.validate_source_sequence import require_exact_bill_operative
                require_exact_bill_operative(sources[independent_ids[1]]['text'], 'S.4465')
                expected_stage = 'Engrossed-in-Senate'
                expected_form = f"S. {proposed['bill_number']}"
                expected_header = f"[S. {proposed['bill_number']} Engrossed in Senate (ES)]"
                complete_extent = (' Passed the Senate April 30, 2026. Attest: Secretary.' in primary['text']
                                   and primary.get('text_version') == 'ES')
            else:
                if conflict is not None or not title.startswith(f"{authoring['congress']} HR {proposed['bill_number']} :"):
                    raise ValueError('legacy CDH title differs or attempts a metadata exception')
                expected_stage = 'Committee-Discharged-House'
                expected_form = f"H. R. {proposed['bill_number']}"
                expected_header = f"[H.R. {proposed['bill_number']} Committee Discharged House (CDH)]"
                complete_extent = primary['text'].endswith(' <all>')
            if (root.tag != 'bill' or root.attrib.get('bill-stage') != expected_stage
                    or root.findtext('form/congress') != f"{authoring['congress']}th CONGRESS"
                    or root.findtext('form/legis-num') != expected_form
                    or f"[Congressional Bills {authoring['congress']}th Congress]" not in primary['text']
                    or expected_header not in primary['text'] or not complete_extent):
                raise ValueError('legacy bill source identity or exact ES/CDH version differs')
            body = root.find('legis-body')
            if body is None or len(body.findall('section')) != 1:
                raise ValueError('legacy extension lacks its complete one-section body')
            paragraphs = body.findall('section/subsection/paragraph')
            if ([p.findtext('enum') for p in paragraphs] != ['(1)', '(2)']
                    or any(len(p.findall('text/quote')) != 2 for p in paragraphs)):
                raise ValueError('legacy extension lacks the two exact repeal operators')
            pairs = [[q.text for q in p.findall('text/quote')] for p in paragraphs]
            for number, pair in enumerate(pairs, 1):
                target_note = ('(50 U.S.C. 1881 note)' if number == 1
                               else '(18 U.S.C. 2511 note)' + (', ' if is_es else ' ')
                               + 'in the matter preceding subparagraph (A)')
                operator = (f"in paragraph ({number}) {target_note}, by striking ``{pair[0]}'' "
                            f"and inserting ``{pair[1]}''")
                if operator not in primary['text']:
                    raise ValueError('captured extension changes a literal repeal operator')
            effective = next((p for p in body.findall('section/subsection')
                              if p.findtext('enum') == '(b)'), None)
            if effective is None or effective.find('text') is None:
                raise ValueError('legacy extension lacks the effective-date clause')
            effective_text = ' '.join(effective.find('text').itertext()).strip()
            if effective_text not in primary['text']:
                raise ValueError('captured extension changes literal effective-date clause')
            normalized = lambda text: re.sub(r'[^a-z0-9]', '', text.casefold())
            end = primary['text'].index(' Passed the Senate ') if is_es else -len(' <all>')
            text = primary['text'][primary['text'].index('SECTION 1.'):end].removeprefix('SECTION ')
            if normalized(' '.join(body.itertext())) != normalized(text):
                raise ValueError('legacy and captured complete operative bodies differ')
            if is_es:
                own = sources[independent_ids[1]]['text']
                own_body = own[own.index('SECTION 1.'):own.index('The SPEAKER pro tempore.')].removeprefix('SECTION ')
                if normalized(' '.join(body.itertext())) != normalized(own_body):
                    raise ValueError('separate own Record complete operative body differs')
    outcome_ids = [clerk_id, *proposed.get('additional_action_outcome_source_ids', [])]
    if (len(outcome_ids) != len(set(outcome_ids))
            or [s['source_id'] for s in canonical['action_outcome_source_identities']] != outcome_ids):
        raise ValueError('legacy candidate outcome witness roles differ')
    for s in canonical['governed_source_identities']:
        if s['source_id'] not in sources or identity(sources[s['source_id']]) != s:
            raise ValueError('legacy candidate source version differs from capture')
    subset = copy.deepcopy(authoring)
    subset['actions'] = [copy.deepcopy(proposed)]
    subset['blocked_episode_ids'] = []
    prepared = common.prepare(subset, capture, member_ids)
    generated = prepared[0]['actions'][0]
    _require_complete_candidate_wrapper(canonical, generated, sources, outcome_ids, dict(
        exact_action_identity=original['exact_action_identity'],
        action_meaning_ref=original['action_meaning_ref'],
        meaning_contract_version='source_qualified_legacy_fisa_extension_v1',
        mechanism_availability='candidate_source_grounded_pending_external_semantic_review',
        mechanism=canonical['mechanism'],
    ))
    for field in ['action_id', 'chamber', 'congress', 'session', 'roll', 'action_date', 'chamber_outcome', 'enactment_status']:
        if canonical[field] != original[field]:
            raise ValueError('legacy candidate changes frozen exact-action metadata: ' + field)
    if (canonical['exact_action_identity'] != f"{authoring['congress']}:{proposed['bill_type']}:{proposed['bill_number']}"
            or canonical['mechanism'] not in [canonical['candidate_exact_action_meaning'], canonical['candidate_short_description']]):
        raise ValueError('legacy candidate exact measure or mechanism differs')
    return copy.deepcopy(canonical), prepared[1]['action_mappings'][0], prepared[1]['episodes'][0]



def _prepare_candidate_core_augmentation(authoring, capture, proposed, canonical, member_ids, health_validation=None):
    """Qualify an existing unapproved candidate without rewriting its meaning."""
    binding = proposed.get('candidate_core_qualification')
    if (not isinstance(binding, dict)
            or set(binding) != {'artifact_ref', 'artifact_id', 'action_core_sha256'}
            or canonical['meaning_contract_version'] != 'source_qualified_candidate_augmentation_v1'
            or canonical['mechanism_availability'] != 'candidate_source_grounded_pending_external_semantic_review'):
        raise ValueError('invalid candidate-core qualification contract')
    path = (ROOT / binding['artifact_ref']).resolve()
    if (path.name != 'shared_action_core.json'
            or not path.is_relative_to((ROOT / 'docs/editorial/shared_candidates').resolve())):
        raise ValueError('candidate qualification must bind an existing shared candidate')
    provider_text = path.read_text(encoding='utf-8')
    provider = json.loads(provider_text)
    if health_validation is not None and Path(binding['artifact_ref']) == _HEALTH_PROVIDER:
        health_validation.validate(ROOT, path, provider_text, provider)
    else:
        validate_shared_action_core(ROOT, provider)
    original = next((a for a in provider['actions'] if a['action_id'] == proposed['action_id']), None)
    if (provider['authoritative_for_new_editorial_work'] is not False
            or provider['artifact_id'] != binding['artifact_id'] or original is None
            or original['action_core_sha256'] != binding['action_core_sha256']
            or 'candidate_exact_action_meaning' not in original
            or canonical['action_meaning_ref'] != original['action_meaning_ref']
            or canonical['exact_action_identity'] != original['exact_action_identity']
            or not canonical['candidate_exact_action_meaning'].startswith(original['candidate_exact_action_meaning'])
            or not set(original['candidate_shared_limitations']) <= set(canonical['candidate_shared_limitations'])):
        raise ValueError('candidate qualification changes original identity or meaning basis')
    sources = {s['source_id']: s for s in capture['sources']}
    if proposed['source_id'] != original['operative_meaning_source_identities'][0]['source_id']:
        raise ValueError('candidate qualification changes original primary source')
    for witness in original['governed_source_identities']:
        if (witness['source_id'] not in sources or identity(sources[witness['source_id']]) != witness
                or witness not in canonical['governed_source_identities']):
            raise ValueError('candidate qualification changes an original governed source identity')
    for witness in canonical['governed_source_identities']:
        if witness['source_id'] not in sources or identity(sources[witness['source_id']]) != witness:
            raise ValueError('candidate qualification source differs from actual capture')
    clerk_id = 'clerk:' + proposed['action_id'].removeprefix('house:')
    outcome_ids = [clerk_id, *proposed.get('additional_action_outcome_source_ids', [])]
    if len(outcome_ids) != len(set(outcome_ids)):
        raise ValueError('candidate qualification repeats an outcome witness')
    subset = copy.deepcopy(authoring)
    subset['actions'] = [copy.deepcopy(proposed)]
    subset['blocked_episode_ids'] = []
    prepared = common.prepare(subset, capture, member_ids)
    generated = prepared[0]['actions'][0]
    for field in ['action_id', 'chamber', 'congress', 'session', 'roll', 'legislative_stage',
                  'action_date', 'exact_question', 'chamber_outcome', 'enactment_status']:
        if generated[field] != original[field]:
            raise ValueError('candidate qualification changes original exact action metadata: ' + field)
    if canonical['mechanism'] not in [canonical['candidate_exact_action_meaning'], canonical['candidate_short_description']]:
        raise ValueError('candidate qualification mechanism differs from current meaning')
    _require_complete_candidate_wrapper(canonical, generated, sources, outcome_ids, dict(
        exact_action_identity=original['exact_action_identity'],
        action_meaning_ref=original['action_meaning_ref'],
        meaning_contract_version='source_qualified_candidate_augmentation_v1',
        mechanism_availability='candidate_source_grounded_pending_external_semantic_review',
        mechanism=canonical['mechanism'],
    ))
    return copy.deepcopy(canonical), prepared[1]['action_mappings'][0], prepared[1]['episodes'][0]


def _prepare_reused_action(authoring, capture, proposed, member_ids, health_validation=None):
    """Bind an ordinary candidate to an existing, sealed V1 core identity."""
    ref = proposed['shared_core_reuse']
    required = {'artifact_ref', 'artifact_id', 'action_id', 'action_meaning_ref', 'action_core_sha256'}
    if (not isinstance(ref, dict) or set(ref) != required
            or ref['action_id'] != proposed['action_id'] or _extended(proposed)):
        raise ValueError('invalid shared-core reuse reference')
    relative = Path(ref['artifact_ref'])
    target = (ROOT / relative).resolve()
    if (relative.is_absolute() or target.name not in {'shared_action_core.json', 'shared_action_core_proposal.json'}
            or not target.is_relative_to((ROOT / 'docs/editorial/shared_candidates').resolve())):
        raise ValueError('shared-core reuse must reference a repository candidate corpus')
    provider = json.loads(target.read_text(encoding='utf-8'))
    if (provider['schema_version'] != 'shared_action_core_v1'
            or provider['review_state'] != CANDIDATE
            or provider['authoritative_for_new_editorial_work']
            or provider['artifact_id'] != ref['artifact_id']
            or provider['corpus_sha256'] != digest(provider['actions'])):
        raise ValueError('invalid shared-core reuse corpus')
    rows = [a for a in provider['actions'] if a['action_id'] == ref['action_id']]
    if len(rows) != 1:
        raise ValueError('shared-core reuse requires one exact action')
    canonical = rows[0]
    if (canonical['action_core_sha256'] != ref['action_core_sha256']
            or canonical['action_meaning_ref'] != ref['action_meaning_ref']
            or canonical['action_core_sha256'] != sealed_digest(canonical, 'action_core_sha256')):
        raise ValueError('stale shared-core reuse reference')
    if target.name == 'shared_action_core_proposal.json':
        validate_shared_action_core(ROOT, provider)
        if proposed.get('candidate_core_qualification'):
            return _prepare_candidate_core_augmentation(authoring, capture, proposed, canonical, member_ids, health_validation)
        if proposed.get('legacy_core_qualification'):
            return _prepare_legacy_fisa_reuse(authoring, capture, proposed, canonical, member_ids)
        return _prepare_source_review_reuse(authoring, capture, proposed, canonical, member_ids)
    if proposed.get('additional_action_outcome_source_ids'):
        raise ValueError('additional outcome witnesses require a source-review candidate')
    suffix = ':' + proposed['action_id'] + ':candidate-v1'
    meaning_ref = canonical['action_meaning_ref']
    if not meaning_ref.endswith(suffix) or not meaning_ref[:-len(suffix)]:
        raise ValueError('unsupported shared-core reuse meaning identity')
    subset = copy.deepcopy(authoring)
    subset['snapshot_id'] = meaning_ref[:-len(suffix)]
    subset['actions'] = [copy.deepcopy(proposed)]
    subset['blocked_episode_ids'] = []
    prepared = common.prepare(subset, capture, member_ids)
    if prepared[0]['actions'] != [canonical]:
        raise ValueError('shared-core reuse input or governed sources differ from canonical core')
    return copy.deepcopy(canonical), prepared[1]['action_mappings'][0], prepared[1]['episodes'][0]


def prepare(authoring, capture, member_ids):
    if authoring.get("domain_id") != "IMMIGRATION_BORDER":
        raise ValueError("Immigration candidate adapter cannot prepare another domain")
    health_validation = _HealthProviderValidation()
    action_constraints = _action_source_constraints(authoring)
    sources = {s["source_id"]: s for s in capture["sources"]}
    for proposed in authoring["actions"]:
        # Reject known incompatible ordinary bill stages before the common
        # adapter. This is not a full vote-time reconstruction: later corrected
        # EH witnesses still require explicit contemporaneous claim bindings.
        # Direct/nested replacement resolutions have their own clause guards.
        if _extended(proposed) or proposed.get("deemed_concurrence") or proposed.get("nested_concurrence"):
            continue
        version = sources[proposed["source_id"]]["text_version"]
        passage_stages = {"final_passage", "suspension_and_passage", "division_retention", "veto_override"}
        if ((version == "EAS" and proposed["stage"] in passage_stages)
                or (version == "EH" and proposed["stage"] in {"concurrence", "suspension_and_concurrence"})):
            raise ValueError("primary bill version differs from exact legislative stage")
    additions = [a for a in authoring["actions"] if _extended(a)]
    reuse_additions = [a for a in authoring["actions"] if "shared_core_reuse" in a]
    ordinary = copy.deepcopy(authoring)
    ordinary["actions"] = [a for a in ordinary["actions"] if not _extended(a) and "shared_core_reuse" not in a]
    ordinary_episodes = {a["episode_id"] for a in ordinary["actions"]}
    ordinary["blocked_episode_ids"] = [e for e in ordinary["blocked_episode_ids"] if e in ordinary_episodes]
    core, mapping, projections, inputs, result = common.prepare(ordinary, capture, member_ids)
    for proposed in reuse_additions:
        reused, row, episode = _prepare_reused_action(authoring, capture, proposed, member_ids, health_validation)
        core["actions"].append(reused)
        mapping["action_mappings"].append(row)
        existing = next((e for e in mapping["episodes"] if e["episode_id"] == episode["episode_id"]), None)
        if existing is None:
            mapping["episodes"].append(episode)
        else:
            existing["action_ids"].extend(episode["action_ids"])
    if not additions and not reuse_additions:
        if action_constraints:
            mapping["source_render_constraints"].extend(action_constraints)
            mapping["mapping_sha256"] = sealed_digest(mapping, "mapping_sha256")
            inputs = adapt_to_semantic_ir_input(ROOT, core, mapping, projections)
            result = run_editorial_pipeline(inputs)
        return core, mapping, projections, inputs, result
    sources = {s["source_id"]: s for s in capture["sources"]}
    for proposed in additions:
        aid = proposed["action_id"]
        _, congress, session, roll = aid.split(":")
        clerk = sources[f"clerk:{congress}:{session}:{roll}"]
        meta = clerk["metadata"]
        if (int(meta["congress"]), int(meta["session"][0]), int(meta["rollcall-num"])) != (int(congress), int(session), int(roll)):
            raise ValueError("Clerk source does not match exact action")
        if meta["legis-num"] != f"H RES {proposed['bill_number']}":
            raise ValueError("Clerk measure and proposed text differ")
        if meta["vote-question"] != "On Agreeing to the Resolution":
            raise ValueError("deemed concurrence differs from exact Clerk question")
        date = datetime.strptime(meta["action-date"], "%d-%b-%Y").date().isoformat()
        if date > authoring["interpretation_action_set_cutoff"]:
            raise ValueError("new raw action cannot extend declared interpretation cutoff")
        if "deemed_replacement_concurrence" in proposed:
            _bind_replacement_concurrence(proposed, sources, congress, clerk)
        else:
            _bind_concurrence(proposed, sources, congress, clerk)
        operative = [sources[sid] for sid in [proposed["source_id"], *proposed.get("additional_source_ids", [])]]
        by_id = {s["source_id"]: s for s in operative}
        if not proposed["compact_source_refs"] or not set(proposed["compact_source_refs"]) <= set(by_id):
            raise ValueError("compact meaning must reference its governed operative sources")
        for claim in proposed["claim_source_map"]:
            if claim["source_id"] not in by_id or claim["passage"] not in by_id[claim["source_id"]]["text"]:
                raise ValueError(f"claim passage absent from bound source: {aid}")
        source_ids = [identity(clerk), *[identity(s) for s in operative]]
        witness = proposed.get("deemed_replacement_concurrence", proposed.get("deemed_concurrence"))
        relationship = (f"H.Res.{proposed['bill_number']} directly deems concurrence in the Senate amendment "
                        f"for H.R.{witness['underlying_bill_number']}")
        if "deemed_replacement_concurrence" in proposed:
            relationship += f" with the whole House replacement in Rules Committee Print {congress}-{witness['rules_committee_print_number']}"
        relationship += "; distinct exact action within the underlying bill episode"
        action = {
            "action_id": aid, "exact_action_identity": aid,
            "chamber": "house", "congress": int(congress), "session": int(session), "roll": int(roll),
            "legislative_stage": "concurrence", "action_date": date,
            "exact_question": meta["vote-question"], "chamber_outcome": meta["vote-result"],
            "enactment_status": "not_inferred_from_house_outcome",
            "mechanism": proposed["short_description"], "mechanism_availability": "candidate_source_mapped",
            "candidate_exact_action_meaning": proposed["meaning"], "candidate_short_description": proposed["short_description"],
            "candidate_compact_description": proposed["compact_description"], "compact_source_refs": proposed["compact_source_refs"],
            "candidate_shared_limitations": proposed["limitations"], "choice_meanings": proposed["choice_meanings"],
            "claim_source_map": proposed["claim_source_map"], "action_meaning_ref": f"{authoring['snapshot_id']}:{aid}:candidate-v1",
            "governed_source_identities": source_ids, "governed_source_identity_sha256": digest(source_ids),
            "action_outcome_source_identities": [identity(clerk)], "operative_meaning_source_identities": [identity(s) for s in operative],
            "semantic_ir_source_ids": [s["source_id"] for s in source_ids],
            "package_component_boundary": {"boundary_type": "whole_measure", "parent_package_meaning_projected": False,
                "basis": proposed["limitations"], "governed_component_relationships": [relationship]},
            "source_contract_version": "shared_legislative_corpus_v1", "meaning_contract_version": "candidate-extension-v1",
        }
        action["action_core_sha256"] = digest(action)
        core["actions"].append(action)
        row = {"action_id": aid, "eligibility": {"decision": "proposed", "parent_context_used": False},
            "episode_id": proposed["episode_id"], "policy_family_refs": [], "policy_trait_refs": [],
            "structural_metadata": {"stage_order": int(session) * 10000 + int(roll)}}
        row["mapping_sha256"] = digest(row)
        mapping["action_mappings"].append(row)
        episode = next((e for e in mapping["episodes"] if e["episode_id"] == proposed["episode_id"]), None)
        if episode is None:
            episode = {"episode_id": proposed["episode_id"], "action_ids": [], "method_boundary_types": [], "policy_family_id": None}
            mapping["episodes"].append(episode)
        episode["action_ids"].append(aid)
    if len({a["action_id"] for a in core["actions"]}) != len(core["actions"]):
        raise ValueError("duplicate exact action in candidate inputs")
    core["actions"].sort(key=lambda a: (a["session"], a["roll"]))
    core["corpus_sha256"] = digest(core["actions"])
    mapping["action_mappings"].sort(key=lambda a: a["structural_metadata"]["stage_order"])
    for episode in mapping["episodes"]:
        episode["action_ids"].sort(key=lambda aid: tuple(map(int, aid.split(":")[2:])))
    mapping["episodes"].sort(key=lambda e: tuple(map(int, e["action_ids"][0].split(":")[2:])))
    blocked = [a for e in mapping["episodes"] if e["episode_id"] in authoring["blocked_episode_ids"] for a in e["action_ids"]]
    mapping["source_render_constraints"] = ([{"action_ids": blocked, "constraint_id": "candidate-episode-hold",
        "detail": authoring["blocked_reason"], "semantic_effect": "blocks_behavioral_propositions"}] if blocked else [])
    mapping["source_render_constraints"].extend(action_constraints)
    mapping["mapping_sha256"] = sealed_digest(mapping, "mapping_sha256")
    for projection in projections:
        rows = []
        names, parties = set(), set()
        for action in core["actions"]:
            source = sources[action["action_outcome_source_identities"][0]["source_id"]]
            official = source["member_records"].get(projection["member_id"])
            if official is None:
                raise ValueError(f"source does not contain member {projection['member_id']}: {action['action_id']}")
            status = {"Aye": "Yea", "No": "Nay"}.get(official["official_label"], official["official_label"])
            names.add(official["name"]); parties.add(official["party"])
            member_sources = copy.deepcopy(action["action_outcome_source_identities"])
            rows.append({"action_id": action["action_id"], "action_core_sha256": action["action_core_sha256"],
                "official_status": status, "service_status": "in_service", "evidence_status": "official_record_resolved",
                "exact_choice_effect": choice_effect(status), "member_action_source_identities": member_sources,
                "member_action_source_identity_sha256": digest(member_sources)})
        projection["actions"] = rows; projection["party"] = "/".join(sorted(parties))
        projection["context_metadata"]["display_name"] = "/".join(sorted(names))
        projection["projection_sha256"] = sealed_digest(projection, "projection_sha256")
    inputs = adapt_to_semantic_ir_input(ROOT, core, mapping, projections)
    result = run_editorial_pipeline(inputs)
    return core, mapping, projections, inputs, result

def _contract_proof(authoring, capture, member_ids):
    """Actual replay plus explicitly controlled, non-authorizing updates."""
    before = prepare(authoring, capture, member_ids)
    core, mapping, projections, inputs, result = before
    rendered = readable_candidates(authoring, core, projections, result)
    after = prepare(authoring, capture, member_ids)
    assert digest(result.compiled_ir) == digest(after[-1].compiled_ir)
    assert digest(rendered) == digest(readable_candidates(authoring, after[0], after[2], after[-1]))
    by_member = {p["member_id"]: {a["action_id"]: a for a in p["actions"]} for p in projections}
    reuse = []
    for action in core["actions"]:
        choices = []
        for mid, rows in by_member.items():
            row = rows[action["action_id"]]
            assert row["action_core_sha256"] == action["action_core_sha256"]
            choices.append({"member_id": mid, "status": row["official_status"],
                "effect": row["exact_choice_effect"], "selected_meaning": action["choice_meanings"].get(row["official_status"]),
                "source_id": row["member_action_source_identities"][0]["source_id"]})
        reuse.append({"action_id": action["action_id"], "shared_sha256": action["action_core_sha256"], "choices": choices})
    raw = copy.deepcopy(capture)
    extra = {"source_id": "synthetic:later-raw-record", "text": "Controlled raw-ledger addition, not historical or interpreted."}
    extra["governed_bytes_sha256"] = digest(extra); raw["sources"].append(extra)
    raw_result = prepare(authoring, raw, member_ids)
    assert core == raw_result[0] and result.compiled_ir == raw_result[-1].compiled_ir
    eligible = result.compiled_ir["members"][0]["action_accounting"]["behavioral_proposition_action_ids"]
    if not eligible:
        raise ValueError("update proof requires an independently compiled behavioral finding")
    differing = [r["action_id"] for r in reuse if r["action_id"] in eligible and
                 {c["status"] for c in r["choices"]} == {"Yea", "Nay"}]
    target = differing[0] if differing else eligible[0]
    correction = copy.deepcopy(core)
    corrected = next(a for a in correction["actions"] if a["action_id"] == target)
    corrected["candidate_shared_limitations"].append("CONTROLLED TEST: shared qualification correction; no real acceptance or publication.")
    corrected["action_core_sha256"] = sealed_digest(corrected, "action_core_sha256")
    correction["corpus_sha256"] = digest(correction["actions"])
    impact = candidate_update_impact(core, correction, projections, result.compiled_ir)
    rejected = []
    for projection in projections:
        try:
            validate_member_projection(ROOT, projection, correction)
        except SharedCorpusValidationError:
            rejected.append(projection["member_id"])
    assert len(rejected) == len(projections)
    # Explicitly admitted candidate input differs from an ignored raw record.
    prior = copy.deepcopy(authoring)
    prior["actions"] = [a for a in prior["actions"] if a["action_id"] != target]
    prior_result = prepare(prior, capture, member_ids)
    assert prior_result[-1].compiled_ir != result.compiled_ir
    return {
        "authority": "candidate proof only; no acceptance, historical authorized update or publication claimed",
        "rule_files_sha256": {name: digest((ROOT / name).read_text(encoding="utf-8")) for name in [
            "scripts/prepare_shared_domain_candidate.py", "backend/app/semantic_ir/shared_corpus.py",
            "backend/app/semantic_ir/compiler.py", "backend/app/semantic_ir/pipeline.py", "backend/app/semantic_ir/adapters.py",
            "backend/app/semantic_ir/validation.py", "docs/semantic_ir/shared_legislative_corpus_v1.schema.json"]},
        "input_sha256": digest(authoring), "source_capture_sha256": digest(capture),
        "core_sha256": core["corpus_sha256"], "compiled_sha256": digest(result.compiled_ir),
        "readable_sha256": digest(rendered), "identical_replay": True,
        "real_member_reuse": reuse,
        "differing_real_choices_exercised": bool(differing),
        "controlled_raw_update": {"interpretation_unchanged": True, "cutoff_unchanged": authoring["interpretation_action_set_cutoff"]},
        "controlled_new_interpretation_input": {"action_id": target, "requires_explicit_authoring_change": True, "acceptance_conferred": False},
        "controlled_shared_correction": {"impact": impact, "stale_projections_rejected": rejected, "historical_core_unchanged": True},
    }


def reproducibility_proof(authoring, capture, member_ids):
    proof = _contract_proof(authoring, capture, member_ids)
    proof["rule_files_sha256"]["scripts/prepare_immigration_shared_candidate.py"] = digest(Path(__file__).read_text(encoding="utf-8"))
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--member", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review-packet", type=Path)
    args = parser.parse_args()
    authoring = json.loads((args.input / "authoring.json").read_text(encoding="utf-8"))
    capture = json.loads((args.input / "sources.json").read_text(encoding="utf-8"))
    common.validate_universe_proposal(json.loads((args.input / "universe_proposal.json").read_text(encoding="utf-8")), authoring,
        capture, json.loads((args.input / "membership_review.json").read_text(encoding="utf-8")))
    core, mapping, projections, inputs, result = prepare(authoring, capture, args.member)
    args.output.mkdir(parents=True, exist_ok=True)
    values = {"shared_action_core": core, "shared_issue_mapping": mapping, "member_projections": projections,
        "compiler_input": inputs, "compiled_ir": result.compiled_ir,
        "readable_candidates": readable_candidates(authoring, core, projections, result),
        "reproducibility_proof": reproducibility_proof(authoring, capture, args.member)}
    for name, value in values.items():write_json(args.output / f"{name}.json", value)
    if args.review_packet:
        text = args.review_packet.read_text(encoding="utf-8")
        start, end = "<!-- GENERATED CANDIDATE START -->", "<!-- GENERATED CANDIDATE END -->"
        if text.count(start) != 1 or text.count(end) != 1:raise ValueError("review packet requires one generated candidate region")
        before, rest = text.split(start); _, after = rest.split(end)
        args.review_packet.write_text(before + start + "\n" + review_text(authoring, core, projections, result, capture) + end + after, encoding="utf-8")
    print(json.dumps({"review_state": CANDIDATE, "validation": result.validation,
        "core_sha256": core["corpus_sha256"], "compiled_sha256": digest(result.compiled_ir)}))

if __name__ == "__main__":main()
