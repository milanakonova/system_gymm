"""
Сервис для работы с контрактами и абонементами
"""
from typing import List
from uuid import UUID
from datetime import date, datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from scr.db.models import Contract, ContractStatus, Subscription, SubscriptionType, User, UserRole
from scr.db.repositories.contract_repository import ContractRepository
from scr.db.repositories.subscription_repository import SubscriptionRepository
from scr.schemas.contract import ContractCreate, ContractUpdate
from scr.schemas.subscription import SubscriptionCreate


class ContractService:
    def __init__(self, db: Session):
        self.db = db
        self.contract_repo = ContractRepository(db)
        self.subscription_repo = SubscriptionRepository(db)

    def create_contract(self, contract_data: ContractCreate, current_user: User) -> Contract:
        """Создание контракта (только администратор)"""
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только администратор может создавать контракты"
            )

        # Проверка уникальности номера контракта
        if self.contract_repo.get_by_contract_number(contract_data.contract_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Контракт с таким номером уже существует"
            )

        contract = Contract(
            client_id=contract_data.client_id,
            contract_number=contract_data.contract_number,
            status=ContractStatus.DRAFT,
            start_date=contract_data.start_date,
            end_date=contract_data.end_date,
            notes=contract_data.notes
        )

        return self.contract_repo.create(contract)

    def get_contract(self, contract_id: UUID, current_user: User) -> Contract:
        """Получение контракта"""
        contract = self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Контракт не найден"
            )

        # Клиент может видеть только свои контракты
        if current_user.role == UserRole.CLIENT and contract.client_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра этого контракта"
            )

        return contract

    def get_client_contracts(self, client_id: UUID, current_user: User) -> List[Contract]:
        """Получение контрактов клиента"""
        # Клиент может видеть только свои контракты
        if current_user.role == UserRole.CLIENT and client_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав"
            )

        return self.contract_repo.get_by_client_id(client_id)

    def update_contract(
        self,
        contract_id: UUID,
        contract_data: ContractUpdate,
        current_user: User
    ) -> Contract:
        """Обновление контракта"""
        contract = self.get_contract(contract_id, current_user)

        # Только администратор может обновлять контракты
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только администратор может обновлять контракты"
            )

        update_data = contract_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contract, field, value)

        return self.contract_repo.update(contract)

    def activate_contract(self, contract_id: UUID, current_user: User) -> Contract:
        """Активация контракта"""
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только администратор может активировать контракты"
            )

        contract = self.get_contract(contract_id, current_user)
        contract.status = ContractStatus.ACTIVE
        contract.signed_at = datetime.now(timezone.utc)
        return self.contract_repo.update(contract)

    def create_subscription(
        self,
        contract_id: UUID,
        subscription_data: SubscriptionCreate,
        current_user: User
    ) -> Subscription:
        """Создание абонемента для контракта"""
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только администратор может создавать абонементы"
            )

        contract = self.get_contract(contract_id, current_user)
        
        if contract.status != ContractStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Абонемент можно создать только для активного контракта"
            )

        subscription = Subscription(
            contract_id=contract_id,
            service_id=subscription_data.service_id,
            subscription_type=subscription_data.subscription_type,
            start_date=subscription_data.start_date,
            end_date=subscription_data.end_date,
            total_visits=subscription_data.total_visits,
            remaining_visits=subscription_data.total_visits if subscription_data.subscription_type == SubscriptionType.VISIT_BASED else None,
            is_active=True
        )

        return self.subscription_repo.create(subscription)

    def get_client_active_subscriptions(self, client_id: UUID, current_user: User) -> List[Subscription]:
        """Получение активных абонементов клиента"""
        # Клиент может видеть только свои абонементы
        if current_user.role == UserRole.CLIENT and client_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав"
            )

        return self.subscription_repo.get_active_subscriptions(client_id)

    def use_visit(self, subscription_id: UUID) -> Subscription:
        """Использование одного посещения из абонемента"""
        subscription = self.subscription_repo.get_by_id(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Абонемент не найден"
            )

        if not subscription.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Абонемент неактивен"
            )

        if subscription.subscription_type == SubscriptionType.VISIT_BASED:
            if subscription.remaining_visits is None or subscription.remaining_visits <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Нет доступных посещений в абонементе"
                )
            subscription.remaining_visits -= 1

        elif subscription.subscription_type == SubscriptionType.TIME_BASED:
            if subscription.end_date and subscription.end_date < date.today():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Абонемент истек"
                )

        return self.subscription_repo.update(subscription)

