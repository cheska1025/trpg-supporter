from __future__ import annotations

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.config import settings

# DB URL 예: "sqlite+aiosqlite:///./dev.db"
DB_URL: str | URL = settings.DB_URL

engine = create_async_engine(DB_URL, future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
