from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.crud import UserProfileCRUD
from app.users.schemas import UserProfileUpdate
from app.auth.models import User


class UserProfileService:

    @staticmethod
    async def get_profile(
        *,
        session: AsyncSession,
        user: User,
    ) -> User:
        db_user = await UserProfileCRUD.get_by_id(
            session=session,
            user_id=user.id,
        )

        if not db_user:
            raise HTTPException(404, "User not found")

        return db_user

    @staticmethod
    async def update_profile(
        *,
        session: AsyncSession,
        user: User,
        data: UserProfileUpdate,
    ) -> User:
        return await UserProfileCRUD.update_profile(
            session=session,
            user=user,
            username=data.username,
            full_name=data.full_name,
            avatar_url=data.avatar_url,
        )
