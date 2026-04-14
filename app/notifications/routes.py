"""
Уведомления: REST и WebSocket.

**Объект уведомления:** id, user_id, title, source, payload (object | null),
created_at, read, idempotency_key (string | null).

**GET /api/notifications** — query: limit (1–100, default 20), cursor (id последней записи
с предыдущей страницы), unread_only (bool). Ответ: JSON-массив уведомлений.
Заголовок `X-Next-Cursor` — id для следующей страницы, если есть.

**POST /api/notifications** — внутренний вызов, заголовок `X-Internal-Key`.

**PATCH /api/notifications/{id}** — тело `{ "read": true }`.

**WebSocket /api/notifications/ws** — после подключения первое сообщение:
`{ "type": "snapshot", "items": [ ... ] }` (непрочитанные), далее `notification` / `notification_updated`.
"""

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketDisconnect

from app.config import settings
from app.db.session import get_db
from app.notifications.crud import NotificationCRUD
from app.notifications.hub import hub
from app.notifications.schemas import (
    NotificationCreateInternal,
    NotificationOut,
    NotificationPatch,
)
from app.notifications.service import (
    create_notification,
    notification_to_out,
    patch_notification_read,
)
from app.notifications.ws_auth import resolve_ws_user
from app.auth.models import User
from app.users.dependency import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


async def require_notifications_internal_key(
    x_internal_key: Annotated[Optional[str], Header(alias="X-Internal-Key")] = None,
) -> None:
    if not settings.NOTIFICATIONS_INTERNAL_KEY:
        raise HTTPException(status_code=503, detail="Internal notifications API not configured")
    if not x_internal_key or x_internal_key != settings.NOTIFICATIONS_INTERNAL_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get(
    "",
    response_model=List[NotificationOut],
    summary="Список уведомлений текущего пользователя",
)
async def list_notifications(
    response: Response,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[int] = Query(None, description="ID последней записи предыдущей страницы (id < cursor)"),
    unread_only: bool = Query(False),
):
    rows, next_cursor = await NotificationCRUD.list_for_user(
        session,
        user_id=user.id,
        unread_only=unread_only,
        limit=limit,
        cursor=cursor,
    )
    if next_cursor is not None:
        response.headers["X-Next-Cursor"] = str(next_cursor)
    return [notification_to_out(n) for n in rows]


@router.post(
    "",
    response_model=NotificationOut,
    summary="Создать уведомление (внутренний вызов)",
    dependencies=[Depends(require_notifications_internal_key)],
)
async def create_notification_endpoint(
    data: NotificationCreateInternal,
    session: AsyncSession = Depends(get_db),
):
    out, _ = await create_notification(session, data)
    return out


@router.patch("/{notification_id}", response_model=NotificationOut)
async def patch_notification(
    notification_id: int,
    patch: NotificationPatch,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if patch.read is None:
        raise HTTPException(status_code=400, detail="No fields to update")
    out = await patch_notification_read(
        session,
        notification_id=notification_id,
        user_id=user.id,
        read=patch.read,
    )
    if not out:
        raise HTTPException(status_code=404, detail="Notification not found")
    return out


@router.websocket("/ws")
async def notifications_websocket(
    websocket: WebSocket,
    session: AsyncSession = Depends(get_db),
):
    user = await resolve_ws_user(websocket, session)
    if not user:
        await websocket.close(code=4401, reason="Unauthorized")
        return

    await websocket.accept()
    hub.register(user.id, websocket)

    unread = await NotificationCRUD.list_unread_for_user(session, user_id=user.id)
    snapshot_items = [notification_to_out(n).model_dump(mode="json") for n in unread]
    try:
        await websocket.send_json({"type": "snapshot", "items": snapshot_items})
    except Exception:
        hub.unregister(user.id, websocket)
        return

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        hub.unregister(user.id, websocket)
