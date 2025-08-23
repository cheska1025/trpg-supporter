from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CharacterIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    clazz: str = Field(..., min_length=1, max_length=32)
    level: int = Field(default=1, ge=1)


class CharacterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    clazz: str
    level: int
