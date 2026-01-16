from fastapi import Request
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from app.config import settings

ALGORITHM = "HS256"

PUBLIC_PATHS = (
    "/api/auth/yandex",
    "/api/auth/refresh",
    "/api/docs",
    "/api/openapi.json",
    "/api/auth/check",
)

#PUBLIC_PATHS_PROD = (
    #"/api/auth/yandex",
    #"/api/auth/refresh",
#)


async def auth_middleware(request: Request, call_next):
    if request.url.path.startswith(PUBLIC_PATHS):
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


async def csrf_middleware(request: Request, call_next):
    if (
        request.method in ("GET", "HEAD", "OPTIONS")
        or request.url.path.startswith(PUBLIC_PATHS)
    ):
        return await call_next(request)

    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")

    if not csrf_cookie or not csrf_header:
        return JSONResponse(
        content={"detail": "CSRF token missing"},
        status_code=403
        )

    if csrf_cookie != csrf_header:
        return JSONResponse(
        content={"detail": "CSRF token missing"},
        status_code=403
        )   

    return await call_next(request)


