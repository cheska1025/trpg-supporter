from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context  # type: ignore[attr-defined]
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from backend.app.core.config import settings
from backend.app.db.base import Base

# --- 앱 설정/메타데이터 불러오기 ------------------------------------------

# Alembic Config 객체: ini 파일 값 접근 가능
config = context.config

# Logging 설정 (alembic.ini 기준)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 마이그 타겟 메타데이터: autogenerate에서 모델 반영
target_metadata = Base.metadata

# DB URL: 앱 settings에서 가져오기
DB_URL = settings.DB_URL


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = DB_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """실제 마이그 실행 함수"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable: AsyncEngine = create_async_engine(DB_URL, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations() -> None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_migrations_online())


run_migrations()
