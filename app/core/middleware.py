from fastapi import Request
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from app.config import settings

ALGORITHM = "HS256"

PUBLIC_PATHS = (
    "/api/auth/yandex/login",
    "/api/auth/yandex/callback",
    "/api/auth/vk/login",
    "/api/auth/vk/callback",
    "/api/auth/refresh",
    "/api/docs",
    "/api/openapi.json",
    "/api/health",
)

async def auth_middleware(request: Request, call_next):
    # Пропускаем публичные пути
    if any(request.url.path.startswith(path) for path in PUBLIC_PATHS):
        return await call_next(request)

    token = request.cookies.get("access_token")
    if not token:
        return JSONResponse(
            content={"detail": "Not authenticated"},
            status_code=401
        )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[ALGORITHM],
        )

        if payload.get("type") != "access":
            raise JWTError()

        request.state.user_id = int(payload["sub"])

    except JWTError:
        return JSONResponse(
            content={"detail": "Invalid or expired token"},
            status_code=401
        )

    return await call_next(request)