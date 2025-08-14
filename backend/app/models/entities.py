from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base

RoleEnum = Enum("GM", "Player", name="role_enum")
SessionStatusEnum = Enum("open", "closed", name="session_status_enum")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    role: Mapped[str] = mapped_column(RoleEnum, nullable=False, default="Player")
    discord_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    characters: Mapped[list["Character"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    sessions_gm: Mapped[list["Session"]] = relationship(back_populates="gm")


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        SessionStatusEnum, default="open", nullable=False
    )
    gm_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    schedule: Mapped[Optional[str]] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    gm: Mapped["User"] = relationship(back_populates="sessions_gm")
    characters: Mapped[list["Character"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    encounters: Mapped[list["Encounter"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    dice_logs: Mapped[list["DiceLog"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    log_entries: Mapped[list["LogEntry"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Character(Base):
    __tablename__ = "characters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    clazz: Mapped[Optional[str]] = mapped_column(String(32))
    stats: Mapped[Optional[dict]] = mapped_column(JSON)  # SQLite에선 TEXT 기반

    owner: Mapped["User"] = relationship(back_populates="characters")
    session: Mapped["Session"] = relationship(back_populates="characters")

    __table_args__ = (Index("ix_char_session_name", "session_id", "name", unique=True),)


class Encounter(Base):
    __tablename__ = "encounters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id"), nullable=False, index=True
    )
    round: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    session: Mapped["Session"] = relationship(back_populates="encounters")
    initiatives: Mapped[list["Initiative"]] = relationship(
        back_populates="encounter", cascade="all, delete-orphan"
    )


class Initiative(Base):
    __tablename__ = "initiatives"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    encounter_id: Mapped[int] = mapped_column(
        ForeignKey("encounters.id"), nullable=False, index=True
    )
    actor_name: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    order: Mapped[Optional[int]] = mapped_column(Integer)
    is_delayed: Mapped[bool] = mapped_column(Boolean, default=False)

    encounter: Mapped["Encounter"] = relationship(back_populates="initiatives")

    __table_args__ = (
        CheckConstraint("value >= -100 and value <= 1000", name="ck_init_value_range"),
        Index("ix_init_encounter_value", "encounter_id", "value"),
    )


class DiceLog(Base):
    __tablename__ = "dice_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id"), nullable=False, index=True
    )
    roller_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    formula: Mapped[str] = mapped_column(String(64), nullable=False)
    detail: Mapped[Optional[dict]] = mapped_column(JSON)  # 각 눈/옵션 정보
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    session: Mapped["Session"] = relationship(back_populates="dice_logs")


class LogEntry(Base):
    __tablename__ = "log_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(
        String(16), default="narrative"
    )  # narrative/system
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    session: Mapped["Session"] = relationship(back_populates="log_entries")
