"""Portable snapshot contract; no browser, database or installed frontend needed."""
import json
from contextlib import contextmanager
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from uuid import uuid4

from scripts.check_representative_journey_preview import (
    HTML_SHA256, PACKAGE, PreviewError, export_snapshot, sha256, verify_snapshot,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_FILES = ('.gitattributes', 'README.md', 'manifest.json', 'browser-review.json', 'preview.html')


@contextmanager
def scratch_directory():
    # Use the repository's test scratch convention and inherited permissions;
    # Windows system-temp directories may be inaccessible to the test process.
    base = (ROOT/'backend/.pytest_tmp').resolve()
    base.mkdir(parents=True, exist_ok=True)
    scratch = base / ('representative-journey-' + uuid4().hex)
    scratch.mkdir()
    try:
        yield scratch
    finally:
        # Delete only the exact newly created child of the intended scratch root.
        if scratch.is_symlink() or scratch.resolve().parent != base:
            raise RuntimeError('Unexpected test cleanup target')
        shutil.rmtree(scratch)


def copy_package(destination):
    destination.mkdir(parents=True)
    for name in PACKAGE_FILES:
        shutil.copyfile(PACKAGE/name, destination/name)
    return destination


class RepresentativeJourneySnapshotTests(unittest.TestCase):
    def test_check_is_read_only_and_binds_reviewed_content(self):
        before = {name: (PACKAGE/name).read_bytes() for name in PACKAGE_FILES}
        report, files = verify_snapshot()
        self.assertEqual(report['html_sha256'], HTML_SHA256)
        self.assertEqual(report['member_case_bindings'], 8)
        self.assertEqual(report['existing_browser_journeys'], 24)
        self.assertEqual(files['preview.html'], before['preview.html'])
        self.assertEqual(before, {name: (PACKAGE/name).read_bytes() for name in PACKAGE_FILES})

    def test_exports_are_byte_identical_and_downloads_are_real_json(self):
        with scratch_directory() as folder:
            first, second = Path(folder)/'first', Path(folder)/'second'
            self.assertEqual(export_snapshot(PACKAGE, first), export_snapshot(PACKAGE, second))
            self.assertEqual({p.name for p in first.iterdir()}, {
                'preview.html', 'four-choice-data.json', 'four-choice-sources.json', 'four-choice-provenance.json'})
            for path in first.iterdir():
                self.assertEqual(path.read_bytes(), (second/path.name).read_bytes())
            self.assertEqual(sha256((first/'preview.html').read_bytes()), HTML_SHA256)
            data = json.loads((first/'four-choice-data.json').read_bytes())
            museum = next(c for c in data['choices'] if c['slug'] == 'hr1329')
            massie = next(m for m in museum['evidence']['members'] if m['member_id'] == 'M001184')
            self.assertEqual((massie['raw_label'], massie['status']), ('Not Voting', 'Not Voting'))

    def test_corrupt_html_fails_before_creating_export(self):
        with scratch_directory() as folder:
            package = copy_package(Path(folder)/'package')
            raw = (package/'preview.html').read_bytes()
            # Same-length content change; size validation alone cannot catch it.
            self.assertIn(b'Valerie Foushee', raw)
            (package/'preview.html').write_bytes(raw.replace(b'Valerie Foushee', b'Valerie Foushee'.upper(), 1))
            destination = Path(folder)/'export'
            with self.assertRaisesRegex(PreviewError, 'Reviewed HTML bytes changed'):
                export_snapshot(package, destination)
            self.assertFalse(destination.exists())

    def test_manifest_cannot_reclassify_the_member_record(self):
        with scratch_directory() as folder:
            package = copy_package(Path(folder)/'package')
            manifest = json.loads((package/'manifest.json').read_bytes())
            museum = next(c for c in manifest['cases'] if c['slug'] == 'hr1329')
            next(m for m in museum['members'] if m['member_id'] == 'M001184')['status'] = 'Nay'
            (package/'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            with self.assertRaisesRegex(PreviewError, 'action/member manifest bindings'):
                verify_snapshot(package)

    def test_download_hash_and_review_receipt_cannot_drift(self):
        for kind in ('download', 'receipt'):
            with self.subTest(kind=kind), scratch_directory() as folder:
                package = copy_package(Path(folder)/'package')
                if kind == 'download':
                    manifest = json.loads((package/'manifest.json').read_bytes())
                    manifest['downloads']['four-choice-sources.json'] = '0' * 64
                    (package/'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
                    message = 'Embedded download hash mismatch'
                else:
                    (package/'browser-review.json').write_bytes((package/'browser-review.json').read_bytes() + b' ')
                    message = 'Browser receipt bytes changed'
                with self.assertRaisesRegex(PreviewError, message):
                    verify_snapshot(package)

    def test_export_never_overwrites_an_existing_destination(self):
        with scratch_directory() as folder:
            destination = Path(folder)/'existing'
            destination.mkdir()
            (destination/'preview.html').write_bytes(b'user-owned content')
            with self.assertRaises(FileExistsError):
                export_snapshot(PACKAGE, destination)
            self.assertEqual((destination/'preview.html').read_bytes(), b'user-owned content')
            self.assertEqual(len(list(destination.iterdir())), 1)

    def test_isolated_copy_without_repository_history_or_dependencies(self):
        with scratch_directory() as folder:
            checkout = Path(folder)/'clean copy with spaces'
            package = copy_package(checkout/'frontend/local-preview/representative-journey')
            scripts = checkout/'scripts'
            scripts.mkdir()
            script = scripts/'check_representative_journey_preview.py'
            shutil.copyfile(ROOT/'scripts'/script.name, script)
            # Only these six files exist: no .tmp, other repo files, node_modules,
            # historical builders, original review directory or Python imports.
            self.assertEqual(len([p for p in checkout.rglob('*') if p.is_file()]), 6)
            unrelated = Path(folder)/'unrelated working directory'
            unrelated.mkdir()
            export = Path(folder)/'portable export'
            result = subprocess.run([sys.executable, '-I', str(script), '--export-dir', str(export)],
                                    cwd=unrelated, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['html_sha256'], HTML_SHA256)
            self.assertEqual((export/'preview.html').read_bytes(), (PACKAGE/'preview.html').read_bytes())
            # Verification must still fail closed with Python assertions disabled.
            (package/'preview.html').write_bytes(b'corrupted')
            rejected = subprocess.run([sys.executable, '-I', '-O', str(script)], cwd=unrelated,
                                      capture_output=True, text=True, timeout=30)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn('Preview verification failed', rejected.stderr)


if __name__ == '__main__':
    unittest.main()
