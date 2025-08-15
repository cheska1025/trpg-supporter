from __future__ import annotations

from typing import Any

from backend.app.core.db import session_scope
from backend.app.models import DiceLog


def save_dice_log(
    *,
    session_id: int,
    total: int,
    formula: str,
    detail: dict[str, Any],
    roller_id: int | None = None,
) -> int:
    """주사위 로그를 DB에 저장하고 새 id를 반환."""
    with session_scope() as s:
        log = DiceLog(
            session_id=session_id,
            roller_id=roller_id,
            formula=formula,
            detail=detail,
            total=total,
        )
        s.add(log)
        s.flush()
        return log.id
