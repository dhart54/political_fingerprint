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
