from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Effect:
    """상태효과: n 턴 지속. 라운드(턴) 경과 시 remain_rounds -= 1, 0이 되면 제거."""

    name: str
    remain_rounds: int

    def tick(self) -> bool:
        """한 턴 감소. 만료되면 True 반환."""
        self.remain_rounds -= 1
        return self.remain_rounds <= 0


@dataclass(slots=True)
class Entry:
    """이니시 엔트리(배우/캐릭터 단위)."""

    name: str
    value: int
    delayed: bool = False
    effects: list[Effect] = field(default_factory=list)
    insert_order: int = 0  # Stable sort 유지용

    def add_effect(self, name: str, turns: int) -> None:
        self.effects.append(Effect(name=name, remain_rounds=turns))

    def remove_effect(self, name: str) -> bool:
        before = len(self.effects)
        self.effects = [e for e in self.effects if e.name != name]
        return len(self.effects) < before

    def list_effects(self) -> list[Effect]:
        return list(self.effects)


class Tracker:
    """
    이니시 트래커.
    - 등록/정렬(안정 정렬): value 내림차순, 동일 값은 insert_order 오름차순
    - next/prev: 지연(delayed=False인 항목만 순회)
    - delay/resume: 지연/재진입 (재진입 시 현재 커서 바로 뒤 또는 라운드 말미 삽입)
    - 라운드 카운트: 커서가 리스트의 처음으로 되돌아올 때 +1, tick_effects() 수행
    """

    def __init__(self) -> None:
        self.entries: list[Entry] = []
        self.round: int = 1
        self._cursor: int = -1  # -1이면 아직 시작 전
        self._seq: int = 0  # insert_order 부여용
        # 재진입 정책: "after_current" 또는 "end_of_round"
        self.resume_policy: str = "after_current"

    # ---------- 내부 유틸 ----------

    def _find_index(self, name: str) -> int | None:
        for i, e in enumerate(self.entries):
            if e.name == name:
                return i
        return None

    def _sort_stable(self) -> None:
        # value 내림차순, insert_order 오름차순 → 안정 정렬 보장
        self.entries.sort(key=lambda e: (-e.value, e.insert_order))

    def _non_delayed_indices(self) -> list[int]:
        return [i for i, e in enumerate(self.entries) if not e.delayed]

    def _advance_cursor(self, step: int) -> int | None:
        """
        step=+1(next)/-1(prev) 기준으로 지연되지 않은 엔트리만 순회.
        라운드 증감/효과 처리 시점 관리.
        """
        if not self.entries:
            self._cursor = -1
            return None

        candidates = self._non_delayed_indices()
        if not candidates:
            # 전원 지연된 경우: 현재 턴 없음
            self._cursor = -1
            return None

        if self._cursor == -1:
            # 시작점: 첫 비지연 엔트리로
            self._cursor = candidates[0]
            return self._cursor

        # 현재 커서가 active 목록에서 어디인지 찾고 이동
        try:
            pos = candidates.index(self._cursor)
        except ValueError:
            # 커서가 active에 없으면(step에 따라) 맨앞/맨뒤로 보정
            self._cursor = candidates[0] if step > 0 else candidates[-1]
            return self._cursor

        new_pos = pos + (1 if step > 0 else -1)

        if step > 0 and new_pos >= len(candidates):
            # 순환 → 라운드 +1 및 효과 tick
            self.round += 1
            self.tick_effects()
            self._cursor = candidates[0]
        elif step < 0 and new_pos < 0:
            # 역순환 → 라운드 -1(최소 1)
            self.round = max(1, self.round - 1)
            self._cursor = candidates[-1]
        else:
            self._cursor = candidates[new_pos]

        return self._cursor

    # ---------- 공개 API ----------

    def add(self, name: str, value: int) -> None:
        if self._find_index(name) is not None:
            raise ValueError(f"'{name}' already exists")
        self.entries.append(Entry(name=name, value=value, insert_order=self._seq))
        self._seq += 1
        self._sort_stable()

    def remove(self, name: str) -> bool:
        idx = self._find_index(name)
        if idx is None:
            return False
        if self._cursor != -1 and idx <= self._cursor:
            self._cursor -= 1
        del self.entries[idx]
        if not self.entries:
            self._cursor = -1
        return True

    def update(self, name: str, value: int) -> None:
        idx = self._find_index(name)
        if idx is None:
            raise ValueError(f"'{name}' not found")
        self.entries[idx].value = value
        self._sort_stable()

    def delay(self, name: str) -> None:
        idx = self._find_index(name)
        if idx is None:
            raise ValueError(f"'{name}' not found")
        self.entries[idx].delayed = True
        if self._cursor == idx:
            self.next()

    def resume(self, name: str) -> None:
        idx = self._find_index(name)
        if idx is None:
            raise ValueError(f"'{name}' not found")
        entry = self.entries[idx]
        if not entry.delayed:
            return
        entry.delayed = False

        if self._cursor == -1:
            self._sort_stable()
            return

        if self.resume_policy == "after_current":
            e = self.entries.pop(idx)
            insert_at = self._cursor + 1
            if idx < insert_at:
                insert_at -= 1
            self.entries.insert(insert_at, e)
        else:
            e = self.entries.pop(idx)
            self.entries.append(e)

    def reset(self) -> None:
        self.round = 1
        self._cursor = -1
        for e in self.entries:
            e.delayed = False

    def next(self) -> Entry | None:
        idx = self._advance_cursor(+1)
        return None if idx is None else self.entries[idx]

    def prev(self) -> Entry | None:
        idx = self._advance_cursor(-1)
        return None if idx is None else self.entries[idx]

    def tick_effects(self) -> list[tuple[str, str]]:
        """라운드 변환 시 효과를 1씩 감소시키고 만료된 항목을 제거. (actor, effect) 반환."""
        expired: list[tuple[str, str]] = []
        for e in self.entries:
            still_alive: list[Effect] = []
            for fx in e.effects:
                if fx.tick():
                    expired.append((e.name, fx.name))
                else:
                    still_alive.append(fx)
            e.effects = still_alive
        return expired

    def state(self) -> dict:
        """상태 덤프(CLI/테스트용)."""
        current = None if self._cursor == -1 else self.entries[self._cursor].name
        return {
            "round": self.round,
            "current": current,
            "entries": [
                {
                    "name": e.name,
                    "value": e.value,
                    "delayed": e.delayed,
                    "effects": [{"name": fx.name, "remain": fx.remain_rounds} for fx in e.effects],
                }
                for e in self.entries
            ],
        }


__all__ = ["Effect", "Entry", "Tracker"]
