from core.dice import roll
from core.initiative import Tracker


def test_roll_basic():
    r = roll("2d6+1")
    assert r.formula == "2d6+1"
    assert isinstance(r.total, int)
    assert len(r.rolls) == 2


def test_initiative_cycle():
    t = Tracker()
    t.add("A", 15)
    t.add("B", 10)
    assert t.current().name == "A"
    t.next()
    assert t.current().name in {"A", "B"}  # 순환 확인
