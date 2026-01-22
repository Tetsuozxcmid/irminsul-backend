from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.models import User


class UserProfileCRUD:

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        user_id: int,
    ) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return await session.scalar(stmt)


    @staticmethod
    async def update_profile(
        session: AsyncSession,
        user: User,
        *,
        username: str | None = None,
        full_name: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        if username is not None:
            user.username = username

        if full_name is not None:
            user.full_name = full_name

        if avatar_url is not None:
            user.avatar_url = avatar_url

        await session.commit()
        await session.refresh(user)
        return user
