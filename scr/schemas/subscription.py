"""
Pydantic схемы для абонементов
"""
from typing import Optional
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel

from scr.db.models import SubscriptionType


class SubscriptionBase(BaseModel):
    """Базовая схема абонемента"""
    service_id: int
    subscription_type: SubscriptionType
    start_date: date
    end_date: Optional[date] = None
    total_visits: Optional[int] = None  # Для VISIT_BASED


class SubscriptionCreate(SubscriptionBase):
    """Схема для создания абонемента"""
    contract_id: UUID


class SubscriptionUpdate(BaseModel):
    """Схема для обновления абонемента"""
    remaining_visits: Optional[int] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class SubscriptionResponse(SubscriptionBase):
    """Схема ответа с данными абонемента"""
    id: UUID
    contract_id: UUID
    remaining_visits: Optional[int]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

