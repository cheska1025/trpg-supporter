import os

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# DATABASE_URL 환경변수에서 읽기 (없으면 기본값으로 SQLite 파일 사용)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

# SQLAlchemy AsyncEngine 생성
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,  # True로 하면 SQL 로그 출력
    future=True,  # SQLAlchemy 2.0 스타일
)
