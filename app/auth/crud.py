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
    async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
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
    
    @staticmethod
    async def update_balance(
        session: AsyncSession,
        user_id: int,
        amount_change: int
    ) -> User:
        """
        Изменяет баланс пользователя
        amount_change: положительное число для пополнения, отрицательное для списания
        """
        # Используем with_for_update() для блокировки строки (race condition protection)
        stmt = select(User).where(User.id == user_id).with_for_update()
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        new_balance = user.balance + amount_change
        if new_balance < 0:
            raise ValueError(f"Insufficient balance. Current: {user.balance}, change: {amount_change}")
        
        user.balance = new_balance
        await session.flush()
        return user

