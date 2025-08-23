from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base

RoleEnum = Enum("GM", "Player", name="role_enum")
SessionStatusEnum = Enum("open", "closed", name="session_status_enum")


class User(Base):  # type: ignore[misc]
    __tablename__ = "users"

    # 컬럼: mypy와 서비스단 호환을 위해 Any로 표기
    id: Any = Column(Integer, primary_key=True)
    name: Any = Column(String(64), nullable=False, index=True)
    role: Any = Column(RoleEnum, nullable=False, default="Player")
    discord_id: Any = Column(String(64))
    created_at: Any = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 관계: Any로 표기하여 stubs의 RelationshipProperty[Never] 문제 회피
    characters: Any = relationship(
        "Character", back_populates="owner", cascade="all, delete-orphan"
    )
    sessions_gm: Any = relationship("Session", back_populates="gm")


class Session(Base):  # type: ignore[misc]
    __tablename__ = "sessions"

    id: Any = Column(Integer, primary_key=True)
    title: Any = Column(String(128), nullable=False)
    status: Any = Column(SessionStatusEnum, default="open", nullable=False)
    gm_id: Any = Column(ForeignKey("users.id"), nullable=False)
    schedule: Any = Column(String(128))
    created_at: Any = Column(DateTime, default=datetime.utcnow, nullable=False)

    gm: Any = relationship("User", back_populates="sessions_gm")
    characters: Any = relationship(
        "Character", back_populates="session", cascade="all, delete-orphan"
    )
    encounters: Any = relationship(
        "Encounter", back_populates="session", cascade="all, delete-orphan"
    )
    dice_logs: Any = relationship("DiceLog", back_populates="session", cascade="all, delete-orphan")
    log_entries: Any = relationship(
        "LogEntry", back_populates="session", cascade="all, delete-orphan"
    )


class Character(Base):  # type: ignore[misc]
    __tablename__ = "characters"

    id: Any = Column(Integer, primary_key=True)
    owner_id: Any = Column(ForeignKey("users.id"), nullable=False)
    session_id: Any = Column(ForeignKey("sessions.id"), nullable=False)
    name: Any = Column(String(64), nullable=False, index=True)
    clazz: Any = Column(String(32))
    stats: Any = Column(JSON)  # dict 저장용

    owner: Any = relationship("User", back_populates="characters")
    session: Any = relationship("Session", back_populates="characters")

    __table_args__ = (Index("ix_char_session_name", "session_id", "name", unique=True),)


class Encounter(Base):  # type: ignore[misc]
    __tablename__ = "encounters"

    id: Any = Column(Integer, primary_key=True)
    session_id: Any = Column(ForeignKey("sessions.id"), nullable=False, index=True)
    round: Any = Column(Integer, default=1)
    notes: Any = Column(Text)

    session: Any = relationship("Session", back_populates="encounters")
    initiatives: Any = relationship(
        "Initiative", back_populates="encounter", cascade="all, delete-orphan"
    )


class Initiative(Base):  # type: ignore[misc]
    __tablename__ = "initiatives"

    id: Any = Column(Integer, primary_key=True)
    encounter_id: Any = Column(ForeignKey("encounters.id"), nullable=False, index=True)
    actor_name: Any = Column(String(64), nullable=False)
    value: Any = Column(Integer, nullable=False)
    order: Any = Column(Integer)
    is_delayed: Any = Column(Boolean, default=False)

    encounter: Any = relationship("Encounter", back_populates="initiatives")

    __table_args__ = (
        CheckConstraint("value >= -100 and value <= 1000", name="ck_init_value_range"),
        Index("ix_init_encounter_value", "encounter_id", "value"),
    )


class DiceLog(Base):  # type: ignore[misc]
    __tablename__ = "dice_logs"

    id: Any = Column(Integer, primary_key=True)
    session_id: Any = Column(ForeignKey("sessions.id"), nullable=False, index=True)
    roller_id: Any = Column(ForeignKey("users.id"))
    formula: Any = Column(String(64), nullable=False)
    detail: Any = Column(JSON)  # 각 눈/옵션 정보
    total: Any = Column(Integer, nullable=False)
    created_at: Any = Column(DateTime, default=datetime.utcnow, nullable=False)

    session: Any = relationship("Session", back_populates="dice_logs")


class LogEntry(Base):  # type: ignore[misc]
    __tablename__ = "log_entries"

    id: Any = Column(Integer, primary_key=True)
    session_id: Any = Column(ForeignKey("sessions.id"), nullable=False, index=True)
    category: Any = Column(String(16), default="narrative")  # narrative/system
    message: Any = Column(Text, nullable=False)
    created_at: Any = Column(DateTime, default=datetime.utcnow, nullable=False)

    session: Any = relationship("Session", back_populates="log_entries")
