"""
Репозиторий для работы с абонементами
"""
from typing import Optional, List
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session

from scr.db.models import Subscription, SubscriptionType


class SubscriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, subscription: Subscription) -> Subscription:
        """Создание абонемента"""
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def get_by_id(self, subscription_id: UUID) -> Optional[Subscription]:
        """Получение абонемента по ID"""
        return self.db.query(Subscription).filter(Subscription.id == subscription_id).first()

    def get_by_contract_id(self, contract_id: UUID) -> List[Subscription]:
        """Получение всех абонементов контракта"""
        return self.db.query(Subscription).filter(Subscription.contract_id == contract_id).all()

    def get_active_subscriptions(self, client_id: UUID) -> List[Subscription]:
        """Получение активных абонементов клиента"""
        from scr.db.models import Contract
        return self.db.query(Subscription).join(Contract).filter(
            Contract.client_id == client_id,
            Subscription.is_active == True
        ).all()

    def get_all(
        self,
        contract_id: Optional[UUID] = None,
        service_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[Subscription]:
        """Получение всех абонементов с фильтрацией"""
        query = self.db.query(Subscription)
        if contract_id:
            query = query.filter(Subscription.contract_id == contract_id)
        if service_id:
            query = query.filter(Subscription.service_id == service_id)
        if is_active is not None:
            query = query.filter(Subscription.is_active == is_active)
        return query.all()

    def update(self, subscription: Subscription) -> Subscription:
        """Обновление абонемента"""
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def delete(self, subscription: Subscription) -> None:
        """Удаление абонемента"""
        self.db.delete(subscription)
        self.db.commit()

