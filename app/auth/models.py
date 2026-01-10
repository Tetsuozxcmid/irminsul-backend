from sqlalchemy import DateTime, String, Boolean, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
import enum
from typing import Optional
from ..db.base import Base

class UserRole(str, enum.Enum):
    MIDDLE = "middle"
    HIGH = "high"
    HELL = "hell"

class AuthProvider(str, enum.Enum):
    YANDEX = "yandex"
    GOOGLE = "google"
    VK = "vk"
    GITHUB = "github"
    MAILRU = "mailru"
    ODNOKLASSNIKI = "odnoklassniki"
    LOCAL = "local"  

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    

    username: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        nullable=False,
        index=True
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), 
        unique=True, 
        nullable=True,
        index=True
    )
    

    provider_id: Mapped[Optional[str]] = mapped_column(
        String(100), 
        unique=True, 
        nullable=True, 
        index=True
    )
    
    auth_provider: Mapped[AuthProvider] = mapped_column(
        Enum(AuthProvider, name="auth_provider_enum", create_constraint=True),
        nullable=False
    )
    
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
 
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", create_constraint=True),
        default=UserRole.MIDDLE,
        nullable=False
    )
    

    full_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), 
        onupdate=func.now(),
        nullable=True
    )
    

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username}, provider={self.auth_provider})"
    
    @property
    def is_yandex_user(self) -> bool:
        return self.auth_provider == AuthProvider.YANDEX
    
    @property
    def is_moderator(self) -> bool:
        return self.role in [UserRole.HIGH]
    
    @property
    def is_developer(self) -> bool:
        return self.role == UserRole.HELL