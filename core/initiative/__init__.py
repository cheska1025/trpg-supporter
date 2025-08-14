from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(order=True)
class InitEntry:
    sort_index: int = field(init=False, repr=False)
    name: str
    value: int
    delayed: bool = False

    def __post_init__(self):
        # 높은 값이 먼저 오도록 음수 정렬 키
        self.sort_index = -self.value


class Tracker:
    def __init__(self):
        self.entries: list[InitEntry] = []
        self.idx = 0
        self.round = 1

    def add(self, name: str, value: int):
        self.entries.append(InitEntry(name=name, value=value))
        self.entries.sort()

    def next(self) -> InitEntry | None:
        if not self.entries:
            return None
        self.idx += 1
        if self.idx >= len(self.entries):
            self.idx = 0
            self.round += 1
        return self.entries[self.idx]

    def current(self) -> InitEntry | None:
        if not self.entries:
            return None
        return self.entries[self.idx]
