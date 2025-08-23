from __future__ import annotations

from dataclasses import dataclass

__all__ = ["InitiativeTracker", "Tracker", "Actor"]


@dataclass(eq=True, frozen=False)
class Actor:
    name: str
    init: int
    delayed: bool = False


class InitiativeTracker:
    """
    간단한 이니시 추적기:
    - add(name, init): 참가자 추가
    - start_encounter(): 정렬하고 라운드 1 시작
    - current: 현재 차례의 Actor (항상 Actor 반환)
    - order: 현재 라운드의 순서(리스트) 프로퍼티
    - next_turn(): 다음 차례로 진행 (리턴값: 진행 후의 current)
    - next(): 테스트 호환용 별칭 (next_turn() 래핑)
    - delay(name): 해당 액터를 지연 상태로 표시하고 턴 순서의 맨 뒤로 보냄
    - return_from_delay(name): 지연 해제 (현 순서 유지)
    - round: 현재 라운드 번호 프로퍼티
    """

    def __init__(self) -> None:
        self._actors: list[Actor] = []
        self._idx: int = -1  # current index
        self._round: int = 0

    # ---- 등록/시작 ---------------------------------------------------------
    def add(self, name: str, init: int) -> None:
        self._actors.append(Actor(name=name, init=init))

    def start_encounter(self) -> None:
        # 높은 이니시어티브 우선, 동률은 이름 사전순
        self._actors.sort(key=lambda a: (-a.init, a.name))
        self._round = 1 if self._actors else 0
        self._idx = 0 if self._actors else -1

    # ---- 조회 프로퍼티 ------------------------------------------------------
    @property
    def round(self) -> int:
        return self._round

    @property
    def order(self) -> list[Actor]:
        # 외부에서 변경 못 하도록 복사 반환
        return list(self._actors)

    def current(self) -> Actor:
        if not self._actors or self._idx < 0:
            # 테스트 기대치에 맞게 Optional이 아닌 Actor를 반환해야 하므로
            # 빈 상태는 논리 오류로 처리
            raise RuntimeError("No active actor; call start_encounter() after adding actors.")
        return self._actors[self._idx]

    # ---- 진행/지연 ----------------------------------------------------------
    def next_turn(self) -> Actor:
        if not self._actors:
            raise RuntimeError("No actors to advance.")
        self._idx += 1
        if self._idx >= len(self._actors):
            self._idx = 0
            self._round += 1
        return self.current()

    # 테스트 호환용 별칭
    def next(self) -> Actor:
        return self.next_turn()

    def delay(self, name: str) -> None:
        # name으로 액터 찾기
        idx = next((i for i, a in enumerate(self._actors) if a.name == name), None)
        if idx is None:
            raise ValueError(f"Actor not found: {name}")

        actor = self._actors[idx]
        actor.delayed = True  # 플래그 설정

        # 현재 인덱스 이전의 항목이 빠지면 인덱스 보정
        remove_affects_current = idx <= self._idx
        # 순서 맨 뒤로 보냄
        self._actors.pop(idx)
        self._actors.append(actor)

        if remove_affects_current:
            # 현재 포인터가 한 칸 앞당겨진 효과이므로 보정
            self._idx = max(0, self._idx - 1)

    def return_from_delay(self, name: str) -> None:
        actor = next((a for a in self._actors if a.name == name), None)
        if actor is None:
            raise ValueError(f"Actor not found: {name}")
        actor.delayed = False


# 테스트에서 Tracker 심볼을 임포트하므로 별칭 제공
Tracker = InitiativeTracker
