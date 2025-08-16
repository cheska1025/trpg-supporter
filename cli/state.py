# cli/state.py
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

STATE_DIR = Path.home() / ".trpg"
STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = STATE_DIR / "state.json"


@dataclass(slots=True)
class CharacterState:
    name: str


@dataclass(slots=True)
class SessionState:
    id: int
    title: str
    is_open: bool = True
    characters: list[CharacterState] = field(default_factory=list)


@dataclass(slots=True)
class AppState:
    current_session_id: int | None = None
    sessions: list[SessionState] = field(default_factory=list)

    # -------- helpers --------
    def _next_session_id(self) -> int:
        return max((s.id for s in self.sessions), default=0) + 1

    def get_current(self) -> SessionState | None:
        if self.current_session_id is None:
            return None
        for s in self.sessions:
            if s.id == self.current_session_id:
                return s
        return None

    # sessions
    def new_session(self, title: str) -> SessionState:
        s = SessionState(id=self._next_session_id(), title=title, is_open=True)
        self.sessions.append(s)
        self.current_session_id = s.id
        return s

    def open_session(self, sid: int) -> SessionState:
        for s in self.sessions:
            if s.id == sid:
                self.current_session_id = sid
                s.is_open = True
                return s
        raise ValueError(f"세션 {sid}을(를) 찾지 못했습니다.")

    def close_session(self) -> None:
        s = self.get_current()
        if not s:
            raise ValueError("열려 있는 세션이 없습니다.")
        s.is_open = False
        self.current_session_id = None

    # characters
    def add_char(self, name: str) -> CharacterState:
        s = self.get_current()
        if not s:
            raise ValueError("먼저 세션을 열어주세요 (session new|open).")
        if any(c.name == name for c in s.characters):
            raise ValueError(f"캐릭터 '{name}'가 이미 존재합니다.")
        c = CharacterState(name=name)
        s.characters.append(c)
        return c


# ---------- load/save ----------
def save(state: AppState) -> None:
    payload = asdict(state)
    STATE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load() -> AppState:
    if not STATE_FILE.exists():
        return AppState()
    data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    # 복원
    sessions: list[SessionState] = []
    for s in data.get("sessions", []):
        chars = [CharacterState(**c) for c in s.get("characters", [])]
        sessions.append(
            SessionState(
                id=int(s["id"]),
                title=s["title"],
                is_open=bool(s.get("is_open", True)),
                characters=chars,
            )
        )
    return AppState(
        current_session_id=data.get("current_session_id"),
        sessions=sessions,
    )
