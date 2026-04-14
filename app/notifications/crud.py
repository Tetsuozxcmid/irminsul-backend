from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import Notification


class NotificationCRUD:
    @staticmethod
    async def get_by_id_for_user(
        session: AsyncSession, notification_id: int, user_id: int
    ) -> Optional[Notification]:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        return await session.scalar(stmt)

    @staticmethod
    async def get_by_idempotency(
        session: AsyncSession, user_id: int, idempotency_key: str
    ) -> Optional[Notification]:
        stmt = select(Notification).where(
            Notification.user_id == user_id,
            Notification.idempotency_key == idempotency_key,
        )
        return await session.scalar(stmt)

    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        user_id: int,
        title: str,
        source: str,
        payload: Optional[dict],
        idempotency_key: Optional[str],
    ) -> Notification:
        n = Notification(
            user_id=user_id,
            title=title,
            source=source,
            payload=payload,
            read=False,
            idempotency_key=idempotency_key,
        )
        session.add(n)
        await session.flush()
        return n

    @staticmethod
    async def list_for_user(
        session: AsyncSession,
        *,
        user_id: int,
        unread_only: bool,
        limit: int,
        cursor: Optional[int],
    ) -> Tuple[list[Notification], Optional[int]]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.read.is_(False))
        if cursor is not None:
            stmt = stmt.where(Notification.id < cursor)
        stmt = (
            stmt.order_by(Notification.id.desc())
            .limit(limit + 1)
        )
        result = await session.execute(stmt)
        rows = list(result.scalars().all())
        next_cursor: Optional[int] = None
        if len(rows) > limit:
            next_cursor = rows[limit - 1].id
            rows = rows[:limit]
        return rows, next_cursor

    @staticmethod
    async def list_unread_for_user(
        session: AsyncSession,
        *,
        user_id: int,
        limit: int = 500,
    ) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read.is_(False),
            )
            .order_by(Notification.id.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
