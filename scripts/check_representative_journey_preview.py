"""Verify/export the immutable local snapshot; never generate editorial meaning."""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

PACKAGE = Path(__file__).resolve().parents[1] / 'frontend/local-preview/representative-journey'
HTML_SHA256 = 'afb47ec78a48ec6b8a9c1aa9ac6fed7e7130a335211cdf512423965321cb1de3'
REVIEW_SHA256 = 'cf438fdd483538c4c7f7ae00ac255eb6c82cdf49551d4f0e7b3420104d57bc65'
DOWNLOADS = ('four-choice-data.json', 'four-choice-sources.json', 'four-choice-provenance.json')
SLUGS = ('hr859', 'hr1329', 'hunt-a7', 'hr164')
MEMBERS = ('F000477', 'M001184')


class PreviewError(ValueError):
    """The package does not satisfy the reviewed snapshot contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PreviewError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(raw: bytes) -> dict:
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique_pairs)


class Snapshot(HTMLParser):
    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.pages = {}
        self.route = None
        self.links = []
        self.ids = []
        self.downloads = {}
        self.csp = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'section':
            route = attrs['data-page']
            require(route not in self.pages, 'Duplicate preview route')
            self.route = route
            self.pages[route] = {'links': [], 'text': [], 'headings': 0}
        if tag == 'h1' and self.route:
            require('data-heading' in attrs and attrs.get('tabindex') == '-1', 'Missing focusable heading')
            self.pages[self.route]['headings'] += 1
        if tag == 'meta' and attrs.get('http-equiv') == 'Content-Security-Policy':
            require(self.csp is None, 'Duplicate CSP')
            self.csp = attrs['content']
        if tag == 'a':
            href = attrs['href']
            self.links.append(href)
            if self.route:
                self.pages[self.route]['links'].append(href)
            if 'download' in attrs:
                name = attrs['download']
                require(name in DOWNLOADS and name not in self.downloads, 'Unexpected or duplicate download')
                prefix = 'data:application/json;base64,'
                require(href.startswith(prefix), 'Download must be embedded JSON')
                self.downloads[name] = base64.b64decode(href[len(prefix):], validate=True)

    def handle_endtag(self, tag):
        if tag == 'section':
            self.route = None

    def handle_data(self, text):
        if self.route:
            self.pages[self.route]['text'].append(text)


def verify_snapshot(package: Path = PACKAGE) -> tuple[dict, dict[str, bytes]]:
    """Read only package-local files; return verified bytes ready for export."""
    manifest = read_json((package / 'manifest.json').read_bytes())
    raw = (package / 'preview.html').read_bytes()
    require(manifest['schema_version'] == 1, 'Unsupported snapshot manifest')
    require(manifest['artifact'] == {'file': 'preview.html', 'sha256': HTML_SHA256, 'bytes': len(raw)},
            'Manifest does not identify the reviewed HTML')
    require(sha256(raw) == HTML_SHA256, 'Reviewed HTML bytes changed; review a replacement snapshot')
    text = raw.decode('utf-8')
    parsed = Snapshot(text)
    require(set(parsed.downloads) == set(DOWNLOADS) == set(manifest['downloads']), 'Download inventory mismatch')
    for name, payload in parsed.downloads.items():
        require(sha256(payload) == manifest['downloads'][name], 'Embedded download hash mismatch: ' + name)
    data, sources, proof = (read_json(parsed.downloads[name]) for name in DOWNLOADS)
    require(proof['data_sha256'] == manifest['downloads'][DOWNLOADS[0]], 'Provenance data binding mismatch')
    require(proof['sources_sha256'] == manifest['downloads'][DOWNLOADS[1]], 'Provenance source binding mismatch')
    require(tuple(c['slug'] for c in data['choices']) == SLUGS, 'Unexpected case set')
    cases = [{'slug': c['slug'], 'action': c['action'], 'exact_version': c['evidence']['exact_version'],
              'members': c['evidence']['members']} for c in data['choices']]
    require(cases == manifest['cases'], 'Exact action/member manifest bindings changed')
    expected_proof = [{'action_id': c['action']['action_id'], 'action_core_sha256': c['action']['action_core_sha256'],
                       'exact_version': c['evidence']['exact_version']} for c in data['choices']]
    require(proof['exact_action_bindings'] == expected_proof, 'Evidence action-core binding mismatch')
    require(len(sources['action_sources']) == 4, 'Unexpected source action count')
    source_actions = {x['action_id']: x['sources'] for x in sources['action_sources']}
    require(set(source_actions) == {c['action']['action_id'] for c in data['choices']}, 'Source actions mismatch')
    expected_routes = {'representatives', 'state/analysis-unavailable', 'state/evidence-unavailable', 'unavailable'}
    expected_status = {'F000477': ('Yea', 'Nay', 'Nay', 'Yea'), 'M001184': ('Nay', 'Not Voting', 'Nay', 'Nay')}
    expected_raw = {'F000477': ('Yea', 'Nay', 'No', 'Yea'), 'M001184': ('Nay', 'Not Voting', 'No', 'Nay')}
    all_sources = []
    for index, case in enumerate(data['choices']):
        require(tuple(m['member_id'] for m in case['evidence']['members']) == MEMBERS, 'Member set mismatch')
        case_sources = source_actions[case['action']['action_id']]
        require(len(case_sources) == (8, 12, 16, 5)[index], 'Source count mismatch')
        all_sources.extend(case_sources)
        for member in case['evidence']['members']:
            mid = member['member_id']
            require(member['status'] == expected_status[mid][index] and member['raw_label'] == expected_raw[mid][index],
                    'Recorded member status mismatch')
            home = 'representative/' + mid
            choice = home + '/choice/' + case['slug']
            evidence = home + '/evidence/' + case['slug']
            expected_routes.update((home, choice, evidence))
            for route in (home, choice, evidence):
                require(route in parsed.pages, 'Missing journey route: ' + route)
                require(case['presentation']['member_actions_by_id'][mid] in parsed.pages[route]['text'],
                        'Displayed action does not match embedded data')
            for route in (choice, evidence):
                urls = [url for url in parsed.pages[route]['links'] if url.startswith('https:')]
                require(urls == [s['url'] for s in case_sources], 'Source receipts differ from embedded data')
            require('#' + choice in parsed.pages[home]['links'] and '#' + evidence in parsed.pages[choice]['links']
                    and '#' + choice in parsed.pages[evidence]['links'] and '#' + home in parsed.pages[choice]['links'],
                    'Journey return/evidence links incomplete')
    require(set(parsed.pages) == expected_routes and len(expected_routes) == 22, 'Route set mismatch')
    require(all(p['headings'] == 1 for p in parsed.pages.values()), 'Missing page heading')
    require(len(parsed.ids) == len(set(parsed.ids)), 'Duplicate HTML IDs')
    for href in parsed.links:
        if href.startswith('#'):
            require(href[1:] in expected_routes or href[1:] in parsed.ids, 'Unresolved local link: ' + href)
    expected_links = Counter({url: count * 4 for url, count in Counter(s['url'] for s in all_sources).items()})
    require(Counter(x for x in parsed.links if x.startswith('https:')) == expected_links, 'Unexpected source links')
    require(parsed.csp is not None and "default-src 'none'" in parsed.csp, 'Missing restrictive CSP')
    for tag in ('script', 'style'):
        chunks = re.findall(r'<' + tag + r'>(.*?)</' + tag + '>', text, re.S)
        require(len(chunks) == 1, 'Unexpected inline asset count')
        token = base64.b64encode(hashlib.sha256(chunks[0].encode()).digest()).decode()
        require(tag + "-src 'sha256-" + token + "'" in parsed.csp, 'Inline CSP hash mismatch')
    require(not re.search(r'<(?:script|link)[^>]+(?:src|href)=', text), 'External runtime dependency')

    review_raw = (package / 'browser-review.json').read_bytes()
    require(manifest['browser_review']['file'] == 'browser-review.json' and
            manifest['browser_review']['sha256'] == REVIEW_SHA256 == sha256(review_raw), 'Browser receipt bytes changed')
    review = read_json(review_raw)
    require(review['sha256'] == HTML_SHA256 and not review['errors'] and not review['overflow'] and not review.get('failure'),
            'Browser receipt does not attest to this snapshot')
    expected_views = {(width, mid, slug) for width in (1440, 390, 320) for mid in MEMBERS for slug in SLUGS}
    require(len(review['views']) == 24 and {(v['width'], v['member'], v['slug']) for v in review['views']} == expected_views,
            'Browser receipt coverage mismatch')
    by_slug = {c['slug']: c for c in data['choices']}
    for view in review['views']:
        require(view['action'] == by_slug[view['slug']]['presentation']['member_actions_by_id'][view['member']],
                'Reviewed action differs from embedded data')
    attributes = (package / '.gitattributes').read_text(encoding='utf-8').splitlines()
    require('preview.html -text' in attributes and 'browser-review.json -text' in attributes,
            'Exact-byte files lack checkout protection')
    require(manifest['provenance']['canonical_or_editorial_acceptance'] is False, 'Snapshot cannot confer editorial acceptance')
    report = {'html_sha256': HTML_SHA256, 'html_bytes': len(raw), 'member_case_bindings': 8,
              'sources': len(all_sources), 'routes': 22, 'downloads': 3,
              'existing_browser_journeys': 24, 'browser_review_reused': True, 'check': 'pass'}
    return report, {'preview.html': raw, **parsed.downloads}


def export_snapshot(package: Path, destination: Path) -> dict:
    report, files = verify_snapshot(package)
    # No overwrite or parent creation. Validate before any output mutation.
    destination.mkdir(exist_ok=False)
    for name, raw in files.items():
        with (destination / name).open('xb') as stream:
            stream.write(raw)
    return {**report, 'exported_files': {name: sha256(raw) for name, raw in files.items()}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export-dir', type=Path, help='Write verified HTML and JSON downloads into a new directory')
    args = parser.parse_args()
    try:
        report = export_snapshot(PACKAGE, args.export_dir) if args.export_dir else verify_snapshot()[0]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('Preview verification failed: ' + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
