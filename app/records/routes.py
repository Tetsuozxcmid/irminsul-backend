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
from app.users.dependency import get_current_user, get_optional_user
from app.auth.models import User

router = APIRouter(prefix="/records", tags=["Records"])


async def _resolve_search_filters(
    session: AsyncSession,
    *,
    institution_id: Optional[int],
    institution: Optional[str],
    specialty_id: Optional[int],
    specialty: Optional[str],
    subject_id: Optional[int],
    subject: Optional[str],
) -> tuple[Optional[int], Optional[int], Optional[int]]:
    resolved_institution_id = institution_id
    resolved_specialty_id = specialty_id
    resolved_subject_id = subject_id

    if resolved_institution_id is None and institution and institution.strip():
        found = await InstitutionCRUD.get_by_name(session, institution.strip())
        if found:
            resolved_institution_id = found.id

    if resolved_specialty_id is None and specialty and specialty.strip():
        found = await SpecialtyCRUD.get_by_name(session, specialty.strip())
        if found:
            resolved_specialty_id = found.id

    if resolved_subject_id is None and subject and subject.strip():
        found = await SubjectCRUD.get_by_name(session, subject.strip())
        if found:
            resolved_subject_id = found.id

    return resolved_institution_id, resolved_specialty_id, resolved_subject_id

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
    institution: Optional[str] = Query(None, description="Название вуза"),
    specialty_id: Optional[int] = Query(None, description="ID специальности"),
    specialty: Optional[str] = Query(None, description="Название специальности"),
    course: Optional[int] = Query(None, ge=1, le=6, description="Курс"),
    work_type: Optional[str] = Query(None, description="Тип работы (course_work, diploma, etc)"),
    subject_id: Optional[int] = Query(None, description="ID предмета"),
    subject: Optional[str] = Query(None, description="Название предмета"),
    q: Optional[str] = Query(None, description="Поисковый запрос"),
    query: Optional[str] = Query(None, description="Алиас для q (совместимость с фронтом)"),
    
    # Пагинация
    limit: int = Query(20, ge=1, le=100, description="Количество записей на странице"),
    cursor: Optional[int] = Query(None, description="ID последней записи с предыдущей страницы"),
    
    # Зависимости
    session: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Поиск записей с фильтрацией и пагинацией
    
    - **q** / **query** - поиск по названию и описанию
    - **institution_id** / **institution**, **specialty_id** / **specialty**, **subject_id** / **subject** - фильтры
    - **limit** - количество записей на странице (1-100)
    - **cursor** - ID последней записи с предыдущей страницы для пагинации
    
    Примеры:
    - `/api/records/records/search?limit=10` - первые 10 записей
    - `/api/records/records/search?institution_id=1&course=4` - фильтр по вузу и курсу
    - `/api/records/records/search?q=диплом&limit=20` - поиск по тексту
    """
    resolved_institution_id, resolved_specialty_id, resolved_subject_id = (
        await _resolve_search_filters(
            session,
            institution_id=institution_id,
            institution=institution,
            specialty_id=specialty_id,
            specialty=specialty,
            subject_id=subject_id,
            subject=subject,
        )
    )

    search_query = q or query

    return await RecordService.search_records(
        session=session,
        institution_id=resolved_institution_id,
        specialty_id=resolved_specialty_id,
        course=course,
        work_type=work_type,
        subject_id=resolved_subject_id,
        search_query=search_query,
        limit=limit,
        cursor=cursor,
        current_user=user
    )

@router.get("/{record_id}", response_model=RecordDetailOut)
async def get_record_detail(
    record_id: int,
    session: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
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

@router.post("/{record_id}/buy")
async def buy_record(
    record_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Покупка записи
    
    - Списывает внутренние баллы у покупателя
    - Начисляет автору
    - Помечает запись как купленную
    - Увеличивает downloads_count
    
    Returns:
    {
        "success": true,
        "record_id": 1,
        "record_title": "Example Work",
        "price": 500,
        "new_balance": 500,
        "message": "Purchase successful"
    }
    """
    return await RecordService.buy_record(
        session=session,
        record_id=record_id,
        user=user
    )