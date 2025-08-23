from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from backend.app.db import engine  # tests에서도 이 모듈의 engine을 사용합니다.

router = APIRouter(prefix="/characters", tags=["characters"])


# ====== Schemas ======
class CharacterCreate(BaseModel):
    name: str = Field(..., min_length=1)
    clazz: Optional[str] = None
    # 기본값과 범위를 명시적으로 부여 (검증은 Pydantic/ FastAPI가 해줌)
    level: int = Field(default=1, ge=1)


class CharacterOut(BaseModel):
    id: int
    name: str
    clazz: Optional[str] = None
    level: int


# ====== Helpers ======
async def _fetch_one(db: AsyncEngine, sql: str, **params: Any) -> Optional[Dict[str, Any]]:
    async with db.begin() as conn:
        res = await conn.execute(text(sql), params)
        row = res.mappings().first()
        return dict(row) if row else None


async def _fetch_all(db: AsyncEngine, sql: str, **params: Any) -> List[Dict[str, Any]]:
    async with db.begin() as conn:
        res = await conn.execute(text(sql), params)
        return [dict(r) for r in res.mappings().all()]


# ====== Routes ======
@router.get("", response_model=List[CharacterOut])
async def list_characters(
    q: Optional[str] = Query(None, description="name 부분 검색"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort: Literal["id", "name", "level"] = "id",
    order: Literal["asc", "desc"] = "asc",
):
    where = ""
    params: Dict[str, Any] = {"limit": limit, "offset": offset}
    if q:
        where = "WHERE name LIKE :q"
        params["q"] = f"%{q}%"

    order_sql = f"ORDER BY {sort} {order.upper()}"
    sql = f"""
        SELECT id, name, clazz, level
        FROM characters
        {where}
        {order_sql}
        LIMIT :limit OFFSET :offset
    """
    rows = await _fetch_all(engine, sql, **params)
    return rows


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CharacterOut)
async def create_character(payload: CharacterCreate):
    # 중복 이름 체크 (unique)
    exists = await _fetch_one(
        engine,
        "SELECT id, name, clazz, level FROM characters WHERE name = :name",
        name=payload.name,
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="name already exists")

    async with engine.begin() as conn:
        res = await conn.execute(
            text(
                """
                INSERT INTO characters (name, clazz, level)
                VALUES (:name, :clazz, :level)
                RETURNING id, name, clazz, level
                """
            ),
            {"name": payload.name, "clazz": payload.clazz, "level": payload.level},
        )
        row = res.mappings().first()

    return CharacterOut(**row)  # type: ignore[arg-type]


@router.get("/{char_id}", response_model=CharacterOut)
async def get_character(char_id: int):
    row = await _fetch_one(
        engine,
        "SELECT id, name, clazz, level FROM characters WHERE id = :id",
        id=char_id,
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return row


@router.put("/{char_id}", response_model=CharacterOut)
async def update_character(char_id: int, payload: CharacterCreate):
    # 대상 확인
    orig = await _fetch_one(engine, "SELECT id FROM characters WHERE id = :id", id=char_id)
    if not orig:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")

    # 이름이 바뀌면 중복 체크
    dup = await _fetch_one(
        engine,
        "SELECT id FROM characters WHERE name = :name AND id <> :id",
        name=payload.name,
        id=char_id,
    )
    if dup:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="name already exists")

    async with engine.begin() as conn:
        res = await conn.execute(
            text(
                """
                UPDATE characters
                SET name = :name, clazz = :clazz, level = :level
                WHERE id = :id
                RETURNING id, name, clazz, level
                """
            ),
            {
                "id": char_id,
                "name": payload.name,
                "clazz": payload.clazz,
                "level": payload.level,
            },
        )
        row = res.mappings().first()

    return row  # type: ignore[return-value]


@router.delete("/{char_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(char_id: int):
    async with engine.begin() as conn:
        res = await conn.execute(text("DELETE FROM characters WHERE id = :id"), {"id": char_id})
        if res.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return None
