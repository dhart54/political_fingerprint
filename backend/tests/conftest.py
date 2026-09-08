import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


import pytest


@pytest.fixture
def fixture_mode(monkeypatch):
    """Explicit opt-in for tests whose input is the repository demo dataset."""
    monkeypatch.setenv("ENABLE_FIXTURE_FALLBACK", "1")
