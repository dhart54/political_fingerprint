import re
import subprocess
import unittest
from pathlib import Path

from backend.tests.ci_workflow_preservation import APPROVED_MAIN, assert_prior_ci_preserved


BEFORE = '''name: Backend tests

on:
  pull_request:
    paths:
      - "backend/**"
      - ".github/workflows/backend-tests.yml"
  push:
    branches:
      - main
    paths:
      - "backend/**"
      - ".github/workflows/backend-tests.yml"

jobs:
  original-job:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha || github.sha }}
      - run: python -m pytest -q backend/tests/test_original.py
'''
ANCHOR = '      - ".github/workflows/backend-tests.yml"'
ADDITION = '\n      - ".gitattributes"'
APPROVED = BEFORE.replace(ANCHOR, ANCHOR + ADDITION)


class CIWorkflowPreservationTests(unittest.TestCase):
    def test_actual_workflow_keeps_attribute_identity_guard_in_both_event_filters(self):
        header = (Path(__file__).resolve().parents[2] / '.github/workflows/backend-tests.yml').read_text(encoding='utf8').split('\njobs:\n', 1)[0]
        for event in ['pull_request', 'push']:
            block = re.search(r'(?ms)^  ' + event + r':\n(.*?)(?=^  [a-z_]+:\n|\Z)', header)
            self.assertIsNotNone(block)
            self.assertEqual(block.group(1).splitlines().count('      - ".gitattributes"'), 1)

    def test_unchanged_header_or_exact_both_filter_additions_preserve_prior_jobs(self):
        assert_prior_ci_preserved(BEFORE, BEFORE)
        assert_prior_ci_preserved(BEFORE, APPROVED)
        assert_prior_ci_preserved(APPROVED, APPROVED)
        assert_prior_ci_preserved(BEFORE, APPROVED + '\n  later-job:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo later\n')

    def test_partial_or_unrelated_trigger_changes_are_rejected(self):
        mutations = [BEFORE.replace(ANCHOR, ANCHOR + ADDITION, 1),
                     APPROVED.replace('"backend/**"', '"frontend/**"', 1),
                     APPROVED.replace('      - main', '      - other', 1),
                     APPROVED.replace('  pull_request:', '  pull_request_target:', 1),
                     APPROVED.replace(ADDITION, ADDITION + '\n      - "unreviewed/**"', 1),
                     APPROVED.replace('    paths:', '    unreviewed:', 1),
                     APPROVED.replace('name: Backend tests', 'name: Other')]
        for index, changed in enumerate(mutations):
            with self.subTest(index=index), self.assertRaisesRegex(AssertionError, 'event/header'):
                assert_prior_ci_preserved(BEFORE, changed)
        with self.assertRaisesRegex(AssertionError, 'event/header'):
            assert_prior_ci_preserved(APPROVED, BEFORE)

    def test_prior_job_runner_permission_checkout_and_test_mutations_are_rejected(self):
        for old, new in [('original-job:', 'renamed-job:'), ('ubuntu-latest', 'windows-latest'),
                         ('contents: read', 'contents: write'), ('actions/checkout@v4', 'actions/checkout@v3'),
                         ('pull_request.head.sha || github.sha', 'pull_request.base.sha || github.sha'),
                         ('test_original.py', 'test_other.py')]:
            with self.subTest(old=old), self.assertRaisesRegex(AssertionError, 'Prior CI job'):
                assert_prior_ci_preserved(BEFORE, APPROVED.replace(old, new))
        with self.assertRaisesRegex(AssertionError, 'Prior CI job'):
            assert_prior_ci_preserved(BEFORE, APPROVED + '      - run: echo unreviewed-extra-step\n')

    def test_a_self_declared_accepted_baseline_cannot_allow_unreviewed_job_changes(self):
        changed = APPROVED.replace('contents: read', 'contents: write')
        with self.assertRaisesRegex(AssertionError, 'baseline identity'):
            assert_prior_ci_preserved(BEFORE, changed, accepted_baseline=changed)

    def test_authenticated_main_baseline_cannot_excuse_a_new_job_change(self):
        accepted = subprocess.check_output(['git', 'show', APPROVED_MAIN + ':.github/workflows/backend-tests.yml'],
                                           cwd=Path(__file__).resolve().parents[2]).decode()
        permitted = accepted.replace(ANCHOR, ANCHOR + ADDITION)
        assert_prior_ci_preserved(accepted, permitted, accepted_baseline=accepted)
        changed = permitted.replace('pg_isready', 'unreviewed_pg_isready', 1)
        self.assertNotEqual(changed, permitted)
        with self.assertRaisesRegex(AssertionError, 'Prior CI job'):
            assert_prior_ci_preserved(accepted, changed, accepted_baseline=accepted)

    def _restore_repair_workflows(self):
        root = Path(__file__).resolve().parents[2]
        before = subprocess.check_output([
            'git', 'show', '65575bf9a045f23c99f07a0750e6560fbd937655:.github/workflows/backend-tests.yml',
        ], cwd=root).decode().replace('\r\n', '\n')
        # Self-contained expected repair; do not depend on a PR-only commit
        # remaining reachable after squash/rebase merge and branch deletion.
        match = re.search(r'(?ms)^  publication-activation-postgres:\n.*?(?=^  [a-zA-Z0-9_-]+:\n|\Z)', before)
        job = match.group().replace('runs-on: ubuntu-latest', 'runs-on: ubuntu-24.04', 1)
        job = job.replace('    env:\n      DATABASE_URL:',
                          '    env:\n      POSTGRES_BIN: /usr/lib/postgresql/16/bin\n      DATABASE_URL:', 1)
        preflight = (
            '      - name: Verify matching PostgreSQL 16 clients and test server\n'
            '        shell: bash\n'
            '        run: |\n'
            '          set -euo pipefail\n'
            '          # Keep host backup/restore tools aligned with the disposable service.\n'
            '          for tool in pg_dump pg_restore psql createdb; do\n'
            '            test -x "$POSTGRES_BIN/$tool"\n'
            '            "$POSTGRES_BIN/$tool" --version | grep -E \'PostgreSQL\\) 16\\.\'\n'
            '          done\n'
            '          echo "$POSTGRES_BIN" >> "$GITHUB_PATH"\n'
            '          server_version=$("$POSTGRES_BIN/psql" -h 127.0.0.1 -U postgres -d postgres -Atc \'SHOW server_version_num\')\n'
            '          echo "Disposable PostgreSQL server_version_num=$server_version"\n'
            '          test "$server_version" -ge 160000\n'
            '          test "$server_version" -lt 170000\n'
            '\n'
        )
        job = job.replace('      - name: Install backend dependencies\n',
                          preflight + '      - name: Install backend dependencies\n', 1)
        return before, before[:match.start()] + job + before[match.end():]

    def test_exact_postgres16_repair_preserves_historical_jobs(self):
        before, after = self._restore_repair_workflows()
        assert_prior_ci_preserved(before, after)
        assert_prior_ci_preserved(before.replace('\n', '\r\n'), after)
        assert_prior_ci_preserved(after, after)
        with self.assertRaisesRegex(AssertionError, 'Prior CI job'):
            assert_prior_ci_preserved(after, before)

    def test_exact_client_update_preserves_tests_and_rejects_unrelated_changes(self):
        original, before = self._restore_repair_workflows()
        anchor = '          # Keep host backup/restore tools aligned with the disposable service.\n'
        update = (
            "          # pg_dump 16.16 understands the source's internal pg_attver metadata.\n"
            '          sudo apt-get update\n'
            '          sudo apt-get install --yes --only-upgrade postgresql-client-16\n'
            '          dump_version=$("$POSTGRES_BIN/pg_dump" --version | awk \'{print $3}\')\n'
            '          dpkg --compare-versions "$dump_version" ge 16.16\n'
        )
        after = before.replace(anchor, update + anchor, 1)
        assert_prior_ci_preserved(original, after)
        assert_prior_ci_preserved(before, after)
        current = (Path(__file__).resolve().parents[2] / '.github/workflows/backend-tests.yml').read_text(encoding='utf8')
        assert_prior_ci_preserved(after, current, accepted_baseline=subprocess.check_output(
            ['git', 'show', APPROVED_MAIN + ':.github/workflows/backend-tests.yml'],
            cwd=Path(__file__).resolve().parents[2]).decode())
        for old, new in [('ge 16.16', 'ge 16.15'), ('--only-upgrade', '--allow-unauthenticated'),
                         ('test_foushee_justice_publication_activation_postgres.py', 'test_other.py')]:
            with self.subTest(old=old), self.assertRaisesRegex(AssertionError, 'Prior CI job'):
                assert_prior_ci_preserved(before, after.replace(old, new))

    def test_postgres16_repair_rejects_every_job_line_mutation(self):
        before, after = self._restore_repair_workflows()
        match = re.search(r'(?ms)^  publication-activation-postgres:\n.*?(?=^  [a-zA-Z0-9_-]+:\n|\Z)', after)
        lines = match.group().splitlines(keepends=True)
        for index, line in enumerate(lines):
            if not line.strip():
                continue
            changed_lines = lines.copy()
            changed_lines[index] = line.rstrip('\n') + ' # unreviewed change\n'
            changed = after[:match.start()] + ''.join(changed_lines) + after[match.end():]
            with self.subTest(line=index), self.assertRaises(AssertionError):
                assert_prior_ci_preserved(before, changed)

    def test_postgres16_repair_requires_exact_old_job_and_preserves_other_jobs(self):
        before, after = self._restore_repair_workflows()
        for original, changed in [
            (before.replace('image: postgres:16', 'image: postgres:15'), after),
            (before, after.replace('contents: read', 'contents: write')),
            (before, after.replace('  m14f-exact-head:', '  unreviewed-job:')),
        ]:
            with self.subTest(original=original == before), self.assertRaises(AssertionError):
                assert_prior_ci_preserved(original, changed)

    def test_actual_reviewed_workflow_rejects_appended_job_then_top_level_settings(self):
        before = subprocess.check_output(['git', 'show', 'a988dd87b307ad9575201130b87105e3717013c1:.github/workflows/backend-tests.yml'],
                                         cwd=Path(__file__).resolve().parents[2]).decode()
        extra_job = '\n  probe-job:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo probe\n'
        assert_prior_ci_preserved(before, before + extra_job)
        for root in ['permissions:\n  contents: write\n', 'on:\n  workflow_dispatch:\n',
                     'env:\n  EXAMPLE: changed\n', 'concurrency: unreviewed\n',
                     'defaults:\n  run:\n    shell: bash\n', 'jobs:\n  duplicate-root:\n']:
            with self.subTest(root=root), self.assertRaisesRegex(AssertionError, 'top-level CI section'):
                assert_prior_ci_preserved(before, before + extra_job + '\n' + root)

    def test_duplicate_job_identity_cannot_hide_a_second_definition(self):
        original_job = BEFORE.split('\njobs:\n', 1)[1]
        with self.assertRaisesRegex(AssertionError, 'Duplicate CI job'):
            assert_prior_ci_preserved(BEFORE, APPROVED + '\n' + original_job)


if __name__ == '__main__':
    unittest.main()
