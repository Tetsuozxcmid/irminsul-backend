from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class NotificationOut(BaseModel):
    """Объект уведомления в API."""

    id: int
    user_id: int
    title: str
    source: str
    payload: Optional[dict[str, Any]] = None
    created_at: datetime
    read: bool
    idempotency_key: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationCreateInternal(BaseModel):
    """Тело POST /api/notifications (внутренний вызов)."""

    user_id: int = Field(..., description="Получатель")
    title: str = Field(..., min_length=1, max_length=500)
    source: str = Field(..., min_length=1, max_length=100)
    payload: Optional[dict[str, Any]] = None
    idempotency_key: Optional[str] = Field(None, max_length=255)


class NotificationPatch(BaseModel):
    read: Optional[bool] = None
