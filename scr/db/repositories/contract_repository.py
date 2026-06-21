"""
Репозиторий для работы с контрактами
"""
from typing import Optional, List
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session

from scr.db.models import Contract, ContractStatus


class ContractRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, contract: Contract) -> Contract:
        """Создание контракта"""
        self.db.add(contract)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def get_by_id(self, contract_id: UUID) -> Optional[Contract]:
        """Получение контракта по ID"""
        return self.db.query(Contract).filter(Contract.id == contract_id).first()

    def get_by_client_id(self, client_id: UUID) -> List[Contract]:
        """Получение всех контрактов клиента"""
        return self.db.query(Contract).filter(Contract.client_id == client_id).all()

    def get_by_contract_number(self, contract_number: str) -> Optional[Contract]:
        """Получение контракта по номеру"""
        return self.db.query(Contract).filter(Contract.contract_number == contract_number).first()

    def get_all(
        self,
        client_id: Optional[UUID] = None,
        status: Optional[ContractStatus] = None
    ) -> List[Contract]:
        """Получение всех контрактов с фильтрацией"""
        query = self.db.query(Contract)
        if client_id:
            query = query.filter(Contract.client_id == client_id)
        if status:
            query = query.filter(Contract.status == status)
        return query.all()

    def get_active_contracts(self, client_id: UUID) -> List[Contract]:
        """Получение активных контрактов клиента"""
        return self.db.query(Contract).filter(
            Contract.client_id == client_id,
            Contract.status == ContractStatus.ACTIVE
        ).all()

    def update(self, contract: Contract) -> Contract:
        """Обновление контракта"""
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def delete(self, contract: Contract) -> None:
        """Удаление контракта"""
        self.db.delete(contract)
        self.db.commit()

