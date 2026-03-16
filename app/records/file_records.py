import os
import shutil
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException
from typing import List, Tuple
import uuid
import mimetypes

class FileService:
    # Директории для хранения файлов
    UPLOAD_DIR = Path("uploads")
    IMAGES_DIR = UPLOAD_DIR / "images"
    FILES_DIR = UPLOAD_DIR / "files"
    
    # Допустимые типы файлов
    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    ALLOWED_FILE_TYPES = {
        "application/pdf", 
        "application/msword", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
        "application/x-rar-compressed",
        "text/plain"
    }
    
    # Максимальный размер файла (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    @classmethod
    async def ensure_directories(cls):
        """Создает необходимые директории, если их нет"""
        cls.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        cls.FILES_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    async def save_image(cls, file: UploadFile) -> Tuple[str, str]:
        """
        Сохраняет изображение и возвращает (путь к файлу, имя файла)
        """
        await cls.ensure_directories()
        
        # Проверяем тип файла
        content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        if content_type not in cls.ALLOWED_IMAGE_TYPES:
            raise HTTPException(400, f"Invalid image type. Allowed: {cls.ALLOWED_IMAGE_TYPES}")
        
        # Проверяем размер
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
        
        if size > cls.MAX_FILE_SIZE:
            raise HTTPException(400, f"File too large. Max size: {cls.MAX_FILE_SIZE} bytes")
        
        # Генерируем уникальное имя файла
        ext = Path(file.filename).suffix
        filename = f"{uuid.uuid4()}{ext}"
        file_path = cls.IMAGES_DIR / filename
        
        # Сохраняем файл
        async with aiofiles.open(file_path, 'wb') as buffer:
            content = await file.read()
            await buffer.write(content)
        
        return str(file_path), filename
    
    @classmethod
    async def save_file(cls, file: UploadFile, user_id: int) -> Tuple[str, str, int, str]:
        """
        Сохраняет файл и возвращает (путь к файлу, имя файла, размер, mime-тип)
        """
        await cls.ensure_directories()
        
        # Проверяем тип файла
        content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        if content_type not in cls.ALLOWED_FILE_TYPES and not content_type.startswith("image/"):
            raise HTTPException(400, f"Invalid file type. Allowed: {cls.ALLOWED_FILE_TYPES}")
        
        # Проверяем размер
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
        
        if size > cls.MAX_FILE_SIZE:
            raise HTTPException(400, f"File too large. Max size: {cls.MAX_FILE_SIZE} bytes")
        
        # Генерируем уникальное имя файла
        original_filename = file.filename
        ext = Path(original_filename).suffix
        filename = f"{uuid.uuid4()}{ext}"
        file_path = cls.FILES_DIR / filename
        
        # Сохраняем файл
        async with aiofiles.open(file_path, 'wb') as buffer:
            content = await file.read()
            await buffer.write(content)
        
        return str(file_path), filename, size, content_type
    
    @classmethod
    async def save_multiple_files(cls, files: List[UploadFile], user_id: int) -> List[Tuple[str, str, int, str]]:
        """Сохраняет несколько файлов"""
        saved_files = []
        for file in files:
            try:
                saved = await cls.save_file(file, user_id)
                saved_files.append(saved)
            except Exception as e:
                # Если произошла ошибка, удаляем уже сохраненные файлы
                for path, _, _, _ in saved_files:
                    try:
                        os.remove(path)
                    except:
                        pass
                raise HTTPException(400, f"Error saving file {file.filename}: {str(e)}")
        return saved_files