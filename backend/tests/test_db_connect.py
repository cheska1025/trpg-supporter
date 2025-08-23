import pytest
from sqlalchemy import text

from backend.app.db.session import AsyncSessionLocal


@pytest.mark.asyncio
async def test_db_connect_and_select_one():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        val = result.scalar_one()
    assert val == 1
