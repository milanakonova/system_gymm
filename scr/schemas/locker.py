"""
Pydantic схемы для шкафчиков
"""
from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class LockerBase(BaseModel):
    """Базовая схема шкафчика"""
    locker_number: str
    zone: Optional[str] = None
    gender: str  # "men" or "women"
    is_available: bool = True


class LockerCreate(LockerBase):
    """Схема для создания шкафчика"""
    pass


class LockerUpdate(BaseModel):
    """Схема для обновления шкафчика"""
    status: Optional[str] = None
    code: Optional[int] = None
    is_available: Optional[bool] = None
    occupied_by_user_id: Optional[UUID] = None


class LockerResponse(BaseModel):
    """Схема ответа с данными шкафчика"""
    id: int
    locker_number: str
    zone: Optional[str]
    gender: str
    status: str
    code: Optional[int]
    is_available: bool
    occupied_by_user_id: Optional[UUID]
    occupied_at: Optional[datetime]

    class Config:
        from_attributes = True

