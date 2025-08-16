import os, shutil, tempfile, pytest

@pytest.fixture(autouse=True)
def _isolate_trpg_home(monkeypatch):
    """
    모든 테스트에서 자동 적용되는 픽스처.
    TRPG_HOME 경로를 임시 디렉토리로 대체하여
    실제 ~/.trpg 데이터를 건드리지 않도록 한다.
    """
    d = tempfile.mkdtemp(prefix="trpg_home_")
    monkeypatch.setenv("TRPG_HOME", d)
    yield
    shutil.rmtree(d, ignore_errors=True)