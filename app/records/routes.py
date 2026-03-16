from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Union
import json

from app.db.session import get_db
from app.records.schemas import (
    PaginatedRecordsResponse, RecordCreate, RecordCreateResponse, RecordDetailOut, RecordOut,
    InstitutionOut, SpecialtyOut, SubjectOut
)
from app.records.service import RecordService
from app.records.crud import InstitutionCRUD, RecordCRUD, SpecialtyCRUD, SubjectCRUD
from app.users.dependency import get_current_user
from app.auth.models import User

router = APIRouter(prefix="/records", tags=["Records"])

@router.post("/create", response_model=RecordCreateResponse)
async def create_record(
    # Form fields
    title: str = Form(...),
    description: Optional[str] = Form(None),
    price: int = Form(...),
    institution: str = Form(...),  # Может быть ID или название
    specialty: str = Form(...),     # Может быть ID или название
    course: int = Form(...),
    work_type: str = Form(...),
    subject: str = Form(...),       # Может быть ID или название
    idempotency_key: Optional[str] = Form(None),
    
    # Files
    image: Optional[UploadFile] = File(None),
    files: List[UploadFile] = File(default=[]),
    
    # Dependencies
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Создание новой записи (работы)
    
    - **institution**, **specialty**, **subject** могут быть:
        - ID существующей записи (число)
        - Название для создания новой записи (строка)
    - **image** - основное изображение (опционально)
    - **files** - дополнительные файлы (массив, опционально)
    - **idempotency_key** - ключ идемпотентности (опционально)
    """
    # Преобразуем строки в нужный формат
    def parse_field(value: str) -> Union[int, str]:
        try:
            return int(value)
        except ValueError:
            return value
    
    # Создаем объект данных
    record_data = RecordCreate(
        title=title,
        description=description,
        price=price,
        institution=parse_field(institution),
        specialty=parse_field(specialty),
        course=course,
        work_type=work_type,
        subject=parse_field(subject),
        idempotency_key=idempotency_key
    )
    
    return await RecordService.create_record(
        session=session,
        data=record_data,
        author=user,
        image=image,
        files=files
    )

@router.get("/institutions", response_model=List[InstitutionOut])
async def get_institutions(
    session: AsyncSession = Depends(get_db)
):
    """Получение списка всех вузов"""
    return await InstitutionCRUD.get_all(session)

@router.get("/specialties", response_model=List[SpecialtyOut])
async def get_specialties(
    session: AsyncSession = Depends(get_db)
):
    """Получение списка всех специальностей"""
    return await SpecialtyCRUD.get_all(session)

@router.get("/subjects", response_model=List[SubjectOut])
async def get_subjects(
    session: AsyncSession = Depends(get_db)
):
    """Получение списка всех предметов"""
    return await SubjectCRUD.get_all(session)



@router.get("/search", response_model=PaginatedRecordsResponse)
async def search_records(
    # Фильтры
    institution_id: Optional[int] = Query(None, description="ID вуза"),
    specialty_id: Optional[int] = Query(None, description="ID специальности"),
    course: Optional[int] = Query(None, ge=1, le=6, description="Курс"),
    work_type: Optional[str] = Query(None, description="Тип работы (course_work, diploma, etc)"),
    subject_id: Optional[int] = Query(None, description="ID предмета"),
    q: Optional[str] = Query(None, description="Поисковый запрос"),
    
    # Пагинация
    limit: int = Query(20, ge=1, le=100, description="Количество записей на странице"),
    cursor: Optional[int] = Query(None, description="ID последней записи с предыдущей страницы"),
    
    # Зависимости
    session: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """
    Поиск записей с фильтрацией и пагинацией
    
    - **q** - поиск по названию и описанию
    - **institution_id**, **specialty_id**, **course**, **work_type**, **subject_id** - фильтры
    - **limit** - количество записей на странице (1-100)
    - **cursor** - ID последней записи с предыдущей страницы для пагинации
    
    Примеры:
    - `/api/records/search?limit=10` - первые 10 записей
    - `/api/records/search?institution_id=1&course=4` - фильтр по вузу и курсу
    - `/api/records/search?q=диплом&limit=20` - поиск по тексту
    """
    return await RecordService.search_records(
        session=session,
        institution_id=institution_id,
        specialty_id=specialty_id,
        course=course,
        work_type=work_type,
        subject_id=subject_id,
        search_query=q,
        limit=limit,
        cursor=cursor,
        current_user=user
    )

@router.get("/{record_id}", response_model=RecordDetailOut)
async def get_record_detail(
    record_id: int,
    session: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """
    Получение детальной информации о записи по ID
    
    Возвращает полную информацию о записи, включая связанные данные
    (вуз, специальность, предмет, автор, количество файлов)
    """
    return await RecordService.get_record_detail(
        session=session,
        record_id=record_id,
        current_user=user
    )