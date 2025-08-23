import os
from logging.config import fileConfig

from alembic import context

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ← 여기가 중요: 환경변수 DATABASE_URL 사용
db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
config.set_main_option("sqlalchemy.url", db_url)

# target_metadata = Base.metadata  등등…
