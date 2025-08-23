from __future__ import annotations

import os
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

# 기본 SQLite 파일 DB. 환경변수로 재정의 가능
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")

# SQLite에서는 커넥션 풀 이슈를 피하기 위해 NullPool 사용 (테스트 안정성)
engine = create_async_engine(DATABASE_URL, echo=False, poolclass=NullPool)

# 세션 팩토리
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

# 하위 호환: 예전 코드/테스트가 기대하는 이름
AsyncSessionLocal = SessionLocal  # alias for backward compatibility


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI Depends 용 비동기 세션 의존성."""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


__all__ = ["engine", "SessionLocal", "AsyncSessionLocal", "get_session"]
