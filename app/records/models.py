from sqlalchemy import String, Text, Integer, Enum, ForeignKey, DateTime, Boolean, Float, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func,UniqueConstraint
import enum
from typing import Optional, List
from ..db.base import Base


record_files = Table(
    'record_files',
    Base.metadata,
    Column('record_id', Integer, ForeignKey('records.id', ondelete='CASCADE'), primary_key=True),
    Column('file_id', Integer, ForeignKey('files.id', ondelete='CASCADE'), primary_key=True)
)

class WorkType(str, enum.Enum):
    COURSE_WORK = "course_work"
    DIPLOMA = "diploma"
    ESSAY = "essay"
    PRACTICE_REPORT = "practice_report"
    OTHER = "other"

class RecordStatus(str, enum.Enum):
    DRAFT = "draft"
    MODERATION = "moderation"
    PUBLISHED = "published"
    REJECTED = "rejected"
    ARCHIVED = "archived"

class Institution(Base):
    __tablename__ = "institutions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    specialties: Mapped[List["Specialty"]] = relationship(back_populates="institution")
    records: Mapped[List["Record"]] = relationship(back_populates="institution")

class Specialty(Base):
    __tablename__ = "specialties"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    institution_id: Mapped[Optional[int]] = mapped_column(ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    institution: Mapped[Optional[Institution]] = relationship(back_populates="specialties")
    records: Mapped[List["Record"]] = relationship(back_populates="specialty")

class Subject(Base):
    __tablename__ = "subjects"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    records: Mapped[List["Record"]] = relationship(back_populates="subject")

class File(Base):
    __tablename__ = "files"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    
    uploader: Mapped["User"] = relationship()
    records: Mapped[List["Record"]] = relationship(
        secondary=record_files,
        back_populates="files"
    )

class Record(Base):
    __tablename__ = "records"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    
    
    institution_id: Mapped[Optional[int]] = mapped_column(ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True)
    specialty_id: Mapped[Optional[int]] = mapped_column(ForeignKey("specialties.id", ondelete="SET NULL"), nullable=True)
    subject_id: Mapped[Optional[int]] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    
    course: Mapped[int] = mapped_column(Integer, nullable=False)
    work_type: Mapped[WorkType] = mapped_column(Enum(WorkType, name="work_type_enum"), nullable=False)
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    
    downloads_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    
    
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, name="record_status_enum"),
        default=RecordStatus.DRAFT,
        nullable=False
    )
    
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    published_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    
    
    institution: Mapped[Optional[Institution]] = relationship(back_populates="records")
    specialty: Mapped[Optional[Specialty]] = relationship(back_populates="records")
    subject: Mapped[Optional[Subject]] = relationship(back_populates="records")
    author: Mapped["User"] = relationship()
    files: Mapped[List[File]] = relationship(
        secondary=record_files,
        back_populates="records",
        cascade="all, delete"
    )

class Purchase(Base):
    __tablename__ = "purchases"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    record_id: Mapped[int] = mapped_column(ForeignKey("records.id", ondelete="CASCADE"), nullable=False)
    price_paid: Mapped[int] = mapped_column(Integer, nullable=False)
    purchased_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    
    
    __table_args__ = (
        UniqueConstraint('user_id', 'record_id', name='unique_user_record_purchase'),
    )