"""
Pydantic схемы для контрактов
"""
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel

from scr.db.models import ContractStatus


class ContractBase(BaseModel):
    """Базовая схема контракта"""
    contract_number: str
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None


class ContractCreate(ContractBase):
    """Схема для создания контракта"""
    client_id: UUID


class ContractUpdate(BaseModel):
    """Схема для обновления контракта"""
    status: Optional[ContractStatus] = None
    end_date: Optional[date] = None
    signed_at: Optional[datetime] = None
    signed_by_client: Optional[bool] = None
    notes: Optional[str] = None


class ContractResponse(ContractBase):
    """Схема ответа с данными контракта"""
    id: UUID
    client_id: UUID
    status: ContractStatus
    signed_at: Optional[datetime]
    signed_by_client: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ContractWithSubscriptions(ContractResponse):
    """Контракт с абонементами"""
    subscriptions: List["SubscriptionResponse"] = []

    class Config:
        from_attributes = True


from scr.schemas.subscription import SubscriptionResponse
ContractWithSubscriptions.model_rebuild()

