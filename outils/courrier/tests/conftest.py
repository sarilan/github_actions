import sys
from datetime import date
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent / "airtable"))

import classify  # noqa: E402

REFERENCE = date(2026, 9, 16)
CORPUS = HERE / "corpus"


@pytest.fixture(scope="session")
def rules():
    return classify.load_rules()


@pytest.fixture(scope="session")
def reference():
    return REFERENCE
