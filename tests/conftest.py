import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.testclient import TestClient

from app.auth.crud import UserCRUD
from app.auth.models import AuthProvider, User  # noqa: F401 — metadata
from app.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.notifications.models import Notification  # noqa: F401 — metadata


@pytest.fixture
def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async def init():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init())
    yield engine

    async def dispose():
        await engine.dispose()

    asyncio.run(dispose())


@pytest.fixture
def session_factory(test_engine):
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
def client(session_factory, monkeypatch):
    monkeypatch.setattr(settings, "NOTIFICATIONS_INTERNAL_KEY", "test-internal-key")

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


async def create_oauth_user(session_factory):
    async with session_factory() as session:
        return await UserCRUD.create_oauth_user(
            session,
            username="testuser",
            email="testuser@example.com",
            provider_id="oauth-test-1",
            provider=AuthProvider.YANDEX,
            full_name="Test User",
            avatar_url=None,
        )


@pytest.fixture
def user(client, session_factory):
    return asyncio.run(create_oauth_user(session_factory))

