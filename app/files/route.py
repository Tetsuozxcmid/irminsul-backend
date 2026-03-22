# app/files/routes.py

import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.records.crud import FileCRUD, PurchaseCRUD
from app.records.models import Record
from app.users.dependency import get_current_user
from app.auth.models import User

router = APIRouter(prefix="/api/files", tags=["Files"])


@router.get("/{file_id}")
async def download_file(
    file_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Скачивание файла (только для купивших запись)
    
    - Проверяет, купил ли пользователь запись
    - Если купил или является автором - отдает файл
    - Иначе возвращает ошибку доступа
    """
    # 1. Получаем информацию о файле
    file = await FileCRUD.get_by_id(session, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # 2. Находим запись, к которой привязан файл
    stmt = select(Record).where(Record.files.any(id=file_id))
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=404, 
            detail="Record not found for this file"
        )
    
    # 3. Проверяем права доступа
    # Автор всегда может скачать
    if user.id == record.author_id:
        pass  # Разрешаем
    else:
        # Проверяем, купил ли пользователь запись
        has_purchased = await PurchaseCRUD.has_purchased(
            session, 
            user.id, 
            record.id
        )
        if not has_purchased:
            raise HTTPException(
                status_code=403, 
                detail="You need to purchase this record to download files"
            )
    
    # 4. Проверяем существование файла на диске
    if not os.path.exists(file.file_path):
        raise HTTPException(
            status_code=404, 
            detail="File not found on server"
        )
    
    # 5. Возвращаем файл
    return FileResponse(
        path=file.file_path,
        filename=file.original_filename,
        media_type=file.mime_type
    )