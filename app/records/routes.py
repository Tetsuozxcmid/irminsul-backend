from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Union
import json

from app.db.session import get_db
from app.records.schemas import (
    RecordCreate, RecordCreateResponse, RecordOut,
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

@router.get("/{record_id}", response_model=RecordOut)
async def get_record(
    record_id: int,
    session: AsyncSession = Depends(get_db)
):
    """Получение записи по ID"""
    record = await RecordCRUD.get_with_relations(session, record_id)
    if not record:
        raise HTTPException(404, "Record not found")
    return record