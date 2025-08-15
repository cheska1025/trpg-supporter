from __future__ import annotations

from core.initiative import Effect, Tracker


def test_stable_sort_for_ties():
    """동점(value 동일)일 때 삽입 순서가 유지되는지 확인."""
    tr = Tracker()
    # 모두 value=10 이지만 삽입 순서를 다르게
    names = ["Alpha", "Bravo", "Charlie", "Delta"]
    for n in names:
        tr.add(n, 10)

    # 내부 정렬 후에도 원래 삽입 순서가 유지되어야 함
    ordered = [e.name for e in tr.entries]
    assert ordered == names, f"stable sort expected {names}, got {ordered}"


def test_delay_and_resume_reinsertion_after_current_index():
    """
    delay(name) 후 resume(name)을 호출하면
    - next() 진행 중이던 '현재 인덱스' 다음 위치 혹은 라운드 말미 안전 위치에 재삽입되어야 한다.
    """
    tr = Tracker()
    tr.add("A", 15)
    tr.add("B", 12)
    tr.add("C", 10)

    # 첫 next() -> 현재 'A'
    cur = tr.next()
    assert cur and cur.name == "A"
    cur_idx_after_next = tr.idx

    # B 를 보류(delay)하면 라인업에서 빠져야 함
    tr.delay("B")
    assert all(e.name != "B" for e in tr.entries)

    # resume 시 현재 인덱스 다음(또는 안전 말미)에 들어와야 함
    tr.resume("B")
    names = [e.name for e in tr.entries]
    # 현재 idx 다음 어딘가에 B가 있어야 함
    assert "B" in names
    assert names.index("B") >= min(cur_idx_after_next + 1, len(names) - 1)


def test_prev_next_round_increase_decrease_bounds():
    """
    next/prev 로 라운드 증감이 올바르게 동작하고,
    prev 에서 라운드가 1 아래로 내려가지 않도록 경계 보장.
    """
    tr = Tracker()
    for name, val in [("A", 15), ("B", 12), ("C", 10)]:
        tr.add(name, val)

    # 세 명이므로 세 번 next() 하면 라운드 +1
    start_round = tr.round
    for _ in range(3):
        tr.next()
    assert tr.round == start_round + 1

    # prev() 한 번이면 다시 이전 엔트리로, 라운드가 다시 줄 수도 있지만 1 아래로는 안 내려감
    tr.prev()
    assert tr.round >= 1
    # prev를 과도하게 호출해도 1 미만으로 내려가지 않음
    for _ in range(10):
        tr.prev()
    assert tr.round == 1


def test_tick_effects_countdown_and_remove_zero():
    """
    tick_effects() 호출 시 각 효과의 남은 라운드가 1씩 줄어들고 0이 되면 제거.
    """
    tr = Tracker()
    tr.add("Poisoned", 11)
    # 효과 부여 (테스트 편의상 직접 접근 허용)
    for e in tr.entries:
        if e.name == "Poisoned":
            e.effects.append(Effect(name="Poison", remain_rounds=2))

    # 1회 감소 -> 1
    tr.tick_effects()
    eff = next(e for e in tr.entries if e.name == "Poisoned").effects
    assert eff and eff[0].remain_rounds == 1

    # 2회차 감소 -> 0 되어 제거
    tr.tick_effects()
    eff = next(e for e in tr.entries if e.name == "Poisoned").effects
    assert len(eff) == 0
