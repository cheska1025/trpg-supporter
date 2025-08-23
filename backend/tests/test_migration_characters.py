import pytest
from sqlalchemy import inspect

from backend.app.db.session import engine


@pytest.mark.asyncio
async def test_characters_table_exists_and_columns():
    async with engine.begin() as conn:

        def _check(sync_conn):
            insp = inspect(sync_conn)
            assert "characters" in insp.get_table_names()
            cols = {c["name"] for c in insp.get_columns("characters")}
            # 기대 컬럼
            assert {"id", "name", "clazz", "level"} <= cols

        await conn.run_sync(_check)
