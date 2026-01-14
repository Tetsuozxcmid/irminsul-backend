import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.auth.crud import UserCRUD
from app.auth.models import AuthProvider
from app.core.security import create_jwt_pair, set_auth_cookies


class YandexOAuthService:

    @staticmethod
    async def get_yandex_token(code: str) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth.yandex.ru/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.YANDEX_CLIENT_ID,
                    "client_secret": settings.YANDEX_CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            return resp.json()["access_token"]

    @staticmethod
    async def get_yandex_user(access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://login.yandex.ru/info",
                headers={"Authorization": f"OAuth {access_token}"},
            )
            resp.raise_for_status()
            return resp.json()


class AuthService:

    @staticmethod
    async def yandex_callback(
        *,
        session: AsyncSession,
        code: str,
    ):
        token = await YandexOAuthService.get_yandex_token(code)
        ya = await YandexOAuthService.get_yandex_user(token)

        email = ya.get("default_email")
        provider_id = ya["id"]

        user = await UserCRUD.get_by_email_or_provider(
            session=session,
            email=email,
            provider_id=provider_id,
        )

        if not user:
            user = await UserCRUD.create_oauth_user(
                session=session,
                username=ya["login"],
                email=email,
                provider_id=provider_id,
                provider=AuthProvider.YANDEX,
                full_name=ya.get("real_name"),
                avatar_url=(
                    f"https://avatars.yandex.net/get-yapic/"
                    f"{ya.get('default_avatar_id')}/islands-200"
                ),
            )

        access, refresh = create_jwt_pair(user)

        return {
            "type": "login",
            "cookies": set_auth_cookies(access, refresh),
            "payload": {
                "success": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                },
            },
        }

