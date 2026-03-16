from sqlalchemy import select, or_, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, Union, List
from app.records.models import Record, Institution, Specialty, Subject, File
from app.records.schemas import RecordCreate

class InstitutionCRUD:
    @staticmethod
    async def get_by_id(session: AsyncSession, institution_id: int) -> Optional[Institution]:
        return await session.get(Institution, institution_id)
    
    @staticmethod
    async def get_by_name(session: AsyncSession, name: str) -> Optional[Institution]:
        stmt = select(Institution).where(Institution.name == name)
        return await session.scalar(stmt)
    
    @staticmethod
    async def create(session: AsyncSession, name: str) -> Institution:
        institution = Institution(name=name)
        session.add(institution)
        await session.flush()  # Не коммитим, чтобы получить ID
        return institution
    
    @staticmethod
    async def get_or_create(session: AsyncSession, value: Union[int, str]) -> Institution:
        """Получает институт по ID или создает новый по названию"""
        if isinstance(value, int):
            institution = await InstitutionCRUD.get_by_id(session, value)
            if not institution:
                raise ValueError(f"Institution with id {value} not found")
            return institution
        else:
            # Ищем по названию
            institution = await InstitutionCRUD.get_by_name(session, value)
            if not institution:
                # Создаем новый
                institution = await InstitutionCRUD.create(session, value)
            return institution
    
    @staticmethod
    async def get_all(session: AsyncSession) -> List[Institution]:
        stmt = select(Institution).order_by(Institution.name)
        result = await session.execute(stmt)
        return result.scalars().all()

class SpecialtyCRUD:
    @staticmethod
    async def get_by_id(session: AsyncSession, specialty_id: int) -> Optional[Specialty]:
        return await session.get(Specialty, specialty_id)
    
    @staticmethod
    async def get_by_name(session: AsyncSession, name: str) -> Optional[Specialty]:
        stmt = select(Specialty).where(Specialty.name == name)
        return await session.scalar(stmt)
    
    @staticmethod
    async def create(session: AsyncSession, name: str, institution_id: Optional[int] = None) -> Specialty:
        specialty = Specialty(name=name, institution_id=institution_id)
        session.add(specialty)
        await session.flush()
        return specialty
    
    @staticmethod
    async def get_or_create(session: AsyncSession, value: Union[int, str]) -> Specialty:
        """Получает специальность по ID или создает новую по названию"""
        if isinstance(value, int):
            specialty = await SpecialtyCRUD.get_by_id(session, value)
            if not specialty:
                raise ValueError(f"Specialty with id {value} not found")
            return specialty
        else:
            specialty = await SpecialtyCRUD.get_by_name(session, value)
            if not specialty:
                specialty = await SpecialtyCRUD.create(session, value)
            return specialty
    
    @staticmethod
    async def get_all(session: AsyncSession) -> List[Specialty]:
        stmt = select(Specialty).order_by(Specialty.name)
        result = await session.execute(stmt)
        return result.scalars().all()

class SubjectCRUD:
    @staticmethod
    async def get_by_id(session: AsyncSession, subject_id: int) -> Optional[Subject]:
        return await session.get(Subject, subject_id)
    
    @staticmethod
    async def get_by_name(session: AsyncSession, name: str) -> Optional[Subject]:
        stmt = select(Subject).where(Subject.name == name)
        return await session.scalar(stmt)
    
    @staticmethod
    async def create(session: AsyncSession, name: str) -> Subject:
        subject = Subject(name=name)
        session.add(subject)
        await session.flush()
        return subject
    
    @staticmethod
    async def get_or_create(session: AsyncSession, value: Union[int, str]) -> Subject:
        """Получает предмет по ID или создает новый по названию"""
        if isinstance(value, int):
            subject = await SubjectCRUD.get_by_id(session, value)
            if not subject:
                raise ValueError(f"Subject with id {value} not found")
            return subject
        else:
            subject = await SubjectCRUD.get_by_name(session, value)
            if not subject:
                subject = await SubjectCRUD.create(session, value)
            return subject
    
    @staticmethod
    async def get_all(session: AsyncSession) -> List[Subject]:
        stmt = select(Subject).order_by(Subject.name)
        result = await session.execute(stmt)
        return result.scalars().all()

