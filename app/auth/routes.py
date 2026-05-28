from fastapi import APIRouter, Depends, Request, HTTPException
from jose import jwt, JWTError
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.config import settings
from app.auth.service import AuthService
from app.core.security import create_jwt_pair, set_auth_cookies, clear_auth_cookies
from app.auth.crud import UserCRUD

router = APIRouter(prefix="/yandex", tags=["OAuth"])
vk_router = APIRouter(prefix="/vk", tags=["OAuth"])
session_router = APIRouter(prefix="", tags=["Auth"])

ALGORITHM = "HS256"


def _append_cookies(response, cookies: dict) -> None:
    for cookie in cookies["Set-Cookie"]:
        response.headers.append("Set-Cookie", cookie)


@router.get("/login")
async def yandex_login():
    url = (
        "https://oauth.yandex.ru/authorize"
        "?response_type=code"
        f"&client_id={settings.YANDEX_CLIENT_ID}"
        f"&redirect_uri={settings.YANDEX_REDIRECT_URI}"
    )
    return RedirectResponse(url)


@vk_router.get("/login")
async def vk_login():
    url = (
        "https://id.vk.com/authorize"
        "?response_type=code"
        f"&client_id={settings.VK_APP_ID}"
        f"&redirect_uri={settings.VK_CALLBACK}"
        "&scope=email"
    )
    return RedirectResponse(url)


@vk_router.get("/callback")
async def vk_callback(
    session: AsyncSession = Depends(get_db),
    code: str | None = None,
    error: str | None = None,
):
    if error:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}?error={error}"
        )

    if not code:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}?error=code_missing"
        )

    result = await AuthService.vk_callback(
        session=session,
        code=code,
    )

    response = RedirectResponse(settings.FRONTEND_URL)
    _append_cookies(response, result["cookies"])
    return response


@router.get("/callback")
async def yandex_callback(
    session: AsyncSession = Depends(get_db),
    code: str | None = None,
    error: str | None = None,
):
    if error:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}?error={error}"
        )

    if not code:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}?error=code_missing"
        )

    result = await AuthService.yandex_callback(
        session=session,
        code=code,
    )

    response = RedirectResponse(settings.FRONTEND_URL)
    _append_cookies(response, result["cookies"])
    return response


@router.post("/refresh")
@session_router.post("/refresh")
async def refresh_token(request: Request, session: AsyncSession = Depends(get_db)):
    refresh = request.cookies.get("refresh_token")

    if not refresh:
        raise HTTPException(401, "Refresh token missing")

    try:
        payload = jwt.decode(
            refresh,
            settings.JWT_SECRET,
            algorithms=[ALGORITHM],
        )

        if payload.get("type") != "refresh":
            raise JWTError()

        user_id = int(payload["sub"])

    except JWTError:
        raise HTTPException(401, "Invalid refresh token")

    user = await UserCRUD.get_by_id(session, user_id)

    if not user:
        raise HTTPException(401, "User not found")

    access, new_refresh = create_jwt_pair(user)
    response = JSONResponse({"success": True})
    _append_cookies(response, set_auth_cookies(access, new_refresh))
    return response


@session_router.post("/logout")
@session_router.get("/logout")
async def logout():
    response = JSONResponse({"ok": True})
    _append_cookies(response, clear_auth_cookies())
    return response


@router.get("/check")
async def check_users(db: AsyncSession = Depends(get_db)):
    result = await UserCRUD.get_users(db)
    return result
