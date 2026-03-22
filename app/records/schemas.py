from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Union
from enum import Enum
from datetime import datetime

class WorkTypeEnum(str, Enum):
    COURSE_WORK = "course_work"
    DIPLOMA = "diploma"
    ESSAY = "essay"
    PRACTICE_REPORT = "practice_report"
    OTHER = "other"

class RecordStatusEnum(str, Enum):
    DRAFT = "draft"
    MODERATION = "moderation"
    PUBLISHED = "published"
    REJECTED = "rejected"
    ARCHIVED = "archived"

# Схемы для справочников
class InstitutionBase(BaseModel):
    name: str

class InstitutionCreate(InstitutionBase):
    pass

class InstitutionOut(InstitutionBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class SpecialtyBase(BaseModel):
    name: str
    institution_id: Optional[int] = None

class SpecialtyCreate(SpecialtyBase):
    pass

class SpecialtyOut(SpecialtyBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class SubjectBase(BaseModel):
    name: str

class SubjectCreate(SubjectBase):
    pass

class SubjectOut(SubjectBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Схемы для файлов
class FileOut(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Основная схема для создания записи
class RecordCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: int = Field(..., ge=0)
    institution: Union[int, str]  # может быть ID или название
    specialty: Union[int, str]     # может быть ID или название
    course: int = Field(..., ge=1, le=6)
    work_type: WorkTypeEnum
    subject: Union[int, str]       # может быть ID или название
    idempotency_key: Optional[str] = None

class RecordCreateResponse(BaseModel):
    record_id: int
    institution_id: int
    specialty_id: int
    subject_id: int
    image_path: Optional[str] = None
    files: List[FileOut]
    message: str = "Record created successfully"

# Схема для ответа с полной информацией о записи
class RecordOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    price: int
    institution: Optional[InstitutionOut]
    specialty: Optional[SpecialtyOut]
    course: int
    work_type: WorkTypeEnum
    subject: Optional[SubjectOut]
    image_path: Optional[str]
    files: List[FileOut]
    author_id: int
    downloads_count: int
    avg_rating: float
    status: RecordStatusEnum
    created_at: datetime
    updated_at: Optional[datetime]
    published_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class RecordSearchItem(BaseModel):
    """Элемент для поисковой выдачи"""
    id: int
    title: str
    image_path: Optional[str] = None
    short_description: str
    created_at: datetime
    downloads_count: int
    avg_rating: float
    price: int
    institution_name: Optional[str] = None
    specialty_name: Optional[str] = None
    work_type: str
    course: int
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedRecordsResponse(BaseModel):
    """Ответ с пагинацией"""
    items: List[RecordSearchItem]
    next_cursor: Optional[int] = None
    total: int

class RecordDetailOut(BaseModel):
    """Детальная информация о записи"""
    id: int
    title: str
    description: Optional[str]
    price: int
    institution: Optional[dict] = None
    specialty: Optional[dict] = None
    course: int
    work_type: str
    subject: Optional[dict] = None
    image_path: Optional[str]
    author_id: int
    author_name: str
    downloads_count: int
    avg_rating: float
    created_at: datetime
    updated_at: Optional[datetime]
    published_at: Optional[datetime]
    files_count: int
    bought: bool = False  # ДОБАВИТЬ ЭТУ СТРОКУ
    
    model_config = ConfigDict(from_attributes=True)