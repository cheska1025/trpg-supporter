from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.core.db import session_scope
from backend.app.models import Session

STATE = Path.home() / ".trpg" / "current_session.json"
STATE.parent.mkdir(parents=True, exist_ok=True)


def _save_current(session_id: int | None) -> None:
    data: dict[str, Any] = {"id": session_id}
    STATE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_current() -> int | None:
    if not STATE.exists():
        return None
    try:
        data = json.loads(STATE.read_text(encoding="utf-8"))
        raw = data.get("id")
        return int(raw) if raw is not None else None
    except Exception:
        return None


def create_session(*, title: str) -> dict[str, Any]:
    with session_scope() as s:
        sess = Session(title=title, gm_id=1, status="open")  # 필요 시 gm_id 조정
        s.add(sess)
        s.flush()
        _save_current(sess.id)
        return {"id": sess.id, "title": sess.title}


def set_current_session(session_id: int) -> None:
    _save_current(session_id)


def current_session() -> dict[str, Any] | None:
    sid = _load_current()
    if not sid:
        return None
    with session_scope() as s:
        obj = s.get(Session, sid)
        if not obj:
            return None
        return {"id": obj.id, "title": obj.title, "status": obj.status}


def close_session(session_id: int) -> None:
    with session_scope() as s:
        obj = s.get(Session, session_id)
        if not obj:
            return
        obj.status = "closed"
        # 현재 세션이면 해제
        cur = _load_current()
        if cur == session_id:
            _save_current(None)
