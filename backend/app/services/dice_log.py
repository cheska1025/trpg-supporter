from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.entities import DiceLog as DiceLog


class DiceLogService:
    """주사위 로그 관리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_log(
        self, session_id: int, roll: str, result: int, roller: Optional[str] = None
    ) -> DiceLog:
        """주사위 굴림 로그 추가"""
        log = DiceLog(session_id=session_id, roll=roll, result=result, roller=roller)
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_logs(self, session_id: int) -> List[DiceLog]:
        """특정 세션의 모든 주사위 로그 조회"""
        result = await self.db.execute(
            select(DiceLog).where(DiceLog.session_id == session_id).order_by(DiceLog.id)
        )
        return result.scalars().all()

    async def get_log(self, log_id: int) -> Optional[DiceLog]:
        """특정 로그 조회"""
        result = await self.db.execute(select(DiceLog).where(DiceLog.id == log_id))
        return result.scalar_one_or_none()
