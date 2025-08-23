from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings

# 단일 설정 진입점: ~/.trpg/data.db (기본) 또는 env DATABASE_URL
engine = create_engine(settings.db_url, future=True, echo=False)

# 세션팩토리
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


@contextmanager
def session_scope() -> Iterator[Session]:
    """
    SQLAlchemy 세션 컨텍스트 매니저.
    with session_scope() as s:
        ... DB 작업 ...
    """
    s: Session = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
