from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import UserCRUD
from app.auth.models import User
from app.config import settings
from fastapi import WebSocket

ALGORITHM = "HS256"


async def resolve_ws_user(
    websocket: WebSocket,
    session: AsyncSession,
) -> User | None:
    """Читает JWT из cookie или query `access_token` (до accept)."""
    token = websocket.cookies.get("access_token")
    if not token:
        token = websocket.query_params.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[ALGORITHM],
        )
        if payload.get("type") != "access":
            return None
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None

    user = await UserCRUD.get_by_id(session, user_id)
    if not user or not user.is_active:
        return None
    return user
