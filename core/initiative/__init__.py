from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

__all__ = ["InitiativeTracker", "Tracker"]


@dataclass
class _Entry:
    """
    내부 관리용 엔트리.
    - value: 이니시 값(높을수록 먼저)
    - seq: 입력 순서(동점 시 안정 정렬 보장)
    - delayed: 보류 상태
    """

    name: str
    value: int
    seq: int
    delayed: bool = False


class InitiativeTracker:
    """
    이니시 티브 트래커(테스트가 기대하는 최소 인터페이스)

    공개 메서드
    - add(name, value): 엔트리 추가
    - start_encounter(): 전투 시작(정렬/라운드 초기화)
    - current() -> 객체(속성 name, value)
    - next_turn(): 턴 진행 (라운드 증가 포함)
    - delay(name): 보류 표시 (현재 턴 보류 시 즉시 다음으로 진행)
    - return_from_delay(name): 같은 라운드 '꼬리'로 재진입
    프로퍼티
    - order: 현 정렬 순서 리스트(각 항목 name/value/delayed 제공)
    - round: 현재 라운드(정수)
    """

    def __init__(self) -> None:
        self._entries: list[_Entry] = []
        self._seq = 0  # 동점 안정 정렬을 위한 입력 순서
        self._index = 0  # 현재 턴 인덱스
        self.round = 0  # 0 = 미시작, 1부터 시작
        self._started = False

    # ---------- 등록/정렬 ----------
    def add(self, name: str, value: int) -> None:
        """엔트리 추가 (아직 시작 전이라면 단순 추가, 시작 후에도 추가 가능)"""
        self._entries.append(_Entry(name=name, value=int(value), seq=self._seq, delayed=False))
        self._seq += 1
        # 전투 시작 이전에는 정렬을 미뤄도 되지만, 시작 이후 추가가 있을 수 있으므로 정렬 유지
        if self._started:
            self._stable_sort()

    def start_encounter(self) -> None:
        """전투 시작: 안정 정렬 후 라운드/인덱스 초기화"""
        self._stable_sort()
        self._index = 0
        self.round = 1 if self._entries else 0
        self._started = True

    def _stable_sort(self) -> None:
        # value 내림차순, seq 오름차순(입력 순서)으로 안정 정렬
        self._entries.sort(key=lambda e: (-e.value, e.seq))

    # ---------- 조회 ----------
    def current(self):
        """현재 턴의 엔트리 반환. 없으면 None."""
        if not self._entries:
            return None
        e = self._entries[self._index]
        return SimpleNamespace(name=e.name, value=e.value, delayed=e.delayed)

    @property
    def order(self):
        """현재 정렬 순서를 반환(테스트에서 리스트 확인용)"""
        return [
            SimpleNamespace(name=e.name, value=e.value, delayed=e.delayed) for e in self._entries
        ]

    # ---------- 턴/라운드 ----------
    def next_turn(self) -> None:
        """다음 턴으로 진행. 라운드 경계를 넘으면 round + 1"""
        if not self._started or not self._entries:
            return
        self._index += 1
        if self._index >= len(self._entries):
            self._index = 0
            self.round += 1

    # ---------- 보류/재진입 ----------
    def delay(self, name: str) -> None:
        """
        주어진 이름을 보류 상태로 표시.
        현재 턴의 엔트리를 보류하면 즉시 다음 턴으로 진행한다.
        """
        for i, e in enumerate(self._entries):
            if e.name == name and not e.delayed:
                e.delayed = True
                # 현재 턴 보류 시 다음 턴으로
                if i == self._index:
                    self.next_turn()
                return

    def return_from_delay(self, name: str) -> None:
        """
        보류된 엔트리를 같은 라운드의 '꼬리'에 재배치하고 보류 해제.
        (정책: 재진입은 동일 라운드 꼬리로. 동점 안정 정렬 유지)
        """
        for i, e in enumerate(self._entries):
            if e.name == name and e.delayed:
                # 꺼내서 꼬리로 보냄(새로운 seq를 부여)
                removed = self._entries.pop(i)
                if i < self._index:
                    # 현재 인덱스 앞쪽이 빠졌다면 보정
                    self._index -= 1
                removed.delayed = False
                removed.seq = self._seq
                self._seq += 1
                self._entries.append(removed)
                # 정렬 정책 유지(꼬리로 보냈지만 value 기준 정렬 필요 시 반영)
                # 여기서는 '같은 라운드 꼬리' 정책을 위해 정렬 대신 위치 고정
                # 다만, value 기반 전역 정렬이 필요하다면 아래 주석을 해제:
                # self._stable_sort()
                # self._index %= len(self._entries)
                return

    def next(self):
        """Back-compat alias for next_turn(). 테스트에서 Tracker.next()를 호출하는 경우 대응."""
        self.next_turn()
        return self.current()


# 하위 호환: 기존 이름 Tracker도 그대로 쓸 수 있도록 별칭 제공
Tracker = InitiativeTracker
