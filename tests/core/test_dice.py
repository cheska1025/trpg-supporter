import types
import pytest

from core.dice import roll
from core.dice import roll  # roll("2d6+3", advantage=False, explode=False) 가정

def test_roll_simple(monkeypatch):
    # randint를 고정 시퀀스로 만들어 2d6 => 4와 6을 반환하게 함
    seq = iter([4, 6])
    def fake_randint(a, b):  # noqa: ARG001
        return next(seq)
    import random
    monkeypatch.setattr(random, "randint", fake_randint)

    r = roll("2d6+3")
    # 결과 구조 예시: {"total": 13, "detail": [4,6], "crit": False, "fumble": False}
    assert r["total"] == 4 + 6 + 3
    assert r["detail"] == [4, 6]

def test_roll_crit_and_fumble_detection(monkeypatch):
    # 1d20 치트: 20 -> 크리틱, 1 -> 펌블
    import random
    monkeypatch.setattr(random, "randint", lambda a, b: 20)
    r1 = roll("1d20")
    assert r1.get("crit", False) is True

    monkeypatch.setattr(random, "randint", lambda a, b: 1)
    r2 = roll("1d20")
    assert r2.get("fumble", False) is True

def test_roll_pool_and_modifier(monkeypatch):
    # 3d4+2 => 1,2,3
    seq = iter([1,2,3])
    import random
    monkeypatch.setattr(random, "randint", lambda a,b: next(seq))
    r = roll("3d4+2")
    assert r["detail"] == [1,2,3]
    assert r["total"] == sum([1,2,3]) + 2

def test_log_export_unsupported_format_raises(tmp_path, monkeypatch):
    from core.log import LogManager
    import pytest
    monkeypatch.setenv("TRPG_HOME", str(tmp_path))
    lm = LogManager("S1")
    with pytest.raises(ValueError):
        lm.export("txt")

def test_roll_invalid_formula_raises():
    with pytest.raises(ValueError):
        roll("bad formula")