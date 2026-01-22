from fastapi import Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.auth.crud import UserCRUD
from app.auth.models import User


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> User:
    user_id = getattr(request.state, "user_id", None)

    if not user_id:
        raise HTTPException(401, "Not authenticated")

    user = await UserCRUD.get_by_id(session, user_id)

    if not user:
        raise HTTPException(401, "User not found")

    if not user.is_active:
        raise HTTPException(403, "User is inactive")

    return user
