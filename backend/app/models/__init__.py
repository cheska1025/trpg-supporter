from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# ruff: noqa: E402  # Base 선언 후 모델 등록을 위해 이 블록만 예외
from .entities import (
    User as User,
    Session as Session,
    Character as Character,
    Encounter as Encounter,
    Initiative as Initiative,
    DiceLog as DiceLog,
    LogEntry as LogEntry,
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
