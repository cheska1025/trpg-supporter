import pytest
from httpx import AsyncClient

from backend.app.main import app


@pytest.mark.asyncio
async def test_healthz():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/api/v1/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
