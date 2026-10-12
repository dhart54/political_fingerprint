"""Both automatic events must cover the isolated proof's actual dependencies."""
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / '.github/workflows/education79-locator-preparation.yml'


def event_paths(event):
    text = WORKFLOW.read_text(encoding='utf-8')
    block = re.search(r'^  ' + event + r':\n(.*?)(?=^  \w|^\w)', text, re.M | re.S).group(1)
    return re.findall(r'^      - "([^"]+)"$', block, re.M)


def matches(path, patterns):
    # These path filters use only literals, * (one segment), and ** (any depth).
    for pattern in patterns:
        regex = re.escape(pattern).replace(r'\*\*', '.*').replace(r'\*', '[^/]*')
        if re.fullmatch(regex, path):
            return True
    return False


@pytest.mark.parametrize('event', ['pull_request', 'push'])
@pytest.mark.parametrize('path', [
    'frontend/lib/recordCard.mjs', 'frontend/lib/recordCardContent.json',
    'frontend/lib/issueEvidenceCoverage.mjs', 'frontend/lib/editorialPresentation.mjs',
    'scripts/education79_card_proof.mjs', 'scripts/validate_education79_locator_card.mjs',
    'docs/review_packets/record_at_a_glance_v1/candidate.json',
    'docs/editorial/publication_replacements/m15b_green_activation_execution/after-justice-live.json.gz',
    'backend/requirements.txt', 'backend/migrations/0012_editorial_artifacts.sql',
    'backend/migrations/staged/normalize_vote_storage.sql',
    'backend/scripts/disposable_database_url.py',
    'backend/scripts/education79_locator_operator.py',
    'backend/scripts/green_vote_storage.py',
    'backend/scripts/m15b_persistence_preparation.py',
    'backend/scripts/foushee_m15a2_core_repair.py',
    'backend/scripts/foushee_justice_receipt_evidence_repair.py',
    'backend/app/main.py', 'backend/app/api/precomputed.py',
    'backend/app/editorial_artifacts/repository.py',
    'backend/app/editorial_presentations/selector.py',
    'backend/app/editorial_presentations/publication_replacement_runtime_v2r.py',
    'backend/tests/conftest.py', 'backend/tests/test_m15b_actual_persistence.py',
    'backend/tests/test_reusable_publication_replacement_v2r.py',
    'backend/tests/test_education79_locator_workflow.py',
    'docs/editorial/shared_corpora/house_119_v2/shared_action_core.json',
    'docs/editorial/shared_corpora/house_119_v2/member_projections/f000477.json',
    'docs/editorial/analytical_candidates/f000477_education_workforce_m14d_v1/accepted_behavioral_findings.json',
    'docs/editorial/interpretability_candidates/house_119_v1/education_workforce_m14c_v1/source_catalog.json',
    'docs/editorial/interpretability_candidates/house_119_v1/education_workforce_m14c_v1/evidence/eaafafb53de434c894f475a864a1cd951118a32f2f98e1e487109f7ef71f5b32.html',
])
def test_proof_input_triggers_both_events(event, path):
    assert matches(path, event_paths(event)), path


@pytest.mark.parametrize('event', ['pull_request', 'push'])
@pytest.mark.parametrize('path', [
    'docs/editorial/analytical_candidates/f000477_immigration_border_m14d_v1/candidate.json',
    'backend/app/editorial_presentations/immigration_border_integration_candidate.py',
    'backend/migrations/staged/immigration_border.sql',
    'frontend/components/RepresentativeExperience.js',
])
def test_unconsumed_parallel_work_does_not_trigger(event, path):
    assert not matches(path, event_paths(event)), path


def test_event_filters_stay_equal_and_proof_runs_filter_tests():
    assert event_paths('pull_request') == event_paths('push')
    assert 'backend/tests/test_education79_locator_workflow.py \\' in WORKFLOW.read_text(encoding='utf-8')
