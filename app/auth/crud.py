from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.models import User, AuthProvider


class UserCRUD:

    @staticmethod
    async def get_by_email_or_provider(
        session: AsyncSession,
        email: str | None,
        provider_id: str,
    ) -> User | None:
        stmt = select(User).where(
            (User.email == email) | (User.provider_id == provider_id)
        )
        return await session.scalar(stmt)

    @staticmethod
    async def create_oauth_user(
        session: AsyncSession,
        *,
        username: str,
        email: str | None,
        provider_id: str,
        provider: AuthProvider,
        full_name: str | None,
        avatar_url: str | None,
    ) -> User:
        user = User(
            username=username,
            email=email,
            provider_id=provider_id,
            auth_provider=provider,
            full_name=full_name,
            avatar_url=avatar_url,
            verified=True,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    
    @staticmethod
    async def get_users(session: AsyncSession) -> list[User]:
        stmt = select(User)
        result = await session.execute(stmt)
        return result.scalars().all()

