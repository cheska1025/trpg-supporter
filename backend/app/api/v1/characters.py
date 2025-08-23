from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_session
from backend.app.schemas import CharacterIn, CharacterOut, ErrorResponse
from backend.app.services.characters import create_character, list_characters

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get(
    "",
    response_model=list[CharacterOut],
    responses={
        200: {
            "description": "Characters list",
            "content": {
                "application/json": {
                    "examples": {
                        "empty": {"value": []},
                        "some": {
                            "value": [{"id": 1, "name": "Alice", "clazz": "Wizard", "level": 2}]
                        },
                    }
                }
            },
        }
    },
    summary="List characters",
)
async def api_list_characters(
    response: Response,
    name: str | None = Query(None, min_length=1, description="Partial match, case-insensitive"),
    limit: int = Query(20, ge=1, le=100, description="Page size (1~100)"),
    offset: int = Query(0, ge=0, description="Page offset"),
    order_by: str = Query("id", pattern="^(id|name|level|clazz)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_session),
) -> list[CharacterOut]:
    items, total = await list_characters(
        db,
        name=name,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order=order,
    )
    # 총개수 헤더로 전달
    response.headers["X-Total-Count"] = str(total)
    return [CharacterOut.model_validate(i) for i in items]


@router.post(
    "",
    response_model=CharacterOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Character created",
            "content": {
                "application/json": {
                    "examples": {
                        "created": {
                            "value": {"id": 1, "name": "Alice", "clazz": "Wizard", "level": 2}
                        }
                    }
                }
            },
        },
        409: {
            "model": ErrorResponse,
            "description": "Duplicate name",
            "content": {
                "application/json": {"example": {"detail": "Character name already exists"}}
            },
        },
        422: {"description": "Validation error"},
    },
    summary="Create character",
)
async def api_create_character(
    payload: CharacterIn,
    db: AsyncSession = Depends(get_session),
) -> CharacterOut:
    obj = await create_character(db, name=payload.name, clazz=payload.clazz, level=payload.level)
    return CharacterOut.model_validate(obj)
