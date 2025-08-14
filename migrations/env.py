from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.app.core.config import settings
from backend.app.models import Base  # target_metadata

config = context.config

config.set_main_option("sqlalchemy.url", settings.db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Offline 모드: 연결 없이 SQL 생성"""
    url = settings.db_url
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online 모드: DB 연결 후 적용"""
    connectable = engine_from_config(
        {"sqlalchemy.url": settings.db_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
