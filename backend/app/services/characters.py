from __future__ import annotations

from typing import Any

from backend.app.core.db import session_scope
from backend.app.models import Character


def add_character(*, session_id: int, name: str) -> dict[str, Any]:
    with session_scope() as s:
        ch = Character(owner_id=1, session_id=session_id, name=name)  # owner_id는 필요 시 조정
        s.add(ch)
        s.flush()
        return {"id": ch.id, "name": ch.name}


def list_characters(*, session_id: int) -> list[dict[str, Any]]:
    with session_scope() as s:
        rows = (
            s.query(Character)
            .filter(Character.session_id == session_id)
            .order_by(Character.name.asc())
            .all()
        )
        return [{"id": c.id, "name": c.name} for c in rows]
