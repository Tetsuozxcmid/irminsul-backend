from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Union
from app.records.models import Record, File
from app.records.crud import (
    InstitutionCRUD, SpecialtyCRUD, SubjectCRUD, 
    RecordCRUD, FileCRUD
)
from app.records.schemas import RecordCreate, RecordCreateResponse
from app.records.file_records import FileService
from app.auth.models import User

class RecordService:
    
    @staticmethod
    async def create_record(
        session: AsyncSession,
        *,
        data: RecordCreate,
        author: User,
        image: Optional[UploadFile] = None,
        files: List[UploadFile] = []
    ) -> RecordCreateResponse:
        """
        Создает новую запись с обработкой справочников и файлов
        """
        # Проверка идемпотентности
        if data.idempotency_key:
            existing = await RecordCRUD.get_by_idempotency_key(session, data.idempotency_key)
            if existing:
                # Возвращаем существующую запись
                return RecordCreateResponse(
                    record_id=existing.id,
                    institution_id=existing.institution_id,
                    specialty_id=existing.specialty_id,
                    subject_id=existing.subject_id,
                    image_path=existing.image_path,
                    files=existing.files,
                    message="Record already exists"
                )
        
        # Обработка института
        institution = await InstitutionCRUD.get_or_create(session, data.institution)
        
        # Обработка специальности
        # Если institution создан новый, передаем его ID в специальность
        specialty_value = data.specialty
        if isinstance(data.specialty, str) and institution.id:
            specialty = await SpecialtyCRUD.get_or_create(session, data.specialty)
            # Обновляем institution_id, если его нет
            if not specialty.institution_id:
                specialty.institution_id = institution.id
        else:
            specialty = await SpecialtyCRUD.get_or_create(session, data.specialty)
        
        # Обработка предмета
        subject = await SubjectCRUD.get_or_create(session, data.subject)
        
        # Сохранение изображения
        image_path = None
        if image:
            image_path, _ = await FileService.save_image(image)
        
        # Сохранение файлов
        saved_files = []
        if files:
            file_infos = await FileService.save_multiple_files(files, author.id)
            for file_path, filename, size, mime_type in file_infos:
                file = await FileCRUD.create(
                    session=session,
                    filename=filename,
                    original_filename=filename,  # Можно сохранить оригинальное имя
                    file_path=file_path,
                    file_size=size,
                    mime_type=mime_type,
                    uploaded_by=author.id
                )
                saved_files.append(file)
        
        # Создание записи
        record = await RecordCRUD.create(
            session=session,
            title=data.title,
            description=data.description,
            price=data.price,
            institution_id=institution.id,
            specialty_id=specialty.id,
            course=data.course,
            work_type=data.work_type.value,
            subject_id=subject.id,
            author_id=author.id,
            image_path=image_path,
            files=saved_files,
            idempotency_key=data.idempotency_key
        )
        
        # Коммитим транзакцию
        await session.commit()
        await session.refresh(record)
        
        # Загружаем связи для ответа
        record_with_rels = await RecordCRUD.get_with_relations(session, record.id)
        
        return RecordCreateResponse(
            record_id=record.id,
            institution_id=institution.id,
            specialty_id=specialty.id,
            subject_id=subject.id,
            image_path=image_path,
            files=record_with_rels.files if record_with_rels else [],
            message="Record created successfully"
        )