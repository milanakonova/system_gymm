"""
Pydantic схемы для расписания тренеров
"""
from typing import Optional
from datetime import time, datetime
from uuid import UUID
from pydantic import BaseModel


class TrainerScheduleBase(BaseModel):
    """Базовая схема расписания"""
    day_of_week: int  # 0-6 (понедельник-воскресенье)
    start_time: time
    end_time: time
    is_working: bool = True
    gym_zone_id: Optional[int] = None  # ID зала


class TrainerScheduleCreate(TrainerScheduleBase):
    """Схема для создания расписания"""
    trainer_id: UUID


class TrainerScheduleUpdate(BaseModel):
    """Схема для обновления расписания"""
    day_of_week: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_working: Optional[bool] = None
    is_cancelled: Optional[bool] = None
    cancellation_reason: Optional[str] = None


class TrainerScheduleResponse(TrainerScheduleBase):
    """Схема ответа с данными расписания"""
    id: int
    trainer_id: UUID
    is_cancelled: bool
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]
    gym_zone_id: Optional[int] = None

    class Config:
        from_attributes = True

