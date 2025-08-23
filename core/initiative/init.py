from __future__ import annotations

from dataclasses import dataclass

__all__ = ["InitiativeTracker", "Actor", "Tracker"]


@dataclass(frozen=True)
class Actor:
    name: str
    init: int
    delayed: bool = False


class InitiativeTracker:
    """
    테스트들이 기대하는 간단한 이니시 추적기 API:
      - add(name, value)
      - start_encounter()
      - current() -> Actor
      - order (property) -> list[Actor]
      - next_turn()
      - next()  # next_turn 별칭
      - delay(name)
      - return_from_delay(name)
      - round (int)
    """

    def __init__(self) -> None:
        self._actors: list[Actor] = []
        self._idx: int = -1
        self.round: int = 0
        self._started: bool = False

    # --- 구성 ---
    def add(self, name: str, value: int) -> None:
        self._actors.append(Actor(name=name, init=value, delayed=False))

    def start_encounter(self) -> None:
        self._actors.sort(key=lambda a: (-a.init, a.name))
        self._idx = 0 if self._actors else -1
        self.round = 1 if self._actors else 0
        self._started = True

    # --- 조회 ---
    def current(self) -> Actor:
        # 테스트는 current()가 None을 반환하지 않는다고 가정
        if not self._started or self._idx < 0 or self._idx >= len(self._actors):
            raise RuntimeError("Encounter not started or no actors.")
        return self._actors[self._idx]

    @property
    def order(self) -> list[Actor]:
        return list(self._actors)

    # --- 진행 ---
    def next_turn(self) -> None:
        if not self._started or not self._actors:
            return
        self._idx += 1
        if self._idx >= len(self._actors):
            self._idx = 0
            self.round += 1

    def next(self) -> None:
        """Alias of next_turn()."""
        self.next_turn()

    # --- 지연 ---
    def delay(self, name: str) -> None:
        for i, a in enumerate(self._actors):
            if a.name == name:
                self._actors[i] = Actor(a.name, a.init, True)
                break

    def return_from_delay(self, name: str) -> None:
        for i, a in enumerate(self._actors):
            if a.name == name and a.delayed:
                self._actors[i] = Actor(a.name, a.init, False)
                actor = self._actors.pop(i)
                # 현재 인덱스 다음 자리로 복귀
                insert_at = min(self._idx + 1, len(self._actors))
                self._actors.insert(insert_at, actor)
                break


# tests/test_smoke.py 에서 Tracker 이름을 임포트하므로 별칭 제공
Tracker = InitiativeTracker
