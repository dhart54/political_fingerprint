"""Read-only, fixture-specific research diagnostic; never a candidate input."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess

SOURCE_REF = '196c68a8d431c4a3f789e47a5536be2a97a58425'
ROOT = 'docs/review_packets/immigration_research_support_20261014/'
OLD = re.compile(r'(?<![\d,])\d{1,3}(?:,\s*\d{3})+(?![\d,])')
RUN = re.compile(r'\d[\d, \t]*')
CANONICAL = re.compile(r'[1-9]\d{0,2}(?:,\d{3})+')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(repo: str, ref: str, path: str) -> bytes:
    spec = ':' + path if ref == 'index' else ref + ':' + path
    return subprocess.check_output(['git', '-C', repo, 'show', spec])


def load_source(repo: str) -> tuple[list, list, dict]:
    base = ROOT + 'batch4/'
    receipt = json.loads(git_blob(repo, SOURCE_REF, base + 'delivered_blobs.json'))
    blobs = {}
    for name in ['record_selected_pages.json', 'roll_2_44_table_evidence.json']:
        raw = git_blob(repo, SOURCE_REF, base + name)
        if digest(raw) != receipt['files'][name]['sha256']:
            raise ValueError('Upstream Git blob identity mismatch: ' + name)
        blobs[name] = json.loads(raw)
    pages = blobs['record_selected_pages.json']['pages']
    return pages, blobs['roll_2_44_table_evidence.json']['account_locators'], receipt


def numeric_spans(literal: str) -> list[dict]:
    """Capture maximal numeric runs; do not accept a suffix of a split run."""
    result = []
    for match in RUN.finditer(literal):
        token = match.group().rstrip(' \t')
        # A number followed only by punctuation (e.g. "District 1, ME")
        # supplies no digit group after a comma and is not a currency span.
        if re.search(r',\s*\d', token) is None:
            continue
        end = match.start() + len(token)
        folded = re.sub(r'[ \t]', '', token)
        bounded = (match.start() == 0 or literal[match.start() - 1].isspace())
        bounded = bounded and (end == len(literal) or literal[end].isspace())
        valid = bounded and CANONICAL.fullmatch(folded) is not None
        result.append(dict(start=match.start(), end=end, literal=token,
                           provisional_value=int(folded.replace(',', '')) if valid else None,
                           valid_numeric_run=valid))
    return result


def split_rows(pages: list, locators: list) -> list[dict]:
    result = []
    seen_pages = set()
    for page in pages:
        n, text = page['pdf_page'], page['text']
        if n in seen_pages:
            raise ValueError('Duplicate page')
        seen_pages.add(n)
        if digest(text.encode()) != page['text_utf8_sha256']:
            raise ValueError('Literal page digest mismatch')
        if not 247 <= n <= 273:
            continue
        starts = list(re.finditer(r'^(?:DOL|HHS|ED) ', text, re.M))
        for index, start in enumerate(starts):
            end = starts[index + 1].start() if index + 1 < len(starts) else text.index('VerDate', start.start())
            literal = text[start.start():end]
            branches = [g['branch'] for g in locators if literal.startswith(g['literal_account_prefix'])]
            if len(branches) != 1:
                raise ValueError('Unknown or ambiguous account prefix')
            legacy = list(OLD.finditer(literal))
            legacy_value = int(re.sub(r'[,\s]', '', legacy[0].group())) if len(legacy) == 1 else None
            spans = numeric_spans(literal)
            provisional = spans[0]['provisional_value'] if len(spans) == 1 else None
            needs_review = provisional is None or legacy_value is None or provisional != legacy_value
            result.append(dict(row_id=f'{n}:{start.start()}', pdf_page=n,
                               printed_page=page['printed_page'], row_on_page=index + 1,
                               start=start.start(), end=end, branch=branches[0], literal=literal,
                               literal_utf8_sha256=digest(literal.encode()),
                               legacy_tokens=[m.group() for m in legacy], legacy_value=legacy_value,
                               numeric_spans=spans, provisional_value=provisional,
                               needs_review=needs_review))
    return result


def make_report(rows: list, reviews: list) -> dict:
    by_id = {row['row_id']: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError('Duplicate row identity')
    checked = {}
    for review in reviews:
        rid = review['row_id']
        if rid in checked or rid not in by_id:
            raise ValueError('Duplicate or unknown visual row')
        row = by_id[rid]
        if not row['needs_review']:
            raise ValueError('Visual record outside targeted discrepancies')
        for field in ['pdf_page', 'printed_page', 'row_on_page', 'start', 'end',
                      'branch', 'literal', 'literal_utf8_sha256']:
            if review[field] != row[field]:
                raise ValueError('Visual binding mismatch: ' + field)
        if review['column_index'] != 4 or review['column_label'] != 'Amount ($)':
            raise ValueError('Wrong visual column')
        if not review.get('image_path') or not re.fullmatch('[a-f0-9]{64}', review.get('image_sha256', '')):
            raise ValueError('Missing source view identity')
        value = review['visual_amount_dollars']
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError('Invalid separate transcription')
        checked[rid] = review
    old, revised, changes, counts = Counter(), Counter(), Counter(), Counter()
    unresolved, target_rows = [], []
    for row in rows:
        branch = row['branch']
        counts[branch] += 1
        old[branch] += row['legacy_value'] or 0
        review = checked.get(row['row_id'])
        status = 'mechanical_agreement_not_visually_certified'
        value = row['legacy_value']
        if row['needs_review']:
            status, value = 'requires_visual_review', None
            if review:
                if review['visual_amount_dollars'] == row['provisional_value']:
                    status, value = 'target_field_visually_checked', review['visual_amount_dollars']
                else:
                    status = 'visual_text_disagreement_unresolved'
            if value is None:
                unresolved.append(row['row_id'])
            else:
                changes[branch] += value - (row['legacy_value'] or 0)
            target_rows.append(dict(copy.deepcopy(row), status=status,
                                    separate_visual_transcription=copy.deepcopy(review)))
        if value is not None:
            revised[branch] += value
    return dict(source_ref=SOURCE_REF, mechanical_row_count=len(rows), account_row_counts=dict(counts),
                legacy_missing_amounts=sum(r['legacy_value'] is None for r in rows),
                legacy_partial_amounts=sum(r['legacy_value'] is not None and r['needs_review'] for r in rows),
                target_rows=target_rows, unresolved_target_rows=unresolved,
                legacy_account_sums=dict(old), revised_partial_or_complete_sums=dict(revised),
                delta_from_separate_visual_transcriptions=dict(changes),
                all_rows_visually_certified=False,
                arithmetic_scope=f"{len(rows) - len(target_rows)} unchanged mechanically agreeing fields plus up to {len(target_rows)} separately transcribed target fields; unresolved targets omitted and listed, never balanced to a desired total",
                source_text_modified=False, candidate_or_publication_authority=False)


def verify_review_views(repo: str, artifact_ref: str, reviews: list) -> None:
    for review in reviews:
        path, ref = review['image_path'], review['image_ref']
        if ref not in [SOURCE_REF, 'delivery']:
            raise ValueError('Unexpected source-view ref')
        permitted = ROOT + ('batch4/' if ref == SOURCE_REF else 'currency44/')
        if not path.startswith(permitted) or '..' in path:
            raise ValueError('Source view outside permitted packet')
        actual = git_blob(repo, SOURCE_REF if ref == SOURCE_REF else artifact_ref, path)
        if digest(actual) != review['image_sha256']:
            raise ValueError('Source view digest mismatch')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='.')
    parser.add_argument('--artifact-ref', default='HEAD')
    parser.add_argument('--without-reviews', action='store_true')
    args = parser.parse_args()
    pages, locators, _ = load_source(args.repo)
    reviews = [] if args.without_reviews else json.loads(git_blob(
        args.repo, args.artifact_ref, ROOT + 'currency44/reviewed_rows.json'))['rows']
    verify_review_views(args.repo, args.artifact_ref, reviews)
    print(json.dumps(make_report(split_rows(pages, locators), reviews), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
