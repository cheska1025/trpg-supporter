from __future__ import annotations

from sqlalchemy import Column, Integer, String

from .base import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
