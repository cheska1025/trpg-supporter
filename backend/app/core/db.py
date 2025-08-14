from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings

# 단일 설정 진입점: ~/.trpg/data.db (기본) 또는 환경변수 DATABASE_URL
engine = create_engine(settings.db_url, future=True, echo=False)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@contextmanager
def session_scope() -> Session:
    """트랜잭션/세션 헬퍼 (commit/rollback 보장)"""
    s: Session = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
