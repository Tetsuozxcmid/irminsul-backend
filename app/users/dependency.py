from fastapi import Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.db.session import get_db
from app.auth.crud import UserCRUD
from app.auth.models import User
from app.config import settings


def _get_token_from_request(request: Request) -> str | None:
    token = request.cookies.get("access_token")
    if token:
        return token

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]

    return None


async def _resolve_user_from_token(
    token: str,
    session: AsyncSession,
) -> User | None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
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


async def get_optional_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> User | None:
    token = _get_token_from_request(request)
    if not token:
        return None
    return await _resolve_user_from_token(token, session)


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> User:
    token = _get_token_from_request(request)
    if not token:
        raise HTTPException(401, "Not authenticated")

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
        )

        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")

        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(401, "Invalid token")

    user = await UserCRUD.get_by_id(session, user_id)

    if not user:
        raise HTTPException(401, "User not found")

    if not user.is_active:
        raise HTTPException(403, "User is inactive")

    return user
