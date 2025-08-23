from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.entities import Session as Session


class SessionStateService:
    """게임 세션의 상태를 관리하는 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_session(self, session_id: int) -> Optional[Session]:
        """특정 ID의 세션 조회"""
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        return result.scalar_one_or_none()

    async def set_state(self, session_id: int, state: str) -> Session:
        """세션 상태 변경"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.state = state
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def reset_state(self, session_id: int) -> Session:
        """세션 상태 초기화"""
        return await self.set_state(session_id, "INIT")
