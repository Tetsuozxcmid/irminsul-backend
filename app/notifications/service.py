from typing import Optional, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.crud import NotificationCRUD
from app.notifications.hub import hub
from app.notifications.models import Notification
from app.notifications.schemas import NotificationCreateInternal, NotificationOut


def notification_to_out(n: Notification) -> NotificationOut:
    return NotificationOut.model_validate(n)


async def create_notification(
    session: AsyncSession, data: NotificationCreateInternal
) -> Tuple[NotificationOut, bool]:
    """
    Создаёт уведомление. При idempotency_key возвращает существующее, created=False.
    После commit рассылает подключённым клиентам только при новой записи.
    """
    if data.idempotency_key:
        existing = await NotificationCRUD.get_by_idempotency(
            session, data.user_id, data.idempotency_key
        )
        if existing:
            await session.commit()
            return notification_to_out(existing), False

    try:
        n = await NotificationCRUD.create(
            session,
            user_id=data.user_id,
            title=data.title,
            source=data.source,
            payload=data.payload,
            idempotency_key=data.idempotency_key,
        )
        await session.commit()
        await session.refresh(n)
    except IntegrityError:
        await session.rollback()
        if data.idempotency_key:
            existing = await NotificationCRUD.get_by_idempotency(
                session, data.user_id, data.idempotency_key
            )
            if existing:
                return notification_to_out(existing), False
        raise
    out = notification_to_out(n)
    await hub.send_json_to_user(
        data.user_id,
        {
            "type": "notification",
            "item": out.model_dump(mode="json"),
        },
    )
    return out, True


async def patch_notification_read(
    session: AsyncSession,
    *,
    notification_id: int,
    user_id: int,
    read: bool,
) -> Optional[NotificationOut]:
    n = await NotificationCRUD.get_by_id_for_user(
        session, notification_id, user_id
    )
    if not n:
        return None
    n.read = read
    await session.commit()
    await session.refresh(n)
    out = notification_to_out(n)
    await hub.send_json_to_user(
        user_id,
        {
            "type": "notification_updated",
            "item": out.model_dump(mode="json"),
        },
    )
    return out
