from __future__ import annotations

import shutil
import tempfile
from collections.abc import Generator

import pytest


@pytest.fixture(autouse=True)
def _isolate_trpg_home(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    d = tempfile.mkdtemp(prefix="trpg_home_")
    monkeypatch.setenv("TRPG_HOME", d)
    try:
        yield
    finally:
        shutil.rmtree(d, ignore_errors=True)
