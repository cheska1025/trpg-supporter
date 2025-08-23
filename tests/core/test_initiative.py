from core.initiative import InitiativeTracker


def test_round_progress_and_stable_ties() -> None:
    t = InitiativeTracker()
    t.add("Rogue", 15)
    t.add("GoblinA", 12)
    t.add("GoblinB", 12)  # 동점 안정성 체크
    t.start_encounter()

    assert t.round == 1
    assert t.current().name == "Rogue"

    t.next_turn()
    first = t.current().name
    t.next_turn()
    second = t.current().name
    assert {first, second} == {"GoblinA", "GoblinB"}
    assert first != second  # 안정적 정렬

    t.next_turn()  # 라운드 증가
    assert t.round == 2
    assert t.current().name == "Rogue"


def test_delay_and_reentry_in_same_round() -> None:
    t = InitiativeTracker()
    t.add("Rogue", 18)
    t.add("Mage", 14)
    t.add("Orc", 10)
    t.start_encounter()

    assert t.current().name == "Rogue"
    t.delay("Rogue")  # 보류
    assert t.current().name == "Mage"

    t.next_turn()  # -> Orc
    t.next_turn()  # 라운드 경계
    assert t.round == 2
    assert t.current().name == "Rogue"  # 재진입 규칙 확인


def test_reentry_ordering_policy() -> None:
    t = InitiativeTracker()
    t.add("A", 20)
    t.add("B", 15)
    t.add("C", 10)
    t.start_encounter()
    t.delay("A")
    t.next_turn()
    t.next_turn()  # B, C
    t.return_from_delay("A")  # 정책상 재배치
    names = [s.name for s in t.order]
    assert "A" in names
