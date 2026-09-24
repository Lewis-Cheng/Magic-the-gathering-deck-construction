from __future__ import annotations

import pytest

from generator.oracle_bridge import get_oracle
from generator.index import get_index


@pytest.fixture(scope="session")
def oracle():
    return get_oracle()


@pytest.fixture(scope="session")
def index(oracle):
    return get_index()