class FileCRUD:
    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        filename: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        mime_type: str,
        uploaded_by: int
    ) -> File:
        file = File(
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by=uploaded_by
        )
        session.add(file)
        await session.flush()
        return file
    
    @staticmethod
    async def get_by_id(session: AsyncSession, file_id: int) -> Optional[File]:
        return await session.get(File, file_id)

class RecordCRUD:
    @staticmethod
    async def get_by_idempotency_key(session: AsyncSession, key: str) -> Optional[Record]:
        if not key:
            return None
        stmt = select(Record).where(Record.idempotency_key == key)
        return await session.scalar(stmt)
    
    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        title: str,
        description: Optional[str],
        price: int,
        institution_id: Optional[int],
        specialty_id: Optional[int],
        course: int,
        work_type: str,
        subject_id: Optional[int],
        author_id: int,
        image_path: Optional[str] = None,
        files: Optional[List[File]] = None,
        idempotency_key: Optional[str] = None
    ) -> Record:
        record = Record(
            title=title,
            description=description,
            price=price,
            institution_id=institution_id,
            specialty_id=specialty_id,
            course=course,
            work_type=work_type,
            subject_id=subject_id,
            author_id=author_id,
            image_path=image_path,
            idempotency_key=idempotency_key,
            status="published"  # Или другой статус по умолчанию
        )
        
        if files:
            record.files = files
        
        session.add(record)
        await session.flush()
        return record
    
    @staticmethod
    async def get_with_relations(session: AsyncSession, record_id: int) -> Optional[Record]:
        stmt = select(Record).where(Record.id == record_id).options(
            selectinload(Record.institution),
            selectinload(Record.specialty),
            selectinload(Record.subject),
            selectinload(Record.files),
            selectinload(Record.author)
        )
        return await session.scalar(stmt)
    
    @staticmethod
    async def search(
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
    ) -> tuple[List[Record], Optional[int]]:
        """
        Поиск записей с фильтрацией и пагинацией
        Возвращает (список записей, следующий курсор)
        """
        # Собираем только не-None фильтры
        filter_params = {
            k: v for k, v in {
                'institution_id': institution_id,
                'specialty_id': specialty_id,
                'course': course,
                'work_type': work_type,
                'subject_id': subject_id
            }.items() if v is not None
        }
        
        # Базовый запрос
        stmt = select(Record).filter_by(**filter_params).where(Record.status == "published")
        
        # Поиск по тексту
        if search_query:
            pattern = f"%{search_query}%"
            stmt = stmt.where(
                or_(
                    Record.title.ilike(pattern),
                    Record.description.ilike(pattern)
                )
            )
        
        # Пагинация
        if cursor:
            stmt = stmt.where(Record.id < cursor)
        
        stmt = stmt.order_by(Record.id.desc())\
                   .limit(limit + 1)\
                   .options(
                       selectinload(Record.institution),
                       selectinload(Record.specialty)
                   )
        
        result = await session.execute(stmt)
        records = result.scalars().unique().all()
        
        next_cursor = records[-2].id if len(records) > limit else None
        return records[:limit], next_cursor
    
    @staticmethod
    async def count(
        session: AsyncSession,
        *,
        institution_id: Optional[int] = None,
        specialty_id: Optional[int] = None,
        course: Optional[int] = None,
        work_type: Optional[str] = None,
        subject_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> int:
        """Подсчитывает количество записей по фильтрам"""
        # Собираем только не-None фильтры
        filter_params = {
            k: v for k, v in {
                'institution_id': institution_id,
                'specialty_id': specialty_id,
                'course': course,
                'work_type': work_type,
                'subject_id': subject_id
            }.items() if v is not None
        }
        
        query = select(func.count()).select_from(Record).where(Record.status == "published")
        
        # Применяем фильтры через where
        for key, value in filter_params.items():
            if hasattr(Record, key):
                query = query.where(getattr(Record, key) == value)
        
        if search_query:
            pattern = f"%{search_query}%"
            query = query.where(
                or_(
                    Record.title.ilike(pattern),
                    Record.description.ilike(pattern)
                )
            )
        
        result = await session.execute(query)
        return result.scalar()