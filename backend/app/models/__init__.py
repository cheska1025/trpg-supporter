from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# ruff: noqa: E402  # Base 선언 후 모델 등록을 위해 이 블록만 예외
from .entities import (
    Character as Character,
)
from .entities import (
    DiceLog as DiceLog,
)
from .entities import (
    Encounter as Encounter,
)
from .entities import (
    Initiative as Initiative,
)
from .entities import (
    LogEntry as LogEntry,
)
from .entities import (
    Session as Session,
)
from .entities import (
    User as User,
)

__all__ = [
    "Base",
    "User",
    "Session",
    "Character",
    "Encounter",
    "Initiative",
    "DiceLog",
    "LogEntry",
]
