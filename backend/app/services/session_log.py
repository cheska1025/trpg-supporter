from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.entities import LogEntry as LogEntry
from backend.app.models.entities import Session as Session


class SessionLogService:
    """세션 로그를 관리하는 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_log(
        self, session_id: int, message: str, author: Optional[str] = None
    ) -> LogEntry:
        """세션 로그 추가"""
        entry = LogEntry(session_id=session_id, message=message, author=author)
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def get_logs(self, session_id: int) -> List[LogEntry]:
        """특정 세션의 로그 목록 조회"""
        result = await self.db.execute(
            select(LogEntry).where(LogEntry.session_id == session_id).order_by(LogEntry.id)
        )
        return result.scalars().all()

    async def get_log(self, log_id: int) -> Optional[LogEntry]:
        """특정 로그 조회"""
        result = await self.db.execute(select(LogEntry).where(LogEntry.id == log_id))
        return result.scalar_one_or_none()
