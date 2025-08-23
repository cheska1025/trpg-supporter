from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from backend.app.db.session import engine
from backend.app.main import app


# 각 테스트 시작 전에 characters 테이블 비우기
@pytest_asyncio.fixture(autouse=True)
async def clean_characters_table():
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM characters"))
        # 필요 시 AUTOINCREMENT 초기화:
        # await conn.execute(text("DELETE FROM sqlite_sequence WHERE name='characters'"))
    yield


@pytest.mark.asyncio
async def test_characters_crud_smoke(tmp_path, monkeypatch):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # list: empty
        r = await ac.get("/api/v1/characters")
        assert r.status_code == 200
        assert r.json() == []

        # create → 201
        r = await ac.post(
            "/api/v1/characters",
            json={"name": "Alice", "clazz": "Wizard", "level": 2},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Alice"
        assert data["clazz"] == "Wizard"
        assert data["level"] == 2
        char_id = data["id"]

        # list: one
        r = await ac.get("/api/v1/characters")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        assert items[0]["id"] == char_id


@pytest.mark.asyncio
async def test_characters_validation_and_defaults():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # invalid: missing name
        r = await ac.post("/api/v1/characters", json={"clazz": "Warrior", "level": 1})
        assert r.status_code == 422

        # invalid: level < 1
        r = await ac.post(
            "/api/v1/characters",
            json={"name": "Bob", "clazz": "Warrior", "level": 0},
        )
        assert r.status_code == 422

        # valid: default level (=1)
        r = await ac.post(
            "/api/v1/characters",
            json={"name": "Charlie", "clazz": "Cleric"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["level"] == 1


@pytest.mark.asyncio
async def test_characters_conflict_on_duplicate_name():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/api/v1/characters",
            json={"name": "DupName", "clazz": "Rogue"},
        )
        assert r.status_code == 201

        # duplicate → 409
        r = await ac.post(
            "/api/v1/characters",
            json={"name": "DupName", "clazz": "Rogue"},
        )
        assert r.status_code == 409
        assert r.json()["detail"] == "Character name already exists"


@pytest.mark.asyncio
async def test_characters_list_filter_paging_and_sort(
    clean_characters_table,
):  # autouse fixture 이미 존재
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # seed
        for name, lvl in [("Alice", 2), ("Bob", 1), ("Charlie", 3)]:
            r = await ac.post("/api/v1/characters", json={"name": name, "clazz": "X", "level": lvl})
            assert r.status_code == 201

        # filter: name=bo (case-insensitive)
        r = await ac.get("/api/v1/characters", params={"name": "bo"})
        assert r.status_code == 200
        assert [it["name"] for it in r.json()] == ["Bob"]
        assert r.headers.get("X-Total-Count") == "1"

        # order_by=level desc, limit/offset
        r = await ac.get("/api/v1/characters", params={"order_by": "level", "order": "desc"})
        assert [it["name"] for it in r.json()] == ["Charlie", "Alice", "Bob"]

        r = await ac.get(
            "/api/v1/characters",
            params={"order_by": "level", "order": "desc", "limit": 2},
        )
        assert [it["name"] for it in r.json()] == ["Charlie", "Alice"]
        assert r.headers.get("X-Total-Count") == "3"

        r = await ac.get(
            "/api/v1/characters",
            params={"order_by": "level", "order": "desc", "limit": 2, "offset": 2},
        )
        assert [it["name"] for it in r.json()] == ["Bob"]
