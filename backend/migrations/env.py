from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# ----- Alembic Config -----
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ----- DATABASE_URL -----
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# ----- import Base (try common paths) -----
Base = None
for path in (
    "backend.app.db",  # e.g. Base in backend/app/db.py
    "backend.db",  # e.g. Base in backend/db.py
    "backend.app.models",  # e.g. Base in backend/app/models/__init__.py
    "backend.models",  # e.g. Base in backend/models/__init__.py
):
    try:
        module = __import__(path, fromlist=["Base"])
        Base = getattr(module, "Base")
        break
    except Exception:
        pass

if Base is None:
    raise RuntimeError(
        "Could not import SQLAlchemy Base. "
        "Set the correct import in backend/migrations/env.py (target_metadata)."
    )

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio

    asyncio.run(run_migrations_online())
