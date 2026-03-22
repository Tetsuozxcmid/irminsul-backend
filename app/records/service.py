from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Union
from app.records.models import Record, File
from app.records.crud import (
    InstitutionCRUD, SpecialtyCRUD, SubjectCRUD, 
    RecordCRUD, FileCRUD,PurchaseCRUD
)
from app.records.schemas import PaginatedRecordsResponse, RecordCreate, RecordCreateResponse, RecordDetailOut, RecordSearchItem

from app.records.file_records import FileService
from app.auth.models import User
from app.auth.crud import UserCRUD
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

    @staticmethod
    async def search_records(
        session: AsyncSession,
        *,
        institution_id: Optional[int] = None,
        specialty_id: Optional[int] = None,
        course: Optional[int] = None,
        work_type: Optional[str] = None,
        subject_id: Optional[int] = None,
        search_query: Optional[str] = None,
        limit: int = 20,
        cursor: Optional[int] = None,
        current_user: Optional[User] = None,
    ) -> PaginatedRecordsResponse:
        """
        Поиск записей с фильтрацией и пагинацией
        """
        # Получаем записи
        records, next_cursor = await RecordCRUD.search(
            session=session,
            institution_id=institution_id,
            specialty_id=specialty_id,
            course=course,
            work_type=work_type,
            subject_id=subject_id,
            search_query=search_query,
            limit=limit,
            cursor=cursor
        )
        
        # Получаем общее количество
        total = await RecordCRUD.count(
            session=session,
            institution_id=institution_id,
            specialty_id=specialty_id,
            course=course,
            work_type=work_type,
            subject_id=subject_id,
            search_query=search_query
        )
        
        # Формируем ответ
        items = []
        for record in records:
            short_desc = record.description[:150] + "..." if record.description and len(record.description) > 150 else (record.description or "")
            
            items.append(RecordSearchItem(
                id=record.id,
                title=record.title,
                image_path=record.image_path,
                short_description=short_desc,
                created_at=record.created_at,
                downloads_count=record.downloads_count,
                avg_rating=record.avg_rating,
                price=record.price,
                institution_name=record.institution.name if record.institution else None,
                specialty_name=record.specialty.name if record.specialty else None,
                work_type=record.work_type,
                course=record.course
            ))
        
        return PaginatedRecordsResponse(
            items=items,
            next_cursor=next_cursor,
            total=total
        )
    
    @staticmethod
    async def get_record_detail(
        session: AsyncSession,
        record_id: int,
        current_user: Optional[User] = None
    ) -> RecordDetailOut:
        """
        Получает детальную информацию о записи
        """
        record = await RecordCRUD.get_with_relations(session, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        
        # Проверяем, купил ли текущий пользователь эту запись
        bought = False
        if current_user:
            bought = await PurchaseCRUD.has_purchased(session, current_user.id, record_id)
        
        return RecordDetailOut(
            id=record.id,
            title=record.title,
            description=record.description,
            price=record.price,
            institution={
                "id": record.institution.id,
                "name": record.institution.name
            } if record.institution else None,
            specialty={
                "id": record.specialty.id,
                "name": record.specialty.name
            } if record.specialty else None,
            course=record.course,
            work_type=record.work_type,
            subject={
                "id": record.subject.id,
                "name": record.subject.name
            } if record.subject else None,
            image_path=record.image_path,
            author_id=record.author_id,
            author_name=record.author.username if record.author else "Unknown",
            downloads_count=record.downloads_count,
            avg_rating=record.avg_rating,
            created_at=record.created_at,
            updated_at=record.updated_at,
            published_at=record.published_at,
            files_count=len(record.files) if record.files else 0,
            bought=bought  
        )
    @staticmethod
    async def buy_record(
        session: AsyncSession,
        record_id: int,
        user: User
    ) -> dict:
        """
        Покупка записи
        Возвращает статус покупки и обновленный баланс
        """
        # Получаем запись с блокировкой для избежания race condition
        stmt = select(Record).where(Record.id == record_id).with_for_update()
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        
        # Проверяем статус записи (только опубликованные можно купить)
        if record.status != "published":
            raise HTTPException(
                status_code=400, 
                detail="Record is not available for purchase"
            )
        
        # Проверяем, не купил ли уже
        already_bought = await PurchaseCRUD.has_purchased(session, user.id, record_id)
        if already_bought:
            raise HTTPException(
                status_code=400, 
                detail="You have already purchased this record"
            )
        
        # Проверяем баланс
        if user.balance < record.price:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient balance. Need {record.price}, have {user.balance}"
            )
        
        try:
            # 1. Списание у покупателя
            buyer_updated = await UserCRUD.update_balance(
                session, 
                user.id, 
                -record.price
            )
            
            # 2. Начисление автору (если покупатель не автор)
            if record.author_id != user.id:
                await UserCRUD.update_balance(
                    session, 
                    record.author_id, 
                    record.price
                )
            
            # 3. Создаем запись о покупке
            await PurchaseCRUD.create_purchase(
                session, 
                user.id, 
                record_id, 
                record.price
            )
            
            # 4. Увеличиваем счетчик скачиваний
            record.downloads_count += 1
            
            # 5. Коммитим все изменения
            await session.commit()
            
            # 6. Возвращаем результат
            return {
                "success": True,
                "record_id": record_id,
                "record_title": record.title,
                "price": record.price,
                "new_balance": buyer_updated.balance,
                "message": "Purchase successful"
            }
            
        except Exception as e:
            # В случае ошибки откатываем транзакцию
            await session.rollback()
            raise HTTPException(
                status_code=500, 
                detail=f"Purchase failed: {str(e)}"
            )