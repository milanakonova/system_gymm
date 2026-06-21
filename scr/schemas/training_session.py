"""
Pydantic схемы для разовых записей расписания (по дате)
"""
from typing import Optional, List
from datetime import date, time, datetime
from uuid import UUID
from pydantic import BaseModel


class TrainerShort(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    middle_name: Optional[str] = None

    class Config:
        from_attributes = True


class ClientShort(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    middle_name: Optional[str] = None

    class Config:
        from_attributes = True


class ZoneShort(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class TrainingSessionCreate(BaseModel):
    session_date: date
    start_time: time
    end_time: time
    gym_zone_id: int


class TrainingSessionResponse(BaseModel):
    id: UUID
    session_date: date
    start_time: time
    end_time: time
    gym_zone: Optional[ZoneShort] = None
    trainer: TrainerShort
    participants_count: int = 0
    participants: Optional[List[ClientShort]] = None  # только для тренера-владельца
    is_signed: Optional[bool] = None  # только для клиента
    is_cancelled: bool = False
    is_completed: bool = False

    class Config:
        from_attributes = True


