"""
Pydantic схемы для бронирований
"""
from typing import Optional
from datetime import date, time, datetime
from uuid import UUID
from pydantic import BaseModel

from scr.db.models import BookingStatus


class BookingBase(BaseModel):
    """Базовая схема бронирования"""
    service_id: int
    booking_date: date
    start_time: time
    end_time: time
    notes: Optional[str] = None


class BookingCreate(BookingBase):
    """Схема для создания бронирования"""
    subscription_id: Optional[UUID] = None
    trainer_schedule_id: Optional[int] = None


class BookingUpdate(BaseModel):
    """Схема для обновления бронирования"""
    booking_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    status: Optional[BookingStatus] = None
    notes: Optional[str] = None


class BookingResponse(BookingBase):
    """Схема ответа с данными бронирования"""
    id: UUID
    client_id: UUID
    subscription_id: Optional[UUID]
    trainer_schedule_id: Optional[int]
    status: BookingStatus
    created_at: datetime

    class Config:
        from_attributes = True


class BookingWithDetails(BookingResponse):
    """Бронирование с деталями"""
    client_name: Optional[str] = None
    service_name: Optional[str] = None
    trainer_name: Optional[str] = None

    class Config:
        from_attributes = True

