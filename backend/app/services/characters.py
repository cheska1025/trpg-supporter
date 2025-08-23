from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import asc, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Character


async def list_characters(
    db: AsyncSession,
    *,
    name: str | None = None,
    limit: int = 20,
    offset: int = 0,
    order_by: str = "id",
    order: str = "asc",
) -> tuple[list[Character], int]:
    """
    목록 조회 with name(부분일치, 대소문자무시), 페이지네이션, 정렬.
    반환값: (items, total)
    """
    base = select(Character)
    count_q = select(func.count()).select_from(Character)

    if name:
        # 대소문자 무시 부분검색: lower(name) LIKE %q%
        q = f"%{name.lower()}%"
        cond = func.lower(Character.name).like(q)
        base = base.where(cond)
        count_q = count_q.where(cond)

    # 정렬 컬럼 화이트리스트
    order_map = {
        "id": Character.id,
        "name": Character.name,
        "level": Character.level,
        "clazz": Character.clazz,
    }
    col = order_map.get(order_by, Character.id)
    order_func = asc if order.lower() != "desc" else desc
    base = base.order_by(order_func(col))

    # total
    total = (await db.execute(count_q)).scalar_one()

    # page
    base = base.limit(limit).offset(offset)
    items = list((await db.execute(base)).scalars())

    return items, total


async def create_character(
    db: AsyncSession,
    *,
    name: str,
    clazz: str,
    level: int = 1,
) -> Character:
    """
    캐릭터 생성 (이름 중복 검사 포함)
    """
    q = select(func.count()).select_from(Character).where(Character.name == name)
    exists = (await db.execute(q)).scalar_one()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Character name already exists",
        )

    obj = Character(name=name, clazz=clazz, level=level)
    db.add(obj)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Character name already exists",
        )
    await db.refresh(obj)
    return obj
