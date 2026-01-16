from datetime import datetime, timedelta
from jose import jwt
from app.config import settings
import secrets

ALGORITHM = "HS256"


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


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


def set_auth_cookies(access: str, refresh: str, csrf: str | None = None) -> dict:
   
    secure = settings.APP_ENV == "prod"
    http_only = settings.APP_ENV == "prod"  

    access_cookie = f"access_token={access}; Path=/; SameSite=Lax"
    refresh_cookie = f"refresh_token={refresh}; Path=/; SameSite=Lax"

    # CSRF токен
    cookies = []
    if csrf:
        csrf_cookie = f"csrf_token={csrf}; Path=/; SameSite=Lax"
        if secure:
            csrf_cookie += "; Secure"
        cookies.append(csrf_cookie)


    if http_only:
        access_cookie += "; HttpOnly"
        refresh_cookie += "; HttpOnly"


    if secure:
        access_cookie += "; Secure"
        refresh_cookie += "; Secure"

    cookies.extend([access_cookie, refresh_cookie])

    return {"Set-Cookie": cookies}

