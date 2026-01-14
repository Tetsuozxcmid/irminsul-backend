from datetime import datetime, timedelta
from jose import jwt
from app.config import settings


ALGORITHM = "HS256"


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


def set_auth_cookies(access: str, refresh: str) -> dict:
    secure = settings.APP_ENV == "prod"

    cookie = (
        f"access_token={access}; Path=/; HttpOnly; SameSite=Lax"
    )

    cookie += (
        f", refresh_token={refresh}; Path=/; HttpOnly; SameSite=Lax"
    )

    if secure:
        cookie += "; Secure"

    return {"Set-Cookie": cookie}