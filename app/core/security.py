from datetime import datetime, timedelta
from jose import jwt
from app.config import settings

ALGORITHM = "HS256"

ACCESS_TOKEN_MAX_AGE = 15 * 60
REFRESH_TOKEN_MAX_AGE = 30 * 24 * 60 * 60


def create_jwt_pair(user):
    now = datetime.utcnow()

    access_payload = {
        "sub": str(user.id),
        "type": "access",
        "exp": now + timedelta(minutes=15),
    }

    refresh_payload = {
        "sub": str(user.id),
        "type": "refresh",
        "exp": now + timedelta(days=30),
    }

    access = jwt.encode(
        access_payload,
        settings.JWT_SECRET,
        algorithm=ALGORITHM,
    )

    refresh = jwt.encode(
        refresh_payload,
        settings.JWT_SECRET,
        algorithm=ALGORITHM,
    )

    return access, refresh


def _cookie_pair(name: str, value: str, max_age: int) -> str:
    parts = [
        f"{name}={value}",
        "Path=/",
        "HttpOnly",
        f"SameSite={settings.cookie_samesite}",
        f"Max-Age={max_age}",
    ]

    if settings.COOKIE_SECURE:
        parts.append("Secure")

    domain = settings.COOKIE_DOMAIN.strip()
    if domain:
        parts.append(f"Domain={domain}")

    return "; ".join(parts)


def _clear_cookie(name: str) -> str:
    parts = [
        f"{name}=",
        "Path=/",
        "HttpOnly",
        f"SameSite={settings.cookie_samesite}",
        "Max-Age=0",
    ]

    if settings.COOKIE_SECURE:
        parts.append("Secure")

    domain = settings.COOKIE_DOMAIN.strip()
    if domain:
        parts.append(f"Domain={domain}")

    return "; ".join(parts)


def set_auth_cookies(access: str, refresh: str) -> dict:
    return {
        "Set-Cookie": [
            _cookie_pair("access_token", access, ACCESS_TOKEN_MAX_AGE),
            _cookie_pair("refresh_token", refresh, REFRESH_TOKEN_MAX_AGE),
        ]
    }


def clear_auth_cookies() -> dict:
    return {
        "Set-Cookie": [
            _clear_cookie("access_token"),
            _clear_cookie("refresh_token"),
        ]
    }
