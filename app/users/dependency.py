from fastapi import Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.db.session import get_db
from app.auth.crud import UserCRUD
from app.auth.models import User
from app.config import settings

async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> User:
    # 1. Пробуем получить токен из куки
    token = request.cookies.get("access_token")
    
    if not token:
        # 2. Если нет в куке, пробуем из Authorization заголовка
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(401, "Not authenticated")
    
    # 3. Валидируем токен
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )
        
        # Проверяем тип токена
        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")
            
        user_id = int(payload.get("sub"))
        
    except JWTError:
        raise HTTPException(401, "Invalid token")
    
    # 4. Получаем пользователя из БД
    user = await UserCRUD.get_by_id(session, user_id)
    
    if not user:
        raise HTTPException(401, "User not found")
    
    if not user.is_active:
        raise HTTPException(403, "User is inactive")
    
    return user